#!/usr/bin/env python3
"""
p2_merge.py -- the knockout merge tables the phase-2 roles pass reads (ticket 04; R16).

Phase 2 runs no single-Component knockout: the measurement of record is the phase-1 completeness sweep over all
1,056 Components (R16), one sample per sweep, so each phase-2 cell's "depends, whether" view is merged from a head
table built here from the sweep files, restricted to the U' rows (U plus the task's operand: the deciding S_k's
heads and the C_t MLP blocks). This covers the S_k heads outside U and the ten MLP blocks, which the 123-row
phase-1 head tables do not. On the U rows the sweep's numbers are the phase-1 head table's numbers (same sample,
verified on far s1: head.17.24 1.89075 +- 0.09799 in both).

    outputs/_analyses/mechanism-analysis-p2/_merge/<t>_<cell>/head_table.{json,csv}

    d <- s1 (D, item swap, all positions; the plain knockout columns) + s2p (D, neutral twin, post-clause; rule 4b's
         `_neutral_twin_paired_after_pressure_clause_excl_readout` columns)
    h <- s5 (H, item swap)      f <- s6 (F, item swap)      i <- s7 (I, neutral twin, post-clause only)

The I cell therefore has no plain knockout view (no phase-1 I item-swap sweep exists): on I only rule 4b can fire,
and roles.json says so. Coverage meta carries each sweep's instance ids (`sweep_instances.json`) and its source.

usage (from the repository root; needs the fetched phase-1 cells and the operands):
    python outputs/_launch_mechanism_analysis/p2_merge.py [--p1-root DIR] [--out-root DIR]
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
import p2_operands  # noqa: E402
from component_analysis import head_table as ht  # noqa: E402

TASKS = ("far", "sdr", "ser")
ROOT = "outputs/_analyses/mechanism-analysis-p2"
SOURCES = {"d": ("s1", "s2p"), "h": ("s5",), "f": ("s6",), "i": ("s7",)}
NAMESPACE = "knockout"
VALUE, SE, ACC = "logit_diff_drop", "standard_error", "accuracy"


def merge_dir(root: str, t: str, cell: str) -> str:
    return f"{root}/_merge/{t}_{cell}"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_merge_table(out_dir: str, keys, sweeps, *, sources=()) -> str:
    """Write a head table over `keys` (ordered (kind, layer, index)) with each sweep's knockout columns under the
    sweep plan's column suffix, and the coverage meta of each. `sweeps` = [(sweep.json dict, sweep_instances dict)];
    `sources` = the matching file paths, recorded in the coverage details. Returns `out_dir`."""
    rows = [{"kind": k, "layer": int(l), "index": int(i)} for k, l, i in keys]
    meta = {}
    for n, (sweep, inst) in enumerate(sweeps):
        suffix = (sweep.get("plan") or {}).get("column_suffix", "") or ""
        by = {(r["kind"], int(r["layer"]), int(r["index"])): r for r in sweep["components"]}
        cols = [VALUE + suffix, SE + suffix, ACC + suffix]
        for row in rows:
            src = by.get((row["kind"], row["layer"], row["index"]))
            row[f"{NAMESPACE}.{cols[0]}"] = src["mean_drop"] if src else None
            row[f"{NAMESPACE}.{cols[1]}"] = src["standard_error"] if src else None
            row[f"{NAMESPACE}.{cols[2]}"] = src.get("accuracy") if src else None
            if src and row.get("kv_group") is None and src.get("kv_group") is not None:
                row["kv_group"] = src["kv_group"]
        details = {"plan": sweep.get("plan"), "sample": sweep.get("sample"), "task": sweep.get("task"),
                   "source": (sources[n] if n < len(sources) else "sweep.json (phase-1 completeness sweep, R16)")}
        meta = ht.add_coverage(meta, cols, inst["instance_ids"], instance_set="causal_sample", namespace=NAMESPACE,
                               details=details)
    meta["built_by"] = "outputs/_launch_mechanism_analysis/p2_merge.py (ticket 04): the phase-1 sweeps' knockout " \
                       "columns over the U' rows, for --roles-merge-from"
    ht.write_head_table(out_dir, rows, meta=meta)
    return out_dir


def u_prime_keys(t: str, sets: dict, prov: dict) -> list:
    """U' = U heads | the operand's heads | the C_t MLP blocks, in model order."""
    U = set().union(*(sets[k] for k in sets))
    heads = U | {(l, h) for _k, l, h in (p2_operands.parse_label(x) for x in prov["heads"])}
    keys = [("head", l, h) for l, h in sorted(heads)] + [("mlp", int(l), 0) for l in sorted(prov["mlp_layers"])]
    return sorted(keys, key=lambda k: (k[1], 0 if k[0] == "head" else 1, k[2]))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--p1-root", default=os.path.join(REPO, p2_jobs.P1_ROOT))
    p.add_argument("--out-root", default=os.path.join(REPO, ROOT))
    p.add_argument("--tasks", default=",".join(TASKS))
    a = p.parse_args(argv)
    sets = p2_jobs.head_sets()
    for t in a.tasks.split(","):
        with open(os.path.join(REPO, p2_jobs.OPERAND.format(t=t), "provenance.json")) as f:
            prov = json.load(f)
        keys = u_prime_keys(t, sets, prov)
        for cell, srcs in SOURCES.items():
            sweeps, paths = [], []
            for s in srcs:
                sp = p2_jobs.sweep_path(a.p1_root, t, cell=s)
                with open(sp) as f:
                    sweep = json.load(f)
                with open(os.path.join(os.path.dirname(sp), sweep.get("instances_file", "sweep_instances.json"))) as f:
                    inst = json.load(f)
                sweeps.append((sweep, inst))
                paths.append(f"{os.path.relpath(sp, REPO)} sha256 {_sha256(sp)}")
            out = build_merge_table(merge_dir(a.out_root, t, cell), keys, sweeps, sources=paths)
            print(out, len(keys), "rows;", [s for s in srcs])
    return 0


if __name__ == "__main__":
    sys.exit(main())
