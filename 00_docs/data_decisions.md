# Data decisions

Every choice that could have gone another way and changes a number. Numbered,
never renumbered, never deleted. A decision that turns out wrong gets a status
change and a superseding entry, so the reasoning stays visible.

Methodology Step 16: every choice is written down beside the result, because
someone will ask "how do you know?" about each number and the answer needs to
be on the page already.

## Format

```
## DD-nn  Short title

**Decision:** what was chosen, in one sentence.

**Alternatives:** what else was available, and what each would have changed.

**Rationale:** why this one. Evidence, not preference.

**Affects:** which figures move if this is wrong.

**Raised by:** script, check, or person. **Date:** YYYY-MM-DD.

**Status:** Active | Superseded by DD-nn | Reversed
```

## What belongs here

- Any column pinned in `schema_map.PINS`, with the reason the resolver could not choose
- A table resolved to a location the methodology did not specify
- Mapping raw business line codes to Medicare and commercial
- Which place-of-service codes count as office, hospital outpatient, inpatient
- Which codes are excluded as laboratory, equipment, ambulance, dental
- The year window, if V4 moves it off 2023/2024
- The minimum panel size, once the observed distribution is known
- Whether the two-mention rule uses separate dates or separate visits
- Which control condition runs alongside diabetes
- Any threshold changed from the value in methodology.md or validation.md

## What does not belong here

Facts about the data go in `data_model.md`. Things nobody has answered yet go
in `open_questions.md`. Assumption status changes go in `assumptions.md`.

---

## DD-01  V3 and V7 read the top-line diagnosis from EMIS_CLAIM_LINE, not the A870800 extract

**Decision:** the top-line comparison field for V3 and for V7's top-line arm is
`EMIS_CLAIM_LINE.pri_icd9_dx_cd`, joined to the diagnosis table at claim-line
grain within EMIS.

**Alternatives:** join `A870800_medicare_analysis_2025_claims` to
`CLM_LN_X_ICD9_DX`, as originally scripted. Not possible: methodology
Appendix A records that the extract does not carry `claim_line_id`, and the
operator-confirmed column list agrees, so no claim-line-grain join from it
exists. A fuzzy join on member and service date would attach diagnoses to the
wrong lines, which is exactly the failure V6 exists to prevent. The extract's
location is also unresolved (Q2) and its name suggests 2025 coverage while the
window is 2023-2024.

**Rationale:** `pri_icd9_dx_cd` on the source claim line is the same top-line
fact the extract carried forward, at the grain the comparison needs, in a table
whose location is confirmed. It also makes V7 a same-population comparison:
both arms count over identical claim lines, so the lift measures only the extra
positions.

**Affects:** V3 agreement rate; V7 top-line prevalence and lift. The 29%
any-HCC figure from the old extract remains context only.

**Raised by:** operator-supplied schema, 2026-08-24 session. **Date:** 2026-08-24.

**Status:** Active

## DD-02  Diabetes family derived from ICD-10 prefix E08-E13 when the mapping has no description

**Decision:** when `HCC_ICD_Mapping_2025` has no description column, the
diabetes HCC set is the distinct `HCC_v24` values reached by diagnosis codes
starting E08-E13, and the diabetes code set is every code mapping to those
HCCs.

**Alternatives:** hardcode the CMS-HCC V24 diabetes HCC numbers (asserts
values the table cannot confirm and hides a mapping-table defect); description
match (preferred, and still tried first, but the confirmed columns are
`diagnosis_code`, `HCC_v24`, `HCC_v28` only).

**Rationale:** E08-E13 is the ICD-10 diabetes mellitus chapter, verifiable
against the published code set. The derivation is printed and written to
`v7_diabetes_hcc_codes.csv` with the evidence per HCC, so the derived set is
confirmed rather than trusted (Q10). E12 is unused in ICD-10-CM and is included
only so a WHO-coded row would not slip past.

**Affects:** every diabetes figure in V7 and downstream.

**Raised by:** operator-supplied schema, 2026-08-24 session. **Date:** 2026-08-24.

**Status:** Active
