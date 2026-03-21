"""
sop_preprocessor.py — Extract structure from raw SOP text before sending to GPT.

Adds real algorithmic logic: heading detection, section segmentation,
noise removal, and structured output — so we're not just throwing a wall
of text at the LLM.
"""

import re
from typing import Optional


def preprocess_sop(raw_text: str) -> dict:
    """
    Convert raw extracted PDF text into a structured representation.

    Pipeline:
        1. Strip [Page X] markers
        2. Detect headings / section titles
        3. Segment text into {heading → body} sections
        4. Clean body text (collapse whitespace, strip noise)

    Args:
        raw_text: Text from pdf_parser.extract_text_from_pdf()

    Returns:
        {
            "cleaned_text": str,       # Full text without page markers
            "sections": [              # Detected sections
                {"heading": str, "body": str},
                ...
            ],
            "stats": {
                "char_count": int,
                "section_count": int,
                "page_markers_stripped": int,
            }
        }
    """
    # Step 1: Strip page markers
    stripped, marker_count = _strip_page_markers(raw_text)

    # Step 2: Clean noise
    cleaned = _clean_noise(stripped)

    # Step 3: Detect sections
    sections = _extract_sections(cleaned)

    return {
        "cleaned_text": cleaned,
        "sections": sections,
        "stats": {
            "char_count": len(cleaned),
            "section_count": len(sections),
            "page_markers_stripped": marker_count,
        },
    }


def format_for_prompt(preprocessed: dict, max_chars: int = 12000) -> str:
    """
    Format preprocessed SOP into a structured prompt input.

    If sections were detected, formats as:
        ## Section Title
        Body text...

    If no sections detected, returns cleaned text directly.
    Truncates intelligently to max_chars (at section boundaries, not mid-sentence).
    """
    sections = preprocessed.get("sections", [])

    if not sections:
        text = preprocessed["cleaned_text"]
        return _smart_truncate(text, max_chars)

    parts = []
    total_len = 0

    for sec in sections:
        heading = sec["heading"]
        body = sec["body"]
        chunk = f"## {heading}\n{body}\n"

        if total_len + len(chunk) > max_chars:
            # Try to fit a truncated version of this last section
            remaining = max_chars - total_len
            if remaining > 100:
                parts.append(f"## {heading}\n{body[:remaining - len(heading) - 5]}...")
            break

        parts.append(chunk)
        total_len += len(chunk)

    return "\n".join(parts)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _strip_page_markers(text: str) -> tuple[str, int]:
    """Remove [Page N] markers injected by pdf_parser. Returns (text, count)."""
    pattern = r"\[Page \d+\]\n?"
    count = len(re.findall(pattern, text))
    cleaned = re.sub(pattern, "", text)
    return cleaned, count


def _clean_noise(text: str) -> str:
    """Remove common PDF extraction noise."""
    # Collapse excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ blank lines → 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip each line
    lines = [line.strip() for line in text.split("\n")]
    # Remove lines that are just page numbers or single chars
    lines = [l for l in lines if not re.match(r"^\d{1,3}$", l)]
    return "\n".join(lines).strip()


def _extract_sections(text: str) -> list[dict]:
    """
    Detect section headings and split text into sections.

    Heading heuristics (prioritized):
    1. Lines that are ALL CAPS and short (< 80 chars)
    2. Lines starting with a number + dot/paren (e.g. "1. RECEIVING", "3) Quality Check")
    3. Lines ending with a colon that are short (< 80 chars)
    4. Lines starting with common SOP heading patterns
    """
    lines = text.split("\n")
    sections = []
    current_heading = None
    current_body_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_body_lines.append("")
            continue

        if _is_heading(stripped):
            # Save previous section
            if current_heading is not None or current_body_lines:
                sections.append({
                    "heading": current_heading or "Introduction",
                    "body": "\n".join(current_body_lines).strip(),
                })
            current_heading = stripped.rstrip(":")
            current_body_lines = []
        else:
            current_body_lines.append(stripped)

    # Save last section
    if current_heading is not None or current_body_lines:
        sections.append({
            "heading": current_heading or "Introduction",
            "body": "\n".join(current_body_lines).strip(),
        })

    # Filter out empty sections
    sections = [s for s in sections if s["body"].strip()]

    return sections


def _is_heading(line: str) -> bool:
    """Determine if a line is likely a section heading."""
    # Too long to be a heading
    if len(line) > 80:
        return False

    # Too short / just punctuation
    if len(line.strip()) < 3:
        return False

    # ALL CAPS (at least 3 alpha chars) — very common in SOPs
    alpha_chars = [c for c in line if c.isalpha()]
    if len(alpha_chars) >= 3 and line == line.upper():
        return True

    # Numbered section: "1. Title", "2) Title", "Step 1:", etc.
    if re.match(r"^(?:step\s*)?\d+[\.\)\:\-]\s*.{3,}$", line, re.IGNORECASE):
        return True

    # Line ending with colon (short lines only)
    if line.endswith(":") and len(line) < 60:
        return True

    # Common SOP heading keywords at start of line
    heading_patterns = [
        r"^(?:purpose|scope|objective|procedure|responsibilities|definitions|references|revision|appendix|equipment|materials|safety|precautions|overview)\b",
    ]
    for pat in heading_patterns:
        if re.match(pat, line, re.IGNORECASE):
            return True

    return False


def _smart_truncate(text: str, max_chars: int) -> str:
    """Truncate text at a sentence boundary near max_chars."""
    if len(text) <= max_chars:
        return text

    # Find last sentence-ending punctuation before max_chars
    truncated = text[:max_chars]
    last_period = max(
        truncated.rfind(". "),
        truncated.rfind(".\n"),
        truncated.rfind("? "),
        truncated.rfind("! "),
    )
    if last_period > max_chars * 0.7:
        return truncated[:last_period + 1]
    return truncated.rstrip() + "..."
