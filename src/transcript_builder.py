"""Build a readable transcript from captured call state (Phase 06, FR10).

Turns are captured live in call_state as (speaker, text) pairs. This renders
them with a scenario header and speaker labels (PRD §9.8).
"""
from typing import Any, Dict

from utils import format_timestamp


def build_transcript(scenario: Dict[str, Any], state: Dict[str, Any]) -> str:
    """Render a transcript string with a header and both-speaker turns."""
    duration = format_timestamp(state.get("duration_seconds", 0))
    lines = [
        f"Call ID: {scenario.get('call_id', '')}",
        f"Scenario: {scenario.get('scenario_name', '')}",
        f"Persona: {scenario.get('persona', '')}",
        f"Duration: {duration}",
        "",
    ]
    for speaker, text in state.get("turns", []):
        lines.append(f"{speaker.capitalize()}: {text}")
    return "\n".join(lines) + "\n"
