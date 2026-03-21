"""
test_sop_preprocessor.py — Tests for SOP text preprocessing.
Runs WITHOUT API keys — pure text processing logic.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.sop_preprocessor import (
    preprocess_sop,
    format_for_prompt,
    _strip_page_markers,
    _clean_noise,
    _extract_sections,
    _is_heading,
    _smart_truncate,
)


class TestStripPageMarkers:
    """Tests for [Page N] marker removal."""

    def test_strips_single_marker(self):
        text, count = _strip_page_markers("[Page 1]\nHello world")
        assert "[Page" not in text
        assert count == 1
        assert "Hello world" in text

    def test_strips_multiple_markers(self):
        text, count = _strip_page_markers("[Page 1]\nPart 1\n[Page 2]\nPart 2\n[Page 3]\nPart 3")
        assert count == 3
        assert "[Page" not in text
        assert "Part 1" in text
        assert "Part 3" in text

    def test_no_markers(self):
        text, count = _strip_page_markers("No markers here")
        assert count == 0
        assert text == "No markers here"


class TestCleanNoise:
    """Tests for noise cleaning."""

    def test_collapses_whitespace(self):
        result = _clean_noise("hello     world")
        assert "     " not in result

    def test_removes_page_number_lines(self):
        result = _clean_noise("content\n42\nmore content")
        assert "42" not in result.split("\n")

    def test_collapses_blank_lines(self):
        result = _clean_noise("a\n\n\n\n\nb")
        assert result == "a\n\nb"


class TestIsHeading:
    """Tests for heading detection heuristics."""

    def test_all_caps_is_heading(self):
        assert _is_heading("RECEIVING PROCEDURE") is True
        assert _is_heading("QUALITY CONTROL") is True

    def test_numbered_section_is_heading(self):
        assert _is_heading("1. Introduction") is True
        assert _is_heading("2) Safety Measures") is True
        assert _is_heading("Step 3: Verification") is True

    def test_colon_ending_is_heading(self):
        assert _is_heading("Materials Required:") is True

    def test_common_keywords_is_heading(self):
        assert _is_heading("Purpose of this document") is True
        assert _is_heading("Scope and applicability") is True
        assert _is_heading("Procedure for receiving") is True

    def test_long_line_not_heading(self):
        long_line = "This is a very long line that definitely should not be considered a heading because it contains way too many characters to be a heading"
        assert _is_heading(long_line) is False

    def test_short_line_not_heading(self):
        assert _is_heading("ab") is False
        assert _is_heading("  ") is False

    def test_normal_sentence_not_heading(self):
        assert _is_heading("The employee should verify the order before accepting.") is False


class TestExtractSections:
    """Tests for section extraction."""

    def test_sections_from_caps_headings(self):
        text = "INTRODUCTION\nThis is the intro.\n\nPROCEDURE\nStep one.\nStep two."
        sections = _extract_sections(text)
        assert len(sections) == 2
        assert sections[0]["heading"] == "INTRODUCTION"
        assert "intro" in sections[0]["body"]
        assert sections[1]["heading"] == "PROCEDURE"

    def test_sections_from_numbered_headings(self):
        text = "1. Overview\nThis is an overview.\n\n2. Steps\nDo this first."
        sections = _extract_sections(text)
        assert len(sections) == 2

    def test_no_headings_returns_single_section(self):
        text = "Just some plain text without any headings or structure at all."
        sections = _extract_sections(text)
        assert len(sections) == 1
        assert sections[0]["heading"] == "Introduction"

    def test_empty_body_sections_filtered(self):
        text = "HEADING ONE\n\nHEADING TWO\nSome content here."
        sections = _extract_sections(text)
        # HEADING ONE has empty body, should be filtered
        assert all(s["body"].strip() for s in sections)


class TestSmartTruncate:
    """Tests for sentence-aware truncation."""

    def test_short_text_unchanged(self):
        assert _smart_truncate("Hello world.", 1000) == "Hello world."

    def test_truncates_at_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence that is very long."
        result = _smart_truncate(text, 35)
        assert result.endswith(".")
        assert len(result) <= 40  # some flexibility

    def test_truncates_with_ellipsis_if_no_boundary(self):
        text = "abcdefghijklmnopqrstuvwxyz"
        result = _smart_truncate(text, 10)
        assert result.endswith("...")


class TestPreprocessSop:
    """Integration tests for the full preprocessing pipeline."""

    def test_full_pipeline(self):
        raw = "[Page 1]\nINTRODUCTION\nThis is the intro.\n\n[Page 2]\nPROCEDURE\nStep one."
        result = preprocess_sop(raw)
        assert "cleaned_text" in result
        assert "sections" in result
        assert "stats" in result
        assert result["stats"]["page_markers_stripped"] == 2
        assert result["stats"]["section_count"] >= 1
        assert "[Page" not in result["cleaned_text"]


class TestFormatForPrompt:
    """Tests for prompt formatting."""

    def test_with_sections(self):
        preprocessed = {
            "sections": [
                {"heading": "Intro", "body": "Introduction text."},
                {"heading": "Steps", "body": "Step details."},
            ],
            "cleaned_text": "Full text here",
        }
        result = format_for_prompt(preprocessed, max_chars=5000)
        assert "## Intro" in result
        assert "## Steps" in result

    def test_without_sections(self):
        preprocessed = {
            "sections": [],
            "cleaned_text": "Just plain text.",
        }
        result = format_for_prompt(preprocessed, max_chars=5000)
        assert result == "Just plain text."

    def test_truncation_respects_max_chars(self):
        preprocessed = {
            "sections": [
                {"heading": f"Section {i}", "body": "X" * 500}
                for i in range(20)
            ],
            "cleaned_text": "X" * 10000,
        }
        result = format_for_prompt(preprocessed, max_chars=2000)
        assert len(result) <= 2200  # slight flexibility for last section
