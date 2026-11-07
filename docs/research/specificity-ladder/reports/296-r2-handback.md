# Hand-back 296-r2: Corrected Task 4 source readiness

Agent: independent source reviewer, gpt-6.1-sol. Ticket: Task 4 correction r2. Status: resolved for bounded root CPU validation readiness only.

## What changed

**Verdict: SOURCE READY for bounded root CPU validation. Both review296 blockers are resolved in source; no further concrete blocker was identified.** This is neither native/integration acceptance nor whole operational/GPU permission. Task 3 acceptance294 remains unchanged.

Only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review296-r2/checks.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review296-r2/checks.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review296-r2/verdict.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/296-r2-handback.md` were written. No source, Git, RS, job, remote or real ledger/MAIN operations occurred. Root should lint centrally under the worker RS prohibition. The requested author correction report/handback were read for context; findings below rest on actual source, original interfaces, pins and independent checks.

Resolved blocker 1: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet289-r2/candidate/tests/test_full_score_integration.py:280` preserves the original root `verify_runtime_pins` before the inherited fixture replaces it, then restores it through the delegating spy installed by `restore_root_gates` (`:260`). The spy calls `real_verify(b,g,c)`; original GPU/CPU module loading, closed config validation, packet/source/input/bank/admission/protection and cutover validation remain active. Loaded GPU guards receive an admission spy that calls their actual original function. `consumer` likewise delegates to `real_reviewed_admission` (`:384`), and no longer replaces packet/input validation with event markers.

`closed_evidence` (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet289-r2/candidate/tests/test_full_score_integration.py:178`) supplies the actual validators' required synthetic manifests, exact 422 ordinary-input/eleven-alias/role closure, GPU resource/capacity/admission documents and CPU resource decision. Evidence remains explicitly synthetic and temporary. The original semantic algorithms are preserved rather than replaced by acceptance flags returned from callbacks. New negative cases (`:547`) reseal fixture hashes/configs so resource review, capacity job, admission scope, successor completeness, CPU resource acceptance and root cap damage reach the intended semantic validator; reason matching and delegating-spy counts prevent an unrelated earlier rejection from satisfying these cases. The full positive case asserts repeated root gate/admission calls and one real consumer admission call.

Resolved blocker 2: `route_main` (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet289-r2/candidate/tests/test_full_score_integration.py:171`) routes only the fixture MAIN constant consistently with GPU config, CPU G3 root and CLI work directory. Every freshly root-loaded GPU guard and the newly loaded consumer receives that routing. Assertions explicitly preserve the original fixed source runtime S and original source commit. The new wrong-MAIN case (`:581`) first builds the coherent fixture, then changes only the release MAIN and requires original consumer rejection before the CLI. No original MAIN, real score or canonical ledger is written; native lineage and score publication continue using owned temporary paths.

All 17 accepted production component files remain unchanged. All original 25 cases' assertion ASTs and decorator/parametrization ASTs are preserved, with seven additional distinct negatives for 32 total. The true native normalizer/protection, final postactivation/consumption, exactly-one original frozen CLI boundary, partial/no-retry behavior, unsupported/control semantics and original atomic stage writer/manifest/full-domain audits remain in the test source. Actual numerical/model work remains forbidden and fake transport/hardware/process observations remain explicit boundaries.

## How verified

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review296-r2/checks.py
```

Observed exit zero in approximately 2.98 seconds. Supplied packet/test digests match; all nine own packet members, frozen dependency/source pins and 17 component hashes match. Independent AST checks find 32 cases and preserve every original test assertion with multiplicity plus decorators. Spies delegate to saved original functions. Extracted namespace routing plus the first two original release checks accept the coherent temporary MAIN and reject wrong MAIN while preserving S; no application/native module was imported. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review296-r2/checks.json`.

Exact packet pins SHA: `7dc299d5f9662b81dd90289f7a1369b0d6bc63f130027d4469895628cf1cfec7`. Test SHA: `f60fafe49d5d3f14f226c7a6286cd7a8ce54153d4cd9b454ff4b0a080f25e9fa`. Reviewed source/diff against preserved r1 and original validators, observer, manifest/proposal/release contract, source-only evidence and relocated wrapper evidence directly.

The observer selects only the new integration file and now requires 32 complete passing cases per normal supported environment. Explicit rootdir/confcutdir, disabled cache/plugin autoload, fresh Alignment output/basetemp, original source/pin checks, interpreter identity/origin logging and bounded timeouts remain. No duplicated accepted 379-case run is needed while production bytes stay identical.

Resource assessment: two CPUs, sixteen GiB, 900 seconds total and 360 seconds per environment are reasonable as a bounded diagnostic test proposal, with root's dispatch decision still required. They are not a validated runtime/RSS upper bound. Restored real packet/source/422-input/admission checks repeat across 32 cases and add unmeasured work; neither diagnostic285's 193.165566-second mgnp path / roughly 3.09-GB cumulative job peak nor Task3's 205-second two-CPU/eight-GiB run bounds this workload. Intended full-domain accounting remains one reconstruction, four serial audits, five context loads and eight row/positive-key enumerations per environment; at most one prepared context and three score graphs are rooted at source level, with additional unmeasured buffers/native temporaries. Timeout must remain evidence of failure with no automatic retry.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No r2 native import, pytest/integration case, full-chain GREEN, measured resource feasibility, source publication, binding, submission or GPU action. Both supported environments still need complete actual 32-case results, exact identities/origins, named coverage, logs/XML/provenance and observed resource/time behavior. Any first native/interface failure must be preserved and diagnosed without bypassing validators or editing accepted production bytes.

All actual operational bindings and feasibility remain null. Actual source/input/cache/SIF/namespace closure, genuine resource/cost proof and capacity, reader-safe reservation plus COMPLETE successor, full native lineage/budget normalization, actual job/full-only admission, fresh owning CPU proof/current catalogue transfer, usage/protection/allocation/deadline checks and once-only remote release remain separate real GPU admission gates. Full scientific result acceptance and summarize/effects decisions remain later gates.

## Open questions

None blocks a bounded root CPU validation attempt of these exact source pins. Default: root may dispatch the proposed isolated CPU-only observer, inspect all results before Task 4 acceptance, and preserve every operational/GPU gate.
