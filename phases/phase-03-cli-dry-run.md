# Phase 03 — CLI & Dry-Run

**Status:** ✅ Done (TDD — 65 tests green; CLI + dry-run verified end-to-end)
**Depends on:** Phase 02
**Maps to PRD:** Phase 3 (FR2, FR3)

## Goal
Build `main.py`'s command-line interface and the spend-free `--dry-run` that renders the instructions prompt, runs guards, and scaffolds the call folder.

## Scope (in)
- `main.py` argument parsing.
- Commands: `--list`, `--scenario <id>`, `--all`, `--dry-run`.
- Dry-run path (no telephony, no API spend).
- Per-call output folder scaffolding.

## Scope (out)
- No real calls (that's Phase 04). `--scenario` without `--dry-run` may stub/raise "not implemented yet" until Phase 04.

## Tasks
1. `python src/main.py --list` → prints all 10 scenario IDs + names.
2. `python src/main.py --scenario call_09 --dry-run`:
   - `[OK]` scenario valid,
   - `[OK]` target authorized (calls config guard),
   - prints `--- RENDERED REALTIME INSTRUCTIONS ---` block from Phase 02,
   - scaffolds `calls/call_09/` and copies scenario snapshot (`scenario.json`),
   - prints `No call placed. No spend.`
3. `--all` iterates all scenarios (in dry-run: renders each; live: deferred to Phase 08 orchestration).
4. Copy active scenario into the output folder (FR2).

## Acceptance criteria (from FR2/FR3)
- `--list` works.
- `--scenario call_09 --dry-run` works and places **no** call.
- Dry-run runs the auth guard and folder scaffolding.
- Clear error if scenario id is unknown.

## Definition of done
The entire non-telephony path is exercisable and cheap; this becomes the primary loop for iterating on prompts in later phases.
