"""
ai_engine.py — GPT-4o-mini powered SOP → Training Content generator.

Two-pass pipeline:
  Pass 1: Generate structured training content (summary, steps, quiz, skills)
  Pass 2: Verify quiz answers are correct and fix any errors

Includes retry logic, deep validation, and smart SOP chunking.
"""

import json
import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            )
        _client = OpenAI(api_key=api_key)
    return _client


# ── Prompts ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert corporate trainer and instructional designer.
Your job is to transform raw SOP (Standard Operating Procedure) documents into
structured employee training content.

Always respond with a single valid JSON object — no markdown fences, no extra text.
The JSON must strictly follow this schema:

{
  "title": "string — concise title of the SOP",
  "objective": "string — 1–2 sentence purpose of this SOP",
  "roles_involved": ["string", ...],
  "summary_points": ["string", ...],  // 5–8 key takeaways
  "training_steps": [
    {
      "step": 1,
      "title": "string",
      "content": "string — 2–4 sentence explanation",
      "common_mistakes": ["string", ...],  // 1–3 mistakes
      "pro_tips": ["string", ...]           // 1–2 tips
    }
  ],
  "quiz": [
    {
      "question": "string",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",  // single letter
      "explanation": "string — why this is correct"
    }
  ],  // exactly 5 questions
  "skills_covered": ["string", ...],  // 3–6 skills
  "estimated_training_time": "string — e.g., '20 minutes'"
}

Be practical, clear, and concise. Use simple language suitable for warehouse/ops staff."""


USER_PROMPT_TEMPLATE = """Here is the SOP document text, pre-processed into sections.
Transform it into structured training content:

---
{sop_text}
---

Return only the JSON object. No explanations, no markdown."""


QUIZ_VERIFY_PROMPT = """You are a quality assurance reviewer for training quiz questions.
Below is a quiz generated from an SOP training module. For each question, verify:

1. The marked answer is actually correct based on the question and options.
2. The explanation logically supports the answer.
3. All 4 options are distinct and plausible.

If you find ANY errors, return a corrected version. If all questions are correct,
return the quiz unchanged.

IMPORTANT: Return ONLY a JSON array of quiz question objects. No markdown, no extra text.

Quiz to verify:
{quiz_json}

