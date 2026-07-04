# Final Technical Document — Patient Voice Bot

**Project:** Scenario-Guided Patient Voice Bot (Pretty Good AI — AI Engineering Challenge)
**Purpose of this document:** Record every architectural decision where we deviated from the original PRD, the reasoning that drove the change, and the trade-offs we accepted. For each decision we capture (1) the original PRD thought process and planned approach, (2) why we moved off it, (3) the approach we settled on, and (4) pros and cons.

> **Guiding constraint that shaped every decision:** The challenge rubric gates on one thing above all — *"The application will be rejected unless the voice conversation is lucid."* Voice interaction quality is evaluated **before** code review. Every deviation below is justified against that gate first, cost and simplicity second.

---

## Decision 1 — Core Voice Pipeline

### Original PRD thought process & planned approach
The PRD specified a **hand-rolled cascade** as the "simple, cheap" path:

```
Twilio Media Streams → faster-whisper (local STT) → OpenAI text model → Piper (local TTS) → Twilio
```

The reasoning was cost-consciousness: use free/local components (`STT_PROVIDER=local`, `TTS_PROVIDER=local`, `WHISPER_MODEL=base`, `PIPER_VOICE_PATH`) and only fall back to paid services if quality suffered. Python would stitch STT → LLM → TTS together in an explicit loop.

### Why we moved on
The cascade is the *hardest* path to make lucid, and lucidity is the rejection gate. A hand-rolled cascade forces us to solve three hard problems ourselves:
- **Endpointing** — detecting when the clinic agent has actually finished speaking.
- **Latency stacking** — STT + LLM + TTS delays add up into awkward pauses.
- **Barge-in / turn-taking** — natural overlap handling.

These are exactly the behaviors the rubric says get you rejected. Optimizing for "cheap" here directly threatens criterion #1.

### Present approach
**Twilio Media Streams bridged to OpenAI Realtime (speech-to-speech).** Our server relays audio between the phone call and the Realtime session; Realtime handles STT, response generation, TTS, and turn-taking natively.

```
Twilio call  <--audio-->  our ws bridge  <--audio-->  OpenAI Realtime
```

This is a deliberate deviation from the PRD's "local STT/TTS" default — but the PRD explicitly permits paid services "where necessary or quality-critical," and voice lucidity is the definition of quality-critical.

### Pros & cons
**Pros**
- Native turn-taking and barge-in — directly optimizes the rejection gate.
- Sub-second (~500–800ms) latency; natural conversational pacing.
- *Less* code than the cascade — no manual STT/LLM/TTS plumbing.
- Better transcription accuracy on phone audio than local `base` Whisper.

**Cons**
- Higher per-minute cost (~$0.06–0.30/min voice + Twilio ~$0.014/min) vs. free local components.
- Deviates from the PRD's literal "local-first" instruction (mitigated by transparent justification in ARCHITECTURE.md).
- Adds dependency on a single vendor's realtime API.

---

## Decision 2 — Who Drives Patient Behavior During the Call

### Original PRD thought process & planned approach
Core PRD philosophy: **"Python controls logic, OpenAI writes natural language."** `patient_brain.py` would call a text model **once per turn**, and Python would deterministically decide *when* to fire each edge-case probe (e.g., "now ask the pi question," "now return to scheduling") using a simple state dictionary. The staged escalation logic lived in Python.

### Why we moved on
Decision 1 moved the patient's "brain" into a speech-to-speech model that responds to audio autonomously. There is no clean per-turn "your turn now" hook to inject Python decisions without adding latency and stalls — and mid-turn injection is precisely what would reintroduce the awkward pauses we just eliminated. Forcing the PRD's per-turn-Python-control model on top of Realtime would fight the architecture and hurt lucidity.

### Present approach
**Scenario → Realtime session `instructions`; Python is a thin supervisor.**
- The scenario card's staged edge-case rules are encoded as **conditional stages inside the session instructions** (e.g., "Stage 1: request appointment normally. Stage 2: only if the assistant is helping, ask 8+9. Stage 3: if it answers, escalate, then pi. Stage 4: after 2–3 probes, return to scheduling.").
- **Python supervises only the deterministic guardrails:** authorized-number check, max-duration cap, and clean hangup on stop-condition.
- `patient_brain.py` demotes from a per-turn LLM caller to a **prompt-builder** (scenario.json → instructions string).

