#!/usr/bin/env python
"""
The id and group files of instructed-route B2 (plan `plans/B2-plan.md`, ticket T3).

Writes, under `docs/research/instructed-route/groups/` by default:

- `sdr_wish_ids.txt`: the 618 instance ids of `sdr_v2_inversion_reported`
  (P2's rows), in dataset order. If the file already exists (ticket T2 may
  write it for a dry run) it is verified against the dataset, never rewritten.
- `<task>_seed0_ids.txt`: the mechanism-analysis selection sample (seed 0),
  copied from the local, untracked `.../s1/U__leaf/<task>_v2/sample.json`.
- `<task>_seed1_ids.txt`: the mechanism-analysis held-out sample (seed 1),
  copied from the tracked `phase1/groups/<task>_heldout_D_sample.json`.
- `<task>_seed2_ids.txt`: a CPU draw with `sampling.draw_sample` on the task's
  v2 test split, n = 100, seed 2, seeds 0 and 1 excluded. It is the procedure
  that drew the held-out sample (seed 1, selection ids excluded), and the
  script refuses to write it unless redrawing seeds 0 and 1 reproduces both
  copied lists exactly.
- `p2_groups.json` and `p3_groups.json` for `--knockout-groups`.
- `b2_inputs_meta.json`: the recipe, sources and their sha256.

Every output is written only when absent; an existing file with the same
content is left alone and one with different content stops the run.

Run from the repo root (CPU only, no model):
    python scripts/instructed_route_b2_inputs.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from typing import Dict, List, Optional, Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from component_analysis import sampling  # noqa: E402

TASKS = ("far", "sdr", "ser")
DEFAULT_DATA_DIR = os.path.join(ROOT, "data", "datasets")
DEFAULT_OUT_DIR = os.path.join(ROOT, "docs", "research", "instructed-route",
                               "groups")
DEFAULT_HELDOUT_DIR = os.path.join(ROOT, "docs", "research",
                                   "mechanism-analysis", "phase1", "groups")
#: Local and untracked, so it lives in the primary checkout, not the worktree.
DEFAULT_SAMPLE_ROOT = ("/projects/beto/swong2/Alignment/Deception-Circuit/outputs/"
                       "_analyses/mechanism-analysis-p1/s1/U__leaf")

WISH_DATASET = "sdr_v2_inversion_reported"
N_SAMPLE = 100
SEED2 = 2

#: Llama-3.1-8B: 32 query heads in 8 KV groups of 4. The quartet L17H24-27 is
#: exactly KV group 6.
LAYER = 17
NUM_HEADS = 32
KV_SIZE = 4
QUARTET = (24, 25, 26, 27)
QUARTET_KV_GROUP = 6
N_NULL = 20
NULL_SEED_BASE = 20261101

P3_MLP_LAYERS = (11, 13, 16, 30, 31, 0)


# ==============================================================================
# GROUPS
# ==============================================================================

def _heads(heads: Sequence[int]) -> List[list]:
    return [["head", LAYER, int(h)] for h in heads]


def null_quartet(seed: int) -> List[int]:
    """Four distinct layer-17 heads outside the quartet, sorted, from `seed`."""
    pool = [h for h in range(NUM_HEADS) if h not in QUARTET]
    return sorted(random.Random(seed).sample(pool, KV_SIZE))


def p2_groups() -> Dict[str, List[list]]:
    """The quartet, L17H24 alone, the seven other KV groups and 20 nulls.

    Null i uses seed NULL_SEED_BASE + i. The draws are checked rather than
    redrawn: a null that repeated another or coincided with a KV group would
    stop here, so the declared seeds are always the ones used.
    """
    groups: Dict[str, List[list]] = {
        "quartet": _heads(QUARTET),
        "L17H24": _heads([QUARTET[0]]),
    }
    for g in range(NUM_HEADS // KV_SIZE):
        if g == QUARTET_KV_GROUP:
            continue
        groups[f"kvg_{g}"] = _heads(range(KV_SIZE * g, KV_SIZE * g + KV_SIZE))
    kv_sets = {frozenset(range(KV_SIZE * g, KV_SIZE * g + KV_SIZE))
               for g in range(NUM_HEADS // KV_SIZE)}
    seen = set()
    for i in range(N_NULL):
        heads = null_quartet(NULL_SEED_BASE + i)
        key = frozenset(heads)
        if key in seen or key in kv_sets:
            raise ValueError(f"null_d{i:02d} (seed {NULL_SEED_BASE + i}) repeats "
                             f"another null or a KV group: {heads}")
        seen.add(key)
        groups[f"null_d{i:02d}"] = _heads(heads)
    return groups


def p3_groups() -> Dict[str, List[list]]:
    """Six one-member MLP groups: three under test, C-MLP's pair, mlp.0."""
    return {f"mlp.{layer}": [["mlp", layer, 0]] for layer in P3_MLP_LAYERS}


