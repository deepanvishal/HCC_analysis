"""
WHAT   V5. How many members present in year one are absent from year two, split
       by whether they still hold coverage. If identifiers change with plan or
       product, members look like they left and their conditions look dropped.
GRAIN  grain probe is one row per rows-per-member value; the pivot summary is
       one row
INPUTS config.T_MEMBERSHIP, config.T_CLAIM_LINE
OUTPUT 01_discovery/output/v5_membership_grain.csv
       01_discovery/output/v5_member_presence.csv
       01_discovery/output/v5_claims_vs_membership.csv

Pass  members with continuous coverage overwhelmingly appear in both years
Fail  a large share of continuously covered members missing from year two

The membership grain is not assumed. The first query reports rows per member
per year so the operator can confirm whether the table is member-month,
member-span or member-year before reading the rest.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

MEMBERSHIP_SPEC = {
    "member_id": ([r"member_id", r"mbr_id", r".*mbr.*id", r".*member.*id"],
                  "membership.member_id"),
    "eff_dt": ([r"eff_dt",
                r"(cvrg|covg|coverage|elig|eligibility|mbrshp|membership)_"
                r"(month|mth|mo|dt|date|yr_mo)",
                r"(eff|start|begin)_(dt|date)",
                r".*(month|yr_mo).*", r".*eff.*dt.*"],
               "membership.eff_dt"),
}

CLAIM_SPEC = {
    "member_id": ([r"member_id", r"mbr_id", r".*mbr.*id", r".*member.*id"],
                  "claim_line.member_id"),
    "srv_start_dt": ([r"srv_start_dt",
                      r"(srv|svc|service)_(start_)?(dt|date)",
                      r".*srv.*start.*dt", r".*service.*start.*date"],
                     "claim_line.srv_start_dt"),
}


def main():
    print("07_v5_member_id_stability")
    m = cfg.resolved(cfg.T_MEMBERSHIP, MEMBERSHIP_SPEC)
    mdt = cfg.date_expr(cfg.T_MEMBERSHIP, m["eff_dt"])
    print("    membership date expression -> {}".format(mdt))

    grain_sql = """
    WITH per_member_year AS (
      SELECT {mid} AS member_id,
             EXTRACT(YEAR FROM {mdt}) AS yr,
             COUNT(*) AS rows_in_year,
             COUNT(DISTINCT DATE_TRUNC({mdt}, MONTH)) AS distinct_months
      FROM `{t}`
      WHERE EXTRACT(YEAR FROM {mdt}) IN ({y1}, {y2})
      GROUP BY 1, 2
    )
    SELECT rows_in_year, distinct_months, COUNT(*) AS member_years
    FROM per_member_year
    GROUP BY 1, 2
    ORDER BY member_years DESC
    LIMIT 100
    """.format(mid=m["member_id"], mdt=mdt, t=cfg.T_MEMBERSHIP,
               y1=cfg.YEAR_1, y2=cfg.YEAR_2)

    grain = cfg.run_query(grain_sql, label="V5 grain")
    cfg.write_csv(grain, "v5_membership_grain.csv")
    print("")
    print("  membership rows per member per year (top combinations):")
    for _, r in grain.head(10).iterrows():
        print("    {:>4} rows / {:>3} distinct months  ->  {:,} member-years"
              .format(int(r["rows_in_year"]), int(r["distinct_months"]),
                      int(r["member_years"])))
    print("  Confirm the grain against 00_docs/data_model.md before reading on.")

    presence_sql = """
    WITH cov AS (
      SELECT {mid} AS member_id,
             EXTRACT(YEAR FROM {mdt}) AS yr,
             COUNT(DISTINCT DATE_TRUNC({mdt}, MONTH)) AS months
      FROM `{t}`
      WHERE EXTRACT(YEAR FROM {mdt}) IN ({y1}, {y2})
      GROUP BY 1, 2
    ),
    piv AS (
      SELECT member_id,
             SUM(IF(yr = {y1}, months, 0)) AS months_y1,
             SUM(IF(yr = {y2}, months, 0)) AS months_y2
      FROM cov
      GROUP BY 1
    )
    SELECT
      COUNTIF(months_y1 > 0)                          AS in_y1,
      COUNTIF(months_y1 > 0 AND months_y2 > 0)        AS in_y1_and_y2,
      COUNTIF(months_y1 > 0 AND months_y2 = 0)        AS y1_only,
      COUNTIF(months_y1 = 12)                         AS full_y1,
      COUNTIF(months_y1 = 12 AND months_y2 > 0)       AS full_y1_present_y2,
      COUNTIF(months_y1 = 12 AND months_y2 = 12)      AS full_both_years,
      COUNTIF(months_y1 = 0 AND months_y2 > 0)        AS y2_only
    FROM piv
    """.format(mid=m["member_id"], mdt=mdt, t=cfg.T_MEMBERSHIP,
               y1=cfg.YEAR_1, y2=cfg.YEAR_2)

    df = cfg.run_query(presence_sql, label="V5 presence")
    cfg.write_csv(df, "v5_member_presence.csv")
    r = df.iloc[0]

    in_y1 = int(r["in_y1"])
    full_y1 = int(r["full_y1"])
    if not in_y1:
        raise SystemExit("no members with coverage in {}".format(cfg.YEAR_1))

    carry = int(r["in_y1_and_y2"]) / in_y1
    full_carry = (int(r["full_y1_present_y2"]) / full_y1) if full_y1 else 0.0

    print("")
    print("  members with coverage in {}          {:,}".format(cfg.YEAR_1, in_y1))
    print("  also present in {}                   {:,}  ({:.1%})"
          .format(cfg.YEAR_2, int(r["in_y1_and_y2"]), carry))
    print("  absent from {}                       {:,}"
          .format(cfg.YEAR_2, int(r["y1_only"])))
    print("  new in {}                            {:,}"
          .format(cfg.YEAR_2, int(r["y2_only"])))
    print("")
    print("  full 12 months in {}                 {:,}".format(cfg.YEAR_1, full_y1))
    print("  of those, present in {}              {:,}  ({:.1%})"
          .format(cfg.YEAR_2, int(r["full_y1_present_y2"]), full_carry))
    print("  of those, full 12 months in {}       {:,}"
          .format(cfg.YEAR_2, int(r["full_both_years"])))

    c = cfg.resolved(cfg.T_CLAIM_LINE, CLAIM_SPEC)
    cdt = cfg.date_expr(cfg.T_CLAIM_LINE, c["srv_start_dt"])

    cross_sql = """
    WITH clm AS (
      SELECT DISTINCT {cid} AS member_id, EXTRACT(YEAR FROM {cdt}) AS yr
      FROM `{tc}`
      WHERE EXTRACT(YEAR FROM {cdt}) IN ({y1}, {y2})
    ),
    cov AS (
      SELECT DISTINCT {mid} AS member_id, EXTRACT(YEAR FROM {mdt}) AS yr,
             TRUE AS has_coverage
      FROM `{tm}`
      WHERE EXTRACT(YEAR FROM {mdt}) IN ({y1}, {y2})
    )
    SELECT clm.yr                                     AS yr,
           COUNT(*)                                   AS claim_members,
           COUNTIF(cov.has_coverage IS NOT NULL)      AS matched_to_coverage,
           COUNTIF(cov.has_coverage IS NULL)          AS no_coverage_row
    FROM clm
    LEFT JOIN cov
      ON cov.member_id = clm.member_id AND cov.yr = clm.yr
    GROUP BY clm.yr
    ORDER BY yr
    """.format(cid=c["member_id"], cdt=cdt, tc=cfg.T_CLAIM_LINE,
               mid=m["member_id"], mdt=mdt, tm=cfg.T_MEMBERSHIP,
               y1=cfg.YEAR_1, y2=cfg.YEAR_2)

    cross = cfg.run_query(cross_sql, label="V5 claims vs membership")
    cfg.write_csv(cross, "v5_claims_vs_membership.csv")
    print("")
    print("  members with claims but no coverage row:")
    for _, x in cross.iterrows():
        share = int(x["no_coverage_row"]) / int(x["claim_members"])
        print("    {}  {:,} of {:,}  ({:.2%})"
              .format(int(x["yr"]), int(x["no_coverage_row"]),
                      int(x["claim_members"]), share))

    if full_y1 == 0:
        result = None
    elif full_carry >= 0.95:
        result = True
    elif full_carry < 0.85:
        result = False
    else:
        result = None

    cfg.verdict("V5", "members with a full year of {} coverage "
                      "overwhelmingly appear in {}".format(cfg.YEAR_1, cfg.YEAR_2),
                result)
    if result is False:
        print("  Identifiers may not be stable across years. A6 in "
              "00_docs/assumptions.md is not satisfied. Establish a crosswalk "
              "before building the two-year pivot.")
    elif result is None:
        print("  Between 85% and 95%, or no full-year cohort. Judge against "
              "expected disenrollment for this population before proceeding.")


if __name__ == "__main__":
    main()
