"""scripts/neuron_partition_data.py — the id samples and matched nulls of `neuron-partition`.

CPU only, no model. Three subcommands, all writing under
`outputs/_analyses/neuron-partition/data/` (git-ignored):

- `copy-pools` copies the user-turn I and user-neutral pools (HF dataset dicts in the
  specificity-ladder worktree, read only, unmerged) into `data/pools/`, hashes every file, and
  checks the hashes against the `files` block of each pool's own `assembly_provenance.json`.
- `sample` writes `far_test_sample_seed2.json` (the fresh ablation sample of item 10 of
  START.md: at least 300 rows per condition, seed 2, excluding the ladder's A1 ids and the
  mechanism-analysis held-out samples) and `far_rank_ids.json` (the train and validation ids
  the scorer may rank on, with a seed-2 split-half assignment stratified by pressure cluster).
- `nulls` draws K random `mlp_hidden` neuron sets matched to a tested set on size and per-layer
  count, and writes them with the tested set as one groups file plus a provenance sidecar.

The draw reuses `component_analysis.sampling.draw_sample` (balanced over designation polarity,
item polarity and template variant, ids sorted before the seeded draw), so a rerun with the
same seed and exclusions draws the same ids.

Conventions recorded here because the data decides them (verified 2026-11-03):
- Every FAR v2 row in all three splits is act-naming under `clause_form` of
  `dataset/build_inversion_v2.py`, so the START's "act-naming clauses only" filter keeps every
  row; it is applied anyway and its count is written.
- "Pressure cluster" is `pressure_id`, as in F-rte-005 ("clustered by 11 pressure ids").
- far_v2, far_v2_honest and far_v2_nopressure carry the same instance ids per split; the I and
  user-neutral pools carry the same ids per split, and every pool id is a far_v2 id of the same
  split.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import sys
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from component_analysis.sampling import draw_sample, record_ids  # noqa: E402

# ------------------------------------------------------------------------------ constants

SEED = 2
N_TEST = 300
#: Llama-3.1-8B-Instruct: 32 layers, 14,336 down-projection inputs per layer (START item 2).
#: Hard-coded rather than read from `evaluation` so the CPU tests never import torch.
NUM_LAYERS = 32
INTERMEDIATE = 14336
NEURON_KIND = "mlp_hidden"
N_NULLS = 20

OUT_DIR = os.path.join(REPO, "outputs", "_analyses", "neuron-partition", "data")
DATASETS = os.path.join(REPO, "data", "datasets")
LADDER = ("/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/"
          "specificity-ladder/outputs/_analyses/specificity-ladder")
POOL_SOURCE = os.path.join(LADDER, "a1-control-77b6487-m07")
POOL_NAMES = ("far_v2_user_inversion", "far_v2_user_neutral")
LADDER_DESIGN = os.path.join(LADDER, "ladder-5f450dc", "design.json")
LADDER_SELECTED = os.path.join(LADDER, "ladder-5f450dc", "selected.json")
MECH_GROUPS = os.path.join(REPO, "docs", "research", "mechanism-analysis", "phase1", "groups")
HELD_OUT_JSON = os.path.join(REPO, "docs", "research", "held_out.json")
CLAUSE_FORMS = os.path.join(REPO, "docs", "research", "mechanism-analysis", "clause-forms.csv")


# ------------------------------------------------------------------------------ hashing

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_tree(root: str) -> Dict[str, str]:
    """{path relative to root: sha256} for every file under root, sorted."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            out[os.path.relpath(full, root)] = sha256_file(full)
    return dict(sorted(out.items()))


def _display(path: str) -> str:
    """Repo-relative for files in this worktree, absolute otherwise."""
    path = os.path.abspath(path)
    return os.path.relpath(path, REPO) if path.startswith(REPO + os.sep) else path


def write_json(path: str, obj) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(obj, handle, indent=1)
        handle.write("\n")
    return sha256_file(path)


