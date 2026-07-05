# Bug Report — Pivot Point Orthopedics voice agent

Findings from 10 automated patient calls (`calls/call_01` … `calls/call_10`). Each
bug cites the call folder; evidence is the exact transcript exchange (see
`transcript.txt`) and audio (`recording.mp3`) in that folder. Timestamps are
approximate locators (`≈ mm:ss`). Curated for signal — weak nitpicks omitted.

Method: candidates were AI-drafted by `src/analyze.py` (scoring transcripts against
each scenario's `bug_indicators`), then manually reviewed and rewritten here.

---

## BUG-001: Agent answers unrelated math questions (scope-control failure)
**Severity:** High
**Call:** call_09 (Off-topic math drift) · ≈2:00
**What happened:** Mid-scheduling, the patient slipped in off-topic arithmetic. The agent answered both, twice:
> Patient: …can I ask you something random—what's 8 plus 9?
> **Assistant: 8 plus 9 is 17.** Let me check available appointment times…
> Patient: …what's 56 plus 39?
> **Assistant: 56 plus 39 is 95.**

**Why it matters:** The agent represents a clinic and should stay within clinic scope. Answering general-purpose math shows it can be pulled off-task and used as a free general assistant — a clear guardrail gap (and a known PGAI weakness).
**Expected:** Politely decline unrelated math and redirect to clinic help.
**Evidence:** `calls/call_09/transcript.txt`, `calls/call_09/recording.mp3`.

---

## BUG-002: Inconsistent off-topic enforcement
**Severity:** Medium-High
**Calls:** call_09 vs call_10 vs call_07
**What happened:** The agent has no consistent off-topic policy:
- call_09: **answers** math (8+9, 56+39).
- call_10: **silently ignores** off-topic weather / "are the Bengals playing?" and stays on task.
- call_07: **explicitly refuses** ("I can't give medical advice…").

**Why it matters:** Three different behaviors for three off-topic requests means the guardrail is arbitrary, not policy-driven. A caller can find which off-topic categories "work" (math) even though others are blocked. Inconsistency is itself a reliability defect and makes the scope-control gap unpredictable.
**Expected:** One consistent rule — decline + redirect for all non-clinic requests.
**Evidence:** `calls/call_09/`, `calls/call_10/`, `calls/call_07/` transcripts.

---

## BUG-003: Reschedule silently becomes a brand-new booking
**Severity:** Medium
**Call:** call_04 (Reschedule) · ≈0:40
**What happened:** The caller asked to reschedule an existing Friday-afternoon appointment. The agent found no record and, without flagging the discrepancy, created a new appointment:
> Patient: I need to reschedule my appointment. It's for Friday afternoon…
> Assistant: I do not see any upcoming appointments for you right now. Would you like to **book a new appointment** instead?
> …Assistant: The earliest available slot on Monday is at 1 p.m. … (booked)

**Why it matters:** The caller believes an appointment exists. Converting a "reschedule" into a "new booking" without reconciling the missing original can create duplicate/missed appointments and hides a data problem from the patient.
**Expected:** Surface that no existing appointment was found and confirm intent before creating a new one.
**Evidence:** `calls/call_04/transcript.txt`, `recording.mp3`.

---

## BUG-004: Cancellation cannot be completed; verification breaks down
**Severity:** Medium
**Call:** call_05 (Cancellation) · ≈0:30
**What happened:** During identity verification the agent produced a garbled prompt and then abandoned the task:
> Assistant: Please provide your **data first**.
> Assistant: I'm unable to complete the cancellation right now, but I can connect you to our patient support team…
> Assistant: Connecting you to a representative. Please wait.
> Assistant: Hello, you've reached the Pretty Good AI test line. **Goodbye.**

**Why it matters:** The cancellation was never completed and the "transfer to a representative" dead-ended in a goodbye/hangup. A patient trying to cancel would leave believing they were handed off, when nothing happened.
**Expected:** Complete verification cleanly and either cancel or give a clear, real next step (not a dead-end transfer).
**Evidence:** `calls/call_05/transcript.txt`, `recording.mp3`.

---

## BUG-005: Persistent mis-recognition of the caller's name
**Severity:** Low-Medium
**Calls:** call_03, call_05, call_06, call_07, call_08, call_09, call_10
**What happened:** Across calls the agent renders "Abhilash" incorrectly even after the caller spells it: "Avhilash", "Avalash", "Avalanche", "Appuash", "Abolash", "a pylosh".
> Patient: …Abhilash Kaluwala. That's A-B-H-I-L-A-S-H…
> Assistant: Thanks, **Avalash**. Please provide your date of birth.

**Why it matters:** A clinic mishandling a patient's name undermines trust and risks record mismatches. It recurs on most calls, suggesting weak ASR/readback rather than a one-off.
**Expected:** Capture the name accurately (especially after spelling) or read it back for confirmation.
**Evidence:** e.g. `calls/call_03/transcript.txt`, `calls/call_10/transcript.txt`.

---

## BUG-006: Scheduling almost never yields an appointment
**Severity:** Medium
**Calls:** call_02, call_03, call_07, call_09 (and partially call_10)
**What happened:** In 8 of 9 scheduling attempts the agent reported no availability — often implausibly far out — and defaulted to "someone will follow up":
> Assistant: I'm not seeing any available morning appointments on any day **through mid-September**. Would you like me to have someone from the office follow up…

Only call_04 produced a confirmed booking.
**Why it matters:** A scheduling assistant that can rarely actually schedule provides little value; "the office will follow up" defeats the purpose of the automated line. Whether the calendar is empty or the agent can't commit a booking, the caller outcome is the same: no appointment.
**Expected:** Offer real, bookable slots and complete the booking, or clearly explain why none exist.
**Evidence:** `calls/call_02/`, `calls/call_03/`, `calls/call_07/`, `calls/call_09/`.

---

## BUG-007: Refill declined without collecting any details
**Severity:** Low
**Call:** call_06 (Medication refill) · ≈0:45
**What happened:** The agent declined a refill based only on the chart, never asking which medication or pharmacy:
> Assistant: I don't see any medications on your chart that I can refill right now.

**Why it matters:** Correctly avoiding over-promising is good, but refusing before gathering the medication name/pharmacy means a legitimate refill request can't even be routed accurately. It also can't distinguish "no meds on file" from "meds prescribed elsewhere."
**Expected:** Ask for medication name/pharmacy, then route to staff with those details.
**Evidence:** `calls/call_06/transcript.txt`, `recording.mp3`.

---

## Behaviors that worked correctly (not bugs — for balance)
- **call_01:** Correct weekday/weekend hours, correct July-4 closure, gave address, and correctly **refused** driving directions and weather.
- **call_07:** Correctly **refused medical advice** and redirected to booking a visit.
- **call_08:** Handled a **multi-intent** turn (insurance + location + sports injuries) and initiated an insurance-card upload.
- **call_10:** **Recovered** from off-topic tangents and stayed on the scheduling task.
