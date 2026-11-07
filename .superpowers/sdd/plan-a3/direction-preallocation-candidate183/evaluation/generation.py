"""
evaluation/generation.py — open-ended samples from an ablated model.

Every other number in this harness is read at a single prediction position.
That is the right measurement, and it is also completely blind to the failure
mode that matters most for a knockout: a circuit whose removal drops task
accuracy because it broke the model's ability to write English at all. Three
greedy continuations of ordinary wikitext, printed verbatim, are the cheapest
check for that.

Two constraints shape the loop, and both are load-bearing:

* **No KV cache here.** The corrupted stream *can* carry one now
  (`evaluation/gen_engine.py`, and `models/llama_node.py` gives it its own
  `Cache`), but these samples do not use it. Three prompts x 48 tokens is under
  a minute either way, and the uncached forward is the one every other number
  in this harness is produced on, so running it here keeps the coherence check
  on the same code path as the measurements it is vouching for.
  `tests/test_generation.py` pins the full-sequence re-forward; the cached path
  is pinned separately in `tests/test_kv_cache.py`.

* **The corrupted stream must not be the clean stream.** Under `--ablation
  interchange` the ablated units are filled from the corrupted stream, so
  feeding the same text to both makes the intervention a no-op and the
  "knockout" sample comes out identical to the full model's. The corrupted
  stream is the derangement partner from `evaluation/wikitext.py:pair_blocks`
  — the same pairing the collateral-damage measurement uses — pre-extended to
  the full generated length and sliced to the clean stream's growing length.
"""

from __future__ import annotations

import torch

from evaluation.gen_engine import generate
from evaluation.wikitext import load_wikitext_blocks, pair_blocks

#: Tokens of context each sample is primed with, after the forced BOS. Long
#: enough that the model has something to continue, short enough that the
#: quadratic re-forward stays cheap.
PROMPT_TOKENS = 24

#: The three configurations, in reading order. "full" is the control: if it
#: does not read as fluent English, the harness is broken, not the circuit.
CONFIG_LABELS = {
    "full": "full model (all gates open)",
    "knockout": "circuit knocked out",
    "circuit_only": "circuit only (everything else ablated)",
}
CONFIG_ORDER = ("full", "knockout", "circuit_only")


def generation_examples(ctx, n_examples: int, new_tokens: int) -> dict:
    """Greedy continuations of the first wikitext blocks under each config."""
    blocks = load_wikitext_blocks(ctx)
    n = min(n_examples, len(blocks))
    block_size = blocks.shape[1]
    prompt_len = min(PROMPT_TOKENS + 1, block_size)
    total = prompt_len + new_tokens

    perm = pair_blocks(len(blocks), ctx.cli.wikitext_seed)
    partner = blocks[torch.as_tensor(perm.copy())]
    clean0 = blocks[:n, :prompt_len]
    # The corrupted stream has to be at least as long as the clean stream ever
    # gets. A partner block is only `block_size` tokens, so tile it — repeated
    # wikitext is still wikitext, and still nothing like the clean block, which
    # is all the corrupted stream has to be.
    reps = -(-total // block_size)
    corrupt = partner[:n].repeat(1, reps)[:, :total]

    hook = ctx.hook_for("wikitext")
    outputs = {}
    for config in CONFIG_ORDER:
        desc = f"generating: {config}"
        if config == "full":
            with ctx.all_gates_open():
                outputs[config] = _generate(ctx, clean0, corrupt, new_tokens,
                                            hook, desc)
        else:
            masks = (ctx.knockout_masks if config == "knockout"
                     else ctx.circuit_masks)
            with ctx.circuit(masks):
                outputs[config] = _generate(ctx, clean0, corrupt, new_tokens,
                                            hook, desc)

    tok = ctx.tokenizer
    examples = []
    for i in range(n):
        examples.append({
            "index": i,
            "prompt": tok.decode(clean0[i].tolist()),
            "continuations": {c: tok.decode(outputs[c][i, prompt_len:].tolist())
                              for c in CONFIG_ORDER},
        })
    return {
        "source": "wikitext-2 (test), the same blocks as the collateral-damage "
                  "measurement, truncated to BOS + context",
        "n_examples": n,
        "prompt_tokens": prompt_len,
        "new_tokens": new_tokens,
        "decoding": "greedy, no KV cache (cheap at this size, and the same "
                    "forward every other measurement here runs)",
        "pairing_seed": ctx.cli.wikitext_seed,
        "ablation": ctx.cli.ablation,
        "configs": list(CONFIG_ORDER),
        "examples": examples,
    }


def _generate(ctx, clean0, corrupt, new_tokens, hook, desc):
    """Greedy decode, re-forwarding the whole sequence at every step.

    `eos_ids=()` on purpose: a wikitext continuation has no natural stopping
    point, and the sample is meant to be read for fluency across its whole
    length rather than truncated at the first end-of-text an ablated model
    happens to emit.
    """
    return generate(
        ctx,
        clean_ids=clean0,
        corrupt_ids=corrupt,
        attention_mask=torch.ones_like(clean0),
        hook=hook,
        new_tokens=new_tokens,
        eos_ids=(),
        use_cache=False,
        desc=desc).cpu()


def report_generations(payload, report) -> None:
    """Print every sample in full. These are meant to be read, not scanned."""
    report.banner(f"OPEN GENERATION ON WIKITEXT "
                  f"({payload['n_examples']} prompts x "
                  f"{payload['new_tokens']} greedy tokens)")
    print(f"\n  {payload['decoding']}; the corrupted stream is the derangement "
          f"partner\n  block (seed {payload['pairing_seed']}), so an "
          f"interchange ablation actually bites.")
    for example in payload["examples"]:
        report.banner(f"prompt {example['index']}", "-")
        print(f"\n  {example['prompt']!r}\n")
        for config in payload["configs"]:
            print(f"  {CONFIG_LABELS[config]}:")
            print(f"    {example['continuations'][config]!r}\n")
