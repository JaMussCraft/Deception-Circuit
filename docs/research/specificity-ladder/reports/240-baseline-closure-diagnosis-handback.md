# A3 baseline context-closure failure diagnosis

Status: handed-back

## What changed

The local r4 baseline export is incomplete, so this is not a Bridges-only transfer defect. The same pending Delta packet is affected. Do not run the unchanged r4 packet expecting valid baseline attribution; root should hold/cancel the still-unstarted Delta job before a corrected immutable packet is prepared. No source files changed.

Exact observed failures: the first three baseline cases fail because `baseline-source/docs/research/held_out.json` is absent; the last two completed-intake cases already fail with the intended `DID NOT RAISE ValueError`. The observer correctly refuses the mixed failure causes and never starts the 223 GREEN stage. Earlier messages overgeneralized the last two failures; this report and per-case evidence correct that attribution.

Two concrete file-relative dependencies are omitted from the baseline export and transport inventory:

- `docs/research/held_out.json`: mandatory branch protected registry read by unchanged `dataset.user_inversion_pipeline.check_registry`.
- `docs/research/directions.json`: mandatory branch frozen-grader registry read by unchanged `ladder_pipeline.grader_registry` after the protected-registry check succeeds.

Neither file exists locally under r4 baseline-source; neither is in its baseline pins or the 1112-file transport list. Baseline has no aliases. Candidate/oracle resolve these registry paths through their existing aliases. Both primary/worktree held-out registries currently contain schema 1 with zero sets and no path-referenced transitive protected-ID files.

## How verified

Read raw actual-job JUnit, stdout and run manifests, baseline fixture/import/guard code, source-pins, actual local paths and transport config. Failure chain for the first three cases is fixture.anchor → prepare_pilot_target → live_guard → artifacts.validate_live → a3_design.validate_access → common.check_registry. It fails before the intended cgroup assertion. `REPO` is correctly derived from the baseline module location; there is no wrong-source import in this trace. The next mandatory `grader_registry` reads baseline directions.json as well as primary directions.json.

A small stdlib-only AST extraction ran the unchanged check_registry function against actual primary registry plus the actual missing local baseline path and reproduced the exact missing-registry message. An ordinary held_out.json copy under a temporary diagnostic root satisfies that same guard without changing its code. This probe took 0.135 seconds; it is not a full fixture pass or a source correction. Evidence: `.superpowers/sdd/plan-a3/baseline-closure-diagnosis240/diagnosis.json`, including all five exact JUnit messages and missing dependency paths/source hashes.

Why earlier checks missed it: `check_pins` authenticates only declared code members; the declaration omitted runtime context. Source-origin checking imports modules without executing live guards. Observer --dry-run checks pins/count/command construction, not baseline fixture setup. The transport inventory test explicitly asserted zero baseline aliases but did not require ordinary registry files. My binding review established equality to that declared inventory; it did not establish completeness of the baseline’s file-relative read set. The full execution gate exposed that gap before any GREEN or scientific acceptance.

The staged transport faithfully preserved the already-incomplete local export. Fixing only Bridges, or reducing the required baseline failure semantics, would leave the Delta defect and invalidate attribution.

## Execution evidence

Actual Bridges job 50316834 is reported FAILED 1:0 after 286 seconds by root; preserved observer/baseline manifests report normal_completion=false and exit 1. JUnit has five cases, five failures, zero collection/setup errors/skips: three missing protected-registry ValueErrors and two intended DID NOT RAISE failures. Baseline wrapper wall 266.723 seconds. The unchanged wrapper checks exact failure text and correctly rejects this as accepted RED. No 223-case GREEN results exist from this attempt.

Reviewer executed only the tiny pure guard probe and receipt/filesystem checks, without native imports, model, full suite or remote work. No job/scheduler action was taken. The pending Delta job’s live state remains root-owned, but its identical local baseline defect is directly observed.

## What is NOT done

No implementation repair, full fixture run, valid five-case RED acceptance, 223 GREEN acceptance, runtime/source publication, genuine resource or numerical/GPU admission. Failed execution artifacts remain unchanged. No git, RS, jobs, SSH or extra agents.

## Open questions

Minimal complete correction proposal for root/implementation owner:

1. Create a new immutable observer/baseline export. Add exact ordinary copies of the two required registry-context files, with declared hashes, under baseline-source/docs/research. Preserve baseline runtime r3 and all test/algorithm bytes. Ordinary files preserve zero baseline aliases and the accepted eight-alias transport policy.
2. Extend baseline context pins/export inventory and final deployment/config binding to cover those files. Declare primary/worktree live registry inputs separately and follow any protected-set path dependencies if sets are later present. Do not patch REPO, validators, guards, baseline failure assertions or expected case counts.
3. Add a stdlib baseline context preflight that rejects missing/wrong registry paths/schema/grader entry before expensive fixture execution. This must inspect actual baseline-relative paths, not just the candidate aliases or listed source hashes.
4. Preserve the failed r4 attempt. Run all five original baseline cases against preserved r3 and require their intended DID NOT RAISE outcomes, then all 223 original GREEN cases in both interpreters under the corrected exact closure. Full fixture success remains an execution gate; the pure probe does not substitute for it.

No new design or scientific decision is needed. Root owns pending-job handling, corrected packet execution and report lint.
