# Complete A2 timing coverage audit handback

Agent: Codex independent CPU auditor. Status: handed-back.

## What changed

Verdict: complete H200 timing coverage passes the existing reservation-projection gates. The conservative reservation estimate, including all pilots and measured outer-job overhead, is 19.216667 GPU-hours. No missing timing group remains. This is a conditional timing/budget assessment for the frozen H200 configuration, not a scientific finding or a new job launch. Evidence: `62-a2-complete-timing-audit-calculations.json`.

The audit extends the earlier standalone FAR/D audit using raw receipts, logs, artifacts, source/data files, cache metadata, and live accounting. The saved projection was compared only after independent recomputation; no root narrative or author result report was used.

Only these audit artifacts were written, mirrored under primary `/projects/beto/swong2/Alignment/Deception-Circuit` and worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`:

- `docs/research/specificity-ladder/reports/62-a2-complete-timing-audit-handback.md`.
- `docs/research/specificity-ladder/reports/62-a2-complete-timing-audit-calculations.json`.
- `docs/research/specificity-ladder/tools/62-a2-complete-timing-audit.py`.

Every receipt is successful, uninjected, seed `42`, and timing-only. Current source hashes, the unchanged raw H200 config, private dataset configs, manifest/build binding, selected IDs, actual Arrow rows/source proofs, registry snapshots, native dataset files, and final artifact hashes match. The separately hashed batch driver agrees with its launch record. All native manifests retain execution revision `6bd8bf5334f2e83613a129d2fcfeacf83e762191` separately from data build revision `77b6487b08b4410a4e5a9995c6ff5e46834a5ce3`.

All receipts report the same single H200 identity and Delta cluster. Cached model configuration, weight-index metadata, and native revision agree on `meta-llama/Llama-3.1-8B-Instruct` revision `0e9e39f249a16976918f6564b8830bc894c89659`; indexed shards exist. The audit does not hash weight-file contents or load the model.

## How verified

Command ran from the worktree:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -B docs/research/specificity-ladder/tools/62-a2-complete-timing-audit.py --repo /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/62-a2-complete-timing-audit-calculations.json
```

Observed: all audit assertions passed, exit `0`. The checker independently recalculates stored row metrics using strict positive target-minus-distractor margin, checks actual epoch/history/output IDs, matches log pruning durations and memory peaks to receipts, and checks current bytes against all recorded hashes.

```bash
sacct -j 23415106,23414611,23414452 --format=JobIDRaw,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocTRES,MaxRSS,Start,End -P
```

Observed: batch job `23415106` is `COMPLETED`, exit `0:0`, elapsed 974 seconds, reserved 26 minutes; standalone H200 job `23414611` is `COMPLETED`, elapsed 235 seconds, reserved 12 minutes; failed A40 job `23414452` is `FAILED`, exit `1:0`, elapsed 157 seconds, reserved 20 minutes. All use a single allocated GPU. Reservations sum to 58 GPU-minutes, including the failed pilot. Evidence: `62-a2-complete-timing-audit-calculations.json`.

The batch child process intervals sum to 925.418788 seconds, leaving 48.581212 seconds of aggregate outer overhead, or 9.716242 seconds per child on average. The largest observed batch launch gap is 14.876762 seconds. The standalone elapsed-minus-child difference is 18.537388 seconds; its initial accounting-start-to-receipt-start gap is 19.034538 seconds. A conservative rounded allowance of 20 seconds per future mask covers these observed per-launch gaps. It is an observed allowance, not a guarantee against future filesystem or startup delays. These are derived calculations in `62-a2-complete-timing-audit-calculations.json`.

For every task/condition, the full process estimate is fixed time plus pruning time scaled from 20 to 500 epochs. Conservative reservation is `ceil((full_seconds + 20) * 1.20 / 60)` minutes. The buffer and upward minute rounding are retained. Each row below applies separately to seeds `42`, `1`, and `123`; only the timing seed was actually measured. Derived evidence: `62-a2-complete-timing-audit-calculations.json`.

