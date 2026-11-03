# Hand-back 02r: independent review of the W2 ablation code (rev2)

Status: done. Verdict PASS WITH FIXES, with no blockers and two majors. The review is
`docs/research/neuron-partition/reviews/02-ablation-review.md`.

## What changed

- Written: `docs/research/neuron-partition/reviews/02-ablation-review.md` and this hand-back.
- Scratch scripts and outputs are in `outputs/_analyses/neuron-partition/review2_tmp/`: `ioi_hash.py`,
  `indep_check.py`, `ids_by_condition.json`, `full.out`, `golden_main.out`, `dry.out` and two pytest basetemps.
- No repository code was changed, and git, sbatch and GPUs were not used.

## How verified

- I read the code under review at e5962fe and diffed `hooks.py` and `knockout.py` against the primary checkout's
  pre-change modules.
- I ran the W2 tests on both interpreters.
- I ran my own tiny-model checks through plain torch hooks, a golden comparison against main's modules, and an IOI
  reproducibility probe under two hash seeds.
- I ran a CPU dry run of the CLI on the real seed-2 sample and W3's pool copies.

## Execution evidence

These were CPU runs on the login node, with no Slurm job. All exited 0.

| Run | Observed | Expected |
|---|---|---|
| pytest, mgnp | 32 passed | 32 |
| pytest, base 3.9 | 16 passed, 16 skipped | 16 skipped for nnsight |
| Zero on all of layer 1, MLP output | 0.0 | 0.0 |
| Twin on all of layer 0, down_proj input diff | 0.0 | 0.0 |
| Golden margins, worktree against main | equal | equal |
| Dry-run rows for D, H, F, I, N and IOI | 300 each, IOI 100 | 300 each, IOI 100 |
| IOI rows, PYTHONHASHSEED 0 against 1 | different | same |

No `run_manifest.json` exists, because no GPU run was made.

## What is NOT done

- The fixes in the review were not applied, because this review is read-only.
- No GPU pilot was run, so the seconds-per-forward estimate is still extrapolated.

## Open questions

- The orchestrator should decide whether to fix the IOI hash dependence inside `dataset/ioi_llama.py` by sorting
  the names, or only to pin `PYTHONHASHSEED=0` in the job script. Sorting changes every existing IOI caller.
- The R4 check against 0.51 must be read from the pilot's summary by hand, after finding 1 is fixed.
