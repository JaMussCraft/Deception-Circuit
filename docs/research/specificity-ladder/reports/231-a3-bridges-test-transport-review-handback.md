# A3 Bridges mgnp test transport independent review

Status: handed-back

## What changed

Reviewed only the new Bridges mgnp-only transport source, template, pure tests, actual observer interface and resource proposal. Did not read author handback229 or re-review A3 scientific source. Canonical reviewed transport manifest SHA is `14adee247cdf1138eeeb0a19ce2536cacc35fc3fd09df8febf578a68d0266a7c`; the preliminary identities were superseded before root deployment. All current manifest members match their hashes.

Source verdict: changes required on one concrete supervisor seam. Resource verdict: the proposed single CPU job, 18 CPUs/32 GiB/59 minutes on Bridges RM-shared under cis260361p/rm, no GPU/requeue, is coherent as a proposal. It is not deployment, scheduler or memory-feasibility admission.

**R231-A: cleanup tracks the observer leader rather than the entire started process group.** In `host.py:main.stop`, an already-exited/reaped leader skips all group signals because `child.poll()` is not None. If an alive leader exits promptly on SIGTERM, `child.wait()` returns and SIGKILL escalation is skipped even if a grandchild ignores TERM. The unchanged observer launches subprocesses; timeout handling can kill an immediate subprocess while descendants remain. Thus a timeout/failed observer can leave test descendants beyond the supervisor’s bound. The outer exception calls the same ineffective cleanup after the leader has exited.

Smallest correction: retain process-group ownership independently of leader liveness; terminate and bound the whole group on failure/signal/timeout, escalate when descendants remain after TERM, tolerate an already-empty group, and reap the leader. Avoid terminal promotion while unowned surviving descendants remain. Add bounded regressions for an exited leader with a live descendant and a TERM-exiting leader with a TERM-ignoring descendant, plus empty-group handling. Keep the existing late-reaped-zero-exit rejection.

## How verified

Read `host.py`, `launch.sh`, `config.template.json`, `test_host.py`, README, current manifest and the actual frozen r4 observer/baseline wrappers. Ran the seven pure wrapper unittest cases locally: exit0, seven passes, reported runtime0.060 seconds. No runtime/native test or production model import was involved.

A separate AST-extracted stop-function probe confirms both cleanup failures without creating processes: an already-exited leader receives zero group signals; a leader returning immediately from wait after TERM receives only SIGTERM and no descendant-liveness check or KILL. Evidence and correction scope are in `.superpowers/sdd/plan/a3-green-bridges-review231/{static-evidence.json,findings.json}`.

Other inspected paths align with the stated transport purpose: absolute spool-independent launcher, packed interpreter bound at the original mgnp path, unchanged observer invoked directly with mgnp-only GREEN, actual Bridges cluster forwarded, parent Alignment/ocean/HF read-only mappings and isolated job output parent writable, no GPU visibility/request, config/transport/source hash checks before/after, four literal aliases and virtual-to-physical mapping, exact current CPU/RAM/account/partition/QoS/requeue checks, allocation shortening, monotonic deadline and late-completion rejection. The supervisor refuses an unbound config. Its normal-manifest check requires mgnp-only actual GREEN and successful baseline/oracle; unchanged observer itself checks exact test counts/function inventory and the five attributable baseline failures. Final root config must bind 223 expected GREEN cases and refresh the stale source inventory to r4.

## Execution evidence

Local pure unittest execution: `python -B -m unittest -v test_host`, exit0, seven of seven cases passed. No Slurm job, Bridges/container execution, Python3.6 host run, source transfer, native/full pytest, production weights or operational resource measurement was performed. The synthetic stop probe is a control-flow counterexample, not an operational process-tree measurement. No test-result acceptance is claimed.

## What is NOT done

No final config/source inventory/alias binding, actual scheduler/account/resource validation, packed-environment pytest/dependency validation, effective container mount/cgroup read-only verification, Python3.6/site dry-run, deployment, submission or A3 source acceptance. Genuine resource/numerical/GPU gates remain separate. BASE remains on Delta. No code edits, git, RS, SSH/remote commands, jobs or extra agents.

## Open questions

Root should request the narrow process-group cleanup correction before binding/deploying this transport. Final config and actual host/container/dependency/resource checks remain root-owned gates; the adjacent older inventory is not final-source authority. After transport closure, actual source-bound five-case RED and 223 GREEN results in both environments remain necessary for A3 source acceptance. Root owns Markdown lint under the worker’s no-RS instruction.
