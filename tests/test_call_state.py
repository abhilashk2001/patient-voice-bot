"""Tests for src/call_state.py — simple per-call state + outcome (Phase 05, PRD §12)."""
import call_state


CARD = {"call_id": "call_09", "scenario_name": "Off-topic math drift"}


class TestNewState:
    def test_initial_fields(self):
        s = call_state.new_state(CARD)
        assert s["call_id"] == "call_09"
        assert s["scenario_name"] == "Off-topic math drift"
        assert s["outcome"] is None
        assert s["ended_by_patient"] is False
        assert s["turns"] == []


class TestRecordTurn:
    def test_appends_turn(self):
        s = call_state.new_state(CARD)
        call_state.record_turn(s, "patient", "Hi there")
        call_state.record_turn(s, "assistant", "How can I help?")
        assert s["turns"] == [("patient", "Hi there"), ("assistant", "How can I help?")]

    def test_ignores_empty_text(self):
        s = call_state.new_state(CARD)
        call_state.record_turn(s, "patient", "   ")
        call_state.record_turn(s, "assistant", "")
        assert s["turns"] == []


class TestFinalize:
    def test_patient_end_call_reason_preserved(self):
        s = call_state.new_state(CARD)
        s["ended_by_patient"] = True
        s["outcome"] = "appointment confirmed"
        call_state.finalize_state(s, duration_seconds=95, timed_out=False)
        assert s["outcome"] == "appointment confirmed"
        assert s["duration_seconds"] == 95

    def test_timeout_without_reason(self):
        s = call_state.new_state(CARD)
        call_state.finalize_state(s, duration_seconds=180, timed_out=True)
        assert s["outcome"] == "Max call duration reached"
        assert s["duration_seconds"] == 180

    def test_ended_without_explicit_stop(self):
        s = call_state.new_state(CARD)
        call_state.finalize_state(s, duration_seconds=60, timed_out=False)
        assert s["outcome"]  # some non-empty description
        assert s["duration_seconds"] == 60
