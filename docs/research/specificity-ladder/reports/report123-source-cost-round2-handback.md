# Source guard cost round-two correction hand-back

Agent: Codex Sol. Status: handed-back. Software correction only; no preparation or performance/admission claim.

## What changed

Only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/source-guard-cost-fix-source-r2/component_analysis/a3_source_validation.py` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/source-guard-cost-fix-source-r2/tests/test_a3_source_validation.py` differ from frozen baseline
`caae47195503460c1df63670d23448c49b316a67`.

B1: capture actual artifact-envelope byte and complete lexical ancestry witnesses before
artifact-to-owned-payload comparison. Require the original envelopes to remain unchanged
through dependency discovery and full semantic validation; the retained state cannot
rebaseline a valid replacement discovered after comparison. Initialization accounting
continues to include this work, and temporary early witnesses are released before the
returned-state RSS sample.

B2: bind every actual file returned by `grader_files` under the same repository used by
`ladder.grader_registry`, together with its actual glob patterns. Those lexical paths and
target ancestors enter the existing static byte/provenance proof. Real current grader
validation still occurs during every successful refresh; source aliases/glob changes
now fail at the earlier byte/closure boundary.

Pipeline, authority, workload, original source and scientific/cap settings are unchanged.
The inventory still has 511 ordinary files with the original input links. Exact source
pre/post hashes, computed blob identities and minimal diff are in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/source-pre.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/source-post.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/source-freeze-manifest.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/candidate-diff.txt`.

## How verified

Both independent counterexamples were reproduced before source changes in both
interpreters: each red pair observed 2 failures because the expected rejection did not
occur. Raw: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/red-r2-mgnp.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/red-r2-base.log` and their command receipts.

The original independent probe file remains unchanged and is included with the complete
affected owner/helper suites. Its exact binding is
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/independent-probe-binding.json`. The initial post-fix helper/control runs passed
the independent probes but showed 2 older message-match failures: static grader bytes
and glob changes now reject before the grader-specific error. Their tests retain the
required `ValueError` rejection and accept the earlier immutable/closure messages.
Raw: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/green-r2-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/green-r2-base.log`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider --basetemp=/tmp/source-cost-123-handoff-r2-mgnp tests/test_a3_source_validation.py tests/test_a3_mask_pipeline.py tests/test_a3_edge_pipeline.py /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/121-source-cost-review-evidence/test_independent_source_boundaries.py
```

Observed: exit 0, 187 passed. Exact environment, source hashes, raw argv, timing and logs: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/handoff-r2-mgnp.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/handoff-r2-mgnp.log`.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider --basetemp=/tmp/source-cost-123-handoff-r2-base tests/test_a3_source_validation.py tests/test_a3_mask_pipeline.py tests/test_a3_edge_pipeline.py /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/121-source-cost-review-evidence/test_independent_source_boundaries.py
```

Observed: exit 0, 187 passed. Exact environment, source hashes, raw argv, timing and logs: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/handoff-r2-base.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/handoff-r2-base.log`.

The base suite retains 3 existing dependency warnings; see `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/handoff-r2-base.log`.

All checks use explicit project interpreters, thread limits, no bytecode/pytest cache,
isolated basetemps and the explicit unchanged original A1 schema fixture. No real-input
fast-path benchmark, fake execution authority or model admission is part of these tests.

## Execution evidence

- Job id and cluster: local CPU software subprocesses only; no scheduler job or GPU allocation.
- Exit codes: final results and every preserved attempt are recorded in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/run_manifest.json`.
- Coverage: expected 187 tests per interpreter, including unchanged independent probes; source inventory observes 511 against expected 511 files, with only the two owned files changed. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/run_manifest.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/source-freeze-manifest.json`.
- Baseline reproduces: the two reviewer counterexamples fail before correction in both interpreters, against expected rejection. Existing positive controls remain in the final group. No pretrained numerical baseline or scientific scoring was run. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/red-r2-mgnp.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/red-r2-base.log` and final receipts.
- Provenance file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/123-source-cost-round2-evidence/run_manifest.json`, baseline commit `caae47195503460c1df63670d23448c49b316a67`. The corrected candidate remains uncommitted; its exact tested bytes are in the freeze-input manifest.

## What is NOT done

No C3/C4/frozen-runtime/artifact change, git, RS/job/reservation mutation, GPU, large
weights, paid API, notebook, subagent, new preparation, real-data performance measurement,
source freeze, cap exception or admission. No retrospective rewrite of handback119.
Mandatory fresh byte/current protection/grader/authority obligations and all scientific
coverage remain in place. Remaining real-input and used-path feasibility questions are
explicitly deferred to the next root-frozen source and separately released measurement.

## Open questions

Root owns exact source freeze and independent review of this correction. Default:
stop after focused software checks and exact hashes; prepare or benchmark only after
root freezes the next source and explicitly releases that phase. The old held mask
source/reservation receives no upgrade or refund from these results.
