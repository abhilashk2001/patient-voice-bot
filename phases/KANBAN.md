# Patient Voice Bot — Kanban Board

Break the build into 10 phases, each with its own PRD in this folder. Move a card down the columns as you go. Dependencies are strict top-to-bottom except where noted.

> Architecture reference: `../FINAL_TECHNICAL_DOCUMENT.md` · Memory: `voice-bot-architecture`

## Columns

Move each phase's line between the three sections below (edit the checkbox / section).

### 📋 To Do
- [ ] **Phase 06** — Artifact Saving → `phase-06-artifacts.md`
- [ ] **Phase 07** — Dev Test Calls & Iteration → `phase-07-dev-calls.md`
- [ ] **Phase 08** — Final 10 Calls → `phase-08-final-calls.md`
- [ ] **Phase 09** — Bug Report → `phase-09-bug-report.md`
- [ ] **Phase 10** — Submission Packaging → `phase-10-submission.md`

### 🚧 In Progress
_(none yet)_

### ✅ Done
- [x] **Phase 01** — Repo Setup & Config → `phase-01-repo-setup.md` _(36 tests green; FR1 guard verified)_
- [x] **Phase 02** — Scenario System → `phase-02-scenario-system.md` _(56 tests green; 10 cards + prompt-builder)_
- [x] **Phase 03** — CLI & Dry-Run → `phase-03-cli-dry-run.md` _(65 tests green; --list/--scenario/--all/--dry-run)_
- [x] **Phase 04** — Telephony + Realtime Bridge → `phase-04-realtime-bridge.md` _(95 tests green; LIVE VERIFIED — lucid bidirectional call)_
- [x] **Phase 05** — Turn-Taking & Call Control → `phase-05-call-control.md` _(109 tests green; LIVE VERIFIED — end_call fired, varied voices, outcome captured)_

## Dependency map

```
01 Repo Setup
   └─> 02 Scenario System
          └─> 03 CLI & Dry-Run
                 └─> 04 Realtime Bridge  ── (the hard one; voice-lucidity gate)
                        └─> 05 Call Control
                               └─> 06 Artifacts
                                      └─> 07 Dev Test Calls & Iteration
                                             └─> 08 Final 10 Calls
                                                    └─> 09 Bug Report
                                                           └─> 10 Submission
```

## Phase-to-PRD map (vs. original PRD roadmap §19)

| Our phase | Original PRD phase(s) | Notes |
|-----------|----------------------|-------|
| 01 Repo Setup & Config | Phase 1 | + auth-number guard in config.py |
| 02 Scenario System | Phase 2, 3 (brain) | patient_brain = prompt-builder |
| 03 CLI & Dry-Run | Phase 3 | dry-run = prompt render + guards |
| 04 Realtime Bridge | Phase 4, 5, 6, 7 | TTS + STT + telephony collapse into Realtime |
| 05 Call Control | (new) | VAD, barge-in off, end_call tool |
| 06 Artifacts | Phase 8 | Twilio recording + Realtime transcript |
| 07 Dev Test Calls | Phase 9 | |
| 08 Final 10 Calls | Phase 10 | |
| 09 Bug Report | Phase 11 | AI-drafts, human-curates |
| 10 Submission | Phase 12 | |
