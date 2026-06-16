"""
config.py — pruning configurations and per-(model, task) defaults.

`NodePruningConfig` enumerates every prunable *granularity* (the structural
level at which the L0 gates operate) together with its sparsity coefficient
`lambda_*`. `EdgeConfig` controls the edge-pruning phase.

Defaults are uniform: every structural lambda is 1.0 and both pruning lambdas
(node/edge sparsity) are 0.95, regardless of model or task. Only the remaining
training hyperparameters (epochs, batch, lr, samples, sequence length) vary
per (family, task) via `default_hyperparams`. Every field is overridable from
the command line (see train.py).
"""

from dataclasses import dataclass, fields


# ==============================================================================
# Granularity / node-pruning configuration
# ==============================================================================

@dataclass
class NodePruningConfig:
    """
    One toggle (`prune_*`) and one sparsity weight (`lambda_*`) per granularity.

    Granularities (coarse -> fine):
      full_layers        — drop an entire transformer block
      attention_blocks   — drop a layer's whole attention sublayer
      mlp_blocks         — drop a layer's whole MLP sublayer
      attention_heads    — drop individual attention heads
      attention_neurons  — drop individual attention head dimensions
      mlp_hidden         — drop individual MLP hidden units
      mlp_output         — drop individual MLP output dimensions
      embedding          — drop the embedding contribution
    """
    init_value: float = 0.5
    sparsity_warmup_steps: int = 1000
    depth_penalty_scaling: float = 0.0

    prune_attention_heads: bool = True
    lambda_attention_heads: float = 1.0
    prune_attention_neurons: bool = True
    lambda_attention_neurons: float = 1.0
    prune_attention_blocks: bool = True
    lambda_attention_blocks: float = 1.0

    prune_mlp_hidden: bool = True
    lambda_mlp_hidden: float = 1.0
    prune_mlp_output: bool = True
    lambda_mlp_output: float = 1.0
    prune_mlp_blocks: bool = True
    lambda_mlp_blocks: float = 1.0

    prune_full_layers: bool = False
    lambda_full_layers: float = 1.0
    prune_embedding: bool = False
    lambda_embedding: float = 1.0


@dataclass
class EdgeConfig:
    """Edge-pruning phase configuration. The edge sparsity/fidelity trade-off is
    governed entirely by --edge-lambda-sparsity (there is a single edge
    granularity, so no separate per-granularity edge lambda is needed)."""
    sparsity_warmup_steps: int = 500
    include_output_edges: bool = True


# Names of every granularity exposed as CLI flags (`--prune-*` / `--lambda-*`).
GRANULARITIES = [
    "attention_heads",
    "attention_neurons",
    "attention_blocks",
    "mlp_hidden",
    "mlp_output",
    "mlp_blocks",
    "full_layers",
    "embedding",
]


# ==============================================================================
# Per-(family, task) defaults — faithful to the original scripts
# ==============================================================================

# Default sparsity-vs-fidelity trade-off (the "pruning lambda") for each phase.
# Uniform across models/tasks; override with --node/--edge-lambda-sparsity.
DEFAULT_NODE_LAMBDA_SPARSITY = 0.95
DEFAULT_EDGE_LAMBDA_SPARSITY = 0.95

# Per-(family, task) training hyperparameters (epochs / batch / lr / samples /
# sequence length) used as argparse fallbacks. Lambdas are NOT here — structural
# lambdas default to 1.0 (NodePruningConfig) and the pruning lambdas to 0.95.
_HYPERPARAMS = {
    ("gpt2", "ioi"): dict(node_epochs=500, edge_epochs=300, batch_size=32,
                          max_seq_length=64, lr=3e-2,
                          train_samples=400, val_samples=200, test_samples=1000),
    ("gpt2", "gp"): dict(node_epochs=500, edge_epochs=300, batch_size=64,
                         max_seq_length=32, lr=3e-1,
                         train_samples=100000, val_samples=10000, test_samples=10000),
    ("gpt2", "gt"): dict(node_epochs=250, edge_epochs=300, batch_size=16,
                         max_seq_length=32, lr=5e-2,
                         train_samples=200, val_samples=200, test_samples=1000),
    ("llama", "ioi"): dict(node_epochs=500, edge_epochs=300, batch_size=16,
                           max_seq_length=64, lr=3e-2,
                           train_samples=200, val_samples=200, test_samples=1000),
    ("llama", "gp"): dict(node_epochs=500, edge_epochs=300, batch_size=64,
                          max_seq_length=64, lr=3e-1,
                          train_samples=100000, val_samples=10000, test_samples=10000),
}


def default_node_config(family: str, task: str) -> NodePruningConfig:
    """Default node config: every structural lambda is 1.0. Override individual
    granularities from the CLI (--lambda-<granularity>)."""
    return NodePruningConfig()


def default_hyperparams(family: str, task: str) -> dict:
    """Return the per-(family, task) training hyperparameters (no lambdas)."""
    if (family, task) not in _HYPERPARAMS:
        raise ValueError(f"No default hyperparameters for ({family!r}, {task!r})")
    return dict(_HYPERPARAMS[(family, task)])


def config_field_names() -> list:
    """All NodePruningConfig field names (for CLI override plumbing)."""
    return [f.name for f in fields(NodePruningConfig)]
