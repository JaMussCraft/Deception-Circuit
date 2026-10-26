#!/usr/bin/env python3
"""
p3_jobs.py -- the phase-3 job files of the mechanism-analysis feature (ticket 05; spec section 4 phase 3, R25 A, R28).

Per task t the grid circuit is the candidate set of spec section 4 phase 3 as ticket 04 proposed it (R28):

    C_t = core | excl_t | ((D_t - H_t) - core) | the heads of the deciding S_k | 10 MLP blocks

bound at leaf as `Ct=(((Df&Ds&De)|(D_t-D_o1-D_o2)|((D_t-H_t)-(Df&Ds&De)))-m)|X` with X = the per-task operand
`outputs/_launch_mechanism_analysis/operands/skct_<t>` (p2_operands.py: the deciding S_k's heads and the C_t MLP
blocks, every unit open). It writes:

    docs/research/mechanism-analysis/jobs/05-p3-<t>.batch   two lines, one model load: the two counterfactuals of
                                                            `--path-counterfactual both` (R25 B, R28) as two lines,
                                                            the Neutral-Clause Twin FIRST into cell `d` (its Segment
                                                            pass at 0.01, R25 A, the receiver category's floor; the
                                                            categories; the completeness sweep, which a twin-only line
                                                            runs under the twin), then the item swap into cell `d_is`
                                                            (Segment pass at the default 0.05)
    docs/research/mechanism-analysis/phase3/ct.json         C_t per task: members by composition set, sizes, sources,
                                                            and the check that C_t is the phase-1C routing check's C_t
                                                            (every Component outside C_t = the route_c group), so
                                                            phase 1C's routing shares apply to this grid unchanged

Why two lines and not one `both` line: `both` runs the item swap first and the twin second, and the head table is
written when an invocation ends; a job killed on the wall clock in the twin's Segment pass (whose selected share at
0.01 is the one cost unknown, ticket 02b) would lose the twin split, the receiver categories, the twin sweep and every
head-table column. Twin first, in its own cell, keeps the A' adjudication's inputs safe; the item-swap cell is merged
into the roles pass (`--roles-merge-from`). The forwards are the same. Two cells are needed because a second
path-patching run into one cell replaces the whole `path_patching.` namespace (`analyze_components.carry_forward`).

The causal sample is the default (n = 100, seed 0): the selection sample, the phase-2 D cell's and the S2p weights'.
The six atomic runs and X_t are bound as references so the head table carries the membership columns.

usage (from the repository root):
    python outputs/_launch_mechanism_analysis/p3_jobs.py [--out-root DIR] [--jobs-dir DIR] [--phase3-dir DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p1b_jobs  # noqa: E402

RUNS, SHORT, ALLMLP = p1b_jobs.RUNS, p1b_jobs.SHORT, p1b_jobs.ALLMLP
TASKS = ("far", "sdr", "ser")
OPERAND = "outputs/_launch_mechanism_analysis/operands/skct_{t}"
OUT_ROOT = "outputs/_analyses/mechanism-analysis-p3"
CELL = "d"
CELL_ITEM_SWAP = "d_is"
JOBS_DIR = "docs/research/mechanism-analysis/jobs"
PHASE3_DIR = "docs/research/mechanism-analysis/phase3"
P1_GROUPS = "docs/research/mechanism-analysis/phase1/groups/{t}_heldout_D.json"
P1C_READINGS = "docs/research/mechanism-analysis/phase1/p1c_readings.json"
#: R25 A: the twin's Segment pass at the receiver category's floor; the item swap keeps the default 0.05.
TWIN_POSITION_THRESHOLD = "0.01"
N_LAYERS, N_HEADS = 32, 32


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ pure rules

def expr(t: str) -> str:
    """C_t at leaf: core | excl_t | ((D_t - H_t) - core), MLPs stripped by `- m`, then X_t (S_k heads + C_t MLPs)."""
    s = SHORT[t]
    o1, o2 = [SHORT[u] for u in TASKS if u != t]
    return f"Ct=(((Df&Ds&De)|(D{s}-D{o1}-D{o2})|((D{s}-H{s})-(Df&Ds&De)))-m)|X"


def binding(t: str) -> list:
    out = []
    for u, (d, h) in RUNS.items():
        out += ["--circuit", f"D{SHORT[u]}={d}", "--circuit", f"H{SHORT[u]}={h}"]
    out += ["--circuit", f"m={ALLMLP}", "--circuit", f"X={OPERAND.format(t=t)}", "--expr", expr(t),
            "--compose-granularity", "leaf"]
    for u, (d, h) in RUNS.items():
        out += ["--reference", f"{u}_D={d}", "--reference", f"{u}_H={h}"]
    out += ["--reference", f"x_{t}={OPERAND.format(t=t)}"]
    return out


def analyses(counterfactual: str, out_root: str = OUT_ROOT) -> list:
    """The twin: Segment pass at the floor, then the categories, then the sweep (under the twin, the one selected
    pair). The item swap: the default Segment threshold, no sweep."""
    if counterfactual == "neutral_twin":
        return ["--analyses", "path_patching", "--path-counterfactual", "neutral_twin",
                "--path-twin-position-threshold", TWIN_POSITION_THRESHOLD, "--path-completeness-sweep",
                "--output-dir", f"{out_root}/{CELL}"]
    if counterfactual == "item_swap":
        return ["--analyses", "path_patching", "--path-counterfactual", "item_swap",
                "--output-dir", f"{out_root}/{CELL_ITEM_SWAP}"]
    raise ValueError(counterfactual)


#: Run order inside the job: the twin first (see the module docstring).
ORDER = (("neutral_twin", CELL), ("item_swap", CELL_ITEM_SWAP))


def line(t: str, counterfactual: str, out_root: str = OUT_ROOT) -> list:
    return binding(t) + ["--task-from", RUNS[t][0]] + analyses(counterfactual, out_root)


def batch_text(t: str, out_root: str = OUT_ROOT) -> str:
    head = [f"# Ticket 05 phase 3, task {t}: path patching on the candidate circuit C_t (spec section 4 phase 3, R28),",
            "# the two counterfactuals of --path-counterfactual both as two lines, the Neutral-Clause Twin first (its",
            "# Segment pass at 0.01, R25 A; categories; the completeness sweep under the twin), then the item swap.",
            "# One model load. The causal sample is the default (n = 100, seed 0).",
            "# Generated by outputs/_launch_mechanism_analysis/p3_jobs.py; do not edit by hand.",
            "# Run from the repo root:  python analyze_components.py batch <this file> "
            f"--timings {out_root}/timings/{t}.json",
            "# Login check:            python analyze_components.py batch <this file> --dry-run", ""]
    body = []
    for counterfactual, cell in ORDER:
        body += [f"# {cell}: C_t on {t}_v2 D, {counterfactual}", shlex.join(line(t, counterfactual, out_root))]
    return "\n".join(head + body) + "\n"


def label(kind: str, layer: int, index: int) -> str:
    return f"{kind}.{int(layer)}.{int(index)}"


def ct_sets(t: str, sets: dict, operand: dict) -> dict:
    """{name: {labels}} of C_t's parts from the six circuits' head sets and the operand's provenance."""
    o1, o2 = [u for u in TASKS if u != t]
    core = sets["D_far"] & sets["D_sdr"] & sets["D_ser"]
    D, H = sets[f"D_{t}"], sets[f"H_{t}"]
    parts = {"core": core, "excl": D - sets[f"D_{o1}"] - sets[f"D_{o2}"], "DmH_minus_core": (D - H) - core}
    out = {name: {label("head", l, h) for l, h in members} for name, members in parts.items()}
    out["S_k_heads"] = set(operand["heads"])
    out["S_k"] = set(operand["members"])
    out["mlps"] = {label("mlp", l, 0) for l in operand["mlp_layers"]}
    out["C_t"] = out["core"] | out["excl"] | out["DmH_minus_core"] | out["S_k_heads"] | out["mlps"]
    return out


