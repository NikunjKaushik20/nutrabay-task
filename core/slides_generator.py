"""
slides_generator.py — Auto-generate a reveal.js HTML slide deck from AI training content.
"""

import html as html_module


def generate_slides_html(data: dict) -> str:
    """
    Build a self-contained reveal.js HTML slide deck from the AI training content.

    Args:
        data: dict from ai_engine.generate_training_content()

    Returns:
        Complete HTML string (CDN-linked reveal.js, no install needed).
    """
    title = html_module.escape(data.get("title", "Training Module"))
    objective = html_module.escape(data.get("objective", ""))
    summary_points = data.get("summary_points", [])
    training_steps = data.get("training_steps", [])
    skills = data.get("skills_covered", [])
    est_time = html_module.escape(data.get("estimated_training_time", ""))

    slides_html = []

    # ── Slide 1: Title ────────────────────────────────────────────────────────
    slides_html.append(f"""
    <section data-background-gradient="linear-gradient(135deg, #0E1117 0%, #1a1040 100%)">
      <h1 style="color:#7C3AED; font-size:2em; margin-bottom:0.3em;">{title}</h1>
      <p style="color:#10B981; font-size:1.1em;">AI-Powered Training Module</p>
      <p style="color:#9CA3AF; font-size:0.8em; margin-top:1.5em;">
        ⏱ Estimated time: {est_time if est_time else 'Self-paced'}
      </p>
      <p style="color:#6B7280; font-size:0.75em;">Powered by Nutrabay SOP Training Engine</p>
    </section>
    """)

    # ── Slide 2: Objective ────────────────────────────────────────────────────
    if objective:
        slides_html.append(f"""
    <section data-background="#0E1117">
      <h2 style="color:#7C3AED;">🎯 Objective</h2>
      <p style="color:#E5E7EB; font-size:1.1em; line-height:1.6; max-width:800px; margin:auto;">
        {objective}
      </p>
    </section>
        """)

    # ── Slide 3: Key Takeaways ────────────────────────────────────────────────
    if summary_points:
        bullets = "".join(
            f'<li style="margin-bottom:0.5em;">{html_module.escape(p)}</li>'
            for p in summary_points
        )
        slides_html.append(f"""
    <section data-background="#0E1117">
      <h2 style="color:#10B981;">📋 Key Takeaways</h2>
      <ul style="color:#D1D5DB; font-size:0.9em; line-height:1.7; text-align:left; max-width:750px; margin:auto;">
        {bullets}
      </ul>
    </section>
        """)

    # ── Training Step Slides ──────────────────────────────────────────────────
    for step in training_steps:
        step_num = step.get("step", "")
        step_title = html_module.escape(step.get("title", ""))
        step_content = html_module.escape(step.get("content", ""))
        mistakes = step.get("common_mistakes", [])
        tips = step.get("pro_tips", [])

        mistakes_html = ""
        if mistakes:
            m_items = "".join(
                f'<li>⚠️ {html_module.escape(m)}</li>' for m in mistakes
            )
            mistakes_html = f"""
            <div style="margin-top:1em;">
              <p style="color:#F59E0B; font-size:0.8em; margin-bottom:0.3em;"><b>Common Mistakes</b></p>
              <ul style="color:#FCD34D; font-size:0.8em; text-align:left;">{m_items}</ul>
            </div>"""

        tips_html = ""
        if tips:
            t_items = "".join(
                f'<li>💡 {html_module.escape(t)}</li>' for t in tips
            )
            tips_html = f"""
            <div style="margin-top:0.5em;">
              <p style="color:#10B981; font-size:0.8em; margin-bottom:0.3em;"><b>Pro Tips</b></p>
              <ul style="color:#6EE7B7; font-size:0.8em; text-align:left;">{t_items}</ul>
            </div>"""

        slides_html.append(f"""
    <section data-background="#0E1117">
      <div style="display:flex; align-items:center; gap:0.5em; justify-content:center; margin-bottom:0.5em;">
        <span style="background:#7C3AED; color:white; border-radius:50%; width:2.2em; height:2.2em;
                     display:inline-flex; align-items:center; justify-content:center;
                     font-weight:bold; font-size:1em; flex-shrink:0;">
          {step_num}
        </span>
        <h2 style="color:#E5E7EB; margin:0; font-size:1.3em;">{step_title}</h2>
      </div>
      <p style="color:#D1D5DB; font-size:0.92em; line-height:1.6; max-width:780px; margin:0 auto 0.5em;">
        {step_content}
      </p>
      {mistakes_html}
      {tips_html}
    </section>
        """)

    # ── Skills Covered ────────────────────────────────────────────────────────
    if skills:
        skill_badges = "".join(
            f'<span style="display:inline-block; background:#1e1040; color:#7C3AED; '
            f'border:1px solid #7C3AED; border-radius:999px; padding:0.3em 1em; '
            f'margin:0.3em; font-size:0.85em;">{html_module.escape(s)}</span>'
            for s in skills
        )
        slides_html.append(f"""
    <section data-background="#0E1117">
      <h2 style="color:#7C3AED;">🎓 Skills You've Learned</h2>
      <div style="margin-top:1em;">{skill_badges}</div>
    </section>
        """)

    # ── Final Slide ──────────────────────────────────────────────────────────
    slides_html.append("""
    <section data-background-gradient="linear-gradient(135deg, #0E1117 0%, #0a2818 100%)">
      <h2 style="color:#10B981; font-size:2em;">✅ Training Complete!</h2>
      <p style="color:#E5E7EB; font-size:1.1em;">Head to the Quiz tab to test your knowledge.</p>
      <p style="color:#6B7280; font-size:0.8em; margin-top:2em;">Nutrabay SOP Training Engine</p>
    </section>
    """)

    all_slides = "\n".join(slides_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Training Slides</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />
  <style>
    body {{ font-family: 'Inter', sans-serif !important; }}
    .reveal {{ font-family: 'Inter', sans-serif !important; }}
    .reveal h1, .reveal h2, .reveal h3 {{ font-family: 'Inter', sans-serif !important; }}
    .reveal .slides {{ text-align: center; }}
    .reveal ul {{ list-style: none; padding: 0; }}
    .reveal ul li::before {{ content: "→ "; color: #7C3AED; }}
  </style>
</head>
<body>
  <div class="reveal">
    <div class="slides">
      {all_slides}
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script>
    Reveal.initialize({{
      hash: true,
      transition: 'slide',
      transitionSpeed: 'default',
      backgroundTransition: 'fade',
      controls: true,
      progress: true,
      center: true,
      slideNumber: true,
    }});
  </script>
</body>
</html>"""
