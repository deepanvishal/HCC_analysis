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

**Never assume a column name, table name, type, or grain.** Verify against the
live schema or `00_docs/data_model.md`. If you cannot verify it, say so and log
it in `00_docs/open_questions.md`.

**If you made an assumption, state it explicitly in your reply.** Do not bury
it.

**Do not invent results, sample data, or placeholder numbers** that could be
mistaken for real output.

**No invented vocabulary.** Use the source column names. Do not rename a
column to something clearer, and do not introduce a term the data does not
already use. Resolver keys, SPEC names, CSV headers and variables carry the
source column name, prefixed by a table shorthand only for disambiguation. If
a new name is genuinely unavoidable — a derived aggregate, a normalised join
key — say so and why.

**Heavy work runs in BigQuery, not in Python.** Aggregate, filter, join and
summarise in SQL and return only small result sets. The machine running this
has little memory. Never pull claim-line or member-level data into a DataFrame
to compute something SQL could have computed. pandas is for assembling small
result frames and writing CSVs, nothing else. This holds hardest in extract
and analysis, where the temptation to pull member-level rows will be
strongest.

---

## Where the code runs

Code is authored on a machine with no BigQuery credentials and executed on a
separate machine that has them. Do not check for `gcloud`, ADC, or credentials,
and do not attempt a connection from the authoring machine. Write every script
as if the environment is correct, runnable as-is when copied across. No
preflight script.

Nothing in this repo has been run against live data. `00_docs/data_model.md`
carries a NOT YET VERIFIED banner until it is rewritten from real discovery
output.

---

## Gate discipline

Checks run in four gates, defined in `00_docs/validation.md`. A gate must pass
before the next one starts.

| Gate | Question | Status |
|---|---|---|
| 1 Foundation | Can the data answer the question at all? | implemented, not run |
| 2 Build | Did the pipeline do what we intended? | not implemented |
| 3 Plausibility | Do the numbers describe a real population? | not implemented |
| 4 Fairness | Would this ranking be defensible if challenged? | not implemented |

**Gate 1 must pass before any extract code is written.** Sign-off requires V1,
V3, V6 and V7. Any failure stops the build. Run
`01_discovery/99_gate1_summary.py` for the current status; it reports from
recorded verdicts and shows a check that was never run as NOT RUN rather than
letting it pass silently.

If V1 fails, the illness table is top-line only and the deliverable becomes the
data-gap finding, not the analysis.

Do not implement a later gate before the one before it passes.

---

## Analysis rules

These are not style preferences. Each one prevents a specific wrong result.

**Never blend Medicare and commercial into one figure.** Commercial members are
decades younger with a fraction of the long-term illness, and
employer-sponsored coverage is not risk-adjusted at all. A doctor whose
patients are mostly commercial would score badly on the makeup of their patient
list alone. Every figure carries its book. Medicare is reported first.

**Never write anything that reads as encouraging providers to code more.** Any
material that appears to encourage recording conditions to raise revenue is a
serious problem regardless of intent. Frame every statement as the record
matching the patient. This applies to variable names, comments, chart titles,
and prose. V25 checks it before anything is circulated.

**Inpatient counts toward the patient picture, never toward a provider score.**
Two measures run side by side: recorded anywhere, which tells us what the
patient has, and recorded in a doctor's office, which tells us what a doctor
did. Hospital and laboratory records must not leak into the office-only score.
Office-only can only ever be equal to or lower than any-source; if it comes out
higher, the pipeline is wrong.

**Provider scores need a minimum panel size. No ranking without it.** With
eight patients, one unusual case swings a score by more than twenty points.
Doctors below the threshold are marked "not enough to tell," which is a real
answer rather than a gap. `config.MIN_PANEL` holds the provisional value of 30;
the real figure is checked against the observed distribution first. Doctors
just above the line have their score pulled partway toward their specialty
average.

**Confirmed means at least two mentions on separate dates.** A single mention
can be a possibility being ruled out, an old note copied forward, or a mistake.

**Report what each exclusion removes.** The count is part of the finding. If
most drops are patients who never came in, the problem is scheduling, not
recording, and the fix is different.

**Claims show what was written down, not what was true.** This is an argument
by elimination. Never describe it as proof.

---

## Data decisions

