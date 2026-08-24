"""
WHAT   Seeded column names and operator pins for the runtime resolver.
GRAIN  one entry per logical column
INPUTS operator observation (2026-08-24); after discovery, data_model.md
OUTPUT none (imported by config)

Resolution order in config.resolve_col:
  1. PINS      operator override. Must exist on the table or the run fails.
  2. DEFAULTS  seeded name. Used when it exists in the live schema. When it
               does not, the resolver prints a note and falls through.
  3. patterns  INFORMATION_SCHEMA search, most specific first. Raises on
               ambiguity rather than guessing.
  4. failure   prints the table's full actual column list with types, so the
               correct name can be pasted back in one trip.

DEFAULTS provenance, by tier:
  grid      observed directly in a BigQuery SELECT * result grid, 2026-08-24.
            The grid had a horizontal scrollbar, so the table's column list is
            probably complete but not certainly.
  sql       used in working SQL in the medicare_analysis repo.
  (absent)  named in medicare_analysis DD 07 but never exercised in any query.
            No default on purpose - the resolver must find and report these:
              claim_line.claim_line_id   join key to the diagnosis table
              claim_line.plc_srv         expected to carry IP / OP / F
              claim_line.plc_srv_ctg     coarser rollup above it
            These three are the highest-risk names in the build.

This layer is scaffolding for the first discovery trip. Once discovery runs,
record the resolved names in data_model.md and switch the scripts to explicit
constants. Every PIN added is a data decision: record it in
00_docs/data_decisions.md with the reason the resolver could not choose.
"""

DEFAULTS = {
    # CLM_LN_X_ICD9_DX - grid
    "dx.claim_line_id": "claim_line_id",
    "dx.dx_code": "icd9_dx_cd",        # ICD-10 content despite the name; dotted
    "dx.member_id": "member_id",
    "dx.poa": "poa_cd",
    "dx.sequence": "sequence_id",      # STRING, zero-padded '01'; SAFE_CAST first
    # also observed, audit only: ziw_target_timestamp, ziw_workflow_run_id

    # EMIS_CLAIM_LINE - sql
    "claim_line.member_id": "member_id",
    "claim_line.service_date": "srv_start_dt",
    "claim_line.topline_dx": "pri_icd9_dx_cd",
    "claim_line.business_line": "business_ln_cd",
    "claim_line.med_cost_ctg": "med_cost_ctg_cd",
    "claim_line.provider_id": "srv_prvdr_id",
    # claim_line.claim_line_id  - no default, see docstring
    # claim_line.plc_srv        - no default, see docstring
    # claim_line.plc_srv_ctg    - no default, see docstring

    # A870800_medicare_analysis_2025_claims - sql; location unresolved (Q2).
    # Carries no claim_line_id (methodology Appendix A), so it cannot join to
    # the diagnosis table at claim-line grain. See DD-01.
    "topline.member_id": "member_id",
    "topline.service_date": "srv_start_dt",
    "topline.dx_code": "pri_icd9_dx_cd",
    "topline.business_line": "business_ln_cd",
    "topline.provider_id": "epdb_dw_prvdr_id",
    "topline.specialty": "specialty_ctg_cd",

    # HCC_ICD_Mapping_2025 - sql. No description column confirmed; see DD-02.
    "hcc_map.icd_code": "diagnosis_code",
    "hcc_map.hcc_v24": "HCC_v24",
    "hcc_map.hcc_v28": "HCC_v28",

    # A870800_medicare_analysis_membership - sql. No death indicator (Q6).
    "membership.member_id": "member_id",
    "membership.period": "eff_dt",
    "membership.business_line": "business_ln_cd",
    "membership.state": "state_postal_cd",
    "membership.medical_ind": "medical_ind",

    # PROVIDER_DM - sql; location unresolved (Q1)
    "provider.provider_id": "provider_id",
    "provider.epdb_provider_id": "epdb_dw_prvdr_id",
    "provider.specialty": "specialty_ctg_cd",

    # ms_dc_ref_ccir - sql; location unresolved (Q3)
    "ccir.icd_code": "icd_code",
    "ccir.description": "icd_description",
    "ccir.chronic_indicator": "chronic_indicator",
}

PINS = {}
