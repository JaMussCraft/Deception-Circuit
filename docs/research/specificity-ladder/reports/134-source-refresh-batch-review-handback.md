# Independent source-refresh batch review

Status: handed-back

## What changed

**Scoped source/spec verdict: PASS. Code-quality verdict: PASS.** Reviewed exact frozen candidate `40fe57289405fd53a3fce02e5d4e47a0ebf78b64` against accepted plan and parent `f5a5687ec12091f0d148b38b301598e9c7cb98cd`. Only helper and focused test changed. Helper SHA is `eaabf9ef8247159686ec6ee00b6dbcb876495a0dac62281bb26077a9eb65fcee`; test SHA is `f3164a051cf18c5f44e7da13b364e02057426e02b7daccd557947afd54c66241`. [Exact source binding](134-source-refresh-batch-review-evidence/static-source-binding.json), [independent diff](134-source-refresh-batch-review-evidence/candidate-diff.txt).

The implementation compiles the full source route graph once under the existing stable mint envelope. A one-shot owner mint and private weak registration bind the scan plan to the original witness object, dictionary, tuple identities and copied nonempty roots/ordered rows. Raw slot changes, forged copies and legacy witness reinitialization cannot rebaseline the proof.

Each refresh still hashes every original file occurrence, including duplicate aliases. Descriptor identity and complete reads are checked before/after; fresh closing file metadata, directory memberships and full route observations run after current protection validation. Route-only normal parents retain current-scan coherence without freezing unrelated catalog content timestamps. Original source semantics, early artifact witness, missing/New30/glob checks, dynamic registry/grader validators and authority/cadence remain intact. New graph/registration memory and constructor time enter existing diagnostics/consumed fields.

## How verified

All substantial tests ran in the root-submitted Slurm CPU job; no local suite or benchmark ran. Independently exercised registered raw slots, original witness dictionary/tuple replacement and reinitialization, raw plan copies, changes after every file had already been hashed, same-inode files behind newly introduced parent aliases, current atomic registry updates/overlaps, complete duplicate-byte occurrence counts and descriptor checks/closure. Original versus batch rows match the unchanged authority oracle. [Independent probes](134-source-refresh-batch-review-evidence/test_independent_batch.py).

The fixed selection also includes the complete candidate helper suite, unchanged earlier independent rejection probes and the selected owner source-cache/copy/startup-projector integrations. It does not use author test passes as independent evidence. The driver authenticates project imports inside the frozen runtime and verifies every ordinary source hash/read-only mode before and after execution; source and harness hashes stayed unchanged. [Exact selection and bindings](134-source-refresh-batch-review-evidence/terminal-review-check.json), [frozen proposal](134-source-refresh-batch-review-evidence/cpu-job-proposal.json).

## Execution evidence

The [final run manifest](134-source-refresh-batch-review-evidence/run_manifest.json) binds the full candidate source map, exact harness hashes, actual allocation/accounting, both interpreter results and the raw-receipt interpretation correction.

CPU job `23456990` ran on `cn093` with four CPUs, sixteen GiB, no GPU and a fifteen-minute requested limit. It completed with exit `0:0` after 110 seconds. Both interpreter selections passed 120 tests: mgnp in 36.33 seconds and base in 39.17 seconds. These are fixture suite times, not production source throughput or pilot forecasts. [Actual allocation/accounting](134-source-refresh-batch-review-evidence/terminal-review-check.json), [mgnp output](134-source-refresh-batch-review-evidence/pytest-mgnp-23456990.log), [base output](134-source-refresh-batch-review-evidence/pytest-base-23456990.log), [terminal batch log](134-source-refresh-batch-review-evidence/slurm-23456990.log).

**Receipt interpretation correction:** the raw child receipts contain `models_or_weights_loaded:false`. The selected integration tests did construct and execute tiny injected CPU fixtures. No pretrained weights or production model were loaded. Raw receipts remain unchanged; their field must not be interpreted as absence of tiny fixture construction. [Explicit correction](134-source-refresh-batch-review-evidence/receipt-interpretation-correction.json).

## What is NOT done

No source/driver edits while the job ran, git, RS mutation, scheduler mutation, remote execution, subagents, notebooks, pretrained weights or GPU work. Root owned submission and the RS watcher; reviewer scheduler calls were read-only allocation/accounting queries. The separate native verification job is outside this review.

No genuine new-source prepared data, full inventories, real-input mutation experiment or performance/cap-feasibility benchmark was produced here. Prior real-input acceptance concerns its exact earlier source. The unit checks establish the repaired mechanism and consumed accounting wiring; they do not substitute for observed whole used-path timing or actual admission.

## Open questions

No remaining source blocker was found in this bounded repair. Root may proceed with genuine fresh preparation and source-only measurement on the reviewed bytes in Slurm CPU jobs, preserving original science/ancestry and comparing original/batch byte occurrences on the same new inputs. Record current protection/byte invalidation negatives, initialization, retained/transient RAM and actual refresh costs before a practical readiness decision.

All existing pilot budgets, original charges, source-bound reservation/admission and live allocation/ledger/lease gates remain unchanged. In particular this source PASS does not retarget the original held mask reservation, authorize a retry or settle the existing M1 budget issue. No whole numerical pipeline or scientific execution acceptance is claimed.
