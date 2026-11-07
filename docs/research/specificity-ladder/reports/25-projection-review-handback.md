# Hand-back twenty-five: Independent A2 projection and clock marker review

Agent: Codex Sol reviewer. Ticket: A2 plan Task three and narrow final wrapper clock marker. Status: resolved review, one compatibility finding outstanding.

## What changed

Only this review report was written; no implementation files were edited.

- Orchestrator commit source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/25-projection-review-handback.md`.
- Primary hand-back destination: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/25-projection-review-handback.md`.

Finding P2: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training_projection.py:59` validates the materializer build hash using `digest`, which defaults to ASCII escaping. The materializer hash uses `ensure_ascii=False`. A legitimate manifest containing non-ASCII source configuration metadata therefore fails before any receipt can be evaluated. This is a false refusal, with no unsafe approval demonstrated. Align only the build-hash canonicalization with the materializer; receipt hashes must retain the wrapper digest convention. Add a non-ASCII build fixture regression.

The direct review otherwise supports the intended conservative gate:

- Exact three tasks, two conditions and three seeds produce eighteen cells. Timing reuse is explicitly limited to seeds within the same task and condition; six task/condition measurements are required. Invalid receipts cannot provide coverage.
- Model, source commit/hashes, build/config hashes, selected ids/counts, padded length, GPU identity/count, cluster/allocation, argv, artifact hashes and pruning granularity are checked. No cross-build, task, condition, hardware or shape reuse is permitted. The CLI compares code hashes to current files.
- Failed and injected-runner receipts are rejected. The wrapper marks any custom clock with both injection flags before allocation checks. Explicit `time.monotonic` and the default clock remain unmarked. Projection rejection uses the runner flag, so current custom-clock receipts are rejected too.
- Full allocation estimate is total minus printed pruning plus epoch-scaled pruning. Buffering and upward whole-minute rounding precede summation; explicit aggregate pilot reservation is added. Exactly sixty GPU-hours can pass; any excess blocks. Missing/invalid pilot cost blocks. Failed pilot costs depend on the caller supplying the ledger aggregate honestly.
- The six-hour trigger uses unbuffered projected allocation time and directs a separately measured heads-only pilot. Heads-only timing has a separate granularity and coverage requirement. No fallback is launched.
- Provisional D-only data cannot approve a fleet. Matched A1 provenance and complete coverage are required. The CLI reports hardware-conditional recommendations from the first candidate receipt; missing hardware blocks, and mixed receipt hardware produces rejection. CLI writes no ledger, job or training artifacts.
- Under two hundred training rows blocks approval and is surfaced for lead review. This is an implementation restriction, not a minimum imposed by START. The plan requires lead review; a future recorded lead ruling needs an explicit supported route if such a cohort is to proceed.

The projection is a recommendation, never authorization to submit. No pilot or fleet reservation is approved by this review.

## How verified

Read START A2, plan-a2 Task three, projection implementation/tests, wrapper receipt schema, and the narrow clock marker/tests directly. Did not read the implementation narrative report.

```
OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_projection.py -p no:cacheprovider -q
```

Observed: forty-eight passed; saved output `/tmp/a2-projection-review-0.log`.

```
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_projection.py -p no:cacheprovider -q
```

Observed: forty-eight passed; saved output `/tmp/a2-projection-review-1.log`.

Inspected existing `/tmp/a2-wrapper-clock-red.log`: custom-clock marker assertion failed before the fix; the default and explicit-monotonic cases passed. Inspected `/tmp/a2-wrapper-clock-mgnp.log` and `/tmp/a2-wrapper-clock-base.log`: eight passed in each environment. The wrapper suite was not rerun by this reviewer.

Focused reproduction: loaded the synthetic test fixture, added source-config description `neutral twin — source metadata`, recomputed build_hash using the materializer convention, and called `project_reserved`. Observed `ValueError: build hash mismatch`; materializer hash equality against projection digest was false. No files were written by that reproduction.

Live Codex usage checkpoint reported eight percent used, below the eighty-percent cap.

## Execution evidence

- Job id and cluster: local CPU test commands above; no Slurm job.
- Exit codes: zero for both projection suites and the handled compatibility reproduction.
- Row counts: forty-eight collected and passed against forty-eight expected per interpreter. No scientific dataset was scored.
- Baseline reproduces: both interpreters returned forty-eight passing projection tests against the same forty-eight-test expectation. Existing wrapper evidence is eight passing cases against eight expected in each log.
- Provenance file: no scientific `run_manifest.json` or commit is claimed for these CPU checks. Scientific runtime and timing estimates are not yet verified by an actual pilot; fixtures are synthetic arithmetic evidence only.

## What is NOT done

No code repair, broad wrapper suite, GPU/API work, notebooks, git, Slurm submission, ledger changes, or implementation narrative review. No measured pilot exists in this review. The Unicode build-hash issue remains for the owning implementer. Conservative lead bounds and under-two-hundred lead-ruling overrides are not implemented.

## Open questions

Default: repair the Unicode build-hash mismatch and add its focused regression before accepting Task three as compatible with all valid materializer outputs. Preserve receipt digest conventions.

Default: keep under-two-hundred cohorts blocked until a lead ruling is recorded and an explicit reviewed override is implemented. Do not infer a START minimum or authorization to submit from the recommendation.
