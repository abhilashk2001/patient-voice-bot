# Patient Voice Bot

An automated voice bot that **phones a clinic's AI receptionist, acts like a real
patient, and hunts for bugs.** It calls the Pretty Good AI test line, holds a
natural spoken conversation, records and transcribes both sides, and produces a
curated bug report — all driven by simple scenario cards and OpenAI's Realtime
voice model bridged to a live phone call over Twilio.

> **The kind of bug it finds:** on one call the patient casually asked *"what's 8
> plus 9?"* mid-scheduling — and the clinic agent answered **"8 plus 9 is 17"**,
> then **"56 plus 39 is 95."** A clinic bot acting as a calculator is a real
> scope-control gap. Full evidence: [`calls/call_09/`](calls/call_09) and
> [`BUG_REPORT.md`](BUG_REPORT.md).

---

## Try it in 2 commands (no paid accounts needed)

```bash
make setup     # creates a virtualenv and installs dependencies
make demo      # renders a real scenario prompt + scaffolds a call folder — no call, no spend
```

Also useful:

```bash
make test      # 139 unit tests
make list      # the 10 patient scenarios
```

`make demo` runs the **dry-run** path: it validates the scenario, enforces the
"only ever dial the authorized number" guard, and prints the exact instructions
the AI patient would use — without placing a real call or spending anything. This
lets a reviewer see the system work end-to-end with zero setup.

## Making real calls (needs your own accounts)

Real calls need a **funded Twilio account** (trial accounts can't dial the test
line — see below), an **OpenAI key with Realtime access**, and **ngrok**.

```bash
cp .env.example .env      # then fill in the values (see the file's comments)
ngrok http 8080           # copy the wss URL into PUBLIC_MEDIA_STREAM_URL

python src/main.py --scenario call_09     # one real call
python src/main.py --all                  # all 10, sequentially
python src/main.py --fetch-recordings     # grab any recording that finalized slowly
```

Each call writes everything to `calls/<call_id>/`:

| File | What it is |
|------|-----------|
| `recording.mp3` | The call audio, both sides (Twilio dual-channel) |
| `transcript.txt` | Both speakers, with a scenario header |
| `scenario.json` | The exact scenario card used |
| `metadata.json` | Call SID, duration, outcome, bugs found |

> ⚠️ **Twilio trial accounts cannot complete this** — they only dial *verified*
> numbers, and you can't verify the clinic's line. This is a hard prerequisite
> (usage is well under $1). The same wall exists on every telephony free tier.

## How it works

```
scenario card (persona, goal, edge case)
   → patient_brain builds the prompt
      → OpenAI Realtime plays the "patient" (speech-to-speech)
         ⇄ Twilio Media Streams ⇄ the live phone call to the clinic
      → recording.mp3 + transcript.txt + metadata.json
   → analyze.py drafts bug candidates → curated into BUG_REPORT.md
```

Python owns the deterministic parts (a hard authorized-number guard, call
timing, artifact saving); the OpenAI Realtime model owns the natural language and
turn-taking. No database, no frontend, no framework. Details in
[`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## How I built it (design-first, AI-assisted)

I optimized for **few bugs by construction**, not heroic debugging:

1. **Interrogated the plan first.** Before writing code I had an AI "grill me" on
   every design decision until the trade-offs were resolved — the voice pipeline,
   turn-taking, how calls end, artifacts. The result is
   [`FINAL_TECHNICAL_DOCUMENT.md`](FINAL_TECHNICAL_DOCUMENT.md): for each decision,
   the original plan, why I changed it, and the pros/cons.
2. **Wrote a technical doc + phased plan.** I broke the build into 10 phases, each
   with its own mini-PRD and acceptance criteria (see [`phases/`](phases) and the
   [Kanban board](phases/KANBAN.md)).
3. **Built test-first (TDD), phase by phase.** Every phase: write failing tests →
   implement → green. 139 tests total. The async audio bridge — which can't be
   meaningfully mocked — was verified on **real phone calls** instead.
4. **Iterated from real calls.** I ran dev calls, watched behavior, and fixed what
   the transcripts revealed. The running log is
   [`docs/iteration_notes.md`](docs/iteration_notes.md).

### The two real problems I hit (and how AI helped fix them)

Because of the design-first process the build was smooth, but two genuine issues
came up — documented in [`docs/iteration_notes.md`](docs/iteration_notes.md):

- **Verification kept looping (a design gap I caught by observing calls).** The
  clinic could never verify my patient because the bot was *inventing* names,
  while the test account has one real registered patient. Fix: inject a fixed
  identity (name/DOB/on-file number from `.env`) and never invent one — only the
  scenario/mood varies. This unblocked every scenario.
- **OpenAI's Realtime API had gone GA and changed its request shape.** The bridge
  connected but OpenAI rejected the session (`beta_api_shape_disabled`) because I
  was sending the retired *beta* format. With AI I looked up the current GA shape,
  updated the tests first, then the code (drop the beta header; nest audio
  settings; use `audio/pcmu` so the phone's 8 kHz audio passes through untouched),
  and confirmed the fix on a live call.

---

## What the bot found

Ten calls covering scheduling, rescheduling, cancellation, refills, insurance,
medical-advice boundaries, and deliberate edge cases. Curated findings in
[`BUG_REPORT.md`](BUG_REPORT.md); per-call table in
[`CALL_SUMMARY.md`](CALL_SUMMARY.md). Highlights:

- **Scope-control failure (High)** — answers off-topic math while scheduling.
- **Inconsistent enforcement** — answers math, ignores weather, refuses medical
  advice: no consistent policy.
- **Reschedule → silent new booking**, **cancellation dead-ends**, **persistent
  name mis-recognition**, and scheduling that rarely yields an actual appointment.

I also documented what the agent got **right** (correct clinic info, refusing
medical advice, handling multi-intent questions) — an honest assessment, not just
fault-finding. Candidates were AI-drafted by [`src/analyze.py`](src/analyze.py)
([`BUG_CANDIDATES.md`](BUG_CANDIDATES.md)) and then curated by hand.

## Repository layout

```
src/            # the bot (config guard, scenario loader, prompt builder, Twilio↔Realtime bridge,
                #   recorder, transcript/metadata, bug analyzer)
tests/          # 139 unit tests
scenarios/      # the 10 scenario cards
calls/          # the 10 completed calls (recording + transcript + scenario + metadata)
phases/         # the phased build plan (planning evidence)
docs/           # iteration notes
ARCHITECTURE.md, FINAL_TECHNICAL_DOCUMENT.md, BUG_REPORT.md, CALL_SUMMARY.md
```

## Cost

Under the challenge's ~$20 guidance: Twilio ≈ **$0.42** for 10 calls (+~$1.15/mo
number), OpenAI Realtime ≈ **$3–15**, ngrok free.

## Known limitations

- ngrok's URL changes each restart — update `PUBLIC_MEDIA_STREAM_URL`.
- Transcript lines can interleave slightly (the assistant's transcription event
  finalizes late); the *audio* order is always correct.
- Recordings occasionally finalize slower than the inline poll —
  `--fetch-recordings` grabs any stragglers.

## Submission

Caller number used for all test calls (E.164): **+15138663293**.
Walkthrough and AI-assisted-debugging videos are provided separately in the
submission form.
