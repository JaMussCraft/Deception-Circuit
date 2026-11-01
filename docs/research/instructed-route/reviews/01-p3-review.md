# Review 01: B2 P3, the SER MLP replication

Independent Opus review, Sun 1 Nov 2026, of Slurm job 23412229 (Delta, H200, host gpue07). I read the cells, the
manifests, the log and the original sweeps directly and recomputed every class with `component_analysis/rcls.py`. I
did not read a result report. CPU only, mgnp interpreter, no git.

**Verdict: trustworthy with caveats.** The computation is clean. Seed 0 reproduces the original selection-sample sweeps
bit for bit, and the reader's CSV and verdict match my recompute exactly. The caveats are bookkeeping. The manifests
record commit a7827d4, not the 4ba00fc named in the brief. 20 of 21 cells ran on a dirty tree. And the "SER alone"
reading does not hold cleanly for mlp.13, the one MLP that replicates.

Rule outcome: mlp.13 replicates (deception-leaning on SER in seed 1 and seed 2). mlp.11 fails (seed 1 "none", seed 2
deception-leaning). mlp.16 fails (seed 1 and seed 2 "none").

## 1. Provenance

- **Cells.** All 21 cells exist (seed 0: SER D, H, F; seeds 1 and 2: FAR, SDR, SER by D, H, F). Each has
  `knockout/groups.json`, `head_table.json` and `run_manifest.json`. The log ends "batch: 21 of 21 invocation(s) ok".
- **Commit.** Every manifest has a 40-hex `git_commit`, and it is the same in all 21:
  `a7827d4e0e03e87da3090cf0b32007f7d659d7c1`. That is not 4ba00fc as the brief states. a7827d4 is the next commit on
  the branch (B3 T4, which also made batch lines pass their own argv to the manifest), so it was HEAD at run time. The
  FINDINGS row should carry a7827d4.
- **Code.** `code_sha256` of `analyze_components.py` is `10e38857…` in all 21 manifests and equals the file in the
  worktree now. `slurm_job_id` is 23412229 and `seed` matches the run in every cell.
- **Dirty tree.** seed0_d (14:34:01) has `git_dirty: false`. The other 20 cells (14:34:08 to 14:36:29) have
  `git_dirty: true` with one constant `dirty_diff_hash` `4c48b554…`. The files modified in that window, outside
  `outputs/`, are `scripts/falsity_probe.py` (B2 T7, committed later as 0ac1c17), `RESUME.md` and hand-backs 20 and 21.
  None is imported by `analyze_components.py`. `component_analysis/route_closure.py` has mtime 14:43:52, after the last
  cell. The batch is one Python process that imported its modules before the first cell. The decisive evidence is
  empirical: the dirty seed0_h and seed0_f cells reproduce the original sweeps to 0.0 per instance (check 2). The
  limitation is that the manifest hashes only `analyze_components.py`, not `component_analysis/*.py`.
- **Id files.** `{ser,far,sdr}_seed{0,1,2}_ids.txt` each hold 100 unique ids. Within each task the pairwise overlaps of
  seeds 0, 1 and 2 are 0, 0 and 0. Seed 0 equals the selection `sample.json` of S1, and seed 1 equals
  `docs/research/mechanism-analysis/phase1/groups/<task>_heldout_D_sample.json`, for all three tasks.
  `b2_inputs_meta.json` records seed 2 as a stratified `draw_sample` with seeds 0 and 1 excluded.
- **Per cell.** In every cell the `--include-ids` argument is the run's id file. The `instances` set equals that file,
  there are 100 instances, every group has n = 100, the clean run has n = 100 and there are 0 unpaired ids. The plan
  is item-swap at all positions. D cells read in the deceptive direction, H and F cells in the honest direction.
- **D, H and F alignment.** Within each of the 7 (run, task) triples the D, H and F instance lists are identical in set
  and in order.

## 2. Reproduction of rcls.csv (seed 0, SER)

The seed-0 cells are compared with the original S1 (D), S5 (H) and S6 (F) `sweep.json` files under
`outputs/_analyses/mechanism-analysis-p1/` in the primary checkout.

