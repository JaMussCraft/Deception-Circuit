# Review 02: B2 P2, the SDR wish test

Independent Opus review, Sun 1 Nov 2026, of Slurm job 23412228 (Delta, A100 40 GB interactive, host gpua034). I read
the six cells, the manifests, the log, the group file and the wish dataset directly. I recomputed every f value and
both clustered intervals from `knockout/groups_instances.json`. I did not read a result report. CPU only, mgnp
interpreter, no git.

**Verdict: trustworthy with caveats.** The computation is clean, and the rule outcome is unambiguous. The quartet's
f_wish is 0.540 and clears 0.5 with both clustered lower bounds. No null quartet or KV group comes near 0.5, so the
"not quartet-specific" label does not apply. The caveats are bookkeeping and reading. The six manifests record four
different commits, because the manifest fingerprints git when each cell is written while the branch moved during the
job. The decision cell ran on a dirty tree. The manifest hashes only the entry script and, for the wish cells, not the
wish dataset. And f is an indirect-effect share through the quartet's output, not evidence that the quartet itself
reads the clause.

Rule outcome (spec R3): f_wish(quartet) = 0.540 at least 0.5, so the wish runs through the route. Quartet-specific:
the largest null quartet is 0.033 and the largest other KV group is 0.005.

## 1. Provenance

- **Job.** `sacct` gives 23412228 COMPLETED, exit 0:0, start 14:30:56, end 14:55:49 (24:53), partition
  gpuA100x4-interactive, node gpua034, one GPU. The log ends "batch: 6 of 6 invocation(s) ok". Each cell's
  `slurm_job_id` is 23412228 and its host is gpua034.
- **Cells.** All six cells (`wish_` and `sdrd_` crossed with `all`, `readout` and `after`) have `knockout/groups.json`,
  `knockout/groups_instances.json` and `run_manifest.json`. Each has 29 groups, and each group file's `source.sha256`
  is `21186201…`, the hash of `groups/p2_groups.json`.
- **Commit.** Every manifest has a 40-hex `git_commit`, but they differ across cells:

| cell | written | git_commit | dirty | dirty_diff_hash |
| --- | --- | --- | --- | --- |
| wish_all | 14:35:58 | a7827d4 | yes | 4c48b554… |
| wish_readout | 14:39:55 | 0ac1c17 | no | none |
| wish_after | 14:43:52 | e885200 | yes | 7beeae34… |
| sdrd_all | 14:47:50 | e885200 | yes | 1d542208… |
| sdrd_readout | 14:51:47 | 384e387 | yes | c69a2772… |
| sdrd_after | 14:55:45 | 384e387 | yes | c69a2772… |

  `run_manifest.py` reads HEAD and the diff when it writes each cell. The orchestrator committed during the job
  (0ac1c17 the falsity-probe script, e885200 a B1 hand-back, 384e387 the F-rte-001 FINDINGS row). The code that ran was
  fixed at process start. The batch is one Python process with one model load. The registry imports every analysis
  module, `route_closure` included, when it builds the parser, because `add_arguments` is a required export. The only
  file under `component_analysis/` with an mtime after 14:30:56 is `route_closure.py` (14:49:26), which was already
  imported and is not on the knockout path. `knockout.py` (13:48:24), `batch.py` (14:21:28), `dataloaders.py`,
  `instances.py` and `registry.py` all predate the job. `code_sha256` of `analyze_components.py` is `10e38857…` in
  all six manifests and equals the file in the worktree now. The decision cell's dirty hash `4c48b554…` is the same diff
  that review 01 traced to `scripts/falsity_probe.py` and docs, none of them imported. The FINDINGS row should carry
  a7827d4, the decision cell's commit and the one F-rte-001 carries.
- **Dataset hashes.** `dataset_files` in every manifest hashes `data/datasets/sdr_v2` only. The wish cells read
  `sdr_v2_inversion_reported` and the twin from `sdr_v2_honest`, and neither is hashed. The log confirms the loads
  ("618 samples" from `sdr_v2_inversion_reported`, "1000 samples" from `sdr_v2_honest`).
- **Ids and counts.** In all six cells the instance list has 618 unique ids. That set equals
  `groups/sdr_wish_ids.txt` (618 unique) and the `instance_id` column of the wish dataset (618 rows). Unpaired ids are
  0 in both `groups.json` and `groups_instances.json`. The clean and twin runs each have n = 618. The six cells list
  the ids in the same order.
- **Clusters.** From the dataset's own columns, the 618 ids carry 41 `instructed_inversion_id` values and 20
  `pressure_id` values. The sensitivity subset (561 ids) carries 40 and 20.
