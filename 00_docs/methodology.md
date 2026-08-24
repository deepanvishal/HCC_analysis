# Provider Coding Consistency — Methodology v1

**Status:** Draft for review
**Scope of this phase:** Florida, diabetes, 2023 → 2024
**Model:** CMS-HCC V24, applied to both years
**Author:** Deepan

---

## 1. The question

When a patient has a long-term illness, does their doctor write it down again the following year?

That is the whole thing. Everything below builds toward answering it, and toward being able to say honestly how much we trust the answer.

### Why it matters

A patient's conditions do not carry over automatically between years. Each year, the record is built fresh from what was written down that year. A patient with diabetes whose diabetes was never noted in 2024 appears, on paper, to have stopped having diabetes.

This has two consequences pulling in opposite directions:

- Conditions that go unrecorded make patients look healthier than they are. Care management does not find them, and for Medicare the plan is funded as though they were well.
- Conditions that appear without justification create the opposite problem. Recording illnesses that are not supported by the medical record is what audits look for.

So the goal is not "record more." The goal is that the record matches the patient. This document measures the first problem. The second is named in Section 10 as out of scope for this phase, and it is out of scope deliberately, not by oversight.

---

## 2. What we are measuring, in one sentence

**Of the patients a doctor recorded as diabetic in the first year, what share did that same doctor record as diabetic again in the second year?**

Read that twice, because three things in it are deliberate:

- **"a doctor recorded"** — we judge each doctor on their own patients, not on an assigned panel. No patient-assignment file is needed, and every kind of doctor can be measured, not just primary care.
- **"that same doctor"** — if a different doctor picked it up, the plan's record is fine, but this doctor still did not do it. We measure both, separately.
- **"diabetic"** — one condition, not all conditions. Section 4 explains why.

---

## 3. Part A — Can the data answer the question at all?

These checks come first. If any of them fails, nothing built afterward is true, and the honest response is to stop and say so.

### Step 1. Confirm the records list every illness, not just the one they came in for

**Goal:** make sure a missing illness means the doctor did not write it down — not that our records only kept the headline.

**How this achieves it:** Most visits are for one thing: a cough, a sore knee. Long-term illnesses like diabetes are noted alongside, further down the page. If our records only keep the top line, then every diabetic who came in for a cough looks like their diabetes vanished, and the measurement is meaningless.

**What we know already:** the existing claims extract keeps only the top line. Its own documentation records the consequence — under it, 29% of members appear to have any long-term condition at all. For a population that includes Medicare, where most members carry several, that number is far too low to be real. A separate table holds the full list, with up to 36 illnesses recorded against a single visit. This step confirms that table behaves as expected and measures what it recovers.

### Step 2. Confirm a patient stays the same patient from one year to the next

**Goal:** do not mistake a bookkeeping change for a person disappearing.

**How this achieves it:** If a patient's identifier changes when their plan or product changes, they look like they left and a stranger arrived. Every one of their conditions would appear to drop. We count how many people are present in the first year and absent from the second, and ask whether that number is believable for a real population.

### Step 3. Confirm both years are equally finished

**Goal:** compare two complete years, not one complete year and one still being written.

**How this achieves it:** Bills arrive late. A visit in December may not reach us until March. Compare a settled year against an unfinished one and every doctor looks like they stopped recording things. We count visits month by month across both years. If the later year thins out toward the end, it is not finished, and we move the window rather than pretend.

---

## 4. Part B — Who and what are we looking at?

### Step 4. One illness first

**Goal:** one clear answer rather than four blurry ones.

**How this achieves it:** We start with diabetes. It is common, so most doctors have enough diabetic patients for their number to mean something. And it does not go away — so if it is missing this year, that is a real question rather than a maybe.

Measuring every illness at once mixes conditions that should never disappear with conditions that legitimately do. A heart attack should drop off the following year; that is correct, not a failure. Blended together, a single number means nothing, because there is no way to know what a good result would look like.

### Step 5. One place, and each kind of coverage kept separate

**Goal:** a group large enough to be meaningful and small enough to finish.

**How this achieves it:** Florida, because that is where we have the most patients and doctors.

We hold Medicare and commercial members apart throughout, and never combine them into a single number. They are different populations judged by different standards: commercial members are decades younger with a fraction of the long-term illness, and employer-sponsored coverage is not risk-adjusted at all. A doctor whose patients are mostly commercial would score badly on the makeup of their patient list alone, before anything about their behaviour entered into it.

