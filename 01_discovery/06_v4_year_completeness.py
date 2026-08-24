"""
WHAT   V4. Claim line counts by month across every candidate year, and the
       Q4 comparison that says whether two consecutive years are equally
       settled. A thin final year makes every doctor look like they stopped
       recording things.
GRAIN  monthly grid is one row per (year, month); the comparison is one row per
       consecutive year pair
INPUTS config.T_CLAIM_LINE
OUTPUT 01_discovery/output/v4_monthly_volume.csv
       01_discovery/output/v4_year_pairs.csv

Pass  the last three months of year two are within 10% of the same months in
      year one
Fail  a visible taper
On failure move the window back a year rather than adjusting for it.

The year window is scanned wide (config.SCAN_YEAR_MIN to SCAN_YEAR_MAX) rather
than assuming config.YEAR_1 and YEAR_2 are the right pair. This check is what
decides the window; the config values are provisional until it passes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg

SPEC = {
    "service_date": ([r"srv_start_dt",
                      r"(srv|svc|service)_(start_)?(dt|date)",
                      r".*srv.*start.*dt", r".*service.*start.*date"],
                     "claim_line.service_date"),
}

MEMBER_PATTERNS = [r"member_id", r"mbr_id", r".*mbr.*id", r".*member.*id"]


def main():
    print("06_v4_year_completeness")
    c = cfg.resolved(cfg.T_CLAIM_LINE, SPEC)
    dt = cfg.date_expr(cfg.T_CLAIM_LINE, c["service_date"])
    print("    date expression            -> {}".format(dt))

    mbr = cfg.resolve_col(cfg.T_CLAIM_LINE, MEMBER_PATTERNS,
                          pin="claim_line.member_id", required=False)
    mbr_sel = "COUNT(DISTINCT {}) AS members".format(mbr) if mbr else "NULL AS members"
    if mbr:
        print("    member column              -> {}".format(mbr))
    else:
        print("    member column              -> not resolved; counts omitted")

    sql = """
    SELECT EXTRACT(YEAR  FROM {dt}) AS yr,
           EXTRACT(MONTH FROM {dt}) AS mo,
           COUNT(*) AS claim_lines,
           {mbr_sel}
    FROM `{t}`
    WHERE {dt} BETWEEN DATE({y0}, 1, 1) AND DATE({y1}, 12, 31)
    GROUP BY 1, 2
    ORDER BY 1, 2
    """.format(dt=dt, mbr_sel=mbr_sel, t=cfg.T_CLAIM_LINE,
               y0=cfg.SCAN_YEAR_MIN, y1=cfg.SCAN_YEAR_MAX)

    df = cfg.run_query(sql, label="V4")
    cfg.write_csv(df, "v4_monthly_volume.csv")
    if not len(df):
        raise SystemExit("no claim lines in the scanned window")

    print("")
    print("  claim lines by year and month (thousands):")
    grid = df.pivot_table(index="yr", columns="mo", values="claim_lines",
                          aggfunc="sum", fill_value=0)
    header = "  year  " + "".join("{:>8}".format(m) for m in grid.columns)
    print(header)
    for yr in grid.index:
        line = "  {:<6}".format(int(yr))
        line += "".join("{:>8,.0f}".format(grid.loc[yr, m] / 1000)
                        for m in grid.columns)
        print(line)

    q4 = df[df["mo"].isin([10, 11, 12])].groupby("yr")["claim_lines"].sum()
    full = df.groupby("yr")["claim_lines"].sum()

    pairs = []
    years = sorted(full.index)
    for i in range(1, len(years)):
        y1, y2 = int(years[i - 1]), int(years[i])
        if y1 not in q4.index or y2 not in q4.index or not q4[y1]:
            continue
        ratio = q4[y2] / q4[y1]
        pairs.append({
            "year_1": y1, "year_2": y2,
            "q4_year_1": int(q4[y1]), "q4_year_2": int(q4[y2]),
            "q4_ratio": round(float(ratio), 4),
            "full_year_1": int(full[y1]), "full_year_2": int(full[y2]),
            "within_10pct": bool(abs(ratio - 1.0) <= 0.10),
        })
    pdf = pd.DataFrame(pairs)
    cfg.write_csv(pdf, "v4_year_pairs.csv")

    print("")
    print("  Q4 completeness by consecutive year pair:")
    for _, r in pdf.iterrows():
        mark = "ok    " if r["within_10pct"] else "TAPER "
        print("    {} {} -> {}  Q4 ratio {:.3f}"
              .format(mark, int(r["year_1"]), int(r["year_2"]), r["q4_ratio"]))

    target = pdf[(pdf["year_1"] == cfg.YEAR_1) & (pdf["year_2"] == cfg.YEAR_2)]
    print("")
    if not len(target):
        print("  configured window {} -> {} not present in the data"
              .format(cfg.YEAR_1, cfg.YEAR_2))
        result = False
    else:
        t = target.iloc[0]
        print("  configured window {} -> {}: Q4 ratio {:.3f}"
              .format(cfg.YEAR_1, cfg.YEAR_2, t["q4_ratio"]))
        result = bool(t["within_10pct"])

    cfg.verdict("V4", "Q4 of year two within 10% of Q4 of year one for the "
                      "configured window", result)
    if result is False:
        ok = pdf[pdf["within_10pct"]] if len(pdf) else pdf
        if len(ok):
            best = ok.iloc[-1]
            print("  Move the window back. Latest settled pair: {} -> {}"
                  .format(int(best["year_1"]), int(best["year_2"])))
            print("  Update config.YEAR_1 / YEAR_2 and record the change as a "
                  "numbered decision in 00_docs/data_decisions.md.")
        else:
            print("  No consecutive pair passes. Investigate claim lag before "
                  "choosing any window.")


if __name__ == "__main__":
    main()
