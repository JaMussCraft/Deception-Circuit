# Hand-back 02: D4 closure riders and the static quartet read

Agent: Opus worker (claude-opus-5-5), direction deception-divergence. Ticket: the orchestrator's D4 message of Mon 2
Nov 2026 (START.md section 2 item D4, section 10 "D4 rules", spec.md D4 rules). Status: resolved. Rider (d) ran end to
end on the login node. Riders (a) to (c) are dry-run and ready for the orchestrator to submit.

## What changed

All files are in the worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
Nothing is staged for the apply tool.

- Committed by the orchestrator from the worktree:
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/d4_static_quartet.py`,
    new. Rider (d): lazy safetensors reads, the P1 Q-composition and P2 copy scores, random baselines, the copy-score
    ceiling over all 1,024 heads, JSON, Markdown and run manifest.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d4_static_quartet.py`,
    new, 10 tests on synthetic weights.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/spontaneous/patching.py`,
    rider (b). It adds the `after_cue` arm to the end of `POSITION_ARMS`, a `last_difference` helper, an optional
    `ends` argument on `arm_mask` and `twin_interchange`, and passes `SycPair.cue_end` from `run_syc`. The `post_tag`
    and `readout` arms are unchanged.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/b3_patch.py`,
    rider (b). The `--positions` help names the new arm, and the dry run prints the cue-window width when the arm is
    asked for. Validation already reads `patching.POSITION_ARMS`, so nothing else changed.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d4_after_cue.py`,
    new, 9 tests. One runs a synthetic pair through the tiny Llama, and one runs `b3_patch.main` end to end with `--positions after_cue,readout` on six committed items.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/component_analysis/attention_patterns.py`,
    rider (a). It adds the opt-in flag `--attention-instances {split,causal_sample}`, default `split`. With
    `causal_sample` the `pressure` and `neutral_twin` conditions read the causal sample, which `--include-ids` and
    `--n-causal` fix, instead of the whole test split. Coverage is then labelled `causal_sample` and
    `causal_sample_neutral_twin_paired`, and `patterns.json` gains `"instances": "causal_sample"`. A default run is
    byte-for-byte as before.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d4a_attention_instances.py`,
    new, 5 tests, two of them through the CLI on a tiny v2 cell.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/jobs/D4a.batch`,
    new, rider (a), with far and ser lines.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/jobs/D4c-sdr.batch`,
    new, rider (c).
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d4_jobs.py`,
    new, 9 tests. They cover both batch files, the C_t component-count check for sdr (66, from ct.json) and the D4a
    lines.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/02-handback.md`,
    this file.
- Git-ignored outputs, not for commit:
  - `outputs/_analyses/deception-divergence/d4d/static_quartet.json`, `static_quartet.md` and `run_manifest.json`.
  - `outputs/_analyses/deception-divergence/d4c/sdr/Ct__leaf/sdr_v2/{head_table.*,segmentation.json,sample.json}`,
    which the D4(c) dry run writes, as every analyze_components dry run does.
  - `outputs/_analyses/deception-divergence/d4a/{far,ser}/...`, the same for D4(a).

## How verified

D4(d) unit tests and the D4 batch and arm tests, both interpreters:

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d4_jobs.py tests/test_d4a_attention_instances.py tests/test_d4_after_cue.py tests/test_d4_static_quartet.py
OMP_NUM_THREADS=4 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_d4_jobs.py tests/test_d4a_attention_instances.py tests/test_d4_after_cue.py tests/test_d4_static_quartet.py
```

Observed: mgnp "33 passed". Base "29 passed, 4 skipped". The skips are the four tests that need nnsight 0.7.0.

The existing suites of the touched modules, before and after the change:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_b3_patching.py
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_b3_patching.py
```

Observed before the edit: mgnp "62 passed, 1 skipped", base "54 passed, 9 skipped". After the edit, run together
with the new arm tests: mgnp "70 passed, 1 skipped", base "61 passed, 10 skipped". The added counts are exactly the
new file's tests, so no existing test changed state.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_attention_patterns.py tests/test_attention_patterns_neutral_twin.py tests/test_attention_token_level.py tests/test_selective_v6_attention.py tests/test_instructed_route_b1_jobs.py
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q (same files)
```

