# Hand-back 32: joint specificity runner and paired metrics

Agent: Codex worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-ladder.md`, Task 2. Status: resolved implementation and focused checks; independent review and empirical assay remain with the lead.

## What changed

Files for the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/specificity_ladder.py`: typed one-stream batches, explicit donor maps, pooled original-H mean-bank adapter, joint sender patches, fail-closed same-union no-op controls, full-vocabulary and binary scoring, and all-sender readout calibration including embeddings.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_metrics.py`: task-separated paired ratios of means, exact START gates, absolute collateral movement, stream-specific effects, pressure-cluster bootstrap, optional outer donor-seed bootstrap, coverage, raw estimates and MMLU utility uncertainty.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_specificity_ladder.py`: padding/readout/map/identity/no-op validation.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_specificity_ladder_model.py`: real CPU tiny NNsight Llama mixed joint patches, group subtraction, all-sender calibration, original-H pooling and full-vocabulary versus binary scoring.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_ladder_metrics.py`: exact boundaries, paired streams, cluster handling, denominator guards, seed averaging, native-task separation, MMLU and conflicting group membership.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/32-ladder-runner-handback.md`: this report. Lead owns the primary mirror.

No apply-tool operations; no shared hooks/dataloader/design edits; no git commands.

Adapter contract sent to lead before implementation: each LadderBatch contains ids, condition, stream, task, input_ids, attention_mask, explicit readout, opposite_token, honest_token, expected_token, records, optional choice_tokens. Canonical token IDs are explicit for each stream. Native task names are far_v2/sdr_v2/ser_v2; utility task names are ioi/mmlu. Records retain split, source_condition, source_hash, flat normalized per-stream layout and source pressure_id where applicable. Native mechanism assessment requires both streams; IOI/MMLU use clean assessment only. The IOI corrupt stream remains a donor. Task-qualified group labels identify actual memberships; all output records preserve group_members, and the summarizer rejects missing/conflicting membership provenance.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_specificity_ladder.py tests/test_ladder_metrics.py tests/test_specificity_ladder_model.py
```

Observed: 28 passed in 15.45 seconds, exit 0. Log: `/tmp/ladder-runner-mgnp-final.log`. Real model tests use NNsight 0.7.0 and random tiny Llama on CPU; no model download.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_specificity_ladder.py tests/test_ladder_metrics.py tests/test_specificity_ladder_model.py
```

Observed: 21 passed, 1 skipped in 16.03 seconds, exit 0. Log: `/tmp/ladder-runner-base-final.log`. Base NNsight 0.5.12 differs from required 0.7.0, so the tiny-model module is explicitly skipped there. Base skips do not establish patching correctness.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m py_compile component_analysis/specificity_ladder.py component_analysis/ladder_metrics.py
```

Observed after final group guard: exit 0.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m py_compile component_analysis/specificity_ladder.py component_analysis/ladder_metrics.py
```

Observed after final group guard: exit 0.

Test-first evidence included absent-module failures, then regressions failing for ambiguous native tasks, missing donor seeds, mislabeled identity donors, mean-bank recipient overlap, exact 5-point subtraction roundoff, absent MMLU intervals and conflicting group membership. Focused scope only, as assigned; no broad repository suite.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No empirical model assessment, GPU, Slurm, API, notebooks, EVAL 5 or protected-set run.
- No Task 3 adapters, Task 4 CLI, real-data sample selection or independent review.
- Recipient execution uses singleton views to retain arbitrary donor padding/readout semantics. Runtime is conservative and must be measured before any reservation; no throughput claim.
- Upstream source completeness remains an adapter/manifest responsibility. Mean collection rejects non-H/non-train-validation sources and missing hashes, records actual observed source splits/IDs, and rejects source IDs overlapping recipients. It does not discover every upstream H source file itself.
- Optional IOI task_resample is outside this operation contract. Native primary IOI corrupt-stream interchange, zero and explicitly off-task H mean work through the runner. No MMLU native swap/H-twin cell is invented.
- Automatic approval review rejected an earlier combined report command because it included copying into the shared primary checkout without established worker permission. Nothing from that rejected command ran. The lead instructed this worker to write/lint only the worktree report and will mirror it under orchestrator ownership.

## Open questions

- Default integration: labels such as far_v2/full_deciding and far_v2/minus_candidates uniquely identify memberships; reuse the same label only for the same set across mechanism/utility rows.
- Full-vocabulary correct-letter argmax remains the MMLU floor; restricted four-choice accuracy/margins are diagnostics. Missing MMLU cannot establish finished utility coverage.
- Live weekly usage at the implementation checkpoint was 11 percent spent (89 percent remaining), reset 2026-11-06 16:07:41 UTC, below the requested 80-percent cap.
