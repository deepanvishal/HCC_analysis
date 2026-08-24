# Data model

## NOT YET VERIFIED

Nothing in this file has been checked against the live schema. No table grain,
column name, type or join key below is confirmed. **Do not rely on anything on
this page, and do not write extract code against it.**

This file is filled from the output of the discovery scripts, run on the
machine that holds credentials:

```
python 01_discovery/00_list_tables.py     -> 00_tables_found.csv, 00_tables_expected.csv
python 01_discovery/01_columns.py         -> 01_columns.csv, 01_brief_column_check.csv
python 01_discovery/02_row_counts.py      -> 02_row_counts.csv, 02_partitions.csv
```

Rewrite the sections below from those CSVs, delete this banner, and record the
date and the person who did it in `run_log.md`.

---

## Operator-observed columns (2026-08-24, pre-discovery)

Seeded into `schema_map.DEFAULTS`. These are operator attestations, not
discovery output; the banner above still applies until `01_columns.py`
confirms them. Provenance tiers:

**Observed directly in a BigQuery SELECT * result grid** — probably complete,
not certainly (the grid had a horizontal scrollbar):

- `CLM_LN_X_ICD9_DX`: `claim_line_id`, `icd9_dx_cd` (ICD-10 content despite
  the name; dotted — E11.9, F31.62, G43.909 seen), `member_id`, `poa_cd`,
  `sequence_id` (STRING, zero-padded '01'; SAFE_CAST before ordering),
  `ziw_target_timestamp` (audit), `ziw_workflow_run_id` (audit)

**Used in working SQL in medicare_analysis:**

- `EMIS_CLAIM_LINE`: `member_id`, `srv_start_dt`, `pri_icd9_dx_cd`,
  `prcdr_cd`, `allowed_amt`, `business_ln_cd`, `summarized_srv_ind`,
  `med_cost_ctg_cd`, `ntwk_srv_area_id`, `duplicate_ind`, `srv_prvdr_id`,
  `member_county_cd`
- `A870800_medicare_analysis_2025_claims`: `member_id`, `age_nbr`,
  `gender_cd`, `mbr_county_cd`, `mbr_submarket`, `srv_start_dt`,
  `pri_icd9_dx_cd`, `prcdr_cd`, `allowed_amt`, `business_ln_cd`,
  `epdb_dw_prvdr_id`, `prvdr_county`, `prvdr_submarket`, `specialty_ctg_cd`
  — no `claim_line_id`, consistent with methodology Appendix A (DD-01)
- `HCC_ICD_Mapping_2025`: `diagnosis_code`, `HCC_v24`, `HCC_v28` — no
  description column (DD-02)
- `ms_dc_ref_ccir`: `icd_code`, `icd_description`, `chronic_indicator`
- membership extract: `member_id`, `eff_dt`, `medical_ind`,
  `business_ln_cd`, `age_nbr`, `gender_cd`, `county_nm`, `zip_cd`,
  `state_postal_cd` — no death indicator (Q6)
- `PROVIDER_DM`: `provider_id`, `epdb_dw_prvdr_id`, `specialty_ctg_cd`,
  `zip_cd`, `county_nm`, `tin_owner_nm`

**Named in docs, never exercised in any query — highest-risk names, no seeded
default, resolver reports what it finds:**

- `EMIS_CLAIM_LINE.claim_line_id` — the join key to the diagnosis table
- `EMIS_CLAIM_LINE.plc_srv_cd` — expected to carry IP / OP / F
- `EMIS_CLAIM_LINE.plc_srv_ctg_cd` — coarser rollup above it

Codes carry dots on the claims side and not in the HCC mapping. Both sides are
normalised with `UPPER(REPLACE(TRIM(x), '.', ''))` before any comparison.

No value list has been seen for `plc_srv_cd`, `plc_srv_ctg_cd`,
`business_ln_cd`, `specialty_ctg_cd`, `med_cost_ctg_cd`, `poa_cd`, or
`medical_ind`. `11_value_profiles.py` profiles each; setting logic and the
Medicare/commercial split cannot be written until those come back.

---

## Tables

Locations marked **unverified** were named in methodology.md Appendix A without
a project or dataset. `00_list_tables.py` searches for them; see
`open_questions.md` Q1–Q3.

| Purpose | Table | Location | Grain | Row count |
|---|---|---|---|---|
| Illnesses per claim line | `CLM_LN_X_ICD9_DX` | `edp-prod-hcbstorage.edp_hcb_core_cnsv` | not verified | not verified |
| Claim lines / visits | `EMIS_CLAIM_LINE` | `edp-prod-hcbstorage.edp_hcb_core_cnsv` | not verified | not verified |
| Code to condition | `HCC_ICD_Mapping_2025` | `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev` | not verified | not verified |
| Coverage months | `A870800_medicare_analysis_membership` | `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev` | not verified | not verified |
| Doctor detail | `PROVIDER_DM` | **unverified** | not verified | not verified |
| Existing top-line extract | `A870800_medicare_analysis_2025_claims` | **unverified** | not verified | not verified |
| Long-term condition flag | `ms_dc_ref_ccir` | **unverified** | not verified | not verified |

