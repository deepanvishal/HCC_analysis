"""
WHAT   V3. For claim lines present in both tables, does diagnosis position 1 in
       the illness table match the single diagnosis column on the existing
       top-line extract? Proves the sequence number means position on the claim.
GRAIN  summary is one row; the sample is one row per disagreeing code pair
INPUTS config.T_DX, config.T_TOPLINE
OUTPUT 01_discovery/output/v3_position1_vs_topline.csv
       01_discovery/output/v3_position1_disagreements.csv

Pass  agreement above 95%
Fail  agreement below 80% - the sequence means something else
Gate 1 sign-off requires V3.

Codes are compared with dots removed, trimmed and upper-cased on both sides, so
a pure formatting difference is not read as a disagreement.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

DX_SPEC = {
    "claim_line_id": ([r"claim_line_id", r"clm_ln_id",
                       r".*clm_ln.*id", r".*claim_line.*id"], "dx.claim_line_id"),
    "sequence": ([r"sequence_id",
                  r"(icd9_)?(dx_)?seq(uence)?_(id|nbr|num|no|cd)",
                  r".*seq.*"], "dx.sequence"),
    "dx_code": ([r"icd9_dx_cd", r"(icd9?_)?dx_cd",
                 r".*icd.*dx.*cd", r".*dx.*cd"], "dx.dx_code"),
}

TOPLINE_SPEC = {
    "claim_line_id": ([r"claim_line_id", r"clm_ln_id",
                       r".*clm_ln.*id", r".*claim_line.*id"], "topline.claim_line_id"),
    "dx_code": ([r"icd9_dx_cd", r"(prmry|primary)_(icd9_)?dx_cd",
                 r"(icd9?_)?dx_cd", r".*dx.*cd"], "topline.dx_code"),
}

NORM = "UPPER(TRIM(REPLACE({col}, '.', '')))"


def main():
    print("05_v3_position1_vs_topline")
    d = cfg.resolved(cfg.T_DX, DX_SPEC)
    o = cfg.resolved(cfg.T_TOPLINE, TOPLINE_SPEC)

    base = """
    WITH pos1 AS (
      SELECT {d_cll} AS claim_line_id,
             {d_norm} AS dx_pos1
      FROM `{t_dx}`
      WHERE SAFE_CAST({d_seq} AS INT64) = 1
    ),
    old AS (
      SELECT {o_cll} AS claim_line_id,
             {o_norm} AS dx_topline
      FROM `{t_old}`
    ),
    j AS (
      SELECT o.claim_line_id AS claim_line_id, p.dx_pos1, o.dx_topline
      FROM old o
      JOIN pos1 p ON p.claim_line_id = o.claim_line_id
    )
    """.format(d_cll=d["claim_line_id"],
               d_norm=NORM.format(col=d["dx_code"]),
               d_seq=d["sequence"], t_dx=cfg.T_DX,
               o_cll=o["claim_line_id"],
               o_norm=NORM.format(col=o["dx_code"]),
               t_old=cfg.T_TOPLINE)

    summary_sql = base + """
    SELECT
      COUNT(*)                                              AS compared_rows,
      COUNT(DISTINCT claim_line_id)                         AS compared_claim_lines,
      COUNTIF(dx_pos1 = dx_topline)                         AS agree,
      COUNTIF(dx_pos1 != dx_topline)                        AS disagree,
      COUNTIF(dx_pos1 IS NULL OR dx_topline IS NULL)        AS null_either
    FROM j
    """

    df = cfg.run_query(summary_sql, label="V3 summary")
    cfg.write_csv(df, "v3_position1_vs_topline.csv")

    if not len(df) or not df.iloc[0]["compared_rows"]:
        raise SystemExit("no claim lines are present in both tables. "
                         "Check the join key and that T_TOPLINE is correct.")

    r = df.iloc[0]
    rows = int(r["compared_rows"])
    lines = int(r["compared_claim_lines"])
    agree = int(r["agree"])
    rate = agree / rows

    print("")
    print("  rows compared          {:,}".format(rows))
    print("  distinct claim lines   {:,}".format(lines))
    if rows != lines:
        print("  NOTE: more rows than claim lines. Position 1 is not unique "
              "per claim line; investigate before relying on it.")
    print("  agree                  {:,}".format(agree))
    print("  disagree               {:,}".format(int(r["disagree"])))
    print("  null on either side    {:,}".format(int(r["null_either"])))
    print("  agreement              {:.2%}".format(rate))

    sample_sql = base + """
    SELECT dx_pos1, dx_topline, COUNT(*) AS n
    FROM j
    WHERE dx_pos1 != dx_topline
    GROUP BY 1, 2
    ORDER BY n DESC
    LIMIT 200
    """
    dis = cfg.run_query(sample_sql, label="V3 disagreements")
    cfg.write_csv(dis, "v3_position1_disagreements.csv")

    if rate > 0.95:
        result = True
    elif rate < 0.80:
        result = False
    else:
        result = None

    cfg.verdict("V3", "agreement above 95%; fail below 80%", result)
    if result is False:
        print("  STOP. Gate 1 sign-off requires V3. The sequence number does "
              "not mean position on the claim. Investigate before any use.")
    elif result is None:
        print("  Agreement between 80% and 95%. Read "
              "v3_position1_disagreements.csv before deciding.")


if __name__ == "__main__":
    main()
