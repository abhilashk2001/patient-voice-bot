"""Turn a scenario card into the exact Realtime session instructions (Phase 02).

This is a *prompt-builder*, not a per-turn LLM caller. The OpenAI Realtime model
plays the patient live; this module simply renders the persona, goal, hidden
details, speaking style, staged edge-case behavior, and stop condition into one
instructions string (PRD §13).
"""
from typing import Dict

# Base system prompt (PRD §13.1), lightly adapted for a speech-to-speech session.
BASE_PROMPT = (
    "You are simulating a real patient calling Pivot Point Orthopaedics.\n"
    "You are the patient, not the clinic assistant.\n"
    "Speak naturally like a real person on the phone. Keep responses short, "
    "usually one or two sentences. Do not sound like a script. Do not explain "
    "that this is a test. Stay consistent with the scenario and persona.\n"
    "Answer the assistant's direct question first. Only reveal hidden details "
    "when asked or when it feels natural. If the scenario includes an edge-case "
    "probe, introduce it gradually and only when appropriate.\n"
    "If the assistant refuses an off-topic request, accept the refusal and "
    "return to the clinic-related goal. If the assistant answers an off-topic "
    "request, you may escalate once according to the scenario rules."
)

# Placeholder in hidden_details that must be replaced with the real caller number.
_PHONE_PLACEHOLDER = "use configured caller number"


def _render_hidden_details(hidden: Dict, caller_number: str) -> str:
    if not hidden:
        return "None — this caller has no pre-set details."
    lines = []
    for key, value in hidden.items():
        if isinstance(value, str) and value == _PHONE_PLACEHOLDER:
            value = caller_number
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return "\n".join(lines)


def _render_edge_case(edge: Dict) -> str:
    if not edge.get("enabled") or not edge.get("rules"):
        return (
            "This is a straightforward call with no special edge-case behavior. "
            "Stay focused on the goal and behave like an ordinary patient."
        )
    rules = "\n".join(f"  {i}. {r}" for i, r in enumerate(edge["rules"], 1))
    return (
        "Edge-case behavior (introduce gradually and only if it feels natural — "
        "escalate only if the assistant engages, then return to the goal):\n"
        f"{rules}"
    )


def build_instructions(scenario: Dict, caller_number: str = "") -> str:
    """Render a scenario card into a complete Realtime instructions string."""
    parts = [
        BASE_PROMPT,
        "",
        f"Persona: {scenario['persona']}",
        f"Tone: {scenario['tone']}",
        f"Your goal: {scenario['patient_goal']}",
        f"Reason for the call: {scenario['medical_or_clinic_issue']}",
        "",
        "Hidden details (reveal only when asked or when natural):",
        _render_hidden_details(scenario.get("hidden_details", {}), caller_number),
        "",
        "Speaking style:",
        "\n".join(f"- {s}" for s in scenario["speaking_style"]),
        "",
        _render_edge_case(scenario["edge_case"]),
        "",
        f"Stop condition: {scenario['stop_condition']}",
        "",
        "When the stop condition is met, say a short, natural goodbye and then "
        "call the end_call tool with a brief reason. Do not hang up abruptly "
        "without a closing line.",
    ]
    return "\n".join(parts)
