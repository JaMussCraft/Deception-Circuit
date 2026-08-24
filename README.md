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
python train.py --model llama-8b-instruct --task std --node-lambda-sparsity 0.7 --edge-lambda-sparsity 0.7 --no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output
python train.py --model llama-8b-instruct --task std --node-lambda-sparsity 0.4 --no-edge-pruning --faithfulness-weight 0.5

# Deception-mechanism family: FAR (fabrication), SDR (omission), SER (pragmatic
# distortion). One shared content pool, one scaffold, three predicates — see
# "The deception-mechanism task family" below.
python dataset/build_deception_dataset.py --task far --no-model      # CPU dry run
sbatch scripts/pilot_deception.sbatch                                # REQUIRED first
sbatch scripts/build_deception.sbatch                                # then the build
sbatch scripts/train_deception.sbatch far
sbatch scripts/train_deception.sbatch far --deception-condition honest


```

## The deception-mechanism task family (FAR / SDR / SER)

Three tasks, one per deception mechanism, built so their discovered circuits can
be compared against one another. They share a single content pool
(`dataset/deception_pools/`) and a single prompt scaffold; what varies is the
**predicate applied to the designated item**, and therefore what the question's
answer space affords:

| Task | Mechanism | Predicate | Question | Deceiving requires |
|------|-----------|-----------|----------|--------------------|
| `far` | fabrication | `failing` / `passing` | "Which result is failing?" | asserting a falsehood |
| `sdr` | omission | `critical` / `harmless` | "Which result will you show me?" | showing only the harmless one |
| `ser` | pragmatic distortion | `unfavorable` / `favorable` | "Which result should I look at?" | choosing the frame |

Everything else — entities, item nouns, corruption site, readout, balancing — is
held constant by construction, so an observed circuit difference is attributable
to the mechanism rather than to prompt format. The three tasks are deliberately
almost the same task: a null result ("no mechanism-specific circuitry at this
granularity") is a live and informative outcome, not a failure.

**Matched triplets.** The instance list — (entity, item pair, item polarity,
designation polarity, pressure slot, template variant) — is task-independent and
seeded, so building the three tasks with the same `--seed` realizes the *same*
instances under the three predicates. Each example carries a stable
`instance_id`; `dataset/deception_comparison_set.py` intersects the three
survivor sets into the **primary comparison set**, and reports the
matched-pressure subset (the five mechanism-neutral clauses shared by all three
pools). Each task's full survivor set is kept as a robustness set.

**Honest twins.** Each build also harvests `<task>_honest` from its own filter
failures: the same prompts under the same pressure, where the base model answered
honestly. The comparison unit is `Δ = C_<task> − C_<task>_honest`, which holds
format, content and pressure-reading constant, so the three flavors of pressure
clause do not confound the comparison. The honest split is resampled to match the
deceptive split's marginals on item pair, pressure, both polarities and template
variant.

**Pilot before building.** At STD's ~2% pass rate a full three-task build is
hundreds of thousands of forward passes. `dataset/pilot_deception.py` measures
the pass rate, the prior-balance margin distribution and the unexpected-argmax
counts on a few hundred instances — and, critically, validates the *honest*
labels by re-running every task with the pressure clause removed and with an
explicit honesty instruction in its place. FAR's honest answer is entailed by
the prompt; SDR's follows from disclosure norms; **SER's is normative**, and if
its label validation lands near 50/50 then `ser_honest` is contaminated and
`Δ_SER` is meaningless until the user turn is reworded.

`dataset/mechanism_purity_check.py` runs the LLM-judge check afterwards: SDR and
SER are the pair at risk of collapsing into each other, and if the judge cannot
separate them, the result is a two-way one and should be reported as such.

STD is kept, demoted from "the fabrication task" to a second scenario family for
fabrication — which gives the variance decomposition its within-mechanism,
cross-template noise-ceiling term for free.

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
(the `masks` object) and asks four questions:

| evaluation | question |
|------------|----------|
| `sanity`   | Does the saved mask reproduce the numbers the run reported? |
| `knockout` | Is the circuit *necessary* — does removing it stop the behaviour, and what does that cost on unrelated text? |
| `null`     | Does a size-matched **random** circuit do just as well? |
| `pressure` | Does the behaviour need the pressure clause, or is the circuit just reading the last sentence of the system prompt? |

```bash
# Validate the circuit, build all 50 random circuits, estimate the runtime.
# Seconds on a login node; loads no model and never touches CUDA.
python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636 --dry-run

# Reproduce the in-run numbers only
python evaluate_circuit.py <run_dir> --evals sanity --strict

# What are the head/block choices worth on their own? Loads only the coarse
# gates and holds every attention neuron and MLP unit under them open.
python evaluate_circuit.py <run_dir> --evals sanity --sanity-granularity coarse

# Everything (~1.5-2 h on one A100)
sbatch scripts/evaluate_circuit.sbatch <run_dir>
python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636 --ablation zero
python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636 --evals knockout --knockout-granularity all
python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636 --evals null --null-alloc perhead
python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636 --evals sanity --sanity-granularity coarse

python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.8_noedge_260722-162843

