# Hand-back: Offline same-item twin training materializer

Agent: Codex research worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a2.md`, Task 1. Status: held after a HOLD.

## What changed

Restart checkpoint: independent review `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/11-a2-materializer-review-handback.md` found that matched mode accepts unscored synthetic inputs, zero inversion threshold, inconsistent model identities and arbitrary source hashes. This blocker is accepted and remains unfixed. The lead requested a restart pause immediately after the worker read the review and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/a1-data-contract.md`. No production or test edits, test subprocesses, or partial fix processes were started in the resumed review-fix turn. The implementation below is the pre-review version; matched readiness must not be relied on until the blocker is fixed and re-reviewed.

Orchestrator commits these worktree files by explicit file list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_twin_training.py`: standalone private D/I Arrow materializer and offline CLI. It validates every source identity before matching, preserves recipient labels and source records, and selects only the same-item neutral clean reference.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training.py`: invalid-source, matching, provenance, optimization-mode, actual Arrow roundtrip, mask, and local-tokenizer checks.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/08-a2-materializer-handback.md`: this report. A hook copy also lives at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/08-a2-materializer-handback.md`.

There are no staged apply operations. No global registry, task, training objective, source data, or other worker files changed.

The public API follows the plan, adding optional `commit`, `input_paths`, and `validate_only` keywords. Explicit mapping JSON is `{task: {D: path, H: path, I: path, I_neutral: path}}`, accepted through `--input-paths`. Ordinary roots resolve the documented task names only. The manifest stores split IDs and order, source file/content/row hashes and schemas, source configs and thresholds, tokenizer identity, matched counts, attrition and strata. Dataset configs also contain exact prompt hashes, replacement spans, label semantics and caller provenance.

D uses `deceptive` and `honest` rows with `honest_twin_kind: neutral_clause`. I uses A1's `user_inversion` and `user_neutral`, `baseline_kind: matched_frame_neutral_request`, matching `request_id`, and exact `request_text` replacement. Its recorded clean request spans must agree with recomputed token spans. No unfinished A1 implementation is imported. Matched builds require full caller commit provenance and scored-source config thresholds/model identity. Raw derived A1 rows alone cannot become fleet-ready datasets.

The new corrupt prompt is always the donor's clean prompt. Nested `source_recipient` and `source_reference` preserve the original designation-swap prompts and metadata through Arrow. The label semantics say clean recipient `target` wins, neutral reference `distractor` wins, and donor labels do not enter the loss. Historical source margins are retained with an explicit historical-value marker. Token proofs use complete untruncated prompts, equal masks and readouts, and unchanged tokens outside the replacement. Explicit exceptions preserve validation under `python -O`.

## How verified

RED: initial tests failed because the materializer module did not exist. Later RED tests exposed independently matching D/I identity drift, missing neutral config metadata, and stale A1 request spans; each was fixed before final focused runs. The ordinary loader and Arrow serialization are exercised directly, including nested A1-style request spans and source hashes. Source bytes remain identical after builds.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training.py -p no:cacheprovider -q
```

Observed: `32 passed`. Log: `/tmp/a2-materializer-focused-mgnp.log`. This includes the real cached Llama tokenizer test, with no model load or inference.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training.py -p no:cacheprovider -q
```

Observed: `31 passed, 1 skipped`. Log: `/tmp/a2-materializer-focused-base.log`. Base lacks its own locally accessible tokenizer cache, so only the optional real-tokenizer check skips. The base warnings concern deprecated Hugging Face cache configuration.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training.py tests/test_inversion_v2.py tests/test_matched_honest.py tests/test_contingency.py tests/test_deception_tasks.py tests/test_mechanism_analysis_mean_bank.py -p no:cacheprovider -q
```

Observed before the final request-span test was added: `236 passed, 1 failed`. Log: `/tmp/a2-materializer-mgnp-tests.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training.py tests/test_inversion_v2.py tests/test_matched_honest.py tests/test_contingency.py tests/test_deception_tasks.py tests/test_mechanism_analysis_mean_bank.py -p no:cacheprovider -q
```

Observed before the final request-span test was added: `236 passed, 1 failed`. Log: `/tmp/a2-materializer-base-tests.log`. Both broader runs fail only `tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms`, the lead's known `120 >= 128` baseline mismatch. No unrelated fix was made. The final focused reruns exercise all changed behavior after source-schema and request-span tightening.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m dataset.build_twin_training --d-root data/datasets --h-root data/datasets --cohort timing-d-only --output-root /tmp/a2-materializer-real-validate-only --max-seq-length 120 --validate-only
```

