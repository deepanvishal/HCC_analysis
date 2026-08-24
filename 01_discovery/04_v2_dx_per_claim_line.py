"""
WHAT   V2. Distribution of the number of illnesses recorded against a single
       claim line. Confirms the fan-out is the rule rather than a handful of
       exceptions.
GRAIN  one row per illness-count value
INPUTS config.T_DX
OUTPUT 01_discovery/output/v2_dx_per_claim_line.csv

Pass  mean clearly above 1, with a visible tail beyond 10
Fail  over 90% of claim lines carry exactly one illness
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

SPEC = {
    "claim_line_id": ([r"claim_line_id",
                       r"clm_ln_id",
                       r".*clm_ln.*id", r".*claim_line.*id"], "dx.claim_line_id"),
}


def main():
    print("04_v2_dx_per_claim_line")
    c = cfg.resolved(cfg.T_DX, SPEC)

    sql = """
    WITH per_line AS (
      SELECT {cll} AS claim_line_id, COUNT(*) AS dx_count
      FROM `{t}`
      GROUP BY 1
    )
    SELECT dx_count, COUNT(*) AS claim_lines
    FROM per_line
    GROUP BY 1
    ORDER BY 1
    """.format(cll=c["claim_line_id"], t=cfg.T_DX)

    df = cfg.run_query(sql, label="V2")
    cfg.write_csv(df, "v2_dx_per_claim_line.csv")

    if not len(df):
        raise SystemExit("no rows returned")

    lines = df["claim_lines"].sum()
    dx_rows = (df["dx_count"] * df["claim_lines"]).sum()
    mean = dx_rows / lines
    share_one = df[df["dx_count"] == 1]["claim_lines"].sum() / lines
    tail = df[df["dx_count"] > 10]["claim_lines"].sum()
    share_tail = tail / lines
    max_dx = int(df["dx_count"].max())

    print("")
    print("  claim lines            {:,}".format(int(lines)))
    print("  illness rows           {:,}".format(int(dx_rows)))
    print("  mean per claim line    {:.2f}".format(mean))
    print("  exactly one illness    {:.1%}".format(share_one))
    print("  more than ten          {:.2%}  ({:,} lines)".format(share_tail, int(tail)))
    print("  maximum observed       {}".format(max_dx))
    print("")
    print("  distribution head:")
    for _, r in df.head(15).iterrows():
        pct = r["claim_lines"] / lines
        print("    {:>3} illnesses  {:>15,} lines  {:>7.2%}"
              .format(int(r["dx_count"]), int(r["claim_lines"]), pct))

    if share_one > 0.90:
        result = False
    elif mean > 1.0 and share_tail > 0:
        result = True
    else:
        result = None

    cfg.verdict("V2", "mean above 1 with a visible tail beyond 10; "
                      "fail if over 90% of lines carry exactly one", result)
    if result is None:
        print("  Mean exceeds 1 but no claim line carries more than ten "
              "illnesses. Check against V1 before proceeding.")


if __name__ == "__main__":
    main()
