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
```

Then write `00_docs/data_model.md` from `01_discovery/output/01_columns.csv`
and remove its NOT YET VERIFIED banner.

## Gate 1

```
python 01_discovery/03_v1_dx_positions.py            V1  multiple diagnosis positions
python 01_discovery/04_v2_dx_per_claim_line.py       V2  fan-out is real
python 01_discovery/05_v3_position1_vs_topline.py    V3  position 1 matches the old field
python 01_discovery/06_v4_year_completeness.py       V4  both years equally settled
python 01_discovery/07_v5_member_id_stability.py     V5  identifiers stable across years
python 01_discovery/08_v6_join_integrity.py          V6  the visit link holds
python 01_discovery/09_v7_recovery_rate.py           V7  what the extra positions recover
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

No column name is hardcoded. `config.resolve_col` reads INFORMATION_SCHEMA at
run time and returns the one column matching an ordered list of patterns. It
raises on ambiguity, raises when nothing matches, and prints every column on
the table so the right one can be pinned in `schema_map.PINS`.

All thirteen column names asserted in the brief are unverified.
`01_columns.py` writes `01_brief_column_check.csv` marking each CONFIRMED or
ABSENT.

## Known gaps

Three tables named in methodology Appendix A have no project or dataset:
`PROVIDER_DM`, `A870800_medicare_analysis_2025_claims`, and `ms_dc_ref_ccir`.
`00_list_tables.py` searches for them. The second and third are needed by V3
and V7, both sign-off checks.

Nineteen open questions are recorded in `00_docs/open_questions.md`, each with
what it blocks.
