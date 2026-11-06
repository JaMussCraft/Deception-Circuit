# Independent completed original oracle audit

Status: handed-back

## What changed

Accepted the completed original mgnp oracle for a subsequent same-environment candidate comparison. The original execution artifacts remain unchanged. [Scoped verdict](160-host-split-operational-review-evidence/oracle-23491516/verdict.json).

## How verified

Read raw child, supervisor, stream, allocation and memory evidence without using the author report. Rehashed the accepted harness and its members, configuration, snapshot, design, builder and receipt chain. Checked that child fields survive supervisor promotion unchanged, the complete summary matches the builder receipt, and the stream receipt matches the final oracle. The accepted child calls both live guards and both source checks around the full original builder and complete publisher-format serialization, including its final newline. Only normal child exit permits supervisor completion. [Accepted execution and source provenance](160-host-split-operational-review-evidence/oracle-23491516/run_manifest.json), [raw child result](160-host-split-operational-review-evidence/oracle-23491516/RESULT.json).

## Execution evidence

Delta CPU job 23491516 ran on the allocated compute host with 4 CPU cores, 192 GiB and no GPU. The child exited 0 without TERM after 3194.5884759929995 seconds. The source commit is `861f84a3938a5e22fa329af0c469b2dd812fe68a`. [Execution provenance](160-host-split-operational-review-evidence/oracle-23491516/run_manifest.json), [child exit](160-host-split-operational-review-evidence/oracle-23491516/child-execution.json), [actual allocation](160-host-split-operational-review-evidence/oracle-23491516/allocation-before.json), [memory conversion](160-host-split-operational-review-evidence/oracle-23491516/verdict.json).

Observed inventory keys 246486 equal expected 246486; observed shards 81904 equal expected 81904; observed capture shards 4256 equal expected 4256. The complete baseline stream receipt and final oracle both contain 11421127399 bytes and digest `c738a185b9a79ef8873113e63aefa197a820f0a5c117159db055de6f70e0a6c9`. This establishes receipt consistency for one complete construction, not independent replication. The full summary retains the forward counts, operation counts and storage bounds. [Observed and expected counts](160-host-split-operational-review-evidence/oracle-23491516/verdict.json), [complete oracle](160-host-split-operational-review-evidence/oracle-23491516/COMPLETE_ORACLE.json), [full stream receipt](160-host-split-operational-review-evidence/oracle-23491516/STREAM_FINISHED_NOT_ORACLE.json).

## What is NOT done

No candidate comparison, numerical admission, speedup claim, model execution or GPU admission. The stream was hashed directly to a sink; no serialized inventory file exists for a post-hoc byte rehash. No partial file or subset was accepted. The current audit did not repeat bulk source/input hashing or rebuild the inventory. [Scope and verification limits](160-host-split-operational-review-evidence/oracle-23491516/verdict.json).

## Open questions

No blocker to using this immutable completed oracle for a same-environment candidate comparison. Any new full-source/input rehash or inventory construction must run on Slurm CPU; no duplicate construction is required for this audit. A separately bound candidate comparison and later source-bound native numerical gates remain outstanding.
