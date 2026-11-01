# Selective deception research: paused session

The user paused this research on 2026-10-31 and requested integration of all eight session branches into `main`, preservation of experiment outputs, and removal of the session worktrees. This is a pause, not a claim that the broader research objective is complete. No new experiment or spending is authorized by this handoff.

## Results and evidence

The study directory is now in this primary checkout at `outputs/_studies/selective-deception/study/`. The old Alignment `.scratch/selective-deception` location is a compatibility symlink to it, so existing reports and artifact links remain usable. The directory was moved on the same filesystem without changing its inode or rewriting frozen files. Large experiment artifacts remain local and are not committed to Git.

Versioned copies of the ten research notes are included in [reports/](reports/). Their originals, including `v5_transfer.md`, `v6_components.md`, and `v7_positions.md`, were in Alignment `project_context/research_notes/Deception specificity and shared circuits/` until 2026-10-31 and now sit, byte for byte, in the local-only `outputs/_studies/project-context-dedupe-20261031/research_notes/`. The archive contains the underlying plans, training outputs, frozen masks, raw evaluation records, plots, code reviews, scientific reviews and budget ledgers.

- Sparse necessary-mask experiments cover preservation objectives including WikiText and expanded all-head search. These are complete historical runs, not an active training process.
- V5 completed the ten frozen-mask eval5 blocks and the necessary-versus-sufficient comparison under the documented grading amendments. The new mask did not establish broad superiority over the old sufficient circuit. Preserve acquisition/classification caveats and the unknown API charge reserve.
- V6 completed head interventions, attention summaries and targeted path/rescue tests. L17H27 affected both deceptive instructions and benign inversion; a smaller L13H23-to-L17H27 query path also affected both. Attention findings are descriptive.
- V7 completed the frozen final-token versus aligned-prompt comparison: 448 rows from 16 previously exposed matched scenarios. Broader New30 patching added similar D/I margin disruption and some first-token changes, alongside benign errors. Native and fp32 boundary differences are retained. No deception-specificity or coherent-refusal/free-generation claim follows from this test.

Detailed evidence: archive `reports/187-final-scientific-review.md`, `210-v6-final-scientific-review.md`, and `217-v7-final-scientific-review.md`; V6/V7 completion receipts retain their historical source and artifact bindings.

## Sources and relocated outputs

`session-branches-20261031.json` records the eight original branch tips. Their commits remain reachable through the merge history on `main` after branch deletion. Loose worktree outputs and logs were copied to primary paths and SHA256-verified; metadata under `.superpowers` was preserved separately under `outputs/_studies/selective-deception/worktree-metadata/`. The exact source-to-destination map is in archive `wrapup-20261031/loose-file-relocation-verified.json`.

Historical manifests and execution receipts intentionally retain their original absolute paths and hashes. A missing retired worktree path does not mean its source commit was lost. To inspect an original runtime, use `git show ORIGINAL_COMMIT:path` or create a fresh checkout of that recorded commit and consult the relocation map. Do not rewrite old receipts to authorize current code, reset consumed guards, or restart old controllers. A faithful historical replay requires an explicit source/data restoration plan; fresh experiments need fresh frozen inputs and receipts.

## Resume safely

1. Read this handoff, the shared Alignment memory, and the latest scientific review before choosing new work. Review any findings from concurrent dataset/mechanism studies separately; this session did not merge or remove their branches.
2. Verify current source, artifact locations, queue state and budgets. Do not rely on historical active-job entries lower down in older chronological notes.
3. Choose and freeze one new question. One candidate is comparing cached-intact L17H27 rescue against natural release under prompt-wide New30, to clarify the reduced restoration in the broader perturbed context. Cleaner behavioral controls and stronger generalization evidence remain separate research needs. These ideas have not been run.
4. Create a fresh worktree from current main; retain original data and completed results. Review changes and test intervention identities before any new GPU/API work.

At pause: 38.35/40 cumulative reserved GPU-hours; 1.65 hours remain under the existing cap. Actual recorded GPU time is 45,167 seconds. API ledger: 1,113 historical attempts, $4.1784295 known cost plus a retained $0.66 unknown-charge reserve; no additional API costs from V6/V7 or wrapup. Larger runs require a new explicit budget decision. Lead compactions confirmed: 16; ordinary check-ins and this wrapup do not increment that count.

Integration and final verification details are recorded in archive `wrapup-20261031/`. No automatic successor experiment is configured.

## Integration verification

All eight branches merged without conflicts. After cleanup, all 24 session test modules passed:694 tests in the production environment;687 passed and7 expected dependency-version skips in base Python. Two test-only fixture repairs removed stale references to an already-retired mechanism worktree; runtime code, source-hash enforcement and frozen results were unchanged. Twenty-three loose files (103,993,205 bytes) were copied and checksum-verified, and81 frozen V6/V7 runtime bindings were verified directly from their original Git commits. Ten research notes are versioned in this directory. The merges are local; no remote push was performed.