- **Groups.** The quartet is heads 24 to 27 of layer 17, which is exactly KV group 6. The seven KV groups are 4g to
  4g+3 for g not 6. I regenerated all 20 null quartets from the rule `random.Random(20261101 + i).sample(heads 0..31
  minus 24..27, 4)`. All 20 match, none overlaps the quartet, the 20 sets are distinct and none equals a KV group.
- **Twin alignment.** `knockout.py` raises when a twin does not end at its prompt's readout. No such error occurred.
  So every reported-wish prompt has the same token length as its neutral twin.

## 2. Execution checks and bf16 drift

| check | expected | observed | within 0.05 |
| --- | --- | --- | --- |
| n | 618 | 618 | yes |
| unpaired | 0 | 0 | yes |
| mean clean wish margin m_I | 3.15 | 3.1445 | yes |
| mean twin margin m_tw | -2.92 | -2.9214 | yes |

Per-row reproduction against the dataset values, on the 618 rows:

| quantity | dataset mean | run mean | mean deviation | mean abs deviation | sd | max abs |
| --- | --- | --- | --- | --- | --- | --- |
| m_I against `clean_margin` | 3.1507 | 3.1445 | -0.0062 | 0.0792 | 0.1004 | 0.354 |
| m_tw against minus `h_neutral_clean` | -2.9163 | -2.9214 | -0.0051 | 0.0797 | | 0.349 |
| SDR D clean against `i_source_clean_margin` | 4.1513 | 4.1530 | 0.0017 | 0.0844 | | |

The per-row deviation of about 0.08 matches the P1 smoke's A100 drift. It cannot move f much, for a structural
reason: m_I, m_tw and m_KO all come from the same A100 bf16 run, so cross-hardware drift enters f only as noise, never
as a mismatch between numerator and denominator. Unbiased noise of sd 0.10 on 618 rows moves each mean by about
0.004 and f by about 0.001. For a bound, the denominator is 6.066 and the numerator 3.273. The mean knocked margin
would have to rise by 0.240 to bring f to 0.5, which is three times the per-row mean absolute deviation and about 40
times the observed mean deviation. A systematic 0.1 on the knocked mean alone gives 0.523. Shifting all three means
by 0.1 in the worst direction gives 0.507. Drift cannot flip the verdict.

## 3. The verdict, recomputed

f = (mean m_I - mean m_KO) / (mean m_I - mean m_tw). Intervals are 2,000 cluster resamples, percentile 95%. My
bootstrap seed differs from the reader's (20261101), so the interval ends differ in the third decimal.

| group | cell | f (mine) | f (reader) | CI by clause, mine | CI by clause, reader | CI by pressure, mine | CI by pressure, reader |
| --- | --- | --- | --- | --- | --- | --- | --- |
| quartet | wish_all | 0.5395 | 0.5395 | 0.522 to 0.555 | 0.524 to 0.555 | 0.521 to 0.555 | 0.519 to 0.554 |
| L17H24 | wish_all | 0.3631 | 0.3631 | 0.354 to 0.371 | 0.354 to 0.371 | 0.352 to 0.372 | 0.352 to 0.371 |
| quartet | wish_readout | 0.5125 | 0.5125 | 0.494 to 0.530 | 0.496 to 0.529 | 0.495 to 0.527 | 0.493 to 0.527 |
| quartet | wish_after | 0.0293 | | 0.027 to 0.032 | | 0.028 to 0.031 | |
| quartet | sdrd_all (f_D) | 0.5813 | 0.5813 | 0.567 to 0.595 | 0.566 to 0.595 | 0.558 to 0.604 | 0.559 to 0.604 |
| quartet | sdrd_readout | 0.5507 | | 0.535 to 0.564 | | 0.527 to 0.575 | |
| quartet | sdrd_after | 0.0388 | | 0.036 to 0.042 | | 0.034 to 0.043 | |
| quartet | wish_all, 561 ids | 0.5386 | 0.5386 | | 0.522 to 0.554 | | 0.519 to 0.554 |

Every group's recomputed knocked mean and mean drop equal `groups.json` to 1e-9.

- **The seven KV groups (wish_all):** kvg_0 0.0025, kvg_1 0.0005, kvg_2 -0.0009, kvg_3 0.0047, kvg_4 0.0002, kvg_5
  -0.0032, kvg_7 0.0051. The maximum is kvg_7 at 0.005.
- **The 20 null quartets (wish_all):** mean 0.0014, sd 0.019, range -0.038 (null_d03) to 0.033 (null_d12).
- **Rows.** The quartet interchange pushes m_KO below 0 on 384 of 618 rows, L17H24 alone on 123. On SDR D it does so
  on 349 of 618. The median per-row ratio is 0.535.
