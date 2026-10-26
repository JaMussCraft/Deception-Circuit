#!/usr/bin/env python3
"""
p2_jobs.py -- the phase-2 groups files and job files of the mechanism-analysis feature (ticket 04; spec section 4
phase 2, R16, R26).

Per task t it writes, under docs/research/mechanism-analysis/phase2/groups/:

    <t>_families.json   the composition sets as named groups (02a's JSON format): core, excl_t, D_t - H_t,
                        (D_t - H_t) - core, H_t - D_t and the late H-D heads (layers 18, 22, 30), read from the six
                        atomic circuits' head masks (an empty set is left out and recorded in meta.json)
    <t>_top20.json      the S2p signed top 20 (1B's sweep, the layer-0 MLP excluded) as 20 singleton groups plus
                        the joint set, for the segment-resolved neutral-twin knockout
    meta.json           sources (sha256), sizes, the Segment lists

and under docs/research/mechanism-analysis/jobs/ one `analyze_components.py batch` file per task, 04-p2-<t>.batch,
one model load each. Every line binds U' = ((Df|Hf|Ds|Hs|De|He)-m) | X_t at leaf (X_t = operands/skct_<t>,
p2_operands.py: the deciding S_k's heads and the C_t MLP blocks), the six atomic runs and X_t as references, and
writes its own cell dir under outputs/_analyses/mechanism-analysis-p2/<cell>/Up__leaf/<test set>/:

| cell      | test set | analyses                                                | knockout plan                      |
| d         | D        | attention (pressure, neutral twin paired), DLA (same), family knockout | item swap, all positions |
| d_twinko  | D        | family knockout                                         | neutral twin, post-clause          |
| h, f      | H, F     | attention (pressure), DLA (pressure), family knockout   | item swap, all (honest margin)     |
| i         | I        | attention (pressure, twin paired), DLA (same), family knockout | neutral twin, post-clause   |
| seg_<S>   | D        | top-20 singletons + joint                               | neutral twin, at Segment S only    |

The seg lines run every v2 Segment but `unsegmented`. The nine Segments before the clause are the zero-by-construction
sanity assertion (R16), never a finding; the informative ones are the clause, the post-clause question and response
line, the four Item Mentions in the question, the stem and the Readout.

usage (from the repository root, after 1B is fetched and p2_operands.py has run):
    python outputs/_launch_mechanism_analysis/p2_jobs.py [--p1-root DIR] [--out-root DIR]
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

import p1b_jobs  # noqa: E402  (RUNS, SHORT, ALLMLP, STANDIN_F, POST)

RUNS, SHORT, ALLMLP, STANDIN_F, POST = p1b_jobs.RUNS, p1b_jobs.SHORT, p1b_jobs.ALLMLP, p1b_jobs.STANDIN_F, p1b_jobs.POST
TASKS = ("far", "sdr", "ser")
STANDIN_I = "outputs/_launch_mechanism_analysis/standins/{t}_v2_inversion"
OPERAND = "outputs/_launch_mechanism_analysis/operands/skct_{t}"
EXPR = "Up=((Df|Hf|Ds|Hs|De|He)-m)|X"
P1_ROOT = "outputs/_analyses/mechanism-analysis-p1"
OUT_ROOT = "outputs/_analyses/mechanism-analysis-p2"
GROUPS_DIR = "docs/research/mechanism-analysis/phase2/groups"
JOBS_DIR = "docs/research/mechanism-analysis/jobs"
LATE_LAYERS = (18, 22, 30)
TOP = 20
POSITIVE_CONTROL = "mlp.0.0"

#: The v2 Segments the segment-resolved knockout runs, in prompt order; `unsegmented` is left out (the attention
#: sink is not a position the twin changes). Imported from the segmenter so the list cannot drift from it.
from component_analysis.segmentation import MECHANISM_V2_SEGMENTS, UNSEGMENTED  # noqa: E402

SEGMENTS = tuple(s for s in MECHANISM_V2_SEGMENTS if s != UNSEGMENTED)
PRE_CLAUSE = SEGMENTS[:SEGMENTS.index("pressure_clause")]
POST_CLAUSE = SEGMENTS[SEGMENTS.index("pressure_clause"):]


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ pure rules

def _keys(pairs) -> list:
    return [["head", int(l), int(h)] for l, h in sorted(pairs)]


def composition_sets(t: str, sets: dict) -> dict:
    """{name: {(layer, head)}} for one task from the six circuits' head sets {D_far, H_far, ...}."""
    others = [u for u in TASKS if u != t]
    D, H = sets[f"D_{t}"], sets[f"H_{t}"]
    core = sets["D_far"] & sets["D_sdr"] & sets["D_ser"]
    out = {"core": core,
           f"excl_{t}": D - sets[f"D_{others[0]}"] - sets[f"D_{others[1]}"],
           f"DmH_{t}": D - H,
           f"DmH_minus_core_{t}": (D - H) - core,
           f"HmD_{t}": H - D}
    out[f"late_HmD_{t}"] = {(l, h) for l, h in out[f"HmD_{t}"] if l in LATE_LAYERS}
    return out


