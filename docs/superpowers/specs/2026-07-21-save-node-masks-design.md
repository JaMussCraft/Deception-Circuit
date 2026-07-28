# Save finalized node gate masks

**Date:** 2026-07-21  
**Status:** Approved design (pending implementation)

## Problem

Node pruning trains and finalizes gates at multiple granularities (heads, attention neurons, MLP hidden/output, blocks, layers, embedding). Only `active_heads` and `active_mlps` are written to `active_nodes.json`. Reproducing the node-pruned circuit for a later evaluation script currently requires re-running `train.py`.

## Goal

After node pruning and hierarchical finalize, persist binary 0/1 masks for every *existing* node gate into `active_nodes.json`, without changing the edge-pruning path.

## Non-goals

- Load / apply helpers that rebuild a prunable model from masks
- A standalone evaluation script
- Saving edge gates
- Changing `--skip-node-pruning` behavior
- Saving soft `log_alpha` values

## Schema

Extend `active_nodes.json` additively:

```json
{
  "active_heads": { "<layer>": [<head_idx>, ...] },
  "active_mlps": [<layer>, ...],
  "masks": {
    "embedding": 0 | 1,
    "layers": [0 | 1, ...],
    "attention_blocks": [0 | 1, ...],
    "mlp_blocks": [0 | 1, ...],
    "attention_heads": { "<layer>": [0 | 1, ...] },
    "attention_neurons": { "<layer>": [0 | 1, ...] },
    "mlp_hidden": { "<layer>": [0 | 1, ...] },
    "mlp_output": { "<layer>": [0 | 1, ...] }
  }
}
```

### Mask rules

- Capture **post-`analyze_and_finalize_circuit`** hard values: `1` iff `gate() > 0.5`, else `0`.
- **Omit** a key under `masks` if that gate module was never created (e.g. `prune_embedding=False`).
- Per-layer lists use the **full gate width** (all heads / all neurons / all MLP dims), including zeros — not sparse active-only indices.
- Layer-keyed dicts use string keys (JSON), same convention as `active_heads`.
- `active_heads` / `active_mlps` remain as today for edge pruning; they must stay consistent with the finalized head/block masks.

## Implementation

1. **`analysis.py`**
   - Add `extract_node_masks(model) -> dict` walking the same layer layout as `extract_active_nodes` / finalize, collecting binary masks for every present gate.
   - Extend `save_active_nodes(active_heads, active_mlps, path, masks=None)` to write `"masks"` when provided.
   - Keep `load_active_nodes(path) -> (active_heads, active_mlps)` unchanged for the edge path (ignore `masks` if present).

2. **`train.py`**
   - After finalize + `extract_active_nodes`, call `extract_node_masks` and pass the result into `save_active_nodes`.

3. **`README.md`**
   - Note that `active_nodes.json` may include a `masks` object with full finalized binary gate masks for later node-circuit evaluation.

## Compatibility

- Existing `active_nodes.json` files without `masks` continue to work for `--skip-node-pruning` / edge pruning.
- New runs write masks; edge pruning does not read them.

## Success criteria

- A completed node-pruning run writes `active_nodes.json` containing `active_heads`, `active_mlps`, and `masks` for every gate type that existed on the model.
- `load_active_nodes` still returns only heads/MLPs and edge pruning still works.
- Masks match the hard circuit used for the in-run node evaluation (post-finalize).
