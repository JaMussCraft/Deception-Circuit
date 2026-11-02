# Hand-back: Full A1 audit preparation

Agent: Codex independent reviewer. Status: handed-back.

## What changed

Prepared the read-only full artifact audit without examining partial full-run output or running canonical summarization. Owned files are:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/tools/98-full-a1-audit.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit-preparation.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit-handback.md`

These are mirrored under the corresponding paths in `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/`. No shared production source, frozen artifact, research-session state or ledger was changed.

The script has three modes: synthetic self-check, preparation-only parent/pilot audit, and the eventual full artifact audit. Default mode requires complete score, run manifest, terminal accounting, and the orchestrator's existing canonical summary before it proceeds. It never calls the canonical summarizer, submits work, or writes a final summary.

The eventual audit checks current code/data/protected-registry/grader identity, immutable parent and sidecar links, exact full row/control coverage, source records and labels, complete frozen donor-map provenance, computed identity/support/gate flags, selected banks, zero logged replay error, and zero all-sender full-vocabulary fp32 donor recovery error. It checks execution identity/timings/memory and terminal accounting, then independently derives primary gate quantities from raw rows and compares them with the canonical summary linked to that exact score hash.

Independent gate calculations include paired-stream ratios of means, pressure-cluster bootstrap intervals, collateral full-vocabulary accuracy, crossed-operation readiness and both fixed MMLU floors. They do not call the production metric implementation or its private helpers. Local numerical point/strong flags, assay completeness, and joined primary gates are separate outputs. A joined gate additionally requires both MMLU floors to pass. SDR remains descriptive even if its numerical quantities pass. An empty answer-contribution candidate set means duplicate full/minus groups under the frozen screen, not absence of answer copying.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/98-full-a1-audit.py --prepare-only > docs/research/specificity-ladder/reports/98-full-a1-audit-preparation.json
```

Observed: exit zero and `preparation_passed`; the JSON explicitly records `full_run_examined: false` and `canonical_summary_examined: false`. The parent/pilot audit uses actual artifact, batch, source validation, selection-sidecar and expected-coverage helpers. It independently rechecks the mover criterion from raw selected DLA arrays. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit-preparation.json`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/98-full-a1-audit.py --self-test
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 docs/research/specificity-ladder/tools/98-full-a1-audit.py --self-test
```

Observed: synthetic self-checks pass on both interpreters. They exercise unequal-denominator ratios, paired streams, cluster intervals, inclusive D and strict I thresholds, point-versus-interval strength, and MMLU completeness-versus-pass. An initial interval-strength fixture failed because both pressure clusters had identical mean gaps; its cluster construction was corrected, and both interpreters were rerun. Base also imports the final module successfully; its existing bottleneck dependency warning does not fail the command.

## Execution evidence

This hand-back covers preparation, not the running full assessment. No GPU, pretrained weights, tokenizer construction, API calls, notebooks, scheduler submission or duplicate summarization was used.

- Local execution: the preparation command and synthetic checks above exited zero.
- Completed baseline job: corrected pilot `23417413` on Delta; its existing accounting records `COMPLETED` and `0:0`.
- Row counts: preparation rechecks 1,188 pilot rows against 1,188 expected keys and 144 positive controls against 144 expected keys. Full expected inventory is 28,884 rows and 3,396 positive controls; these are expected counts only, not observed full-run results. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit-preparation.json`.
- Baseline reproduces: corrected pilot logged empty/self-replay maximum margin error zero against expected zero and all positive-control full-vocabulary fp32 donor-recovery errors zero against zero. Source and map provenance were compared to frozen parents rather than inferred from outcomes.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/pilot-4/score/run_manifest.json`, source commit `5f450dc93dac707af649dee8c8ca60888b2831db`. Parents remain the original fresh design/selection plus the immutable original scientific equivalents.

## What is NOT done

The full assessment job is owned by the orchestrator. This reviewer did not inspect an incomplete result, poll its scheduler state, claim its completion, or take over its waiter. No full effect, specificity verdict, canonical-summary agreement, or full-run pass is claimed. Default audit mode and the real-data independent bootstrap remain to be executed after completed evidence exists.

The synthetic checks validate the calculation implementation but do not substitute for checking agreement with the eventual canonical summary. The full audit deliberately preserves unsupported rows and descriptive qualifications rather than interpreting the pilot or a partial sample.

## Open questions

No preparation question blocks handing back. The orchestrator should resume this reviewer once it has reconciled terminal accounting and produced the canonical summary. The exact ready command is:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/98-full-a1-audit.py > docs/research/specificity-ladder/reports/98-full-a1-audit.json
```

It expects `full/score/score.json`, `full/score/run_manifest.json`, `full/accounting.txt`, and `full/summary.json` under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/`. It checks full job identity `23417811`, while the orchestrator remains responsible for job reconciliation and canonical summary creation. After it runs, extend this hand-back with actual full execution evidence and any numerical discrepancies; do not treat this preparation hand-back as a completed full audit.
