# Merge and apply checklist: autoresearch-workflow

Written by ticket 12 on 2026-10-31 for the orchestrator. It records what is already done and lists only the remaining
steps, in order. Every apply command names the durable staging root
`/u/swong2/.claude/research-session/staging-20261031`, called DS below. Before the merge the tools live in the worktree
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow`, called W; after the merge
the same files are in the main checkout `/projects/beto/swong2/Alignment/Deception-Circuit`, called DC.

## Done already

- Wave A is applied for tickets 01, 02, 03 (with the 03b ledger fixes), 06 (code), 07, 08, 09 and 11. Ticket 05 had no
  ops. Each run has a journal under `/u/swong2/.claude/research-session/backups/`.
- Wave H is applied (4:04 pm EDT): the hooks in the Alignment and worktree project settings and in
  `~/.codex/hooks.json`, and the Codex note block in the Alignment `CLAUDE.md`. The hook smoke test passed after the
  install, and the user trusted the Codex hooks with `/hooks` at 4:18 pm EDT.
- The worklog import ran, so RS owns `worklog.json` and `WORKLOG.md`. The bridge sync ran after wave H. `AGENTS.md`
  is a pointer to `CLAUDE.md`, so nothing needed regenerating.
- `W/.claude/settings.json` is force-added, because the repository's local `info/exclude` ignores `.claude/`. The user
  decides whether it stays tracked.

## 1. Make the staging root durable

Copy the job's staging root once ticket 12's hand-back is in. The job tmp directory goes away with the job.

```
cp -a /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging /u/swong2/.claude/research-session/staging-20261031
diff -rq /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging /u/swong2/.claude/research-session/staging-20261031
```

Expect no output from `diff`. The default `--staging` of `migrate_scratch.py` still names the job tmp path, so every
command below passes `--staging` explicitly.

## 2. Apply ticket 12's wave A

Dry-run, then apply. Expect 18 WOULD APPLY, then 18 APPLY. Re-read the memory files first if Codex has been busy:
the memory and documentation ops are text ops, and the three whole-file writes check `expect_sha256`.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --only 12 --wave A --dry-run
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --only 12 --wave A
```

Then, in this order:

1. The RS tests from the installed path, in both environments. Expect 273 passed in each.

```
/u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider /projects/beto/swong2/Alignment/.agents/tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider /projects/beto/swong2/Alignment/.agents/tests
```

2. The hook smoke test, timed. Expect every check to pass.

```
/usr/bin/time -p /sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/hook_smoke.py --live
```

3. The bridge sync, because `ticket-implementer.md` changed and Codex reads a generated adapter of it. Then check that
   nothing drifts.

```
python3 /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py --apply
python3 /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py --check
```

4. The post-apply re-run of waves A and H. Expect every op to report SKIP. Writes that later text ops changed report
   "applied in run ..." instead of "already applied".

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --wave A --dry-run
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --wave H --dry-run
```

## 3. Commit

- **Deception-Circuit branch.** Commit ticket 12's files from W by explicit list (the "Ticket 12" block below). The
  pytest cache copy is a deletion: `docs/research/component-analysis/scratch-copy/component-analysis/.pytest_cache/README.md`.
- **Alignment.** After step 2, commit the Alignment files of wave A, ticket 12 (block below), by explicit list.

## 4. Merge Deception-Circuit, after the user's approval

Ask the user before merging `autoresearch-workflow` into DC main. Keep the worktree until step 5 has passed: the wave
B records name the Markdown copies by their worktree paths, so `verify` reads them there.

## 5. Wave B, after the merge

The sequence is ticket 10's, with the durable staging root and the merged tools path.

1. Immediately before applying, verify once. Expect "not applied yet" and 0 problems for all five entries. On any
   problem, rerun ticket 10's `plan` rather than applying stale ops.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py verify --wave B --staging /u/swong2/.claude/research-session/staging-20261031
```

2. Apply. The autoresearch-workflow link needs `DC/docs/research/autoresearch-workflow`, which exists only after the
   merge.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --only 10 --wave B
```

3. Verify. Expect "applied" for all five entries and 0 problems.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py verify --wave B --staging /u/swong2/.claude/research-session/staging-20261031
```

4. Check that every recorded `.scratch` string still resolves. Expect 33 strings and 0 missing.

