-- ===========================================================================
-- 09_v7_diabetes_share.sql
--
-- V7. What do we recover?
--
-- WHAT   Share of members recorded with diabetes in 2023, computed two ways:
--        from pri_icd9_dx_cd only, and from every diagnosis position in
--        CLM_LN_X_ICD9_DX. Both a check and the headline finding.
-- WHY    The existing extract records 29% of members with any long-term
--        condition; the corrected figure should be far higher. This measures
--        what the extra positions recover, for diabetes.
-- PASSES Diabetes lands near 25-30% for Medicare and 8-12% for commercial,
--        and the every-position share sits above the pri_icd9_dx_cd share.
--        business_ln_cd values are raw and unmapped: judging which value is
--        which book is open question Q9 and a numbered decision, not
--        something these queries assume. Gate 1 sign-off requires V7.
-- FAILS  Too low: something is still being filtered out. No change between
--        the two arms: the extra positions carry nothing and the rework was
--        unnecessary. Report it either way.
-- ON FAILURE  Stop before the extract. Report the finding as it is.
-- DD-01  These queries read raw EMIS_CLAIM_LINE and depend on
--        EMIS_CLAIM_LINE.claim_line_id existing. That column was never
--        exercised in any prior query. If it does not exist, this check, V3
--        and V6 cannot run, and Gate 1 cannot sign off.
--        COMPARABILITY: the 29% figure came from the curated extract under
--        its own filters - summarized_srv_ind = 'Y', duplicate_ind = 'N',
--        dental excluded via med_cost_ctg_cd, DPPO excluded via
--        ntwk_srv_area_id, footprint submarkets only. Raw EMIS_CLAIM_LINE
--        applies none of them. The difference between the two arms is the
--        finding and stays valid, because both arms share one population.
--        The absolute pri_icd9_dx_cd-only share is NOT the 29% and must not
--        be presented as its replacement.
-- DD-02  The diabetes HCC set is derived from the mapping table, not
--        hardcoded. The mapping's confirmed columns carry no description, so
--        Query A derives by ICD-10 diabetes chapter prefix E08-E13. If
--        01_columns.sql shows a description column, also run the description
--        variant noted below Query A and compare the two sets. Check the
--        derived set against the CMS-HCC V24 definition (Q10) before
--        trusting Query D.
-- NOTES  No all-book total is produced, on purpose: Medicare and commercial
--        are never combined into one figure.
--        Codes are matched with dots removed, trimmed and upper-cased on
--        both sides. Four queries. Run them one at a time. Query D is the
--        heaviest query in Gate 1.
-- ===========================================================================

-- Query A: the derived diabetes HCC set, with evidence. Confirm against the
-- CMS-HCC V24 definition before reading Query D.
-- Description variant, only if 01_columns.sql showed a description column on
-- the mapping: replace the REGEXP_CONTAINS predicate with
-- LOWER(<description_column>) LIKE '%diabet%' and compare the two sets.
SELECT
  CAST(HCC_v24 AS STRING) AS hcc_v24,
  COUNT(DISTINCT diagnosis_code) AS icd_codes,
  STRING_AGG(DISTINCT UPPER(TRIM(REPLACE(diagnosis_code, '.', ''))), ', '
             ORDER BY UPPER(TRIM(REPLACE(diagnosis_code, '.', ''))) LIMIT 5)
    AS example_codes
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.HCC_ICD_Mapping_2025`
WHERE REGEXP_CONTAINS(UPPER(TRIM(REPLACE(diagnosis_code, '.', ''))),
                      r'^E(08|09|10|11|12|13)')
  AND HCC_v24 IS NOT NULL
  AND CAST(HCC_v24 AS STRING) NOT IN ('', '0')
GROUP BY 1
ORDER BY 1;

-- Query B: raw business_ln_cd values in the 2023 Florida membership. These
-- stay unmapped; assigning Medicare and commercial is Q9.
SELECT
  business_ln_cd,
  COUNT(DISTINCT member_id) AS members
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_membership`
WHERE CAST(eff_yr AS INT64) = 2023
  AND UPPER(TRIM(mbr_state)) = 'FL'
