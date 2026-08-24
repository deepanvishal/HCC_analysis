"""
WHAT   V7. Share of members recorded with diabetes in year one, computed two
       ways: from pri_icd9_dx_cd only, and from every diagnosis position in
       CLM_LN_X_ICD9_DX. Both a check and the headline finding of this repo.
GRAIN  diabetes HCC list is one row per HCC; the result is one row per
       (business_ln_cd, method)
INPUTS config.T_MEMBERSHIP, config.T_CLAIM_LINE, config.T_DX, config.T_HCC_MAP
OUTPUT 01_discovery/output/v7_diabetes_hcc_codes.csv
       01_discovery/output/v7_business_ln_cd.csv
       01_discovery/output/v7_diabetes_share.csv

Pass  diabetes lands near 25-30% for Medicare and 8-12% for commercial
Fail (too low)     something is still being filtered out
Fail (no change)   the extra positions carry nothing. Report either way.
Gate 1 sign-off requires V7.

Both arms read raw EMIS_CLAIM_LINE per DD-01. COMPARABILITY: the 29% any-HCC
figure came from the curated extract under its own filters -
summarized_srv_ind = 'Y', duplicate_ind = 'N', dental excluded via
med_cost_ctg_cd, DPPO excluded via ntwk_srv_area_id, footprint submarkets
only. Raw EMIS_CLAIM_LINE applies none of them. The difference between the two
arms is the finding and stays valid, because both arms share one population.
The absolute pri_icd9_dx_cd-only share is NOT the 29% and must not be
presented as its replacement.

DD-01 depends on EMIS_CLAIM_LINE.claim_line_id - named in prior docs, never
exercised in any query, no seeded default. If it does not resolve, this check
is blocked and fails with a named message.

The diabetes HCC set is derived from the mapping table: by description match
where a description column exists, otherwise from the ICD-10 diabetes chapter
prefix E08-E13. The derived set is printed for confirmation either way. See
DD-02 and Q10.

Business line values are reported raw: mapping them to Medicare and commercial
is a numbered data decision, not an assumption this script makes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config as cfg

MAP_SPEC = {
    "diagnosis_code": ([r"diagnosis_code", r"icd_?(10)?_?(cd|code)",
                        r"(dx|diag(nosis)?)_(cd|code)", r".*icd.*(cd|code).*"],
                       "hcc_map.diagnosis_code"),
    "hcc_v24": ([r"hcc_v24", r"hcc_?v?24.*", r".*v24.*"], "hcc_map.hcc_v24"),
}
MAP_DESC_PATTERNS = [r"(hcc_)?(desc|description|label|name|long_name)",
                     r".*desc.*", r".*label.*"]

MEMBERSHIP_SPEC = {
    "member_id": ([r"member_id", r"mbr_id", r".*mbr.*id", r".*member.*id"],
                  "membership.member_id"),
    "eff_dt": ([r"eff_dt",
                r"(cvrg|covg|coverage|elig|eligibility|mbrshp|membership)_"
                r"(month|mth|mo|dt|date|yr_mo)",
                r"(eff|start|begin)_(dt|date)",
                r".*(month|yr_mo).*", r".*eff.*dt.*"],
               "membership.eff_dt"),
}
BOOK_PATTERNS = [r"business_ln_cd", r"(business|bus)_(line|ln)_(cd|code)",
                 r".*business.*ln.*", r".*lob.*", r".*product.*(cd|type)"]
STATE_PATTERNS = [r"state_postal_cd", r"(mbr_)?(state|st)_(cd|code|abbr)",
                  r"state", r".*state.*cd"]

CLAIM_LINE_ID_PATTERNS = [r"claim_line_id", r"clm_ln_id",
                          r".*clm_ln.*id", r".*claim_line.*id"]

CLAIM_SPEC = {
    "member_id": ([r"member_id", r"mbr_id", r".*mbr.*id", r".*member.*id"],
                  "claim_line.member_id"),
    "srv_start_dt": ([r"srv_start_dt", r"(srv|svc|service)_(start_)?(dt|date)",
                      r".*srv.*start.*dt", r".*service.*start.*date"],
                     "claim_line.srv_start_dt"),
    "pri_icd9_dx_cd": ([r"pri_icd9_dx_cd", r"(pri|prmry|primary)_(icd9?_)?dx_cd",
                        r".*pri.*dx.*cd"], "claim_line.pri_icd9_dx_cd"),
}

DX_SPEC = {
    "claim_line_id": ([r"claim_line_id", r"clm_ln_id",
                       r".*clm_ln.*id", r".*claim_line.*id"], "dx.claim_line_id"),
    "icd9_dx_cd": ([r"icd9_dx_cd", r"(icd9?_)?dx_cd",
                    r".*icd.*dx.*cd", r".*dx.*cd"], "dx.icd9_dx_cd"),
}

NORM = "UPPER(TRIM(REPLACE({col}, '.', '')))"

# ICD-10 diabetes mellitus chapter. Used only when the mapping table has no
# description column. E12 is unused in ICD-10-CM; included so a WHO-coded row
# would not slip past. See DD-02.
DIABETES_ICD_PREFIX = r"^E(08|09|10|11|12|13)"


def emis_claim_line_id():
    try:
        return cfg.resolve_col(cfg.T_CLAIM_LINE, CLAIM_LINE_ID_PATTERNS,
                               pin="claim_line.claim_line_id")
    except cfg.SchemaError as exc:
        print(exc)
        raise SystemExit(
            "V7 BLOCKED: no resolvable claim_line_id on EMIS_CLAIM_LINE.\n"
            "DD-01 rests on this column, and it was never exercised in any "
            "prior query. Without it V3, V6 and V7 cannot run, and Gate 1 "
            "cannot sign off. Paste the column list above back so the correct "
            "name can be pinned in schema_map.PINS.")


def diabetes_hccs(mp, desc_col):
    """Distinct HCC_v24 values for diabetes, with the derivation printed.

    By description match when a description column exists; by ICD-10 prefix
    E08-E13 otherwise."""
    if desc_col:
        method = "description match on {}".format(desc_col)
        sql = """
        SELECT CAST({hcc} AS STRING) AS hcc_v24,
               ANY_VALUE({desc}) AS evidence,
               COUNT(DISTINCT {icd}) AS icd_codes
        FROM `{t}`
        WHERE LOWER({desc}) LIKE '%diabet%'
          AND {hcc} IS NOT NULL AND CAST({hcc} AS STRING) NOT IN ('', '0')
        GROUP BY 1
        ORDER BY 1
        """.format(hcc=mp["hcc_v24"], desc=desc_col, icd=mp["diagnosis_code"],
                   t=cfg.T_HCC_MAP)
    else:
        method = "ICD-10 prefix E08-E13 (no description column on the mapping)"
        sql = """
        SELECT CAST({hcc} AS STRING) AS hcc_v24,
               STRING_AGG({norm}, ', ' ORDER BY {norm} LIMIT 5) AS evidence,
               COUNT(DISTINCT {icd}) AS icd_codes
        FROM `{t}`
        WHERE REGEXP_CONTAINS({norm}, r'{pre}')
          AND {hcc} IS NOT NULL AND CAST({hcc} AS STRING) NOT IN ('', '0')
        GROUP BY 1
        ORDER BY 1
        """.format(hcc=mp["hcc_v24"], norm=NORM.format(col=mp["diagnosis_code"]),
                   icd=mp["diagnosis_code"], t=cfg.T_HCC_MAP,
                   pre=DIABETES_ICD_PREFIX)
    print("  diabetes HCC derivation: " + method)
    df = cfg.run_query(sql, label="V7 diabetes HCCs")
    df.insert(0, "derived_by", method)
    return df


def main():
    print("09_v7_diabetes_share")

    mp = cfg.resolved(cfg.T_HCC_MAP, MAP_SPEC)
    desc_col = cfg.resolve_col(cfg.T_HCC_MAP, MAP_DESC_PATTERNS,
                               pin="hcc_map.description", required=False)
    print("    description                -> {}".format(desc_col or "ABSENT"))

    hccs = diabetes_hccs(mp, desc_col)
    cfg.write_csv(hccs, "v7_diabetes_hcc_codes.csv")
    if not len(hccs):
        raise SystemExit("no diabetes HCCs derived from {}. Inspect the "
                         "mapping table before continuing."
                         .format(cfg.T_HCC_MAP))
    hcc_list = sorted(set(hccs["hcc_v24"].tolist()))
    print("")
    print("  diabetes HCCs derived from the mapping table - confirm against "
          "the CMS-HCC V24 definition (Q10):")
    for _, r in hccs.iterrows():
        print("    HCC {:<5} {:>6} codes   {}".format(
            r["hcc_v24"], int(r["icd_codes"]), str(r["evidence"])[:70]))
    in_list = ", ".join("'{}'".format(h) for h in hcc_list)

    m = cfg.resolved(cfg.T_MEMBERSHIP, MEMBERSHIP_SPEC)
    mdt = cfg.date_expr(cfg.T_MEMBERSHIP, m["eff_dt"])
    business_ln_cd = cfg.resolve_col(cfg.T_MEMBERSHIP, BOOK_PATTERNS,
                                     pin="membership.business_ln_cd",
                                     required=False)
    state_postal_cd = cfg.resolve_col(cfg.T_MEMBERSHIP, STATE_PATTERNS,
                                      pin="membership.state_postal_cd",
                                      required=False)
    book_sel = business_ln_cd if business_ln_cd else "'UNKNOWN'"
    print("    business_ln_cd             -> {}".format(business_ln_cd or "ABSENT"))
    print("    state_postal_cd            -> {}".format(state_postal_cd or "ABSENT"))
    if state_postal_cd:
        state_filter = "AND UPPER(TRIM({})) = '{}'".format(state_postal_cd,
                                                           cfg.STATE)
        print("    state filter applied       -> {}".format(cfg.STATE))
    else:
        state_filter = ""
        print("    state filter               -> NOT APPLIED; figures are "
              "all-states. Log in 00_docs/open_questions.md.")

    if business_ln_cd:
        bl = cfg.run_query("""
        SELECT {b} AS business_ln_cd, COUNT(DISTINCT {mid}) AS members
        FROM `{t}`
        WHERE EXTRACT(YEAR FROM {mdt}) = {y1} {sf}
        GROUP BY 1 ORDER BY members DESC
        """.format(b=business_ln_cd, mid=m["member_id"], t=cfg.T_MEMBERSHIP,
                   mdt=mdt, y1=cfg.YEAR_1, sf=state_filter),
                          label="V7 business_ln_cd")
        cfg.write_csv(bl, "v7_business_ln_cd.csv")
        print("")
        print("  business_ln_cd values present (raw, unmapped):")
        for _, r in bl.iterrows():
            print("    {:<20} {:,} members".format(str(r["business_ln_cd"]),
                                                   int(r["members"])))

        multi = cfg.run_query("""
        WITH per_member AS (
          SELECT {mid} AS member_id, COUNT(DISTINCT {b}) AS books
          FROM `{t}`
          WHERE EXTRACT(YEAR FROM {mdt}) = {y1} {sf}
          GROUP BY 1
        )
        SELECT COUNT(*) AS members, COUNTIF(books > 1) AS members_multi_book
        FROM per_member
        """.format(mid=m["member_id"], b=business_ln_cd, t=cfg.T_MEMBERSHIP,
                   mdt=mdt, y1=cfg.YEAR_1, sf=state_filter),
                              label="V7 multi-book members")
        mm = int(multi.iloc[0]["members_multi_book"])
        tot = int(multi.iloc[0]["members"])
        print("")
        print("  members holding more than one business_ln_cd in {}: {:,} of {:,}"
              .format(cfg.YEAR_1, mm, tot))
        if mm:
            print("  Those members are counted once under each of their values "
                  "in the table below, so the per-value denominators sum to "
                  "more than the distinct member count. Deciding which value "
                  "wins is open question Q9 and becomes a numbered decision.")

    emis_cll = emis_claim_line_id()
    print("  resolving columns on " + cfg.T_CLAIM_LINE)
    print("    claim_line_id              -> {}".format(emis_cll))
    c = cfg.resolved(cfg.T_CLAIM_LINE, CLAIM_SPEC)
    cdt = cfg.date_expr(cfg.T_CLAIM_LINE, c["srv_start_dt"])
    d = cfg.resolved(cfg.T_DX, DX_SPEC)

    sql = """
    WITH dm AS (
      SELECT DISTINCT {mnorm} AS diagnosis_code
      FROM `{t_map}`
      WHERE CAST({hcc} AS STRING) IN ({hcc_list})
    ),
    denom AS (
      SELECT DISTINCT {mid} AS member_id, {book} AS business_ln_cd
      FROM `{t_mem}`
      WHERE EXTRACT(YEAR FROM {mdt}) = {y1} {sf}
    ),
    y1_lines AS (
      SELECT {c_mid} AS member_id, {c_cll} AS claim_line_id,
             {pnorm} AS pri_icd9_dx_cd
      FROM `{t_cl}`
      WHERE EXTRACT(YEAR FROM {cdt}) = {y1}
    ),
    all_pos AS (
      SELECT DISTINCT l.member_id, TRUE AS flag
      FROM y1_lines l
      JOIN `{t_dx}` x ON x.{d_cll} = l.claim_line_id
      JOIN dm ON dm.diagnosis_code = {dnorm}
    ),
    pri_dx AS (
      SELECT DISTINCT l.member_id, TRUE AS flag
      FROM y1_lines l
      JOIN dm ON dm.diagnosis_code = l.pri_icd9_dx_cd
    )
    SELECT denom.business_ln_cd                            AS business_ln_cd,
           COUNT(*)                                        AS members,
           COUNTIF(a.flag IS NOT NULL)                     AS diabetes_icd9_dx_cd,
           COUNTIF(p.flag IS NOT NULL)                     AS diabetes_pri_icd9_dx_cd
    FROM denom
    LEFT JOIN all_pos a ON a.member_id = denom.member_id
    LEFT JOIN pri_dx  p ON p.member_id = denom.member_id
    GROUP BY denom.business_ln_cd
    ORDER BY members DESC
    """.format(mnorm=NORM.format(col=mp["diagnosis_code"]), t_map=cfg.T_HCC_MAP,
               hcc=mp["hcc_v24"], hcc_list=in_list,
               mid=m["member_id"], book=book_sel, t_mem=cfg.T_MEMBERSHIP,
               mdt=mdt, y1=cfg.YEAR_1, sf=state_filter,
               c_mid=c["member_id"], c_cll=emis_cll,
               pnorm=NORM.format(col=c["pri_icd9_dx_cd"]),
               t_cl=cfg.T_CLAIM_LINE, cdt=cdt,
               t_dx=cfg.T_DX, d_cll=d["claim_line_id"],
               dnorm=NORM.format(col="x." + d["icd9_dx_cd"]))

    df = cfg.run_query(sql, label="V7 shares")
    df["share_icd9_dx_cd"] = df["diabetes_icd9_dx_cd"] / df["members"]
    df["share_pri_icd9_dx_cd"] = df["diabetes_pri_icd9_dx_cd"] / df["members"]
    df["diff_pct_points"] = (df["share_icd9_dx_cd"]
                             - df["share_pri_icd9_dx_cd"]) * 100
    cfg.write_csv(df, "v7_diabetes_share.csv")

    print("")
    print("  diabetes share in {} by business_ln_cd:".format(cfg.YEAR_1))
    print("  {:<20} {:>12} {:>16} {:>16} {:>9}"
          .format("business_ln_cd", "members", "pri_icd9_dx_cd",
                  "every position", "diff pp"))
    for _, r in df.iterrows():
        print("  {:<20} {:>12,} {:>15.1%} {:>15.1%} {:>9.1f}"
              .format(str(r["business_ln_cd"]), int(r["members"]),
                      r["share_pri_icd9_dx_cd"], r["share_icd9_dx_cd"],
                      r["diff_pct_points"]))

    total_mem = df["members"].sum()
    total_all = df["diabetes_icd9_dx_cd"].sum()
    total_pri = df["diabetes_pri_icd9_dx_cd"].sum()
    rel_diff = (total_all - total_pri) / total_pri if total_pri else float("inf")
    print("")
    print("  overall pri_icd9_dx_cd    {:.1%}".format(total_pri / total_mem))
    print("  overall every position    {:.1%}".format(total_all / total_mem))
    print("  relative difference       {:.1%}".format(rel_diff))

    if rel_diff < 0.02:
        result = False
        note = ("No change. The extra positions carry nothing and the rework "
                "was unnecessary. Report this either way.")
    else:
        result = None
        note = ("Judge each business_ln_cd value against its own band: "
                "Medicare 25-30%, commercial 8-12%. The values are unmapped, "
                "so this script does not assign the bands. Record the mapping "
                "as a numbered decision in 00_docs/data_decisions.md.")

    cfg.verdict("V7", "diabetes near 25-30% for Medicare and 8-12% for "
                      "commercial, and the every-position share above the "
                      "pri_icd9_dx_cd share", result)
    print("  " + note)
    print("  COMPARABILITY: both arms read raw EMIS_CLAIM_LINE per DD-01, "
          "without the curated extract's filters (summarized_srv_ind, "
          "duplicate_ind, med_cost_ctg_cd, ntwk_srv_area_id, submarkets). "
          "The pri_icd9_dx_cd-only share above is NOT the extract's 29% "
          "any-HCC figure and must not be presented as its replacement. The "
          "finding is the difference between the two arms.")
    print("  Note: this script measures diabetes only. The any-condition "
          "figure needs ms_dc_ref_ccir, whose location is unresolved. See "
          "00_docs/open_questions.md.")


if __name__ == "__main__":
    main()
