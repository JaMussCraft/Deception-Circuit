"""
write_format_control_summary.py — the format-control suite summary and verdict.

Reads a merged format-control suite (`outputs/_suites/format-control-*`, built
by `outputs/_launch_format_control/`): its cells, `overlap.json` and
`flip_audit.json`, plus the F dataset's `dataset_config.json` for pairing and
each run's `config.json` for its condition. Writes `evaluation_summary.md` and
`decision.json` into the suite: the paired table for D, H and F, the overlap
table, the delta rows, and the spec's pre-registered (a)/(b)/(c) verdict with
every sub-condition. Missing cells are listed, never crashed on.

Usage (from the repo root):

    python write_format_control_summary.py outputs/_suites/format-control-far-nls0.3

    # with the eval 5 suites (ticket 06; the sm and lb benchmark groups, named in
    # outputs/_launch_format_control/README_eval5.md), which add the benchmark
    # columns and an informational eval 5 deception-drop row, and switch the
    # collateral condition to the reference-NLL rise
    python write_format_control_summary.py outputs/_suites/format-control-far-nls0.3 \\
        --eval5-dir outputs/eval5_format_far --eval5-dir outputs/eval5_format_far_lb

    # likewise for SDR: outputs/eval5_format_sdr and outputs/eval5_format_sdr_lb
    # with format-control-sdr-nls0.3; outputs/eval5_format_sdr_coarse and
    # outputs/eval5_format_sdr_coarse_lb with format-control-sdr-coarse-nls0.3
"""

from __future__ import annotations

import argparse
import json

import os

from evaluation import format_control_summary as fcs

DEFAULT_MANIFEST = "outputs/_launch_format_control/suite_manifest.json"


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("suite_root", help="a merged format-control suite directory")
    p.add_argument("--data-dir", default="data/datasets",
                   help="where <task>_nopressure/dataset_config.json lives (pairing)")
    p.add_argument("--eval5-dir", action="append", default=[],
                   help="an eval 5 suite directory with D, H and F cells; repeatable")
    p.add_argument("--manifest", default=DEFAULT_MANIFEST,
                   help="ticket 04's suite manifest; its per-suite cells index gives each "
                        "cell's path and dataset condition (default: %(default)s when it "
                        "exists; pass '' to read the default layout)")
    p.add_argument("--honest-rows", choices=fcs.HONEST_ROWS_MODES, default="variants",
                   help="honest-answer rows in the rule: 'variants' (default; the spec's eval 2 "
                        "no_pressure and honest_instruction rows) or 'all' (adds the H and F "
                        "test sets, where F's knockout is in-distribution)")
    p.add_argument("--family", choices=("fine", "coarse"), default=None,
                   help="override the family inferred from the suite name and cells")
    p.add_argument("--task", default=None,
                   help="override the task inferred from the suite name")
    p.add_argument("--out", default=None, help="default <suite_root>/evaluation_summary.md")
    p.add_argument("--decision-out", default=None, help="default <suite_root>/decision.json")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    manifest = args.manifest
    if manifest == DEFAULT_MANIFEST and not os.path.exists(manifest):
        manifest = None
    md, js = fcs.write_summary(args.suite_root, data_dir=args.data_dir,
                               eval5_dirs=args.eval5_dir, family=args.family, task=args.task,
                               manifest=manifest or None, honest_rows=args.honest_rows,
                               out_md=args.out,
                               out_json=args.decision_out)
    with open(js) as f:
        d = json.load(f)
    v = d["verdict"]
    print(f"wrote {md}\nwrote {js}")
    print(f"{d['suite']}: verdict {('(' + v + ')') if v else 'undecided'} "
          f"[{d['evaluated_on']}]; {len(d['missing'])} missing item(s)")
    return d


if __name__ == "__main__":
    main()
