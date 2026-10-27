#!/usr/bin/env python3
"""
p3_merge.py -- the merge tables the phase-3 roles pass reads (ticket 05; R16, R26).

The phase-3 cell `outputs/_analyses/mechanism-analysis-p3/d/Ct__leaf/<t>_v2` holds path patching under the
Neutral-Clause Twin on C_t (plus the Components the twin completeness sweep appended); `d_is` holds the item swap
on C_t. The other views come from earlier phases, restricted to the phase-3 cell's own rows, because
`--roles-merge-from` appends every row it does not find (`head_table.merge_columns`) and the phase-2 cell has the
146 / 136 / 144 rows of U', not C_t's 72 / 66 / 78. Two tables per task:

    _merge/<t>_p2d   attention_patterns.* and dla.* of the phase-2 D cell (Delta copy), on the rows of the phase-3
                     cell that U' holds: a copy of the phase-2 D cell under carry-forward's own row rule (an intake row
                     of another circuit is dropped), its coverage meta carried; roles.* and knockout.* left out
    _merge/<t>_ko    the phase-1 sweeps' knockout columns on every row of the phase-3 cell (s1: D, item swap, all
                     positions; s2p: D, neutral twin, post-clause), built with p2_merge.build_merge_table (R16: the
                     sweeps are the measurement of record), so sweep-appended rows outside U' get them too

usage (from the repository root, after the phase-3 cells are fetched):
    python outputs/_launch_mechanism_analysis/p3_merge.py [--p3-root DIR] [--p2-root DIR] [--p1-root DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p2_jobs  # noqa: E402
import p2_merge  # noqa: E402
from component_analysis import head_table as ht  # noqa: E402

TASKS = ("far", "sdr", "ser")
P3_ROOT = "outputs/_analyses/mechanism-analysis-p3"
P2_ROOT = "outputs/_analyses/mechanism-analysis-p2"
#: The phase-2 D cell's views the phase-3 roles pass needs: reads (attention, the B2 signature) and writes (DLA).
COPIED = ("attention_patterns", "dla")
KO_SWEEPS = ("s1", "s2p")


def p3_cell(root: str, t: str, cell: str = "d") -> str:
    return os.path.join(root, cell, "Ct__leaf", f"{t}_v2")


def p2_d_cell(root: str, t: str) -> str:
    return os.path.join(root, "d", "Up__leaf", f"{t}_v2")


def merge_dir(root: str, t: str, what: str) -> str:
    return os.path.join(root, "_merge", f"{t}_{what}")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def restrict_columns(rows, meta, keys, namespaces=COPIED):
    """`(rows, meta)`: the source rows whose key is in `keys` (in `keys` order), holding only the key columns,
    `kv_group` and the columns under `namespaces`; the meta keeps the coverage of those columns and the instance sets
    they point at. A key the source does not hold gets no row (the merge would append it otherwise)."""
    wanted = tuple(f"{one}." for one in namespaces)
    by = {ht.row_key(row): row for row in rows}
    out = []
    for key in keys:
        src = by.get(tuple(key))
        if src is None:
            continue
        row = {"kind": key[0], "layer": int(key[1]), "index": int(key[2]), "kv_group": src.get("kv_group")}
        row.update({c: v for c, v in src.items() if c.startswith(wanted)})
        out.append(row)
    columns = {c for row in out for c in row if c.startswith(wanted)}
    coverage = {c: e for c, e in ((meta or {}).get(ht.COVERAGE_KEY) or {}).items() if c in columns}
    used = {e.get("instance_set") for e in coverage.values()}
    sets = {k: v for k, v in ((meta or {}).get(ht.INSTANCE_SETS_KEY) or {}).items() if k in used}
    return out, {ht.COVERAGE_KEY: coverage, ht.INSTANCE_SETS_KEY: sets}


def build_p2d(out_dir: str, p3_rows, p2_dir: str) -> dict:
    keys = [ht.row_key(row) for row in p3_rows]
    rows, meta = restrict_columns(ht.load_head_table(p2_dir), ht.load_head_table_meta(p2_dir), keys)
    meta["built_by"] = ("outputs/_launch_mechanism_analysis/p3_merge.py (ticket 05): the phase-2 D cell's "
                        "attention_patterns.* and dla.* on the phase-3 cell's rows, for --roles-merge-from")
    meta["source"] = {"cell": p2_dir, "head_table_sha256": _sha256(os.path.join(p2_dir, ht.JSON_NAME))}
    ht.write_head_table(out_dir, rows, meta=meta)
    return {"dir": out_dir, "rows": len(rows), "not_in_p2": [list(k) for k in keys
                                                           if k not in {ht.row_key(r) for r in rows}]}


def build_ko(out_dir: str, p3_rows, p1_root: str, t: str) -> dict:
    keys = [ht.row_key(row) for row in p3_rows]
    sweeps, paths = [], []
    for s in KO_SWEEPS:
        sp = p2_jobs.sweep_path(p1_root, t, cell=s)
        with open(sp) as f:
            sweep = json.load(f)
        with open(os.path.join(os.path.dirname(sp), sweep.get("instances_file", "sweep_instances.json"))) as f:
            inst = json.load(f)
        sweeps.append((sweep, inst))
        paths.append(f"{os.path.relpath(sp, REPO)} sha256 {_sha256(sp)}")
    p2_merge.build_merge_table(out_dir, keys, sweeps, sources=paths)
    return {"dir": out_dir, "rows": len(keys)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--p3-root", default=os.path.join(REPO, P3_ROOT))
    p.add_argument("--p2-root", default=os.path.join(REPO, P2_ROOT))
    p.add_argument("--p1-root", default=os.path.join(REPO, p2_jobs.P1_ROOT))
    p.add_argument("--tasks", default=",".join(TASKS))
    a = p.parse_args(argv)
    for t in a.tasks.split(","):
        rows = ht.load_head_table(p3_cell(a.p3_root, t))
        p2d = build_p2d(merge_dir(a.p3_root, t, "p2d"), rows, p2_d_cell(a.p2_root, t))
        ko = build_ko(merge_dir(a.p3_root, t, "ko"), rows, a.p1_root, t)
        print(t, f"p3 rows {len(rows)}; p2d {p2d['rows']} rows (not in U': {p2d['not_in_p2']}); ko {ko['rows']} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