| Task | Condition | Measured total seconds | Pruning seconds | Projected full seconds | Existing contract minutes per seed | Conservative minutes per seed |
|---|---|---:|---:|---:|---:|---:|
| FAR | D | 216.462612 | 119.7 | 3089.262612 | 62 | 63 |
| FAR | I | 190.958491 | 116.4 | 2984.558491 | 60 | 61 |
| SDR | D | 191.820913 | 121.3 | 3103.020913 | 63 | 63 |
| SDR | I | 192.734113 | 123.0 | 3144.734113 | 63 | 64 |
| SER | D | 173.905511 | 108.9 | 2787.505511 | 56 | 57 |
| SER | I | 175.999761 | 109.0 | 2791.999761 | 56 | 57 |

The unmodified projection exactly matches the independently recomputed saved tool output: 18 covered seed cells, no gaps or rejected receipts, and 18.966667 GPU-hours including pilots. The conservative table raises the total to 1153 GPU-minutes, or 19.216667 GPU-hours. This remains below the 60 GPU-hour phase cap. Even the longest projected mask plus the outer allowance remains below the six-hour fallback threshold. The exact cohort ruling clears only the smaller-cohort review hold; its recorded digest matches the approved ruling. Derived totals and gate evidence: `62-a2-complete-timing-audit-calculations.json`.

Negative controls preserve the gates: removing a timing group prevents approval; removing the cohort ruling holds the under-size cohorts; foreign hardware prevents approval; increasing pilot reservation beyond the phase budget prevents approval; synthetic long timings trigger the heads-only fallback and prevent heads-plus-MLP approval. All checks ran against CPU copies of receipt dictionaries and changed no artifacts.

## Execution evidence

- Jobs and cluster: standalone H200 `23414611` and coverage H200 `23415106`, Delta; preserved failed A40 `23414452`, Delta. Terminal states and allocations are above.
- Cohort counts observed against expected, for both D and I: FAR train/validation/test 177/177/891 against 177/177/891; SDR 187/187/952 against 187/187/952; SER 168/167/835 against 168/167/835. Evidence: `62-a2-complete-timing-audit-calculations.json`.
- Epoch evidence: each receipt has all 20 requested epochs and validation records at 0, 10, and 20, on the exact validation IDs. Baseline and final test-output IDs/counts match each task’s expected test cohort. Evidence: `62-a2-complete-timing-audit-calculations.json`.
- Baseline evidence actually present: all six saved baseline outputs recompute to accuracy 1.0, matching their results files. These are same-run consistency checks; no independent baseline replay was performed. The SDR/I final timing mask has 948 strictly positive margins, three ties and one negative margin among 952 rows, matching reported accuracy 0.9957983193. Its nonperfect output does not invalidate timing completion and is not a specificity finding. Evidence: `62-a2-complete-timing-audit-calculations.json`.
- Native provenance: each audited receipt’s native manifest path is recorded in `cells[].native_manifest` in `62-a2-complete-timing-audit-calculations.json`. Every native manifest names the same full execution revision and separate build revision given above, and passes its manifest hash check. Native git collection remains disabled by design; matching source bytes and caller-supplied full revision provide the recorded provenance.
- Peak memory is the tracker’s binary GiB despite the legacy field/log label GB. Values are retained per cell in the calculations. Slurm MaxRSS is host memory. No independent full-vocabulary token replay is claimed from decoded output words.

## What is NOT done

No job was submitted, model loaded, GPU used, paid API called, notebook run, git command executed, or subagent spawned by this audit. No runtime source or live ledger was edited. No full scientific seed exists from these timing runs, and no scientific A2 gate was assessed. Short pilots use a shorter scheduler horizon. Seed-only timing reuse is conditional on the same application bytes, data/configuration, hardware, padding and granularity; it does not establish coverage for changed plans.

## Open questions

None blocking the timing/budget assessment. Default: retain the failed A40 cost and all H200 pilot costs, use the conservative per-seed table, and recheck live usage, phase ledger and protected registries before any separately authorized full training launch. Reassess reservations if full-run observations exceed the conditional estimates.
