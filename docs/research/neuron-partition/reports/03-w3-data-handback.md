# Hand-back 03: W3 data preparation, matched nulls and Bridges-2 sync

Agent: implementation worker W3 (Claude Opus 5.5). Ticket: the team lead's W3 brief of Tue 3 Nov 2026 (tasks A to
D), against item 10 of `docs/research/neuron-partition/START.md` ("Ids" and "Nulls"). Status: resolved, with one
change outside the brief's file list (see What changed and Open questions).

## What changed

Committed by the orchestrator from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_data.py`
  (new). CPU-only CLI with three subcommands: `copy-pools`, `sample` and `nulls`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/tests/test_neuron_partition_data.py`
  (new). 20 tests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/remote/b2.sh`. Adds
  `"neuron-partition*"` to `FETCH_ANALYSIS_GLOBS`, with a one-line comment.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/tests/test_d4_jobs.py`. This file
  is outside my brief. Line 180 asserted the glob list exactly, so the b2.sh edit broke it. It now asserts that the
  three old globs come first and in order. I sent the lead a message before making the change and named this default.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/03-w3-data-handback.md`
  (this file).

Outputs, git-ignored, under
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/data/`:

| file | sha256 |
| --- | --- |
| `far_test_sample_seed2.json` | `cdbfca851a004069c31c1390eebcda03fc4845ce73fb6d8f2fbb50bbff48a845` |
| `far_rank_ids.json` | `724e81a084266e43f45d6515a018d6e37c84d6e12d70ca72240e626a35351842` |
| `pools_manifest.json` | `7d9b185d713d0ee6f1d32a4eef1ec4b268085d10e6595515fee6e8d6d0b70a3f` |
| `pools/far_v2_user_inversion/`, `pools/far_v2_user_neutral/` | 17 files each, hashed in `pools_manifest.json` |

Nothing is staged for the apply tool.

### The test sample (task A)

The sample has 300 rows per condition, drawn with seed 2 by `component_analysis.sampling.draw_sample`. That draw is
balanced over designation polarity, item polarity and template variant, and it sorts ids before the seeded draw.

| condition | source | rows |
| --- | --- | --- |
| D | `data/datasets/far_v2` test | 300 |
| H | `far_v2_honest`, the same ids as D | 300 |
| F | `far_v2_nopressure`, the same ids as D | 300 |
| I | `pools/far_v2_user_inversion` test | 300 |
| N | `pools/far_v2_user_neutral`, the same ids as I | 300 |

| pool | test rows | removed by exclusions | eligible | drawn |
| --- | --- | --- | --- | --- |
| D | 1,000 | 356 | 644 | 300 |
| I | 891 | 325 | 566 | 300 |

The I sample was drawn independently of D, with the same exclusions. 164 ids appear in both samples.

**Exclusions.** The sample excludes the union of four id lists, 356 ids. All four lie in the test split.

| list | path and key | sha256 of file | n | in D test | in I test |
| --- | --- | --- | --- | --- | --- |
| A1 assessment | ladder `ladder-5f450dc/design.json`, `payload.designs.far_v2.assessment_ids` | `fe8d3887…554a0d` | 100 | 100 | 100 |
| A1 selection | same file, `mover_selection_ids` | `fe8d3887…554a0d` | 100 | 100 | 88 |
| mechanism held-out D | `docs/research/mechanism-analysis/phase1/groups/far_heldout_D_sample.json` | `8d355080…2fdb66` | 100 | 100 | 91 |
| mechanism held-out I | `.../far_heldout_I_sample.json` | `a7884d54…833705` | 100 | 100 | 89 |
| `docs/research/held_out.json` | `sets` is empty | `801b24e3…70425e` | 0 | 0 | 0 |