Observed: exit success; no output root exists; `fleet_ready:false`. Full diagnostic log and returned build manifest: `/tmp/a2-materializer-real-validation.log`. Each original D/H task preserves every split ID. The source thresholds are read from each config, including H's own threshold.

Counts below come from `/tmp/a2-materializer-real-validation.log`.

| Task | Train | Validation | Test |
|---|---:|---:|---:|
| far_v2 | 200 | 200 | 1000 |
| sdr_v2 | 200 | 200 | 1000 |
| ser_v2 | 200 | 200 | 1000 |

## Execution evidence

Local CPU checks only; no cluster job, GPU, behavioral scoring or inference was run. Focused suites and full-source offline CLI exited successfully; the broader regression commands exited with the documented baseline failure. Row counts observed equal the source expectations in the table. The broader baseline reproduces the known default-length assertion `120 >= 128` in both environments, and the derived unchanged-suite total is 205 passing tests in each broader run.

Provenance: `/tmp/a2-materializer-real-validation.log` contains the returned manifest, source hashes, schemas and exact split IDs. No `run_manifest.json` with a full caller commit was supplied for this timing-only diagnostic. Scientific training results are therefore not yet verified; no scientific result is claimed. Matched production builds explicitly require the full caller commit.

## What is NOT done

Review fix remains entirely outstanding. On resume, write RED tests before changes to the owned materializer and test file. Require inversion threshold exactly `.7` or `.5`, neutral diagnostic threshold `.3`, common D/H/I/neutral model identity, and both I/neutral rows' canonical `source_row_hashes` equal actual joined original D/H rows. The canonical `_hash` matches A1's constructor: sorted compact JSON with `ensure_ascii=False`.

Then implement the frozen scoring receipt contract: config-relative non-escaping receipt and score paths, byte digests, exact receipt identity across arms, required full scoring commit/model/tokenizer/revision/precision/request-pool/scorer fields, split-disjoint unique score IDs including rejected IDs, complete retained-row membership, both arms and streams' exact canonical prompt hashes and honest/opposite words, finite native score values, inversion full-vocabulary `choice:b` and opposite-over-honest margin meeting its declared threshold in both streams. Baseline competence remains diagnostic. Do not accept a boolean readiness marker. Preserve timing-only D behavior. The contract file is the binding schema; do not invent an incompatible producer shape or import unfinished A1 builder code. The lead owns independent re-review after fixes.

No RED test for this review blocker has yet been written or run. All suite results below/above refer to the pre-review implementation. Re-run focused tests in both interpreters after the fix, then relevant regression suites if the change warrants it. No process remains running for this worker.

`Task 2` and `Task 3` are outside this worker's scope. No wrapper, pilot, mask training, fleet reservation, A1 scoring, empirical threshold selection, full real matched dataset, GPU or paid API request, notebook execution, or git operation occurred. Fixtures cover matched serialization and provenance; actual matched materialization awaits scored A1 I/neutral datasets with their config thresholds. No persistent training dataset was built; the real-data invocation was validation-only. The unrelated baseline failure remains open.

## Open questions

The accepted review blocker prevents matched-cohort acceptance. The user-requested restart pause is the only reason its fix has not begun. The orchestrator supplies the full source commit and explicit A1 input-path mapping when scored inputs exist. Default: keep timing-only diagnostics provisional and refuse matched builds until the source configs include task, condition, model, margin threshold and A1 baseline identity. Logs under `/tmp` are diagnostic evidence; preserve them separately if long-term raw logs are wanted.
