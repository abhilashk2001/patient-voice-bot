# Phase 08 — Final 10 Calls

**Status:** To Do
**Depends on:** Phase 07
**Maps to PRD:** Phase 10 (NFR3)

## Goal
Run all 10 scenarios as real, valid calls, each producing a complete artifact folder.

## Scope (in)
- `python src/main.py --all` (or run each scenario) placing 10 real calls sequentially.
- One caller number for ALL calls (challenge rule — single E.164 number).
- Verify each call is *valid*: connects, real conversation, tests the scenario, has recording + transcript.

## Scope (out)
- Bug analysis (Phase 09), packaging (Phase 10).

## Tasks
1. Confirm ngrok URL current in `.env`; confirm auth guard.
2. Run all 10 scenarios sequentially with a short gap between calls.
3. For each, verify `calls/call_NN/` has `recording.mp3` + `transcript.txt` + `scenario.json` + `metadata.json`.
4. Re-run any call that failed or was low quality (keep the single caller number).
5. Target 1–3 min full conversations (not single-question hang-ups).

## Acceptance criteria (NFR3)
- ≥10 valid call folders exist.
- Each call: connected, real multi-turn conversation, tested its scenario, has recording + transcript.
- All calls used the same caller number.

## Definition of done
10 complete, valid, lucid call folders ready for bug mining and submission.
