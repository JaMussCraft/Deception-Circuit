# 10 — Hand-back: migration B, the scripted `.scratch` archive

Implementer: Opus, ticket 10, 2026-10-31. No git command was run. Nothing was moved, renamed or linked in `A/.scratch` or in `DC/outputs/_studies`. The script read the `.scratch` directories only to hash them, to copy their Markdown and to run the secret scan, and no file content was printed. Every write went to W, S or T.

## What changed

### Committed by the orchestrator from W

All paths are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/`.

- `autoresearch-workflow/tools/migrate_scratch.py`: the migration script, stdlib only. `plan` hashes, copies the curated Markdown, writes ops, records and the registry update, and never moves anything. `plan --report-only` hashes and reports and writes nothing. `verify` re-hashes every recorded path before or after the apply.
- `autoresearch-workflow/tools/test_migrate_scratch.py`: 17 tests on temporary fixture trees. The simulated apply runs the real `apply_staged.py`.
- `directions.json`: the `archive` field of five rows gained one entry each (diff under How verified). Nothing else changed.
- `SESSIONS.md`: re-rendered by `research-session render`. Only its render time and last-worklog time changed, and both come from the orchestrator's state file. `DIRECTIONS.md` was unchanged.
- Markdown copies, each folder with a `provenance.json`:
  - `component-analysis/scratch-copy/component-analysis/` (41 files),
  - `format-control/scratch-copy/format-control/` (29 files),
  - `mechanism-analysis/scratch-copy/mechanism-analysis/` (49 files),
  - `mechanism-datasets/scratch-copy/mechanism-datasets/` (92 files).
- `autoresearch-workflow/reports/10-scratch-paths-before.json`: 33 `.scratch` strings in DC code with their resolution and existence.
- `autoresearch-workflow/reports/10-tests-before.md`: pass, fail, error and skip names of the seven test modules, from both checkouts and both interpreters.
- `autoresearch-workflow/reports/10-handback.md` (this file) and `autoresearch-workflow/issues/10-migration-b-scratch-archive.md` (status, checkboxes, comments).

The directories `component-analysis/` and `format-control/` under `docs/research/` did not exist before. They now hold only `scratch-copy/`, while `INDEX.md` still says they do not exist yet. I did not edit `INDEX.md`.

### Staged in S, ops file `S/ops/10-migration-b.json` (wave B)

- `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/10-migration-b.json`: 20 ops, all wave B. They are 5 `mkdir`, 5 `move`, 5 `symlink` and 5 `write` ops.
- `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/records/10-migration-b.json`: every file's path, size and sha256, every directory, the source inode and the copies, for `verify`. It sits outside `ops/`, so the apply tool does not load it.
- `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/u/swong2/.claude/research-session/backups/scratch-autoresearch-workflow-20261031/`: the five byte-identical files that the `write` ops copy to the backup root.

For each of `component-analysis`, `format-control`, `mechanism-analysis` and `mechanism-datasets`, the ops are:

1. `mkdir DC/outputs/_studies/<slug>`;
2. `move A/.scratch/<slug>` to `DC/outputs/_studies/<slug>/scratch`, a rename on the same filesystem;
3. `symlink A/.scratch/<slug>` to that absolute path, as in the selective-deception precedent.

For `autoresearch-workflow` (R34), the ops are:

1. five `write` ops, one per file, to `/u/swong2/.claude/research-session/backups/scratch-autoresearch-workflow-20261031/`;
2. `mkdir DC/outputs/_studies/autoresearch-workflow`;
3. `move A/.scratch/autoresearch-workflow` to `DC/outputs/_studies/autoresearch-workflow/scratch-stale-20261031`;
4. `symlink A/.scratch/autoresearch-workflow` to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow`.

All five files have a sha256 twin in F, so nothing was kept back. Why this case uses copies plus a stash rather than one move is the first open question.

### Scratch files in T

Helper scripts in `/u/swong2/.claude/jobs/b2cb53cd/tmp/10/`:

