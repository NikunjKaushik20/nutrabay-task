"""
styles.py — Injects premium dark-theme CSS into the Streamlit app.
"""

CUSTOM_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
/* ── Base ──────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
}
.stApp {
  background: #0E1117;
  color: #E5E7EB;
}

/* ── Hide Streamlit chrome ─────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }

/* ── App header ────────────────────────────────────────── */
.app-header {
  background: linear-gradient(135deg, #1a0a40 0%, #0E1117 60%, #0a2020 100%);
  border-radius: 16px;
  padding: 2rem 2.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(124,58,237,0.3);
  position: relative;
  overflow: hidden;
}
.app-header::before {
  content: '';
  position: absolute;
  top: -50%; left: -20%;
  width: 60%; height: 200%;
  background: radial-gradient(ellipse, rgba(124,58,237,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.app-header h1 {
  font-size: 2.1rem;
  font-weight: 800;
  background: linear-gradient(135deg, #7C3AED, #10B981);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 0.3rem 0;
}
.app-header p {
  color: #9CA3AF;
  font-size: 0.95rem;
  margin: 0;
}

/* ── Glassmorphism cards ────────────────────────────────── */
.glass-card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  transition: border-color 0.3s ease, transform 0.2s ease;
}
.glass-card:hover {
  border-color: rgba(124,58,237,0.4);
  transform: translateY(-2px);
}

/* ── Step card ──────────────────────────────────────────── */
.step-card {
  background: rgba(124,58,237,0.07);
  border: 1px solid rgba(124,58,237,0.2);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  transition: all 0.25s ease;
}
.step-card:hover {
  background: rgba(124,58,237,0.12);
  border-color: rgba(124,58,237,0.5);
}
.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.2rem; height: 2.2rem;
  background: linear-gradient(135deg, #7C3AED, #5B21B6);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.95rem;
  margin-right: 0.75rem;
  flex-shrink: 0;
}
.step-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: #E5E7EB;
}
.step-content {
  color: #9CA3AF;
  font-size: 0.92rem;
  line-height: 1.65;
  margin-top: 0.6rem;
}
.mistake-tag {
  background: rgba(245,158,11,0.12);
  color: #FCD34D;
  border: 1px solid rgba(245,158,11,0.25);
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
  margin: 0.2rem;
  display: inline-block;
}
.tip-tag {
  background: rgba(16,185,129,0.1);
  color: #6EE7B7;
  border: 1px solid rgba(16,185,129,0.25);
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
  margin: 0.2rem;
  display: inline-block;
}

/* ── Summary bullets ───────────────────────────────────── */
.summary-point {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.75rem 1rem;
  border-left: 3px solid #7C3AED;
  margin-bottom: 0.6rem;
  background: rgba(124,58,237,0.05);
  border-radius: 0 8px 8px 0;
  color: #D1D5DB;
  font-size: 0.93rem;
  line-height: 1.55;
}

/* ── Skill badge ────────────────────────────────────────── */
.skill-badge {
  display: inline-block;
  background: rgba(124,58,237,0.15);
  color: #A78BFA;
  border: 1px solid rgba(124,58,237,0.35);
  border-radius: 999px;
  padding: 0.35rem 1rem;
  margin: 0.25rem;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
}
.skill-badge:hover {
  background: rgba(124,58,237,0.3);
  color: #DDD6FE;
}

/* ── Quiz ────────────────────────────────────────────────── */
.quiz-question {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
}
.quiz-question h4 {
  color: #E5E7EB;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.75rem 0;
}

/* ── Scenario cards ──────────────────────────────────────── */
.scenario-card {
  background: rgba(124,58,237,0.06);
  border: 1px solid rgba(124,58,237,0.18);
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 0.75rem;
  transition: all 0.25s ease;
}
.scenario-card:hover {
  background: rgba(124,58,237,0.1);
  border-color: rgba(124,58,237,0.4);
  transform: translateY(-1px);
}

/* ── Score ring ─────────────────────────────────────────── */
.score-ring-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}
.score-ring {
  position: relative;
  width: 140px;
  height: 140px;
}
.score-ring svg {
  transform: rotate(-90deg);
}
.score-text {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  font-size: 1.6rem;
  font-weight: 800;
  color: #E5E7EB;
}

/* ── Streamlit overrides ────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  padding: 0.3rem;
  gap: 0.25rem;
  border: 1px solid rgba(255,255,255,0.07);
}
.stTabs [data-baseweb="tab"] {
  border-radius: 7px;
  color: #9CA3AF !important;
  font-weight: 500;
  padding: 0.5rem 1rem;
  transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(124,58,237,0.5), rgba(124,58,237,0.3)) !important;
  color: #E5E7EB !important;
}
.stButton > button {
  background: linear-gradient(135deg, #7C3AED, #5B21B6);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  padding: 0.6rem 1.5rem;
  transition: all 0.25s ease;
  font-family: 'Inter', sans-serif;
}
.stButton > button:hover {
  background: linear-gradient(135deg, #6D28D9, #4C1D95);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(124,58,237,0.4);
}
.stFileUploader {
  border: 2px dashed rgba(124,58,237,0.4) !important;
  border-radius: 12px;
  background: rgba(124,58,237,0.05);
}
.stRadio > div { gap: 0.4rem; }
.stRadio label {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  color: #D1D5DB;
  transition: all 0.2s;
  cursor: pointer;
}
.stRadio label:hover {
  border-color: rgba(124,58,237,0.5);
  background: rgba(124,58,237,0.08);
}
div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3 {
  color: #E5E7EB;
}
.st-emotion-cache-1629p8f h1 { color: #7C3AED; }
.stAlert { border-radius: 10px; }
.stSuccess { background: rgba(16,185,129,0.12) !important; border-color: rgba(16,185,129,0.3) !important; }
.stError { background: rgba(239,68,68,0.12) !important; }
.stInfo { background: rgba(124,58,237,0.1) !important; border-color: rgba(124,58,237,0.3) !important; }
</style>
"""


def inject_css():
    """Call this once at the top of app.py to apply the design system."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
