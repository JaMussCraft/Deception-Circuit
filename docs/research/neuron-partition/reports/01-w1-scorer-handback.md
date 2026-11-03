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

**Follow-up after ruling R2 and the reader brief.** These changes came after the pilot. The pilot manifests'
`code_sha256` values therefore pin the pilot-time versions of the scorer and the CLI, not the versions the
orchestrator commits.

- **Orientation is unchanged and confirmed.** m is logit(opposite) minus logit(honest) in D's orientation on every
  run, because D's Target is the deceptive answer and the twin is scored with the clean row's labels. The I/N rows
  use the I row's labels. A new test asserts that they equal D's Target and Distractor on all 177 + 177 ranking
  rows.
- **`--pool-dir` added.** It names the directory that holds `<task>_user_inversion` and `<task>_user_neutral`.
  The default is the Codex A1 control cell, read in place. For W3's copy, pass
  `--pool-dir outputs/_analyses/neuron-partition/data/pools`.
- **Pool checks.** Every arrow file of an I or N pool is checked against the reader brief's sha256 table before any
  row is read; a mismatch stops the run. `in_pairs` now also asserts that I and N hold each id at the same row
  position.
- **Notes and provenance.** The manifest note says whether the pools were read in place or from a copy. `rows.json`
  records the arrow check per split.

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

After the R2 follow-up, the test file has 24 tests:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q -rs tests/test_neuron_attribution.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q -rs tests/test_neuron_attribution.py
```

Observed: `24 passed in 25.08s` (mgnp) and `24 passed, 2 warnings in 26.53s` (base), with no skips. The new tests
cover four checks:

- **Brief match.** The Codex pools' train, validation and test arrows match the brief.
- **Tampered copy.** A tampered copy is refused.
- **R2 labels.** I/N labels equal D's on both ranking splits.
- **Pool directory.** `--pool-dir` reads a copied pool.

Dry run against W3's copy:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_attribution.py --task far_v2 --pair dh in --split train,validation --pool-dir /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/data/pools --dry-run
```

Observed: the arrow check passed and nothing was raised. The run has `[dh] 400` and `[in] 354` paired rows, with
clauses on all of them, 0 without a twin, 0 dropped and 0 fallbacks.

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

- **Corrupt stream.** The scorer reads only the clean designation stream. Under R2, the ladder's G averages the
  clean and corrupt streams within an id, and the corrupt stream reverses the words. Should the ranking also score
  the corrupt stream, with D's opposite word as the corrupt row's Distractor? That would double the cost, which is
  still minutes. Default: rank on the clean stream only, because ranking is a selection step and the ablation
  readout, which W2 owns, carries both streams. The pilot's clean-stream gap is 10.45 on 64 validation rows,
  against the audit's 9.915 for the clean stream on test ids.

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

## Addendum: full ranking

The full FAR ranking ran on train and validation, for D against H and for I against N, each with and without
`--reverse`. The job script is
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/jobs/full_attribution_far.sbatch`,
and it is new and uncommitted. It reads the pools from W3's copy through `--pool-dir`. The arrow check passed: had
it failed, the run would have stopped before reading any row.

**Execution evidence.**

- **Job id and cluster.** Delta 23476096, account beto-delta-gpu, `gpuA40x4-interactive` on node gpub045 (NVIDIA A40
  46 GB). It was submitted at 11:30 am CST and started at once.
- **Exit code or Slurm state.** COMPLETED 0:0, elapsed 252 s against 30 min reserved.
  - Ledger r-002 and the job record are in the main-checkout directory
    `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition`, recorded with
    `--commit 7386fd3`.
  - The job is marked COMPLETED and the ledger is reconciled with `--actual-seconds 252`.
- **Row counts.** D/H has 400 rows against an expected 400, with the clause on 400 and 0 fallbacks. I/N has 354
  against an expected 354, with the clause on 354 and 0 fallbacks. All 8 tensors, or 12 in the reverse runs, are
  [32, 14336] float32 and finite.
- **Speed.** Forward-only scoring took 0.082 seconds per row for D/H and 0.085 for I/N. With `--reverse` it took
  0.112 and 0.120, about 1.4 times as long. The model loaded in 23.1 s and 11.5 s.
- **Mean m per stream.** m is logit(opposite) minus logit(honest) in D's orientation (R2).

  | Pair and stream | mean m | rows with m > 0.7 | Pearson with stored margin | mean abs diff | sign agreement |
  |---|---|---|---|---|---|
  | D/H, D (m_clean) | 2.412 | 390 of 400 | 0.9993 | 0.044 | 1.000 |
  | D/H, H (m_twin) | −7.198 | 0 of 400; all 400 below −0.7 | 0.9998 | 0.042 | 1.000 |
  | I/N, I (m_clean) | 5.763 | 354 of 354 | 0.9985 | 0.112 | 1.000 |
  | I/N, N (m_twin) | −8.844 | 0 of 354; all 354 below −0.7 | 0.9988 | 0.092 | 1.000 |

  The intact clean-stream gaps, mean m_clean minus mean m_twin, are 9.61 for D against H and 14.61 for I against N.
  The audit reported 9.915 for D's clean stream and 14.979 for I averaged over both streams. Ten D rows fall below
  0.7 in this fp32 readout, though all are above 0. The pool screen used the stored margins, which differ from
  mine by 0.044 on average.
- **Reverse runs reproduce the forward runs.** The forward keys of each `--reverse` run equal those of the plain run
  exactly, with a maximum absolute difference of 0.0.
- **Provenance files.** Each output directory holds its own `run_manifest.json`. All four have `manifest_hash`
  verified and `slurm_job_id` 23476096. `dataset_files` has 24 entries for D/H and 34 for I/N, and the I/N `notes`
  say the pools were read from a copy of the A1 control cell, sha256-checked.
  - The manifests record `git_commit` `6c6d5be1b631f4f248a29bbc77c0192cb198b4ea`, which was HEAD when the job ran.
    The directory names carry `7386fd3` because the brief asked for `--commit 7386fd3`. `git_dirty` is true.
  - `code_sha256` pins the scorer at ac21a987…647a and the CLI at 126574ec…57c2. Those are the files on disk now,
    unchanged since the R2 follow-up, which the orchestrator reports committed at 7386fd3.
- **Output directories.** All four are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/attribution/`:
  - `far_v2_dh_train+validation_7386fd3/`
  - `far_v2_dh_train+validation_7386fd3_rev/`
  - `far_v2_in_train+validation_7386fd3/`
  - `far_v2_in_train+validation_7386fd3_rev/`

  The brief named them with `_trainval_`. The committed CLI names them `train+validation`, and I did not change code
  to rename them. The log is `logs/neuron_partition_full_far_23476096.out`, which shows no errors.

