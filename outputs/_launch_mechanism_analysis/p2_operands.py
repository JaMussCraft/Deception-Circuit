#!/usr/bin/env python3
"""
p2_operands.py -- the phase-2 operand per task (ticket 04; spec section 4 phase 2, R26).

Phase 2 analyses U' = U | the heads of the task's deciding S_k | the proposed C_t MLP blocks, where U is the
123-head union of the six coarse v2 circuits minus the all-MLP operand m, at leaf. No circuit expression can name
single heads or MLP blocks, so each task gets an operand run dir in the recipe of
outputs/_launch_format_control/build_allmlp.py (the m operand): the far D run's mask keys, with the deciding set's
heads open at every neuron, the C_t MLP blocks open at every unit (the set's own MLPs are among them), and every
other gate closed. Composed at leaf, `((Df|Hf|Ds|Hs|De|He)-m) | X_t` is then U's heads plus X_t's heads and MLP
blocks, nothing else (tests/test_mechanism_analysis_p2.py). Operands must share mask keys
(evaluation/algebra._operand_keys), which is why the operand carries the full vectors.

    operands/skct_<t>/active_nodes.json, config.json, provenance.json

The deciding sets and C_t MLPs come from docs/research/mechanism-analysis/phase1/p1c_readings.json (ticket 03's
reading; far and ser greedy k = 20, sdr single k = 20 descriptive, R26).

usage (from the repository root):
    python outputs/_launch_mechanism_analysis/p2_operands.py [--readings FILE] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

READINGS = "docs/research/mechanism-analysis/phase1/p1c_readings.json"
OPERANDS_DIR = "outputs/_launch_mechanism_analysis/operands"
BASE_RUN = "outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717"
TASKS = ("far", "sdr", "ser")
NOTE = ("phase-2 operand X_t of the mechanism-analysis feature (ticket 04, R26): the heads of the task's deciding "
        "S_k and the proposed C_t MLP blocks, every leaf open; not a trained circuit. U' = ((Df|Hf|Ds|Hs|De|He)-m)|X_t "
        "at leaf. Built by p2_operands.py from p1c_readings.json; see provenance.json.")


def parse_label(label: str) -> tuple:
    kind, layer, index = label.split(".")
    return (kind, int(layer), int(index))


def label_of(key) -> str:
    return f"{key[0]}.{key[1]}.{key[2]}"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ pure rules

def operand_masks(base: dict, *, heads, mlp_layers, num_heads: int, head_dim: int) -> dict:
    """A mask object with `base`'s keys: the named heads and MLP layers open at every leaf, all else closed."""
    heads = [(str(k), int(l), int(i)) for k, l, i in heads]
    head_layers = {l for _k, l, _i in heads}
    mlp_layers = sorted(int(l) for l in mlp_layers)
    out = {}
    for key, value in base.items():
        if isinstance(value, dict):
            layers = sorted(value, key=int)
            size = {l: int(np.asarray(value[l]).size) for l in layers}
            if key == "attention_heads":
                out[key] = {l: np.zeros(size[l], dtype=np.uint8) for l in layers}
                for _k, l, i in heads:
                    out[key][str(l)][i] = 1
            elif key == "attention_neurons":
                out[key] = {l: np.zeros(size[l], dtype=np.uint8) for l in layers}
                for _k, l, i in heads:
                    out[key][str(l)][i * head_dim:(i + 1) * head_dim] = 1
            elif key in ("mlp_hidden", "mlp_output"):
                out[key] = {l: (np.ones if int(l) in mlp_layers else np.zeros)(size[l], dtype=np.uint8)
                            for l in layers}
            else:
                out[key] = {l: np.zeros(size[l], dtype=np.uint8) for l in layers}
        else:
            n = int(np.asarray(value).size)
            vec = np.zeros(n, dtype=np.uint8)
            if key == "attention_blocks":
                for l in head_layers:
                    vec[l] = 1
            elif key == "mlp_blocks":
                for l in mlp_layers:
                    vec[l] = 1
            elif key == "layers":
                for l in head_layers | set(mlp_layers):
                    vec[l] = 1
            out[key] = vec
    return out


def _jsonable(masks: dict) -> dict:
    return {k: ({l: np.asarray(a).astype(int).tolist() for l, a in v.items()} if isinstance(v, dict)
                else np.asarray(v).astype(int).tolist()) for k, v in masks.items()}