# Check the conclusions against ablation-scheme sensitivity
sbatch scripts/evaluate_circuit.sbatch <run_dir> --ablation mean
```

`knockout` also re-runs its three configurations on an **honest-instructed**
variant of the same prompts, and emits open generations on wikitext for the
full model, the knockout and the circuit alone (`--gen-examples`,
`--gen-new-tokens`). Read the `full` column of those generations first: fluent
wikitext there is what says the generation loop itself is sound.

**Under a prompt variant the metrics read backwards.** `pressure` and the
honest-instruction section of `knockout` rebuild the prompts with the pressure
clause dropped or replaced, and keep the labels exactly as they were — the
deceptive answer stays the "target". A model that stops being deceptive once
the pressure is gone therefore shows *falling* accuracy and a *negative* logit
diff, and that is the result the control is looking for. `pressure` reports
accuracy and logit diff only: the full model under a variant is a different
distribution, so a KL column there would invite a cross-variant comparison
nothing supports.

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

### More than one circuit, more than one task

Bind circuits to names and the same CLI evaluates any expression over them
against any set of tasks — one process, one model load:

```bash
# Faithfulness matrix: three mechanism circuits x their three tasks.
python evaluate_circuit.py \
    --circuit far=outputs/llama-8b-instruct_far/<run_dir> \
    --circuit sdr=outputs/llama-8b-instruct_sdr/<run_dir> \
    --circuit ser=outputs/llama-8b-instruct_ser/<run_dir> \
    --task far --task sdr --task ser --suite-name mechanism-matrix

# Is the shared core sufficient on its own?
python evaluate_circuit.py --circuit far=... --circuit sdr=... --circuit ser=... \
    --expr 'shared=far & sdr & ser' --task far --task sdr --task ser

# Specificity asymmetry: the exclusive family, six circuits x three tasks.
python evaluate_circuit.py --circuit far=... --circuit sdr=... --circuit ser=... \
    --xor far,sdr,ser --task far --task sdr --task ser
```

Expressions take `|` union, `&` intersection, `\` (or `-`) difference and
parentheses — quote them, since every one of those characters means something
to the shell as well. `--all-pairs-delta` is shorthand for every ordered
`X\Y`.

**Set membership has two readings, and both are computed.**
`--compose-granularity leaf` composes the finest gates (attention neurons, MLP
units); `head` composes heads and MLP blocks. Two circuits can share every head
and almost no neuron, so the default `both` evaluates each expression twice, as
separate cells suffixed `__leaf` and `__head`. Coarse gates are re-derived
bottom-up from whatever the composition leaves open, so a composed circuit is
always hierarchy-valid.

`--task NAME` inherits the model and data directory from the bound circuits and
uses that task's default hyperparameters; `--task-from <run_dir>` inherits an
existing run's dataset arguments instead. `sanity` has nothing to compare
against on a cell whose circuit was not trained on that task, or on a composed
circuit, so it skips itself there with the reason recorded.

`--dry-run` prints the resolved circuits, the tasks, the cell grid and a
per-stage runtime estimate without loading a model — worth doing before every
suite, since the grid is a product and a cell is not cheap.

Useful knobs: `--evals`, `--n-random`, `--test-samples`, `--wikitext-blocks`,
`--skip-wikitext`, `--eval-batch-size`, `--reference shared` (drops the second
copy of the weights — the prunable model's ungated single-stream path *is* the
full model), `--sanity-granularity`, `--knockout-granularity`, `--mean-source`,
`--gen-examples`, `--gen-new-tokens`, `--compose-granularity`, `--suite-name`,
`--output-dir`, `--strict`. See
`python evaluate_circuit.py --help`.

A single circuit on its own task lands in `<run_dir>/evaluations/<ablation>/`:

```
evaluations/
  index.json                    scheme -> {last_run, headline numbers}
  interchange/
    evaluation.log              appended, one banner per invocation
    summary.json                resolved CLI, circuit counts, verification block
    sanity.json  knockout.json  null.json  pressure.json
    random_circuits.json        seed + counts, NOT the masks
    plots/null_distribution.pdf  plots/wikitext_null.pdf
```

Anything else — more than one circuit, any composed circuit, any task that is
not the circuit's own, or an explicit `--suite-name` — writes a suite and
leaves the run directories alone:

```
outputs/_suites/<suite-name>/
  suite.json    the spec and its provenance: circuits, tasks, geometry
  suite.log     tee'd stdout/stderr
  matrix.json   circuit x task x eval -> headline metrics
  matrix.csv    the same, one row per (cell, eval, metric), for the 3x3 / 3x6 tables
  cells/<circuit-label>/<task-label>/<ablation>/   exactly the tree above
```

The per-cell body is the same code either way, so a suite cell's JSON is
byte-comparable with a legacy run's.

## Tests

```bash
pytest tests/ -q          # CPU only, no downloads, ~20 s
```

`tests/test_evaluation.py` covers the mask loader, the ablation hooks and the
random-circuit sampler on a 2-layer random Llama (plus the real saved circuit's
geometry when a run directory is present). `tests/test_end_to_end.py` drives the
real `evaluate_circuit.py` CLI over a synthetic run directory, faking only the
model loader, the tokenizer and the corpus. `tests/test_algebra.py` covers the
set operations and the bottom-up coarse re-derivation, `tests/test_variants.py`
the prompt rebuilds and their token-alignment invariants,
`tests/test_generation.py` the greedy loop (which cannot use a KV cache — the
corrupted stream carries no `past_key_value`), and `tests/test_suite_layout.py`
the legacy-vs-suite layout decision and the matrix files.

## Repository layout

```
train.py            Unified CLI: parse flags -> node phase -> edge phase -> report
evaluate_circuit.py Rebuild saved circuits (or expressions over them) and
                    evaluate them on one or more tasks
config.py           NodePruningConfig / EdgeConfig + per-(model, task) defaults
pruning.py          Shared node/edge training loops + GPU memory tracker
analysis.py         Node circuit finalisation, mask save/load, edge analysis
l0.py               Hard-Concrete L0 gate
models/             Model registry + ModelAdapter, and the prunable model classes
                    (gpt2_node, gpt2_edge, llama_node, llama_edge)
tasks/              Task interface + ioi / gp / gt / std / far / sdr / ser
                    (objective, data, eval); deception.py holds the shared
                    FAR/SDR/SER implementation
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
