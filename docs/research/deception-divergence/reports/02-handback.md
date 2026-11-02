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

## Addendum: GPU riders

The orchestrator submitted the three riders on Delta interactive partitions from commit c6752c0 on Mon 2 Nov 2026. I
monitored them, read them and record them here. Every elapsed time is sacct's `Elapsed` for the job allocation.

Follow-up edit in the same pass, for the orchestrator to commit:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/remote/b2.sh`, where
`FETCH_ANALYSIS_GLOBS` gains `deception-divergence*` and keeps the two existing globs. The test is in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d4_jobs.py`
(`test_b2_fetch_brings_back_the_deception_divergence_root_and_keeps_the_old_globs`). Every suite that touches `b2.sh`
passes: mgnp "142 passed", base "142 passed". The sync dry run follows:

```
bash scripts/remote/b2.sh sync-code --dry --branch deception-divergence
```

Observed: exit 0. Both SSH masters were open (`ssh -O check` answered "Master running" for bridges2 and b2dtn). It
printed one command and ran nothing. Over `ssh -o BatchMode=yes bridges2`, that command would:
1. In `/ocean/projects/cis260361p/swong2/Deception-Circuit`, run `git fetch origin
   +deception-divergence:refs/remotes/origin/deception-divergence`.
2. Check out a local `deception-divergence` branch, creating it with `--track origin/deception-divergence` if absent.
3. Fast-forward it to origin, or `reset --keep` after a force-push, printing the old head.
4. Print `git status --short` and `remote_head`.
A real `fetch` writes into `$DC_REPO_ROOT`, which the Delta profile defaults to the mechanism-analysis worktree. A
fetch for this direction therefore needs `DC_DELTA_REPO_ROOT=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.

### D4(a): the quartet's attention under D against the twin

- Job id and cluster: 23443932 on Delta (gpuA100x4-interactive, host gpua001).
- Slurm state: COMPLETED, exit 0:0, elapsed 134 s. The timings file records a 24.6 s model load, 65.5 s for far and
  40.2 s for ser.
- Row counts: far and ser each profile 100 of 100 held-out ids on both sides. `pressure_neutral_twin_paired` and
  `neutral_twin` carry identical `instance_ids`. Every pair aligns: 100 pairs, 0 differing outside the clause, 0
  identical to the pressure prompt. Rows sum to one, with 0 NaN. The split is 52 identity and 48 inversion on both
  tasks, as the dry run's sample showed. `patterns.json` records `"instances": "causal_sample"`.
- Baseline reproduces: the cell holds 62 heads on far and 68 on ser, as the dry run printed. The four quartet heads
  read KV group 6.
- Provenance file: `outputs/_analyses/deception-divergence/d4a/{far,ser}/Ct__leaf/<task>_v2/run_manifest.json`,
  commit `c6752c05478c2e0b6f8b6b18df3ca3f478de9afb`. `git_dirty` is true from other workers' untracked files. The sha256
  of `component_analysis/attention_patterns.py` in the worktree equals `git show c6752c0:` of it (c1780949).

Reading (descriptive, deciding nothing). **Yes: the pressure changes which positions the quartet attends to from the
Readout, on both tasks.** The measure is half the L1 distance between the mean per-Segment mass under D and under the
twin. It is a total-variation distance between the two mean attention profiles over 19 Segments. Paired standard
errors exist only for the clause mass, which is the B2 column.

| task | head | shift D against twin | rank of the shift among C_t heads | median of the other C_t heads (90th pct) |
|---|---|---|---|---|
| far | L17H24 | 0.329 | 8 of 62 | 0.100 (0.312) |
| far | L17H25 | 0.243 | 13 of 62 | |
| far | L17H26 | 0.476 | 2 of 62 | |
| far | L17H27 | 0.198 | 17 of 62 | |
| ser | L17H24 | 0.166 | 7 of 68 | 0.041 (0.158) |
| ser | L17H25 | 0.155 | 10 of 68 | |
| ser | L17H26 | 0.316 | 2 of 68 | |
| ser | L17H27 | 0.058 | 26 of 68 | |

Where the mass moves, as the quartet mean over the 100 ids, D against twin:

| task | Segment | D | twin |
|---|---|---|---|
| far | designating_sentence | 0.064 | 0.184 |
| far | designation_suffix | 0.015 | 0.077 |
| far | item_2_question_pair | 0.167 | 0.092 |
| far | item_2_question_option | 0.118 | 0.051 |
| ser | designation_suffix | 0.024 | 0.129 |
| ser | pressure_clause | 0.067 | 0.020 |
| ser | unsegmented | 0.168 | 0.128 |
| ser | item_1_question_pair | 0.060 | 0.039 |

On far, under pressure the quartet reads less of the designation and more of the item options. L17H26 drops from
0.453 to 0.151 on the designating sentence, and L17H24 rises from 0.205 to 0.377 on item 2's question pair. On ser,
under pressure it reads less of the designation suffix and more of the pressure clause. The B2 clause-mass drops are
L17H26 0.094 (SE 0.011) and L17H25 0.071 (SE 0.007) on ser, and under 0.013 for every quartet head on far. The same
direction holds in the identity and the inversion halves. So the query-side entry of F-rte-006 comes with a change in
where the quartet looks, not only in what it writes. Whether that attention shift carries the effect is not tested
here; B1's key restoration at the options was about zero.

### D4(b): the after-cue arm of J4

- Job id and cluster: 23443933 on Delta (gpuA100x8-interactive, host gpuc05).
- Slurm state: COMPLETED, exit 0:0, elapsed 1,048 s. Pass 2 took 977 s.
- Row counts: 800 items with 0 dropped, 530 kept and 154 flips, identical to J4 (800, 530, 154). There were 84 arms,
  with 20 null draws per set and position.
- Baseline reproduces: S_all at `post_tag` f = 0.7241 (0.7017 to 0.7463) against J4's 0.724, with null maximum 0.5051
  against J4's 0.505. heads_only at `post_tag` f = 0.4984 (0.4699 to 0.5262) against the supplement's 0.4984, with
  null maximum 0.2706 against 0.2706. Each null set reproduces its recorded maximum exactly.
- Provenance file: `outputs/_analyses/deception-divergence/d4b/run_manifest.json`, commit
  `c6752c05478c2e0b6f8b6b18df3ca3f478de9afb`, slurm_job_id 23443933, model revision 0e9e39f2. `git_dirty` is true from
  other workers' files. The sha256 of `spontaneous/patching.py` (05a26445) and `scripts/b3_patch.py` (447416db)
  equals the committed files.

| set at positions | f (kept, 95% CI) | flip reversal | null f max (20 draws) | draws at or above f |
|---|---|---|---|---|
| S_all at after_cue | 0.662 (0.644 to 0.679) | 0.825 | 0.383 | 0 |
| S_all at post_tag | 0.724 (0.702 to 0.746) | 0.942 | 0.505 | 0 |
| heads_only at after_cue | 0.582 (0.563 to 0.601) | 0.779 | 0.346 | 0 |
| heads_only at post_tag | 0.498 (0.470 to 0.526) | 0.805 | 0.271 | 0 |

Reading (rule: report the numbers). Every row's cue window is 7 tokens, followed by 23 after-cue positions.
- **Mostly downstream of the cue window.** Patching S_all only after the window keeps 0.662 of the cue effect, 91
  percent of its 0.724 over the whole post-tag span. So the transfer runs mainly through state computed after the
  cue, not through substituting the cue tokens.
- **The cue window costs the heads alone.** heads_only does better after the cue (0.582) than over the whole span
  (0.498).
- **What the MLPs add.** S_all minus heads_only falls from 0.226 at `post_tag` to 0.080 at `after_cue`. So most of
  mlp.5 to mlp.7's extra contribution sits on the cue window itself, which answers the F-rte-008 caveat.
- **No longer non-specific.** At `after_cue`, S_all's null maximum is 0.383, under the R5 non-specific line of 0.5.
  The "shared, non-specific" label of F-rte-008 came from the `post_tag` arm, where the null reached 0.505. On the
  after-cue span, S_all reads as shared and specific against its R10a nulls. This is a reading, not a re-decision of
  F-rte-008, whose frozen arm is `post_tag`.

### D4(c): SDR key against query on the B1 code path

The orchestrator cancelled the Delta submission, job 23443934 (gpuH200x8-interactive). It never started, because
squeue had projected its start at Wed 4 Nov 11:52 CST. The orchestrator resubmitted it on Bridges-2.

- Job id and cluster: 50132625 on Bridges-2 (GPU-shared, H100-80, host w001.ib.bridges2.psc.edu).
- Slurm state: COMPLETED, exit 0:0, elapsed 1,868 s. The timings file records a 394 s model load and 1,711 s for the
  line, which fits the 0.6 GPU-hour estimate above.
- Fetch:
  `DC_DELTA_REPO_ROOT=<this worktree> bash scripts/remote/b2.sh fetch outputs/_analyses/deception-divergence/d4c`
  exited 0. The local dry-run files were replaced by the job's and kept as `.pre-b2fetch` backups.
  `route_closure.json` arrived at 5,113,046 bytes, the same as on Bridges-2. The job log was copied to
  `logs/bridges2/analyze_components_50132625.out`.
- Row counts: 100 instances in `baseline.m_D` and in `instances.pressure_ids`, over 19 pressure-id clusters. The
  sample ids equal the 100 ids of `phase1/groups/sdr_heldout_D_sample.json`. The grid is 66 Components (ct.json sdr),
  with 47 arms.
- Baseline reproduces:
  - Gate G1 is bit-identical (max absolute difference 0.0), and G2's max difference is 0.0.
  - G3 passed: the largest per-sender difference is 0.00031 (T:head.13.7) against 0.01, and the summed difference is
    0.0138 against 0.02.
  - The readings tool reproduces B1's far T2 row exactly (r_Q 0.321, r_K -0.012) when given B1's far file. That check
    is under How verified; this job ran sdr only.
- Provenance file: `outputs/_analyses/deception-divergence/d4c/sdr/Ct__leaf/sdr_v2/run_manifest.json`, commit
  `c6752c05478c2e0b6f8b6b18df3ca3f478de9afb`, dirty flag false, slurm_job_id 50132625, model revision 0e9e39f2.

Readings, which ran on the Delta login node with exit 0:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/route_closure_readings.py outputs/_analyses/deception-divergence/d4c/sdr/Ct__leaf/sdr_v2/route_closure/route_closure.json --out-dir docs/research/deception-divergence/results/d4c
```

