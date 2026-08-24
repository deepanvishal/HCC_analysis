# Data decisions

Every choice that could have gone another way and changes a number. Numbered,
never renumbered, never deleted. A decision that turns out wrong gets a status
change and a superseding entry, so the reasoning stays visible.

Methodology Step 16: every choice is written down beside the result, because
someone will ask "how do you know?" about each number and the answer needs to
be on the page already.

## Format

```
## DD-nn  Short title

**Decision:** what was chosen, in one sentence.

**Alternatives:** what else was available, and what each would have changed.

**Rationale:** why this one. Evidence, not preference.

**Affects:** which figures move if this is wrong.

**Raised by:** script, check, or person. **Date:** YYYY-MM-DD.

**Status:** Active | Superseded by DD-nn | Reversed
```

## What belongs here

- Any column name corrected by hand after a BigQuery error, with the wrong and the right name
- A table resolved to a location the methodology did not specify
- Mapping raw business line codes to Medicare and commercial
- Which place-of-service codes count as office, hospital outpatient, inpatient
- Which codes are excluded as laboratory, equipment, ambulance, dental
- The year window, if V4 moves it off 2023/2024
- The minimum panel size, once the observed distribution is known
- Whether the two-mention rule uses separate dates or separate visits
- Which control condition runs alongside diabetes
- Any threshold changed from the value in methodology.md or validation.md

## What does not belong here

Facts about the data go in `data_model.md`. Things nobody has answered yet go
in `open_questions.md`. Assumption status changes go in `assumptions.md`.

---

## DD-01  V3 and V7 read the top-line diagnosis from EMIS_CLAIM_LINE, not the A870800 extract

**Decision:** the top-line comparison field for V3 and for V7's top-line arm is
`EMIS_CLAIM_LINE.pri_icd9_dx_cd`, joined to the diagnosis table at claim-line
grain within EMIS.

**Alternatives:** join `A870800_medicare_analysis_2025_claims` to
`CLM_LN_X_ICD9_DX`, as originally scripted. Not possible: methodology
Appendix A records that the extract does not carry `claim_line_id`, and the
operator-confirmed column list agrees, so no claim-line-grain join from it
exists. A fuzzy join on member and service date would attach diagnoses to the
wrong lines, which is exactly the failure V6 exists to prevent. The extract's
location is also unresolved (Q2) and its name suggests 2025 coverage while the
window is 2023-2024.

**Rationale:** `pri_icd9_dx_cd` on the source claim line is the same top-line
fact the extract carried forward, at the grain the comparison needs, in a table
whose location is confirmed. It also makes V7 a same-population comparison:
both arms count over identical claim lines, so the difference measures only
the extra positions.

**Depends on:** `EMIS_CLAIM_LINE.claim_line_id` — one of the three names with
no seeded default, never exercised in any query, flagged highest-risk. The
remedy for the extract's missing join key rests on this unconfirmed join key.
If it does not resolve, V3 and V7 are blocked (and V6, which needed it
regardless), and Gate 1 cannot sign off. `05_v3_seq1_vs_pri_icd9_dx_cd.sql`,
`08_v6_join_integrity.sql` and `09_v7_diabetes_share.sql` each carry this
dependency in their header; the failure surfaces as BigQuery's
"Unrecognized name: claim_line_id" error (DD-03).

**Comparability:** the 29% any-HCC figure came from the curated extract under
its own filters — `summarized_srv_ind = 'Y'`, `duplicate_ind = 'N'`, dental
excluded via `med_cost_ctg_cd`, DPPO excluded via `ntwk_srv_area_id`,
footprint submarkets only. Raw `EMIS_CLAIM_LINE` applies none of them. The
difference between V7's two arms stays valid because both arms share one
population; the absolute `pri_icd9_dx_cd`-only share is not the 29% and must
not be presented as its replacement.

