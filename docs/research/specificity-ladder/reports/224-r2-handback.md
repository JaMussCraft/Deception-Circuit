# CPU proof correction scoped rereview

Status: handed-back

## What changed

The production correction addresses R224-A through D statically, but the new marker regression has a fixture blocker. The inherited prospective GPU job id is `T1-FIXTURE-JOB`; the new actual-marker test sends it to the existing numeric-only Slurm guard and fails with `ValueError: actual GPU job identity`. Keep that production guard. Bind one coherent numeric prospective id in the new fixture before the actual GPU module writes its marker/config.

## How verified

Compared the preserved baseline with the corrected CPU code, narrow ruling, original test bodies/parameterizations and added regressions. All 229 frozen pins match `80b67c4aac5535dcbfe2b88e192c1cde270bde3b445bfccf97b2307abb628859`. Original test function names and parameterizations remain; two direct assertions reflect the reviewed fixture correction. Both accepted controller test files remain unchanged. Evidence: `plan-a2-task2-review224/r2/pin-and-static-checks.json`.

Actual marker names and same-buffer acquisition now align; request and marker bytes are checked again before Popen. Alias validation iterates the complete authenticated map. The supervisor exports all required CPU COMPLETE fields and requires reconstructed-domain/support evidence. The runner selects every required test file. No further production blocker was found within this fix diff.

## Execution evidence

Three independent tiny cases observed two passes and one failure: the original short-window marker case fails at the numeric job guard, while real eleven-alias metadata and CPU COMPLETE through the actual GPU consumer pass. Two further tiny cases pass after only an in-memory numeric fixture-id change, preserving the actual source-produced marker bytes. These are concrete pure endpoint checks, not the full suite. Evidence: `plan-a2-task2-review224/r2/tiny-endpoints.json`, `plan-a2-task2-review224/r2/numeric-diagnosis.json`.

Root job `23620719` was last reported pending; no terminal RED/GREEN result was supplied to this reviewer and no scheduler polling occurred. The full intended corrected scope remains 226 cases in each environment, following the preserved-candidate 22-case attribution check. No GREEN acceptance is issued. Evidence: `plan-plan-a2-full-score-operational186/task2/green-r2/pins.json`.

## What is NOT done

No candidate, source or test file was edited. No native/full suite, model, proof, scheduler, remote, git, RS or additional agent work occurred. No author handback was read. The scientific source remains unchanged context; no genuine resource/GPU/full-score admission follows. Exact local receipts, failure XML and fixture diagnosis are in `plan-a2-task2-review224/r2/run_manifest.json`.

## Open questions

After root confirms the frozen job terminal or unstarted cancellation, publish a test-only pinned successor that gives the new cross-endpoint fixture a numeric prospective GPU job id. Preserve the failed/unrun packet and production guard. Observe the full attributable RED and corrected dual-environment GREEN before scoped acceptance. No broader redesign or second production correction is requested.
