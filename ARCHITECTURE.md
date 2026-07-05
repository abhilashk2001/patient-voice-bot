# Architecture

This project uses a **simple scenario-guided voice bot** rather than a complex
multi-agent architecture. Each call is driven by a saved scenario card containing
the patient persona, goal, hidden details, speaking style, staged edge-case
behavior, and stop condition. During the call, Python manages the call flow, a
hard authorized-number guard, simple state, and artifact saving, while an
**OpenAI Realtime** speech-to-speech model generates the patient's spoken turns
based on the scenario and the assistant's audio. This keeps the caller adaptive
and realistic without becoming a rigid script or an over-engineered system.

The system minimizes cost by using free/local components wherever practical
(scenario management, state, transcript formatting, metadata, the bug analyzer)
and pays only where quality is critical: real outbound telephony (Twilio) and the
Realtime voice. Each call is saved with its recording, transcript, scenario
snapshot, and metadata, so every bug in [`BUG_REPORT.md`](BUG_REPORT.md) traces
back to concrete evidence.

## Pipeline

```
scenarios/scenarios.json     10 scenario cards
        │
     main.py                 CLI: --list / --scenario / --all / --dry-run / --fetch-recordings
        │                    config.py enforces TARGET == +18054398008 before any call
     call_runner.py          starts ws media server, places the call, runs the bridge
        │
  Twilio Media Streams  ⇄  realtime_bridge  ⇄  OpenAI Realtime  (patient_brain builds the prompt)
        │                        │
  recorder.py (mp3)      transcript_builder.py + call_state.py
        │                        │
                metadata.json / transcript.txt / recording.mp3
        │
     analyze.py → BUG_CANDIDATES.md → (curated) BUG_REPORT.md + CALL_SUMMARY.md
```

## Key design decisions (and why we deviated from the original PRD)

The PRD proposed a hand-rolled cascade (local Whisper STT + text LLM + local TTS).
We deviated deliberately; the full rationale is in
[`FINAL_TECHNICAL_DOCUMENT.md`](FINAL_TECHNICAL_DOCUMENT.md). Highlights:

- **Twilio + OpenAI Realtime instead of a hand-rolled cascade.** The rubric gates
  on voice lucidity; a speech-to-speech model gives native turn-taking and
  sub-second latency with *less* code. The PRD explicitly permits paid services
  where quality-critical.
- **Scenario → Realtime instructions; Python is a thin supervisor.** Staged
  edge-case logic lives in the prompt; Python enforces only the deterministic
  guardrails (auth number, max duration, clean hangup via an `end_call` tool).
- **g711 μ-law passthrough (`audio/pcmu`)** both directions, so Twilio's 8 kHz
  audio needs no resampling. Uses the **GA `gpt-realtime`** session shape.
- **Fixed patient identity.** The PGAI account has a real registered patient; the
  bot must verify with a constant name/DOB/on-file number (in `.env`, PII) — only
  the scenario/persona varies. Inventing identities made verification loop
  forever.

## Module deltas vs. the PRD

- `transcriber.py` / `tts.py` — collapsed into the Realtime session (no
  faster-whisper / Piper).
- `patient_brain.py` — a prompt-builder (scenario → instructions), not a
  per-turn LLM caller.
- Everything else follows the PRD structure: `config.py`, `main.py`,
  `call_runner.py`, `recorder.py`, `transcript_builder.py`, `utils.py`,
  `scenarios.json`, plus `realtime_bridge.py`, `call_state.py`, `artifacts.py`,
  and `analyze.py`.

## Testing

139 unit tests cover the deterministic pieces (config guard, scenario loading,
prompt building, session/event translation, TwiML + media framing, artifacts,
recorder, analyzer). The async audio bridge is verified on real calls, not mocks.