Context from the SOP (for reference):
{sop_context}"""


# ── Main Pipeline ──────────────────────────────────────────────────────────────


def generate_training_content(sop_text: str, progress_callback=None) -> dict:
    """
    Two-pass pipeline: Generate training content, then verify quiz accuracy.

    Args:
        sop_text: Pre-processed SOP text (ideally from sop_preprocessor.format_for_prompt).
        progress_callback: Optional callable(step_name, step_number, total_steps)
                           for UI progress updates.

    Returns:
        dict with title, objective, roles, summary, steps, quiz, skills, etc.

    Raises:
        ValueError: If the AI response cannot be parsed or validated.
        EnvironmentError: If OPENAI_API_KEY is missing.
    """
    total_steps = 3

    # ── Pass 1: Generate content ──────────────────────────────────────────────
    if progress_callback:
        progress_callback("Generating training content", 1, total_steps)

    data = _call_with_retry(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT_TEMPLATE.format(sop_text=sop_text),
        max_tokens=4000,
    )

    _validate_structure(data)

    # ── Pass 2: Verify quiz ───────────────────────────────────────────────────
    if progress_callback:
        progress_callback("Verifying quiz answers", 2, total_steps)

    quiz = data.get("quiz", [])
    if quiz:
        verified_quiz = _verify_quiz(quiz, sop_text)
        if verified_quiz:
            data["quiz"] = verified_quiz

    if progress_callback:
        progress_callback("Finalising", 3, total_steps)

    return data


def _call_with_retry(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    max_retries: int = 3,
) -> dict:
    """Call OpenAI with exponential backoff retry on failure."""
    client = _get_client()

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )

            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            return data

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}: Invalid JSON from GPT: {e}")
            if attempt == max_retries - 1:
                raise ValueError(
                    f"AI returned invalid JSON after {max_retries} attempts: {e}"
                )
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}: API error: {e}")
            if attempt == max_retries - 1:
                raise

        # Exponential backoff: 1s, 2s, 4s
        time.sleep(2 ** attempt)

    raise ValueError("Exhausted all retry attempts")  # shouldn't reach here


def _verify_quiz(quiz: list[dict], sop_context: str) -> Optional[list[dict]]:
    """
    Second GPT pass: verify each quiz answer is correct.
    Returns corrected quiz list, or None if verification fails.
    """
    try:
        quiz_json = json.dumps(quiz, indent=2)
        # Use only first 3000 chars of SOP for context (saves tokens)
        sop_short = sop_context[:3000]

        prompt = QUIZ_VERIFY_PROMPT.format(
            quiz_json=quiz_json,
            sop_context=sop_short,
        )

        data = _call_with_retry(
            system_prompt="You are a quiz QA reviewer. Return only a JSON object with a 'quiz' key containing the corrected quiz array.",
            user_prompt=prompt,
            max_tokens=2000,
            max_retries=2,
        )

        # The response might be {"quiz": [...]} or just [...]
        if isinstance(data, dict) and "quiz" in data:
            verified = data["quiz"]
        elif isinstance(data, list):
            verified = data
        else:
            logger.warning("Quiz verification returned unexpected format, keeping original")
            return None

        # Basic sanity check
        if len(verified) >= 3 and all(
            isinstance(q, dict) and "question" in q and "answer" in q
            for q in verified
        ):
            return verified

        logger.warning("Verified quiz failed sanity check, keeping original")
        return None

    except Exception as e:
        logger.warning(f"Quiz verification failed, keeping original: {e}")
        return None


def _validate_structure(data: dict) -> None:
    """Deep validation — ensure structure and content quality."""
    required_keys = [
        "title",
        "objective",
        "summary_points",
        "training_steps",
        "quiz",
        "skills_covered",
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"AI response missing required keys: {missing}")

    # Validate training_steps
    steps = data.get("training_steps")
    if not isinstance(steps, list) or len(steps) == 0:
        raise ValueError("training_steps must be a non-empty list")

    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"training_steps[{i}] must be a dict")
        if not step.get("title", "").strip():
            raise ValueError(f"training_steps[{i}] has empty title")
        if not step.get("content", "").strip():
            raise ValueError(f"training_steps[{i}] has empty content")

    # Validate quiz
    quiz = data.get("quiz")
    if not isinstance(quiz, list) or len(quiz) == 0:
        raise ValueError("quiz must be a non-empty list")

    for i, q in enumerate(quiz):
        if not isinstance(q, dict):
            raise ValueError(f"quiz[{i}] must be a dict")
        if not q.get("question", "").strip():
            raise ValueError(f"quiz[{i}] has empty question")
        if not q.get("answer", "").strip():
            raise ValueError(f"quiz[{i}] has empty answer")
        options = q.get("options", [])
        if not isinstance(options, list) or len(options) < 3:
            raise ValueError(f"quiz[{i}] must have at least 3 options, got {len(options)}")
        # Verify answer letter is one of A/B/C/D
        answer = q["answer"].strip().upper()
        if answer not in ("A", "B", "C", "D"):
            raise ValueError(f"quiz[{i}] answer must be A/B/C/D, got '{answer}'")

    # Validate summary_points
    points = data.get("summary_points")
    if not isinstance(points, list) or len(points) < 3:
        raise ValueError("summary_points must have at least 3 items")


def get_sample_output() -> dict:
    """Return a realistic mock output for UI development / testing without API calls."""
    return {
        "title": "Warehouse Inbound Receiving SOP",
        "objective": "Ensure accurate and efficient receiving of goods at the warehouse dock, maintaining inventory integrity and minimising errors.",
        "roles_involved": ["Receiving Associate", "QC Inspector", "Warehouse Supervisor"],
        "is_sample": True,  # Flag for UI to show sample badge
        "summary_points": [
            "All inbound shipments must be verified against the Purchase Order (PO) before acceptance.",
            "Physical count must match the packing slip; discrepancies must be reported within 2 hours.",
            "Products must be QC-inspected for damage, expiry, and labelling before putaway.",
            "All received items are scanned into the WMS immediately after QC clearance.",
            "Rejected goods are quarantined and flagged for vendor return within 24 hours.",
            "Cold-chain products must be temperature-logged on receipt.",
        ],
        "training_steps": [
            {
                "step": 1,
                "title": "Verify Purchase Order",
                "content": "Before unloading, retrieve the Purchase Order from the WMS and cross-check it with the vendor's delivery note. Confirm supplier name, PO number, and expected item list match.",
                "common_mistakes": [
                    "Accepting delivery without locating the PO first.",
                    "Ignoring PO quantity and just accepting whatever arrives.",
                ],
                "pro_tips": [
                    "Always have the PO open on your scanner before the truck is unloaded.",
                ],
            },
            {
                "step": 2,
                "title": "Physical Count & Packing Slip Match",
                "content": "Count each SKU as it is unloaded. Compare physical count against packing slip. Any shortages or overages must be recorded on the Discrepancy Report form immediately.",
                "common_mistakes": [
                    "Skipping the count on large shipments due to time pressure.",
                    "Signing the packing slip before the count is complete.",
                ],
                "pro_tips": [
                    "Use a tally counter for high-unit cartons to stay accurate.",
                    "Photograph any damaged outer cartons before opening.",
                ],
            },
            {
                "step": 3,
                "title": "Quality Control Inspection",
                "content": "Inspect a random sample (minimum 10% of units) for physical damage, correct labelling, batch number, and expiry date. Products failing QC must go to the quarantine zone.",
                "common_mistakes": [
                    "Inspecting only the top layer of a pallet.",
                    "Not checking expiry dates on perishable items.",
                ],
                "pro_tips": [
                    "Check inner and outer packaging for dents, leaks, and seal integrity.",
                ],
            },
            {
                "step": 4,
                "title": "WMS Entry & Barcode Scan",
                "content": "After QC clearance, scan each product barcode into the WMS to officially receive it into inventory. Confirm the bin location assignment generated by the system.",
                "common_mistakes": [
                    "Scanning items before QC approval is given.",
                    "Entering quantities manually instead of scanning.",
                ],
                "pro_tips": [
                    "If a barcode won't scan, flag the item — never guess the product code.",
                ],
            },
            {
                "step": 5,
                "title": "Putaway & Documentation",
                "content": "Move QC-cleared items to the assigned bin locations. File the completed Receiving Report and Discrepancy Report (if any) in the daily folder and notify the supervisor.",
                "common_mistakes": [
                    "Putaway to wrong bin location without confirming WMS assignment.",
                ],
                "pro_tips": [
                    "Always confirm putaway in the WMS — don't just physically place the item.",
                ],
            },
        ],
        "quiz": [
            {
                "question": "What is the FIRST thing you must do before unloading a delivery?",
                "options": [
                    "A. Sign the packing slip",
                    "B. Retrieve and verify the Purchase Order",
                    "C. Begin unloading to save time",
                    "D. Notify the QC inspector",
                ],
                "answer": "B",
                "explanation": "The PO must be verified first to ensure you are receiving the correct goods from the approved vendor.",
            },
            {
                "question": "Where should a product go if it fails QC inspection?",
                "options": [
                    "A. Back on the delivery truck immediately",
                    "B. To the regular bin location",
                    "C. Quarantine zone",
                    "D. Supervisor's desk",
                ],
                "answer": "C",
                "explanation": "All QC-failed items must be isolated in the quarantine zone and flagged for vendor return within 24 hours.",
            },
            {
                "question": "When should items be scanned into the WMS?",
                "options": [
                    "A. During unloading",
                    "B. Only at end of shift",
                    "C. After QC clearance",
                    "D. Before the physical count",
                ],
                "answer": "C",
                "explanation": "WMS entry happens after QC approval to ensure only accepted goods enter inventory records.",
            },
            {
                "question": "What is the minimum sample percentage for QC inspection?",
                "options": ["A. 5%", "B. 10%", "C. 25%", "D. 50%"],
                "answer": "B",
                "explanation": "At least 10% of received units must be inspected to statistically validate the shipment quality.",
            },
            {
                "question": "A barcode refuses to scan. What should you do?",
                "options": [
                    "A. Enter the product code manually",
                    "B. Skip the item and continue",
                    "C. Flag the item and notify a supervisor",
                    "D. Use another product's barcode",
                ],
                "answer": "C",
                "explanation": "Manual entry risks incorrect product codes. Always flag and escalate so the correct item is identified.",
            },
        ],
        "skills_covered": [
            "Purchase Order verification",
            "Physical inventory counting",
            "Quality control inspection",
            "WMS data entry",
            "Documentation & reporting",
        ],
        "estimated_training_time": "25 minutes",
    }


if __name__ == "__main__":
    import sys
    from core.pdf_parser import extract_text_from_pdf
    from core.sop_preprocessor import preprocess_sop, format_for_prompt

    if len(sys.argv) < 2:
        print("Usage: python -m core.ai_engine <path_to_sop_pdf>")
        print("\nRunning with SAMPLE DATA (no API call)...")
        sample = get_sample_output()
        print(json.dumps(sample, indent=2))
        sys.exit(0)

    pdf_path = sys.argv[1]
    print(f"Processing: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(raw_text)} characters from PDF")

    print("Preprocessing SOP text...")
    preprocessed = preprocess_sop(raw_text)
    print(f"Found {preprocessed['stats']['section_count']} sections")

    prompt_text = format_for_prompt(preprocessed)
    print(f"Prompt text: {len(prompt_text)} chars")

    print("Calling GPT-4o-mini (two-pass pipeline)...")
    result = generate_training_content(prompt_text)
    print(json.dumps(result, indent=2))
