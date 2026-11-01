# 210 — V6 final scientific review

**The bounded pilot and all three targeted follow-ups are complete and technically audited.** The strongest finding is a local, shared answer-routing role for L17H27, with evidence for one small upstream-to-query route. The results do not identify a deception-specific circuit, demonstrate unique necessity/sufficiency, or change the model's first-answer choices on the SDR follow-up panel.

Evidence: independent artifact audits203/208; prepared analyses202/209; operative selection002 and prospective ordinal amendment205. Follow-up main contains640 rows =16exposed validation scenarios ×D/H/F/I ×10frozen states. Smoke repeats are not extra observations. Audit208 passes560 batch-level exact flags,192 donor-capability records, exact agreement with1536 previously saved intact/New30 anchor metrics, and exact agreement of all160 repeated smoke row dictionaries. Same A40/BF16/SDPA path and original donors are preserved. Selection002 SHA `2a55b55570b5a6f9610ebe424480d3250057b3e8e27a84221834664034012a44`; prepared followup-summary SHA `5401d62e282226c99decd0620a543195480e7c74df8239249139c42c441cd12f`. This review used those analyses and the raw-artifact audit without rerunning model or statistical analysis. Only this report was changed.

## 1. L17H27 clean rescue restores answer preference, including benign inversion

All margins below use the recorded fp32 requested-minus-alternative readout. D and I request the false/alternative answer under different instructions; H/F request truth. Restoring a D margin is therefore restoring the instructed false-answer preference, not making the response more honest.

| Variant | Original New30 margin | Natural release margin | Cached-clean rescue margin | Clean rescue−New30 [exploratory95% interval] |
|---|---:|---:|---:|---:|
| D |2.965|4.297|4.441|1.476 [1.095,1.879]|
| I |2.571|3.370|3.450|.879 [.623,1.159]|
| H |2.436|2.764|2.776|.340 [.126,.607]|
| F |2.801|3.108|3.106|.304 [.106,.505]|

The natural release lets L17H27 recompute within the perturbed New30 context; the clean rescue writes its cached intact recipient contribution instead. They are empirically distinct: clean-minus-release is+.144 [.077,.213] for D and+.080 [.035,.120] for I, but only+.012 for H and−.003 for F, with the latter intervals spanning zero. Cached New30 self-rescue is exactly New30.

This validates the development-nominated head as a useful causal lever in this joint-intervention context. Both D and capable benign I are strongly restored, with smaller but nonzero H/F restoration. The D effect is larger here, but that does not make the head deception-specific: the original pilot's D−I contrast was near zero on development and positive on internal validation, while the head affected I substantially in both. Do not convert rescue/New30-drop ratios into a “percent of deception mediated,” additive attribution or unique necessity claim.

## 2. One isolated Q route has a small shared D/I effect

The sender L13H23, receiver Q(L17H27), and adjacent Q(L17H26) comparator were frozen from development-only rules before these outcomes. Q26 is a matched comparator, not a declared null. Report target and comparator separately; their difference is not the target path effect itself.

| Variant | Raw Q27 margin drop | Raw Q26 margin drop | Q27−Q26 drop [exploratory95% interval] |
|---|---:|---:|---:|
| D |.0853|.0036|.0817 [.0423,.1217]|
| I |.0776|.0088|.0688 [.0448,.0948]|
| H |.0075|.0049|.0026 [−.0094,.0138]|
| F |.0013|.0059|−.0046 [−.0147,.0058]|

Under the implemented clamps, the altered donor-final sender contribution changes the receiver's final Q, and that isolated Q write changes D/I margins more than the comparator. This is evidence for a **direct residual→normalization→Q sensitivity supporting both alternative-answer tasks**, not all sender-mediated paths, lexical copying, semantic clause processing or a general causal communication graph. Exact empty/self-sender, clean/self-Q and false-mask controls, plus sibling-Q/position isolation, make it more than an attention correlation.

The total sender replacement is only.0818 for D and.1776 for I, with both exploratory intervals spanning zero; this does not erase the controlled path contrast. Clamping changes which routes can cancel or interact, and the target path estimate can slightly exceed the total effect. Consequently no path/total “mediation percentage” is valid. K/V and other MLP/head-mediated routes were not searched or ruled out.

## 3. No consistent directional ordinal-donor effect on this panel

