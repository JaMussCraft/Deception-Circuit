# V4 quantitative validation results

October21,2026. Both3072-update fits passed the complete96-checkpoint audit. **Initialization10 produces a frozen23-head joint-preserving checkpoint with67.17% D-surrogate reduction; the frozen30-head WT-only checkpoint reaches70.12% but loses3baseline-correct H examples.** Root froze these exact audited finalists after independent review130, at2026-10-21T19:02:08.033735+00:00. This derived report changes no selection. No new GPU, generation, source edit or heldout outcome was used.

## Reproduction and matched horizons

Fresh init1 reproduces oldv3all-W exactly through1536updates: identical baseline; all24validation checkpoints agree across19scientific fields, including head sets, D/H logits/argmaxes/probabilities and WT metrics; all1536complete training loss-log records agree exactly. Study/source/policy/horizon/receipt identities and checkpoint/export hashes appropriately differ. Thus the following horizon and initialization contrasts share a verified numerical prefix.

| Arm | Update | Binary removed | D surrogate reduction | H lost / gained | WT PPL rise | WT KL |
|---|---:|---:|---:|---:|---:|---:|
|init1|1536|28|65.27%|5 /4|5.56%|.06963|
|init1|3072|61|74.33%|6 /9|5.47%|.08892|
|init10|1536|58|76.74%|3 /9|4.50%|.07524|
|init10|3072|92|85.70%|3 /20|6.64%|.10083|

Doubling the horizon adds9.07percentage points of reduction for init1 and8.96for init10, while adding33/34binary heads. Init10exceeds init1by11.47points at1536and11.36at3072. Late training continues improving this surrogate but does not retain joint preservation: all four matched endpoints fail at least one frozen limit. In particular, init10's1536PPL is within5%, but KL fails; increased H gains do not cancel lost baseline-correct examples.

The strongest unconstrained checkpoints are init1/update2944:59heads,74.98%reduction, H6lost/8gained, WT+5.81%PPL/KL.09287; and init10/update3008:92heads,86.67%, H4lost/20gained, WT+7.44%/KL.10663. **No checkpoint reaches90%or95%.** These maxima are descriptive; neither replaces the audited finalists.

## Constrained frontier and frozen finalists

Eligibility requires positive deterministic removal and suppression improvement, WT PPL rise<=5%and KL<=.05; joint eligibility additionally permits zero baseline-capable H losses. “Smallest” below is merely a descriptive smallest positive eligible mask, not another recommendation or selection rule.

| Arm / tier | Eligible checkpoints | Strongest constrained | Smallest positive eligible |
|---|---:|---|---|
|init1 / joint|0|none|none|
|init1 / WT-only|5|14heads @960;55.89%|1head @704;10.89%|
|init10 / joint|2|23heads @768;67.17%|17heads @640;60.32%|
|init10 / WT-only|7|30heads @832;70.12%|2heads @384;23.80%|

The existing95→90→strongest-constrained fallback policy therefore selected init10/update768for the joint tier and update832for WT-only; these are the root-frozen masks. The23-head checkpoint preserves all86baseline-correct H examples and gains3, with WT PPL+2.771%and KL.041337. The30-head checkpoint loses3and gains3, leaving total H correctness86; its WT PPL+3.438%and KL.049117pass WT-only limits. Net unchanged H correctness conceals actual losses.

The23-head mask is a subset of the30-head mask; the additional heads are L7H31,L8H10,L13H15,L13H23,L17H27,L19H13,L20H19. This does not authorize pruning, addbacks or a new mask. Expected stochastic removal counts at these checkpoints are46.99/50.20, distinct from deterministic binary23/30exports; this is not fractional-forward evidence.

## Exact saved readouts and approximate probability

D/H/other counts below are exact saved argmax categories over119SDRvalidation pairs, not native generated-response labels. Margins are arithmetic on exact saved D-label and H-label logits. Approximate mean pD is the average per-pair inversion `−expm1(−saved surrogate_i)`, **not exact pD** and not inversion of the aggregate scalar. FP32 computation/clamping can lose pre-clamp probability; inferred saturation counts are0for both frozen finalists and their baseline.