- `ar_match.py` matched the autoresearch-workflow files against F by hash.
- `scratch_paths.py` wrote `10-scratch-paths-before.json`.
- `junit_names.py` and `tests_before_md.py` wrote `10-tests-before.md` from the four JUnit XML files `before-{mgnp,base}-{DC,W}.xml`.
- `check_r28.py` checks the op file against R28.
- `check_copies.py` re-scans the copies against their provenance.
- `glue_count.py` counts copies in the glue-lint scope.
- `directions.before.json` is the registry before the plan.

## How verified

### Script tests, both interpreters

```
/u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider F/tools/test_migrate_scratch.py F/tools/test_apply_staged.py
50 passed in 1.16s
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider F/tools/test_migrate_scratch.py F/tools/test_apply_staged.py
50 passed in 1.81s
```

Of the 50 tests, 17 are this ticket's and 33 are the apply tool's, which still pass. The ticket's tests cover the following:

- **Archive move and symlink.** A fixture with nested Markdown, JSON, a binary file, an inner symlink and an empty directory is planned, applied by `apply_staged.py --wave B`, and checked. The link points at the archive, the archive keeps the source inode, so it is a rename, and every file's sha256 is unchanged.
- **Verify.** It passes before the apply ("not applied yet") and after it. It fails after a one-byte append to an archived file, and it fails when a Markdown copy changes.
- **R28.** An `sdr-*` directory is refused without the flag, and no op file is written. A mixed include refuses only the protected directory. With `--confirmed-live-session-finished`, the ops are wave D in `10-migration-d.json`, `--wave B` selects none of them, and `--wave D` applies them. An already-archived `selective-deception` symlink gets a copy only, with no ops.
- **12-hour skip.** One file touched an hour ago skips the whole directory. `autoresearch-workflow` is exempt.
- **Destination exists.** An existing `outputs/_studies/<slug>/scratch` is refused.
- **Markdown selection.** Every `*.md` is copied at depths 0 to 3, including `reports/`, `reviews/` and `handbacks/`, and nothing else is. A 200 KB plus 1 byte file is excluded by the file cap. The ninth 190 KB file is excluded by the 1.5 MB directory cap. Both exclusions are listed in `provenance.json` with path and size, and archive-only files are counted.
- **Planted fake token.** A `ghp_` token blocks only that copy. It is reported by path, pattern name and line number, and the token text appears in no output, provenance or record.
- **Missing scanner.** The plan stops with exit 2 and writes nothing.
- **autoresearch-workflow.** All files matched gives write, mkdir, move and symlink ops, a byte-identical backup and stash, and a passing verify. A file without a twin is listed as kept, and the directory ops are withheld.
- **Registry.** The archive paths are added once, and a second plan does not duplicate them.

The caps are 200 KB = 204,800 bytes per file and 1.5 MB = 1,572,864 bytes per directory.

### The real plan, report-only first and then for real

