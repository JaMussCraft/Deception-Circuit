# V7 aligned-prompt position bridge implementation plan

> For agentic workers: use subagent-driven-development, one implementation task and independent review. Root alone commits and launches; do not spawn more agents.

Goal: test whether broadening intervention positions changes the fixed New30/L17H27 effects on matched D/H/F/I prompts.
Architecture: one new runner reuses frozen V6 manifest, hooks, metrics and model identity. A separately frozen selection document binds report212, cases, supports, position mapping and statistics before GPU outcomes.
Tech stack: existing Python/torch/nnsight0.7.0 stack, mgnp live, base pure/toy tests where supported; no installations.
Spec: ../reports/212-v7-position-bridge-design.md (final prospective authority; resolve disagreements with root before coding).

## Global constraints

- Existing isolated worktree: Deception-Circuit/.claude/worktrees/selective-components-v6, starting HEAD57c53ac539d55ae5c6bff67cdb5be31c2289e802. New V7 files only; old runtime/data remain immutable. Not alone in codebase; preserve others' edits.
- No pretrained model on login, notebook execution, API calls, worker git changes or job submissions. Root cap40 cumulative reservedGPUh;38.0166666667 alreadyreserved. New study initial root allowance<=25min reserved (smoke10/main<=15), not permission for worker launch.
- Fixed16 previously exposed SDR validation scenarios×DHFI=64variants. Same original independent honest donors; no data/head/mask search, exclusion/refill or new free-generation assessment.
- Seven conditions: intact; new30_final, single17_final, release17_final; new30_prompt, single17_prompt, release17_prompt. Release17 means New30 minusL17H27 recomputes, not cachedcleanrescue.
- Final condition: donor own last nonpad→recipient own last nonpad. Aligned condition: unpadded index p maps q=Ld-Lr+p only if0<=q<Ld; write at recipient nonpadpositions only; unmatched prefix untouched. NO tiling donorfinal, no padding values, no prefix/native response packing. This is NOT an exact V5eval5 protocol replication.
- Every metric sign/denominator and limitation from report212 stays explicit; first-token choices are not freegen/refusal outcomes. Store both native andfp32argmax; numerical margins/probs/KL explicitlyfp32; additionally save native requested/truth margin as separate native fields.

## Review focus

Unequal donor/recipient lengths and both padding sides; accidental donorfinal broadcasting; writes to wrong heads/positions; source/case/receipt drift; changed batching misrepresented as exact historical replication.

## Task 1: self-contained position-bridge runner and tests

Ownership:
- Create component_analysis/selective_v7.py
- Create tests/test_selective_v7.py
- Create .scratch/selective-deception/component-analysis-v7/launch.template.sbatch and task-1-report.md
- Root writes selection/receipts; worker may create CPUdryrun output in new subdirectories only.

Interfaces:
- CLI --manifest frozenV6path --selection frozenV7path --output-dir NEWpath --mode dry-run|smoke|main --execution-receipt PATH --batch-size4.
- Dryrun verifies source/data/selection/support bindings without model construction and writes plan.json with exact caseIDs,7conditions and source hashes.
- selection expected to bind fullpanel hash, report212hash, fixedcaseIDs, fixedsmokecaseIDs(firstscenario/cell allDHFI), supports and mapping/statistical design. Agree schema with root.
- Reuse selective_v6.last_nonpad,padded,final_replacements,metrics,identity_controls,sha256,_write_json; selective_v6_followup sourceclosure helper if appropriate. No changes to shared functions.

Steps:
- [ ] Test mapping on unequal lengths and mixed padded rows; donorlonger crops earlier donor prefix, donorshorter leaves recipientprefix untouched, final mapping equals existingfinalcondition, padsneverwritten; eachrowusesitsdonor, supports exactly30/1/29.
- [ ] Test receipt rejection/source drift/badcasecoverage/one-use behavior; no pretrainedmodel in dryrun. Meaningful tiny randomLlama test proves hook writes and native/fp32 selfidentity, not merely mirroring implementation.
- [ ] Implement aligned_replacements by gathering donor head banks at explicit rowwise mappedindices and recipient positionmask. Clean selfcontrol maps ownpositions with no reorder, full andfinal, exactbackend native+fp32 proof.
- [ ] Run same64cases in same fixed order/batches as V6 followup where possible,7conditions. Technicalsmoke first4stratumscenarios×4variants×7=112rows; main448rowsincludes theseagain, not extraN.
- [ ] ActualGPU controls: plain/noop/finalself/alignedself identities; falsepositionmask identity; earliest affectedlayer siblings/allpositions writeisolation for aligned interventions; originaldonor capability native+fp32; new30_final and release17_final historicalV6anchors check with precision/batching metadata (do not silentlyforce or relabel drift).
- [ ] Save plan/header/rows/controls/completion with hashes, exact recipe, lengths/indices/coverage, rawargmax IDs, requested/truthcorrect booleans, fullvocabidentity scalars/flags, runtime/peakmemory; old fulltensor artifacts not required, disclose boundary.
- [ ] Live requires SlurmGPU, A40, nnsight0.7.0, frozenmodel files verified before load, one-use hashbound receipt, sourceimport closure, noauto-retry. Shared budgets enforced byroot ledger andSlurmwalltime.
- [ ] Run only focused new tests plus necessary helper tests in mgnp/base (BLAS1, toy nnsightintegration skips onbase expected). Run actualwrapperCPUdryrun. Report exactcommand/outcomes, sourcefiles, estimate and remainingconcerns. Never claim fullsuitepass.

## Root integration and acquisition

- [ ] Independentreview newfiles+selection+wrapper; fix blockers throughworker, freeze source byexplicitfilelist.
- [ ] Root10minA40smoke after actualwrapperdryrun+schedulertestonly+ledgerreservation. Audit actualcontrols/casecounts, nohypothesistuningfromsmoke.
- [ ] Root measured main wallrequest<=15min if fit (otherwise explicitoperationaldecision withinremainingcap); full448rows. Nooutcome-dependentexpansion.
- [ ] Independent rawartifactaudit; pairedscenario-bootstrap summary with rawDHFIeffects, predeterminedNew30positionincrement andD−Icontrast, release/single secondaries, argmaxtransitions/coverage.
- [ ] Astra final interpretation; save concise sharedreport +rootcompletion/hashbindings and reconcilebudgets, no merge/push automatically.
