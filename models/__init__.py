"""
models package — model registry + a family-dispatching ModelAdapter.

The adapter hides every GPT-2 vs Llama difference behind one interface so the
training loops in pruning.py stay model-agnostic:

  * loading the frozen reference model and tokenizer,
  * building the node-prunable and edge-prunable models (correct dtype, which
    parameters are trainable, dropout disabled),
  * finalizing a node model before analysis,
  * whether to pre-cache the reference logits (done for Llama to avoid running
    a second large forward pass each step),
  * reporting layer / head counts for dense-edge accounting.

The four CLI model names map to a HuggingFace id + a family:

    gpt2     -> gpt2                      (gpt2)
    gpt2-xl  -> gpt2-xl                   (gpt2)
    llama-1b -> meta-llama/Llama-3.2-1B   (llama)
    llama-8b -> meta-llama/Llama-3.1-8B   (llama)
"""

import torch

from analysis import disable_dropout
from config import NodePruningConfig, EdgeConfig

# name -> (huggingface_id, family)
MODEL_REGISTRY = {
    "gpt2":     ("gpt2",                    "gpt2"),
    "gpt2-xl":  ("gpt2-xl",                 "gpt2"),
    "llama-1b": ("meta-llama/Llama-3.2-1B", "llama"),
    "llama-8b": ("meta-llama/Llama-3.1-8B", "llama"),
}

# HardConcreteGate parameter name patterns — used to select trainable gate
# params on Llama without matching the SwiGLU `gate_proj` weights.
_LLAMA_GATE_PATTERNS = ("_gates.", "_gate.", "embedding_gate.", "layer_gates.")


def list_models():
    return list(MODEL_REGISTRY.keys())


class ModelAdapter:
    """Encapsulates all family-specific model handling."""

    def __init__(self, model_name: str, hf_token=None):
        if model_name not in MODEL_REGISTRY:
            raise ValueError(
                f"Unknown model {model_name!r}. Choose from {list_models()}."
            )
        self.model_name = model_name
        self.hf_id, self.family = MODEL_REGISTRY[model_name]
        self.hf_token = hf_token
        self.is_llama = self.family == "llama"
        # Llama: pre-cache reference logits to avoid a second big forward/step.
        self.cache_target_logits = self.is_llama

    # ---- common kwargs -------------------------------------------------
    def _hf_model_kwargs(self):
        kw = {}
        if self.is_llama:
            kw["torch_dtype"] = torch.bfloat16
            if self.hf_token:
                kw["token"] = self.hf_token
        return kw

    # ---- tokenizer & reference model -----------------------------------
    def load_tokenizer(self):
        if self.is_llama:
            from transformers import AutoTokenizer
            tok = AutoTokenizer.from_pretrained(self.hf_id, token=self.hf_token)
            if tok.pad_token is None:
                tok.pad_token = tok.eos_token
                tok.pad_token_id = tok.eos_token_id
        else:
            from transformers import GPT2Tokenizer
            tok = GPT2Tokenizer.from_pretrained(self.hf_id)
            if tok.pad_token is None:
                tok.pad_token = tok.eos_token
        return tok

    def load_full_model(self, device):
        if self.is_llama:
            from transformers import LlamaForCausalLM
            model = LlamaForCausalLM.from_pretrained(
                self.hf_id, **self._hf_model_kwargs()
            ).to(device).eval()
        else:
            from transformers import GPT2LMHeadModel
            model = GPT2LMHeadModel.from_pretrained(self.hf_id).to(device).eval()
        for p in model.parameters():
            p.requires_grad = False
        return model

    # ---- node-prunable model -------------------------------------------
    def build_node_model(self, node_cfg: NodePruningConfig, device):
        if self.is_llama:
            from models.llama_node import PrunableLlamaForCausalLM
            model = PrunableLlamaForCausalLM.from_pretrained_with_pruning(
                self.hf_id, node_cfg, **self._hf_model_kwargs()
            ).to(device).eval()
            disable_dropout(model)
            for name, param in model.named_parameters():
                if any(p in name for p in _LLAMA_GATE_PATTERNS):
                    param.requires_grad = True
                    param.data = param.data.float()   # train gates in fp32
                else:
                    param.requires_grad = False
        else:
            from models.gpt2_node import PrunableGPT2LMHeadModel
            model = PrunableGPT2LMHeadModel.from_pretrained_with_pruning(
                self.hf_id, node_cfg
            ).to(device).eval()
            disable_dropout(model)
            for name, param in model.named_parameters():
                param.requires_grad = "gate" in name
        return model

    def finalize_node_model(self, model, node_cfg: NodePruningConfig):
        """Enable full-layer pruning for the final analysis (GPT-2 only)."""
        if not self.is_llama and hasattr(model, "set_pruning_config"):
            node_cfg.prune_full_layers = True
            model.set_pruning_config(node_cfg)

    # ---- edge-prunable model -------------------------------------------
    def build_edge_model(self, active_heads, active_mlps, edge_cfg: EdgeConfig, device):
        if self.is_llama:
            from models.llama_edge import EdgePrunableLlama, EdgePruningConfig
            cfg = EdgePruningConfig(
                sparsity_warmup_steps=edge_cfg.sparsity_warmup_steps,
                include_output_edges=edge_cfg.include_output_edges,
            )
            model = EdgePrunableLlama.from_pretrained_with_edges(
                self.hf_id, active_heads, active_mlps, cfg, **self._hf_model_kwargs()
            ).to(device)
            disable_dropout(model)
            for param in model.parameters():
                if param.requires_grad:
                    param.data = param.data.float()
        else:
            from models.gpt2_edge import EdgePrunableGPT2, EdgePruningConfig
            cfg = EdgePruningConfig(
                sparsity_warmup_steps=edge_cfg.sparsity_warmup_steps,
                include_output_edges=edge_cfg.include_output_edges,
            )
            model = EdgePrunableGPT2.from_pretrained_with_edges(
                self.hf_id, active_heads, active_mlps, cfg
            ).to(device)
            disable_dropout(model)
        return model

    # ---- model geometry (for dense-edge accounting) --------------------
    @staticmethod
    def num_layers(model):
        c = model.config
        return getattr(c, "num_hidden_layers", None) or c.n_layer

    @staticmethod
    def num_heads(model):
        c = model.config
        return getattr(c, "num_attention_heads", None) or c.n_head
