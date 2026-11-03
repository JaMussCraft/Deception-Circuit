"""
scripts/neuron_partition_sets.py — the N1 neuron classes and the N3 split-half stability of `neuron-partition`.

Implements ruling R6 of `docs/research/neuron-partition/spec.md`. CPU only (numpy, torch only to read `scores.pt`).

**Scores** (W1's `component_analysis/neuron_attribution.py`; every `scores.pt` is {name: float32 [32, 14336]}):

* s_D = `atp_<pos>_mean` of the `--dh` run (D clean, H twin). Positive: the neuron supports the deceptive answer.
* s_I = `atp_<pos>_mean` of the `--in` run (I clean, user-neutral twin). Positive: supports the inverted answer.
* s_H = minus `rev_atp_<pos>_mean` of the `--dh-reverse` run. The scorer's `--reverse` adds the `rev_atp_*` keys to
  the dh run's own `scores.pt`: (a_H - a_D) * dm_H/da with H as the clean stream and D as the twin, m still
  logit(opposite) - logit(honest) in D's orientation. A neuron that holds H on the honest answer has a negative
  `rev_atp`, so the flip makes positive mean "supports the honest answer". The `atp_*` keys of a `_rev` directory are
  still the D-clean forward scores and are never used for s_H.
* `--score contrast` (R6's comparison ranking): s_D = `contrast_<pos>_mean` of dh (mean a_D - a_H), s_I the same of
  in (a_I - a_N), and s_H = minus `contrast_<pos>_mean` of dh (a_H - a_D, "more active under H"). Contrast has no
  readout orientation, so no reverse run enters, and T_D and T_H are disjoint by construction: all_shared is
  always empty and H_only is T_H - T_I. That is a property of the rule, not a finding.
* `--position clause` reads the `*_clause_*` keys instead of `*_readout_*`; `--position all` reads the all-position
  keys `atp_all_mean` and `rev_atp_all_mean` (ruling R11: the primary ranking, because the twin ablation writes every
  position). The scorer writes no `contrast_all_*` keys, so `--score contrast --position all` stops with the missing
  key named.

**Partition** (R6), for each k of the ladder 500, 1,000, 2,000: T_X = the top-k neurons by s_X among those with
s_X > 0 (all positive ones when fewer than k are positive, recorded), ties broken by the flat index (layer * 14336 +
index) ascending. D_only = T_D - (T_I | T_H); DI_shared = (T_D & T_I) - T_H; H_only = T_H - (T_D | T_I);
all_shared = T_D & T_I & T_H.

    python scripts/neuron_partition_sets.py partition --dh DH_REV_DIR --in IN_DIR --dh-reverse DH_REV_DIR --out-dir OUT

writes `<prefix>[_contrast][_clause]_sets_k<k>.json` ({name: [["mlp_hidden", layer, index], ...]}, the four classes
and T_D, T_I, T_H, empty sets omitted because the groups loaders refuse them), `..._sets_k<k>_with_nulls.json` (the
four classes, each followed by 20 size-and-layer-matched nulls `null_<class>_<k>_<i>` from W3's
`scripts/neuron_partition_data.py nulls`, seed 2), the per-class null files with W3's provenance sidecars under
`nulls/`, and `partition_summary[_contrast][_clause].json` (sizes, per-layer histograms, thresholds, overlaps,
provenance with the sha256 of every input and output).

**Stability** (N3): `stability --dh A B --in A B --dh-reverse A B` partitions each half and reports, per k, the
Jaccard of T_D, T_I, T_H and of every class between the halves, against the ceiling J(T_D(A), T_D(B)) (the
same-condition split-half of the D-versus-H run) and two floors: the analytic expected Jaccard of two uniform random
sets of the observed sizes out of 32 * 14336 = 458,752 neurons, and an empirical floor from 20 seeded uniform draws
(not layer-matched). A set is "stable" iff its Jaccard >= half the ceiling (START item 10, N3).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NULLS_SCRIPT = os.path.join(REPO, "scripts", "neuron_partition_data.py")
NUM_LAYERS = 32
INTERMEDIATE = 14336
N_NEURONS = NUM_LAYERS * INTERMEDIATE        # 458,752
NEURON_KIND = "mlp_hidden"
LADDER = (500, 1000, 2000)
POSITIONS = ("readout", "clause", "all")
CLASSES = ("D_only", "DI_shared", "H_only", "all_shared")
TOP_SETS = ("T_D", "T_I", "T_H")
N_NULLS = 20
NULL_SEED = 2
FLOOR_DRAWS = 20
FLOOR_SEED = 2

CLASS_RULES = {
    "D_only": "T_D - (T_I | T_H)",
    "DI_shared": "(T_D & T_I) - T_H",
    "H_only": "T_H - (T_D | T_I)",
    "all_shared": "T_D & T_I & T_H",
}


# ==============================================================================
# INPUTS
# ==============================================================================

def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_run(directory: str) -> dict:
    """{dir, scores {name: float64 ndarray [32, 14336]}, provenance} for one scorer output directory."""
    import torch

    path = os.path.join(directory, "scores.pt")
    if not os.path.isfile(path):
        raise SystemExit(f"{directory}: no scores.pt")
    try:
        raw = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:                                   # torch without weights_only
        raw = torch.load(path, map_location="cpu")
    scores = {}
    for name, value in raw.items():
        array = value.detach().double().cpu().numpy()
        if array.shape != (NUM_LAYERS, INTERMEDIATE):
            raise SystemExit(f"{path}: {name} has shape {array.shape}, expected ({NUM_LAYERS}, {INTERMEDIATE})")
        if not np.all(np.isfinite(array)):
            raise SystemExit(f"{path}: {name} has non-finite values")
        scores[name] = array
    prov = {"dir": os.path.abspath(directory), "dir_name": os.path.basename(os.path.normpath(directory)),
            "scores_sha256": sha256_file(path), "keys": sorted(scores)}
    rows_path = os.path.join(directory, "rows.json")
    if os.path.isfile(rows_path):
        rows = json.load(open(rows_path))
        prov.update({"rows_sha256": sha256_file(rows_path), "n_rows": rows.get("n_rows"),
                     "reverse": rows.get("reverse"), "task": rows.get("task"), "pair": rows.get("pair"),
                     "splits": rows.get("splits")})
    manifest_path = os.path.join(directory, "run_manifest.json")
    if os.path.isfile(manifest_path):
        manifest = json.load(open(manifest_path))
        prov.update({"manifest_sha256": sha256_file(manifest_path),
                     "git_commit": manifest.get("git_commit"), "git_dirty": manifest.get("git_dirty"),
                     "dirty_diff_hash": manifest.get("dirty_diff_hash"),
                     "manifest_hash": manifest.get("manifest_hash"),
                     "slurm_job_id": manifest.get("slurm_job_id"), "created": manifest.get("created"),
                     "code_sha256": manifest.get("code_sha256")})
    else:
        prov["git_commit"] = None
    return {"dir": directory, "scores": scores, "provenance": prov}


def _key(run: dict, key: str) -> np.ndarray:
    if key not in run["scores"]:
        raise SystemExit(f"{run['dir']}: scores.pt has no {key!r} (it has {sorted(run['scores'])})")
    return run["scores"][key]


def signed_scores(dh: dict, inv: dict, rev: Optional[dict], *, score: str, position: str,
                  allow_missing_reverse: bool) -> dict:
    """{s_D, s_I, s_H (or None), keys, notes} per R6; see the module docstring for the signs."""
    if score not in ("atp", "contrast") or position not in POSITIONS:
        raise ValueError(f"score {score!r} / position {position!r}")
    notes = []
    s_d = _key(dh, f"{score}_{position}_mean")
    s_i = _key(inv, f"{score}_{position}_mean")
    keys = {"s_D": f"+{score}_{position}_mean of --dh", "s_I": f"+{score}_{position}_mean of --in"}
    if score == "contrast":
        s_h = -s_d
        keys["s_H"] = f"-contrast_{position}_mean of --dh (a_H - a_D)"
        notes.append("contrast ranking: s_H = -s_D, so T_D and T_H are disjoint by construction; all_shared is "
                     "empty and H_only = T_H - T_I by the rule, not by the data")
    else:
        rev_key = f"rev_atp_{position}_mean"
        if rev is not None and rev_key in rev["scores"]:
            s_h = -rev["scores"][rev_key]
            keys["s_H"] = f"-{rev_key} of --dh-reverse"
            fwd = f"atp_{position}_mean"
            if rev is not dh and fwd in rev["scores"]:
                diff = float(np.max(np.abs(rev["scores"][fwd] - s_d)))
                notes.append(f"consistency: max |{fwd}(--dh) - {fwd}(--dh-reverse)| = {diff:.3g}")
        elif allow_missing_reverse:
            s_h = None
            keys["s_H"] = "absent (--allow-missing-reverse)"
            notes.append(f"s_H absent: {rev_key} is not in the --dh-reverse scores, so T_H is empty, H_only and "
                         f"all_shared are not built, and D_only here is only T_D - T_I")
        else:
            where = "no --dh-reverse given" if rev is None else f"{rev['dir']} has no {rev_key}"
            raise SystemExit(f"s_H needs {rev_key} from a scorer run with --reverse ({where}); the atp_* keys of "
                             f"any run are D-clean scores and cannot stand in. Pass --allow-missing-reverse for a "
                             f"D/I-only partition.")
    return {"s_D": s_d, "s_I": s_i, "s_H": s_h, "keys": keys, "notes": notes}


# ==============================================================================
# THE PARTITION (pure functions; flat index = layer * 14336 + neuron)
# ==============================================================================

def top_positive(score: np.ndarray, k: int) -> dict:
    """The top-k flat indices by score among score > 0; ties by flat index ascending.

    -> {set (frozenset of flat ints), n_positive, size, truncated, threshold (k-th score or None), max}
    """
    flat = np.asarray(score, dtype=np.float64).reshape(-1)
    positive = np.flatnonzero(flat > 0)
    order = positive[np.lexsort((positive, -flat[positive]))]
    chosen = order[:k]
    return {"set": frozenset(int(i) for i in chosen), "n_positive": int(positive.size), "size": int(chosen.size),
            "truncated": bool(positive.size < k),
            "threshold": float(flat[chosen[-1]]) if chosen.size else None,
            "max": float(flat[chosen[0]]) if chosen.size else None}


def classes_from_tops(t_d: frozenset, t_i: frozenset, t_h: Optional[frozenset]) -> Dict[str, frozenset]:
    """R6's four classes; with t_h None (s_H absent) only D_only = T_D - T_I and DI_shared = T_D & T_I."""
    if t_h is None:
        return {"D_only": t_d - t_i, "DI_shared": t_d & t_i}
    return {"D_only": t_d - (t_i | t_h), "DI_shared": (t_d & t_i) - t_h,
            "H_only": t_h - (t_d | t_i), "all_shared": t_d & t_i & t_h}


