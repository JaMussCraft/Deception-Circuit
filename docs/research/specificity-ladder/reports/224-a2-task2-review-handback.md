# Independent CPU proof review

Status: handed-back

## What changed

Issued REVISE for three narrow production-contract gaps and one verification-packet gap. No candidate or tests changed; the author handback was not read.

- R224-A: CPU supervisor expects WAITING fields `packet_manifest_sha256` and `deadline_unix`, but unchanged accepted Task one emits `launch_packet_manifest_sha256` and `publication_deadline`. A direct source-produced marker raises both KeyErrors. Its separate hash and parse reads also allow a swapped decoded buffer to supply a later deadline while original file hashes still match. Consume one authenticated raw marker buffer using the established field names; never rewrite or renew the actual marker.
- R224-B: input closure hardcodes five aliases. The actual immutable 422-input manifest declares eleven; the real function rejects it before data reads. Preserve the original manifest and check all declared literal aliases and targets. Keep the exact 418 immutable plus four current catalogue split. Evidence: `plan-a2-task2-review224/pure-interface-results.json`, `plan-a2-full-score-operational186/candidate/cpu/validate-phase.py`.
- R224-C: CPU COMPLETE omits nine fields required by the accepted Task one `actual_CPU_COMPLETE` consumer: `timely_window`, `bank_file_sha256`, `bank_manifest_sha256`, `full_rows`, `full_controls`, `full_domain_support_audit_complete`, `waiting_sha256`, `bound_gpu_config_sha256` and `launch_packet_manifest_sha256`. Derive these established fields from completed authenticated guard/request/window facts in the supervisor receipt. Task three still owns the later composite; it must not rewrite actual CPU evidence to disguise this mismatch.
- R224-D: GREEN selects only the 107 CPU tests and original eighty-two controller tests. It omits the fifteen accepted final-entry race tests, so its declared 204-case scope would collect 189. Include all accepted controller files plus the new correction tests and freeze fresh exact expectations. Evidence: `plan-a2-task2-review224/pure-interface-results.json`, `plan-plan-a2-full-score-operational186/task2/green/pins.json`.

## How verified

Read the six CPU members, unchanged tests, accepted Task one marker/CPU-proof endpoints, Task two plan and original native bank/domain/calibration paths. Independently rehashed all 210 frozen members; pins match `52858183652f0ad2aa3a8ec1b264838245d2e34fb0d0bd7f5d7c9688938ad933`. The original 107-test SHA remains `4ffdb6b0adba7680247f05d07af8316ab9053fb4c280c923f186c50bc1db1f3e`. Evidence: `plan-a2-task2-review224/input-checks.json`, `plan-plan-a2-full-score-operational186/task2/green/pins.json`.

Brief pure probes execute the actual GPU marker write statement and real CPU consumers, reject the real eleven-alias manifest, inspect producer/consumer fields and expose the omitted test file. A separate real-supervisor orchestration probe replaces only external metadata/process boundaries: original marker permits a deadline of 1125 after publication margin, but a swapped parse buffer reaches the mocked Popen boundary with 1250 while original file hashes still match. No actual process starts. Both probes complete well under one second. Evidence: `plan-a2-task2-review224/marker-acquisition-result.json`.

The native bank reader/validator, tokenizer/layout/live order, exact bank numeric environment and full unique row/control/support-reason checks are present. Deadline/reap/publication strictness and no retry remain intact apart from the marker-acquisition issue. No new architecture or scientific redesign is requested.

## Execution evidence

Original RED job 23618388 on Delta records 107 of 107 intended missing-implementation failures in each actual Python 3.9.18/3.12.13 environment, exit one and zero errors. Proposed GREEN job 23620336 was cancelled by root while PENDING; its saved scheduler receipt shows CANCELLED with zero runtime. No actual GREEN result exists and no passing suite is claimed. Evidence: `plan-plan-a2-full-score-operational186/task2/red/root-red-01/RESULT.json`, `plan-a2-task2-review224/verdict.json`.

The local pure checks executed only stdlib CPU-wrapper paths and metadata, with zero native/scientific/model/scoring calls and zero actual child processes. Scientific row reproduction and an adapter commit do not apply. Exact findings, source sites, repro scripts/output, source pins and receipt hashes are in `plan-a2-task2-review224/verdict.json` and `plan-a2-task2-review224/run_manifest.json`. The scientific source commit is unchanged context only.

## What is NOT done

No implementation acceptance, full/native test run, resource proof, bound CPU/GPU configuration, full-score launch or scientific interpretation follows. No candidate/source/test edits, git, RS, scheduler, SSH, transfers or other agents were used. Root preserved the original candidate/packet before the correction round. Actual Task three producer/composite/current-root checks and whole-packet integration remain later work; those do not remove the direct Task two endpoint mismatches.

## Open questions

Use one corrected successor with attributable regressions for the unchanged Task one marker, marker read/hash race, original eleven-alias metadata and actual Task two COMPLETE through the real Task one consumer. Preserve original child/supervisor receipts and all source/bank/G3 inputs. Then run the full intended dual-environment fixture scope, including all ninety-seven accepted controller cases and all original 107 CPU cases plus new regressions. Reinspect genuine terminal outputs before any GREEN or Task two acceptance claim. The verdict gives the minimal correction and regression list for each finding. Evidence: `plan-plan-a2-full-score-operational186/task2/green/pins.json`.
