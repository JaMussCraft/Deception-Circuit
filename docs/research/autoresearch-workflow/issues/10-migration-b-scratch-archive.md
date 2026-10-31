# 10 — Migration B: archive the closed `.scratch` directories and index their text

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 01 (apply tool, lint), 05 (directions.json)
**Wave:** B (applied after the DC merge, and after the orchestrator confirms with the user that no live session uses
these directories).
**Estimated size:** reading about 40k tokens (spec §3, R3, R14, R15; lane 3 §1-2 and §4 "What to track";
`DC/docs/research/selective-deception/README.md` for the precedent), writing about 40k tokens of script and tests.
You do not read the contents of the `.scratch` directories; your script hashes and scans them.
**Hand-back:** `F/reports/10-handback.md`

## What to do

Write and test a migration script that archives each closed `.scratch` directory byte for byte under
`DC/outputs/_studies/<slug>/scratch/`, leaves a symlink at the old path, and copies a curated text subset into
`docs/research/` with a provenance map (R3). Stage the moves and symlinks; write the curated copies in W.

## Facts to build on

- Precedent: `A/.scratch/selective-deception` is a symlink to
  `DC/outputs/_studies/selective-deception/study` (inode-preserving rename on the same filesystem, per its README).
  `outputs/_studies/` is ignored by DC's `.gitignore`.
- Candidates (16 real directories): `component-analysis`, `eval5-grader-fixes`, `format-control`,
  `mechanism-analysis`, `mechanism-datasets`, the ten `sdr-*` study directories, and `autoresearch-workflow`.
  Excluded: `sdr-session-wrapup` (written today by another session) and `selective-deception` (already moved).
- `autoresearch-workflow` holds stale copies of this feature's reports. It moves to
  `DC/outputs/_studies/autoresearch-workflow/scratch-stale/` and its symlink points to
  `DC/docs/research/autoresearch-workflow` (exists only after the merge).
- Code and tests that read `.scratch` paths, all of which must keep resolving: `W/tests/test_selective_v6_manifest.py`,
  `test_sdr_cue_probe.py`, `test_mechanism_analysis_figures.py`, `test_selective_v7.py`, `test_frozen_head_masks.py`,
  `test_sdr_cue_positions.py`, `test_sdr_routing_validation.py`, `W/scripts/sdr_clause_choice.py`,
  `sdr_cue_circuits.py`, `sdr_native_controls.py`, `sdr_routing_validation.py`, `W/evaluation/frozen_head_masks.py`,
  `format_control_summary.py`, `eval5_format_summary.py`. Examples: `.scratch/sdr-native-controls/selection-audit.json`,
  `.scratch/sdr-clause-choice/spec.md` and `rubric.md`, `.scratch/eval5-grader-fixes/issues/`.
- Several of these files are hash-pinned by receipts, so not one byte may change.

## Scope

In W:
- `F/tools/migrate_scratch.py` with `plan` (writes `S/ops/10-migration-b.json` and the curated copies), `verify`
  (checks every recorded path and hash after the orchestrator applies wave B), and a liveness check that skips any
  directory with a file modified in the last 12 hours, except `autoresearch-workflow`.
- `F/tools/test_migrate_scratch.py` with fixture trees in temporary directories.
- Curated copies under `W/docs/research/<direction>/scratch-copy/<scratch-slug>/` (sdr studies go under
  `sdr-mechanism`), each folder with `provenance.json` mapping every copy to its archive path and sha256, and
  listing archive-only files by count and total size. The curated subset is Markdown at depth 2 or less named
  `spec*`, `plan*`, `progress*`, `RESUME*`, `analysis*`, `*final-report-review*`, `*design-review*`, `agent-brief*`,
  plus `issues/*.md`; each file at most 200 KB and at most 1.5 MB per directory.
- `W/docs/research/directions.json`: fill `legacy_scratch` and `archive` for each migrated directory; validate.
- `S/ops/10-migration-b.json` (wave B): `mkdir`, `move` and `symlink` ops.

## Acceptance criteria

- [ ] Script tests cover: archive move and symlink on a fixture tree; byte-identity by sha256 of every file; the
      liveness skip; refusal when the destination exists; the curated selection rules and size caps; a planted fake
      token that blocks the copy of that file and is reported; `verify` passing after a simulated apply and failing
      after a one-byte change. Both envs.
- [ ] `migrate_scratch.py plan` ran on the real directories. Its summary (directories, files, bytes, copied files,
      skipped directories with reasons, secret-scan hits) is pasted. No file contents were printed.
- [ ] Every `.scratch/...` string found in the files listed above resolves today; the list, with existence results,
      is saved to `F/reports/10-scratch-paths-before.json`.
- [ ] The seven test modules listed above were run in both envs before migration; pass and fail names are saved to
      `F/reports/10-tests-before.md`. The hand-back gives the orchestrator the exact commands to rerun them and
      `migrate_scratch.py verify` after wave B.
- [ ] Every curated copy passes the secret scan; copies that fail are not written and are listed.
- [ ] `directions.json` validates after the edit.
- [ ] `apply_staged.py --staging S --only 10 --wave B --dry-run` output pasted.

## Verification

Both interpreters for the script tests. The real moves happen only when the orchestrator applies wave B.

## Comments
