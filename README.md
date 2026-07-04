# Patient Voice Bot

A scenario-guided voice bot that calls the Pretty Good AI test line, behaves like a
realistic patient, records and transcribes each call, and surfaces bugs in the
clinic assistant.

> **Status:** in development (Phase 01 complete). Full setup/usage docs are written in Phase 10.
> Architecture rationale: [`FINAL_TECHNICAL_DOCUMENT.md`](FINAL_TECHNICAL_DOCUMENT.md).
> Build plan: [`phases/KANBAN.md`](phases/KANBAN.md).

## Quick start (dev)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill in your values
python -m pytest          # run the test suite
```

The bot only ever calls the authorized assessment number; any other target is refused at config load.

## Telephony setup — a funded Twilio account is required ⚠️

**Twilio *trial* accounts cannot complete this challenge.** Trial accounts may
only dial *verified* numbers, and you cannot verify the PGAI test line (the
verification code is delivered to that number, which you don't control). This is
a hard prerequisite:

1. **Upgrade the Twilio account** (add a balance / leave trial). Usage is well
   under $1; the upgrade minimum is a balance you draw down, not a spend.
2. Buy/keep a Twilio phone number and put its SID/token/number in `.env`.
3. Start ngrok: `ngrok http 8080`, then set `PUBLIC_MEDIA_STREAM_URL=wss://<id>.ngrok-free.app/media`.
4. Use an OpenAI key with **Realtime API** access; `OPENAI_REALTIME_MODEL=gpt-realtime`.

(The same verified-destination wall exists on Telnyx / SignalWire / Plivo free
tiers — there is no genuinely free path to programmatically call an arbitrary
number.)

## Cost estimate

| Item | Estimate |
|------|----------|
| Twilio outbound (US) | ~$0.014/min → 10 calls × ~3 min ≈ **$0.42** |
| Twilio number rental | ~$1.15/month |
| OpenAI Realtime (gpt-realtime) audio | dominant cost; ~$0.30–1.50 per 3-min call → 10 calls ≈ **$3–15** |
| ngrok | free |
| **Total** | **comfortably under the challenge's ~$20 guidance** |

Verify actuals in the Twilio and OpenAI dashboards after your final 10 calls.