**Affects:** V3 agreement rate; V7 shares and the difference between its two
arms. The 29% any-HCC figure from the old extract remains context only.

**Raised by:** operator-supplied schema, 2026-08-24 session. **Date:** 2026-08-24.

**Status:** Active

**Correction (2026-08-24):** the extract was rebuilt after Gate 1 was written
and now carries `claim_line_id`; its location is also now known (Q2,
answered). The no-join-key premise above no longer holds. The retarget was
correct at the time on the grounds listed - no join key in the table as it
then existed, location unknown - and V3, V6 and V7 stay pointed at
EMIS_CLAIM_LINE. The rebuilt extract is the base table of the Step 1 EDA
(`eda_*.sql`). Original entry unedited above.

## DD-02  Diabetes family derived from ICD-10 prefix E08-E13 when the mapping has no description

**Decision:** when `HCC_ICD_Mapping_2025` has no description column, the
diabetes HCC set is the distinct `HCC_v24` values reached by diagnosis codes
starting E08-E13, and the diabetes code set is every code mapping to those
HCCs.

**Alternatives:** hardcode the CMS-HCC V24 diabetes HCC numbers (asserts
values the table cannot confirm and hides a mapping-table defect); description
match (preferred, and still tried first, but the confirmed columns are
`diagnosis_code`, `HCC_v24`, `HCC_v28` only).

**Rationale:** E08-E13 is the ICD-10 diabetes mellitus chapter, verifiable
against the published code set. The derivation is returned by 09 Query A with
the evidence per HCC, so the derived set is confirmed rather than trusted
(Q10). E12 is unused in ICD-10-CM and is included
only so a WHO-coded row would not slip past.

**Affects:** every diabetes figure in V7 and downstream.

**Raised by:** operator-supplied schema, 2026-08-24 session. **Date:** 2026-08-24.

**Status:** Active

## DD-03  Gate 1 as plain SQL, drop Python

**Decision:** Gate 1 is eleven flat SQL files at the repo root, run by hand in
the BigQuery console. All Python is deleted: config, the resolver,
schema_map, and the fourteen discovery scripts.

**Alternatives:** keep the Python and set up the office machine (gcloud, ADC,
an interpreter with the SDK) — rejected, the machine will not be set up; a
runner script or wrapper — rejected, flat files only.

**Rationale:** the office machine has no gcloud, no ADC, and a PATH default
interpreter without the SDK. Every Gate 1 check is a GROUP BY, a JOIN or a
COUNT — no calculation needs Python. BigQuery's own error message is a better
column resolver than anything we would write: "Unrecognized name: x" says
exactly what is wrong, and names are fixed by hand as they surface.

**Consequences:** no CSV outputs or verdict files; results are saved from the
console and recorded in run_log.md. Column names are hardcoded source names;
the seeded-resolver layer is gone. Table locations are hardcoded
fully-qualified, verified against the prior repo's SQL. DD-01 and DD-02 carry
forward unchanged; their implementations now live in 05, 08 and 09 (DD-01)
and 09 Query A (DD-02). The A870800 extract is dropped from Gate 1 entirely:
after DD-01 its only remaining use was one specialty value profile, which now
reads PROVIDER_DM instead. Its location remains open as Q2 and 01_columns.sql
still searches for it.

**Affects:** how Gate 1 runs, not what it checks. Every criterion is carried
across unchanged from validation.md.

**Raised by:** operator, 2026-08-24 session. **Date:** 2026-08-24.

**Status:** Active

## DD-04  Membership dates are eff_yr and eff_mo, cast from STRING

**Decision:** every membership date reference reads `eff_yr` and `eff_mo`,
each `CAST(... AS INT64)` before any comparison. All
`EXTRACT(YEAR FROM eff_dt)` predicates on the membership table are replaced.

**Alternatives:** none once the schema is known; `eff_dt` does not exist on
the curated table.