---

## Columns

One section per table. Fill each from `01_columns.csv`. Give the real column
name, the real type, and whether this analysis needs it.

### CLM_LN_X_ICD9_DX

| Column | Type | Needed | Used for |
|---|---|---|---|
| | | | |

**Grain:** not verified.
**Primary key:** not verified.

### EMIS_CLAIM_LINE

| Column | Type | Needed | Used for |
|---|---|---|---|
| | | | |

**Grain:** not verified.
**Primary key:** not verified.

### HCC_ICD_Mapping_2025

| Column | Type | Needed | Used for |
|---|---|---|---|
| | | | |

**Grain:** not verified.
Methodology Appendix A names the field `HCC_v24`. Unverified.

### A870800_medicare_analysis_membership

| Column | Type | Needed | Used for |
|---|---|---|---|
| | | | |

**Grain:** not verified. Member-month, member-span and member-year are all
possible and the difference changes every coverage calculation.
`07_v5_member_id_stability.py` prints a grain probe before anything else.

### PROVIDER_DM

| Column | Type | Needed | Used for |
|---|---|---|---|
| | | | |

**Grain:** not verified.

### A870800_medicare_analysis_2025_claims

| Column | Type | Needed | Used for |
|---|---|---|---|
| | | | |

**Grain:** not verified.

### ms_dc_ref_ccir

| Column | Type | Needed | Used for |
|---|---|---|---|
| | | | |

**Grain:** not verified. AHRQ CCIR v2026.1.

---

## Join keys

Every join below is proposed, not verified. V6
(`08_v6_join_integrity.py`) tests the first one and is a Gate 1 sign-off check.

| From | To | On | Verified |
|---|---|---|---|
| `EMIS_CLAIM_LINE` | `CLM_LN_X_ICD9_DX` | claim line identifier | no — V6 |
| claims | `HCC_ICD_Mapping_2025` | diagnosis code, dots removed | no — V8 |
| claims | `A870800_medicare_analysis_membership` | member identifier | no |
| claims | `PROVIDER_DM` | servicing provider identifier | no |

---

## Column names asserted in the task brief

None is discovery-confirmed yet. Provenance below is operator attestation
(grid = seen in a result grid; sql = used in working SQL; never exercised =
named in docs only). `01_columns.py` writes `01_brief_column_check.csv`
marking each CONFIRMED or ABSENT against the live schema; transfer that result
here.

| Brief name | Provenance | Expected on | Live schema |
|---|---|---|---|
| `claim_line_id` | grid (dx table); never exercised on EMIS_CLAIM_LINE | CLM_LN_X_ICD9_DX; EMIS_CLAIM_LINE | not checked |
| `sequence_id` | grid; STRING zero-padded | CLM_LN_X_ICD9_DX | not checked |
| `icd9_dx_cd` | grid; ICD-10 content, dotted | CLM_LN_X_ICD9_DX | not checked |
| `poa_cd` | grid; values unseen | CLM_LN_X_ICD9_DX | not checked |
| `member_id` | grid + sql | dx, EMIS, topline, membership | not checked |
| `plc_srv_cd` | never exercised | EMIS_CLAIM_LINE | not checked |
| `plc_srv_ctg_cd` | never exercised | EMIS_CLAIM_LINE | not checked |
| `med_cost_ctg_cd` | sql | EMIS_CLAIM_LINE | not checked |
| `srv_prvdr_id` | sql | EMIS_CLAIM_LINE | not checked |
| `epdb_dw_prvdr_id` | sql | topline, PROVIDER_DM | not checked |
| `specialty_ctg_cd` | sql | topline, PROVIDER_DM | not checked |
| `business_ln_cd` | sql | EMIS, topline, membership | not checked |
| `srv_start_dt` | sql | EMIS, topline | not checked |

---

## Columns this analysis needs

From methodology.md. The purpose is settled; the column that serves it is not.

| Need | Purpose | Methodology reference |
|---|---|---|
| Claim line identifier | Link a claim line to its illness positions | Appendix A, "columns the current extract does not carry" |
| Diagnosis sequence | Read every position, not just the first | Step 1, V1 |
| Diagnosis code | Name the condition | Step 7 |
| Place of service | Separate office from hospital | Step 9, A3 |
| Member identifier | One line per patient per year | Step 9 |
| Service date | Two-mention rule on separate dates; year window | Step 8, Step 6 |
| Servicing provider identifier | Score the individual clinician | Step 12, A2 |
| Provider specialty | Compare like with like | Step 14 |
| Business line | Keep Medicare and commercial apart | Step 5 |
| Coverage months | Require unbroken coverage across both years | Step 11 |
| Death indicator | Exclude patients not alive at the end of year two | Step 11 |
| State | Florida scope | Step 5 |

**Not yet located in any table:** death indicator (Q6), place of service (the
two `plc_srv` columns are named but never exercised, Q11). Provider specialty
and state now have operator-attested homes (`PROVIDER_DM.specialty_ctg_cd`,
membership `state_postal_cd`) pending discovery confirmation. See
`open_questions.md`.
