"""
component_analysis/head_table.py — the one table every analysis writes into.

One row per Component, keyed by (kind, layer, index). Every analysis adds its
own columns through `merge_columns`, which namespaces them (`dla.differential`,
`attention.designation_site`, ...) so that two analyses can never collide on a
name, and refuses to touch `role_confirmed`, which is the human's column.

The JSON file is the typed source of truth — it keeps ints as ints, booleans as
booleans and missing cells as null. The CSV is a view of the same rows for
spreadsheets and for `pandas.read_csv`; everything in it is a string, so read
the JSON back when a number matters.

**Coverage.** Columns of one table are not all computed over the same
instances: on SDR the paired honest-instruction columns cover the 71 of the
100-instance causal sample that have a Matched Honest Instruction, and the
descriptive columns the whole test split. The JSON's `meta` says so per
column, rather than the column name:

    meta.coverage       {column: {"n": int, "instance_set": set id or null}}
    meta.instance_sets  {set id: {"name", "n", "instance_ids", "dataset"}}

An analysis declares it with `add_coverage` (through
`AnalysisContext.declare_coverage`); a reader asks `coverage_of`. Each set is
written once and every column over it points at it, and a set id is its name
plus a digest of its ids, so two columns over the same instances share an id
and two over different instances never do. A table written before coverage
existed has neither key, and every reader here treats that as "not recorded".

**Paired names.** Every column computed over the same instance ids on both
sides carries `paired` in its bare name (the researcher's 2026-10-13 decision).
`LEGACY_COLUMNS` maps the names written before that to the current ones, and
`modernize_columns` is the one place a reader translates an old table.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time

#: The key of a row. Never namespaced, never written by an analysis.
KEY_COLUMNS = ("kind", "layer", "index")

#: The intake columns ticket 01 writes; later analyses append to the right.
BASE_COLUMNS = KEY_COLUMNS + ("kv_group", "head_gate_active",
                              "active_neuron_count")

#: Columns only a human writes. `merge_columns` refuses to set them, because an
#: analysis silently overwriting a confirmed role would make the final labels
#: unreviewable.
PROTECTED_COLUMNS = ("role_confirmed",)

SCHEMA_VERSION = 1

CSV_NAME = "head_table.csv"
JSON_NAME = "head_table.json"

#: The two meta keys that carry per-column coverage.
COVERAGE = "coverage"
INSTANCE_SETS = "instance_sets"

#: The bare names `path_patching` writes per counterfactual. Spelled here only
#: to derive their legacy names; `path_patching.COLUMN_NAMES` is the owner and a
#: test pins the two equal.
_PATH_COLUMNS = ("strongest_incoming", "strongest_incoming_effect",
                 "strongest_outgoing", "strongest_outgoing_effect",
                 "direct_effect", "direct_effect_se")
_SWEEP_COLUMNS = ("sweep_direct_effect", "sweep_direct_effect_se", "sweep_rank",
                  "sweep_in_circuit", "sweep_flagged")

#: Column names a head table may carry from before a rename, old -> current.
#: Values are never changed by the rename, only names: a column whose *meaning*
#: changes (a sign flip, say) gets a new name and a meta note of its own, never
#: an entry here.
LEGACY_COLUMNS = {
    # 2026-10-13, ticket 13: "paired" goes into every paired column's name.
    "attention_patterns.honest_instruction_top_segment":
        "attention_patterns.honest_instruction_paired_top_segment",
    "attention_patterns.honest_instruction_top_mass":
        "attention_patterns.honest_instruction_paired_top_mass",
    "dla.honest_instruction": "dla.honest_instruction_paired",
    "dla.differential": "dla.differential_paired",
    "dla.differential_se": "dla.differential_paired_se",
    **{f"path_patching.{name}_honest_instruction":
       f"path_patching.{name}_honest_instruction_paired"
       for name in _PATH_COLUMNS + _SWEEP_COLUMNS},
    "roles.direct_support_honest_instruction":
        "roles.direct_support_honest_instruction_paired",
    # 2026-09-20, ticket 10: the role family is not a task family.
    "knockout.family": "knockout.role_family",
    "knockout.family_logit_diff_drop": "knockout.role_family_logit_diff_drop",
}


def row_key(row) -> tuple:
    """(kind, layer, index) for a row, a Component or a hand-built key.

    Always (str, int, int), whatever the caller had to hand: a key rebuilt from
    a CSV read carries `layer` and `index` as strings, and an uncoerced key
    would miss the row it names and silently append a duplicate Component.
    """
    if isinstance(row, tuple):
        kind, layer, index = row
    elif hasattr(row, "key"):
        return row.key
    else:
        kind, layer, index = row["kind"], row["layer"], row["index"]
    return (str(kind), int(layer), int(index))


def rows_from_components(components, extra=None) -> list:
    """The intake rows for a Component list.

    `extra` is an optional {component key: {column: value}} of columns that are
    part of the intake itself rather than of a later analysis — the reference
    membership columns are merged in separately, through `merge_columns`.
    """
    rows = []
    for component in components:
        row = {"kind": component.kind, "layer": component.layer,
               "index": component.index, "kv_group": component.kv_group,
               "head_gate_active": component.head_gate_active,
               "active_neuron_count": component.active_neuron_count}
        row.update((extra or {}).get(component.key, {}))
        rows.append(row)
    return rows


def columns_of(rows) -> list:
    """Every column present, base columns first and then in insertion order."""
    columns = [c for c in BASE_COLUMNS if any(c in r for r in rows)]
    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(column)
    return columns


def merge_columns(rows, updates, *, namespace: str = None) -> list:
    """Add one analysis's columns to the table, keyed by Component.

    `updates` maps a Component key — (kind, layer, index), or a Component — to
    {column: value}. With `namespace` given every column is written as
    `<namespace>.<column>`.

    Rows the update says nothing about still gain the column, set to None, so
    that "this analysis did not score this Component" is visible rather than
    ragged. A key with no row yet appends one: a completeness sweep scores
    Components outside the circuit, and they belong in the same table.

    Returns new rows; the input is not mutated.
    """
    merged = [dict(row) for row in rows]
    by_key = {row_key(row): row for row in merged}

    named = {}
    for key, values in (updates or {}).items():
        key = row_key(key)
        named[key] = {(f"{namespace}.{c}" if namespace else c): v
                      for c, v in values.items()}

    new_columns = []
    for values in named.values():
        for column in values:
            if column in PROTECTED_COLUMNS:
                raise ValueError(
                    f"{column!r} is written by the researcher, not by an "
                    f"analysis — merge_columns will not set it.")
            if column in KEY_COLUMNS:
                raise ValueError(f"{column!r} is part of the row key and "
                                 f"cannot be merged over.")
            if column not in new_columns:
                new_columns.append(column)

    for key, values in named.items():
        row = by_key.get(key)
        if row is None:
            row = {"kind": key[0], "layer": key[1], "index": key[2]}
            merged.append(row)
            by_key[key] = row
        row.update(values)

    # Every row carries every column, so that "this analysis said nothing about
    # this Component" reads as an empty cell rather than a ragged row — and so
    # that an appended Component shows blank intake columns rather than none.
    for column in columns_of(merged):
        for row in merged:
            row.setdefault(column, None)
    return merged


def modernize_columns(rows) -> tuple:
    """`(rows, {old: new})`: a table's legacy column names, translated.

    Every reader of a head table that may predate a rename goes through this,
    so the translation lives in one place. A row holding both spellings with
    different values is refused by name: which of the two is the measurement
    cannot be decided here. Returns new rows; the input is not mutated.
    """
    renamed = {}
    out = []
    for row in rows:
        row = dict(row)
        for old, new in LEGACY_COLUMNS.items():
            if old not in row:
                continue
            value = row.pop(old)
            held = row.get(new)
            if held is not None and value is not None and held != value:
                raise ValueError(
                    f"{old!r} and its current name {new!r} both hold a value on "
                    f"{row_key(row)} ({value!r} against {held!r}); one table "
                    f"cannot carry both spellings of one column.")
            if held is None:
                row[new] = value
            renamed[old] = new
        out.append(row)
    return out, renamed


def instance_set_id(name: str, instance_ids, dataset: str = None):
    """`<name>:<digest>`, the same for the same instances in any order.

    None for an empty set: a column computed over nothing points at no set.
    """
    ids = sorted(str(one) for one in instance_ids or ())
    if not ids:
        return None
    digest = hashlib.sha1(json.dumps([dataset, ids]).encode()).hexdigest()[:10]
    return f"{name}:{digest}"


def add_coverage(meta, columns, instance_ids, *, instance_set: str,
                 namespace: str = None, dataset: str = None) -> dict:
    """Declare which instances some columns were computed over.

    `columns` are bare names, namespaced like `merge_columns` namespaces them;
    `instance_set` names the kind of set (`causal_sample`, `test_split`,
    `paired_honest_instruction`, ...) and the id adds a digest of the ids, so a
    name is never mistaken for a guarantee that two sets are equal. Returns a
    new meta; the input is not mutated. Redeclaring a column replaces it.
    """
    meta = dict(meta or {})
    coverage = dict(meta.get(COVERAGE) or {})
    sets = dict(meta.get(INSTANCE_SETS) or {})
    ids = [str(one) for one in instance_ids or ()]
    set_id = instance_set_id(instance_set, ids, dataset)
    if set_id is not None and set_id not in sets:
        sets[set_id] = {"name": instance_set, "n": len(ids),
                        "dataset": dataset, "instance_ids": ids}
    for column in columns:
        name = f"{namespace}.{column}" if namespace else column
        coverage[name] = {"n": len(ids), "instance_set": set_id}
    meta[COVERAGE] = coverage
    meta[INSTANCE_SETS] = sets
    return meta


def coverage_of(meta, column):
    """`{"n", "instance_set", "instance_ids", "dataset"}` for one column, or None.

    None means the table does not record it — a table written before coverage
    existed, or a column nothing declared — which is not the same as n = 0.
    """
    entry = ((meta or {}).get(COVERAGE) or {}).get(column)
    if entry is None:
        return None
    found = ((meta or {}).get(INSTANCE_SETS) or {}).get(entry.get("instance_set")) or {}
    return {"n": entry.get("n"), "instance_set": entry.get("instance_set"),
            "instance_ids": list(found.get("instance_ids", [])),
            "dataset": found.get("dataset")}


def _pruned(meta, columns) -> dict:
    """The meta with coverage only for columns the table holds.

    A column dropped from the table takes its coverage with it, and an instance
    set nothing points at any more is dropped too, so the meta never describes
    a column the reader cannot find.
    """
    meta = dict(meta or {})
    if COVERAGE not in meta and INSTANCE_SETS not in meta:
        return meta
    coverage = {column: entry for column, entry in (meta.get(COVERAGE) or {}).items()
                if column in columns}
    used = {entry.get("instance_set") for entry in coverage.values()}
    meta[COVERAGE] = coverage
    meta[INSTANCE_SETS] = {set_id: one for set_id, one
                           in (meta.get(INSTANCE_SETS) or {}).items()
                           if set_id in used}
    return meta


def write_head_table(cell_dir: str, rows, *, meta: dict = None) -> dict:
    """Write `head_table.json` and `head_table.csv`. Returns both paths.

    `meta` may carry the coverage `add_coverage` builds; entries for columns the
    rows do not hold are dropped on the way out.
    """
    os.makedirs(cell_dir, exist_ok=True)
    columns = columns_of(rows)
    meta = _pruned(meta, columns)

    json_path = os.path.join(cell_dir, JSON_NAME)
    with open(json_path, "w") as f:
        json.dump({"schema_version": SCHEMA_VERSION,
                   "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "columns": columns,
                   "meta": meta or {},
                   "rows": [{c: row.get(c) for c in columns} for row in rows]},
                  f, indent=2, default=str)

    csv_path = os.path.join(cell_dir, CSV_NAME)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: _csv_cell(row.get(c)) for c in columns})

    return {"csv": csv_path, "json": json_path}


def _csv_cell(value):
    """CSV has no null and no boolean; write blanks and 0/1 rather than 'None'."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return int(value)
    return value


def load_head_table(cell_dir: str) -> list:
    """The rows of a written head table, from the JSON twin, as written."""
    with open(os.path.join(cell_dir, JSON_NAME)) as f:
        return json.load(f)["rows"]


def load_head_table_meta(cell_dir: str) -> dict:
    """The `meta` block of a written head table; `{}` when it has none."""
    with open(os.path.join(cell_dir, JSON_NAME)) as f:
        return json.load(f).get("meta") or {}
