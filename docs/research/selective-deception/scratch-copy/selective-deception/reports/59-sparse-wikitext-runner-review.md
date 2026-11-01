# Independent Task B and A/B integration review — 2026-10-19

**Verdict: PASS for the final frozen implementation, with one review finding corrected and verified. No remaining code/spec blocker identified.** This is a CPU code/integration review, not real-model numerical certification or production permission. Root still owns measured reference preparation, numerical/distributional review, cost/reservation decisions, complete integrated suites, and any actual receipt/launch. The pending native fresh-cluster evaluation adapter does not block authorized training.

Scope: ticket06 Task B, final scientific report52, canonical sparse-wikitext-v2 protocol, four Task B production files and associated focused tests in `Deception-Circuit/.claude/worktrees/selective-wikitext`, relative to base08c032f. Task A internals were accepted from independent report57; its implementation/test hashes remain unchanged. Review examined its API use, token alignment, detached references, runtime/cache identity and nonself intervention integration. No production/test edits, git mutations, network/API/install, pretrained weights/inference, GPUs, Slurm jobs, notebooks or nested agents were used. The reviewer wrote only this report and a temporary CPU analytic-check script. Default sandbox initialization failed, so narrow approved escalated commands were used for reads, CPU checks and this report.

## Frozen identities

| File | SHA256 |
|---|---|
| train_selective_mask.py | db85a17cff0dff4806db74af59c6eafdda595774194e2ac41515297e68ac68ca |
| evaluation/selective_mask_runner.py | e2deca68a89b71482fe7b4425ab0f65ba8cd560e4291f45132033a538d666c4d |
| evaluation/selective_mask.py | 952819f1a7ebbf2c5071484244f049cf17a255a15db6a84303bea6739dfad34c |
| scripts/selective_mask.sbatch | 3ac4514212c4a576fea5e50b71b2b8f99a1457f49c98c070753230abf6dd00ba |
| tests/test_selective_amendment.py | 8d368cea850558e4d93bd83c183b8d428ac727fc3551e9c83e9762409d080f71 |
| tests/test_selective_mask.py | 384662ed6839027131f2dc360cab1a9708b0010a05805e24b3e489c3142d1a9b |
| tests/test_selective_mask_runner.py | ec04145ca5f1cbe043984adcb67ca7093164caa61436b783807b72bf5b303d3e |
| evaluation/selective_wikitext.py (unchanged A) | b1e68a3b61ed4b560253dfd5a08a55e2df6b7c2810469ccb7f454344892fa65a |
| tests/test_selective_wikitext.py (unchanged A) | 5f851e96fb70a5b12548d9fc2bb355d0723f995de25999d0ff23a6ed406ab2cb |

Canonical protocol raw-file SHA256 independently confirmed: `f973ecadc851666646795ab5bf9cdb5990326c123acc6c8b3470bd7f8b71255e`. Prepared manifests use its canonical content hash, a separate intentional representation. Actual WT manifest/token/source provenance remains the independently checked report57 snapshot; its embedded manifest hash is `dce0f346dd0381d2ee44ef0b1b5d849afab29230ff8afc1766836f4d23d882bd`.

## Corrected finding

Before correction, `frontier.json` evaluated `compact_useful_finding` on only the selected finalist. An earlier admissible two-head checkpoint with 11% D-surrogate reduction could be superseded by a 20-head checkpoint with 30% reduction, incorrectly reporting no compact result and potentially prompting the conditional expansion. This violated the report52 criterion that any useful compact restricted finding prevents that trigger.

The implementer corrected this to `has_compact_amended_finding(history, baseline, arm)`, scanning all checkpoints without changing best-D finalist selection. The new regression explicitly retains the 20-head finalist while finding the earlier compact result. Reviewed final source contains the corrected call/helper. Root must combine these per-run frontier flags across the complete valid restricted grid before deciding expansion. No automatic expansion/submission exists in this runner.

## Scientific and integration conclusions

