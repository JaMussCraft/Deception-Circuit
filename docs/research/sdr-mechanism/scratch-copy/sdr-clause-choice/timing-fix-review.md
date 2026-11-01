# Scoped publication timing fix re-review

2026-10-26. **Spec compliance: PASS for the previously identified interrupted-resume defect. Code quality: PASS for this fix; no new material finding.** The P2 finding in task-review.md is resolved at the source hashes below. Other checks from that review remain applicable; this scoped review does not independently release GPU work or certify pending final execution evidence.

Reviewed timing-fix-review-package.md and the live accept_batch/batch_timing code plus its two regression tests. Beyond the previously reviewed import cleanup, behavior changes are confined to optional timing publication and recovery. No source edits, model/GPU execution, jobs, git operations, or suite repeats performed. Only this assigned review file written.

The accepted terminal remains authoritative and unchanged. A process interruption after its publication no longer makes a missing auxiliary timing file fatal: recovery checks terminal, manifest and bound run hashes, reads decoder/external/max-forward timing facts already sealed with acceptance, and supplies publication latency of at least1second and the invocation's declared initial IO budget. It explicitly marks that publication estimate as unmeasured. Present timing files retain envelope and accepted-file binding checks. Optional timing-write OSError after acceptance no longer manufactures a nonresumable numerical/provenance failure. The existing accepted_batches path still validates complete planned membership, first-step/numerical controls and run provenance before those terminals can be skipped. The numerical/provenance failure stop was not relaxed.

The new tests address the failure boundary directly: an abrupt BaseException between accepted and timing publication leaves the accepted bytes unchanged and recoverable; injected timing OSError across the full fake672-row run yields84 accepted terminals without failure records, and explicit resume keeps the same84 decoder calls and accepted bytes. Existing interrupted-resume and numerical-failure tests remain in the focused suite. Inspected test-timing-gap-red.txt: both new regressions failed before the change. Inspected test-base-timingfix.txt and test-mgnp-timingfix.txt:30passed in each supported environment (base retains its unrelated pandas/bottleneck warning). No reviewer rerun was needed.

The refreshed provisional freeze binds all three reviewed source hashes. Scientific hash is unchanged, `d22cb1edbb8ed2b3109c3142d74460da9aa360b4cfb4615e6b05d21e6ed94d7c`; provisional manifest is `b5a86c90a41e9166d4775dae11d6b8e78a26ad0c9dee58d1ce549b99cf7a99e3`. It remains explicitly provisional and cannot authorize actual inference. Final committed-source rebind, complete independent input-oracle rebind, implementation report and fresh actual-wrapper CPU dry-run are separate evidence checks, not unresolved defects in this scoped change.

Reviewed live SHA256:

- scripts/sdr_clause_choice.py: `24d02bf06d4ef6fd164f1a34fd5c4414ed98b118d673892bca28ee33cc5bade1`
- scripts/jobs/run_sdr_clause_choice.sh: `2c3a771d9edd869042efcc81e117aa664961f655930adb123a44dbc1cc827fe3`
- tests/test_sdr_clause_choice.py: `583a5052c1e206b791827b418e2504115c5005e86367d0a1001c7a6081be2855`
