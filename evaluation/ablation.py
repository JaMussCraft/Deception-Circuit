"""
evaluation/ablation.py — what fills an ablated node.

Every gate in `models/llama_node.py` computes

    out = gate * clean + (1 - gate) * reference

and `_ablation_ref` decides what `reference` is:

    interchange  the corrupted-stream activation (the training-time behaviour;
                 no hook installed at all, so the forward is bit-identical)
    zero         a broadcast scalar zero
    mean         the site's mean activation over a prompt distribution

The reference is only ever the *mixing* value — the corrupted stream itself is
never perturbed. That matters here because it is what makes the mean bank
reusable: the corrupted stream is a pure function of `corrupted_input_ids` and
`attention_mask`, with no gate value anywhere in its path, so the bank is
circuit-independent and can be collected once and shared across all ~100 gate
configurations an evaluation run visits.

Site reference tensors and their mean shapes (Llama-3.1-8B numbers):

    attn_head / attn_neuron   corr_attn_out (pre-o_proj)     [B,S,32,128] -> [32,128]
    attn_block                corrupted_attn_output          [B,S,4096]   -> [4096]
    mlp_hidden                corrupted_act                  [B,S,14336]  -> [14336]
    mlp_output / mlp_block    corrupted_output (post-down)   [B,S,4096]   -> [4096]
    layer                     hidden_states_corrupted        [B,S,4096]   -> [4096]

Two pairs alias, but all seven keys are kept: the collector is site-agnostic
(reduce batch and sequence, keep the trailing dims), so no site needs special
casing and a new site needs no code. The whole bank is ~4.4 MB.
"""

from __future__ import annotations

from contextlib import contextmanager

import torch
from tqdm import tqdm

from models.llama_node import (ABLATION_SITES, clear_ablation_hook,
                               install_ablation_hook)

ABLATION_SCHEMES = ("interchange", "zero", "mean")


# ==============================================================================
# WHICH SITES A MODEL ACTUALLY USES
# ==============================================================================

def required_sites(model) -> dict:
    """{site: sorted layer indices} for every gate this model actually has."""
    sites = {s: [] for s in ABLATION_SITES}
    for i, block in enumerate(model.model.layers):
        if getattr(block.attn, "head_gates", None) is not None:
            sites["attn_head"].append(i)
        if getattr(block.attn, "neuron_gates", None) is not None:
            sites["attn_neuron"].append(i)
        if getattr(block, "attention_block_gate", None) is not None:
            sites["attn_block"].append(i)
        if getattr(block.mlp, "hidden_gates", None) is not None:
            sites["mlp_hidden"].append(i)
        if getattr(block.mlp, "output_gates", None) is not None:
            sites["mlp_output"].append(i)
        if getattr(block, "mlp_block_gate", None) is not None:
            sites["mlp_block"].append(i)
        if getattr(model, "layer_gates", None) is not None:
            sites["layer"].append(i)
    return {s: ls for s, ls in sites.items() if ls}


# ==============================================================================
# HOOKS
# ==============================================================================

class ZeroHook:
    """Zero-ablation: the reference is a 0-dim zero, which broadcasts to any
    site's shape."""

    def __init__(self):
        self._cache = {}

    def __call__(self, module, corrupted, site):
        key = (corrupted.dtype, corrupted.device)
        t = self._cache.get(key)
        if t is None:
            t = torch.zeros((), dtype=corrupted.dtype, device=corrupted.device)
            self._cache[key] = t
        return t


class MeanHook:
    """Mean-ablation: the reference is the site's mean activation.

    The mean is broadcast to every position, pads included. That is harmless
    under right padding: pad positions are causally invisible to the prediction
    position, and every metric here reads a real position.
    """

    def __init__(self, bank: dict):
        self.bank = bank
        self._views = {}

    def __call__(self, module, corrupted, site):
        layer = getattr(module, "layer_idx", None)
        key = (site, layer, corrupted.dtype, corrupted.device)
        view = self._views.get(key)
        if view is None:
            try:
                mean = self.bank[site][layer]
            except KeyError:
                raise KeyError(
                    f"mean bank has no entry for site {site!r} layer {layer!r} "
                    f"(have {sorted(self.bank)}). Collect the bank with the same "
                    f"model the hook is installed on.")
            view = mean.reshape((1, 1) + tuple(mean.shape)).to(
                dtype=corrupted.dtype, device=corrupted.device)
            self._views[key] = view
        return view

    def validate(self, model) -> None:
        """Fail at install time, not four layers into a forward pass."""
        missing = []
        for site, layers in required_sites(model).items():
            for l in layers:
                if site not in self.bank or l not in self.bank[site]:
                    missing.append(f"{site}[{l}]")
        if missing:
            raise KeyError(
                f"mean bank is missing {len(missing)} site/layer entries, e.g. "
                f"{missing[:8]}")


