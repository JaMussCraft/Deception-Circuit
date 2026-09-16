"""
A stub analysis: the smallest module the registration seam accepts.

It exists for two jobs and produces no finding of its own.

  * In `tests/test_analyze_components_registry.py` it proves the seam — that an
    analysis registered in one list gets its flags, its `--dry-run` estimate,
    its own subdirectory and its head-table columns namespaced under its name,
    without the CLI knowing anything about it.
  * On a GPU it is the block-C scaffold check: `scripts/verify_block_c.py`
    registers it and runs the real CLI over the real SDR circuit, and
    `measure` records the numbers ticket 02b asks for — the clean-minus-corrupt
    Readout logit difference, whether replacing every Component with its
    corrupt capture reproduces the corrupt logits, and the wall time per
    forward pass that tickets 03, 04, 07 and 08 size their grids from.

It **records rather than asserts**: the same code runs on the tiny random model,
where a positive logit difference is not expected, and a check that quietly
passes on noise is worse than a number in a file. `verify_block_c.py` reads
`check.json` and does the asserting.

Analyses live in `component_analysis/`; this one lives in `tests/` because it
is scaffolding, not an analysis.
"""

from __future__ import annotations

import time

NAME = "stub"
SUBDIR = "stub"

#: The file `run` writes under `<cell>/stub/`.
CHECK_FILE = "check.json"


def add_arguments(group) -> None:
    group.add_argument("--stub-batches", type=int, default=2,
                       help="How many batches of the causal sample the stub "
                            "measures. All of them when 0.")


def estimate(ctx) -> str:
    batches = ctx.causal_batches()
    wanted = getattr(ctx.cli, "stub_batches", 2) or len(batches)
    measured = min(wanted, len(batches))
    return (f"{measured} batch(es) of {batches.report['batch_size']}, "
            f"3 forward passes each (clean capture, corrupt capture, "
            f"replace-all), {len(ctx.components)} Component(s) in the circuit")


def run(ctx) -> dict:
    """Write `stub/check.json`, and give every Component one column."""
    payload = {
        "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name,
        "n_components": len(ctx.components),
        "measurements": None if ctx.model is None else measure(ctx),
    }
    ctx.write_json(SUBDIR, CHECK_FILE, payload)
    return {component.key: {"captured": True} for component in ctx.components}


# ==============================================================================
# THE MEASUREMENT
# ==============================================================================

def _logit_difference(logits, target, distractor):
    """logit(Target) - logit(Distractor), with the *clean* stream's assignment.

    The corrupt stream swaps which word is the Target, so reading its own
    assignment would make the gap a difference of two positive numbers instead
    of the drop the patching metric normalizes by.
    """
    import torch

    rows = torch.arange(logits.shape[0], device=logits.device)
    return (logits[rows, target].float() - logits[rows, distractor].float())


def _timed(function, *, cuda: bool):
    import torch

    if cuda:
        torch.cuda.synchronize()
    started = time.perf_counter()
    value = function()
    if cuda:
        torch.cuda.synchronize()
    return value, time.perf_counter() - started


def measure(ctx) -> dict:
    """The three scaffold numbers, over the first batches of the causal sample."""
    import torch

    from component_analysis import hooks

    device = next(iter(ctx.model._model.parameters())).device
    cuda = device.type == "cuda"
    keys = hooks.all_component_keys(ctx.model)
    batches = list(ctx.causal_batches())
    wanted = getattr(ctx.cli, "stub_batches", 2) or len(batches)
    batches = batches[:wanted]

    gaps, worst_replace, widest_stream, timings = [], 0.0, 0.0, {}
    warmed = False
    for batch in batches:
        ids = batch.input_ids.to(device)
        mask = batch.attention_mask.to(device)
        corrupt_ids = batch.corrupt_input_ids.to(device)
        corrupt_mask = batch.corrupt_attention_mask.to(device)
        target = batch.target_token.to(device)
        distractor = batch.distractor_token.to(device)
        readout = batch.readout.to(device)

        if not warmed:
            # One untimed pass, so the timings below are not the first CUDA
            # kernel launch and the first weight page-in.
            hooks.capture_forward(ctx.model, ids, mask, components=[],
                                  positions=readout)
            warmed = True

        clean, clean_seconds = _timed(
            lambda: hooks.capture_forward(ctx.model, ids, mask, components=keys,
                                          positions=readout), cuda=cuda)
        corrupt, _ = _timed(
            lambda: hooks.capture_forward(ctx.model, corrupt_ids, corrupt_mask,
                                          components=keys, positions=readout),
            cuda=cuda)
        replaced, replace_seconds = _timed(
            lambda: hooks.replace_forward(ctx.model, ids, mask,
                                          replacements=corrupt.outputs,
                                          positions=readout), cuda=cuda)

        gap = (_logit_difference(clean.logits, target, distractor)
               - _logit_difference(corrupt.logits, target, distractor))
        gaps.extend(gap.tolist())
        worst_replace = max(
            worst_replace,
            float((replaced.float() - corrupt.logits.float()).abs().max()))
        # The scale the replace-all error is read against: how far apart the
        # two streams' Readout logits are in the first place. In bfloat16 the
        # replacement need not be bit-exact, so "small" only means anything
        # beside the difference it is supposed to have reproduced.
        widest_stream = max(
            widest_stream,
            float((clean.logits.float() - corrupt.logits.float()).abs().max()))

        if not timings:
            eager = hooks.attention_weights(ctx.model, ids, mask, layer=0,
                                            heads=[0], query_positions=[0])
            _, eager_seconds = _timed(
                lambda: hooks.attention_weights(ctx.model, ids, mask, layer=0,
                                                heads=[0],
                                                query_positions=[0]), cuda=cuda)
            del eager
            timings = {
                "batch_size": int(ids.shape[0]),
                "sequence_length": int(ids.shape[1]),
                "capture_all_components_sdpa_s": clean_seconds,
                "replace_all_components_sdpa_s": replace_seconds,
                "attention_weights_eager_s": eager_seconds,
                "per_instance_capture_s": clean_seconds / int(ids.shape[0]),
            }

    mean = sum(gaps) / len(gaps) if gaps else float("nan")
    return {
        "device": str(device),
        "dtype": str(next(iter(ctx.model._model.parameters())).dtype),
        "n_instances": len(gaps),
        "n_batches": len(batches),
        "n_keys_replaced": len(keys),
        "clean_minus_corrupt_logit_difference": {
            "mean": mean,
            "n_positive": sum(1 for one in gaps if one > 0),
            "n_negative": sum(1 for one in gaps if one < 0),
            "min": min(gaps) if gaps else None,
            "max": max(gaps) if gaps else None,
        },
        "replace_all_with_corrupt_max_abs_logit_error": worst_replace,
        "clean_vs_corrupt_max_abs_logit_difference": widest_stream,
        "timings": timings,
    }
