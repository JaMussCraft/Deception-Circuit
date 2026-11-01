# 212 — Prospective V7 position bridge

Decision: proceed with one frozen, readout-scored position bridge on the existing 16 SDR internal-validation scenarios, crossing three already selected masks with final-token versus right-aligned prompt-intersection replacement. Keep original V6 donors. Do not add free generation, a lexical-donor arm, head/path search, or a new dataset to this experiment.

This report is design advice for root implementation/review, not an execution receipt or a claim that jobs have run. No code, GPU, API, or other-study artifacts were changed for this review. Source evidence: reports210/211, `v6_components.md`, V6 `spec.md`/`implementation-plan.md`, and actual V5/V6 implementations cited below. The parent supplies the current remaining envelope of 1.983333 reserved GPU-hours; root must verify the ledger before reservation.

## Question and interpretation

Does expanding the frozen honest-donor replacement from the final prompt token to all aligned prompt tokens change New30's effect on requested-answer preference, and does L17H27 retain its shared D/I role in that expanded intervention?

V6 established local D/I margin effects without any SDR requested-choice changes. V5 includes all-position/free-generation effects, but changes in hardware, model wrapper, prompt family and decoding prevent attributing those differences solely to intervention position. V7 keeps the V6 runtime, cases, donor assignment and readout fixed while varying position support. It bridges intervention support, not the entirety of V5's behavioral result.

## Fixed population and conditions

Copy, hash and verify the exact SDR `split=validation` cases from `.scratch/selective-deception/component-analysis-v6/panel.frozen.json`: 16 scenario clusters, four construction strata with four scenarios each, D/H/F/I per scenario, 64 cases. Retain case IDs, token IDs, requested/alternative/truth labels, donors and provenance exactly. These are previously exposed internal-validation cases, not independent confirmation. No exclusions or replacements based on V7 effects or capability.

Use the same honest donor for all four variants of each recipient scenario and all conditions. Preserve original V6 source-ID/scenario disjointness; neither ordinal alternative donors nor newly composed donors enter V7.

| State | Replaced head set | Position support |
|---|---|---|
| intact | none | none |
| new30_final | original New30 | final actual prompt token |
| single17_final | L17H27 | final actual prompt token |
| release17_final | New30 minus L17H27 | final actual prompt token |
| new30_prompt | original New30 | mapped prompt intersection |
| single17_prompt | L17H27 | mapped prompt intersection |
| release17_prompt | New30 minus L17H27 | mapped prompt intersection |

Total: 64 × 7 = **448 unique causal rows**, plus technical controls. There is one intact state, not duplicated observations for the two position supports. Natural release means L17H27 computes in the currently perturbed network at every token; it is not cached-clean rescue and is not New23. Freeze this seven-state list before acquiring outcomes. No new random mask is necessary for the within-mask position question; this study cannot estimate whether New30 is exceptional among equal-sized masks.

## Exact intervention and alignment

Use the V6 head site: each head's slice at `o_proj` input, before heads are projected and summed. Capture each original donor's intact per-token bank with its own genuine prompt/token positions and causal attention mask. Donors are not run on recipient tokens, padded to synthetic content, or modified by the intervention.

For actual unpadded lengths R (recipient) and D (donor), map recipient token ordinal p in [0,R−1] to:

`q(p) = max(-1, D - R + p)`.

For `q >= 0`, write donor head value at q to recipient head value at p. For `q = -1`, perform no write. Thus exactly `min(R,D)` prompt positions are mapped; a longer donor's early positions are unused, and a longer recipient's early prefix remains untouched. Final support is the restriction p=R−1, q=D−1. Never broadcast donor-final values across prompt positions. Map actual token ordinals, then translate to padded tensor indices separately for each row; pads are never valid sources or destinations.

This is the existing V5 label-readout/native-replay `right-aligned-intersection-keep-clean-prefix` policy, implemented in `.scratch/selective-deception/analysis/transfer_v5_v2.py:position_map` and `selective-native-replay/evaluation/native_interchange.py:make_position_map`. V6 `selective_v6.py:final_replacements` is its final-token restriction. V5's untouched early prefix uses an identical-input clean shadow. Under causal attention and this contiguous-suffix support at every selected layer, that prefix cannot depend on later interventions, so leaving it unwritten in the V6 hook runner has the same causal meaning. Verify the prefix remains equal in runtime controls; do not introduce clean clamping on other positions.

