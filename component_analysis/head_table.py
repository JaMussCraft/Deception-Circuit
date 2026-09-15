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
"""

from __future__ import annotations

import csv
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


def write_head_table(cell_dir: str, rows, *, meta: dict = None) -> dict:
    """Write `head_table.json` and `head_table.csv`. Returns both paths."""
    os.makedirs(cell_dir, exist_ok=True)
    columns = columns_of(rows)

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
    """The rows of a written head table, from the JSON twin."""
    with open(os.path.join(cell_dir, JSON_NAME)) as f:
        return json.load(f)["rows"]
