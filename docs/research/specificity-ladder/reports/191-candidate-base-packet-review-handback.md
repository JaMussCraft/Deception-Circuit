# Independent candidate-base packet semantics review

Status: handed-back

## What changed

Accepted only the packet semantics of the separate deadline successor. Final completion now rejects observed elapsed time at or beyond the configured child cap, including an already-reaped normal zero exit. Copied resource constants grant no resource or launch authority. [Verdict](191-candidate-base-packet-review-evidence/verdict.json).

## How verified

Read raw production diff, boundary tests and both environments' RED/GREEN logs without the author hand-back. Rehashed manifest members and compared the immutable parent: scientific child, allocation facts, shell and template configuration remain byte-identical. All candidate/oracle binding fields remain null. The completion rule matches the previously reviewed fail-closed original-base supervisor fix. Independently ran the focused boundary fixtures; no broad suite rerun. [Exact scope](191-candidate-base-packet-review-evidence/verdict.json), [raw supervisor](191-candidate-base-packet-review-evidence/supervisor.py), [template](191-candidate-base-packet-review-evidence/config.template.json).

## Execution evidence

No Slurm job or genuine builder/comparison ran. Base observed 5 passing pure tests against 5 expected; mgnp observed 5 against 5 expected, both exit 0. Raw RED shows 2 expected boundary failures against 2 observed in each environment. Before-cap completion, deadline/late-zero rejection and TERM rejection remain explicit. Missing-stream/postguard fixtures simulate failed children only. No scientific baseline replication is claimed. [Counts and fixture limits](191-candidate-base-packet-review-evidence/verdict.json), [RED](191-candidate-base-packet-review-evidence/red-base.log), [provenance and old input-context commit](191-candidate-base-packet-review-evidence/run_manifest.json).

## What is NOT done

No resource decision, completed base-oracle acceptance, candidate equivalence, bound configuration, source publication, model execution or GPU admission. Existing candidate sources and the separately owned new candidate remain untouched.

## Open questions

Require the complete genuine BASE oracle and its actual costs, explicit root resource selection, and separately reviewed immutable candidate/oracle configuration before one deliberate comparison. Preserve exact same-environment full-stream and postguard contracts and all prior artifacts; no automatic retry or inherited-timeout admission. [Remaining gates](191-candidate-base-packet-review-evidence/verdict.json).