Observed after the edit: mgnp "100 passed", base "56 passed, 33 skipped". No failures, so there was nothing to compare
by name against the main baseline.

Dry runs, all from the worktree root:

```
HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python analyze_components.py batch docs/research/deception-divergence/jobs/D4a.batch --dry-run
```

Observed: "batch: 2 of 2 invocation(s) ok", exit 0. far: 62 C_t heads over 11 layers; sample 100 of 100 from
`far_heldout_D_sample.json`, 13 batches of 8; neutral twin on 100 of 100; "neutral twin (paired), both sides: 100
instance(s) in 13 batch(es) read 2x, 286 eager forward(s) ~54 s". ser: 68 heads over 12 layers, 100 of 100, "312
eager forward(s) ~59 s". Without the new flag the same line reads 1,000 instances in 125 batches (checked on a
scratch far line), so the flag is what puts the profile on the B1 held-out ids.

```
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python scripts/b3_patch.py --task syc --sets S_all,heads_only --positions after_cue,post_tag --null 20 --out outputs/_analyses/deception-divergence/d4b --dry-run
```

Observed, exit 0: "800 twin pairs ... (0 dropped)"; "S_all (35, null seed 20261025, layer_matched, members excluded,
MLP members kept: mlp.6.0 mlp.7.0 mlp.5.0), heads_only (32, null seed 20266025, heads_only, members excluded)";
"positions: after_cue, post_tag; 20 null draws per set; 84 arms"; "cue window: 7 to 7 tokens (mean 7.0); after_cue
positions per row: 23 to 23 (mean 23.0)"; "walltime estimate: A100 0.22 h compute + 8 min load = 0.35 h". The null
seeds equal J4's (review 07 records 20266025 for heads_only).

```
HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python analyze_components.py batch docs/research/deception-divergence/jobs/D4c-sdr.batch --dry-run
```

Observed: "batch: 1 of 1 invocation(s) ok", exit 0. Ct__leaf x sdr_v2 holds "56 head(s) and 10 MLP block(s)", 66
Components. The sample is 100 of 100 from `sdr_heldout_D_sample.json`, and the neutral twin covers 100 of 100. The
route_closure line reads "35 arm(s) ... = 481 forward(s), plus 25922 T1 sweep and control forward(s) (990 outside
sender(s), estimators both) and 1742 path-patching forward(s); about 86.7 min at the A40 rate". B1 far priced at 86.2
min on the same rate (instructed-route hand-back 23).

