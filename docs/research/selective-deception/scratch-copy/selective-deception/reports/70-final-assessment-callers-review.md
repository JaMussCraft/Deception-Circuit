# Independent final-assessment caller review

2026-10-19. **Caller review PASS after the native lineage fix and independent WT orchestration probe.** This review covers only the two final callers and their direct integration. Native replay helper internals are reviewed separately in report69. No GPU, real-model generation, heldout outcome inspection, APIs, git operation, production edit, or subagent was used by this reviewer.

## Findings

**Native N1 closed.** The initial caller hashed checkpoint/manifest bytes without validating their contents against the designated export/arm/model. The owner fixed this before any assessment output: `check_finalist_identity` verifies canonical manifest hash; exact amendment/identity arm and candidate space; canonical frozen protocol/WikiText digests; actual snapshot path and freshly streamed original weight/tokenizer/config hashes versus training identity; exact candidate list/hash/count and frozen103/full-head support; scheduled completed checkpoint update64..512 step64; gate payload digest/fingerprint; and deterministic checkpoint-derived K, gate logits and eligibility versus the bound export. Nonhead eligibility must remain false and exact export geometry/all-MLP-open validation still runs. This reconstruction loads only small CPU gate state and introduces zero model forwards. The actual canonical protocol/WT reader also executed successfully outside test mocking.

The owner also closed the concurrency/runtime observations: exclusive output writer flock covers production model load and generation; inflight markers use exclusive creation; deterministic algorithms, CUBLAS workspace and TF32-off are explicit; NumPy/package identity is retained; root execution receipt must match actual allocated GPU name/CUDA/capability and cannot change across resume. Prepared source/runtime/model/data/receipt manifests remain exact-match prerequisites.

**WT PASS. Verification gap W1 closed:** the independent `/tmp/test_final_wt_orchestration_review.py` now executes actual `run()` through runtime, checkpoint restore/export checking, reference writing, exact all-open comparisons, all three finalist scores, final publication and restart refusal. The tiny CPU model and real helper/cache/scoring functions are retained; only allocated-CUDA telemetry, request validation and production weight-loading identity/context are mocked. It asserts exactly96 model calls,16 self-reference calls,16 cache shards,3×16 finalist window outputs, final binding revalidation, and no additional calls on forbidden restart. Base **1 passed** in28.07s; mgnp **1 passed** in13.54s. No WT production blocker remains.



## Checks already verified

The shared receipt schema agrees between callers: all three H/W/HW union finalists, or all six union/all finalists, must be frozen before any heldout outputs, with failed-frontier arms retained. The corrected actual final/prior data are structurally disjoint, eight/eight by truth. Native reads only structural prompt/source/truth fields, assigns all 16 prior H donors once with four assignments per truth-pair cell, preserves original native prompt bytes through manual Llama-3 rendering with no date injection, and does not screen donor outcomes. The known ambiguous prior donor remains eligible.

Native schedules 16 genuine donor completions plus 192/336 target completions, totaling 208/352 and at most 53,248/90,112 generated tokens. Individual unpadded target generation reuses each bank across D/H/R and masks. Completed records and banks are fingerprint/hash bound; an interrupted inflight task refuses automatic retry. Donor completions are charged separately. Bank/dual-stream work still needs measured runtime; token/completion limits are not GPU-time estimates.

WT retains all 16 frozen official-test windows, 128 tokens/127 predictions each, totaling 2,032 predictions per finalist. It uses recipient next-token targets, full-vocabulary predictive KL, token-weighted aggregate NLL/perplexity ratio, paired window summaries, and the mean of per-window NLL hinges. It restores and exactly compares every checkpoint export before creating heldout references; checks compatible finalist retained identities; recomputes actual runtime/model/source identity; uses fresh final-test-only reference shards; and requires exact all-open self/nonself full-distribution equality. It holds one GPU reference block at a time. All-open scoring and every arm remain in denominators, with no ranking or optimizer step. Final publication revalidates frozen bindings, and an exclusive start marker prevents silent restart/reference reuse.

WT's `48 + 16 * n_finalists` bound is correct for actual model invocations: 16 self-reference calls, 16 all-open donor-identity calls, 16 all-open scoring calls, then 16 per finalist. Thus 96/144 calls for three/six finalists. Export reconstruction itself adds no model forward. Each model invocation still includes its dual-stream workload and must be priced accordingly.

## Independent verification

Base Python3.9 focused tests: native **12 passed** (28.26s), WT **11 passed** (34.04s); dependency warnings only. These results precede requested review fixes and cannot certify later source changes.

The actual native `scripts/native_sparse.sbatch --dry-run` executed under its mgnp activation with the real frozen structural input JSONs and exited0: 16 recipients,16 donors,192/336 target bounds, `structural_only:true`, `weights_loaded:false`; no output directory created. This is structural validation, not a tokenizer/model-weight or GPU smoke.

Independent mgnp focused suites: native **12 passed** in19.15s and WT **11 passed** in25.88s on pre-fix native source. Actual WT CLI `--dry-run` in its mgnp shell environment also exited0 using synthetic hash-bound finalist files and the real canonical protocol/WT manifests; reported3finalists,16windows,2032positions,96forwards,0optimizersteps,`weights_loaded:false`. No WT-specific shell wrapper exists; the actual evaluator script was invoked through the same mgnp initialization pattern. The synthetic checkpoint bytes are intentionally not a claim of restore readiness; actual tiny checkpoint equivalence is covered separately. Those native results preceded the final lineage fix; final evidence appears below.


## Final verification and bounds

Final native source independently passed **14 focused tests in base** (16.50s). Final actual mgnp `native_sparse.sbatch --dry-run` exited0 on the real frozen structural JSONs, with source inventory digest `726ae3a7f197e301826fd3ed805b3c1a91edb5dfefaccfc940a3b9797bf054f7`,16donors/16recipients,192/336target bounds, and no weights loaded. Final native source independently passed **14 focused tests in mgnp** (18.19s), closing both supported environments. No full suite was run.

Reviewed source SHA256: native caller `ea84869adc3a31f8568372ea06ca210c9e464533afecfec42326d68feca76863`; native wrapper `d13b7df537fd8bd76c87167ca733f02a0912a3c6d789289851082187228407e8`; WT caller `82030dd932e04ad1a2df557a33d6035d7da11e6782d24e5df2d19ef6c864e2fc`.

This PASS covers callers. It does not substitute for the separate native helper review, measured runtime/storage/memory pricing, root final selection/expansion closure, exact real prepared manifests, or root budget/hardware execution receipts. Actual heldout outcomes and donor blind annotations remain pending. No GPU reservation or launch is authorized by this report.
