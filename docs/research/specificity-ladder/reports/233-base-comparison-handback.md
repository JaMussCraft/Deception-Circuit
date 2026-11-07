# Full-size BASE metadata comparison independent audit

Status: handed-back

## What changed

Accepted the completed BASE same-environment algorithm comparison for the frozen metadata builder only. Full original/candidate publisher-format streams have identical SHA-256 and byte count, and the entire summaries—including every storage tier/component—match. No new static or receipt finding blocks this narrowly scoped result. No source files changed.

For this pair, build time fell from 2628.661 to 1882.742 seconds (28.38%); actual supervised child wall fell from 3748.805 to 2996.172 seconds (20.08%). Stream time rose from 986.934 to 1004.647 seconds (1.79%). These are observations from one pair at different times. Both recorded allocations were on cn034 with the same EPYC 7763 model, four CPUs and 192 GiB, although account/partition differed. The brief’s suggestion of different recorded nodes is not supported by these receipts.

Memory did not materially improve: child wait4 peak RSS was 133,804,548,096 original versus 133,830,811,648 candidate bytes, a 0.020% increase. Whole-job cgroup peaks were 134,215,749,632 versus 133,858,664,448 bytes. These scopes differ; neither is a prepared receiver bound. Own-job memory event counters show no OOM/max events. Shared ancestor historical events are not attributed to these jobs.

## How verified

Read raw accepted packet code, both complete/child/stage receipts, bound config, allocation and memory snapshots, sample records and preserved terminal scheduler accounting. Used stdlib-only JSON/hash/arithmetic checks; never rebuilt the giant inventory. All packet members match both recorded harness manifests. Candidate config SHA is `ac2a0bf852e53a863dc0e46c4a303e54de015b5493a8bdfee67a837d20ba6773`; candidate harness manifest is `a52c8696e83b525f64347ec8d714fb9bc450befa2e4638d6a46a6192eea8befe`. Candidate builder SHA remains `765b22a006ab519186a168bf455f4084915457d4ffce88881e76bf31b71a37cb`.

The full 11,421,127,399-byte stream SHA is `c738a185b9a79ef8873113e63aefa197a820f0a5c117159db055de6f70e0a6c9` in both receipts. The common summary has 246,486 raw keys, 81,904 shards, 4,256 capture shards, 618,117 requirements and 45,042 captures. Full forward/operation counts and all storage bounds match by dictionary equality; the host-RAM tier remains 1,396,027,015,524 bytes. The inventory SHA is `daf672c166396518e9ed207e7c2dc14a5ff4adcc3f2b763d5fbf95b1fc83d9db`.

The source code enforces fresh original live guards before build and after the complete stream, source/snapshot/input pins before/after, candidate builder hash before/after, same-environment original receipt binding and exact full summary/stream comparison before RESULT. RESULT is explicitly incomplete until the supervisor observes normal zero exit before the child bound, then rechecks packet hashes and promotes it. Receipt/result hashes and stage markers agree. Candidate child finished at 2996.172 seconds before the 3300-second bound, with no TERM. Post-run allocation observation remained 592.106 seconds before its end. Original child finished at 3748.805 seconds; its post-run allocation observation remained 740.244 seconds before its end. Both source-before/source-after records agree exactly.

Detailed comparisons, exact paths, metric arithmetic and provenance checks are saved in `.superpowers/sdd/plan-a3/base-comparison-review233/receipt-audit.json`.

## Execution evidence

- Candidate: Delta CPU job 23613360, cn034, scheduler COMPLETED 0:0, job elapsed 3007 seconds; child exit 0, wall 2996.171678505 seconds, user 2724.989372, system 238.233636; no TERM.
- Original baseline: Delta CPU job 23608994, cn034, scheduler COMPLETED 0:0, job elapsed 3759 seconds; child exit 0, wall 3748.804658305 seconds, user 3459.304569, system 243.165237; no TERM.
- Baseline reproduction assertion: original and candidate each produce exactly 11,421,127,399 publisher-format bytes with identical full SHA above, matching the complete summary and all storage bounds—not a prefix or count-only comparison.
- Provenance: candidate `genuine-oracle-executions/candidate-base-r4-01/COMPLETE_COMPARISON.json` SHA `fd2ab6676feffc036bbc52828e9fdf36c06366623ef10f619f5c12dc8de9b7c5`; original `original-base-r3-01/COMPLETE_ORACLE.json` SHA `463591fc08f04a8275042a68e9c884b22c264eac5bf11bd87679a17a5594973a`. This accepted harness uses those completion/provenance receipts rather than a standard `run_manifest.json`.
- Frozen input source commit is `861f84a3938a5e22fa329af0c469b2dd812fe68a`. Candidate `source_commit` and `unpublished_candidate_source_commit` are NULL; the frozen input commit is not the candidate commit. This audit does not confer a published-source scientific-result status.

## What is NOT done

No saved full inventory file exists from this hash-to-sink run; it is not prepared artifact publication or receiver read/parse/freeze evidence. No preallocation runtime, genuine receiver/RAM, fresh source-dependent numerical case, model, GPU or production-admission gate is closed by this comparison. It establishes equality for this full fit-select target in BASE, not all targets or environments, and one timing pair does not establish general speedup or memory savings. No new tests, models, jobs, remote calls, git, RS or source edits were performed by this reviewer.

## Open questions

None for this completed BASE algorithm-equivalence gate. Root may record that narrow acceptance and keep Tasks 2–3 execution, source publication, authentic prepared materialization/resource evidence and numerical/GPU gates separate. Root owns report lint/number checks under the no-RS worker instruction.
