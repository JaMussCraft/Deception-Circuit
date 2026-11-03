# Hand-back 06: D1 follow-up under ruling R6 (phrasing 4, content-clause reading, flip pools)

Agent: Opus worker (claude-opus-5-5), direction deception-divergence. Ticket: the lead's brief of Mon 2 Nov 2026, the
option B follow-up to D1, pre-registered as ruling R6 in `docs/research/deception-divergence/spec.md`. Status:
resolved for the CPU parts. The phrasing-4 GPU job is built, dry-run and ready for the orchestrator to submit.

## What changed

Committed by the orchestrator from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/d1_followup.py`
  is new. It imports `scripts/d1_visibility.py` without editing it. It has three stages: `build` (CPU report),
  `score` (GPU) and `read` (CPU).
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/jobs/run_d1_followup.sh`
  is new. It is modeled on `run_d1_visibility.sh`, covers Bridges-2 and Delta, and runs `build --dry-run` under
  `--dry-run`. It has no sample stage, because the ids are D1's.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d1_followup.py`
  is new, with 15 tests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/06-handback.md`
  is this file.

Written under `outputs/_analyses/deception-divergence/d1/`, which is git-ignored:

- `followup_readings.json` and `followup_readings.md` hold the read on phrasings 1 to 3. The job's read stage
  overwrites them once phrasing 4 is scored.
- `<task>/build_report_l4.json`, one per task, comes from the wrapper dry run.

Nothing was staged for the apply tool. D1's own files (`sample.jsonl`, `scores.jsonl`, `run_manifest.json`,
`readings.*`, `chunks/`) are untouched.

**Deviation from the brief.** The brief names the phrasing-4 manifest `run_manifest.json`. That name would overwrite
D1's manifest, which records D1's commit, job id and scores hash and which D1's read stage checks. The score stage
therefore writes `run_manifest_l4.json` and keeps its chunks in `chunks_l4/` with their own `run_key.json`.

**One addition beyond the brief.** The score stage also rescores D on the 1,000 anchors per task, in an arm called
`D_repro`, at the builder's length 120 and batch 32. The phrasing-4 flip pool combines D from the D1 job with L4 from
the new job. This control measures the per-id agreement between the two jobs and costs 6,000 forwards.

**How the code works.**

- **Inputs.** Every stage refuses to run unless D1's `sample.jsonl` and `scores.jsonl` hash to the values in D1's
  `sample_report.json` and `run_manifest.json`.
- **Live ids.** The live ids are D1's: prior-kept on D1's own P rescore, plus the anchors. P is not rescored.
- **Phrasing 4 prompts.** The L4 arms are built by string surgery on the builder's D prompts. The sentence goes after
  the user turn's response-format instruction, before the user turn's end token. The code asserts that the user turn
  occurs once, that the system turn and assistant stem are unchanged, and that the item-swap alignment holds.
- **Read inputs.** The read merges `scores_l4.jsonl` when it exists and refuses one made against other D1 inputs.

## How verified

```
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d1_followup.py tests/test_d1_visibility.py --basetemp=/u/swong2/.claude/jobs/5b9b1c28/tmp/pt_mgnp2
```

Observed: `46 passed in 80.70s`. The 46 are the 15 new tests and the 31 existing D1 tests, with none skipped.

```
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_d1_followup.py tests/test_d1_visibility.py --basetemp=/u/swong2/.claude/jobs/5b9b1c28/tmp/pt_base2
```

Observed: `46 passed, 1 warning in 97.68s`. The warning is the pandas bottleneck version notice.

The new tests cover these points:

- **Prompt construction.** The L4 arms are built against the user turn read off the stored far_v2 rows. Each arm
  equals the stored prompt with the sentence inserted. The system turn and stem are unchanged, and the alignment
  holds.
- **Token twins.** Visible and hidden are twins of D plus 9 tokens.
- **Input guards.** A missing or repeated user turn raises. The D1 hash guard refuses altered scores.
- **Score chunk.** It scores the L4 arms and puts D_repro on the anchors only, at length 120 and batch 32.
- **Flip pools.** The tests use synthetic rows for the D gate, the inclusive 0.3 honest gate and the one-stream case.
  They also cover the reverse pool, all four definitions and the shared-clause split.
- **Admission rule.** 400 ids over 10 clauses admits. 399 ids, or 9 clauses, does not.
- **Content-clause exclusion.** The read excludes the shared clauses and both phrasing-4 verdicts are read. The
  D_repro control check, `merge_l4` and the context table are covered.
- **End to end.** A build, score and read run with a stub scorer on 30 real D1 rows passes. It resumes, and D1's
  manifest is not touched.

```
bash scripts/jobs/run_d1_followup.sh --dry-run
```

Observed: exit 0. The key lines:

```
d1-followup: host dt-login04.delta.ncsa.illinois.edu, cluster delta, job none, commit none, python /u/swong2/.conda/envs/mgnp/bin/python, dry-run 1
far_v2: 10954 live ids (1000 anchors), 0 dropped for length > 120; L4 visible - hidden tokens per id {0: 10954}
  D           tokens min 94 median 98 p99 101 max 101
  L4_visible  tokens min 103 median 107 p99 110 max 110
  L4_hidden   tokens min 103 median 107 p99 110 max 110
  phrasing 1 twins: 21908/21908 same length, 21908/21908 one differing position
  phrasing 4 twins: 21908/21908 same length, 21908/21908 one differing position
  forwards expected {'L4_pairs': 43816, 'D_repro_anchors': 2000, 'total': 45816}; 40.1 s
