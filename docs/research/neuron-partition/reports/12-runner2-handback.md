# Hand-back 12: Runner 2 (SER jobs), standing by

Agent: job runner R2, Claude Sonnet 5.5. Ticket: SER job running for worker w10-ser. Status: resolved for now, idle with no job received.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/12-runner2-handback.md`, this file only.
- Staged: nothing.

## How verified

No command was run. Nothing in this hand-back claims a check.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No job line has arrived from w10-ser, so no job was test-only checked, submitted, ledgered or post-processed.
- Addendum blocks for future jobs will be appended to this file.

## Open questions

- Waiting for w10-ser to send the first job line. The team lead can wake this runner again when one exists.

## Addendum: SER all-position attribution ranking (nrn-allpos-atp-ser)

- Job id and cluster: 23520107, Delta, partition gpuH200x8-interactive,gpuA40x4-interactive (ran on gpub090, NVIDIA A40), account beto-delta-gpu.
- State: COMPLETED 0:0. Elapsed 360 s against 1800 s reserved (ledger r-014, 0.5 GPU-h).
- Rows against expected: all ten directories present, n_rows and n_clause_rows match the table (253, 201, 253, 201, 127, 97, 127, 126, 104, 126); clause_fallback_ids empty; all score tensors [32, 14336] float32 and finite.
- Means: dh m_clean 2.906, m_twin -3.671; in m_clean 3.838, m_twin -3.715. Seconds per row 0.089 (dh) and 0.098 (in).
- Manifest: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/attribution/ser_v2_dh_train+validation_predicate_a41752a/run_manifest.json`.
- Commit discrepancy: the manifests name git_commit d5f6b1750e5b5a770d48b5c44cd4cb2c688236c6 (git_dirty false), not the a41752a8f88b9990a6a74d84bfa3891d78b32705 that the ledger records. The worktree HEAD evidently moved between the job line and the run.