Readings for D4(c): `scripts/route_closure_readings.py` is task-agnostic. I relabelled B1's far `route_closure.json`
as `sdr_v2` and wrote the readings into a scratch directory:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/route_closure_readings.py <scratch>/rc_relabelled_sdr.json --out-dir <scratch>/readings_check
```

Observed: exit 0, "wrote ... (sdr_v2)"; the T2 row reads "sdr_v2 | 100 | 9.886 | 0.321 [0.302, 0.344] | -0.012
[-0.017, -0.007] | -0.333 ... | query-side | query-side", the B1 far numbers exactly, with rule estimator offline (R9).
The default `--out-dir` is the instructed-route results directory, so the D4(c) command below overrides it.

## Execution evidence

Rider (d) is the only run claimed.

- Job id and cluster: a local command on the Delta login node, with no Slurm job:
  `OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 HF_HUB_OFFLINE=1 HF_HOME=/work/nvme/beto/swong2 /u/swong2/.conda/envs/mgnp/bin/python scripts/d4_static_quartet.py --out outputs/_analyses/deception-divergence/d4d`.
  It took 17:54 wall clock with a peak RSS of 4.9 GB. An earlier attempt with `--verify-hashes` was OOM-killed with
  exit 137. The cause was the user slice's shared 40 GB cap, which logged one `oom_kill` while other workers' jobs
  ran. That attempt wrote nothing. The first complete run, before the ceiling scan was added, gave identical P1 and
  P2 numbers, and its outputs were replaced.
- Exit code: 0.
- Row counts:
  - 320 sender scores in `P1.ranking`, against 10 layers times 32 heads.
  - 20 random P1 draws and 20 random P2 heads.
  - 82 unique single-token item tokens, none dropped as multi-token: far_v2 78, sdr_v2 78, ser_v2 66, from the 1,000
    test rows of each task.
  - 1,024 heads in `P2.ceiling.copy_score_by_head`, against 32 times 32.
- Baseline reproduces:
  - The low-rank score of head.15.8 equals its dense 4096 by 4096 computation to 12 digits: 0.038365429945 against
    0.038365429945.
  - The shapes are q_proj [4096, 4096], k_proj and v_proj [1024, 4096], o_proj [4096, 4096] and lm_head
    [128256, 4096], with lm_head's Frobenius norm 295.0510.
  - All four quartet heads read KV group 6, as `route_closure.py` states.
  - The shards' sha256, read from their LFS blob names, equal an independent `sha256sum` of the four files: 2b1879f3,
    09d433f6, fc1cdddd and 92ecfe1a. The index is 146776fc and config.json 29e4c210. All are recorded in
    `static_quartet.json` under `weights`.
- Provenance file: `outputs/_analyses/deception-divergence/d4d/run_manifest.json`, commit
  `b324c507cfa59cb60d63d927fe03573267cfe2a9`, `git_dirty` true. The script was uncommitted, so the manifest's
  `code_sha256` for `scripts/d4_static_quartet.py` (895ae401...) is what ties the output to the file the orchestrator
  commits. The model revision is 0e9e39f249a16976918f6564b8830bc894c89659, the same as the J4 manifest.

**D4(d) results**, read on the frozen rule. Both fail.

| quantity | value | rule |
|---|---|---|
| head.15.8 rank, stacked quartet W_Q | 7 of 320 (score 0.0384) | at most 16 |
| head.14.4 rank | 24 of 320 (score 0.0295) | at most 16 |
| layer-sum order, layers 7 to 16 | 14, 13, 12, 15, 11, 10, 16, 8, 9, 7 | 14 and 15 above every other layer |
| P1 | fail: head.14.4 misses, and layer 15 is fourth | |
| quartet copy scores | 0.000, 0.000, 0.012, 0.000 | at least 2 of 4 reach 0.5 |
| P2 | fail | |

- **P1, against the random baseline.** No random draw of four layer-17 heads passes the rule. Into all 20 draws,
  head.15.8 scores below its quartet score: draw max 0.0319 against 0.0384. So does head.14.4: draw max 0.0224
  against 0.0295. The two named senders therefore compose more with the quartet's queries than with other layer-17
  heads, but not enough to meet the pre-registered ranks. Read per quartet head and beside the rule, head.15.8 ranks
  15, 3, 5 and 17, and head.14.4 ranks 14, 85, 32 and 29. Under the spec, a P1 fail reads as activation-dependent
  routing, which supports the distributed parallel route.
- **P2, against its ceiling.** The read has almost no power on this model. The identity map, embedding straight to
  W_U, scores 0.000, because Llama-3.1's embeddings are untied. None of the 1,024 heads reaches 0.5; the best are
  head.30.12 at 0.390 and head.27.7 at 0.317. The 20 random layer-17 heads have mean 0.006 and max 0.024. The quartet
  ranks 70th (head.17.26) and about 390th of 1,024 (the other three, tied at 0). The mlp.0 variant gives the same
  quartet scores. P2 fails under the frozen rule, but the fail mostly reflects a read that no head of this model
  passes. It is weak evidence against copying.

Riders (a) to (c) did not run on a GPU. Each is dry-run only, so its numbers are not yet verified. Below are the
sbatch-ready commands for Delta, submitted from the worktree. The account is the orchestrator's choice; bgrb has
started sooner than beto and bimc. Every estimate includes the model load.

| rider | dry-run price | basis of the estimate | estimate | reserve |
|---|---|---|---|---|
| (a) | 54 s + 59 s of eager forwards at the A40 rate | load about 6 to 8 min per job (B1 smoke load 477 s) | 0.2 GPU-h | 0:30 |
| (b) | A100 0.35 h, H100 0.24 h | J4 supplement, 126 arms, 1,455 s compute on A100; this job has 84 arms | 0.45 GPU-h on A100 | 0:45 |
| (c) | 86.7 min at the A40 rate | B1 far priced 86.2 min and ran 1,598 s plus 362 s load on an H100 | 0.6 GPU-h on H100 or H200, about 0.9 on A100 | 1:15 |

D4(a), the quartet's attention under D and the twin:

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence && mkdir -p logs && sbatch --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence --time=00:30:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/analyze_components.sbatch batch docs/research/deception-divergence/jobs/D4a.batch --timings outputs/_analyses/deception-divergence/d4a/timings/d4a.json
```

