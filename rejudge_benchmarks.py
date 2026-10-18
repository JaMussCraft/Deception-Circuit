#!/usr/bin/env python
"""
rejudge_benchmarks.py — buy the EVAL 5 verdicts a judge outage left unbought.

    python rejudge_benchmarks.py outputs/eval5_format_sdr_coarse --dry
    python rejudge_benchmarks.py outputs/eval5_format_sdr_coarse \\
        outputs/eval5_format_sdr_coarse_lb --max-calls 7000

Walks `<suite>/cells/*/*/*/benchmarks.json`, re-judges every label whose judge
call failed (`raw == "judge-failed"`) on the generation already stored there,
through the suite's own `judge_cache.jsonl`, and recomputes counts, rates, the
random-circuit null, the examples, the cell headline and the suite matrix.
No GPU, no model. See `evaluation/rejudge.py` for what is checked before any
row is touched.

Exit codes: 0 nothing left failing (dry: plan clean); 1 labels still failing
(cap reached or the judge failed again); 2 a dataset or cell was refused
(prompt/model drift, or stored numbers that do not reproduce from stored
labels); 3 a suite was skipped before anything was written to it (missing
key, or its preflight call failed); the other suites still ran.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation import rejudge  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("suites", nargs="+", help="EVAL 5 suite directories")
    parser.add_argument("--dry", action="store_true",
                        help="Count what needs re-judging and how many judge "
                             "calls that is after cache hits. No API call, "
                             "nothing written.")
    parser.add_argument("--max-calls", type=int, default=None,
                        help="Cap on judge requests that miss the cache, over "
                             "the whole invocation (retries not counted). Rows "
                             "past the cap stay failing; re-run to continue.")
    args = parser.parse_args(argv)
    for suite in args.suites:
        if not os.path.isfile(os.path.join(suite, "suite.json")):
            parser.error("%s has no suite.json" % suite)
    return rejudge.run(args.suites, dry=args.dry, max_calls=args.max_calls)


if __name__ == "__main__":
    sys.exit(main())
