# Phase 02 — Scenario System

**Status:** ✅ Done (TDD — 56 tests green; 10 scenario cards + prompt-builder verified)
**Depends on:** Phase 01
**Maps to PRD:** Phase 2 + Phase 3 (patient_brain as prompt-builder)

## Goal
Author the 10 scenario cards and the code that loads them and renders each into the exact Realtime `instructions` prompt (staged edge-case logic included).

## Scope (in)
- `scenarios/scenarios.json` — exactly the 10 cards from PRD §11 (call_01…call_10), full schema per §10.2.
- Scenario loader (in `utils.py` or a small `scenarios` loader): read, validate schema, list.
- `patient_brain.py` as a **prompt-builder**: `build_instructions(scenario, config) -> str` that turns a scenario card into the staged Realtime instructions (persona + goal + hidden details + speaking style + staged edge-case stages + stop condition), plus the base system prompt from PRD §13.1.

## Scope (out)
- No live model calls; no telephony. Rendering only.

## Tasks
1. Transcribe all 10 scenario cards verbatim from PRD §11 into `scenarios.json`.
2. Validate the JSON loads and each card has required keys (call_id, scenario_name, persona, tone, patient_goal, medical_or_clinic_issue, hidden_details, speaking_style, edge_case, stop_condition, expected_assistant_behavior, bug_indicators).
3. `patient_brain.build_instructions()`:
   - Start from PRD §13.1 base ("You are simulating a real patient calling Pivot Point Orthopaedics…").
   - Inject persona/tone/goal/hidden details (reveal only when asked) + speaking style.
   - Convert `edge_case.rules` into explicit **staged** conditional instructions (Stage 1 normal → Stage 2 only if engaged → escalate → return to goal after 2–3 probes).
   - Append stop condition + instruction to say a natural goodbye then call `end_call` (tool wired in Phase 05).
4. Map `hidden_details.phone_number = "use configured caller number"` → real `CALLER_PHONE_NUMBER`.

## Acceptance criteria
- `scenarios.json` contains 10 valid cards.
- `build_instructions(call_09)` produces a readable staged prompt with the math→pi escalation and the return-to-scheduling step.
- Loader can list all 10 (id + name).

## Definition of done
Every scenario renders to a coherent instructions string; feeds directly into Phase 03's `--dry-run` output.
