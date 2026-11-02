# Hand-back: A2 ladder pipeline independent review

Agent: Sol independent reviewer. Status: handed-back.

## What changed

Current scoped closure recommendation: accept the bank-vector and empty-group readiness fixes. Both findings below are closed by source inspection, focused regression tests and independent replay. No new blocker was found within this closure scope. No implementation files were changed. The author hand-back was not read, and no scientific mask or assessment outcome was consumed.

The initial request-changes findings below remain as historical evidence; the closure recommendation supersedes them.

- Orchestrator commit file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/101-a2-ladder-pipeline-review-handback.md`.
- Identical primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/101-a2-ladder-pipeline-review-handback.md`.

**P1 — Bank vectors need exact independently derived typed widths before scoring.** Location: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_pipeline.py:653`. `validate_banks` accepts any nonempty finite list for a component vector. The downstream H-mean replacement uses `expand_as`, so a scalar list silently broadcasts across the entire component dimension. An independent tiny CPU probe collected genuine original-H union banks, whose MLP vectors had width `64`, replaced each value with `[1.0]`, published a new file with matching content hashes, and then passed actual `score`. The resulting output had `621` rows against `621` expected and `36` positive controls. The malformed vector therefore does not fail coverage, file/content checks, source contract or calibration. The H-mean patch no longer applies the collected per-coordinate mean. Require exact finite dimensions derived from the frozen model/config, distinguishing head width from whole-MLP hidden width; a shape declared only by the bank is insufficient. Reject the malformed bank before model scoring, and add scalar, wrong-head-width and wrong-MLP-width tests. This fix can stay entirely in the A2 layer without changing canonical A1 sources.

**P2 — Empty groups bypass required crossed-assay failures when assigning a scientific null.** Location: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_pipeline.py:412`. `empty_failure` checks only the primary item's support, interpretable effect denominator and below-threshold D removal. The subsequent `complete or empty_failure` admits a completed necessity failure even when required crossed readiness is false. Independent full synthetic-row summaries on both interpreters reproduced the same label after a required D zero row was made unsupported and, separately, after a required D H-twin row was made unsupported. In each case the seed still had `assessment_status='failed_necessity_empty_group'`, `specificity_assessment_complete=True` and `complete_assay_ready=False`. A valid empty group must remain a failed necessity result; an unsupported required crossed/control row must instead block the scientific label. Preserve complete accounting separately, and distinguish expected empty-patch degeneracy from missing/unsupported/invalid required assay evidence. Add an end-to-end summary regression using empty memberships and an unsupported required H-twin, alongside the valid empty-group case. Do not merely require the current nonempty-specific MMLU/IOI gate-valid flags from empty patches; retain the expected empty-control semantics while validating the required evidence.

The remaining inspected contracts align with the accepted plan: the CLI re-audits all training sources before freezing groups and again before model stages/resume; original A1 selection/sidecar ancestry stays separate from A2 execution identity; runtime source, grader, live protected registry and file guards run before loading; assessment/utility domains and donor plans are inherited from the frozen prepared artifact. New original-H banks use train/validation ids, both streams and unpadded equal-token pooling through the existing collector. Bank references bind file/content, task owner and runtime numerical labels. Each mixed group is patched jointly; identical memberships retain their seed aliases, and compute traversal preserves the fixed seed order despite sorted JSON. Joined MMLU floors are required separately from primary point pass and coverage readiness. Required primary failures block robust pass, and predeclared unsupported optional diagnostics are retained. The original SDR deciding-set ancestry is not assigned to the new trained groups. Typed memberships, MLP predictions and native training metrics remain separate from ladder outcomes. Successful dry runs do not authorize GPU spending; cost admission remains orchestrator-owned.

This review did not reopen the accepted comparison algebra or later research choices. A1 runtime files remained untouched.

Closure source review: bank geometry now comes from the pinned local model configuration, bound by model/revision, config content hash and file hash; injected fixtures must provide an explicit model config. Required head and MLP vector widths are derived independently of bank values, checked against exact keys, and validated before loaded-model execution begins. Loaded geometry is also compared with the frozen metadata. Empty necessity failure now requires a separately computed complete-required-evidence flag. That validator uses the exact row domain checked by scope validation and requires support, assay validity and finite outcomes across crossed operations, replay/empty controls and utility rows. It allows empty-patch degeneracy and retains the predeclared unsupported F H-twin/optional independent-donor policy. These fixes remain in the A2 layer; no canonical A1 source change was required.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider
```

Observed: `26 passed, 1 warning in 28.25s` on mgnp; `25 passed, 1 skipped, 3 warnings in 27.12s` on base. The base skip is the explicit pinned NNsight hook requirement. The mgnp tiny hook test executed and passed. These commands also exercise the fixture-driven actual shell-wrapper dry run.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a2_review101_probes.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/a2_review101_probes.py
```