D4(b), the after-cue arm on the sycophancy twins:

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence && mkdir -p logs && sbatch --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence --time=00:45:00 --partition=gpuA100x4 --account=bgrb-delta-gpu --nodes=1 --gpus-per-node=1 --cpus-per-task=1 --mem=64G --job-name=d4b-after-cue --output=logs/d4b_after_cue_%j.out --wrap 'export HF_HOME=/work/nvme/beto/swong2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1; exec /u/swong2/.conda/envs/mgnp/bin/python scripts/b3_patch.py --task syc --sets S_all,heads_only --positions after_cue,post_tag --null 20 --out outputs/_analyses/deception-divergence/d4b'
```

D4(c), SDR route closure:

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence && mkdir -p logs && sbatch --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence --time=01:15:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/analyze_components.sbatch batch docs/research/deception-divergence/jobs/D4c-sdr.batch --timings outputs/_analyses/deception-divergence/d4c/timings/sdr.json
```

D4(c) readings, on CPU after the job. They apply the T2 rule, query share minus key share against 0.15, with T1 on the
R9 offline estimator, which is the default:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/route_closure_readings.py outputs/_analyses/deception-divergence/d4c/sdr/Ct__leaf/sdr_v2/route_closure/route_closure.json --out-dir docs/research/deception-divergence/results/d4c
```

The output files are named `b1_readings.json` and `b1_readings.md`, because the script hard-codes those names.

## What is NOT done

- Riders (a), (b) and (c) are not submitted, as the ticket says. Their results, and the D4(c) readings, wait for the
  jobs.
- The Bridges-2 route is not ready for these jobs. `scripts/remote/b2.sh` fetches only `mechanism-analysis-*` and
  `instructed-route-b1*` under `outputs/_analyses/`, so a Bridges-2 run of any D4 rider would not come back to Delta
  without a glob for `deception-divergence*`. The branch also has to be pushed and synced with `sync-code --branch
  deception-divergence` first, and the SU balance was not checked. I did not edit `b2.sh`, because the D1 worker may
  need the same line.
- `scripts/jobs/run_b3_patch.sh` refuses any cwd but the instructed-route worktree, so the D4(b) command below calls
  the interpreter directly instead of changing that wrapper.
- I did not run `sbatch --test-only` for any rider.

## Open questions

- D4(b) sets: the ticket names S_all. I added `heads_only` and the `post_tag` arm in the same job, because the F-rte-008
  caveat is whether mlp.5 to mlp.7 act over the cue window. That needs S_all and its heads alone on both spans, and
  `post_tag` reproduces J4's S_all number (0.724) as the in-run anchor. Default: submit as written. Dropping the
  extra sets saves about 0.1 GPU-hour.
- P1 scope: the score of record is the stacked quartet W_Q, because the spec says "the quartet's W_Q" and that form
  is exactly RoPE-invariant. The literal Elhage W_QK form and the per-head scores are beside it and decide nothing.
  Default: keep.
- P2 power: see the ceiling numbers above. Default: report P2 as failed under the frozen rule, with the ceiling as its
  caveat. Do not re-specify the read after seeing the result.
