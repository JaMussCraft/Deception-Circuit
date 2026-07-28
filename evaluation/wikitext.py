"""
evaluation/wikitext.py — the collateral-damage reference stream.

A knockout that stops the model lying is only interesting if it has not also
broken the model. This measures what an intervention costs on text that has
nothing to do with the task: mean per-token KL(full ‖ ablated) and the
perplexity ratio over wikitext-2.

Three details that matter:

* **Paired blocks.** The dual-stream forward always needs a corrupted stream, so
  blocks are paired by a fixed derangement (a permutation with no fixed point),
  computed once and reused by every configuration — no pairing noise enters the
  null.
* **Loop order.** Wikitext batches outer, gate configurations inner. Re-applying
  log_alpha takes microseconds, so this way the full-model forward happens once
  per batch instead of once per (batch, configuration), and there is no need to
  cache 8.4 GB of wikitext logits.
* **Position 0.** Each block's first token is replaced with <|begin_of_text|>;
  position-0 activations are badly off-distribution for a Llama-3 Instruct model
  otherwise, and they would dominate the per-token averages.
"""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from tqdm import tqdm

from evaluation.ablation import ablation_hook

# Sequence-dim chunk for the fp32 log-softmax / KL reduction. A
# [4, 512, 128256] fp32 pair is ~2.1 GB transient; chunking keeps it under
# control on a 40 GB card without changing a single number.
_VOCAB_CHUNK = 64


# ==============================================================================
# BLOCKS
# ==============================================================================

def load_wikitext_blocks(ctx):
    """[n_blocks, block_size] token ids, first token forced to BOS."""
    cached = getattr(ctx, "_wikitext_blocks", None)
    if cached is not None:
        return cached

    from datasets import load_dataset

    cli = ctx.cli
    print(f"  Loading wikitext-2 (test): {cli.wikitext_blocks} blocks x "
          f"{cli.wikitext_block_size} tokens")
    ds = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")
    text = "\n\n".join(ds["text"])
    ids = ctx.tokenizer(text, add_special_tokens=False)["input_ids"]

    size = cli.wikitext_block_size
    n_full = len(ids) // size
    if n_full < cli.wikitext_blocks:
        raise ValueError(
            f"wikitext-2 test yields only {n_full} full blocks of {size} tokens; "
            f"--wikitext-blocks {cli.wikitext_blocks} is too many.")
    blocks = torch.tensor(ids[:n_full * size], dtype=torch.long).view(n_full, size)
    blocks = blocks[:cli.wikitext_blocks].clone()

    bos = ctx.tokenizer.bos_token_id
    if bos is not None:
        blocks[:, 0] = bos
    return _cache_blocks(ctx, blocks)


def _cache_blocks(ctx, blocks):
    ctx._wikitext_blocks = blocks
    return blocks


def pair_blocks(n: int, seed: int):
    """A fixed derangement of range(n) — a permutation with no fixed point."""
    import numpy as np

    if n < 2:
        raise ValueError("need at least 2 wikitext blocks to pair them")
    rng = np.random.default_rng(seed)
    for _ in range(1000):
        perm = rng.permutation(n)
        if not (perm == np.arange(n)).any():
            return perm
    raise RuntimeError("could not draw a derangement in 1000 attempts")


def wikitext_batches(ctx):
    """[(clean, corrupt, mask)] batches of paired blocks, on CPU."""
    blocks = load_wikitext_blocks(ctx)
    perm = pair_blocks(len(blocks), ctx.cli.wikitext_seed)
    partner = blocks[torch.as_tensor(perm.copy())]

    bs = ctx.cli.wikitext_batch_size
    out = []
    for i in range(0, len(blocks), bs):
        clean = blocks[i:i + bs]
        out.append((clean, partner[i:i + bs],
                    torch.ones_like(clean)))
    return out


def wikitext_stream_batches(ctx):
    """The same batches in Task.model_inputs shape, for the mean-bank collector."""
    return [{"input_ids": c, "corrupted_input_ids": x, "attention_mask": m}
            for c, x, m in wikitext_batches(ctx)]


# ==============================================================================
# PER-BATCH REDUCTIONS
# ==============================================================================

def _chunks(seq):
    for start in range(0, seq, _VOCAB_CHUNK):
        yield start, min(start + _VOCAB_CHUNK, seq)


def reference_log_probs(logits):
    """fp32 log-softmax of the full model's logits, chunked over the sequence.

    Held for the whole batch (one fp32 copy, ~1 GB at the default block/batch
    size) rather than recomputed inside every configuration: the point of the
    chunking is to avoid materialising *two* such tensors at once, not to avoid
    the reference one.
    """
    return {start: F.log_softmax(logits[:, start:stop].float(), dim=-1)
            for start, stop in _chunks(logits.shape[1])}


