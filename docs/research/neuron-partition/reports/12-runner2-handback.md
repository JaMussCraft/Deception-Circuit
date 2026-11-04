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

## Addendum: SER k-500 ablation cell (np-ablate-ser)

- Job id and cluster: 50213549, Bridges-2, account cis260372p, partition GPU-shared, one H100-80 on node w008.
- State: COMPLETED 0:0. Elapsed 3572 s against 7200 s reserved (ledger r-017, 2 GPU-h).
- Inputs: 69 files rsynced, sha256 identical on both sides; clone HEAD d5f6b17.
- Rows against expected: rows.jsonl 310,800 lines against 310,800 by the formula; 84 sets; unpaired empty; self-replay error D 0.0 and I 0.0; twin cross-check maximum difference 0.0 (mean:D and mean:I, n 600 each). Intact IOI argmax accuracy 0.511 (ladder reference 0.51; the job line said about 0.513).
- Manifest: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/ser_predicate_k500-d5f6b17/run_manifest.json`, commit d5f6b1750e5b5a770d48b5c44cd4cb2c688236c6, git_dirty false. Fetched summary.json, rows.jsonl and run_manifest.json match Bridges-2 by sha256 (summary.json 0e868dc5295e1719...).
- Timing correction: I first reported 0.477 s per forward from the log, which is seconds per 300-id cell. The summary records 0.042 s per forward (3,420 forwards per cell), so the 0.09 threshold was not exceeded.
- Verdict directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/verdict/ser_predicate_k500-d5f6b17/`.
- verdict.json sha256 `f65e74212bb4cb6fa427bcfd8dafdd41de9f35187742178eae5e0ea3e0983b4a`.
- verdict.md sha256 `6992cf0c327911ca9745947c45bedb91e0371784d09fa15711d7093e31cd9a12`.
- Verdict line: "N1 pass at any k: False."
