"""Tests for src/transcript_builder.py — readable transcript (Phase 06, FR10)."""
import transcript_builder


SCENARIO = {
    "call_id": "call_02",
    "scenario_name": "Normal doctor appointment scheduling",
    "persona": "Calm adult patient with knee pain",
}


def state_with_turns():
    return {
        "call_id": "call_02",
        "duration_seconds": 154,
        "turns": [
            ("assistant", "How can I help you today?"),
            ("patient", "Hi, I'd like to schedule a visit for knee pain."),
            ("assistant", "Sure, what day works?"),
        ],
    }


class TestBuildTranscript:
    def test_header_fields(self):
        t = transcript_builder.build_transcript(SCENARIO, state_with_turns())
        assert "Call ID: call_02" in t
        assert "Scenario: Normal doctor appointment scheduling" in t
        assert "Persona: Calm adult patient with knee pain" in t
        assert "Duration: 02:34" in t  # 154s -> 02:34

    def test_both_speakers_labeled(self):
        t = transcript_builder.build_transcript(SCENARIO, state_with_turns())
        assert "Assistant: How can I help you today?" in t
        assert "Patient: Hi, I'd like to schedule a visit for knee pain." in t

    def test_turn_order_preserved(self):
        t = transcript_builder.build_transcript(SCENARIO, state_with_turns())
        assert t.index("How can I help") < t.index("schedule a visit") < t.index("what day works")

    def test_handles_no_turns(self):
        empty = {"call_id": "call_02", "duration_seconds": 0, "turns": []}
        t = transcript_builder.build_transcript(SCENARIO, empty)
        assert "Call ID: call_02" in t  # header still present, no crash