- **Where the A1 ids were.** The brief pointed to `a1-full-77b6487-a100/` or `a1-derive-dd9aed6/`. Neither holds a
  100-id list: both hold whole splits of 200, 200 and 1,000 rows. The 100 FAR assessment ids are in the ladder design
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json`.
  The same list appears in 19 ladder files, including the A2 and A3 payloads, all with the same content.
- **Second candidate.** The same design holds a second 100-id FAR test list, the ladder's selection sample
  (`mover_selection_ids`, also `selected.json` `screen.selection_ids`). The brief said to exclude the union when several
  candidates exist, so I excluded both. Each list is recorded separately, so the selection list can be lifted.
- **Not excluded.** The design's 298-id `selection_exclusion_ids` is a list of ids the ladder itself avoided, so it
  stays in the pool. The ladder's 400-id `bank_ids` is exactly the far_v2 train and validation splits, which START
  allows for ranking.

**Act-naming filter.** No row is removed. Every far_v2 row in all three splits is act-naming under `clause_form` of
`dataset/build_inversion_v2.py`. One train row's `pressure_id`, `r8_rule_strong_far_v2_13`, is missing from
`docs/research/mechanism-analysis/clause-forms.csv`, but the text rule still calls it act-naming. Pool rows store the
neutral sentence in `pressure`. Their form is therefore read from the D row with the same id.

**Twins.** far_v2, far_v2_honest and far_v2_nopressure carry identical ids in the same order in every split. The I and
N pools carry identical ids in every split, and each pool id is a far_v2 id of the same split. No row was dropped for
lacking a twin.

**Pools.** Both pools are full copies of
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a1-control-77b6487-m07/far_v2_user_{inversion,neutral}`,
including `scores/`. They hold 177, 177 and 891 rows. In each pool, all 16 files listed in its own
`assembly_provenance.json` match their recorded sha256. The 17th file is that provenance file itself. The copies are
unmerged Codex data, read only at the source.

**Rank ids.** `far_rank_ids.json` lists the ids the scorer may rank on, after the same exclusions.

| set | train | validation |
| --- | --- | --- |
| D, with H and F twins | 200 | 200 |
| I, with N twins | 177 | 177 |

No exclusion falls in these splits.

**Split halves.** The halves are stratified by `pressure_id`, the pressure cluster of F-rte-005. The D rank ids form
13 clusters, of sizes 1 to 60. Within each cluster the ids are sorted and shuffled with `random.Random(2)`. They then
alternate between halves, and each cluster starts where the previous cluster's parity left off.

| half | D ids | I ids, which inherit the half of their D id |
| --- | --- | --- |
| A | 200 | 174 |
| B | 200 | 180 |

Every cluster splits within one id. The marginals per half are recorded in the file.

### Matched nulls (task B)

Usage:

```
python scripts/neuron_partition_data.py nulls SET.json --out OUT.json [--set NAME] [-k 20] [--seed 2]
```

- **Input.** `{name: [["mlp_hidden", layer, index], ...]}`, one set per call. Pass `--set` when the file holds
  several sets.
- **Output.** A flat groups file: the tested set followed by `null_0` to `null_{k-1}`. Provenance goes in a sidecar,
  `OUT.provenance.json`, holding the seed, k, the source path and its sha256, per-layer counts and the output sha256.
  The sidecar keeps the groups file in the shape `component_analysis/knockout.py` `load_groups` reads. That loader
  still accepts only `head` and `mlp` kinds; extending it to `mlp_hidden` is W2's job.
- **Matching.** The draw mirrors the `mlp_hidden` branch of `evaluation/masks.py` `sample_random_masks`, the null
  behind `evaluate_circuit.py --n-random`. It uses one RNG per draw, `np.random.default_rng([seed, k])`, and draws
  uniformly without replacement within each layer, in ascending layer order.
- **One departure.** The brief requires excluding the tested set's own neurons, so each layer draws from its 14,336
  indices minus the tested ones. The repo's null draws from all 14,336.
- **Geometry.** 32 layers by 14,336 neurons is hard-coded, so the CPU tests never import torch.

### Bridges-2 (task C)

- **Masters.** `ssh -O check` reported both masters running on dt-login04: bridges2 as pid 2139363 and b2dtn as pid
  2481672.
- **Code sync.** `sync-code --branch neuron-partition` fetched the new branch, created a tracking branch and switched
  to it cleanly. `remote_head` is `618efdde96c3df0707dea679586835374b149fc5`. The clone was previously at 54cd1eb.
