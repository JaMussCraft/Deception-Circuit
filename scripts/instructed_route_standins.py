#!/usr/bin/env python3
"""
instructed_route_standins.py -- the config-only stand-in of the reported-wish I condition (instructed-route B2 plan,
ticket T2), and the 618-id file P2 runs over.

The stand-in is `outputs/_launch_mechanism_analysis/standins/sdr_v2_inversion/config.json` (mechanism-analysis
ticket 03) with `deception_condition: inversion_reported`, so `analyze_components.py --task-from` on it loads
`data/datasets/sdr_v2_inversion_reported` (`component_analysis.instances.dataset_dir`). It is never a run and never
bound as a circuit. Its `data_dir` is relative (`./data/datasets`), so run the analyses from the repository root.

The id file is `docs/research/instructed-route/groups/sdr_wish_ids.txt`, one instance id per line in split order.
Ticket T3 (`scripts/instructed_route_b2_inputs.py`) also writes it, so this script writes it only when it is absent
and never overwrites it.

usage (from the repository root):
    python scripts/instructed_route_standins.py [--out-repo DIR] [--no-ids]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

CONDITION = "inversion_reported"
SOURCE_STANDIN = "outputs/_launch_mechanism_analysis/standins/sdr_v2_inversion"
STANDIN = f"outputs/_launch_instructed_route/standins/sdr_v2_{CONDITION}"
DATASET = f"data/datasets/sdr_v2_{CONDITION}"
WISH_IDS = "docs/research/instructed-route/groups/sdr_wish_ids.txt"
NOTE = ("config-only task source for --task-from (the sdr_v2 reported-wish I test set, "
        "data/datasets/sdr_v2_inversion_reported); not a run and never bound as a circuit "
        "(instructed-route B2 ticket T2).")


def write_standin(repo: str = REPO, out_repo: str = None) -> str:
    """Copy the `sdr_v2_inversion` stand-in with the condition changed; return the written path."""
    out_repo = out_repo or repo
    with open(os.path.join(repo, SOURCE_STANDIN, "config.json")) as f:
        cfg = json.load(f)
    if cfg.get("deception_condition") != "inversion" or cfg.get("task") != "sdr_v2":
        raise ValueError(f"{SOURCE_STANDIN}/config.json is not the sdr_v2 inversion stand-in "
                         f"(task {cfg.get('task')!r}, condition {cfg.get('deception_condition')!r})")
    cfg["deception_condition"] = CONDITION
    cfg["standin"] = NOTE
    cfg["standin_source"] = SOURCE_STANDIN
    d = os.path.join(out_repo, STANDIN)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "config.json")
    with open(path, "w") as f:
        json.dump(cfg, f, indent=1)
        f.write("\n")
    return path


def wish_ids(repo: str = REPO) -> list:
    """The reported-wish test split's instance ids, in split order, as the loaders key them."""
    sys.path.insert(0, repo)
    from datasets import load_from_disk
    from component_analysis import sampling
    rows = [dict(r) for r in load_from_disk(os.path.join(repo, DATASET))["test"]]
    return sampling.record_ids(rows)


def write_wish_ids(repo: str = REPO, out_repo: str = None):
    """(path, written): write the id file only when it does not exist yet (T3 may have written it)."""
    out_repo = out_repo or repo
    path = os.path.join(out_repo, WISH_IDS)
    if os.path.exists(path):
        return path, False
    ids = wish_ids(repo)
    if len(ids) != len(set(ids)):
        raise ValueError(f"{DATASET} has duplicate instance ids")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "x") as f:          # "x": lose a race with T3 rather than overwrite it
            f.write("".join(f"{one}\n" for one in ids))
    except FileExistsError:
        return path, False
    return path, True


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out-repo", default=REPO)
    p.add_argument("--no-ids", action="store_true", help="Write the stand-in only.")
    a = p.parse_args(argv)
    print(write_standin(REPO, a.out_repo))
    if not a.no_ids:
        path, written = write_wish_ids(REPO, a.out_repo)
        print(f"{path} ({'written' if written else 'exists, left as it is'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
