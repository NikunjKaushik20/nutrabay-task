"""
test_pdf_parser.py — Tests for PDF text extraction and cleaning.
Uses the bundled SOP PDF in data/ and synthetic test cases.
"""

import os
import pytest

# Add project root to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.pdf_parser import extract_text_from_pdf, extract_with_metadata, _clean_text, _format_table


# ── Paths ─────────────────────────────────────────────────────────────────────
SAMPLE_PDF = os.path.join(os.path.dirname(__file__), "..", "data", "nutrabay_inbound_sop.pdf")


class TestExtractTextFromPdf:
    """Tests for the main extraction function."""

    @pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="Sample PDF not found")
    def test_extracts_text_from_real_pdf(self):
        text = extract_text_from_pdf(SAMPLE_PDF)
        assert isinstance(text, str)
        assert len(text) > 100, "Expected substantial text from sample SOP"

    @pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="Sample PDF not found")
    def test_no_page_markers_by_default(self):
        text = extract_text_from_pdf(SAMPLE_PDF, include_page_markers=False)
        assert "[Page " not in text, "Page markers should not be present by default"

    @pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="Sample PDF not found")
    def test_optional_page_markers(self):
        text = extract_text_from_pdf(SAMPLE_PDF, include_page_markers=True)
        assert "[Page 1]" in text, "Page markers should be present when requested"

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("/nonexistent/path/fake.pdf")


class TestExtractWithMetadata:
    """Tests for the metadata-enriched extraction."""

    @pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="Sample PDF not found")
    def test_returns_structured_output(self):
        result = extract_with_metadata(SAMPLE_PDF)
        assert "full_text" in result
        assert "pages" in result
        assert "page_count" in result
        assert "metadata" in result
        assert result["page_count"] > 0

    @pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="Sample PDF not found")
    def test_pages_have_correct_structure(self):
        result = extract_with_metadata(SAMPLE_PDF)
        for page in result["pages"]:
            assert "page" in page
            assert "text" in page
            assert "char_count" in page
            assert isinstance(page["page"], int)


class TestCleanText:
    """Tests for the text cleaning function."""

    def test_collapses_extra_spaces(self):
        assert _clean_text("hello    world") == "hello world"

    def test_collapses_extra_newlines(self):
        result = _clean_text("line1\n\n\n\n\nline2")
        assert result == "line1\n\nline2"

    def test_strips_line_whitespace(self):
        result = _clean_text("  hello  \n  world  ")
        assert result == "hello\nworld"

    def test_empty_string(self):
        assert _clean_text("") == ""

    def test_single_line(self):
        assert _clean_text("  single line  ") == "single line"


class TestFormatTable:
    """Tests for table formatting."""

    def test_empty_table(self):
        assert _format_table([]) == ""
        assert _format_table(None) == ""

    def test_simple_table(self):
        table = [["Name", "Role"], ["Alice", "QC"], ["Bob", "Receiving"]]
        result = _format_table(table)
        assert "Name | Role" in result
        assert "Alice | QC" in result

    def test_table_with_none_cells(self):
        table = [["A", None, "C"], [None, "B", None]]
        result = _format_table(table)
        assert "A |  | C" in result

    def test_all_empty_row_skipped(self):
        table = [[None, None], ["A", "B"]]
        result = _format_table(table)
        # First row is all empty/None, should be skipped
        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert "A | B" in lines[0]