- **Data sync.** `sync-data --what runs` does not cover this data, because its manifest lists six coarse run
  directories under the primary checkout. I created the directory over `ssh bridges2 mkdir -p` and rsynced
  `outputs/_analyses/neuron-partition/data/` through b2dtn: 37 files, 12.36 MB. sha256 of all 37 files is identical
  on both sides. The Bridges-2 mgnp environment loads both pool copies with 177, 177 and 891 rows.
- **Fetch.** `b2.sh fetch --dry` now prints `--include=/neuron-partition*/***`.

SU balances from `projects` on Bridges-2:

| allocation | GPU SU | other |
| --- | --- | --- |
| cis260361p | 390 of 452 left | Regular Memory 200 of 200; ocean 967 of 1,000 GB |
| cis260372p | 89 of 100 left | ocean 99 of 100 GB |
| cis260382p, not named in the brief | 100 of 100 left | ocean 99 of 100 GB |

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py copy-pools
```

Observed: "far_v2_user_inversion: 17 files; provenance matched 16, mismatched 0, missing 0, not listed
['assembly_provenance.json']", and the same line for far_v2_user_neutral.

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py sample
```

Observed: per_condition D, H, F, I and N all 300. D eligible 644, I eligible 566, overlap 164. Halves A 200, B 200,
I_A 174, I_B 180. Run twice, and both runs gave the same sha256 for both files.

The first run of `sample` drew 0 I rows. Its act-naming filter read the I row's `pressure` field, which holds the
neutral sentence. I fixed the filter to use the D row's clause and reran.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_neuron_partition_data.py -p no:cacheprovider -q
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_neuron_partition_data.py -p no:cacheprovider -q
```

Observed: "20 passed" on mgnp and "20 passed, 1 warning" on base.

```
<both interpreters> -m pytest tests/test_d4_jobs.py tests/test_instructed_route_b1_jobs.py tests/test_neuron_partition_data.py -p no:cacheprovider -q
```

Observed before the test_d4_jobs edit: one failure, `test_b2_fetch_brings_back_the_deception_divergence_root_and_keeps_the_old_globs`,
at line 180. Observed after: "54 passed" on mgnp and "54 passed, 3 warnings" on base.

Full suite on both interpreters: FULL_SUITE_PLACEHOLDER

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && git log --oneline -1 && git status --short | head'
```

Observed: "618efdd neuron-partition: freeze spec.md from item 10 of START; first RESUME". The status lines are only
`??` lines for untracked outputs from earlier sessions, such as `outputs/_build_inversion_v2/far_v2/`. There are no
tracked modifications.

```
find . -type f | sort | xargs sha256sum   # on Delta, and the same over ssh bridges2; then diff
```

Observed: "IDENTICAL", 37 files.

## Execution evidence

Not applicable: no runs.

The sync results are in task C above. No GPU job and no sbatch were submitted.

## What is NOT done

- **SER.** I built only the FAR sample. SER is the secondary task; its sample is the same call with other paths, but
  the CLI covers FAR only.
- **Null sets.** No null set exists yet, because no tested neuron set exists. The `nulls` subcommand is tested on
  synthetic sets only.
- **dataset_files.** `far_test_sample_seed2.json` holds a `dataset_files` map of 75 paths. Recording it in a
  `run_manifest.json` is the scorer's and ablation runner's job.

## Open questions

1. **Lifting the A1 selection ids.** Should the ladder's 100 selection ids stay excluded? Default: keep them
   excluded. The pools stay comfortably above 300 either way.
2. **Paired D and I draws.** Should the I sample be drawn from the D sample's ids, for a paired D-against-I
   comparison? Default: keep the independent draw, as the brief says. 164 ids overlap already.
3. **The test_d4_jobs.py edit.** Should it stand? Default: keep the prefix check. The test's name says "keeps the old
   globs", and the check still enforces exactly that.
4. **Sample size.** Is 300 rows per condition enough? Default: 300, the START floor. Rerunning with `--n` gives a
   larger sample, up to 644 for D and 566 for I.
