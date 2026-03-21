"""
scenario_engine.py — Generate interactive workplace scenarios from SOP training content.

Uses GPT-4o-mini to create realistic "what would you do?" decision points
that test practical application of SOP knowledge, not just memorisation.
"""

import json
import logging
from typing import Optional

from core.ai_engine import _call_with_retry

logger = logging.getLogger(__name__)


SCENARIO_SYSTEM_PROMPT = """You are a corporate training scenario designer.
Given structured SOP training content, create realistic workplace scenarios
that test whether an employee can APPLY the procedure in messy, real-world situations.

Return a JSON object with this exact structure:
{
  "scenarios": [
    {
      "id": 1,
      "situation": "string — 2–4 sentence scenario description. Include realistic pressure, ambiguity, or time constraints.",
      "sop_step_reference": "string — which training step this tests, e.g. 'Step 2: Physical Count'",
      "choices": [
        {
          "label": "A",
          "text": "string — a plausible action the employee could take",
          "is_correct": false,
          "feedback": "string — explain why this choice is right or wrong, referencing the SOP"
        }
      ]
    }
  ]
}

Rules:
- Generate exactly 3 scenarios.
- Each scenario must have exactly 4 choices (A, B, C, D).
- Exactly one choice per scenario must be correct (is_correct: true).
- Scenarios should feel realistic — include time pressure, colleague opinions, shortcuts.
- Feedback must cite the specific SOP step/rule that applies.
- Use simple, direct language suitable for operations/warehouse staff."""


SCENARIO_USER_TEMPLATE = """Here is the SOP training content. Create 3 interactive scenarios:

Title: {title}
Objective: {objective}

Training Steps:
{steps_text}

Key Points:
{summary_text}

Return only the JSON object. No markdown, no explanations."""


def generate_scenarios(data: dict, progress_callback=None) -> list[dict]:
    """
    Generate interactive workplace scenarios from training content.

    Args:
        data: dict from ai_engine.generate_training_content()
        progress_callback: Optional callable(step_name, step_num, total)

    Returns:
        List of scenario dicts with situation, choices, and feedback.
    """
    if progress_callback:
        progress_callback("Generating scenarios", 1, 2)

    # Build context from training data
    steps_text = "\n".join(
        f"Step {s.get('step', i+1)}: {s.get('title', '')} — {s.get('content', '')}"
        for i, s in enumerate(data.get("training_steps", []))
    )
    summary_text = "\n".join(
        f"- {pt}" for pt in data.get("summary_points", [])
    )

    prompt = SCENARIO_USER_TEMPLATE.format(
        title=data.get("title", ""),
        objective=data.get("objective", ""),
        steps_text=steps_text,
        summary_text=summary_text,
    )

    try:
        result = _call_with_retry(
            system_prompt=SCENARIO_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=3000,
            max_retries=2,
        )

        scenarios = result.get("scenarios", [])
        if not scenarios:
            logger.warning("GPT returned empty scenarios list")
            return []

        # Basic validation
        valid_scenarios = []
        for sc in scenarios:
            if (
                isinstance(sc, dict)
                and sc.get("situation")
                and isinstance(sc.get("choices"), list)
                and len(sc["choices"]) >= 3
            ):
                valid_scenarios.append(sc)

        if progress_callback:
            progress_callback("Done", 2, 2)

        return valid_scenarios

    except Exception as e:
        logger.error(f"Scenario generation failed: {e}")
        return []


