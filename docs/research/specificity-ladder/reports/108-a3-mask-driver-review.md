# Independent mask driver review

Agent: independent Codex reviewer. Session: `codex-01a1987e`. Status: handed-back.

## What changed

Review only; no application source, shared runtime, registry, scheduler or git mutations. The orchestrator may commit `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/108-a3-mask-driver-review.md`. A primary mirror and required handback copy accompany it under `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`.

**Independent spec verdict: request changes. Independent code-quality verdict: request changes.** The load-bearing blocker is missing typed H-bank validation. Production admission remains closed.

**B1 — malformed H-mean vectors silently become scientific interventions.** In `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_mask_pipeline.py:303`, `torch.as_tensor(mean_bank[key]).expand_as(original)` accepts scalar or singleton lists and broadcasts them across a head or entire MLP output. Bank reuse in the same file at line `1129` checks declared source/runtime/base identity but does not check vector geometry, exact required support, duplicates or finite values. Final intake at line `1379` checks declared source/profile fields but also omits vector validation. Declared geometry does not authenticate actual vector shape.

Reproduction: `/tmp/a3_mask_review108_probe.py` creates a genuine tiny native H-bank, replaces every value with `[0.0]`, publishes a completed bank, runs the complete crossed assessment and passes `validate_assessment_result`. The singleton vectors are accepted for independently known head width `4` and MLP width `8`. Both interpreters print `BUG_MALFORMED_BANK_ACCEPTED`; see `/tmp/a3-review108-probe-mgnp.log` and `/tmp/a3-review108-probe-base.log`. This is a completed malformed artifact, not merely an exception-path concern.

Required fix: validate unique exact typed support, valid layer/head/whole-MLP keys, exact flat vector lengths from authenticated actual model geometry, finite numeric values, original source counts/domain and current numeric/base identity before any bank reuse or intervention; repeat the applicable checks at final assessment intake. Reject scalar/broadcastable malformed arrays. Add focused regressions for malformed vectors, duplicate/missing/extra entries and changed geometry/profile. Preserve the reviewed mask objective and all frozen cohorts.

The fixed scheduling, validation-only selection, completed-history anchor, JSON checkpoint boundaries, typed random controls, original-H recollection, descriptive transfer and read-only reference lineage are coherent in the inspected source. Wrapper deployment checks pass on the refreshed copied-Slurm-script version. No second concrete blocker was found in this owned consumer scope.

## How verified

Read the accepted Tasks `1`, `5`, `6`, operational and pilot ruling JSONs, exact source diff, adjacent hash JSON, numerical consumer interfaces, workload, tests and wrapper. Author report `102` and author handoff prose were excluded. Exact diff reconstruction and live hashes match the supplied four-file package; see `/tmp/a3-review108-adversarial-corrected.log`. Shared runtime was checked at frozen SHA256 `16f069ca5d314ab1f9ceccaad57baf64b1ef811c932bb0e7c7851c61e4d976c8`.

All following commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`; standalone probes also used `PYTHONPATH="$PWD"`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_mask_review108_probe.py
/sw/external/python/anaconda3/bin/python3.9 /tmp/a3_mask_review108_probe.py
```

