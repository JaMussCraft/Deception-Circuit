#!/usr/bin/env python3
"""Merge per-job shard suites into one suite directory, filed by test set.

Adapted from outputs/_suites/_launch_260922/merge_shards.py (the 2026-09-22
cross-task rerun). Each job ran

    evaluate_circuit.py ... --task-from <run> --output-dir <suite>/_shards/<job>

and so wrote <shard>/cells/<circuit>/<task>/<ablation>/*.json plus its own
suite.json / matrix.json. With one `--task-from` per invocation the evaluator
labels the task by its bare name (`far`) whatever the condition of the test
set, so the D, H and F test sets of one circuit would all land in
cells/<circuit>/far/. This merge therefore files every cell under its test
set's directory name instead, read from the shard's own task provenance
(`dataset.deception_condition`):

    cells/<circuit>/<task>[_honest|_nopressure]/<ablation>/

which is also the directory `flip_audit_analysis.py --data-dir` loads. The
matrix cells keep the evaluator's label as `task_name` and gain
`dataset_condition` and `shard`.

When the suite manifest is given (`--manifest`), every finished shard must
produce exactly the cells the manifest planned for its job, and planned jobs
with no shard directory yet are reported as missing.

usage: python merge_shards.py <suite_root> [--manifest suite_manifest.json]
                              [--ablation interchange] [--force]
Run from the repo root (imports evaluation.suite and tasks).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fc_cells import dataset_label  # noqa: E402


def _task_conditions(suite: dict) -> dict:
    """evaluator task label -> (task name, condition) from a shard's suite.json."""
    out = {}
    for t in suite.get("tasks", []):
        cond = (t.get("dataset") or {}).get("deception_condition") or "deceptive"
        out[t["label"]] = (t.get("task") or t["label"], cond)
    return out


def merge_suite(root: str, expected_cells: dict = None, ablation: str = "interchange",
                force: bool = False, log=print) -> dict:
    """Merge <root>/_shards/* into <root>/cells, matrix.{json,csv}, suite.json.

    expected_cells: {job: [{"circuit", "dataset"}, ...]} from the manifest, or
    None to merge whatever is there. Returns {"merged", "pending", "missing",
    "cells"}.
    """
    from evaluation.suite import write_matrix

    root = root.rstrip("/")
    shards = sorted(glob.glob(os.path.join(root, "_shards", "*")))
    planned = []          # (shard, suite, [(cell, dataset, cond, name)])
    pending, seen = [], {}
    for sh in shards:
        job = os.path.basename(sh)
        mpath = os.path.join(sh, "matrix.json")
        if not os.path.exists(mpath):
            pending.append(job)
            continue
        with open(mpath) as f:
            m = json.load(f)
        with open(os.path.join(sh, "suite.json")) as f:
            s = json.load(f)
        conds = _task_conditions(s)
        rows = []
        for cell in m["cells"]:
            if cell["ablation"] != ablation:
                continue
            name, cond = conds.get(cell["task"], (cell["task"], "deceptive"))
            dataset = dataset_label(name, cond)
            key = f"{cell['circuit']}/{dataset}"
            if key in seen:
                raise ValueError(f"cell {key} is produced by two shards: {seen[key]} and {job}")
            seen[key] = job
            rows.append((cell, dataset, cond, name))
        if expected_cells is not None:
            if job not in expected_cells:
                raise ValueError(f"shard {job} is not a job of the manifest")
            want = sorted((c["circuit"], c["dataset"]) for c in expected_cells[job])
            got = sorted((c["circuit"], d) for c, d, _, _ in rows)
            if want != got:
                raise ValueError(f"shard {job} produced cells {got}, the manifest planned {want}")
        planned.append((sh, s, rows))

    missing = sorted(j for j in (expected_cells or {})
                     if not os.path.isdir(os.path.join(root, "_shards", j)))
    cells, circuits, tasks, merged, first = [], {}, {}, [], None
    for sh, s, rows in planned:
        job = os.path.basename(sh)
        first = first or s
        for c in s.get("circuits", []):
            circuits.setdefault(c["label"], c)
        for cell, dataset, cond, name in rows:
            src = os.path.join(sh, "cells", cell["circuit"], cell["task"], ablation)
            dst = os.path.join(root, "cells", cell["circuit"], dataset, ablation)
            if os.path.exists(dst) and not force:
                log(f"  keep existing {os.path.relpath(dst, root)}")
            else:
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                log(f"  copied {os.path.relpath(src, root)} -> {os.path.relpath(dst, root)}")
            for t in s.get("tasks", []):
                if t["label"] == cell["task"]:
                    tasks.setdefault(dataset, dict(t, label=dataset, evaluator_label=t["label"]))
            cell = dict(cell, task=dataset, task_name=name, dataset_condition=cond,
                        out_dir=dst, shard=job)
            cells.append(cell)
        merged.append(job)

    if pending:
        log(f"  {len(pending)} shard(s) not finished: {', '.join(pending)}")
    if missing:
        log(f"  {len(missing)} planned job(s) have no shard yet: {', '.join(missing)}")
    report = {"merged": merged, "pending": pending, "missing": missing, "cells": len(cells)}
    if not cells:
        log("  nothing to merge")
        return report
    cells.sort(key=lambda c: (c["task"], c["circuit"]))
    for p in write_matrix(root, cells):
        log(f"  wrote {p}")
    suite = dict(first)
    suite.update({"root": os.path.abspath(root), "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                  "circuits": list(circuits.values()), "tasks": list(tasks.values()),
                  "merged_from": merged, "shards_pending": pending, "shards_missing": missing,
                  "note": "merged from per-job shards by _launch_format_control/merge_shards.py; "
                          "task labels are test-set directory names; argv/cli are the first shard's"})
    with open(os.path.join(root, "suite.json"), "w") as f:
        json.dump(suite, f, indent=2, default=str)
    log(f"  wrote {os.path.join(root, 'suite.json')}  ({len(cells)} cells, "
        f"{len(pending)} pending, {len(missing)} missing)")
    return report


def expected_from_manifest(manifest_path: str, suite_name: str) -> dict:
    with open(manifest_path) as f:
        manifest = json.load(f)
    jobs = manifest["suites"][suite_name]["jobs"]
    return {j["job"]: j["cells"] for j in jobs}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("suite_root")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--ablation", default="interchange")
    ap.add_argument("--force", action="store_true", help="overwrite existing merged cells")
    a = ap.parse_args(argv)
    expected = None
    if a.manifest:
        expected = expected_from_manifest(a.manifest, os.path.basename(a.suite_root.rstrip("/")))
    merge_suite(a.suite_root, expected, a.ablation, a.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