- **Sensitivity.** Dropping the 57 ids shared with the SDR held-out sample leaves 561 ids and f = 0.5386, a change of
  0.001.
- **Margin over the rule.** R3 is a point rule. The point estimate clears 0.5 by 0.040, and both clustered lower
  bounds clear it by about 0.02.

## 4. Interpretation risks

- **Where the effect sits.** readout 0.513 plus after-the-clause 0.029 gives 0.542, against 0.540 at all positions.
  So the clause span and the positions before it contribute nothing measurable (about -0.002). On SDR D the same split
  gives 0.551 plus 0.039 against 0.581. The share lives at the readout, where the quartet is query-fed (F-mech-007).
  The readout-only cell's clause-clustered lower bound is 0.494, but the plan marks that cell as locating, not deciding.
- **Mediation, not total effect.** The interchange writes the quartet's output from a full forward pass on the
  neutral twin. That value carries everything upstream of layer 17 that differs on the twin, including the clause
  readers of layers 7 to 14. So m_I - m_KO is the share of the clause-to-answer effect that passes through the
  quartet's output, with downstream components free to react. It is an indirect-effect share. It does not say whether
  the quartet reads the clause itself or relays what earlier heads computed. It is not a zero-ablation total effect
  of the quartet, which would also remove its ordinary answer work. Because the clause positions add nothing, the
  concern that the all-positions interchange also replaces the quartet's reading at the clause tokens is moot here.
- **Self-repair (plan risk 4).** Downstream compensation can only shrink the measured drop, so 0.540 is a floor on the
  route's share under that risk, not a ceiling. The plan reads f_wish against f_D. The ratio is 0.540 / 0.581 = 0.93.
  This run cannot measure self-repair directly.
- **Do the wish and the instruction share the route.** Two similar scalar shares are weak evidence alone. The
  stronger evidence is per row. On the identical 618 ids with the identical twin stream (the twin margins are equal
  row for row across `wish_` and `sdrd_` cells), the per-row ratios correlate at 0.80 and the per-row drops at 0.54,
  while the clean margins correlate at only 0.43. That is consistent with a shared route through the quartet. It is
  not a demonstration that the quartet carries the same content in both, which a cross-patch from the D stream into
  the wish stream would test.
- **Selected rows.** The 618 ids are the SDR rows where the reported wish flips the choice (F-mech-012). f_wish and
  f_D are both conditional on those ids, and the result says nothing about rows where the wish fails.
- **The plan's reading.** The plan maps f_wish of at least 0.5 to "the quartet routes any stated preference: a
  selector, not deception machinery". The data support a route shared by the instruction and a third-party wish. That
  belongs in the review and synthesis, not in the FINDINGS claim.
- **Log.** No warnings, errors or skipped rows. Each of the six invocations loaded its dataset, ran 29 groups in 231
  to 232 s and wrote its three files. The only messages besides loads are "0 Component(s) updated", which is expected
  for a groups-only pass with singles off.

## 5. Strength

The execution-evidence block is complete from primary sources: job 23412228 COMPLETED 0:0 in 24:53; n = 618 with 0
unpaired in every cell; m_I 3.1445 against 3.15 and m_tw -2.9214 against -2.92; a 40-hex commit in every manifest.
The result deserves **reviewed** with commit a7827d4. Before a later "replicated" status, the open items are a
code-tree hash in the manifest (all of `component_analysis/`), hashes of the task and twin datasets actually read, and
a manifest fingerprint taken at process start.

## Proposed FINDINGS row

| F-rte-002 | 2026-11-01 | instructed-route | Does the reported SDR wish run through the layer 17 quartet H24 to H27: yes, its neutral-twin interchange at all positions removes 0.540 of the wish effect on the 618 reported-wish ids (interval 0.524 to 0.555 clustered by 41 clauses, 0.519 to 0.554 by 20 pressure ids), against at most 0.033 for 20 random layer 17 quartets, 0.005 for the 7 other layer 17 KV groups and 0.363 for L17H24 alone, with 0.513 at the readout and 0.029 after the clause, while the same interchange removes 0.581 of the SDR D effect on the same ids. | reviewed | a7827d4 | docs/research/instructed-route/results/p2/p2_wish.json<br>docs/research/instructed-route/reviews/02-p2-review.md<br>outputs/_analyses/instructed-route-b2/p2/wish_all/U__leaf/sdr_v2/run_manifest.json<br>outputs/_analyses/instructed-route-b2/p2/sdrd_all/U__leaf/sdr_v2/run_manifest.json | docs/research/instructed-route/reviews/02-p2-review.md |
