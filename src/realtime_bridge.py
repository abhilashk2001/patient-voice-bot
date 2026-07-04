"""OpenAI Realtime message construction and event translation (Phase 04).

Pure helpers for the bridge: build the ``session.update``, wrap inbound audio,
and pull audio / end_call signals out of Realtime server events. The async
socket loop that uses these lives in ``call_runner``.
"""
import json
from typing import Any, Dict, List, Optional

# The tool the patient calls to end the conversation (wired in Phase 05).
END_CALL_TOOL: Dict[str, Any] = {
    "type": "function",
    "name": "end_call",
    "description": (
        "End the phone call. Call this only after saying a short, natural goodbye, "
        "once the scenario's stop condition is met."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Brief reason the call is ending, e.g. 'appointment confirmed'.",
            }
        },
        "required": ["reason"],
    },
}


# Distinct GA voices, cycled per scenario so personas don't all sound identical.
VOICE_POOL = ["alloy", "ash", "ballad", "coral", "sage", "verse"]


def _call_number(call_id: str) -> int:
    digits = "".join(c for c in call_id if c.isdigit())
    return int(digits) if digits else 0


def voice_for_scenario(scenario: Dict[str, Any], default: str = "alloy") -> str:
    """Pick a voice for a scenario: explicit override, else a stable pool choice.

    Varying voices across the 10 calls makes each persona read as a distinct
    real caller (a cheap realism win for the voice-quality gate).
    """
    override = scenario.get("realtime_voice")
    if override:
        return override
    n = _call_number(scenario.get("call_id", ""))
    return VOICE_POOL[(n - 1) % len(VOICE_POOL)] if n else default


def session_kwargs_for_scenario(scenario: Dict[str, Any], cfg: Any) -> Dict[str, Any]:
    """Derive build_session_update kwargs from a scenario card (+ config defaults)."""
    return {
        "voice": voice_for_scenario(scenario, getattr(cfg, "realtime_voice", "alloy")),
        "silence_ms": int(scenario.get("vad_silence_ms", 600)),
        "allow_barge_in": bool(scenario.get("allow_barge_in", False)),
    }


def build_session_update(
    instructions: str,
    *,
    voice: str = "alloy",
    input_format: str = "audio/pcmu",
    output_format: str = "audio/pcmu",
    silence_ms: int = 600,
    allow_barge_in: bool = False,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build the GA ``session.update`` for the Realtime patient session.

    Uses the GA ``gpt-realtime`` shape (session.type="realtime", nested
    audio.input/audio.output, output_modalities). Defaults to audio/pcmu (G.711
    u-law) both directions so Twilio's 8 kHz mu-law audio flows through without
    resampling. Server VAD handles turn-taking; barge-in tuning is Phase 05.
    """
    return {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "instructions": instructions,
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": input_format},
                    "transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "silence_duration_ms": silence_ms,
                        "create_response": True,
                        # Polite by default: clinic speech interrupts the patient
                        # so the bot never talks over the agent. Barge-in scenarios
                        # flip this off so the patient keeps going.
                        "interrupt_response": not allow_barge_in,
                    },
                },
                "output": {
                    "voice": voice,
                    "format": {"type": output_format},
                },
            },
            "tools": tools if tools is not None else [END_CALL_TOOL],
            "tool_choice": "auto",
        },
    }


def build_audio_append(payload_b64: str) -> Dict[str, Any]:
    """Wrap base64 μ-law audio from Twilio as a Realtime input append event."""
    return {"type": "input_audio_buffer.append", "audio": payload_b64}


def extract_audio_delta(event: Dict[str, Any]) -> Optional[str]:
    """Return base64 audio from an output-audio delta event, else ``None``.

    Accepts both the GA ``response.output_audio.delta`` and the legacy
    ``response.audio.delta`` event names.
    """
    if event.get("type") in ("response.output_audio.delta", "response.audio.delta"):
        return event.get("delta")
    return None


def _parse_args(raw: Any) -> Dict[str, Any]:
    try:
        return json.loads(raw or "{}")
    except (ValueError, TypeError):
        return {}


def extract_end_call_reason(event: Dict[str, Any]) -> Optional[str]:
    """Return the end_call reason if ``event`` is the end_call tool completing.

    Handles both ``response.function_call_arguments.done`` and the GA
    ``response.output_item.done`` (item.type == "function_call"). Returns the
    reason string (possibly empty) when it is end_call, else ``None``.
    """
    etype = event.get("type")
    if etype == "response.function_call_arguments.done":
        if event.get("name") != "end_call":
            return None
        return str(_parse_args(event.get("arguments")).get("reason", ""))
    if etype == "response.output_item.done":
        item = event.get("item") or {}
        if item.get("type") == "function_call" and item.get("name") == "end_call":
            return str(_parse_args(item.get("arguments")).get("reason", ""))
    return None
