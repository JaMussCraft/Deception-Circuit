"""
overlap.py — Jaccard overlap of D, H and F, written into the suite directory.

For each pair D/H, D/F, H/F: Jaccard over attention heads and over fine units
(attention neurons, MLP hidden and MLP output pooled: summed intersections over
summed unions), from `evaluation.mask_compare.compare_masks`.

Coarse circuits are compared on `active_nodes.coarse.json` (the un-expanded
masks the run pruned), heads only: the expanded `active_nodes.json` puts every
MLP unit in every coarse circuit, and a heads-only circuit's attention neurons
are its heads x head_dim, so a fine-unit Jaccard would add nothing.

Writes <suite_root>/overlap.json and <suite_root>/overlap.md.
"""

from __future__ import annotations

import json
import os

from evaluation.mask_compare import compare_masks, load_masks
from evaluation.masks import FINEST_KEYS

PAIRS = (("D", "H"), ("D", "F"), ("H", "F"))
COARSE_FILE = "active_nodes.coarse.json"


def _pooled(granularities: dict, keys) -> dict:
    present = [granularities[k] for k in keys if k in granularities]
    if not present:
        return None
    tot = {f: sum(int(g.get(f, 0)) for g in present)
           for f in ("intersection", "union", "active_a", "active_b")}
    tot["jaccard"] = tot["intersection"] / tot["union"] if tot["union"] else 1.0
    return tot


def overlap_table(cfg: dict) -> dict:
    coarse = cfg["family"] == "coarse"
    filename = COARSE_FILE if coarse else "active_nodes.json"
    runs = cfg["runs"]
    masks = {r: load_masks(p, filename) for r, p in runs.items() if p}
    pairs = []
    for a, b in PAIRS:
        awaits = [r for r in (a, b) if r not in masks]
        if awaits:
            pairs.append({"pair": f"{a}/{b}", "awaits": awaits, "heads": None, "fine_units": None})
            continue
        g = compare_masks(masks[a], masks[b])["granularities"]
        pairs.append({"pair": f"{a}/{b}", "awaits": [],
                      "heads": _pooled(g, ("attention_heads",)),
                      "fine_units": None if coarse else _pooled(g, FINEST_KEYS)})
    return {"family": cfg["family"], "task": cfg["task"], "mask_file": filename,
            "runs": runs, "pairs": pairs,
            "note": ("coarse: heads only, from the un-expanded masks" if coarse else
                     "fine units pool attention_neurons, mlp_hidden and mlp_output")}


def _f(x):
    return f"{x:.3f}" if isinstance(x, float) else "-"


def render_md(table: dict) -> str:
    lines = [f"# Overlap of D, H and F ({table['task']}, {table['family']})", "",
             f"Masks: `{table['mask_file']}`. {table['note']}.", "",
             "| pair | Jaccard heads | heads A / B / both | Jaccard fine units | fine units A / B / both |",
             "| --- | --- | --- | --- | --- |"]
    for r in table["pairs"]:
        if r["awaits"]:
            lines.append(f"| {r['pair']} | awaits {', '.join(r['awaits'])} | | | |")
            continue
        h, fu = r["heads"], r["fine_units"]
        hs = f"{h['active_a']} / {h['active_b']} / {h['intersection']}" if h else "-"
        fs = f"{fu['active_a']} / {fu['active_b']} / {fu['intersection']}" if fu else "-"
        lines.append(f"| {r['pair']} | {_f(h['jaccard'] if h else None)} | {hs} | "
                     f"{_f(fu['jaccard'] if fu else None)} | {fs} |")
    return "\n".join(lines) + "\n"


def write_overlap(suite_root: str, cfg: dict) -> list:
    table = overlap_table(cfg)
    os.makedirs(suite_root, exist_ok=True)
    jp = os.path.join(suite_root, "overlap.json")
    mp = os.path.join(suite_root, "overlap.md")
    with open(jp, "w") as f:
        json.dump(table, f, indent=2)
    with open(mp, "w") as f:
        f.write(render_md(table))
    return [jp, mp]
