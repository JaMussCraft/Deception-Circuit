# Hand-back 01: W1, the N1 neuron attribution scorer and its pilot

Agent: implementation worker W1 (Claude, Opus). Ticket: the orchestrator's W1 brief (neuron attribution scorer,
tests on both interpreters, one Delta interactive pilot). Status: resolved. The scorer and tests are done, the pilot
COMPLETED, and the job is reconciled in the ledger.

## What changed

All four files are new. No existing file was edited. The orchestrator commits them from the worktree.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/component_analysis/neuron_attribution.py`
  holds the scorer.
  - **Unit and hooks.** It scores the `down_proj` input (the post-SwiGLU neuron) with plain torch hooks; nnsight is
    not used.
  - **Gradients.** The embedding output is made to require grad, so all 32 captures share one graph. One
    `torch.autograd.grad` call per batch gives every layer's total derivative, with frozen parameters and no
    parameter grads.
  - **Metric.** m is logit(Target) minus logit(Distractor) at the Readout. It goes through an fp32 recomputation of
    the final RMSNorm and an fp32 dot product with the difference of the two unembedding rows. The clean row's
    labels are used for both streams.
  - **Pair loaders.** `dh_pairs` goes through `dataloaders.neutral_twin_batches`, which asserts clause alignment.
    `in_pairs` is its own join by instance id, because the loader's twin pairing does not cover
    `user_inversion`/`user_neutral`. It asserts equal length and mask, the same Readout as the pool's `readouts`,
    and every differing token inside `request_spans["clean"]`. Otherwise it falls back to the Readout only and
    records the row.
  - **Accumulation and outputs.** Running float64 sums live on the device, and no per-row per-neuron tensors are
    kept. `write_outputs` and `write_manifest` produce `run_manifest.py`'s record plus a `notes` list. The hash is
    recomputed with the notes in, and existing files are never overwritten.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_attribution.py`
  is the CLI.
  - **Flags.** `--task far_v2|ser_v2`, `--pair dh in` (one model load, one output directory per pair),
    `--split train,validation` (any other split is refused, per item 10 of START), `--limit`, `--batch-size`
    (default 4), `--reverse`, `--inversion-dir`/`--neutral-dir` overrides, `--note` and `--dry-run`.
  - **Dry run.** It loads the tokenizer and the paired rows, prints counts and a runtime estimate, and loads no
    model.
  - **Commit.** The commit for the directory name is read from the `.git` files; no git process is started.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/tests/test_neuron_attribution.py`
  holds 19 tests. They use a tiny 2-layer Llama with the real Llama-3 tokenizer and the real far_v2 and I/N pools.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/jobs/pilot_attribution.sbatch`
  is modelled on `scripts/evaluate_circuit.sbatch`. It sets `RESEARCH_DIRECTION=neuron-partition` and logs to
  `logs/neuron_partition_pilot_%j.out`.
- **Untracked outputs of the pilot.** The orchestrator decides what to keep.
  - `outputs/_analyses/neuron-partition/attribution/far_v2_dh_validation_f4ce555_limit64/` and
    `.../far_v2_in_validation_f4ce555_limit64/` each hold `scores.pt`, `rows.json` and `run_manifest.json`.
  - The job log is `logs/neuron_partition_pilot_23475874.out`. Both paths are under the worktree.

**Output format.** `scores.pt` is a dict of float32 tensors of shape [32, 14336]:

- `atp_readout_mean`, `atp_readout_absmean`, `atp_clause_mean`, `atp_clause_absmean`.
- `contrast_readout_mean`, `contrast_readout_std`, `contrast_clause_mean`, `contrast_clause_std`.
- With `--reverse`, also `rev_atp_{readout,clause}_{mean,absmean}`.

The sign convention is s = (a_clean − a_twin) · dm_clean/da. A positive s means that patching the neuron to its
twin value lowers m, so the neuron pushes toward the deceptive or inverted answer.

## How verified

Baseline before any change, on both interpreters, for the neighbouring tests:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d2_premise.py tests/test_component_analysis_v2_dataloaders.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_d2_premise.py tests/test_component_analysis_v2_dataloaders.py
```

Observed: `40 passed` (mgnp) and `40 passed, 2 warnings` (base). There were no baseline failures in these files.

The new tests on both interpreters:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_neuron_attribution.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q -rs tests/test_neuron_attribution.py
```

