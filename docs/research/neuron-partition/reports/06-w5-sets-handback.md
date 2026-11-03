# Hand-back 06: W5, the all-position sets and jobs A and B

Agent: implementation worker W5 (Claude, Opus), session claude-5201d56c. Ticket: the team lead's W5 brief of Tue 3 Nov
2026 (verify the all-position runs, partition and stability under R11, sync, submit jobs A and B, write the
addenda). Status: resolved. The full record is in the two addenda named below. This file is the summary the
research-session stop hook asks for.

## What changed

All edits are in the worktree
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`, for the orchestrator to commit
by file list:

- `docs/research/neuron-partition/reports/04-w4-partition-handback.md` gains "Addendum: all-position partition
  (R11)".
- `docs/research/neuron-partition/reports/01-w1-scorer-handback.md` gains "Addendum: all-position run".
- `docs/research/neuron-partition/jobs/ablation_bridges2.md` gains "Submitted: jobs A and B" with the literal lines.
- `docs/research/neuron-partition/reports/06-w5-sets-handback.md` is this file.

The outputs are git-ignored, under `outputs/_analyses/neuron-partition/sets/` in the worktree:
`far_atp_all_c3d7763/` and `far_atp_readout_c3d7763/`, with four logs beside them. The temporary scripts are in
`outputs/_analyses/neuron-partition/w5_tmp/`.

## How verified

- **Inputs.** Every scores file of Delta job 23478550 has the all-position keys. The row counts are 400 and 354 for
  the full runs, 200 and 174 for half 1, and 200 and 180 for half 2. Every key shared with the earlier runs is equal,
  with a maximum absolute difference of 0.0.
- **Sets.** The readout rerun at c3d7763 is byte-identical to `sets/far_atp_66741d7/`. Every all-position
  with-nulls file holds 84 groups, which the ablation loader accepts, and every null matches its class.
- **Sync.** All 66 files have the same sha256 on Delta and in the Bridges-2 clone.
- **Lint.** Every edited document lints clean.

## Execution evidence

- **Local runs.** The partition and stability runs ran on the CPU of the login node, each with exit code 0. No Slurm
  job was used for them.
- **Bridges-2 jobs.** These were submitted on account cis260372p, partition GPU-shared, one H100, with 04:00:00
  reserved, at commit fe2db9e.

| Job | id | Ledger | Projected start (test-only) | Last seen at 2:57 pm EST |
| --- | --- | --- | --- | --- |
| A | 50183187 | r-007 | 3:06 pm EST | pending on priority |
| B | 50183194 | r-008 | 3:07 pm EST | pending on priority |

Both are recorded in the ledger and the job list of the main-checkout direction directory. Worker w6-babysit has the
ids.

## What is NOT done

- **Job starts.** Neither start is confirmed. The Bridges-2 login host has not answered ssh since about 3:00 pm EST,
  while b2dtn still answers.
- **Results.** No ablation result exists yet. Nothing in the addenda is a finding.
- **Main-checkout copy.** The stop hook asked for this file under the main checkout, but worktree isolation refuses
  writes there. It lives in the worktree and reaches main with the orchestrator's commit.

## Open questions

1. **Early D-only neurons.** Under all positions, the D-only class sits 62 to 65 percent in layers 0 to 9. Its overlap
   with the readout D-only class is 0.04 to 0.06. These neurons may only read the pressure-clause tokens. Jobs A and
   B will show whether removing them changes the D effect beyond the matched nulls.
