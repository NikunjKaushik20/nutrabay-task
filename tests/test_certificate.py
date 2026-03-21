"""
test_certificate.py — Tests for quiz scoring and certificate generation.
Runs WITHOUT API keys.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.certificate import analyse_quiz_results, generate_certificate


class TestAnalyseQuizResults:
    """Tests for quiz scoring logic."""

    def _make_quiz(self, answers: list[str]) -> list[dict]:
        """Helper to create quiz questions with given correct answers."""
        return [
            {"question": f"Q{i+1}?", "answer": ans, "explanation": f"Because {ans}"}
            for i, ans in enumerate(answers)
        ]

    def test_perfect_score(self):
        quiz = self._make_quiz(["A", "B", "C"])
        result = analyse_quiz_results(quiz, ["A", "B", "C"])
        assert result["score"] == 100
        assert result["correct"] == 3
        assert result["total"] == 3
        assert result["passed"] is True
        assert len(result["gap_questions"]) == 0

    def test_zero_score(self):
        quiz = self._make_quiz(["A", "B", "C"])
        result = analyse_quiz_results(quiz, ["B", "C", "A"])
        assert result["score"] == 0
        assert result["correct"] == 0
        assert result["passed"] is False
        assert len(result["gap_questions"]) == 3

    def test_partial_score_passing(self):
        quiz = self._make_quiz(["A", "B", "C", "D", "A"])
        # 4 out of 5 correct = 80%
        result = analyse_quiz_results(quiz, ["A", "B", "C", "D", "B"])
        assert result["score"] == 80
        assert result["correct"] == 4
        assert result["passed"] is True
        assert len(result["gap_questions"]) == 1

    def test_partial_score_failing(self):
        quiz = self._make_quiz(["A", "B", "C", "D", "A"])
        # 3 out of 5 correct = 60%
        result = analyse_quiz_results(quiz, ["A", "B", "C", "A", "B"])
        assert result["score"] == 60
        assert result["passed"] is False

    def test_boundary_score_70_passes(self):
        # 7/10 = 70% exactly
        quiz = self._make_quiz(["A"] * 10)
        answers = ["A"] * 7 + ["B"] * 3
        result = analyse_quiz_results(quiz, answers)
        assert result["score"] == 70
        assert result["passed"] is True

    def test_boundary_score_69_fails(self):
        # ~69%
        quiz = self._make_quiz(["A"] * 10)
        answers = ["A"] * 6 + ["B"] * 4  # 60%
        result = analyse_quiz_results(quiz, answers)
        assert result["passed"] is False

    def test_case_insensitive_matching(self):
        quiz = self._make_quiz(["A", "b", "C"])
        result = analyse_quiz_results(quiz, ["a", "B", "c"])
        assert result["correct"] == 3
        assert result["score"] == 100

    def test_empty_user_answers(self):
        quiz = self._make_quiz(["A", "B"])
        result = analyse_quiz_results(quiz, ["", ""])
        assert result["correct"] == 0
        assert result["score"] == 0

    def test_none_user_answers(self):
        quiz = self._make_quiz(["A"])
        result = analyse_quiz_results(quiz, [None])
        assert result["correct"] == 0

    def test_gap_questions_have_correct_info(self):
        quiz = [{"question": "What is X?", "answer": "A", "explanation": "Because A"}]
        result = analyse_quiz_results(quiz, ["C"])
        gap = result["gap_questions"][0]
        assert gap["question"] == "What is X?"
        assert gap["user_answer"] == "C"
        assert gap["correct_answer"] == "A"
        assert gap["explanation"] == "Because A"


class TestGenerateCertificate:
    """Tests for PDF certificate generation."""

    def test_returns_bytes_and_id(self):
        pdf_bytes, cert_id = generate_certificate(
            employee_name="Test User",
            sop_title="Test SOP",
            score=85,
            passed=True,
            skills_covered=["Skill 1", "Skill 2"],
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100, "PDF should have substantial content"
        assert isinstance(cert_id, str)
        assert len(cert_id) > 0

    def test_pdf_starts_with_correct_header(self):
        pdf_bytes, _ = generate_certificate(
            employee_name="Test",
            sop_title="SOP",
            score=50,
            passed=False,
            skills_covered=[],
        )
        assert pdf_bytes[:5] == b"%PDF-", "Output should be valid PDF"

    def test_unique_certificate_ids(self):
        """Each certificate should have a unique ID."""
        ids = set()
        for _ in range(5):
            _, cert_id = generate_certificate(
                employee_name="Test",
                sop_title="SOP",
                score=100,
                passed=True,
                skills_covered=["A"],
            )
            ids.add(cert_id)
        assert len(ids) == 5, "All certificate IDs should be unique"

    def test_failed_certificate_generates(self):
        """Should generate certificate even for failed attempts."""
        pdf_bytes, _ = generate_certificate(
            employee_name="Failing User",
            sop_title="Hard SOP",
            score=30,
            passed=False,
            skills_covered=["A", "B"],
        )
        assert len(pdf_bytes) > 100
