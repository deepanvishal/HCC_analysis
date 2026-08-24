"""
WHAT   V1. The spread of diagnosis position numbers across the whole illness
       table. If only position 1 exists the extract is top-line only and the
       analysis cannot run.
GRAIN  one row per diagnosis position
INPUTS config.T_DX
OUTPUT 01_discovery/output/v1_dx_positions.csv

Pass  positions span 1 to roughly 12 or beyond
Fail  only position 1 appears
On failure the deliverable becomes the data-gap finding (methodology 3.1).

Sequence is stored as text with a leading zero, so it is cast to INT64 before
comparison. Values that fail to cast are reported separately rather than
silently dropped.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

SPEC = {
    "sequence": ([r"sequence_id",
                  r"(icd9_)?(dx_)?seq(uence)?_(id|nbr|num|no|cd)",
                  r".*seq.*"], "dx.sequence"),
    "claim_line_id": ([r"claim_line_id",
                       r"clm_ln_id",
                       r".*clm_ln.*id", r".*claim_line.*id"], "dx.claim_line_id"),
}


def main():
    print("03_v1_dx_positions")
    c = cfg.resolved(cfg.T_DX, SPEC)

    sql = """
    SELECT SAFE_CAST({seq} AS INT64)          AS dx_position,
           COUNT(*)                           AS dx_rows,
           COUNT(DISTINCT {cll})              AS claim_lines
    FROM `{t}`
    GROUP BY 1
    ORDER BY 1
    """.format(seq=c["sequence"], cll=c["claim_line_id"], t=cfg.T_DX)

    df = cfg.run_query(sql, label="V1")
    cfg.write_csv(df, "v1_dx_positions.csv")

    uncastable = df[df["dx_position"].isna()]["dx_rows"].sum()
    valid = df[df["dx_position"].notna()]
    if not len(valid):
        raise SystemExit("no diagnosis position cast to an integer. "
                         "Column {} is not a sequence.".format(c["sequence"]))

    total = valid["dx_rows"].sum()
    max_pos = int(valid["dx_position"].max())
    min_pos = int(valid["dx_position"].min())
    n_pos = len(valid)
    share_pos1 = valid[valid["dx_position"] == 1]["dx_rows"].sum() / total

    print("")
    print("  distinct positions   {}".format(n_pos))
    print("  range                {} to {}".format(min_pos, max_pos))
    print("  rows at position 1   {:.1%}".format(share_pos1))
    if uncastable:
        print("  UNCASTABLE sequence values: {:,} rows".format(int(uncastable)))
    print("")
    print("  top positions by volume:")
    for _, r in valid.head(15).iterrows():
        print("    {:>3}  {:>15,} rows  {:>15,} claim lines"
              .format(int(r["dx_position"]), int(r["dx_rows"]),
                      int(r["claim_lines"])))

    if n_pos <= 1:
        result = False
    elif max_pos >= 12:
        result = True
    else:
        result = None

    cfg.verdict("V1", "positions span 1 to roughly 12 or beyond; "
                      "fail if only position 1 appears", result)
    if result is False:
        print("  STOP. Gate 1 sign-off requires V1. The illness table is "
              "top-line only and the deliverable becomes the data-gap finding.")
    elif result is None:
        print("  Positions exceed 1 but stop below 12. Judge against "
              "methodology section 8, which expects up to 36.")


if __name__ == "__main__":
    main()
