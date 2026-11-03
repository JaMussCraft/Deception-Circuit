# Hand-back 04: W4, the R6 partition sets and the N3 stability script

Agent: implementation worker W4 (Claude, Opus). Ticket: the team lead's W4 brief of Tue 3 Nov 2026 (partition and
stability, ruling R6 of `spec.md`). Status: resolved. The script and its tests are done, and the pilot partition ran
end to end. The real inputs, a dh run with `--reverse` and the half runs, do not exist yet.

## What changed

Both code files are new. No existing file was edited. The orchestrator commits these from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_sets.py`
  is the CLI, with the subcommands `partition` and `stability`. It runs on the CPU and needs numpy, plus torch to
  read `scores.pt`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/tests/test_neuron_partition_sets.py`
  holds 15 tests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/04-w4-partition-handback.md`
  is this file.

Nothing is staged for the apply tool. The pilot outputs are temporary files under
`/u/swong2/.claude/jobs/5201d56c/tmp/w4/pilot_partition/`, and no finding rests on them.

**Which key holds each score.** These are the decisions that change the sets.

- **s_D and s_I** are `atp_<pos>_mean` of `--dh` and of `--in`.
- **s_H is minus `rev_atp_<pos>_mean`**, never minus `atp_readout_mean`. W1's `--reverse` does not write a
  separate H-clean run. It adds `rev_atp_*` to the dh run's own `scores.pt`, which is
  (a_H − a_D) · dm_H/da with m still logit(opposite) − logit(honest). A neuron that keeps H on the honest answer
  has a negative `rev_atp`, so the flip gives it a positive s_H. The `atp_*` keys of a `_rev` directory are still
  the D-clean scores. Negating them would make T_H the negative tail of s_D. The script refuses when the
  `rev_atp` key is missing, unless `--allow-missing-reverse` is passed.
- **When `--dh-reverse` names a directory other than `--dh`**, the summary records
  max |`atp_<pos>_mean`(dh) − `atp_<pos>_mean`(dh-reverse)| as a consistency check.
- **Under `--score contrast`**, s_H is minus `contrast_<pos>_mean` of dh, that is a_H − a_D, and no reverse run
  is used. Contrast has no readout orientation, so this is the only H-positive reading. As a result, T_D and T_H
  are disjoint by construction. all_shared is always empty, and H_only is T_H − T_I. The summary states this, and
  it is not a finding.

**The rest of the rule.**

- **Top-k.** For each k on the ladder (500, 1,000 and 2,000), T_X is the top k by s_X among the neurons with
  s_X > 0. If fewer than k are positive, it takes all of them, records the shortfall and adds a note. Ties go to
  the lower flat index, layer · 14,336 + index.
- **Classes.** The four classes follow R6 literally.
- **`--position clause`** reads the `*_clause_*` keys.

**Outputs of `partition`.** The tag is empty for AtP at the readout, `_contrast` for the contrast score and
`_clause` for the clause position, so all variants can share one `--out-dir`.

- **`<prefix><tag>_sets_k<k>.json`** holds the four classes and T_D, T_I and T_H as
  `{name: [["mlp_hidden", layer, index], ...]}`. Empty sets are left out, because both `load_groups` and W3's
  `parse_neuron_set` refuse empty groups. The summary records them under `empty_omitted`.
- **`<prefix><tag>_sets_k<k>_with_nulls.json`** holds each non-empty class followed by its 20 nulls, named
  `null_<class>_<k>_<i>` with i from 0 to 19. The brief's `null_<class>_<k>` would give 20 names the same, so I
  added the index. Nulls are drawn for the four classes only, not for T_D, T_I or T_H.
- **`nulls/<prefix><tag>_k<k>_<class>_nulls.json`** is W3's raw output, with its `.provenance.json` sidecar.
- **`partition_summary<tag>.json`** holds:
  - sizes and 32-bin per-layer histograms of every set;
  - the k-th score (the threshold), the maximum and the positive count of each T_X;
  - pairwise overlaps and Jaccards, and the seven Venn region counts when s_H exists;
  - the exact null command for every class;
  - provenance: the directory name, `git_commit`, `git_dirty`, `dirty_diff_hash`, `manifest_hash`, Slurm id,
    `n_rows`, the `reverse` flag, and the sha256 of `scores.pt`, `rows.json` and `run_manifest.json` for each
    input;
  - the sha256 of this script and of W3's script, the argv, and the sha256 of every output.
- **No overwrites.** Existing outputs are never overwritten without `--force`.

**The nulls call.** It is made once per non-empty class and k, with the interpreter that runs this script:

```
<python> /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_data.py nulls <out>/<prefix><tag>_sets_k<k>.json --set <class> --out <out>/nulls/<prefix><tag>_k<k>_<class>_nulls.json -k 20 --seed 2
```

The script checks that W3's file repeats the tested set unchanged before it renames the nulls.

**What `stability` does.** It takes `--dh A B --in A B --dh-reverse A B` and partitions each half with the same
rule. For each k, it reports the Jaccard between the halves of T_D, T_I, T_H and every class.

- **Ceiling.** The ceiling is J(T_D(A), T_D(B)), the same-condition split-half of the D-versus-H run, as the brief
  defines it. T_D's own row therefore sits at the ceiling by definition.
- **Analytic floor.** It is (n₁n₂/N) / (n₁ + n₂ − n₁n₂/N), with N = 458,752 and the observed sizes. When
  n₁ = n₂ = k, it equals k / (2N − k).
- **Empirical floor.** It comes from 20 draws with `default_rng([2, j])`, uniform over all N neurons and not
  layer-matched.
- **Verdict.** A set is "stable" if its Jaccard is at least half the ceiling. A set that is empty in either half
  gets "n/a".
- **Outputs.** It writes `stability_summary<tag>.json` and `stability_summary<tag>.md`.
- **No IOI floor.** START's N3 names an "IOI floor". The brief replaced it with the random-set floor, and I
  followed the brief.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q -rs tests/test_neuron_partition_sets.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q -rs tests/test_neuron_partition_sets.py
```

