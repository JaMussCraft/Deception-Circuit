# Hand-back: Independent full A1 artifact and primary-gate audit

Agent: Codex independent reviewer. Status: handed-back.

## What changed

Completed the prepared read-only audit against the actual full score and orchestrator-generated final summary. No scoring, summary, frozen-parent, shared-source, research-session or ledger files were changed. Owned artifacts are:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/tools/98-full-a1-audit.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit-handback.md`

Preparation evidence remains in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit-preparation.json`. Review files are mirrored at the corresponding paths under `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/`.

Audit verdict: accept artifact integrity, coverage and canonical primary numerical calculations. No actionable artifact or numerical discrepancies were found. This is an audit pass; the registered scientific specificity gates fail for the tested original FAR and SER groups. SDR retains its original descriptive qualification.

## How verified

The final audit command ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/98-full-a1-audit.py > docs/research/specificity-ladder/reports/98-full-a1-audit.json
```

Observed: exit zero and `full_audit_passed`, with `full_run_examined`, `canonical_summary_examined` and `canonical_summary_final` all true. The script never calls the canonical summarizer. Independent calculations reconstruct paired pressure-effect ratios, full-vocabulary accuracy shifts, pressure-cluster bootstrap intervals, crossed-assay readiness and joined MMLU floors directly from raw rows, then compare with the existing canonical summary.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/98-full-a1-audit.py --self-test
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 docs/research/specificity-ladder/tools/98-full-a1-audit.py --self-test
```

Synthetic checks pass on both interpreters. They cover unequal-denominator ratios, paired streams, cluster intervals, inclusive D and strict I thresholds, point-versus-interval strength, and MMLU completeness-versus-pass. During preparation an incorrectly constructed cluster fixture failed and was corrected before both interpreters passed. During the full audit the obsolete reviewer process was deliberately stopped with exit `143` so the accounting reader could accept the actual top-level receipt format. It was replaced by the successful command above. No production computation was interrupted or repeated.

The artifact audit uses actual content-hash readers, source/design validation, selection-sidecar validation, protected-registry and frozen-grader checks, exact expected row/control generators, batch constructors and immutable bank-reference resolution. It checks current code and source-data hashes; model, tokenizer and execution identity; score-envelope and published-manifest agreement; design, selection, domain, group, bank and utility hashes; and canonical summary linkage to the exact scored artifact. Repeated bank references are checked for exact equality after validating the canonical reference, including its exact selected-file path.

Every row matches its frozen recipient record, canonical token labels, selected group, donor map, support/identity/gate flags and bank reference. Every positive control matches its explicit frozen donor and readout mapping and uses all sender keys including embeddings, excluding READOUT. All original scientific design fields and selected groups/banks remain exactly equal to the immutable pre-fix originals; only the previously reviewed metadata/calibration identity changed. No author interpretation report was used.

The audit independently compares all primary point estimates, per-stream denominators, collateral shifts and bootstrap intervals to the canonical primary cells. It also checks the exact canonical cell inventory, crossed readiness, fixed MMLU floor quantities and descriptive qualification across SDR operations. Numerical comparison tolerance is `1e-9`; this is an audit-comparison tolerance, not a change to production scoring or calibration tolerance.

## Execution evidence

- Job and cluster: `23417811` on Delta. `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/full/accounting.txt` records `COMPLETED`, exit `0:0`, elapsed 8,158 seconds, and one allocated GPU. The saved top-level receipt omits a cluster column; cluster identity is checked against the runtime manifest. Root's existing canonical finalization log says `summarize: complete`.
- Row counts: 28,884 observed against 28,884 unique frozen expected rows; 3,396 observed against 3,396 unique frozen positive controls. Task totals are 9,000 each for FAR, SDR and SER, 1,500 IOI rows and 384 MMLU rows. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json`.
- Baseline reproduces: every logged intact-versus-empty/self-replay maximum margin error is zero against expected zero; production assay validity also checks argmax agreement. Every all-sender full-vocabulary fp32 donor-logit recovery error is zero against zero. The completed pilot's 1,188 rows and 144 controls are independently rechecked against their frozen expected scope; raw full-run effect values are not required to equal pilot values because parent padding can differ. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json`.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/full/score/run_manifest.json`, source commit `5f450dc93dac707af649dee8c8ca60888b2831db`; exact content-hashed score `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/full/score/score.json`; canonical result `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/full/summary.json` has `final: true` and the matching score hash.

All 28,884 rows carry valid numerical assays; 23,112 are supported, 18,120 are gate-valid, and 7,992 are marked degenerate. These flags describe different properties. Unsupported secondary donor rows are preserved in the full denominator. Every primary item-swap cell has complete paired support and complete crossed-assay coverage. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json` and the canonical summary above.

