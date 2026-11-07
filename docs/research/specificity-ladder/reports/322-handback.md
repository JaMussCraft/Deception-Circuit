# Held candidate CPU deployment review 322

Status: handed-back

ACCEPT_EXISTING_HELD_CANDIDATE_CPU_RELEASE_AFTER_FINAL_ROOT_CHECKS. This covers only existing held job 50319720, after the final root checks below.

## What changed

Created reviewer-owned checks, checker copies and the [machine verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/producer-deployment320-review/verdict.json), SHA `ac8de62cbf6616a3443b96dc95a4e454b59b95557c497e44dd23df52fd54d25e`. Source, inputs, scheduler and remote state were not modified by this review.

The verdict binds deployment manifest `98da72ff996334b51488f7b32bb8c3b9df9c09fc379d0261804dbec4f15f9e33`, config `ce924437438d95b8d3048688ebd9dec0dae9095f0209526009aecbfdb441b104` and actual submitted spool/dispatch `199adc171ab612b0b247b47e55433f91b4c90849780bb4e6cfc7ca8ac82cb9af`. The spool was hashed remotely by the root checker; this reviewer audited its raw receipt and checker, without independently accessing the scheduler spool.

## How verified

Rehashed all eight deployment-manifest members and all 702 regular source-tree files, totaling 296,637,138 bytes, with exact membership and no substituted symlinks. Config and hash pointer agree. Source snapshot and accepted reviews 310/316 rehash; all 362 exported code members match the staged closure. Original packet 311 and H200 execution settings remain pinned. The dedicated physical Alignment maps to the unchanged virtual Alignment; global image, packed environment and nested HF hub mappings remain explicit.

Joined every required input in source-derived closure 319 to the exact 326-row config and successful actual readback: 295 required, ten optional cache rows and twenty-one historical/old-context extras. These latter rows are preserved without giving old code authority. All input hashes/sizes match the stable 317 observations and either staged regular rows or sixteen external HF rows. All seventeen literal aliases match the required/optional alias inventory, including five export aliases. The earlier 317 receipt explicitly has closure_accepted false; closure acceptance here uses the later source-derived inventory and actual deployment authentication, not that historical flag alone. Current grader-registry raw bytes remain a captured snapshot; the historical raw digest is not substituted for current bytes or the native code-derived grader field. Snapshots are not continuous synchronization with Delta.

Audited root checkers: actual host readback hashes all staged files, input targets, alias literals, packet and image; final held binding rechecks sources/inputs/image/config and actual spooled bytes. Native guards still execute inside the real job. Actual smoke enters the existing container inner helper, checks effective declared cgroup read-only mounts, confirms source-root write rejection and child-only write access, and checks HF constants. It imports no native runtime, Torch or Transformers. Canonical producer output remains absent.

## Execution evidence

Captured scheduler state is PENDING/JobHeldUser, zero runtime, account cis260361p, partition RM, QOS rm, one node and one task, 128 CPUs, 192 GiB, ninety minutes, zero GPU TRES, Requeue/Restarts zero. Command and working directory match this deployment and accepted producer packet. Own UID is 105853. The actual canonical run root has raw mode 0700, no symlink ancestry, is empty, and has no child directory. Actual ninety-minute scheduler preview succeeded; its test-only identifier is not an executed producer job.

Actual host Python 3.6.8 dry-run and container Python 3.12.13/pytest 9.1.1 smoke passed without native execution; smoke is not an allocation identity proof. Actual running allocation/controller/CPU checks remain the unchanged host's responsibility inside job 50319720.

Captured available filesystem bytes are 1,017,742,364,672, exceeding the 68,719,476,736-byte diagnostic reserve. Project 560453 quota shows 54,394,916 KiB used of 1,048,576,000 KiB, leaving 1,018,041,430,016 bytes and 5,839,844 file slots. This is a current reserve check, not a final output-size or memory bound. Source-free pure hash/receipt work took under four seconds; no tests, native imports, remote access or jobs were performed by this review. Live usage was 55 percent, below the 80-percent cap.

## What is NOT done

No CPU outcome, successful native freeze/prefit/target, measurement, resource fit guarantee, receiver readiness, model execution, selection/admission, GPU permission, final source publication or whole-code/native acceptance follows. The unchanged 5,040-second child cap, final reserve, cleanup and margin remain inside 5,400 seconds. No extension, retry, reduced scientific workload or parallel-speedup assumption is authorized.

Candidate commit 2ba697d7f5fdfd7cebc7225ae004ec9e731e434f remains provisional under ruling 308. Reuse requires the same eventual accepted execution commit, design/protocol, namespace and bytes. Otherwise preserve outputs only as diagnostic evidence. Producer observations cannot establish receiver/handle/full-final-cost bounds.

## Open questions

Root must freshly confirm live usage/session state, exact source/input/config/hash-pointer/SIF/spooled-script identity, this same held job's scheduler/resource/UID/zero-runtime/no-GPU/no-requeue state, and canonical empty private root/free reserve immediately before one release. The prepared root release helper implements those captured checks; root alone runs it. Preserve all failures and incomplete outputs. Actual producer terminal/source/allocation/resource evidence requires a separate review; remaining BASE validation, final publication, applicable receiver and downstream science/GPU gates remain separate.
