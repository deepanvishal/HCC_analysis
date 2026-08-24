# Run order

Standalone runbook for the machine that holds credentials. Everything needed
to run discovery and Gate 1 is on this page; no other context is required.

## Before anything

- Needs Python 3 with `google-cloud-bigquery` and `pandas` installed, and
  working application default credentials.
- `python` may not be on PATH. If not, call the interpreter by full path,
  for example:
  `C:\path\to\python.exe 01_discovery\00_list_tables.py`
  Every command below writes `python`; substitute the full path throughout.
- Run from the repo root. The scripts also work when run from inside
  `01_discovery`.
- Every query dry-runs first and prints its size in GB. Anything above 50 GB
  prompts before running (`HCC_CONFIRM_GB` changes the threshold). Set
  `HCC_YES=1` to auto-accept in a batch run.
- All outputs land in `01_discovery\output\`.
- **Copy back after the run: the full console output of every script, plus
  every file in `01_discovery\output\`.** The console output contains resolver
  results and verdicts that the CSVs do not.

## What a failure looks like

- A block starting `UNRESOLVED` or `AMBIGUOUS`, ending with
  `columns present:` and a list. Paste the whole block back. This is the
  resolver saying a column name could not be confirmed; the list is what the
  table actually contains.
- A block starting `V3 BLOCKED`, `V6 BLOCKED` or `V7 BLOCKED`: the
  `claim_line_id` join key on EMIS_CLAIM_LINE did not resolve. Gate 1 cannot
  sign off. Stop and paste the block back.
- `aborted at cost gate`: a query was larger than the threshold and was
  declined. Paste the dry-run GB line back.
- A `PASS` / `FAIL` / `REVIEW` verdict line: expected output, not an error.
  FAIL and REVIEW both need the surrounding numbers pasted back.
- Any Python traceback: paste it in full.

## Step 1 of 2 - schema discovery (all cheap, metadata only)

| # | Command | Cost | Copy back |
|---|---|---|---|
| 1 | `python 01_discovery\00_list_tables.py` | metadata only | `00_tables_found.csv`, `00_tables_expected.csv` |
| 2 | `python 01_discovery\01_columns.py` | metadata only | `01_columns.csv`, `01_brief_column_check.csv` |
| 3 | `python 01_discovery\02_row_counts.py` | metadata only | `02_row_counts.csv`, `02_partitions.csv` |
| 4 | `python 01_discovery\11_value_profiles.py` | scans single columns of large tables; the gate prompts if large | `11_value_profiles.csv` |

Step 1 notes:

- Step 1 reports `MISSING` for tables it cannot find. Three tables have
  unconfirmed locations (`PROVIDER_DM`, `A870800_medicare_analysis_2025_claims`,
  `ms_dc_ref_ccir`); candidates found elsewhere are listed in
  `00_tables_found.csv`. A missing table does not stop the later steps that do
  not read it.
- Step 4 prints `COLUMN NOT FOUND` with the table's full column list for any
  column it cannot resolve - expected for `plc_srv_cd` and `plc_srv_ctg_cd` if
  those names are wrong. Not a failure; paste the lists back.

## STOP POINT

**Do not run any V-check until `00_docs/data_model.md` has been rewritten from
`01_columns.csv` and its NOT YET VERIFIED banner removed.** If the person at
this machine is not doing that rewrite, stop here, send everything back, and
wait for the go-ahead plus any `schema_map.PINS` entries that come out of it.

## Step 2 of 2 - Gate 1 checks

Run in order. Each prints its pass or fail criterion next to the observed
result and records the verdict for the summary.

| # | Command | Check | Cost | Copy back |
|---|---|---|---|---|
| 5 | `python 01_discovery\03_v1_dx_positions.py` | V1 | full scan of two columns of CLM_LN_X_ICD9_DX | `v1_dx_positions.csv` |
| 6 | `python 01_discovery\04_v2_dx_per_claim_line.py` | V2 | GROUP BY over CLM_LN_X_ICD9_DX | `v2_dx_per_claim_line.csv` |
| 7 | `python 01_discovery\05_v3_seq1_vs_pri_icd9_dx_cd.py` | V3 | joins CLM_LN_X_ICD9_DX to EMIS_CLAIM_LINE - large | `v3_seq1_vs_pri_icd9_dx_cd.csv`, `v3_seq1_disagreements.csv` |
| 8 | `python 01_discovery\06_v4_year_completeness.py` | V4 | date scan of EMIS_CLAIM_LINE 2019-2025 - large | `v4_monthly_volume.csv`, `v4_year_pairs.csv` |
| 9 | `python 01_discovery\07_v5_member_id_stability.py` | V5 | membership scans plus claims join | `v5_membership_grain.csv`, `v5_member_presence.csv`, `v5_claims_vs_membership.csv` |
| 10 | `python 01_discovery\08_v6_join_integrity.py` | V6 | joins EMIS_CLAIM_LINE to CLM_LN_X_ICD9_DX - large | `v6_join_integrity.csv`, `v6_member_mismatch_sample.csv` if written |
| 11 | `python 01_discovery\09_v7_diabetes_share.py` | V7 | heaviest step: membership, claims, diagnosis and mapping joins | `v7_diabetes_hcc_codes.csv`, `v7_business_ln_cd.csv`, `v7_diabetes_share.csv` |
| 12 | `python 01_discovery\10_v8_code_mapping.py` | V8 | diagnosis code column plus mapping table | `v8_code_formats.csv`, `v8_code_mapping.csv`, `v8_unmatched_codes.csv` |
| 13 | `python 01_discovery\99_gate1_summary.py` | summary | no queries | `99_gate1_summary.csv`, `gate1_verdicts.csv` |

Step 2 stop rules:

- **If V1 fails (only position 1 exists), stop everything.** Nothing after it
  is meaningful. The deliverable becomes the data-gap finding.
- **If any of V1, V3, V6, V7 fails, do not proceed past Gate 1.** Finish the
  remaining V-checks if they run (their output is still wanted), run the
  summary, and send everything back. Do not touch `02_extract`.
- V4 failing means the 2023 vs 2024 window is not settled. The script names
  the latest settled pair. Changing the window is a recorded decision, not
  something to do at this machine - paste the output back first.
- `02_extract`, `03_analysis` and `04_output` are empty by design. Nothing in
  them should be created or run.

## After the run

1. Copy back the full console output and all of `01_discovery\output\`.
2. Record each script run in `00_docs/run_log.md` (format is at the top of
   that file), or send the console output back for someone else to record.
3. Gate 1 is signed off only when `99_gate1_summary.py` prints
   `GATE 1: SIGNED OFF` - V1, V3, V6 and V7 all PASS. Record sign-off in the
   table at the end of `00_docs/validation.md`.
