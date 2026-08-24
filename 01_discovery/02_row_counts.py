"""
WHAT   Row count, storage size and partitioning metadata for every table this
       analysis needs. Establishes the scale each later query works against and
       whether the claim tables are date-partitioned.
GRAIN  one row per table
INPUTS __TABLES__ and INFORMATION_SCHEMA.PARTITIONS per dataset
OUTPUT 01_discovery/output/02_row_counts.csv
       01_discovery/output/02_partitions.csv

Row counts come from table metadata, not COUNT(*), so this script scans no
table data and costs nothing.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg


def meta_for(proj, ds):
    sql = """
    SELECT '{p}' AS project_id, '{d}' AS dataset_id,
           table_id AS table_name,
           row_count,
           size_bytes,
           TIMESTAMP_MILLIS(creation_time)     AS created,
           TIMESTAMP_MILLIS(last_modified_time) AS last_modified
    FROM `{p}.{d}.__TABLES__`
    """.format(p=proj, d=ds)
    return cfg.run_query(sql, label="{}.{}".format(proj, ds))


def partitions_for(table_fqn):
    proj, ds, tbl = cfg.split_fqn(table_fqn)
    sql = """
    SELECT '{f}' AS table_fqn,
           COUNT(*)                       AS partition_count,
           MIN(partition_id)              AS min_partition,
           MAX(partition_id)              AS max_partition,
           SUM(total_rows)                AS total_rows
    FROM `{p}.{d}.INFORMATION_SCHEMA.PARTITIONS`
    WHERE table_name = '{t}'
    """.format(f=table_fqn, p=proj, d=ds, t=tbl)
    return cfg.run_query(sql, label=tbl + " partitions")


def main():
    print("02_row_counts")

    meta = []
    for proj, ds in cfg.SEARCH_DATASETS:
        print("  reading metadata for {}.{}".format(proj, ds))
        try:
            meta.append(meta_for(proj, ds))
        except Exception as exc:
            print("    UNREADABLE: {}".format(exc))
    if not meta:
        raise SystemExit("no dataset metadata could be read")
    meta = pd.concat(meta, ignore_index=True)
    meta["fqn"] = (meta["project_id"] + "." + meta["dataset_id"]
                   + "." + meta["table_name"])

    rows = []
    for label in cfg.ALL_TABLES:
        fqn = cfg.ALL_TABLES[label]
        hit = meta[meta["fqn"] == fqn]
        if len(hit):
            r = hit.iloc[0]
            rows.append({
                "needed_as": label,
                "fqn": fqn,
                "found": True,
                "row_count": int(r["row_count"]) if pd.notna(r["row_count"]) else None,
                "size_gb": round(r["size_bytes"] / 1024 ** 3, 3)
                           if pd.notna(r["size_bytes"]) else None,
                "created": r["created"],
                "last_modified": r["last_modified"],
            })
        else:
            rows.append({"needed_as": label, "fqn": fqn, "found": False,
                         "row_count": None, "size_gb": None,
                         "created": None, "last_modified": None})
    counts = pd.DataFrame(rows)
    cfg.write_csv(counts, "02_row_counts.csv")

    parts = []
    for label in cfg.ALL_TABLES:
        fqn = cfg.ALL_TABLES[label]
        try:
            df = partitions_for(fqn)
        except Exception as exc:
            print("  partitions unreadable for {}: {}".format(label, exc))
            continue
        if len(df):
            df.insert(0, "needed_as", label)
            parts.append(df)
    if parts:
        cfg.write_csv(pd.concat(parts, ignore_index=True), "02_partitions.csv")

    print("")
    for _, r in counts.iterrows():
        if r["found"]:
            print("  {:<40} {:>15,} rows  {:>10} GB"
                  .format(r["needed_as"], r["row_count"] or 0, r["size_gb"]))
        else:
            print("  {:<40} NOT FOUND".format(r["needed_as"]))

    cfg.verdict(
        "02_row_counts",
        "every table in config.ALL_TABLES reports a row count",
        bool(counts["found"].all()))
    print("  Methodology section 8 expects roughly 40M claim lines and "
          "180M line-x-illness rows. Compare against the figures above.")


if __name__ == "__main__":
    main()
