"""Live call orchestration: place the call and bridge Twilio <-> OpenAI Realtime.

``validate_ready_for_call`` is a deterministic pre-flight check (unit-tested).
The async bridge below is thin glue over the pure helpers in ``telephony`` and
``realtime_bridge``; it is verified on real calls rather than in unit tests.
Artifact capture (recording/transcript) is layered on in Phase 06.
"""
import asyncio
import json
import sys
from typing import Any, Dict

import config as config_mod
import patient_brain
import realtime_bridge
import telephony
from config import MissingConfigError

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model={model}"


def _log(msg: str) -> None:
    """Lightweight call tracing to stderr (invaluable on the first live call)."""
    print(f"[call] {msg}", file=sys.stderr, flush=True)

# Fields that must be present before we place a real outbound call.
_TELEPHONY_REQUIRED = (
    "twilio_account_sid",
    "twilio_auth_token",
    "twilio_phone_number",
    "public_media_stream_url",
    "caller_phone_number",
    "openai_api_key",
)


def validate_ready_for_call(cfg: config_mod.Config) -> None:
    """Raise :class:`MissingConfigError` if any telephony setting is absent."""
    missing = [name for name in _TELEPHONY_REQUIRED if not getattr(cfg, name, "")]
    if missing:
        raise MissingConfigError(
            "Missing telephony config for a real call: " + ", ".join(sorted(missing))
        )


async def _bridge(twilio_ws, cfg: config_mod.Config, instructions: str, state: Dict[str, Any]) -> None:
    """Bridge one Twilio media stream to a fresh OpenAI Realtime session."""
    import websockets  # lazy: keeps unit tests dependency-light

    url = OPENAI_REALTIME_URL.format(model=cfg.openai_realtime_model)
    # GA Realtime: no OpenAI-Beta header (that triggers the retired beta shape).
    headers = [("Authorization", f"Bearer {cfg.openai_api_key}")]
    _log(f"connecting to OpenAI Realtime ({cfg.openai_realtime_model})...")
    async with websockets.connect(url, additional_headers=headers) as oai:
        await oai.send(
            json.dumps(
                realtime_bridge.build_session_update(
                    instructions, voice=cfg.realtime_voice, silence_ms=600
                )
            )
        )
        _log("Realtime session.update sent")
        stream_sid = {"value": None}
        counters = {"in": 0, "out": 0}

        async def twilio_to_openai():
            async for raw in twilio_ws:
                msg = telephony.parse_twilio_message(raw)
                if msg["event"] == "start":
                    stream_sid["value"] = msg["stream_sid"]
                    _log(f"twilio stream started sid={msg['stream_sid']}")
                elif msg["event"] == "media" and msg["payload"]:
                    counters["in"] += 1
                    if counters["in"] == 1:
                        _log("first assistant audio frame received from Twilio")
                    await oai.send(json.dumps(realtime_bridge.build_audio_append(msg["payload"])))
                elif msg["event"] == "stop":
                    _log("twilio stream stopped")
                    return

        async def openai_to_twilio():
            async for raw in oai:
                event = json.loads(raw)
                etype = event.get("type", "")
                if etype == "error":
                    _log(f"OpenAI ERROR: {event.get('error')}")
                    continue
                delta = realtime_bridge.extract_audio_delta(event)
                if delta and stream_sid["value"]:
                    counters["out"] += 1
                    if counters["out"] == 1:
                        _log("first patient audio frame sent to Twilio")
                    await twilio_ws.send(telephony.build_media_message(stream_sid["value"], delta))
                    continue
                reason = realtime_bridge.extract_end_call_reason(event)
                if reason is not None:
                    _log(f"patient called end_call: {reason!r}")
                    state["outcome"] = reason
                    state["ended_by_patient"] = True
                    return
                # Transcript capture (both sides) — smoke-test visibility; Phase 06
                # formats these into transcript.txt.
                if etype == "conversation.item.input_audio_transcription.completed":
                    text = (event.get("transcript") or "").strip()
                    if text:
                        _log(f"ASSISTANT: {text}")
                        state.setdefault("turns", []).append(("assistant", text))
                elif etype == "response.output_audio_transcript.done":
                    text = (event.get("transcript") or "").strip()
                    if text:
                        _log(f"PATIENT:   {text}")
                        state.setdefault("turns", []).append(("patient", text))

        tasks = [asyncio.ensure_future(twilio_to_openai()), asyncio.ensure_future(openai_to_twilio())]
        try:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                exc = task.exception()
                if exc:
                    _log(f"bridge task error: {exc!r}")
        finally:
            for task in tasks:
                task.cancel()
            _log(f"bridge closed (frames in={counters['in']} out={counters['out']})")


async def run_call(scenario: Dict[str, Any], cfg: config_mod.Config, state: Dict[str, Any]) -> Dict[str, Any]:
    """Start the media server, place the call, bridge audio, then hang up."""
    import websockets  # lazy

    instructions = patient_brain.build_instructions(scenario, caller_number=cfg.caller_phone_number)
    done = asyncio.Event()

    async def handler(twilio_ws):
        _log("Twilio connected to media WebSocket")
        try:
            await _bridge(twilio_ws, cfg, instructions, state)
        except Exception as exc:  # surface bridge failures on the first call
            _log(f"bridge exception: {exc!r}")
        finally:
            done.set()

    server = await websockets.serve(handler, "0.0.0.0", cfg.media_server_port)
    _log(f"media server listening on :{cfg.media_server_port}")
    client = telephony.make_twilio_client(cfg.twilio_account_sid, cfg.twilio_auth_token)
    try:
        twiml = telephony.build_stream_twiml(cfg.public_media_stream_url)
        _log(f"placing call to {cfg.target_phone_number} from {cfg.twilio_phone_number}")
        sid = telephony.place_outbound_call(
            client, to=cfg.target_phone_number, from_=cfg.twilio_phone_number, twiml=twiml
        )
        state["call_sid"] = sid
        _log(f"call SID {sid}; waiting up to {cfg.max_call_seconds}s")
        try:
            await asyncio.wait_for(done.wait(), timeout=cfg.max_call_seconds)
        except asyncio.TimeoutError:
            _log("max call duration reached")
            state.setdefault("outcome", "Max call duration reached")
        # Best-effort hangup (runaway backstop / clean end).
        try:
            client.calls(sid).update(status="completed")
        except Exception:  # pragma: no cover - network best-effort
            pass
    finally:
        server.close()
        await server.wait_closed()
    return state


def place_call(scenario: Dict[str, Any], cfg: config_mod.Config) -> Dict[str, Any]:
    """Synchronous entry point: validate, then run the async call to completion."""
    validate_ready_for_call(cfg)
    state: Dict[str, Any] = {"call_id": scenario["call_id"], "outcome": None, "ended_by_patient": False}
    asyncio.run(run_call(scenario, cfg, state))
    return state