GROUP BY 1
ORDER BY members DESC;

-- Query C: members holding more than one business_ln_cd in 2023. Above zero
-- means the per-value denominators in Query D sum to more than the distinct
-- member count; deciding which value wins is Q9.
WITH per_member AS (
  SELECT member_id, COUNT(DISTINCT business_ln_cd) AS business_ln_cd_values
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_membership`
  WHERE CAST(eff_yr AS INT64) = 2023
    AND UPPER(TRIM(mbr_state)) = 'FL'
  GROUP BY 1
)
SELECT
  COUNT(*) AS members,
  COUNTIF(business_ln_cd_values > 1) AS members_multi_business_ln_cd
FROM per_member;

-- Query D: the check itself. Diabetes share per business_ln_cd, both arms,
-- 2023, Florida. relative_difference near zero is the no-change failure.
WITH diabetes_hccs AS (
  SELECT DISTINCT CAST(HCC_v24 AS STRING) AS hcc_v24
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.HCC_ICD_Mapping_2025`
  WHERE REGEXP_CONTAINS(UPPER(TRIM(REPLACE(diagnosis_code, '.', ''))),
                        r'^E(08|09|10|11|12|13)')
    AND HCC_v24 IS NOT NULL
    AND CAST(HCC_v24 AS STRING) NOT IN ('', '0')
),
dm AS (
  SELECT DISTINCT UPPER(TRIM(REPLACE(diagnosis_code, '.', ''))) AS diagnosis_code
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.HCC_ICD_Mapping_2025`
  WHERE CAST(HCC_v24 AS STRING) IN (SELECT hcc_v24 FROM diabetes_hccs)
),
denom AS (
  SELECT DISTINCT member_id, business_ln_cd
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_membership`
  WHERE CAST(eff_yr AS INT64) = 2023
    AND UPPER(TRIM(mbr_state)) = 'FL'
),
y1_lines AS (
  SELECT
    member_id,
    claim_line_id,
    UPPER(TRIM(REPLACE(pri_icd9_dx_cd, '.', ''))) AS pri_icd9_dx_cd
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
  WHERE EXTRACT(YEAR FROM srv_start_dt) = 2023
),
all_pos AS (
  SELECT DISTINCT l.member_id
  FROM y1_lines l
  JOIN `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX` x
    ON x.claim_line_id = l.claim_line_id
  JOIN dm
    ON dm.diagnosis_code = UPPER(TRIM(REPLACE(x.icd9_dx_cd, '.', '')))
),
pri_dx AS (
  SELECT DISTINCT l.member_id
  FROM y1_lines l
  JOIN dm ON dm.diagnosis_code = l.pri_icd9_dx_cd
)
SELECT
  denom.business_ln_cd,
  COUNT(*) AS members,
  COUNTIF(p.member_id IS NOT NULL) AS diabetes_pri_icd9_dx_cd,
  COUNTIF(a.member_id IS NOT NULL) AS diabetes_every_position,
  ROUND(COUNTIF(p.member_id IS NOT NULL) / COUNT(*), 4) AS share_pri_icd9_dx_cd,
  ROUND(COUNTIF(a.member_id IS NOT NULL) / COUNT(*), 4) AS share_every_position,
  ROUND((COUNTIF(a.member_id IS NOT NULL) - COUNTIF(p.member_id IS NOT NULL))
        / COUNT(*) * 100, 1) AS diff_pct_points,
  ROUND(SAFE_DIVIDE(COUNTIF(a.member_id IS NOT NULL)
                    - COUNTIF(p.member_id IS NOT NULL),
                    COUNTIF(p.member_id IS NOT NULL)), 4) AS relative_difference
FROM denom
LEFT JOIN all_pos a ON a.member_id = denom.member_id
LEFT JOIN pri_dx p ON p.member_id = denom.member_id
GROUP BY denom.business_ln_cd
ORDER BY members DESC;