def get_sample_scenarios() -> list[dict]:
    """Hardcoded sample scenarios for demo mode (no API call)."""
    return [
        {
            "id": 1,
            "situation": (
                "A delivery truck arrives at 4:45 PM, 15 minutes before your shift ends. "
                "The driver is irritated and says he has two more stops. He pushes the packing "
                "slip toward you and asks you to sign quickly so he can leave. You haven't "
                "opened the Purchase Order in the WMS yet."
            ),
            "sop_step_reference": "Step 1: Verify Purchase Order",
            "choices": [
                {
                    "label": "A",
                    "text": "Sign the packing slip to help the driver — you can check the PO later tonight.",
                    "is_correct": False,
                    "feedback": "❌ The SOP requires PO verification BEFORE accepting any delivery. Signing without verification could mean accepting wrong goods, wrong quantities, or items from an unapproved vendor.",
                },
                {
                    "label": "B",
                    "text": "Tell the driver to wait while you pull up the PO in the WMS and verify the delivery details.",
                    "is_correct": True,
                    "feedback": "✅ Correct. Per Step 1, you must always retrieve and verify the Purchase Order before unloading begins, regardless of time pressure. The PO must be open on your scanner before the truck is unloaded.",
                },
                {
                    "label": "C",
                    "text": "Ask a colleague to sign for you while you find the PO.",
                    "is_correct": False,
                    "feedback": "❌ Having someone else sign without PO verification doesn't solve the problem — it just transfers the risk. The procedure requires verification first, not delegation of shortcuts.",
                },
                {
                    "label": "D",
                    "text": "Refuse the delivery entirely and tell the driver to come back tomorrow.",
                    "is_correct": False,
                    "feedback": "❌ There's no need to refuse the delivery. The correct action is to verify the PO first, which takes only a few minutes. Refusing creates unnecessary delays in the supply chain.",
                },
            ],
        },
        {
            "id": 2,
            "situation": (
                "You're doing a physical count on a large shipment of 450 cartons. "
                "After counting 380 cartons, your supervisor walks over and says the warehouse is "
                "backed up — he asks you to just sign the packing slip for 450 and finish the count "
                "'when you get a chance'. The packing slip says 450 cartons."
            ),
            "sop_step_reference": "Step 2: Physical Count & Packing Slip Match",
            "choices": [
                {
                    "label": "A",
                    "text": "Follow the supervisor's instruction — he outranks you, and the warehouse is busy.",
                    "is_correct": False,
                    "feedback": "❌ The SOP is clear: never sign the packing slip before the count is complete, regardless of who asks. Signing for 450 when you've only counted 380 creates an inventory discrepancy of unknown magnitude.",
                },
                {
                    "label": "B",
                    "text": "Complete the count before signing. Explain to the supervisor that the SOP prohibits signing before the count is finished.",
                    "is_correct": True,
                    "feedback": "✅ Correct. Per Step 2, physical count must match the packing slip, and you must never sign before the count is complete. Discrepancies must be recorded on the Discrepancy Report form immediately.",
                },
                {
                    "label": "C",
                    "text": "Sign for 380 cartons instead and note the remainder as 'uncounted'.",
                    "is_correct": False,
                    "feedback": "❌ Partial signing isn't in the procedure. You need to complete the full count first. If there's a shortage, it goes on the Discrepancy Report — not as a partial sign-off.",
                },
                {
                    "label": "D",
                    "text": "Estimate the remaining cartons by multiplying pallet layers × cartons per layer.",
                    "is_correct": False,
                    "feedback": "❌ Estimation is not an acceptable substitute for actual counting. The SOP requires a physical count against the packing slip. Use a tally counter for high-unit cartons to stay accurate.",
                },
            ],
        },
        {
            "id": 3,
            "situation": (
                "During QC inspection of a supplement shipment, you notice that 3 bottles out of your "
                "30-bottle sample have slightly dented caps but the seal is intact. The nutritional labels "
                "look correct, batch numbers are present, and expiry dates are 18 months out. Your colleague "
                "says 'dented caps are fine, the product inside is okay — just put them through'."
            ),
            "sop_step_reference": "Step 3: Quality Control Inspection",
            "choices": [
                {
                    "label": "A",
                    "text": "Your colleague is right — the seal is intact, so the product is safe. Proceed to putaway.",
                    "is_correct": False,
                    "feedback": "❌ Dented packaging is considered physical damage per the QC inspection criteria. You must check inner and outer packaging for dents, leaks, and seal integrity. Dented items should be flagged even if the seal appears intact.",
                },
                {
                    "label": "B",
                    "text": "Send all 450 units to the quarantine zone since your sample showed defects.",
                    "is_correct": False,
                    "feedback": "❌ This is overly aggressive. 3 out of 30 (10%) have minor cosmetic damage. The correct approach is to quarantine the damaged units and flag them, not reject the entire shipment.",
                },
                {
                    "label": "C",
                    "text": "Quarantine the 3 dented units, flag them for vendor return, and note the finding on your QC report. Pass the remaining units.",
                    "is_correct": True,
                    "feedback": "✅ Correct. Per Step 3, products failing QC must go to the quarantine zone and be flagged for vendor return within 24 hours. The undamaged units can proceed normally through the receiving process.",
                },
                {
                    "label": "D",
                    "text": "Take a larger sample (60 bottles) to see if the defect rate is really that high before deciding.",
                    "is_correct": False,
                    "feedback": "❌ While due diligence is good, you've already found damaged items. Those damaged units need to be quarantined per SOP regardless of further sampling. You can expand the sample, but the 3 dented units must still be flagged immediately.",
                },
            ],
        },
    ]
