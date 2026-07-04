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


def build_session_update(
    instructions: str,
    *,
    voice: str = "alloy",
    input_format: str = "audio/pcmu",
    output_format: str = "audio/pcmu",
    silence_ms: int = 600,
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