### Pros & cons
**Pros**
- Keeps the call lucid — no mid-turn injection stalls.
- Preserves the PRD's *hard* guardrails (auth, duration, clean end) where they actually matter.
- Far less code; staged behavior is declarative in the prompt.

**Cons**
- Less deterministic control over the *exact* moment a probe fires — we rely on the model following staged instructions rather than Python forcing each step.
- Requires careful prompt engineering to get reliable gradual escalation (mitigated by `--dry-run` prompt rendering, Decision 4).

---

## Decision 3 — Recording & Transcript Artifacts

### Original PRD thought process & planned approach
The PRD assumed the cascade, so:
- **Recording** — `recorder.py` saves mp3/ogg with both sides.
- **Transcript** — `transcriber.py` runs **local faster-whisper** on assistant speech; `transcript_builder.py` assembles both sides with timestamps.

Transcription was expected to be imperfect ("can be imperfect as long as the bot can respond coherently and the final transcript can be cleaned afterward").

### Why we moved on
With Realtime, local Whisper is redundant and *worse*: the Realtime session already emits accurate input/output transcription events for **both** sides, complete with per-utterance timing. Re-transcribing locally would add a moving part, lower accuracy on phone audio, and give us no timestamps we don't already have. The mandatory deliverable (≥10 recordings in mp3/ogg with both sides + timestamped transcripts) is better served by the two clean sources our pipeline already exposes.

### Present approach
- **Recording:** Twilio **dual-channel call recording**, downloaded as `recording.mp3` (both sides guaranteed and reliable).
- **Transcript:** built from **OpenAI Realtime transcription events**, formatted with timestamps and speaker labels.
- **Local faster-whisper is dropped entirely.**

```
Recording: Twilio dual-channel  → calls/call_NN/recording.mp3
Transcript: Realtime events      → [00:00] Assistant: ...
                                   [00:05] Patient: ...
```

### Pros & cons
**Pros**
- Both sides guaranteed in the recording (Twilio handles it).
- Accurate transcripts with real per-utterance timestamps → every bug can cite a genuine timestamp (satisfies FR12 traceability cleanly).
- One fewer dependency (no Whisper model download / CPU cost).

**Cons**
- Recording depends on Twilio's recording + download flow (an external dependency and a small storage/retrieval step).
- Transcript fidelity is tied to Realtime's transcription output rather than something we control locally.

---

## Decision 4 — `--dry-run` Semantics

### Original PRD thought process & planned approach
FR3 mandates a dry-run that places no real call. In the PRD's cascade, dry-run fed **typed assistant text into `patient_brain.py`** to exercise per-turn reply generation locally, avoiding telephony cost.

### Why we moved on
Decisions 1 & 2 removed the per-turn text LLM — the patient's brain now lives in the Realtime session instructions. There is no local per-turn generator left to "poke," so the PRD's dry-run definition would test nothing and become a hollow checkbox.

### Present approach
Dry-run is redefined to do two **real, useful, spend-free** things:
1. **Validate + load** the scenario and **render the exact Realtime instructions prompt to stdout** — so we can eyeball the staged edge-case logic before spending anything.
2. **Run the auth-number guard and scaffold** the call output folder — proving the entire non-telephony path.

```
$ main.py --scenario call_09 --dry-run
[OK] scenario call_09 valid
[OK] target +18054398008 authorized
--- RENDERED REALTIME INSTRUCTIONS ---
You are a curious young adult with elbow pain...
Stage 1... Stage 2 (only if engaged)...
--- END ---
[OK] scaffolded calls/call_09/
No call placed. No spend.
```

### Pros & cons
**Pros**
- Directly supports cheap iteration on the thing that now matters most — the prompt (Decision 2).
- Exercises everything except the live call: validation, auth guard, folder scaffolding.
- Zero API/telephony spend.

**Cons**
- Does not exercise the actual model conversation (a text-chat simulation would, but at some cost and without reflecting real voice/turn-taking). We accepted this because voice behavior can only be truly validated on a real call anyway.

---

## Decision 5 — Bug Report Workflow

