# Hand-back: A2 wrapper scoped re-review

Agent: Codex reviewer. Ticket: frozen training wrapper. Status: resolved.

## What changed

No implementation edits. Both blockers in the earlier review are closed. This report supersedes its blocking verdict.

- Worktree report for orchestrator commit: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/23-wrapper-rereview-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/23-wrapper-rereview-handback.md`.

The frozen configuration and argv now specify training margin `0.7` explicitly for both D and I. The expected-config subset parses it as a float, and artifact checks reject a persisted mismatch. Historical screening margins remain independent. Direct actual-parser/loss-resolver checks produced training `0.7/0.7` from historical D/I screening `0.7/0.5`. Evidence: `/tmp/a2-wrapper-rereview-focused.log`.

Before the CLI can call training, `plan_run` now loads actual stored splits and checks full counts, full ID order, selected prefixes, and every stored row's clean/reference prompts, recipient labels, twin metadata, and prompt proofs. Both conditions are inspected for matched data. Source authentication compares complete source-file hash maps, their canonical aggregate hashes, and decoded source-row hashes against the build manifest. Stored `source_recipient` and `source_reference` must equal those authenticated source rows. Consequently label checks do not merely trust the embedded row provenance. Prompt hashes are compared to private configuration proofs using the materializer's canonical JSON hashing. The materializer itself is unchanged by these fixes.

The original stale fixture `/tmp/a2-wrapper-review-stale-8hxss75s`, previously accepted with different actual IDs, now fails with `stored split id/order mismatch: D/train` before launch. There are no remaining blockers in this scoped re-review.

## How verified

Read updated wrapper, frozen JSON, direct test source, and actual materializer hashing implementation. Inspected the direct logs rather than relying on the worker's narrative:

- `/tmp/a2-wrapper-fix-base.log`: `49 passed`, one pandas/bottleneck warning.
- `/tmp/a2-wrapper-fix-mgnp.log`: `49 passed`.
- `/tmp/a2-wrapper-stale-red.log`: stale-row regressions failed before the fix.
- `/tmp/a2-wrapper-stale-green.log`: targeted regressions pass after the fix.

Direct test source covers changed ID, count, and order beyond the selected prefix; changed clean/reference prompts and target/distractor labels; forged embedded source labels; forged prompt proof; and changed original source bytes. Margin tests use the actual parser/resolver and reject both a changed frozen margin and wrong output-artifact margin.

Ran one focused read-only Python check with base Python and `PYTHONDONTWRITEBYTECODE=1`, importing `train.build_parser`, `train.resolve_args`, and `dataset.deception_common.resolve_margin`. It resolved both historical screening cases to the explicit training margin, compared updated direct/module dry-run JSON, checked current source hashes and absent outputs, and retried the original stale fixture through `plan_run`. Exact observed output is `/tmp/a2-wrapper-rereview-focused.log`; exit was `0`.

The updated `/tmp/a2-wrapper-finish-check/direct-fix-dry-run.json` and `/tmp/a2-wrapper-finish-check/module-fix-dry-run.json` differ only by interpreter executable. All recorded source hashes match current files. Neither the requested receipt nor planned training directory exists. No broader suite or duplicate focused suite was run during this re-review because complete direct logs already exist.

## Execution evidence

- Job id and cluster: local CPU parser, file-hash, and stale-input checks only; no Slurm job.
- Exit code: focused re-review check returned `0`; inspected completed worker pytest logs show no failures.
- Counts: inspected suites show `49/49` tests passing in both interpreters. The original materialized fixture remains `1/1/1` rows; the separate stored-cohort test fixture exercises full `205/3/4` rows and selected `200/3/4` prefixes.
- Baseline reproduces: previous stale acceptance now produces the expected prelaunch rejection. Training margin is `0.7` against the lead's required `0.7` for each condition. No model baseline is claimed.
- Provenance file: no scientific `run_manifest.json` exists because no scientific run occurred. Synthetic commit `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` remains fixture-only. Current dry-run source hashes match the reviewed implementation.
- Usage: live weekly reading was `7` percent used against cap `80`, reset `2026-11-06T16:07:41+00:00`.

## What is NOT done

No model/tokenizer load, GPU run, paid API, Slurm submission, git, notebook execution, subagent, pipeline edit, or scientific result. Projection remains the separate deferred task. Approval covers the wrapper preparation implementation and closes the earlier two defects; it grants no additional execution or fleet authorization.

## Open questions

None for these fixes. Default: proceed to the separately scoped next preparation task under existing authorization and budget gates.
