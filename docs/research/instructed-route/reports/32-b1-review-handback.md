# Hand-back 32: independent review of the B1 results (review 05)

Agent: independent review agent (Claude Opus 5.5), session claude-230e4716. Task: the lead's request to review the B1
loop-closure (T1) and key-side versus query-side (T2) results on the 100 held-out ids for FAR and SER (Bridges-2
jobs 50106660 and 50106721, commit 476c187). Status: resolved. The review is
`docs/research/instructed-route/reviews/05-b1-review.md`.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reviews/05-b1-review.md`,
  the review. Its headings are Verdict, Checks, Problems found and Proposed finding text.
- Committed by the orchestrator from the worktree: this file.

No code, output, results file, `spec.md` or `FINDINGS.md` was edited. The recomputation scripts sit in the job's
temporary directory, which is deleted with the job, so the review's tables are the record.

## How verified

The three scripts read both `route_closure.json` files, both `run_manifest.json` and `sample.json` files,
`phase3/ct.json`, the held-out sample and deciding-set files, and `results/b1/b1_readings.json`:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/rev05/recompute.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/rev05/prov.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/rev05/pp.py
```

A fourth script, `extra.py` in the same directory, checked the key arm per instance and the readings' input hashes.

**Observed.** Every headline number of `b1_readings.md` reproduces to three decimals, and the intervals agree
within 0.002 under an independent clustered bootstrap. That bootstrap used 4,000 resamples and seed 777. The run
matches the pre-registration in every respect checked:

- the 100 ids in order;
- C_t of 72 and 78;
- `greedy_k20`;
- KV group 6;
- the neutral-twin interchange;
- disjoint seeded controls;
- path patching on;
- `not_implemented` empty.

## Execution evidence

Not applicable: no runs. This is a CPU review of fetched outputs.

- **Jobs.** The manifests name Slurm jobs 50106660 (far, host w004) and 50106721 (ser, host w003).
- **Commit.** Both name commit 476c18770bcd3d461368ce67faeb535e45b29270 with `git_dirty` false.
- **Rows.** Each task has 100 instances against 100 expected, and no instance lacks a twin.
- **Gates.** G1 is bit-identical on both tasks and G2's maximum difference is 0.0. G3 passed on far and failed on
  ser's summed check, 0.029 against 0.02. R9 covers that failure; see problem 1 of the review.

## What is NOT done

- **FINDINGS.md.** The rows were not written into it. The proposed text for two rows is in the review.
- **The stale estimator labels.** The `t1.summary.rule_estimator` labels inside `route_closure.json` were not
  corrected (problem 2). The fix is a note, not a rerun.
- **Attention patterns.** None were captured or analysed, so the T2 reading stops at "query-side".

## Open questions

1. **How should the ser G3 miss be recorded?** Default: record it as failed and explained under R9, in the finding
   caveats and in the direction README.
2. **Should a note mark `t1.summary` in the JSON as pre-R9?** Its forward numbers are labelled as the rule.
   Default: add one line to the B1 results or README and leave the JSON untouched.
3. **Should the parallel route behind the bypass be chased?** It is the roughly 0.64 (far) and 0.54 (ser) of the
   outside share that leaves the deciding set without passing through the quartet. Default: not within B1. B1's
   exit criteria are met, and naming the route would be a new descriptive test.
