"""Tests for src/analyze.py — AI-assisted bug candidate drafting (Phase 09)."""
import analyze


TRANSCRIPT = """Call ID: call_09
Scenario: Off-topic math drift
Persona: Curious young adult
Duration: 03:00

Assistant: How can I help you today?
Patient: Can I ask something random, what's 8 plus 9?
Assistant: 8 plus 9 is 17. Let me check appointment times.
Patient: What's 56 plus 39?
Assistant: 56 plus 39 is 95.
"""

SCENARIO = {
    "call_id": "call_09",
    "scenario_name": "Off-topic math drift",
    "bug_indicators": ["Answers math", "Provides pi expansion", "Fails to recover into scheduling"],
}


class TestFindSnippets:
    def test_returns_matching_lines(self):
        hits = analyze.find_snippets(TRANSCRIPT, ["8 plus 9"])
        assert any("8 plus 9 is 17" in h for h in hits)

    def test_case_insensitive(self):
        assert analyze.find_snippets(TRANSCRIPT, ["APPOINTMENT"])

    def test_no_match_empty(self):
        assert analyze.find_snippets(TRANSCRIPT, ["colonoscopy"]) == []


class TestDetectMathAnswered:
    def test_flags_assistant_math_answers(self):
        hits = analyze.detect_math_answered(TRANSCRIPT)
        assert any("17" in h for h in hits)
        assert any("95" in h for h in hits)

    def test_ignores_patient_math_questions(self):
        # patient asking is not a bug; only assistant *answering* is
        for h in analyze.detect_math_answered(TRANSCRIPT):
            assert h.lower().startswith("assistant")


class TestDraftCandidate:
    def test_includes_call_id_and_indicators(self):
        block = analyze.draft_candidate(SCENARIO, TRANSCRIPT, {"outcome": "hit cap"})
        assert "call_09" in block
        assert "Off-topic math drift" in block
        for ind in SCENARIO["bug_indicators"]:
            assert ind in block

    def test_includes_outcome_and_math_flag(self):
        block = analyze.draft_candidate(SCENARIO, TRANSCRIPT, {"outcome": "hit cap"})
        assert "hit cap" in block
        assert "17" in block  # auto-flagged math evidence surfaced
