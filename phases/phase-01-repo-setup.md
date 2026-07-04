# Phase 01 — Repo Setup & Config

**Status:** ✅ Done (TDD — 36 tests green; FR1 guard verified via demo)
**Depends on:** none
**Maps to PRD:** Phase 1 (+ config.py auth guard from FR1)

## Goal
Create the repository skeleton and a `config.py` that loads/validates environment and — critically — refuses to call any number except the authorized test line.

## Scope (in)
- Directory structure per PRD §7.
- `.env.example` (PRD §8.2) and `.gitignore` (PRD §8.3).
- `config.py`: load env, validate required vars, normalize + validate `TARGET_PHONE_NUMBER`.
- `utils.py`: phone normalization, folder creation, JSON read/write, timestamp formatting.
- `requirements.txt` (twilio, websockets/async server, openai, python-dotenv, etc.).

## Scope (out)
- No telephony, no Realtime, no scenarios yet.

## Tasks
1. Create tree:
   ```
   README.md ARCHITECTURE.md BUG_REPORT.md CALL_SUMMARY.md
   .env.example .gitignore requirements.txt
   src/{main,call_runner,patient_brain,recorder,transcript_builder,utils,config}.py
   scenarios/scenarios.json   calls/   docs/{loom_links,iteration_notes}.md
   ```
   (transcriber.py / tts.py intentionally omitted — see FINAL_TECHNICAL_DOCUMENT.md; note this in ARCHITECTURE.md.)
2. Write `.env.example` from PRD §8.2 (Twilio + OpenAI Realtime + app settings; drop local WHISPER/PIPER vars, keep OPENAI_API_KEY, add OPENAI_REALTIME_MODEL, keep PUBLIC_WEBHOOK_URL / PUBLIC_MEDIA_STREAM_URL).
3. `.gitignore`: `.env *.key *.pem __pycache__/ .venv/ venv/ .env.local .DS_Store calls/*/recording.*` (decide whether to commit recordings — likely yes for submission, so DON'T ignore them; confirm in Phase 10).
4. `config.py`:
   - `normalize_phone(s)` → strip spaces, dashes, parens.
   - `AUTHORIZED_TARGET = "+18054398008"`.
   - On load, if normalized `TARGET_PHONE_NUMBER != AUTHORIZED_TARGET` → raise/refuse with a clear message **before** any provider call.
   - Expose typed constants (max seconds, output dir, model names, recent turns limit).
5. `utils.py`: small helpers only.

## Acceptance criteria
- Repo tree exists and is clean.
- Importing `config` with a wrong `TARGET_PHONE_NUMBER` raises a clear refusal error.
- Importing `config` with `+1-805-439-8008` (any format) normalizes to `+18054398008` and succeeds.
- `.env` is git-ignored; `.env.example` is committed.

## Definition of done
Guard is provably enforced (a quick unit check or `python -c` demo), structure matches the plan, ready for Phase 02.
