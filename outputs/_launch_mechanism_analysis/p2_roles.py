#!/usr/bin/env python3
"""
p2_roles.py -- the roles pass on the phase-2 cells (ticket 04; spec section 4 phase 2, R7/R10), on CPU.

Phase 2 runs no single-Component knockout (R16), so each cell's "depends, whether" view is merged from the phase-1
single-knockout cell on the same test set (`--roles-merge-from`; the rows are keyed by Component, and U' = U plus
the operand, so every U row finds its knockout columns and the operand's extra heads stay unmeasured on that view):

    d  <- s1 (D, item swap, all positions) and s2p (D, neutral twin, post-clause: rule 4b's knockout column)
    h  <- s5 (H, item swap)        f <- s6 (F, item swap)        i <- s7 (I, neutral twin, post-clause)

No phase-2 cell has path patching (phase 3 brings it on C_t), so `--roles-allow-missing-views` is passed and
every role proposed here is read as "without the where-clause"; roles.json records the missing view.

usage (from the repository root, after the cells are fetched):
    python outputs/_launch_mechanism_analysis/p2_roles.py [--root DIR] [--dry-run] [--tasks far,sdr,ser]
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p2_jobs  # noqa: E402

TASKS = ("far", "sdr", "ser")
ROOT = "outputs/_analyses/mechanism-analysis-p2"
P1_CELL = "outputs/_analyses/mechanism-analysis-p1/{s}/U__leaf/{t}_v2"
MERGE = {"d": ("s1", "s2p"), "h": ("s5",), "f": ("s6",), "i": ("s7",)}
B2_FLOOR = "0.05"


def roles_argv(t: str, cell: str, *, cell_dir: str) -> list:
    argv = ["roles", cell_dir]
    for s in MERGE[cell]:
        argv += ["--roles-merge-from", P1_CELL.format(s=s, t=t)]
    argv += ["--roles-b2-floor", B2_FLOOR, "--roles-allow-missing-views"]
    return argv


def cell_dir(root: str, cell: str, t: str) -> str:
    """The task's test-set dir under <root>/<cell>/Up__leaf/ (the three tasks share a cell root; the test set is
    named after the task: <t>_v2, <t>_v2_nopressure, <t>_v2_inversion)."""
    hits = [h for h in sorted(glob.glob(os.path.join(root, cell, "Up__leaf", f"{t}_*"))) if os.path.isdir(h)]
    if len(hits) != 1:
        raise FileNotFoundError(f"{cell}/{t}: expected one test-set dir under {root}/{cell}/Up__leaf/{t}_*, found {hits}")
    return hits[0]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=ROOT, help="the fetched phase-2 cells, relative to the repo root")
    p.add_argument("--tasks", default=",".join(TASKS))
    p.add_argument("--cells", default=",".join(MERGE))
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    os.chdir(REPO)
    import analyze_components
    failures = []
    for t in a.tasks.split(","):
        for cell in a.cells.split(","):
            try:
                cdir = cell_dir(a.root, cell, t)
            except FileNotFoundError as exc:
                print("  skip:", exc)
                failures.append((t, cell, "missing"))
                continue
            args = roles_argv(t, cell, cell_dir=os.path.relpath(cdir, REPO)) + (["--dry-run"] if a.dry_run else [])
            print("\n$ analyze_components.py", " ".join(args))
            code = analyze_components.main(args)
            if code:
                failures.append((t, cell, code))
    print("\nfailures:", failures or "none")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
