"""
WHAT   Pinned column names. Overrides the runtime resolver in config.resolve_col.
GRAIN  one entry per logical column
INPUTS 00_docs/data_model.md, once 01_discovery/01_columns.py has been run
OUTPUT none (imported by config)

Empty by design. The resolver searches INFORMATION_SCHEMA and succeeds on its
own wherever exactly one column matches. Add an entry here only when the
resolver reports AMBIGUOUS or UNRESOLVED, or when discovery shows it picked the
wrong column. The error message names the pin key to use and lists every column
on the table.

    PINS = {
        "dx.sequence": "DX_SEQ_NBR",
    }

Every pin is a data decision. Record it in 00_docs/data_decisions.md with the
reason the resolver could not choose, and reflect the confirmed name in
00_docs/data_model.md.
"""

PINS = {}
