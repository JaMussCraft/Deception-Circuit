# Hand-back `65`: A3 design scoped closure review

Agent: Codex independent reviewer. Ticket: A3 Task `1`, closure of report `61`. Status: resolved; no remaining blocker in the reviewed CPU scope.

## What changed

Only the assigned report was written, in the worktree and primary copies:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/65-a3-design-rereview-handback.md`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/65-a3-design-rereview-handback.md`.

**Finding A closed.** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_pipeline.py` now constructs a separate canonical source lookup rooted at the explicit A1 repository. It handles relative A1 paths and absolute matched paths, rejects aliases with conflicting digests, and does not replace the immutable original parent fields. `_validate_parent_files` uses the same lookup. The real source-path comparison passed from an unrelated working directory, and the complete original A1 payload hash stayed unchanged.

**Finding B closed.** `_matched_rows` calls the existing A2 `_stored_rows` validator before extracting memberships. That validator independently hashes source files and records, checks exact split counts and ordered IDs, and checks actual top-level recipient/reference prompts, labels, token-proof linkage, orientation and donor metadata against authoritative source rows. Production `prepare` always supplies the tokenizer, so `_matched_rows` also recomputes `_pair` and requires the stored proof and label semantics to match. The optional no-tokenizer fixture seam does not bypass this production path. New mutations reject top-level clean/corrupt prompts, target/distractor, orientation and proof changes. This closes the previous acceptance reproduction without editing A2 files in this task.

**Question coverage limitation addressed.** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_design.py` uses the existing segmentation resolver and validation on each condition's actual prompt. The resolver gives question-frame tokens priority after item mentions and response material have been separated; the new fixture checks item exclusion. Corrupt streams use their own prompt and honest designation; no D index is reused in I. Unsupported resolution still yields empty positions. Real representative questions now resolve in every sampled condition, including F and both user conditions.

**Bootstrap ambiguity closed prospectively.** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md` and the frozen policy now specify canonical D pressure wording, cluster draws with replacement, complete cluster membership, multiplicity weights normalized to sum one, no fixed-row truncation or instance fallback, and expanded/unique/effective size reporting. The constrained-mask family keeps the complete matched cohort. This review accepts the recorded policy; the later numerical implementation still needs its own review.

Original parent identity/full task scope/selection completion, fixed assessment membership, exclusion minima, semantic unsupported handling and metadata-only nuisance fitting retain the previously reviewed contracts. No new findings in this scoped closure.

## How verified

Both commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_a3_design.py tests/test_a3_pipeline.py
```

Observed stdout:

```text
42 passed in 12.03s
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_a3_design.py tests/test_a3_pipeline.py
```

Observed stdout:

```text
42 passed, 1 warning in 14.27s
```

The warning is the existing pandas/bottleneck version warning. The scoped suites retain the subprocess optimized-Python rejection test and add path-alias, materialized-field mutation, question-bin and cluster-policy regressions.

Independent representative check, executed with `/tmp` as the working directory:

```bash
PYTHONPATH=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false /u/swong2/.conda/envs/mgnp/bin/python -u /tmp/a3-review65-real.py > /tmp/a3-review65-real.log 2>&1
```

Observed exit zero. Exact diagnostic source and raw output are `/tmp/a3-review65-real.py` and `/tmp/a3-review65-real.log`. It loaded the actual A1 parent/selection, checked original source files and all matched source-path links, loaded only the cached tokenizer, recomputed the first actual D and I training row proofs per task, and checked all conditions in both streams for the corresponding representative rows. These are sample coverage checks, not full-cohort coverage estimates.

Observed raw evidence includes `CANONICAL_ALL_MATCHED_SOURCES_OK`, `PARENT_UNCHANGED`, and supported `4/4` semantic twin maps per task. All sampled `30/30` question bins resolved; each FAR question frame has `7` tokens, SDR `9`, SER `10`. All designation/readout positions resolved. F's absent pressure clause remains explicitly unsupported. The parent hash was compared before and after every independent operation.

An initial invocation from `/tmp` without an explicit import path failed with `ModuleNotFoundError`; rerunning with the explicit worktree `PYTHONPATH` produced the successful evidence above. This was a diagnostic command setup issue, not a code finding. I inspected the prior raw diagnostic script supplied by root but did not read author report `63` or rely on its reported full `prepare` outcome.

Reviewed file SHA256 identities:

```text
a3_design.py 8933a9b8461bfa68f6348bbbbc73bde8954dfcf74bd3fe90d9946861afd40f9a
a3_pipeline.py 3606a8e27b9055ceef9d4fdf3fdaef0bbbc6cfba471f230fd118a13b9eabdbd6
test_a3_design.py 785a263be4f5ae524e99772c5b0607a15e517d7a36758146c58d1037cecb8735
test_a3_pipeline.py 0ac60ae328fe061c8972521dcbe40461258fd217b8845b259119f974336b2750
reused scripts/twin_training.py 6707caff04a961d7848031d412c139a33918d902d1e8ba87c0c3dbd2df85a341
reused dataset/build_twin_training.py 381e8d9a0221caf6b16c594e94a8056a673f3167d35da5df6e1fa686f8f62367
```

## Execution evidence

- Job and cluster: local CPU pytest and the independent diagnostic command above; no Slurm or model weights.
- Exit code: both test commands and the corrected real-data diagnostic zero; initial missing-import-path diagnostic one.
- Counts: `42/42` tests passed on each interpreter. Independent actual-row proof recomputations covered `6/6` selected rows; representative condition/stream coverage was `30/30`.
- Baseline comparison: `42` passing on mgnp against `42` passing on base. No scientific intact or intervention baseline was run.
- Provenance: existing worktree A1 `outputs/_analyses/specificity-ladder/ladder-0253f49/selection_run_manifest.json`, parent commit `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`. Raw local diagnostic evidence is under `/tmp` as linked above. No new scientific `run_manifest.json` is claimed.

## What is NOT done

No code changes, git, GPU/API/model-weight use, notebook execution, subagents, production A3 freeze, or fitting. I did not independently rerun whole-cohort `prepare`; the scoped real check covers the repaired path join and representative actual builder proofs/maps directly. Raw `/tmp` diagnostics are review evidence rather than production artifacts and may be ephemeral. Later activation nuisance directions, model-based inference, direction/nulls, bootstrap numerics and mask implementation remain outside this review.

Declined to judge: later-task numerical behavior and full scientific outcomes, because this ticket is CPU closure; complete future assessment semantic coverage, because only representative real rows were sampled here.

## Open questions

None blocking this scope. Default: root may finalize CPU preparation after its own whole-cohort checks, preserving this review's exact code identities and future per-task review gates.
