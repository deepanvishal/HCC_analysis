-- ===========================================================================
-- 06_v4_year_completeness.sql
--
-- V4. Are both years equally complete?
--
-- WHAT   Claim line counts by month across all candidate years, and the Q4
--        comparison per consecutive year pair.
-- WHY    Bills arrive late. A thin final year makes every doctor look like
--        they stopped recording things. This is the most common way a
--        comparison like this goes wrong.
-- PASSES The last three months of year two are within 10% of the same months
--        in year one, for the configured window 2023 -> 2024.
-- FAILS  A visible taper.
-- ON FAILURE  Move the window back a year rather than adjusting for it.
--        The years 2023/2024 are hardcoded in files 07, 08 and 09; moving
--        the window means editing those by hand and recording the change as
--        a numbered decision in 00_docs/data_decisions.md.
-- NOTES  This check decides the window; 2023/2024 is provisional until it
--        passes. The scan is deliberately wide (2019-2025).
--        srv_start_dt's type is unverified; EXTRACT works for DATE, DATETIME
--        and TIMESTAMP. If it errors, the column is not a date type - adjust
--        by hand and record the real type in data_model.md.
--        Two queries. Run them one at a time. Date scan of EMIS_CLAIM_LINE -
--        large.
-- ===========================================================================

-- Query A: claim lines and members by year and month. A settled year is flat
-- into December; an unfinished one thins out.
SELECT
  EXTRACT(YEAR FROM srv_start_dt) AS yr,
  EXTRACT(MONTH FROM srv_start_dt) AS mo,
  COUNT(*) AS claim_lines,
  COUNT(DISTINCT member_id) AS members
FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
WHERE EXTRACT(YEAR FROM srv_start_dt) BETWEEN 2019 AND 2025
GROUP BY 1, 2
ORDER BY 1, 2;

-- Query B: Q4 volume ratio for every consecutive year pair. The pass
-- criterion reads off the within_10pct column for year_1=2023, year_2=2024;
-- if that row is false, the latest true row is the window to move back to.
WITH q4 AS (
  SELECT
    EXTRACT(YEAR FROM srv_start_dt) AS yr,
    COUNT(*) AS q4_claim_lines
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
  WHERE EXTRACT(YEAR FROM srv_start_dt) BETWEEN 2019 AND 2025
    AND EXTRACT(MONTH FROM srv_start_dt) IN (10, 11, 12)
  GROUP BY 1
),
pairs AS (
  SELECT
    LAG(yr) OVER w AS year_1,
    yr AS year_2,
    LAG(q4_claim_lines) OVER w AS q4_year_1,
    q4_claim_lines AS q4_year_2
  FROM q4
  WINDOW w AS (ORDER BY yr)
)
SELECT
  year_1,
  year_2,
  q4_year_1,
  q4_year_2,
  ROUND(SAFE_DIVIDE(q4_year_2, q4_year_1), 4) AS q4_ratio,
  ABS(SAFE_DIVIDE(q4_year_2, q4_year_1) - 1) <= 0.10 AS within_10pct
FROM pairs
WHERE year_1 IS NOT NULL
ORDER BY year_2;
