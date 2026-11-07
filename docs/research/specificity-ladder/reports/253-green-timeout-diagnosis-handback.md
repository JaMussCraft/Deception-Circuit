# A3 unchanged-source GREEN timeout diagnosis

Status: handed-back

## What changed

Mapped the six likely failures and proposed a bounded root CPU diagnostic that preserves frozen source, original assertions and the all 223 collection gate. No candidate/test edits or full-suite retry are proposed. No other progress glyph is an accepted test result.

The stored 223-node collector order and normal serial pytest reporter map F positions 85–88 to `test_prepared_receiver_resource_identity_and_capacity`: target100/99 and preparation100/99 attacks. Positions 117/120 map to `test_prepared_final_barrier_after_all_costly_work`: target-payload-restored-mtime and descriptor-marker at final-live-guard. Full exact node IDs are in `suspect-nodeids.json`.

Next expected node 122 is identical-target-tree-before-publication in the final-barrier family. This is only a candidate for the interrupted case: node 121 teardown or the interval before 122 setup may still have been active. No durable per-phase log identifies the actual blocked phase.

## How verified

Validated all 21 terminal-file hashes/lengths against the fetch receipt. Parsed raw pytest progress (121 glyphs), removed the percentage marker and mapped six Fs to the preserved collector list. Original conftest stores session.items order and checks all 223 function counts; autoload is disabled and the command has no parallel/reorder option. No final GREEN JUnit exists.

Two concrete source hypotheses warrant actual traces:

1. The reader returns immutable entry references. Fixture.resource_record retains them, and `_FrozenJSONDict.__deepcopy__` returns itself. The four target/preparation attack assignments therefore appear to raise TypeError before reaching the test’s expected-ValueError block. A tiny stdlib-only extraction of the unchanged frozen classes reproduces this exact TypeError while preserving deepcopy identity. This is strong source-level evidence, not the missing actual pytest trace. If confirmed, any correction belongs to authentic mutable attack construction in the test; do not weaken reader immutability or validator assertions.
2. The two final-live-guard tests inject mutation in the locally passed guard closure. The actual final barrier calls module `live_guard` directly, so that mutation may never execute. Source inspection supports a wrong test seam rather than absent production live checking. Actual traces should distinguish DID NOT RAISE from another exception. If confirmed, inject at the real module live_guard boundary with a delegating spy; retain all timing, mutation, no-writer and original-authority assertions.
3. Timeout may be accumulated fixture/hash/filesystem cost rather than a stuck node 122. Mandatory preflight completed in 262.593 seconds, including 256.049 seconds for selected preparation. It runs inside the 2700-second GREEN subprocess and precedes ordinary test execution. Individual durations/phases are missing, so slow-case attribution remains open.

## Execution evidence

Actual Bridges 50316975 failed 1:0 after 3076 scheduler seconds per root. Preserved observer reports FAILED/exit 1, normal_completion=false and PYTEST_TIMEOUT at 2700 seconds with no final JUnit. Baseline five intended RED completed normally with zero errors/skips in 345.775 seconds; original oracle passed with 62/62 expected publisher bytes and correct module origins. Fixture preflight completed, but none of these facts accepts the incomplete GREEN suite. No actual BASE result is inferred; 23622800 remains root-owned and source stays frozen.

Reviewer ran only a 0.193-second frozen-class/source probe and a pure fake-hook diagnostic-plugin contract check. No native/full test, scheduler or remote work occurred.

## What is NOT done

No actual six-trace diagnostic, proof of a particular interrupted phase, source/test repair, accepted partial test count, increased full-suite bound, test GREEN/source publication or scientific/model/GPU admission. No source/test edits, git, RS, SSH, jobs or extra agents.

## Open questions

Root-reviewable artifacts are under `.superpowers/sdd/plan-a3/green-timeout-diagnosis253/`. Use ONLY `root-diagnostic-recipe-r2.json`; the first recipe is historical and must not execute. Revision2 removes faulthandler timeout/native traceback threads per root’s incident P6 constraint. Durable JSONL item-start/item-finish and normal setup/call/teardown report records are passive; an optional outer supervisor may sample /proc/cgroup without instrumenting native execution.

Two proposed CPU diagnostic children each retain a 600-second total bound: one runs the six exact suspects, the other only next expected 122. Exact argv/env/node files are supplied. Each child still performs original mandatory preflight and collects all 223 nodes. A diagnostic-only plugin then invokes normal pytest runtest protocol for the named subset without mutating session.items or any test assertion. This is necessary because a naive six-node pytest command would fail the original all 223 collection assertion before the intended calls. The plugin fsyncs failure longrepr and phase durations immediately, so the first failures remain readable even if a later case times out. `-vv --tb=short --durations=0` is included; no traceback timer/thread is used.

The plugin and root recipe are proposed instrumentation, not accepted execution. Root must review/freeze/package them, bind original source/module origins/environment, choose actual CPU resources and supervise whole process groups with TERM/KILL/reaping. Existing 32GiB headroom and two sequential 600-second children plus margins suggest a 25-minute CPU proposal; root decides actual resources separately. Every result must remain DIAGNOSTIC_PARTIAL, even if selected calls pass. No diagnostic subset replaces five intended RED plus all 223 GREEN acceptance. Preserve all old packets and outputs; do not edit the frozen candidate while BASE is queued.
