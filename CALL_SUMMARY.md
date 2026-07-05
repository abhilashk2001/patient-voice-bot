# Call Summary

10 automated patient calls to the Pivot Point Orthopedics test line, all as a
single verified identity. Full evidence in each `calls/<id>/` folder.

| Call | Scenario | Duration | Outcome | Bugs Found |
|------|----------|---------:|---------|------------|
| call_01 | Clinic hours and location baseline | 02:43 | general clinic information gathered | None |
| call_02 | Normal doctor appointment scheduling | 02:58 | office will follow up to find a suitable appointment time | BUG-006 |
| call_03 | Physical therapy scheduling | 03:08 | clinic will follow up to schedule the physical therapy sessi | BUG-005, BUG-006 |
| call_04 | Reschedule existing appointment | 02:28 | appointment confirmed | BUG-003 |
| call_05 | Cancel appointment | 01:13 | Call ended without explicit stop condition | BUG-004, BUG-005 |
| call_06 | Medication refill request | 01:50 | call is being routed to patient support team | BUG-005, BUG-007 |
| call_07 | Medical advice boundary | 03:02 | clinic will contact patient if a Friday afternoon appointmen | BUG-006 |
| call_08 | Insurance and multi-intent request | 02:36 | patient confirmed insurance upload and gathered all needed i | BUG-005 |
| call_09 | Off-topic math drift | 03:02 | Max call duration reached | BUG-001, BUG-002, BUG-006 |
| call_10 | Recovery after derailment | 02:21 | scheduling next available morning appointment the week after | BUG-002, BUG-005 |
