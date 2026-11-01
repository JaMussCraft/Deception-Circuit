# Hand-back `48`: Mean-bank reference re-review

Agent: Codex independent reviewer. Ticket: narrow post-review bank provenance compaction. Status: handed-back.

## What changed

Production files were read only. The orchestrator may commit `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report48-ladder-bank-reference-rereview-handback.md`. The same report is mirrored in primary. No staged operations exist.

**Verdict: no blocking finding in the scoped change.** The canonical selected artifact retains the complete original-H bank values and source provenance. The scoring runner still receives that full bank in memory. Compaction happens only after scoring and exact row/control coverage validation; it changes the repeated output provenance field rather than any inputs, scores, group membership or gate calculation.

Inspection of `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_pipeline.py:359` shows that `resolve_bank_reference` reads the sealed selected artifact when no already-loaded artifact is supplied, checks the full selected payload hash, requires the referenced task, checks the task bank hash, and checks source IDs, condition, splits, instance count and token count against the retained complete provenance. Thus recomputing a modified artifact's own envelope hash does not satisfy an older scored row's reference.

`compact_bank_provenance` constructs task-specific references, associates utility and native rows with the bank's mechanism task through their exact group labels, and compares the original row provenance against the canonical selected-bank provenance before replacing it. It retains the artifact location, both content hashes, task, source IDs, condition, splits and counts. Canonical row metadata is checked once per shared provenance object, avoiding repeated hashing of identical large dictionaries. Rows without mean-bank provenance are left alone. The full and subtracted groups share their mechanism's bank, as before.

The actual score-stage entry point supplies the selected artifact named by the CLI. The fallback nonfile reference is used only by injected direct-call fixtures, which cannot produce production final results. Existing selection/score hash joins remain in place. The SDR summary qualification remains wired into the summary path and passes its regression.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -k 'bank_provenance_reference or summary_preserves_sdr' -q
```

Observed: `2 passed, 19 deselected in 2.23s`; exit code `0`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -k 'bank_provenance_reference or summary_preserves_sdr' -q
```

Observed: `2 passed, 19 deselected, 1 warning in 2.35s`; exit code `0`. The warning concerns the existing base pandas/bottleneck version combination.

The bank regression writes a real immutable selected artifact, compacts the repeated row provenance, JSON-roundtrips the reference, dereferences from the actual file, and checks full provenance hash equality. It then changes the canonical bank token count and recomputes the file's envelope hash; dereferencing the old row reference is rejected. The summary regression checks that SDR remains descriptive-only while retaining numerical diagnostics.

## Execution evidence

Local scoped CPU tests only. In each interpreter the observed count was `2` passing against `2` selected tests, with `19` intentionally deselected. Both commands exited `0`. No pretrained model, GPU, API, Slurm job, notebook, behavioral baseline or production assessment output was run here. No scientific run manifest is claimed; real-model behavior is not yet verified by this narrow re-review.

## What is NOT done

No production edits, git commands, broad rerun, full model execution, new run reservation or alteration to unrelated training/runtime work. The prior full pipeline review remains in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report46-ladder-pipeline-review-handback.md`. Author report `42` was not read. The real-model pilot remains a separate required acceptance step.

## Open questions

No current blocker. Preserve the selected artifact alongside scored rows: compact provenance is a checked reference to that artifact, so the artifact must remain available for later full provenance inspection.
