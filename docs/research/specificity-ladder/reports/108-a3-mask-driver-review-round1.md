# Independent mask review: B1 correction round

Agent: independent Codex reviewer. Session: `codex-01a1987e`. Status: handed-back.

## What changed

**Independent spec verdict: PASS for scoped B1 closure. Independent code-quality verdict: PASS for this correction.** No remaining concrete blocker was found within the fix-only scope. These verdicts close B1 from `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/108-a3-mask-driver-review.md`; the original failure report and original reviewer reproduction are preserved. This is not shared-runtime acceptance or production admission.

Reviewed exact correction package `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/mask-review108-round1.diff` and adjacent `.sha256.json`. Pipeline SHA256: `d082395ff1a97e9fa825a7dd1c4a36e9ebb6b2fa0738a726b7ebc6fffa97b246`; tests SHA256: `5f2bfd0b5dd0bbfba9e7add96073d9a75695ec8aa04eb4cd4dfa8e39f075aa87`. Wrapper/workload and accepted numerical core are unchanged. The shared-runtime dependency was inspected only as needed and remained at `691c258d8a46140eef0c4407cf8f06a8f36890d475fe3320fdb19fe2326d9871`.

The correction validates exact unique typed support and bounds, flat finite vectors with independently expected width, representability in the actual dtype, ancestral IDs/counts/domain, pooling/padding profile, and runtime/base identity. It validates collection before publication, reuse before intervention, direct exported H-mean hooks and completed CPU final intake. Native preparation binds fixed native geometry; collection and reuse compare actual model geometry. CPU final intake obtains model proof from the immutable execution manifest and checks its base identity against measured admission before validating vectors against preparation geometry. Bank-declared dimensions cannot authorize themselves. Injected tiny geometry is captured separately from the actual model and is barred from production admission by the existing canonical path.

Reviewer changes are documentation only: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/108-a3-mask-driver-review-round1.md`, its primary mirror, and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/108-a3-mask-driver-review-round1-handback.md`. Root owns source changes and commits. Author report `102` was not read.

## How verified

All CPU commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`, with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`. Standalone probes additionally used `PYTHONPATH="$PWD"`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_mask_pipeline.py -p no:cacheprovider -q -k 'exported_h_mean_rejects or assessment_rejects_invalid_bank or final_intake_rejects_completed or valid_bank_preserves or bank_reuse_checks or cpu_bank_geometry or final_intake_revalidates or actual_native_assessment or actual_validation_only_pilot'
/sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_mask_pipeline.py -p no:cacheprovider -q -k 'exported_h_mean_rejects or assessment_rejects_invalid_bank or final_intake_rejects_completed or valid_bank_preserves or bank_reuse_checks or cpu_bank_geometry or final_intake_revalidates or actual_native_assessment or actual_validation_only_pilot'
```

Observed independently: mgnp `51 passed, 37 deselected in 14.77s` ([mgnp test log](/tmp/a3-review108-round1-selected-mgnp.log)); base `51 passed, 37 deselected, 3 warnings in 24.45s` ([base test log](/tmp/a3-review108-round1-selected-base.log)). Both exit `0`. The scoped checks include actual native assessment, valid empty removal and the actual validation-only pilot; no broad unrelated suite was rerun.

```bash
/u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_review108_round1_counterexamples.py
```

Exit `0`, `/tmp/a3-review108-round1-counterexamples.log`: a valid completed CPU final intake passes while model access is replaced with an assertion; `16` independent counterexamples reject. Cases include scalar/singleton/nested values, finite host values overflowing the model dtype, duplicate/extra/missing support, boolean key coordinates, ancestral ID/count changes, wrong pooling, runtime/base/geometry changes and joint proof/preparation geometry redeclaration. This supplements rather than merely observes the new author tests. [Independent counterexample log](/tmp/a3-review108-round1-counterexamples.log).

```bash
/u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_review108_round1_flow.py
/sw/external/python/anaconda3/bin/python3.9 /tmp/a3_review108_round1_flow.py
```

Both exit `0`: `/tmp/a3-review108-round1-flow-mgnp.log` and `/tmp/a3-review108-round1-flow-base.log`. I independently adapted `/tmp/a3_mask_review108_probe.py` only to use the correction hashes and require rejection of the original malformed bank. `/tmp/a3_review108_round1_prepare.py` records that adaptation; the original probe remains unchanged. Both new runs complete actual native `200` updates and ten validation checkpoints, resume from disk at `100` to identical gate/Adam/RNG state at `200`, and complete `73` assessment rows, `8` positive controls and `6` summary cells. The original B1 now prints `ORIGINAL_B1_NOW_REJECTED`. Missing coverage, missing positives and wrong-purpose results still reject. [mgnp full-flow log](/tmp/a3-review108-round1-flow-mgnp.log), [base full-flow log](/tmp/a3-review108-round1-flow-base.log).

The original supplied source package was independently reconstructed under `/tmp/a3-review108-round1-packet-4ip1v3__`; `patch -p1` applied only the correction diff there, and both resulting files match the new hash JSON and live source byte for byte. No git command or source mutation was used.

## Execution evidence

- Job/cluster: local CPU only, tiny randomly initialized native models. No scheduler job or production model access.
- Exit codes: both scoped test runs, both complete native flow runs and the independent counterexample script exit `0`.
- Rows: `73` observed against expected `73`; `8` observed against expected `8` positive controls; `6` summary cells. Complete schedule and assessment outputs: [mgnp](/tmp/a3-review108-round1-flow-mgnp.log), [base](/tmp/a3-review108-round1-flow-base.log).
- Baseline reproduces: replay margin error `0.0` against expected `0.0`, recorded tolerance `1e-05`; disk-resumed final gate/Adam/RNG fingerprint exactly equals uninterrupted state. Selection correctly fails the tiny specificity gate and selects the last scheduled checkpoint, without shortening training. [Baseline manifest](/tmp/a3-review108-mjj7aulx/fit/run-manifests/fit-1793606121567225753/run_manifest.json), [exact-state continuation log](/tmp/a3-review108-round1-flow-mgnp.log).
- Provenance: `/tmp/a3-review108-mjj7aulx/fit/run-manifests/fit-1793606121567225753/run_manifest.json` and `/tmp/a3-review108-mjj7aulx/runs/assess-1793606127388395736/run_manifest.json`; both expressly have `injected: true`, `commit: null`. These are CPU review evidence, not scientific provenance. Frozen source identity is the exact correction package and hashes above.
- Artifact roots: `/tmp/a3-review108-mjj7aulx` and `/tmp/a3-review108-ahqlhiv1`; counterexamples: `/tmp/a3-review108-round1-counter-8e_5qhx5`.

## What is NOT done

No source edits, broad core re-review, git, RS mutation, GPU or large-weight work, paid API, notebook execution, scheduler work or delegated agents. No scientific mask result, native BF16 pilot, measured production admission or full production fleet. No full independent acceptance of the separately owned shared runtime. The existing CPU/injected limitations and original review boundaries still apply.

## Open questions

No unresolved question within B1. Default: accept this bounded correction and retain the original report as historical failure evidence. Root alone combines this consumer verdict with the separate shared-runtime review and decides source integration and production admission.
