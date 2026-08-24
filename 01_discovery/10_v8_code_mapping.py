"""
WHAT   V8. Share of distinct diagnosis codes in the claims data that are found
       in the HCC mapping table once dots are removed. A formatting mismatch
       between the two sides silently drops conditions.
GRAIN  format profile is one row per (side, code shape); the unmatched list is
       one row per code
INPUTS config.T_DX, config.T_HCC_MAP
OUTPUT 01_discovery/output/v8_code_formats.csv
       01_discovery/output/v8_code_mapping.csv
       01_discovery/output/v8_unmatched_codes.csv

Pass  above 95% of distinct codes match
Fail  below 90%

Match is measured against the mapping table as a whole, not against codes
carrying an HCC. Most diagnosis codes have no HCC; that is expected and is not
what this check is looking for.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg

DX_SPEC = {
    "icd9_dx_cd": ([r"icd9_dx_cd", r"(icd9?_)?dx_cd",
                    r".*icd.*dx.*cd", r".*dx.*cd"], "dx.icd9_dx_cd"),
}
MAP_SPEC = {
    "diagnosis_code": ([r"diagnosis_code", r"icd_?(10)?_?(cd|code)",
                        r"(dx|diag(nosis)?)_(cd|code)",
                        r".*icd.*(cd|code).*"], "hcc_map.diagnosis_code"),
    "hcc_v24": ([r"hcc_v24", r"hcc_?v?24.*", r".*v24.*"], "hcc_map.hcc_v24"),
}

NORM = "UPPER(TRIM(REPLACE({col}, '.', '')))"


def format_profile(table_fqn, col, side):
    sql = """
    SELECT '{s}' AS side,
           LENGTH(TRIM({c}))                     AS raw_length,
           STRPOS({c}, '.') > 0                  AS has_dot,
           COUNT(DISTINCT {c})                   AS distinct_codes,
           COUNT(*)                              AS rows
    FROM `{t}`
    WHERE {c} IS NOT NULL AND TRIM({c}) != ''
    GROUP BY 1, 2, 3
    ORDER BY rows DESC
    """.format(s=side, c=col, t=table_fqn)
    return cfg.run_query(sql, label="V8 format " + side)


def main():
    print("10_v8_code_mapping")
    d = cfg.resolved(cfg.T_DX, DX_SPEC)
    mp = cfg.resolved(cfg.T_HCC_MAP, MAP_SPEC)

    fmt = pd.concat([
        format_profile(cfg.T_DX, d["icd9_dx_cd"], "claims"),
        format_profile(cfg.T_HCC_MAP, mp["diagnosis_code"], "hcc_map"),
    ], ignore_index=True)
    cfg.write_csv(fmt, "v8_code_formats.csv")

    print("")
    print("  code shape on each side:")
    print("  {:<10} {:>10} {:>8} {:>16} {:>16}"
          .format("side", "length", "dotted", "distinct codes", "rows"))
    for _, r in fmt.head(20).iterrows():
        print("  {:<10} {:>10} {:>8} {:>16,} {:>16,}"
              .format(r["side"], int(r["raw_length"]), str(r["has_dot"]),
                      int(r["distinct_codes"]), int(r["rows"])))

    sql = """
    WITH claims AS (
      SELECT {dnorm} AS code, COUNT(*) AS dx_rows
      FROM `{t_dx}`
      WHERE {draw} IS NOT NULL AND TRIM({draw}) != ''
      GROUP BY 1
    ),
    mapping AS (
      SELECT {mnorm} AS code,
             LOGICAL_OR({hcc} IS NOT NULL
                        AND CAST({hcc} AS STRING) NOT IN ('', '0')) AS has_hcc
      FROM `{t_map}`
      WHERE {mraw} IS NOT NULL AND TRIM({mraw}) != ''
      GROUP BY 1
    )
    SELECT
      COUNT(*)                                          AS distinct_claim_codes,
      COUNTIF(m.has_hcc IS NOT NULL)                    AS matched_codes,
      COUNTIF(m.has_hcc IS NULL)                        AS unmatched_codes,
      SUM(c.dx_rows)                                    AS dx_rows,
      SUM(IF(m.has_hcc IS NOT NULL, c.dx_rows, 0))      AS matched_rows,
      COUNTIF(m.has_hcc)                                AS codes_with_hcc,
      SUM(IF(m.has_hcc, c.dx_rows, 0))                  AS rows_with_hcc
    FROM claims c
    LEFT JOIN mapping m ON m.code = c.code
    """.format(dnorm=NORM.format(col=d["icd9_dx_cd"]), draw=d["icd9_dx_cd"],
               t_dx=cfg.T_DX,
               mnorm=NORM.format(col=mp["diagnosis_code"]), mraw=mp["diagnosis_code"],
               hcc=mp["hcc_v24"], t_map=cfg.T_HCC_MAP)

    df = cfg.run_query(sql, label="V8 mapping")
    r = df.iloc[0]
    distinct = int(r["distinct_claim_codes"])
    if not distinct:
        raise SystemExit("no diagnosis codes found in " + cfg.T_DX)

    by_code = int(r["matched_codes"]) / distinct
    by_rows = int(r["matched_rows"]) / int(r["dx_rows"])
    out = df.copy()
    out["match_rate_by_code"] = by_code
    out["match_rate_by_volume"] = by_rows
    cfg.write_csv(out, "v8_code_mapping.csv")

    print("")
    print("  distinct claim codes    {:,}".format(distinct))
    print("  matched to mapping      {:,}  ({:.2%})"
          .format(int(r["matched_codes"]), by_code))
    print("  unmatched               {:,}".format(int(r["unmatched_codes"])))
    print("  match rate by volume    {:.2%}".format(by_rows))
    print("  codes carrying an HCC   {:,}".format(int(r["codes_with_hcc"])))
    print("  rows carrying an HCC    {:,}  ({:.1%})"
          .format(int(r["rows_with_hcc"]),
                  int(r["rows_with_hcc"]) / int(r["dx_rows"])))

    unmatched_sql = """
    WITH claims AS (
      SELECT {dnorm} AS code, COUNT(*) AS dx_rows
      FROM `{t_dx}`
      WHERE {draw} IS NOT NULL AND TRIM({draw}) != ''
      GROUP BY 1
    ),
    mapping AS (
      SELECT DISTINCT {mnorm} AS code FROM `{t_map}`
      WHERE {mraw} IS NOT NULL AND TRIM({mraw}) != ''
    )
    SELECT c.code AS code, c.dx_rows AS dx_rows
    FROM claims c
    LEFT JOIN mapping m ON m.code = c.code
    WHERE m.code IS NULL
    ORDER BY dx_rows DESC
    LIMIT 500
    """.format(dnorm=NORM.format(col=d["icd9_dx_cd"]), draw=d["icd9_dx_cd"],
               t_dx=cfg.T_DX,
               mnorm=NORM.format(col=mp["diagnosis_code"]), mraw=mp["diagnosis_code"],
               t_map=cfg.T_HCC_MAP)

    un = cfg.run_query(unmatched_sql, label="V8 unmatched")
    cfg.write_csv(un, "v8_unmatched_codes.csv")
    if len(un):
        print("")
        print("  highest-volume unmatched codes:")
        for _, x in un.head(15).iterrows():
            print("    {:<10} {:,} rows".format(str(x["code"]), int(x["dx_rows"])))

    if by_code > 0.95:
        result = True
    elif by_code < 0.90:
        result = False
    else:
        result = None

    cfg.verdict("V8", "above 95% of distinct codes match; fail below 90%", result)
    if result is not True:
        print("  Compare the shapes in v8_code_formats.csv. A whole-side "
              "length or dot difference is a formatting mismatch, not a "
              "coverage gap. Fix the normalisation before Gate 1 sign-off.")


if __name__ == "__main__":
    main()
