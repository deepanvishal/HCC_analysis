"""
WHAT   V6. What share of claim lines find a match in the illness table, and
       whether the member identifier agrees on both sides. A wrong join key
       attaches illnesses to the wrong members and produces confident,
       plausible, completely false results.
GRAIN  one row per direction summary; the sample is one row per mismatching pair
INPUTS config.T_CLAIM_LINE, config.T_DX
OUTPUT 01_discovery/output/v6_join_integrity.csv
       01_discovery/output/v6_member_mismatch_sample.csv

Pass  match rate above 95% and zero member mismatches
Fail  any member mismatch at all. This is not a tolerance question.
Gate 1 sign-off requires V6.

If the illness table carries no member identifier the agreement half of this
check cannot run. That is reported as UNVERIFIABLE, not as a pass.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

CLAIM_SPEC = {
    "claim_line_id": ([r"claim_line_id", r"clm_ln_id",
                       r".*clm_ln.*id", r".*claim_line.*id"],
                      "claim_line.claim_line_id"),
    "member_id": ([r"member_id", r"mbr_id", r".*mbr.*id", r".*member.*id"],
                  "claim_line.member_id"),
    "service_date": ([r"srv_start_dt",
                      r"(srv|svc|service)_(start_)?(dt|date)",
                      r".*srv.*start.*dt", r".*service.*start.*date"],
                     "claim_line.service_date"),
}

DX_ID_PATTERNS = [r"claim_line_id", r"clm_ln_id",
                  r".*clm_ln.*id", r".*claim_line.*id"]
DX_MBR_PATTERNS = [r"member_id", r"mbr_id", r".*mbr.*id", r".*member.*id"]


def main():
    print("08_v6_join_integrity")
    c = cfg.resolved(cfg.T_CLAIM_LINE, CLAIM_SPEC)
    cdt = cfg.date_expr(cfg.T_CLAIM_LINE, c["service_date"])

    dx_cll = cfg.resolve_col(cfg.T_DX, DX_ID_PATTERNS, pin="dx.claim_line_id")
    print("  resolving columns on " + cfg.T_DX)
    print("    claim_line_id              -> {}".format(dx_cll))
    dx_mbr = cfg.resolve_col(cfg.T_DX, DX_MBR_PATTERNS, pin="dx.member_id",
                             required=False)
    if dx_mbr:
        print("    member_id                  -> {}".format(dx_mbr))
    else:
        print("    member_id                  -> ABSENT; agreement half of V6 "
              "cannot run")

    if dx_mbr:
        dx_member_sel = ("COUNT(DISTINCT {m}) AS distinct_members, "
                         "ANY_VALUE({m}) AS member_id".format(m=dx_mbr))
        mismatch_sel = ("COUNTIF(d.member_id IS NOT NULL "
                        "AND l.member_id != d.member_id) AS member_mismatch, "
                        "COUNTIF(d.distinct_members > 1) AS multi_member_lines")
    else:
        dx_member_sel = "0 AS distinct_members, CAST(NULL AS STRING) AS member_id"
        mismatch_sel = ("CAST(NULL AS INT64) AS member_mismatch, "
                        "CAST(NULL AS INT64) AS multi_member_lines")

    base = """
    WITH l AS (
      SELECT {c_cll} AS claim_line_id, {c_mid} AS member_id
      FROM `{t_cl}`
      WHERE EXTRACT(YEAR FROM {cdt}) IN ({y1}, {y2})
    ),
    d AS (
      SELECT {d_cll} AS claim_line_id, COUNT(*) AS dx_rows, {dsel}
      FROM `{t_dx}`
      GROUP BY 1
    )
    """.format(c_cll=c["claim_line_id"], c_mid=c["member_id"],
               t_cl=cfg.T_CLAIM_LINE, cdt=cdt,
               y1=cfg.YEAR_1, y2=cfg.YEAR_2,
               d_cll=dx_cll, dsel=dx_member_sel, t_dx=cfg.T_DX)

    sql = base + """
    SELECT
      COUNT(*)                                    AS claim_lines,
      COUNTIF(d.dx_rows IS NOT NULL)              AS matched,
      COUNTIF(d.dx_rows IS NULL)                  AS unmatched,
      {mismatch}
    FROM l
    LEFT JOIN d ON d.claim_line_id = l.claim_line_id
    """.format(mismatch=mismatch_sel)

    df = cfg.run_query(sql, label="V6 forward")
    cfg.write_csv(df, "v6_join_integrity.csv")
    r = df.iloc[0]

    lines = int(r["claim_lines"])
    if not lines:
        raise SystemExit("no claim lines in {}-{}".format(cfg.YEAR_1, cfg.YEAR_2))
    match_rate = int(r["matched"]) / lines

    print("")
    print("  claim lines in {}-{}      {:,}".format(cfg.YEAR_1, cfg.YEAR_2, lines))
    print("  matched to illness table    {:,}  ({:.2%})"
          .format(int(r["matched"]), match_rate))
    print("  unmatched                   {:,}".format(int(r["unmatched"])))

    mismatch = r["member_mismatch"]
    if dx_mbr:
        mismatch = int(mismatch or 0)
        multi = int(r["multi_member_lines"] or 0)
        print("  member mismatches           {:,}".format(mismatch))
        print("  lines with >1 member        {:,}".format(multi))
        if mismatch or multi:
            sample_sql = base + """
            SELECT l.claim_line_id AS claim_line_id,
                   l.member_id AS claim_member,
                   d.member_id AS dx_member, d.dx_rows, d.distinct_members
            FROM l JOIN d ON d.claim_line_id = l.claim_line_id
            WHERE l.member_id != d.member_id OR d.distinct_members > 1
            LIMIT 500
            """
            sample = cfg.run_query(sample_sql, label="V6 mismatch sample")
            cfg.write_csv(sample, "v6_member_mismatch_sample.csv")
    else:
        multi = None
        print("  member mismatches           UNVERIFIABLE (no member column "
              "on the illness table)")

    if match_rate <= 0.95:
        result = False
    elif dx_mbr is None:
        result = None
    elif mismatch or multi:
        result = False
    else:
        result = True

    cfg.verdict("V6", "match rate above 95% and zero member mismatches", result)
    if result is False:
        print("  STOP. Gate 1 sign-off requires V6. Do not build the extract "
              "on this join key.")
    elif result is None:
        print("  Match rate passes but member agreement could not be tested. "
              "Log the missing member column in 00_docs/open_questions.md and "
              "find another way to verify the join before Gate 1 sign-off.")


if __name__ == "__main__":
    main()