| MLP | d(D) | d(H) | d(F) | class | rcls.csv | max abs diff |
| --- | --- | --- | --- | --- | --- | --- |
| mlp.11 | 0.2386 | 0.0587 | 0.0373 | deception-leaning | deception-leaning | 0.0 |
| mlp.13 | 0.2034 | 0.0066 | 0.0048 | deception-leaning | deception-leaning | 0.0 |
| mlp.16 | 0.1752 | 0.0363 | 0.0434 | deception-leaning | deception-leaning | 0.0 |

The match is exact, beyond the 0.01 tolerance. The instance lists are equal in order. The clean margins are equal
(2.3547, 3.7087, 3.5584). The per-instance clean, counterfactual and knocked logit differences are equal to 0.0 for all
six groups in D, H and F, including the controls. So there is no positional or item-swap mismatch between the groups
path and the sweep path.

## 3. The verdict, recomputed

I rebuilt `{drop, se, clean}` from each `groups.json` (`mean_drop`, `standard_error`,
`clean_run.mean_logit_difference`) and ran `rcls`. All 42 rows of `p3_rcls.csv` agree with my recompute on d(D), d(H),
d(F) to 1e-12 and on class (0 mismatches). `p3_verdict.json` follows from those classes.

SER, per seed. The ratio column is d(D) / (2 U_HF), the deception-leaning bar (at least 1 passes). z is drop / SE.

| MLP | seed | class | d(D) | d(H) | d(F) | z(D) | z(H) | z(F) | U_HF | ratio | d(D)/m_HF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mlp.11 | 0 | deception-leaning | 0.239 | 0.059 | 0.037 | 8.37 | 2.24 | 1.82 | 0.110 | 1.09 | 4.1 |
| mlp.11 | 1 | none | 0.202 | 0.055 | 0.064 | 7.63 | 2.04 | 3.01 | 0.107 | 0.94 | 3.2 |
| mlp.11 | 2 | deception-leaning | 0.211 | 0.035 | 0.026 | 8.70 | 1.54 | 1.42 | 0.079 | 1.34 | 6.1 |
| mlp.13 | 0 | deception-leaning | 0.203 | 0.007 | 0.005 | 5.06 | 0.19 | 0.19 | 0.074 | 1.37 | 31 |
| mlp.13 | 1 | deception-leaning | 0.163 | -0.007 | -0.001 | 4.35 | -0.23 | -0.02 | 0.055 | 1.47 | n/a |
| mlp.13 | 2 | deception-leaning | 0.217 | -0.017 | -0.022 | 5.65 | -0.48 | -0.95 | 0.053 | 2.06 | n/a |
| mlp.16 | 0 | deception-leaning | 0.175 | 0.036 | 0.043 | 8.00 | 1.78 | 2.33 | 0.080 | 1.10 | 4.0 |
| mlp.16 | 1 | none | 0.150 | 0.040 | 0.044 | 8.36 | 1.72 | 2.56 | 0.085 | 0.88 | 3.4 |
| mlp.16 | 2 | none | 0.151 | 0.034 | 0.046 | 7.95 | 1.58 | 2.51 | 0.082 | 0.92 | 3.3 |

Controls on SER, seeds 0, 1 and 2:

| MLP | class (all three seeds) | d(D) | d(H) | d(F) |
| --- | --- | --- | --- | --- |
| mlp.30 | opposes | -0.259, -0.238, -0.190 | -0.180, -0.183, -0.104 | -0.195, -0.193, -0.126 |
| mlp.31 | shared | 0.230, 0.273, 0.235 | 0.311, 0.355, 0.301 | 0.285, 0.319, 0.282 |
| mlp.0 | shared | 1.969, 1.990, 1.868 | 1.863, 1.920, 1.846 | 1.885, 1.881, 1.843 |

The positive control mlp.0 sits at d about 1.9 as the plan expects, and the controls keep one class across all seeds
and tasks.