```
/sw/external/python/anaconda3/bin/python3.9 -B F/tools/migrate_scratch.py plan --include component-analysis,format-control,mechanism-analysis,mechanism-datasets,autoresearch-workflow
registry: component-analysis archive += outputs/_studies/component-analysis/scratch
registry: format-control archive += outputs/_studies/format-control/scratch
registry: mechanism-analysis archive += outputs/_studies/mechanism-analysis/scratch
registry: mechanism-datasets archive += outputs/_studies/mechanism-datasets/scratch
registry: autoresearch-workflow archive += outputs/_studies/autoresearch-workflow/scratch-stale-20261031
migrate_scratch plan (ops, copies, records)
component-analysis           planned  wave B
    kind archive, direction component-analysis, 45 files in 6 directories, 672.2 KB, newest entry 411.2 h old
    markdown 41, copied 41 (672.0 KB), cap exclusions 0, secret-scan blocks 0, archive-only 4 files (232 B)
    ops 3
format-control               planned  wave B
    kind archive, direction format-control, 97 files in 19 directories, 1.1 MB, newest entry 289.0 h old
    markdown 29, copied 29 (439.4 KB), cap exclusions 0, secret-scan blocks 0, archive-only 68 files (642.7 KB)
    ops 3
mechanism-analysis           planned  wave B
    kind archive, direction mechanism-analysis, 167 files in 6 directories, 4.0 MB, newest entry 75.7 h old
    markdown 49, copied 49 (672.1 KB), cap exclusions 0, secret-scan blocks 0, archive-only 118 files (3.4 MB)
    ops 3
mechanism-datasets           planned  wave B
    kind archive, direction mechanism-datasets, 648 files in 52 directories, 52.6 MB, newest entry 149.6 h old
    markdown 92, copied 92 (1.2 MB), cap exclusions 0, secret-scan blocks 0, archive-only 556 files (51.4 MB)
    ops 3
autoresearch-workflow        planned  wave B
    kind autoresearch, direction autoresearch-workflow, 5 files in 4 directories, 96.6 KB, newest entry 3.1 h old
    5 file(s) with a sha256 twin in F, 0 without
    ops 8
total: 5 directories inventoried, 962 files, 58.4 MB; markdown 216, copied 211 (2.9 MB), cap exclusions 0, secret-scan blocks 0, ops 20
```

The `--report-only` run just before gave the same numbers and wrote nothing. The five Markdown files of `autoresearch-workflow` are not copied, because their canonical copies are in F. No directory was skipped and none was refused.

### Deferred directories: refusal, then a report-only preview

Without the flag, all 13 deferred directories are refused with the R28 reason, and the run exits 1. With the flag and `--report-only`, the script only hashed and wrote nothing:

```
sdr-assay-diagnosis          planned  wave D   8 files, 422.3 KB, newest 240.1 h; copied 4
sdr-behavior-identification  planned  wave D   56 files, 48.1 MB, newest 142.5 h; copied 20
sdr-clause-choice            planned  wave D   396 files, 39.3 MB, newest 117.4 h; copied 32
sdr-cue-circuits             planned  wave D   2653 files, 41.6 GB, newest 151.1 h; copied 28
sdr-cue-followup             planned  wave D   1272 files, 73.8 MB, newest 143.1 h; copied 32
sdr-cue-probe                planned  wave D   100 files, 17.7 MB, newest 238.6 h; copied 13
sdr-native-controls          planned  wave D   107 files, 1.0 MB, newest 241.2 h; copied 20
sdr-routing-pilot            planned  wave D   27 files, 345.4 KB, newest 258.7 h; copied 10
sdr-routing-validation       planned  wave D   39 files, 288.9 KB, newest 245.0 h; copied 20
sdr-shared-composition       skipped  wave D   reason: an entry was modified 6.4 hours ago (12-hour rule, R3)
sdr-session-wrapup           skipped  wave D   reason: an entry was modified 6.4 hours ago (12-hour rule, R3)
selective-deception          skipped  wave D   reason: an entry was modified 6.7 hours ago (12-hour rule, R3)
eval5-grader-fixes           planned  wave D   3 files, 4.9 KB, newest 1085.2 h; copied 3
total: 13 directories inventoried, 11220 files, 62.0 GB; markdown 518, copied 182 (1.9 MB), cap exclusions 0, secret-scan blocks 0, ops 30
```

The lines above are condensed from the script's output; the counts are unchanged. Three of the deferred directories were written about 6.5 hours ago, around 08:30 today, so the 12-hour guard alone would hold them back today. `selective-deception` holds 254 Markdown files, so its copy will meet the 1.5 MB directory cap when it runs.

### No op touches R28

```
/sw/external/python/anaconda3/bin/python3.9 -B T/10/check_r28.py
ops checked: 20 (mkdir 5, move 5, symlink 5, write 5); all wave B: True; R28 violations: 0
```

The script applies the apply tool's own `protected_reason` to every op. It also runs a plain substring test for `/.scratch/sdr-`, `/.scratch/selective-deception`, `/.scratch/eval5-grader-fixes`, the two memory notes and `MEMORY.md`.

