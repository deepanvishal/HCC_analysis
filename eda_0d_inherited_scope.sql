-- ===========================================================================
-- eda_0d_inherited_scope.sql          EDA Step 0, file 4 of 4. READ ONLY.
--
-- WHAT   What scope the curated table inherited from its build: every
--        business_ln_cd value, distinct counts and the top 10 values of
--        mbr_submarket and prvdr_submarket, and the date range by year.
-- WHY    The curated table is already filtered and the EDA adds no
--        geography or business line filters of its own. The inherited scope
--        goes on the record rather than being assumed.
-- STOPS  Nothing stops here; this is the record. But if Query D shows years
--        outside 2023-2025, later files' srv_start_dt filter is doing real
--        work; if business_ln_cd shows one value, the scope is already one
--        book - report either way.
-- NOTES  Runnable any time after 0a passes; 0b and 0c do not depend on it.
--        Full-table GROUP BYs on single columns - check the console estimate
--        top right. The top-10 in Query C is a display choice on an
--        unbounded distribution, not an analysis cutoff; Query B says how
--        many values the 10 leave out. Four queries. Run one at a time.
--        If 0a showed srv_start_dt is not a date type, adjust the EXTRACT
--        in Query D by hand first.
-- ===========================================================================

-- Query A: every business_ln_cd value.
SELECT
  COALESCE(CAST(business_ln_cd AS STRING), '(null)') AS business_ln_cd,
  COUNT(*) AS n_rows,
  COUNT(DISTINCT member_id) AS members
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
GROUP BY 1
ORDER BY n_rows DESC;

-- Query B: submarket cardinality and null share.
SELECT
  'mbr_submarket' AS profiled,
  COUNT(DISTINCT mbr_submarket) AS distinct_values,
  COUNTIF(mbr_submarket IS NULL) AS null_rows,
  COUNT(*) AS n_rows
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
UNION ALL
SELECT
  'prvdr_submarket',
  COUNT(DISTINCT prvdr_submarket),
  COUNTIF(prvdr_submarket IS NULL),
  COUNT(*)
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
ORDER BY profiled;

-- Query C: top 10 values of each submarket column by row count.
SELECT profiled, raw_value, n_rows
FROM (
  SELECT
    'mbr_submarket' AS profiled,
    COALESCE(CAST(mbr_submarket AS STRING), '(null)') AS raw_value,
    COUNT(*) AS n_rows
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
  GROUP BY 2
  UNION ALL
  SELECT
    'prvdr_submarket',
    COALESCE(CAST(prvdr_submarket AS STRING), '(null)'),
    COUNT(*)
  FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
  GROUP BY 2
)
QUALIFY ROW_NUMBER() OVER (PARTITION BY profiled ORDER BY n_rows DESC) <= 10
ORDER BY profiled, n_rows DESC;

-- Query D: date range by year, whole table, no date filter - shows what
-- exists outside 2023-2025 as well.
SELECT
  EXTRACT(YEAR FROM srv_start_dt) AS yr,
  COUNT(*) AS claim_lines,
  MIN(srv_start_dt) AS min_srv_start_dt,
  MAX(srv_start_dt) AS max_srv_start_dt
FROM `anbc-hcb-dev.provider_ds_netconf_data_hcb_dev.A870800_medicare_analysis_2025_claims`
GROUP BY 1
ORDER BY 1;
