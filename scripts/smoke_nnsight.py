#!/usr/bin/env python
"""
scripts/smoke_nnsight.py — does nnsight trace this repo's model, in this env?

Run it in the `mgnp` environment, which is the only one where nnsight installs
(it needs Python >= 3.10; the login-node base env is 3.9):

    source /sw/external/python/anaconda3/etc/profile.d/conda.sh
    conda activate mgnp
    python scripts/smoke_nnsight.py

It traces one CPU forward of the 2-layer random Llama from `tests/helpers.py`
and checks the four things every later analysis depends on:

  1. nnsight 0.7.0 is the installed version, and transformers / torch are the
     versions the training and evaluation code runs on (5.13.0 / 2.11.0). An
     nnsight install that moved either of those would silently change every
     number this repo has already produced.
  2. Tracing reproduces a plain forward exactly. If it does not, nothing
     measured through a hook can be trusted.
  3. The module boundaries ADR-0001 names are reachable and have the shapes it
     claims: `model.embed_tokens`, the *input* to `self_attn.o_proj` (the
     per-head output, laid out [batch, seq, n_heads * head_dim] — slicing the
     o_proj *output* is not a head), `q_proj`/`k_proj`/`v_proj` with k and v
     narrower than q under grouped-query attention, `mlp`, and `lm_head`.
  4. Attention weights come back only under eager attention. Under SDPA in
     transformers 5.13 they are None, which is why pattern extraction switches
     the implementation and nothing else pays for it.

One nnsight 0.7.0 constraint this script pins down, because it costs an hour to
diagnose from its error message: envoy accesses inside a trace are resolved
lazily against the forward as it runs, so they must be written in *execution
order*. Reading `o_proj.input` before `q_proj.output` makes the trace end with
`MissedProviderError: ... was not provided`, as though q_proj had never run.

The tiny model is built as a plain `LlamaForCausalLM`; the prunable wrapper is
never instantiated on the analysis path (ADR-0001).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from transformers import LlamaForCausalLM

from tests.helpers import TINY, tiny_config

SEQ = 8


def build_tiny(attn_implementation="sdpa"):
    cfg = tiny_config(attn_implementation=attn_implementation)
    torch.manual_seed(0)
    return LlamaForCausalLM(cfg).eval()


def check_versions():
    import nnsight
    import transformers

    print(f"  nnsight       {nnsight.__version__}")
    print(f"  transformers  {transformers.__version__}")
    print(f"  torch         {torch.__version__}")
    assert nnsight.__version__ == "0.7.0", \
        f"ADR-0001 pins nnsight 0.7.0; found {nnsight.__version__}"
    assert transformers.__version__ == "5.13.0", \
        f"the mgnp env must stay on transformers 5.13.0; found {transformers.__version__}"
    assert torch.__version__.startswith("2.11.0"), \
        f"the mgnp env must stay on torch 2.11.0; found {torch.__version__}"


def check_trace_matches_a_plain_forward(model, input_ids):
    from nnsight import NNsight

    with torch.no_grad():
        expected = model(input_ids).logits

    traced = NNsight(model)
    with traced.trace(input_ids):
        logits = traced.output.logits.save()

    assert torch.equal(logits, expected), \
        "nnsight's traced logits differ from a plain forward"
    print(f"  traced logits {tuple(logits.shape)} — identical to a plain forward")


def check_module_boundaries(model, input_ids):
    from nnsight import NNsight

    n_heads, head_dim = TINY["heads"], TINY["head_dim"]
    n_kv = TINY["kv_heads"]
    traced = NNsight(model)
    layer = traced.model.layers[0]

    # Order matters. nnsight 0.7.0 resolves these lazily against the forward as
    # it runs, so an envoy touched out of execution order never fires and the
    # trace ends with `MissedProviderError: ... was not provided`. Asking for
    # o_proj's input before q_proj's output is enough to trigger it. Keep every
    # access inside a trace in the order the modules run.
    with traced.trace(input_ids):
        embedded = traced.model.embed_tokens.output.save()
        q = layer.self_attn.q_proj.output.save()
        k = layer.self_attn.k_proj.output.save()
        v = layer.self_attn.v_proj.output.save()
        # The per-head output is the INPUT to o_proj, not a slice of its output.
        head_output = layer.self_attn.o_proj.input.save()
        mlp_out = layer.mlp.output.save()
        unembedded = traced.lm_head.output.save()

    batch = input_ids.shape[0]
    assert tuple(embedded.shape) == (batch, SEQ, TINY["hidden"]), embedded.shape
    assert tuple(head_output.shape) == (batch, SEQ, n_heads * head_dim), \
        head_output.shape
    assert tuple(q.shape) == (batch, SEQ, n_heads * head_dim), q.shape
    assert tuple(k.shape) == tuple(v.shape) == (batch, SEQ, n_kv * head_dim), \
        (k.shape, v.shape)
    assert tuple(mlp_out.shape) == (batch, SEQ, TINY["hidden"]), mlp_out.shape
    assert tuple(unembedded.shape) == (batch, SEQ, TINY["vocab"]), unembedded.shape

    print(f"  o_proj input  {tuple(head_output.shape)} = "
          f"{n_heads} heads x {head_dim}")
    print(f"  k/v_proj      {tuple(k.shape)} = {n_kv} KV heads x {head_dim} "
          f"({n_heads // n_kv} query heads per group)")


def check_attention_weights_need_eager(input_ids):
    from nnsight import NNsight

    for implementation, expected in (("sdpa", False), ("eager", True)):
        traced = NNsight(build_tiny(implementation))
        # Save the whole (attn_output, attn_weights) tuple rather than
        # indexing inside the trace: under SDPA the second element is None,
        # and `.save()` on it never binds, which surfaces as an
        # UnboundLocalError instead of the None the caller expects.
        with traced.trace(input_ids):
            attention = traced.model.layers[0].self_attn.output.save()
        weights = attention[1]
        got = weights is not None
        assert got is expected, \
            f"{implementation}: attention weights present={got}, expected {expected}"
        if got:
            assert tuple(weights.shape) == (input_ids.shape[0], TINY["heads"],
                                            SEQ, SEQ), weights.shape
            print(f"  eager weights {tuple(weights.shape)}")
        else:
            print("  sdpa weights  None, as transformers 5.13 documents")


def main() -> int:
    print("nnsight smoke test — tiny random Llama, CPU\n")
    check_versions()

    torch.manual_seed(1)
    input_ids = torch.randint(0, TINY["vocab"], (2, SEQ))

    model = build_tiny()
    check_trace_matches_a_plain_forward(model, input_ids)
    check_module_boundaries(model, input_ids)
    check_attention_weights_need_eager(input_ids)

    print("\nOK — nnsight traces this repo's model and every sender and "
          "receiver ADR-0001 names is reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
