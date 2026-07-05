# Loom links

Two recordings are required for submission (free Loom account, each ≤ 5 min).

## 1. Walkthrough — approach & what you built
_How the bot works: scenario cards → Realtime patient → Twilio bridge → recordings/
transcripts → bug report. Show a live/played-back call and the artifacts._

- Link: **<paste Loom URL here>**

## 2. AI-assisted debugging screen recording
_Show iteratively prompting the AI to debug and fix code — e.g. the OpenAI Realtime
GA `beta_api_shape_disabled` fix, the recording 404 (poll on status), or the
fixed-identity / on-file-phone verification fixes._

- Link: **<paste Loom URL here>**

---

### Suggested talking points
- The voice-lucidity gate → why Twilio + OpenAI Realtime (not a cascade).
- The fixed-identity insight (verification kept looping until we used the real
  registered name/DOB/on-file number).
- Best bug found: BUG-001 scope-control (agent answered 8+9=17, 56+39=95).
- TDD throughout (139 tests); live calls to verify the bridge.

### Submission form checklist
- [ ] Public GitHub repo link
- [ ] Loom walkthrough link (above)
- [ ] AI-debugging screen recording link (above)
- [ ] Caller number in E.164: **+15138663293**
