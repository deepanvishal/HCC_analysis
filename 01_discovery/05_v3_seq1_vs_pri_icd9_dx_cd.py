"""
WHAT   V3. For claim lines present in both tables, does the diagnosis at
       sequence_id 1 in CLM_LN_X_ICD9_DX match pri_icd9_dx_cd on
       EMIS_CLAIM_LINE? Proves the sequence number means position on the claim.
GRAIN  summary is one row; the sample is one row per disagreeing code pair
INPUTS config.T_DX, config.T_CLAIM_LINE
OUTPUT 01_discovery/output/v3_seq1_vs_pri_icd9_dx_cd.csv
       01_discovery/output/v3_seq1_disagreements.csv

Pass  agreement above 95%
Fail  agreement below 80% - the sequence means something else
Gate 1 sign-off requires V3.

The comparison target is EMIS_CLAIM_LINE.pri_icd9_dx_cd, not the A870800
extract: the extract carries no claim_line_id (methodology Appendix A), so no
claim-line-grain join from it is possible, and pri_icd9_dx_cd is the same
field on the source table. See DD-01 in 00_docs/data_decisions.md.

DD-01 depends on EMIS_CLAIM_LINE.claim_line_id - named in prior docs, never
exercised in any query, no seeded default. If it does not resolve, this check
is blocked and fails with a named message.

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
    "sequence_id": ([r"sequence_id",
                     r"(icd9_)?(dx_)?seq(uence)?_(id|nbr|num|no|cd)",
                     r".*seq.*"], "dx.sequence_id"),
    "icd9_dx_cd": ([r"icd9_dx_cd", r"(icd9?_)?dx_cd",
                    r".*icd.*dx.*cd", r".*dx.*cd"], "dx.icd9_dx_cd"),
}

CLAIM_LINE_ID_PATTERNS = [r"claim_line_id", r"clm_ln_id",
                          r".*clm_ln.*id", r".*claim_line.*id"]

PRI_DX_SPEC = {
    "pri_icd9_dx_cd": ([r"pri_icd9_dx_cd", r"(pri|prmry|primary)_(icd9?_)?dx_cd",
                        r".*pri.*dx.*cd"], "claim_line.pri_icd9_dx_cd"),
}

NORM = "UPPER(TRIM(REPLACE({col}, '.', '')))"


def emis_claim_line_id():
    try:
        return cfg.resolve_col(cfg.T_CLAIM_LINE, CLAIM_LINE_ID_PATTERNS,
                               pin="claim_line.claim_line_id")
    except cfg.SchemaError as exc:
        print(exc)
        raise SystemExit(
            "V3 BLOCKED: no resolvable claim_line_id on EMIS_CLAIM_LINE.\n"
            "DD-01 rests on this column, and it was never exercised in any "
            "prior query. Without it V3, V6 and V7 cannot run, and Gate 1 "
            "cannot sign off. Paste the column list above back so the correct "
            "name can be pinned in schema_map.PINS.")


def main():
    print("05_v3_seq1_vs_pri_icd9_dx_cd")
    d = cfg.resolved(cfg.T_DX, DX_SPEC)
    emis_cll = emis_claim_line_id()
    print("  resolving columns on " + cfg.T_CLAIM_LINE)
    print("    claim_line_id              -> {}".format(emis_cll))
    c = cfg.resolved(cfg.T_CLAIM_LINE, PRI_DX_SPEC)

    base = """
    WITH seq1 AS (
      SELECT {d_cll} AS claim_line_id,
             {d_norm} AS icd9_dx_cd_seq1
      FROM `{t_dx}`
      WHERE SAFE_CAST({d_seq} AS INT64) = 1
    ),
    emis AS (
      SELECT {c_cll} AS claim_line_id,
             {c_norm} AS pri_icd9_dx_cd
      FROM `{t_cl}`
    ),
    j AS (
      SELECT e.claim_line_id AS claim_line_id, s.icd9_dx_cd_seq1,
             e.pri_icd9_dx_cd
      FROM emis e
      JOIN seq1 s ON s.claim_line_id = e.claim_line_id
    )
    """.format(d_cll=d["claim_line_id"],
               d_norm=NORM.format(col=d["icd9_dx_cd"]),
               d_seq=d["sequence_id"], t_dx=cfg.T_DX,
               c_cll=emis_cll,
               c_norm=NORM.format(col=c["pri_icd9_dx_cd"]),
               t_cl=cfg.T_CLAIM_LINE)

    summary_sql = base + """
    SELECT
      COUNT(*)                                                    AS compared_rows,
      COUNT(DISTINCT claim_line_id)                               AS compared_claim_lines,
      COUNTIF(icd9_dx_cd_seq1 = pri_icd9_dx_cd)                   AS agree,
      COUNTIF(icd9_dx_cd_seq1 != pri_icd9_dx_cd)                  AS disagree,
      COUNTIF(icd9_dx_cd_seq1 IS NULL OR pri_icd9_dx_cd IS NULL)  AS null_either
    FROM j
    """

    df = cfg.run_query(summary_sql, label="V3 summary")
    cfg.write_csv(df, "v3_seq1_vs_pri_icd9_dx_cd.csv")

    if not len(df) or not df.iloc[0]["compared_rows"]:
        raise SystemExit("no claim lines are present in both tables. "
                         "Check the join key on EMIS_CLAIM_LINE - it is one of "
                         "the three never-exercised names.")

    r = df.iloc[0]
    rows = int(r["compared_rows"])
    lines = int(r["compared_claim_lines"])
    agree = int(r["agree"])
    rate = agree / rows

    print("")
    print("  rows compared          {:,}".format(rows))
    print("  distinct claim lines   {:,}".format(lines))
    if rows != lines:
        print("  NOTE: more rows than claim lines. sequence_id 1 is not "
              "unique per claim line; investigate before relying on it.")
    print("  agree                  {:,}".format(agree))
    print("  disagree               {:,}".format(int(r["disagree"])))
    print("  null on either side    {:,}".format(int(r["null_either"])))
    print("  agreement              {:.2%}".format(rate))

    sample_sql = base + """
    SELECT icd9_dx_cd_seq1, pri_icd9_dx_cd, COUNT(*) AS n
    FROM j
    WHERE icd9_dx_cd_seq1 != pri_icd9_dx_cd
    GROUP BY 1, 2
    ORDER BY n DESC
    LIMIT 200
    """
    dis = cfg.run_query(sample_sql, label="V3 disagreements")
    cfg.write_csv(dis, "v3_seq1_disagreements.csv")

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
              "v3_seq1_disagreements.csv before deciding.")


if __name__ == "__main__":
    main()
