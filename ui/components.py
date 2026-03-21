"""
components.py — Reusable HTML component builders for the Streamlit UI.
"""

import streamlit as st


def render_app_header(sop_title: str = "", language: str = "EN"):
    """Render the top header bar with app title and optional SOP title."""
    lang_indicator = "🌐 हिंदी" if language == "HI" else "🌐 English"
    subtitle = (
        f'<p>Analysing: <b style="color:#10B981;">{sop_title}</b></p>'
        if sop_title
        else '<p>Upload an SOP below to begin &nbsp;👇</p>'
    )
    st.markdown(
        f"""<div class="app-header">
          <h1>🧠 SOP Training Engine</h1>
          {subtitle}
        </div>""",
        unsafe_allow_html=True,
    )


def render_summary_section(data: dict):
    """Render the Smart Summary tab content."""
    st.markdown(
        f"""<div class="glass-card">
          <h3 style="color:#7C3AED; margin-top:0;">🎯 Objective</h3>
          <p style="color:#D1D5DB; font-size:0.97rem; line-height:1.65;">{data.get('objective','')}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Roles
    roles = data.get("roles_involved", [])
    if roles:
        roles_html = "".join(
            f'<span class="skill-badge">{r}</span>' for r in roles
        )
        st.markdown(
            f'<div style="margin-bottom:1.2rem;"><b style="color:#9CA3AF;">👥 Roles Involved</b><br/><div style="margin-top:0.5rem;">{roles_html}</div></div>',
            unsafe_allow_html=True,
        )

    # Summary bullets
    st.markdown('<b style="color:#9CA3AF;">📋 Key Takeaways</b>', unsafe_allow_html=True)
    for point in data.get("summary_points", []):
        st.markdown(
            f'<div class="summary-point">→ {point}</div>',
            unsafe_allow_html=True,
        )

    # Time estimate
    est = data.get("estimated_training_time", "")
    if est:
        st.markdown(
            f'<p style="color:#6B7280; font-size:0.85rem; margin-top:0.5rem;">⏱ Estimated training time: <b style="color:#10B981;">{est}</b></p>',
            unsafe_allow_html=True,
        )


def render_training_steps(data: dict, audio_map: dict = None):
    """Render the Training Module tab with step cards, mistakes, tips, and optional audio."""
    for step in data.get("training_steps", []):
        num = step.get("step", "")
        title = step.get("title", "")
        content = step.get("content", "")
        mistakes = step.get("common_mistakes", [])
        tips = step.get("pro_tips", [])

        mistakes_html = ""
        if mistakes:
            tags = "".join(f'<span class="mistake-tag">⚠️ {m}</span>' for m in mistakes)
            mistakes_html = f'<div style="margin-top:0.75rem;"><small style="color:#9CA3AF;">Common Mistakes:</small><br/>{tags}</div>'

        tips_html = ""
        if tips:
            tags = "".join(f'<span class="tip-tag">💡 {t}</span>' for t in tips)
            tips_html = f'<div style="margin-top:0.5rem;"><small style="color:#9CA3AF;">Pro Tips:</small><br/>{tags}</div>'

        st.markdown(
            f"""<div class="step-card">
              <div style="display:flex;align-items:center;">
                <span class="step-number">{num}</span>
                <span class="step-title">{title}</span>
              </div>
              <div class="step-content">{content}</div>
              {mistakes_html}
              {tips_html}
            </div>""",
            unsafe_allow_html=True,
        )

        # Audio button if available
        if audio_map and num in audio_map and audio_map[num]:
            st.audio(audio_map[num], format="audio/wav")


def render_skills_section(data: dict, quiz_results: dict = None):
    """Render the Skills & Readiness tab with score ring and gap analysis."""
    skills = data.get("skills_covered", [])
    if skills:
        badges = "".join(f'<span class="skill-badge">{s}</span>' for s in skills)
        st.markdown(
            f'<div class="glass-card"><b style="color:#9CA3AF;">🎓 Skills Covered</b><div style="margin-top:0.75rem;">{badges}</div></div>',
            unsafe_allow_html=True,
        )

    if quiz_results:
        score = quiz_results.get("score", 0)
        passed = quiz_results.get("passed", False)
        correct = quiz_results.get("correct", 0)
        total = quiz_results.get("total", 0)

        color = "#10B981" if passed else "#EF4444"
        circumference = 2 * 3.14159 * 54
        dash = circumference * score / 100

        st.markdown(
            f"""<div class="glass-card" style="text-align:center;">
              <b style="color:#9CA3AF;">📊 Readiness Score</b>
              <div class="score-ring-container" style="margin-top:1rem;">
                <div class="score-ring">
                  <svg width="140" height="140" viewBox="0 0 140 140">
                    <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="12"/>
                    <circle cx="70" cy="70" r="54" fill="none" stroke="{color}" stroke-width="12"
                      stroke-dasharray="{dash:.1f} {circumference:.1f}"
                      stroke-linecap="round"/>
                  </svg>
                  <div class="score-text">{score}%</div>
                </div>
                <p style="color:{color}; font-weight:700; font-size:1.1rem; margin:0;">
                  {'✅ PASSED' if passed else '❌ NEEDS REVIEW'}
                </p>
                <p style="color:#9CA3AF; font-size:0.85rem;">
                  {correct} / {total} correct
                </p>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Gap analysis
        gaps = quiz_results.get("gap_questions", [])
        if gaps:
            st.markdown(
                f'<div class="glass-card"><b style="color:#F59E0B;">🔍 Knowledge Gaps ({len(gaps)} area{"s" if len(gaps)>1 else ""})</b>',
                unsafe_allow_html=True,
            )
            for g in gaps:
                st.markdown(
                    f"""<div style="border-left:3px solid #EF4444; padding:0.5rem 1rem; margin:0.5rem 0;
                                   background:rgba(239,68,68,0.07); border-radius:0 8px 8px 0;">
                      <p style="color:#E5E7EB; font-size:0.9rem; margin:0 0 0.3rem;"><b>Q:</b> {g['question']}</p>
                      <p style="color:#9CA3AF; font-size:0.82rem; margin:0;">
                        You answered: <span style="color:#F87171;">{g['user_answer']}</span> &nbsp;·&nbsp;
                        Correct: <span style="color:#6EE7B7;">{g['correct_answer']}</span>
                      </p>
                      <p style="color:#6B7280; font-size:0.8rem; margin-top:0.3rem;"><i>{g['explanation']}</i></p>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                '<p style="color:#10B981; font-size:0.95rem;">🎉 No knowledge gaps — perfect score!</p>',
                unsafe_allow_html=True,
            )
