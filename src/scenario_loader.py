"""Load, validate, and look up scenario cards (Phase 02, FR2).

A scenario card is a *behavior plan*, not a script (PRD §10). This module only
reads and validates them; turning a card into a Realtime prompt is the job of
``patient_brain.build_instructions``.
"""
from typing import Dict, List, Tuple

from utils import read_json

PathLike = str

# Keys every scenario card must define (PRD §10.2).
REQUIRED_KEYS = (
    "call_id",
    "scenario_name",
    "persona",
    "tone",
    "patient_goal",
    "medical_or_clinic_issue",
    "hidden_details",
    "speaking_style",
    "edge_case",
    "stop_condition",
    "expected_assistant_behavior",
    "bug_indicators",
)

_EDGE_KEYS = ("type", "enabled", "rules")


class ScenarioError(Exception):
    """A scenario card is missing required fields or is malformed."""


def validate_scenario(card: Dict) -> None:
    """Raise :class:`ScenarioError` if ``card`` is missing required fields."""
    missing = [k for k in REQUIRED_KEYS if k not in card]
    if missing:
        raise ScenarioError(
            f"Scenario {card.get('call_id', '<unknown>')} missing keys: {missing}"
        )
    edge = card["edge_case"]
    edge_missing = [k for k in _EDGE_KEYS if k not in edge]
    if edge_missing:
        raise ScenarioError(
            f"Scenario {card['call_id']} edge_case missing keys: {edge_missing}"
        )


def load_scenarios(path: PathLike) -> List[Dict]:
    """Load and validate all scenario cards from a JSON array file."""
    data = read_json(path)
    if not isinstance(data, list):
        raise ScenarioError("scenarios.json must contain a JSON array of cards")
    for card in data:
        validate_scenario(card)
    return data


def get_scenario(scenarios: List[Dict], call_id: str) -> Dict:
    """Return the card with ``call_id`` or raise ``KeyError``."""
    for card in scenarios:
        if card["call_id"] == call_id:
            return card
    raise KeyError(f"No scenario with call_id={call_id!r}")


def list_scenarios(scenarios: List[Dict]) -> List[Tuple[str, str]]:
    """Return ``(call_id, scenario_name)`` pairs for display."""
    return [(c["call_id"], c["scenario_name"]) for c in scenarios]
