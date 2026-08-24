# Open questions

Things nobody has answered yet. Each one blocks something specific, named here
so it is obvious what stalls if it stays open.

Once answered, the answer moves to `data_model.md` (a fact), `data_decisions.md`
(a choice), or `assumptions.md` (a status change). The question stays here with
a pointer, so nothing looks like it was never asked.

Status: **Open** | **Answered** (with pointer) | **Will not resolve**

---

## Table locations

### Q1. Where is `PROVIDER_DM`?
Named in the task brief and methodology Appendix A with no project or dataset.
`config.T_PROVIDER_DM` currently guesses
`anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.PROVIDER_DM`.
**Blocks:** all provider scoring (methodology steps 12–14).
**Resolved by:** `00_list_tables.py`, which searches both datasets.
**Status:** Open

### Q2. Where is `A870800_medicare_analysis_2025_claims`?
The existing top-line-only extract, named in methodology Appendix A without a
location.
**No longer blocks V3 or V7:** per DD-01 both now read the top-line diagnosis
from `EMIS_CLAIM_LINE.pri_icd9_dx_cd`, since the extract carries no
`claim_line_id` and cannot join at claim-line grain. The extract remains wanted
as reference: it is the source of the 29% any-HCC figure, and its name
suggests 2025 coverage — whether it covers 2023-2024 at all is part of this
question.
**Resolved by:** `00_list_tables.py`.
**Status:** Open

### Q3. Where is `ms_dc_ref_ccir`?
AHRQ CCIR v2026.1, the long-term-condition flag. Named in methodology
Appendix A without a location.
**Blocks:** the "any long-term condition" half of V7 — the figure that compares
against the 29% the old extract reports. `09_v7_diabetes_share.py` measures
diabetes only and says so in its output.
**Status:** Open

---

## Column names

### Q4. Which of the thirteen asserted column names actually exist?
`claim_line_id`, `sequence_id`, `icd9_dx_cd`, `poa_cd`, `member_id`,
`plc_srv_cd`, `plc_srv_ctg_cd`, `med_cost_ctg_cd`, `srv_prvdr_id`,
`epdb_dw_prvdr_id`, `specialty_ctg_cd`, `business_ln_cd`, `srv_start_dt`.

Operator attestation now covers most of them (see the provenance table in
`data_model.md` and `schema_map.DEFAULTS`), with three exceptions that remain
named-but-never-exercised: `claim_line_id` on EMIS_CLAIM_LINE, `plc_srv_cd`,
and `plc_srv_ctg_cd`. Discovery confirmation is still pending for all
thirteen.
**Resolved by:** `01_columns.py`, which writes `01_brief_column_check.csv`
marking each CONFIRMED or ABSENT.
**Status:** Open

### Q5. Does `CLM_LN_X_ICD9_DX` carry a member identifier?
V6 must confirm the member identifier agrees on both sides of the claim-line
join. Without a member column on the illness table that half of the check
cannot run, and V6 reports UNVERIFIABLE rather than passing.
**Update 2026-08-24:** `member_id` was observed on the table in a result grid
and is seeded as a default. Likely closable once `01_columns.py` confirms it.
**Blocks:** Gate 1 sign-off, which requires V6.
**If absent:** another way to verify the join is needed before sign-off.
**Status:** Open

### Q6. Where is the death indicator?
Methodology step 11 requires excluding patients not alive at the end of year
two. No table in Appendix A is identified as carrying date of death, and the
operator-confirmed membership columns do not include one.
**Blocks:** the first fairness gate.
**Status:** Open

### Q7. Where is provider specialty?
Methodology step 14 compares doctors within specialty.
**Update 2026-08-24:** operator attests `specialty_ctg_cd` on `PROVIDER_DM`
and on the A870800 extract. What remains is PROVIDER_DM's location (Q1) and
the value set (`11_value_profiles.py`).
**Blocks:** peer comparison and the shrinkage in step 13.
**Status:** Open

### Q8. Where is member state?
Florida scope, methodology step 5. `09_v7_diabetes_share.py` applies a state
filter only if it resolves a state column, and prints that the figures are
all-states when it cannot.
**Update 2026-08-24:** operator attests `state_postal_cd` on the membership
extract; seeded as the default. Values unverified — `11_value_profiles.py`
profiles them, and the FL filter is only trustworthy once 'FL' is seen there.
**Blocks:** scoping every figure to Florida.
**Status:** Open