Observed: `15 passed in 6.11s` on mgnp and `15 passed in 5.36s` on base, with no skips. The pilot-fixture test ran
on both. The first run failed one assertion, because my hand-typed value of 1000/916504 was rounded too coarsely for
`rel=1e-8`. I corrected the constant, and the formula was not touched. The tests cover:

- **Designed classes.** Synthetic tensors with a known T_D, T_I and T_H at k = 3 produce D_only, DI_shared,
  H_only and all_shared of one neuron each, and the CLI writes them.
- **Sign flip.** s_H equals −`rev_atp_readout_mean`, a negative `rev_atp` becomes a member of T_H, and s_H is not
  −s_D.
- **Missing reverse.** It is refused without the flag. With the flag, s_H is absent and only D_only and DI_shared
  are built.
- **Truncation.** When k exceeds the positive count, all positives are taken and the shortfall is recorded. Ties
  go to the lower flat index.
- **Contrast.** s_H = −s_D, and T_D ∩ T_H is empty.
- **Clause position.** `--position clause` reads the clause keys.
- **Nulls through W3's subprocess.** There are 20 per class, named `null_D_only_500_0` to `_19`. Each has the
  same size and the same 32-layer histogram as its class, none contains a tested neuron, and all 20 are distinct.
  Empty classes are left out of both files.
- **Overwrite.** Rewriting an existing output is refused.
- **Formulas.** Jaccard, the analytic floor against k/(2N−k) and against a hand value for unequal sizes, and a
  seeded empirical floor whose mean lies within 0.002 of the analytic one.
- **Stability.** Identical halves give 1.0 and "stable", disjoint ones give 0.0 and "not stable", a class empty in
  one half gives "n/a", and the Markdown row has the expected form.
- **Pilot fixtures.** These are git-ignored, so the test skips if they are absent. It checks that n_rows = 64,
  that the commit is f4ce555, that T_D and T_I hold k each, that D_only + DI_shared = k, and that every histogram
  has 32 bins.

The groups loader W2 extended accepts the files, and the pilot nulls are matched:

```
/u/swong2/.conda/envs/mgnp/bin/python -c "... knockout.load_groups(P+f'far_sets_k{k}_with_nulls.json') ... layer_histogram checks ..."
```

Observed: `load_groups groups 42` and `nulls matched+disjoint True` at k = 500, 1,000 and 2,000. That is 2 classes
and 40 nulls per file.

