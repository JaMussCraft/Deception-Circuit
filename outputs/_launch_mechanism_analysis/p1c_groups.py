#!/usr/bin/env python3
"""
p1c_groups.py -- the phase-1C wave-b groups files, paired R-inv ids and job file (ticket 03; spec 2.3, 2.4, 4; R11,
R16, R19(3)).

Reads, per task, 1B's S2p sweep (the signed ranking; sweep.json `signed_rank`, as the greedy pool does) and 1C-a's
greedy.json, both fetched to Delta, and writes under docs/research/mechanism-analysis/phase1/groups/:

    <t>_heldout_D.json   every candidate S_k of both selectors; 20 layer-matched null draws per candidate; the
                         routing groups (a) all 32 MLPs, (b) heads outside C_t, (c) every Component outside C_t, per
                         candidate's preliminary C_t; the named groups core, excl_t, (D_t - H_t) - core
    <t>_heldout_HF.json  every S_k with k <= 20 of both selectors, plus the named groups (item-swap on H and F)
    <t>_rinv.json        every S_k with k <= 20 of both selectors (neutral twin, post-clause, on D and on I)
    <t>_rinv_ids.txt     the ids the paired R-inv lines run on (R23): option B's ids (I's own held-out sample, seed 1,
                         the selection ids excluded; D on the same ids) followed by the R19(3) robustness ids (D's
                         held-out ids that survive I's filter) not already listed
    <t>_rinv_ids_optionB.txt, <t>_rinv_ids_r19.txt   the two id sets, read back separately
    <t>_heldout_D_sample.json, <t>_heldout_I_sample.json   the seed-1 samples the id sets came from
    meta.json            selectors, k grids, the null RNG seed, C_t rule, sizes, sources (sha256)

and docs/research/mechanism-analysis/jobs/03-p1c-b.batch (held-out D, H, F; paired D and I; one model load).

Selectors (spec 2.3): single = top k of the S2p signed ranking, layer-0 MLP excluded, k in {1,2,3,5,10,20,40,80};
greedy = the greedy prefix of size k, k in {1,2,3,5,10,20}. Null: 20 random k-sets from the 1,055 Components (layer-0
MLP excluded) with the same number of heads and MLPs per layer as S_k (an MLP member forces that layer's MLP: one
block per layer). C_t (spec 4, phase 3) = core | excl_t | ((D_t - H_t) - core) | the heads of S_k | 10 MLP blocks
(S_k's MLPs first, then by S2p rank; layer-0 MLP never).

usage (from the repository root, after 1B and 1C-a are fetched):
    python outputs/_launch_mechanism_analysis/p1c_groups.py --heldout-root DIR_D --rinv-sample-root DIR_I
        (DIR_D holds the held-out D sample and DIR_I I's own held-out sample, each <DIR>/U__leaf/<t>_v2/sample.json,
         from a login dry-run: seed 1, the S1 selection ids excluded)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

N_LAYERS, N_HEADS = 32, 32
ALL = [("head", l, h) for l in range(N_LAYERS) for h in range(N_HEADS)] + [("mlp", l, 0) for l in range(N_LAYERS)]
POSITIVE_CONTROL = ("mlp", 0, 0)
SINGLE_KS = (1, 2, 3, 5, 10, 20, 40, 80)
GREEDY_KS = (1, 2, 3, 5, 10, 20)
N_NULL = 20
NULL_SEED = 20261025
MAX_MLPS = 10


# ------------------------------------------------------------------ pure rules

def single_sets(ranking, ks=SINGLE_KS):
    """{k: top k of the signed ranking}, the positive control skipped."""
    r = [k for k in ranking if k != POSITIVE_CONTROL]
    return {k: r[:k] for k in ks if k <= len(r)}


def u_only_sets(ranking, U, ks=SINGLE_KS):
    """R24 (descriptive arm): {k: top k of the signed ranking among U's heads only}."""
    r = [k for k in ranking if k in U]
    return {k: r[:k] for k in ks if k <= len(r)}


def greedy_sets(steps, ks=GREEDY_KS):
    """{k: the first k greedy additions} for every k the greedy run reached."""
    return {k: list(steps[:k]) for k in ks if k <= len(steps)}


def layer_matched_nulls(S, n=N_NULL, seed=NULL_SEED):
    """n random sets with S's (kind, layer) counts, drawn without replacement within each (kind, layer)."""
    rng = random.Random(seed)
    need = {}
    for kind, layer, _ in S:
        need[(kind, layer)] = need.get((kind, layer), 0) + 1
    pools = {(kind, layer): [k for k in ALL if k[0] == kind and k[1] == layer and k != POSITIVE_CONTROL]
             for kind, layer in need}
    out = []
    for _ in range(n):
        draw = []
        for key in sorted(need):
            draw += rng.sample(pools[key], need[key])
        out.append(draw)
    return out


def grid_circuit(named_heads, S, ranking, max_mlps=MAX_MLPS):
    """Preliminary C_t: the named head sets, S's heads, then MLPs: S's first, then by S2p rank, to max_mlps."""
    C = set(named_heads) | {k for k in S if k[0] == "head"}
    mlps = [k for k in S if k[0] == "mlp" and k != POSITIVE_CONTROL]
    for k in ranking:
        if len(mlps) >= max_mlps:
            break
        if k[0] == "mlp" and k != POSITIVE_CONTROL and k not in mlps:
            mlps.append(k)
    return sorted(C | set(mlps[:max_mlps]))


def routing_groups(C):
    C = set(C)
    a = [k for k in ALL if k[0] == "mlp"]
    b = [k for k in ALL if k[0] == "head" and k not in C]
    c = [k for k in ALL if k not in C]
    return a, b, c


def to_json(groups: dict) -> dict:
    return {name: [[k[0], int(k[1]), int(k[2])] for k in members] for name, members in groups.items()}


# ------------------------------------------------------------------ inputs

def _key(label):
    kind, layer, index = label.split(".")
    return (kind, int(layer), int(index))


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def signed_ranking(sweep_path):
    with open(sweep_path) as f:
        comps = json.load(f)["components"]
    return [tuple(c["key"]) if isinstance(c["key"], list) else _key(c["label"])
            for c in sorted(comps, key=lambda c: c["signed_rank"])]


def greedy_steps(greedy_path):
    with open(greedy_path) as f:
        return [_key(s["added"]) for s in json.load(f)["steps"]]


def named_sets(t):
    import ma_cells as mc
    S = mc._head_sets(mc.REPO)
    core = S["D_far"] & S["D_sdr"] & S["D_ser"]
    u, v = [x for x in ("far", "sdr", "ser") if x != t]
    as_keys = lambda hs: sorted(("head", l, h) for l, h in hs)          # noqa: E731
    return {"core": as_keys(core), f"excl_{t}": as_keys(S[f"D_{t}"] - S[f"D_{u}"] - S[f"D_{v}"]),
            f"DmH_minus_core_{t}": as_keys((S[f"D_{t}"] - S[f"H_{t}"]) - core)}


# ------------------------------------------------------------------ build

def u_heads():
    """U's 123 heads as (head, layer, index) keys: the union of the six coarse v2 circuits' heads."""
    import ma_cells as mc
    return {("head", l, h) for hs in mc._head_sets(mc.REPO).values() for l, h in hs}


def build_task(t, ranking, steps, U=None):
    named = named_sets(t)
    named_heads = set().union(*map(set, named.values()))
    cands = {f"single_k{k}": s for k, s in single_sets(ranking).items()}
    cands.update({f"greedy_k{k}": s for k, s in greedy_sets(steps).items()})
    uonly = {f"uonly_k{k}": s for k, s in u_only_sets(ranking, U).items()} if U else {}
    D, HF, RINV, meta = {}, {}, {}, {"candidates": {}}
    for i, (name, S) in enumerate(list(cands.items()) + list(uonly.items())):
        D[name] = S
        for j, draw in enumerate(layer_matched_nulls(S, seed=NULL_SEED + 1000 * i)):
            D[f"null_{name}_d{j:02d}"] = draw
        if name.startswith("uonly_"):
            # R24: descriptive arm only -- held-out D with its nulls, and H/F for k <= 20; no routing, no R-inv.
            if len(S) <= 20:
                HF[name] = S
            meta["candidates"][name] = {"k": len(S), "members": [".".join(map(str, x)) for x in S],
                                        "null_seed": NULL_SEED + 1000 * i, "arm": "uonly (R24, descriptive)"}
            continue
        C = grid_circuit(named_heads, S, ranking)
        _, b, c = routing_groups(C)
        D[f"route_b_{name}"] = b
        D[f"route_c_{name}"] = c
        k = len(S)
        if k <= 20:
            HF[name] = S
            RINV[name] = S
        meta["candidates"][name] = {"k": k, "members": [".".join(map(str, x)) for x in S],
                                    "null_seed": NULL_SEED + 1000 * i, "C_t_size": len(C),
                                    "C_t_mlps": [".".join(map(str, x)) for x in C if x[0] == "mlp"]}
    D["route_a_all_mlps"] = routing_groups(set())[0]
    for name, members in named.items():
        D[f"named_{name}"] = members
        HF[f"named_{name}"] = members
    meta["named"] = {n: len(m) for n, m in named.items()}
    meta["n_groups"] = {"heldout_D": len(D), "heldout_HF": len(HF), "rinv": len(RINV)}
    return D, HF, RINV, meta


def paired_ids(heldout_sample, inversion_ds):
    from datasets import load_from_disk
    with open(heldout_sample) as f:
        held = json.load(f)["instance_ids"]
    kept = set(load_from_disk(inversion_ds)["test"]["instance_id"])
    return [i for i in held if i in kept]


STRATA = ("designation_polarity", "item_polarity", "template_variant")


def paired_strata(ids, rows_by_id):
    """The sampler-strata mix of the paired R-inv ids, and their inversion-polarity subset (in id order).

    FAR's I keeps mostly inversion-polarity rows, so its pooled R-inv is polarity-confounded; the reading adds a
    within-stratum comparison on this subset (orchestrator ruling with 8bf0109).
    """
    from collections import Counter
    rows = [rows_by_id[i] for i in ids]
    out = {"n": len(rows)}
    for key in STRATA:
        out[key] = dict(Counter(str(r[key]) for r in rows))
    out["inversion_polarity_ids"] = [i for i in ids if rows_by_id[i]["designation_polarity"] == "inversion"]
    return out


def rinv_union(ids_b, ids_r19):
    """Option B's ids in order, then the R19(3) ids not already among them (R23: one paired run serves both)."""
    seen = set(ids_b)
    return list(ids_b) + [i for i in ids_r19 if i not in seen]


def batch_b(out_root, groups_dir):
    import p1b_jobs as pb
    import p1c_jobs as pc
    post = ["--knockout-counterfactual", "neutral_twin", "--knockout-positions", pb.POST]
    head = ["# Ticket 03 phase 1C wave b: held-out tests (seed 1, the 1B selection sample excluded) and the paired "
            "R-inv runs, U bound, one model load.",
            "# Generated by outputs/_launch_mechanism_analysis/p1c_groups.py from 1B's S2p sweep and 1C-a's greedy.json.",
            f"# Run: python analyze_components.py batch <this file> --timings {out_root}/timings/1c-b.json", ""]
    lines = []
    for t, (d, h) in pb.RUNS.items():
        sel = f"{out_root}/s1/U__leaf/{t}_v2/sample.json"
        f = pb.STANDIN_F.format(t=t)
        i = pc.STANDIN_I.format(t=t)
        held = ["--seed", "1", "--exclude-ids", sel, "--analyses", "knockout", "--knockout-singles", "off"]
        ids = f"{groups_dir}/{t}_rinv_ids.txt"
        cells = [
            ("heldout_D", ["--task-from", d] + held + post + ["--knockout-groups", f"{groups_dir}/{t}_heldout_D.json",
                                                              "--output-dir", f"{out_root}/heldout_d"]),
            ("heldout_H", ["--task-from", h] + held + ["--knockout-groups", f"{groups_dir}/{t}_heldout_HF.json",
                                                       "--output-dir", f"{out_root}/heldout_h"]),
            ("heldout_F", ["--task-from", f] + held + ["--knockout-groups", f"{groups_dir}/{t}_heldout_HF.json",
                                                       "--output-dir", f"{out_root}/heldout_f"]),
            ("rinv_D", ["--task-from", d, "--include-ids", ids, "--n-causal", "1000", "--analyses", "knockout",
                        "--knockout-singles", "off"]
             + post + ["--knockout-groups", f"{groups_dir}/{t}_rinv.json", "--output-dir", f"{out_root}/rinv_d"]),
            ("rinv_I", ["--task-from", i, "--include-ids", ids, "--n-causal", "1000", "--analyses", "knockout",
                        "--knockout-singles", "off"]
             + post + ["--knockout-groups", f"{groups_dir}/{t}_rinv.json", "--output-dir", f"{out_root}/rinv_i"]),
        ]
        for name, argv in cells:
            lines += [f"# {t} {name}", shlex.join(pb.binding() + argv)]
    return "\n".join(head + lines) + "\n"


def main(argv=None) -> int:
    import p1b_jobs as pb
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=os.path.join(pb.REPO, pb.OUT_ROOT), help="fetched 1B/1C-a cells (Delta)")
    p.add_argument("--heldout-root", required=True, help="a held-out D sample: <DIR>/U__leaf/<t>_v2/sample.json")
    p.add_argument("--rinv-sample-root", required=True,
                   help="I's own held-out sample (R23 option B; seed 1, selection ids excluded): "
                        "<DIR>/U__leaf/<t>_v2/sample.json")
    p.add_argument("--groups-dir", default="docs/research/mechanism-analysis/phase1/groups")
    p.add_argument("--jobs-dir", default=os.path.join(pb.REPO, pb.JOBS_DIR))
    p.add_argument("--out-root", default=pb.OUT_ROOT, help="cell output root written into the batch lines")
    a = p.parse_args(argv)
    gdir = os.path.join(pb.REPO, a.groups_dir)
    os.makedirs(gdir, exist_ok=True)
    meta = {"null_seed_base": NULL_SEED, "single_ks": SINGLE_KS, "greedy_ks": GREEDY_KS, "n_null": N_NULL,
            "max_mlps": MAX_MLPS, "ranking": "sweep.json signed_rank of 1B S2p, layer-0 MLP excluded", "tasks": {}}
    U = u_heads()
    meta["uonly_arm"] = {"ruling": "R24", "U_heads": len(U), "ks": SINGLE_KS,
                         "rule": "single selector restricted to U's heads; descriptive, outside the R-AB reading"}
    for t in pb.RUNS:
        s2p = os.path.join(a.root, "s2p", "U__leaf", f"{t}_v2", "knockout", "sweep.json")
        greedy = os.path.join(a.root, "greedy", "U__leaf", f"{t}_v2", "knockout", "greedy.json")
        D, HF, RINV, m = build_task(t, signed_ranking(s2p), greedy_steps(greedy), U=U)
        for name, groups in (("heldout_D", D), ("heldout_HF", HF), ("rinv", RINV)):
            with open(os.path.join(gdir, f"{t}_{name}.json"), "w") as f:
                json.dump(to_json(groups), f)
        inv_ds = os.path.join(pb.REPO, "data", "datasets", f"{t}_v2_inversion")
        d_sample = os.path.join(a.heldout_root, "U__leaf", f"{t}_v2", "sample.json")
        i_sample = os.path.join(a.rinv_sample_root, "U__leaf", f"{t}_v2", "sample.json")
        ids_b, ids_r19 = paired_ids(i_sample, inv_ds), paired_ids(d_sample, inv_ds)
        ids = rinv_union(ids_b, ids_r19)
        for suffix, xs in (("", ids), ("_optionB", ids_b), ("_r19", ids_r19)):
            with open(os.path.join(gdir, f"{t}_rinv_ids{suffix}.txt"), "w") as f:
                f.write("\n".join(xs) + "\n")
        for name, src in (("D", d_sample), ("I", i_sample)):
            with open(src) as fi, open(os.path.join(gdir, f"{t}_heldout_{name}_sample.json"), "w") as fo:
                fo.write(fi.read())
        from datasets import load_from_disk
        inv_rows = {r["instance_id"]: r for r in load_from_disk(inv_ds)["test"]}
        strata_b, strata_r19 = paired_strata(ids_b, inv_rows), paired_strata(ids_r19, inv_rows)
        m.update({"sources": {"s2p": {"path": s2p, "sha256": _sha(s2p)}, "greedy": {"path": greedy,
                                                                                   "sha256": _sha(greedy)}},
                  "rinv_rule": ("R23: option B (I's own held-out sample, seed 1, the selection ids excluded; D on the "
                                "same ids) primary; R19(3) subset (D's held-out ids surviving I's filter) as a "
                                "robustness row; one paired run on their union"),
                  "rinv_seed": 1, "rinv_union_ids": len(ids), "rinv_paired_ids": len(ids_b),
                  "rinv_paired_strata": strata_b,
                  "rinv_sets": {"optionB": {"file": f"{t}_rinv_ids_optionB.txt", "sample": f"{t}_heldout_I_sample.json",
                                            **strata_b},
                                "r19": {"file": f"{t}_rinv_ids_r19.txt", "sample": f"{t}_heldout_D_sample.json",
                                        **strata_r19}}})
        meta["tasks"][t] = m
        print(t, m["n_groups"], "R-inv ids: option B", len(ids_b), "R19(3)", len(ids_r19), "union", len(ids))
    with open(os.path.join(gdir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    path = os.path.join(a.jobs_dir, "03-p1c-b.batch")
    with open(path, "w") as f:
        f.write(batch_b(a.out_root, a.groups_dir))
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
