-- ===========================================================================
-- eda_0c_dx_probe.sql                 EDA Step 0, file 3 of 4. READ ONLY.
--
-- WHAT   On 10,000 deterministically sampled claim_line_id values from the
--        curated table: match rate into CLM_LN_X_ICD9_DX, and whether
--        member_id agrees on both sides.
-- WHY    Decides whether Step 4 (the one full-detail read of
--        CLM_LN_X_ICD9_DX) runs at all. A wrong join key attaches diagnoses
--        to the wrong members and produces confident, false results.
-- STOPS  match_rate below 0.95: stop everything, send the result back.
--        lines_member_disagree above 0: stop everything. Not a tolerance
--        question. A probed line whose diagnosis rows carry more than one
--        member also lands in this count, because at least one row must
--        differ from the curated side.
-- NOTES  This is the two-column probe scan of CLM_LN_X_ICD9_DX agreed on top
--        of the Step 4 full read - BigQuery has no index, so joining 10,000
--        ids still scans the claim_line_id and member_id columns in full.
--        Check the console estimate top right before running.
--        The 10,000 and the FARM_FINGERPRINT ordering are deterministic:
--        rerunning picks the same lines.
--        dx_member_null_lines counts matched lines whose diagnosis rows
--        carry a NULL member_id - not agreement, not disagreement; report.
--        One query.
-- ===========================================================================

WITH pick AS (
  SELECT
    CAST(claim_line_id AS STRING) AS claim_line_id,
    MIN(CAST(member_id AS STRING)) AS member_id
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
  WHERE claim_line_id IS NOT NULL
  GROUP BY 1
  ORDER BY FARM_FINGERPRINT(CAST(claim_line_id AS STRING))
  LIMIT 10000
)
SELECT
  COUNT(DISTINCT p.claim_line_id) AS probe_lines,
  COUNT(DISTINCT IF(x.claim_line_id IS NOT NULL, p.claim_line_id, NULL)) AS matched_lines,
  ROUND(COUNT(DISTINCT IF(x.claim_line_id IS NOT NULL, p.claim_line_id, NULL))
        / COUNT(DISTINCT p.claim_line_id), 4) AS match_rate,
  COUNT(DISTINCT IF(CAST(x.member_id AS STRING) != p.member_id,
                    p.claim_line_id, NULL)) AS lines_member_disagree,
  COUNT(DISTINCT IF(x.claim_line_id IS NOT NULL AND x.member_id IS NULL,
                    p.claim_line_id, NULL)) AS dx_member_null_lines
FROM pick p
LEFT JOIN `edp-prod-hcbstorage.edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX` x
  ON CAST(x.claim_line_id AS STRING) = p.claim_line_id;
