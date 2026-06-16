# Node-Pruning for Circuit Discovery

A minimal, self-contained codebase for **two-phase circuit discovery** in
transformer language models. Given a task, it finds a small sub-network (a
*circuit*) that reproduces the full model's behaviour, in two phases:

1. **Node pruning** — learn which structural components matter (attention heads,
   attention/MLP neurons, whole sublayers, …) using differentiable L0
   (Hard-Concrete) gates.
2. **Edge pruning** — on the surviving nodes, learn which *connections* between
   them matter (source → query / key / value / MLP / output edges).

Both phases freeze the base model and train only the gates against a
KL-to-the-full-model objective plus an optional task-margin term.

One entry point — `train.py` — drives every supported model and task, with
flags to toggle edge pruning, choose granularities, and set every sparsity
coefficient (`lambda_*`).

## Supported models and tasks

| `--model`   | HuggingFace id              | `--task ioi` | `--task gp` | `--task gt` |
|-------------|-----------------------------|:------------:|:-----------:|:-----------:|
| `gpt2`      | `gpt2`                      | ✅ | ✅ | ✅ |
| `gpt2-xl`   | `gpt2-xl`                   | ✅ | ✅ | ✅ |
| `llama-1b`  | `meta-llama/Llama-3.2-1B`   | ✅ | ✅ | ❌ |
| `llama-8b`  | `meta-llama/Llama-3.1-8B`   | ✅ | ✅ | ❌ |

- **IOI** — Indirect Object Identification.
- **GP** — Gendered-Pronoun prediction.
- **GT** — Greater-Than. Relies on GPT-2's single-token two-digit years, so it
  is **not supported for Llama** (the program prints a message and exits).

Llama models are gated on HuggingFace and require an access token (see below);
they load in bfloat16 and pre-cache the reference logits to fit in memory.

## Install

```bash
pip install -r requirements.txt
```

Requires `torch >= 2.7` and `transformers >= 4.52` (the GPT-2 node model uses
`transformers.masking_utils`).

On a Compute Canada / SLURM cluster the dependencies come from modules + a venv:

```bash
module load StdEnv/2023 python-build-bundle/2025a gcc arrow
source /path/to/project_env/bin/activate
```

## Quick start

```bash
# Defaults: --model gpt2 --task ioi, edge pruning ON.
# Node pruning + edge pruning on GPT-2 / IOI:
python train.py

# Node pruning only (no Phase 2)
python train.py --model gpt2 --task gp --no-edge-pruning

# Edge pruning only, reusing previously saved nodes
python train.py --model gpt2 --task ioi --skip-node-pruning \
  --node-checkpoint outputs/gpt2_ioi/active_nodes.json

# Llama 3.2 1B on IOI (needs HF token)
python train.py --model llama-1b --task ioi --hf-token hf_xxx

# Greater-Than on GPT-2-XL
python train.py --model gpt2-xl --task gt

# Fast smoke test
python train.py --model gpt2 --task ioi --node-epochs 2 --edge-epochs 2 \
  --train-samples 64 --val-samples 32 --test-samples 64 --batch-size 16
```

## Controlling granularities

Node pruning operates at several **granularities**, each independently
toggleable and weighted. Enable/disable a granularity with
`--prune-<name>` / `--no-prune-<name>`, and set its sparsity weight with
`--lambda-<name>`:

```bash
# Prune only attention heads and MLP blocks; tune their pressures
python train.py --model gpt2 --task ioi \
  --no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output \
  --lambda-attention-heads 2.0 --lambda-mlp-blocks 0.5
```

Granularities (coarse → fine): `full_layers`, `attention_blocks`, `mlp_blocks`,
`attention_heads`, `attention_neurons`, `mlp_hidden`, `mlp_output`, `embedding`.

The overall sparsity/fidelity trade-off per phase — the **pruning lambdas** — is
set by `--node-lambda-sparsity` and `--edge-lambda-sparsity` (both default
**0.95**). Edge pruning has a single granularity, so `--edge-lambda-sparsity`
alone governs edge-gate pressure. See `python train.py --help` for the full list.

**Defaults**: every structural lambda defaults to **1.0** and the two pruning
lambdas to **0.95**, uniformly across models and tasks. The remaining training
hyperparameters (epochs, batch size, learning rate, sample counts, sequence
length) keep sensible per-(model, task) values in `config.py`. Override any of
them from the CLI.

## Data

`--data-dir` (default `./data/datasets`) holds one folder per task:
`ioi/`, `gp/`, `gt/`, each a HuggingFace `save_to_disk` dataset with
`train` / `validation` / `test` splits.

- **GP** and **GT** datasets are included under `data/datasets/`.
- **IOI** is large and not committed. Provide it at `data/datasets/ioi`
  (e.g. symlink an existing copy) or point `--data-dir` at a directory that
  contains it. The Llama IOI variant is generated synthetically and needs no
  files.

## Outputs

Each run writes to `--output-dir` (default `outputs/<model>_<task>/`):

- `active_nodes.json` — the discovered surviving heads/MLPs (reusable via
  `--skip-node-pruning`).
- `results.json` — baseline / node / edge fidelity metrics, dense- and
  active-edge counts, and the per-granularity node summary.

The console prints the per-granularity node report, dense-edge accounting, the
edge-pruning summary, a fidelity comparison table, the end-to-end edge
compression, and a GPU memory map.

## Repository layout

```
train.py        Unified CLI: parse flags -> node phase -> edge phase -> report
config.py       NodePruningConfig / EdgeConfig + per-(model, task) defaults
pruning.py      Shared node/edge training loops + GPU memory tracker
analysis.py     Node circuit finalisation + edge analysis / dense-edge counting
l0.py           Hard-Concrete L0 gate
models/         Model registry + ModelAdapter, and the prunable model classes
                (gpt2_node, gpt2_edge, llama_node, llama_edge)
tasks/          Task interface + ioi / gp / gt (objective, data, evaluation)
dataset/        Vendored dataset builders & task-specific evaluation
```

## How it fits together

`train.py` builds a `ModelAdapter` (hides GPT-2 vs Llama: dtype, which params
are trainable, logit caching) and a `Task` (hides IOI/GP/GT: data, objective,
evaluation metrics). `pruning.py` then runs one shared loop for each phase,
so adding a model or task means adding one small module — not another copy of
the training script.
