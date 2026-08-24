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

## Status

Discovery and structure only. No extract or analysis code exists, and none is
written until Gate 1 passes.

**Nothing here has been run against live data.** `00_docs/data_model.md` is
stubbed NOT YET VERIFIED and stays that way until it is rewritten from real
discovery output.

## Setup

Python 3, `google-cloud-bigquery`, `pandas`. Credentials come from the ambient
environment — application default credentials or
`GOOGLE_APPLICATION_CREDENTIALS`. Nothing is hardcoded and no credential path
appears anywhere in this repo.

Code is authored on one machine and executed on another that holds the
credentials. Scripts are written to run as-is when copied across.

Projects, datasets, the year window and the Florida scope are set at the top of
`config.py`.

## Running discovery

Each script is standalone and rerunnable. Every query is dry-run first; anything
above `config.CONFIRM_GB` (default 50 GB) prompts before it runs. Set
`HCC_YES=1` to accept automatically in a batch run.

```
python 01_discovery/00_list_tables.py
python 01_discovery/01_columns.py
python 01_discovery/02_row_counts.py
python 01_discovery/11_value_profiles.py
```

Then write `00_docs/data_model.md` from `01_discovery/output/01_columns.csv`
and remove its NOT YET VERIFIED banner.

## Gate 1

```
python 01_discovery/03_v1_dx_positions.py            V1  multiple diagnosis positions
python 01_discovery/04_v2_dx_per_claim_line.py       V2  fan-out is real
python 01_discovery/05_v3_seq1_vs_pri_icd9_dx_cd.py  V3  sequence_id 1 matches pri_icd9_dx_cd
python 01_discovery/06_v4_year_completeness.py       V4  both years equally settled
python 01_discovery/07_v5_member_id_stability.py     V5  identifiers stable across years
python 01_discovery/08_v6_join_integrity.py          V6  the visit link holds
python 01_discovery/09_v7_diabetes_share.py          V7  what the extra positions add
python 01_discovery/10_v8_code_mapping.py            V8  codes map to the condition list
python 01_discovery/99_gate1_summary.py              sign-off status
```

Each writes CSV to `01_discovery/output/` and prints its pass or fail
criterion alongside the observed result.

**Sign-off requires V1, V3, V6 and V7.** Any failure stops the build. If V1
fails, the illness table is top-line only and the deliverable becomes the
data-gap finding rather than the analysis.

Record the run in `00_docs/run_log.md` and the sign-off in the table at the end
of `00_docs/validation.md`.

## Column names

No column name is hardcoded in SQL. `config.resolve_col` resolves each one at
run time: an operator pin in `schema_map.PINS` wins, then a seeded default in
`schema_map.DEFAULTS` (operator-attested names, used when present in the live
schema), then an INFORMATION_SCHEMA pattern search. It raises on ambiguity,
raises when nothing matches, and prints the table's full actual column list so
the correct name can be pasted back in one trip. Every script prints which real
column it used and whether it came from a pin, a default, or a pattern.

Three names have no seeded default on purpose — named in prior docs but never
exercised in a query: `EMIS_CLAIM_LINE.claim_line_id`, `plc_srv_cd`,
`plc_srv_ctg_cd`. Setting logic and the diagnosis join depend on them; the
resolver reports what it finds.

The resolver is scaffolding for the first discovery trip. After it, resolved
names go into `00_docs/data_model.md` and the scripts switch to explicit
constants.

## Known gaps

Three tables named in methodology Appendix A have no project or dataset:
`PROVIDER_DM`, `A870800_medicare_analysis_2025_claims`, and `ms_dc_ref_ccir`.
`00_list_tables.py` searches for them. Per DD-01, V3 and V7 no longer depend
on the A870800 extract; the CCIR table is still needed for the any-condition
figure.

No value list has been seen for any code column (`plc_srv_cd`,
`business_ln_cd`, `specialty_ctg_cd`, `med_cost_ctg_cd`, `poa_cd`,
`medical_ind`). `11_value_profiles.py` profiles each; the setting groups and
the Medicare/commercial split are written only after it comes back.

Twenty open questions are recorded in `00_docs/open_questions.md`, each with
what it blocks.
