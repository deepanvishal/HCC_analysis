"""
WHAT   Shared config for the HCC coding consistency analysis: BigQuery client,
       project/dataset/table constants, repo paths, CSV writer, cost gate, and
       the runtime column resolver.
GRAIN  n/a
INPUTS none
OUTPUT none (imported by every script)

Column names are never hardcoded in analysis SQL. Every column is obtained via
resolve_col(), which reads INFORMATION_SCHEMA at run time and raises unless
exactly one column matches. Confirmed names may be pinned in schema_map.PINS.
"""

import os
import re

# --- projects and datasets ---------------------------------------------------

CLIENT_PROJECT = "anbc-dev-prv-nc-ds"          # billing/auth project
EDP_PROJECT    = "edp-prod-hcbstorage"         # source claims
EDP_DATASET    = "edp_hcb_core_cnsv"
DEV_PROJECT    = "anbc-hcb-dev"                # curated / reference
DEV_DATASET    = "provider_ds_netconf_data_hcb_dev"


def edp(name):
    return "{}.{}.{}".format(EDP_PROJECT, EDP_DATASET, name)


def dev(name):
    return "{}.{}.{}".format(DEV_PROJECT, DEV_DATASET, name)


# --- tables ------------------------------------------------------------------
# Location confirmed by the task brief.
T_DX         = edp("CLM_LN_X_ICD9_DX")               # illness positions per claim line
T_CLAIM_LINE = edp("EMIS_CLAIM_LINE")                # claim lines / visits
T_HCC_MAP    = dev("HCC_ICD_Mapping_2025")           # code -> HCC (field HCC_v24)
T_MEMBERSHIP = dev("A870800_medicare_analysis_membership")

# Location NOT confirmed. Named in methodology Appendix A without a project or
# dataset. 01_discovery/00_list_tables.py searches for these.
# See 00_docs/open_questions.md Q1-Q3. Values below are starting points only.
T_PROVIDER_DM = dev("PROVIDER_DM")
T_TOPLINE     = dev("A870800_medicare_analysis_2025_claims")
T_CCIR        = dev("ms_dc_ref_ccir")

UNVERIFIED_TABLES = {
    "PROVIDER_DM": T_PROVIDER_DM,
    "A870800_medicare_analysis_2025_claims": T_TOPLINE,
    "ms_dc_ref_ccir": T_CCIR,
}

ALL_TABLES = {
    "CLM_LN_X_ICD9_DX": T_DX,
    "EMIS_CLAIM_LINE": T_CLAIM_LINE,
    "HCC_ICD_Mapping_2025": T_HCC_MAP,
    "A870800_medicare_analysis_membership": T_MEMBERSHIP,
}
ALL_TABLES.update(UNVERIFIED_TABLES)

# Datasets swept by 00_list_tables.py when a table's location is unknown.
SEARCH_DATASETS = [
    (DEV_PROJECT, DEV_DATASET),
    (EDP_PROJECT, EDP_DATASET),
]


# --- analysis scope ----------------------------------------------------------
# Phase 1 per methodology sections 4-6. YEAR_1/YEAR_2 are provisional: V4
# (06_v4_year_completeness.py) confirms both years are settled or moves the
# window back. Do not treat them as decided until V4 passes.

YEAR_1 = 2023
YEAR_2 = 2024
SCAN_YEAR_MIN = 2019          # V4 scans this wide before the window is fixed
SCAN_YEAR_MAX = 2025

STATE = "FL"
HCC_MODEL = "V24"             # applied to both years (methodology step 7)
MIN_PANEL = 30                # methodology Appendix A, provisional


# --- paths -------------------------------------------------------------------

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DISCOVERY_OUT = "01_discovery/output"


def repo_path(*parts):
    """Absolute path under the repo root, independent of CWD."""
    return os.path.join(_REPO_ROOT, *parts)


# --- client ------------------------------------------------------------------
# google.cloud.bigquery is imported lazily so this module stays importable for
# path and constant use without the SDK present.

_CLIENT = None


def client():
    """BigQuery client on the billing project. Credentials come from the
    ambient environment (ADC or GOOGLE_APPLICATION_CREDENTIALS)."""
    global _CLIENT
    if _CLIENT is None:
        from google.cloud import bigquery
        _CLIENT = bigquery.Client(project=CLIENT_PROJECT)
    return _CLIENT


