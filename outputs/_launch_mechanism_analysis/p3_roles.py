#!/usr/bin/env python3
"""
p3_roles.py -- the roles pass on the phase-3 cells (ticket 05; R7, R10, R25, R27), on CPU.

The phase-3 cell of record per task is `<root>/d/Ct__leaf/<t>_v2` (path patching under the Neutral-Clause Twin, the
receiver categories, the twin completeness sweep's columns). The roles pass merges into it:

    <root>/_merge/<t>_p2d   attention and DLA of the phase-2 D cell on these rows (p3_merge.py)
    <root>/_merge/<t>_ko    the phase-1 sweeps' knockout columns (s1, s2p) on these rows (p3_merge.py)
    <root>/d_is/Ct__leaf/<t>_v2   path patching under the item swap on C_t (the same job's second line)

so one table carries all views, and rule 4b's where-clause reads the receiver category (R25). The pass is tried first
WITHOUT --roles-allow-missing-views; only if the roles CLI refuses for a missing view (MISSING_VIEW_REFUSAL) is the
refusal printed and the pass rerun with the flag (roles.json then records the missing view). Any other refusal or
non-zero exit is a failure. The rows the twin sweep appended (Components outside
C_t that clear the sweep threshold) carry no path grid of their own and are reported apart.

usage (from the repository root, after the cells are fetched and p3_merge.py has run):
    python outputs/_launch_mechanism_analysis/p3_roles.py [--root DIR] [--tasks far,sdr,ser] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p3_merge  # noqa: E402

TASKS = ("far", "sdr", "ser")
ROOT = p3_merge.P3_ROOT
B2_FLOOR = "0.05"


def roles_argv(t: str, root: str = ROOT, *, allow_missing: bool = False) -> list:
    out = ["roles", p3_merge.p3_cell(root, t, "d"),
           "--roles-merge-from", p3_merge.merge_dir(root, t, "p2d"),
           "--roles-merge-from", p3_merge.merge_dir(root, t, "ko"),
           "--roles-merge-from", p3_merge.p3_cell(root, t, "d_is"),
           "--roles-b2-floor", B2_FLOOR]
    return out + (["--roles-allow-missing-views"] if allow_missing else [])


#: The roles CLI's refusal for a view absent from every merged table (component_analysis/roles.py); the only
#: refusal --roles-allow-missing-views is meant to override.
MISSING_VIEW_REFUSAL = "has no column at all for"


def missing_view_refusal(exc: SystemExit) -> bool:
    return isinstance(exc.code, str) and MISSING_VIEW_REFUSAL in exc.code


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=ROOT, help="the fetched phase-3 cells, relative to the repo root")
    p.add_argument("--tasks", default=",".join(TASKS))
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    os.chdir(REPO)
    import analyze_components
    failures = []
    for t in a.tasks.split(","):
        for allow in (False, True):
            args = roles_argv(t, a.root, allow_missing=allow) + (["--dry-run"] if a.dry_run else [])
            print("\n$ analyze_components.py", " ".join(args), flush=True)
            try:
                code = analyze_components.main(args)
            except SystemExit as exc:
                print(f"  refused: {exc}", flush=True)
                if not allow and missing_view_refusal(exc):
                    print("  DOWNGRADE: rerunning with --roles-allow-missing-views; roles.json records the missing "
                          "view", flush=True)
                    continue
                failures.append((t, f"refused: {exc}"))
                break
            if code == 0:
                break
            failures.append((t, code))
            break
    print("\nfailures:", failures or "none")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