Observed: `19 passed in 25.65s` (mgnp) and `19 passed, 2 warnings in 27.15s` (base), with no skips. The tests cover
these checks:

- **Capture.** The capture is the down_proj input, equal to `act_fn(gate_proj(x)) * up_proj(x)`, with shape
  [B, T, 128].
- **Metric.** The fp32 metric equals the full-logit target minus distractor.
- **Padding.** Trimming shared padding leaves m unchanged.
- **AtP at the Readout (key test).** AtP matches (a_clean − a_twin) times a central-difference dm/da of a
  one-neuron shift, within 1e-4 relative. This is checked at layer 0, where a cut graph would show, and at layer 1.
- **AtP over the clause.** Clause AtP equals the summed per-position finite differences.
- **Full one-neuron patch.** A full patch matches AtP within 5% on the tiny model.
- **Reverse.** The reverse scores equal the forward scores with the streams swapped.
- **Batch independence.** Rows in one batch score the same as rows scored alone.
- **Contrast.** The activation contrast and its standardized version match a numpy recomputation at the Readout and
  over the clause, including a Readout-only fallback row.
- **Output files.** The files carry the expected keys and shapes. The manifest hash verifies with notes in, and
  the writer never overwrites.
- **Real loaders.** The real D/H and I/N loaders produce aligned spans.
- **CLI.** The CLI runs end to end on the tiny model with both pairs, and the dry run loads no model.

One debugging note. The first finite-difference test used a forward difference with a 1e-5 step and failed at
layer 0. Graph and leaf gradients agreed exactly, and the gap came from Llama's RMSNorm, which casts to float32
inside even a float64 model. A central difference converges to the graph gradient: at a step of 1e-3, the values
0.1033197 against 0.1033192 and −0.3222778 against −0.3222773.

