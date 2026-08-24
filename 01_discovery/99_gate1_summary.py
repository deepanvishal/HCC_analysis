"""
WHAT   Gate 1 sign-off status. Reads the verdicts recorded by V1-V8 and reports
       whether extract code may be written.
GRAIN  one row per check
INPUTS 01_discovery/output/gate1_verdicts.csv
OUTPUT 01_discovery/output/99_gate1_summary.csv

Runs no queries. Reports only what the V-scripts recorded, so a check that was
never run shows as NOT RUN rather than silently passing.

Gate 1 sign-off requires V1, V3, V6 and V7. Any failure stops the build.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg

ALL_CHECKS = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]


def main():
    print("99_gate1_summary")
    path = cfg.repo_path(cfg.DISCOVERY_OUT, cfg.VERDICT_FILE)
    recorded = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(
        columns=["check", "criterion", "result"])

    rows = []
    for chk in ALL_CHECKS:
        hit = recorded[recorded["check"] == chk]
        rows.append({
            "check": chk,
            "required_for_signoff": chk in cfg.GATE1_REQUIRED,
            "result": hit.iloc[0]["result"] if len(hit) else "NOT RUN",
            "criterion": hit.iloc[0]["criterion"] if len(hit) else "",
        })
    df = pd.DataFrame(rows)
    cfg.write_csv(df, "99_gate1_summary.csv")

    print("")
    for _, r in df.iterrows():
        flag = "*" if r["required_for_signoff"] else " "
        print("  {} {:<4} {:<8} {}".format(flag, r["check"], r["result"],
                                           r["criterion"][:70]))
    print("  * required for sign-off")

    req = df[df["required_for_signoff"]]
    blocked = req[req["result"] != "PASS"]

    print("")
    if len(blocked):
        print("  GATE 1: NOT SIGNED OFF")
        for _, r in blocked.iterrows():
            print("    {} is {}".format(r["check"], r["result"]))
        print("  Do not write extract code. Resolve each item above, or record "
              "the reason it is acceptable as a numbered decision in "
              "00_docs/data_decisions.md and have it reviewed.")
    else:
        print("  GATE 1: SIGNED OFF")
        print("  V1, V3, V6 and V7 all pass. Record the sign-off in the table "
              "at the end of 00_docs/validation.md and in 00_docs/run_log.md, "
              "then extract code may be written.")

    non_pass = df[(~df["required_for_signoff"]) & (df["result"] != "PASS")]
    if len(non_pass):
        print("")
        print("  Not blocking, but unresolved: {}"
              .format(", ".join(non_pass["check"].tolist())))


if __name__ == "__main__":
    main()
