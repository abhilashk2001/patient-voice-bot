# Patient Voice Bot

An automated voice bot that calls the Pretty Good AI test line, behaves like a
realistic patient, holds a natural spoken conversation with the clinic's AI
agent, records and transcribes both sides, and surfaces bugs in the agent's
behavior.

## Challenge objective

Build a Python voice bot that calls **+1‑805‑439‑8008**, simulates realistic
patient scenarios (scheduling, refills, questions, edge cases), records and
transcribes the conversations, and documents bugs it finds — with a minimum of
10 full calls. Voice-interaction quality is the top priority.

## System architecture (summary)

Each call is driven by a saved **scenario card** (persona, goal, hidden details,
speaking style, staged edge case, stop condition). Python controls the call flow
and a hard authorized-number guard, while an **OpenAI Realtime** speech‑to‑speech
session — bridged to the phone call over **Twilio Media Streams** — plays the
patient live, handling turn-taking, transcription, and speech natively.

```
scenarios.json → main.py → call_runner.py
   → Twilio places call to +18054398008
   → Twilio Media Streams  ⇄  (our ws bridge)  ⇄  OpenAI Realtime (the "patient")
   → recording.mp3 (Twilio dual-channel) + transcript.txt (Realtime events)
   → metadata.json → BUG_REPORT.md
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the design and the key decisions
(and [`FINAL_TECHNICAL_DOCUMENT.md`](FINAL_TECHNICAL_DOCUMENT.md) for the full
decision log).

## Free vs. paid strategy

- **Paid (quality-critical):** OpenAI Realtime (the patient voice + conversation)
  and Twilio (outbound telephony + dual-channel recording). Voice lucidity is the
  rubric's gate, so these are worth paying for.
- **Free:** ngrok (public tunnel), the whole scenario/state/transcript/metadata
  layer (plain Python + files), and the bug-candidate analyzer. No database, no
  frontend, no framework.

## Telephony setup — a funded Twilio account is required ⚠️

**Twilio *trial* accounts cannot complete this challenge.** Trial accounts may
only dial *verified* numbers, and you cannot verify the PGAI test line (the code
is sent to that number, which you don't control). Upgrade to a funded account
(usage is well under $1; the minimum is a balance you draw down). The same
verified-destination wall exists on Telnyx / SignalWire / Plivo free tiers, so
there is no genuinely free path to call an arbitrary number.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the values below

# in a separate terminal, expose the media server:
ngrok http 8080
# copy the wss URL into PUBLIC_MEDIA_STREAM_URL in .env
```

### Environment variables (`.env`)

| Variable | What it is |
|----------|------------|
| `TARGET_PHONE_NUMBER` | Authorized assessment number — **must** be `+18054398008` (guarded). |
| `CALLER_PHONE_NUMBER` / `TWILIO_PHONE_NUMBER` | Your Twilio number (the single number used for all calls). |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | Twilio REST credentials. |
| `PUBLIC_MEDIA_STREAM_URL` | ngrok `wss://…/media` URL (changes each ngrok restart). |
| `OPENAI_API_KEY` / `OPENAI_REALTIME_MODEL` | OpenAI key with Realtime access; `gpt-realtime`. |
| `REALTIME_VOICE` | Default voice (varied per scenario automatically). |
| `PATIENT_NAME` / `PATIENT_DOB` | Your **registered** PGAI patient identity (used to verify every call). |
| `PATIENT_PHONE_ON_FILE` | The phone number on file in your PGAI account (may differ in format from the Twilio number). |
| `MEDIA_SERVER_PORT` | Local ws port ngrok forwards to (default 8080). |
| `MAX_CALL_SECONDS` | Runaway backstop (default 180). |

> Secrets live only in `.env` (gitignored). `.env.example` has placeholders.
> **Note:** because the clinic verifies you by name + DOB, the real identity is
> spoken on calls and appears in the committed transcripts/recordings.

## Running it

```bash
# list scenarios
python src/main.py --list

# dry-run: render the prompt + run guards + scaffold folder, NO call, NO spend
python src/main.py --scenario call_09 --dry-run

# one real call
python src/main.py --scenario call_09

# all 10 scenarios, sequentially
python src/main.py --all

# download any recordings that finalized slowly, after a batch
python src/main.py --fetch-recordings
```

## Where outputs go

Each call writes `calls/<call_id>/`:

- `recording.mp3` — Twilio dual-channel (both sides)
- `transcript.txt` — both speakers, with a scenario header
- `scenario.json` — the exact scenario card used
- `metadata.json` — call id/SID, duration, outcome, bugs found

## Reviewing results

- **Recordings:** open `calls/<id>/recording.mp3`.
- **Transcripts:** read `calls/<id>/transcript.txt`.
- **Bugs:** [`BUG_REPORT.md`](BUG_REPORT.md) (curated) and
  [`CALL_SUMMARY.md`](CALL_SUMMARY.md) (per-call table). Candidates the analyzer
  drafted are in `BUG_CANDIDATES.md`.

## Cost estimate

| Item | Estimate |
|------|----------|
| Twilio outbound (US) | ~$0.014/min → 10 calls ≈ **$0.42** |
| Twilio number rental | ~$1.15/month |
| OpenAI Realtime audio | dominant cost; ~$0.30–1.50 per 3-min call → 10 calls ≈ **$3–15** |
| ngrok | free |
| **Total** | under the challenge's ~$20 guidance |

## Known limitations

- **ngrok URL changes** on each restart — update `PUBLIC_MEDIA_STREAM_URL`.
- **Transcript ordering:** occasionally a patient line prints just before the
  assistant question it answers — the *audio* order is correct; only the text log
  interleaves (the assistant's input-transcription event finalizes late).
- **Recording timing:** dual-channel recordings can take longer than the inline
  poll to finalize; `--fetch-recordings` grabs any stragglers.
- **Scenario reach depends on the agent:** if the clinic agent stalls (e.g., no
  availability), some edge-case probes may not fully play out.

## Testing

```bash
python -m pytest        # 139 tests (unit-level; the live bridge is verified on real calls)
```

## Loom & submission

- Walkthrough + AI-debugging screen recording: see [`docs/loom_links.md`](docs/loom_links.md).
- Caller number used for all test calls (E.164): **+15138663293**.