```
/sw/external/python/anaconda3/bin/python3.9 -B -c "import json,os;d=json.load(open('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/reports/10-scratch-paths-before.json'));m=[e['resolved'] for e in d['entries'] if not os.path.exists(e['resolved'])];print(len(d['entries']),'strings,',len(m),'missing',m)"
```

5. Rerun the seven test modules from DC main in each environment, and compare by name with the DC main rows of
   `reports/10-tests-before.md`. If the merge changed one of these modules or its imports, a name may move for that
   reason rather than the migration.

```
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider -rA /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v6_manifest.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_probe.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_mechanism_analysis_figures.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v7.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_frozen_head_masks.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_positions.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_routing_validation.py
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider -rA /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v6_manifest.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_probe.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_mechanism_analysis_figures.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_selective_v7.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_frozen_head_masks.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_cue_positions.py /projects/beto/swong2/Alignment/Deception-Circuit/tests/test_sdr_routing_validation.py
```

Rollback is `apply_staged.py --rollback <journal>`, which reverses the renames and removes the links. A re-run of
wave B after the apply reports all 20 ops as SKIP; a move whose source path is now its link counts as moved.

## 6. Remove worktrees, after ExitWorktree (orchestrator only)

The `mechanism-datasets` worktree and branch are fully merged. Check that the branch is 0 commits ahead of main, then:

```
git -C /projects/beto/swong2/Alignment/Deception-Circuit worktree remove .claude/worktrees/mechanism-datasets
git -C /projects/beto/swong2/Alignment/Deception-Circuit branch -d mechanism-datasets
git -C /projects/beto/swong2/Alignment/Deception-Circuit push origin --delete mechanism-datasets
```

Remove the `autoresearch-workflow` worktree only after step 5 has passed.

## 7. Wave C, after the user's go for Codex

Codex must restart afterwards. Op `01#21` is stale: the live bridge gained code that keeps Codex hook trust after
ticket 01 staged its whole-file copy, so the op reports CONFLICT and must never be forced. Op `12c#1` makes the same
one-sentence change as a text op; the bridge tests pass on a copy with 07's ops and `12c#1` applied (8 of 8, both
interpreters). Expect 01#21 CONFLICT and every other op APPLY.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --wave C --allow codex-config --dry-run
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --wave C --allow codex-config
/u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider /projects/beto/swong2/Alignment/.agents/tests/test_claude_codex_sync.py
```

Then the user restarts Codex. The hook trust stays, because the hook commands do not change; if `/hooks` lists any
hook as untrusted, the user trusts it again.

## 8. Wave D, after the user confirms the live Codex session is finished (R28)

1. Re-stage ticket 12's wave D ops, because their hashes and line texts go stale while Codex works. The script
   re-reads the two notes and `MEMORY.md`, and it refuses if a copy destination already holds other bytes.

```
/sw/external/python/anaconda3/bin/python3.9 -B /u/swong2/.claude/research-session/staging-20261031/scripts/restage_12d.py --staging /u/swong2/.claude/research-session/staging-20261031
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --only 12d --wave D --dry-run
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --only 12d --wave D
```

Expect 32 ops. They copy the two notes verbatim to `DC/outputs/_studies/<slug>/memory-log-20261031.md`, rewrite the
notes as pointers, rewrite `MEMORY.md` lines 27 and 29 in full sentences, move the 21 duplicates from
`project_context` to `DC/outputs/_studies/project-context-dedupe-20261031/`, update the two folder READMEs, and edit
the selective-deception README sentence on DC main.

2. Ticket 10's deferred migration, verbatim, from DC main:

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py plan --confirmed-live-session-finished --staging /u/swong2/.claude/research-session/staging-10d --include sdr-assay-diagnosis,sdr-behavior-identification,sdr-clause-choice,sdr-cue-circuits,sdr-cue-followup,sdr-cue-probe,sdr-native-controls,sdr-routing-pilot,sdr-routing-validation,sdr-shared-composition,sdr-session-wrapup,selective-deception,eval5-grader-fixes
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-10d --only 10 --wave D
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py verify --wave D --staging /u/swong2/.claude/research-session/staging-10d
```

3. Commit on DC main by explicit list: the selective-deception README, and ticket 10's copies and `directions.json`.
   **The user approves** the Alignment commit that removes the 21 deduplicated `project_context` files and updates
   the two folder READMEs.

## 9. User actions