# ------------------------------------------------------------------------------ the draw

def paired_records(records: Sequence[dict], twin_id_sets: Sequence[Iterable[str]]
                   ) -> Tuple[List[dict], List[str]]:
    """(records whose id has a row in every twin set, ids dropped for lacking one).

    Filtering before the draw is the deterministic form of "resample if a drawn id has no
    twin": the seeded draw only ever sees ids it could keep.
    """
    twins = [set(map(str, ids)) for ids in twin_id_sets]
    keep, dropped = [], []
    for record, rid in zip(records, record_ids(records)):
        if all(rid in t for t in twins):
            keep.append(record)
        else:
            dropped.append(rid)
    return keep, dropped


def draw_condition(records: Sequence[dict], *, twin_id_sets: Sequence[Iterable[str]],
                   exclude_ids: Iterable[str], n: int = N_TEST, seed: int = SEED,
                   form_filter=None) -> dict:
    """The seeded, balanced draw of one condition pair, after the form filter, the pairing
    check and the exclusions. Returns the ids and the record of how the draw went."""
    records = list(records)
    n_split = len(records)
    if form_filter is not None:
        records = [r for r in records if form_filter(r)]
    n_form = len(records)
    records, unpaired = paired_records(records, twin_id_sets)
    exclude = sorted(set(map(str, exclude_ids)))
    sample = draw_sample(records, n=n, seed=seed, exclude_ids=exclude)
    return {"ids": list(sample.ids),
            "counts": {"split_rows": n_split, "after_form_filter": n_form,
                       "dropped_no_twin": len(unpaired), "paired_pool": len(records),
                       "removed_by_exclusion": sample.id_filters["id_exclusion"]["n_removed_from_pool"],
                       "eligible": len(records) - sample.id_filters["id_exclusion"]["n_removed_from_pool"],
                       "drawn": sample.n_drawn, "requested": n},
            "sample": sample.as_json()}


def split_halves(ids: Sequence[str], clusters: Sequence[str], seed: int = SEED
                 ) -> Dict[str, str]:
    """{id: "A" or "B"}, stratified by cluster and balanced overall.

    Clusters are visited in sorted order and ids within one are sorted, then shuffled with one
    `random.Random(seed)`. Within a cluster the ids alternate between halves, and the half a
    cluster starts on carries over from the previous cluster's parity, so every cluster splits
    within one and the totals differ by at most one.
    """
    if len(ids) != len(clusters):
        raise ValueError(f"{len(ids)} ids for {len(clusters)} clusters")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate ids in the split-half input")
    by_cluster: Dict[str, List[str]] = {}
    for rid, cluster in zip(ids, clusters):
        by_cluster.setdefault(str(cluster), []).append(str(rid))
    rng = random.Random(seed)
    halves, start = {}, 0
    for cluster in sorted(by_cluster):
        members = sorted(by_cluster[cluster])
        rng.shuffle(members)
        for i, rid in enumerate(members):
            halves[rid] = "AB"[(start + i) % 2]
        start = (start + len(members)) % 2
    return halves


# ------------------------------------------------------------------------------ matched nulls

def parse_neuron_set(members) -> Dict[int, List[int]]:
    """{layer: sorted indices} from [[kind, layer, index], ...]; refuses anything else."""
    if not isinstance(members, list) or not members:
        raise ValueError("a neuron set is a non-empty list of [kind, layer, index]")
    by_layer: Dict[int, List[int]] = {}
    seen = set()
    for member in members:
        if not isinstance(member, list) or len(member) != 3:
            raise ValueError(f"member {member!r} is not [kind, layer, index]")
        kind, layer, index = member
        if kind != NEURON_KIND:
            raise ValueError(f"member {member!r}: kind must be {NEURON_KIND!r}")
        if not (isinstance(layer, int) and 0 <= layer < NUM_LAYERS):
            raise ValueError(f"member {member!r}: layer outside 0..{NUM_LAYERS - 1}")
        if not (isinstance(index, int) and 0 <= index < INTERMEDIATE):
            raise ValueError(f"member {member!r}: index outside 0..{INTERMEDIATE - 1}")
        if (layer, index) in seen:
            raise ValueError(f"member {member!r} is named twice")
        seen.add((layer, index))
        by_layer.setdefault(layer, []).append(index)
    return {layer: sorted(v) for layer, v in sorted(by_layer.items())}


