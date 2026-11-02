# Hand-back 28: B2-T9, the P1 probe's run manifests and the I-minus-H attribution

Agent: ticket implementer (Opus), session claude-230e4716, direction instructed-route. Brief: close problems 1 and 4
of `reviews/04-p1-review.md` in `scripts/falsity_probe.py`, re-run `fit`, `score` and `read` on the P1 capture exactly
as hand-back 25 records them, and confirm that every number of hand-back 25 is unchanged. CPU only. No Slurm job, no
frozen file edited, no rule changed. I ran no git command myself. The manifest helper made its two bounded read-only
git calls, `rev-parse HEAD` and `diff HEAD`, inside the script, as the ticket requires, and the hook let them through.

## What changed

Files written:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/falsity_probe.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_falsity_probe.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_fit.json` (rewritten, byte-identical)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_fit.pt` (rewritten, byte-identical)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_probe.json` (rewritten, byte-identical)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_probe.md` (rewritten, byte-identical)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_tokens.json` (gains the two I entries and a longer `sign` text)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_tokens.md` (gains a second table)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/run_manifest.json` (new, `fit`)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/run_manifest.1.json` (new, `score`)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/run_manifest.2.json` (new, `read`)
- This hand-back: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/28-handback.md`

Scratch, not for commit: the pre-change snapshot of p1-probe in `/u/swong2/.claude/jobs/230e4716/tmp/p1-probe-before/`
and the comparison script `/u/swong2/.claude/jobs/230e4716/tmp/t9_compare.py`.

`component_analysis/probe.py` is unchanged; the logic lives in the script.

**Problem 1, provenance.** `fit`, `score` and `read` each call a new `write_manifest`, which wraps the existing
`run_manifest.write_run_manifest`. No new manifest code was written. Each manifest records:

- argv: the process argv, or the script path plus the arguments when a caller passes them;
- the git fingerprint from the `DC_RUN_MANIFEST_GIT`-aware helper;
- `code_sha256` of the script and `component_analysis/probe.py`;
- `dataset_files`, the sha256 of every input the command read. These are the capture's rows plus resid or tokens files
  of the cells it touches, `capture_plan.json` and the capture's `run_manifest.json`. `score` also lists `p1_fit.pt`
  and `p1_fit.json`;
- the seed: null for `fit`, which draws nothing, and 20261101 for `score` and `read`;
- the created time, and the helper's other standard fields.

A manifest failure is printed and never stops a run, as in the capture script. The helper never overwrites a manifest
with different content. So the three commands into one `--out` leave three files in run order: `run_manifest.json` for
fit, `run_manifest.1.json` for score and `run_manifest.2.json` for read. Each names its command in `argv[1]`. The
module docstring gains a RUN MANIFEST section saying this.

