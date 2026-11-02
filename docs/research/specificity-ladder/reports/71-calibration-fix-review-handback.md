# Hand-back 71: Independent calibration fix review

Agent: Codex review worker. Status: handed-back.

## What changed

No production or test files were edited. This review writes only this report and its primary mirror:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/71-calibration-fix-review-handback.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/71-calibration-fix-review-handback.md`

Verdict: accept the narrow calibration change. No actionable implementation findings, at any severity, were found within the requested scope. This is bounded approval of the implementation and supporting diagnostic, not a complete GPU pilot pass.

The reviewed implementation is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/specificity_ladder.py`:

- Lines 312–329 add a singleton padding helper. It validates input geometry, rejects truncation and invalid widths, appends only zero-mask suffix positions, retains original prefix tokens and mask values, preserves tensor dtype/device, and retains readout/labels/records/task/choices through dataclass replacement. Equal widths return the original object.
- Lines 356–359 compute the maximum of the two original padded widths, then align both inputs before intact, donor, or patched capture. No parent padding is removed. Mapping remains explicit readout-to-readout.
- Lines 341 and 360–364 still use all sender keys, mapped sender replacement, the ordinary capture/readout path, and unchanged absolute and relative tolerance of `1e-5`. There is no READOUT receiver replacement or loosened comparison.

Baseline comparison used the orchestrator's exported original files in `/tmp/calibration71-baseline/`, from commit `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`, and `/tmp/calibration71-production.diff`. The only changed existing function AST is `positive_control`; `_pad_calibration_batch` is new. `score_cell`, `_capture`, `_noop_error`, and the other existing functions have identical ASTs. Generic hooks and the pipeline are byte-identical to their original exports and match the raw manifest's hashes.

Scientific effect scoring therefore retains its original path: `score_cell` captures intact, empty, replay, and patched recipient evaluations with the same recipient geometry and shared fp32 readout, and checks noops through `_noop_error`. It does not call the calibration padding helper. The existing real-model joint-group test compares this scoring path against a direct joint patch. Acceptance does not assume that padding is numerically neutral.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py tests/test_specificity_ladder.py tests/test_calibration_diagnostic_67.py tests/test_specificity_ladder_cli.py -q
```

Observed: exit 0; 118 passed in 27.18 seconds. The model module actually ran; it was not dependency-skipped. Its appended test at lines 166–198 observes real tiny-Llama native captures, requires common geometry for all captures, checks donor recovery in fp32/native logits and final residual, excludes READOUT from senders, and tests empty/self replay on both aligned inputs. Geometry tests cover dtypes, devices, absolute readouts, retained labels/records, equal-width identity, invalid widths, invalid masks, and singleton enforcement.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py tests/test_specificity_ladder.py tests/test_calibration_diagnostic_67.py tests/test_specificity_ladder_cli.py -q -rs
```

Observed: exit 0; 105 passed, 2 skipped in 23.45 seconds. Base has nnsight 0.5.12; the model module and one CLI test require pinned nnsight 0.7.0. These are dependency skips, not passing model coverage in base.

Additional direct Python checks parsed the raw JSONL, compared source bytes/ASTs against exported baseline files, and checked the diagnostic source SHA256 against its manifest. The diagnostic source hash matched. Calling `ladder_pipeline.validate_prepared` against the original immutable design and its original manifest arguments raised exactly `ValueError: stale design code/grader hash`. The old design remains rejected; no artifact identity was rewritten. The unchanged selection reader also retains its code-identity gate at line 474.

The synthetic geometry regression was also exercised against the original `positive_control` function bound to current module globals in process memory, with no production-file modification; its expected failure demonstrates that the geometry test distinguishes the old behavior.

## Execution evidence

This review submitted no jobs, loaded no pretrained weights, used no GPU, made no API calls, and ran no notebooks. The following is an independent reading of existing raw execution evidence, not a new model run.

- Job and cluster: diagnostic `23416716` on Delta. `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/calibration-diagnostic-0253f49/accounting.txt` records main and batch `COMPLETED`, exit `0:0`, elapsed 254 seconds. The diagnostic intentionally exits successfully after diagnosing its first original recovery failure.
- Row counts: raw `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/calibration-diagnostic-0253f49/pairs.jsonl` contains 105 `pair_started` and 105 `original` records against 120 expected pairs, one common-parent alternative, one common-unpadded alternative, and one summary. Original ordinals 0–103 pass; ordinal 104 fails. Fifteen original pairs were not scanned, and alternatives were tested only at the first failure.
- Baseline reproduces: the diagnostic's first failing pair has fp32 maximum absolute error `0.041628360748291016`, exactly against `0.041628360748291016` in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/logs/lad-a1-pilot-23415975.err`. It is task `ser_v2`, condition `I`, clean stream, instance `00b809b51070`, recipient/donor padded widths 128/129, unpadded widths 128/128, and both readouts 127.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/calibration-diagnostic-0253f49/run_manifest.json` names full original production commit `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`, pinned model/tokenizer revision, BF16, A100 hardware, diagnostic hash, code hashes, frozen design/selection hashes and job logs. Its `scientific_scoring` flag is false.

The original failing pair has native-logit error 0.0625 and final-residual error 0.25. Both equal-width alternatives recover donor fp32/native logits and final residual with exactly zero error. All four noops on each alternative pass with zero error; all original-pair production noop checks pass. Each failing/alternative record lists 1,057 sender keys, including embeddings and excluding READOUT.

The common-parent alternative uses widths 129/129 and preserves the donor reference exactly. It changes the recipient intact fp32 logits by 0.1021733283996582, native logits by 0.125 and final residual by 0.25 relative to original geometry. The common-unpadded alternative uses 128/128 and preserves the recipient reference, but changes donor fp32 logits by 0.17800521850585938, native logits by 0.25 and final residual by 0.1875. Argmax remains equal in these drift comparisons. This evidence supports the conservative common-parent geometry choice within calibration; it does not support changing scientific scoring geometry or claiming padding invariance.

Local test commands above exited 0. The expected baseline negative-control pytest run exits 1 internally and the wrapper requires that result. A live Codex reading at hand-back reported 20 percent weekly spent, 80 percent remaining, and `should_pause: false` at the requested 80-percent threshold.

The report-number checker was run. Its unresolved tokens were reconciled manually: report and source-line identifiers against the files above; test counts, durations, exit codes and dependency versions against this reviewer's command outputs; geometry, errors and sender count against the raw JSONL; expected totals against the summary; and the usage percentages against the live command output. The sender count is derived by taking the length of the recorded key list. No unresolved scientific quantity remains.

## What is NOT done

- No full production GPU calibration or scoring pass was run after this change. The diagnostic is bounded to the first original failure; it is not a 120-of-120 calibration pass.
- The tiny model checks real hook algebra in CPU float precision; they do not reproduce BF16 A100 kernel behavior. That numerical evidence comes from the existing raw diagnostic only.
- No claim about particular BF16 kernel internals is established. Shape dependence is supported by the controlled same-token alternatives; the precise backend cause remains an inference.
- No regeneration, commit, merge, scientific effect estimate, or findings-register change was performed. No author hand-back was read.

## Open questions

No code changes are requested. Default: accept this patch, commit it through the orchestrator, regenerate frozen provenance under the new full commit in a distinct artifact location, preserve old artifacts and their rejection, then run the authorized bounded pilot before asserting production success.