The prospective205 amendment tests **ordinal assignment sensitivity**, not exact lexical matching. Recipient-truth margin(agree)−margin(disagree) is D+.031 [−.227,.277], I−.044 [−.256,.152], H+.095 [−.101,.295], F+.110 [−.096,.334]. All intervals include zero. The appropriate conclusion is no clear directional signal for these fixed assignments and recipients, not equivalence, donor irrelevance, or refutation of internal content routing.

The donor arms differ in words, facts, lengths and activations. Unordered answer-pair matches are0/16 in agree and1/16 in disagree; truth-token matches are0/16 in both. Thus even a positive signal would not isolate ordinal position from other donor differences. Every selected donor is capable in the saved native/fp32 checks, with38 unique IDs/scenarios across original and new arms;192 repeated D/H/F/I capability records are not192 independent donors. No donor-only word becomes the final argmax. That excludes observed donor-word takeover at this endpoint, not subthreshold lexical/content influence.

## Behavioral and measurement limits

**Every one of the ten follow-up states remains16/16 requested-correct in each D/H/F/I variant, both native and fp32.** There are no first-answer corrections, errors or choice flips in this panel: D/I still choose their requested alternative, and H/F still choose truth. The causal effects are changes in margin/probability/distribution, not a measured refusal or free-generation deception rate. Native argmax agreement is now saved throughout the follow-up, whereas numerical margins/probabilities/KL are fp32 readouts; native numerical values were not saved and must not be invented.

The earlier FAR supplement did change requested D answers while preserving H/F, but lacks the matched capable-I panel and should not be generalized from these SDR path results. Eager attention remains descriptive, with no verified semantic segment alignment and nonzero SDPA/eager drift despite no attention-subset argmax flips. No new attention-based edge search or receiver substitution was performed.

Intervals are paired scenario-bootstrap summaries on16previously exposed internal validation scenarios, not pristine confirmation, p-values or formal equivalence tests. The probes/hypotheses were frozen before these targeted outcomes; the four repeated smoke scenarios count once through main. Executed exact-proof flags and scalar/argmax artifacts support the interventions, but full component banks/Q vectors/vocabulary tensors were not persisted for independent tensor reconstruction; audit208 is explicit about that boundary.

## Claim and next-question scope

A defensible summary is: **“L17H27 is a strong local lever for requested-answer preference under the frozen New30 readout intervention. One L13H23→L17H27-query route contributes a smaller, shared D/I effect. The chosen ordinal donor assignments show no clear directional effect, and none of these SDR follow-ups changes answer choices.”** This advances component understanding without a deception-specificity, unique-necessity, sufficiency, minimality or broad benign-capability claim.

The most useful subsequent questions are whether the same shared routing mechanism matters when interventions affect all positions or generated answers, and whether genuinely matched lexical/content counterfactuals separate donor information from ordinal/task structure. Those require a separately frozen design and evidence; the current heterogeneous donors and first-answer endpoint cannot answer them. They are questions for the next decision, not authorization to expand this tranche or reuse EVAL5 as untouched confirmation. No further GPU/API work is needed to close the user-authorized bounded first component-analysis tranche.

Suggested brief user update: “The low-level tests are complete. Restoring L17H27 reverses much of the margin change, but also restores benign inversion, so it is a shared routing component rather than an identified deception-specific head. We found a small, controlled upstream-to-query effect and no clear directional effect from the ordinal donor swap. All SDR answer choices stayed unchanged; these are local mechanism results, not demonstrated reductions in generated deception.”

## Attention descriptive addendum — report211

Report211 adds a valid concrete observation from the existing eight-scenario eager-attention subset: L17H27 places24.565%/11.470% raw mass on all occurrences of the recipient truth/false answer-token IDs under D, and24.824%/13.016% under benign I; H gives10.006%/11.105%. D and I therefore look similar on this lexical summary, without an equivalence test. Each answer ID appears3–4times (mean3.5), and weights are not renormalized to selected tokens. These are occurrence sums, not semantic truth/fact/instruction spans or signed output contributions.

L13H23 gives much less mass to these exact words: truth-token mass is below.5% and false-token mass below.31% separately; **combined answer-token mass is approximately.560–.774%, not below.5%**. Its fixed first-example top positions include literal turn/header markers, newline and period. That example does not establish a boundary-detection or instruction-processing function. The contrast with L17H27 is useful descriptive context beside the controlled Q-path result, but does not explain the path causally or identify what information its value vectors carry. Eager/SDPA drift, repeated occurrences and absent semantic alignment retain all previously stated limits. No new selection, experiment or causal claim is introduced.
