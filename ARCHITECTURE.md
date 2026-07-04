# Architecture

_Full document written in Phase 10. See [`FINAL_TECHNICAL_DOCUMENT.md`](FINAL_TECHNICAL_DOCUMENT.md) for the decision log._

This project uses a simple scenario-guided voice bot rather than a complex multi-agent
architecture. Each call is driven by a saved scenario card (persona, goal, hidden details,
speaking style, staged edge-case behavior, stop condition). Python manages call flow and the
authorized-number guard, while an **OpenAI Realtime** speech-to-speech session bridged to
**Twilio** holds the live conversation — handling turn-taking, transcription, and speech
natively. This deviates from the PRD's local STT/TTS default because the rubric gates on voice
lucidity and the PRD permits paid services where quality-critical.

**Module deltas vs. PRD §7:** `transcriber.py` / `tts.py` collapse into the Realtime session;
`patient_brain.py` is a prompt-builder (scenario → Realtime instructions), not a per-turn LLM
caller. Everything else follows the PRD structure.
