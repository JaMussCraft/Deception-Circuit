# Hand-back: Deterministic user-turn inversion construction

Agent: Codex implementation worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a1.md`, Task 1 only. Status: resolved.

## What changed

Files for the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_user_inversion_v2.py`: CPU-only deterministic `derive_pairs`, source-twin validation, user-role append, bounded padding search and full-token proofs.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/user_inversion_requests_v2.json`: frozen primary FAR, SDR and SER inversion and matched-frame neutral requests from the plan.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_user_inversion_v2.py`: structural, invalid-source, padding, source-score invalidation, optimized-Python refusal, SER wording and cached real-tokenizer acceptance tests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/06-a1-builder-handback.md`: this handback, mirrored to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/06-a1-builder-handback.md`.

No staged apply operation. No git was run.

`condition` is `user_inversion` or `user_neutral`; `baseline_kind` is `matched_frame_neutral_request`. Both arms retain literal neutral H `pressure`, with `honest_twin_kind=None`. Requests live only in the actual user turn. Labels inherit D for inversion and H for neutral. Source prior-balance text becomes `source_neutral_prompt`. Old margins, argmax, choices, answer-token readouts, scores and honest-instruction prompts cannot remain active new-condition fields; behavioral values move under pair `source_behavior`.

Pairs record explicit `request_inversion`/`request_neutral`, `request_id`, request hash, source D/H row hashes, source pressure, source behavioral metadata, padding counts and added tokens, stream token lengths, readouts, token spans and prompt hashes. Each row exposes request text/id, per-stream token spans, lengths/readouts and source hashes. Token spans are zero-based half-open, cover the space-prefixed complete padded request and exclude the role terminator/readout.

Padding counts range from zero through twelve for each permitted phrase on each arm. Search indexes cached standalone token lengths, then minimizes total added tokens, total repetitions, lexical text and count ties. Every chosen candidate passes the existing full-prompt clause assertion in both directions and both streams, plus each arm's designation-swap assertion. Equal physical padding is never evidence. Python `-O` raises explicitly before any construction, because reused assertions would otherwise disappear.

SER supports only stored wording B and both audit/lab stems, “The result you should check is” and “The reading you should check is”. Wording A is refused. Original relevance suffixes remain unchanged; pair metadata records that they may compete with the user request. New conditions retain the increased-position and wording/padding confounds; this construction makes no specificity claim.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/06-a1-builder-tokenizer-summary.json`: final tokenizer coverage and padding counts, equal on both interpreters.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` with the three BLAS thread counts set to one. No notebooks executed and no model loaded.

```bash
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_user_inversion_v2.py
```

Initial RED: thirteen failures because the module/request pool did not exist, in `/tmp/user-inversion-red.log`. Subsequent focused RED checks caught missing padding repetition priority and SER-A rejection (`/tmp/user-inversion-review-red.log`), inherited old score/readout fields (`/tmp/user-inversion-scores-red.log`), rejection of valid SER reading stem (`/tmp/user-inversion-stems-red.log`), and padding masking a duplicated unpadded request (`/tmp/user-inversion-duplicate-red.log`). Each was implemented after its failing test. The SER fake fixture uses equal-word-count requests to isolate stem validity from whitespace-tokenizer padding parity; the real frozen pool is tested with the actual tokenizer.

```bash
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -s -p no:cacheprovider tests/test_user_inversion_v2.py tests/test_inversion_v2.py tests/test_matched_honest.py tests/test_contingency.py tests/test_deception_tasks.py tests/test_mechanism_analysis_mean_bank.py
```

Observed: 223 passed and two failed in `/tmp/user-inversion-final-mgnp.log`. One is the documented baseline failure. The other was the artificial single-letter padding fixture described below.

```bash
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -s -p no:cacheprovider tests/test_user_inversion_v2.py tests/test_inversion_v2.py tests/test_matched_honest.py tests/test_contingency.py tests/test_deception_tasks.py tests/test_mechanism_analysis_mean_bank.py
```

Observed: 223 passed and the same two failures in `/tmp/user-inversion-final-base.log`. Base emits existing pandas, Transformers-cache and TensorFlow dependency warnings. Independent review caught that the padding-priority fixture used the one-character request `a`, which legitimately matched source prose after duplicate protection was added. The test now uses unique text `Quizzical`, preserving the six-word length gap and unchanged padding assertion. The production duplicate guard was retained. The direct tie-break/duplicate rerun passed both tests; log `/tmp/user-inversion-fixture-green.log`.

```bash
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed November 1 at 19:38 UTC: weekly spent 5 percent, remaining 95 percent; reset November 6 at 16:07 UTC; `should_pause=false`; reading saved in `/tmp/user-inversion-final-usage.json`.

```bash
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -s -p no:cacheprovider tests/test_user_inversion_v2.py
```

Observed after the fixture correction: 19 passed in `/tmp/user-inversion-final-focused-mgnp.log`.

```bash
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -s -p no:cacheprovider tests/test_user_inversion_v2.py
```

Observed after the fixture correction: 19 passed in `/tmp/user-inversion-final-focused-base.log`. Final focused checks exit zero on both interpreters; the broad-suite fixture failure is resolved.

## Execution evidence

- Local CPU pytest commands are quoted above; no Slurm job or model inference.
- Both broad suites retain the known baseline failure `tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms`: sequence length 120 versus required 128, as recorded in `/tmp/user-inversion-final-mgnp.log`. This is the same failure in the lead's original baseline. No unrelated fix was made.
- Real cached `meta-llama/Llama-3.1-8B-Instruct` tokenizer is required with `local_files_only=True`; missing cache fails acceptance rather than skipping it. Every source row is processed in every source split. Each task has 200 train, 200 validation and 1000 test rows; all are accepted with no construction rejections, totaling 4200 paired instances. Counts by request id and source pressure id, including rejection diagnostics, are printed as `REAL_TOKENIZER_DERIVATION` JSON in each final log and in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/06-a1-builder-tokenizer-summary.json`.
- FAR uses no padding. SDR inversion adds three “Please proceed.” repetitions and neutral adds one “Please use the stated response format.” repetition, totaling sixteen added tokens across arms. SER inversion adds one “Please proceed.” repetition, totaling three added tokens; neutral adds none. These choices hold across every split and source pressure.
- Baseline comparison is software-only: the known failure remains 120 against 128 on each interpreter in `/tmp/user-inversion-final-mgnp.log` and `/tmp/user-inversion-final-base.log`; there are no new model behavioral baseline scores.
- No scientific `run_manifest.json` exists because scoring is out of scope and code is not committed by this worker. Experiment-level results are not yet verified. The orchestrator owns provenance at the later scoring stage.

## What is NOT done

Task2 scoring/filter/metrics, Task3 CLI/assembly/job wrapper, GPU/API work, model loading, threshold filtering, ladder interventions and scientific specificity inference are outside this ticket. The count above is construction coverage, not a behavioral survivor pool or the A1 success gate. No model/tokenizer revision or behavioral threshold is fabricated into pure derivation rows; these belong to later run/config metadata. Full-repository integration testing remains the lead's responsibility; this worker ran the named surrounding suites on both supported interpreters.

## Open questions

None blocking Task1. The lead can begin independent review and later stages using the frozen row schema above. Default: retain the documented baseline failure and all construction/position/wording caveats.