### Verify before the apply

```
/sw/external/python/anaconda3/bin/python3.9 -B F/tools/migrate_scratch.py verify --wave B
ok      component-analysis: not applied yet; source still matches its 45 recorded entries
ok      format-control: not applied yet; source still matches its 97 recorded entries
ok      mechanism-analysis: not applied yet; source still matches its 167 recorded entries
ok      mechanism-datasets: not applied yet; source still matches its 648 recorded entries
ok      autoresearch-workflow: not applied yet; source still matches its 5 recorded entries
verify /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/records/10-migration-b.json: 5 entries, 0 problem(s)
```

### Copies: secret scan and provenance

```
/sw/external/python/anaconda3/bin/python3.9 -B T/10/check_copies.py
component-analysis/scratch-copy/component-analysis   copies  41 ( 688138 bytes) provenance  41, missing 0, secret hits 0 (+0 in provenance), excluded by caps 0, blocked 0, archive-only 4
format-control/scratch-copy/format-control           copies  29 ( 449990 bytes) provenance  29, missing 0, secret hits 0 (+0 in provenance), excluded by caps 0, blocked 0, archive-only 68
mechanism-analysis/scratch-copy/mechanism-analysis   copies  49 ( 688182 bytes) provenance  49, missing 0, secret hits 0 (+0 in provenance), excluded by caps 0, blocked 0, archive-only 118
mechanism-datasets/scratch-copy/mechanism-datasets   copies  92 (1260476 bytes) provenance  92, missing 0, secret hits 0 (+0 in provenance), excluded by caps 0, blocked 0, archive-only 556
total copies 211, 3086786 bytes, problems 0
```

This check is independent of the plan. It re-hashes every file on disk against `provenance.json` and re-runs the RS `scan_secrets` on each copy and on each provenance file. No copy was blocked, so the list of copies that failed the scan is empty. Three copies fall in the RS glue-lint scope because of their names: two `RESUME.md` and one `README.md`. All three pass the glue lint (`T/10/glue_count.py`: "copies in glue scope 3, failing 0").

### directions.json

```
diff T/10/directions.before.json W/docs/research/directions.json
80c80,82  mechanism-analysis     "archive": [] -> ["outputs/_studies/mechanism-analysis/scratch"]
109c111   mechanism-datasets     "archive": [] -> ["outputs/_studies/mechanism-datasets/scratch"]
136c140   component-analysis     "archive": [] -> ["outputs/_studies/component-analysis/scratch"]
163c169   format-control         "archive": [] -> ["outputs/_studies/format-control/scratch"]
220c228   autoresearch-workflow  "archive": [] -> ["outputs/_studies/autoresearch-workflow/scratch-stale-20261031"]
research-session validate W/docs/research/directions.json
.../directions.json: valid
```

The diff lines are condensed; the raw diff shows only these five `archive` changes. `legacy_scratch` already listed each directory from ticket 05, so it needed no change. The `updated` fields were already 2026-10-31. The file is written in the RS JSON style, with indent 2, sorted keys, ASCII and a trailing newline, so all other bytes are unchanged.

### `.scratch` strings in DC code resolve today

```
/sw/external/python/anaconda3/bin/python3.9 -B T/10/scratch_paths.py <the 9 extra files>
strings 33, exist 33, fixture-only 1, in wave B directories 10
```

The 14 files named in the ticket hold 23 strings. A grep over every `*.py` in W found 9 more files with 10 more strings:

- `evaluate_native_sparse.py`, `dataset/check_v2_scaffold.py` and `dataset/purity_judge_v2.py`;
- five `outputs/_launch_mechanism_analysis/p*_results.py` files;
- `outputs/_launch_mechanism_v2/evals/stage1_results.py`.

