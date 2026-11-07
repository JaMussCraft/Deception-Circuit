"""Tiny CPU models shared by the test modules.

2 layers, 64 hidden, 4 heads, vocab 101 — small enough that a full forward is
sub-millisecond, large enough that GQA, per-head gating and the MLP granularities
are all exercised.
"""

from __future__ import annotations

import torch
from transformers import LlamaConfig, LlamaForCausalLM

from config import NodePruningConfig
from models.llama_node import PrunableLlamaForCausalLM, apply_pruning_wrappers

TINY = {
    "layers": 2,
    "hidden": 64,
    "heads": 4,
    "kv_heads": 2,
    "head_dim": 16,
    "intermediate": 128,
    "vocab": 101,
    "max_pos": 1024,
}


def tiny_config(num_hidden_layers=None, attn_implementation=None):
    return LlamaConfig(
        hidden_size=TINY["hidden"],
        num_hidden_layers=num_hidden_layers or TINY["layers"],
        num_attention_heads=TINY["heads"],
        num_key_value_heads=TINY["kv_heads"],
        intermediate_size=TINY["intermediate"],
        vocab_size=TINY["vocab"],
        max_position_embeddings=TINY["max_pos"],
        attn_implementation=attn_implementation,
    )


def build_tiny_pair(node_cfg=None, num_hidden_layers=None, seed=0,
                    attn_implementation=None):
    """(plain LlamaForCausalLM, prunable model carrying identical weights)."""
    cfg = tiny_config(num_hidden_layers, attn_implementation)
    torch.manual_seed(seed)
    plain = LlamaForCausalLM(cfg).eval()

    pruned = PrunableLlamaForCausalLM(cfg)
    pruned.load_state_dict(plain.state_dict())
    apply_pruning_wrappers(pruned, node_cfg or NodePruningConfig())
    pruned.eval()
    return plain, pruned
