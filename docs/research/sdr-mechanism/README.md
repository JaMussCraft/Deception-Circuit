# Paused SDR mechanism investigation

This session studies how the original D/H/F coarse heads-only SDR circuits compose to produce deceptive reporting. Research is paused, with the completed studies and unsuccessful protocols preserved for future extension. Ordinary-task reuse is acceptable; deception specificity is not a prerequisite.

Start with [the shared-component composition findings](<reports/SDR shared-component composition findings.md>). Earlier shared heads influence reporting through a downstream attention group: restoring its outputs blocks most observed choice changes, while transferring induced receiver states alone reproduces only part of the effect. This is a partial conditional causal explanation, not a complete mechanism.

## Reports

- [SDR circuit mechanism review](<reports/SDR circuit mechanism review.md>)
- [SDR cue probe findings](<reports/SDR cue probe findings.md>)
- [SDR cue-circuit transplant findings](<reports/SDR cue-circuit transplant findings.md>)
- [SDR mechanism investigation status](<reports/SDR mechanism investigation status.md>)
- [SDR named-consequence probe findings](<reports/SDR named-consequence probe findings.md>)
- [SDR native controls findings](<reports/SDR native controls findings.md>)
- [SDR native evidence audit](<reports/SDR native evidence audit.md>)
- [SDR routing pilot findings](<reports/SDR routing pilot findings.md>)
- [SDR routing validation findings](<reports/SDR routing validation findings.md>)
- [SDR shared-component composition findings](<reports/SDR shared-component composition findings.md>)
- [SDR shared-head position findings](<reports/SDR shared-head position findings.md>)

These are byte-identical archival copies. Their original locations and SHA256 values are recorded in [session-archive.json](session-archive.json). Historical reports describe their contemporary stopping points; the latest result is the shared-component composition report.

## Evidence and restart

Raw results remain local in the primary checkout under `outputs/_analyses/sdr-*`. Later phases already live in the parent Alignment checkout under `.scratch/sdr-*`. Worktree-local plans, review records and scheduler logs are preserved in `Alignment/.scratch/sdr-session-wrapup/preserved/`. The archive manifest records every migrated file and checksum, including explicitly marked synthetic test fixtures. These raw files are not embedded in this Git repository.

The detailed restart guide, preservation reviews, test logs and complete-history branch bundle are in `Alignment/.scratch/sdr-session-wrapup/`. Source history retains both original branch tips. Historical manifests bind exact source commits, environments and absolute paths: recreate the original checkout and fixtures to reproduce those runs. Do not rewrite their hashes or resume them against changed main code. Some wrappers intentionally reject execution outside their historical approved worktree. The unused H100 port must not reactivate its superseded transfer/job plan.

Useful next questions are which heads or queries account for the downstream quartet contribution, which surrounding upstream-induced states enable full rescue, and how the five earlier heads divide their contributions. These are new research proposals, not unfinished jobs. Earlier failed gates and their stopped conditional assays remain closed.

## Validation scope

The session code is checked using both supported Python environments and restored fixtures in a disposable combined-source snapshot. Some archival integration tests require old absolute source paths and preserved `.superpowers` fixtures. Test-only integration repairs preserve production provenance checks and explicitly verify that historical wrappers reject relocated execution. Passing those checks does not establish replayability on changed hardware or source.

A small cleanup-independent CPU check is `python -m pytest -q -p no:cacheprovider tests/test_sdr_clause_choice.py tests/test_sdr_native_controls.py`, with BLAS threads pinned to 1. It requires the retained parent-checkout `.scratch/sdr-native-controls/selection-audit.json`. No notebooks, real-model inference or new GPU jobs are needed for wrap-up.

Lead orchestrator context compactions at this checkpoint: **10**.