`stability` was timed on real-size tensors: the pilot directories as one half and the 7386fd3 full runs as the
other, which share rows, so this is a smoke run only. It finished every computation in 7.5 s of wall time and then
failed writing its JSON with `OSError: [Errno 122] Disk quota exceeded`, for the reason given under What is NOT
done. No smoke output exists, and none is claimed.

## Execution evidence

Not applicable: no runs.

No job and no GPU were used. The one local CPU run of the pilot partition, labelled "pilot, 64 rows, not for
findings", was:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_sets.py partition --dh /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/attribution/far_v2_dh_validation_f4ce555_limit64 --in /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/attribution/far_v2_in_validation_f4ce555_limit64 --dh-reverse /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/attribution/far_v2_dh_validation_f4ce555_limit64 --allow-missing-reverse --label "pilot, 64 rows, not for findings" --out-dir /u/swong2/.claude/jobs/5201d56c/tmp/w4/pilot_partition
```

The run took 13.7 s of wall time, including 6 nulls calls. Its output, verbatim:

```
note: s_H absent: rev_atp_readout_mean is not in the --dh-reverse scores, so T_H is empty, H_only and all_shared are not built, and D_only here is only T_D - T_I
note: far_v2_dh_validation_f4ce555_limit64 was scored without --reverse; s_H needs a --reverse rerun of the dh pair
k=500: D_only 219, DI_shared 281, T_D 500, T_I 500
  thresholds: T_D 0.01675 (pos 234647), T_I 0.02962 (pos 235813)
  D_only densest layers: L13 54, L12 40, L15 30, L14 27, L31 15
  DI_shared densest layers: L13 53, L14 47, L15 45, L16 23, L31 23
k=1000: D_only 460, DI_shared 540, T_D 1000, T_I 1000
  thresholds: T_D 0.01034 (pos 234647), T_I 0.01963 (pos 235813)
  D_only densest layers: L13 117, L14 78, L12 57, L15 50, L11 39
  DI_shared densest layers: L13 106, L14 102, L15 79, L12 43, L31 42
k=2000: D_only 1010, DI_shared 990, T_D 2000, T_I 2000
  thresholds: T_D 0.006771 (pos 234647), T_I 0.01324 (pos 235813)
  D_only densest layers: L13 262, L12 171, L14 166, L11 105, L15 73
  DI_shared densest layers: L13 204, L14 184, L15 134, L12 94, L31 84
```

The readings below are descriptive only: 64 validation rows, no s_H, and no ablation.

| k | D_only | DI_shared | Jaccard of T_D and T_I | D_only share in L11 to L16 | DI_shared share in L11 to L16 | DI_shared in L31 |
| --- | --- | --- | --- | --- | --- | --- |
| 500 | 219 | 281 | 0.39 | 0.80 | 0.67 | 23 |
| 1,000 | 460 | 540 | 0.37 | 0.81 | 0.69 | 42 |
| 2,000 | 1,010 | 990 | 0.33 | 0.82 | 0.72 | 84 |

- **Overlap with I.** More than half of T_D is also in T_I at k = 500 and 1,000, and about half at 2,000.
- **Layer concentration.** Both classes sit mostly in L11 to L16, with the peak at L13.
- **L31.** DI_shared has a second, smaller block in L31, and D_only has little there.
- **Positive scores.** About 51 percent of all neurons have a positive s_D (234,647 of 458,752), so the cut at k
  is far into the positive tail.
- **Provenance.** The inputs' manifests name commit f4ce555ad223f81a0f775274164d405e5130ceb3. The summary is
  `/u/swong2/.claude/jobs/5201d56c/tmp/w4/pilot_partition/partition_summary.json`.

## What is NOT done

- **Real partition.** The real partition has not been run. No dh run with `--reverse` exists. The full runs
  `far_v2_dh_train+validation_7386fd3` and `far_v2_in_train+validation_7386fd3` have `reverse: false` (their
  manifests say `git_commit` 6c6d5be). They can give D_only = T_D − T_I only, which is not R6. The `in` run needs
  no reverse and can be reused as `--in`.
- **Stability.** Stability has not been run on halves, because no half runs exist. W1's scorer now has `--ids`,
  `--ids-key` and `--tag`, so the half runs below are possible.
- **SER.** SER is not covered by a run. The script is task-agnostic: the prefix comes from `rows.json` `task`.
- **Disk quota.** `/u/swong2` is over its file-count quota: 761k files against a 760k hard limit, while bytes are
  fine at 87 GB of 100 GB. New files under `/u/swong2`, including this job's tmp directory, fail. My message to
  team-lead also failed, probably for the same reason or because no agent goes by that name. `main` accepted the
  alert. I deleted nothing. Write the real outputs
  under `/projects`, as in the commands below.

**Commands for the orchestrator.** `<C>` is the 7-character commit the scorer puts in the directory name, and
`ATT` is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/attribution`.
Write it out in full in real commands.