The list is in `10-scratch-paths-before.json`, with each string grouped as "listed" or "additional". Relative strings were resolved against the Alignment root, because every caller builds them from it. The one fixture string, in `test_frozen_head_masks.py:71`, is built on `tmp_path`. The 10 strings in wave B directories all point into `mechanism-analysis/reports` or `mechanism-datasets/reports`, which keep resolving through the symlinks.

### The seven test modules before migration

The full name lists are in `10-tests-before.md`. Counts:

| Run | Passed | Failed | Errors | Skipped |
|-----|--------|--------|--------|---------|
| DC main, mgnp | 91 | 1 | 58 | 0 |
| DC main, base | 89 | 1 | 58 | 2 |
| W, mgnp | 53 | 5 | 90 | 2 |
| W, base | 51 | 5 | 90 | 4 |

- **DC main.** Every error and the one failure come from a missing `DC/.superpowers/sdd/plan-*` file. None of them involves `.scratch`.
- **Worktree.** It adds failures because the tests resolve `.scratch` from `parents[1].parent`, which is `DC/.claude/worktrees` there.
- **What to compare.** The comparison after wave B is the DC main rows.

### apply_staged dry run

```
/sw/external/python/anaconda3/bin/python3.9 -B F/tools/apply_staged.py --staging S --only 10 --wave B --dry-run
dry run, wave B: 20 op(s) selected from 20
[10#1] mkdir .../outputs/_studies/component-analysis WOULD APPLY: mkdir
[10#2] move .../outputs/_studies/component-analysis/scratch ERROR: move destination parent missing
[10#3] symlink /projects/beto/swong2/Alignment/.scratch/component-analysis CONFLICT: link path exists
[10#4]-[10#12] the same three lines for format-control, mechanism-analysis and mechanism-datasets
[10#13] write .../backups/scratch-autoresearch-workflow-20261031/lane1-public-patterns.md WOULD APPLY: +89 -0 lines, new file
[10#14] write .../lane2-harness.md WOULD APPLY: +205 -0 lines, new file
[10#15] write .../lane3-repo-structure.md WOULD APPLY: +172 -0 lines, new file
[10#16] write .../lane4-oversight.md WOULD APPLY: +265 -0 lines, new file
[10#17] write .../proposal-full.md WOULD APPLY: +168 -0 lines, new file
[10#18] mkdir .../outputs/_studies/autoresearch-workflow WOULD APPLY: mkdir
[10#19] move .../outputs/_studies/autoresearch-workflow/scratch-stale-20261031 ERROR: move destination parent missing
[10#20] symlink /projects/beto/swong2/Alignment/.scratch/autoresearch-workflow CONFLICT: link path exists
(exit 1)
```

Paths are shortened above; the raw output has them in full. The ERROR and CONFLICT lines are expected in a dry run. The dry run does not carry state from one op to the next, so a move cannot see the parent its own `mkdir` would create. Likewise the symlink still sees the directory its `move` would have renamed. The fixture test applies the same three-op sequence for real, and every op succeeds. The dry run does confirm that the R28 refusal does not fire and that every `write` is a new file.

## Execution evidence

Not applicable: no runs. No Slurm job, GPU job or paid API call was made, and nothing was moved.

## What is NOT done

- The real moves, links and backup writes. They are the orchestrator's wave B step, after the DC merge.
- Wave D. It needs the user's confirmation that the Codex session is finished. Three of the 13 directories would be skipped by the 12-hour guard today in any case.
- `INDEX.md` still says `docs/research/component-analysis/` and `format-control/` do not exist. Both now exist with only `scratch-copy/`.

### Commands for the orchestrator after wave B

Immediately before applying, run the `verify --wave B` command below once. It must report "not applied yet" and 0 problems for all five entries. It catches any file written since the plan, for example into the empty subdirectories of `.scratch/autoresearch-workflow`. If it reports a problem, rerun the `plan` command above rather than applying the stale ops.

Apply after the DC merge, because the autoresearch-workflow link needs `DC/docs/research/autoresearch-workflow` to exist:

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --only 10 --wave B
```

Verify. Expect "applied" for all five entries and 0 problems:

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py verify --wave B
```

