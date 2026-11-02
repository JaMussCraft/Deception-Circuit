# Hand-back 01: D1 scoring pipeline (listener knowledge and the role-matched operator-turn inversion)

Agent: Opus worker (claude-opus-5-5), direction deception-divergence. Ticket: the orchestrator's D1 message of Mon 2
Nov 2026 (START.md section 2 item D1, section 10 "D1 done", spec.md rulings R1 to R4). Status: resolved. The
pipeline is built, tested on both interpreters and dry-run through its wrapper. No GPU job was submitted.

## What changed

All files are in the worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
Nothing is staged for the apply tool. No existing file was edited; the pinned builders are imported only.

- Committed by the orchestrator from the worktree:
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/d1_visibility.py`,
    new. Four stages: `sample`, `build --dry-run`, `score` and `read`.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d1_visibility.py`,
    new, 24 tests.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/jobs/run_d1_visibility.sh`,
    new Slurm wrapper for Delta and Bridges-2.
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/01-handback.md`,
    this file.
- Not committed, because `outputs/_analyses/` is git-ignored. The CPU outputs of the verification runs are in
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/outputs/_analyses/deception-divergence/d1/<task>/`:
  `sample.jsonl`, `sample_report.json` and `build_report.json` for far_v2, sdr_v2 and ser_v2. The GPU job regenerates
  the sample and refuses to overwrite a different one, so these files are a check, not an input the job needs.

How the stages work:

- **Context.** The cell, spec and framing come from each stored dataset's `provenance.json`, so the pilot selection
  file in Alignment `.scratch` is not needed. Every pool file except the neutral pool is checked against the
  provenance sha256. The seeded lists come from `build_deception_v2.shared_instance_lists` on the plan in
  `filter_report.json`, seed 42, with the builder's `_gate_pairs`.
- **Scored prefix.** The build scored only part of the plan's test list for two tasks. The candidates are that scored
  prefix, read from the base test chunks in `filter_report.json` "compute".

| task | plan test count | scored prefix | anchor positions |
| --- | --- | --- | --- |
| far_v2 | 162,500 | 140,000 | max 139,656 |
| sdr_v2 | 54,168 | 40,000 | max 39,964 |
| ser_v2 | 81,588 | 81,588 | max 81,542 |

- **Sample.** The draw is stratified by pressure clause id and designation polarity, which gives 50 cells per task.
  Each cell draws ceil(200 / rate) unselected ids, at the R3 rates 0.42, 0.31 and 0.32. The 1,000 selected test ids
  are appended as anchors with their stored margins, `h_*` fields and stored `<task>_inversion` pick. No cell was
  short. The smallest unselected pool per cell was 2,704 for FAR and 729 for SDR.
- **Arms.** P is the builder's `neutral_prompt`, scored once with pairs (item_1, item_2) as `gate_chunk` does. D is
  `render_pressure`. Each listener arm passes the clause plus one space plus the R2 sentence as the clause argument of
  `build_prompt_pair`, so the sentence ends the system turn directly after the clause. I is the same clause surgery
  `build_inversion_v2.inversion_row` uses, with `build_inversion_v2.select` over every pool clause of D's task and
  form, and no token match, per the orchestrator's clarification.
- **Score.** The model is loaded once through `build_deception_v2._load_model`, which is `pilot_v2.load_model` in
  bf16. Every prompt goes through `dc.score_prompts` with the arguments `_score` uses, and the two item logits are kept.
  P is scored for every id. The other arms are scored only for prior-kept ids, |P margin| < 0.5 on the rescore, and
  for the anchors. Anchors also get D and P at the builder's max length 120 and batch 32 as a same-path control.
  Chunks of 2,000 ids are written atomically, and a rerun skips finished chunks. `run_manifest.json` records DD_COMMIT,
  which must be 40 hex characters or the stage exits. It also records code and pool hashes, the sample hash, the model,
  cluster, job id, GPU and library versions.
- **Read.** R1 primary compliance is `contingency._deceptive` at 0.7. Secondary compliance is clean-stream choice
  "b". The verdict pool is the prior-kept sampled ids; the anchors are excluded. Each comparison reports its
  matched-pool count per task and per cell. The interval is a 95 percent percentile bootstrap with 2,000 resamples,
  clustered by D's pressure clause id; an I row is clustered under the D clause it replaces. The listener verdict reads
  phrasing 1 first, then 2 and 3 only if 1 is null. It needs |visible minus hidden| of at least 10 points with the
  interval excluding zero. The override verdict needs I minus D of at least 10 points, and its interval is reported.
  The anchor check reports the signed mean, mean absolute difference, exact share, shares within one and two bf16 ulps,
  the two-ulp tail share, sign flips and the own-field gap. A sign-flip rate above 1 percent marks every verdict "not
  read". The read stage writes `readings.json` and `readings.md` under the out-root, and every table carries
  denominators.
- **Length.** Every arm fits the builder's 120 tokens: the longest arm is 113 tokens on FAR, 118 on SDR and 116 on
  SER. The default max length is therefore 120, so D is scored on the builder's exact path and no row is dropped.
  A row whose longest arm exceeds `--max-seq-length` is dropped from every arm and counted.

## How verified

Sample stage, mgnp interpreter (it was first run directly, then again through the wrapper, which reported "sample
unchanged" for every task):

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -I scripts/d1_visibility.py sample
```

