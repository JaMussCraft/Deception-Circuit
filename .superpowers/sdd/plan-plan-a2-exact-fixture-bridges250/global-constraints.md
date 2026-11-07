# A2 exact fixture transport to Bridges-2 implementation plan

> Root-assigned implementers use executing-plans after root accepts this plan; no extra agents. Root alone reviews/commits by explicit file list and owns copies, transfers, scheduler, RS and publication. This design authorizes no implementation or deployment.

**Goal:** run the unchanged Task2 fixture RED/GREEN packet on Bridges-2 with exact selected Delta interpreter/package bytes and literal origins, without porting the scientific BASE environment.

**Architecture:** adapt the accepted229-r3 host transport/process-group mechanics. One real Bridges host wrapper launches four isolated SIF invocations, one per environment/phase, with sealed actual host allocation receipts and only fresh private phase outputs writable. A new fixture observer variant consumes those receipts, preserving original commands/tests/oracle; it never invents Delta Slurm metadata or needs container scontrol.

**Tech stack:** host Python3.6 stdlib; pinned Ubuntu2204 SIF; exact BASE3.9.18/pytest8.3.3 slice; existing packed mgnp3.12.13/pytest9.1.1; original pytest fixtures. `contracts.json` supplies exact paths, hashes, names, resource/deadline fields and unset deployment bindings.

**Spec:** root's design-only250 brief, source r4 observer/pins/oracle, inventories248/251, accepted229-r3 transport and CPU-proof actual host receipt precedents. Proposed technical choices remain subject to independent review and root acceptance.

## Exact source and global constraints

`W=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`, `S=W/.superpowers/sdd`.

- Packet: `S/plan-plan-a2-full-score-operational186/task2/green-r4`; pins SHA256 `ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4`, all266 members immutable.
- Candidate: `S/plan-a2-full-score-operational186/candidate` (single-plan namespace). `packet.parents[4] == W` is valid. No path correction is needed.
- Baseline: `S/plan-plan-a2-full-score-operational186/task2/green/root-dispatch/candidate-before-interface-review`, with unchanged seven-member manifest.
- Runtime inventory251: `S/plan-a2-exact-base-inventory251/manifest.json`, SHA256 `d15679ce4f535fac8f8ec737cd9c52980ff05ce87d4cc0bd93f285d01f9ecbb1`; proposed1103-entry/89-ELF inventory, eleven system dependencies. This is not remote compatibility evidence.
- Reuse host/cleanup/shell patterns from `S/plan/a3-green-bridges-transport229-r3`, not its A3 counts/resources or mgnp-only scope. Reuse actual host receipt ideas from `S/plan-a2-full-score-bridges-cpu-proposal199/proof-adapter-r4/host_supervisor.py`, not failed proof authority.
- Preserve valid Delta job23623058, both queued jobs and all running jobs/results. No cancellation, retarget or native scientific source/test/diagnostic239/A3 change. Existing Bridges authorization covers placement; technical plan/runtime acceptance remains required.
- No GPU, weights/model, native scientific pipeline, effects, cache downloads, operational CPU_COMPLETE, release, ledger transition or scientific cap change. Ordinary80-percent usage cap and forty-point native cadence remain root checks.
- This task writes only this plan, contracts and primary250 handback. No code, bundle copy/install, SSH, jobs, tests, git, RS, source publication or extra agents.

## Review focus

1. Byte-identical Python/packages can still fail SIF ABI/startup/import resolution: actual bounded compatibility gates are mandatory.
2. The observer-inspection hook must retain different original RED/new GREEN targets or the RED signature changes.
3. Missing container scontrol must not produce fake Delta facts: real immutable host receipts establish actual Bridges identity.
4. Missing .pth/helper/ELF/alias closure can change imports despite equal versions: close actual imports and declare unused exclusions.
5. Expiry and leader exit must not allow late success or live descendants: preserve fresh entry checks, nonincreasing deadlines, strict post-reap checks and owned-group cleanup.

## Proposed file layout after acceptance

Only new `S/plan-a2-exact-fixture-bridges250/candidate/{host.py,observer.py,launch.sh,runtime-probe.py,bindings.template.json,test_transport.py}`. Root generates separate immutable runtime/fixture closure manifests and actual bindings. Use controlled exact copies, not a generic environment/package manager. Do not modify original packet or production files.