Every choice that could have gone another way and changes a number goes in
`00_docs/data_decisions.md`, numbered `DD-nn`, with the decision, the
alternatives, the rationale, what it affects, and who raised it. Numbers are
never reused and entries are never deleted; a decision that turns out wrong
gets a status change and a superseding entry.

That includes any column pinned in `schema_map.PINS`, any table resolved to a
location the methodology did not specify, the business line to book mapping,
the place-of-service groupings, the year window if V4 moves it, and any
threshold changed from the value in the methodology or validation docs.

Facts about the data go in `data_model.md`. Unanswered things go in
`open_questions.md`. Assumption status changes go in `assumptions.md`.

---

## Conventions

Python and BigQuery. Numbered filenames. CSV outputs. Each script standalone
and rerunnable.

**Docstring per script**, in this form and this order:

```
"""
WHAT   what the script does, and why it matters
GRAIN  one row per what
INPUTS tables and files read
OUTPUT files written
"""
```

For a validation check, follow it with the pass and fail criteria and whether
it is a sign-off check.

**A confirmation gate before anything expensive.** `config.run_query` dry-runs
every query, prints the bytes, and prompts above `config.CONFIRM_GB`. Set
`HCC_YES=1` for batch runs. Never bypass the gate by calling the client
directly.

**Column names come from the seeded resolver, never hardcoded in SQL.**
Resolution order in `config.resolve_col`: `schema_map.PINS` (operator
override, must exist), `schema_map.DEFAULTS` (operator-attested names, used
when present in the live schema), then INFORMATION_SCHEMA pattern search. It
raises on ambiguity and raises when nothing matches, printing the table's full
actual column list so the correct name can be pasted back in one trip. It
never guesses.

Three names have no default on purpose — named in prior docs, never exercised
in any query, and everything about setting and the diagnosis join depends on
them: `EMIS_CLAIM_LINE.claim_line_id`, `plc_srv_cd`, `plc_srv_ctg_cd`. The
resolver must find and report these.

The resolver is scaffolding for the first discovery trip. Once discovery runs,
record the resolved names in `data_model.md` and switch the scripts to explicit
constants. Do not add a pin to work around a resolver failure without first
checking that the column is the right one; every pin is a numbered decision in
`data_decisions.md`.

**Dates are not assumed to be DATE.** `config.date_expr` picks the conversion
from the declared type and raises on a type it has no rule for.

---

## Layout

```
config.py            client, constants, paths, cost gate, column resolver
schema_map.py        seeded default column names + operator pins
00_docs/
  methodology.md     what we measure and why
  validation.md      the four gates
  data_model.md      real schema, NOT YET VERIFIED
  data_decisions.md  numbered choices
  assumptions.md     A1-A10 from methodology section 9
  open_questions.md  unanswered, with what each blocks
  run_log.md         what was run and what came back
01_discovery/        schema, profiling, Gate 1 only
02_extract/          empty until Gate 1 passes
03_analysis/         empty
04_output/           empty
```

Run order in `01_discovery`: `00_list_tables`, `01_columns`, `02_row_counts`,
`11_value_profiles`, then `03` through `10` for V1 to V8, then
`99_gate1_summary`. The standalone runbook for the machine with credentials is
`00_docs/run_order.md`.

---

## Current state

Discovery and structure only. No extract or analysis code has been written, and
none should be until Gate 1 signs off.

Column names are seeded from operator observation (2026-08-24) in
`schema_map.DEFAULTS`; none is discovery-confirmed yet. Two data decisions are
recorded: DD-01 retargets V3 and V7's top-line arm to
`EMIS_CLAIM_LINE.pri_icd9_dx_cd` (the A870800 extract carries no
claim_line_id), and DD-02 derives the diabetes family from ICD-10 prefix
E08-E13 when the mapping has no description column.

Twenty questions are recorded, eighteen still open. `PROVIDER_DM` and the
CCIR table have locations from the prior repo's SQL (Q1, Q3 - answered); the
A870800 extract's location is still unknown (Q2). The three never-exercised
column names everything about setting and the diagnosis join depends on
remain unconfirmed. No value list has been seen for any code column;
`11_value_profiles.py` exists for that, and the setting logic and
Medicare/commercial split cannot be written until it comes back.
