#!/usr/bin/env python3
"""
build_allmlp.py — the `m` operand of the coarse heads-only knockout `(X) - m`.

Same recipe as outputs/llama-8b-instruct_sdr_coarse/_launch/submit_headsko.sh:
take a coarse run's expanded mask and keep its keys, close every head (and
attention block and attention neuron), open every MLP unit (and MLP block).
`(X) - m` composed at leaf is then X's heads with no MLP unit, so its knockout
removes the heads only. The run's config.json is copied so the evaluator can
load the operand like a run.

usage: python outputs/_launch_format_control/build_allmlp.py <coarse_run_dir> <out_dir>
"""

from __future__ import annotations

import json
import os
import sys


def build_allmlp(run_dir: str, out_dir: str) -> str:
    with open(os.path.join(run_dir, "active_nodes.json")) as f:
        masks = json.load(f)["masks"]
    out = {}
    for key, value in masks.items():
        if key == "attention_blocks":
            out[key] = [0] * len(value)
        elif key == "mlp_blocks":
            out[key] = [1] * len(value)
        elif key in ("attention_heads", "attention_neurons"):
            out[key] = {layer: [0] * len(v) for layer, v in value.items()}
        elif key in ("mlp_hidden", "mlp_output"):
            out[key] = {layer: [1] * len(v) for layer, v in value.items()}
        else:
            out[key] = value
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "active_nodes.json"), "w") as f:
        json.dump({"masks": out, "built_from": os.path.abspath(run_dir)}, f)
    with open(os.path.join(run_dir, "config.json")) as f:
        config = json.load(f)
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=1)
    return out_dir


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(build_allmlp(sys.argv[1], sys.argv[2]))
