-- ===========================================================================
-- eda_0a_curated_columns.sql          EDA Step 0, file 1 of 4. READ ONLY.
--
-- WHAT   Does the curated table exist at the location the brief gives, does
--        claim_line_id exist and with what type, and what type is
--        srv_start_dt. Also its size, from metadata.
-- WHY    Every later step joins on claim_line_id and filters on srv_start_dt.
--        This also closes Q2 (location) and confirms the DD-01 correction
--        (the rebuilt table carries claim_line_id).
-- STOPS  No rows from Query A: the table is not at this location - stop
--        everything, Q2 reopens.
--        claim_line_id absent from Query A: stop everything - the EDA has no
--        join key.
--        srv_start_dt not DATE/DATETIME/TIMESTAMP: do not stop, but the
--        EXTRACT calls in eda_0d and later files need a hand adjustment
--        before running.
-- NOTES  Metadata only, scans no table data. Two queries. Run one at a time.
--        Paste both results back in full.
-- ===========================================================================

-- Query A: columns and types.
SELECT column_name, data_type
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'A870800_medicare_analysis_2025_claims'
ORDER BY ordinal_position;

-- Query B: size, from metadata.
SELECT
  table_id AS table_name,
  row_count,
  ROUND(size_bytes / POW(1024, 3), 2) AS size_gb,
  TIMESTAMP_MILLIS(last_modified_time) AS last_modified
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.__TABLES__`
WHERE table_id = 'A870800_medicare_analysis_2025_claims';
