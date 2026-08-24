# Run log

What was run, when, by whom, and what came back. validation.md: results are
written to file, not read off a screen and forgotten — anyone asking six months
from now should be able to see what was checked.

One entry per script execution that produced output. A rerun gets its own
entry; do not edit an old one.

## Format

```
## YYYY-MM-DD  script_name.py

**Run by:** name. **Machine:** where. **Duration:** approx. **Bytes billed:** from the dry run.

**Result:** PASS | FAIL | REVIEW | n/a for discovery scripts.

**Output:** files written, under 01_discovery/output/.

**What it showed:** two or three sentences. The number that matters, not a
restatement of the criterion.

**Action taken:** what changed as a result — a doc updated, a decision
recorded, a question closed, nothing.
```

## Gate sign-off

Record a gate sign-off here as well as in the table at the end of
`validation.md`. Gate 1 requires V1, V3, V6 and V7 to pass.
`99_gate1_summary.py` reports the status from the recorded verdicts.

---

*No runs recorded yet. Nothing in this repo has been executed against live
data.*
