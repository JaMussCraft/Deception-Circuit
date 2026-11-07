# Hand-back 59: A3 CPU design and A1 parent gates

Agent: Codex worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/task-1-brief.md`. Status: handed-back.

## What changed

Files for the orchestrator to review and commit from the existing worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_design.py`: pure split/site freeze, exact historical exclusion union, preserved assessment order, actual matched membership requirements, eligible unique fit/validation minima, GQA receiver deduplication, semantic boundary support, metadata confound table and train-only nuisance predictor, utility prompt/donor exclusions, fresh registry checks.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_pipeline.py`: original-identity A1 parent loader through `ladder_pipeline.read_artifact` and `read_selection`, retained completion sidecar/file hashes, CPU preparation API, source/Arrow membership adapter, exact tokenizer/source checks and builder-verified twin maps. Preparation never redraws assessment rows. The future stage CLI belongs to Task 6.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_design.py`: injected pure-parent tests and byte/word/BPE tokenizer contracts.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_pipeline.py`: real A1 completion-sidecar fixtures, original identity/full scope, actual matched-source adapter and optimized-Python regression.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/59-a3-design-handback.md`: this hand-back; identical copy at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/59-a3-design-handback.md`.

No apply operation file, git operation, model load, GPU submission, API call or notebook execution was used.

The minimal root scientific ruling contract is `ROOT_RULING_V1` in the design module: schema version 1, kind `specificity_ladder_a3_root_ruling`, seeds `[42, 1, 123]`, confirmatory family `[direction_FAR, direction_SER]`, constrained-mask task `far_v2`, and direction-null continuation `{neurons: deferred, edges: continue_bounded, mask: continue}`. Root supplies the real object before production preparation. This is a versioned scientific contract, without invented human authentication or approval requirements.

Semantic clause positions use each condition's actual source text and builder/tokenizer boundary APIs, retaining the leading-space BPE token. Unsupported or ambiguous bins retain empty positions and coverage reasons. The D/H and I/user-neutral maps are explicitly bidirectional only after builder alignment and explicit length, clause-width, outside-clause and readout checks. D/I has pooled-summary semantics only. Designation positions come from each condition's own clean/corrupt builder pair. Legacy assertion invariants are repeated explicitly so optimized Python cannot remove validation.

## How verified

Initial collection failed because the A3 modules were absent. Subsequent failing regressions demonstrated missing source enrichment/donor registry protection, lost leading-space BPE clause tokens, absent own-condition designation positions, and acceptance of outside-clause changes under optimized Python before the corresponding fixes.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py -p no:cacheprovider -q
```

Observed: 33 passed in 10.42 seconds, exit 0.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py -p no:cacheprovider -q
```

Observed: 33 passed in 13.76 seconds, exit 0. Base emitted its pandas/bottleneck dependency-version warning. Both suites include a real subprocess using the corresponding interpreter with `-O` and explicit failure if an invalid map is accepted.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No production `a3_design.json` was emitted. A late existence-only check saw `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-0253f49/selected.json`; this worker did not load that artifact or claim its completion evidence valid.
- Production preparation, complete historical/source/registry inspection, and the availability of sufficient seed-2 IOI validation prompts remain for root after review. Preparation will block if any parent source, actual membership, tokenizer, grader, exclusion, minimum cohort or registry gate fails.
- Neutral-frame activation directions and cosine diagnostics are specified as Task 2 work. Only metadata nuisance prediction is computed here. No direction, neuron, edge, gradient or mask algorithm was implemented.
- The later stage CLI, model geometry assertions at load, GPU admission, pilots, fitting, selection and assessment remain outside Task 1. Existing A1 files, generic hooks and other workers' files were not edited.
- No scientific outcome or direction-specificity claim is made by the injected fixtures or diagnostic classifier.

## Open questions

- Root should create the real scientific ruling object and independently review these four code/test files before production preparation. Default: retain the exact version-1 contract, FAR-only constrained mask family, direction-only FAR/SER confirmatory family and the accepted null continuation.
- If the immutable A1 assessment ids are absent from the actual matched test intersection, or eligible train/validation counts fall below the operational minima, default: block with the preserved assessment ids; do not redraw, borrow assessment data or lower thresholds.
- Missing or ambiguous semantic spans remain explicitly unsupported. Default: retain coverage and narrow the interpretation; do not interpolate, clamp, or reuse another condition's token indices.
