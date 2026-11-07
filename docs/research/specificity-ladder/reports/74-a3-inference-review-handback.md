# Hand-back 74: A3 pure inference and conditional-power review

Agent: Codex independent statistical reviewer. Scope: bounded Task 2b in the A3 plan. Status: handed-back.

## What changed

Review report only; no implementation or test edits. Author report 70 was not read. No git, subagents, model loading, GPU, Slurm, API calls, datasets or notebooks were used.

- Worktree report for the orchestrator: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/74-a3-inference-review-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/74-a3-inference-review-handback.md`.

Reviewed the complete Task 2 executable power specification and global constraints in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md`, the pure statistics implementation, its owning synthetic tests, and relevant inherited denominator/gate logic in ladder metrics.

Finding: no blocking numerical defect identified in the bounded pure inference/power implementation. No severity/location/reproduction defect entry is warranted from the evidence below.

The implementation follows these specified contracts:

- Separate paired-stream D/H and I/user-neutral ratio-of-means gaps; per-stream finite positive gaps above the supplied replay epsilon; all three fixed seed gates; failed triplets represented internally by negative infinity.
- Exactly 199 null triplets; strict noninterpolated empirical percentile; tied nulls count against the learned statistic; failed learned triplets receive rank probability one. Holm uses exactly FAR and SER, including deterministic FAR-first ties and step-down stopping.
- Exact canonical-wording linkage across tasks; task-incidence-pattern cluster resampling; every member of unequal clusters contributes with equal ID weight. Seeds, streams, conditions and axes share the same draw. Utility draws use prompt identity and remain paired across tasks, seeds and both MMLU operations.
- Both MMLU_zero and MMLU_h_mean require the same 32 prompt IDs and independently obey the one-additional-error guard. These are subspace zero/centered-H operations under the accepted root schema. Absent assessment floors block the point gate. Absent validation floors produce explicitly conditional power.
- Validation kind/split and complete axis/seed schema are required. Explicit assessment-ID and assessment-utility-ID exclusion lists reject overlap; assessment outcome fields are rejected. Original validation residuals and gaps define injection, while resampled intact gaps define the fractional statistic.
- The 32 observed calibration null axes expand to 199 using a common replacement-index bank. Null effects remain observed rather than receiving synthetic learned effects. All 20 shared and 40 task-asymmetric scenarios retain the two-task Holm family.
- Collateral flips share keyed cluster-occurrence or prompt uniforms across tasks/seeds; task/seed accuracy controls thresholds. Repeated bootstrap occurrences have distinct uniforms. Expected loss uses original validation accuracy, leaves original incorrect rows incorrect, handles zero accuracy/zero loss, and labels infeasibility.
- Original-invalid/infeasible cells have undefined rejection probability; resampled-invalid draws remain nonrejections in the full replicate denominator. Any/both probabilities require both cells interpretable. Detectability requires the smallest tested fraction reaching the probability threshold and a lower tested neighbor below it. Binomial Monte Carlo intervals and calibration-null approximation labels remain explicit.

## How verified

Commands were run from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_statistics.py -p no:cacheprovider -q
```

Observed: 21 passed in 1.57 seconds; exit zero.

```bash
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_statistics.py -p no:cacheprovider -q
```

Observed: 21 passed in 1.84 seconds; exit zero.

An additional local Python heredoc used the synthetic panel factory, random independent finite margins/correctness, and explicit scalar loops. It compared both D and I ratios for every axis/seed/task, using a repeated unequal ID draw. Observed: all 2,400 comparisons agreed within relative and absolute tolerance 1e-13.

For an independent denominator reproduction, set each seed's D and I intact margins across four IDs to `[1,2,3,4]`, neutral margins to zero, and learned per-ID drops to `[0.2,0.4,0.8,1.6]`. Select bootstrap IDs `[0,0,1]`, inject D fraction 0.75 with zero collateral loss, and evaluate the synthetic panel. The original gap is 2.5, centered drop residuals on selected IDs are `[-0.55,-0.55,-0.35]`, and resampled gap is 4/3. Expected and observed D fraction are both `(0.75*2.5 + mean([-0.55,-0.55,-0.35]))/(4/3) = 1.04375`. This explicitly differs from incorrectly returning the injected fraction.

Reversing utility prompt IDs and their corresponding outcome columns in both tasks preserved the entire synthetic assessment summary under the same bootstrap seed. This checks identity-based utility pairing rather than accidental array-column pairing.

## Execution evidence

- Execution was local synthetic CPU testing only; no scientific/model run is claimed.
- Both owning pytest commands exited zero with 21 observed tests against 21 expected tests in each interpreter. The independent numerical probe exited zero.
- Synthetic baseline/reference agreement: scalar paired-ratio reference matched 2,400 of 2,400 estimates; the separate hand calculation was 1.04375 against observed 1.04375.
- Scientific rows, Slurm job, model baseline and model-run provenance manifest: not applicable. No scientific result is asserted and no production power estimate was computed. Source commit binding is intentionally left to the orchestrator; this worker never ran git.

All numbers in this report are frozen specification values, source locations/report identifiers, synthetic inputs/reference calculations, explicit test tolerances, or observed local-test outputs. None is an empirical model effect or production power result.

## What is NOT done

No pipeline implementation, selected-artifact integration, model-run coverage audit, real assessment, production conditional-power run, or full repository suite was performed. The caller must bind the normalized arrays to immutable A1 assessment IDs, frozen source/grader/model identities, replay-derived epsilon, supported assay flags, actual condition/stream ordering and canonical wording. The pure API intentionally has no independent access to those frozen artifacts; caller-side binding is an integration obligation, not a demonstrated numerical defect.

The caller must also supply genuinely disjoint validation utility rows, preserve both accepted MMLU operations, freeze fit/site/null identities and use the production replicate counts and seeds. Schema labels and supplied exclusion lists alone cannot authenticate provenance. Synthetic passing tests establish the reviewed numerical behavior only.

## Open questions

None blocking within this bounded review. Default: accept the pure numerical seam subject to the caller's frozen-artifact binding and actual model-run coverage checks; keep unexecuted model work and production power explicitly unclaimed.
