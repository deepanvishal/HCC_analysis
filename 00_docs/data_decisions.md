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

*No decisions recorded yet.*
