# 🧠 Nutrabay SOP Training Engine

**Problem 4: SOP → AI Training System**
*Submitted by Nikunj Kaushik for the Nutrabay AI Automation Intern role*

---

## 💡 The Problem

Training employees using manual SOP documents is slow, passive, and hard to measure. Employees read a PDF, forget 90% of it, and there's no way to verify they can actually *apply* the procedure on the floor.

## 🎯 My Approach

Instead of building another "PDF summariser," I built a **complete training platform** that follows the learning lifecycle:

1. **Understand** → AI generates a structured summary with key takeaways
2. **Learn** → Step-by-step training with common mistakes and pro tips
3. **Practice** → Interactive workplace scenarios (the key differentiator)
4. **Assess** → Quiz with immediate feedback and knowledge gap analysis
5. **Certify** → Downloadable PDF certificate with unique ID

> *"Reading a fire safety manual doesn't prepare you for a fire — a fire drill does."*
> The Scenario Simulator is the "fire drill" for SOPs.

---

## ✨ Features

| Feature | Description |
|:---|:---|
| **PDF & Text Input** | Upload a PDF or paste SOP text directly |
| **AI-Powered Analysis** | GPT-4o-mini generates structured training content |
| **SOP Preprocessor** | Custom NLP pipeline: heading detection, section segmentation, noise removal |
| **Two-Pass Quiz Verification** | Second AI pass validates all quiz answers for accuracy |
| **Interactive Scenario Simulator** | 3 realistic "what would you do?" workplace scenarios with SOP-referenced feedback |
| **Reveal.js Slide Deck** | Auto-generated presentation, downloadable as HTML |
| **Hindi Translation & Audio** | Sarvam AI integration for Hindi TTS narration |
| **PDF Certificate** | Downloadable training certificate with unique ID and pass/fail status |
| **REST API** | `POST /api/train` endpoint for automation/integration |

---

## 🏗️ Architecture

```
SOP Input (PDF / Text)
      │
      ▼
┌─────────────────┐
│  PDF Parser      │ ← pdfplumber extraction
│  (core/)         │
└────────┬────────┘
         ▼
┌─────────────────┐
│  SOP Preprocessor│ ← heading detection, section segmentation, noise removal
│  (core/)         │
└────────┬────────┘
         ▼
┌─────────────────┐
│  AI Engine       │ ← GPT-4o-mini (Pass 1: Generate → Pass 2: Verify Quiz)
│  (core/)         │
└────────┬────────┘
         ▼
    ┌────┴────┐
    │         │
    ▼         ▼
Slides    Scenarios ← GPT-4o-mini generates workplace scenarios
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│  Streamlit UI    │ ← 7-tab dashboard with premium dark theme
│  (app.py + ui/)  │
└─────────────────┘
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
cp .env.example .env
# Add your OPENAI_API_KEY (required)
# Add your SARVAM_API_KEY (optional — for Hindi translation)
```

### 3. Run the app
```bash
streamlit run app.py --server.headless true --server.port 8501
```

### 4. (Optional) Run the REST API
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

```bash
# Test with curl:
curl -X POST http://localhost:8000/api/train \
  -H "Content-Type: application/json" \
  -d '{"sop_text": "1. Purpose: This SOP covers the receiving process..."}'
```

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

Tests cover: AI engine validation, SOP preprocessor, PDF parser, and certificate generation. All tests run **without API keys** (test local logic only).

---

## 📁 Project Structure

```
nutrabay/
├── app.py                    # Main Streamlit dashboard (7 tabs)
├── api.py                    # FastAPI REST endpoint
├── requirements.txt
├── .env.example
├── core/
│   ├── ai_engine.py          # GPT-4o-mini two-pass pipeline
│   ├── scenario_engine.py    # Interactive scenario generator
│   ├── sop_preprocessor.py   # NLP preprocessing (heading detection, segmentation)
│   ├── pdf_parser.py         # PDF text extraction
│   ├── slides_generator.py   # Reveal.js slide deck builder
│   ├── certificate.py        # PDF certificate generator
│   └── sarvam.py             # Sarvam AI (Hindi translation + TTS)
├── ui/
│   ├── styles.py             # Design system (CSS)
│   └── components.py         # Reusable UI components
└── tests/
    ├── test_ai_engine.py
    ├── test_sop_preprocessor.py
    ├── test_pdf_parser.py
    └── test_certificate.py
```

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit with custom CSS design system (Inter font, glassmorphism, dark theme)
- **AI**: OpenAI GPT-4o-mini (structured JSON output, two-pass pipeline)
- **Translation**: Sarvam AI (Mayura v1 for translation, Bulbul v1 for TTS)
- **Slides**: Reveal.js (CDN-linked, self-contained HTML)
- **Certificate**: ReportLab (PDF generation)
- **API**: FastAPI + Uvicorn
- **Testing**: pytest

---

## 🤔 Design Decisions

1. **Two-pass quiz verification** — LLMs can generate wrong quiz answers. A second GPT call verifies each answer against the SOP, catching errors before they reach the employee.

2. **SOP preprocessor (not just raw text → GPT)** — Real SOPs have page markers, inconsistent formatting, and noise. The preprocessor does heading detection, section segmentation, and whitespace normalisation *before* sending to GPT. This produces better training content.

3. **Scenario Simulator** — Quizzes test memorisation. Scenarios test application. In a real warehouse, you face ambiguity, time pressure, and shortcuts from colleagues. The scenarios recreate that environment.

4. **Sample data mode** — The app includes hardcoded sample output so evaluators can test the full UI without needing an API key.

---

## 📊 Scoring Rubric Coverage

| Criteria | How This Project Addresses It |
|:---|:---|
| **Practical Execution (30%)** | Working end-to-end system. Upload → train → quiz → certify. REST API for automation. |
| **Output Quality (25%)** | Two-pass verified quiz, interactive scenarios, professional slide deck |
| **Problem Understanding (20%)** | Goes beyond "generate summary" to address the real problem: employees don't retain passive training |
| **Simplicity & Clarity (15%)** | Clean module separation, documented code, comprehensive tests |
| **Creativity (10%)** | Scenario Simulator, Hindi TTS audio, PDF certificates, reveal.js slides |
