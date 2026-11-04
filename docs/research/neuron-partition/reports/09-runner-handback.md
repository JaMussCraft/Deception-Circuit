# Hand-back 09: runner R1 job log

Agent: runner R1 (Sonnet 5.5). Ticket: the N2 fresh-data cell of ruling R14 in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/spec.md`. Status: resolved for job 1, waiting for further job lines.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/09-runner-handback.md`, this file.
- Untracked outputs: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/confirm_h_only_k2000-3486f1a` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/verdict/confirm_h_only_k2000-3486f1a`.

## How verified

```
sacct -j 23519165 -X -n -o State,ElapsedRaw,NodeList
```

Observed: COMPLETED, 2480 s, gpub007. Row counts per condition and set match the expected counts below.

## Execution evidence

Addendum: np-n2 (N2 honest-only class, size 2,000, with 20 nulls, seed-3 sample).

- Job id and cluster: 23519165 on Delta, interactive partition, node gpub007, account beto-delta-gpu.
- Exit code or Slurm state: COMPLETED, 2480 s elapsed against 3600 s reserved (ledger r-013, reconciled).
- Row counts: 56,784 rows in rows.jsonl against 56,784 expected. That is 21 sets times D 208, H 208, F 208 (mean only), I 166, N 166 and IOI 1000 (mean only), with twin rows for D, H, I and N.
- Baseline reproduces: intact IOI argmax accuracy 0.513 against 0.510 in the ladder reference, a difference of 0.3 points. Self-replay error is 0.0 for D and I.
- Provenance file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/confirm_h_only_k2000-3486f1a/run_manifest.json`, commit `d5f6b1750e5b5a770d48b5c44cd4cb2c688236c6`. The job line named 3486f1a, which is the ledger value; the manifest records the commit above.

## What is NOT done

- The verdict numbers are not reviewed. The verdict script ran with defaults plus the sample file.

## Open questions

- The manifest commit differs from the 3486f1a in the job line and ledger. Default: treat the manifest value as the one the run used, and leave the ledger as is.

## Addendum: np-ladder (R15(b), Bridges-2)

- Job id and cluster: 50212883 on Bridges-2, GPU-shared, allocation cis260372p, ledger r-015. The job record tool caps its timeout at 60 minutes, so the 90-minute reservation sits only in the ledger.
- Slurm state: COMPLETED, 3041 s elapsed against 5400 s reserved.
- Row counts: 227,136 rows against 227,136 expected, which is 84 sets times 2,704 rows per set.
- Baseline reproduces: intact IOI accuracy 0.511 against 0.510 in the ladder reference. Self-replay error 0.0 for D and I.
- Transfer: sha256 of summary.json, rows.jsonl, cells_partial.jsonl and run_manifest.json match on Bridges-2 and Delta. Input and code hashes matched the expected values before submission.
- Provenance file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/ladder-92fc6fb/run_manifest.json`, commit `d5f6b1750e5b5a770d48b5c44cd4cb2c688236c6`. The manifest commit differs from 92fc6fb in the job name, as in the N2 cell.
- Verdict: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/verdict/ladder-92fc6fb/verdict.md`. N1 passes at k 250, 375, 625 and 750 under both references, on the whole sample and both halves.
