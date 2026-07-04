"""Twilio glue: TwiML, Media Streams framing, and the guarded outbound dial.

The heavy async plumbing lives in ``call_runner``. Everything here is pure and
unit-testable; the only side effect is ``place_outbound_call``, which takes an
injected Twilio client so tests can pass a fake.
"""
import json
from typing import Any, Dict, Optional

from config import AUTHORIZED_TARGET, UnauthorizedTargetError
from utils import normalize_phone


def build_stream_twiml(media_ws_url: str) -> str:
    """Return TwiML that connects the call's audio to our media WebSocket.

    ``<Connect><Stream>`` is bidirectional: Twilio sends inbound audio to the
    URL and plays back audio we send on the same socket.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Connect>"
        f'<Stream url="{media_ws_url}"/>'
        "</Connect>"
        "</Response>"
    )


def build_media_message(stream_sid: str, payload_b64: str) -> str:
    """Build an outbound Twilio media message carrying base64 μ-law audio."""
    return json.dumps(
        {"event": "media", "streamSid": stream_sid, "media": {"payload": payload_b64}}
    )


def parse_twilio_message(raw: str) -> Dict[str, Any]:
    """Normalize an incoming Twilio Media Stream message.

    Returns a dict with ``event``, ``stream_sid``, ``payload`` (μ-law base64 for
    media events, else ``None``), and the original ``raw`` dict.
    """
    data = json.loads(raw)
    event = data.get("event")
    stream_sid = data.get("streamSid")
    if not stream_sid and isinstance(data.get("start"), dict):
        stream_sid = data["start"].get("streamSid")
    payload = None
    if event == "media":
        payload = data.get("media", {}).get("payload")
    return {"event": event, "stream_sid": stream_sid, "payload": payload, "raw": data}


def place_outbound_call(client: Any, *, to: str, from_: str, twiml: str, record: bool = True) -> str:
    """Place an outbound call — but only to the authorized number.

    ``client`` is any object exposing ``calls.create(**kwargs)`` (the Twilio
    REST client, or a fake in tests). Records dual-channel by default so the
    saved recording carries both sides (FR9). Returns the created call SID.
    """
    normalized = normalize_phone(to)
    if normalized != AUTHORIZED_TARGET:
        raise UnauthorizedTargetError(
            f"Refusing to dial {normalized!r}; only {AUTHORIZED_TARGET} is authorized."
        )
    kwargs = {"to": normalized, "from_": from_, "twiml": twiml}
    if record:
        kwargs["record"] = True
        kwargs["recording_channels"] = "dual"
    call = client.calls.create(**kwargs)
    return call.sid


def make_twilio_client(account_sid: str, auth_token: str) -> Any:  # pragma: no cover
    """Construct a real Twilio REST client (imported lazily to keep tests light)."""
    from twilio.rest import Client

    return Client(account_sid, auth_token)
