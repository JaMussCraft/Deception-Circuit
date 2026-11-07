# Corrected Bridges CPU test binding release review

Status: handed-back

## What changed

Accepted corrected held binding 50316834 for one mgnp-only CPU test run, subject to root’s fresh usage, actual held/cancellation and source/config readback checks. Both named review 236 gaps are closed. No source/test changes or wider re-review were needed.

The actual new held Command passes exactly the config path, config SHA and transport manifest SHA as three positional launcher arguments. Its spooled script matches frozen launcher SHA `e015a251ff55de96fc495628b3095dbbbd09481f3b90b2474f4727bbc8ec711d`. Both direct and relocated launcher interception now yield the exact correct host flag/value sequence. Host code was not executed by these probes.

Actual same-container statvfs and mountinfo readback show the source namespace, cache and packed environment read-only, including the original virtual interpreter path; cgroup parent and the explicitly overbound memory controller are read-only. The fresh private output parent is writable. This closes the effective-mount evidence gap for the reviewed pattern without claiming a production allocation or unrelated cgroup controllers are read-only.

## How verified

Read `held-r2-submission.json`, `positional-launch-probe.json`, `effective-mount-check.json` and raw cancellation receipt. Checked actual positional args against unchanged config SHA `2fd8748eec825bcc379cb54f40be89c9dac2dceb00fff3433994e900d8e42895`, transport manifest `bd3533cc18025d7d2bf97515060a46f793abd4f4a43609e8dc6c9626d8a6e6e2` and frozen launcher hash. Job 50316834 is recorded HELD/PENDING with zero runtime, 18 CPUs, 32 GiB, 59 minutes, correct account/partition/QoS, no GPU/requeue and absent execution output. The earlier 1112-file/eight-alias closure and actual virtual inventory/dry-run success remain unchanged evidence; they were not rerun.

One cancellation attribution caveat remains for root’s final live check: `cancel-held-bad-argv.json` records scancel exit 0 for 50316662, but its immediate accounting `after` string still says PENDING. It does not itself prove terminal CANCELLED. No cancellation claim here relies on RS. Root should save/check actual terminal cancellation or actual cancelled state as already planned before releasing the corrected job.

Detailed scoped evidence: `.superpowers/sdd/plan/a3-green-bridges-binding-review236/r2/verdict.json`.

## Execution evidence

No A3 tests or model work started in the reviewed held binding. Actual positional probes exit 0 twice and do not execute host code; actual effective-mount probe exits 0. This reviewer performed only local receipt/hash comparisons. Source-bound 223 GREEN plus five attributable r3 RED cases remain future execution gates.

## What is NOT done

No job release, fresh live scheduler/usage verification, terminal cancellation claim from a stale accounting row, source/test GREEN acceptance, genuine resource feasibility, numerical/GPU or production admission. The release ruling applies only to 50316834 and its unchanged bounded CPU test packet. No code edits, git, RS, remote calls, jobs or agents.

## Open questions

No further source/binding correction is requested. Root may release exactly the corrected held job after its ordinary fresh checks, including old-job actual cancellation and new-job held identity, source/config readbacks and usage. Preserve all failed/intermediate receipts. Root owns report lint and release actions.