Medicare is reported first, because that is where the measure has a definition, a published benchmark, and a consequence.

### Step 6. Two years, side by side

**Goal:** a fair before-and-after.

**How this achieves it:** The two most recent years that are both fully settled. The first is the "before" picture, the second the "after." Step 3 confirms which two years those are.

---

## 5. Part C — Build the picture

### Step 7. Turn codes into illness names

**Goal:** get from raw billing shorthand to something a person can reason about.

**How this achieves it:** Every illness on a bill is a code. An official list says which codes mean which conditions. We use the same version of that list for both years — otherwise a code retired in between looks exactly like a patient who got better.

### Step 8. Require more than one mention before calling it real

**Goal:** be sure the patient actually has the condition before holding anyone responsible for it going missing.

**How this achieves it:** A single mention can be a possibility being ruled out, an old note copied forward, or a straightforward mistake. If we treat a one-off mention as fact, and it disappears the following year, we would record a failure where the likeliest explanation is that the patient never had the condition.

So we require the condition to appear at least twice, on separate dates, before a patient enters the group being measured. This gives us a group we are confident about. It also makes the group smaller, and how much smaller is worth reporting in its own right: if a large share of apparent diabetics are single mentions, that is a finding about data quality regardless of anything else.

### Step 9. One line per patient per year

**Goal:** one clean fact per person per year, instead of hundreds of scattered bills.

**How this achieves it:** A patient might have twenty visits in a year with diabetes noted on twelve of them. That is still one fact: in this year, this person had diabetes recorded. We collapse it to a single entry. The repetition tells us nothing new, and left alone it would inflate every count made afterward.

We keep two versions of this fact side by side:

- **recorded anywhere** — including during a hospital stay
- **recorded in a doctor's office** — a clinician seeing the patient face to face

The first tells us what the patient has. The second tells us what a doctor did. Where the two differ, the condition is being kept on the record by hospital admissions rather than by ongoing care — which is worth knowing on its own.

### Step 10. Line the two years up

**Goal:** see, person by person, what carried over and what did not.

**How this achieves it:** For everyone confirmed diabetic in the first year, we look for diabetes in the second. It is either there or it is not. That yes/no is the entire measurement.

```
        Patient confirmed diabetic in year one
                        |
            +-----------+-----------+
            |                       |
      still recorded            missing
       in year two            in year two
            |                       |
        carried                 the thing
         over                worth asking about
```

---

## 6. Part D — Judge fairly

### Step 11. Set aside the people we cannot fairly judge

**Goal:** do not blame a doctor for something that was never theirs.

**How this achieves it:** A condition can vanish from the record for reasons that have nothing to do with the doctor. We remove each of them, one at a time:

| Reason the record went quiet | How we remove it |
|---|---|
| The patient died | Exclude patients not alive at the end of year two |
| They left the plan | Require unbroken coverage across both years |
| They changed doctors | Require the same doctor in both years |
| They never came in | Flag patients with no visit; count them separately |
| The code was retired, or moved within the diabetes family | Measure at the family level, using one code list for both years |

What is left after all five is the group where the question is genuinely open.

**We report how many patients each gate removes.** That count is part of the finding. If most of the drops turn out to be patients who never came in, then the problem is that people are not being seen — a scheduling problem, not a recording one, with an entirely different fix.

### Step 12. Score each doctor

**Goal:** turn one-patient answers into something comparable between doctors.

**How this achieves it:** Of all the diabetic patients a doctor had in the first year, what share still had it recorded in the second? Ninety out of a hundred is ninety percent.

Two scores per doctor: one counting any record, one counting only what happened in the doctor's own office.

### Step 13. Ignore doctors with too few patients

**Goal:** do not chase noise, and do not send someone to have a conversation that should not happen.

**How this achieves it:** With eight patients, one unusual case swings the score by more than twenty points. Only doctors with enough patients get a score. Everyone else is marked "not enough to tell," which is a real answer rather than a gap.

For doctors just above the line, we pull their score partway toward the average for their specialty — a small group tells us something, but less than a large one, and the score should say so.

### Step 14. Compare doctors to their own kind

**Goal:** make the comparison reflect the doctor, not their patients.

**How this achieves it:** A heart specialist and a family doctor see different people and should not be held to the same number. A doctor whose patients are older and sicker will look different again. So we group similar doctors together, and account for the age and illness burden of their patients, before comparing anyone to anyone.

