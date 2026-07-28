# Epoch-0 validation eval during gate optimization

**Date:** 2026-07-21  
**Status:** Approved

## Problem

During node and edge pruning, `_optimize_gates` only runs `task.evaluate` on the validation set every `eval_every` epochs (default 10). There is no checkpoint of the freshly built / initialized gate model before training. For edge pruning especially, fidelity can collapse before the first mid-run eval, with no early signal.

## Goal

Run one validation evaluation at epoch 0 (before any gate updates) for every phase that uses `_optimize_gates`, using the same path and labeling as the existing periodic evals.

## Non-goals

- Test-set evaluation at init (post-phase test evals in `train.py` stay as they are)
- New CLI flags or changing default `eval_every`
- Adding an Ep 0 row to the final fidelity comparison table
- Rebuilding / evaluating a full node-pruned model on `--skip-node-pruning` (no mask apply yet; `Edge Ep 0` covers that path)
- Changing finalize or post-phase test evals

## Behavior

In `_optimize_gates` (`pruning.py`):

1. When `eval_every` is truthy, before the epoch training loop, call `task.evaluate` on `val_dl` with label `{phase_label} Ep 0`.
2. If metrics are a dict, append `{"epoch": 0, **metrics}` to `history["evals"]`.
3. Restore `model.train()` afterward, same as the periodic evals.
4. When `eval_every` is falsy (`0` / `None`), skip Ep 0 as well as mid-run evals.

Applies to both node and edge pruning (both call `_optimize_gates`).

## Success criteria

- A node-pruning run prints `EVALUATING: Node Ep 0` before epoch 1 training.
- An edge-pruning run prints `EVALUATING: Edge Ep 0` before epoch 1 training.
- `history["evals"]` includes an entry with `"epoch": 0` when `eval_every` is set.
- Existing Ep 10 / 20 / … evals are unchanged.
