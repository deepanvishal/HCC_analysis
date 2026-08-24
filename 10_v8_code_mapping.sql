-- ===========================================================================
-- 10_v8_code_mapping.sql
--
-- V8. Do the codes map?
--
-- WHAT   Share of distinct diagnosis codes in the claims data found in the
--        HCC mapping table after removing dots.
-- WHY    A formatting mismatch between the two sides silently drops
--        conditions.
-- PASSES Above 95% of codes that should map, do.
-- FAILS  Below 90%.
-- ON FAILURE  Compare the shapes in Query A. A whole-side length or dot
--        difference is a formatting mismatch, not a coverage gap. Fix the
--        normalisation before Gate 1 sign-off.
-- NOTES  Match is measured against the mapping table as a whole, not against
--        codes carrying an HCC. Most diagnosis codes have no HCC; that is
--        expected and is not what this check is looking for.
--        Both sides are normalised with UPPER(TRIM(REPLACE(x, '.', ''))).
--        Three queries. Run them one at a time. Queries B and C scan the
--        diagnosis code column of CLM_LN_X_ICD9_DX - moderate.
-- ===========================================================================

-- Query A: code shape on each side, raw (before normalisation). Length and
-- dot patterns should differ only in ways the normalisation removes.
SELECT
  'CLM_LN_X_ICD9_DX.icd9_dx_cd' AS side,
  LENGTH(TRIM(icd9_dx_cd)) AS raw_length,
  STRPOS(icd9_dx_cd, '.') > 0 AS has_dot,
  COUNT(DISTINCT icd9_dx_cd) AS distinct_codes,
  COUNT(*) AS n_rows
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
WHERE icd9_dx_cd IS NOT NULL AND TRIM(icd9_dx_cd) != ''
GROUP BY 1, 2, 3
UNION ALL
SELECT
  'HCC_ICD_Mapping_2025.diagnosis_code',
  LENGTH(TRIM(diagnosis_code)),
  STRPOS(diagnosis_code, '.') > 0,
  COUNT(DISTINCT diagnosis_code),
  COUNT(*)
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.HCC_ICD_Mapping_2025`
WHERE diagnosis_code IS NOT NULL AND TRIM(diagnosis_code) != ''
GROUP BY 1, 2, 3
ORDER BY side, n_rows DESC;

-- Query B: the match rate. The pass criterion reads off match_rate_by_code.
WITH claims AS (
  SELECT
    UPPER(TRIM(REPLACE(icd9_dx_cd, '.', ''))) AS icd9_dx_cd,
    COUNT(*) AS dx_rows
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  WHERE icd9_dx_cd IS NOT NULL AND TRIM(icd9_dx_cd) != ''
  GROUP BY 1
),
mapping AS (
  SELECT
    UPPER(TRIM(REPLACE(diagnosis_code, '.', ''))) AS diagnosis_code,
    LOGICAL_OR(HCC_v24 IS NOT NULL
               AND CAST(HCC_v24 AS STRING) NOT IN ('', '0')) AS has_hcc_v24
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.HCC_ICD_Mapping_2025`
  WHERE diagnosis_code IS NOT NULL AND TRIM(diagnosis_code) != ''
  GROUP BY 1
)
SELECT
  COUNT(*) AS distinct_claim_codes,
  COUNTIF(m.diagnosis_code IS NOT NULL) AS matched_codes,
  COUNTIF(m.diagnosis_code IS NULL) AS unmatched_codes,
  ROUND(COUNTIF(m.diagnosis_code IS NOT NULL) / COUNT(*), 4) AS match_rate_by_code,
  SUM(c.dx_rows) AS dx_rows,
  ROUND(SUM(IF(m.diagnosis_code IS NOT NULL, c.dx_rows, 0)) / SUM(c.dx_rows), 4)
    AS match_rate_by_volume,
  COUNTIF(m.has_hcc_v24) AS codes_with_hcc_v24,
  ROUND(SUM(IF(m.has_hcc_v24, c.dx_rows, 0)) / SUM(c.dx_rows), 4)
    AS share_of_rows_with_hcc_v24
FROM claims c
LEFT JOIN mapping m ON m.diagnosis_code = c.icd9_dx_cd;

-- Query C: the highest-volume unmatched codes. A recognisable ICD-10 shape
-- here points at a normalisation problem; junk values point at data quality.
WITH claims AS (
  SELECT
    UPPER(TRIM(REPLACE(icd9_dx_cd, '.', ''))) AS icd9_dx_cd,
    COUNT(*) AS dx_rows
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  WHERE icd9_dx_cd IS NOT NULL AND TRIM(icd9_dx_cd) != ''
  GROUP BY 1
),
mapping AS (
  SELECT DISTINCT UPPER(TRIM(REPLACE(diagnosis_code, '.', ''))) AS diagnosis_code
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.HCC_ICD_Mapping_2025`
  WHERE diagnosis_code IS NOT NULL AND TRIM(diagnosis_code) != ''
)
SELECT
  c.icd9_dx_cd,
  c.dx_rows
FROM claims c
LEFT JOIN mapping m ON m.diagnosis_code = c.icd9_dx_cd
WHERE m.diagnosis_code IS NULL
ORDER BY c.dx_rows DESC
LIMIT 500;