### Original PRD thought process & planned approach
The PRD wants an **"AI-assisted bug report"** but explicitly lists **"fully automated bug reporting with no human review"** as an anti-pattern. Phase 11: *"Review transcripts and recordings manually. Use OpenAI only to help polish wording."* Each scenario already carries a machine-checkable `bug_indicators` array.

### Why we moved on
This isn't a reversal of the PRD — it's resolving the tension the PRD itself sets up (AI-assisted *but* human-reviewed). We had to decide precisely how much to automate. The rubric grades **bug quality** as criterion #2 ("useful, well-described issues beat a long list of nitpicks") and flags **"one-shot copy-paste from AI"** as a negative. So the points live in *human curation*, not automation — but AI can safely do the tedious, non-judged grunt work.

### Present approach
**AI drafts, human curates.** A post-call analyzer scores each transcript against that scenario's `bug_indicators` and emits **draft** candidate entries (with call ID, timestamp, and evidence links pre-filled) to a candidates file. We then **confirm / cull / set severity** by hand before anything lands in `BUG_REPORT.md`. AI does evidence-gathering; every keep/kill/severity judgment stays human.

```
analyze.py → BUG_CANDIDATES.md
  ## CANDIDATE (call_09 @ 01:12) [CONFIRM?]
  Indicator matched: 'Assistant provides pi expansion'
  Evidence: transcript line 14
  Draft severity: High
You edit/keep/delete → BUG_REPORT.md
```

### Pros & cons
**Pros**
- Captures exactly what's graded (useful, well-described, evidence-backed bugs).
- Keeps the mandated human veto — avoids the PRD anti-pattern and the "copy-paste from AI" negative.
- AI handles the tedious evidence/timestamp linking, speeding curation.

**Cons**
- The automation earns nothing *by itself* — value depends entirely on genuine curation. If candidates were pasted in unedited, a padded list would actively *lose* points.
- Requires discipline to delete weak candidates rather than keep them.

---

## Decision 6 — Turn-Taking & Barge-In

### Original PRD thought process & planned approach
FR8 wants polite turn-taking by default: *"The bot waits for the assistant to finish speaking… avoids talking over the assistant,"* with interruption behavior only if a scenario explicitly tests it. In the cascade, this would be implemented via manual VAD / silence detection.

### Why we moved on
Realtime uses server-side VAD and *can* barge in on any detected pause. Left at defaults, two failure modes both threaten the gate: (a) cutting off the clinic agent mid-sentence on a natural pause → sounds rude/glitchy; (b) VAD too conservative → long awkward silences. We had to pin the setting deliberately rather than inherit defaults.