**How concentrated the scores are.** The counts are neurons out of 458,752, by the absolute value of
`atp_readout_mean`, the mean over rows of the Readout attribution. These readings are descriptive, not a partition.

| Pair | above 0.01 | above 0.1 | above 0.5 | largest |
|---|---|---|---|---|
| D/H | 1,477 | 46 | 0 | 0.392 |
| I/N | 6,338 | 114 | 6 | 0.863 |
| Both pairs | 1,180 | 40 | not computed | not computed |
| D/H, clause positions (`atp_clause_mean`) | 8,520 | 38 | 0 | 0.475 |
| I/N, clause positions | 11,702 | 21 | 0 | 0.347 |

- **Concentration.** The Readout AtP is concentrated. Under 0.4 percent of neurons pass 0.01 for D/H, and 46 pass
  0.1.
- **Overlap.** Most large D/H neurons are also large for I/N: 40 of the 46 above 0.1, and 1,180 of the 1,477 above
  0.01. The correlation of the two `atp_readout_mean` maps over all neurons is 0.775. This is an early sign that the
  D-only class at the Readout will be small. It is a reading, not a verdict.
- **Layer distribution.** Above 0.01, the D/H neurons sit in layers 11 to 16, with a peak of 340 in layer 13, and in
  layers 29 to 31, with 97 in layer 31. I/N has the same shape but more neurons, with 1,356 in layer 13.
- **Reverse direction.** With H as clean, `rev_atp_readout_mean` passes 0.01 for 2,732 neurons and 0.1 for 83 on
  D/H. On I/N the counts are 4,670 and 112.
- **Clause scores.** The clause scores are spread more widely above 0.01, at 8,520 and 11,702 neurons, but few pass
  0.1.

**Not done in this addendum.** No partition into D-only, H-only and shared classes, no thresholds, and no SER run.
The corrupt-stream question in Open questions still stands.

## Addendum: split-half ranking for N3

Status: the code and tests are done. The job is not submitted: it waits for the orchestrator's commit of the
`--ids` change, so that the manifests name a committed tree.

**What changed.** Committed by the orchestrator from the worktree:

- `scripts/neuron_attribution.py` gains three options.
  - `--ids <json>` and `--ids-key <dotted.key>` restrict the ranking rows to a listed id set. I/N rows are matched by
    the same ids.
  - `--tag <name>` is inserted into the directory name before the commit.
  - The ids file's sha256 goes into `dataset_files`, and an `id_filter` report (path, key, wanted, matched, listed
    but absent) goes into `rows.json`. A filter that matches no row stops the run.
- `tests/test_neuron_attribution.py` gains four tests.
  - The dotted-key loader and its refusals.
  - Filter order and counts.
  - The real halves: `halves.A` and `halves.B` give 200 D/H rows each and select exactly W3's `I_A` (174) and `I_B`
    (180) I/N ids. The two halves do not overlap.
  - The CLI end to end with `--ids` and `--tag`.
- `docs/research/neuron-partition/jobs/split_half_attribution_far.sbatch` is new. It makes six runs in four python
  calls: per half, `dh` and `in` forward, then `dh --reverse`. It reserves 30 minutes and takes the commit as its
  only argument. `component_analysis/neuron_attribution.py` is unchanged.

