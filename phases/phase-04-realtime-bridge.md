# Phase 04 — Telephony + Realtime Bridge  ⭐ (the hard one)

**Status:** ✅ Done — 95 tests green + **live verified 2026-07-04**: real call to +18054398008 connected, bidirectional audio confirmed, patient held a lucid in-scenario conversation (clinic responded contextually). Required moving to GA `gpt-realtime` shape (audio/pcmu passthrough, no beta header) + a funded Twilio account.
**Depends on:** Phase 03
**Maps to PRD:** Phases 4, 5, 6, 7 (collapsed — TTS/STT/telephony all handled by Realtime)

## Goal
Place a real outbound call to the authorized number and bridge the call's audio to an OpenAI Realtime session so the bot holds a live spoken conversation. **This is the phase the voice-lucidity gate lives in.**

## Scope (in)
- Outbound call via Twilio to `+18054398008` (guarded).
- A public WebSocket media server (ngrok-fronted) that Twilio Media Streams connects to.
- Bidirectional audio relay: Twilio media frames ↔ OpenAI Realtime (handle the audio format/codec conversion, e.g. g711 μ-law ↔ PCM16 as required).
- Realtime session created with the scenario `instructions` (from Phase 02) and a natural voice.
- `call_runner.py` orchestrates: start call → open Realtime session → relay loop.

## Scope (out)
- Fine-grained turn-taking/end tuning → Phase 05.
- Recording/transcript persistence → Phase 06.

## Tasks
1. Twilio outbound call: TwiML returns `<Connect><Stream url="wss://…/media">` (from `PUBLIC_MEDIA_STREAM_URL`); assert target == authorized before dialing.
2. WS server (`websockets`/`aiohttp`/FastAPI): accept Twilio media stream; parse `start`/`media`/`stop` events.
3. Open OpenAI Realtime session; send `session.update` with instructions + voice + audio format.
4. Relay: Twilio inbound audio → Realtime input; Realtime output audio → Twilio outbound media frames. Handle base64 + codec conversion + timing/chunking.
5. `call_runner.py` ties `main.py --scenario <id>` (no dry-run) to this flow; picks the scenario's rendered instructions.
6. Log Realtime + Twilio events for debugging.

## Acceptance criteria (FR4, FR5)
- A real call connects to `+18054398008`.
- The bot **sends audio into** the call and **receives** the agent's audio.
- A short multi-turn exchange happens and is audible/lucid.
- Call duration is tracked; failed calls are logged (not counted as valid).

## Risks / watch-items
- Audio codec/sample-rate mismatch → garbled audio (most common failure).
- Latency/chunking → pauses (revisit in Phase 05).
- ngrok URL must match `.env` before dialing.

## Definition of done
One coherent, audible bot-driven call completes end-to-end (even if turn-taking/end handling is still rough — that's Phase 05).