class MeanCollector:
    """Accumulates per-site means. Returns the reference unchanged, so the
    forward it rides along on is exactly the forward that would have run.

    fp32 accumulation is required: bf16 sums over ~90K positions drift badly.
    """

    def __init__(self):
        self.sums = {}       # site -> layer -> fp32 tensor over the trailing dims
        self.counts = {}     # site -> layer -> token count
        self._mask = None

    def set_mask(self, mask) -> None:
        """The [B, S] attention mask for the forward about to run."""
        self._mask = mask

    def __call__(self, module, corrupted, site):
        layer = getattr(module, "layer_idx", None)
        mask = self._mask
        if mask is None:
            mask = torch.ones(corrupted.shape[:2], device=corrupted.device)
        view = mask.reshape(mask.shape[0], mask.shape[1],
                            *([1] * (corrupted.dim() - 2))).float()

        # Site-agnostic reduction: collapse batch and sequence, keep every
        # trailing dim. That is why a new site needs no code here.
        contrib = (corrupted.float() * view).sum(dim=(0, 1))
        n = float(mask.sum())

        site_sums = self.sums.setdefault(site, {})
        site_counts = self.counts.setdefault(site, {})
        if layer in site_sums:
            site_sums[layer] += contrib
            site_counts[layer] += n
        else:
            site_sums[layer] = contrib
            site_counts[layer] = n
        return corrupted

    def bank(self) -> dict:
        return {site: {l: s / max(self.counts[site][l], 1.0)
                       for l, s in layers.items()}
                for site, layers in self.sums.items()}

    def n_tokens(self) -> float:
        for layers in self.counts.values():
            for n in layers.values():
                return n
        return 0.0


def make_hook(scheme: str, bank=None, model=None):
    """The hook for an ablation scheme (None means interchange / no hook)."""
    if scheme not in ABLATION_SCHEMES:
        raise ValueError(f"unknown ablation scheme {scheme!r}; "
                         f"choose from {list(ABLATION_SCHEMES)}")
    if scheme == "interchange":
        return None
    if scheme == "zero":
        return ZeroHook()
    if bank is None:
        raise ValueError("--ablation mean needs a mean bank")
    hook = MeanHook(bank)
    if model is not None:
        hook.validate(model)
    return hook


@contextmanager
def ablation_hook(model, hook):
    """Install `hook` for the duration of the block (None = interchange)."""
    if hook is None:
        clear_ablation_hook(model)
        try:
            yield 0
        finally:
            pass
        return
    n = install_ablation_hook(model, hook)
    try:
        yield n
    finally:
        clear_ablation_hook(model)


# ==============================================================================
# MEAN BANK COLLECTION
# ==============================================================================

def _forward_for_bank(model, collector, input_ids, corrupted_input_ids, attention_mask):
    collector.set_mask(attention_mask)
    with torch.no_grad():
        model(input_ids=input_ids,
              corrupted_input_ids=corrupted_input_ids,
              attention_mask=attention_mask,
              use_cache=False)


def collect_mean_bank(model, stream_batches, *, device, source: str = "pooled",
                      desc: str = "Mean bank", verbose: bool = True) -> dict:
    """Site means over the corrupted stream of `stream_batches`.

    `stream_batches` is an iterable of dicts with input_ids / corrupted_input_ids
    / attention_mask (the shape `Task.model_inputs` already produces). It is
    consumed once per requested pass, so pass a list, not a generator, unless
    source is "clean" or "corrupt".

    source:
      corrupt  one pass — the hook sees corrupt-prompt activations
      clean    one pass with the two streams swapped — clean-prompt activations
      pooled   both passes into one bank, equal token weight (the default:
               site means depend on the input distribution, and an evaluation
               reads both streams' worth of behaviour)

    Gate values never touch the corrupted stream, so the bank does not depend on
    which circuit is loaded.
    """
    if source not in ("pooled", "clean", "corrupt"):
        raise ValueError(f"mean source must be pooled/clean/corrupt, got {source!r}")

    passes = {"corrupt": [False], "clean": [True], "pooled": [False, True]}[source]
    collector = MeanCollector()

    with ablation_hook(model, collector):
        for swap in passes:
            label = f"{desc} ({'clean' if swap else 'corrupt'} prompts)"
            iterator = tqdm(stream_batches, desc=label, leave=False) if verbose \
                else stream_batches
            for batch in iterator:
                clean = batch["input_ids"].to(device)
                corrupt = batch["corrupted_input_ids"].to(device)
                mask = batch["attention_mask"].to(device)
                if swap:
                    clean, corrupt = corrupt, clean
                _forward_for_bank(model, collector, clean, corrupt, mask)

    return collector.bank()
