# Review272 correction amendment

Status: handed-back.

The distinct corrected packet is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded`. Only the three consolidated review findings are addressed. Frozen r6 source and evidence remain unchanged; its entire recorded file hash manifest still matches. This is source implementation evidence for independent re-review, with no native or deployment acceptance.

## B1: retain host evidence outside child writable storage

Actual output now has the shape `job-<actual-job>/child/execution`. Host receipts, command records, stage terminals and logs remain at the job root. The single container writable bind targets only `job-<actual-job>/child`; the rest of the staged tree retains its readonly bind. The host validates this layout in command construction and derives its physical receipt root separately. `aggregate.py` requires the independently bound host receipt at the job root, outside the child subtree. Stage terminal refs use that same root.

Focused pure tests reject the old output layout and inspect the actual generated mount plan. The payload and inner receipt paths are writable according to its explicit longest-target bind; host-before, prior command/terminal and final host receipts are outside that writable bind. These tests model command permissions only; actual container permissions remain a root deployment gate. Existing distinct inner receipt names are byte-for-byte preserved. Evidence: `test_review272.py`, `evidence/source.diff` and `evidence/static-self-review.json`.

## B2: preserve both original stage bounds through preparation

`execute_stage` captures an absolute wall bound and corresponding monotonic bound before source checks, image checks, command construction, durable command receipt and log I/O. It passes those original bounds into `supervisor.execute`. The supervisor can only shrink the wall bound with allocation end observations; it never adds a fresh cap after preparation or a controller query. Both clocks are checked after the final pre-launch allocation query and immediately before `Popen`. Expired preparation or query time prevents launch. A zero exit observed at either bound fails, including expiration during the final controller query. The original shared cleanup function is unchanged, and a failed stage aborts the remaining sequence. Evidence: `supervisor.py`, `bridges/host.py` and `test_review272.py`.

The focused tests cover slow command I/O, either clock already expired, either clock expiring during the final query, successful use of the remaining original budget, and late zero exit with exactly one cleanup. Original stage caps, final reserve and allocation resource checks remain unchanged.

## B3: exact repaired families

The promoted families are independently fixed in the verifier and tests to `test_prepared_receiver_resource_identity_and_capacity` and `test_prepared_final_barrier_after_all_costly_work`. A self-consistent partition that promotes the former wrong family is rejected. Full collection, parity membership and multiplicities are unchanged: 223 original nodes, with partitions of 112 and 111. Evidence: `evidence/static-self-review.json` and `partition.json`.

## Pure checks and provenance

The new focused tests first produced 12 failures in each exact interpreter before implementation. Both RED sources and attributable command/hash records are retained. Evidence: `evidence/red-base.log`, `evidence/red-mgnp.log` and `evidence/red-test-review272.py`.

The final combined suite passes 46 of 46 cases in each exact interpreter: BASE 2.68 seconds and mgnp 2.29 seconds. Every original test function AST is unchanged; only the shared synthetic terminal helper uses the successor revision and host/child layout. Evidence: `evidence/green-base.log`, `evidence/green-mgnp.log` and `evidence/static-self-review.json`.

Source-bound observer dry runs and actual relocated shell-wrapper dry runs exit 0 in both interpreters. Shell syntax checks pass. Python 3.6 host syntax and frozen-r6 integrity checks pass. Normal interpreter startup is preserved; recorded pytest versions/origins are BASE 8.3.3 and mgnp 9.1.1. All pure subprocesses have short explicit timeouts. No hook rejection occurred this round. Evidence: `evidence/observer-base.json`, `evidence/observer-mgnp.json`, `evidence/relocated-base.json`, `evidence/relocated-mgnp.json`, `evidence/interpreter-base.json`, `evidence/interpreter-mgnp.json` and `evidence/run_manifest.json`.

The explicit inventory has 1133 files and eight unchanged aliases. Actual config, job, output, account, partition, QoS and expected bindings remain NULL in templates. Full baseline registry closure, corrected native fixture bytes, original conftest/baseline/preflight controls and stage-specific inner receipts are unchanged. Namespace constants, source pins, transport inventory and unbound command proposals now target r2. Evidence: `evidence/static-self-review.json`, `bridges/config.template.json` and `proposal.json`.

## Frozen hashes

| Artifact | SHA256 |
| --- | --- |
| Source pins | `0028bac99907b0f44781d668d3cd97f58030ac51c493c857456a58b90b7b1833` |
| Partition | `73aa13bd780837687cc2953fe6f64cd1df60b92056d856b7aad74d0dfb8a5306` |
| Transport inventory | `0d35b0ed94c5e5eb0759adee9add614bbe21842a9d66d34e121aaa87bf17dd9c` |
| Host executable manifest | `46d52e51eefcde1b59147e59750651f44e156607dac1e95a40d814360e64e96c` |
| Corrected native fixture | `e2a7c5622508974fafafe016e9c3d1d55903302f646f05c5f35630570a1f6e86` |
| Runtime, unchanged | `aea07dbf153824f373be70629dd24edc28dd6566cafa5955f43c69fd1119ec90` |

## Remaining gates

Root must independently re-review the frozen successor source and perform actual deployment/bootstrap/config/spool/container/resource checks before releasing any native job. Both complete shards per exact interpreter, original native controls, actual terminal accounting and independently bound final aggregation remain unrun. No Git, remote, scheduler, model, GPU, protected-data or scientific action was performed by this worker.
