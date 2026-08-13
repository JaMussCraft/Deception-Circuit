"""
deception_comparison_set.py — the primary comparison set across FAR/SDR/SER.

Downstream, cross-mechanism circuit comparisons are paired: they are computed on
the instances that survived behavioral filtering in ALL THREE tasks, so content,
corruption site and every balancing factor are identical across mechanisms. Each
task's full survivor set is kept as a robustness set; this script only computes
and reports the intersection, plus the matched-pressure subset (the instances
whose pressure clause was one of the five shared, mechanism-neutral ones).

    python dataset/deception_comparison_set.py
    python dataset/deception_comparison_set.py --condition honest
"""

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset import deception_common as dc


def build_parser():
    p = argparse.ArgumentParser(
        description="Compute the three-way instance intersection for FAR/SDR/SER.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--data-dir", default=os.path.join("data", "datasets"))
    p.add_argument("--condition", default="deceptive",
                   choices=["deceptive", "honest"])
    p.add_argument("--splits", nargs="+",
                   default=["train", "validation", "test"])
    p.add_argument("--output", default=None,
                   help="Default: <data-dir>/comparison_set[_honest].json")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    suffix = "_honest" if args.condition == "honest" else ""
    if args.output is None:
        args.output = os.path.join(args.data_dir, f"comparison_set{suffix}.json")

    from datasets import load_from_disk

    per_task_split = {}
    missing = []
    for task in sorted(dc.SPECS):
        path = os.path.join(args.data_dir, f"{task}{suffix}")
        if not os.path.exists(os.path.join(path, "dataset_dict.json")):
            missing.append(task)
            continue
        dd = load_from_disk(path)
        per_task_split[task] = {
            split: list(dd[split]["instance_id"])
            for split in args.splits if split in dd
        }
    if missing:
        raise SystemExit(f"Not built yet: {missing}. Build all three tasks first "
                         f"(dataset/build_deception_dataset.py --task ...).")

    report = {"condition": args.condition, "splits": {}}
    for split in args.splits:
        by_task = {t: [{"instance_id": i} for i in per_task_split[t].get(split, [])]
                   for t in per_task_split}
        common, sizes = dc.three_way_intersection(by_task)
        report["splits"][split] = {
            "per_task_sizes": sizes,
            "intersection_size": len(common),
            "instance_ids": sorted(common),
        }
        print(f"{split:<11} per-task {sizes} -> intersection {len(common)}")

    # Matched-pressure subset: instances whose clause was one of the shared five.
    shared_ids = {p["id"] for p in dc.load_pressures("far") if p["shared"]}
    matched = {}
    for split in args.splits:
        common = set(report["splits"][split]["instance_ids"])
        counts = Counter()
        for task in per_task_split:
            path = os.path.join(args.data_dir, f"{task}{suffix}")
            dd = load_from_disk(path)
            if split not in dd:
                continue
            rows = dd[split]
            for iid, pid in zip(rows["instance_id"], rows["pressure_id"]):
                if iid in common and pid in shared_ids:
                    counts[iid] += 1
        matched[split] = sorted(i for i, c in counts.items()
                                if c == len(per_task_split))
        print(f"{split:<11} matched-pressure subset (shared clauses): "
              f"{len(matched[split])}")
    report["matched_pressure_subset"] = matched

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved comparison set to {args.output}")


if __name__ == "__main__":
    main()
