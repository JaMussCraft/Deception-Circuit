# Bridges transport process-group correction review

Status: handed-back

## What changed

R231-A is closed at source level. No new static findings in the requested cleanup correction and namespace diff. Reviewed only `a3-green-bridges-transport229-r2` against the frozen predecessor; no A3 scientific-source re-review. Canonical manifest SHA is `c8b9f2a43027134d1ae7b2c7e17c7f588c5524ff00c3e3aa70f2185d0c88d4e5`, and all members match.

Cleanup now signals the owned process group regardless of observer leader liveness. It gives the group bounded TERM grace, checks group existence independently while polling/reaping the leader, sends KILL to the remaining group and waits for the leader. An already-empty group is tolerated. Normal observer completion rejects a remaining process group and enters cleanup rather than promoting a receipt. Timeout raises into the same cleanup path. Existing deadline/late-zero-exit and manifest rules remain. Other source changes are the literal r2 packet/output namespace and absolute launcher path; config, observer command and CPU-only resource proposal are unchanged.

## How verified

Read the exact diff, raw base/mgnp RED/GREEN logs and manifest. Independently reran only the two bounded actual process regressions: reaped leader with live TERM-ignoring descendant, and TERM-exiting leader with TERM-ignoring descendant. Both passed, exit 0, reported runtime0.545 seconds. These tests inspect descendant disappearance/zombie state after cleanup and retain a final defensive group kill. The packet logs record nine passing pure fixtures per environment, and both intended predecessor process-escape failures per environment. No native/full suite ran.

Evidence is in `.superpowers/sdd/plan/a3-green-bridges-review231/r2/verdict.json`. The initial R231-A counterexamples are addressed directly; cleanup no longer treats `leader.wait()` as evidence all descendants exited.

## Execution evidence

Local command: `python -B -m unittest -v test_host.ProcessGroups`; exit 0; two of two cases passed in 0.545 seconds. Raw frozen logs: base nine GREEN fixtures in 0.617 seconds; mgnp nine in 0.554 seconds; two intended predecessor escape failures in each interpreter. These are wrapper checks, not Bridges host/container runs, scientific output or source-bound A3 GREEN evidence.

## What is NOT done

No final r4 config/inventory/alias binding, actual host Python 3.6 or Apptainer/site dry-run, effective mount/cgroup read-only validation, scheduler/resource check, deployment or submission. Packed-environment dependency availability was reported by root and is outside this scoped source ruling. Resource proposal remains 18 CPUs, 32 GiB, 59 minutes, no GPU/requeue, subject to root’s actual checks. No code edits, git, RS, SSH, jobs or extra agents. The source-bound five-case RED/223-case GREEN checks in both environments and all later genuine resource/numerical/GPU gates remain separate.

## Open questions

No further source correction is requested for this diff. Root can proceed with final binding and actual deployment checks, then submit the unchanged mgnp-only test packet if those checks pass. BASE remains on Delta. Root owns report lint under the worker’s no-RS instruction.