This is not V5 EVAL5 alignment: `selective-transfer-v5/evaluation/benchmark_eval.py:pack_reference/build_corrupt_stream` packs donor prompt plus native response, truncates its prefix to the recipient prompt-plus-generation horizon, and fills shortages by repeating the response (prompt fallback only when response is empty), respecting recipient left padding. V7 does not reproduce that EVAL5 packing or decode intervention. It deliberately extends V6 using the already implemented label-readout/native-replay alignment.

This is positional alignment by distance from prompt end, not semantic alignment. D/H/F/I lengths can differ, so their mapped counts and interior token correspondence differ. Persist per-case lengths, maps, unmapped count, mapped fraction, final indices and donor token hashes. Recheck V5's exact common readout-suffix guarantee where applicable; do not assume an added I variant shares every older suffix invariant. A suffix discrepancy is a reported limitation or prelaunch design decision, never an excuse for silent retokenization/rematching. No semantic segment labels are needed.

The prospective CPU inventory `.scratch/selective-deception/component-analysis-v7/alignment-inventory-001.json` shows D/H/I have equal lengths within each scenario (100–105 tokens), identical mapping support, mean coverage approximately 99.391%, and 0–3 untouched prefix tokens. F is shorter (89–91 tokens) and has 100% coverage. Thus the primary D−I contrast does not have a mapped-count mismatch in this frozen panel, but matched counts do not imply matched semantic positions. F comparisons have different absolute counts and donor correspondence; retain F as a descriptive control, report these differences, and do not normalize margin effects by token count or claim position-matched F selectivity. No extra alignment alternative or subset is added.

## Controls and runtime requirements

Keep the V6 frozen model snapshot, A40/BF16/SDPA, tokenizer, fp32 readout and pinned environment. No eager attention is needed. Use the same batch size/grouping as the saved V6 comparison anchors where feasible; any altered batching/backend must be named and checked, not concealed by tolerance-based identity claims.

1. On the actual production path, compare plain native forward, hooked empty forward, empty/all-false replacement, and cached-self replacement over final and mapped-prompt support. Require exact full-vocabulary equality within each backend for native logits and fp32 readout. Self replay must use clean recipient activations at the same recipient positions with the original donor-derived write mask; it must not realign recipient activations by donor length. Check each selected mask/support at least in the balanced smoke; retain per-batch whole-New30 self/noop proofs in main.
2. Prove correct donor rows and actual-token indexing. Unit tests cover donor shorter/equal/longer, heterogeneous batch lengths, pad exclusion, final restriction, and nontrivial donor values. Smoke must check the actual input writes against expected donor slices, with untouched head slices/pads/prefix checked at the write site. Later unselected activations can legitimately change downstream; do not incorrectly demand global equality after intervention.
3. Recompute every intact and final-support anchor in the same V7 batches as its prompt-support comparison; historical values never substitute for these contemporary baselines. Compare final-support intact/New30/release17 anchors to saved V6 follow-up results by case. Saved fp32 scalar anchors can establish reproduction; V6 does not provide historical full-vocabulary arrays or native numerical margins. Under identical execution expect exact stored anchors. Investigate any mismatch before interpreting position effects; do not silently replace historical values. Single17 validation can be newly measured without reopening selection.
4. Reconfirm recipient and original donor requested-answer capability using fresh native and fp32 argmax. Retain failures; report them and withhold capability-dependent specificity claims. Record unique donor counts separately from repeated case records.
5. Persist complete row IDs, support/mask identities, native and fp32 argmax, finite metrics, source/model/manifest hashes, exact-control flags and maximum differences. Saving native numerical margins alongside fp32 margins now is inexpensive and avoids extending V6's native-numerics omission. Maintain independent artifact audit before scientific interpretation.

