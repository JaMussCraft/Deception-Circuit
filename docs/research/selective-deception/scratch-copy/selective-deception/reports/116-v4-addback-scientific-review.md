# Scientific review of the fixed allW28 addback panel

October21,2026. **PASS for the descriptive results and limits in report114.** The panel establishes stronger suppression of this validation surrogate than three specified matched random interventions, and small single-head effects conditional on the other27removed heads. It does not establish a minimal deception circuit, identified redundant pathways, strategic-deception specificity or generalization.

Reviewed report114's table/limits, `fixed-allW28-analysis/summary.json`, and the33raw condition metrics. The analysis records exact reproduction of oldv3 full28 suppression/WT scalars and discrete readouts. Performed only read-only CPU arithmetic on saved probabilities/logits; no new model execution, mask selection or artifact mutation.

## What the comparison establishes

Full28 reduces D surrogate65.27%, versus24.68%,35.09%,41.54% for the three size/layer-matched masks. Thus optimization located a support with a substantially stronger measured effect than these three particular controls. This is exploratory reused validation and three controls are insufficient to characterize a random-mask distribution or support a general significance claim.

Full28 WT PPL rises5.56%, below each random control's6.82%/9.19%/5.77%. H loss counts are5 versus8/9/5, with different affected examples. There is no uniform collateral dominance: full28 KL.06963 exceeds seed0's.06588 and seed2's.06211. Full28 itself fails the5%PPL/.05KL preservation limits and loses5baseline-correct H examples. Similar net H correctness can conceal these losses and offsetting gains.

All28single-head restorations retain at least63.44% surrogate reduction;15retain at least65%. The largest restored-surrogate increments are L12H22:.03305 and L5H19:.02518, approximately2.79% and2.13% of the full intact-to-full28 surrogate effect. Seven restorations decrease the aggregate surrogate rather than recovering it. Thus no one head is individually indispensable for retaining60% suppression under this particular intervention context. This does not imply all heads can be restored simultaneously without losing the effect, nor identify a smaller jointly-preserving circuit. Every addback still fails the WT KL threshold; the best KL is.05645.

## Nonlinear readouts materially change the apparent interaction gap

For each validation pair i and readout f, define the whole effect as f(intact_i)-f(full28_i), and the sum of conditional marginals as the sum over28heads of f(addback_h,i)-f(full28_i). Average these paired quantities over119examples. The following are descriptive arithmetic, not independently estimated causal decompositions:

| Readout | Whole mean effect | Sum of mean conditional marginals | Sum / whole |
|---|---:|---:|---:|
| Recorded suppression surrogate |1.182866|.165231|13.97%|
| D-label probability |.424923|.107266|25.24%|
| Per-pair log[p(D)/(1-p(D))] |2.242026|.691056|30.82%|
| Raw D-label minus H-label logit |2.239496|.674370|30.11%|

Probability-to-surrogate curvature therefore explains part of the especially small surrogate ratio. The gap persists on logodds and on the direct two-label logit margin, so it cannot be attributed solely to the final scalar loss transform. For logodds, whole-minus-summed residual averages1.550971, has median1.527651 and is positive on90/119pairs; absolute residual averages2.130683. It is heterogeneous, not an identical deficit on every example.

Logodds were computed separately per pair from saved `d_label_mass_per_pair`, then averaged; this is not logodds of the mean probability. Across all33conditions probabilities range.01097157–.99638319. An epsilon1e-12 guard was specified but clipped **zero** values. Stored FP32 loss scalars were used for the surrogate row: recomputing -log(1-p) from saved probabilities differs by roughly1e-5–3e-5 from the original logsumexp computation, which does not change the conclusion. D-versus-rest logodds still contains a logsumexp over competing tokens; the direct D-minus-H margin is included to avoid treating that transformed quantity as a unique underlying mechanism coordinate.

The defensible conclusion is **non-additivity of these conditional intervention responses**, including on a direct output margin. Many explanations remain compatible: distributed recovery, thresholds, interactions within model computation, changes in the donor-replaced representations, and mixtures of effects across examples. The28marginals all sit at the same heavily intervened endpoint; they are not a telescoping restoration path or Shapley contributions. Small marginals alone do not distinguish redundancy from complementarity, establish a specific higher-order interaction, or certify global minimality.

One untested hypothesis is that hard stochastic-mask training with rho0 produces an overcomplete deterministic intervention because the objective does not penalize extra removed heads. Serial cuts, compensation and nonlinear responses remain alternative explanations. If a later question specifically concerns removable excess support, a bounded jointly-restored validation contrast would test it more directly than immediately changing rho to.001, which also changes the optimization objective. Neither is a reason to alter the current fixed3072-update comparison or launch a new grid now.

## The L4H5 observation is metric-specific

Restoring L4H5 increases reported surrogate reduction65.27%→65.35%, reduces WT PPL rise5.56%→4.67%, and changes H losses/gains5/4→4/3. Yet KL remains.06326, above.05. More importantly, mean D-label probability rises.373997→.381338; D probability increases on75/119pairs and decreases on44. Mean D logodds rises.06227. Consequently this is not an across-readout improvement in suppression: a redistribution of example probabilities can lower the nonlinear surrogate while raising mean D probability. It is a useful warning against naming a head harmful or pruning it from one aggregate number. No new mask is selected here.

## Highest-value next contrast after the two3072fits

First complete and analyze the already-fixed optimization contrast. Then prioritize **one independently valid donor-reassignment contrast on the frozen oldallW28 mask**, with intact/full28 under original versus one preregistered alternate SDR donor mapping. Keep recipients, prompts, head mask and WT evaluation fixed; establish donor validity/alignment and all-open identity under a separately reviewed diagnostic identity before execution. Report paired D probability, surrogate and logit-margin effects plus H loss identities, without ranking or updating masks.

This directly tests an unresolved mechanism ambiguity: whether the observed effect survives changing which honest activations replace the removed components, or depends strongly on the particular donor content. A positive result would support robustness of this interchange effect, not strategic-deception specificity; a negative result would narrow what the circuit claim means. It offers more immediate interpretive value than a new optimizer grid or interpreting the present addback sum as a mechanism proof. The earlier donor-policy deferral remains in force until that narrow design is technically reviewed. No further GPU run is authorized or launched by this report.
