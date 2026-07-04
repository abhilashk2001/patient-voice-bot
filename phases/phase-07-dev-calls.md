# Phase 07 — Dev Test Calls & Iteration

**Status:** ✅ Done — 2 dev calls (call_09, call_01) 2026-07-04. KEY FIX: fixed patient identity (real name+DOB from .env) so verification passes and scenarios reach intended behavior. call_09 captured the scope-control bug (agent answered 8+9=17, 23+58=81); call_01 baseline passed (correct hours/holiday/address, refused directions+weather). 129 tests green. OPEN: PII in deliverables (real name/DOB in transcripts+recordings) — decide before Phase 10 push.
**Depends on:** Phase 06
**Maps to PRD:** Phase 9

## Goal
Run 2–3 real development calls, find and fix the rough edges before spending on the final 10. This is where "evidence you iterated" (rubric #5) is earned.

## Scope (in)
- 2–3 live calls across a couple of scenarios (e.g., call_02 normal scheduling, call_09 math drift).
- Review recording + transcript for: voice quality, turn-taking, latency, transcript accuracy, scenario behavior.
- Fix major issues (VAD timing, prompt staging, codec/audio glitches, endpointing).
- Log findings in `docs/iteration_notes.md` (feeds the Loom + rubric #5).

## Scope (out)
- Not the final graded 10 (Phase 08).

## Tasks
1. Run `python src/main.py --scenario call_02` and `--scenario call_09` (real).
2. Listen back; note every glitch/awkward pause/scope-miss.
3. Adjust: VAD `silence_duration_ms`, instruction staging, voice choice, chunking.
4. Re-run to confirm improvement; capture before/after notes.

## Acceptance criteria
- Voice is lucid and natural on dev calls (the rejection gate).
- Turn-taking and pacing acceptable.
- Transcript good enough to continue conversation and to cite in bugs.
- Iteration notes recorded.

## Definition of done
Confidence that the final 10 will be lucid; major issues resolved and documented.
