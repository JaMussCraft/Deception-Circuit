#!/usr/bin/env python3
"""
drift.py -- compare a heads-only knockout cell with its Delta reference (ticket 06 drift control).

`metrics_of(knockout_json)` flattens the numbers the stage-1 table reads (task knockout row, circuit-alone
row, task-side knockout null with its 4/4 separation count, wikitext collateral and its null, flips,
pressure-variant headlines). `compare(ref, new)` gives per-metric deltas.

Separation rule (the coarse SDR wave's KO-null gate): a metric separates when the knockout's percentile
among the 20 random head sets is <= 5 and its z <= -2, both oriented so lower is a stronger knockout.

usage (from the repository root, after the drift-control jobs):
    python outputs/_launch_mechanism_v2/evals/drift.py                 # both drift cells, each vs its reference
    python outputs/_launch_mechanism_v2/evals/drift.py <knockout.json>  # any cell vs both references
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
METRICS = ("accuracy", "logit_diff", "kl_div", "exact_match")
SEPARATION_PCT, SEPARATION_Z = 5.0, -2.0


def metrics_of(ko: dict) -> dict:
    out = {}
    task = ko["task"]
    for row in ("knockout", "circuit"):
        for m in METRICS:
            out[f"task.{row}.{m}"] = task[row][m]
    stats = task["null"]["stats"]
    separated = 0
    for m in METRICS:
        s = stats[m]
        out[f"task.null.{m}.mean"] = s["mean"]
        out[f"task.null.{m}.percentile"] = s["percentile"]
        out[f"task.null.{m}.z"] = s["z"]
        separated += int(s["percentile"] <= SEPARATION_PCT and s["z"] <= SEPARATION_Z)
    out["task.null.separated"] = separated
    out["task.flip.n_flipped_honest"] = task["flip_summary"]["n_flipped_honest"]
    wt = ko["wikitext"]
    out["wikitext.kl_per_token"] = wt["discovered"]["kl_per_token"]
    out["wikitext.ppl_ratio"] = wt["discovered"]["ppl_ratio"]
    out["wikitext.null.kl_per_token.mean"] = wt["null"]["stats"]["kl_per_token"]["mean"]
    out["wikitext.null.kl_per_token.percentile"] = wt["null"]["stats"]["kl_per_token"]["percentile"]
    for name, v in sorted((ko.get("variants") or {}).items()):
        head = v.get("headline") or {}
        for key in ("full_accuracy", "knockout_accuracy"):
            if key in head:
                out[f"variants.{name}.{key}"] = head[key]
    return out


def compare(ref: dict, new: dict) -> dict:
    rows = {}
    for key in list(ref) + [k for k in new if k not in ref]:
        a, b = ref.get(key), new.get(key)
        delta = (b - a) if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
        rows[key] = {"ref": a, "new": b, "delta": delta}
    return rows


def _print(ref, new, path):
    print(f"\n== {path}\n   vs Delta job {ref['slurm_job']} ({ref['role']}, {ref['gpu']}, {ref['created']})")
    print(f"{'metric':45s} {'ref':>12s} {'new':>12s} {'delta':>12s}")
    for key, r in compare(ref["metrics"], new).items():
        d = "" if r["delta"] is None else f"{r['delta']:+.6f}"
        print(f"{key:45s} {r['ref']!s:>12.12s} {r['new']!s:>12.12s} {d:>12s}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import mv2_cells as mc
    refs = mc.load_suite()["drift_control"]["references"]
    if len(argv) > 1:
        sys.exit(__doc__)
    pairs = [(r, argv[0]) for r in refs] if argv else [(r, os.path.join(mc.REPO, r["result"])) for r in refs]
    for ref, path in pairs:
        with open(path) as f:
            _print(ref, metrics_of(json.load(f)), path)


if __name__ == "__main__":
    main()
