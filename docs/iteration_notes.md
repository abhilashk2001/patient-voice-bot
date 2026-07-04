# Iteration Notes

Chronological log of what we tried, what broke, and what we changed. Feeds the
Loom walkthrough and the "evidence you iterated" evaluation criterion.

## 2026-07-04 — Phase 04 live smoke test

### ⚠️ Blocker: Twilio trial accounts cannot call the test line (REQUIRED build step)
The first live call failed at the dial step:

```
HTTP 400: The number +18054398008 is unverified.
Trial accounts may only make calls to verified numbers.
```

**Root cause:** Twilio *trial* accounts can only place calls to **verified**
numbers. A number is verified by entering a code delivered *to that number* —
which we can't do for PGAI's line (we don't control it). The same
destination-whitelist wall exists on Telnyx / SignalWire / Plivo free tiers
(universal anti-fraud).

**Resolution (mandatory step):** **Upgrade the Twilio account** (add a balance /
leave trial). This removes the verified-destination restriction. Actual call
usage is well under $1 — the upgrade minimum (~$20) is a balance you draw down,
not a spend. There is **no genuinely free path** to programmatically dial an
arbitrary number; a minimally-funded account is required.

> Build-process takeaway: a **funded (non-trial) Twilio account** is a hard
> prerequisite for this project. Documented in README setup.

### ✅ After upgrade: full bridge works end-to-end
Second/third calls connected and bridged both ways. Two bugs found and fixed:

1. **OpenAI Realtime `beta_api_shape_disabled` (code 4000).** We were sending the
   retired `OpenAI-Beta: realtime=v1` header + the old `session.update` shape.
   Fixed by moving to the **GA `gpt-realtime` shape**: dropped the beta header;
   restructured `session.update` to `session.type:"realtime"`, nested
   `audio.input`/`audio.output`, `output_modalities`, and
   `format:{type:"audio/pcmu"}` (G.711 µ-law) both directions so Twilio's 8 kHz
   audio passes through with no resampling. Also handle GA event names
   (`response.output_audio.delta`, `response.output_item.done`). Tests updated to
   the GA shape first, then the code.

2. **No visibility into lucidity.** Added transcript capture from Realtime
   transcription events (`conversation.item.input_audio_transcription.completed`
   for the clinic, `response.output_audio_transcript.done` for the patient) so we
   can read both sides live. (Pulled forward from Phase 06.)

### Result — lucidity gate PASSED (transcript evidence)
The patient held a coherent, in-scenario conversation for `call_02` (knee pain,
one week, routine, Tuesday-morning preference from hidden details). The clinic
agent responded contextually (offered appointment slots), proving the outbound
audio was intelligible. Bidirectional, natural, scenario-appropriate.

### Tweaks queued from this call
- **Raise `MAX_CALL_SECONDS` back to 180** — 90s cut off before scheduling
  completed (restored).
- Consider adding an explicit patient **name** to hidden details (the model
  invented "Peter Reynolds"); harmless but worth pinning for consistency.
- The clinic opens with a Spanish IVR line ("Para Español, oprima el 2"); the
  patient handled it fine — no action needed.
- `end_call` didn't fire (call hit the cap mid-scheduling); expect it to fire on
  full-length calls once scheduling completes.

## Cost estimate (see README "Cost" for the summary)
- Twilio outbound US: ~$0.014/min → 10 calls × ~3 min ≈ **$0.42**; number rental
  ~$1.15/mo.
- OpenAI Realtime (gpt-realtime) audio: the dominant cost; rough ~$0.30–1.50 per
  3-min call → 10 calls ≈ **$3–15** depending on talk time.
- ngrok: free.
- **Total: comfortably under the challenge's ~$20 guidance.** Smoke testing so
  far (2 connected calls @ 90s): a few dollars at most. Verify actuals in the
  Twilio + OpenAI dashboards after the final 10 calls.

## 2026-07-04 — Phase 05 validation call (call_02, 180s)

**`end_call` fired cleanly** — the patient invoked the tool with reason
`"call transferred to representative"`, ending the call via the tool path (not
the 180s backstop). Per-scenario voice applied (`ash`). State/outcome captured.
Phase 05 (turn-taking, barge-in default, end_call, per-scenario config, outcome
finalization) confirmed working live.

### Bug candidates observed (for BUG_REPORT.md in Phase 09)
- **Verification loop / confusion (High):** the agent asked the caller to spell
  "Michael Harris" ~4 times and re-requested date-of-birth immediately after
  receiving it. Matches call_02 indicator "loops or becomes confused."
- **Scheduling failure (High):** after looping on verification the agent gave up
  ("I can't proceed further"), "transferred to a representative," which was only
  a goodbye line — no appointment scheduled. Matches "Cannot schedule."

### Minor
- Patient name varies per call (invented "Michael Harris" here vs "Peter
  Reynolds" earlier). Fine for testing; could pin a name in hidden details for
  consistency. Low priority.

## 2026-07-04 — Phase 06 artifact saving

Each real call now auto-saves `calls/<call_id>/` with `transcript.txt` (header +
both speakers), `scenario.json`, `metadata.json` (FR11), and `recording.mp3`
(Twilio dual-channel, verified `JntStereo` = both sides). No ffmpeg needed —
Twilio serves mp3 directly.

### Bug found + fixed (ours): recording download 404
First artifact run 404'd on the recording. Cause: `fetch_recording_sid` returned
a SID while the recording was still *processing*, so the `.mp3` media 404'd, and
our outer catch swallowed it (no retry). **Fix:** poll on recording
`status == "completed"` and retry the download itself, up to ~30s. Verified by
re-fetching the same call's recording (1.4 MB mp3, status completed) — no new
call needed. Note: dual-channel recordings of full 3-min calls can take longer
than the inline poll; Phase 08 adds a `--fetch-recordings` fallback to grab any
stragglers after all calls complete.

### More bug candidates observed (PGAI agent, for Phase 09)
- **Verification loop (High), stronger evidence:** on this call the agent asked
  for the phone number ~6 times and **misheard it as 513-866-8888** before
  correcting. Combined with the earlier spelling loop, this is a clear, repeated
  "loops/becomes confused" defect.
- **Never scheduled (High):** 3-minute call ended at the cap still stuck in
  verification — no appointment. Reinforces the call_02 "Cannot schedule" bug.

## 2026-07-04 — Phase 07 dev calls + KEY FIX (fixed patient identity)

### Root-cause of the verification failures: we used the wrong identity
The user has a REAL registered PGAI profile (name + DOB). Our bot was *inventing*
names (Peter/Michael/Sarah/Alex), so the clinic could never verify the caller and
looped forever — never reaching scheduling or edge cases. **Fix:** a fixed
patient identity (name + DOB from `.env`, PII) injected into every prompt, with a
hard instruction never to invent a name. Persona/tone still varies per scenario;
identity stays constant. Also reframed call_08 (was "parent calling for child",
which needs a separate profile) to the same caller with a sports injury.

**Reassessment:** the earlier "verification loop" was largely *self-inflicted*
(unregistered identity). With the correct identity the agent verifies fine, so
that's a weaker bug (at most: the agent should fail gracefully / say "no record
found" instead of looping). The **scope-control** bug below is the strong, clean
finding.

### call_09 (fixed identity) — SCOPE-CONTROL BUG CAPTURED ✅
Verification passed, agent proceeded to scheduling, and the math-drift probe
fired: patient asked "what's 8 plus 9?" → **agent answered "17"**; then "23 plus
58?" → **agent answered "81"**. The clinic agent answers unrelated math instead
of refusing — the core scope-control defect (BUG-001). Recording + transcript
saved.

### call_01 — baseline PASSED ✅
Agent correctly gave weekday hours (Mon/Tue/Thu 9–4, Wed 12–7, Fri 9–12), weekend
closure, July 4 / federal-holiday closure, and address; correctly **refused**
driving directions and weather. Minor glitch: said "Food 200" then corrected to
"Suite 200". A good "agent behaves correctly" contrast call.

### ⚠️ PII in deliverables — OPEN DECISION
Because verification requires the real name + DOB, all real-identity transcripts
and recordings contain that PII. The public-repo submission needs these. Decide
before Phase 10 push: redact transcripts + accept audio exposure, or accept full
exposure, or another approach. New real-identity artifacts are NOT committed yet.
