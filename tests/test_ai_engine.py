"""
test_ai_engine.py — Tests for AI engine validation and sample output.
Runs WITHOUT API keys — only tests local logic.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.ai_engine import _validate_structure, get_sample_output


class TestValidateStructure:
    """Tests for the deep validation function."""

    def test_valid_data_passes(self):
        """Sample output should pass validation without errors."""
        data = get_sample_output()
        _validate_structure(data)  # should not raise

    def test_missing_required_key_raises(self):
        data = get_sample_output()
        del data["title"]
        with pytest.raises(ValueError, match="missing required keys"):
            _validate_structure(data)

    def test_missing_multiple_keys_raises(self):
        data = {"quiz": [], "training_steps": []}
        with pytest.raises(ValueError, match="missing required keys"):
            _validate_structure(data)

    def test_empty_training_steps_raises(self):
        data = get_sample_output()
        data["training_steps"] = []
        with pytest.raises(ValueError, match="non-empty list"):
            _validate_structure(data)

    def test_empty_quiz_raises(self):
        data = get_sample_output()
        data["quiz"] = []
        with pytest.raises(ValueError, match="non-empty list"):
            _validate_structure(data)

    def test_quiz_with_invalid_answer_letter_raises(self):
        data = get_sample_output()
        data["quiz"][0]["answer"] = "Z"
        with pytest.raises(ValueError, match="must be A/B/C/D"):
            _validate_structure(data)

    def test_quiz_with_too_few_options_raises(self):
        data = get_sample_output()
        data["quiz"][0]["options"] = ["A. Only one"]
        with pytest.raises(ValueError, match="at least 3 options"):
            _validate_structure(data)

    def test_training_step_empty_title_raises(self):
        data = get_sample_output()
        data["training_steps"][0]["title"] = ""
        with pytest.raises(ValueError, match="empty title"):
            _validate_structure(data)

    def test_training_step_empty_content_raises(self):
        data = get_sample_output()
        data["training_steps"][0]["content"] = "   "
        with pytest.raises(ValueError, match="empty content"):
            _validate_structure(data)

    def test_summary_points_too_few_raises(self):
        data = get_sample_output()
        data["summary_points"] = ["Only one"]
        with pytest.raises(ValueError, match="at least 3"):
            _validate_structure(data)


class TestSampleOutput:
    """Tests that sample output matches the expected schema."""

    def test_sample_has_all_required_keys(self):
        data = get_sample_output()
        required = ["title", "objective", "summary_points", "training_steps", "quiz", "skills_covered"]
        for key in required:
            assert key in data, f"Sample output missing key: {key}"

    def test_sample_has_is_sample_flag(self):
        data = get_sample_output()
        assert data.get("is_sample") is True

    def test_sample_quiz_has_5_questions(self):
        data = get_sample_output()
        assert len(data["quiz"]) == 5

    def test_sample_quiz_options_format(self):
        data = get_sample_output()
        for i, q in enumerate(data["quiz"]):
            assert len(q["options"]) == 4, f"Quiz Q{i+1} should have 4 options"
            assert q["answer"] in ("A", "B", "C", "D"), f"Quiz Q{i+1} answer must be A-D"
            for opt in q["options"]:
                assert ". " in opt, f"Quiz Q{i+1} option '{opt}' should be in format 'X. text'"

    def test_sample_training_steps_ordered(self):
        data = get_sample_output()
        steps = data["training_steps"]
        for i, step in enumerate(steps):
            assert step["step"] == i + 1, f"Step {i+1} has wrong step number: {step['step']}"

    def test_sample_skills_not_empty(self):
        data = get_sample_output()
        assert len(data["skills_covered"]) >= 3

    def test_sample_has_estimated_time(self):
        data = get_sample_output()
        assert "estimated_training_time" in data
        assert len(data["estimated_training_time"]) > 0