# --- cost gate ---------------------------------------------------------------

CONFIRM_GB = float(os.environ.get("HCC_CONFIRM_GB", "50"))


def dry_run_bytes(sql):
    """Bytes the query would process. Free."""
    from google.cloud import bigquery
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    return client().query(sql, job_config=cfg).total_bytes_processed


def confirm(prompt):
    """Interactive gate. Set HCC_YES=1 to auto-accept in batch runs."""
    if os.environ.get("HCC_YES") == "1":
        print(prompt + " -> auto-accepted (HCC_YES=1)")
        return True
    try:
        return input(prompt + " [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def run_query(sql, label=""):
    """Dry-run, gate on size, execute, return a DataFrame.

    Rows are materialised as dicts so no db-dtypes dependency is needed."""
    import pandas as pd
    gb = dry_run_bytes(sql) / 1024 ** 3
    tag = " [{}]".format(label) if label else ""
    print("  dry run{}: {:.2f} GB".format(tag, gb))
    if gb > CONFIRM_GB:
        msg = "  {:.2f} GB exceeds {:.0f} GB. Run anyway?".format(gb, CONFIRM_GB)
        if not confirm(msg):
            raise SystemExit("aborted at cost gate")
    rows = [dict(r) for r in client().query(sql).result()]
    return pd.DataFrame(rows)


def write_csv(df, filename, subdir=DISCOVERY_OUT):
    """Write a DataFrame to subdir/filename and return the absolute path."""
    path = repo_path(subdir, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print("  wrote {}  ({} rows)".format(os.path.relpath(path, _REPO_ROOT), len(df)))
    return path


VERDICT_FILE = "gate1_verdicts.csv"

# Gate 1 sign-off requires these four (validation.md, Gate 1 sign-off).
GATE1_REQUIRED = ["V1", "V3", "V6", "V7"]


def verdict(check, criterion, passed):
    """Print the pass/fail criterion and the observed result for one check, and
    record it so 99_gate1_summary.py can report sign-off without rerunning
    anything.

    passed may be True, False, or None where the criterion needs a human call."""
    import pandas as pd
    mark = {True: "PASS", False: "FAIL", None: "REVIEW"}[passed]
    print("")
    print("  criterion: " + criterion)
    print("  {}: {}".format(check, mark))

    path = repo_path(DISCOVERY_OUT, VERDICT_FILE)
    row = {"check": check, "criterion": criterion, "result": mark}
    if os.path.exists(path):
        df = pd.read_csv(path)
        df = df[df["check"] != check]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df = df.sort_values("check").reset_index(drop=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return passed


# --- schema resolution -------------------------------------------------------

class SchemaError(LookupError):
    pass


_COL_CACHE = {}


def split_fqn(table_fqn):
    parts = table_fqn.split(".")
    if len(parts) != 3:
        raise ValueError("expected project.dataset.table, got " + repr(table_fqn))
    return parts


def columns_of(table_fqn):
    """[(column_name, data_type), ...] in ordinal order, from INFORMATION_SCHEMA."""
    if table_fqn in _COL_CACHE:
        return _COL_CACHE[table_fqn]
    proj, ds, tbl = split_fqn(table_fqn)
    sql = """
    SELECT column_name, data_type, ordinal_position
    FROM `{p}.{d}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{t}'
    ORDER BY ordinal_position
    """.format(p=proj, d=ds, t=tbl)
    rows = [(r["column_name"], r["data_type"]) for r in client().query(sql).result()]
    if not rows:
        raise SchemaError(
            "{} has no columns in INFORMATION_SCHEMA. The table does not exist "
            "at this location, or is not visible to {}. Run "
            "01_discovery/00_list_tables.py and see 00_docs/open_questions.md."
            .format(table_fqn, CLIENT_PROJECT))
    _COL_CACHE[table_fqn] = rows
    return rows


def _fail(table_fqn, patterns, cols, reason, hits=None):
    listing = "\n    ".join("{}  {}".format(c, t) for c, t in cols)
    extra = "\n  matched: " + ", ".join(hits) if hits else ""
    raise SchemaError(
        "\n{reason} on {tbl}"
        "\n  patterns tried: {pats}{extra}"
        "\n  columns present:\n    {listing}"
        "\n  Fix: add the correct name to schema_map.PINS, then rerun."
        .format(reason=reason, tbl=table_fqn, pats=patterns,
                extra=extra, listing=listing))


def resolve_col(table_fqn, patterns, pin=None, required=True):
    """The single column on table_fqn matching one of patterns.

    Resolution order:
      1. schema_map.PINS[pin]     - operator override; must exist or the run fails
      2. schema_map.DEFAULTS[pin] - seeded name; used when present in the live
                                    schema, otherwise a note is printed and the
                                    search falls through
      3. patterns                 - full-match regexes, case-insensitive, most
                                    specific first; a pattern matching more than
                                    one column raises rather than guessing
      4. failure                  - raises, printing the table's full actual
                                    column list for one-trip paste-back

    required=False returns None instead of raising when nothing matches, for
    genuinely optional columns.
    """
    import schema_map
    cols = columns_of(table_fqn)
    names = [c for c, _ in cols]

    if pin:
        pinned = schema_map.PINS.get(pin)
        if pinned:
            if pinned not in names:
                _fail(table_fqn, patterns, cols,
                      "PINNED column {} (pin={}) does not exist"
                      .format(repr(pinned), repr(pin)))
            return pinned
        default = schema_map.DEFAULTS.get(pin)
        if default:
            hit = [c for c in names if c.lower() == default.lower()]
            if len(hit) == 1:
                return hit[0]
            print("  NOTE: seeded default {} (pin={}) is not on {}; "
                  "falling back to pattern search"
                  .format(repr(default), repr(pin), table_fqn))

    for pat in patterns:
        hits = [c for c in names if re.fullmatch(pat, c, re.IGNORECASE)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            _fail(table_fqn, patterns, cols,
                  "AMBIGUOUS: pattern {} matched {} columns".format(repr(pat), len(hits)),
                  hits=sorted(hits))
    if not required:
        return None
    _fail(table_fqn, patterns, cols, "UNRESOLVED: no pattern matched any column")


def date_expr(table_fqn, col):
    """A DATE-typed SQL expression for col, chosen from its declared type.

    Avoids assuming the column is already a DATE. Raises on a type with no
    defined conversion rather than producing silently wrong results."""
    types = dict(columns_of(table_fqn))
    t = types[col].upper()
    if t == "DATE":
        return col
    if t in ("DATETIME", "TIMESTAMP"):
        return "DATE({})".format(col)
    if t == "STRING":
        return ("COALESCE(SAFE.PARSE_DATE('%Y-%m-%d', {c}), "
                "SAFE.PARSE_DATE('%Y%m%d', {c}), "
                "SAFE.PARSE_DATE('%Y-%m', {c}))".format(c=col))
    if t in ("INT64", "INTEGER", "NUMERIC", "BIGNUMERIC"):
        return ("COALESCE("
                "SAFE.PARSE_DATE('%Y%m%d', CAST({c} AS STRING)), "
                "SAFE.PARSE_DATE('%Y%m', CAST({c} AS STRING)))".format(c=col))
    raise SchemaError(
        "{}.{} has type {}; no date expression is defined for it. "
        "Add one to config.date_expr.".format(table_fqn, col, t))


def resolved(table_fqn, spec):
    """Resolve a {logical_name: (patterns, pin)} spec and print each result.

    Returns {logical_name: actual_column_name}. Printing the mapping, with the
    source of each name (pin, default, or pattern), is part of the output:
    every script states which real column it used and how it got it."""
    import schema_map
    out = {}
    print("  resolving columns on " + table_fqn)
    for logical in spec:
        args = spec[logical]
        patterns, pin = args if isinstance(args, tuple) else (args, None)
        col = resolve_col(table_fqn, patterns, pin=pin)
        if pin and schema_map.PINS.get(pin):
            src = "pin"
        elif pin and schema_map.DEFAULTS.get(pin, "").lower() == col.lower():
            src = "default"
        else:
            src = "pattern"
        out[logical] = col
        print("    {:<26} -> {}  [{}]".format(logical, col, src))
    return out
