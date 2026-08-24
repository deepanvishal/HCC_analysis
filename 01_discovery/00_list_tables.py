"""
WHAT   Locate every table this analysis needs. Sweeps both datasets and
       matches every needed table against what is actually there, rather than
       trusting the locations in config. PROVIDER_DM and the CCIR table carry
       locations from the prior repo's SQL and should resolve on the first
       try; this sweep is the safety net for them and the search for the
       A870800 extract, whose location is still a guess (Q2).
GRAIN  one row per candidate table found in a searched dataset
INPUTS INFORMATION_SCHEMA.TABLES on the datasets in config.SEARCH_DATASETS
OUTPUT 01_discovery/output/00_tables_found.csv
       01_discovery/output/00_tables_expected.csv
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg

# Substrings that identify each table we need, matched case-insensitively
# against every table name in the searched datasets.
NEEDLES = {
    "CLM_LN_X_ICD9_DX": r"CLM_LN_X_ICD9_DX",
    "EMIS_CLAIM_LINE": r"EMIS_CLAIM_LINE",
    "HCC_ICD_Mapping_2025": r"HCC_ICD_Mapping",
    "A870800_medicare_analysis_membership": r"medicare_analysis_membership",
    "PROVIDER_DM": r"PROVIDER_DM",
    "A870800_medicare_analysis_2025_claims": r"medicare_analysis.*claims",
    "ms_dc_ref_ccir": r"ccir",
}


def inventory():
    frames = []
    for proj, ds in cfg.SEARCH_DATASETS:
        sql = """
        SELECT '{p}' AS project_id, '{d}' AS dataset_id,
               table_name, table_type, creation_time
        FROM `{p}.{d}.INFORMATION_SCHEMA.TABLES`
        """.format(p=proj, d=ds)
        print("  scanning {}.{}".format(proj, ds))
        try:
            frames.append(cfg.run_query(sql, label="{}.{}".format(proj, ds)))
        except Exception as exc:
            print("    UNREADABLE: {}".format(exc))
    if not frames:
        raise SystemExit("no dataset could be listed")
    return pd.concat(frames, ignore_index=True)


def main():
    print("00_list_tables")
    inv = inventory()
    print("  {} tables visible across {} datasets"
          .format(len(inv), len(cfg.SEARCH_DATASETS)))

    hits = []
    for label in NEEDLES:
        pat = NEEDLES[label]
        matched = inv[inv["table_name"].str.contains(pat, case=False, regex=True)]
        for _, r in matched.iterrows():
            hits.append({
                "needed": label,
                "project_id": r["project_id"],
                "dataset_id": r["dataset_id"],
                "table_name": r["table_name"],
                "table_type": r["table_type"],
                "fqn": "{}.{}.{}".format(r["project_id"], r["dataset_id"], r["table_name"]),
            })
    found = pd.DataFrame(hits)
    cfg.write_csv(found, "00_tables_found.csv")

    rows = []
    for label in cfg.ALL_TABLES:
        expected = cfg.ALL_TABLES[label]
        sub = found[found["needed"] == label] if len(found) else found
        exact = sub[sub["fqn"] == expected] if len(sub) else sub
        rows.append({
            "needed": label,
            "expected_fqn": expected,
            "location_confirmed_in_brief": label not in cfg.UNVERIFIED_TABLES,
            "exists_at_expected_fqn": bool(len(exact)),
            "candidates_found": len(sub),
            "candidate_fqns": "; ".join(sub["fqn"].tolist()) if len(sub) else "",
        })
    exp = pd.DataFrame(rows)
    cfg.write_csv(exp, "00_tables_expected.csv")

    print("")
    for _, r in exp.iterrows():
        state = "OK " if r["exists_at_expected_fqn"] else "MISSING"
        print("  {:<7} {:<40} {}".format(state, r["needed"], r["expected_fqn"]))
        if not r["exists_at_expected_fqn"] and r["candidates_found"]:
            print("          candidates: {}".format(r["candidate_fqns"]))

    missing = exp[~exp["exists_at_expected_fqn"]]
    cfg.verdict(
        "00_list_tables",
        "every table in config.ALL_TABLES resolves to a real location",
        len(missing) == 0)
    if len(missing):
        print("  Resolve each missing table before running any V-check that "
              "reads it. Update config.T_* and log the decision in "
              "00_docs/data_decisions.md.")


if __name__ == "__main__":
    main()
