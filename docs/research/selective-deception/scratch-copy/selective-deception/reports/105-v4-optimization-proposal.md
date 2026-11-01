# Proposed v4 optimization diagnostic — October 21, 2026

Status: read-only trace/code audit and independent Astra design review completed. No new training, implementation, reservation or submission. Await high-level plan acceptance before implementation fleet, consistent with the user's stated preference. This is a new prospective study; v3 results and receipts remain immutable.

## Evidence and decision

The user requests additional sparse-necessary training tweaks and useful interim analysis while cleaner datasets are still being built. Prior advice against a broad grid is not a restriction on this newly requested bounded diagnostic. No numeric compute-cap increase was supplied.

Sol audited v3 saved histories and source. Restricted union-W peaks at58.99% reduction/update1344 and ends58.35%; union-HW peaks58.74%/1472 and ends58.09%. All-W improves57.73%/1024 →63.79%/1280 →65.13%/1408 →65.27%/1536, with16→23→25→28 deterministic removed heads. Stochastic training T averages0.633 over1025–1280 and0.557 over1281–1536. These support testing further optimization, not predicting90–100% suppression.

All-head binary masks remain empty through640 updates, first nonempty704; union first nonempty320. Initial logit is log((N−1)/1), hence6.930 for1024 candidates versus4.625 for103. Fixed expected removal1 makes initial individual-head removal much less likely in all-head search. Expected removal10 over1024 gives initial logit log((1024−10)/10)≈4.619, approximately the union's initial per-head probability. Candidate content differs too; this is not an explanation proved by the existing contrast.

Training already uses hard binary stochastic masks with straight-through gradients; export is deterministic binary. There is no established fractional-forward/export bug. Do not confuse expected binary removals with the generic hard-concrete nonzero-support statistic. Existing all-W late scalar WT cost averages0.0777 vsT0.557, but production gradient component norms were not recorded; scalar magnitude does not establish gradient dominance. Existing HW halves WT coefficients relative to W, so it is not a clean add-H contrast.

Astra reviewed these findings and recommends initialization/horizon first, withdrawing its preliminary4xWT preference. Root accepts this recommendation for the proposed study.

## Proposed fixed first batch

Two fresh all-head W fits, each3072updates, seed0, initial expected removals1 vs10. Keep AdamW lr0.03 constant, weight_decay0, rho0, batches, sampling/gate-noise streams, data, donor policy, validation cadence64, export semantics and WT objective unchanged. Other gates remain open. No new collateral weights, temperature schedule, sparsity penalty or seed sweep in this batch.

Compare each arm at1536 and3072, plus complete trajectories and validated frontier. The fresh init1 arm supplies a same-source baseline; its1536 checkpoint checks consistency with prior all-W, with numerical compatibility differences explicitly handled. Same initialization with more updates measures horizon effects; equal-horizon between-arm comparison measures initialization effects. Record hard and expected head counts, mask turnover, separate loss terms and per-example H losses/gains; scalar suppression alone is insufficient.

Use a new v4 protocol/run identity and isolated worktree. V3 resume binds the1536 horizon and source/receipt/data/cache identities, so do not modify or reuse its immutable receipts to extend it. Existing checkpoint restore is not a license to change horizon/objective. Fresh fits avoid introducing an additional warm-start migration question. Code implementation must expose only the required new policy/horizon/initialization parameters with explicit identity binding and tests, then independent review and measured calibration before production. Root alone submits; do not execute pretrained models on login or notebooks anywhere for verification.

## Selection and evaluation

Retain v3 prospective90/95 target ordering, smallest mask at target, strongest constrained fallback, separate joint-H/WT and WT-only tiers, WT≤5%PPL andKL≤.05, and zero baseline-capable H loss for joint eligibility. Deduplicate masks, max2finalists. Explicitly report failed preservation frontiers and no-target outcomes. Reused development validation is exploratory and increasingly exposed; more checkpoints do not justify confirmatory claims.

No old native32, SDR-test or WT-test outcomes may choose a checkpoint, hyperparameter, head or donor. Those remain frozen historical/descriptive comparisons. Any new generalization claim requires newly frozen heldout data and the same-protocol baseline comparison after selection; cleaner-dataset effort remains separate and is not consumed by this diagnostic. Coherent D refusal stays desired suppression; honest-task refusal is utility loss.

## Budget and execution gates

Cumulative cap20reservedGPUh; already15.25reserved, remaining4.75. Actual use5h49m1s does not replenish reservations.

| Work | Maximum new reserved GPUh |
|---|---:|
| Technical calibration/identity checks |0.25|
| Fresh init1 fit,3072updates |2.00|
| Fresh init10 fit,3072updates |2.00|
| Conditional limited validation/control or fresh assessment |0.50|
| Maximum |4.75|

First batch ceiling4.25; do not automatically spend remaining0.5. Production history suggests80–95minutes/3072fit; this is an estimate until measured calibration. Start init1 first and release init10 only after technical/runtime checks show it fits. No automatic retry, extension, hidden extra arms or moving compute from the separate dataset budget. Submit with explicit time cap and dry-run; review any failure before additional reservation. Larger followup requires a concrete numeric cap increase from the user. Ending an assistant turn cannot automatically restart root review; arrange only explicitly bounded unattended steps and state any manual review boundary clearly.

## Other useful analyses and deferred contrasts

CPU: gate trajectories/turnover, validation Pareto frontiers, per-example loss/gain concentration and mask overlaps. Root verified W13 andallW28 share onlyL17H26/L17H27 (2shared/39union); this nominates components without proving specificity or stability.

GPU followup:28 individual addbacks to frozenallW28, small size/layer-matched random masks, one independent donor reassignment, evaluated on validation with suppression and collateral effects reported separately. Calibration determines whether a meaningful subset fits0.5h; otherwise request a separate1–2h bound before launching the panel. Addback estimates conditional contributions and cannot certify global minimality; a handful of random controls is a diagnostic, not a well-powered null.

A later zero-WT arm could test suppression attainable when generic-LM preservation is removed. Success would expose a preservation tradeoff under this optimizer, not yield a useful selective circuit; failure would not prove infeasibility. Defer it, objective reweighting and seed grids until the initial contrast establishes what to test next.

Sources: sparse-extension-v3/audit/{summary.json,summary.md}; selective-extension/evaluation/selective_mask.py:301; evaluation/selective_mask_runner.py:839,901,1087; l0.py:76; compute-ledger.json. Read-only Sol audit v4_optimization_audit and Astra review v4_strategy_review. Root compactions unchanged10.
