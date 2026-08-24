# Run order

Standalone runbook for Gate 1, run by hand in the BigQuery console. Everything
needed is on this page.

## Before anything

- Open the BigQuery console with `anbc-dev-prv-nc-ds` as the selected billing
  project (Q18).
- Paste a file's contents into the editor. Files with more than one query say
  so at the top: run those one statement at a time.
- Before running anything marked large below, check the estimated bytes the
  console shows in the top right of the editor. That estimate replaces the
  old cost gate: if it looks like a full-table scan you did not expect, stop.
- Save every result: Download CSV, named after the file and query, for
  example `03_v1_sequence_values.csv` or `05_v3_query_b.csv`.
- **Copy back after the run: every saved result, and every error message
  verbatim.**

## What a failure looks like

- `Unrecognized name: x` — the column name is wrong at that table. The
  console usually suggests the right one ("Did you mean ..."); otherwise find
  it in the 01_columns.sql result. Fix the file by hand, record the real name
  in data_model.md, rerun. Expected first at `claim_line_id`, `plc_srv_cd`
  and `plc_srv_ctg_cd` on EMIS_CLAIM_LINE — the three names never exercised
  in any prior query. If `claim_line_id` has no equivalent at all, V3, V6 and
  V7 cannot run and Gate 1 cannot sign off (DD-01).
- `Not found: Table ...` — the table is not at that location. Stop on that
  file; log in open_questions.md.
- A type error on EXTRACT — `srv_start_dt` is not a date type. Adjust the
  cast by hand and record the real type in data_model.md.
- An empty result where rows were expected — say so; do not fill anything in.
- A `PASSES` criterion not met — expected output, not an error. The header of
  each file says what to do.

## Step 1 of 2 - schema discovery

| # | File | Cost | Result |
|---|---|---|---|
| 1 | `01_columns.sql` | metadata only | actual columns and types, all tables |
| 2 | `02_row_counts.sql` | metadata only | row counts and sizes |
| 3 | `11_value_profiles.sql` (9 queries) | single-column scans of large tables | value sets for every code column |

## STOP POINT

**Do not run any V-check until `00_docs/data_model.md` has been rewritten from
the 01_columns.sql result and its NOT YET VERIFIED banner removed, and any
wrong column name in files 03-10 corrected by hand.** If that rewrite is not
happening at this machine, stop here and send the results back.

## Step 2 of 2 - Gate 1 checks

Run in order. Each file's header carries the pass and fail criteria from
validation.md.

| # | File | Check | Cost |
|---|---|---|---|
| 4 | `03_v1_sequence_values.sql` | V1 | scan of CLM_LN_X_ICD9_DX - large |
| 5 | `04_v2_dx_per_claim_line.sql` (2 queries) | V2 | scan of CLM_LN_X_ICD9_DX - large |
| 6 | `05_v3_seq1_vs_pri_icd9_dx_cd.sql` (2 queries) | V3 | joins two large tables |
| 7 | `06_v4_year_completeness.sql` (2 queries) | V4 | date scan of EMIS_CLAIM_LINE - large |
| 8 | `07_v5_member_id_stability.sql` (3 queries) | V5 | membership scans plus one large claims join |
| 9 | `08_v6_join_integrity.sql` (2 queries) | V6 | joins two large tables |
| 10 | `09_v7_diabetes_share.sql` (4 queries) | V7 | Query D is the heaviest in Gate 1 |
| 11 | `10_v8_code_mapping.sql` (3 queries) | V8 | code column scans - moderate |

Stop rules:

- **If V1 fails (only position 1 exists), stop everything.** Nothing after it
  is meaningful. The deliverable becomes the data-gap finding.
- **Gate 1 sign-off requires V1, V3, V6 and V7. If any fails, do not proceed
  past Gate 1.** Finish the remaining checks if they run - their output is
  still wanted - then send everything back. No extract work of any kind.
- V4 failing means the 2023 vs 2024 window is not settled. Query B names the
  latest settled pair. Moving the window means editing the years in files
  07-09 by hand and a numbered decision - send the output back first.

## After the run

1. Send back every saved result and every error, verbatim.
2. Record each run in `00_docs/run_log.md` (format at the top of that file),
   or send the results back for someone else to record.
3. Gate 1 is signed off only when V1, V3, V6 and V7 all pass. Record the
   sign-off in the table at the end of `00_docs/validation.md`.
