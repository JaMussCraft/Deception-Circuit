# Independent original-base oracle packet review

Status: handed-back

## What changed

Accepted the exact new packet and configuration for one deliberate original-base oracle attempt. Resource changes follow the reviewed narrower bound; an explicitly approved supervisor check also rejects a normal child reaped at or beyond its cap. [Verdict](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/verdict.json).

## How verified

Read raw diffs, tests and RED/GREEN logs. Rehashed both immutable packet manifests and all members. The original builder child and shell are byte-identical; configuration changes only child cap and allocation minutes. Reviewed the allocation guard changes and deadline rejection. Checked grammar and shell syntax and independently ran the focused pure suites. [Packet and limits](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/verdict.json), [raw supervisor](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/supervisor.py).

## Execution evidence

No Slurm job or genuine inventory construction was started by this review. Base observed 9 passing pure tests against 9 expected; mgnp observed 9 against 9 expected, both exit 0. Scientific dependency source is `861f84a3938a5e22fa329af0c469b2dd812fe68a`. These mocked metadata tests are not a scientific baseline reproduction. [Counts](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/verdict.json), [provenance](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/run_manifest.json).

Raw RED contains 2 expected deadline-boundary failures against 2 observed failures; corrected tests reject both at-cap and after-cap normal exits while preserving before-cap completion and TERM failure. [Boundary evidence](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/verdict.json), [raw RED](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/red-boundary-base.log), [base GREEN](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/green-base.log), [mgnp GREEN](160-host-split-operational-review-evidence/base-oracle-r3-packet-review/green-mgnp.log).

## What is NOT done

No completed base oracle, candidate equivalence, source publication or GPU admission. Missing-stream/postguard fixtures simulate failed children; genuine enforcement still depends on the unchanged pinned child and its actual completed run.

## Open questions

Root may submit the single accepted original-base attempt using the exact packet/config hashes, reviewed CPU resources and a distinct absent output directory. Preserve failed attempts and existing completed oracles. No automatic retry or completion guarantee applies.
