# Hand-back 10: B2 ticket T4, the R-cls port and the P2 and P3 readers

Agent: ticket implementer (Opus), impl-B2-t4. Ticket: `docs/research/instructed-route/plans/B2-plan.md` section 6, T4.
Status: resolved.

## What changed

Committed by the orchestrator from the worktree. All four files are new, and no existing file was edited.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/rcls.py`
  ports R-cls. The code is identical to lines 12 to 68 of the untracked
  `outputs/_launch_mechanism_analysis/p1_readings.py`, checked with `diff`. The module docstring names the source,
  the job and the definitions.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/instructed_route_b2_read.py`
  holds the readers.
  - `p3` reads the D, H and F `knockout/groups.json` of each run and task from a layout JSON. It writes
    `results/p3_rcls.csv` and `results/p3_verdict.json`.
  - The `p3` verdict is per MLP: "replicates", "fails" or "not yet verified" with each missing item named. It also
    has an optional seed-0 baseline check against `rcls.csv`, which requires d within 0.01 and the same class.
  - `p2` reads `groups.json` and `groups_instances.json` and computes f_wish per group. Its CIs are 2,000-resample
    whole-cluster bootstraps, seed 20261101, clustered once by `instructed_inversion_id` and once by `pressure_id`.
  - `p2` also reports the largest null of each kind, the 0.5 verdict with the R3 label "not quartet-specific" and
    the section 7 execution checks. It writes `results/p2_wish.json`. Optional descriptive extras are position-set
    cells, reference cells such as SDR D for f_D, and a sensitivity row that drops given ids.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/fixtures/instructed_route_rcls_golden.json`
  is the golden fixture. It holds the seed-0 sweep entries of SER mlp.11, mlp.13 and mlp.16 and FAR mlp.13 from S1
  (D), S5 (H) and S6 (F), with their source paths. It also holds the class, d, sig, m_HF and U_HF that `rcls.csv`
  records for those rows. It was extracted on CPU with a scratch script that is not part of the commit.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_instructed_route_b2_read.py`
  holds 30 tests.

Nothing is staged for the apply tool.

## How verified

```
diff <(sed -n 12,68p /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_launch_mechanism_analysis/p1_readings.py) <(sed -n '/^from __future__/,$p' component_analysis/rcls.py) && echo IDENTICAL
```

Observed: `IDENTICAL`.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_instructed_route_b2_read.py
```

Observed: `30 passed in 1.57s`. Before the code existed, the same command failed at collection with
`ImportError: cannot import name 'rcls'`.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_instructed_route_b2_read.py
```

Observed: `30 passed in 9.57s`.

The tests cover each item the ticket names:

- The golden fixture reproduces the class, d, sig, m_HF and U_HF of `rcls.csv` to 1e-9.
- f is 1 when the knockout equals the twin and 0 when it equals the clean margin.
- An f of 0.5 passes and 0.4999 fails, both as numbers and through a cell.
- The bootstrap resamples whole clusters: two internally constant clusters give at most three distinct f values. The
  bootstrap is identical under the same seed, differs under another seed and does not depend on instance order.
- A run without a manifest reads "not yet verified" and names the file. A commit that is not 40-hex does the same.
- A `null_d` or `kvg_` group at 0.5 adds "not quartet-specific", and L17H24 alone is not treated as a null.

The extra tests cover a single replication run, a class failure in one run, CSV and JSON output, a baseline pass from
the golden entries and a baseline miss. They also cover missing cluster ids, the sensitivity exclusion and the
section 7 checks through the function and the CLI. D, H and F cells are compared by id set, not list order, because
H and F come from other dataset directories. One test lists the same ids in another order and still replicates, and
another with different ids reads "not yet verified".

```
python /u/swong2/.claude/jobs/230e4716/tmp/check_clusters.py   # load_clusters() on data/datasets/sdr_v2_inversion_reported
```

Observed on mgnp: `3.12.13 ids 618 inversion clusters 41 pressure clusters 20`. Base 3.9 gave the same counts.

`docs/research/instructed-route/groups/p2_groups.json` was written by T3. It names `quartet`, `L17H24`, `kvg_0` to
`kvg_7` without `kvg_6`, and `null_d00` to `null_d19`, which matches the reader's defaults. T3's `p3_groups.json`
holds one-member MLP groups. `knockout.component_label` writes their members as `mlp.11.0` and so on, the labels
`rcls.csv` uses, and the reader keys its rows by that label.
```
research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/10-handback.md
```

Observed: no output, exit 0.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No reader has run on real P2 or P3 output, because those jobs have not run.
- The full test suite was not run. Only the new test file was run, on both interpreters. The ticket adds new files
  and edits none, so no existing test imports them.
- T8 still has to write the P3 layout JSON that `p3 --layout` expects, and its ticket does not mention it. The format
  is below, and each DIR is a cell directory `<root>/<circuit>/<task>`, its `knockout/` or the `groups.json`.

```
{"replication_runs": ["seed1", "seed2"], "baseline_run": "seed0",
 "runs": {"seed1": {"cells": {"ser": {"D": DIR, "H": DIR, "F": DIR}, "far": {...}, "sdr": {...}}}, ...}}
```

## Open questions

- **Which manifests count for "each run directory".** T1 writes one manifest per cell, so the reader requires one in
  each SER D, H and F cell of both runs. Default: keep that stricter reading.
- **Whether a quartet that fails still gets the "not quartet-specific" label.** R3 says "also reaches", but plan
  section 2 says any null at 0.5 sets the label. Default: attach the label whenever a null reaches 0.5, whatever the
  quartet's f, so a strong null is never hidden.
- **Whether the section 7 checks gate the verdict.** In P2, a failed check or a missing manifest turns the status to
  "not yet verified" and leaves the computed f and verdict text in place. Default: keep this.
- **Which clusters the reference cell uses.** SDR D for f_D uses the wish rows' cluster ids by instance id. Default:
  keep it, since f_D is descriptive.