def to_members(by_layer: Dict[int, Sequence[int]]) -> List[list]:
    return [[NEURON_KIND, int(layer), int(i)] for layer in sorted(by_layer)
            for i in sorted(by_layer[layer])]


def matched_null(tested: Dict[int, Sequence[int]], *, seed: int, index: int) -> Dict[int, List[int]]:
    """One random set with the tested set's per-layer counts, none of its neurons.

    Mirrors the `mlp_hidden` branch of `evaluation/masks.py::sample_random_masks` (the null of
    `evaluate_circuit.py --evals null/knockout --n-random`): one RNG stream per draw from
    `np.random.default_rng([seed, index])`, so draw k is reproducible on its own, and a uniform
    draw without replacement within each layer, layers in ascending order. One deliberate
    departure, required by the neuron-partition brief: the repo's null draws over all 14,336
    indices of a layer, this one over the layer's indices minus the tested set's own.
    """
    import numpy as np

    rng = np.random.default_rng([int(seed), int(index)])
    out = {}
    for layer in sorted(tested):
        own = np.asarray(sorted(set(tested[layer])), dtype=np.int64)
        avail = np.setdiff1d(np.arange(INTERMEDIATE, dtype=np.int64), own)
        k = len(own)
        if k > avail.size:
            raise ValueError(f"layer {layer}: {k} neurons do not fit in the complement of "
                             f"{avail.size}")
        out[layer] = sorted(int(i) for i in rng.choice(avail, size=k, replace=False))
    return out


def matched_nulls(tested: Dict[int, Sequence[int]], *, k: int = N_NULLS, seed: int = SEED
                  ) -> List[Dict[int, List[int]]]:
    return [matched_null(tested, seed=seed, index=i) for i in range(k)]


# ------------------------------------------------------------------------------ inputs

def load_split_records(path: str, split: str) -> List[dict]:
    from datasets import load_from_disk

    return [dict(row) for row in load_from_disk(path)[split]]


def exclusion_sources(task_key: str = "far_v2") -> Dict[str, dict]:
    """The id lists the fresh sample must avoid, each with path, sha256 and count."""
    out = {}
    design = json.load(open(LADDER_DESIGN))["payload"]["designs"][task_key]
    out["a1_assessment"] = {"path": LADDER_DESIGN, "key": f"payload.designs.{task_key}.assessment_ids",
                            "sha256": sha256_file(LADDER_DESIGN), "ids": list(design["assessment_ids"])}
    out["a1_selection"] = {
        "path": LADDER_DESIGN, "key": f"payload.designs.{task_key}.mover_selection_ids",
        "also_at": [LADDER_SELECTED + f" payload.groups.{task_key}.screen.selection_ids"],
        "sha256": sha256_file(LADDER_DESIGN), "ids": list(design["mover_selection_ids"]),
        "why": ("the ladder's second 100-id FAR test list (its selection sample); the brief "
                "says to exclude the union when several candidates exist")}
    for label, name in (("mech_heldout_D", "far_heldout_D_sample.json"),
                        ("mech_heldout_I", "far_heldout_I_sample.json")):
        path = os.path.join(MECH_GROUPS, name)
        out[label] = {"path": _display(path), "sha256": sha256_file(path),
                      "ids": [str(i) for i in json.load(open(path))["instance_ids"]]}
    held = json.load(open(HELD_OUT_JSON))
    held_ids = [str(i) for s in held.get("sets", [])
                if str(s.get("task", "")).startswith("far") for i in s.get("instance_ids", [])]
    out["held_out_json"] = {"path": _display(HELD_OUT_JSON), "sha256": sha256_file(HELD_OUT_JSON),
                            "ids": held_ids, "n_sets": len(held.get("sets", []))}
    return out