- Target suppression retains full-vocabulary complement semantics. H capable-KL and all-H truth hinges have separate correct eight-pair/capable denominators. W-only excludes both H terms from the backward graph; HW uses quarter coefficients for the four collateral components. WT loss uses every clean next-token target and applies its NLL hinge after the complete window mean. Empty capable-H explicitly yields zero KL and absence reporting without the old capability floor.
- Each update shares one eligible-gate draw across all eight SDR forwards and the optional WT forward, reconstructing differentiable graphs for accumulation. Context exit removes hooks and restores the post-draw RNG position, so extra W forwards do not change subsequent gate samples across arms. Only candidate gate entries can acquire/update gradients; frozen base weights and noncandidate/other gates remain protected by eligibility and checks.
- The fixed seeded 119-pair permutation wraps without tail loss for512 updates/4096 presentations. One seeded32-block WT cycle repeats16 times. Validation every64 updates evaluates SDR D/H plus WT for every arm. Gate-only checkpoints bind identity, optimizer, RNG and schedule state, and exact tiny resume is covered.
- Amended manifests reconstruct original SDR lineage, retain the frozen103-head union, and require exact1024 query-head support in all-head space. Runtime identities include source/model/tokenizer/software/hardware, original SDR/WT/protocol and relevant arm/space/schedule settings. Shared baseline fingerprints intentionally omit changing arm/space optimizer metadata while preserving the immutable source/data/runtime lineage.
- WT forwards use split-local different-document donors; references use the declared all-open same-path baseline. A block is loaded/staged individually, with reference digest/fingerprint/token identity validated and gradients detached. Only train/validation references are prepared; test tokens are frozen without test scoring or selection. No prior16 native development outcomes enter fitting or selection.
- Legacy gates remain unchanged. Amendment receipts record user authorization and prior failures without demanding that those failures passed. Source/cache hashes and an actual root-reviewed calibration/profile artifact are verified before production fitting. Root remains responsible for factual historical receipt fields and measured budgets.
- Selection uses validation only, nonzero hard removal and lower D surrogate, then each arm's own constraints; H loss does not veto W and WT loss does not veto H. All D/H/W metrics remain in each frontier, with failed-frontier examples retained. Selection ties follow suppression, size, update, rho.
- Calibration performs actual self/nonself/eval-gradient comparisons and backward checks, profiles both candidate spaces and all three objectives, tests nonempty deterministic export equivalence, measures update/validation/checkpoint/startup/storage/memory costs and restores smoke gate/RNG state. The semantic H-label tolerance is0.02; full-vocabulary WT distributional/reference floors are reported for root interpretation, without inventing a0.02 WT cutoff. CPU fixtures verify the control flow and disposal; real103/1024-head numerical/resource behavior remains unmeasured here.

## Independent verification

All commands used `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` and ran from the new worktree.

1. Focused `pytest -q tests/test_selective_amendment.py tests/test_selective_mask.py tests/test_selective_mask_runner.py` before the one-line trigger correction: **61 passed** under base Python3.9 in28.80s and **61 passed** under mgnp Python3.12 in28.29s. This included actual tiny six-profile calibration and measured-artifact corruption rejection. Existing base warnings concern pandas/bottleneck, TRANSFORMERS_CACHE and ml_dtypes.
2. After production correction/freeze, `pytest -q tests/test_selective_amendment.py`: **14 passed** under base in21.70s and **14 passed** under mgnp in13.63s. A concurrent intermediate run observed the deliberately RED missing-helper regression while the implementer was applying the fix; the subsequent frozen runs above passed.
3. Additional independent analytic script constructed differentiable gate-dependent mock SDR/WT logits, an uneven capable-H subset, eight nonuniform repeated pair presentations and actual Task A references. It compared gradients from `_amended_update` against one independently assembled complete objective, including count penalty and clipping, for H/W/HW. **All three gradient comparisons passed in both environments** at atol1e-7/rtol1e-6. This directly checks the executed accumulation path rather than only the helper formula; it does not replace real-model calibration.
4. Worker report55 records actual sbatch-wrapper CPU dry-run and shell/compile checks. Those were inspected, not represented as independently rerun by this reviewer. Root full suites remain separately required after final source freeze.

Final test-only strengthening: the exact-resume regression now compares the complete latest checkpoint digest (gates, optimizer, cursor and RNG), beyond the selected-finalist gate comparison. Production hashes are unchanged. The table records the strengthened final test hash.

Independent final strengthened-test verification: `pytest -q tests/test_selective_amendment.py::test_tiny_training_exact_resume_and_bounded_checkpoint_schedule` passed in both environments: **1 passed** base23.93s, **1 passed** mgnp22.72s. The final source/test identities above are the review freeze; no unresolved finding remains.
