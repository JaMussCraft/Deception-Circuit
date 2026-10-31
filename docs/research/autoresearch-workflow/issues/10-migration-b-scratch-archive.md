# 10 — Migration B: archive the closed `.scratch` directories and index their Markdown

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 01 (apply tool, lint), 05 (directions.json)
**Wave:** B (applied after the DC merge). The directories R28 protects are not migrated now; this ticket only gives
the command that migrates them later.
**Estimated size:** reading about 40k tokens (spec §3, R3, R14, R15, R28, R34; lane 3 §1-2 and §4 "What to track";
`DC/docs/research/selective-deception/README.md` for the precedent), writing about 45k tokens of script and tests.
You do not read the contents of the `.scratch` directories; your script hashes and scans them.
**Hand-back:** `F/reports/10-handback.md`

## What to do

Write and test a migration script that archives a closed `.scratch` directory byte for byte under
`DC/outputs/_studies/<slug>/scratch/`, leaves a symlink at the old path, and copies its Markdown into `docs/research/`
with a provenance map (R3, R34). Run it now for the directories wave B may move; stage those moves and symlinks; and
write the Markdown copies in W.

## Facts to build on

- Precedent: `A/.scratch/selective-deception` is a symlink to `DC/outputs/_studies/selective-deception/study`
  (inode-preserving rename on the same filesystem, per its README). `outputs/_studies/` is ignored by DC's
  `.gitignore` (`W/.gitignore:15`).
- Wave B directories: `component-analysis`, `format-control`, `mechanism-analysis`, `mechanism-datasets`, and the
  special case `autoresearch-workflow`.
- Deferred until the user confirms the live Codex session is finished (R28): the ten `sdr-*` study directories,
  `sdr-session-wrapup`, `selective-deception` (already archived; it needs only a Markdown copy) and
  `eval5-grader-fixes`. Their mtimes run from 20 to 26 October, so the 12-hour skip alone would not protect them.
- `autoresearch-workflow` (R34) holds stale copies of this feature's lane reports and proposal, whose canonical copies
  are in F. Each of its files is moved to `/u/swong2/.claude/research-session/backups/scratch-autoresearch-workflow-20261031/`
  only if a file with the same sha256 exists in F; any file without a match is listed and kept. Then the directory
  is replaced by a symlink to `DC/docs/research/autoresearch-workflow`, which exists only after the merge.
- Code and tests that read `.scratch` paths, all of which must keep resolving: `W/tests/test_selective_v6_manifest.py`,
  `test_sdr_cue_probe.py`, `test_mechanism_analysis_figures.py`, `test_selective_v7.py`, `test_frozen_head_masks.py`,
  `test_sdr_cue_positions.py`, `test_sdr_routing_validation.py`, `W/scripts/sdr_clause_choice.py`,
  `sdr_cue_circuits.py`, `sdr_native_controls.py`, `sdr_routing_validation.py`, `W/evaluation/frozen_head_masks.py`,
  `format_control_summary.py`, `eval5_format_summary.py`. Examples: `/Alignment/.scratch/mechanism-analysis/reports`,
  `.scratch/sdr-native-controls/selection-audit.json`, `.scratch/eval5-grader-fixes/issues/`.
- Several of these files are hash-pinned by receipts, so not one byte may change.

## Scope

In W:
- `F/tools/migrate_scratch.py` with `plan --include <slug>[,<slug>...]` (writes `S/ops/10-migration-b.json` and the
  Markdown copies for the named directories), `verify` (checks every recorded path and hash after the orchestrator
  applies the ops), and two guards: a refusal for any directory listed in R28 unless `--confirmed-live-session-finished`
  is passed, and a skip for any directory with a file modified in the last 12 hours (except `autoresearch-workflow`).
- `F/tools/test_migrate_scratch.py` with fixture trees in temporary directories.
- Markdown copies under `W/docs/research/<direction>/scratch-copy/<scratch slug>/`: every `*.md` at any depth,
  including `reports/`, `reviews/` and `handbacks/`, at most 200 KB per file and 1.5 MB per directory, each folder
  with `provenance.json` mapping every copy to its archive path and sha256 and listing what the caps excluded by
  path and size, plus archive-only files by count and total size.
- `W/docs/research/directions.json`: fill `legacy_scratch` and `archive` for each migrated directory; validate.
- `S/ops/10-migration-b.json` (wave B): `mkdir`, `move` and `symlink` ops for the wave B directories only.

## Acceptance criteria

- [ ] Script tests cover: archive move and symlink on a fixture tree; byte-identity by sha256 of every file; the R28
      refusal and its override flag; the 12-hour skip; refusal when the destination exists; the Markdown selection at
      any depth and both size caps with the exclusions reported; a planted fake token that blocks the copy of that
      file and is reported; the `autoresearch-workflow` case keeping a file with no match in F; `verify` passing after
      a simulated apply and failing after a one-byte change. Both envs.
- [ ] `migrate_scratch.py plan --include component-analysis,format-control,mechanism-analysis,mechanism-datasets,autoresearch-workflow`
      ran on the real directories. Its summary (directories, files, bytes, copied files, cap exclusions, skipped
      directories with reasons, secret-scan hits) is pasted. No file contents were printed.
- [ ] No op in `S/ops/10-migration-b.json` touches a directory listed in R28 (a script checks; output pasted).
- [ ] The hand-back gives the one-line command for the deferred directories, to run only after the user's
      confirmation, for example
      `/sw/external/python/anaconda3/bin/python3.9 F/tools/migrate_scratch.py plan --confirmed-live-session-finished --include sdr-assay-diagnosis,...,eval5-grader-fixes`
      with the full list written out.
- [ ] Every `.scratch/...` string found in the files listed above resolves today; the list, with existence results,
      is saved to `F/reports/10-scratch-paths-before.json`.
- [ ] The seven test modules listed above were run in both envs before migration; pass and fail names are saved to
      `F/reports/10-tests-before.md`. The hand-back gives the orchestrator the exact commands to rerun them and
      `migrate_scratch.py verify` after wave B.
- [ ] Every Markdown copy passes the secret scan; copies that fail are not written and are listed.
- [ ] `directions.json` validates after the edit.
- [ ] `apply_staged.py --staging S --only 10 --wave B --dry-run` output pasted.

## Verification

Both interpreters for the script tests. The real moves happen only when the orchestrator applies wave B.

## Comments