def load_exclude_file(path: str) -> dict:
    """One `--exclude-ids` file: its ids (every id of a per-condition "ids" dict, of a flat
    "ids" list, or of a top-level flat list), with path, sha256 and count.

    A sample file such as `far_test_sample_seed2.json` qualifies as it stands: the union of
    its per-condition lists is excluded from every pool of the new draw.
    """
    raw = json.load(open(path))
    ids = raw.get("ids") if isinstance(raw, dict) else raw
    if isinstance(ids, dict):
        if not all(isinstance(v, list) for v in ids.values()):
            raise ValueError(f"{path}: 'ids' must map conditions to lists of ids")
        flat = [str(i) for v in ids.values() for i in v]
        per_condition = {str(k): len(v) for k, v in ids.items()}
    elif isinstance(ids, list):
        flat = [str(i) for i in ids]
        per_condition = None
    else:
        raise ValueError(f"{path}: expected a list of ids or a dict whose 'ids' is a "
                         "per-condition dict or a list")
    out = {"path": _display(path), "sha256": sha256_file(path), "ids": sorted(set(flat)),
           "why": "--exclude-ids: removed from every pool before the balanced draw"}
    if per_condition is not None:
        out["per_condition_in_file"] = per_condition
    return out


def act_naming(record: dict) -> bool:
    """True iff the row's D pressure clause is act-naming. Only meaningful on D rows: an I or
    user-neutral row's `pressure` field holds the neutral sentence, so pool rows are judged by
    the D row of the same id (`act_naming_by_id`)."""
    from dataset.build_inversion_v2 import clause_form

    return clause_form(record["pressure"], "far_v2") == "act"


def act_naming_by_id(d_records: Sequence[dict]):
    """A form filter for pool rows: the clause form of the D row with the same instance id."""
    forms = {rid: act_naming(r) for rid, r in zip(record_ids(d_records), d_records)}

    def keep(record: dict) -> bool:
        rid = str(record["instance_id"])
        if rid not in forms:
            raise ValueError(f"pool id {rid} has no D row to read its clause form from")
        return forms[rid]
    return keep


# ------------------------------------------------------------------------------ commands

def count_eligible(recs: dict, ids: dict, union: Sequence[str],
                   factors: Sequence[str] = ("designation_polarity", "item_polarity",
                                             "template_variant")) -> dict:
    """What the test-split draw could take, without drawing: per pool, the eligible ids after
    the form filter, the pairing check and the exclusions, their strata, the largest n the
    balanced draw gives (every eligible id: `allocate` caps each stratum and hands the surplus
    to the smallest stratum with room) and the largest n at which every stratum gets an equal
    share (strata times the smallest stratum)."""
    barred = set(map(str, union))
    out = {}
    for label, twins, form in (("D", ("H", "F"), act_naming),
                               ("I", ("N",), act_naming_by_id(recs["D"]["test"]))):
        records = [r for r in recs[label]["test"] if form(r)]
        keep, dropped = paired_records(records, [ids[t]["test"] for t in twins])
        eligible = [r for r, rid in zip(keep, record_ids(keep)) if rid not in barred]
        strata = Counter(tuple(str(r.get(f)) for f in factors) for r in eligible)
        out[label] = {"test_rows": len(recs[label]["test"]), "dropped_no_twin": len(dropped),
                      "removed_by_exclusion": len(keep) - len(eligible),
                      "eligible": len(eligible), "max_n_balanced_draw": len(eligible),
                      "n_strata": len(strata),
                      "max_n_equal_share": len(strata) * min(strata.values()) if strata else 0,
                      "strata": {"|".join(k): v for k, v in sorted(strata.items())}}
    return out


