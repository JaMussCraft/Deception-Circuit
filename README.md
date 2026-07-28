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
python train.py --model gpt2 --task gp --node-epochs 12 --edge-epochs 2 \
  --train-samples 64 --val-samples 32 --test-samples 64 --batch-size 16
python train.py --model llama-8b --task ioi --node-epochs 12 --no-edge-pruning \
  --train-samples 64 --val-samples 32 --test-samples 64

# Trying to get Llama 3.2 8B on IOI to work
python train.py --model llama-8b --task ioi # nope with 0.95 default lambda sparsity
python train.py --model llama-8b --task ioi --node-lambda-sparsity 0.7 # ...
python train.py --model llama-8b --task ioi --node-lambda-sparsity 0.5 # ...
python train.py --model llama-8b --task ioi --node-lambda-sparsity 0.3 # ...
python train.py --model llama-8b --task ioi --node-lambda-sparsity 0.7 --edge-lambda-sparsity 0.7 # ...

# STD data generation
python dataset/build_std_dataset.py --statement-source azaria --max-seq-length 90 --train-samples 100 --val-samples 100 --test-samples 100 --margin-thresh 0 # quick test
python dataset/build_std_dataset.py --statement-source neutral --max-seq-length 90 --train-samples 100 --val-samples 100 --test-samples 100 --margin-thresh 0
python dataset/build_std_dataset.py --statement-source azaria --max-seq-length 90 --margin-thresh 0.7 --overgen-factor 60

# Testing out new STD task
python train.py --model llama-8b-instruct --task std --node-lambda-sparsity 0.7 --edge-lambda-sparsity 0.7
python train.py --model llama-8b-instruct --task std --node-lambda-sparsity 0.7 --no-edge-pruning
python train.py --model llama-8b-instruct --task std --skip-node-pruning --node-checkpoint outputs/llama-8b-instruct_std/nls0.7_els0.7_260721-063553/active_nodes.json --edge-lambda-sparsity 0.3 # rerun only for edge pruning


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

- `active_nodes.json` — surviving heads/MLPs for edge pruning (`--skip-node-pruning`),
  plus a `masks` object with post-finalize binary 0/1 gates at every node
  granularity (for later node-circuit evaluation without re-running training).
- `results.json` — baseline / node / edge fidelity metrics, dense- and
  active-edge counts, and the per-granularity node summary.

The console prints the per-granularity node report, dense-edge accounting, the
edge-pruning summary, a fidelity comparison table, the end-to-end edge
compression, and a GPU memory map.

## Evaluating a discovered circuit

`train.py` evaluates the node-pruned circuit once, in-process, right after
pruning. `evaluate_circuit.py` rebuilds it later from `active_nodes.json`
(the `masks` object) and asks three questions:

| evaluation | question |
|------------|----------|
| `sanity`   | Does the saved mask reproduce the numbers the run reported? |
| `knockout` | Is the circuit *necessary* — does removing it stop the behaviour, and what does that cost on unrelated text? |
| `null`     | Does a size-matched **random** circuit do just as well? |

```bash
# Validate the circuit, build all 50 random circuits, estimate the runtime.
# Seconds on a login node; loads no model and never touches CUDA.
python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636 --dry-run

# Reproduce the in-run numbers only
python evaluate_circuit.py <run_dir> --evals sanity --strict

# Everything (~1.5-2 h on one A100)
sbatch scripts/evaluate_circuit.sbatch <run_dir>
python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636

# Check the conclusions against ablation-scheme sensitivity
sbatch scripts/evaluate_circuit.sbatch <run_dir> --ablation mean
```

**`--ablation` means different things in different evaluations.** `sanity` and
`null` fill the *complement* of a ~1%-of-model circuit, so `zero`/`mean` there
means "zero/mean-ablate ~99% of the model" — the standard, much harsher
faithfulness measure. `knockout` fills the circuit itself. Only `interchange`
(the corrupted stream, i.e. the reference the gates were trained against) can
reproduce the in-run numbers. The log banners this on every invocation.

**The random circuits are size-matched exactly**: same blocks, same per-layer
head and neuron counts at every granularity, drawn from a `(seed, index)`
stream so sample *k* is reproducible independent of loop order — which is what
lets `--null-start/--null-count` shard the null across an sbatch array without
changing a single number. They are not serialised; `random_circuits.json`
records the seed and counts, and the set is exactly regenerable.

Useful knobs: `--evals`, `--n-random`, `--test-samples`, `--wikitext-blocks`,
`--skip-wikitext`, `--eval-batch-size`, `--reference shared` (drops the second
copy of the weights — the prunable model's ungated single-stream path *is* the
full model), `--knockout-granularity`, `--mean-source`, `--strict`. See
`python evaluate_circuit.py --help`.

Results land in `<run_dir>/evaluations/<ablation>/`:

```
evaluations/
  index.json                    scheme -> {last_run, headline numbers}
  interchange/
    evaluation.log              appended, one banner per invocation
    summary.json                resolved CLI, circuit counts, verification block
    sanity.json  knockout.json  null.json
    random_circuits.json        seed + counts, NOT the masks
    plots/null_distribution.pdf  plots/wikitext_null.pdf
```

## Tests

```bash
pytest tests/ -q          # CPU only, no downloads, ~20 s
```

`tests/test_evaluation.py` covers the mask loader, the ablation hooks and the
random-circuit sampler on a 2-layer random Llama (plus the real saved circuit's
geometry when a run directory is present). `tests/test_end_to_end.py` drives the
real `evaluate_circuit.py` CLI over a synthetic run directory, faking only the
model loader, the tokenizer and the corpus.

## Repository layout

```
train.py            Unified CLI: parse flags -> node phase -> edge phase -> report
evaluate_circuit.py Rebuild a saved circuit and evaluate it (sanity/knockout/null)
config.py           NodePruningConfig / EdgeConfig + per-(model, task) defaults
pruning.py          Shared node/edge training loops + GPU memory tracker
analysis.py         Node circuit finalisation, mask save/load, edge analysis
l0.py               Hard-Concrete L0 gate
models/             Model registry + ModelAdapter, and the prunable model classes
                    (gpt2_node, gpt2_edge, llama_node, llama_edge)
tasks/              Task interface + ioi / gp / gt / std (objective, data, eval)
dataset/            Vendored dataset builders & task-specific evaluation
evaluation/         Circuit evaluations + their shared context, masks, ablation
                    schemes, metrics, wikitext harness and reporting
```

## How it fits together

`train.py` builds a `ModelAdapter` (hides GPT-2 vs Llama: dtype, which params
are trainable, logit caching) and a `Task` (hides IOI/GP/GT: data, objective,
evaluation metrics). `pruning.py` then runs one shared loop for each phase,
so adding a model or task means adding one small module — not another copy of
the training script.
