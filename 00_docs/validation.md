# Provider Coding Consistency — Validation Plan v1

**Companion to:** Coding Consistency Methodology v1
**Status:** Draft for review

---

## How this works

Checks run in four gates. **A gate must pass before the next one starts.** The point is to fail early and cheaply, rather than discover a problem after a doctor's name is on a list.

| Gate | Question | Failure means |
|---|---|---|
| **1. Foundation** | Can the data answer the question at all? | Stop. The finding is the data gap |
| **2. Build** | Did the pipeline do what we intended? | Fix and rebuild |
| **3. Plausibility** | Do the numbers describe a real population? | Investigate before believing anything |
| **4. Fairness** | Would this ranking be defensible if challenged? | Do not circulate |

Every check states what passes, what fails, and what to do about it. Results are written to file, not read off a screen and forgotten — anyone asking six months from now should be able to see what was checked.

---

# Gate 1 — Foundation

Run these before writing any pipeline code. All are cheap: they read one or two columns.

### V1. Are there multiple illness positions?

**Checks:** the spread of sequence numbers across the whole illness table.
**Why:** everything depends on this. If only position 1 exists, the illness list is top-line only and the analysis cannot run.
**Pass:** numbers span 1 to roughly 12 for office visits, higher for hospital claims.
**Fail:** only 1 appears.
**On failure:** stop. The deliverable becomes the data-gap finding.
**Note:** sequence is stored as text with a leading zero. Convert to a number before comparing, or 10 sorts before 2.

### V2. How many illnesses per visit?

**Checks:** distribution of illness count per visit.
**Why:** confirms the fan-out is real rather than a handful of exceptions.
**Pass:** average clearly above 1. A visible tail beyond 10.
**Fail:** over 90% of visits carry exactly one.

### V3. Is position 1 the same as the old top-line field?

**Checks:** for visits present in both, does position 1 match the existing single-illness column?
**Why:** proves the sequence number means "position on the claim." Without this, we know there are several illnesses but not what their order signifies.
**Pass:** agreement above 95%.
**Fail:** agreement below 80% — the sequence means something else and needs investigating before use.

### V4. Are both years equally complete?

**Checks:** visit counts by month across all candidate years.
**Why:** a thin final year makes every doctor look like they stopped recording things. This is the most common way a comparison like this goes wrong.
**Pass:** the last three months of year two are within 10% of the same months in year one.
**Fail:** a visible taper.
**On failure:** move the window back a year rather than adjusting for it.

### V5. Do patients keep the same identifier?

**Checks:** how many patients appear in year one and not year two, split by whether they still have coverage.
**Why:** if identifiers change with product or plan, patients look like they left and their conditions look dropped.
**Pass:** patients with continuous coverage overwhelmingly appear in both years.
**Fail:** a large share of continuously covered patients missing from year two.

### V6. Does the visit link hold?

**Checks:** what share of visits find a match in the illness table, and whether the patient identifier agrees on both sides.
**Why:** if the join key is wrong, illnesses attach to the wrong patients — which produces confident, plausible, completely false results.
**Pass:** match rate above 95%, zero patient mismatches.
**Fail:** any patient mismatch at all. This is not a tolerance question.

### V7. What do we recover?

**Checks:** share of patients with any long-term condition, and with diabetes, computed two ways — top-line only versus every position.
**Why:** this is both a check and the headline finding. The existing extract records 29% of members with any condition; the corrected figure should be far higher.
**Pass:** diabetes lands near 25–30% for Medicare, 8–12% for commercial.
**Fail — too low:** something is still being filtered out.
**Fail — no change:** the extra positions carry nothing, and the rework was unnecessary. Report it either way.

### V8. Do the codes map?

**Checks:** share of distinct codes matching the condition list after removing dots.
**Why:** a formatting mismatch between the two sides silently drops conditions.
**Pass:** above 95% of codes that should map, do.
**Fail:** below 90%.

**Gate 1 sign-off:** V1, V3, V6 and V7 must all pass. Any failure stops the build.

---

# Gate 2 — Build

Run after the extract exists, before any result is computed.

### V9. Nothing was lost or invented in transit

**Checks:** row counts and distinct patient counts at each stage, against the stage before.
**Why:** a bad join silently multiplies rows. Counts that grow where they should shrink catch it immediately.
**Pass:** every step accounts for its inputs. Fan-out only where fan-out is intended.

### V10. The collapse worked

**Checks:** confirm one row per patient per year per condition after the collapse.
**Why:** if repeats survive, every count downstream is inflated.
**Pass:** exactly one row per combination.

### V11. Setting is assigned correctly

**Checks:** the spread of setting codes, and whether they agree with the type of provider.
**Why:** office visits drive the doctor's score. Hospital and lab records must not leak into it.
**Pass:** office visits are the largest category. Disagreement between setting and provider type is rare.
**Fail:** any category unassigned, or frequent disagreement.

### V12. Excluded sources really are excluded

**Checks:** confirm no laboratory, equipment, ambulance or dental records survive into the measurement.
**Why:** a lab record carries the ordering doctor's suspicion, not a confirmed diagnosis. Counting it invents conditions nobody diagnosed.
**Pass:** zero.

### V13. Retired codes are not being read as recoveries

**Checks:** codes present in year one and absent from year two — are they retired, or genuinely not used?
**Why:** the code list changes every October. A retired code looks exactly like a patient who got better.
**Pass:** no diabetes code changed status between the two years.
**On failure:** map old to new before comparing.

### V14. The two-mention rule behaves

**Checks:** how many patients are lost by requiring two mentions rather than one, and whether persistence differs between the two groups.
**Why:** the rule should remove errors and doubtful cases. If single-mention patients persist at a similar rate, they were probably real, and the rule is discarding good data.
**Pass:** single-mention patients persist noticeably less. Report both figures.

