# Hand-back 287: Slurm identity expectation in startup test

Agent: Sol. Status: resolved read-only diagnosis; no correction implemented.

## What changed

Only this report and bounded diagnosis artifacts were added under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/startup-diagnosis`: `identity_probe.py`, `pure-results.json`, and `terminal-summary.json`. No active source, frozen packet, suite or prior correction was edited.

The additional failure is a test expectation defect. The exercised test at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded/suite/test_a3_direction_runtime.py:1411` always supplies `expected_job_id='injected-cpu'`. Its native producer at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py:1743` instead records the real `SLURM_JOB_ID` whenever present, falling back to `injected-cpu` only for an injected design without that environment variable. The same statement records `os.getpid()`.

The validator at runtime lines 1775–1776 correctly checks the expected job and positive integer PID, then any supplied expected PID. Source identity, artifact bytes, and scenario checks surround these guards and need no change. Production shard intake derives expected identity from the linked shard's execution at runtime lines 1365–1371, including job/PID equality for cached records. A neighboring production-shaped fixture already expects the ambient Slurm job or `host-cpu` fallback at suite line 1479.

The actual failed test reaches the validator only after constructing and reading the startup record and passing the preceding positive PID, source and cost assertions at suite lines 1402–1410. The saved job manifest identifies Bridges job 50319108; the trace matches a hardcoded injected fallback used inside that real allocation. The actual startup payload is not present in the mirrored temporary directory, so its job field was not independently read here. Source derivation and the saved trace establish the narrow mismatch without requiring that unavailable payload.

Candidate test-only correction, awaiting root authorization: before constructing the index, capture `expected_job_id = os.environ.get('SLURM_JOB_ID', 'injected-cpu')` and `expected_pid = os.getpid()` directly from the test process. Use those independent values for the positive validator call, explicitly checking both record fields against them. Use the same expected job plus `expected_pid + 1` for the existing wrong-PID rejection. Add an explicit wrong-job rejection using `expected_job_id + ':wrong-job'` with the correct expected PID. Replace all four hardcoded job arguments within this test, including its missing-marker and changed-payload checks at suite lines 1456 and 1461, so no unrelated job mismatch can mask the intended checks. Preserve all cost, resource, publication, row/linkage and tamper assertions. Do not read the expected identity from the produced record, unset/spoof Slurm, or alter the production validator.

The existing wrong-PID call at suite line 1412 currently also uses the hardcoded job. Under Slurm it could reject for the job mismatch first, so a correct ambient job expectation is necessary to preserve an attributable PID check. An explicit wrong-job check separately protects job equality. The optional PID is independently derived from the process rather than accepting the record as its own oracle.

The other terminal shard failure, `legacy-no-preparation`, reaches the same missing `target_preparation_reference` dereference as report 282's narrow guard correction. No additional production change is indicated for it.

## How verified

Read the saved terminal observation, exact suite/runtime source, selected event trace, JUnit and manifest. Summarized the large manifest with stdlib parsing rather than importing application code. JUnit contains 111 cases, two failures, no errors or skips. Manifest source-before and source-after pins are equal.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/startup-diagnosis/identity_probe.py
```

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/startup-diagnosis/identity_probe.py
```

Observed both exit zero. The script AST-extracts only the producer's process-expression and the validator's two process/job guards. Four literal environment/design specimens cover injected and production with/without a Slurm job. The injected Slurm specimen generates job 50319108, rejects the old hardcoded `injected-cpu`, accepts the independently specified literal job/PID pair, and rejects separate wrong-job and wrong-PID pairs. Controlled `os` stand-ins leave the real environment untouched. These are expression/guard checks only: no full validator, native record authentication, target construction or cost calculation ran. Full command outputs are in `pure-results.json`.

## Execution evidence

- Saved native job: Bridges job 50319108, mgnp; observed from Delta. Child manifest exit one, `normal_completion=false`, `full_suite_accepted=false`.
- Cases: 109 passed against 111 expected; two failed, zero errors/skips. Failed names are the legacy preparation rejection and startup identity test named above.
- Baseline: no scientific baseline reproduction claim; root-provided terminal accounting and saved manifest concern validation, not scientific estimates.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded/jobs/job-50319108/child/execution/run_manifest.json`, commit `538109e809285b6ddc45d42df8786270a65f7b12`. The manifest explicitly labels that commit as the accepted worktree baseline and binds the isolated revision with exact source pins; runtime pin is `aea07dbf153824f373be70629dd24edc28dd6566cafa5955f43c69fd1119ec90`.
- Local probes: two bounded stdlib/AST commands, exit zero on both interpreters; four synthetic identity specimens each. Native correction acceptance remains not yet verified.

## What is NOT done

No source/test/packet correction, native import or full/local test, artifact publication, job operation, Slurm/SSH/Git/RS command, agent or environment mutation. The frozen unsubmitted successor packet remains untouched. Root owns lint/number checks, authorization and complete successor validation across both environments. No production guard or original scope is relaxed.

## Open questions

- Does root authorize the narrow test-only expectation correction above in a new successor draft? Default: wait without editing.
- Should the positive call explicitly pass the independently captured PID as proposed? Default: yes, preserving distinct wrong-PID and wrong-job checks and all existing assertions.