- **Codex restart** after wave C, and `/hooks` trust if Codex asks again.
- **Install session-report** (ticket 07), then re-run ticket 07's wave A so `enabledPlugins` keeps it off at user
  level. The install may need network for the marketplace.

```
/u/swong2/.local/bin/claude plugin install session-report@claude-plugins-official --scope user
/u/swong2/.conda/envs/mgnp/bin/python -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/research-session/staging-20261031 --only 07 --wave A
/sw/external/python/anaconda3/bin/python3.9 -c "import json;print(json.load(open('/u/swong2/.claude/settings.json'))['enabledPlugins'].get('session-report@claude-plugins-official'))"
```

- **Start the pilot** from `docs/research/autoresearch-workflow/pilot-checklist.md` (direction `pilot-hooks`).

## Kill switch, for emergencies

```
touch /u/swong2/.claude/research-session/DISABLED
```

Every hook then exits 0 with no output. Delete the file to turn the hooks back on.

## Post-apply checks, after each wave

- Re-run that wave with `--dry-run`. Every applied op reports SKIP. The one standing exception is `01#21` in wave C,
  which keeps reporting CONFLICT because `12c#1` replaced it.
- `python3 /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py --check` reports no drift.

## File lists

The lists below come from the hand-backs and the op files. Ticket 12 checked that every path exists and compared the
lists with the hand-backs; `reports/12-handback.md` has the output. Paths ending in `/` are directories committed
whole. The orchestrator's own files (plan, spec, state, research reports) form the first block.

### Deception-Circuit files committed from the worktree, by ticket

#### Orchestrator files (plan, spec, state, research reports)

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/spec.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/agent-brief.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/START.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/RESUME.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/WORKLOG.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/worklog.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/state.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/00-plan-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/00-plan-review.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/00-plan-fixes.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/00-orchestrator-rulings.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/proposal-full.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/lane1-public-patterns.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/lane2-harness.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/lane3-repo-structure.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/lane4-oversight.md
```

#### Ticket 01

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/test_apply_staged.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/01-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/01-lint-apply-tool-hygiene-config.md
```

#### Ticket 02

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/02-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/02-rs-core-usage-state-gate.md
```

#### Ticket 03

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/WORKLOG.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/03-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/03-rs-records-registry-worklog-findings.md
```

#### Ticket 04

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/run_manifest.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/evaluation/grader_hash.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/scripts/check_report_numbers.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/tests/test_run_manifest.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/tests/test_grader_hash.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/tests/test_check_report_numbers.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/tests/conftest.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/run_io.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/evaluation/suite.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/conftest.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/held-out.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/held_out.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/04-baseline-failures.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/04-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/04-science-guards.md
```

#### Ticket 05

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/INDEX.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/FINDINGS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/directions.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/DIRECTIONS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/SESSIONS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/selective-deception/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/mechanism-analysis/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/mechanism-datasets/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/sdr-mechanism/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/05-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/05-index-and-registry-seeding.md
```

#### Ticket 06

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/.gitignore
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/.claude/settings.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/staged/dc-claude-settings.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/staged/claude-hooks-fragment.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/staged/codex-hooks-fragment.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/staged/codex-hooks-note.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/hook_smoke.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/hook_smoke.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/test_hook_settings.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/06-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/06-hooks-both-tools.md
```

#### Ticket 07

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/07-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/07-profiles-both-tools.md
```

#### Ticket 08

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/START.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/proposal.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/WORKLOG.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/RESUME.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/audit.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/state.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/worklog.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/08-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/08-protocol-docs-and-templates.md
```

#### Ticket 09

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/mechanism-analysis/README.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/sdr-mechanism/history/sdr-clause-choice-RESUME-readable.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/09-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/09-migration-a-standardize-dedupe-claude-md.md
```

#### Ticket 10

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/migrate_scratch.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/test_migrate_scratch.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/directions.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/SESSIONS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/component-analysis/scratch-copy/component-analysis/
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/format-control/scratch-copy/format-control/
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/mechanism-analysis/scratch-copy/mechanism-analysis/
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/mechanism-datasets/scratch-copy/mechanism-datasets/
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/10-scratch-paths-before.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/10-tests-before.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/10-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/10-migration-b-scratch-archive.md
```

#### Ticket 11

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/pilot-checklist.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/pilot-hooks/START.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/pilot-hooks/README.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/pilot-hooks/RESUME.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/pilot-hooks/WORKLOG.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/pilot-hooks/state.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/pilot-hooks/worklog.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/pilot-hooks/ledger.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/directions.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/DIRECTIONS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/SESSIONS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/11-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/11-pilot-checklist-and-audit-scan.md
```

