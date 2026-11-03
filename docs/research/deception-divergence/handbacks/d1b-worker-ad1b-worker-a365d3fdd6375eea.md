# Last message of d1b-worker ad1b-worker-a365d3fdd6375eea (2026-11-02T19:00:59-05:00)

The phrasing-1 flip pool is empty on every task, so U1 is not admitted through phrasing 1. The same evidence makes the phrasing-4 flip route under R6 (iii) almost certainly null as well. Among ids that comply under D, no listener sentence of phrasings 1 or 2 moves a single id to the honest gate, in either polarity. Only SDR's phrasing-3 visible arm does, for 8 of 4,789 ids. The I arm gets there for 76 to 214 ids, so the gate is reachable. The GPU job's value therefore rests on the R6 (i) full-pool listener verdict.

**Flip pools, phrasing 1** (primary definition, unselected pool):

| task | forward pool | reverse pool | clauses | admit U1 |
| --- | ---: | ---: | ---: | --- |
| far_v2 | 0 of 9,954 | 0 | 0 | no |
| sdr_v2 | 0 of 9,563 | 0 | 0 | no |
| ser_v2 | 0 of 9,846 | 0 | 0 | no |

The anchors also give 0 in both directions. Under the looser informational definitions the forward pools hold 13 to 123 ids, still far below 400.

**Content clauses** (five shared clauses excluded, primary, points with the clustered interval):

| task | ids | phrasing 1 visible minus hidden | phrasing 2 | phrasing 3 | I minus D |
| --- | ---: | --- | ---: | --- | --- |
| far_v2 | 8,380 | +3.0 [+1.4, +4.9] | -0.3 | -0.1 | -7.4 [-17.4, +1.7], 6,328 ids |
| sdr_v2 | 7,741 | -0.9 [-2.8, +0.9] | -0.1 | +1.4 | -4.1 [-9.4, +1.3] |
| ser_v2 | 7,947 | -2.9 [-4.7, -1.1] | -1.7 | -6.8 [-11.1, -2.9] | -3.4 [-14.3, +6.2] |

No listener comparison reaches 10 points, and I minus D is negative on all three tasks. Every content-clause number in review 02 reproduces exactly. The content and shared pools also add back to the pooled phrasing-1 counts in the D1 readings.

**What was built.** The new script `scripts/d1_followup.py` imports the D1 script without changing it. It has a CPU build report, a GPU score stage and a CPU read stage, plus a job wrapper and 15 tests. Two points differ from the brief:
- **Manifest name.** The phrasing-4 manifest is `run_manifest_l4.json`, so it cannot overwrite D1's own manifest.
- **Anchor control.** The job also rescores D on the 1,000 anchors per task. This measures how far the two jobs agree per id, for 6,000 extra forwards.

**Checks.**
- **Tests.** All 46 pass on both interpreters, with no skips. That is the 15 new tests plus the 31 existing D1 tests.
- **Wrapper dry run.** It exited 0 and dropped no row. The phrasing-4 arms fit the builder length of 120.
- **Twins.** The visible and hidden arms differ at exactly one token on every id, for phrasings 1 and 4.
- **Hand-back lint.** It passes.

**Files to commit:**
- `scripts/d1_followup.py`
- `scripts/jobs/run_d1_followup.sh`
- `tests/test_d1_followup.py`
- `docs/research/deception-divergence/reports/06-handback.md`

The readings and build reports are under `outputs/_analyses/`, which git ignores.

**GPU estimate.** The job is 135,452 forwards, about 25 minutes or 0.4 GPU-hours on one H100. That is above R6's "about 0.3" because it counts model load and the anchor control. Run it from the Bridges-2 clone root after syncing the branch and creating `logs/` there. The job refuses to start unless D1's sample and scores in that clone match their recorded hashes.

```
sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 00:45:00 --job-name=d1-followup scripts/jobs/run_d1_followup.sh
```

The hand-back records three default readings for the orchestrator to confirm:
- **Two-sided rule.** The phrasing-4 listener rule is two-sided, as the D1 rule is.
- **Clause count.** "At least 10 clauses" counts distinct clauses with at least one id.
- **Reverse pool.** The reverse pool also requires D compliance.

The hand-back is at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/06-handback.md`, and the same summary went to the team lead.
