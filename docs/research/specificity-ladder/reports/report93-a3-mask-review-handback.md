# Hand-back report93: Independent A3 mask numerical-core review

Agent: Codex Sol reviewer. Ticket: A3 Task 5a in the accepted plan. Status: handed-back.

## What changed

Initial review verdict, superseded by the closure re-review below: request changes for two gaps in the promised exactness guards. Ordinary numerical, replay, eligibility and export cases pass the focused CPU checks. No implementation or test source was edited, and the author report was not read.

- Medium, chunk mutation is accepted during an update. At `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_mask.py:432`, chunk bytes are fingerprinted once. The `unchanged()` guard at `line 446` checks model parameter versions, gate buffers and modes, but never rechecks cohort contents. The reproducer changes an I baseline margin by `100` during the first D replay callback. All six forwards complete, the changed preservation target is consumed, and Adam steps successfully. This violates the frozen chunk/data contract and records the pre-mutation fingerprint for an update computed using changed targets. Enforce immutable cohort identity across the update, including targets, payload, ids, order and boundaries, and fail before stepping. Add this failure case beside the existing parameter/RNG mutation tests.
- Medium, exact resume does not bind all base computation settings. `_base_identity` at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_mask.py:614` hashes only named parameters. A destination with identical parameters, chunks, support and caller identity but final native RMSNorm epsilon changed from `0.000001` to `1.0` is accepted at restore and at the next update. With exactly the saved RNG, its next gate parameters differ from uninterrupted training by 0.01619124412536621 in both environments (`report93-mask-review-mgnp.log`, `report93-mask-review-base.log`). This epsilon is actually consumed by the FP32 differentiable readout. Bind effective base configuration and relevant non-gate buffers, or require and enforce a content identity that covers them; weights plus caller labels are insufficient for the present exact-source rejection claim. Guarding non-gate computation state throughout an update follows the same principle.

Commit by explicit file list from the worktree report directory `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/`: this handback, `report93-mask-review-repro.py`, its two environment logs, and `report93-mask-review-observations.txt`. Matching primary copies live under `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`.

**Closure re-review: accept the two fixes within Task 5a scope.** Cohort bytes are now authenticated before and after every callback and before Adam. Effective base identity now includes configuration, native module types and public runtime settings/tensors, non-gate buffers and numerical runtime settings, alongside frozen source parameters at checkpoint boundaries. The original target-mutation and changed-native-norm probes now reject; ordinary exact updates still pass. No new blocker was found in these fixes. This supersedes both initial medium findings above. No implementation source was edited by the reviewer.

Additional review artifacts in the same report directories: `report93-closure-repro.py`, `report93-closure-pytest-mgnp.log`, `report93-closure-pytest-base.log`, `report93-closure-repro-mgnp.log`, and `report93-closure-repro-base.log`.

## How verified

Commands below ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_a3_mask.py
```

Observed: 24 passed in 12.86 seconds, exit 0 (`report93-mask-review-observations.txt`).

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_a3_mask.py
```

Observed: 24 passed in 15.13 seconds, exit 0; three dependency warnings (`report93-mask-review-observations.txt`).

```bash
PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python -u docs/research/specificity-ladder/reports/report93-mask-review-repro.py
```

```bash
PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 -u docs/research/specificity-ladder/reports/report93-mask-review-repro.py
```

The reviewer-owned retained graph uses its own scalar loss and KL algebra, independent of `mask_objective`, while deliberately sharing the native forward. Both environments pass all six active/inactive/exact-kink by constrained/unconstrained cases, with paired streams and unequal chunks of two ids then one id. Every gate-tensor gradient, next parameter, Adam step and moments, and final CPU RNG agree; maximum gradient error is 2.9103830456733704e-11 (`report93-mask-review-mgnp.log`, `report93-mask-review-base.log`). The reproducer also prints the accepted target mutation, failed-update checkpoint rejection, and changed-base-epsilon resume divergence. An initial reviewer harness omitted the arm argument on the streamed call; that harness error was corrected before the evidence runs preserved here.

Code and the passing scoped tests establish the following bounded evidence:

- Canonical opposite-minus-honest margins; full-cohort difference-first suppression hinge; zero kink derivative; detached baseline margins, denominator and KL targets; full-cohort id weights and equal stream weights; fixed Adam defaults and one optimizer step; candidate-only removal regularizer with the required sign.
- Native eligibility hard-opens every noncandidate, including extreme logits. Base model remains eval/frozen while eligible gates train. A direct native-margin backward, without the regularizer, produces nonzero eligible gradients and leaves base parameters unchanged. FP32 readout casts the residual without detaching it and detaches only frozen norm/unembedding weights.
- D replay compares CPU and all-CUDA RNG snapshots, exact candidate gate samples and margins, model parameter/gate-buffer versions and training modes. It restores post-first-D RNG before I. CPU continuation is exercised; CUDA handling is inspected only.
- Export calls actual deterministic native gate forward and takes its complement. Tests exercise the probability-cutoff versus native-eval-cutoff interval and strict eval tie, all-retained, individual head/whole-MLP and all-candidate removals. Actual dual-stream D and I outputs agree with independent native donor-capture/patch hooks using the same condition's neutral donors; wrong-condition donors fail that comparison. Single-stream bypass is not used as evidence.
- Ordinary resume reproduces the next update exactly and rejects changed source weights, chunks, identity, support/eligibility, arm, objective epsilon, gap and Adam configuration. Both in-flight and failed-update checkpoints are rejected. These passing checks do not cover the two gaps above.

```bash
cmp l0.py /projects/beto/swong2/Alignment/Deception-Circuit/l0.py
cmp models/llama_node.py /projects/beto/swong2/Alignment/Deception-Circuit/models/llama_node.py
cmp models/_compat.py /projects/beto/swong2/Alignment/Deception-Circuit/models/_compat.py
```

Observed: all three native source comparisons exit 0 (`report93-mask-review-observations.txt`). No shared A1 runtime file was edited by this review. The primary checkout does not contain the worktree's new ladder runtime, so a primary comparison cannot establish its pre-review baseline; orchestrator source-list review remains necessary for that broader claim.

**Closure commands.** Same working directory and thread/environment limits as above; outputs are preserved in the closure logs.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_a3_mask.py
```

