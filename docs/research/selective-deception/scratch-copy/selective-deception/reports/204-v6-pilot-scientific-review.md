# 204 — V6 pilot scientific review and bounded follow-ups

**Proceed with three bounded follow-ups.** The pilot identifies a concrete readout-routing lead, especially L17H27, while showing substantial shared effects on deceptive instructions and capable benign inversion. It does not establish a deception-specific head. This is sufficient reason to investigate the mechanism now; a positive global selectivity result is not an advance requirement.

Evidence is report202 and its prepared `component-analysis-v6/analysis-001/pilot-summary.json`, independently checked against raw artifacts by203. I read the prepared aggregate, all30 single-head means, seven release effects and attention/provenance summaries without rerunning the full analysis. Audit203 passes2688development causal rows,560aggregate-validation rows and720attention rows. All causal phases use A40/BF16/SDPA with exact same-backend clean/no-op/self controls. The frozen panel and source identities remain those recorded in203. No GPU/API/source/label changes were made by this review; only this report is owned here.

## What the pilot establishes

Positive drops below mean reduced requested-target margin. D requests the instructed false answer; I requests the transparent benign inversion; H/F request truth. F is the frozen no-pressure form.

| SDR New30 | ΔD | ΔI | ΔH | ΔF | Paired ΔD−ΔI, exploratory95% interval |
|---|---:|---:|---:|---:|---:|
| Development16 |1.245|1.352|.274|.328|−.107 [−.316,.093]|
| Internal validation16 |1.709|1.254|.301|.265|+.455 [.079,.856]|

The primary D−I contrast is near zero on development, positive on validation. The latter supports a local differential on that panel; it does not erase the substantial I effect, establish stable specificity across panels, or prove the panels differ statistically. These are exposed mechanism partitions and exploratory scenario-bootstrap intervals, not pristine confirmation or multiplicity-corrected head discoveries. Preserve all raw effects and strata rather than highlighting the favorable interval alone.

New30 leaves **16/16 requested full-vocabulary argmax answers unchanged in every SDR D/H/F/I panel**, despite margin reductions. Thus this pilot shows weakened answer preference, not an observed SDR answer correction/refusal rate. All176intact causal rows are requested-correct under the recorded fp32 final readout; the saved native full-panel argmax vectors are not available for independent reconstruction. Native/fp32 agreement and correctness are directly verified for the24attention cases. Do not silently promote this to a saved-native176case guarantee.

FAR provides a useful family contrast: New30 reduces D requested argmax16→6/16, while H/F remain16/16. This is consistent with the previous stronger FAR transfer, but FAR has no matched capable-I panel here, so it cannot establish superior D-vs-benign-inversion specificity. The study remains readout-only replacement of each recipient's last actual prompt position by its donor's own last position, not all-position V5 or free generation.

OldD69 has substantially larger D and I drops, together with larger H/F losses. The fixed random30 has almost no mean D suppression on these panels. This supports nontrivial frozen-mask structure at this readout, while neither one random mask nor the69-versus30 comparison is a matched population null or proof of unique necessity. H/F accuracy preservation is real on this small panel, but positive margin losses and changed distributions preclude claiming cost-free or general capability preservation.

## Head lead and attention limits

The predeclared development-only release rule nominates **L17H27**: conditional D restoration+.8236 [ .5109,1.2093 ]. Its I restoration is+.8649, with H+.304 and F+.403. Single-head replacement in the intact context likewise drops D1.0155 and I1.0991, H.305/F.382. This is a strong shared answer/instruction-routing candidate, not preferential D removal. It is also the sole added head overlapping the historical D support; membership is provenance, not functional proof.

L13H23 is the next clear added-head lead: single D drop.1779/I.2392 and conditional D/I restoration.132/.128. Most other single readout replacements are small here. That is a statement about this donor/position/context; it does not show the other heads are globally irrelevant. Conditional releases are not cached-clean rescues, additive fractions of the joint effect, or seven isolated causal contributions. Do not report L17H27 as “responsible for” a percentage of the mask effect by dividing these numbers.