Both exit `0`. Logs `/tmp/a3-review108-probe-mgnp.log` and `/tmp/a3-review108-probe-base.log` show actual native `200` updates, ten scheduled immutable validations, disk continuation from update `100` to `200` with exact core fingerprint equality including gate/Adam/RNG state, complete assessment and summary, B1 reproduction, and rejection of missing rows, missing positives and wrong purpose. The fit cannot access assessment rows because those rows were removed from the supplied fit design.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_mask_pipeline.py -p no:cacheprovider -q -k 'genuine_completed or cost_uses or source_adapter or changed_native or safe_checkpoint or spooled or clean_cluster or actual_module or selection_fail or inventory_binds or actual_validation_only_pilot'
/sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_mask_pipeline.py -p no:cacheprovider -q -k 'genuine_completed or cost_uses or source_adapter or changed_native or safe_checkpoint or spooled or clean_cluster or actual_module or selection_fail or inventory_binds'
```

Observed mgnp: `15 passed, 24 deselected in 28.43s`, `/tmp/a3-review108-target-mgnp.log`; base: `14 passed, 25 deselected, 3 warnings in 45.99s`, `/tmp/a3-review108-target-base.log`. This deliberately targeted source, resume, caps, authority, inventory, offline metadata and wrapper seams instead of repeating the broad author suites. The mgnp pilot check actually executes both objective arms, every timing adapter and nonfinal receipt, and rejects reusing the disposable pilot model for scientific fitting.

```bash
/u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_mask_review108_adversarial.py
bash -n scripts/jobs/specificity_a3_mask.sh
```

Both exit `0`. The corrected adversarial probe rejects mask subcap overflow, global overflow, a consistent expired live allocation and wrong normalized job IDs; it reconstructs the exact package source. Log: `/tmp/a3-review108-adversarial-corrected.log`. An earlier exploratory harness modified the unused raw `job_id` field after normalization and failed its own assertion; it was corrected to modify `job_ids`, then passed. That exploratory failure is not a product finding; its original log is `/tmp/a3-review108-adversarial.log`.

The consumer requests validator-created process-local authority context before model loading and refreshes reservation authority at update/shard entry. Scope includes stage, seed/arm or task/group, source inventory, work directory, reservation, ledger and admission. Scope, current allocation, original charges and append-only successor safety remain properties of the separately owned shared-runtime dependency; these consumer checks do not constitute full independent acceptance of that runtime.

## Execution evidence

- Job and cluster: local CPU only; no Slurm job, GPU, large weights, remote API or notebook execution.
- Exit codes: both native standalone probes and both targeted pytest commands exit `0`; corrected adversarial probe and shell syntax check exit `0`.
- Row counts: `73` observed against expected `73` tiny assessment rows, `8` observed against expected `8` positive controls and `6` summary cells; both standalone logs above carry these outputs. Counts are derived from the complete tiny source design, not production cohort sizes.
- Baseline reproduces: native fit replay margin error `0.0` against exact replay expectation `0.0`, with recorded acceptance tolerance `1e-05`; exact final resumed core-state fingerprint equals uninterrupted fingerprint. The tiny specificity selection fails and correctly selects the last scheduled checkpoint; no scientific success is inferred.
- Provenance: `/tmp/a3-review108-r5qw_yek/fit/run-manifests/fit-1793603898414971994/run_manifest.json` and `/tmp/a3-review108-r5qw_yek/runs/assess-1793603903411467278/run_manifest.json`. These expressly contain `injected: true` and `commit: null`; this CPU review is not scientific execution provenance. Source identity instead comes from the supplied exact diff and four-file SHA256 package under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/`.
- Temporary complete-flow artifact roots: `/tmp/a3-review108-r5qw_yek` and `/tmp/a3-review108-xe6wo788`. The standalone script, logs and immutable JSON boundaries remain available for root/author reproduction.

## What is NOT done

No source fix or production acceptance. No GPU timing, native BF16 measurement, production reservation, model fit, protected archive scoring, complete production cohort assessment or scientific verdict. The tiny flow exercises an actual complete trained run, disk resume, assessment and reporting primitives; it does not claim the full six-run production fleet or root CLI admission. No new review of the already accepted numerical core. No full independent review of `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_runtime.py`; that remains separately pending. Author-reported broad test results were not substituted for reviewer execution.

## Open questions

Root should route a bounded B1 bank-validator correction and request scoped independent re-review of its reuse, intervention and final-intake paths. Default: keep scientific execution closed until that correction and the separate shared-runtime review pass. Preserve this pinned-package review as the pre-fix evidence. Root alone decides production admission and commits by explicit file list.