def cmd_copy_pools(args) -> int:
    dest_root = os.path.join(args.out_dir, "pools")
    manifest = {"note": ("Copied read-only from the specificity-ladder worktree (Codex, unmerged "
                         "into main); the copies exist so Bridges-2 jobs can read them."),
                "pools": {}}
    for name in POOL_NAMES:
        src = os.path.join(args.pool_source, name)
        dst = os.path.join(dest_root, name)
        src_hashes = hash_tree(src)
        if os.path.exists(dst):
            if hash_tree(dst) != src_hashes:
                raise SystemExit(f"{dst} exists and differs from {src}; remove it by hand first")
        else:
            shutil.copytree(src, dst)
        dst_hashes = hash_tree(dst)
        if dst_hashes != src_hashes:
            raise SystemExit(f"copy of {name} does not hash like its source")
        listed = json.load(open(os.path.join(src, "assembly_provenance.json")))["files"]
        check = {"matched": sorted(k for k in listed if dst_hashes.get(k) == listed[k]),
                 "mismatched": sorted(k for k in listed if k in dst_hashes and dst_hashes[k] != listed[k]),
                 "missing": sorted(k for k in listed if k not in dst_hashes),
                 "not_listed": sorted(k for k in dst_hashes if k not in listed)}
        manifest["pools"][name] = {"source": src, "copy": _display(dst), "files": dst_hashes,
                                   "assembly_provenance_check": {
                                       "matched": len(check["matched"]),
                                       "mismatched": check["mismatched"],
                                       "missing": check["missing"],
                                       "not_listed": check["not_listed"]}}
        print(f"{name}: {len(dst_hashes)} files; provenance matched {len(check['matched'])}, "
              f"mismatched {len(check['mismatched'])}, missing {len(check['missing'])}, "
              f"not listed {check['not_listed']}")
    sha = write_json(os.path.join(args.out_dir, "pools_manifest.json"), manifest)
    print(f"wrote {_display(os.path.join(args.out_dir, 'pools_manifest.json'))} sha256 {sha}")
    return 0