def all_components(n_layers: int = N_LAYERS, n_heads: int = N_HEADS) -> set:
    return ({label("head", l, h) for l in range(n_layers) for h in range(n_heads)}
            | {label("mlp", l, 0) for l in range(n_layers)})


def routing_identity(ct: set, route_c: list, universe: set) -> dict:
    """Is C_t the complement of phase 1C's route_c group (every Component outside the preliminary C_t)?"""
    outside = {label(*one) for one in route_c}
    prelim = universe - outside
    return {"identical": prelim == ct, "n_ct": len(ct), "n_prelim": len(prelim),
            "only_in_ct": sorted(ct - prelim), "only_in_prelim": sorted(prelim - ct),
            "overlap_with_outside": sorted(ct & outside)}


# ------------------------------------------------------------------ main

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out-root", default=OUT_ROOT, help="cell output root written into the lines")
    p.add_argument("--jobs-dir", default=os.path.join(REPO, JOBS_DIR))
    p.add_argument("--phase3-dir", default=os.path.join(REPO, PHASE3_DIR))
    a = p.parse_args(argv)
    os.makedirs(a.jobs_dir, exist_ok=True)
    os.makedirs(a.phase3_dir, exist_ok=True)
    import ma_cells as mc
    sets = {k: set(v) for k, v in mc._head_sets(REPO).items()}
    readings = json.load(open(os.path.join(REPO, P1C_READINGS)))
    meta = {"rule": "C_t = core | excl_t | ((D_t - H_t) - core) | S_k heads | the operand's 10 MLP blocks (R28)",
            "sample": "the default causal sample: n = 100, seed 0 (the selection sample)",
            "twin_position_threshold": float(TWIN_POSITION_THRESHOLD), "tasks": {}, "sources": {}}
    for t in TASKS:
        op_dir = os.path.join(REPO, OPERAND.format(t=t))
        operand = json.load(open(os.path.join(op_dir, "provenance.json")))
        parts = ct_sets(t, sets, operand)
        groups_file = os.path.join(REPO, P1_GROUPS.format(t=t))
        route_c = json.load(open(groups_file))[f"route_c_{operand['candidate']}"]
        ident = routing_identity(parts["C_t"], route_c, all_components())
        if not ident["identical"]:
            raise SystemExit(f"{t}: C_t differs from phase 1C's preliminary C_t: {ident}")
        routing = readings["routing"][t]
        meta["tasks"][t] = {
            "candidate": operand["candidate"], "reading": operand.get("reading"),
            "sizes": {k: len(v) for k, v in parts.items()},
            "members": {k: sorted(v, key=lambda s: (s.split(".")[0], int(s.split(".")[1]), int(s.split(".")[2])))
                        for k, v in parts.items()},
            "routing_identity": ident,
            "routing_shares": {k: routing[k] for k in ("a_all_mlps", "b_heads_outside_C", "c_all_outside_C")},
            "expr": expr(t)}
        meta["sources"][os.path.relpath(groups_file, REPO)] = _sha256(groups_file)
        meta["sources"][os.path.relpath(os.path.join(op_dir, "provenance.json"), REPO)] = _sha256(
            os.path.join(op_dir, "provenance.json"))
        path = os.path.join(a.jobs_dir, f"05-p3-{t}.batch")
        with open(path, "w") as f:
            f.write(batch_text(t, a.out_root))
        print(path, meta["tasks"][t]["sizes"], "routing identical:", ident["identical"])
    meta["sources"][P1C_READINGS] = _sha256(os.path.join(REPO, P1C_READINGS))
    with open(os.path.join(a.phase3_dir, "ct.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
