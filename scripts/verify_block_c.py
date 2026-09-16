#!/usr/bin/env python
"""
scripts/verify_block_c.py — does the block-C scaffold work on a real GPU?

The component analyses are built on three shared forward passes, a registration
seam and a dataloader, all of which are tested on a 2-layer random Llama. This
script is the one thing those tests cannot do: run the same code against
Llama-3.1-8B-Instruct on a GPU, through the real CLI, on the real SDR circuit.

It takes the same arguments as `analyze_components.py` and forwards them, after
registering `tests/stub_analysis.py` — the stub that records rather than
asserts. It then reads the `stub/check.json` the run wrote and asserts:

  0. **First, before anything else:** `load_analysis_model` returns a model
     whose weights are on CUDA in bfloat16. Ticket 01 shipped that function
     without a GPU to try it on, and every later analysis starts with this call.
  1. The mean clean-minus-corrupt Readout logit difference over the sampled
     instances is positive — the Corruption does flip the answer this model
     gives, which is the premise every patching number is normalized by.
  2. Replacing every head, every MLP block and the embedding with the corrupt
     stream's captures reproduces the corrupt run's Readout logits, to a
     tolerance read against how far apart the two streams are to begin with.
     In bfloat16 the reproduction cannot be bit-exact; what matters is that the
     residue is a rounding error and not a missing sender.
  3. It prints the wall time per forward pass, which is what tickets 03, 04, 07
     and 08 size their grids from.

Submit it with `scripts/verify_block_c.sbatch`. It is a one-off check of the
scaffold, not an analysis, which is why it lives in `scripts/` beside
`smoke_nnsight.py` rather than in `component_analysis/`.
"""

from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: How large the replace-all residue may be, as a fraction of the largest
#: clean-versus-corrupt Readout logit difference in the same batch. A missing
#: sender leaves a residue of the same order as the difference itself; bfloat16
#: rounding leaves one orders of magnitude below it.
REPLACE_TOLERANCE = 0.05


def loading_model_is_the_first_assertion(cli, resolved):
    """Replaces `analyze_components.load_model` for this run."""
    import torch

    from component_analysis.hooks import load_analysis_model

    print(f"[0] load_analysis_model({resolved.model!r}, device={cli.device!r})")
    model = load_analysis_model(resolved.model, device=cli.device,
                                hf_token=cli.hf_token)
    parameter = next(iter(model._model.parameters()))
    assert parameter.device.type == "cuda", \
        f"weights are on {parameter.device}, not CUDA"
    assert parameter.dtype is torch.bfloat16, \
        f"weights are {parameter.dtype}, not the bfloat16 default for a GPU"
    print(f"    OK — {type(model).__name__} over "
          f"{type(model._model).__name__}, {parameter.device}, "
          f"{parameter.dtype}, attn "
          f"{model._model.config._attn_implementation}")
    return model


def find_checks(output_dir: str) -> list:
    from tests import stub_analysis

    pattern = os.path.join(output_dir, "*", "*", stub_analysis.SUBDIR,
                           stub_analysis.CHECK_FILE)
    return sorted(glob.glob(pattern)) or sorted(glob.glob(
        os.path.join(output_dir, "**", stub_analysis.CHECK_FILE),
        recursive=True))


def check(path: str) -> None:
    with open(path) as handle:
        payload = json.load(handle)
    measured = payload["measurements"]
    print(f"\n=== {path}")
    print(f"    circuit {payload['circuit']}  task {payload['task']}  "
          f"{payload['n_components']} Component(s)")
    assert measured is not None, "the run wrote no measurements, so no model ran"

    gap = measured["clean_minus_corrupt_logit_difference"]
    print(f"[1] clean - corrupt logit(Target) - logit(Distractor) over "
          f"{measured['n_instances']} instance(s): mean {gap['mean']:.4f}, "
          f"{gap['n_positive']} positive / {gap['n_negative']} negative, "
          f"range [{gap['min']:.4f}, {gap['max']:.4f}]")
    assert gap["mean"] > 0, \
        (f"the mean clean-minus-corrupt Readout logit difference is "
         f"{gap['mean']}, not positive: the Corruption does not move this "
         f"model's answer on this sample, so no patching metric normalized by "
         f"it would mean anything")

    residue = measured["replace_all_with_corrupt_max_abs_logit_error"]
    spread = measured["clean_vs_corrupt_max_abs_logit_difference"]
    print(f"[2] replacing all {measured['n_keys_replaced']} sender(s) with the "
          f"corrupt captures: max |logit| error {residue:.5f} against a "
          f"clean-vs-corrupt spread of {spread:.5f} "
          f"({residue / spread:.2%} of it)")
    assert residue <= REPLACE_TOLERANCE * spread, \
        (f"replacing every head, MLP block and the embedding with the corrupt "
         f"stream's captures left {residue:.5f} of Readout logit error, more "
         f"than {REPLACE_TOLERANCE:.0%} of the {spread:.5f} the two streams "
         f"differ by. Something the residual stream reads is not in the "
         f"replaced set.")

    timings = measured["timings"]
    print(f"[3] wall time per forward, batch {timings['batch_size']} x "
          f"{timings['sequence_length']} tokens, on {measured['device']} in "
          f"{measured['dtype']}:")
    for name in ("capture_all_components_sdpa_s", "replace_all_components_sdpa_s",
                 "attention_weights_eager_s", "per_instance_capture_s"):
        print(f"      {name:38s} {timings[name]:.4f} s")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--output-dir" not in argv:
        raise SystemExit("verify_block_c.py needs --output-dir so it can find "
                         "the check files the run writes")
    output_dir = argv[argv.index("--output-dir") + 1]

    import analyze_components
    from component_analysis import registry
    from tests import stub_analysis

    registry.ANALYSES.append(stub_analysis)
    analyze_components.load_model = loading_model_is_the_first_assertion

    code = analyze_components.main(argv)
    if code != 0:
        return code
    if "--dry-run" in argv:
        # The same command the job will run, rehearsed on the login node: it
        # resolves the circuit, the sample and the loaders and prints the
        # stub's estimate, but writes no check file to read back.
        print("\n--dry-run: the scaffold resolved. Drop --dry-run on a GPU "
              "node to measure it.")
        return 0

    checks = find_checks(output_dir)
    if not checks:
        raise SystemExit(f"the run wrote no {stub_analysis.CHECK_FILE} under "
                         f"{output_dir}")
    for path in checks:
        check(path)

    print(f"\nOK — the block-C scaffold works on this GPU over "
          f"{len(checks)} cell(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