**Rationale:** `eff_dt` was asserted in error. The prior repo splits the raw
date during its build (test_sql.sql: `extract(year from eff_dt) as eff_yr`);
`eff_dt` exists only on the raw EMIS_MEMBERSHIP, and the curated
A870800_medicare_analysis_membership carries `eff_yr` and `eff_mo`, both
stored as STRING. The prior repo casts both to INT64 before comparing; this
repo does the same. Corrected against the prior repo's build SQL, not
inferred.

**Affects:** V5 (all three queries: the grain probe's distinct_months now
counts distinct `eff_mo` values, the presence pivot, the claims
cross-check) and V7 (the 2023 membership denominators in Queries B, C, D).

**Raised by:** operator, against the prior repo's build SQL. **Date:** 2026-08-24.

**Status:** Active

## DD-05  Membership column names come from the build SQL, not assertion

**Decision:** the curated A870800_medicare_analysis_membership is treated as
having exactly the columns its build SQL emits (test_sql.sql lines 123-140):
`member_id`, `eff_yr`, `eff_mo`, `age_nbr`, `gender_cd`, `mbr_county_cd`,
`mbr_state`, `mbr_submarket`. Every membership reference in Gate 1 is
corrected to this list.

**Alternatives:** none; the build's SELECT list is the table.

**Rationale:** four asserted membership columns were wrong. `eff_dt` (already
corrected, DD-04). `state_postal_cd` - a column on ZIP_X_ST_X_COUNTY used
inside a build CTE, never emitted; the emitted column is `mbr_state`.
`medical_ind` - not a column; a build filter (`where m.medical_ind = 'Y'`),
so every row already satisfies it. `business_ln_cd` - not a column; also a
build filter (`business_ln_cd IN ('CP','ME')`), so both books are present,
mixed, with no way to tell them apart. All membership names now come from the
build SQL rather than assertion.

**Affects:** V7's Florida filter (now `mbr_state`); the value profiles
(medical_ind dropped - nothing to profile; state profile now `mbr_state`);
Q8 and Q20. The business_ln_cd consequence is bigger than a rename and is
decided in DD-06.

**Raised by:** operator, against test_sql.sql lines 123-140. **Date:** 2026-08-24.

**Status:** Active

## DD-06  Medicare only; business line removed from Gate 1

**Decision:** the analysis is scoped to Medicare, and business line is out of
Gate 1 entirely - no split, no value profile, no per-book bands, no both-books
member count. V7 reports a single figure: diabetes share from pri_icd9_dx_cd
versus every position, and the difference between them, with no band
assignment. Membership is used for coverage months only.

**Alternatives:** split the membership denominator by book - impossible, the
curated table carries no book column (DD-05); join membership to claims or to
the raw EMIS_MEMBERSHIP inside Gate 1 to label books - adds a join whose
integrity V6 has not yet established, to a gate whose job is establishing it.

**Rationale:** the curated membership cannot distinguish Medicare from
commercial: its build applies `business_ln_cd IN ('CP','ME')` as a filter
without keeping the column, so both books are present, mixed, unlabelled. Any
book split built on it would be a guess. The Medicare scope is applied on
claims - `EMIS_CLAIM_LINE.business_ln_cd` - or from the raw
`edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_MEMBERSHIP`, which has the
column, when the extract is built. Which value means Medicare still needs
confirming (Q9).

**Consequences:** V7's per-book pass bands from validation.md (25-30%
Medicare, 8-12% commercial) are dropped - the one recorded deviation from the
validation criteria. V7's absolute level has no benchmark and is a
data-quality figure over a mixed population, not a reportable prevalence; the
difference between its two arms is the check. The never-blend rule is
unaffected for everything downstream: once the claims-side scope exists, no
reported figure blends the books.

**Affects:** V7 (single row, bands dropped); 11_value_profiles (no
business_ln_cd profile); Q9 rescoped to the extract.

**Raised by:** operator. **Date:** 2026-08-24.

**Status:** Active
