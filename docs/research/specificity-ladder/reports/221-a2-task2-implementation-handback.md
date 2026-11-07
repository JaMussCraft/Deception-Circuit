# Hand-back 221: A2 full-score owning CPU Task 2 implementation

Agent: assigned implementation worker.

Status: handed-back

Current revision: observer-oracle-only r4 is frozen in `task2/green-r4/`, pins `ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4`. Actual r3 job 23620810 stopped before GREEN because its expected baseline count was wrong: both environments observed the same 19 failures and 3 passes. The additional pass is the valid negative timely_window rejection. R4 changes only the observer oracle to exact observed failed/passed name sets; all production and semantic test bodies remain frozen. Root accepted that narrow correction; independent review precedes root dispatch. Earlier appendices and packets remain historical, preserved evidence.

## What changed

Correction 224 consumes the accepted Task 1 `launch_packet_manifest_sha256` and `publication_deadline` fields directly. Request/marker bytes are read, authenticated and parsed from the same immutable buffers, with another byte check immediately before Popen. The input guard validates every alias declared by the authenticated manifest, returning the actual count of eleven; historical 422 is unchanged. COMPLETE now carries the nine fields consumed by actual Task 1, derived from validated config/request/marker/window and full reconstructed-domain/support evidence. Missing audit evidence rejects promotion. Task 1 production remains unchanged.

Added 22 direct endpoint/marker-swap/actual-manifest/audit/selection regression cases and retained all 107 original semantic cases. Narrow fixture rulings use actual marker field names and eleven aliases; original test names/cardinalities remain. `green-r2/narrow-ruling.json` lists the two original test functions whose fixture field/count assertions changed. GREEN selects 129 CPU cases plus 82 controller and 15 entry 198 cases, 226 per environment. The initial packet incorrectly called its selected controller 82 cases 97 and omitted entry 198; it was cancelled before execution and remains preserved.

Current r 2 pins SHA256 is `80b67c4aac5535dcbfe2b88e192c1cde270bde3b445bfccf97b2307abb628859`, binding 229 files. The new packet runs 22 new regressions against the immutable pre-review candidate first in both environments, then corrected 226 cases in each environment. It requires 20 baseline failures and 2 baseline passes; the two passes are negative alias cases rejected by the original blanket count guard. No original packet, README or dry-run was edited.

The original implementation scope below describes the preserved first revision; the correction above supersedes its interface and verification-scope claims.