def build_operand(run_dir: str, out_dir: str, *, heads, mlp_layers, num_heads: int, head_dim: int,
                  provenance: dict) -> str:
    """Write the operand run dir (active_nodes.json, config.json, provenance.json) and return its path."""
    from evaluation.masks import load_circuit_masks, validate_hierarchy
    base = load_circuit_masks(run_dir)
    masks = operand_masks(base, heads=heads, mlp_layers=mlp_layers, num_heads=num_heads, head_dim=head_dim)
    validate_hierarchy(masks, num_heads=num_heads, head_dim=head_dim, label="phase-2 operand")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "active_nodes.json"), "w") as f:
        json.dump({"masks": _jsonable(masks), "built_from": os.path.relpath(run_dir, REPO)
                   if os.path.isabs(run_dir) else run_dir}, f)
    with open(os.path.join(run_dir, "config.json")) as f:
        config = json.load(f)
    config["operand"] = NOTE
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=1)
    prov = dict(provenance)
    prov["heads"] = [label_of(k) for k in heads]
    prov["mlp_layers"] = sorted(int(l) for l in mlp_layers)
    with open(os.path.join(out_dir, "provenance.json"), "w") as f:
        json.dump(prov, f, indent=1)
    return out_dir


def deciding_sets(readings: dict) -> dict:
    """{task: {candidate, selector, k, heads, mlps, ct_mlp_layers, members}} from p1c_readings.json.

    The set's own MLP blocks must be among the C_t blocks (spec section 4 phase 3: the deciding set's MLPs first),
    otherwise the operand would not hold the whole deciding set; refused by name.
    """
    out = {}
    for t, rab in readings["rab"].items():
        numbers = rab["deciding_numbers"]
        members = [parse_label(m) for m in numbers["members"]]
        routing = readings["routing"][t]
        if routing.get("candidate") not in (None, rab["deciding"]):
            raise ValueError(f"{t}: routing C_t is for {routing['candidate']!r}, the deciding set is {rab['deciding']!r}")
        ct = [parse_label(m) for m in routing["C_t_mlps"]]
        ct_layers = sorted(l for _k, l, _i in ct)
        mlps = [k for k in members if k[0] == "mlp"]
        missing = [label_of(k) for k in mlps if k[1] not in ct_layers]
        if missing:
            raise ValueError(f"{t}: deciding-set MLP(s) {missing} are not among C_t's MLP blocks {ct_layers}")
        out[t] = {"candidate": rab["deciding"], "selector": numbers["selector"], "k": numbers["k"],
                  "reading": rab["reading"], "members": [label_of(k) for k in members],
                  "heads": [k for k in members if k[0] == "head"], "mlps": mlps, "ct_mlp_layers": ct_layers}
    return out


# ------------------------------------------------------------------ CLI

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--readings", default=os.path.join(REPO, READINGS))
    p.add_argument("--base-run", default=os.path.join(REPO, BASE_RUN))
    p.add_argument("--out-dir", default=os.path.join(REPO, OPERANDS_DIR))
    a = p.parse_args(argv)
    with open(a.readings) as f:
        readings = json.load(f)
    sets = deciding_sets(readings)
    from evaluation.context import geometry_from_masks
    from evaluation.masks import load_circuit_masks
    geom = geometry_from_masks(load_circuit_masks(a.base_run))
    for t in TASKS:
        s = sets[t]
        prov = {"task": t, "candidate": s["candidate"], "selector": s["selector"], "k": s["k"], "reading": s["reading"],
                "members": s["members"], "readings_file": os.path.relpath(a.readings, REPO),
                "readings_sha256": _sha256(a.readings), "base_run": os.path.relpath(a.base_run, REPO),
                "rule": "R26: U' = U | heads of the deciding S_k | the proposed C_t MLP blocks (<= 10)"}
        out = build_operand(a.base_run, os.path.join(a.out_dir, f"skct_{t}"), heads=s["heads"],
                            mlp_layers=s["ct_mlp_layers"], num_heads=geom["num_heads"], head_dim=geom["head_dim"],
                            provenance=prov)
        print(out, len(s["heads"]), "heads", s["ct_mlp_layers"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
