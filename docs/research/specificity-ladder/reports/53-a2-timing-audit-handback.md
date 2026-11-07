# A2 H200 timing audit handback

Agent: Codex independent CPU auditor. Status: handed-back.

## What changed

Verdict: the H200 receipt is usable timing evidence for FAR/D on the measured configuration. The fleet remains on hold because the other task/condition timings are absent. No runtime source or live state was changed.

Files written in both the worktree and primary `docs/research/specificity-ladder/` trees:

- `reports/53-a2-timing-audit-handback.md`, this independent audit.
- `reports/53-a2-timing-audit-calculations.json`, assertions, accounting snapshot, and recomputed projection.
- `tools/53-a2-timing-audit.py`, reproducible CPU-only checker.

Absolute worktree root: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. Absolute primary root: `/projects/beto/swong2/Alignment/Deception-Circuit`. The author/root result report was not read.

The successful receipt and native manifest consistently name execution revision `6bd8bf5334f2e83613a129d2fcfeacf83e762191`, separately from the unchanged data build revision `77b6487b08b4410a4e5a9995c6ff5e46834a5ce3`. Native git collection was disabled as intended. Current bytes match all six recorded source hashes, all five artifact hashes, both private dataset configuration hashes, the raw configuration/build files, and both protected-registry hashes. Native dataset-file hashes also match current bytes. Exact selected IDs, actual Arrow rows, source-row proofs, and the approved cohort ruling pass the wrapper contracts. Evidence: `53-a2-timing-audit-calculations.json`.

The cached model reference and native manifest agree on revision `0e9e39f249a16976918f6564b8830bc894c89659` of `meta-llama/Llama-3.1-8B-Instruct`. Cached configuration and weight-index hashes match preflight, architecture/dimensions match the declared Llama model, and all indexed weight shards exist. Weight-file bytes were not independently hashed; this is a metadata identity audit, not a complete weight-content attestation.

## How verified

The saved checker imports the standard wrapper and projection contracts, rechecks actual stored rows on CPU, independently recomputes row metrics and timing arithmetic, and queries accounting read-only. It never calls the training entrypoint or loads a model.

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -B docs/research/specificity-ladder/tools/53-a2-timing-audit.py --repo /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/53-a2-timing-audit-calculations.json
```

Observed: all audit assertions passed, exit 0. Output is `53-a2-timing-audit-calculations.json`.

```bash
sacct -j 23414611,23414452 --format=JobIDRaw,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocTRES,MaxRSS,Start,End -P
```

Observed: H200 completed with exit `0:0`, elapsed 235 seconds and a 12-minute single-GPU allocation. A40 failed with exit `1:0`, elapsed 157 seconds and a 20-minute single-GPU allocation. Both terminal states and elapsed times now agree with the reconciled primary ledger. The worktree ledger is a stale empty branch copy and was not used for accounting. Evidence: `53-a2-timing-audit-calculations.json`.

The exact FAR train/validation/test counts are 177/177/891 against expected 177/177/891; ordered baseline and final node-evaluation outputs each contain the expected 891 test IDs. History contains all 20 requested epochs, and validation records occur at epochs 0, 10, and 20 on the expected validation IDs. Receipt flags identify real execution with neither runner nor clock injection. Evidence: `53-a2-timing-audit-calculations.json`.

The measured process interval is 216.462612 seconds, including 119.7 seconds of printed pruning time. The fixed component is therefore 96.762612 seconds; scaling pruning to 500 epochs gives 2992.5 seconds, for 3089.262612 seconds total, or 51.487710 minutes. A 20 percent buffer rounds upward to a 62-minute reservation under the approved process-time contract. These are derived calculations in `53-a2-timing-audit-calculations.json`.

Slurm elapsed includes another 18.537388 seconds outside the receipt interval, covering outer activation/preflight and scheduler rounding. Using Slurm elapsed as the fixed-cost anchor gives 3107.8 seconds and a buffered 63-minute reservation. Prefer this conservative outer-overhead allowance when proposing the next comparable reservation; the exact existing projection still reports 62 minutes. These are derived calculations in `53-a2-timing-audit-calculations.json`.

Both pilots count toward reserved cost: the failed A40 reservation plus the H200 reservation total 32 GPU-minutes, or 0.533333 GPU-hours. Their combined actual allocation time is 392 GPU-seconds. The A40 failure remains preserved and contributes no usable timing estimate. Evidence: `53-a2-timing-audit-calculations.json`.

Only one of the six task/condition groups has measured timing. Seed-only reuse projects three of eighteen planned seed cells; fifteen remain uncovered. Missing groups are FAR/I, SDR/D, SDR/I, SER/D, and SER/I. The partial reservation total, including both pilots, is not a full-fleet budget estimate and cannot establish compliance with the phase cap. Projection returns `hold` and `fleet_reservation_allowed:false`. The measured FAR/D estimate does not trigger the six-hour fallback. Counts and projection: `53-a2-timing-audit-calculations.json`.

The receipt field named `peak_memory_gb` is a rounded value in GiB: the tracker divides bytes by binary gigabytes but labels output GB. The log peak is 51.610 GiB, approximately 55.416 decimal GB, with 53.49 GiB reserved at the recorded checkpoint. Slurm MaxRSS is host memory, not this GPU peak. The A40 log records a CUDA out-of-memory failure; success on H200 does not imply A40 capacity. Unit conversion is derived from `53-a2-timing-audit-calculations.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/pruning.py`.

## Execution evidence

- Job and cluster: H200 timing job `23414611`, Delta; preserved failed A40 pilot `23414452`, Delta.
- Terminal evidence: H200 `COMPLETED`, exit `0:0`; A40 `FAILED`, exit `1:0`, from live accounting.
- Observed against expected: train/validation/test 177/177/891 against 177/177/891; completed epochs 20 against 20. Both test-output sets contain 891 against 891 expected rows. Evidence: `53-a2-timing-audit-calculations.json`.
- Baseline evidence actually present: the H200 log reports accuracy 1.0000 and its results file reports 1.0; recomputation from the saved test outputs gives 1.0. This establishes same-run artifact consistency, not an independent replay. Evidence: `53-a2-timing-audit-calculations.json`.
- The failed A40 job also completed an initial baseline summary: accuracy 1.0000, logit difference 2.5328, compared with the H200 log summary of accuracy 1.0000 and logit difference 2.5391. Those logs are observations from different jobs/hardware/execution revisions; they do not establish an exact per-row cross-hardware replay. No such replay was performed by this audit. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-timing-224823f-a40/far-D-seed42.stdout-stderr.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/far-D-seed42.stdout-stderr.log`.
- Native provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_training_specificity_ladder/a2-h200/far_v2_D_seed42_heads-mlp_741e575c346e3f25_timing20/run_manifest.json`; declared execution commit `6bd8bf5334f2e83613a129d2fcfeacf83e762191`; data build commit `77b6487b08b4410a4e5a9995c6ff5e46834a5ce3`. Native git commit is null by design; provenance rests on the supplied full revision plus matching source hashes.

## What is NOT done

No new model/GPU/API execution, notebook, job submission, git command, or delegated agent was used. No runtime code was edited. No independent model baseline replay or full scientific training seed was produced. The timing-only mask has a shorter scheduler horizon and cannot be promoted to a full scientific seed. No timing extrapolation across task, condition, hardware, data build, padded shape, or granularity is supported. No complete fleet budget approval is possible from this receipt.

## Open questions

None blocking receipt use as timing evidence. Default: retain both pilot costs, use the conservative outer-overhead allowance for comparable reservation proposals, and obtain independent timing coverage for the missing task/condition groups before evaluating fleet approval.
