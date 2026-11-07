"""Open-ended generation from an ablated circuit — the loop's two invariants.

The tiny 2-layer Llama with random weights writes nonsense, which is fine: what
is being checked here is mechanical, not linguistic.

  * every configuration produces exactly `--gen-new-tokens` new tokens, and the
    whole sequence is re-forwarded each step (no KV cache, because the
    corrupted stream cannot carry one)
  * the corrupted stream is never the clean stream — if it were, an interchange
    ablation would be a silent no-op and the "knockout" sample would come back
    identical to the full model's
"""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from analysis import apply_node_masks, open_all_gates
from evaluation import generation as G
from evaluation.masks import knockout_masks
from tests.fakes import FakeWordTokenizer
from tests.helpers import TINY, build_tiny_pair

N_BLOCKS = 4
BLOCK_SIZE = 12
NEW_TOKENS = 3


def circuit_masks_for(model, seed=0, density=0.5):
    """A hierarchy-valid mask object matching the tiny model's geometry."""
    rng = np.random.default_rng(seed)
    n_layers = len(model.model.layers)
    masks = {}
    for key, size in (("attention_neurons", TINY["heads"] * TINY["head_dim"]),
                      ("mlp_hidden", TINY["intermediate"]),
                      ("mlp_output", TINY["hidden"])):
        masks[key] = {str(l): (rng.random(size) < density).astype(np.uint8)
                      for l in range(n_layers)}
    heads, attn_blocks, mlp_blocks = {}, [], []
    for l in range(n_layers):
        key = str(l)
        by_head = masks["attention_neurons"][key].reshape(
            TINY["heads"], TINY["head_dim"]).any(axis=1)
        heads[key] = by_head.astype(np.uint8)
        attn_blocks.append(int(by_head.any()))
        mlp_blocks.append(int(masks["mlp_hidden"][key].any()
                              or masks["mlp_output"][key].any()))
    masks["attention_heads"] = heads
    masks["attention_blocks"] = np.asarray(attn_blocks, dtype=np.uint8)
    masks["mlp_blocks"] = np.asarray(mlp_blocks, dtype=np.uint8)
    # No "embedding" key: the default NodePruningConfig gives the tiny model no
    # embedding gate, and apply_node_masks refuses masks it cannot place.
    return masks


class StubContext:
    """Only the EvalContext surface `generation_examples` actually touches."""

    def __init__(self, model, blocks):
        self.node_model = model
        self.tokenizer = FakeWordTokenizer()
        self.device = "cpu"
        self.cli = SimpleNamespace(ablation="interchange", wikitext_seed=0,
                                   wikitext_blocks=N_BLOCKS,
                                   wikitext_block_size=BLOCK_SIZE)
        self._wikitext_blocks = blocks
        self.circuit_masks = circuit_masks_for(model)
        self.knockout_masks = knockout_masks(self.circuit_masks, "finest")

    def hook_for(self, bank_name="task"):
        return None                      # interchange installs no hook

    @contextmanager
    def all_gates_open(self):
        open_all_gates(self.node_model)
        try:
            yield self.node_model
        finally:
            apply_node_masks(self.node_model, self.circuit_masks)

    @contextmanager
    def circuit(self, masks, verify=False):
        apply_node_masks(self.node_model, masks)
        try:
            yield self.node_model
        finally:
            apply_node_masks(self.node_model, self.circuit_masks)


class Recorder:
    """Records the (clean, corrupt) ids of every forward the loop performs."""

    def __init__(self, model):
        self.calls = []
        self.handle = model.register_forward_pre_hook(self, with_kwargs=True)

    def __call__(self, module, args, kwargs):
        self.calls.append((kwargs["input_ids"].clone(),
                           kwargs["corrupted_input_ids"].clone()))
        return None


@pytest.fixture
def ctx():
    _, pruned = build_tiny_pair()
    g = torch.Generator().manual_seed(7)
    blocks = torch.randint(2, TINY["vocab"], (N_BLOCKS, BLOCK_SIZE),
                           generator=g)
    context = StubContext(pruned, blocks)
    apply_node_masks(pruned, context.circuit_masks)
    return context


def test_every_config_generates_the_requested_number_of_tokens(ctx):
    payload = G.generation_examples(ctx, n_examples=2, new_tokens=NEW_TOKENS)

    assert payload["n_examples"] == 2
    assert payload["new_tokens"] == NEW_TOKENS
    assert payload["prompt_tokens"] == BLOCK_SIZE   # the block is shorter than PROMPT_TOKENS
    assert len(payload["examples"]) == 2
    for example in payload["examples"]:
        assert set(example["continuations"]) == set(G.CONFIG_ORDER)
        for text in example["continuations"].values():
            assert len(text.split()) == NEW_TOKENS


def test_the_sequence_grows_one_token_per_forward_with_no_cache(ctx):
    recorder = Recorder(ctx.node_model)
    try:
        G.generation_examples(ctx, n_examples=2, new_tokens=NEW_TOKENS)
    finally:
        recorder.handle.remove()

    assert len(recorder.calls) == len(G.CONFIG_ORDER) * NEW_TOKENS
    per_config = NEW_TOKENS
    for c in range(len(G.CONFIG_ORDER)):
        lengths = [clean.shape[1] for clean, _ in
                   recorder.calls[c * per_config:(c + 1) * per_config]]
        # The whole prompt is re-forwarded every step: 12, 13, 14 — not 12, 1, 1.
        assert lengths == [BLOCK_SIZE + i for i in range(NEW_TOKENS)]


def test_the_corrupted_stream_is_never_the_clean_stream(ctx):
    recorder = Recorder(ctx.node_model)
    try:
        G.generation_examples(ctx, n_examples=2, new_tokens=NEW_TOKENS)
    finally:
        recorder.handle.remove()

    assert recorder.calls
    for clean, corrupt in recorder.calls:
        assert corrupt.shape == clean.shape
        assert not torch.equal(corrupt, clean)
        # Per-row, too: a derangement gives every example a different partner.
        for row in range(clean.shape[0]):
            assert not torch.equal(corrupt[row], clean[row])


def test_the_corrupted_stream_is_tiled_when_the_block_runs_out(ctx):
    """total = 12 prompt + 3 new > 12-token blocks, so the partner is repeated."""
    recorder = Recorder(ctx.node_model)
    try:
        G.generation_examples(ctx, n_examples=2, new_tokens=NEW_TOKENS)
    finally:
        recorder.handle.remove()

    _, corrupt = recorder.calls[-1]
    assert corrupt.shape[1] == BLOCK_SIZE + NEW_TOKENS - 1
    # The tail is the head of the same partner block coming round again.
    assert torch.equal(corrupt[:, BLOCK_SIZE:],
                       corrupt[:, :corrupt.shape[1] - BLOCK_SIZE])