#### Ticket 12

```text
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/test_apply_staged.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/migrate_scratch.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/test_migrate_scratch.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/agent-brief.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/README.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/merge-checklist.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/FINDINGS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/INDEX.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/directions.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/DIRECTIONS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/SESSIONS.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/component-analysis/scratch-copy/component-analysis/provenance.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/component-analysis/scratch-copy/component-analysis/.pytest_cache/README.md (deleted)
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/12-handback.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/12-wrap-up.md
```

### Alignment files changed by staged ops, by wave and ticket

Memory notes under `.agents/memory/` are ignored by the Alignment repository and are not committed.

#### Wave A, ticket 01

```text
/projects/beto/swong2/Alignment/.agents/research_session/__init__.py
/projects/beto/swong2/Alignment/.agents/research_session/cli.py
/projects/beto/swong2/Alignment/.agents/research_session/lint.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_lint.py
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_lane2_plugin_table.md
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_lane4_section0.md
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_proposal_header.md
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_synthesis_prose.md
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_synthesis_table.md
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/glued_memory_line27.md
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/glued_memory_line29.md
/projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/glued_resume_excerpt.md
/projects/beto/swong2/Alignment/.claude/agents/idea-critic.md
/projects/beto/swong2/Alignment/.claude/agents/paper-reader.md
/projects/beto/swong2/Alignment/.claude/agents/paper-searcher.md
```

#### Wave A, ticket 02

```text
/projects/beto/swong2/Alignment/.agents/research_session/paths.py
/projects/beto/swong2/Alignment/.agents/research_session/usage.py
/projects/beto/swong2/Alignment/.agents/research_session/oauth_refresh.py
/projects/beto/swong2/Alignment/.agents/research_session/state.py
/projects/beto/swong2/Alignment/.agents/research_session/gate.py
/projects/beto/swong2/Alignment/.agents/research_session/cli.py
/projects/beto/swong2/Alignment/.agents/tests/_rs_testlib.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_usage.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_state.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_gate.py
/projects/beto/swong2/Alignment/.agents/tests/fixtures/gate/pretooluse_agent.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/gate/pretooluse_bash_sbatch.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/gate/pretooluse_sendmessage_orchestrator.json
```

#### Wave A, ticket 03

```text
/projects/beto/swong2/Alignment/.agents/research_session/records.py
/projects/beto/swong2/Alignment/.agents/research_session/registry.py
/projects/beto/swong2/Alignment/.agents/research_session/worklog.py
/projects/beto/swong2/Alignment/.agents/research_session/findings.py
/projects/beto/swong2/Alignment/.agents/research_session/jobs.py
/projects/beto/swong2/Alignment/.agents/research_session/ledger.py
/projects/beto/swong2/Alignment/.agents/research_session/setup.py
/projects/beto/swong2/Alignment/.agents/research_session/cli.py
/projects/beto/swong2/Alignment/.agents/tests/_rs_records.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_registry.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_worklog.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_findings.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_ledger.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_init.py
/projects/beto/swong2/Alignment/.agents/tests/fixtures/worklog/legacy_feature_WORKLOG.md
```

#### Wave A, ticket 03b

```text
/projects/beto/swong2/Alignment/.agents/research_session/registry.py
/projects/beto/swong2/Alignment/.agents/research_session/worklog.py
/projects/beto/swong2/Alignment/.agents/research_session/ledger.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_registry.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_ledger.py
```

#### Wave A, ticket 06

```text
/projects/beto/swong2/Alignment/.agents/research_session/hooks.py
/projects/beto/swong2/Alignment/.agents/research_session/cli.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_hooks.py
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_post_compact_auto.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_posttooluse_agent.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_posttooluse_edit.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_posttooluse_write.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_agent.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_bash_sbatch.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_edit_token.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_edit_worklog_json.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_sendmessage.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_write_clean.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_write_session_root.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_write_state_json.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_write_templates_state.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_pretooluse_write_worklog_glued.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_session_start_clear.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_session_start_compact.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_session_start_resume.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_session_start_startup.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_stop.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_stop_background.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_subagent_start.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_subagent_start_explore.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_subagent_stop.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_subagent_stop_explore.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_userpromptsubmit.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_userpromptsubmit_agent_message.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_userpromptsubmit_cross_session.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_userpromptsubmit_task_notification.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_userpromptsubmit_teammate.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_userpromptsubmit_teammate_inner.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_posttooluse_apply_patch.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_posttooluse_spawn_agent.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_pretooluse_apply_patch_clean.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_pretooluse_apply_patch_glued.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_pretooluse_apply_patch_state.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_pretooluse_apply_patch_token.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_pretooluse_bash_sbatch.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_pretooluse_spawn_agent.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_session_start_compact.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_session_start_startup.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_stop.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_subagent_start.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_subagent_stop.json
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/codex_userpromptsubmit.json
```

