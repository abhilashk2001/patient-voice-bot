# Phase 09 — Bug Report (AI-drafts, human-curates)

**Status:** To Do
**Depends on:** Phase 08
**Maps to PRD:** Phase 11 (FR12, FR13) — rubric criterion #2

## Goal
Turn the 10 transcripts into a curated, evidence-backed `BUG_REPORT.md`. This is the second-highest-weighted deliverable.

## Scope (in)
- A post-call analyzer that scores each transcript against that scenario's `bug_indicators` and emits **draft** candidates (with call_id, timestamp, evidence links) to `BUG_CANDIDATES.md`.
- **Human curation**: confirm/cull each candidate, set severity, write "why it matters," delete nitpicks → `BUG_REPORT.md` (PRD §18 format).
- `CALL_SUMMARY.md` table (FR13).
- Back-fill `bugs_found` in each `metadata.json`.

## Scope (out)
- No live/in-call detection (rejected in design). No auto-publish without review.

## Tasks
1. `analyze.py`: per transcript, match `bug_indicators`, pull the relevant timestamp/line, draft an entry (severity guess, evidence path).
2. Review every candidate manually — keep useful, well-described issues; **delete weak nitpicks**.
3. Focus categories: scope-control, scheduling, recovery, medical-safety, verification, inconsistent refusal, multi-intent, factual clinic errors (PRD §16). Reproduce known candidates (§17): off-topic math/pi, inconsistent guardrail, failed recovery.
4. Write final `BUG_REPORT.md` (each bug: ID, severity, call, timestamp, what happened, why it matters, expected behavior, evidence).
5. Fill `CALL_SUMMARY.md` table + `bugs_found` in metadata.

## Acceptance criteria (FR12/FR13)
- Every bug: ID, severity, call link, timestamp, what/why/expected, evidence.
- No weak nitpicks.
- `CALL_SUMMARY.md` table present.
- Every bug traces to call/transcript/recording/timestamp.

## Definition of done
A tight, curated bug report where each entry is defensible and evidence-linked — quality over quantity.