def partition(s_d, s_i, s_h, k: int) -> dict:
    """{tops: {T_X: top_positive record}, sets: {name: frozenset}} at one k."""
    tops = {"T_D": top_positive(s_d, k), "T_I": top_positive(s_i, k)}
    if s_h is not None:
        tops["T_H"] = top_positive(s_h, k)
    t_h = tops["T_H"]["set"] if "T_H" in tops else None
    sets = dict(classes_from_tops(tops["T_D"]["set"], tops["T_I"]["set"], t_h))
    for name, rec in tops.items():
        sets[name] = rec["set"]
    return {"tops": tops, "sets": sets}


def to_members(flat_set) -> List[list]:
    return [[NEURON_KIND, int(i // INTERMEDIATE), int(i % INTERMEDIATE)] for i in sorted(flat_set)]


def from_members(members) -> frozenset:
    return frozenset(int(layer) * INTERMEDIATE + int(index) for _, layer, index in members)


def layer_histogram(flat_set) -> List[int]:
    counts = np.zeros(NUM_LAYERS, dtype=np.int64)
    for i in flat_set:
        counts[i // INTERMEDIATE] += 1
    return [int(c) for c in counts]


def overlaps(sets: Dict[str, frozenset]) -> dict:
    out = {}
    names = [n for n in TOP_SETS if n in sets]
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            x, y = sets[names[a]], sets[names[b]]
            out[f"{names[a]}&{names[b]}"] = {"n": len(x & y), "jaccard": jaccard(x, y)}
    if len(names) == 3:
        d, i, h = (sets[n] for n in names)
        out["regions"] = {"D_only_region": len(d - i - h), "I_only_region": len(i - d - h),
                          "H_only_region": len(h - d - i), "DI_not_H": len((d & i) - h),
                          "DH_not_I": len((d & h) - i), "IH_not_D": len((i & h) - d), "DIH": len(d & i & h)}
    return out


# ==============================================================================
# JACCARD AND FLOORS
# ==============================================================================

def jaccard(a, b) -> Optional[float]:
    a, b = set(a), set(b)
    union = len(a | b)
    return None if union == 0 else len(a & b) / union


def expected_random_jaccard(n1: int, n2: int, n: int = N_NEURONS) -> Optional[float]:
    """Approximate E[J] of two independent uniform random sets of sizes n1, n2 out of n: E[|A & B|] = n1 n2 / n,
    divided by n1 + n2 - n1 n2 / n. With n1 = n2 = k it is k / (2n - k)."""
    if n1 + n2 == 0:
        return None
    inter = n1 * n2 / n
    return inter / (n1 + n2 - inter)


def empirical_floor(n1: int, n2: int, *, draws: int = FLOOR_DRAWS, seed: int = FLOOR_SEED,
                    n: int = N_NEURONS) -> Optional[dict]:
    """Jaccard of two uniform random sets of sizes n1 and n2 (over all n neurons, not layer-matched), `draws` times;
    draw j uses np.random.default_rng([seed, j])."""
    if n1 + n2 == 0:
        return None
    values = []
    for j in range(draws):
        rng = np.random.default_rng([int(seed), int(j)])
        a = rng.choice(n, size=n1, replace=False)
        b = rng.choice(n, size=n2, replace=False)
        values.append(jaccard(a.tolist(), b.tolist()))
    return {"mean": float(np.mean(values)), "max": float(np.max(values)), "draws": draws, "seed": seed,
            "values": [float(v) for v in values]}


# ==============================================================================
# NULLS (W3's `nulls` subcommand)
# ==============================================================================

def null_command(set_path: str, name: str, out_path: str, *, k: int, seed: int) -> List[str]:
    return [sys.executable, NULLS_SCRIPT, "nulls", set_path, "--set", name, "--out", out_path, "-k", str(k),
            "--seed", str(seed)]


def call_nulls(set_path: str, name: str, out_path: str, *, k: int = N_NULLS, seed: int = NULL_SEED) -> dict:
    """Run W3's generator for one named set and -> {command, groups (ordered dict), provenance, sha256s}."""
    command = null_command(set_path, name, out_path, k=k, seed=seed)
    done = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit(f"nulls failed for {name}: {' '.join(command)}\n{done.stdout}\n{done.stderr}")
    groups = json.load(open(out_path))
    stem = out_path[:-5] if out_path.endswith(".json") else out_path
    prov_path = stem + ".provenance.json"
    return {"command": command, "groups": groups, "path": os.path.abspath(out_path),
            "sha256": sha256_file(out_path), "provenance_path": os.path.abspath(prov_path),
            "provenance_sha256": sha256_file(prov_path), "provenance": json.load(open(prov_path))}


# ==============================================================================
# OUTPUT HELPERS
# ==============================================================================

def write_json(path: str, obj, *, force: bool) -> str:
    if os.path.exists(path) and not force:
        raise SystemExit(f"{path} exists; pass --force to replace it or choose another --out-dir")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(obj, handle, indent=1)
        handle.write("\n")
    return sha256_file(path)


def variant_tag(score: str, position: str) -> str:
    return ("" if score == "atp" else "_contrast") + ("" if position == "readout" else f"_{position}")


def task_prefix(dh: dict) -> str:
    task = dh["provenance"].get("task") or "far_v2"
    return task.split("_")[0]


def script_provenance(argv) -> dict:
    return {"script": os.path.abspath(__file__), "script_sha256": sha256_file(os.path.abspath(__file__)),
            "nulls_script": NULLS_SCRIPT,
            "nulls_script_sha256": sha256_file(NULLS_SCRIPT) if os.path.isfile(NULLS_SCRIPT) else None,
            "argv": list(argv), "python": sys.executable,
            "created": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}


def _load_triplet(dh_dir, in_dir, rev_dir):
    dh = load_run(dh_dir)
    inv = load_run(in_dir)
    if rev_dir is None:
        rev = None
    elif os.path.abspath(rev_dir) == os.path.abspath(dh_dir):
        rev = dh
    else:
        rev = load_run(rev_dir)
    return dh, inv, rev


# ==============================================================================
# PARTITION COMMAND
# ==============================================================================

def run_partition(args, argv) -> dict:
    dh, inv, rev = _load_triplet(args.dh, args.in_dir, args.dh_reverse)
    signed = signed_scores(dh, inv, rev, score=args.score, position=args.position,
                           allow_missing_reverse=args.allow_missing_reverse)
    prefix = args.prefix or task_prefix(dh)
    tag = variant_tag(args.score, args.position)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    null_dir = os.path.join(out_dir, "nulls")

    summary = {
        "kind": "neuron_partition_sets", "ruling": "R6 (docs/research/neuron-partition/spec.md)",
        "label": args.label, "score": args.score, "position": args.position, "ladder": list(args.k),
        "signed_scores": signed["keys"], "notes": list(signed["notes"]),
        "class_rules": {n: r for n, r in CLASS_RULES.items()
                        if signed["s_H"] is not None or n in ("D_only", "DI_shared")},
        "top_rule": ("top-k by signed score among neurons with score > 0; all positive ones when fewer than k; "
                     "ties by flat index layer*14336+index ascending"),
        "nulls": None if args.no_nulls else {
            "generator": NULLS_SCRIPT, "per_class": args.n_nulls, "seed": args.null_seed,
            "naming": "null_<class>_<k>_<i>, i = W3's null index 0..n-1",
            "for": "the four classes only (not T_D, T_I, T_H)",
            "command_template": " ".join(null_command("<class file>", "<class>", "<out>", k=args.n_nulls,
                                                      seed=args.null_seed))},
        "inputs": {"dh": dh["provenance"], "in": inv["provenance"],
                   "dh_reverse": None if rev is None else rev["provenance"]},
        "provenance": script_provenance(argv), "by_k": {}, "outputs": {}}
    if dh["provenance"].get("reverse") is False and signed["s_H"] is None:
        summary["notes"].append(f"{dh['provenance']['dir_name']} was scored without --reverse; s_H needs a "
                                f"--reverse rerun of the dh pair")

    for k in args.k:
        part = partition(signed["s_D"], signed["s_I"], signed["s_H"], k)
        sets = part["sets"]
        entry = {
            "tops": {n: {kk: v for kk, v in rec.items() if kk != "set"} for n, rec in part["tops"].items()},
            "sizes": {n: len(sets[n]) for n in list(CLASSES) + list(TOP_SETS) if n in sets},
            "per_layer": {n: layer_histogram(sets[n]) for n in list(CLASSES) + list(TOP_SETS) if n in sets},
            "overlaps": overlaps(sets),
            "empty_omitted": [n for n in list(CLASSES) + list(TOP_SETS) if n in sets and not sets[n]],
            "not_built": [n for n in list(CLASSES) + list(TOP_SETS) if n not in sets]}
        for n, rec in part["tops"].items():
            if rec["truncated"]:
                summary["notes"].append(f"k={k}: {n} has only {rec['n_positive']} positive scores, fewer than k")
        sets_obj = {n: to_members(sets[n]) for n in list(CLASSES) + list(TOP_SETS) if n in sets and sets[n]}
        sets_path = os.path.join(out_dir, f"{prefix}{tag}_sets_k{k}.json")
        summary["outputs"][f"sets_k{k}"] = {"path": sets_path, "sha256": write_json(sets_path, sets_obj,
                                                                                     force=args.force)}
        if not args.no_nulls:
            with_nulls = {}
            calls = {}
            for name in CLASSES:
                if name not in sets_obj:
                    continue
                out = os.path.join(null_dir, f"{prefix}{tag}_k{k}_{name}_nulls.json")
                if os.path.exists(out) and not args.force:
                    raise SystemExit(f"{out} exists; pass --force or choose another --out-dir")
                got = call_nulls(sets_path, name, out, k=args.n_nulls, seed=args.null_seed)
                if got["groups"].get(name) != sets_obj[name]:
                    raise SystemExit(f"W3's nulls file {out} does not repeat {name} unchanged")
                with_nulls[name] = sets_obj[name]
                for i in range(args.n_nulls):
                    with_nulls[f"null_{name}_{k}_{i}"] = got["groups"][f"null_{i}"]
                calls[name] = {"command": " ".join(got["command"]), "path": got["path"], "sha256": got["sha256"],
                               "provenance_path": got["provenance_path"],
                               "provenance_sha256": got["provenance_sha256"]}
            entry["null_calls"] = calls
            if with_nulls:
                path = os.path.join(out_dir, f"{prefix}{tag}_sets_k{k}_with_nulls.json")
                summary["outputs"][f"sets_k{k}_with_nulls"] = {
                    "path": path, "sha256": write_json(path, with_nulls, force=args.force),
                    "groups": len(with_nulls)}
        summary["by_k"][str(k)] = entry

    summary_path = os.path.join(out_dir, f"partition_summary{tag}.json")
    write_json(summary_path, summary, force=args.force)
    summary["summary_path"] = summary_path
    return summary


def print_partition(summary: dict) -> None:
    print(f"label: {summary['label']}")
    print(f"score {summary['score']}, position {summary['position']}; s_X: {summary['signed_scores']}")
    for note in summary["notes"]:
        print(f"note: {note}")
    for k, entry in summary["by_k"].items():
        sizes = ", ".join(f"{n} {v}" for n, v in entry["sizes"].items())
        thresholds = ", ".join(f"{n} {rec['threshold']:.4g} (pos {rec['n_positive']})"
                               if rec["threshold"] is not None else f"{n} none" for n, rec in entry["tops"].items())
        print(f"k={k}: {sizes}")
        print(f"  thresholds: {thresholds}")
        for name in ("D_only", "DI_shared", "H_only", "all_shared"):
            hist = entry["per_layer"].get(name)
            if hist and sum(hist):
                top = sorted(range(NUM_LAYERS), key=lambda layer: -hist[layer])[:5]
                print(f"  {name} densest layers: " + ", ".join(f"L{layer} {hist[layer]}" for layer in top))
    print(f"wrote {summary['summary_path']}")
    for name, out in summary["outputs"].items():
        print(f"  {name}: {out['path']}")


# ==============================================================================
# STABILITY COMMAND
# ==============================================================================

def compare_halves(part_a: dict, part_b: dict, *, floor_draws: int, floor_seed: int) -> dict:
    """Per set name present in either half: sizes, Jaccard, the ceiling ratio inputs and the two floors."""
    ceiling = jaccard(part_a["sets"]["T_D"], part_b["sets"]["T_D"])
    rows = {}
    names = [n for n in list(TOP_SETS) + list(CLASSES) if n in part_a["sets"] or n in part_b["sets"]]
    for name in names:
        a = part_a["sets"].get(name, frozenset())
        b = part_b["sets"].get(name, frozenset())
        j = jaccard(a, b) if a and b else None
        stable = None if j is None or ceiling is None else bool(j >= 0.5 * ceiling)
        rows[name] = {"size_a": len(a), "size_b": len(b), "intersection": len(a & b), "jaccard": j,
                      "ceiling": ceiling, "half_ceiling": None if ceiling is None else 0.5 * ceiling,
                      "floor_analytic": expected_random_jaccard(len(a), len(b)),
                      "floor_empirical": empirical_floor(len(a), len(b), draws=floor_draws, seed=floor_seed),
                      "stable": stable,
                      "verdict": "n/a (empty in a half)" if j is None else ("stable" if stable else "not stable")}
    return {"ceiling": ceiling, "sets": rows}


def stability_markdown(summary: dict) -> str:
    lines = [f"# Split-half stability ({summary['score']}, {summary['position']})", "",
             f"Label: {summary['label']}. Ceiling: Jaccard of T_D between the halves of the D-versus-H run (so T_D "
             f"sits at the ceiling by definition). Floors: analytic expected Jaccard of two uniform random sets of the "
             f"observed sizes out of {N_NEURONS:,} neurons, and the mean of {summary['floor']['draws']} seeded "
             f"uniform draws (seed {summary['floor']['seed']}, not layer-matched). Stable means Jaccard >= half the "
             f"ceiling.", ""]
    lines.append("| k | set | size A | size B | Jaccard | ceiling | floor (analytic) | floor (empirical) | verdict |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    fmt = (lambda v: "n/a" if v is None else f"{v:.4f}")
    for k, entry in summary["by_k"].items():
        for name, row in entry["sets"].items():
            emp = row["floor_empirical"]["mean"] if row["floor_empirical"] else None
            lines.append(f"| {k} | {name} | {row['size_a']} | {row['size_b']} | {fmt(row['jaccard'])} | "
                         f"{fmt(row['ceiling'])} | {fmt(row['floor_analytic'])} | {fmt(emp)} | {row['verdict']} |")
    return "\n".join(lines) + "\n"


def run_stability(args, argv) -> dict:
    halves = {}
    rev_dirs = args.dh_reverse or [None, None]
    for h, label in enumerate(("A", "B")):
        dh, inv, rev = _load_triplet(args.dh[h], args.in_dir[h], rev_dirs[h])
        signed = signed_scores(dh, inv, rev, score=args.score, position=args.position,
                               allow_missing_reverse=args.allow_missing_reverse)
        halves[label] = {"runs": (dh, inv, rev), "signed": signed}
    tag = variant_tag(args.score, args.position)
    summary = {
        "kind": "neuron_partition_stability", "label": args.label, "score": args.score, "position": args.position,
        "ladder": list(args.k), "signed_scores": halves["A"]["signed"]["keys"],
        "notes": sorted(set(halves["A"]["signed"]["notes"] + halves["B"]["signed"]["notes"])),
        "ceiling_rule": "Jaccard of T_D(half A) and T_D(half B): the same-condition split-half of the D-versus-H run",
        "floor": {"analytic": "E[J] ~ (n1 n2 / N) / (n1 + n2 - n1 n2 / N), N = 458,752; k / (2N - k) when n1 = n2 "
                              "= k", "draws": args.floor_draws, "seed": args.floor_seed,
                  "empirical": "uniform over all N neurons, not layer-matched; draw j uses default_rng([seed, j])"},
        "stable_rule": "Jaccard >= 0.5 * ceiling (START item 10, N3); n/a when the set is empty in a half",
        "inputs": {label: {"dh": h["runs"][0]["provenance"], "in": h["runs"][1]["provenance"],
                           "dh_reverse": None if h["runs"][2] is None else h["runs"][2]["provenance"]}
                   for label, h in halves.items()},
        "provenance": script_provenance(argv), "by_k": {}}
    for k in args.k:
        parts = {label: partition(h["signed"]["s_D"], h["signed"]["s_I"], h["signed"]["s_H"], k)
                 for label, h in halves.items()}
        summary["by_k"][str(k)] = compare_halves(parts["A"], parts["B"], floor_draws=args.floor_draws,
                                                 floor_seed=args.floor_seed)
    out_dir = os.path.abspath(args.out_dir)
    json_path = os.path.join(out_dir, f"stability_summary{tag}.json")
    md_path = os.path.join(out_dir, f"stability_summary{tag}.md")
    write_json(json_path, summary, force=args.force)
    if os.path.exists(md_path) and not args.force:
        raise SystemExit(f"{md_path} exists; pass --force")
    with open(md_path, "w") as handle:
        handle.write(stability_markdown(summary))
    summary["summary_path"] = json_path
    summary["markdown_path"] = md_path
    return summary


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(q):
        q.add_argument("--score", choices=("atp", "contrast"), default="atp")
        q.add_argument("--position", choices=POSITIONS, default="readout",
                       help="readout (default), clause, or all (R11: every position)")
        q.add_argument("-k", "--k", type=int, nargs="+", default=list(LADDER), help="the ladder (default 500 1000 "
                                                                                     "2000)")
        q.add_argument("--allow-missing-reverse", action="store_true",
                       help="treat s_H as absent when the reverse keys are missing (pilot only): T_H empty, only "
                            "D_only (= T_D - T_I) and DI_shared built")
        q.add_argument("--label", default="neuron-partition N1 ranking")
        q.add_argument("--out-dir", required=True)
        q.add_argument("--force", action="store_true", help="replace existing output files")

    a = sub.add_parser("partition", help="R6 classes at every k, with matched nulls")
    a.add_argument("--dh", required=True, help="scorer directory of the D-versus-H run (D clean)")
    a.add_argument("--in", dest="in_dir", required=True, help="scorer directory of the I-versus-user-neutral run")
    a.add_argument("--dh-reverse", default=None, help="scorer directory holding rev_atp_* (a dh run with --reverse; "
                                                      "usually the same directory as --dh)")
    a.add_argument("--prefix", default=None, help="file prefix (default: the task's first word, e.g. far)")
    a.add_argument("--n-nulls", type=int, default=N_NULLS)
    a.add_argument("--null-seed", type=int, default=NULL_SEED)
    a.add_argument("--no-nulls", action="store_true")
    common(a)

    s = sub.add_parser("stability", help="N3 split-half Jaccard against ceiling and floors")
    s.add_argument("--dh", nargs=2, required=True, metavar=("HALF_A", "HALF_B"))
    s.add_argument("--in", dest="in_dir", nargs=2, required=True, metavar=("HALF_A", "HALF_B"))
    s.add_argument("--dh-reverse", nargs=2, default=None, metavar=("HALF_A", "HALF_B"))
    s.add_argument("--floor-draws", type=int, default=FLOOR_DRAWS)
    s.add_argument("--floor-seed", type=int, default=FLOOR_SEED)
    common(s)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    argv_list = list(sys.argv if argv is None else ["scripts/neuron_partition_sets.py"] + list(argv))
    if any(k <= 0 for k in args.k):
        raise SystemExit("every k must be positive")
    if args.cmd == "partition":
        print_partition(run_partition(args, argv_list))
    else:
        summary = run_stability(args, argv_list)
        print(stability_markdown(summary))
        print(f"wrote {summary['summary_path']} and {summary['markdown_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
