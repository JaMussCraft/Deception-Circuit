# Hand-back 03: correct the provenance gaps of finding F-rte-008

Agent: Opus worker (claude-opus-5-5). Ticket: the lead's brief "F-rte-008 findings correction" of 2026-11-02, no
ticket file, plus the lead's follow-up "Apply the two extra FINDINGS corrections". Status: resolved.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/FINDINGS.md`,
  the F-rte-008 row only (line 73, still one table line, id kept, status `reviewed`, commit `21bc397`). The changes:
  - The subject-clustered interval now states its method (2,000 resamples at seed 1), says no run file stores it,
    points to the reproduction file and gives the seed 0 and seed 20261101 intervals.
  - A new "Provenance" sentence before the caveats says which arms come from which run: S_all, the quartet, Gupta's
    six and their nulls from the main J4 run at 21bc397, the heads-only, FAR-set and SER-set arms from the
    supplement at c32627e, and parity from a6ae1a6, with identical code hashes in all three manifests. The commit
    column stays `21bc397` because the findings checker accepts one short SHA only (`SHORT_SHA_RE` in
    `.agents/research_session/registry.py`).
  - Flip coverage is now qualified by position: S_all at the post-cue span covers every reversal of Gupta's six or
    the quartet at either position, and S_all at the readout misses 2 and 1 of their readout reversals.
  - The near-zero range now reads "S_all draws with f between -0.05 and 0.05 reverse 0.30 to 0.43 of flips", in
    place of "f near zero reverse 0.34 to 0.43".
  - The evidence cell gains `outputs/_studies/b3/parity/run_manifest.json`, `data/b3/syc_items.json` and the two
    reproduction files.
- Same FINDINGS.md file, three more rows, on the lead's follow-up instruction. Nothing else in these rows changed.
  - F-rte-005 (line 70): "across layers 18 to 31" now reads "across layers 22 to 31". Verifying file:
    `outputs/_analyses/instructed-route-b1/{far,ser}/Ct__leaf/{far,ser}_v2/route_closure/route_closure.json`, keys
    `t1.sweeps.offline.{T,dq_all}.senders`, top 25 in-sum outside senders by absolute `e` on arm T.
  - F-rte-006 (line 71): "mean absolute change 0.21 and 0.17 against 0.02" now reads "mean absolute change 0.21
    and 0.17 in raw logits, or 0.021 and 0.028 of the mean twin gap G, against 0.02". Verifying file: the same two
    `route_closure.json` files, keys `baseline.m_D`, `baseline.mean_G` and `arms.<arm>.margins`.
  - F-mech-009 (line 41): the claim now ends with "(superseded by F-rte-001)", which findings-check requires of a
    superseded row. Its existing text already said it was superseded by F-rte-001.
- Committed by the orchestrator from the worktree (new):
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/f-rte-008-interval-repro.py`
  and its output
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/f-rte-008-interval-repro.json`.
- Committed by the orchestrator from the worktree (new): this hand-back.
- Nothing staged for the apply tool.

The two flip-coverage and near-zero-range fixes go beyond the four points the brief listed. They are the review's
"caveat imprecisions" for F-rte-008 and are claim-text errors in this row, so they were fixed. The lead may revert
them.

## How verified

Manifests (script in the job tmp directory, read-only, mgnp interpreter with `-I`):

```
/u/swong2/.conda/envs/mgnp/bin/python -I /u/swong2/.claude/jobs/5b9b1c28/tmp/frte8/manifests.py /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_studies/b3
```

Observed, key lines:

| Manifest | git_commit | git_dirty | seed |
|---|---|---|---|
| `outputs/_studies/b3/j4_syc/run_manifest.json` | 21bc397a304f778131214d41191e3392f125481f | false | 0 |
| `outputs/_studies/b3/j4_syc_supplement/run_manifest.json` | c32627e37900e23a63f3deb8d1b955182700647b | false | 0 |
| `outputs/_studies/b3/parity/run_manifest.json` | a6ae1a68f3b7f66bcecf3d334baf4fde6e7f48e4 | false | 0 |

All three record the same `code_sha256` for seven files (`component_analysis/hooks.py`, `scripts/b3_patch.py`,
`spontaneous/{af_prompts,patching,proxy,sets,stats}.py`; `b3_patch.py` is c95ced73…). The supplement argv is
`--sets heads_only,S_far,S_ser`. Parity `abs_diff` is 0.0 at both positions. The J4 and supplement manifests name
`data/b3/syc_items.json` with sha256 4a9e5e5a…, and `sha256sum` of the worktree copy gives the same hash. The
claim "git log shows no change between the commits" was not re-checked, because workers do not run git. The hash
identity is the evidence used.

Subject-clustered interval (see Execution evidence).

Top 25 outside senders (F-rte-005 wording, not in F-rte-008):

```
/u/swong2/.conda/envs/mgnp/bin/python -I /u/swong2/.claude/jobs/5b9b1c28/tmp/frte8/layers_logits.py
```

