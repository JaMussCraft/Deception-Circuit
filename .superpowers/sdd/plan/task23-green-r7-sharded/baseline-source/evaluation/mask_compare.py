"""
evaluation/mask_compare.py — overlap and difference metrics for saved node masks.

Compares the binary gate masks stored under the "masks" key of
`active_nodes.json` (and the coarse active_heads / active_mlps summaries).
"""

from __future__ import annotations

import json
import os
from itertools import combinations

import numpy as np

from evaluation.masks import ALL_KEYS, BLOCK_KEYS, FINEST_KEYS, SCALAR_KEYS, VECTOR_KEYS, count_masks

GRANULARITY_GROUPS = {
    "all": ALL_KEYS,
    "finest": FINEST_KEYS,
    "coarse": SCALAR_KEYS + BLOCK_KEYS + ("attention_heads",),
}


def resolve_active_nodes_path(path: str, filename: str = "active_nodes.json") -> str:
    """Accept a run directory or a direct path to active_nodes.json."""
    if os.path.isdir(path):
        path = os.path.join(path, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{path} not found")
    return path


def default_label(path: str, filename: str = "active_nodes.json") -> str:
    """Short human-readable label derived from a run path."""
    resolved = resolve_active_nodes_path(path, filename)
    parent = os.path.basename(os.path.dirname(resolved))
    if parent and parent not in (".", ""):
        return parent
    return os.path.splitext(os.path.basename(resolved))[0]


def load_active_nodes_payload(path: str, filename: str = "active_nodes.json") -> dict:
    resolved = resolve_active_nodes_path(path, filename)
    with open(resolved) as f:
        return json.load(f)


def load_masks(path: str, filename: str = "active_nodes.json") -> dict:
    payload = load_active_nodes_payload(path, filename)
    if "masks" not in payload:
        raise ValueError(
            f"{resolve_active_nodes_path(path, filename)} has no 'masks' key — "
            f"only active_heads / active_mlps are available.")
    return payload["masks"]


def _as_vector(value) -> np.ndarray:
    return np.asarray(value, dtype=np.uint8).reshape(-1)


def compare_vectors(a, b) -> dict:
    """Set algebra on two equal-length binary vectors."""
    xa, xb = _as_vector(a), _as_vector(b)
    if xa.size != xb.size:
        return {
            "compatible": False,
            "size_a": int(xa.size),
            "size_b": int(xb.size),
        }

    inter = int((xa & xb).sum())
    only_a = int((xa & (1 - xb)).sum())
    only_b = int(((1 - xa) & xb).sum())
    union = int((xa | xb).sum())
    active_a = int(xa.sum())
    active_b = int(xb.sum())
    identical = bool(np.array_equal(xa, xb))

    return {
        "compatible": True,
        "active_a": active_a,
        "active_b": active_b,
        "intersection": inter,
        "union": union,
        "only_a": only_a,
        "only_b": only_b,
        "symmetric_diff": only_a + only_b,
        "jaccard": (inter / union) if union else 1.0,
        "overlap_coef": (inter / min(active_a, active_b)) if min(active_a, active_b) else 1.0,
        "identical": identical,
        "total": int(xa.size),
    }


def _layer_keys(*entries: dict) -> list[str]:
    keys = set()
    for entry in entries:
        if entry:
            keys.update(entry)
    return sorted(keys, key=int)


def compare_mask_entry(a, b) -> dict:
    """Compare one granularity entry (scalar, vector, or per-layer dict)."""
    if isinstance(a, dict) or isinstance(b, dict):
        if not isinstance(a, dict):
            a = {}
        if not isinstance(b, dict):
            b = {}
        layer_keys = _layer_keys(a, b)
        per_layer = {}
        totals = {
            "active_a": 0, "active_b": 0, "intersection": 0, "union": 0,
            "only_a": 0, "only_b": 0, "symmetric_diff": 0, "total": 0,
        }
        incompatible = []
        for key in layer_keys:
            va = a.get(key, np.zeros(0, dtype=np.uint8))
            vb = b.get(key, np.zeros(0, dtype=np.uint8))
            if key not in a or key not in b:
                if key not in a:
                    va = np.zeros_like(_as_vector(vb))
                else:
                    vb = np.zeros_like(_as_vector(va))
            layer = compare_vectors(va, vb)
            per_layer[key] = layer
            if not layer["compatible"]:
                incompatible.append(key)
                continue
            for k in totals:
                if k in layer:
                    totals[k] += layer[k]

        union = totals["union"]
        inter = totals["intersection"]
        active_a, active_b = totals["active_a"], totals["active_b"]
        return {
            "kind": "per_layer",
            "compatible": not incompatible,
            "incompatible_layers": incompatible,
            "per_layer": per_layer,
            "active_a": active_a,
            "active_b": active_b,
            "intersection": inter,
            "union": union,
            "only_a": totals["only_a"],
            "only_b": totals["only_b"],
            "symmetric_diff": totals["symmetric_diff"],
            "jaccard": (inter / union) if union else 1.0,
            "overlap_coef": (inter / min(active_a, active_b)) if min(active_a, active_b) else 1.0,
            "identical": all(layer.get("identical", False) for layer in per_layer.values()
                             if layer.get("compatible")),
            "total": totals["total"],
        }

    return {"kind": "flat", **compare_vectors(a, b)}


def compare_masks(a: dict, b: dict, keys=None) -> dict:
    """Pairwise comparison across mask granularities."""
    keys = list(keys or sorted(set(a) | set(b)))
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    granularities = {}
    problems = []

    for key in keys:
        if key not in a or key not in b:
            problems.append(f"{key}: present in only one circuit")
            continue
        entry = compare_mask_entry(a[key], b[key])
        granularities[key] = entry
        if not entry.get("compatible", True):
            problems.append(f"{key}: incompatible shapes")

    return {
        "keys_only_a": only_a,
        "keys_only_b": only_b,
        "granularities": granularities,
        "problems": problems,
    }


def compare_many(masks_list: list[dict], keys=None) -> dict:
    """Multi-way intersection / union across N mask objects."""
    if len(masks_list) < 2:
        raise ValueError("compare_many requires at least two mask objects")

    keys = list(keys or sorted(set().union(*[set(m) for m in masks_list])))
    only_missing = {i: sorted(set(keys) - set(m)) for i, m in enumerate(masks_list)}
    granularities = {}

    for key in keys:
        if any(key not in m for m in masks_list):
            granularities[key] = {
                "compatible": False,
                "missing_in": [i for i, m in enumerate(masks_list) if key not in m],
            }
            continue

        entries = [m[key] for m in masks_list]
        if isinstance(entries[0], dict):
            layer_keys = _layer_keys(*entries)
            per_layer = {}
            totals = {"all_active": 0, "any_active": 0, "union": 0, "total": 0}
            for layer in layer_keys:
                vectors = []
                for entry in entries:
                    if layer not in entry:
                        ref = next(_as_vector(entry[k]) for k in _layer_keys(entry))
                        vectors.append(np.zeros(ref.size, dtype=np.uint8))
                    else:
                        vectors.append(_as_vector(entry[layer]))
                sizes = {v.size for v in vectors}
                if len(sizes) != 1:
                    per_layer[layer] = {"compatible": False, "sizes": sorted(sizes)}
                    continue
                stack = np.stack(vectors, axis=0)
                active_counts = stack.sum(axis=0)
                n = len(vectors)
                all_active = int((active_counts == n).sum())
                any_active = int((active_counts > 0).sum())
                per_layer[layer] = {
                    "compatible": True,
                    "all_active": all_active,
                    "any_active": any_active,
                    "union": any_active,
                    "total": int(stack.shape[1]),
                    "active_counts": {str(i): int(v.sum()) for i, v in enumerate(vectors)},
                }
                totals["all_active"] += all_active
                totals["any_active"] += any_active
                totals["union"] += any_active
                totals["total"] += int(stack.shape[1])
            union = totals["union"]
            all_active = totals["all_active"]
            granularities[key] = {
                "kind": "per_layer",
                "compatible": True,
                "per_layer": per_layer,
                "all_active": all_active,
                "any_active": union,
                "jaccard_all_vs_any": (all_active / union) if union else 1.0,
                "total": totals["total"],
            }
            continue

        vectors = [_as_vector(v) for v in entries]
        sizes = {v.size for v in vectors}
        if len(sizes) != 1:
            granularities[key] = {"compatible": False, "sizes": sorted(sizes)}
            continue
        stack = np.stack(vectors, axis=0)
        active_counts = stack.sum(axis=0)
        n = len(vectors)
        all_active = int((active_counts == n).sum())
        any_active = int((active_counts > 0).sum())
        granularities[key] = {
            "kind": "flat",
            "compatible": True,
            "all_active": all_active,
            "any_active": any_active,
            "union": any_active,
            "jaccard_all_vs_any": (all_active / any_active) if any_active else 1.0,
            "total": int(stack.shape[1]),
            "active_counts": {str(i): int(v.sum()) for i, v in enumerate(vectors)},
        }

    return {"keys_missing": only_missing, "granularities": granularities}


def compare_active_summaries(payloads: list[dict]) -> dict:
    """Coarse overlap on active_heads / active_mlps (always present)."""
    head_sets = []
    mlp_sets = []
    for payload in payloads:
        heads = {int(layer): set(indices)
                 for layer, indices in payload.get("active_heads", {}).items()}
        head_sets.append(heads)
        mlp_sets.append(set(payload.get("active_mlps", [])))

    n = len(payloads)
    all_layers = sorted(set().union(*[h.keys() for h in head_sets]))
    per_layer_heads = {}
    for layer in all_layers:
        sets = [h.get(layer, set()) for h in head_sets]
        union = set().union(*sets)
        inter = set.intersection(*sets) if sets else set()
        per_layer_heads[str(layer)] = {
            "active_counts": [len(s) for s in sets],
            "intersection": len(inter),
            "union": len(union),
            "jaccard": (len(inter) / len(union)) if union else 1.0,
        }

    mlp_union = set().union(*mlp_sets)
    mlp_inter = set.intersection(*mlp_sets) if mlp_sets else set()
    return {
        "attention_heads": {
            "per_layer": per_layer_heads,
            "total_active": [sum(len(h.get(l, set())) for l in all_layers) for h in head_sets],
        },
        "active_mlps": {
            "active_counts": [len(s) for s in mlp_sets],
            "intersection": len(mlp_inter),
            "union": len(mlp_union),
            "jaccard": (len(mlp_inter) / len(mlp_union)) if mlp_union else 1.0,
            "only_in": [sorted(s - mlp_inter) for s in mlp_sets],
        },
    }


def summarize_pairwise(labels: list[str], masks: list[dict], keys=None) -> dict:
    pairs = {}
    for (i, j) in combinations(range(len(masks)), 2):
        name = f"{labels[i]} vs {labels[j]}"
        pairs[name] = compare_masks(masks[i], masks[j], keys=keys)
    return pairs


def build_report(labels: list[str], paths: list[str], keys=None,
                 filename: str = "active_nodes.json") -> dict:
    payloads = [load_active_nodes_payload(p, filename) for p in paths]
    masks = [p["masks"] for p in payloads if "masks" in p]
    if len(masks) != len(payloads):
        missing = [labels[i] for i, p in enumerate(payloads) if "masks" not in p]
        raise ValueError(f"these inputs lack saved masks: {missing}")

    counts = {label: count_masks(m) for label, m in zip(labels, masks)}
    pairwise = summarize_pairwise(labels, masks, keys=keys)
    multi = compare_many(masks, keys=keys)
    summaries = compare_active_summaries(payloads)

    return {
        "labels": labels,
        "paths": [resolve_active_nodes_path(p, filename) for p in paths],
        "counts": counts,
        "pairwise": pairwise,
        "multi": multi,
        "active_summaries": summaries,
        "keys": list(keys or ALL_KEYS),
    }
