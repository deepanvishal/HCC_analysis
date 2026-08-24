# Assumptions

Extracted from methodology.md section 9. That section is the source; this file
is the working copy the scripts and reviews refer to.

**Blocking assumptions must be resolved before any result is circulated.**

| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | The illness-detail table carries every position, not just the first | **Confirmed** — up to 36 observed. Full check in validation V1–V3 | Analysis not possible; deliverable becomes the data-gap finding |
| A2 | Provider identifier is an individual clinician | **Confirmed** by data owner | Scores would describe practices, not people |
| A3 | Setting can be told from the place-of-service code | **Confirmed** — IP / OP / F | Cannot separate office from hospital |
| A4 | The commercial book mixes exchange and employer-sponsored | **Confirmed** | Already handled by reporting separately |
| A5 | No retrospective chart-review or health-assessment records in this data | **Assumed, not verified** | Doctors graded on work done by the plan's own coders. **Highest residual risk** |
| A6 | Patient identifiers are stable across years | Unverified — validation V5 | False drops |
| A7 | Both years are equally complete | Unverified — validation V4 | Every doctor looks worse in year two |
| A8 | Diabetes does not meaningfully resolve in this population | Clinically sound | Some drops are recoveries, not failures |
| A9 | The chronic-condition reference list is a reasonable stand-in for "should not disappear" | Approximate | Overstates the count of conditions that ought to persist |
| A10 | The visit link between the two claim tables is reliable | Unverified — validation V6 | Illnesses attached to the wrong visits |

---

## Which Gate 1 check tests which assumption

| Assumption | Tested by | Script |
|---|---|---|
| A1 | V1, V2, V3 | `03_v1_sequence_values.sql`, `04_v2_dx_per_claim_line.sql`, `05_v3_seq1_vs_pri_icd9_dx_cd.sql` |
| A6 | V5 | `07_v5_member_id_stability.sql` |
| A7 | V4 | `06_v4_year_completeness.sql` |
| A10 | V6 | `08_v6_join_integrity.sql` |

A2, A3, A4 are confirmed but not independently tested here. A5, A8, A9 are not
testable by any check in the validation plan.

**A5 is the highest residual risk and no check closes it.** validation.md
records the one partial test available: retrospective submissions arrive in
batches, clustered before deadlines and detached from any visit, so a
month-by-month count would show that shape if it exists. Absence of the pattern
is not proof of absence. Closing A5 requires an answer from whoever owns risk
adjustment. See `open_questions.md`.

---

## Status changes

Record any change to a status here, with the evidence and the date. Do not edit
a status in the table above without adding a line below.

| Date | Assumption | From | To | Evidence |
|---|---|---|---|---|
| | | | | |
