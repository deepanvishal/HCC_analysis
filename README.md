# HCC coding consistency

Measures whether providers re-document chronic conditions year over year.
Phase 1: diabetes, Florida, 2023 vs 2024, CMS-HCC V24.

The prior `medicare_analysis` extract kept only the primary diagnosis per claim
line and sees 29% of members with any HCC, which is far too low.
`CLM_LN_X_ICD9_DX` holds every diagnosis position, up to 36 per claim line.
Recovering those positions is the point of this repo.

Read `00_docs/methodology.md` for what is measured and why, and
`00_docs/validation.md` for the four gates. `CLAUDE.md` holds the working
rules.

## Shape

Gate 1 is plain SQL: eleven flat files at the repo root, run by hand in the
BigQuery console, SELECT only, nothing written anywhere (DD-03). There is no
config, no runner, no local runtime of any kind. Table locations are
fully-qualified inline, verified against the prior repo's SQL. Column names
are the attested source names; a wrong one surfaces as BigQuery's
"Unrecognized name" error and is fixed by hand.

## Status

Gate 1 implemented, not run. **Nothing here has been run against live data.**
`00_docs/data_model.md` is stubbed NOT YET VERIFIED until it is rewritten from
the 01_columns.sql result. No extract or analysis code exists, and none is
written until Gate 1 signs off (V1, V3, V6 and V7 must pass).

## Files

```
01_columns.sql                    actual columns and types, all tables
02_row_counts.sql                 row counts and sizes, metadata only
03_v1_sequence_values.sql         V1  multiple diagnosis positions exist
04_v2_dx_per_claim_line.sql       V2  the fan-out is real
05_v3_seq1_vs_pri_icd9_dx_cd.sql  V3  sequence_id 1 matches pri_icd9_dx_cd
06_v4_year_completeness.sql       V4  both years equally settled
07_v5_member_id_stability.sql     V5  identifiers stable across years
08_v6_join_integrity.sql          V6  the visit link holds
09_v7_diabetes_share.sql          V7  what the extra positions add
10_v8_code_mapping.sql            V8  codes map to the condition list
11_value_profiles.sql             value sets for every code column
```

Each file's header carries WHAT / WHY / PASSES / FAILS / ON FAILURE, taken
from `00_docs/validation.md`. Run order, costs, stop points and what to copy
back: `00_docs/run_order.md`.

## Known gaps

- `EMIS_CLAIM_LINE.claim_line_id`, `plc_srv_cd` and `plc_srv_ctg_cd` were
  named in prior docs but never exercised in any query. V3, V6 and V7 all
  depend on the first; if it does not exist, Gate 1 cannot sign off (DD-01).
- `A870800_medicare_analysis_2025_claims` has no confirmed location (Q2) and
  is dropped from Gate 1; `01_columns.sql` still searches for it.
- No value list has been seen for any code column; `11_value_profiles.sql`
  exists for that. The setting groups and the Medicare/commercial split are
  written only after it comes back.
- Open questions, each with what it blocks: `00_docs/open_questions.md`.
