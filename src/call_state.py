"""Simple per-call state and outcome finalization (Phase 05, PRD §12).

Deliberately a plain dict with a few helpers — not a state machine. The Realtime
model drives the conversation; Python only needs to track turns and settle a
final outcome string for metadata (Phase 06).
"""
from typing import Any, Dict


def new_state(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create the initial state for a call."""
    return {
        "call_id": scenario.get("call_id"),
        "scenario_name": scenario.get("scenario_name"),
        "outcome": None,
        "ended_by_patient": False,
        "turns": [],
    }


def record_turn(state: Dict[str, Any], speaker: str, text: str) -> None:
    """Append a (speaker, text) turn, ignoring empty/whitespace text."""
    if text and text.strip():
        state.setdefault("turns", []).append((speaker, text.strip()))


def finalize_state(state: Dict[str, Any], duration_seconds: int, timed_out: bool = False) -> Dict[str, Any]:
    """Settle duration and a human-readable outcome at the end of a call."""
    state["duration_seconds"] = duration_seconds
    if state.get("ended_by_patient") and state.get("outcome"):
        pass  # patient's end_call reason wins
    elif timed_out:
        state["outcome"] = state.get("outcome") or "Max call duration reached"
    else:
        state["outcome"] = state.get("outcome") or "Call ended without explicit stop condition"
    return state
