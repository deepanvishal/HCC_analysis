-- ===========================================================================
-- eda_0b_grain.sql                    EDA Step 0, file 2 of 4. READ ONLY.
--
-- WHAT   Rows per claim_line_id on the curated table - one row per line, or
--        repeats. Full distribution, no cutoff.
-- WHY    The whole EDA is claim line grain. If claim_line_id repeats, every
--        later count is inflated and the 0c probe's one-member-per-line
--        assumption breaks.
-- STOPS  Any value of rows_per_claim_line_id above 1 in Query A: stop and
--        send the distribution back before running 0c. The grain assumption
--        does not hold and the dedup rule becomes a decision.
-- NOTES  Two queries. Run one at a time. Scans one column of the curated
--        table - check the console estimate top right before running.
-- ===========================================================================

-- Query A: the distribution.
WITH per_line AS (
  SELECT claim_line_id, COUNT(*) AS n_rows
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
  GROUP BY 1
)
SELECT n_rows AS rows_per_claim_line_id, COUNT(*) AS claim_line_ids
FROM per_line
GROUP BY 1
ORDER BY 1;

-- Query B: totals behind it, including NULL join keys.
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT claim_line_id) AS distinct_claim_line_ids,
  COUNTIF(claim_line_id IS NULL) AS null_claim_line_id_rows
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`;