Created only the six owned production files under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-operational186/candidate/cpu/`: `supervisor.py`, `validate-phase.py`, `launch.sh`, `config.template.json`, `parameters.template.json` and `request.template.json`.

The validator derives the original unlimited score arguments, executes native context/live/geometry/bank-stage/bank-contract/tokenizer/layout/live guards, compares the actual numerical environment with every bank task, and preserves immutable G2/G3 science. It authenticates the exact 511 ordinary source files and four literal links, all 422 ordinary inputs with 418 immutable roles and four fresh current catalogue witnesses, and five literal namespace aliases. Actual native batches and operation-filtered maps reconstruct the complete row/control identities and unsupported reasons; the complete support mask must match the bound accepted domain proof. No model, weights, freeze, score or effect-content operation is called.

The supervisor permits one full-score request and one child. It binds fetched WAITING bytes, actual CPU job/resources and packet/source/G3/bank identities. Trigger age is at most 15 seconds; the fixed WAITING window is at most 300 seconds. The child deadline is the minimum reviewed cap, initial/current CPU ends minus finish margin, and WAITING deadline minus publication margin. A reaped zero exit is checked against the clock before promotion. Source/input/G3/bank/current-catalogue identities, immutable child parameters and catalogue captures are checked independently before separate supervisor COMPLETE publication. Failed/late attempts remain preserved and cannot retry. Unbound resource templates fail closed.

Prepared root-only execution material under sibling `.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green/`. The frozen pin manifest SHA256 is `52858183652f0ad2aa3a8ec1b264838245d2e34fb0d0bd7f5d7c9688938ad933`, covering 210 files. It retains the unchanged 107 Task 2 cases plus the accepted 97 Task 1 controller regressions, 204 cases per interpreter. Task 1 implementation/tests and every historical packet were preserved. No git was run.

## How verified

For correction 224, syntax/JSON/shell checks passed. Metadata-only AST inventory gives 129 CPU, 82 controller and 15 entry 198 cases; every original 107 test name/cardinality remains. Direct observer preview and an actual relocated-wrapper preview exited zero. No pytest or native suite ran locally. `green-r2/static-checks.json` and `green-r2/relocated-dry-run.json` record these checks; they are not RED/GREEN evidence. The first freeze enumeration encountered a preexisting `__pycache__` directory and stopped; it was corrected to enumerate only the six owned members before producing the r 2 pins. No test or scientific process ran during that setup failure.

The original static evidence below remains historical.

Read the accepted RED receipt and its exact pin identity before implementation. The actual root job recorded 107 intended implementation-missing failures in both interpreters, with zero errors; the root accepted that RED observation.

For this implementation, base-Python AST parsing passed for both production Python files and the GREEN observer; three template JSON files parsed; shell syntax passed for production and observer wrappers. The observer dry-run exited zero and printed both original interpreter commands and 90-second per-environment bounds. An actual relocated observer-wrapper dry-run also exited zero and did not create an execution directory. Evidence is `green/static-checks.json` and `green/relocated-dry-run.json`.

No pytest or native suite ran locally. These static checks do not establish GREEN or genuine owning-proof performance.

## Execution evidence

Root reported the first GREEN job 23620336 was cancelled while confirmed unstarted, terminal CANCELLED with zero runtime. This worker did not query or change the scheduler. No r 2 suite result has been observed by this worker. The prospective r 2 packet requires 22 baseline cases (20 failures,2 passes) and 226 corrected passes in each supported interpreter, no errors/skips and matching test names. No genuine native rows or numerical baseline were executed.

Fresh `codex-usage --pause-at 80` returned 23 percent used/77 remaining, status ok and should_pause false; reset is 2026-11-13T16:18:29Z. No expired exception or old 33-percent boundary was used. There is no new native run_manifest or scientific commit. Current candidate provenance is the 229-file r 2 pin manifest above; original RED job/provenance follows unchanged.

Accepted RED evidence: Delta job `23618388`, root observer normal completion, receipt `.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/red/root-red-01/RESULT.json`. Python 3.9.18 and 3.12.13 each observed 107 of 107 intended body failures, zero errors, and no skips. The receipt pins SHA256 `f225d7dc1d9a431d0e102b796c8cf938f3372b56569fe0ac0ea5ef576203d75e` and immutable scientific source `50e947bb852613e3a270082651f2bd1b7bb0c525`. This reproduces the missing-implementation baseline as 107 failures against 107 expected in each environment.

This worker's execution consisted only of reads, owned-file writes, stdlib syntax/metadata and dry-run checks, all final checks exiting zero. There is no new Slurm job, scientific row output, numerical baseline or run_manifest from this worker. The fixture inventory expects 204 of 204 passes per interpreter; actual GREEN is not yet observed. The prospective native validator requires 59,652 rows and 3,396 controls but has not executed them. `green/pins.json` provides exact candidate/source provenance; no new scientific commit or admission is claimed.

## What is NOT done

The correction packet is a prepared root CPU fixture dispatch, with no worker-owned process left running. Root still needs attributable r 2 RED/GREEN and independent correction acceptance. Actual owning-resource selection, fresh Task 2 job/packet catalogue witness, real finite-window owning proof, Task 3 composite, full packet integration and scientific/GPU admission remain separate. The Bridges proof running under separate source was not touched. No new scheduler, RS, remote, transfer, source publication, git or additional-agent action occurred.

The original unbound-scope statement follows; its assertion that no independent review had occurred refers to the first revision before independent 224.

Root has not yet returned an attributable GREEN receipt or independent implementation review. Real resource selection, real fresh Task 2 catalogue witness, actual owning job/config binding, genuine finite-window owning proof, full packet integration, source publication, transfer, reservation, native ledger successor, release and scientific/GPU execution remain separate root work. Passing fixtures cannot provide any of those authorities.

No RS, scheduler, SSH/transfer, source publication, additional agent or edit outside the assigned candidate/preparation/report scope was performed. Default local command setup failed in bwrap before executing commands; approved escalated local commands were used thereafter. No automatic-approval rejection occurred. Report lint remains root's action because the assignment prohibited RS use.

## Open questions

Current root action: use `task2/green-r2/README.md` and `request.json`, never the superseded `green/` observer. Exact command is `bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r2/launch_cpu_green.sh --pins-sha256 80b67c4aac5535dcbfe2b88e192c1cde270bde3b445bfccf97b2307abb628859 --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r2/root-green-01`. Output must be absent. Proposal: one Delta CPU node/task, two CPUs, eight GiB, six minutes, no GPU/requeue. RED bound is 30 seconds/environment and GREEN 90 seconds/environment. Stop/preserve on any unexpected RED/GREEN result; no automatic retry. Root can lint this report, as RS remained prohibited in worker scope.

The following initial dispatch suggestion is historical and superseded by r 2; retain it as evidence of the original scope mistake.

Root can submit the exact command in `task2/green/README.md`, using a fresh absent output directory. The proposal is one Delta CPU node/task, two CPUs, eight GiB, four minutes, no GPU/requeue; each environment is hard-bounded at 90 seconds. `green/request.json` records the exact command and resources. Root should require observer exit zero, 204 passes with zero failures/errors/skips in both environments, matching test names and unchanged before/after pins. Preserve any failed job/packet and request a separately frozen correction if needed.

The real proof must use a fresh catalogue witness bound to its actual owning CPU job and this packet, never another Bridges proof's witness. The compatible witness schema does not make older evidence current authority. Fresh CPU resource review must show the genuine proof and publication margins fit the fixed GPU window; no 720-second child cap or standing-allocation duration may extend it. A FAILED receipt supersedes any partial or late COMPLETE artifact. Default: keep all real execution bindings unbound until root accepts those actual facts.


### Current r3 fixture-only handback

Status: handed-back

Independent review `review224/r2/verdict.json` closed all four production findings and isolated a new fixture inconsistency: `gpu_c` inherited `T1-FIXTURE-JOB`, while the real CPU request guard correctly requires a numeric Slurm identity. Read its exact numeric-diagnosis evidence. Before the change, preserved all six CPU files and the test in `task2/green-r3/candidate-before-fixture-id/`, with `manifest.json`. The sole candidate change sets `gpu_c['actual_job_id']='456'` inside the new `task1_waiting` helper before Task1 config/environment binding. All production file hashes and every original 107 assertion remain unchanged. No numeric guard was weakened.

The specifically authorized tiny actual-marker cases ran locally in both original interpreters with a 12-second bound per interpreter, no plugin autoload/cache/conftest/native/model work. Base Python 3.9 and mgnp Python 3.12 each passed 2 of 2, zero failures/errors, for original deadline pairs 1300/1250 and 1140/1125. Combined elapsed time was 2.95 seconds. `green-r3/tiny-marker-checks.json` retains exact commands, and both XML/logs are pinned. These fixture observations do not provide native scientific rows or a native run_manifest. The original 107-case RED baseline remains the accepted Delta job 23618388.

Root reported job 23620719 cancelled while confirmed unstarted, terminal CANCELLED with zero runtime; its receipt is preserved at `green-r2/root-dispatch/cancel-unstarted-fixture-id.json`. This worker did not query or mutate the scheduler. The original r2 packet and its receipts remain unchanged. No full suite ran locally.

R3 pins SHA256 `0430226d0b3fb3f231292229b5e215dea614ed2da4ea2dd5c7468ef29faf1ba2` bind 252 files. AST/shell checks and relocated observer preview exited zero. Root proposal remains one node/task, two CPUs, eight GiB, six minutes, no GPU/requeue. The observer runs the same 22 new regressions against the preserved original pre-interface-review candidate in both environments, requiring 20 failures and 2 passes, then all 226 corrected cases in each environment, requiring zero failures/errors/skips and unchanged pins. Resources and per-environment bounds remain unchanged: RED 30 seconds, GREEN 90 seconds. The new r2-before-fixture snapshot is additional preservation; it is not substituted for the original semantic RED baseline.

Exact current root command (fresh absent output directory): `bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r3/launch_cpu_green.sh --pins-sha256 0430226d0b3fb3f231292229b5e215dea614ed2da4ea2dd5c7468ef29faf1ba2 --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r3/root-green-01`. README and request JSON carry the same command/resources. Root was notified that the frozen packet is ready. No worker process remains running. No git, RS, scheduler, remote, source publication or additional-agent action was performed; root retains report lint. Genuine owning proof, actual resource/witness/config bindings, Task3 and scientific/GPU admission remain unbound.


### Current r4 observer-oracle-only handback

Status: handed-back

Read both actual r3 baseline XMLs and result JSON from job 23620810. Root reported terminal FAILED 1:0 after 21 seconds. Both environments observed 22 cases, 19 failures, 3 passes, zero errors/skips. The name sets match exactly. The additional pass beyond the predicted two alias-negative passes is `test_review224_actual_Task2_COMPLETE_satisfies_actual_Task1_consumer[timely_window]`.

Exact attribution: this negative test inserts `timely_window=False` into the original CPU COMPLETE. Actual accepted Task1 `validate_release` reads complete/phase then short-circuits on the false timely flag and raises the expected ValueError before attempting the other missing CPU fields. The positive `[None]` producer-compatibility case still fails, as do the other missing-field cases. This pass demonstrates an already-enforced negative consumer check; it does not show that the original CPU producer emits timely_window or satisfies the full contract. No semantic assertion should be changed to force RED. The other two passing alias-negative cases remain as previously explained: the original fixed alias-count guard rejects before examining the additional alias.

Root accepted a narrow oracle correction. Created distinct `green-r4/` without changing production, semantic test bodies, baseline source, previous observer packets or any actual failed output. Every prior 252 pin was checked unchanged. `red-oracle.json` records the exact 19 failed names and 3 passed names from both actual XMLs, with source hashes. The r4 observer requires those exact sets and 22 unique names in each environment, rejecting duplicate, substituted or missing cases; it then retains all 226 corrected GREEN cases in each environment. `narrow-ruling.json` records the precise case and cause. No additional local pytest or native run was performed for this attribution; actual XML plus source establishes it. No new native rows, numerical baseline, scientific commit or native run_manifest is claimed.

R4 pins SHA256 `ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4` bind 266 files, including the preserved failed job's raw XML/logs/results. AST/shell and relocated-wrapper preview exited zero; preview reports 19 failures/3 passes and 226 GREEN cases. These checks do not establish corrected GREEN. Exact current root command is `bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r4/launch_cpu_green.sh --pins-sha256 ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4 --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r4/root-green-01`, using a fresh absent output directory after independent oracle review.

Resource proposal remains one Delta CPU node/task, two CPUs, eight GiB, six minutes, no GPU/requeue; RED 30 seconds/environment and GREEN 90 seconds/environment. Root received frozen readiness commands/pins/resources. This worker owns no unfinished process/job and performed no git, RS, scheduler, remote, publication or extra-agent action. Root retains report lint, independent review and submission. Real resource/witness/owning proof, Task3 and scientific/GPU admission remain separate and unbound. Preserve any unexpected r4 observation; no automatic retry.