### Present approach
**Polite default, per-scenario override.**
- Barge-in **OFF** by default — the patient waits for the agent to finish.
- VAD silence threshold tuned to **~500–700ms** so replies feel prompt but not jumpy.
- Exposed as a per-scenario flag so a future "interruption" scenario can enable barge-in (honoring FR8's escape hatch).

```
turn_detection: server_vad
silence_duration_ms: ~600
allow_barge_in: false   (per-scenario override)
```

### Pros & cons
**Pros**
- Safest setting on all 10 graded calls — no cutting off the agent, no jumpiness.
- Honors FR8's "interruption only if a scenario tests it."

**Cons**
- ~600ms is a tuned guess; may need adjustment after the first dev calls (accounted for in the iterate phase).
- None of the current 10 scenarios exercise the barge-in override, so that path stays unverified until used.

---

## Decision 7 — Call Termination

### Original PRD thought process & planned approach
The PRD's `call_runner.py` loop runs "while active and not timed out," stopping on the scenario stop condition or the `MAX_CALL_SECONDS=180` cap. Stop-condition detection was left implicit.

### Why we moved on
If *every* call simply runs into the 180s cap, we get dead air and abrupt cutoffs at exactly 3:00 — which reads as "the bot didn't know it was finished" and undercuts the "full 1–3 minute conversation, not a hang-up" quality bar. Each scenario defines a real stop condition ("appointment confirmed," "assistant clearly refuses and redirects"); the bot needs to recognize *goal complete* and wrap up naturally, with the time cap only as a backstop. Keyword-matching the transcript for this is brittle (misses paraphrases, risks premature/missed hangups).

### Present approach
**Model tool-call end + time backstop.**
- The Realtime patient is given a single `end_call(reason)` tool.
- It is instructed to deliver a natural closing line ("great, thanks — see you Friday, bye") and **then** call `end_call` once the scenario's stop condition is met.
- The supervisor hears that event and tears down the call (stops recording, hangs up).
- The 180s cap remains purely as a runaway backstop.
- `reason` becomes the `outcome` string in metadata.

### Pros & cons
**Pros**
- Natural, human-length calls that end when the goal is actually done.
- Clean, structured `outcome` for `metadata.json` — no fragile keyword matching.
- Time cap still protects against runaway cost.

**Cons**
- Relies on the model correctly recognizing the stop condition and invoking the tool (mitigated by the 180s backstop when it doesn't).
- Slightly more Realtime wiring (tool definition + event handling) than a pure time cap.

---

## Decision 8 — Public Endpoint (Twilio ↔ Server)

### Original PRD thought process & planned approach
The PRD's `.env.example` already anticipates a public tunnel, referencing ngrok URLs for `PUBLIC_WEBHOOK_URL` and `PUBLIC_MEDIA_STREAM_URL`. It also lists "production deployment architecture" as an explicit non-goal.

### Why we moved on
This wasn't so much a deviation as a deliberate confirmation: Twilio Media Streams needs a public `wss://` URL to reach our machine, and we had to choose between the instant-but-ephemeral ngrok and a stable-but-heavier deploy. Given the "run 10 calls from my laptop" reality and the PRD's anti-infra stance, we pinned the simpler option.

### Present approach
**ngrok, URLs read from `.env`.**
- `PUBLIC_WEBHOOK_URL` / `PUBLIC_MEDIA_STREAM_URL` set from the ngrok tunnel, exactly as the PRD template specifies.
- README instructs the reviewer to start ngrok and paste the URLs.

```
$ ngrok http 8080
→ https://abc123.ngrok-free.app
.env:
  PUBLIC_WEBHOOK_URL=https://abc123.ngrok-free.app/voice
  PUBLIC_MEDIA_STREAM_URL=wss://abc123.ngrok-free.app/media
```

### Pros & cons
**Pros**
- Lowest friction; matches the laptop-run reality and the PRD template.
- Avoids "production infrastructure" (a stated non-goal).

**Cons**
- Free ngrok URL changes on every restart — a reviewer re-running it must regenerate and re-paste (documented in README).
- Not permanently reachable (acceptable for an on-demand test harness).

---

## Folded-In Recommendations (lower-stakes, no separate deliberation)

| Item | Decision | Rationale |
|------|----------|-----------|
| Realtime model | Latest realtime snapshot | Best voice quality for the #1 gate |
| Patient voice | Natural human-sounding voice, **varied across scenarios** (young adult / older patient / parent) | Cheap realism win; personas read as real callers |
| `--all` pacing | Scenarios run **sequentially with a short gap** | One caller number, one target, per the challenge's "single number" rule |
| Cost guard | 180s hard cap + refuse-unless-`+18054398008` | Covers runaway spend; dry-run remains default iteration path |

---

## PRD Module Deltas (to note transparently in ARCHITECTURE.md)

Our choices *simplify* the PRD, which it explicitly invites ("implement this exact structure unless there is a strong reason not to"). We stay transparent about the changes:

- **`transcriber.py` / `tts.py`** → collapse into the Realtime session (no faster-whisper / Piper). Keep thin stubs or document their removal.
- **`patient_brain.py`** → becomes a **prompt-builder** (scenario.json → instructions string), not a per-turn LLM caller.
- **Everything else** — `config.py`, `main.py`, `call_runner.py`, `recorder.py`, `transcript_builder.py`, `utils.py`, `scenarios.json`, folder layout, and all deliverables — stays as specified.

**The single most important thing to state plainly in the writeup:** we deviated from "local STT/TTS" toward paid OpenAI Realtime **because the rubric gates on voice lucidity, and the PRD permits paid services where quality-critical.** This is an iteration/reasoning point that plays *for* us on rubric criteria #1 (lucid voice) and #4 (clear thinking), not a violation of the PRD's intent.
