# Hand-back 63: A3 real-input validation and source-derived question frames

Agent: Codex worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/61-a3-design-review-handback.md`. Status: handed-back.

## What changed

Files for the orchestrator to review and commit:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_pipeline.py`: separate canonical source-hash comparison lookup rooted at the explicit A1 repository; conflicting aliases rejected; parent files and original path/hash identities retained unchanged. Parent-file validation also resolves relative paths against this root. Actual Arrow validation now reuses the existing reviewed `scripts.twin_training._stored_rows` over the entire matched membership. Production preparation additionally recomputes each materialized builder token proof with `dataset.build_twin_training._pair` and checks label semantics. Existing A2 runtime files were not edited. The preparation result retains the validator file digest and explicit A1 root.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_design.py`: question frames come from the existing source-aware `resolve_segmentation` and `validate_segmentation` helpers. Their established priority removes item mentions and the response line before claiming the question frame. Each condition and stream uses its own original prompt and checked source metadata; F uses the checked D scaffold metadata with its own unchanged F prompt and absent pressure clause. No new regex, entire-user-turn question approximation, cross-condition index reuse or fabricated correspondence was introduced. Unsupported reconstructions still retain empty positions. The accepted cluster-bootstrap policy is frozen in the design: sample the eligible number of canonical D-wording clusters with replacement, carry every member ID, normalize member multiplicity weights to sum one, report expanded/unique/effective sizes, and prohibit truncation or instance fallback. No fitting algorithm was added.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_pipeline.py`: canonical relative/absolute aliases from another cwd, conflicting aliases, and top-level materialized clean/corrupt prompt, target, distractor, orientation and proof tampering.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_design.py`: existing-segmenter question frame equality, exclusion of item mentions, and the frozen cluster policy.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/63-a3-design-fix-handback.md`: this report, copied identically to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/63-a3-design-fix-handback.md`.

No staged apply operation or git command was used. A1 parents and A2 runtime code were not modified.

## How verified

New regressions were run before implementation: nine failed and the previous 33 passed. They reproduced absent canonical lookup, accepted top-level materialized tampering, missing question frames and absent cluster policy.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py -p no:cacheprovider -q
```

Observed: 42 passed in 11.81 seconds, exit zero.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py -p no:cacheprovider -q
```

Observed: 42 passed in 14.66 seconds, exit zero. Base emitted the existing pandas/bottleneck dependency warning. The optimized-Python mapping regression remains included.

The following model-free invocation ran with cwd `/tmp`, using the actual completed A1 parents, actual matched materialized data, and the cached tokenizer; it did not write a production artifact:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3-real-prepare63.py > /tmp/a3-real-prepare63-mgnp.json
```

The diagnostic script adds the absolute worktree root to `sys.path`, obtains the model/tokenizer revision from the existing A1 artifact, loads only the cached tokenizer through `common.load_tokenizer`, and calls:

```python
result = prepare(
    a1_design=ROOT/'outputs/_analyses/specificity-ladder/ladder-0253f49/design.json',
    a1_selected=ROOT/'outputs/_analyses/specificity-ladder/ladder-0253f49/selected.json',
    matched_root=ROOT/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07',
    historical_csv=ROOT/'docs/research/mechanism-analysis/phase3/a_prime.csv',
    root_ruling=ROOT_RULING_V1, tokenizer=tokenizer,
    a1_repo_root=ROOT, output=None,
)
```

Here `ROOT` is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. The temporary stdout file contains source-loader logging followed by the diagnostic JSON summary. The process exited zero; measured preparation elapsed time was 218.487 seconds, including cached tokenizer loading.

## Execution evidence

- Job and cluster: local CPU commands above; no Slurm, GPU, pretrained weight load, model inference, API or notebook.
- Exit status: zero for both test suites and the actual model-free preparation.
- Test counts: 42 passed against 42 collected on each interpreter.
- Actual cohort counts and full semantic coverage, derived from the returned design:

| Task | Eligible fit | Eligible selection | Fixed A1 assessment | Supported twin maps | Question coverage per condition |
| --- | ---: | ---: | ---: | ---: | ---: |
| FAR | 177 | 177 | 100 | 1816 / 1816 | 908 / 908 |
| SDR | 187 | 187 | 100 | 1896 / 1896 | 948 / 948 |
| SER | 168 | 167 | 100 | 1740 / 1740 | 870 / 870 |

Question coverage is the count of supported condition/ID/stream records for each of D, H, F, I and user-neutral separately. The summary contained no unsupported question examples. The values are arithmetic over the returned access rows; they are not behavioral scores. There were 100 eligible seed-2 IOI validation rows.

- Baseline comparison: fixed A1 assessment membership remained 100 against the required 100 in every task; no new assessment draw occurred. No scientific model baseline was run or claimed.
- Parent provenance: the existing A1 completion manifest under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-0253f49/selection_run_manifest.json`, naming commit `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`.
- Returned parent payload digests: prepared `883e0c25418a9216c11244d444c91ec0a2664b152d27c0aff5cfd3f28b00ca2f`; selected `e110f879d97540df6fa8374f87569e708d69cf18b623ad515aea83a900423dc2`; enriched matched manifest `437a64bc472fc742aeef4f4b0dc1affe2e5dd4d71a2ab20d502fadffa5fb3131`.
- Local diagnostic evidence: `/tmp/a3-real-prepare63.py` and `/tmp/a3-real-prepare63-mgnp.json`. These are temporary validation evidence, not a scientific run receipt or a production A3 artifact. No scientific result is claimed.

## What is NOT done

- No production `a3_design.json` was written. Root review and the real root-ruling object remain required before root chooses to freeze it.
- No direction, neutral-frame activation direction/cosine, neuron, edge, gradient, mask, bootstrap fitting or scoring algorithm was implemented or run.
- The real preparation check ran on mgnp; base coverage is the complete CPU test suite. It was not a second full real preparation.
- No A1/A2 source or immutable parent artifact was rewritten to add path aliases or repair materialized rows. Invalid rows fail rather than being repaired.
- No Slurm, model-weight load, API, notebook, protected-set scoring, benchmark run, budget change or git operation occurred.

## Open questions

- Root should independently review this correction before production freezing. Default: preserve the versioned ruling, exact A1 identity/full scope, original assessment membership and accepted cluster multiplicity policy.
- Later Task 2 must implement and report the frozen variable-size cluster fit, including expanded/unique/effective sizes. Default: no cluster truncation, fixed-row draw substitute or per-instance fallback.
- Unknown future scaffold variants or unavailable exact segmentations remain unsupported. Default: retain explicit coverage reasons rather than infer spans from punctuation or approximate token positions.