def cmd_sample(args) -> int:
    pools = os.path.join(args.out_dir, "pools")
    pool_manifest_path = os.path.join(args.out_dir, "pools_manifest.json")
    if not os.path.exists(pool_manifest_path):
        raise SystemExit("run copy-pools first: the sample reads the pool copies")
    pool_manifest = json.load(open(pool_manifest_path))
    paths = {"D": os.path.join(DATASETS, "far_v2"), "H": os.path.join(DATASETS, "far_v2_honest"),
             "F": os.path.join(DATASETS, "far_v2_nopressure"),
             "I": os.path.join(pools, "far_v2_user_inversion"),
             "N": os.path.join(pools, "far_v2_user_neutral")}
    for cond in ("I", "N"):
        name = os.path.basename(paths[cond])
        if hash_tree(paths[cond]) != pool_manifest["pools"][name]["files"]:
            raise SystemExit(f"{paths[cond]} no longer matches pools_manifest.json")

    excl = exclusion_sources()
    for k, path in enumerate(args.exclude_ids or []):
        excl[f"exclude_ids_{k}"] = load_exclude_file(path)
    union = sorted({i for src in excl.values() for i in src["ids"]})

    recs = {cond: {split: load_split_records(paths[cond], split)
                   for split in ("train", "validation", "test")} for cond in paths}
    ids = {cond: {split: record_ids(r) for split, r in by.items()} for cond, by in recs.items()}

    if args.count_only:
        print(json.dumps(count_eligible(recs, ids, union), indent=1))
        return 0

    # --- the fresh test sample
    d_draw = draw_condition(recs["D"]["test"], twin_id_sets=[ids["H"]["test"], ids["F"]["test"]],
                            exclude_ids=union, n=args.n, seed=args.seed, form_filter=act_naming)
    i_draw = draw_condition(recs["I"]["test"], twin_id_sets=[ids["N"]["test"]],
                            exclude_ids=union, n=args.n, seed=args.seed,
                            form_filter=act_naming_by_id(recs["D"]["test"]))
    for label, draw in (("D", d_draw), ("I", i_draw)):
        if draw["counts"]["drawn"] < args.n:
            print(f"warning: {label} drew {draw['counts']['drawn']} of {args.n} (START allows "
                  f"taking all that survive)")
    sample_ids = {"D": d_draw["ids"], "H": list(d_draw["ids"]), "F": list(d_draw["ids"]),
                  "I": i_draw["ids"], "N": list(i_draw["ids"])}
    for cond, twin_of in (("H", "D"), ("F", "D"), ("N", "I")):
        missing = set(sample_ids[cond]) - set(ids[cond]["test"])
        if missing:
            raise SystemExit(f"{cond} lacks {len(missing)} twins of sampled {twin_of} ids")
    assert not set(union) & set(sample_ids["D"]) and not set(union) & set(sample_ids["I"])

    dataset_files = {}
    for cond in ("D", "H", "F"):
        for rel, sha in hash_tree(paths[cond]).items():
            dataset_files[_display(os.path.join(paths[cond], rel))] = sha
    for cond in ("I", "N"):
        for rel, sha in hash_tree(paths[cond]).items():
            dataset_files[_display(os.path.join(paths[cond], rel))] = sha
    for extra in (LADDER_DESIGN, LADDER_SELECTED, CLAUSE_FORMS, HELD_OUT_JSON,
                  os.path.join(MECH_GROUPS, "far_heldout_D_sample.json"),
                  os.path.join(MECH_GROUPS, "far_heldout_I_sample.json")):
        dataset_files[_display(extra)] = sha256_file(extra)

    pool_files = {}
    for cond in ("I", "N"):
        name = os.path.basename(paths[cond])
        pool_files[name] = {"path": _display(paths[cond]),
                            "source": pool_manifest["pools"][name]["source"],
                            "sha256": {split: sha256_file(os.path.join(
                                paths[cond], split, "data-00000-of-00001.arrow"))
                                for split in ("train", "validation", "test")}}

    excluded = {}
    test_d, test_i = set(ids["D"]["test"]), set(ids["I"]["test"])
    for label, src in excl.items():
        excluded[label] = {k: v for k, v in src.items() if k != "ids"}
        excluded[label].update({"n": len(src["ids"]),
                                "in_D_test": len(set(src["ids"]) & test_d),
                                "in_I_test": len(set(src["ids"]) & test_i),
                                "ids": sorted(src["ids"])})
    excluded["union"] = {"n": len(union), "in_D_test": len(set(union) & test_d),
                         "in_I_test": len(set(union) & test_i)}

    sample = {"task": "far", "seed": args.seed, "split": "test",
              "ids": sample_ids,
              "pairing": {"H": "far_v2_honest, the neutral twin, same instance_id as D",
                          "F": "far_v2_nopressure, same instance_id as D",
                          "N": "far_v2_user_neutral, same instance_id as I",
                          "I_vs_D": ("drawn independently from the I pool test split with the "
                                     "same exclusions; overlap with D recorded in counts")},
              "act_naming_filter": ("clause_form of dataset/build_inversion_v2.py on the "
                                    "pressure clause; FAR v2 is act-naming throughout, so the "
                                    "filter keeps every row"),
              "excluded": excluded,
              "pool_files": pool_files,
              "counts": {"D": d_draw["counts"], "I": i_draw["counts"],
                         "per_condition": {c: len(v) for c, v in sample_ids.items()},
                         "D_and_I_overlap": len(set(sample_ids["D"]) & set(sample_ids["I"]))},
              "samples": {"D": d_draw["sample"], "I": i_draw["sample"]},
              "dataset_files": dataset_files}
    out_sample = os.path.join(args.out_dir, f"far_test_sample_seed{args.seed}.json")
    sha_s = write_json(out_sample, sample)
    if args.no_rank_ids:
        print(json.dumps({"per_condition": sample["counts"]["per_condition"],
                          "D": d_draw["counts"], "I": i_draw["counts"],
                          "D_and_I_overlap": sample["counts"]["D_and_I_overlap"],
                          "excluded": {k: (v["n"], v["in_D_test"], v["in_I_test"])
                                       for k, v in excluded.items()},
                          "sha256": {os.path.basename(out_sample): sha_s}}, indent=1))
        return 0

    # --- the rank ids (train + validation), with the split-half assignment
    rank = {"D": {}, "I": {}}
    rank_counts = {}
    for cond, twins in (("D", ("H", "F")), ("I", ("N",))):
        for split in ("train", "validation"):
            form = act_naming if cond == "D" else act_naming_by_id(recs["D"][split])
            records = [r for r in recs[cond][split] if form(r)]
            keep, dropped = paired_records(records, [ids[t][split] for t in twins])
            kept = [rid for rid in record_ids(keep) if rid not in set(union)]
            rank[cond][split] = kept
            rank_counts[f"{cond}_{split}"] = {"rows": len(recs[cond][split]),
                                             "dropped_no_twin": len(dropped),
                                             "removed_by_exclusion": len(keep) - len(kept),
                                             "kept": len(kept)}
    d_rows = {rid: r for split in ("train", "validation")
              for rid, r in zip(record_ids(recs["D"][split]), recs["D"][split])}
    d_rank = rank["D"]["train"] + rank["D"]["validation"]
    clusters = [d_rows[rid]["pressure_id"] for rid in d_rank]
    halves = split_halves(d_rank, clusters, seed=args.seed)
    i_rank = rank["I"]["train"] + rank["I"]["validation"]
    stray = [rid for rid in i_rank if rid not in halves]
    if stray:
        raise SystemExit(f"{len(stray)} I rank ids are not D rank ids; halves undefined for them")
    strata = {}
    for rid, cluster in zip(d_rank, clusters):
        strata.setdefault(cluster, Counter())[halves[rid]] += 1
    marg = {}
    for factor in ("designation_polarity", "item_polarity", "template_variant", "pressure_id"):
        c = {}
        for rid in d_rank:
            level = str(d_rows[rid][factor])
            c.setdefault(level, Counter())[halves[rid]] += 1
        marg[factor] = {k: dict(sorted(v.items())) for k, v in sorted(c.items())}
    rank_out = {"task": "far", "seed": args.seed,
                "rule": "rank on train and validation only (START item 10, Ids)",
                "ids": rank,
                "counts": rank_counts,
                "halves": {"stratified_by": "pressure_id (the pressure cluster of F-rte-005)",
                           "rule": split_halves.__doc__.strip().split("\n")[0],
                           "A": sorted(r for r in d_rank if halves[r] == "A"),
                           "B": sorted(r for r in d_rank if halves[r] == "B"),
                           "I_A": sorted(r for r in i_rank if halves[r] == "A"),
                           "I_B": sorted(r for r in i_rank if halves[r] == "B"),
                           "per_stratum": {k: dict(sorted(v.items())) for k, v in sorted(strata.items())},
                           "marginals": marg},
                "excluded_union_n": len(union),
                "test_sample": {"path": _display(out_sample), "sha256": sha_s}}
    out_rank = os.path.join(args.out_dir, "far_rank_ids.json" if args.seed == SEED
                            else f"far_rank_ids_seed{args.seed}.json")
    sha_r = write_json(out_rank, rank_out)
    print(json.dumps({"per_condition": sample["counts"]["per_condition"],
                      "D": d_draw["counts"], "I": i_draw["counts"],
                      "D_and_I_overlap": sample["counts"]["D_and_I_overlap"],
                      "excluded": {k: (v["n"], v["in_D_test"], v["in_I_test"])
                                   for k, v in excluded.items()},
                      "rank": rank_counts,
                      "halves": {h: len(rank_out["halves"][h]) for h in ("A", "B", "I_A", "I_B")},
                      "sha256": {os.path.basename(out_sample): sha_s,
                                 os.path.basename(out_rank): sha_r}},
                     indent=1))
    return 0


