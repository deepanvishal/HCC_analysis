# CLAUDE.md

## The question

When a patient has a long-term illness, does their doctor write it down again
the following year? Phase 1 measures one condition — diabetes — in Florida,
comparing 2023 with 2024 under CMS-HCC V24, and reports what share of patients
a doctor recorded as diabetic in the first year that same doctor recorded again
in the second.

The goal is that the record matches the patient. It is not that more gets
recorded.

## Why this repo exists

A prior project (`medicare_analysis`) built a claims extract that kept only the
primary diagnosis per claim line. Under it, 29% of members appear to have any
HCC, which is far too low for a population including Medicare. A separate
table, `CLM_LN_X_ICD9_DX`, holds every diagnosis position — up to 36 per claim
line. Recovering those positions is the point of this repo.

---

## Standing rules

**Confirm before executing anything.** Show what you intend to run and wait.
This applies to queries, builds, file writes, and any command with a cost or
side effect.

**Short answer first.** Elaborate only when asked.

**No fluff code.** No unnecessary comments. No emojis anywhere — not in code,
docs, output, commit messages, or replies.

**Never assume a column name, table name, type, or grain.** If you cannot
verify it, say so and log it in `00_docs/open_questions.md`.

**If you made an assumption, state it explicitly in your reply.** Do not bury
it.

**Do not invent results, sample data, or placeholder numbers** that could be
mistaken for real output.

**No invented vocabulary.** Use the source column names. Do not rename a
column to something clearer, and do not introduce a term the data does not
already use. A derived aggregate or a normalised join key needs some name;
where one is genuinely unavoidable, say so and why.

**Heavy work runs in BigQuery, not in Python.** Aggregate, filter, join and
summarise in SQL and return only small result sets. In this repo the rule is
structural: Gate 1 is SQL and nothing else.

---

## How this repo runs

Gate 1 is eleven flat SQL files at the repo root, run by hand in the BigQuery
console (DD-03). No config, no runner script, no makefile, no wrapper, no
local runtime. SELECT only — no CREATE, no INSERT, no writes anywhere in
Gate 1.

Table locations are hardcoded fully-qualified, verified against the prior
repo's SQL. Column names are the operator-attested source names; none is
live-verified until 01_columns.sql has been run. A wrong name surfaces as
BigQuery's "Unrecognized name" error, which names the problem exactly — fix
the file by hand and record the real name in `00_docs/data_model.md`.

Three names were never exercised in any prior query and are the highest-risk
in the build: `EMIS_CLAIM_LINE.claim_line_id`, `plc_srv_cd`,
`plc_srv_ctg_cd`. V3, V6 and V7 all depend on the first existing; if it does
not, they cannot run and Gate 1 cannot sign off (DD-01).

The year window 2023/2024 and the Florida scope are hardcoded inline in files
07-09. V4 confirms the window or moves it back; moving it means editing those
files by hand and a numbered decision.

Nothing in this repo has been run against live data. `00_docs/data_model.md`
carries a NOT YET VERIFIED banner until it is rewritten from the
01_columns.sql result.

---

## Gate discipline

Checks run in four gates, defined in `00_docs/validation.md`. A gate must pass
before the next one starts.

| Gate | Question | Status |
|---|---|---|
| 1 Foundation | Can the data answer the question at all? | implemented as SQL, not run |
| 2 Build | Did the pipeline do what we intended? | not implemented |
| 3 Plausibility | Do the numbers describe a real population? | not implemented |
| 4 Fairness | Would this ranking be defensible if challenged? | not implemented |

**Gate 1 must pass before any extract code is written.** Sign-off requires V1,
V3, V6 and V7. Any failure stops the build. If V1 fails, the illness table is
top-line only and the deliverable becomes the data-gap finding, not the
analysis.

Do not implement a later gate before the one before it passes.

---

## Analysis rules

These are not style preferences. Each one prevents a specific wrong result.