### V15. The fairness gates remove roughly what we expect

**Checks:** count removed at each gate — death, coverage, doctor change, no visit.
**Why:** each has a plausible range. Deaths in a Medicare population run a few percent a year. A gate removing far more than expected is a bug, not a finding.
**Pass:** each removal within a defensible range, and the reason for each documented.
**Fail:** any single gate removing more than a third of the group without explanation.

**Gate 2 sign-off:** V9, V10 and V12 must pass. V15 must be explained even where it passes.

---

# Gate 3 — Plausibility

Run once results exist, before anyone sees them.

### V16. Does the overall figure sit where published work would suggest?

**Checks:** the persistence rate across the whole population.
**Why:** published and industry sources put chronic condition carry-over roughly in the 65–85% range.
**Pass:** within or near that band.
**Fail — above 95%:** conditions are being carried forward somewhere. Look for stale problem lists or a pipeline error.
**Fail — below 50%:** a filter is too aggressive, or the years are not comparable.

### V17. Does the doctor-level spread look real?

**Checks:** the distribution of doctor scores.
**Why:** real behaviour varies smoothly. Odd shapes point at data problems.
**Pass:** a broad single peak with tails.
**Fail:** clustering at 0% or 100%, or two separate humps — usually two populations mixed together.

### V18. Do the extremes hold up individually?

**Checks:** read every visit for ten patients each from the highest and lowest scoring doctors.
**Why:** the single most effective check available. Aggregate numbers hide errors that are obvious in one patient's history.
**Pass:** each patient's story is coherent and consistent with their score.
**Fail:** any patient whose record contradicts their classification. Stop and find out why.

### V19. Does the control condition behave?

**Checks:** run the same measure on a condition that cannot resolve.
**Why:** any drop there is a recording failure with no recovery mixed in — the cleanest possible floor.
**Pass:** the control drops at a rate comparable to diabetes, supporting the argument that recording, not recovery, drives the result.
**Fail:** control persists far better than diabetes. Some diabetes drops may be genuine, and the claim must be weakened.

### V20. Do office-only and any-source diverge sensibly?

**Checks:** the gap between the two scores.
**Why:** office-only should be equal or lower. A large gap means conditions are being kept on the record by hospital admissions.
**Pass:** office-only at or below any-source.
**Fail:** office-only higher. Impossible by construction — the pipeline is wrong.

### V21. Do the two books stay separate?

**Checks:** confirm Medicare and commercial are never combined in any reported figure.
**Why:** commercial patients are far younger with far less long-term illness. Blending them makes doctor comparisons meaningless.
**Pass:** every figure labelled with its book.

**Gate 3 sign-off:** V16, V18 and V20 must pass.

---

# Gate 4 — Fairness

Run before any doctor's name leaves the analysis. These are not statistical checks; they are questions about whether the output is fit to act on.

### V22. Would each flagged doctor survive a challenge?

**Checks:** for every doctor on the list — how many patients, what is the confidence range, does the specialty comparison hold, does the sample review support it?
**Why:** a flagged doctor may get a conversation. That conversation should not be based on eleven patients and a coincidence.
**Pass:** every flagged doctor has enough patients, a range not spanning the peer average, and sample evidence consistent with the score.
**Fail:** remove from the list.

### V23. Is anyone being penalised for their patients?

**Checks:** compare flagged doctors against unflagged peers on patient age, illness burden, visit frequency and coverage stability.
**Why:** if flagged doctors systematically see sicker or less engaged patients, we are measuring the patients, not the doctor.
**Pass:** flagged and unflagged doctors are broadly similar on these measures.
**Fail:** adjust further, or restrict what the output claims.

### V24. Does the ranking hold under different choices?

**Checks:** rerun with the minimum patient count at 20 and 50, and with the two-mention rule relaxed to one.
**Why:** if a doctor only appears on the list under one specific set of choices, the finding is about our choices, not their behaviour.
**Pass:** the bottom group is largely the same across all versions.
**Fail:** report only the doctors who appear consistently.

### V25. Is the language safe to hand over?

**Checks:** read the output for anything that reads as an instruction to record more conditions.
**Why:** any material that appears to encourage recording conditions to raise revenue is a serious problem, regardless of intent. The finding is about accuracy, not volume.
**Pass:** every statement frames the goal as the record matching the patient.
**Fail:** rewrite before circulation.

### V26. Are the limits attached to the numbers?

**Checks:** does every figure leaving this analysis carry the assumptions behind it?
**Why:** numbers travel and lose their caveats. A slide reaching leadership without its limitations will be read as more certain than it is.
**Pass:** limitations on the same page as the numbers, not in an appendix.

**Gate 4 sign-off:** all six. No exceptions — this gate is the one protecting people.

---

## Open risks not closed by any check

**Retrospective coding records.** If the plan's own coders submitted conditions through the same feed, a doctor who records poorly will score well because someone else corrected it behind them. No check here detects this; it requires an answer from whoever owns risk adjustment. Currently assumed absent, unverified.

**One partial check available:** retrospective submissions tend to arrive in batches, clustered before deadlines and detached from any visit. A month-by-month count would show that shape if it exists. Worth running, but absence of the pattern is not proof of absence.

---

## Sign-off record

| Gate | Checks | Run by | Date | Result |
|---|---|---|---|---|
| 1 Foundation | V1–V8 | | | |
| 2 Build | V9–V15 | | | |
| 3 Plausibility | V16–V21 | | | |
| 4 Fairness | V22–V26 | | | |

---

*End of v1.*
