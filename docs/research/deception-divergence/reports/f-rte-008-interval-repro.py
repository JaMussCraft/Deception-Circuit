"""Reproduce the MMLU-subject-clustered interval of finding F-rte-008 (B3 J4 sycophancy transfer).

The row reports, for S_all at the post-cue span, f 0.724 with an item bootstrap of 0.702 to 0.746 (stored in
`results.json`) and a subject-clustered interval of 0.669 to 0.770 that no data file records. The J4 review
(`docs/research/instructed-route/reviews/07-j4-review.md`, section on bootstrap clustering) states the clustered
interval as a sensitivity check with 2,000 resamples at seed 1, plus 0.292 to 0.371 for S_q. This script recomputes
both from the stored pass-2 margins and the item file, with no model run.

Method. f = (mean C - mean K) / (mean C - mean T) over the kept items, where C is the cued margin, K the patched
margin and T the uncued-twin margin (`spontaneous.stats.mediated_fraction`). Each resample draws as many subjects as
there are among the kept items, with replacement from the sorted subject labels, using
`numpy.random.default_rng(seed).integers(0, k, size=(n_boot, k))`, and takes every kept item of each drawn subject.
The interval is the 2.5 and 97.5 percentiles. This is the scheme of `cluster_bootstrap` in
`scripts/instructed_route_b2_read.py`, with subjects as clusters. The item bootstrap is recomputed too, as the
ported `instance_boot` and `f_boot` at seed 0, to check it against `results.json`.

Run with the mgnp interpreter, isolated, from any directory:

    /u/swong2/.conda/envs/mgnp/bin/python -I f-rte-008-interval-repro.py MARGINS ITEMS RESULTS OUT_JSON

Pure NumPy and the standard library; it imports nothing from the repository.
"""
import hashlib
import json
import sys

import numpy as np

N_BOOT = 2000
SEEDS = [1, 0, 20261101]
ARMS = ["S_all@post_tag", "S_q@post_tag"]


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def repo_relative(path):
    """The path below the Deception-Circuit checkout or one of its worktrees, so the record outlives a worktree."""
    marker = "/Deception-Circuit/"
    if marker not in path:
        return path
    rest = path.split(marker, 1)[1]
    if rest.startswith(".claude/worktrees/"):
        rest = rest.split("/", 3)[3]
    return rest


def f_point(C, K, T):
    c = C.mean()
    return float((c - K.mean()) / (c - T.mean()))


def clustered(C, K, T, subjects, seed):
    labels = sorted(set(subjects))
    index = {s: i for i, s in enumerate(labels)}
    codes = np.array([index[s] for s in subjects], dtype=np.int64)
    k = len(labels)
    num = np.bincount(codes, weights=C - K, minlength=k)
    den = np.bincount(codes, weights=C - T, minlength=k)
    draws = np.random.default_rng(seed).integers(0, k, size=(N_BOOT, k))
    counts = np.zeros((N_BOOT, k))
    np.add.at(counts, (np.repeat(np.arange(N_BOOT), k), draws.ravel()), 1.0)
    vals = (counts @ num) / (counts @ den)
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return k, float(lo), float(hi)


def item_boot(C, K, T, seed=0):
    idx = np.random.default_rng(seed).integers(0, len(C), (N_BOOT, len(C)))
    c = C[idx].mean(1)
    vals = (c - K[idx].mean(1)) / (c - T[idx].mean(1))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def main(margins_path, items_path, results_path, out_path):
    run = json.load(open(margins_path))
    m = run["margins"]
    items = {it["id"]: it for it in json.load(open(items_path))["items"]}
    results = json.load(open(results_path))
    kept_rows = list(m["kept_rows"])
    subjects = [items[m["ids"][r]]["subject"] for r in kept_rows]
    p2 = m["pass2"]
    C = np.asarray(p2["clean"], dtype=np.float64)
    T = np.asarray(p2["twin"], dtype=np.float64)
    out = {
        "inputs": {repo_relative(p): sha256(p) for p in (margins_path, items_path, results_path)},
        "n_items": len(m["ids"]), "n_kept": len(kept_rows), "n_subjects": len(set(subjects)),
        "n_boot": N_BOOT, "cluster": "MMLU subject of each kept item", "arms": {},
    }
    for arm in ARMS:
        K = np.asarray(p2["arms"][arm], dtype=np.float64)
        stored = results["f"][arm]
        rec = {"f": f_point(C, K, T), "stored_f": stored["f"], "stored_item_ci": stored["ci"],
               "item_ci_seed0": item_boot(C, K, T), "subject_clustered": {}}
        for seed in SEEDS:
            k, lo, hi = clustered(C, K, T, subjects, seed)
            rec["subject_clustered"][str(seed)] = [round(lo, 6), round(hi, 6)]
        out["arms"][arm] = rec
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    for arm, rec in out["arms"].items():
        print(f"{arm}: f {rec['f']:.4f} (stored {rec['stored_f']:.4f}); item CI seed 0 "
              f"{rec['item_ci_seed0'][0]:.4f} to {rec['item_ci_seed0'][1]:.4f} (stored "
              f"{rec['stored_item_ci'][0]:.4f} to {rec['stored_item_ci'][1]:.4f})")
        for seed, (lo, hi) in rec["subject_clustered"].items():
            print(f"  subject-clustered seed {seed}: {lo:.3f} to {hi:.3f}")
    print(f"kept {out['n_kept']} of {out['n_items']}, {out['n_subjects']} subjects")


if __name__ == "__main__":
    main(*sys.argv[1:5])