| Readout | Intact |23heads @768|30heads @832|
|---|---:|---:|---:|
|D-stream argmax D/H/other|119/0/0|30/89/0|30/89/0|
|H-stream argmax D/H/other|33/86/0|30/89/0|33/86/0|
|Mean D-stream D−H logit margin|+1.603992|−.878151|−1.109244|
|Mean H-stream D−H logit margin|−.984244|−1.102941|−.950630|
|Approximate mean pD|≈.798920|≈.344618|≈.309062|
|D-margin paired change negative/zero/positive|—|104/3/12|102/2/15|
|H-margin paired change negative/zero/positive|—|65/11/43|46/10/63|

The equal Dargmax counts do not mean the same cases:4D-stream argmax identities change between the frozen finalists. Their H-stream identities differ on7cases. The30-head checkpoint improves mean D confidence/surrogate while introducing honest-task losses. The23-head gains are indices94,101,106; the30-head losses53,67,109and gains2,101,103, using the frozen validation order. Full paired data remain in the audited/derived JSON.

## Membership with actual all-head base rates

Use the frozen original D69/H56/F68supports and103-head union, with **all1024query heads** as each proposal's candidate pool. Exact layer-matched references fix the proposal's observed count in every layer and convolve within-layer hypergeometric distributions, as in report127. Intervals are descriptive discrete central95%ranges, not confirmatory significance tests.

| Proposal / support | Observed | Global expected | Layer-matched expected | Layer-matched95%range |
|---|---:|---:|---:|---|
|23heads / D|1|1.550|2.656|0–6|
|23heads / H|0|1.258|2.438|0–5|
|23heads / F|1|1.527|2.594|0–5|
|23heads / union|2|2.313|4.031|1–7|
|30heads / D|2|2.021|3.688|1–7|
|30heads / H|0|1.641|3.250|0–7|
|30heads / F|1|1.992|3.531|1–7|
|30heads / union|3|3.018|5.500|2–9|

The23-head mask contains D-onlyL14H31and F-onlyL12H2; its other21heads lie outside the discovered union. The30-head mask adds D-onlyL17H27and has27heads outside the union. They share7/8heads respectively with oldallW28and1/2with oldW13. All observed D/H/F/union overlaps lie within their layer-matched ranges. Most all-head candidates already lie outside the discovered union; these raw outside fractions do not establish a distinct mechanism. “Outside discovered F” is set membership only: the coarse sufficient support does not exhaust format machinery or establish absence of format effects/deception specificity.

## Prospective next-step boundary and evidence

The23-head frozen joint finalist satisfies gate124's validation criteria:67.168119%exceeds the exact historical65.265235%, zero baseline-correct H losses, and both WT limits. The30-head finalist fails the gate's H criterion. Root has independently confirmed the freeze and gate; actual assessment execution still requires its separate authorization. Native transfer and strategic-deception generalization remain untested here. Both runs use one seed and reused development validation; these are optimization diagnostics, not replicated comparative efficacy estimates.

Machine-readable derived analysis: `sparse-optimization-v4/optimization-results-derived.json`, SHA256 `dc9484c4aad0482516fcbd7c4eec67087f7bd06283f6883a5ccab06106e6a981`, canonical hash `55db13ff3a2e88a536bf2614682f9380924444bcbbaa2bc73e0eed2ba795a1e3`. It binds the complete audit, supplementary readouts, frozen membership reference and oldv3validation audit by exact SHA, retains the prefix checks, matched rows, constrained descriptive extrema, unchanged frozen finalists, complete membership PMFs and overlap identities. Exact PMF means/masses passed1e−12checks. It is explicitly nonauthoritative and creates no selection receipt.

Root selection receipt: `comparison/selection-receipt.json`, SHA256 `3b095b5774e7521080de92a7af94243acd76e4df9725541f8ce61f55ff23f525`. The derived artifact binds it and verifies both frozen head lists/checkpoint identities.

New standalone final figure: `figures/optimization-v4-final-frontier.png` and `.svg`. It shows all96audited checkpoints against mask size, WT PPL and WT KL, with frozen23/30, oldallW28and unconstrained descriptive maxima clearly marked. The historical provisional audit figure/readouts remain unchanged. Figure hashes are retained in the derived artifact; the PNG was visually inspected for labels/limits.
