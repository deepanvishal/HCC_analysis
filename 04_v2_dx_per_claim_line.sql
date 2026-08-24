-- ===========================================================================
-- 04_v2_dx_per_claim_line.sql
--
-- V2. How many illnesses per visit?
--
-- WHAT   Distribution of illness count per claim line.
-- WHY    Confirms the fan-out is real rather than a handful of exceptions.
-- PASSES Average clearly above 1. A visible tail beyond 10.
-- FAILS  Over 90% of claim lines carry exactly one.
-- ON FAILURE  Check against V1 before proceeding.
-- NOTES  Two queries. Run them one at a time.
--        GROUP BY over CLM_LN_X_ICD9_DX - large.
-- ===========================================================================

-- Query A: summary. The pass criterion reads directly off this row.
WITH per_line AS (
  SELECT claim_line_id, COUNT(*) AS dx_per_claim_line
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  GROUP BY 1
)
SELECT
  COUNT(*) AS claim_lines,
  SUM(dx_per_claim_line) AS dx_rows,
  ROUND(AVG(dx_per_claim_line), 2) AS avg_dx_per_claim_line,
  ROUND(COUNTIF(dx_per_claim_line = 1) / COUNT(*), 4) AS share_exactly_one,
  ROUND(COUNTIF(dx_per_claim_line > 10) / COUNT(*), 4) AS share_over_ten,
  MAX(dx_per_claim_line) AS max_dx_per_claim_line
FROM per_line;

-- Query B: the full distribution behind the summary.
WITH per_line AS (
  SELECT claim_line_id, COUNT(*) AS dx_per_claim_line
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  GROUP BY 1
)
SELECT
  dx_per_claim_line,
  COUNT(*) AS claim_lines,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share_of_claim_lines
FROM per_line
GROUP BY 1
ORDER BY 1;
