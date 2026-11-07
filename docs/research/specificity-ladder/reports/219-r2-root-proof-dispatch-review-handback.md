# Root proof late-binding dispatcher review

Status: handed-back. Exact dispatcher transport accepted; actual per-job binding and deployment gates remain open.

## What changed

Created only reviewer-owned review219-r2 evidence and this handback. No dispatcher, frozen adapter, source, authority, scheduler or remote changes. [Scoped verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-root-proof-dispatch-review219-r2/verdict.json) accepts dispatch SHA `8abf86b1295addd5cd8b41f13176199fb0fcf753cf6f1c40c044a073fa05e6aa` and test SHA `47855038052b2ffc3f14365df70858fac1e1cd6493ee69c756dbca6d90076afe`, targeting combined manifest `4e4b4bcf1ddcd6481fac1eccd966a2a1cbfa385b2bd16a9a00504cfaa05def3f`.

## How verified

The dispatcher follows the historical per-job digest-sidecar pattern identified in source review219. It derives an exact root-owned job directory from numeric actual `SLURM_JOB_ID`, rejects symlink leaves/ancestors, verifies exact resolution, reads a separately sealed expected hash and compares the binding's raw SHA. It accepts only 64 lowercase hexadecimal characters with either zero or one final newline. It pins the reviewed packet manifest and passes exact output, packet hash, binding path and expected binding hash to unchanged launch. It does not adopt a computed hash as expectation or create new native authority.

Output remains the existing allowed `root-genuine-proof-r2/job-ID/execution` namespace. Bash syntax passes. The dispatcher itself adds no Python dependency; the existing combined adapter's host compatibility was reviewed in219.

## Execution evidence

Nine supplied fixtures passed in base and mgnp, against nine each. Three independent cases passed in each, against three each, all four runs exit zero with no errors/skips. Independent checks verify exact hashes and target packet, rejection of an unsealed changed binding and raw sidecar junk including CRLF/NUL/extra lines, unchanged output confinement/occupied-directory rejection, and unchanged host rejection of a correctly hashed wrong-job binding. [Commands and logs](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-root-proof-dispatch-review219-r2/run_manifest.json). Only temporary substituted paths and a launch recorder ran; no actual root path, job, native context or model executed. Cadence remains forty points, tool checkpoint three at plus 120 since registration, ordinary cap eighty.

## What is NOT done

No actual held job, per-job bindings or digest sidecar accepted, no transfer completion, fresh catalogue witness, genuine proof/resource result or GPU admission. Passing a launch recorder is transport evidence only; actual unchanged host guards remain mandatory.

## Open questions

Root must stage/readback the exact dispatcher and every combined packet member, pin dispatcher bytes in actual submission evidence, then use the actual held job ID to create the exclusive owned job directory. Seal reviewed final `bindings.json` and separate `bindings.sha256` once; verify actual job/packet/output and all probe/review/transfer/catalogue references, remotely read back the exact known bytes, and only then release. Never rewrite sealed files or derive authority by adopting an arbitrary remote file hash. All remaining deployment, four-catalogue, live-entry, source/cache/protection/usage/deadline and normal CPU terminal/resource interpretation gates stay in force. No automatic retry or full-score admission follows.