Failures in identity/indexing/source integrity stop the study. No automatic retry, donor refill, or position-policy adjustment after inspecting effects.

## Prespecified endpoints

Let m(v,s,c) be fp32 requested-minus-alternative margin for variant v, scenario s, condition c. Define drop E(c)=m(intact)−m(c), positive when the requested answer weakens. D and I request the false/alternative token; H/F request truth.

Primary estimand: the New30 position increment `P_v = E(new30_prompt) - E(new30_final)`. Report the four raw P_D/P_I/P_H/P_F and the paired contrast `P_D - P_I`. Positive means broader support produces a greater requested-margin drop. A positive D−I contrast on this exposed small panel is not sufficient to call a deception-specific circuit.

Secondary fixed component estimands:

- Natural-release restoration at each support: `R_v,support = m(release17_support) - m(new30_support)`, and `R_v,prompt - R_v,final`.
- Single-head drop at each support, plus its prompt-minus-final difference; raw D/I/H/F and D−I contrasts.
- Requested and truthful probabilities, KL(intact || condition), and native/fp32 requested/truthful argmax counts. Report each first-choice transition as requested→truth, requested→other, or the applicable H/F error; list case IDs. A non-answer argmax is not automatically a coherent refusal. D truth corrections and I task failures may be the same answer switch under different instructions.

Show paired case plots and stratum summaries, then paired scenario-bootstrap 95% descriptive intervals (10,000 draws, fixed seed 1729). Resample the 16 scenario clusters with all variants/conditions together; do not treat 64 cases or technical repeats as independent observations. Preserve existing V6 analysis conventions where compatible. No significance gates, equivalence claims, mediation percentages, mask ranking, or adaptive follow-up selection.

Prompt-minus-final measures the total incremental effect of intervening at earlier aligned positions in the presence of the final write, including nonlinear interactions. It does not localize a critical earlier token, isolate information content, or equal an additive earlier-position contribution. Different variant lengths/alignment remain a limitation even with shared donors.

## Why defer generation and lexical donors

Free generation is not required to answer the position question. Generation adds donor continuation alignment/terminal-hold semantics, recipient trajectory divergence, length and coherence endpoints, and annotation. Previous SDR free-generation baselines already had poor joint headroom. Unchanged first-token choices would not establish that generation is unchanged; changed choices would not establish coherent deception suppression. Either outcome motivates a separately frozen behavioral study if warranted, without automatically reopening the failed SDR generation gate or spending the remaining envelope.

Exact lexical/counterfactual donors address content versus ordinal/task routing, a different question. Report210's ordinal assignments were heterogeneous and mostly unmatched. A lexically matched arm would require constructing and validating counterfactual prompts, their truth/request labels, donor capability and token correspondence before effects. Combining that with position expansion would confound the bridge. Preserve original donors here and record lexical mismatches descriptively. No new donor construction/search now.

## Bounded execution and budget

Suggested reservation: one 10-minute A40 smoke on a deterministic four-scenario subset (one per stratum, all variants/states), then one measured, at-most-15-minute A40 main job after technical review and a measured forecast. Total proposed charge **0.416667 reserved GPU-hours**, leaving approximately **1.566666 hours** of the supplied envelope. Smoke repeats are technical and count once through main. Historical V6 smoke was 79 seconds, the much larger pilot 301 seconds, and the full V6 tranche 602 seconds; these support a small initial reservation but do not prove V7 timing. Wider activation writes/support controls may change costs.

Use CPU dry-run exact row counts, bounded toy tests and independent code review first. Root freezes manifest/source/receipt, measures smoke load and per-case costs, then sets main walltime from that forecast plus reasonable buffer. Do not reserve all remaining time by default. If the measured forecast does not fit 15 minutes, revise the prospective reservation before main while preserving the frozen scientific design and cumulative cap. No paid APIs, optimization, FAR/WikiText add-ons, decoder experiments, or automatic successor runs are included.

Completion criterion: all 448 expected rows, all planned control proofs and source bindings, deduplicated smoke/main comparison, paired analysis and independent technical/scientific review. A null position increment or unchanged choices is a complete, useful answer to this bounded question.
