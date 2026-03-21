"""
pdf_parser.py — Extract clean text from SOP PDF files using pdfplumber.
Supports multi-page docs, basic table detection, and optional metadata.
"""

import pdfplumber
import re
from pathlib import Path


def extract_text_from_pdf(pdf_path: str, include_page_markers: bool = False) -> str:
    """
    Extract and clean text from all pages of a PDF.

    Args:
        pdf_path: Absolute path to the PDF file.
        include_page_markers: If True, prefix each page's text with [Page N].
                              Default False — markers add noise for LLM processing.

    Returns:
        Cleaned, concatenated text from all pages.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If the PDF contains no extractable text.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_parts = []

            # Extract main text
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                page_parts.append(text)

            # Extract tables as formatted text
            tables = page.extract_tables()
            for table in tables:
                formatted = _format_table(table)
                if formatted:
                    page_parts.append(formatted)

            if page_parts:
                content = "\n".join(page_parts)
                if include_page_markers:
                    content = f"[Page {i + 1}]\n{content}"
                all_text.append(content)

    if not all_text:
        raise ValueError("No extractable text found in the PDF. It may be image-based.")

    combined = "\n\n".join(all_text)
    cleaned = _clean_text(combined)
    return cleaned


def extract_with_metadata(pdf_path: str) -> dict:
    """
    Extract text with page-level metadata.

    Returns:
        {
            "full_text": str,
            "pages": [{"page": int, "text": str, "char_count": int}, ...],
            "metadata": dict,
            "page_count": int,
        }
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages_data = []

    with pdfplumber.open(pdf_path) as pdf:
        pdf_meta = pdf.metadata or {}

        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""

            # Also grab tables
            tables = page.extract_tables()
            for table in tables:
                formatted = _format_table(table)
                if formatted:
                    text += "\n" + formatted

            pages_data.append({
                "page": i + 1,
                "text": text.strip(),
                "char_count": len(text.strip()),
            })

    full_text = "\n\n".join(p["text"] for p in pages_data if p["text"])
    full_text = _clean_text(full_text)

    return {
        "full_text": full_text,
        "pages": pages_data,
        "metadata": pdf_meta,
        "page_count": len(pages_data),
    }


def get_pdf_meta(pdf_path: str) -> dict:
    """Return basic metadata about the PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        return {
            "page_count": len(pdf.pages),
            "metadata": pdf.metadata or {},
        }


def _format_table(table: list) -> str:
    """Convert a pdfplumber table (list of lists) to readable text."""
    if not table:
        return ""
    rows = []
    for row in table:
        cells = [str(cell).strip() if cell else "" for cell in row]
        if any(cells):  # skip fully empty rows
            rows.append(" | ".join(cells))
    return "\n".join(rows) if rows else ""


def _clean_text(text: str) -> str:
    """Remove noise: excessive whitespace, repeated separators, etc."""
    # Collapse runs of 3+ spaces into a single space
    text = re.sub(r"  +", " ", text)
    # Collapse 3+ newlines into two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <path_to_pdf>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Extracting text from: {file_path}")
    result = extract_with_metadata(file_path)
    print(f"Pages: {result['page_count']}")
    print(f"Characters extracted: {len(result['full_text'])}")
    print("\n--- EXTRACTED TEXT (first 1000 chars) ---")
    print(result["full_text"][:1000])