# ==============================================================================
# IDS
# ==============================================================================

def _load_split(path: str, split: str = "test") -> List[dict]:
    # The repo's own loader (`instances.load_records`) is load_from_disk plus a
    # row limit equal to the split size for these tasks; draw_sample sorts by
    # id within strata, so row order cannot change a draw.
    from datasets import load_from_disk
    return [dict(row) for row in load_from_disk(path)[split]]


def wish_ids(data_dir: str = DEFAULT_DATA_DIR) -> List[str]:
    """The ids of the 618 reported-wish rows, in dataset order, unique."""
    records = _load_split(os.path.join(data_dir, WISH_DATASET))
    ids = sampling.record_ids(records)
    if len(set(ids)) != len(ids):
        raise ValueError(f"{WISH_DATASET} repeats an instance id")
    return ids


def test_records(data_dir: str, task: str) -> List[dict]:
    """The `<task>_v2` test split, the population of every causal sample."""
    return _load_split(os.path.join(data_dir, f"{task}_v2"))


def draw_ids(records: Sequence[dict], *, seed: int,
             exclude: Optional[Sequence[str]] = None,
             n: int = N_SAMPLE) -> List[str]:
    """The ids `analyze_components` would sample with `--seed seed
    [--exclude-ids FILE]` and the default stratification."""
    return sampling.draw_sample(records, n=n, seed=seed,
                                exclude_ids=exclude).ids


def _sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


# ==============================================================================
# WRITING
# ==============================================================================

def _ids_text(ids: Sequence[str]) -> str:
    return "".join(f"{one}\n" for one in ids)


def _json_text(obj) -> str:
    return json.dumps(obj, indent=1) + "\n"


def _write_new(path: str, text: str) -> str:
    """Write `text` to `path` if absent; leave an identical file; refuse a
    different one. Returns "written" or "unchanged"."""
    if os.path.exists(path):
        with open(path) as handle:
            if handle.read() == text:
                return "unchanged"
        raise SystemExit(f"{path} exists with different content; it is a "
                         f"pre-registered input, so it is not overwritten")
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as handle:
        handle.write(text)
    os.replace(tmp, path)
    return "written"


def _write_wish_ids(path: str, ids: Sequence[str]) -> str:
    """As `_write_new`, except an existing file (ticket T2's) is accepted when
    it names the same ids, in any order, each once."""
    if os.path.exists(path):
        with open(path) as handle:
            theirs = [line.strip() for line in handle if line.strip()]
        if len(theirs) == len(set(theirs)) and set(theirs) == set(ids):
            return "verified"
        raise SystemExit(f"{path} exists but does not name exactly the "
                         f"{len(ids)} ids of {WISH_DATASET} once each "
                         f"({len(theirs)} lines, {len(set(theirs))} unique); "
                         f"left untouched")
    return _write_new(path, _ids_text(ids))