Observed: 43 passed in 16.35 seconds (`report93-closure-pytest-mgnp.log`).

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_a3_mask.py
```

Observed: 43 passed in 20.47 seconds (`report93-closure-pytest-base.log`).

```bash
PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python -u docs/research/specificity-ladder/reports/report93-closure-repro.py
```

```bash
PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 -u docs/research/specificity-ladder/reports/report93-closure-repro.py
```

The closure script preserves the independent six-case mathematical oracle unchanged, then asserts the new rejection and recovery behavior. Both environments retain maximum gradient error 2.9103830456733704e-11 (`report93-closure-repro-mgnp.log`, `report93-closure-repro-base.log`). The original I-target mutation rejects during D replay. The native RMSNorm substitution rejects without loading optimizer state; correcting the setting then restores the exact next update. An additional mutation after the final I forward rejects before Adam, preserving all gate parameters and pre-existing Adam moments exactly. The failed boundary rejects checkpoint creation and a subsequent update; restoring the saved valid boundary recovers the exact next parameters and CPU RNG. The expanded suite additionally covers target logits, payloads, token counts, ids/order, changed effective attention/configuration/rotary state, and changed completed checkpoint boundaries. No accepted objective or export semantics were reopened.

The same native-source comparison commands still exit successfully. Current reviewed mask SHA256: `255292d252caa7f8eda91e31f488f4dbd1f06814762ba90b86ffc547016a1c1f`; test SHA256: `8205a3b1642e53a4eb2eed4ab7eb75e08c7ad51038e5f6e7842991541a0b8ebd`.

## Execution evidence

- Job and cluster: local tiny CPU tests and the two local reviewer scripts above; no scheduled or production job.
- Exit code: both pytest commands and both final reproduction commands exit 0 (`report93-mask-review-observations.txt`).
- Counts: 24 observed tests against 24 expected in each environment (`report93-mask-review-observations.txt`); six observed oracle cases against six expected per environment.
- Baseline reproduces: retained and streamed gradients agree with maximum absolute error 2.9103830456733704e-11 against the chosen assertion tolerance `0.0000002` (`report93-mask-review-mgnp.log`, `report93-mask-review-base.log`); exact uninterrupted/restored next parameters and CPU RNG are exercised in the scoped suite. Changed native norm epsilon yields a difference of 0.01619124412536621 against the unchanged-source expectation of zero (`report93-mask-review-mgnp.log`, `report93-mask-review-base.log`).
- Provenance: report-local reproduction source and environment logs. Reviewed mask source SHA256 is `2b2afafdbf6ad455a70e1cc0146301f1c35da31db9793a5f269007e9be0aea09`; focused test SHA256 is `8daaa370d393ea7c3033c87b0a904dbf9ce4cc542df509b3dcafc518e01cb612`. No scientific run manifest or full-commit provenance was created; these are local implementation-review observations, not a verified scientific result.

Closure execution evidence: both scoped pytest commands and both closure reproducer commands returned exit `0`. Observed case counts are forty-three against forty-three expected tests per environment and six against six expected independent oracle cases. Baseline comparison remains exact next-update parameter/RNG equality against uninterrupted training. Evidence is in the four closure logs and reviewer-owned closure script named above; no scientific run or production provenance claim is added.

## What is NOT done

No source fix, broad suite, production weights, GPU/CUDA execution, Slurm work, API call, notebook execution, git command or subagent delegation. The full scientific driver, `200`-update budget, validation checkpoint selection, dataset/provenance admission, atomic on-disk checkpoint writes and scheduling remain explicitly deferred to Task 5b. The reviewer made no source fixes; the author changes closing both initial gaps were independently exercised in the closure re-review.

## Open questions

No open blocker remains from this scoped re-review. Default: accept the Task 5a guard fixes and retain the stated Task 5b and GPU/runtime limitations. These local checks do not replace later production resource and provenance admission.