sdr_v2: 10563 live ids (1000 anchors), 0 dropped for length > 120; L4 visible - hidden tokens per id {0: 10563}
  L4_visible  tokens min 107 median 111 p99 115 max 115
  phrasing 1 twins: 21126/21126 same length, 21126/21126 one differing position
  phrasing 4 twins: 21126/21126 same length, 21126/21126 one differing position
  forwards expected {'L4_pairs': 42252, 'D_repro_anchors': 2000, 'total': 44252}; 35.1 s
ser_v2: 10846 live ids (1000 anchors), 0 dropped for length > 120; L4 visible - hidden tokens per id {0: 10846}
  L4_visible  tokens min 105 median 110 p99 113 max 113
  phrasing 1 twins: 21692/21692 same length, 21692/21692 one differing position
  phrasing 4 twins: 21692/21692 same length, 21692/21692 one differing position
  forwards expected {'L4_pairs': 43384, 'D_repro_anchors': 2000, 'total': 45384}; 35.1 s
```

So every L4 arm fits the builder's own length of 120, and no row is dropped. L4 is therefore scored on the same
length and batch path as D1's D. The two L4 arms have the same token length on every id, so the per-id difference is
0 on all 32,363 live ids. They differ at exactly one position, " can" against " cannot", on every id and stream. The
same holds for phrasing 1.

## Results

All numbers come from the read stage on the D1 scores of Bridges-2 job 50145353. Points are percentage points.
Intervals are the R4 clause-clustered 95 percent bootstrap with 2,000 resamples and seed 20261102. The pool is the
unselected prior-kept ids.

### Flip pools for U1, phrasing 1 (R6 iii)

**No primary flip pool exists for phrasing 1, and U1 is not admitted on any task.**

| task | matched ids | D compliant | forward pool | clauses | reverse pool | admit U1 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| far_v2 | 9,954 | 1,326 | 0 of 9,954 | 0 | 0 of 9,954 | no |
| sdr_v2 | 9,563 | 4,789 | 0 of 9,563 | 0 | 0 of 9,563 | no |
| ser_v2 | 9,846 | 1,715 | 0 of 9,846 | 0 | 0 of 9,846 | no |

The 1,000 anchors of each task also give 0 forward and 0 reverse ids.

**Why the pool is empty.** Among the ids that comply under D, no listener sentence of phrasings 1 or 2 brings a single
id to the honest gate, in either polarity. The I arm does, so the gate is reachable. The maximum, over D-compliant
ids, of the smaller stream margin under L1 visible is -0.625, -0.25 and -0.5 for FAR, SDR and SER.

| task | D compliant | honest under L1 visible | L1 hidden | L2 either arm | L3 visible | L3 hidden | I |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| far_v2 | 1,326 | 0 | 0 | 0 | 0 | 0 | 214 of 1,318 |
| sdr_v2 | 4,789 | 0 | 0 | 0 | 8 | 0 | 76 of 4,789 |
| ser_v2 | 1,715 | 0 | 0 | 0 | 0 | 0 | 190 of 1,715 |

**Secondary definitions, for information only.** These definitions decide nothing.

| task | definition | forward n of matched | clauses | content / shared | reverse n | reverse clauses |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| far_v2 | clean-stream argmax only | 22 of 9,954 | 10 | 20 / 2 | 198 | 18 |
| far_v2 | primary, no D gate | 0 of 9,954 | 0 | 0 / 0 | 0 | 0 |
| far_v2 | compliance lost (visible not R1-compliant) | 13 of 9,954 | 5 | 12 / 1 | 208 | 14 |
| sdr_v2 | clean-stream argmax only | 123 of 9,563 | 18 | 80 / 43 | 135 | 22 |
| sdr_v2 | primary, no D gate | 172 of 9,563 | 6 | 3 / 169 | 0 | 0 |
| sdr_v2 | compliance lost | 109 of 9,563 | 19 | 104 / 5 | 177 | 21 |
| ser_v2 | clean-stream argmax only | 62 of 9,846 | 22 | 58 / 4 | 24 | 12 |
| ser_v2 | primary, no D gate | 0 of 9,846 | 0 | 0 / 0 | 0 | 0 |
| ser_v2 | compliance lost | 68 of 9,846 | 12 | 67 / 1 | 52 | 15 |

The SDR no-D-gate pool of 172 sits almost entirely on the shared stakes clauses. There the hidden sentence raises
compliance from 3.2 to 26.8 percent, which is review 02's issue 4. FAR's reverse pools are the larger side of the
visibility effect: the visible arm complies where the hidden arm does not. Under the primary definition they are
still 0.

### Content-clause reading (R6 ii)

The excluded clauses are shared_00 to shared_04 in every task. Under this reading the content pools hold 8,380 FAR
ids, 7,741 SDR ids and 7,947 SER ids over 20 clauses each. The shared pools hold 1,574, 1,822 and 1,899 ids. The rule
is descriptive for phrasings 1 to 3.

| task | comparison, primary | a k of n | b k of n | a - b | interval |
| --- | --- | ---: | ---: | ---: | --- |
| far_v2 | L1 visible - hidden | 1,285 of 8,380 | 1,034 of 8,380 | +3.0 | +1.4 to +4.9 |
| far_v2 | L2 visible - hidden | 1,179 | 1,201 | -0.3 | -0.9 to +0.4 |
| far_v2 | L3 visible - hidden | 1,170 | 1,179 | -0.1 | -1.4 to +1.1 |
| far_v2 | I - D (16 clusters) | 846 of 6,328 | 1,315 of 6,328 | -7.4 | -17.4 to +1.7 |
| far_v2 | L1 hidden - D | 1,034 | 1,315 | -3.4 | -5.8 to -1.2 |
| sdr_v2 | L1 visible - hidden | 4,273 of 7,741 | 4,346 of 7,741 | -0.9 | -2.8 to +0.9 |
| sdr_v2 | L2 visible - hidden | 4,296 | 4,307 | -0.1 | -3.5 to +3.0 |
| sdr_v2 | L3 visible - hidden | 4,263 | 4,158 | +1.4 | -1.6 to +3.9 |
| sdr_v2 | I - D | 4,414 | 4,731 | -4.1 | -9.4 to +1.3 |
| sdr_v2 | L1 hidden - D | 4,346 | 4,731 | -5.0 | -8.1 to -1.7 |
| ser_v2 | L1 visible - hidden | 2,419 of 7,947 | 2,649 of 7,947 | -2.9 | -4.7 to -1.1 |
| ser_v2 | L2 visible - hidden | 1,834 | 1,966 | -1.7 | -5.4 to +2.0 |
| ser_v2 | L3 visible - hidden | 1,815 | 2,357 | -6.8 | -11.1 to -2.9 |
| ser_v2 | I - D | 1,435 | 1,709 | -3.4 | -14.3 to +6.2 |
| ser_v2 | L1 hidden - D | 2,649 | 1,709 | +11.8 | +7.8 to +16.5 |

**No listener comparison reaches 10 points on the content clauses.** The largest is SER phrasing 3 at -6.8. I minus D
is negative on all three tasks. FAR's I minus D on the token-matched rows is identical to its whole content pool,
because FAR's form-only rows are the shared clauses. SER's token-matched rows give -3.5 (7,832 ids, 19 clusters).

**One large descriptive effect.** On SER's content clauses, "The user cannot see these instructions" raises
compliance over D by +11.8 points. The visible sentence raises it by +8.9 (30.4 against 21.5 percent). So most of
the SER movement comes from adding a sentence, not from its polarity.

The secondary rows and the shared-pool rows are in `followup_readings.md`. On the shared pool, SDR's L1 is -23.3 and
its I minus D is +60.5, as review 02 found.

### Phrasing 4 (R6 i)

Phrasing 4 is not scored yet. The read stage reports two verdicts once it is scored:

- **Full pool.** The D1 listener rule on the unselected pool: at least 10 points, primary compliance, interval
  excluding zero. A pass admits U1.
- **Content pool.** The same rule on the content pool.

It also adds the phrasing-4 flip pools and the D_repro control.

**GPU estimate for phrasing 4.**

| quantity | value |
| --- | ---: |
| live ids, three tasks | 32,363 |
| forwards: L4 arms, four per id | 129,452 |
| forwards: D_repro, two per anchor | 6,000 |
| forwards total | 135,452 |
| D1 per-forward time on an H100, upper bound | 0.0053 to 0.0058 s |
| scoring time | about 12 to 13 minutes |
| model load plus L4 prompt preparation | about 10 minutes |
| read stage on CPU | about 2 minutes |
| estimate | about 25 minutes, 0.4 GPU-hours |
| requested wall time | 00:45:00 |

The per-forward bound comes from D1's chunk metas: summed seconds over summed forwards, with D1's CPU-side I pick
included. The estimate is above R6 (v)'s "about 0.3 GPU-hours" because it counts model load and the anchor control.

## Execution evidence

- **Job id and cluster.** No GPU job was run. The CPU read ran locally on the Delta login node:
  `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -I scripts/d1_followup.py read`,
  from the worktree root. The inputs are the D1 scores of Bridges-2 job 50145353.
- **Exit code.** 0, on the final run, which wrote `followup_readings.json` at 2026-11-02T17:51:22.
- **Row counts.**

  | task | scores.jsonl rows | verdict pool | content pool | shared pool | anchors |
  | --- | ---: | ---: | ---: | ---: | ---: |
  | far_v2 | 24,850 | 9,954 | 8,380 | 1,574 | 1,000 |
  | sdr_v2 | 33,300 | 9,563 | 7,741 | 1,822 | 1,000 |
  | ser_v2 | 32,250 | 9,846 | 7,947 | 1,899 | 1,000 |

  Each verdict pool equals readings.json's `n_prior_kept_sampled` and review 02's count.
- **Baseline reproduces.** The content and shared pools sum to D1's pooled phrasing-1 counts on every task:

  | task | visible, content + shared | readings.json | hidden, content + shared | readings.json |
  | --- | --- | ---: | --- | ---: |
  | far_v2 | 1,285 + 11 = 1,296 | 1,296 | 1,034 + 11 = 1,045 | 1,045 |
  | sdr_v2 | 4,273 + 63 = 4,336 | 4,336 | 4,346 + 488 = 4,834 | 4,834 |
  | ser_v2 | 2,419 + 5 = 2,424 | 2,424 | 2,649 + 10 = 2,659 | 2,659 |

  Every content-pool point estimate in review 02's decomposition table reproduces exactly. Those are FAR +3.0 and
  -7.4, SDR -0.9 and -4.1, and SER -2.9 and -3.4, plus SDR shared -23.3 and +60.5.
- **Provenance.** `outputs/_analyses/deception-divergence/d1/<task>/run_manifest.json` names commit
  `4bdf6bb3a313453ce7e0a66d0a8d812451c94a60` and job 50145353. The read stage checks each `scores.jsonl` against the
  `scores_sha256` there. The code that produced the read is uncommitted worktree code, so its commit is pending the
  orchestrator's commit.

## What is NOT done

- **Phrasing 4 is not scored.** The GPU job is the orchestrator's to submit, and parts (a) and (c) for phrasing 4
  wait on it.
- **Inputs on Bridges-2.** I did not check that the Bridges-2 clone still holds D1's `sample.jsonl`,
  `sample_report.json`, `scores.jsonl` and `run_manifest.json`. The job refuses to start if their hashes differ.
- **Full suite.** I did not run the full test suite. I ran only the two D1 files, on both interpreters.
- **Base interpreter dry run.** The wrapper dry run and the read ran on mgnp only. The base interpreter ran the tests,
  including the end-to-end stub run of build, score and read.
- **Output tracking.** `outputs/_analyses/` is git-ignored, so `followup_readings.*` and `build_report_l4.json` are
  not in the commit list. Whether to track the readings is the orchestrator's call.
- **Git.** I did not commit, push, sync or submit anything.

## Open questions

- **Is phrasing 4 still worth its 0.4 GPU-hours?** The phrasing-1 flip pool is empty on every task, and no one-sentence
  listener arm moves a D-compliant id to the honest gate. So the phrasing-4 flip route under R6 (iii) is very
  unlikely to reach 400 ids. Phrasing 4 can still admit U1 through the full-pool listener rule of R6 (i), which the
  job decides. Default: submit as pre-registered, since R6 budgets it and the listener verdict is the deciding read.
- **Does the R6 (i) listener rule count a negative difference?** I applied the D1 rule as R2a defines it: two-sided,
  with the sign reported. A pass with hidden more compliant than visible would therefore admit U1 as written. Default:
  two-sided, as frozen, with the sign reported beside the verdict.
- **What does "over at least 10 clauses" count?** I counted the distinct clauses with at least one forward id, and the
  per-clause counts are reported. Default: that count. A stricter reading, such as a per-clause minimum, would need a
  ruling.
- **Should the reverse pool require D compliance?** The reverse pool requires D compliance, mirroring the forward
  pool. The brief says only "visible compliant, hidden honest". The no-D-gate variant is reported beside it. Default:
  keep the D gate.
- **Which inputs does the Bridges-2 job read?** It reads D1's inputs in the Bridges-2 clone. If they are missing,
  the orchestrator can push the Delta copies, which hash to the D1 manifests. Default: the clone's copies are intact.

The Bridges-2 command, run from the Bridges-2 clone root after syncing the branch and `mkdir -p logs`:

```
sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 00:45:00 --job-name=d1-followup scripts/jobs/run_d1_followup.sh
```
