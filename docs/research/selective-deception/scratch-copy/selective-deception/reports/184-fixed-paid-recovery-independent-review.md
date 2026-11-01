# Independent review184 — one five-block recovery

**PASS, 2026-10-25.** Reviewed the new recovery controller182, tests/template, and machine prefix reconciliation183. No blocking finding remains. Root may finalize a new source-bound recovery manifest, run its CPU-only dry run, then activate it within the already reserved budget. This reviewer made no source, receipt, ledger, cache, guard, job, API or model changes.

The observed failure was an accounting-visibility race after submission, not a failed generation job. Prefix reconciliation binds jobs23191888/23191980/23192484 to the first three original receipts and successful fresh results. Terminal COMPLETED/0:0 and elapsed163/1366/769seconds are explicitly root-supplied scheduler evidence; this reviewer did not query Slurm. The first two were validated by the original controller, while the third completed after that controller stopped.

Recovery imports the exact reviewed179 controller and pins the original eight-entry manifest. Its only accepted work list is the identical original entries[3:]—MASK disinformation, doubling_down_known_facts, known_facts, provided_facts, statistics—with unchanged receipts, reservations, argv, account and scheduler paths. It requires zero additional GPU hours, five remaining precharged hours and cumulative36.6reserved. Neither prefix replay nor suffix reordering/skipping is permitted. The complete original source-binding union, original manifest/guard/state, new recovery source/tests, prefix audit and three prefix receipt/result/guard files must be bound. Prefix results are also checked through strict completion and frozen content/donor/state gates.

The scheduler change is appropriately narrow. An empty exact-job sacct result consults exact-job squeue: one matching active witness waits on that same job; both absent permit at most300seconds of continuous absence. Visibility resets that absence timer. Neither branch submits a replacement. Duplicate/foreign/malformed records, scheduler command failures and unexpected live states stop; exact terminal accounting is still required for completion. The inherited dispatcher stops on nonzero exits/non-COMPLETED terminal states. The grace period addresses propagation only and does not weaken generation or judging coverage.

A separate permanent recovery001 guard and append-only fsynced state preserve all original artifacts and prevent reuse. The inherited per-job gates still require an idle GPU queue, exact job/receipt guard, fresh result, strict completion, frozen input/prompt/donor identities, source/cache integrity, and fully reconciled global billing. Other datasets receive no instructed-INVALID exception. Root must verify the old controller is stopped and no conflicting job exists before activation; the scheduler gate checks again before each submission.

Independent evidence:

- **49 tests passed in mgnp and49 in base Python3.9**:16 recovery regressions plus33 unchanged controller tests. Scheduler/time are mocked; tests cover live-witness waiting, transient absence, five-minute cutoff, malformed/foreign/duplicate records, transport/real-job failure, exact suffix and guard reuse.
- Independently rehashed all prefix receipt/result/guard/source bindings, three checkpoint run manifests, and **108 saved checkpoint batch files (42+42+24)** against183. All match. Prefix audit reports no issues, preserved strict completeness, native512 and all five frozen states.
- Independently confirmed the five suffix receipt hashes match183 and their guards/results/output/checkpoint directories are absent. Original manifest and stopped-state hashes match the reconciliation.
- Global183 snapshot is560 known-settled attempts/$1.97812 with zero pending/unknown reserves and a valid cache prefix. Recovery rechecks the live authoritative ledger before launch and between blocks; this snapshot is not a new spending allowance.

Reviewed SHA256:

- run-fixed-paid-recovery.py: `469d36d9de22a7ebf08b36bf56bd45d57dd8db4cded848a2971b7f8cad48f03e`
- test_fixed_paid_recovery.py: `9af9e952f992d3b7eecdb8ed76316edfa9a296c2df6b1554e5845d0e648dd1e0`
- fixed-paid-recovery-001.manifest.template.json: `aea105e68c1094d59669e3dd6ac0faed2269396583a543d0c16c52ff034cf072`
- machineprefix-reconciliation.json: `e459853a9a75bd11d2281c66a276f20192e9785d584cc0f944a4064c62bc8b8d`

This is operational recovery of a fixed assessment, not a new scientific design or outcome-selected continuation. No new model proof, generation rerun or paid rejudgment is needed for the scheduler fix. The established independent-token-decoding/per-label-cache-linkage boundary remains, and final semantic/coherence interpretation still requires root's scientific review. A completed recovery means mechanically complete acquisition under the frozen gates, not an efficacy claim.