def family_groups(t: str, sets: dict) -> dict:
    """The task's non-empty composition sets as a 02a-format groups object."""
    return {name: _keys(members) for name, members in composition_sets(t, sets).items() if members}


def empty_families(t: str, sets: dict) -> list:
    return [name for name, members in composition_sets(t, sets).items() if not members]


def top20_groups(sweep: dict, top: int = TOP, exclude=(POSITIVE_CONTROL,)) -> dict:
    """The S2p signed top `top` as singleton groups (named by label, in rank order) plus `top20_joint`."""
    excluded = set(exclude) | set(sweep.get("excluded_from_ranking") or [])
    rows = sorted((r for r in sweep["components"] if r["label"] not in excluded), key=lambda r: r["signed_rank"])
    rows = rows[:top]
    out = {r["label"]: [[r["kind"], int(r["layer"]), int(r["index"])]] for r in rows}
    out["top20_joint"] = [[r["kind"], int(r["layer"]), int(r["index"])] for r in rows]
    return out


# ------------------------------------------------------------------ the job files

def binding(t: str) -> list:
    """U' at leaf: the six atomic runs, m and X_t bound; the six runs and X_t as references."""
    out = []
    for u, (d, h) in RUNS.items():
        out += ["--circuit", f"D{SHORT[u]}={d}", "--circuit", f"H{SHORT[u]}={h}"]
    out += ["--circuit", f"m={ALLMLP}", "--circuit", f"X={OPERAND.format(t=t)}", "--expr", EXPR,
            "--compose-granularity", "leaf"]
    for u, (d, h) in RUNS.items():
        out += ["--reference", f"{u}_D={d}", "--reference", f"{u}_H={h}"]
    out += ["--reference", f"x_{t}={OPERAND.format(t=t)}"]
    return out


def cells(t: str, out_root: str = OUT_ROOT, groups_dir: str = GROUPS_DIR) -> list:
    """[(cell, argv)] for one task, in run order."""
    d, h = RUNS[t]
    f, i = STANDIN_F.format(t=t), STANDIN_I.format(t=t)
    fam = f"{groups_dir}/{t}_families.json"
    top = f"{groups_dir}/{t}_top20.json"
    desc = ["--analyses", "attention_patterns,dla,knockout", "--knockout-singles", "off"]
    twin = ["--attention-conditions", "pressure,neutral_twin", "--dla-conditions", "pressure,neutral_twin"]
    plain = ["--attention-conditions", "pressure", "--dla-conditions", "pressure"]
    twin_post = ["--knockout-counterfactual", "neutral_twin", "--knockout-positions", POST]

    def out(cell):
        return ["--output-dir", f"{out_root}/{cell}"]
    rows = [
        ("d", ["--task-from", d] + desc + twin + ["--knockout-groups", fam, "--attention-token-level"] + out("d")),
        ("d_twinko", ["--task-from", d, "--analyses", "knockout", "--knockout-singles", "off", "--knockout-groups", fam]
         + twin_post + out("d_twinko")),
        ("h", ["--task-from", h] + desc + plain + ["--knockout-groups", fam] + out("h")),
        ("f", ["--task-from", f] + desc + plain + ["--knockout-groups", fam] + out("f")),
        ("i", ["--task-from", i] + desc + twin + ["--knockout-groups", fam] + twin_post + out("i")),
    ]
    for seg in SEGMENTS:
        rows.append((f"seg_{seg}", ["--task-from", d, "--analyses", "knockout", "--knockout-singles", "off",
                                    "--knockout-groups", top, "--knockout-counterfactual", "neutral_twin",
                                    "--knockout-positions", seg] + out(f"seg_{seg}")))
    return rows


