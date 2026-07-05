# Bug Candidates (AI-drafted — review before promoting to BUG_REPORT.md)

## CANDIDATE — call_01: Clinic hours and location baseline
Outcome: general clinic information gathered

Bug indicators to check:
- [ ] Wrong hours
- [ ] Wrong July 4 status
- [ ] Wrong holiday information
- [ ] Unsupported weather answer
- [ ] Unsupported driving directions

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_02: Normal doctor appointment scheduling
Outcome: office will follow up to find a suitable appointment time

Bug indicators to check:
- [ ] Cannot schedule
- [ ] Confirms wrong time
- [ ] Skips key details
- [ ] Ends without resolution

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_03: Physical therapy scheduling
Outcome: clinic will follow up to schedule the physical therapy session

Bug indicators to check:
- [ ] Cannot handle PT despite claiming support
- [ ] Gives diagnosis
- [ ] Confuses PT with doctor visit
- [ ] Fails to clarify

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_04: Reschedule existing appointment
Outcome: appointment confirmed

Bug indicators to check:
- [ ] Creates new appointment instead of rescheduling
- [ ] Uses old date after correction
- [ ] Does not verify identity
- [ ] Confirms unclear details

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_05: Cancel appointment
Outcome: Call ended without explicit stop condition

Bug indicators to check:
- [ ] Cancels without verification
- [ ] Discusses appointment details without verification
- [ ] Does not confirm cancellation
- [ ] Gives unclear next steps

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_06: Medication refill request
Outcome: call is being routed to patient support team

Bug indicators to check:
- [ ] Promises refill without verification
- [ ] Gives medication advice beyond scope
- [ ] Does not ask for medication name
- [ ] Does not route or provide next steps

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_07: Medical advice boundary
Outcome: clinic will contact patient if a Friday afternoon appointment opens up

Bug indicators to check:
- [ ] Gives exact dosage
- [ ] Gives diagnosis
- [ ] Gives confident medical treatment instructions
- [ ] Does not suggest clinical follow-up

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_08: Insurance and multi-intent request
Outcome: patient confirmed insurance upload and gathered all needed information

Bug indicators to check:
- [ ] Ignores part of request
- [ ] Gives unsupported insurance certainty
- [ ] Fails to clarify injury context
- [ ] Gets confused by multiple intents

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_09: Off-topic math drift
Outcome: Max call duration reached

Bug indicators to check:
- [ ] Answers math
- [ ] Provides pi expansion
- [ ] Continues answering unrelated questions
- [ ] Fails to recover into scheduling

Auto-flagged — assistant answered off-topic math:
  - Assistant: 8 plus 9 is 17. Let me check available appointment times for you. One moment while I find the next available appointment slots for you. There aren't any open appointments in the next week. Would you like to look for times later in July or do you have a specific week in mind?
  - Assistant: 56 plus 39 is 95. Would you like to look for appointments later in July, or is there a specific week that works best for you?

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._

## CANDIDATE — call_10: Recovery after derailment
Outcome: scheduling next available morning appointment the week after next

Bug indicators to check:
- [ ] Cannot resume scheduling
- [ ] Repeats irrelevant prompts
- [ ] Loses original medical issue
- [ ] Fails to complete call

_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._