Attention has exact raw token indices/weights for all30 heads over the fixed eight development scenarios, but **no verified semantic segment mapping**. No instruction/clause/fact alignment or “deception attention” claim follows. Eager and SDPA independently pass their controls but are numerically different: max absolute drift.4375 native/.4631 fp32, requested-margin drift up to.25/.2364, with0/24argmax changes. Small SDPA head effects must not be explained quantitatively using eager-logit differences. The follow-up causal path should remain on SDPA; attention is descriptive context only.

## Freeze these three follow-ups before any new head-validation outcome

1. **Cached-clean L17H27 rescue on the16 SDR validation scenarios, D/I/H/F.** Keep New30 as the recipient intervention and insert that recipient/variant's cached intact L17H27 output at its own final position. Report margin(rescue)−margin(New30), with actual contemporaneous intact/New30 anchors, New30 cached-self reinsertion and the L17H27 contextual release comparator. This tests whether restoring the intact contribution reverses the joint perturbation, versus merely allowing the head to recompute in the perturbed context. Similar D/I rescue supports shared routing; failed rescue despite successful contextual release is informative about upstream/context interactions. Either result is useful. Partial rescue is not whole-circuit sufficiency or unique necessity.

2. **New30 donor-label/content contrast on the same16validation scenarios.** Freeze two scenario-disjoint independent honest-donor assignments with construction truth labels agreeing/disagreeing with recipient truth; no donor may be chosen from intervention performance. Keep each assignment fixed across D/I/H/F. Report truth-oriented margin(agree)−margin(disagree), plus all requested-target margins/accuracies and per-scenario results. Consistent attraction toward donor labels supports content/label routing as a contributor. It does not isolate label from every other donor difference, prove copying of factual details, or justify replacing the original V5 donor policy. Record unavoidable donor length/content differences and retain all cases.

3. **One development-nominated direct sender→receiver-Q path, with one same-layer comparator.** Fix sender **L13H23** and receiver **Q(L17H27)**: the receiver comes from the original development-only release rule; the sender is the largest positive development single-D-effect head among frozen heads in strictly earlier layers, with numeric(layer,head) tie-break. This nomination uses no validation head/path effects. Fix comparator **Q(L17H26)** now by numerical adjacency in the same layer/shared KV group; do not search for a weak receiver. H26 is a matched comparator, **not a guaranteed null**.

For the path, construct the recipient-shaped clean component bank and change only senderL13H23's recipient-final output slice to its independent honest donor's own final value. Freeze embedding/every other head/every MLP output at their recipient-clean values while capturing the receiver Q response, then write only the captured receiver's final Q into a clean recipient run and allow downstream propagation. This tests the isolated direct residual→normalization→Q route under those clamps, not every mediated path from the sender. It needs no cross-prompt all-token alignment and implies no semantic clause route.

Primary path readouts are intact-minus-Q-write requested margin for D/I/H/F, and the paired target-Q minus comparator-Q effect. A nonzero target path under exact no-ops supports sensitivity of that route; a similar comparator effect suggests less localized Q mediation. A null cannot rule out K/V, MLP or other mediated routes. Do not select another sender/receiver after seeing this result or turn it into a grid.

Technical prerequisites for this third contrast: clean bank contains exactly the hook component keys, excluding READOUT_KEY; own-final indices are correct; total sender replacement reproduces the independently computed donor sender intervention; empty-sender, self-sender, clean-Q/self-Q and false-position-mask controls give exact same-backend identities; intended Q-slice isolation is checked. Actual self/empty/false-mask operations are the negative controls, distinct from H26. If these conditions fail, repair or defer the path rather than claiming it was tested. Root/explorer should verify primitive semantics before implementation approval.

## Exact follow-up state and donor freeze

Use all **16 SDR validation scenarios × D/H/F/I =64case variants**. Preserve the original scenario/variant order and original independent-H donor baseline. Freeze these ten reported conditions before implementation/GPU:

| State | Recipient computation / replacement |
|---|---|
| intact | Clean recipient, no intervention |
| original_New30 | All30 final-head slices from the original frozen donor |
| release_17 | original_New30 except L17H27 computes normally |
| clean_rescue_17 | original_New30 except L17H27 receives that recipient/variant's cached intact final slice |
| self_rescue_17 | original_New30 with its own cached perturbed L17H27 slice reinserted; equals original_New30 |
| agree_New30 | All30 final-head slices from the new truth-agreeing H donor |
| disagree_New30 | All30 final-head slices from the new truth-disagreeing H donor |
| total_sender_13 | Otherwise intact recipient with only L13H23 final slice from the original donor |
| path_Q27 | Only final Q(L17H27) receives the isolated donor-sender-induced Q value |
| path_Q26 | Identical construction, only final Q(L17H26) receives its induced value |

The clean/rescue, donor-pair and path/comparator pairs are the three scientific contrasts. The other states are anchors, contextual comparisons and actual shams; they do not authorize a broader search. Recompute anchors in the same follow-up job rather than treating old saved scalar metrics as fresh identity checks.

**Donor packaging rule:** source candidates only from the existing frozen V5 SDR neutral-H validation donor pool referenced by `transfer-v5/v2-prepared-frozen.json` / its bound source manifest. Reapply the existing entity+unordered-item scenario exclusion, and exclude every V6 recipient scenario (across both SDR partitions and the FAR supplement). Do not use the six-coarse-circuit study's masks, intervention rankings or newly generated pool. Derive donor and recipient truth labels from construction metadata, never model effects.

Process validation recipients in lexicographic stable recipient-ID order, and arms in fixed agree→disagree order. Within the required construction-label bin, rank eligible donors lexicographically by SHA256 of UTF-8 `v6-followup-donor|20261026|ARM|RECIPIENT_ID|DONOR_ID`, tie-break donor ID. Select the first remaining donor; exclude that recipient's original donor and forbid donor-ID or donor-scenario reuse across all32 new assignments. Use the resulting pair unchanged for all four variants. Serialize exact candidate source hashes, recipient/donor IDs, scenario keys, labels, prompts/token IDs, ordering and assignments in a new frozen receipt before model execution. If32 unique scenario-disjoint candidates cannot satisfy the bins, stop packaging and resolve that feasibility constraint explicitly; do not silently refill, shrink the panel or change the matching rule after outcomes. Record fresh intact donor capability but never swap a selected donor based on its intervention result.

**Minimum actual model proofs:** on every included case and both receivers, demonstrate clean-bank replay/no-op, empty-sender capture/write, recipient-self sender capture/write, clean-Q/self-Q write and false-position-mask identity against the same SDPA clean readout; verify only the intended final Q slice is written. For clean rescue, cached New30 self reinsertion must reproduce New30. The synthetic sender tensor must equal clean everywhere except the declared final slice; verify every clean-bank key and tensor shape and reproduce total_sender_13 independently. Prefix padding indices must be masked out. Save native same-backend identity evidence and the fp32 metric convention separately. These technical controls may share captures but cannot be replaced by assumptions or the eager attention pass.

## Bounds and claims

The follow-ups are three hypothesis contrasts, not three broad sweeps; anchors and technical controls are necessary parts of those contrasts. Reuse A40, the frozen16validation scenarios and recorded fp32 metric convention. Target one15minute technical smoke followed by one measured15minute acquisition tranche; root may revise the latter bound from measured technical throughput, retaining the2.4reserved GPU-hours ceiling and no automatic retries. No API, new mask training/reselection, free-generation judge campaign, or duplicate six-coarse-V2 study is required.

Suggested high-level update: “The pilot localizes much of the readout effect to L17H27, but that head affects benign inversion almost as much as deceptive instructions. The30-head intervention weakens SDR answer margins without changing its answers on this panel; FAR answers change more strongly. We can now test a clean L17H27 rescue, donor-content dependence and one narrowly isolated upstream-to-query path, without claiming a deception-specific circuit.”