**Never blend Medicare and commercial into one figure.** Commercial members are
decades younger with a fraction of the long-term illness, and
employer-sponsored coverage is not risk-adjusted at all. Every figure carries
its book. Medicare is reported first. This is why 09 produces no all-book
total.

**Never write anything that reads as encouraging providers to code more.** Any
material that appears to encourage recording conditions to raise revenue is a
serious problem regardless of intent. Frame every statement as the record
matching the patient. This applies to column aliases, comments, chart titles,
and prose. V25 checks it before anything is circulated.

**Inpatient counts toward the patient picture, never toward a provider score.**
Two measures run side by side: recorded anywhere, and recorded in a doctor's
office. Hospital and laboratory records must not leak into the office-only
score. Office-only can only ever be equal to or lower than any-source; if it
comes out higher, the pipeline is wrong.

**Provider scores need a minimum panel size. No ranking without it.** Doctors
below the threshold are marked "not enough to tell," which is a real answer
rather than a gap. 30 is the provisional value (methodology Appendix A),
checked against the observed distribution first.

**Confirmed means at least two mentions on separate dates.** A single mention
can be a possibility being ruled out, an old note copied forward, or a
mistake.

**Report what each exclusion removes.** The count is part of the finding.

**Claims show what was written down, not what was true.** This is an argument
by elimination. Never describe it as proof.

---

## Data decisions

Every choice that could have gone another way and changes a number goes in
`00_docs/data_decisions.md`, numbered `DD-nn`, with the decision, the
alternatives, the rationale, what it affects, and who raised it. Numbers are
never reused and entries are never deleted.

That includes any column name corrected by hand after a BigQuery error, the
business line to book mapping, the place-of-service groupings, the year window
if V4 moves it, and any threshold changed from the value in the methodology or
validation docs.

Facts about the data go in `data_model.md`. Unanswered things go in
`open_questions.md`. Assumption status changes go in `assumptions.md`. Runs
and results go in `run_log.md`.

---

## Conventions

Flat SQL files at the repo root, numbered, nothing importing anything.

**Header comment per file**, in this form:

```
-- WHAT   what it checks
-- WHY    why it matters
-- PASSES the pass criterion, carried from validation.md
-- FAILS  the fail criterion, carried from validation.md
-- ON FAILURE  what to do
```

Criteria are carried from `00_docs/validation.md`, never rewritten.

One query per file, or a small number of clearly separated queries with a
comment saying to run them one at a time. Fully-qualified table names inline —
no variables, no parameters, no scripting syntax. Label rows and columns so
the result explains itself without the file open beside it.

The console's estimated-bytes display (top right of the editor) replaces the
old cost gate: check it before running anything the header marks large.

---

## Layout

```
01_columns.sql ... 11_value_profiles.sql    Gate 1, flat at root
00_docs/
  methodology.md     what we measure and why
  validation.md      the four gates
  data_model.md      real schema, NOT YET VERIFIED
  data_decisions.md  numbered choices
  assumptions.md     A1-A10 from methodology section 9
  open_questions.md  unanswered, with what each blocks
  run_log.md         what was run and what came back
  run_order.md       the console runbook
```

Run order: 01, 02, 11, then the stop point (rewrite data_model.md), then
03-10, per `00_docs/run_order.md`.

---

## Current state

Gate 1 exists as SQL and has not been run. Two of twenty questions are
answered (Q1, Q3 — table locations from the prior repo's SQL); the A870800
extract's location is still unknown (Q2) and that table is dropped from
Gate 1. Three data decisions are recorded: DD-01 (top-line source is
EMIS_CLAIM_LINE.pri_icd9_dx_cd, with the claim_line_id dependency and the
29%-comparability caveat), DD-02 (diabetes family derived from the mapping by
ICD-10 prefix E08-E13), DD-03 (Gate 1 as plain SQL, no Python).

No extract or analysis code exists, and none is written until Gate 1 signs
off.
