-- ===========================================================================
-- eda_1_dm_codes.sql                  EDA Step 1. DISPLAY ONLY, NO WRITE.
--
-- WHAT   Which HCC_v24 categories are reached by ICD-10 codes matching
--        ^E(08|09|10|11|12|13) in HCC_ICD_Mapping_2025: the category, its
--        distinct code count among those codes, and five examples each.
-- WHY    This derives the diabetes HCC set from the data instead of
--        hardcoding category numbers. The confirmed set defines the diabetes
--        family everywhere downstream; nothing is materialized until the set
--        is confirmed against the CMS-HCC V24 definition.
-- STOPS  Zero rows: the mapping reaches no HCC from the diabetes ICD block -
--        stop, inspect HCC_ICD_Mapping_2025 before anything else.
--        Any category in the result that is not a diabetes category on
--        inspection: stop and resolve before the set is used.
--        Nothing downstream is written until this set is confirmed.
-- NOTES  Codes normalised with UPPER(REPLACE(TRIM(diagnosis_code), '.', '')).
--        icd_codes counts only codes inside the E08-E13 block; the confirmed
--        categories later expand to every code that maps to them, in either
--        direction of the block boundary. E12 is unused in ICD-10-CM and is
--        included so a WHO-coded row would not slip past. One query, small
--        table.
-- ===========================================================================

SELECT
  CAST(HCC_v24 AS STRING) AS hcc_v24,
  COUNT(DISTINCT UPPER(REPLACE(TRIM(diagnosis_code), '.', ''))) AS icd_codes,
  STRING_AGG(DISTINCT UPPER(REPLACE(TRIM(diagnosis_code), '.', '')), ', '
             ORDER BY UPPER(REPLACE(TRIM(diagnosis_code), '.', '')) LIMIT 5)
    AS example_codes
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.HCC_ICD_Mapping_2025`
WHERE REGEXP_CONTAINS(UPPER(REPLACE(TRIM(diagnosis_code), '.', '')),
                      r'^E(08|09|10|11|12|13)')
  AND HCC_v24 IS NOT NULL
  AND CAST(HCC_v24 AS STRING) NOT IN ('', '0')
GROUP BY 1
ORDER BY 1;
