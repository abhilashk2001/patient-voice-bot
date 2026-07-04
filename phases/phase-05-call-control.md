# Phase 05 — Turn-Taking & Call Control

**Status:** To Do
**Depends on:** Phase 04
**Maps to PRD:** (new — FR7, FR8, stop conditions)

## Goal
Make the conversation feel natural and end cleanly: tune turn-taking, keep the bot from talking over the agent, and wire the `end_call` tool + time backstop.

## Scope (in)
- Server VAD configuration on the Realtime session (silence ~500–700ms).
- Barge-in **OFF** by default; per-scenario `allow_barge_in` override honored.
- `end_call(reason)` tool defined on the Realtime session; instructions tell the patient to say a natural goodbye, then call it when the scenario stop condition is met.
- Supervisor: on `end_call` event → tear down (trigger Phase 06 artifact save + hang up). 180s hard cap as runaway backstop.
- Simple state dict per PRD §12 (probe count, appointment_confirmed, etc.) if useful for outcome/metadata.

## Scope (out)
- No new telephony plumbing (built in Phase 04).

## Tasks
1. Set `turn_detection: server_vad`, `silence_duration_ms ~600` in `session.update`.
2. Enforce no barge-in unless scenario flag set (gate outbound patient audio until agent utterance completes, if needed).
3. Register `end_call` tool; handle the tool-call event in `call_runner.py`.
4. Instruction wording: "When the goal is met / assistant clearly refuses / can't proceed, say a short natural goodbye, THEN call end_call with a brief reason."
5. Supervisor: 180s cap → hard stop; capture `reason` → `outcome` for metadata (Phase 06).

## Acceptance criteria (FR8)
- Bot waits for the agent to finish; no talking over on natural pauses.
- Replies feel prompt (not jumpy, not laggy).
- A call ends via `end_call` with a natural goodbye when the goal completes.
- Runaway calls stop at 180s.

## Definition of done
Calls sound polite and end naturally with a clean `outcome` string ready for metadata.