def build(data_dir: str, sample_root: str, heldout_dir: str) -> dict:
    """Every output's content, plus the meta record. Raises on any check."""
    wish = wish_ids(data_dir)
    tasks = {}
    for task in TASKS:
        seed0_path = os.path.join(sample_root, f"{task}_v2", "sample.json")
        seed1_path = os.path.join(heldout_dir, f"{task}_heldout_D_sample.json")
        seed0 = sampling.read_id_file(seed0_path)
        seed1 = sampling.read_id_file(seed1_path)
        records = test_records(data_dir, task)
        if draw_ids(records, seed=0) != seed0:
            raise SystemExit(f"{task}: redrawing seed 0 does not reproduce "
                             f"{seed0_path}")
        if draw_ids(records, seed=1, exclude=seed0) != seed1:
            raise SystemExit(f"{task}: redrawing seed 1 with the seed-0 ids "
                             f"excluded does not reproduce {seed1_path}")
        sample2 = sampling.draw_sample(records, n=N_SAMPLE, seed=SEED2,
                                       exclude_ids=seed0 + seed1)
        seed2 = sample2.ids
        if len(seed2) != N_SAMPLE or set(seed2) & (set(seed0) | set(seed1)):
            raise SystemExit(f"{task}: the seed-2 draw is short or overlaps "
                             f"seeds 0 and 1")
        tasks[task] = {
            "seed0": seed0, "seed1": seed1, "seed2": seed2,
            "meta": {
                "split": "test", "population": len(records),
                "seed0_source": seed0_path, "seed0_sha256": _sha256(seed0_path),
                "seed1_source": seed1_path, "seed1_sha256": _sha256(seed1_path),
                "seed0_redraw_matches": True, "seed1_redraw_matches": True,
                "seed2": {
                    "seed": SEED2, "n": N_SAMPLE,
                    "excluded": "seed0 + seed1 ids",
                    "factors": list(sample2.factors),
                    "strata": [{"key": s.key, "available": s.available,
                                "achieved": s.achieved}
                               for s in sample2.strata],
                    "marginals": sample2.marginals,
                },
            },
        }
    meta = {
        "written_by": "scripts/instructed_route_b2_inputs.py (B2 ticket T3)",
        "procedure": ("component_analysis.sampling.draw_sample(test split, "
                      f"n={N_SAMPLE}, seed=s, default factors, exclude_ids=...),"
                      " as analyze_components --seed s --exclude-ids FILE: "
                      "seed 0 no exclusion, seed 1 excludes seed 0, seed 2 "
                      "excludes seeds 0 and 1"),
        "wish": {"dataset": WISH_DATASET, "n": len(wish)},
        "p2": {"layer": LAYER, "quartet": list(QUARTET),
               "quartet_kv_group": QUARTET_KV_GROUP,
               "null_seeds": [NULL_SEED_BASE + i for i in range(N_NULL)],
               "null_rule": ("random.Random(seed).sample(heads 0..31 minus "
                             "24..27, 4), sorted")},
        "p3": {"mlp_layers": list(P3_MLP_LAYERS)},
        "tasks": {task: value["meta"] for task, value in tasks.items()},
    }
    return {"wish": wish, "tasks": tasks, "meta": meta}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--sample-root", default=DEFAULT_SAMPLE_ROOT,
                        help="directory holding <task>_v2/sample.json (seed 0)")
    parser.add_argument("--heldout-dir", default=DEFAULT_HELDOUT_DIR,
                        help="directory holding <task>_heldout_D_sample.json")
    args = parser.parse_args(argv)

    built = build(args.data_dir, args.sample_root, args.heldout_dir)
    os.makedirs(args.out_dir, exist_ok=True)
    out = args.out_dir
    status = {"sdr_wish_ids.txt": _write_wish_ids(
        os.path.join(out, "sdr_wish_ids.txt"), built["wish"])}
    for task, value in built["tasks"].items():
        for seed in ("seed0", "seed1", "seed2"):
            name = f"{task}_{seed}_ids.txt"
            status[name] = _write_new(os.path.join(out, name),
                                      _ids_text(value[seed]))
    status["p2_groups.json"] = _write_new(os.path.join(out, "p2_groups.json"),
                                          _json_text(p2_groups()))
    status["p3_groups.json"] = _write_new(os.path.join(out, "p3_groups.json"),
                                          _json_text(p3_groups()))
    status["b2_inputs_meta.json"] = _write_new(
        os.path.join(out, "b2_inputs_meta.json"), _json_text(built["meta"]))
    for name, state in status.items():
        print(f"{state:>9}  {os.path.join(out, name)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