Observed:

```
far_v2: prefix 140000 of 162500; sampled 23850 over 50 cells (477 per cell requested); anchors 1000 byte-identical {'clean_prompt': '1000/1000', 'corrupt_prompt': '1000/1000', 'neutral_prompt': '1000/1000'}; out of window 0; cells below floor 0
sdr_v2: prefix 40000 of 54168; sampled 32300 over 50 cells (646 per cell requested); anchors 1000 byte-identical {'clean_prompt': '1000/1000', 'corrupt_prompt': '1000/1000', 'neutral_prompt': '1000/1000'}; out of window 0; cells below floor 0
ser_v2: prefix 81588 of 81588; sampled 31250 over 50 cells (625 per cell requested); anchors 1000 byte-identical {'clean_prompt': '1000/1000', 'corrupt_prompt': '1000/1000', 'neutral_prompt': '1000/1000'}; out of window 0; cells below floor 0
```

The anchor byte-identity check passes 1,000 of 1,000 on every task for the D clean prompt, the D corrupt prompt and
the P prompt. The sample stage exits unless all three match. The sample hashes are FAR `f4c36f9d9d91`, SDR
`900dcc770dde` and SER `cfe13594eeb4`. The clause-form table agrees with the text rule on every clause it lists:
12 of 12 for FAR and 20 of 20 for SDR.

Wrapper dry run on the login node, mgnp through the Delta profile, no git call:

```
bash scripts/jobs/run_d1_visibility.sh --dry-run
```

Observed (exit 0; per-arm token maxima shown, full histograms in `build_report.json`):

| task | ids | sampled | anchors | length drops at 120 | longest arm | I coverage | expected forwards |
| --- | --- | --- | --- | --- | --- | --- | --- |
| far_v2 | 24,850 | 23,850 | 1,000 | 0 | 113 (L3 hidden) | 18,172 of 24,850 | 198,201 |
| sdr_v2 | 33,300 | 32,300 | 1,000 | 0 | 118 (L3 hidden) | 33,300 of 33,300 | 212,508 |
| ser_v2 | 32,250 | 31,250 | 1,000 | 0 | 116 (L3 hidden) | 32,250 of 32,250 | 211,250 |

- **FAR I coverage.** FAR's pool has only act-naming clauses. The seven predicate or other D clauses get no I arm:
  r8_rule_strong_far_v2_02, 04, 16 and 17, and shared_00, 02 and 03. Each drops 954 ids.
- **Token-match counts.** These ids would also have passed `build_inversion_v2`'s standalone and token-count match
  without the twin half. The chosen clause itself passes on far fewer.

| task | any clause passes | chosen clause passes |
| --- | --- | --- |
| far_v2 | 16,264 of 18,172 | 4,039 |
| sdr_v2 | 33,300 of 33,300 | 7,166 |
| ser_v2 | 31,000 of 32,250 | 9,504 |

- **Anchors against the stored I picks.** With the token match, `select` reproduces the stored
  `<task>_inversion` pick on 1,000 of 1,000 anchors in every task, which confirms the salt and hash. The form-only D1
  pick agrees with the stored pick on 246 FAR anchors, 193 SDR anchors and 285 SER anchors. No anchor has a same-form
  set equal to its token-matched set.