def _nll(logits, targets):
    """Summed NLL over positions 0..S-2, predicting 1..S-1."""
    nll_sum, n = 0.0, 0
    seq = logits.shape[1]
    for start, stop in _chunks(seq):
        last = min(stop, seq - 1)
        if last <= start:
            continue
        chunk = logits[:, start:last].float()
        tgt = targets[:, start:last]
        nll_sum += float(F.cross_entropy(
            chunk.reshape(-1, chunk.shape[-1]), tgt.reshape(-1), reduction="sum"))
        n += tgt.numel()
    return nll_sum, n


def _kl_and_nll(ablated_logits, full_log_probs, targets):
    """Per-token KL(full ‖ ablated), its sum of squares, and the ablated NLL.

    Uses the repo's KL convention exactly (dataset/std_llama.py:420-423):
    F.kl_div(log_softmax(ablated), log_softmax(full), log_target=True), summed
    over the vocabulary in fp32. The sum of squares is what gives kl_sem —
    per-token KL is heavy-tailed, and the SEM is what says whether a
    discovered-vs-null gap is real.
    """
    kl_sum = kl_sq = 0.0
    n_kl = 0
    for start, stop in _chunks(ablated_logits.shape[1]):
        log_q = F.log_softmax(ablated_logits[:, start:stop].float(), dim=-1)
        kl = F.kl_div(log_q, full_log_probs[start], reduction="none",
                      log_target=True).sum(-1)
        kl_sum += float(kl.sum())
        kl_sq += float((kl ** 2).sum())
        n_kl += kl.numel()
        del log_q, kl

    nll_sum, n_nll = _nll(ablated_logits, targets)
    return kl_sum, kl_sq, n_kl, nll_sum, n_nll


class _Accumulator:
    def __init__(self):
        self.kl_sum = self.kl_sq = 0.0
        self.n_kl = 0
        self.nll_sum = 0.0
        self.n_nll = 0

    def add(self, kl_sum, kl_sq, n_kl, nll_sum, n_nll):
        self.kl_sum += kl_sum
        self.kl_sq += kl_sq
        self.n_kl += n_kl
        self.nll_sum += nll_sum
        self.n_nll += n_nll

    def result(self, full_nll_sum, full_n_nll):
        mean_kl = self.kl_sum / max(self.n_kl, 1)
        var = max(self.kl_sq / max(self.n_kl, 1) - mean_kl ** 2, 0.0)
        sem = (var / max(self.n_kl, 1)) ** 0.5
        mean_nll = self.nll_sum / max(self.n_nll, 1)
        full_mean_nll = full_nll_sum / max(full_n_nll, 1)
        return {
            "kl_per_token": mean_kl,
            "kl_sem": sem,
            "ppl_ablated": math.exp(min(mean_nll, 50.0)),
            "ppl_full": math.exp(min(full_mean_nll, 50.0)),
            "ppl_ratio": math.exp(min(mean_nll - full_mean_nll, 50.0)),
            "n_tokens": self.n_kl,
        }


# ==============================================================================
# THE HARNESS
# ==============================================================================

def collateral_damage(ctx, configs, hook=None, desc="wikitext") -> dict:
    """Run every gate configuration over the wikitext stream.

    `configs` is [(label, masks)]. Returns {label: {kl_per_token, kl_sem,
    ppl_full, ppl_ablated, ppl_ratio, n_tokens}}.
    """
    batches = wikitext_batches(ctx)
    accs = {label: _Accumulator() for label, _ in configs}
    full_nll_sum, full_n_nll = 0.0, 0

    n_forwards = len(batches) * (len(configs) + 1)
    bar = tqdm(total=n_forwards, desc=f"{desc} ({len(configs)} configs)",
               leave=False)

    with torch.no_grad(), ablation_hook(ctx.node_model, hook):
        for clean, corrupt, mask in batches:
            clean = clean.to(ctx.device)
            corrupt = corrupt.to(ctx.device)
            mask = mask.to(ctx.device)
            targets = clean[:, 1:]

            full_logits = ctx.reference_logits(clean, mask)
            full_log_probs = reference_log_probs(full_logits)
            nll_sum, n_nll = _nll(full_logits, targets)
            full_nll_sum += nll_sum
            full_n_nll += n_nll
            bar.update(1)

            for label, masks in configs:
                ctx.apply_circuit(masks)
                logits = ctx.node_model(input_ids=clean,
                                        corrupted_input_ids=corrupt,
                                        attention_mask=mask,
                                        use_cache=False).logits
                accs[label].add(*_kl_and_nll(logits, full_log_probs, targets))
                bar.update(1)

            del full_logits, full_log_probs

    bar.close()
    ctx.apply_circuit(ctx.circuit_masks)
    return {label: accs[label].result(full_nll_sum, full_n_nll)
            for label, _ in configs}
