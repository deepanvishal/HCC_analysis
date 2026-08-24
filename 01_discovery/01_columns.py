"""
WHAT   Report the actual columns, types, nullability, partitioning and
       clustering for every table this analysis needs. The source of truth for
       00_docs/data_model.md. Also tests each column name asserted in the task
       brief and marks it confirmed or absent.
GRAIN  one row per (table, column)
INPUTS INFORMATION_SCHEMA.COLUMNS for each table in config.ALL_TABLES
OUTPUT 01_discovery/output/01_columns.csv
       01_discovery/output/01_brief_column_check.csv
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg

# Column names asserted in the task brief. Every one is unverified. This script
# reports which exist and on which table. Nothing downstream may rely on a name
# that does not come back confirmed here.
BRIEF_COLUMNS = [
    "claim_line_id",
    "sequence_id",
    "icd9_dx_cd",
    "poa_cd",
    "member_id",
    "plc_srv_cd",
    "plc_srv_ctg_cd",
    "med_cost_ctg_cd",
    "srv_prvdr_id",
    "epdb_dw_prvdr_id",
    "specialty_ctg_cd",
    "business_ln_cd",
    "srv_start_dt",
]


def columns_for(table_fqn):
    proj, ds, tbl = cfg.split_fqn(table_fqn)
    sql = """
    SELECT '{f}' AS table_fqn,
           ordinal_position,
           column_name,
           data_type,
           is_nullable,
           is_partitioning_column,
           clustering_ordinal_position
    FROM `{p}.{d}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{t}'
    ORDER BY ordinal_position
    """.format(f=table_fqn, p=proj, d=ds, t=tbl)
    return cfg.run_query(sql, label=tbl)


def main():
    print("01_columns")
    frames = []
    unreadable = []
    for label in cfg.ALL_TABLES:
        fqn = cfg.ALL_TABLES[label]
        print("  {}".format(fqn))
        try:
            df = columns_for(fqn)
        except Exception as exc:
            print("    UNREADABLE: {}".format(exc))
            unreadable.append(label)
            continue
        if not len(df):
            print("    NO COLUMNS - table absent at this location")
            unreadable.append(label)
            continue
        df.insert(0, "needed_as", label)
        print("    {} columns".format(len(df)))
        frames.append(df)

    if not frames:
        raise SystemExit("no table could be read")

    allcols = pd.concat(frames, ignore_index=True)
    cfg.write_csv(allcols, "01_columns.csv")

    lower = allcols.assign(lc=allcols["column_name"].str.lower())
    rows = []
    for name in BRIEF_COLUMNS:
        hit = lower[lower["lc"] == name.lower()]
        rows.append({
            "brief_column": name,
            "exists": bool(len(hit)),
            "found_on": "; ".join(
                "{} ({})".format(r["needed_as"], r["column_name"])
                for _, r in hit.iterrows()),
            "data_types": "; ".join(sorted(set(hit["data_type"]))) if len(hit) else "",
        })
    check = pd.DataFrame(rows)
    cfg.write_csv(check, "01_brief_column_check.csv")

    print("")
    print("  brief column names, verified against live schema:")
    for _, r in check.iterrows():
        state = "CONFIRMED" if r["exists"] else "ABSENT   "
        print("    {} {:<20} {}".format(state, r["brief_column"], r["found_on"]))

    absent = check[~check["exists"]]
    if len(absent):
        print("")
        print("  {} brief names are absent. Log each in "
              "00_docs/open_questions.md and find the real column in "
              "01_columns.csv before using it.".format(len(absent)))
    if unreadable:
        print("  UNREADABLE tables: {}".format(", ".join(unreadable)))

    cfg.verdict(
        "01_columns",
        "every table in config.ALL_TABLES returns a column list",
        len(unreadable) == 0)
    print("  Next: write 00_docs/data_model.md from 01_columns.csv.")


if __name__ == "__main__":
    main()
