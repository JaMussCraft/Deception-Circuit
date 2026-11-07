#!/usr/bin/env python3
"""
expand_coarse_masks.py — add synthetic fine-grained masks to a coarse-only run.

Some training runs disable attention_neurons / mlp_hidden / mlp_output pruning
(noan_nomh_nomo). evaluate_circuit.py needs those mask keys (and matching gate
modules) to infer geometry and apply circuits. This script:

  1. Expands coarse masks so every live head / open MLP block has all fine
     units open (same semantics as evaluation.coarsen_masks).
  2. Sets prune_attention_neurons, prune_mlp_hidden, prune_mlp_output to true
     in config.json so the rebuilt eval model has the gate modules.

Usage:
    python expand_coarse_masks.py outputs/llama-8b-instruct_std/<run_slug>
    python expand_coarse_masks.py <run_dir> --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from transformers import AutoConfig

from evaluation.context import geometry_from_masks
from evaluation.masks import as_arrays, as_lists, validate_hierarchy
from models import MODEL_REGISTRY


FINE_PRUNE_KEYS = (
    "prune_attention_neurons",
    "prune_mlp_hidden",
    "prune_mlp_output",
)


def model_geometry(model_name: str) -> dict:
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"unknown model {model_name!r}; known: {sorted(MODEL_REGISTRY)}")
    hf_id, _family = MODEL_REGISTRY[model_name]
    cfg = AutoConfig.from_pretrained(hf_id)
    num_heads = getattr(cfg, "num_attention_heads", None) or cfg.n_head
    hidden_size = cfg.hidden_size
    head_dim = hidden_size // num_heads
    intermediate_size = getattr(cfg, "intermediate_size", None)
    if intermediate_size is None:
        intermediate_size = cfg.n_inner if getattr(cfg, "n_inner", None) else 4 * hidden_size
    num_layers = getattr(cfg, "num_hidden_layers", None) or cfg.n_layer
    return {
        "num_heads": int(num_heads),
        "head_dim": int(head_dim),
        "hidden_size": int(hidden_size),
        "intermediate_size": int(intermediate_size),
        "num_layers": int(num_layers),
    }


def _layer_open(l: int, layers, mlp_blocks) -> bool:
    if layers is not None and not bool(np.asarray(layers)[l]):
        return False
    if mlp_blocks is not None and not bool(np.asarray(mlp_blocks)[l]):
        return False
    return True


def expand_fine_masks(masks: dict, geom: dict) -> dict:
    """Add all-open fine masks under live coarse parents."""
    heads = masks.get("attention_heads")
    layers = masks.get("layers")
    mlp_blocks = masks.get("mlp_blocks")
    head_dim = geom["head_dim"]
    num_layers = geom["num_layers"]

    out = {k: (v.copy() if isinstance(v, dict) else v) for k, v in masks.items()}
    if isinstance(out.get("attention_blocks"), list):
        out["attention_blocks"] = list(out["attention_blocks"])
    if isinstance(out.get("mlp_blocks"), list):
        out["mlp_blocks"] = list(out["mlp_blocks"])
    if isinstance(out.get("layers"), list):
        out["layers"] = list(out["layers"])

    if heads is not None and "attention_neurons" not in out:
        out["attention_neurons"] = {}
        for key, head_mask in heads.items():
            hm = np.asarray(head_mask, dtype=np.uint8)
            out["attention_neurons"][key] = np.repeat(hm, head_dim).astype(np.uint8)

    if "mlp_hidden" not in out:
        out["mlp_hidden"] = {}
        for l in range(num_layers):
            key = str(l)
            open_ = _layer_open(l, layers, mlp_blocks)
            size = geom["intermediate_size"]
            out["mlp_hidden"][key] = (
                np.ones(size, dtype=np.uint8) if open_ else np.zeros(size, dtype=np.uint8))

    if "mlp_output" not in out:
        out["mlp_output"] = {}
        for l in range(num_layers):
            key = str(l)
            open_ = _layer_open(l, layers, mlp_blocks)
            size = geom["hidden_size"]
            out["mlp_output"][key] = (
                np.ones(size, dtype=np.uint8) if open_ else np.zeros(size, dtype=np.uint8))

    return out


def flip_fine_prune_flags(node_config: dict) -> list[str]:
    changed = []
    for key in FINE_PRUNE_KEYS:
        if not node_config.get(key):
            node_config[key] = True
            changed.append(key)
    return changed


def build_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir", help="Run directory with config.json and active_nodes.json")
    p.add_argument("--dry-run", action="store_true",
                   help="Validate and print a summary without writing files")
    p.add_argument("--force", action="store_true",
                   help="Replace existing fine mask keys if present")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir
    config_path = os.path.join(run_dir, "config.json")
    nodes_path = os.path.join(run_dir, "active_nodes.json")

    for path in (config_path, nodes_path):
        if not os.path.isfile(path):
            print(f"error: {path} not found", file=sys.stderr)
            return 2

    with open(config_path) as f:
        run_config = json.load(f)
    with open(nodes_path) as f:
        payload = json.load(f)

    if "masks" not in payload:
        print("error: active_nodes.json has no 'masks' key", file=sys.stderr)
        return 2

    masks = payload["masks"]
    geom = model_geometry(run_config["model"])
    existing_fine = [k for k in ("attention_neurons", "mlp_hidden", "mlp_output")
                     if k in masks]
    if existing_fine and not args.force:
        print(f"fine mask keys already present: {existing_fine} (use --force to replace)",
              file=sys.stderr)
        return 2

    expanded = expand_fine_masks(as_arrays(masks), geom)
    validate_hierarchy(expanded, num_heads=geom["num_heads"],
                       head_dim=geom["head_dim"], label="expanded circuit")
    recovered = geometry_from_masks(expanded)

    config_changed = flip_fine_prune_flags(run_config["node_config"])
    payload["masks"] = as_lists(expanded)

    print(f"run dir: {run_dir}")
    print(f"model geometry: {geom}")
    print(f"recovered geometry: {recovered}")
    for key in ("attention_neurons", "mlp_hidden", "mlp_output"):
        active = int(sum(np.asarray(v).sum() for v in expanded[key].values()))
        total = int(sum(np.asarray(v).size for v in expanded[key].values()))
        print(f"  {key}: {active}/{total} active")
    print(f"config flags set true: {config_changed or '(already enabled)'}")

    if args.dry_run:
        print("dry run — no files written")
        return 0

    with open(nodes_path, "w") as f:
        json.dump(payload, f, indent=2)
    with open(config_path, "w") as f:
        json.dump(run_config, f, indent=2)
    print(f"wrote {nodes_path}")
    print(f"wrote {config_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