1. GPU, the full ranking with the reverse pass, about 30 minutes reserved on one H100, H200 or A40. This writes
   `ATT/far_v2_dh_train+validation_<C>_rev` and `ATT/far_v2_in_train+validation_<C>_rev`.

   ```
   python scripts/neuron_attribution.py --task far_v2 --pair dh in --split train,validation --batch-size 4 --reverse
   ```

2. CPU, the partition and its contrast comparison, into one directory on `/projects`:

   ```
   /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_sets.py partition --dh ATT/far_v2_dh_train+validation_<C>_rev --in ATT/far_v2_in_train+validation_<C>_rev --dh-reverse ATT/far_v2_dh_train+validation_<C>_rev --out-dir /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/sets/far_<C>
   /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_sets.py partition --score contrast --dh ATT/far_v2_dh_train+validation_<C>_rev --in ATT/far_v2_in_train+validation_<C>_rev --out-dir /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/sets/far_<C>
   ```

   The ablation inputs are `far_sets_k{500,1000,2000}_with_nulls.json` in that directory, passed to W2's
   `scripts/neuron_set_ablation.py --sets`. That runner ablates every named set in the file and leaves the null
   comparison to downstream analysis (its hand-back 02, What is NOT done). The analysis pairs each class with
   its nulls by the name prefix `null_<class>_<k>_`.

3. GPU, the half runs, about 30 minutes each, or both in one job. W3's half A holds D ids, and the I rows matched
   by the same ids are exactly W3's `I_A`, so one key serves both pairs.

   ```
   python scripts/neuron_attribution.py --task far_v2 --pair dh in --split train,validation --batch-size 4 --reverse --ids /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/data/far_rank_ids.json --ids-key halves.A --tag halfA
   python scripts/neuron_attribution.py --task far_v2 --pair dh in --split train,validation --batch-size 4 --reverse --ids /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/data/far_rank_ids.json --ids-key halves.B --tag halfB
   ```

4. CPU, the stability report, which takes about 10 s:

   ```
   /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_sets.py stability --dh ATT/far_v2_dh_train+validation_halfA_<C>_rev ATT/far_v2_dh_train+validation_halfB_<C>_rev --in ATT/far_v2_in_train+validation_halfA_<C>_rev ATT/far_v2_in_train+validation_halfB_<C>_rev --dh-reverse ATT/far_v2_dh_train+validation_halfA_<C>_rev ATT/far_v2_dh_train+validation_halfB_<C>_rev --out-dir /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/sets/far_<C>
   ```

## Open questions

1. **AtP makes T_D and T_H nearly the same set to first order.** s_D = Δa · g_D and s_H = Δa · g_H, with the same
   Δa = a_D − a_H and the gradient taken in D or in H. Where g_D ≈ g_H, T_D and T_H coincide. all_shared will then
   be large, and D_only = T_D − (T_I ∪ T_H) keeps only neurons whose gradient differs between D and H. That is
   R6's literal rule, and I implemented it unchanged. This is a prediction, not a measurement, because no reverse
   data exist. Default: run R6 as written and read the T_D ∩ T_H Jaccard in `partition_summary.json`
   (`overlaps["T_D&T_H"]`) before planning ablations. If it is near 1, the orchestrator should rule on whether
   D_only is still the intended class.
2. **Contrast s_H.** I used s_H = a_H − a_D with no flip, because the AtP flip exists only to undo D's metric
   orientation. Applying the flip literally to contrast would make s_H = s_D and D_only empty. Default: keep
   a_H − a_D and report the contrast variant as a comparison only.
3. **Null names.** The nulls are named `null_<class>_<k>_<i>`, not the brief's `null_<class>_<k>`, so each name is
   unique. Default: keep.
4. **Nulls for T_D, T_I and T_H.** The brief said "each class", so the T sets get no nulls. If they are ablated
   too, the same nulls command with `--set T_D` covers them. Default: classes only.
