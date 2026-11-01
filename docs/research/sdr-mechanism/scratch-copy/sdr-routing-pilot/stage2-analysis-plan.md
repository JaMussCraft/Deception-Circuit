# Stage 2 interpretation rubric — written before results

2026-10-21 UTC. This records interpretations of the approved fixed39-cell path grid and family interactions, without new experiments, changes to splits, or additional outcome selection. Stage2results were not inspected. Authority: [pilot spec](spec.md), [path seam](stage2-path-seam.md), and [Stage1 independent analysis](stage1-analysis.md). Scope remains **answer/content diagnostic**; pure pressure mediation is unidentified.

## Comparisons to retain

Report recipient-truth-minus-other margin change, full-vocabulary outcomes, row/story counts, and95%story-bootstrap intervals. Keep P←H, H←P, P←N and N←P separate; then separate unchanged versus changed designation/truth/content, both recipient truths, and donor actual emitted answer relative to recipient truth and baseline emission. P0↔P1 is a separate same-pressure, changed-content diagnostic. Cross-story N donors remain content-confounded controls. Never pool reciprocal signed changes into a claim of weak effects.

Explicit Stage1-motivated stratum: **changed-truth H/N→P where the donor emits the recipient's same false item**. Report H and N separately where support permits, followed by a clearly labeled combined summary, maintaining recipient-story averaging. Candidate6 improved recipient truth in this stratum despite the unchanged false donor emission. Ask whether that effect reaches the tested receivers, rather than relabeling it donor-answer copying. Conversely preserve changed-truth P→H/N, where pressure donors emit the recipient's truthful item: candidate effects need not follow that emitted answer.

Use the frozen discovery/confirmation split. Report every fixed-grid confirmation cell, including nulls, reversals and incomplete cells. At most3position followups may use the already authorized ranking by absolute discovery raw effect; label them exploratory, report all their confirmation outcomes, and do not introduce a second selection rule. No confirmation-based filtering, new family, donor replacement, or pressure search.

## How to read path patterns

| Observed pattern | Supported interpretation | Limit |
|---|---|---|
| Candidate→selector Q/K effects have consistent direction within the specified donor stratum and recur on confirmation; V/direct-readout effects are smaller under matched scope | Evidence that the tested candidate perturbation influences answer processing through the selector's query/key input; compatible with an attention-selection contribution | Q/K effects do not establish an abstract selection role, pressure representation, or pressure-specific computation. Magnitude rankings alone are insufficient. |
| Candidate→selector V effects recur and track donor/recipient answer-content changes more than Q/K under matched scope | Evidence that a value-input route carries the tested answer/content-dependent perturbation; compatible with content transport | A V patch can change subsequent computation rather than copy an emitted token; grouped V affects all query heads in that KV group. |
| Candidate→READOUT effects recur, with little effect through tested selector inputs | Evidence for a direct contribution from that candidate output to the tested readout under the freeze | Does not show that direct writing dominates ordinary total effects or that selector/MLP routes are absent. |
| Q/K, V and direct-readout routes all contribute, or differ by direction/content stratum | Mixed/context-dependent routing through measured interfaces | Do not force one semantic role per head or infer a single circuit-wide mechanism. |
| Paths are small/uncertain despite Stage1 family effects | No large effect identified along these specific direct edges, positions, mappings and donors | Does not rule out multi-hop routes, omitted heads/MLPs, family synergy, distributed effects, or effects outside the semantic maps. |

Compare route magnitudes only within matching recipient/donor/scoring/scope definitions. Q is one query head; K/V are layer-specific KV groups affecting heads24–27, including nonselectors. They are not equally sized interventions. Same-layer L17H26→L17selector Q/K/V cells are absent by design, not measured nulls. Q/K are before RoPE; these tests recompute recipient-position projections and do not transplant donor attention patterns.

Preserve the existing two-pass formalism: pass1 injects only the mapped sender with recipient-baseline fill elsewhere and freezes **every other component output** at its recipient capture; pass2 replaces only the selected receiver input and lets downstream components evolve. Ordinary total family effects and these direct-edge effects are different estimands. Direct-path patching does not by itself establish natural mechanism mediation or intent. No-sender/self controls and same-provenance baseline equality must pass before interpreting any path.

## Interactions without redundancy stories

For candidate C and selector S, retain baseline and singles alongside joint CS and compute the authorized raw-margin interaction:

`I_CS = (m_CS − m_C) − (m_S − m_0)`

Use the identical contrast for candidate/outsider. Pair rows and resample story groups; preserve donor direction and truth/content strata. Report signs alongside singles: a negative interaction is not inherently suppression or antagonism because the single effects can be negative too.

A joint perturbation adding little beyond the stronger single, together with a compatible direct candidate→selector route, is **consistent with** serial dependence/occlusion. It is not proof: saturation, nonlinear combination and shared downstream bottlenecks produce similar outcomes. A joint effect larger than singles can support conditional dependence or compensatory contributions; it does not establish redundant mechanisms. Approximately additive margins support separability only under the tested intervention and precision.

The fixed .5shared32 dose helps show whether whole-family effects are compressed near an outcome floor/ceiling. It is not a full dose-response curve and does not alone establish linearity or redundancy. Interactions use the ordinary freely evolving background and masked replacements; **do not apply the direct-path freeze or baseline-clamp unmapped positions** to those cells.

Conclusions must remain about these donor-conditioned attention/readout interventions. MLPs remain active and are outside the modeled path graph; null attention paths cannot exclude their mediation. No completeness, external suppression, semantic-role certainty, strategic intent, or pure pressure-routing claim follows from this stage.
