# Phase 06 — Artifact Saving

**Status:** To Do
**Depends on:** Phase 05
**Maps to PRD:** Phase 8 (FR9, FR10, FR11)

## Goal
Persist every call's recording, both-sides transcript, scenario snapshot, and metadata to its call folder.

## Scope (in)
- `recorder.py`: enable Twilio **dual-channel** recording; download to `calls/call_NN/recording.mp3`.
- `transcript_builder.py`: assemble `transcript.txt` from Realtime transcription events (both speakers, timestamps, scenario header per PRD §9.8).
- `metadata.json` writer per FR11 (call_id, scenario_name, start_time, duration_seconds, files, outcome, bugs_found placeholder, call_quality_notes).
- Scenario snapshot `scenario.json` (already copied in Phase 03; ensure present).

## Scope (out)
- Bug linkage (`bugs_found`) filled in Phase 09.

## Tasks
1. Turn on Twilio recording (dual channel) for the call; retrieve recording URL on completion; download + convert to mp3 if needed (ffmpeg).
2. Collect Realtime input/output transcription events during the call with timestamps; buffer per turn.
3. On call end, write `transcript.txt` with header (Call ID, Scenario, Persona, Duration) + `[MM:SS] Speaker: text` lines.
4. Write `metadata.json` (outcome from Phase 05's `end_call` reason).
5. Ensure each `calls/call_NN/` has: `recording.mp3`, `transcript.txt`, `scenario.json`, `metadata.json`.

## Acceptance criteria (FR9/FR10/FR11)
- Recording is mp3 (or ogg), includes both sides, correct filename/folder.
- Transcript includes both speakers, timestamps, header; readable.
- Metadata JSON present and well-formed.

## Definition of done
A completed call auto-produces all four artifacts with no manual steps.