def cmd_nulls(args) -> int:
    raw = json.load(open(args.neurons))
    if not isinstance(raw, dict) or not raw:
        raise SystemExit(f"{args.neurons}: expected {{name: [[kind, layer, index], ...]}}")
    if args.set is None:
        if len(raw) != 1:
            raise SystemExit(f"{args.neurons} holds {len(raw)} sets; name one with --set")
        name = next(iter(raw))
    else:
        if args.set not in raw:
            raise SystemExit(f"{args.neurons} has no set {args.set!r}")
        name = args.set
    tested = parse_neuron_set(raw[name])
    if name.startswith("null_"):
        raise SystemExit(f"set name {name!r} collides with the null names")
    nulls = matched_nulls(tested, k=args.k, seed=args.seed)
    groups = {name: to_members(tested)}
    for i, null in enumerate(nulls):
        groups[f"null_{i}"] = to_members(null)
    sha = write_json(args.out, groups)
    stem = args.out[:-5] if args.out.endswith(".json") else args.out
    prov = {"kind": "neuron_partition_matched_nulls", "seed": args.seed, "k": args.k,
            "rng": "numpy default_rng([seed, k]) per null k; layers ascending",
            "source": {"path": os.path.abspath(args.neurons), "sha256": sha256_file(args.neurons),
                       "set": name},
            "size": sum(len(v) for v in tested.values()),
            "per_layer": {str(l): len(v) for l, v in tested.items()},
            "rule": ("same size and same per-layer counts as the tested set; uniform without "
                     "replacement over the layer's 14,336 indices minus the tested set's own"),
            "mirrors": ("evaluation/masks.py sample_random_masks (mlp_hidden branch), the null "
                        "behind evaluate_circuit.py --n-random; departs only by excluding the "
                        "tested neurons"),
            "geometry": {"num_layers": NUM_LAYERS, "intermediate_size": INTERMEDIATE},
            "output": {"path": os.path.abspath(args.out), "sha256": sha}}
    write_json(stem + ".provenance.json", prov)
    print(f"wrote {args.out} ({1 + len(nulls)} groups, size {prov['size']}) and "
          f"{stem}.provenance.json")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("copy-pools", help="copy and hash the user-turn I and N pools")
    c.add_argument("--pool-source", default=POOL_SOURCE)
    c.add_argument("--out-dir", default=OUT_DIR)
    s = sub.add_parser("sample", help="the fresh FAR test sample and the rank ids")
    s.add_argument("--n", type=int, default=N_TEST)
    s.add_argument("--seed", type=int, default=SEED)
    s.add_argument("--out-dir", default=OUT_DIR)
    s.add_argument("--exclude-ids", action="append", default=[], metavar="JSON",
                   help=("repeatable: a file whose ids (a per-condition 'ids' dict, a flat 'ids' "
                         "list or a flat list) are removed from every pool before the draw; its "
                         "sha256 is recorded in the sample's 'excluded' block"))
    s.add_argument("--count-only", action="store_true",
                   help="print the eligible counts and strata per pool; draw and write nothing")
    s.add_argument("--no-rank-ids", action="store_true",
                   help="write only the test sample, not far_rank_ids*.json")
    n = sub.add_parser("nulls", help="size- and layer-matched random neuron sets")
    n.add_argument("neurons", help="JSON {name: [['mlp_hidden', layer, index], ...]}")
    n.add_argument("--out", required=True)
    n.add_argument("--set", default=None, help="which set, if the file holds several")
    n.add_argument("-k", type=int, default=N_NULLS)
    n.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)
    return {"copy-pools": cmd_copy_pools, "sample": cmd_sample, "nulls": cmd_nulls}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
