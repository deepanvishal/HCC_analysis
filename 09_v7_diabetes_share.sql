-- ===========================================================================
-- 09_v7_diabetes_share.sql
--
-- V7. What do we recover?
--
-- WHAT   Share of members recorded with diabetes in 2023, computed two ways:
--        from pri_icd9_dx_cd only, and from every diagnosis position in
--        CLM_LN_X_ICD9_DX. One figure per arm, and the difference between
--        them. Both a check and the headline finding.
-- WHY    The existing extract records 29% of members with any long-term
--        condition; the corrected figure should be far higher. This measures
--        what the extra positions recover, for diabetes.
-- PASSES The every-position share sits clearly above the pri_icd9_dx_cd
--        share. Gate 1 sign-off requires V7.
--        The per-book bands in validation.md V7 (25-30% Medicare, 8-12%
--        commercial) are dropped per DD-06: the membership denominator mixes
--        both books without labels, so no band can be assigned. The
--        difference between the arms is the check; the absolute level is
--        reported without a benchmark.
-- FAILS  No change between the two arms: the extra positions carry nothing
--        and the rework was unnecessary. Report it either way.
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
--        trusting Query B.
-- DD-06  The analysis is Medicare only, and business line is out of Gate 1
--        entirely. The curated membership cannot distinguish the books - its
--        build filtered to business_ln_cd IN ('CP','ME') without keeping the
--        column - so the denominator here is the mixed Florida membership,
--        used for coverage only. The Medicare scope is applied on claims
--        when the extract is built, not here.
-- NOTES  Codes are matched with dots removed, trimmed and upper-cased on
--        both sides. Two queries. Run them one at a time. Query B is the
--        heaviest query in Gate 1.
-- ===========================================================================

-- Query A: the derived diabetes HCC set, with evidence. Confirm against the
-- CMS-HCC V24 definition before reading Query B.
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

-- Query B: the check itself. Diabetes share, both arms, 2023, Florida.
-- One row. relative_difference near zero is the no-change failure.
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
  SELECT DISTINCT member_id
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
LEFT JOIN pri_dx p ON p.member_id = denom.member_id;