---

## 7. Part E — Find the why

### Step 15. Read the stories behind the lowest scores

**Goal:** find the reason, not just the ranking.

**How this achieves it:** We take thirty to fifty patients from the lowest-scoring doctors and follow each one through the year. Did they come in at all? Did they see someone else instead? Was there a hospital stay in between?

The numbers only tell us where to look. The individual cases tell us what actually happened, and any recommendation has to rest on those rather than on the ranking.

### Step 16. Write down what we could not answer

**Goal:** make the result survive its first hard question.

**How this achieves it:** Every choice — every group excluded, every place a best guess stood in for a fact — is written down beside the result. Someone will ask "how do you know?" about each number. The answer needs to be on the page already, not reconstructed under pressure.

---

## 8. How the data moves

Row counts show shape, not estimates.

```
  claim lines               ~40M     one illness each
        |
        |  bring in every illness position
        v
  line x illness           ~180M     up to 36 per visit
        |
        |  name the conditions, mark the setting, drop the rest
        v
  labelled illnesses       ~180M
        |
        |  collapse to one fact per person per year
        v
  patient x year            ~2M
        |
        |  require 2+ mentions; pivot to two years
        v
  patient outcomes         ~400K     carried over / missing
        |
        |  fairness gates
        v
  judgeable patients       ~250K
        |
        |  roll up
        v
  doctors                    ~3K
        |
        |  minimum size, peer comparison
        v
  scoreable doctors        ~1.5K     ranked
```

Widen right out, then collapse hard. The widest point is the one currently missing.

### Worked example

Five patients, all recorded diabetic in 2023.

| Patient | 2024 | What actually happened | Verdict |
|---|---|---|---|
| A | recorded | seen twice, noted both times | carried over — counts |
| B | missing | seen twice, not noted | **missing — counts** |
| C | missing | died in March | removed — death |
| D | recorded | changed doctors | removed — different doctor |
| E | missing | no visits at all | flagged separately |

Only A and B answer the question. C, D and E would each have looked like a failure, and none of them is one.

Patient B is the case that matters, and the case the current extract cannot see: their diabetes was recorded in 2023 in the third position on a visit for something else. Under a top-line-only extract, B is not a diabetic in either year, and the failure is invisible.

---

## 9. Assumptions

Blocking assumptions must be resolved before any result is circulated.

| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | The illness-detail table carries every position, not just the first | **Confirmed** — up to 36 observed. Full check in validation V1–V3 | Analysis not possible; deliverable becomes the data-gap finding |
| A2 | Provider identifier is an individual clinician | **Confirmed** by data owner | Scores would describe practices, not people |
| A3 | Setting can be told from the place-of-service code | **Confirmed** — IP / OP / F | Cannot separate office from hospital |
| A4 | The commercial book mixes exchange and employer-sponsored | **Confirmed** | Already handled by reporting separately |
| A5 | No retrospective chart-review or health-assessment records in this data | **Assumed, not verified** | Doctors graded on work done by the plan's own coders. **Highest residual risk** |
| A6 | Patient identifiers are stable across years | Unverified — validation V5 | False drops |
| A7 | Both years are equally complete | Unverified — validation V4 | Every doctor looks worse in year two |
| A8 | Diabetes does not meaningfully resolve in this population | Clinically sound | Some drops are recoveries, not failures |
| A9 | The chronic-condition reference list is a reasonable stand-in for "should not disappear" | Approximate | Overstates the count of conditions that ought to persist |
| A10 | The visit link between the two claim tables is reliable | Unverified — validation V6 | Illnesses attached to the wrong visits |

---

## 10. What this cannot tell you

Stated plainly, because each of these will be asked.

**It cannot prove a condition was still present.** Claims show what was written down, not what was true. We remove every competing explanation we can identify — death, leaving, switching doctors, never attending, code changes — and report what is left. What is left is a mixture of conditions that went unrecorded and conditions that genuinely resolved, and claims cannot separate the two. For diabetes, genuine resolution is rare, which is why diabetes was chosen. It is an argument by elimination, not proof, and should never be described as proof.

**One way to strengthen it:** run a condition alongside that cannot possibly resolve — amputation status, for example. Any drop there is by definition a recording failure, with no recovery mixed in. If diabetes drops at a similar rate, resolution is not what is driving the number. Published work has found this pattern: among Medicare patients recorded with quadriplegia in one year, only 61% were recorded with it the next. Nobody recovers from quadriplegia.