They wrote `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/results/d4c/b1_readings.json`
and `.md`, for the orchestrator to commit.

| task | P | r_Q | r_K | r_K - r_Q | r_out | T2 frozen rule |
|---|---|---|---|---|---|---|
| sdr_v2 | 6.547 | 0.524 (0.488 to 0.556) | -0.002 (-0.012 to 0.008) | -0.526 (-0.556 to -0.490) | 0.558 (0.524 to 0.589) | query-side |
| far_v2 (B1) | 9.886 | 0.321 | -0.012 | -0.333 | 0.327 | query-side |
| ser_v2 (B1) | 5.960 | 0.426 | 0.014 | -0.412 | 0.433 | query-side |

**Verdict on the D4(c) rule: query-side on SDR.** r_Q minus r_K is 0.526, against the 0.15 margin, with the interval
far from it. On one code path and one estimator, SDR therefore looks like FAR and SER. The SDR-against-FAR/SER
contrast of F-sdr-012 against F-rte-006 does not survive. F-sdr-012's key-side account came from a different setup:
the earlier sdr-routing pilot, its candidate perturbations and a truth margin on confirmation stories. So the contrast
belonged to the method or the dataset, not to the tasks.

T1, reported beside the rule and not part of D4(c)'s rule:

| task | O | O_q | M_q | M_C3 | max C1/C2 | M_S | label |
|---|---|---|---|---|---|---|---|
| sdr_v2 | 0.857 (0.823 to 0.891) | 0.468 | 0.546 (0.511 to 0.577) | -0.032 | 0.022 | 0.821 | closes, route-specific |

On sdr_v2 the loop closes through the quartet: M_q is 0.546 on the R9 offline estimator, and 0.550 on the forward
estimator. That differs from the bypass on FAR (0.360) and SER (0.462). The lower interval end of 0.511 sits close to
the 0.50 bar.
