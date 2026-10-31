# SDR shared-component composition findings

2026-10-26; acquisition and audits completed 2026-10-27 UTC.

**The influence of five earlier shared heads depends on different layer 17 interfaces when the clause changes versus when the facts change.** The task instructs the model to show the damaging, relevant evidence; choosing the harmless item commits to withholding the relevant one. With facts fixed, transplanting their no-pressure states into pressured prompts changed damaging-item commitments from **0/48 to 23/48**. Restoring the recipient’s original query state reduced this to **9/48**; restoring the shared key state left **22/48**. When the facts changed within pressured prompts, the same source intervention produced **39/48** damaging commitments; query restoration left **32/48**, key restoration **15/48**, and joint restoration **3/48**. This constrains how shared components compose without requiring them to serve deception exclusively. Queries and keys determine attention weights; values supply the content those weights combine.

We tested original Llama-3.1-8B-Instruct prompts from 24 historical stories: 96 baselines and 192 directed pairs across 20 fixed interventions, totaling 3,936 completions. P means pressure; N omits the pressure clause. U5 comprises five shared heads in layers 12–14. Their donor states replace mapped original-prefix outputs; the rest of the model, including every MLP, evolves naturally. Receiver restoration inserts the recipient’s baseline state; rescue inserts the receiver state induced by U5 into a baseline recipient without U5.

The table counts **recipient damaging-item commitments out of 48 pairs**. Each row pools only the two truth variants over the same 24 stories. Reciprocal clause directions remain separate; fact-flip rows retain the recipient’s factual roles.

| Recipient ← donor | Baseline | U5 | U5 + clean Q | U5 + clean K | U5 + clean QK | U5 + clean quartet output | Induced QK alone | Induced quartet alone |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P ← N, same facts | 0 | 23 | 9 | 22 | 8 | 1 | 0 | 7 |
| N ← P, same facts | 40 | 37 | 40 | 37 | 39 | 40 | 40 | 40 |
| P ← P, fact flip | 0 | 39 | 32 | 15 | 3 | 0 | 19 | 26 |
| N ← N, fact flip | 40 | 30 | 30 | 30 | 31 | 31 | 36 | 36 |

**The downstream contribution extends beyond H24 alone.** Restoring H24’s output left 9/48 clause-change and 15/48 pressured fact-flip commitments, compared with 1/48 and 0/48 after restoring outputs H24–27 together. The quartet’s induced state alone produced 7/48 and 26/48. These are conditional dependence and sufficiency results; they do not identify a natural mediated fraction. QK rescue shifted first-token margins in the clause comparison but changed no complete-response choices there, preserving an important sufficiency limit.

The contrasts also constrain alternatives. V restoration left 23/48 and 38/48; the fixed outside-group key control left 23/48 and 39/48. H26 alone changed no choices, although it shifted margins; adding it to U5 yielded 24/48 and 41/48, below S32’s 39/48 and 48/48. Margin interactions were subadditive in both pressured strata. Negative interaction alone establishes neither competition nor redundancy. Ordinary N comparisons showed margin effects and some choice changes, supporting reuse of these interfaces.

Q24 affects one query head; K/V group 6 supplies heads 24–27, so magnitudes are not size-controlled semantic comparisons. H25/H27 are outside S32. No attention allocation or semantic representation was measured. Pressured fact-flip donors always emit the recipient’s damaging identity, leaving literal copying aliased with that role. These historically selected, supplied-stem disclosure commitments establish neither false factual assertions nor strategic intent, prevalence, or generalization. Both blinded raters agreed on every one of 32 unique views; all completions were EOS commitments, and every clean-only control matched baseline.

[Technical analysis and complete directional tables](../../.scratch/sdr-shared-composition/analysis.md) · [Standalone figure](../../.scratch/sdr-shared-composition/figures/commitment-counts.svg)