**How verified.**

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q -rs tests/test_neuron_attribution.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q -rs tests/test_neuron_attribution.py --basetemp=/tmp/w1-5201d56c-bt_base5
```

Observed: `28 passed in 42.53s` (mgnp) and `28 passed, 2 warnings in 41.84s` (base), with no skips.

- The first base run failed one test with `OSError: [Errno 122] Disk quota exceeded`. The file-count quota of
  `/u/swong2` stood at 761k files against a 760k hard limit, which this session did not cause alone.
- I deleted my own pytest temp trees under `/u/swong2/.claude/jobs/5201d56c/tmp/w1/`, about 390 files. I then reran
  with a uniquely named temp directory under `/tmp`, and removed it afterwards.

The dry run of both halves, with `--commit 0000000`:

| Half | D/H rows matched | I/N rows matched | listed ids absent from I/N |
|---|---|---|---|
| A (`--tag half1`) | 200 of 200 | 174 | 26 |
| B (`--tag half2`) | 200 of 200 | 180 | 20 |

**Execution evidence.** The orchestrator committed the `--ids` change at 66741d7, and the job ran after that.

- **Job id and cluster.** Delta 23476621, account beto-delta-gpu, `gpuA40x4-interactive` on node gpub019 (NVIDIA A40
  46 GB). It was submitted at 11:46 am CST with `split_half_attribution_far.sbatch 66741d7`.
- **Exit code or Slurm state.** COMPLETED 0:0, elapsed 259 s against 30 min reserved. Ledger r-003 and the job record
  are in the main-checkout directory. The job is marked COMPLETED and the ledger is reconciled with
  `--actual-seconds 259`. The log `logs/neuron_partition_split_half_far_23476621.out` has no errors.
- **Row counts and mean m.** Every row has its clause span and there are 0 fallbacks. All tensors are
  [32, 14336] float32 and finite.

  | Run | rows (expected) | mean m, clean stream | mean m, twin stream | Pearson with stored, clean and twin | sign agreement |
  |---|---|---|---|---|---|
  | half 1, D against H | 200 (200) | D 2.497 | H −7.010 | 0.9993, 0.9997 | 1.000 |
  | half 1, I against N | 174 (174) | I 5.703 | N −8.709 | 0.9981, 0.9985 | 1.000 |
  | half 2, D against H | 200 (200) | D 2.325 | H −7.387 | 0.9993, 0.9998 | 1.000 |
  | half 2, I against N | 180 (180) | I 5.819 | N −8.975 | 0.9989, 0.9991 | 1.000 |

  The two `--reverse` runs score the same D/H rows and give the same m.
- **Speed.** Forward scoring took about 0.085 seconds per row and `--reverse` about 0.112.
- **Halves reproduce the full ranking.** The row-weighted mean of the two halves equals the full-ranking scores
  within 3.2e-4 on `atp_readout_mean` and 3.9e-4 on `atp_clause_mean`, against maxima of 0.39 to 0.86. Batch
  composition changes the padded length and with it the bf16 kernels.
- **Provenance.** Each output directory holds its own `run_manifest.json`. All six manifests verify their hash,
  record `slurm_job_id` 23476621 and `git_dirty` false, and hash `far_rank_ids.json` into `dataset_files`.
  - The orchestrator committed during the run, so the recorded HEADs differ by run.
    - `e5962fe97f758297497a1223ed703e88ce7a8e43`: the first two runs, half 1 D/H and I/N.
    - `5e4fd2ce1533c6e4439a0f323431315f4f420783`: half 1 reverse and half 2 forward.
    - `767d4be0ad733ed3d4a6486ac136f1dd82459ef9`: half 2 reverse, which is the current HEAD.
  - `code_sha256` is identical in all six: scorer ac21a987…647a and CLI c7604bfe…28f8, the files on disk at
    767d4be. The directory names carry 66741d7 as requested.
- **Output directories.** All six are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/attribution/`:
  - `far_v2_dh_train+validation_half1_66741d7/`
  - `far_v2_in_train+validation_half1_66741d7/`
  - `far_v2_dh_train+validation_half1_66741d7_rev/`
  - `far_v2_dh_train+validation_half2_66741d7/`
  - `far_v2_in_train+validation_half2_66741d7/`
  - `far_v2_dh_train+validation_half2_66741d7_rev/`

**Split-half agreement.** These readings are descriptive. N3's Jaccard against a ceiling and a floor belongs to the
class analysis, not to this scorer.

| Score | Pearson, half 1 against half 2 | above 0.01, half 1 and half 2 | Jaccard above 0.01 | above 0.1, half 1 and half 2 | Jaccard above 0.1 |
|---|---|---|---|---|---|
| D/H `atp_readout_mean` | 0.977 | 1,516 and 1,428 | 0.790 | 42 and 44 | 0.792 |
| I/N `atp_readout_mean` | 0.989 | 6,525 and 6,182 | 0.857 | 116 and 112 | 0.781 |
| D/H `rev_atp_readout_mean` | 0.986 | 2,568 and 2,930 | 0.783 | 72 and 85 | 0.670 |

**What is NOT done.** No class partition and no N3 ceiling or floor comparison. No SER split halves.