- **Prompt counts per arm.** Every pair arm has 2 x ids prompts. P has one prompt per id. The anchor controls add
  2,000 D prompts and 1,000 P prompts per task.

The wrapper dry run was repeated on the final code (only a docstring changed afterwards), exit 0. Its output after
the header line is identical to the first run, compared with `diff`. Each task reported "sample unchanged".

The same two stages on the base interpreter, into a scratch out-root:

```
OMP_NUM_THREADS=4 /sw/external/python/anaconda3/bin/python3.9 -I scripts/d1_visibility.py sample --out-root <job tmp>/py39
OMP_NUM_THREADS=4 /usr/bin/time -v /sw/external/python/anaconda3/bin/python3.9 -I scripts/d1_visibility.py build --dry-run --out-root <job tmp>/py39
```

Observed:

- **Sample.** The same three summary lines as on mgnp, with 1,000 of 1,000 byte-identical anchors per task. The
  `sample.jsonl` sha256 is identical across the interpreters on all three tasks.
- **Build.** Exit 0, wall clock 32:47, maximum resident set 640,624 kB. Each task's `build_report.json` equals the
  mgnp one on every key except `created` and `seconds_cpu`.
- **A killed first attempt.** The first py3.9 build was killed with exit 137 during SER. My cgroup showed `oom_kill
  0`, and the login node was under memory pressure from other sessions' processes of 2 to 2.5 GB each. At that point
  the build held every row's prompts at once. I changed `build` to stream rows, and `score` to check every task's
  sample before loading the model and then build prompts one task at a time. The rerun above is on that code. The
  score-path change is tested only through the stub end-to-end test, not on a GPU node.

Unit and integration tests, both interpreters:

```
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_d1_visibility.py -q -k "not end_to_end"
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_d1_visibility.py -q -k "end_to_end"
OMP_NUM_THREADS=4 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_d1_visibility.py -q -rs -k "not end_to_end"
```

Observed: mgnp `23 passed, 1 deselected`, then `1 passed, 23 deselected`; base py3.9 `23 passed, 1 deselected`.
On py3.9 with `HF_HUB_OFFLINE=1`, the tokenizer tests skip because transformers 4.57 will not resolve the cached
tokenizer offline (`OfflineModeIsEnabled`). Without the flag they run and pass. The tests cover:

- D, corrupt and P prompts byte-identical to 60 stored anchor rows per task.
- The listener sentence placed directly after the clause, once, in both streams, with item alignment holding in
  every arm.
- `pick_inversion` equal to `build_inversion_v2.select` over the same-form clauses, and the salted sha1 index.
- On stored `<task>_inversion` rows, `candidates` plus `select` reproduces every stored pick, and the clause surgery
  reproduces the stored I prompts: 13, 52 and 14 kept rows checked of the first 60 D rows.
- The scoring wrapper returns `_score`'s fields exactly.
- The P gate and the anchor controls of `score_chunk`, including the controls at length 120 and batch 32, and the
  DD_COMMIT refusal.
- R1 compliance, the clustered bootstrap, the paired comparison and its per-cell counts, the phrasing reading order,
  the 10-point override rule, the bf16 ulp, and the anchor check failing above 1 percent sign flips.
- A sample, build, score and read pass on far_v2 with a stub scorer.

Full suite, mgnp, before the memory change below. The final D1 file was rerun afterwards: 24 of 24 pass on both
interpreters.

```
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests -q -rf --basetemp=<job tmp>/pt_full_mgnp
```

Observed: `19 failed, 3733 passed, 23 skipped, 2 warnings, 101 errors in 1958.14s`.

- **The 101 errors.** All are FileNotFoundError at setup, on git-ignored artifacts of other directions that this
  worktree does not hold. Examples are `.superpowers/sdd/plan-sdr-cue-circuits/...`,
  `outputs/_analyses/sdr-routing-pilot/...` and `.scratch/selective-deception/...`.
