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

All thirteen are **unverified**. `01_columns.py` writes
`01_brief_column_check.csv` marking each CONFIRMED or ABSENT and naming the
table it was found on. Transfer that result here.

| Brief name | Exists | Found on | Type |
|---|---|---|---|
| `claim_line_id` | not checked | | |
| `sequence_id` | not checked | | |
| `icd9_dx_cd` | not checked | | |
| `poa_cd` | not checked | | |
| `member_id` | not checked | | |
| `plc_srv_cd` | not checked | | |
| `plc_srv_ctg_cd` | not checked | | |
| `med_cost_ctg_cd` | not checked | | |
| `srv_prvdr_id` | not checked | | |
| `epdb_dw_prvdr_id` | not checked | | |
| `specialty_ctg_cd` | not checked | | |
| `business_ln_cd` | not checked | | |
| `srv_start_dt` | not checked | | |

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

**Not yet located in any table:** death indicator, provider specialty, state.
See `open_questions.md`.
