#!/usr/bin/env python3
"""
Write `result_summary.md` and `eval5_format.json` for format-control EVAL 5
suites (ticket 06). Thin CLI over `evaluation/eval5_format_summary.py`.

    python outputs/_launch_format_control/write_eval5_format_summary.py \
        outputs/eval5_format_far outputs/eval5_format_far_lb [--stdout]

Run from the worktree root after the suite's job finished. A missing cell or a
failed dataset is reported in the summary, not raised.
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from evaluation.eval5_format_summary import render, write  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("suite_dirs", nargs="+")
    ap.add_argument("--stdout", action="store_true",
                    help="print the summary instead of writing files")
    a = ap.parse_args(argv)
    for d in a.suite_dirs:
        if not os.path.isdir(d):
            print(f"not a directory: {d}", file=sys.stderr)
            return 2
        if a.stdout:
            print(render(d))
        else:
            for path in write(d):
                print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