The runtime manifest records model load 39.3117 seconds, scoring compute 8,059.2503 seconds, stage 8,099.6478 seconds, peak allocated 19,582,702,592 bytes and peak reserved 20,797,456,384 bytes, using BF16 on A100. The completed run fit the prior three-hour reservation recommendation; the reviewer started no GPU work. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/full/score/run_manifest.json` and its accounting file.

The primary interpretation table uses independently recomputed raw D target-choice rates and pressure-effect removal fractions from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json`. Percentages below are derived from the recorded fractions; intervals are nominal 95% paired pressure-cluster bootstrap intervals.

| Group and role | D target choice, intact → patched | D pressure fraction removed, interval | I pressure fraction removed, interval | Local point / strong | Joined point / strong |
| --- | --- | --- | --- | --- | --- |
| FAR, confirmatory (derived percentages) | 100% → 53% | 23.9% [21.7%, 26.0%] | 31.6% [30.5%, 32.7%] | fail / fail | fail / fail |
| SER, confirmatory (derived percentages) | 100% → 80% | 23.5% [18.8%, 26.8%] | 30.4% [28.1%, 32.3%] | fail / fail | fail / fail |
| SDR, descriptive only (derived percentages) | 100% → 1% | 110.6% [98.8%, 119.8%] | 129.2% [125.0%, 133.2%] | numerical fail / fail | ineligible / ineligible |

Raw D rates measure fixed-answer full-vocabulary argmax choices across both designation streams. They do not evaluate generated-text honesty, refusal or coherence. The D target-choice drop and the registered ratio-of-means margin gate are separate quantities. In particular, the large FAR target-choice decline does not satisfy the registered pressure-effect threshold.

FAR and SER each remove less than the required half of the D pressure effect and more than the allowed quarter of the I effect. Their D upper interval endpoints remain below the D threshold, and their I lower endpoints remain above the I threshold. Neither has a local point or interval-strength pass. The intervals use eleven FAR and sixteen SER pressure clusters, so the registered few-cluster precision caveat remains. SDR uses nineteen clusters; its ratios can exceed unity when patching overshoots the neutral reference. The recorded SDR source set did not pass its earlier mediation criterion, so the current numerical results retain descriptive-only status. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json`; thresholds and source qualifications are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/spec.md`.

Collateral accuracy also fails preservation. FAR H/F/IOI shifts are derived −32.5/−34.5/−5 percentage points; SER shifts are −22/−17.5/−1 percentage points. The FAR IOI boundary does not satisfy the strict preservation threshold. SDR's descriptive shifts are −98.5/−99/−51 percentage points. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json`.

Both MMLU floors are complete on the same 32 frozen items, but none passes the at-most-one-additional-error rule. These are joined zero/H-mean utility floors, not an invented MMLU item swap. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json`.

| Group | Zero additional errors | H-mean additional errors | Coverage readiness | Both floors passed |
| --- | ---: | ---: | --- | --- |
| FAR | 15 | 7 | complete | no |
| SER | 7 | 4 | complete | no |
| SDR, descriptive | 17 | 14 | complete | no |

The joined primary gate requires local numerical success, complete crossed coverage, both MMLU floors, and an eligible confirmatory source group. FAR and SER fail already at the local point gate and also fail their joined floors. A final summary and complete assay coverage therefore do not mean that specificity passed.

Independent recomputation of the frozen selection screen finds zero answer-contribution candidates for every group, so full and minus groups are identical and the duplicate contrasts were correctly collapsed. This run cannot compare a distinct mover-removed group with the full group. The empty screen does not establish that answer-copying machinery is absent, nor that the frozen criterion identified every answer mover. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/98-full-a1-audit.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_design.py`.

## What is NOT done

No model work, API calls, tokenizer regeneration, native-logit/residual rerun, EVAL 5, source changes, finalization rerun, research-state update, commit or merge was performed. Noops here mean the recorded production margin/argmax assay; donor recovery refers to the recorded full-vocabulary fp32 logits. No unrecorded full-native-logit equality is claimed.

Independent scientific recalculation covers the preregistered primary item-swap quantities, their intervals and joined floors. Secondary operations retain exact artifact coverage/provenance checks, but their complete scientific summaries were not independently reimplemented. This is one frozen run, not a distinct-seed replication or a proof about every possible deception circuit.

## Open questions

No blocking integrity or primary-calculation discrepancy remains. Default: the orchestrator records the registered FAR/SER primary-gate failures with raw D behavior and collateral harm, retains SDR as descriptive, and states that the mover contrast collapsed because its frozen screen selected no candidates. The orchestrator owns the final gate decision and any consequent research-session state or direction change.
