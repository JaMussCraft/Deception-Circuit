# Faster execution: operational options

2026-10-24. Historical options analysis. Root selected whole-H100 portability for preparation; see amendment.md and plan-h100.md. GPU release is held for other-agent Bridges-2 capacity/budget clearance. Shard options below are not activated. Lead compactions6. No code/job/GPU/API/git action is authorized by this document. User requests faster completion and has authorized more GPU resources and delegation; this permits proposing a prospective operational amendment, not weakening the frozen scientific contract.

## Recommendation

Prefer moving the **whole unchanged study** to Bridges-2 H100 if a fresh source-bound calibration and live scheduler checks support a complete-cap allocation. This avoids implementing shard merge/registry machinery. Keep Delta main23162012/sourceca41bfd untouched while preparing the replacement. Cancel it only after a viable replacement is concrete and a fresh zero-attempt gate passes. If the old job starts or has any attempted scientific batch, stop automatic replacement and ask root to choose the scientifically valid continuation.

Live eligibility belongs to `cue_fast_ops`; its current report says all64 Delta H200s allocated, short normal projections weeks away and H200 interactive occupied by an unrelated job. Bridges-2 H100 GPU-shared projects a start roughly17minutes away for both1h and7h. These are transient projections, not reservations or guarantees. Historical H100 model load is about458s. Source/path portability belongs to `cue_fast_seam`; no old calibration transfers between GPU classes or changed source.

## What stays fixed

Exactly384 baselines +8,960 interventions =9,344 scientific rows;640 directed pairs;14 original families;1,168 physical B8/L224 batches;cap64/EOS behavior, every original global batch and slot, prompts/tokens/masks/donors, prefix transplantation and all numerical controls, blinded two-person full-coverage labels/adjudication, complete triples and frozen analysis. Preserve all original inputs, source, outputs, calibration receipts and gates. No response length or outcome, label, baseline capability or effect size determines execution allocation or selection.

## Measured complete-cap costs

Sourceca41bfd calibration23161426 completed663s, not a663s estimate of the main. Independent actual audit and manual closure PASS. Selected7h forecast is21,483.54020392304s, made from compute10,438.979487398174s; writes485.588990226388s; packing4,687.342092560604s; audit133.99798470188398s;25% margin on their15,745.90855488705s subtotal; then1,801.154510314227s fixed costs. Fixed costs include measured premodel261.267147064209s plus model load, and unchanged120/1200/90/120s startup/premodel/shutdown/safety allowances. Packing is1,168×4.013135353219695s. Calibration performed44.507GB maximum-payload I/O stress, which must not be confused with expected main output size.

H1007h fit is uncertain: keeping all other old costs, it permits compute≤13,412.147324259742s (~1.285×H200). Replacing old~9.887s load with historical458s lowers compute allowance to~13,053.657s (~1.250×). Changed filesystem/verification/packing terms require direct measurement. One-hour **full** main cannot fit the old noncompute bound even with zero compute. Request live projections for a longer complete-cap H100 allocation as fallback; do not trim the panel or use typical short completions to force7h. H100 memory80GB exceeds old20.268GB peak, but actual calibration still proves fit.

## Options

| Option | Operational work | Conservative timing | Decision |
|---|---|---|---|
| Keep existing Delta monolith | None |21,483.54s cap bound after its queue wait | Retain until replacement proven |
| Entire panel on one H100 | Portable binding +new exact-H100 calibration; no merge | Fresh calibration decides;7h not assured | Preferred if live queue/runtime fit |
| Same-H200 contiguous80-batch shards | Small range/receipt/merge extension +fresh calibration |15 shards:14×80 plus48; worst3,505.39s; summed bounds13.188GPUh | One-hour fallback if eligible; only one interactive job at a time, normal jobs may run concurrently |
| Same-H200 contiguous200-batch shards | Same extension |6 shards:5×200 plus168; worst5,467.48s; summed bounds8.546GPUh |90min request insufficient; use≥92min plus operator scheduling rounding |
| Multiple GPU workers in one allocation | Per-process GPU isolation, aggregate CPU/RAM/I/O calibration and worker receipts | Not measured; shared I/O/startup cannot be divided by GPU count | More complexity and larger contiguous request; defer unless scheduler demonstrates advantage |

Shard numbers are planning calculations, not release forecasts. They reproduce the full21,483.5402s bound exactly when all1,168 batches are selected. For each contiguous range: count65 plain+1 empty forwards per baseline batch;1 family capture+128 patched forwards per intervention batch; sum measured cold+(count−1)warm-max per exact signature; count attempts=n,terminals=n,progress=n+2,metadata3,assembly1,emergency1; packing=n×4.013135353219695. Conservatively retain the **full-panel**26.732931075966917s audit CPU and maximum full-panel assembly write, then add per-range attempt n/terminal2n read charges,25% subtotal margin and the entire1,801.154510314227s fixed cost. Different signatures have materially different recurrent maxima (.061–.139s; baseline plain .223s), so equal range sizes are not equal costs. Fixed80 has only94.61s slack beyond its existing bound. Concurrent I/O contention and fresh timing can invalidate it. Do not automatically reuse80.

A one-hour partition offers one eligible interactive allocation at a time, not15 simultaneous slots. Submit disjoint frozen shards to normal allocations in parallel only where live policy/resources permit; at most one interactive slot. Do not move shard work to a different GPU class on old calibration. Mixed-class scientific panels are outside this proposal.

## Smallest implementation if fallback is selected

Keep decoder/hooks and all control recipes untouched. Add range ownership, immutable plan/claim/receipt metadata and strict CPU merge around the existing B8 loop; use the existing six bounded record classes and ceilings conservatively wherever possible. No new scheduler daemon, adaptive allocator, token checkpointing, cache union, dynamic shard resizing or numerical shortcut. Root commits reviewed source, freezes science-equal provenance and obtains fresh calibration before main release. See `amendment.md` for release gates.

Evidence read: frozen `../spec.md`; `../calibration-audit/{actual-review.md,actual-audit.json,manual-closure.json}`; actual `../operator/calibration-ca41bfd-20261024T203619Z/{protocol.json,progress.json}`; selected `../operator/operations-main-proposed-25200-ca41bfd.json`; prior `.scratch/sdr-native-controls/sharding-spec.md` as an integrity pattern, not an implementation requirement. No notebooks/models were executed.