**It does not cover conditions that appear without justification.** Requirements bullet four asks about new conditions against expected progression. That is the opposite failure and the one that carries audit risk. It needs a second measure — how often conditions newly appear — and a baseline for what normal looks like. Not in this phase, and named here so its absence is not mistaken for an oversight.

**It measures one condition.** Diabetes, not the full picture. The method extends to any condition; the numbers here do not.

**It measures doctors against their own patients.** Not against an assigned panel. A doctor is not held responsible for a patient who drifted away, and gets no credit for catching something a colleague missed. If a patient-assignment file becomes available, the panel view can be added as a second measure, and the gap between the two is itself informative.

**Money.** No dollar figure can be attached to the commercial side, because employer-sponsored coverage is not risk-adjusted. Any financial framing applies to Medicare only.

---

## 11. Relationship to published work

The central measure — the share of patients recorded with a condition in one year who are recorded again the next — appears in the health economics literature as **persistence**, most directly in McGuire et al., *Incidence, Persistence, and Steady-State Prevalence in Coding Intensity for Health Plan Payment* (Health Services Research, 2026). They break the prevalence of a condition into how often it newly appears and how often it carries over, and use the two together to project where coding practice would settle in the long run.

**What we take from it:** the persistence measure itself, unchanged.

**Where we differ, deliberately:**

| | Published work | This analysis |
|---|---|---|
| Unit | Whole population | Individual doctor |
| Grain | Each code separately | Condition family |
| Purpose | Explain national trends | Identify who to talk to |
| Newly appearing conditions | Measured | Not in this phase |

The move to doctor level introduces problems the published work never faced: small patient counts, differences in who each doctor sees, and the need to compare like with like. Sections 6 and 13 address these, and that machinery is ours to defend on its own terms.

**Caveat:** this comparison rests on the paper's abstract and summary, not a full reading. Before this framing is used externally, someone should read the paper and confirm the denominator construction matches — particularly how they handled deaths and continuous enrolment.

---

## 12. What the 24 August requirements ask for, and what this covers

| Requirement | Covered | Note |
|---|---|---|
| Document a provider-level methodology | **Yes** | This document |
| Share of patients with a stable picture | Partial | Diabetes only, not the full picture |
| Share of prior conditions recorded again | **Yes** | The central measure |
| Share dropped without evidence of recovery | Partial | By elimination, not proof. Section 10 |
| Newly appearing conditions vs expected | **No** | Needs the second measure. Section 10 |
| Doctor and specialty comparisons | **Yes** | Steps 12–14 |
| Doctors differing from benchmark | **Yes** | Step 14 |
| Sample review of causes | **Yes** | Step 15 |
| Summary presentation | Separate deliverable | |

---

## Appendix A — Technical detail

**Tables**

| Purpose | Table |
|---|---|
| Visits | `EMIS_CLAIM_LINE` |
| Illnesses per visit | `edp_hcb_core_cnsv.CLM_LN_X_ICD9_DX` |
| Existing curated extract (top-line only) | `A870800_medicare_analysis_2025_claims` |
| Code to condition | `HCC_ICD_Mapping_2025`, field `HCC_v24` |
| Long-term condition flag | `ms_dc_ref_ccir` (AHRQ CCIR v2026.1) |
| Coverage months | `A870800_medicare_analysis_membership` |
| Doctor detail | `PROVIDER_DM` |

**Columns needed that the current extract does not carry:** `claim_line_id` (the link to the illness list), `plc_srv_cd` (setting), and every illness position.

**Definitions**

- *Confirmed diabetic, year 1* — at least two records of a diabetes condition on separate service dates, from an acceptable setting
- *Carried over* — at least one record of a diabetes condition in year 2
- *Persistence rate* — carried over ÷ confirmed in year 1
- *Office-only persistence* — the same, counting only office-based records in year 2
- *Acceptable setting, patient picture* — hospital inpatient, hospital outpatient, doctor's office
- *Acceptable setting, doctor's score* — doctor's office only, individual clinician
- *Excluded throughout* — laboratory, equipment, ambulance, dental
- *Minimum for a score* — 30 confirmed diabetic patients

**Not yet decided**

- Exact minimum patient count (30 is a starting point, to be checked against the observed distribution)
- Which control condition to run alongside
- Whether the two-mention rule uses separate dates or separate visits

---

*End of v1. Comments to Deepan.*
