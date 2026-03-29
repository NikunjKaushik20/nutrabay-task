# 🤖 AI-Powered SOP Training Automation System

**Nutrabay Internal Ops Tool — Powered by GPT-4o-mini + FastAPI**  
*Built by Nikunj Kaushik | Nutrabay AI Automation Intern Submission*

---

## 🚨 The Problem

Every time Nutrabay launches a new warehouse process, supplier protocol, or compliance SOP, the ops team faces the same bottleneck:

- Someone writes a 10-page SOP PDF
- It gets shared on WhatsApp or email
- Employees skim it once, maybe
- Mistakes happen. Audits fail. Onboarding slows down.

**Manual SOP training doesn't scale. This system does.**

---

## ✅ What This System Does

Paste any SOP into a Google Sheet → click one button → your entire training module is generated and filled in automatically:

| What you get | Detail |
|:---|:---|
| **Summary** | 5–8 bullet key takeaways |
| **Step-by-step training** | Each step with description, common mistakes, pro tips |
| **Quiz** | MCQs with verified correct answers |
| **Skills covered** | Mapped competencies |
| **Estimated training time** | Auto-calculated |
| **Certificate link** | Ready to share with employee |

No developer needed after setup. Any ops manager can run it.

---

## 🗺️ How It Works — Workflow Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    OPS PERSON'S WORKFLOW                       │
└────────────────────────────────────────────────────────────────┘

  Step 1          Step 2             Step 3            Step 4
  ────────        ────────           ────────          ────────
  Paste SOP    →  Click              API calls      →  Results
  text into       "Run               FastAPI            auto-fill
  Google Sheet    Automation"        /api/train         in Sheet
  (Column B)      button             endpoint           (D–K)

┌──────────────────────────────────────────────────────────────────────┐
│                     TECHNICAL FLOW                                   │
│                                                                      │
│  Google Sheet                                                        │
│  (Status = Pending) ──► Apps Script  ──► POST /api/train            │
│                                                ▼                     │
│                              ┌─────────────────────────────┐        │
│                              │      FastAPI Backend         │        │
│                              │  ┌──────────────────────┐   │        │
│                              │  │  SOP Preprocessor     │   │        │
│                              │  │  (heading detection,  │   │        │
│                              │  │   section segment.)   │   │        │
│                              │  └──────────┬───────────┘   │        │
│                              │             ▼                │        │
│                              │  ┌──────────────────────┐   │        │
│                              │  │  AI Engine (GPT-4o)   │   │        │
│                              │  │  Pass 1: Generate     │   │        │
│                              │  │  Pass 2: Verify Quiz  │   │        │
│                              │  └──────────┬───────────┘   │        │
│                              │             ▼                │        │
│                              │       JSON Response          │        │
│                              └─────────────┬───────────────┘        │
│                                            ▼                         │
│  Google Sheet ◄─── Apps Script writes results back to row           │
│  Status → ✅ Done                                                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Google Sheet Structure

Set up your sheet with these 11 columns:

| # | Column | Purpose | Who fills it |
|:--|:-------|:--------|:------------|
| A | **SOP Name** | Human-readable label | Ops person |
| B | **SOP Input (Text)** | Full SOP text pasted here | Ops person |
| C | **Status** | `Pending` → `⏳ Processing` → `✅ Done` / `❌ Error` | Auto |
| D | **Summary** | AI-generated key takeaways | Auto |
| E | **Training Steps** | Step-by-step training content | Auto |
| F | **Quiz** | MCQs with answers | Auto |
| G | **Skills Covered** | Competency tags | Auto |
| H | **Est. Training Time** | Minutes to complete | Auto |
| I | **Certificate Link** | Link to PDF cert or "Generate via app.py" | Auto |
| J | **Error** | Error message if API failed | Auto |
| K | **Processed At** | Timestamp | Auto |

### Example Row

| SOP Name | SOP Input | Status | Summary | ... |
|:---------|:----------|:-------|:--------|:----|
| Warehouse Receiving SOP | "1. Purpose: This SOP covers the receiving and inspection of goods from suppliers at the Nutrabay warehouse. 2. Scope: Applies to all receiving dock staff..." | Pending | *(auto-filled)* | ... |

---

## ⚙️ Setup Guide (One-Time, ~20 Minutes)

### Step 1 — Start your FastAPI backend

```bash
# In your project directory:
uvicorn api:app --host 0.0.0.0 --port 8000
```

> For production: deploy to Railway, Render, or fly.io so it's always accessible.

### Step 2 — Create the Google Sheet

