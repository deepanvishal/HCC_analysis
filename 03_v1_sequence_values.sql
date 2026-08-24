-- ===========================================================================
-- 03_v1_sequence_values.sql
--
-- V1. Are there multiple illness positions?
--
-- WHAT   The spread of sequence numbers across the whole illness table.
-- WHY    Everything depends on this. If only position 1 exists, the illness
--        list is top-line only and the analysis cannot run.
-- PASSES Numbers span 1 to roughly 12 for office visits, higher for hospital
--        claims.
-- FAILS  Only 1 appears.
-- ON FAILURE  Stop. The deliverable becomes the data-gap finding. Gate 1
--        sign-off requires V1.
-- NOTES  sequence_id is stored as text with a leading zero ('01'), so it is
--        cast to a number before grouping - otherwise 10 sorts before 2.
--        A NULL sequence_id row in the result means values that did not cast
--        to an integer; report them, do not ignore them.
--        Full scan of two columns of CLM_LN_X_ICD9_DX - large.
-- ===========================================================================

WITH by_position AS (
  SELECT
    SAFE_CAST(sequence_id AS INT64) AS sequence_id,
    COUNT(*) AS dx_rows,
    COUNT(DISTINCT claim_line_id) AS claim_lines
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  GROUP BY 1
)
SELECT
  sequence_id,
  dx_rows,
  claim_lines,
  ROUND(dx_rows / SUM(dx_rows) OVER (), 4) AS share_of_rows
FROM by_position
ORDER BY sequence_id;
