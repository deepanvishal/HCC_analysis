-- ===========================================================================
-- 02_row_counts.sql
--
-- WHAT   Row count, storage size and last-modified time for every table Gate 1
--        reads, from table metadata rather than COUNT(*).
-- WHY    Establishes the scale each later query works against. Methodology
--        section 8 expects roughly 40M claim lines and roughly 180M
--        line-x-illness rows; compare against those shapes.
-- PASSES Every table reports a row count.
-- FAILS  A table is missing from the result: it is not at that location.
-- ON FAILURE  Same as 01_columns.sql.
-- NOTES  Metadata only, scans no table data.
-- ===========================================================================

SELECT
  'edp-prod-hcbstorage.edp_hcb_core_cnsv' AS dataset_searched,
  table_id AS table_name,
  row_count,
  ROUND(size_bytes / POW(1024, 3), 2) AS size_gb,
  TIMESTAMP_MILLIS(last_modified_time) AS last_modified
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.__TABLES__`
WHERE table_id IN ('CLM_LN_X_ICD9_DX',
                   'EMIS_CLAIM_LINE',
                   'PROVIDER_DM')
UNION ALL
SELECT
  'anbc-hcb-dev.provider_ds_netconf_data_hcb_dev',
  table_id,
  row_count,
  ROUND(size_bytes / POW(1024, 3), 2),
  TIMESTAMP_MILLIS(last_modified_time)
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.__TABLES__`
WHERE table_id IN ('A870800_medicare_analysis_membership',
                   'HCC_ICD_Mapping_2025',
                   'A870800_medicare_supply_demand_ms_dc_ref_ccir')
ORDER BY dataset_searched, table_name;