Login-node dry run of the full ranking plan:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_attribution.py --task far_v2 --pair dh in --split train,validation --dry-run
```

Observed:

- `[dh] 400 paired row(s) from train, validation; clause on 400`, with 200 of 200 paired in each split, 0 without
  a twin, 0 dropped and 0 clause fallbacks.
- `[in] 354 paired row(s) ...; clause on 354`, with 177 of 177 in each split and 0 in every exclusion count.

## Execution evidence

- **Job id and cluster.** Delta 23475874, account beto-delta-gpu (projected 11:49 against 12:11 for bimc under
  `--test-only`). Partition `gpuA40x4-interactive`, node gpub002, NVIDIA A40 46 GB. Submitted at 11:20 am CST and
  started at once.
- **Exit code or Slurm state.** COMPLETED 0:0, elapsed 89 s against 45 min reserved.
  - Ledger r-001 is reconciled with `--actual-seconds 89 --status COMPLETED`.
  - The job tracker shows COMPLETED.
  - The ledger entry was recorded with `--commit f4ce555`, not 618efdd, because HEAD had moved to f4ce555 by
    submission; it was read from the `.git` files.
- **Row counts.** D/H has 64 of 64 requested rows, 64 with the clause and 0 fallbacks. I/N has 64 of 64, 64 with
  the clause and 0 fallbacks. Every score tensor is [32, 14336] float32 and finite.
- **Baseline reproduces.** The table below compares the pilot's m with the datasets' stored margins, which are
  `-h_pressure_clean` and `-h_neutral_clean` for D/H and the pool's `scores/validation.jsonl`
  `opposite_minus_honest` for I/N.

  | Pair and stream | mean m | rows with m > 0.7 | Pearson with stored | mean abs diff | sign agreement |
  |---|---|---|---|---|---|
  | D/H, m_clean (D) | 3.090 | 64 of 64 | 0.9996 | 0.040 | 1.000 |
  | D/H, m_twin (H) | −7.362 | 0 of 64 | 0.9998 | 0.038 | 1.000 |
  | I/N, m_clean (I) | 6.820 | 64 of 64 | 0.9991 | 0.103 | 1.000 |
  | I/N, m_twin (N) | −9.091 | 0 of 64 | 0.9985 | 0.094 | 1.000 |

- **Measured speed.** Scoring takes 0.098 seconds per row for D/H (64 rows in 6.3 s) and 0.084 for I/N (64 rows in
  5.4 s) at batch 4 on an A40. The model loaded in 25.6 s from the node cache.
- **Provenance files.** `.../far_v2_dh_validation_f4ce555_limit64/run_manifest.json` and
  `.../far_v2_in_validation_f4ce555_limit64/run_manifest.json` both name commit
  `f4ce555ad223f81a0f775274164d405e5130ceb3`.
  - Both have `manifest_hash` verified, `slurm_job_id` 23475874 and `direction` neuron-partition.
  - `dataset_files` has 24 sha256 entries for D/H (far_v2 and far_v2_honest) and 34 for I/N, which include both pool
    directories and their `scores/*.jsonl`.
  - The I/N manifest's `notes` says "unmerged Codex pool: I = <path>, N = <path> (specificity-ladder A1 control
    cell, read in place)", and `rows.json` records the pool paths, file hashes and the same note.
  - `git_dirty` is true: a tracked file was modified in the worktree at job time. `component_analysis/hooks.py`,
    W2's file, was seen changing on disk, and the manifest records `dirty_diff_hash`. My new files are untracked, so
    `code_sha256` pins the scorer (`component_analysis/neuron_attribution.py` 673882…e617) and the
    CLI (`scripts/neuron_attribution.py` cb3e6a…98a8).

**Descriptive pilot readings.** These come from 64 rows and are not claims.

- **AtP over all neurons.** The sum of `atp_readout_mean` over every neuron is 9.07 against a mean m_clean − m_twin
  of 10.45 for D/H, and 17.3 against 15.9 for I/N. The magnitudes are comparable, and the MLP neurons are only part
  of the paths.
- **Layer mass.** Readout AtP mass sits in layers 13 to 16, 19 to 21 and 31 in both pairs.
- **Top neurons overlap.** The top readout neurons overlap between D/H and I/N: L15 N11788, L15 N2808, L16 N8935
  and L13 N4212.

**Estimate for the full ranking on FAR.** The run covers 400 D/H rows and 354 I/N rows from train and validation.

- On the A40 it is about 70 s of scoring.
- On an H100 80 GB, an assumed 1.5 to 2.5 times the A40's speed gives about 30 to 50 s of scoring. Bridges-2's
  model load was about 460 s historically, so the total is about 9 to 10 minutes.
- `--reverse` adds a second backward per batch, about 1.5 to 1.8 times the scoring time (not measured).
- **Recommended reservation.** `--time 00:30:00` on one H100 for FAR `dh` and `in` together with `--reverse`, and
  the same again for SER. Memory was not a limit at batch 4 on the 46 GB A40, and batch 8 is likely fine on 80 GB.

## What is NOT done

- **Reverse direction.** It is implemented and tested (`--reverse`) but was not run in the pilot, so its cost is an
  estimate.
- **Full train+validation ranking.** It has not been submitted; that is the orchestrator's next job.
- **SER.** It is supported by `--task ser_v2` for `dh` (and `in` when the pools exist), but it was neither
  dry-run nor run.
- **Pilot scope.** The pilot also ran the I/N pair on 64 validation rows inside the same job (5.4 s), beyond the
  brief's D/H-only pilot. This validated the unmerged-pool path on the GPU at no extra reservation.
- **Neuron classes and ablation.** No D-only, H-only or shared classes are derived and nothing is ablated. That is
  later N1 work: W2 owns the ablation and W3 the test sample.

## Open questions

- **Standardized contrast floor.** `contrast_readout_std` is dominated by neurons that are nearly constant under
  the twin. Its top magnitudes reach 94 on D/H and 260 on I/N because the 1e-6 floor barely acts. Should the ranking
  use a floor such as the median twin standard deviation of the layer, or rank on `contrast_readout_mean`? Default:
  rank on AtP and `contrast_readout_mean`, and treat `_std` as descriptive until the orchestrator rules.
- **Ranking aggregate.** Should the ranking use the signed mean or the absolute mean of AtP? Default: signed
  `atp_readout_mean` for the D/I direction-specific partition, with `atp_readout_absmean` as the tie-break and
  comparison.
- **Cluster for the full run.** Should it run on Bridges-2 (START's first choice) or on another Delta interactive
  job, given that the A40 interactive partition started at once and the whole FAR run fits in a few minutes?
  Default: one Delta interactive job of 30 minutes, because it is faster end to end than a Bridges-2 model load.
  The pilot sbatch hard-codes `--split validation --limit 64`, and a later argument cannot remove `--limit`. The
  full run therefore needs a copy of the sbatch whose python line is
  `--task far_v2 --pair dh in --split train,validation --batch-size 4 [--reverse]`.