1. Go to [sheets.new](https://sheets.new)
2. Rename Sheet 1 to **"SOP Automation"**
3. Open **Extensions → Apps Script**
4. Paste the code from `automation/google_apps_script.js`
5. Update line 14: `const API_ENDPOINT = "https://your-server.com/api/train";`
6. Click **Save**
7. Run `setupSheetHeaders` once (from the Apps Script editor) to add column headers

### Step 3 — Run it

1. Go back to your Sheet
2. Refresh — a new menu **"🤖 SOP Automation"** appears
3. Paste an SOP into Column B, type `Pending` in Column C
4. Click **🤖 SOP Automation → ▶ Run Automation**
5. Watch the row fill in automatically

---

## 🔁 Trigger Options

| Mode | How | Use Case |
|:-----|:----|:---------|
| **Manual button** | Click "Run Automation" in menu | On-demand, most common |
| **onEdit auto-trigger** | Set Status = "Pending" in any row | Instant, per-row processing |
| **15-min time trigger** | Click "Enable Auto-Trigger" | Batch processing mode |

---

## 💡 API Response Format

The `/api/train` endpoint returns clean JSON — no changes needed to the backend:

```json
{
  "title": "Warehouse Goods Receiving SOP",
  "objective": "Ensure all incoming goods are inspected and logged within 2 hours of arrival.",
  "summary_points": [
    "Verify purchase order before accepting delivery",
    "Inspect for physical damage before signing",
    "Log quantity discrepancies within 30 minutes"
  ],
  "training_steps": [
    {
      "title": "Receive Delivery Note",
      "description": "Cross-check supplier delivery note against PO number in the system.",
      "common_mistake": "Accepting delivery without PO verification",
      "pro_tip": "Keep a printed PO copy at the dock station for quick reference"
    }
  ],
  "quiz": [
    {
      "question": "What should you do before signing the delivery receipt?",
      "options": ["Sign immediately", "Inspect all items for damage", "Call the supplier", "File the paperwork"],
      "answer": "Inspect all items for damage",
      "explanation": "Per SOP Section 3.2, physical inspection must precede any signatures."
    }
  ],
  "skills_covered": ["Inventory Management", "Quality Control", "Documentation"],
  "estimated_training_time": "25 minutes",
  "scenarios": []
}
```

---

## 🪄 Bonus Features

### Slack Notification (When Training is Ready)

Add this to `google_apps_script.js` inside `runAutomation()` after a successful row:

```javascript
// At top of file:
const SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL";

// After writeResultToSheet_():
notifySlack_(sopName, data.estimated_training_time);

// New function:
function notifySlack_(sopName, trainingTime) {
  const msg = {
    text: `✅ *SOP Training Ready*\n*SOP:* ${sopName}\n*Est. Time:* ${trainingTime}\n_Training content has been generated and is ready for review._`
  };
  UrlFetchApp.fetch(SLACK_WEBHOOK, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(msg),
  });
}
```

### Zapier / Make Alternative

| Tool | How | Best For |
|:-----|:----|:---------|
| **Zapier** | Google Sheets "New Row" → Webhooks POST → update row | Non-technical teams, no script setup |
| **Make (ex-Integromat)** | Google Sheets → HTTP Module → Google Sheets | More control, free tier available |
| **n8n (self-hosted)** | Full workflow builder with HTTP nodes | Developers who want full control |

> Recommendation: Use **Apps Script** (free, no third-party dependency).  
> Fall back to **Make** if you want a visual workflow diagram for stakeholders.

### Scaling Ideas

1. **Column B as Drive Link** — extend the script to fetch text from a Google Drive `.txt` or Doc link
2. **Multi-language** — call Sarvam AI after `/api/train` to translate output into Hindi
3. **Email delivery** — use `GmailApp.sendEmail()` to mail the training module to the employee
4. **Auto-share Doc** — use `DocumentApp` to write the training content into a Google Doc and share it

---

## 🚀 Quick Start (Full System)

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# → Add OPENAI_API_KEY

# 3. Run the Streamlit UI
streamlit run app.py

# 4. (For Google Sheets integration) Run the API
uvicorn api:app --host 0.0.0.0 --port 8000
```

---

## 🗃️ Project Structure

```
nutrabay/
├── app.py                         # Streamlit dashboard (7-tab UI)
├── api.py                         # FastAPI REST endpoint (/api/train)
├── requirements.txt
├── .env.example
│
├── automation/
│   └── google_apps_script.js      # ← NEW: Google Sheets automation script
│
├── core/
│   ├── ai_engine.py               # GPT-4o-mini two-pass pipeline
│   ├── scenario_engine.py         # Workplace scenario generator
│   ├── sop_preprocessor.py        # NLP preprocessing
│   ├── pdf_parser.py              # PDF text extraction
│   ├── slides_generator.py        # Reveal.js slide builder
│   ├── certificate.py             # PDF certificate generator
│   └── sarvam.py                  # Hindi translation + TTS
│
├── ui/
│   ├── styles.py                  # Design system (CSS)
│   └── components.py              # Reusable UI components
│
└── tests/
    ├── test_ai_engine.py
    ├── test_sop_preprocessor.py
    ├── test_pdf_parser.py
    └── test_certificate.py
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|:------|:-----------|
| **Automation** | Google Apps Script (GAS) — zero infra, runs in Google Cloud |
| **Trigger** | Manual button / onEdit / time-based (15 min) |
| **API** | FastAPI + Uvicorn |
| **AI** | OpenAI GPT-4o-mini (two-pass: generate → verify) |
| **UI** | Streamlit (custom dark theme, glassmorphism) |
| **Translation** | Sarvam AI (Hindi TTS) |
| **Certificates** | ReportLab PDF |
| **Slides** | Reveal.js |
| **Testing** | pytest |

---

## 📊 Why This Matters for Companies

| Problem | This System's Answer |
|:--------|:---------------------|
| SOP training takes days to design | Generated in < 2 minutes |
| Content goes stale, no one updates it | Re-run automation on updated SOP |
| No way to verify employee understood | Quiz + Scenario Simulator built-in |
| Training not tracked | Google Sheet is the live dashboard |
| HR/L&D team bottleneck | Ops manager runs it independently |
| Expensive LMS tools | This runs on free Google Sheets + cheap API calls |

---