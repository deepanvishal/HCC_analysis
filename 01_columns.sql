-- ===========================================================================
-- 01_columns.sql
--
-- WHAT   Actual column names, types, nullability, partitioning and clustering
--        for every table Gate 1 reads. Also searches both datasets for
--        A870800_medicare_analysis_2025_claims, whose location is unknown
--        (Q2) - that table is not used by any Gate 1 check.
-- WHY    Source of truth for 00_docs/data_model.md. Nothing else runs until
--        these results have been read and any wrong column name in the later
--        files corrected by hand.
-- PASSES Every table returns rows.
-- FAILS  A table returns no rows: it does not exist at that location, or is
--        not visible to the billing project.
-- ON FAILURE  Find the table before running anything that reads it. Log in
--        00_docs/open_questions.md.
-- NOTES  Metadata only, scans no table data. Copy the full result back and
--        into data_model.md.
-- ===========================================================================

SELECT
  'edp-prod-hcbstorage.edp_hcb_core_cnsv' AS dataset_searched,
  table_name,
  ordinal_position,
  column_name,
  data_type,
  is_nullable,
  is_partitioning_column,
  clustering_ordinal_position
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('CLM_LN_X_ICD9_DX',
                     'EMIS_CLAIM_LINE',
                     'PROVIDER_DM',
                     'A870800_medicare_analysis_2025_claims')
UNION ALL
SELECT
  'anbc-hcb-dev.provider_ds_netconf_data_hcb_dev',
  table_name,
  ordinal_position,
  column_name,
  data_type,
  is_nullable,
  is_partitioning_column,
  clustering_ordinal_position
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('A870800_medicare_analysis_membership',
                     'HCC_ICD_Mapping_2025',
                     'A870800_medicare_supply_demand_ms_dc_ref_ccir',
                     'A870800_medicare_analysis_2025_claims')
ORDER BY dataset_searched, table_name, ordinal_position;
