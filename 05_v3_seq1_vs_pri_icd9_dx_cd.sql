-- ===========================================================================
-- 05_v3_seq1_vs_pri_icd9_dx_cd.sql
--
-- V3. Is position 1 the same as the old top-line field?
--
-- WHAT   For claim lines present in both tables, does the diagnosis at
--        sequence_id 1 in CLM_LN_X_ICD9_DX match pri_icd9_dx_cd on
--        EMIS_CLAIM_LINE?
-- WHY    Proves the sequence number means position on the claim. Without
--        this, we know there are several illnesses but not what their order
--        signifies.
-- PASSES Agreement above 95%.
-- FAILS  Agreement below 80% - the sequence means something else and needs
--        investigating before use. Gate 1 sign-off requires V3.
-- ON FAILURE  Stop. Read the disagreement sample (Query B) before deciding
--        anything.
-- DD-01  This check reads EMIS_CLAIM_LINE and depends on
--        EMIS_CLAIM_LINE.claim_line_id existing. That column was never
--        exercised in any prior query. If it does not exist, this check,
--        V6 and V7 cannot run, and Gate 1 cannot sign off. An error
--        "Unrecognized name: claim_line_id" here means exactly that - find
--        the real join key in the 01_columns.sql result and correct these
--        files by hand.
--        (The comparison target is EMIS_CLAIM_LINE.pri_icd9_dx_cd, not the
--        A870800 extract, which carries no claim_line_id. See DD-01.)
-- NOTES  Codes are compared with dots removed, trimmed and upper-cased on
--        both sides, so a pure formatting difference is not a disagreement.
--        Two queries. Run them one at a time. Joins two large tables - large.
-- ===========================================================================

-- Query A: agreement summary. compared_rows above compared_claim_lines means
-- sequence_id 1 is not unique per claim line - investigate before relying
-- on it.
WITH seq1 AS (
  SELECT
    claim_line_id,
    UPPER(TRIM(REPLACE(icd9_dx_cd, '.', ''))) AS icd9_dx_cd_seq1
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  WHERE SAFE_CAST(sequence_id AS INT64) = 1
),
emis AS (
  SELECT
    claim_line_id,
    UPPER(TRIM(REPLACE(pri_icd9_dx_cd, '.', ''))) AS pri_icd9_dx_cd
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
),
j AS (
  SELECT e.claim_line_id, s.icd9_dx_cd_seq1, e.pri_icd9_dx_cd
  FROM emis e
  JOIN seq1 s ON s.claim_line_id = e.claim_line_id
)
SELECT
  COUNT(*) AS compared_rows,
  COUNT(DISTINCT claim_line_id) AS compared_claim_lines,
  COUNTIF(icd9_dx_cd_seq1 = pri_icd9_dx_cd) AS agree,
  COUNTIF(icd9_dx_cd_seq1 != pri_icd9_dx_cd) AS disagree,
  COUNTIF(icd9_dx_cd_seq1 IS NULL OR pri_icd9_dx_cd IS NULL) AS null_either,
  ROUND(COUNTIF(icd9_dx_cd_seq1 = pri_icd9_dx_cd) / COUNT(*), 4) AS agreement
FROM j;

-- Query B: the highest-volume disagreeing code pairs. Read before deciding a
-- result between 80% and 95%.
WITH seq1 AS (
  SELECT
    claim_line_id,
    UPPER(TRIM(REPLACE(icd9_dx_cd, '.', ''))) AS icd9_dx_cd_seq1
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX`
  WHERE SAFE_CAST(sequence_id AS INT64) = 1
),
emis AS (
  SELECT
    claim_line_id,
    UPPER(TRIM(REPLACE(pri_icd9_dx_cd, '.', ''))) AS pri_icd9_dx_cd
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
)
SELECT
  s.icd9_dx_cd_seq1,
  e.pri_icd9_dx_cd,
  COUNT(*) AS n_rows
FROM emis e
JOIN seq1 s ON s.claim_line_id = e.claim_line_id
WHERE s.icd9_dx_cd_seq1 != e.pri_icd9_dx_cd
GROUP BY 1, 2
ORDER BY n_rows DESC
LIMIT 200;
