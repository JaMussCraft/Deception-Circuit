# Hand-back 09: B2 ticket T3, id and group files

Agent: implementer, Claude Opus 5.5. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B2-plan.md` section 6, T3. Status: resolved.

## What changed

All files are committed by the orchestrator from the worktree. Nothing is staged for the apply tool.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/instructed_route_b2_inputs.py` (new) writes every file below. It runs on CPU and loads no model. It writes a file only when it is absent. An identical existing file is left alone, and a different one stops the run. An existing `sdr_wish_ids.txt` from T2 is accepted when it names the same 618 ids once each, in any order. Before drawing seed 2, the script checks that redrawing seed 0, and seed 1 with the seed-0 ids excluded, reproduces both copied lists exactly. Otherwise it stops.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_instructed_route_b2_inputs.py` (new) has 15 tests.
- These files are written under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/groups/`:
  - `sdr_wish_ids.txt` holds the 618 ids of `sdr_v2_inversion_reported`, in dataset order.
  - `{far,sdr,ser}_seed0_ids.txt` are copied from the primary checkout's untracked `outputs/_analyses/mechanism-analysis-p1/s1/U__leaf/<task>_v2/sample.json`.
  - `{far,sdr,ser}_seed1_ids.txt` are copied from `docs/research/mechanism-analysis/phase1/groups/<task>_heldout_D_sample.json`.
  - `{far,sdr,ser}_seed2_ids.txt` come from `sampling.draw_sample` on the `<task>_v2` test split with n = 100 and seed 2, excluding the seed-0 and seed-1 ids. This is the same call `analyze_components` makes with `--seed 2 --exclude-ids`.
  - `p2_groups.json` holds `quartet`, `L17H24`, `kvg_{0,1,2,3,4,5,7}` and `null_d00` to `null_d19`. Null i is `sorted(random.Random(20261101 + i).sample(heads 0..31 minus 24..27, 4))`. The script refuses a null that repeats another null or coincides with a key-value (KV) group, so the declared seeds are always the ones used.
  - `p3_groups.json` holds `mlp.11`, `mlp.13`, `mlp.16`, `mlp.30`, `mlp.31` and `mlp.0`. Each has one member, `["mlp", L, 0]`.
  - `b2_inputs_meta.json` records the recipe, the source paths with their sha256, the null seeds, and the seed-2 strata and marginals.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_instructed_route_b2_inputs.py
```

Observed: red before the script existed, with a collection error saying the script file was not found. After the script was written: `15 passed in 23.08s`.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_instructed_route_b2_inputs.py
```

Observed: `15 passed, 1 warning in 16.22s`.

The tests cover the following:
- The 618 wish ids equal the dataset's `instance_id` column and are unique.
- The quartet is exactly `[["head",17,h] for h in 24..27]`.
- The KV groups are seven disjoint runs of four. Their union is every layer-17 head outside 24 to 27, and adding the quartet gives all 32 heads.
- The 20 nulls are distinct sorted layer-17 quartets outside 24 to 27, and none equals a KV group. They are identical across two calls and match their declared seeds.
- Both group files load through `knockout.load_groups` and pass `check_groups`.
- Redrawing seed 1 reproduces the tracked held-out ids for far, sdr and ser. Redrawing seed 0 reproduces the local selection sample.
- Seed 2 has 100 unique ids, is disjoint from seeds 0 and 1, and is deterministic.
- The writer is idempotent. It keeps an equal wish file written in another order, refuses a different one, and refuses a seed-1 mismatch.
- The tracked files equal a fresh build.

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/instructed_route_b2_inputs.py
```

Observed: on the first run, 13 files were reported as `written`. On the rerun, 12 were `unchanged` and `sdr_wish_ids.txt` was `verified`.

As a sanity check, 57 of the 618 wish ids lie in `sdr_seed1_ids.txt`, which matches plan section 0. The other overlaps were 59 with seed 0 and 67 with seed 2.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No `--dry-run` of `analyze_components` was run against these files. The T2 and T8 login checks cover that.
- I did not run the repository-wide suite. No shared module was changed: only the two new files and the generated group files.

## Open questions

- **The seed-2 overlap with the wish ids.** 67 of SDR's seed-2 ids are also wish ids, while P3 reads only the SER replication verdict. My default is to leave this as is, because P3's SDR cells are descriptive under R3.
- **Absolute source paths in the meta file.** `b2_inputs_meta.json` records absolute source paths, and the seed-0 source points into the primary checkout's untracked `outputs/`. My default is to keep them, because the sha256 next to each path identifies the content.