---

## Values and mappings

### Q9. Which business line codes are Medicare and which are commercial?
Methodology step 5 requires the two books never be combined.
`09_v7_diabetes_share.py` reports raw business line values and does not assign
them, because guessing here would silently blend the books.
**Blocks:** V7's pass criterion, which has separate bands per book, and every
later figure.
**Becomes:** a numbered decision in `data_decisions.md`.
**Status:** Open

### Q10. Which HCC values are diabetes?
`09_v7_diabetes_share.py` derives the set from the mapping table: by
description match where a description column exists, otherwise by ICD-10
prefix E08-E13 (DD-02 — the confirmed mapping columns carry no description).
It prints the derived HCCs with evidence. The derived set needs confirming
against the CMS-HCC V24 definition.
**Status:** Open

### Q11. Which place-of-service values mean office, hospital outpatient, inpatient?
Methodology A3 records that setting can be told from the place-of-service code
and that IP / OP / F are the values. `plc_srv_cd` and `plc_srv_ctg_cd` are
named in prior docs but never exercised in any query — with
`EMIS_CLAIM_LINE.claim_line_id`, the highest-risk names in the build. No
seeded default; the resolver reports what it finds, and
`11_value_profiles.py` profiles the values.
**Blocks:** the office-only score, which is the doctor-facing measure.
**Status:** Open

### Q12. Which values identify laboratory, equipment, ambulance and dental?
Methodology Appendix A excludes these throughout. V12 in Gate 2 asserts zero
survive.
**Status:** Open

### Q13. Is a 2025-vintage mapping right for 2023 and 2024 service dates?
`HCC_ICD_Mapping_2025` with field `HCC_v24`. Methodology step 7 requires the
same code list for both years, which this satisfies. But codes retired before
the 2025 vintage may be absent from it entirely, which would look like a
patient who got better. V8 measures the unmatched rate; V13 in Gate 2 tests
retired codes directly.
**Status:** Open

---

## Method and scope

### Q14. Are there retrospective chart-review or health-assessment records in this feed?
Assumption A5, the highest residual risk, and no check in validation.md closes
it. If the plan's own coders submit through the same feed, a doctor who records
poorly scores well because someone corrected it behind them.
**Needs:** an answer from whoever owns risk adjustment. This is a person, not a
query.
**Partial test available:** retrospective submissions cluster before deadlines
and detach from any visit, so a month-by-month count would show that shape.
Absence of the pattern is not proof of absence.
**Status:** Open

### Q15. What is the minimum panel size?
Methodology Appendix A gives 30 as a starting point, to be checked against the
observed distribution. `config.MIN_PANEL` holds the provisional value.
**Blocks:** any ranking. No doctor is scored without it.
**Status:** Open

### Q16. Does the two-mention rule use separate dates or separate visits?
Listed as not yet decided in methodology Appendix A.
**Status:** Open

### Q17. Which control condition runs alongside diabetes?
Methodology section 10 proposes amputation status. Not decided.
**Blocks:** V19 in Gate 3.
**Status:** Open

### Q18. Is `anbc-dev-prv-nc-ds` the right billing project?
Carried over from the prior medicare_analysis repo and set in
`config.CLIENT_PROJECT`. Not confirmed for this repo, and this repo reads from
`edp-prod-hcbstorage`, a third project.
**Status:** Open

### Q19. Does the McGuire et al. denominator match ours?
Methodology section 11 records that the comparison to published work rests on
the abstract and summary, not a full reading, and that someone should confirm
the denominator construction — particularly deaths and continuous enrolment —
before the framing is used externally.
**Status:** Open

### Q20. What does `medical_ind` mean, and should membership denominators filter on it?
Operator-confirmed on the membership extract; values unseen. If it flags
medical (vs dental/pharmacy-only) coverage, the denominators in V5 and V7
should probably require it — a member without medical coverage cannot have
claims. No script filters on it yet; `11_value_profiles.py` profiles the
values.
**Blocks:** nothing yet; potentially every denominator once answered.
**Becomes:** a numbered decision in `data_decisions.md`.
**Status:** Open