Check that every recorded `.scratch` string still resolves:

```
/sw/external/python/anaconda3/bin/python3.9 -B -c "import json,os;d=json.load(open('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/reports/10-scratch-paths-before.json'));m=[e['resolved'] for e in d['entries'] if not os.path.exists(e['resolved'])];print(len(d['entries']),'strings,',len(m),'missing',m)"
```

Rerun the seven modules from DC main in each env, and compare by name with the DC main lists in `10-tests-before.md`:

```
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider -rA /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v6_manifest.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_probe.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_mechanism_analysis_figures.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v7.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_frozen_head_masks.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_positions.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_routing_validation.py
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider -rA /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v6_manifest.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_probe.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_mechanism_analysis_figures.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v7.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_frozen_head_masks.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_positions.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_routing_validation.py
```

The before runs were made against the pre-merge DC main code. If the merge changed any of these modules or the code they import, a name may move for that reason rather than the migration. Rollback is `apply_staged.py --rollback <journal>`, which reverses the renames and removes the links.

### The deferred command (wave D), to run only after the user confirms the Codex session is finished

Run it from DC main after the merge. Copies then go to `DC/docs/research/<direction>/scratch-copy/`, and the registry edit goes to DC main's `directions.json`. `--staging` names a durable root, because the job's tmp directory may be gone by then.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py plan --confirmed-live-session-finished --staging /u/swong2/.claude/research-session/staging-10d --include sdr-assay-diagnosis,sdr-behavior-identification,sdr-clause-choice,sdr-cue-circuits,sdr-cue-followup,sdr-cue-probe,sdr-native-controls,sdr-routing-pilot,sdr-routing-validation,sdr-shared-composition,sdr-session-wrapup,selective-deception,eval5-grader-fixes
```

Then apply and verify with the same staging root:

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-10d --only 10 --wave D
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py verify --wave D --staging /u/swong2/.claude/research-session/staging-10d
```

Wave D writes its ops to `10-migration-d.json` and never touches the wave B file. Any directory touched in the 12 hours before the run is skipped and reported, and running the same command again later picks it up. `selective-deception` is already archived, so it gets only the Markdown copy. The copies and the `directions.json` change are then committed on DC main.

## Open questions

1. **R34 deviation: backup root by copy plus a stash.** R34 says the directory "moves to the backup root". The backup root is on `/u`, and `.scratch` is on `/projects`, two different filesystems (`df -P`). The apply tool's `move` is `os.rename`, which cannot cross filesystems, and the tool has no delete op. So the five files are copied to the backup root by `write` ops, byte for byte, which is checked by `verify`. The directory is then renamed on the same filesystem to `DC/outputs/_studies/autoresearch-workflow/scratch-stale-20261031`, which is ignored, so that the path is free for the symlink. Please confirm this before applying wave B. If you prefer, the stash can be removed by hand after `verify` passes. I recorded the stash path in the row's `archive` field so it can be found. If you prefer to leave `archive` empty for this row, that one entry should be dropped.
2. **Empty subdirectories.** `.scratch/autoresearch-workflow` holds three empty subdirectories, `issues/`, `reports/` and `handbacks/`, created at 11:59 today. If anything writes a file there before wave B, `verify` reports an unexpected entry, and that file has no twin in F. Is anything still writing there?
3. **Apply-tool dry run.** The dry run cannot simulate a chain of dependent ops, so every migration dry run exits 1. Should ticket 01's tool carry the planned state forward in dry-run mode?
4. **Ticket's file list.** The list of files that read `.scratch` missed 9 files with 10 strings, listed above. All of them resolve today, and the 10 in wave B directories keep resolving through the symlinks.
5. **Public copies.** The 211 copies are now in `docs/research/**`, which is pushed to a public repository. They passed the secret scan, but they include Slurm account names, job ids and absolute paths, as ticket 05's ledgers do (ticket 05's open question 2).