def batch_text(t: str, out_root: str = OUT_ROOT, groups_dir: str = GROUPS_DIR) -> str:
    head = [f"# Ticket 04 phase 2, task {t}: the four cells (D, H, F, I) on U' = U | S_k heads | C_t MLPs at leaf (R26),",
            "# the composition-set family knockouts and the segment-resolved neutral-twin knockout of the S2p top 20,",
            "# one model load. Generated by outputs/_launch_mechanism_analysis/p2_jobs.py; do not edit by hand.",
            "# Run from the repo root:  python analyze_components.py batch <this file> "
            f"--timings {out_root}/timings/{t}.json",
            "# Login check:            python analyze_components.py batch <this file> --dry-run", ""]
    lines = []
    for cell, argv in cells(t, out_root, groups_dir):
        lines += [f"# {cell}", shlex.join(binding(t) + argv)]
    return "\n".join(head + lines) + "\n"


# ------------------------------------------------------------------ inputs

def head_sets(repo: str = REPO) -> dict:
    """{D_far, H_far, ...: {(layer, head)}} from the six atomic runs' masks."""
    import ma_cells as mc
    return {k: set(v) for k, v in mc._head_sets(repo).items()}


def sweep_path(p1_root: str, t: str, cell: str = "s2p") -> str:
    """The phase-1 completeness sweep of one cell (s1, s2, s2p, s3, s4, s5, s6, s7) on one task."""
    return os.path.join(p1_root, cell, "U__leaf", f"{t}_v2", "knockout", "sweep.json")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--p1-root", default=os.path.join(REPO, P1_ROOT), help="the fetched phase-1 cells (S2p sweeps)")
    p.add_argument("--out-root", default=OUT_ROOT, help="cell output root written into the lines")
    p.add_argument("--groups-dir", default=os.path.join(REPO, GROUPS_DIR))
    p.add_argument("--jobs-dir", default=os.path.join(REPO, JOBS_DIR))
    a = p.parse_args(argv)
    os.makedirs(a.groups_dir, exist_ok=True)
    os.makedirs(a.jobs_dir, exist_ok=True)
    sets = head_sets()
    meta = {"rule": "families = the composition sets at leaf from the six atomic runs' head masks; top20 = the S2p "
                    "signed top 20 (layer-0 MLP excluded) as singletons plus the joint set; one seg line per v2 Segment",
            "late_layers": list(LATE_LAYERS), "segments": list(SEGMENTS), "pre_clause": list(PRE_CLAUSE),
            "post_clause": list(POST_CLAUSE), "sources": {}, "tasks": {}}
    for t in TASKS:
        fam = family_groups(t, sets)
        with open(os.path.join(a.groups_dir, f"{t}_families.json"), "w") as f:
            json.dump(fam, f, indent=1)
        sp = sweep_path(a.p1_root, t)
        with open(sp) as f:
            sweep = json.load(f)
        top = top20_groups(sweep)
        with open(os.path.join(a.groups_dir, f"{t}_top20.json"), "w") as f:
            json.dump(top, f, indent=1)
        meta["sources"][os.path.relpath(sp, REPO)] = _sha256(sp)
        meta["tasks"][t] = {"families": {k: len(v) for k, v in fam.items()}, "empty_families": empty_families(t, sets),
                            "top20": [k for k in top if k != "top20_joint"]}
        path = os.path.join(a.jobs_dir, f"04-p2-{t}.batch")
        groups_dir = os.path.relpath(a.groups_dir, REPO) if os.path.isabs(a.groups_dir) else a.groups_dir
        with open(path, "w") as f:
            f.write(batch_text(t, a.out_root, groups_dir))
        print(path, meta["tasks"][t]["families"], "empty:", meta["tasks"][t]["empty_families"])
    for u, (d, h) in RUNS.items():
        for r in (d, h):
            meta["sources"][f"{r}/active_nodes.json"] = _sha256(os.path.join(REPO, r, "active_nodes.json"))
    for t in TASKS:
        op = os.path.join(REPO, OPERAND.format(t=t), "active_nodes.json")
        meta["sources"][os.path.relpath(op, REPO)] = _sha256(op)
    with open(os.path.join(a.groups_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