The independent probe constructs the existing fabricated inputs through `tests/test_a2_pipeline.py`'s `inputs.__wrapped__`. It makes D and I memberships equal in every source, rebuilds their typed algebra and comparison hashes, freezes groups through the real A1 sidecar checks, and emits the exact expected synthetic row domain. Empty-patch rows retain intact margins and set `gate_valid=False`, `degenerate=True`. It supplies the complete positive-control key domain and runs real `summarize` with a small diagnostic bootstrap. The unsupported rows are introduced one at a time after a valid empty baseline.

Both interpreters exited `0` and printed:

```text
empty valid failed_necessity_empty_group True False
empty REQUIRED zero unsupported failed_necessity_empty_group True False
empty REQUIRED H-twin unsupported failed_necessity_empty_group True False
scalar vectors + WRONG_OWNER + unrelated row provenance accepted
```

The last line is a supplementary pure-validation probe: the bank contract currently checks only selected aggregate provenance fields. The blocking bank finding does not depend on the owner/provenance changes; the genuine-bank tiny-hook test below isolates scalar width alone.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a2_review101_scalar_hooks.py
```

This probe uses the same tiny randomly initialized CPU model setup as the scoped hook test, collects actual banks with the real collector, changes only every value vector to `[1.0]`, retains genuine contract/provenance, publishes through the A2 artifact writer, and calls actual A2 scoring. Observed exit `0`:

```text
real collected widths [64]
scalar replacement score accepted {'rows': 621, 'expected': 621, 'positive_controls': 36}
```

```bash
bash -n scripts/jobs/specificity_a2.sh
```

Observed: exit `0`. No broad suite or production model execution was run.

Scoped closure commands ran only the covering shape/readiness regressions, the positive tiny-hook path, the affected bank contract and the CPU dry run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider -k 'typed_bank_rejects or empty_group_requires or tiny_actual_hooks or bank_contract_exact or cpu_cli_dry_run'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider -k 'typed_bank_rejects or empty_group_requires or tiny_actual_hooks or bank_contract_exact or cpu_cli_dry_run'
```

Observed: `21 passed, 23 deselected, 1 warning in 22.15s` on mgnp; `20 passed, 1 skipped, 23 deselected, 3 warnings in 24.63s` on base. The base skip is the known pinned NNsight hook requirement.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a2_review101_closure_probes.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/a2_review101_closure_probes.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a2_review101_closure_scalar_hooks.py
```

These adapt the original independent probes only to catch the expected scalar rejection. Both pure-contract runs exited `0` and printed:

```text
empty valid failed_necessity_empty_group True False
empty REQUIRED zero unsupported blocked_uninterpretable False False
empty REQUIRED H-twin unsupported blocked_uninterpretable False False
scalar vectors REJECTED nonfinite/malformed bank vectors or wrong typed shape
```

The tiny-hook replay exited `0`, collected genuine banks, and rejected the malformed bank before scoring:

```text
real collected widths [64]
scalar replacement REJECTED before scoring nonfinite/malformed bank vectors or wrong typed shape
```

A metadata-only production-path check used `HF_HOME=/work/nvme/beto/swong2`, offline flags and mgnp, calling `model_geometry_receipt` for `meta-llama/Llama-3.1-8B-Instruct` at revision `0e9e39f249a16976918f6564b8830bc894c89659`, with `injected=False`. It exited `0` and obtained hidden size `4096`, head count `32`, layer count `32` and head dimension `128` from the local pinned configuration. The config file hash was `29e4c210b0d6ac178b16b2a255a568bdb23b581e50ca1ef6a6d071dd85704e6e`. No weights were loaded.

## Execution evidence

Local CPU software evidence only. The scoped pytest commands, both pure counterexample commands, tiny-hook counterexample and shell syntax check all exited `0`. Test counts and tiny scoring row/control counts are recorded above. The tiny baseline collected real per-coordinate bank vectors; the scalar replacement then scored with unchanged source contract and complete expected rows. This is an admission counterexample, not scientific replication. No scientific baseline metric or production training/ladder run is claimed; a scientific `run_manifest.json` is not applicable to these fabricated CPU fixtures. Production science remains not yet verified.

Live `/u/swong2/.local/bin/codex-usage --pause-at 80` returned `status: ok`, weekly `used_percent: 30`, `remaining_percent: 70`, `should_pause: false`, reset `2026-11-06T16:07:41+00:00`.

Closure execution evidence: every focused command and independent replay above exited `0`. Positive tiny-hook behavior remained passing, valid empty-patch necessity failure was retained, and the former malformed-bank/unsupported-control cases now reject or block. Production metadata was read without model execution. These are software contract checks; no scientific baseline reproduction, outcome or final specificity claim is made.

## What is NOT done

No author-report reading, implementation edits, git, research-session state writes, Slurm/GPU execution, external API, model weights, notebooks, scientific outcome consumption, broad retesting or additional agents. The scoped closure accepts the bounded implementation fixes; production cost admission and scientific execution remain unperformed by this reviewer. Cost and GPU admission remain with the orchestrator. Existing A1 runner/metric/selection sources were used as references and were not edited.

## Open questions

No blocker remains within this scoped closure. Default: the orchestrator may integrate the A2-only fixes, retaining independent budget/source guards before any scientific execution. No threshold, membership or assessment-domain change is needed.