#### Wave A, ticket 07

```text
/projects/beto/swong2/Alignment/.claude/settings.local.json
/projects/beto/swong2/Alignment/docs/agents/claude-codex.md
```

#### Wave A, ticket 08

```text
/projects/beto/swong2/Alignment/docs/agents/research-session.md
/projects/beto/swong2/Alignment/docs/agents/synthesis-session.md
/projects/beto/swong2/Alignment/docs/agents/session-audit.md
/projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md
```

#### Wave A, ticket 09

```text
/projects/beto/swong2/Alignment/.claude/CLAUDE.md
/projects/beto/swong2/Alignment/docs/agents/issue-tracker.md
/projects/beto/swong2/Alignment/project_context/prompts/README.md
/projects/beto/swong2/Alignment/project_context/prompts/autoresearch.md
```

#### Wave A, ticket 11

```text
/projects/beto/swong2/Alignment/.agents/research_session/audit.py
/projects/beto/swong2/Alignment/.agents/research_session/cli.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_audit.py
```

#### Wave A, ticket 12

```text
/projects/beto/swong2/Alignment/.agents/research_session/hooks.py
/projects/beto/swong2/Alignment/.agents/tests/test_research_session_hooks.py
/projects/beto/swong2/Alignment/.agents/tests/fixtures/hooks/claude_subagent_stop_handback_pending.json
/projects/beto/swong2/Alignment/docs/agents/research-session.md
/projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md
/projects/beto/swong2/Alignment/.claude/CLAUDE.md
/projects/beto/swong2/Alignment/project_context/reports/README.md
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/README.md
```

#### Wave H, ticket 06

```text
/projects/beto/swong2/Alignment/.claude/settings.json
/projects/beto/swong2/Alignment/.claude/CLAUDE.md
```

#### Wave B, ticket 10

```text
/projects/beto/swong2/Alignment/.scratch/component-analysis (moved away)
/projects/beto/swong2/Alignment/.scratch/component-analysis
/projects/beto/swong2/Alignment/.scratch/format-control (moved away)
/projects/beto/swong2/Alignment/.scratch/format-control
/projects/beto/swong2/Alignment/.scratch/mechanism-analysis (moved away)
/projects/beto/swong2/Alignment/.scratch/mechanism-analysis
/projects/beto/swong2/Alignment/.scratch/mechanism-datasets (moved away)
/projects/beto/swong2/Alignment/.scratch/mechanism-datasets
/projects/beto/swong2/Alignment/.scratch/autoresearch-workflow (moved away)
/projects/beto/swong2/Alignment/.scratch/autoresearch-workflow
```

#### Wave C, ticket 01

```text
/projects/beto/swong2/Alignment/.agents/claude_codex_sync.py
```

#### Wave C, ticket 07

```text
/projects/beto/swong2/Alignment/.agents/claude_codex_sync.py
/projects/beto/swong2/Alignment/.agents/tests/test_claude_codex_sync.py
```

#### Wave D, ticket 12d

```text
/projects/beto/swong2/Alignment/project_context/reports/SDR circuit mechanism review.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR cue probe findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR cue-circuit transplant findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR mechanism investigation status.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR named-consequence probe findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR native controls findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR native evidence audit.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR routing pilot findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR routing validation findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR shared-component composition findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/SDR shared-head position findings.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/astra_review.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/necessity_prior_art.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/next_steps.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/project_evidence.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/shared_components.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/stage1_diagnostic.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/v3_extension.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/v5_transfer.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/v6_components.md (moved away)
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/v7_positions.md (moved away)
/projects/beto/swong2/Alignment/project_context/reports/README.md
/projects/beto/swong2/Alignment/project_context/research_notes/Deception specificity and shared circuits/README.md
```