**Near-miss or clear.** Every failure is on the factor-two bar against U_HF, never on the 2 SE bar: z(D) is 7.6 to 8.4
in each failing cell. The shortfalls are 6% for mlp.11 seed 1 (d(D) 0.202 against 2 U_HF 0.214), 12% for mlp.16 seed 1
(0.150 against 0.170) and 8% for mlp.16 seed 2 (0.151 against 0.164). For mlp.11 seed 1, H at z 2.04 only just clears
2 SE, but that does not decide the class. F is significant (z 3.01) anyway, the ratio to m_HF (3.2) is outside
[0.5, 2] so "shared" is out, and the factor-two bar fails on U_HF. So mlp.11 is a near-miss that splits across seeds.
mlp.16 is a consistent near-miss: it fails by 8% to 12% in both held-out seeds, and it cleared the bar on the selection
sample by only 10% (ratio 1.10). By point estimate, d(D) is 3.2 to 3.4 times the honest-side effect m_HF in every
failing cell. That is description only. The plan forbids pooling seeds, so the rule's verdict stands. The selection
values regress on held-out ids, as expected for selected components: mlp.11 d(D) went from 0.239 to 0.202 and 0.211,
and mlp.16 from 0.175 to 0.150 and 0.151. mlp.13 holds at 0.163 and 0.217 with honest-side effects at or below zero.

## 4. Threats to trust

- **Positional or item-swap mismatch.** None. The seed-0 groups cells match the original sweeps per instance, in
  order, to 0.0 (check 2).
- **bf16 drift, H200 against H100.** None observed. The seed-0 numbers are bit-identical to job 49825318. The seed-1
  clean margins are also bit-identical per instance to the earlier mechanism-analysis held-out runs (`heldout_d`,
  `heldout_h`, `heldout_f`) on all three tasks, and the H and F counterfactual margins too. H100 and H200 share the
  Hopper architecture, so identical kernels are plausible. The seed-1 D counterfactual margins differ, because
  `heldout_d` used a neutral-twin counterfactual after the pressure clause, not item-swap. So the seed-1 D cells have no
  earlier item-swap comparator.
- **Short cells.** None. Every group in every cell has n = 100, every clean run has n = 100, and no ids are unpaired.
- **Non-determinism.** None observed. The two independent comparisons above are exact. One limit remains: no cell of
  seed 2 was run twice.
- **Dirty tree and commit.** See check 1. Neither changes a number, but the manifest commit is a7827d4 and the code
  outside `analyze_components.py` is not hashed.

## 5. FAR and SDR descriptive rows (R3)

| MLP | FAR seed 1 | FAR seed 2 | SDR seed 1 | SDR seed 2 |
| --- | --- | --- | --- | --- |
| mlp.11 | shared | none (d(D)/m_HF 2.01) | none | shared |
| mlp.13 | none (ratio 0.99) | **deception-leaning** (ratio 1.34) | honest-leaning | honest-leaning |
| mlp.16 | shared | shared | shared | shared |

mlp.11 and mlp.16 stay "SER alone". Neither is deception-leaning on FAR or SDR in either seed. **mlp.13 does not stay
SER alone.** On FAR, seed 2 is deception-leaning, with d(D) 0.081 (z 3.30), d(H) 0.004 and d(F) -0.040, the last
significantly negative (z -2.62). Seed 1 misses the bar by 1% (d(D) 0.074, z 2.65, ratio 0.99). The original
`rcls.csv` had FAR mlp.13 as "none" (d(D) 0.067). The FAR effect is about 40% to 50% of the SER effect (0.074 and 0.081
against 0.163 and 0.217). On SDR, mlp.13 is honest-leaning in both seeds, as in `rcls.csv`. Under R3 these rows are
descriptive and do not change the SER verdict. But a finding should say "strongest on SER, with a weaker
deception-leaning FAR effect" rather than "SER alone".

The controls on FAR and SDR: mlp.30 opposes, mlp.31 and mlp.0 are shared, in both seeds and both tasks.

## Proposed FINDINGS row (F-rte, supersedes F-mech-009)

Claim: Do the SER deception-leaning MLPs of F-mech-009 replicate on held-out ids: only mlp.13, which is
deception-leaning on SER in 2 of 2 held-out runs of 100 ids (d(D) 0.163 and 0.217), while mlp.11 is in 1 of 2 and
mlp.16 in 0 of 2, each miss 6% to 12% short of the factor-two bar with d(D) 0.150 to 0.202, and mlp.13 is also
deception-leaning on FAR in 1 of 2 runs at d(D) 0.081, so it is not SER alone.

Commit a7827d4. Evidence: `docs/research/instructed-route/results/p3/p3_rcls.csv`,
`docs/research/instructed-route/results/p3/p3_verdict.json`, `outputs/_analyses/instructed-route-b2/p3/`. Report:
this review.