**Problem 4, the inversion contrast.** `read` adds `tasks.far_I` (FAR gate I against FAR gate H, with FAR's late
heads) and `tasks.ser_I` (SER I against SER H, with SER's late heads). It reuses `read_task`, the function that builds
the D rows, so the join is the same: an inner join on `instance_id`, a token-id agreement check per pair, and the
`pressure_id` cluster bootstrap with seed 20261101 and 2,000 resamples. The entries are skipped when a capture has no I
cell. `far_minus_ser` stays D only. `p1_tokens.md` keeps its first table unchanged and adds a second, headed
"Instructed inversion (I minus H) next to D minus H". That table sets the FAR D, FAR I, SER D and SER I columns side by
side. The `sign` text and the READ docstring say that I, not D, is the left side in those entries.

## How verified

Tests, with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`:

```
python -m pytest -p no:cacheprovider -q tests/test_falsity_probe.py tests/test_falsity_probe_capture.py tests/test_run_manifest.py
```

| interpreter | `tests/test_falsity_probe.py` | the three files together |
| --- | --- | --- |
| mgnp `/u/swong2/.conda/envs/mgnp/bin/python` | 42 passed | 85 passed |
| base `/sw/external/python/anaconda3/bin/python3.9` | 42 passed | 84 passed, 1 skipped |

The skip is the existing nnsight-pin test in `tests/test_falsity_probe_capture.py`, which reads "nnsight 0.5.12 is
installed, not the pinned 0.7.0". It is not new. The full suite was not run.

The four new tests in `tests/test_falsity_probe.py`:

- `test_read_adds_the_i_minus_h_contrast_joined_on_instance_id`. The synthetic capture gets a known I-minus-H
  contrast on both tasks. The I files' rows are in reverse order, and mlp.30 carries each row's id number on both
  files. Only an `instance_id` join can reproduce the planted -0.3 and -0.7 exactly, with sd 0. The test also checks
  the planted quartet promotion, the pair and cluster counts, CIs bracketing the means, and the markdown labels.
- `test_the_inversion_contrast_leaves_the_d_entries_unchanged`. A copy of the capture without the I cells gives
  identical D, SDR and `far_minus_ser` entries. Its markdown is a prefix of the full one.
- `test_fit_score_and_read_each_write_a_run_manifest`. It checks the three file names in run order, `argv[1]` per
  file and the manifest hash. It checks `code_sha256` against both files' real hashes and every `dataset_files` hash
  against its file. It checks which inputs each command lists, and the seeds. It also checks
  `git_fingerprint_error` "disabled", which `tests/conftest.py` sets.
- `test_a_rerun_with_identical_content_writes_no_new_manifest_and_a_failure_never_stops_the_run`. An identical rerun
  adds no file. A raising helper prints its warning, writes no manifest, and the outputs are still written.

**Number check.** I copied p1-probe to the job's temp directory before any edit. After the re-run I compared it file
by file with the comparison script named under "What changed".

## Execution evidence

Re-run from the worktree with the thread variables above and the mgnp interpreter, written `PY`. The arguments are
hand-back 25's, with the default 2,000 resamples, 200 permutations and seeds. p1-probe held no `run_manifest*.json`
before the run.

```
PY scripts/falsity_probe.py fit   --capture outputs/_analyses/instructed-route-b2/p1-cap --out outputs/_analyses/instructed-route-b2/p1-probe
PY scripts/falsity_probe.py score --capture outputs/_analyses/instructed-route-b2/p1-cap --out outputs/_analyses/instructed-route-b2/p1-probe
PY scripts/falsity_probe.py read  --capture outputs/_analyses/instructed-route-b2/p1-cap --out outputs/_analyses/instructed-route-b2/p1-probe
```

Stdout. The first lines of score and read are the helper's notice that it wrote a numbered manifest:

```
fit: selected row 18 (layer 17), C 0.001, select AUROC 1.0000; 0 fit(s) not converged
  run_manifest.json already exists with different content; wrote outputs/_analyses/instructed-route-b2/p1-probe/run_manifest.1.json instead
score: FAR gate 1.0000, rule (SER D vs H) 0.9999 [0.999826507148696, 1.0], band misleadingness, R2 instruction-confounded; reading: misleadingness, instruction-confounded: the per-token DLA carries the reading
  run_manifest.json already exists with different content; wrote outputs/_analyses/instructed-route-b2/p1-probe/run_manifest.2.json instead
read: FAR 800 pairs, SER 800 pairs; quartet FAR - SER promotion 0.083 [0.062, 0.104]
```

Fit took 17 s, score 54 s and read 9 s on the login node, manifest hashing included.

**The manifests.**

| file | command | git_commit | git_dirty | seed | inputs hashed |
| --- | --- | --- | --- | --- | --- |
| `run_manifest.json` | fit | `518d582339ee59b974dd537f66ed5ced2d3d9474` | true | null | 12 |
| `run_manifest.1.json` | score | same | true | 20261101 | 38 |
| `run_manifest.2.json` | read | same | true | 20261101 | 20 |

- **The commit is HEAD at run time.** It is 40-hex, and `git_fingerprint_error` is absent. I read the worktree's
  branch ref from the file system, without git, and it holds the same value. HEAD moved there from `8402fc4` after this
  session's start.
- **The code ran uncommitted.** `git_dirty` is true because this ticket's edits are not committed; workers do not run
  git. The hash that pins the code that ran is `code_sha256`, identical in all three files:
  - `scripts/falsity_probe.py`: `dd4f7cade4518661f3f677ced291488b8cf0039b53268b8f21eeceb5bd362724`
  - `component_analysis/probe.py`: `956dc64ccd71e0d9d241575bad21855748523b3393fa3338ea213839cf58dac0`

  After the run, `sha256sum` of the script in the worktree gives `dd4f7c...` too. So the script as it stands is the
  one that ran, and it pins these outputs if it is committed unchanged.

**Every number of hand-back 25 is unchanged.** These outputs are byte-identical to the pre-change snapshot (sha256):

- `p1_fit.json` and `p1_fit.pt`. The .pt tensors and fields are also equal under `torch.equal`.
- `p1_probe.json` and `p1_probe.md`. These hold the selected layer 17 and C 0.001, the FAR gate, the rule number
  0.99993 and its CI, all control AUROCs and CIs, the R2 label, the by-layer SER curve, the permutation null, the
  leave-one-clause-out result and the SDR rows.

In `p1_tokens.json`:

- `tasks.far`, `tasks.ser`, `tasks.sdr`, `tasks.sdr_I_reported` and `far_minus_ser` are identical to the snapshot.
  So every D attribution number and CI of hand-back 25 is unchanged.
- The only other change is the longer `sign` text.
- The new `p1_tokens.md` begins with the old file byte for byte.

**The new I-against-H numbers.** These are paired means with 95% clustered CIs (2,000 resamples, seed 20261101).
FAR I against FAR gate H has 177 pairs in 12 clusters. SER I against SER H has 194 pairs in 13 clusters. Both have
0 unjoined pairs and 0 token mismatches. D minus H is repeated from hand-back 25 for comparison.

| group | FAR D - H suppression | FAR I - H suppression | FAR D - H promotion | FAR I - H promotion |
| --- | --- | --- | --- | --- |
| whole model, centred | -4.73 (-4.98, -4.44) | -5.21 (-5.41, -5.06) | 5.05 (4.85, 5.27) | 5.19 (4.92, 5.46) |
| whole model, raw | -4.37 (-4.62, -4.11) | -4.83 (-5.03, -4.69) | 5.41 (5.20, 5.64) | 5.58 (5.27, 5.87) |
| whole model, log-softmax | -2.68 (-2.90, -2.45) | -2.62 (-2.90, -2.28) | 7.10 (6.79, 7.43) | 7.78 (7.35, 8.33) |
| quartet L17H24 to H27 | -0.143 (-0.155, -0.132) | -0.179 (-0.196, -0.166) | 0.202 (0.182, 0.219) | 0.185 (0.156, 0.202) |
| late honest heads, own task | -0.53 (-0.58, -0.47) | -0.53 (-0.60, -0.42) | 0.92 (0.87, 0.98) | 0.96 (0.90, 1.02) |
| late honest heads, FAR and SER union | -0.59 (-0.64, -0.53) | -0.59 (-0.66, -0.48) | 1.03 (0.98, 1.09) | 1.09 (1.03, 1.14) |
| mlp.30 | 0.14 (0.07, 0.21) | 0.15 (-0.00, 0.26) | -0.49 (-0.63, -0.37) | -0.52 (-0.75, -0.33) |
| mlp.31 | -0.60 (-0.77, -0.46) | -0.94 (-1.12, -0.80) | 1.39 (1.24, 1.49) | 1.16 (1.04, 1.31) |

| group | SER D - H suppression | SER I - H suppression | SER D - H promotion | SER I - H promotion |
| --- | --- | --- | --- | --- |
| whole model, centred | -3.09 (-3.38, -2.70) | -2.65 (-2.83, -2.44) | 3.09 (2.64, 3.44) | 3.15 (2.93, 3.36) |
| whole model, raw | -3.07 (-3.39, -2.63) | -2.56 (-2.78, -2.30) | 3.11 (2.72, 3.43) | 3.24 (3.00, 3.50) |
| whole model, log-softmax | -2.72 (-3.20, -2.06) | -2.54 (-2.73, -2.32) | 3.46 (3.24, 3.62) | 3.27 (3.06, 3.46) |
| quartet L17H24 to H27 | -0.120 (-0.135, -0.102) | -0.116 (-0.130, -0.102) | 0.119 (0.107, 0.127) | 0.104 (0.094, 0.114) |
| late honest heads, own task | -0.28 (-0.31, -0.24) | -0.26 (-0.30, -0.22) | 0.41 (0.38, 0.45) | 0.44 (0.38, 0.50) |
| late honest heads, FAR and SER union | -0.61 (-0.65, -0.54) | -0.54 (-0.60, -0.48) | 0.75 (0.68, 0.81) | 0.75 (0.67, 0.82) |
| mlp.30 | 0.23 (0.15, 0.30) | 0.31 (0.20, 0.40) | -0.36 (-0.42, -0.31) | -0.38 (-0.47, -0.28) |
| mlp.31 | -0.25 (-0.39, -0.06) | -0.02 (-0.18, 0.21) | 0.48 (0.31, 0.60) | 0.56 (0.35, 0.73) |

- **The review's point estimates reproduce.** Review 04 gave these whole-model values:

  | contrast | centred suppression / promotion | log-softmax suppression / promotion |
  | --- | --- | --- |
  | SER I minus H | -2.65 / 3.15 | -2.54 / 3.27 |
  | FAR I minus H | -5.21 / 5.19 | -2.62 / 7.78 |

  The script gives the same values to two decimals, and they now have intervals.
- **Measured, I against D.** I and D are close on every whole-model reading.
  - On SER, every whole-model I CI overlaps the matching D CI.
  - On FAR, the I suppression CI and the D suppression CI do not overlap in the centred and raw readings. There FAR
    I lowers the honest item by about 0.5 logits more than FAR D. On log-softmax they overlap.
  - Overlap of two marginal CIs is not a test of the D-minus-I difference, which this ticket did not compute.

## What is NOT done

- **No D-minus-I contrast.** Neither the ticket nor the review asked for one. If the write-up needs "I matches D" as
  a claim, it needs its own CI. That CI would come from a paired or independent bootstrap of D minus I on the matching
  H ids, and it is not computed here.
- **`p1-margin-check/` still has no manifest.** Review 04's problem 4 names it beside `p1-probe/`. It holds hand-back
  25's helper scripts and `taskA.json`, which `falsity_probe.py` does not write, so this ticket did not cover it.
- **No FINDINGS or other `docs/research` file was edited**, apart from this hand-back. Review 04's proposed F-rte-003
  text has two parts this ticket changes:
  - Its last caveat, "the probe output root has no run manifest", no longer holds.
  - It says the I-against-H attribution comes from the review's scripts. That attribution is now a tracked output, in
    `p1_tokens.json` under `tasks.ser_I` and `tasks.far_I`, with CIs.
- **The full test suite was not run**, only the three falsity-probe and manifest test files on both interpreters.
- **Nothing was committed.** The orchestrator commits by file list. The pre-change snapshot in the job temp
  directory is the only record of the old p1-probe bytes, apart from the matching hashes above.

## Open questions

1. **Is one manifest per command, in numbered files, the wanted shape?** The ticket says "write (or update) a
   run_manifest.json". The shared helper's rule forbids rewriting a manifest with other content. So score and read
   land in `run_manifest.1.json` and `run_manifest.2.json`, and `run_manifest.json` is fit's. `instructed_route_b2_read.manifest_problem` reads only `run_manifest.json`, and that file passes
   its 40-hex check. Default: keep the helper's rule. A merged single file would need a change to the shared helper's
   contract.
2. **Rerunning p1-probe adds manifests.** Each later run of a command writes the next free number, because `created`
   differs. Default: anyone re-running p1-probe deletes its `run_manifest*.json` first and runs fit, score and read in
   order, as was done here.
