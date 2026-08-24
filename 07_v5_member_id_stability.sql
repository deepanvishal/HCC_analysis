-- ===========================================================================
-- 07_v5_member_id_stability.sql
--
-- V5. Do patients keep the same identifier?
--
-- WHAT   How many members present in year one are absent from year two,
--        split by coverage; plus a grain probe on the membership table and a
--        claims-vs-coverage cross-check.
-- WHY    If identifiers change with product or plan, members look like they
--        left and their conditions look dropped.
-- PASSES Members with continuous coverage overwhelmingly appear in both
--        years (share_full_2023_present_2024 at or above roughly 0.95).
-- FAILS  A large share of continuously covered members missing from year two
--        (below roughly 0.85). Between the two, judge against expected
--        disenrollment for this population.
-- ON FAILURE  Identifiers may not be stable across years - assumption A6 is
--        not satisfied. Establish a crosswalk before building the two-year
--        pivot.
-- NOTES  The membership grain is not assumed: Query A reports rows per
--        member per year. Confirm the grain against data_model.md before
--        reading Queries B and C.
--        eff_dt's type is unverified; EXTRACT and DATE_TRUNC work for DATE,
--        DATETIME and TIMESTAMP. If it errors, adjust by hand and record the
--        real type in data_model.md.
--        Three queries. Run them one at a time. Membership scans plus one
--        claims join - the claims join is large.
-- ===========================================================================

-- Query A: grain probe. One row per (rows-per-member-year, distinct-months)
-- combination. 12 rows / 12 months dominating means member-month grain.
WITH per_member_year AS (
  SELECT
    member_id,
    EXTRACT(YEAR FROM eff_dt) AS yr,
    COUNT(*) AS rows_in_year,
    COUNT(DISTINCT DATE_TRUNC(eff_dt, MONTH)) AS distinct_months
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_membership`
  WHERE EXTRACT(YEAR FROM eff_dt) IN (2023, 2024)
  GROUP BY 1, 2
)
SELECT rows_in_year, distinct_months, COUNT(*) AS member_years
FROM per_member_year
GROUP BY 1, 2
ORDER BY member_years DESC
LIMIT 100;

-- Query B: presence across the two years. The pass criterion reads off
-- share_full_2023_present_2024.
WITH cov AS (
  SELECT
    member_id,
    EXTRACT(YEAR FROM eff_dt) AS yr,
    COUNT(DISTINCT DATE_TRUNC(eff_dt, MONTH)) AS months
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_membership`
  WHERE EXTRACT(YEAR FROM eff_dt) IN (2023, 2024)
  GROUP BY 1, 2
),
piv AS (
  SELECT
    member_id,
    SUM(IF(yr = 2023, months, 0)) AS months_2023,
    SUM(IF(yr = 2024, months, 0)) AS months_2024
  FROM cov
  GROUP BY 1
)
SELECT
  COUNTIF(months_2023 > 0) AS members_2023,
  COUNTIF(months_2023 > 0 AND months_2024 > 0) AS in_both_years,
  COUNTIF(months_2023 > 0 AND months_2024 = 0) AS only_2023,
  COUNTIF(months_2023 = 0 AND months_2024 > 0) AS new_2024,
  COUNTIF(months_2023 = 12) AS full_12m_2023,
  COUNTIF(months_2023 = 12 AND months_2024 > 0) AS full_2023_present_2024,
  COUNTIF(months_2023 = 12 AND months_2024 = 12) AS full_12m_both,
  ROUND(SAFE_DIVIDE(COUNTIF(months_2023 > 0 AND months_2024 > 0),
                    COUNTIF(months_2023 > 0)), 4) AS share_present_2024,
  ROUND(SAFE_DIVIDE(COUNTIF(months_2023 = 12 AND months_2024 > 0),
                    COUNTIF(months_2023 = 12)), 4) AS share_full_2023_present_2024
FROM piv;

-- Query C: members with claims but no coverage row, per year. A large share
-- here means the claims and membership populations do not line up.
WITH clm AS (
  SELECT DISTINCT
    member_id,
    EXTRACT(YEAR FROM srv_start_dt) AS yr
  FROM `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_CLAIM_LINE`
  WHERE EXTRACT(YEAR FROM srv_start_dt) IN (2023, 2024)
),
cov AS (
  SELECT DISTINCT
    member_id,
    EXTRACT(YEAR FROM eff_dt) AS yr
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_membership`
  WHERE EXTRACT(YEAR FROM eff_dt) IN (2023, 2024)
)
SELECT
  clm.yr,
  COUNT(*) AS claim_members,
  COUNTIF(cov.member_id IS NOT NULL) AS matched_to_coverage,
  COUNTIF(cov.member_id IS NULL) AS no_coverage_row,
  ROUND(COUNTIF(cov.member_id IS NULL) / COUNT(*), 4) AS share_no_coverage_row
FROM clm
LEFT JOIN cov ON cov.member_id = clm.member_id AND cov.yr = clm.yr
GROUP BY clm.yr
ORDER BY clm.yr;
