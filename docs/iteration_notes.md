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
