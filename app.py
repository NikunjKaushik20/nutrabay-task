"""
app.py — Nutrabay SOP Training Engine
Premium Streamlit dashboard — 6 tabs, dark theme, GPT-4o-mini + Sarvam AI
"""

import os
import io
import tempfile

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Nutrabay SOP Training Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Internal imports ──────────────────────────────────────────────────────────
from ui.styles import inject_css
from ui.components import (
    render_app_header,
    render_summary_section,
    render_training_steps,
    render_skills_section,
)
from core.pdf_parser import extract_text_from_pdf
from core.sop_preprocessor import preprocess_sop, format_for_prompt
from core.ai_engine import generate_training_content, get_sample_output
from core.sarvam import translate_training_content, generate_audio
from core.certificate import analyse_quiz_results, generate_certificate
from core.slides_generator import generate_slides_html
from core.scenario_engine import generate_scenarios, get_sample_scenarios

# ── CSS ───────────────────────────────────────────────────────────────────────
inject_css()

# ── Session state init ────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "data": None,
        "data_hi": None,
        "sop_text": "",
        "sop_title": "",
        "language": "EN",
        "quiz_answers": {},
        "quiz_submitted": False,
        "quiz_results": None,
        "audio_map": {},
        "slides_html": "",
        "use_sample": False,
        "preprocess_stats": None,
        "cert_id": None,
        "scenarios": [],
        "scenario_answers": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Helper: Get active data (EN or HI) ───────────────────────────────────────
def active_data() -> dict:
    if st.session_state.language == "HI" and st.session_state.data_hi:
        return st.session_state.data_hi
    return st.session_state.data or {}


