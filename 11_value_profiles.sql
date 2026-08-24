-- ===========================================================================
-- 11_value_profiles.sql
--
-- WHAT   Distinct-value profiles for the code columns whose value sets nobody
--        has seen: plc_srv_cd, plc_srv_ctg_cd, business_ln_cd,
--        med_cost_ctg_cd, poa_cd, mbr_state, specialty_ctg_cd.
-- WHY    Setting logic and the Medicare/commercial split cannot be written
--        until these come back. Raw values only; nothing here maps or
--        interprets a value - that is a numbered decision in
--        00_docs/data_decisions.md.
-- PASSES Not a pass/fail check.
-- FAILS  n/a. An error "Unrecognized name: x" means the column name is wrong
--        at that table - take the console's did-you-mean suggestion or the
--        01_columns.sql listing, correct by hand, and record the real name
--        in data_model.md.
-- ON FAILURE  n/a.
-- NOTES  plc_srv_cd and plc_srv_ctg_cd were named in prior docs but never
--        exercised in any query - with EMIS_CLAIM_LINE.claim_line_id, the
--        highest-risk names in the build. Expect Unrecognized-name errors
--        here first.
--        Seven queries, one per (table, column). Run them one at a time.
--        Queries 1-4 scan single columns of EMIS_CLAIM_LINE - large.
--        Query 5 scans CLM_LN_X_ICD9_DX - large. The rest are small tables.
--        No membership queries for business_ln_cd or medical_ind: neither is
--        a column on the curated table - both are build filters (DD-05), so
--        there is nothing to profile.
-- ===========================================================================

-- Query 1: EMIS_CLAIM_LINE.plc_srv_cd (expected to carry IP / OP / F)
SELECT
  'EMIS_CLAIM_LINE.plc_srv_cd' AS profiled,
  COALESCE(CAST(plc_srv_cd AS STRING), '(null)') AS raw_value,
  COUNT(*) AS n_rows,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
GROUP BY 2
ORDER BY n_rows DESC;

-- Query 2: EMIS_CLAIM_LINE.plc_srv_ctg_cd (coarser rollup above plc_srv_cd)
SELECT
  'EMIS_CLAIM_LINE.plc_srv_ctg_cd' AS profiled,
  COALESCE(CAST(plc_srv_ctg_cd AS STRING), '(null)') AS raw_value,
  COUNT(*) AS n_rows,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
GROUP BY 2
ORDER BY n_rows DESC;

-- Query 3: EMIS_CLAIM_LINE.business_ln_cd
SELECT
  'EMIS_CLAIM_LINE.business_ln_cd' AS profiled,
  COALESCE(CAST(business_ln_cd AS STRING), '(null)') AS raw_value,
  COUNT(*) AS n_rows,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
GROUP BY 2
ORDER BY n_rows DESC;

-- Query 4: EMIS_CLAIM_LINE.med_cost_ctg_cd (dental exclusion lives here)
SELECT
  'EMIS_CLAIM_LINE.med_cost_ctg_cd' AS profiled,
  COALESCE(CAST(med_cost_ctg_cd AS STRING), '(null)') AS raw_value,
  COUNT(*) AS n_rows,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
GROUP BY 2
ORDER BY n_rows DESC;

-- Query 5: CLM_LN_X_ICD9_DX.poa_cd
SELECT
  'CLM_LN_X_ICD9_DX.poa_cd' AS profiled,
  COALESCE(CAST(poa_cd AS STRING), '(null)') AS raw_value,
  COUNT(*) AS n_rows,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
GROUP BY 2
ORDER BY n_rows DESC;

-- Query 6: membership mbr_state ('FL' must appear, or the Florida filter
-- in 09 finds nothing)
SELECT
  'membership.mbr_state' AS profiled,
  COALESCE(CAST(mbr_state AS STRING), '(null)') AS raw_value,
  COUNT(*) AS n_rows,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_membership`
GROUP BY 2
ORDER BY n_rows DESC;

-- Query 7: PROVIDER_DM.specialty_ctg_cd (peer grouping for steps 13-14)
SELECT
  'PROVIDER_DM.specialty_ctg_cd' AS profiled,
  COALESCE(CAST(specialty_ctg_cd AS STRING), '(null)') AS raw_value,
  COUNT(*) AS n_rows,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.PROVIDER_DM`
GROUP BY 2
ORDER BY n_rows DESC;
