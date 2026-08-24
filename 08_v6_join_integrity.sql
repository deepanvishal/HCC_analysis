-- ===========================================================================
-- 08_v6_join_integrity.sql
--
-- V6. Does the visit link hold?
--
-- WHAT   What share of claim lines find a match in the illness table, and
--        whether the member identifier agrees on both sides of the join.
-- WHY    If the join key is wrong, illnesses attach to the wrong patients -
--        which produces confident, plausible, completely false results.
-- PASSES Match rate above 95%, zero member mismatches.
-- FAILS  Any member mismatch at all. This is not a tolerance question.
--        Gate 1 sign-off requires V6.
-- ON FAILURE  Stop. Do not build the extract on this join key. Read the
--        mismatch sample (Query B).
-- DD-01  This check depends on EMIS_CLAIM_LINE.claim_line_id existing. That
--        column was never exercised in any prior query. If it does not
--        exist, this check, V3 and V7 cannot run, and Gate 1 cannot sign
--        off. An error "Unrecognized name: claim_line_id" on the
--        EMIS_CLAIM_LINE side means exactly that - find the real join key in
--        the 01_columns.sql result and correct these files by hand.
-- NOTES  Two queries. Run them one at a time. Joins two large tables - large.
-- ===========================================================================

-- Query A: match rate and member agreement, claim lines with service in
-- 2023-2024. multi_member_lines counts claim lines whose illness rows carry
-- more than one member - any value above zero needs the sample read.
WITH l AS (
  SELECT claim_line_id, member_id
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
  WHERE EXTRACT(YEAR FROM srv_start_dt) IN (2023, 2024)
),
d AS (
  SELECT
    claim_line_id,
    COUNT(*) AS dx_rows,
    COUNT(DISTINCT member_id) AS distinct_members,
    ANY_VALUE(member_id) AS member_id
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  GROUP BY 1
)
SELECT
  COUNT(*) AS claim_lines,
  COUNTIF(d.dx_rows IS NOT NULL) AS matched,
  COUNTIF(d.dx_rows IS NULL) AS unmatched,
  ROUND(COUNTIF(d.dx_rows IS NOT NULL) / COUNT(*), 4) AS match_rate,
  COUNTIF(d.member_id IS NOT NULL AND l.member_id != d.member_id) AS member_mismatch,
  COUNTIF(d.distinct_members > 1) AS multi_member_lines
FROM l
LEFT JOIN d ON d.claim_line_id = l.claim_line_id;

-- Query B: sample of claim lines where the member disagrees across the join,
-- or where the illness rows carry more than one member. Only meaningful if
-- Query A reports either count above zero.
WITH l AS (
  SELECT claim_line_id, member_id
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
  WHERE EXTRACT(YEAR FROM srv_start_dt) IN (2023, 2024)
),
d AS (
  SELECT
    claim_line_id,
    COUNT(*) AS dx_rows,
    COUNT(DISTINCT member_id) AS distinct_members,
    ANY_VALUE(member_id) AS member_id
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  GROUP BY 1
)
SELECT
  l.claim_line_id,
  l.member_id AS emis_member_id,
  d.member_id AS dx_member_id,
  d.dx_rows,
  d.distinct_members
FROM l
JOIN d ON d.claim_line_id = l.claim_line_id
WHERE l.member_id != d.member_id OR d.distinct_members > 1
LIMIT 500;