- **The 19 failures.** None is in the D1 file. They come from `test_deception_common.py` (6), `test_sdr_shared_composition.py` (4),
  `test_selective_v6_manifest.py` (3), `test_sdr_cue_circuits.py` (2), and one each from `test_selective_v7.py`,
  `test_sdr_cue_positions.py`, `test_deception_tasks.py` and `test_benchmarks.py`.
- **Independence from this ticket.** I reran those eight files alone, without the D1 test module. The failing test
  names were identical, compared with `diff`, and the run ended `19 failed, 319 passed, 19 skipped, 1 warning, 52 errors`.
  No existing file was edited.
- **Comparison with main.** The main checkout's baseline list of names was not available to me, so I did not compare
  against it. The base py3.9 full suite was not run.

## Execution evidence

Not applicable: no runs. No GPU job was submitted and nothing was scored. The CPU dry runs above are the only
executions, with the commands and outputs given in "How verified".

Runtime estimate, from the expected forwards in the build reports. The pair arms run only on prior-kept ids and
anchors, at the R3 rates.

| quantity | value |
| --- | --- |
| expected forwards, three tasks | 621,959 |
| H100 rate (Bridges-2 `<task>_inversion` scoring, max length 120, batch 32) | 0.0042 s per forward |
| A100 rate (Delta v2 build, `filter_report` compute) | 0.011 s per forward |
| H100 total (44 min scoring, 8 min model load, about 10 min CPU preparation and sample) | about 1.05 GPU-h |
| A100 total | about 2.2 GPU-h |

Bridges-2 is preferred by START section 7. Push the branch, run `scripts/remote/b2.sh sync-code --branch
deception-divergence`, then submit:

```
scripts/remote/b2.sh submit --time 01:45:00 --script scripts/jobs/run_d1_visibility.sh --job-name d1-visibility
```

That is this sbatch on the Bridges-2 login node:

```
cd /ocean/projects/cis260361p/swong2/Deception-Circuit && mkdir -p logs && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 01:45:00 --job-name=d1-visibility scripts/jobs/run_d1_visibility.sh
```

Fetch the results with:

```
scripts/remote/b2.sh fetch outputs/_analyses/deception-divergence/d1
```

The Delta fallback runs from the worktree root after `mkdir -p logs`:

```
sbatch --time=03:00:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/jobs/run_d1_visibility.sh
```

## What is NOT done

- The GPU score and read stages have not run, so there are no compliance numbers, verdicts or anchor margins yet.
  The orchestrator submits the job.
- The H100 rate is the steady-state rate of a 2,000-forward job. The CPU preparation time inside the job is
  extrapolated from the final login-node build times on mgnp (284, 523 and 494 s, which include the token-match
  counting that the score stage skips). Neither has been measured inside this job.
- The anchor check compares against the stored margins, which carry the 2026-10-21 build's bf16 drift (instructed-
  route R7). With max length 120 the D arm is on the builder's path, so the D_at120 control differs only in batch
  composition.
- I did not commit, push or sync to Bridges-2; workers never run git.

## Open questions

- **Candidate pool is the scored prefix.** The build never gated the last 22,500 FAR and 14,168 SDR test-list
  entries, so they are not candidates. Default: sample from the scored prefix only. That is the population the funnel
  rates and the selected ids come from.
- **I pick without the token match.** Per the clarification, the D1 I clause is `select` over every same-form pool
  clause. It agrees with the stored `<task>_inversion` pick on only 19 to 29 percent of anchors, and no anchor has
  equal form and token sets. So the D1 I arm is not the stored I condition, and its prompt lengths differ from D for
  most ids. Default: keep the form-only pick and report the token-match counts beside it.
- **FAR I coverage.** Seven FAR clauses have no form-matched I, so the FAR honesty-override pool covers 18 of 25
  clauses. Default: report it per clause and do not borrow act-naming I clauses for predicate or other D clauses.
- **The verdict pool excludes the selected ids.** These are the "unselected" candidates of START, which slightly
  under-represents D-compliant ids in the population. Default: as built; the anchors' arm compliance is reported
  separately, labelled descriptive.
- **Reading direction of the listener rule.** The rule says compliance "differs", so either sign passes. The sign is
  reported. Default: two-sided, as implemented.
- **Override interval.** R4 reads the override against 10 points without naming an interval. Default: the point
  estimate decides, and the interval and whether it excludes zero are reported beside it.