# ── Header ────────────────────────────────────────────────────────────────────
render_app_header(
    sop_title=st.session_state.sop_title,
    language=st.session_state.language,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📥 Upload",
    "🧩 Summary",
    "🧠 Training",
    "❓ Quiz",
    "🎯 Skills",
    "🎥 Slides",
    "🎮 Scenarios",
])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — UPLOAD
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        '<div class="glass-card"><h3 style="color:#7C3AED;margin-top:0;">📥 Upload your SOP Document</h3>',
        unsafe_allow_html=True,
    )

    input_col1, input_col2 = st.columns([1, 1])

    with input_col1:
        uploaded_file = st.file_uploader(
            "Drag & drop a PDF here, or click to browse",
            type=["pdf"],
            help="Supports any SOP PDF up to 200 MB",
        )

    with input_col2:
        pasted_text = st.text_area(
            "Or paste your SOP text directly",
            height=150,
            placeholder="Paste your Standard Operating Procedure text here...\n\nExample:\n1. Purpose: This SOP covers...\n2. Procedure: First, verify...",
            help="Supports any SOP text — works great for short procedures",
        )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        use_sample = st.checkbox(
            "🧪 Use built-in sample SOP (no PDF needed)",
            value=st.session_state.use_sample,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Language toggle
    st.markdown(
        '<div class="glass-card"><b style="color:#9CA3AF;">🌐 Training Language</b>',
        unsafe_allow_html=True,
    )
    lang = st.radio(
        "",
        options=["EN", "HI"],
        format_func=lambda x: "🇬🇧 English" if x == "EN" else "🇮🇳 हिंदी (Hindi)",
        horizontal=True,
        index=0 if st.session_state.language == "EN" else 1,
        label_visibility="collapsed",
    )
    if lang != st.session_state.language:
        st.session_state.language = lang
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Process button
    process_clicked = st.button("⚡ Generate Training Content", use_container_width=True)

    if process_clicked:
        if use_sample:
            st.session_state.use_sample = True
            with st.spinner("Loading sample SOP training content..."):
                data = get_sample_output()
                st.session_state.data = data
                st.session_state.sop_title = data.get("title", "Sample SOP")
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                st.session_state.quiz_results = None
                st.session_state.cert_id = None
                st.session_state.slides_html = generate_slides_html(data)
                st.session_state.scenarios = get_sample_scenarios()
                st.session_state.scenario_answers = {}
            st.success("✅ Sample content loaded! Switch to the Summary tab.")

        elif uploaded_file is not None or (pasted_text and pasted_text.strip()):
            st.session_state.use_sample = False
            is_pdf = uploaded_file is not None
            tmp_path = None

            if is_pdf:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

            try:
                # Multi-step progress pipeline
                total_steps = 5 if not is_pdf else 5
                progress_bar = st.progress(0, text="📖 Step 1/5: Extracting text...")

                # Step 1: Extract text
                if is_pdf:
                    raw_text = extract_text_from_pdf(tmp_path)
                    os.unlink(tmp_path)
                    tmp_path = None
                else:
                    raw_text = pasted_text.strip()

                st.session_state.sop_text = raw_text
                progress_bar.progress(20, text="🔍 Step 2/5: Preprocessing SOP structure...")

                # Step 2: Preprocess
                preprocessed = preprocess_sop(raw_text)
                prompt_text = format_for_prompt(preprocessed)
                st.session_state.preprocess_stats = preprocessed["stats"]
                progress_bar.progress(35, text="🤖 Step 3/5: GPT-4o-mini generating training content...")

                # Step 3: Generate content with progress callback
                def _progress_cb(step_name, step_num, total):
                    pct = 35 + int((step_num / total) * 35)
                    progress_bar.progress(min(pct, 75), text=f"🤖 Step 3/5: {step_name}...")

                data = generate_training_content(prompt_text, progress_callback=_progress_cb)
                st.session_state.data = data
                st.session_state.sop_title = data.get("title", uploaded_file.name if is_pdf else "Pasted SOP")
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                st.session_state.quiz_results = None
                st.session_state.cert_id = None

                progress_bar.progress(75, text="🎥 Step 4/5: Generating slide deck...")

                # Step 4: Generate slides
                st.session_state.slides_html = generate_slides_html(data)
                progress_bar.progress(85, text="🎮 Step 5/5: Generating interactive scenarios...")

                # Step 5: Generate scenarios
                st.session_state.scenarios = generate_scenarios(data)
                st.session_state.scenario_answers = {}
                progress_bar.progress(100, text="✅ Complete!")

                st.success("✅ Training content generated! Explore the tabs above.")

                # Show preprocessing stats
                stats = preprocessed["stats"]
                input_type = "PDF" if is_pdf else "Text"
                st.markdown(
                    f'<div class="glass-card">'
                    f'<b style="color:#9CA3AF;">📊 Processing Pipeline</b>'
                    f'<p style="color:#6B7280; font-size:0.85rem; margin:0.5rem 0 0;">'
                    f'📄 {input_type} input: {stats["char_count"]:,} chars &nbsp;·&nbsp; '
                    f'📑 Detected {stats["section_count"]} sections &nbsp;·&nbsp; '
                    f'🧹 Stripped {stats["page_markers_stripped"]} page markers &nbsp;·&nbsp; '
                    f'✅ Quiz verified by 2nd AI pass &nbsp;·&nbsp; '
                    f'🎮 {len(st.session_state.scenarios)} scenarios generated'
                    f'</p></div>',
                    unsafe_allow_html=True,
                )

                # Extracted text preview
                with st.expander("🔍 View extracted SOP text"):
                    st.text_area("Raw text", raw_text[:3000], height=200, disabled=True)

            except Exception as e:
                st.error(f"❌ Error processing SOP: {e}")
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            st.warning("⚠️ Please upload a PDF, paste text, or enable the sample SOP checkbox.")

    # Hindi translation (lazy — only when user switches to HI and data exists)
    if (
        st.session_state.language == "HI"
        and st.session_state.data
        and not st.session_state.data_hi
    ):
        with st.spinner("🌐 Translating to Hindi via Sarvam AI..."):
            st.session_state.data_hi = translate_training_content(st.session_state.data)
        st.success("✅ Hindi translation complete!")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — SUMMARY
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.data:
        st.info("👈 Upload an SOP (or use the sample) on the Upload tab first.")
    else:
        data = active_data()

        # Show sample data badge if applicable
        if data.get("is_sample"):
            st.markdown(
                '<div style="background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.4); '
                'border-radius:8px; padding:0.5rem 1rem; margin-bottom:1rem; color:#FCD34D; font-size:0.85rem;">'
                '⚠️ <b>Sample Data</b> — This is hardcoded demo content, not AI-generated from a real SOP.'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<h2 style="color:#E5E7EB; margin-bottom:1.2rem;">📋 {data.get("title","")}</h2>',
            unsafe_allow_html=True,
        )
        render_summary_section(data)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — TRAINING MODULE
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.data:
        st.info("👈 Upload an SOP (or use the sample) on the Upload tab first.")
    else:
        data = active_data()

        if data.get("is_sample"):
            st.markdown(
                '<div style="background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.4); '
                'border-radius:8px; padding:0.5rem 1rem; margin-bottom:1rem; color:#FCD34D; font-size:0.85rem;">'
                '⚠️ <b>Sample Data</b></div>',
                unsafe_allow_html=True,
            )

        col_title, col_audio_btn = st.columns([3, 1])
        with col_title:
            st.markdown(
                f'<h2 style="color:#E5E7EB;">🧠 Training Steps</h2>',
                unsafe_allow_html=True,
            )
        with col_audio_btn:
            if st.session_state.language == "HI":
                if st.button("🔊 Generate Audio Narration"):
                    audio_map = {}
                    audio_errors = []
                    with st.spinner("🎙️ Generating Hindi audio via Sarvam TTS..."):
                        for step in data.get("training_steps", []):
                            num = step.get("step")
                            text = f"{step.get('title', '')}. {step.get('content', '')}"
                            audio_bytes, error = generate_audio(text)
                            if audio_bytes:
                                audio_map[num] = audio_bytes
                            if error:
                                audio_errors.append(error)
                    st.session_state.audio_map = audio_map
                    if audio_map:
                        st.success(f"✅ Audio generated for {len(audio_map)} steps")
                    else:
                        st.warning("Add SARVAM_API_KEY to .env to enable audio.")
                    if audio_errors:
                        with st.expander("⚠️ Audio generation warnings"):
                            for err in audio_errors:
                                st.caption(err)

        render_training_steps(data, audio_map=st.session_state.audio_map)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — QUIZ
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    if not st.session_state.data:
        st.info("👈 Upload an SOP (or use the sample) on the Upload tab first.")
    else:
        # Always use English quiz (multiple choice letters are language-neutral)
        quiz = st.session_state.data.get("quiz", [])

        st.markdown(
            '<h2 style="color:#E5E7EB;">❓ Knowledge Assessment</h2>',
            unsafe_allow_html=True,
        )

        if not quiz:
            st.warning("No quiz questions were generated.")
        else:
            with st.form("quiz_form"):
                answers = {}
                for i, q in enumerate(quiz):
                    q_key = f"q_{i}"
                    st.markdown(
                        f'<div class="quiz-question"><h4>Q{i+1}. {q["question"]}</h4></div>',
                        unsafe_allow_html=True,
                    )
                    options = q.get("options", [])

                    selected = st.radio(
                        f"question_{i}",
                        options=options,
                        key=q_key,
                        label_visibility="collapsed",
                    )
                    if selected:
                        answers[i] = selected.split(".")[0].strip()
                    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

                submitted = st.form_submit_button(
                    "📊 Submit & See Results", use_container_width=True
                )

            if submitted:
                user_answers = [answers.get(i, "") for i in range(len(quiz))]
                results = analyse_quiz_results(quiz, user_answers)
                st.session_state.quiz_results = results
                st.session_state.quiz_submitted = True

                score = results["score"]
                passed = results["passed"]
                correct = results["correct"]
                total = results["total"]

                if passed:
                    st.success(
                        f"🎉 Excellent! You scored **{score}/100** ({correct}/{total} correct). You've passed!"
                    )
                else:
                    st.error(
                        f"📚 You scored **{score}/100** ({correct}/{total} correct). Review the training module and try again."
                    )

                # Show answer feedback
                st.markdown('<h3 style="color:#9CA3AF; margin-top:1.5rem;">📝 Answer Review</h3>', unsafe_allow_html=True)
                for i, q in enumerate(quiz):
                    ua = answers.get(i, "")
                    correct_ans = q.get("answer", "")
                    is_correct = ua.strip().upper() == correct_ans.strip().upper()
                    icon = "✅" if is_correct else "❌"
                    bg = "rgba(16,185,129,0.08)" if is_correct else "rgba(239,68,68,0.08)"
                    border = "#10B981" if is_correct else "#EF4444"
                    st.markdown(
                        f"""<div style="background:{bg}; border-left:3px solid {border};
                                       padding:0.75rem 1rem; border-radius:0 8px 8px 0; margin-bottom:0.75rem;">
                          <b style="color:#E5E7EB;">{icon} Q{i+1}: {q['question']}</b><br/>
                          <span style="color:#9CA3AF; font-size:0.85rem;">
                            Your answer: <b>{ua}</b> &nbsp;·&nbsp; Correct: <b style="color:#10B981;">{correct_ans}</b>
                          </span><br/>
                          <span style="color:#6B7280; font-size:0.82rem;"><i>{q.get('explanation','')}</i></span>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                st.markdown('<p style="color:#9CA3AF; font-size:0.85rem; margin-top:1rem;">👉 Head to the 🎯 Skills tab to download your certificate.</p>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — SKILLS & CERTIFICATE
# ════════════════════════════════════════════════════════════════════════════════
with tab5:
    if not st.session_state.data:
        st.info("👈 Upload an SOP (or use the sample) on the Upload tab first.")
    else:
        data = active_data()
        st.markdown(
            '<h2 style="color:#E5E7EB;">🎯 Skills & Readiness</h2>',
            unsafe_allow_html=True,
        )

        render_skills_section(data, quiz_results=st.session_state.quiz_results)

        # Certificate download
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<b style="color:#9CA3AF;">📄 Download Training Certificate</b>', unsafe_allow_html=True)

        emp_name = st.text_input(
            "Your Name",
            placeholder="Enter your full name for the certificate",
        )

        if st.session_state.quiz_results:
            score = st.session_state.quiz_results["score"]
            passed = st.session_state.quiz_results["passed"]
        else:
            st.markdown(
                '<p style="color:#F59E0B; font-size:0.85rem;">'
                '⚠️ You must complete the quiz first before generating a certificate.</p>',
                unsafe_allow_html=True,
            )
            score = 0
            passed = False

        can_generate_cert = st.session_state.quiz_submitted and passed

        if st.button("🏆 Generate Certificate PDF", disabled=not can_generate_cert, use_container_width=True):
            if not emp_name.strip():
                st.warning("Please enter your name first.")
            else:
                with st.spinner("Generating certificate..."):
                    pdf_bytes, cert_id = generate_certificate(
                        employee_name=emp_name.strip(),
                        sop_title=st.session_state.sop_title,
                        score=score,
                        passed=passed,
                        skills_covered=data.get("skills_covered", []),
                    )
                    st.session_state.cert_id = cert_id
                st.markdown(
                    f'<p style="color:#9CA3AF; font-size:0.82rem;">Certificate ID: <code>{cert_id}</code></p>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    label="⬇️ Download Certificate (PDF)",
                    data=pdf_bytes,
                    file_name=f"certificate_{emp_name.replace(' ','_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        if not can_generate_cert:
            if st.session_state.quiz_submitted and not passed:
                st.markdown(
                    '<p style="color:#F87171; font-size:0.82rem;">'
                    '❌ You must pass the quiz (≥70%) to generate a certificate. '
                    'Review the training module and try again.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<p style="color:#6B7280; font-size:0.82rem;">'
                    'Complete the quiz on the Quiz tab to unlock certificate generation.</p>',
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 6 — SLIDES
# ════════════════════════════════════════════════════════════════════════════════
with tab6:
    if not st.session_state.data:
        st.info("👈 Upload an SOP (or use the sample) on the Upload tab first.")
    elif not st.session_state.slides_html:
        st.warning("Slides were not generated. Re-process the SOP.")
    else:
        data = active_data()
        st.markdown(
            '<h2 style="color:#E5E7EB;">🎥 Training Slide Deck</h2>',
            unsafe_allow_html=True,
        )

        # Download slides button
        slides_bytes = st.session_state.slides_html.encode("utf-8")
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                label="⬇️ Download Slides (HTML)",
                data=slides_bytes,
                file_name=f"{st.session_state.sop_title.replace(' ','_')}_slides.html",
                mime="text/html",
            )

        # Embed reveal.js iframe
        import streamlit.components.v1 as components
        components.html(
            st.session_state.slides_html,
            height=520,
            scrolling=False,
        )


# ════════════════════════════════════════════════════════════════════════════════
# TAB 7 — SCENARIO SIMULATOR
# ════════════════════════════════════════════════════════════════════════════════
with tab7:
    if not st.session_state.data:
        st.info("👈 Upload an SOP (or use the sample) on the Upload tab first.")
    else:
        scenarios = st.session_state.scenarios

        st.markdown(
            '<h2 style="color:#E5E7EB;">🎮 Scenario Simulator</h2>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#9CA3AF; font-size:0.92rem; margin-bottom:1.5rem;">'
            'Test your knowledge in realistic workplace situations. '
            'Choose what you would do — then see if the SOP agrees with your decision.</p>',
            unsafe_allow_html=True,
        )

        if not scenarios:
            st.warning("No scenarios were generated. Re-process the SOP to generate scenarios.")
        else:
            for i, sc in enumerate(scenarios):
                sc_key = f"scenario_{i}"
                ref = sc.get("sop_step_reference", "")

                st.markdown(
                    f'<div class="scenario-card">'
                    f'<div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.75rem;">'
                    f'<span class="step-number">{i+1}</span>'
                    f'<span style="color:#A78BFA; font-size:0.82rem; font-weight:500;">'
                    f'📋 {ref}</span>'
                    f'</div>'
                    f'<p style="color:#E5E7EB; font-size:0.97rem; line-height:1.65; margin:0;">'
                    f'{sc.get("situation", "")}</p></div>',
                    unsafe_allow_html=True,
                )

                choices = sc.get("choices", [])
                choice_labels = [
                    f"{c.get('label', chr(65+j))}. {c.get('text', '')}"
                    for j, c in enumerate(choices)
                ]

                selected = st.radio(
                    f"What would you do?",
                    options=choice_labels,
                    key=sc_key,
                    label_visibility="collapsed",
                )

                # Show feedback when user selects an answer
                if selected and sc_key in st.session_state:
                    selected_label = selected.split(".")[0].strip()
                    for c in choices:
                        if c.get("label", "") == selected_label:
                            is_correct = c.get("is_correct", False)
                            feedback = c.get("feedback", "")
                            if is_correct:
                                st.markdown(
                                    f'<div style="background:rgba(16,185,129,0.1); '
                                    f'border-left:3px solid #10B981; padding:0.75rem 1rem; '
                                    f'border-radius:0 8px 8px 0; margin:0.5rem 0 1.5rem;">'
                                    f'<p style="color:#6EE7B7; font-size:0.9rem; margin:0;">'
                                    f'{feedback}</p></div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    f'<div style="background:rgba(239,68,68,0.08); '
                                    f'border-left:3px solid #EF4444; padding:0.75rem 1rem; '
                                    f'border-radius:0 8px 8px 0; margin:0.5rem 0 1.5rem;">'
                                    f'<p style="color:#FCA5A5; font-size:0.9rem; margin:0;">'
                                    f'{feedback}</p></div>',
                                    unsafe_allow_html=True,
                                )
                            break

                st.markdown(
                    '<hr style="border-color:rgba(255,255,255,0.06); margin:0.5rem 0;">',
                    unsafe_allow_html=True,
                )

# ── Sidebar — API status ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    sarvam_key = os.getenv("SARVAM_API_KEY", "")

    st.markdown(
        f'<p style="font-size:0.85rem;">OpenAI: {"✅ Connected" if openai_key and openai_key != "your_openai_api_key_here" else "❌ Missing"}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="font-size:0.85rem;">Sarvam AI: {"✅ Connected" if sarvam_key and sarvam_key != "your_sarvam_api_key_here" else "⚠️ Optional — Hindi disabled"}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        '<p style="color:#6B7280; font-size:0.8rem;">Add API keys to a <code>.env</code> file in the project root.</p>',
        unsafe_allow_html=True,
    )
    if st.session_state.data:
        st.markdown("---")
        st.markdown("### 📊 Session Info")
        d = st.session_state.data
        st.markdown(
            f"""<p style="font-size:0.82rem; color:#9CA3AF;">
              📄 <b>SOP:</b> {d.get('title','')}<br/>
              📚 <b>Steps:</b> {len(d.get('training_steps',[]))}<br/>
              ❓ <b>Quiz Qs:</b> {len(d.get('quiz',[]))}<br/>
              🎓 <b>Skills:</b> {len(d.get('skills_covered',[]))}
            </p>""",
            unsafe_allow_html=True,
        )

        # Show preprocessing stats if available
        stats = st.session_state.preprocess_stats
        if stats:
            st.markdown("---")
            st.markdown("### 🔬 Preprocessing")
            st.markdown(
                f"""<p style="font-size:0.82rem; color:#9CA3AF;">
                  📏 <b>Chars:</b> {stats['char_count']:,}<br/>
                  📑 <b>Sections:</b> {stats['section_count']}<br/>
                  🧹 <b>Markers stripped:</b> {stats['page_markers_stripped']}
                </p>""",
                unsafe_allow_html=True,
            )