Observed: ranked by absolute offline `e` on arm T over in-sum outside senders, FAR gives layers 22 to 31 and mediated
fraction e(dq_all)/e(T) 0.300 to 0.696; SER gives layers 22 to 31 and 0.241 to 0.733. Ranked by signed e, the
layers are 20 to 31 and the fractions no longer match the row. So the row's 0.30 to 0.70 and 0.24 to 0.73 use the
absolute ranking, under which the layers are 22 to 31, not 18 to 31.

Key-arm dispersion (F-rte-006 wording, not in F-rte-008):

```
/u/swong2/.conda/envs/mgnp/bin/python -I /u/swong2/.claude/jobs/5b9b1c28/tmp/frte8/keyarm.py
```

Observed: mean |m_D − m_arm| from `baseline.m_D` and `arms.<arm>.margins` is 0.208 on FAR and 0.169 on SER for
`k_options`, against 0.019 to 0.030 for the seven other-group key arms and five random-position key arms, and 0.0
for `kv_preclause_mentions`. In units of mean G these are 0.021 and 0.028. So "0.21 and 0.17 against 0.02" is in raw
logits.

F-rte-008 caveat imprecisions:

```
/u/swong2/.conda/envs/mgnp/bin/python -I /u/swong2/.claude/jobs/5b9b1c28/tmp/frte8/caveats.py
```

Observed: at the post-cue span Gupta's six reverse 113 flips and the quartet 93, with 0 not reversed by S_all there.
At the readout they reverse 73 and 60, with 2 and 1 not reversed by S_all at the readout and 0 not reversed by S_all
at the post-cue span. S_all post-cue null draws with |f| < 0.05 are draws 0, 3, 4, 13, 17 and 18, reversing 0.429,
0.344, 0.299, 0.429, 0.351 and 0.390 of flips.

Checks on the edited file, after all four row edits:

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence && /u/swong2/.local/bin/research-session findings-check --root /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research
```

Observed, exit 0:

```
findings-check: 0 error(s), 0 warning(s)
```

Without `--root`, findings-check reads the main checkout's FINDINGS.md even when run from the worktree. Run that
way, it still reports the F-mech-009 error from main's unedited copy, exit 1. The worktree file must be checked with
`--root` until the orchestrator commits it.

```
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/FINDINGS.md
```

Observed: exit 0, no output.

`diff` against the main checkout's FINDINGS.md shows exactly four changed rows: F-mech-009, F-rte-005, F-rte-006 and
F-rte-008. Each is still one table line.

## Execution evidence

- Job id and cluster: local login-node command, no Slurm job, no GPU.

  ```
  cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports && /u/swong2/.conda/envs/mgnp/bin/python -I f-rte-008-interval-repro.py /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_studies/b3/j4_syc/margins.json /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/data/b3/syc_items.json /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_studies/b3/j4_syc/results.json /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/f-rte-008-interval-repro.json
  ```

  Printed:

  ```
  S_all@post_tag: f 0.7241 (stored 0.7241); item CI seed 0 0.7017 to 0.7463 (stored 0.7017 to 0.7463)
    subject-clustered seed 1: 0.669 to 0.770
    subject-clustered seed 0: 0.672 to 0.772
    subject-clustered seed 20261101: 0.672 to 0.771
  S_q@post_tag: f 0.3315 (stored 0.3315); item CI seed 0 0.3109 to 0.3522 (stored 0.3109 to 0.3522)
    subject-clustered seed 1: 0.292 to 0.369
    subject-clustered seed 0: 0.293 to 0.370
    subject-clustered seed 20261101: 0.292 to 0.370
  kept 530 of 800, 56 subjects
  ```

- Exit code: 0.
- Row counts: 530 kept of 800 items against 530 of 800 in the row; 56 subjects against 56.
- Baseline reproduces: S_all post-cue f 0.7241 against 0.7241 stored, and the item bootstrap 0.7017 to 0.7463
  against 0.7017 to 0.7463 stored. The seed 1 subject-clustered interval is 0.669 to 0.770 against 0.669 to 0.770 in
  the row.
- Provenance files, with the 40-hex commit each names:

  | Manifest | Commit |
  |---|---|
  | `outputs/_studies/b3/j4_syc/run_manifest.json` (wrote `margins.json`) | 21bc397a304f778131214d41191e3392f125481f |
  | `outputs/_studies/b3/j4_syc_supplement/run_manifest.json` | c32627e37900e23a63f3deb8d1b955182700647b |
  | `outputs/_studies/b3/parity/run_manifest.json` | a6ae1a68f3b7f66bcecf3d334baf4fde6e7f48e4 |

The S_q seed 1 interval prints 0.292 to 0.369, while the J4 review states 0.292 to 0.371. S_q's clustered interval
is not in the row, so nothing changes; the difference is recorded here only.

## What is NOT done

- The "no script changed between 21bc397 and c32627e" part of the review was not re-checked with git.
- The F-rte-006 "against 0.02" was left as written, per the lead's "change nothing else". The verified control range
  is 0.019 to 0.030 logits.

## Open questions

- The flip-coverage and near-zero-range fixes in F-rte-008 go beyond the four listed points. Default: keep them.
