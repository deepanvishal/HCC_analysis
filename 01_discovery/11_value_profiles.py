"""
WHAT   Distinct-value profiles for the code columns whose value sets nobody has
       seen. Setting logic and the Medicare/commercial split cannot be written
       until these come back.
GRAIN  one row per (table, column, value)
INPUTS config.T_CLAIM_LINE, config.T_DX, config.T_MEMBERSHIP,
       config.T_PROVIDER_DM, config.T_A870800_2025_CLAIMS
OUTPUT 01_discovery/output/11_value_profiles.csv

Not a pass/fail check. Raw values only; no value is mapped or interpreted here.
A column that does not resolve is reported with the table's full column list
rather than skipped silently. A table that cannot be read (the unlocated ones)
is reported and the rest continue.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg

LIMIT = 10000

# (table label, table fqn, column label, patterns, pin)
TARGETS = [
    ("EMIS_CLAIM_LINE", cfg.T_CLAIM_LINE, "plc_srv_cd",
     [r"plc_srv_cd", r"(plc|place)_(of_)?(srv|service)_cd",
      r".*plc.*srv.*cd", r".*pos.*cd"], "claim_line.plc_srv_cd"),
    ("EMIS_CLAIM_LINE", cfg.T_CLAIM_LINE, "plc_srv_ctg_cd",
     [r"plc_srv_ctg_cd", r".*plc.*srv.*ctg.*", r".*place.*ctg.*"],
     "claim_line.plc_srv_ctg_cd"),
    ("EMIS_CLAIM_LINE", cfg.T_CLAIM_LINE, "business_ln_cd",
     [r"business_ln_cd", r"(business|bus)_(line|ln)_(cd|code)",
      r".*business.*ln.*"], "claim_line.business_ln_cd"),
    ("EMIS_CLAIM_LINE", cfg.T_CLAIM_LINE, "med_cost_ctg_cd",
     [r"med_cost_ctg_cd", r".*med.*cost.*ctg.*"], "claim_line.med_cost_ctg_cd"),
    ("CLM_LN_X_ICD9_DX", cfg.T_DX, "poa_cd",
     [r"poa_cd", r".*poa.*"], "dx.poa_cd"),
    ("membership", cfg.T_MEMBERSHIP, "business_ln_cd",
     [r"business_ln_cd", r"(business|bus)_(line|ln)_(cd|code)",
      r".*business.*ln.*"], "membership.business_ln_cd"),
    ("membership", cfg.T_MEMBERSHIP, "medical_ind",
     [r"medical_ind", r".*medical.*ind.*"], "membership.medical_ind"),
    ("membership", cfg.T_MEMBERSHIP, "state_postal_cd",
     [r"state_postal_cd", r"(mbr_)?(state|st)_(cd|code|abbr)", r"state"],
     "membership.state_postal_cd"),
    ("PROVIDER_DM", cfg.T_PROVIDER_DM, "specialty_ctg_cd",
     [r"specialty_ctg_cd", r".*specialty.*"], "provider.specialty_ctg_cd"),
    ("A870800_2025_claims", cfg.T_A870800_2025_CLAIMS, "specialty_ctg_cd",
     [r"specialty_ctg_cd", r".*specialty.*"], "a870800_2025_claims.specialty_ctg_cd"),
]


def profile(table_fqn, col):
    sql = """
    SELECT COALESCE(CAST({c} AS STRING), '(null)') AS value,
           COUNT(*) AS rows
    FROM `{t}`
    GROUP BY 1
    ORDER BY rows DESC
    LIMIT {lim}
    """.format(c=col, t=table_fqn, lim=LIMIT)
    return cfg.run_query(sql, label=col)


def main():
    print("11_value_profiles")
    frames = []
    failures = []

    for tlabel, fqn, clabel, patterns, pin in TARGETS:
        print("")
        print("  {} . {}".format(tlabel, clabel))
        try:
            col = cfg.resolve_col(fqn, patterns, pin=pin, required=False)
        except Exception as exc:
            print("    TABLE UNREADABLE: {}".format(exc))
            failures.append((tlabel, clabel, "table unreadable"))
            continue
        if not col:
            names = ", ".join(c for c, _ in cfg.columns_of(fqn))
            print("    COLUMN NOT FOUND. Columns present on {}:".format(fqn))
            print("      {}".format(names))
            failures.append((tlabel, clabel, "column not found"))
            continue
        print("    resolved -> {}".format(col))
        df = profile(fqn, col)
        total = df["rows"].sum()
        if len(df) == LIMIT:
            print("    NOTE: {} values returned; the list is TRUNCATED at the "
                  "limit and the shares below understate the tail.".format(LIMIT))
        df.insert(0, "table", tlabel)
        df.insert(1, "column", clabel)
        df.insert(2, "resolved_column", col)
        df["share"] = df["rows"] / total
        frames.append(df)
        print("    {} distinct values, {:,} rows. Top values:"
              .format(len(df), int(total)))
        for _, r in df.head(12).iterrows():
            print("      {:<24} {:>15,}  {:>7.2%}"
                  .format(str(r["value"])[:24], int(r["rows"]), r["share"]))

    if frames:
        out = pd.concat(frames, ignore_index=True)
        cfg.write_csv(out, "11_value_profiles.csv")

    print("")
    if failures:
        print("  unresolved targets:")
        for tlabel, clabel, why in failures:
            print("    {} . {}  ({})".format(tlabel, clabel, why))
        print("  Log each in 00_docs/open_questions.md. plc_srv_cd and "
              "plc_srv_ctg_cd are the highest-risk names in the build; if "
              "neither resolves, setting logic cannot be written.")
    else:
        print("  every target resolved and profiled.")
    print("  Paste the value lists into 00_docs/data_model.md. Mapping any of "
          "them (setting groups, Medicare vs commercial) is a numbered "
          "decision in 00_docs/data_decisions.md, not something this script "
          "or the extract may assume.")


if __name__ == "__main__":
    main()
