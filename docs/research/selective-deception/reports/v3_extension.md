# Stronger sparse necessity search and matched sufficient-circuit comparison

Status: V3 completed October 20; V4 training, donor diagnostic and fresh native comparison completed October 21, 2026. The design below was recorded prospectively; completed findings follow. Authoritative execution state is in `.scratch/selective-deception/compute-ledger.json` and `sparse-extension-v3/`.

## Questions

1. Can longer optimization or expanding the candidate set from the 103-head D/H/F union to all 1,024 heads produce stronger SDR suppression while preserving generic language modeling and, separately, matched honest responses?
2. Does stronger SDR suppression transfer to coherent suppression of instructed lying on fresh native prompts?
3. Under identical knockout and evaluation conditions, do the new necessary masks suppress lying as effectively as the original 69-head sufficient D circuit, with fewer removed heads or less collateral damage?

The prior nine-head WikiText-only necessary mask achieved roughly 55% reduction in the nonlinear SDR suppression surrogate, but corrected only two of fourteen baseline false native outputs. It retained all sixteen native honest responses in that small slice, while losing fourteen and gaining seven honest SDR label predictions. These are different outcomes and must remain separate.

## Fixed design

Four fresh fits cross union/all-head search with WikiText-only (W) and matched-H plus WikiText (HW) preservation. Each uses seed 0, 1,536 updates, validation every 64 updates, otherwise the previous optimizer and objectives. Rho is zero: sparsity comes from initialization and selection of compact binary checkpoints, not an explicit nonzero L0 penalty. No inference about optimal hyperparameters or seed robustness follows from this four-run contrast.

Validation selection first seeks the smallest mask meeting 95% reduction, then 90%; if neither target is reached, it selects the strongest constrained reduction. Joint H/WT and WT-only preservation tiers remain separate. Head sets are deduplicated; a strongest unconstrained frontier can fill an otherwise empty comparison slot, clearly marked as failing preservation. The exact ordering and eligibility rules were frozen before outcomes in `sparse-extension-v3/protocol.json`. All four equal-horizon fits must finish before final selection.

The target quantity is `mean[-log(1-p_D)]`; its percentage reduction is neither percentage-point reduction in deceptive-label probability nor reduction in generated deception. Near-zero surrogate values can be numerically delicate. Final SDR results also retain deceptive, truthful and other-token probability mass.

The fresh evaluation compares intact, old sufficient D69, old necessary W9, and at most two new masks. All conditions use the same donor mapping and intervention protocol. Only D69's active attention heads are removed; incidental expanded MLP entries are excluded. Native evaluation contains 32 paired instructed-lying/honesty prompts, balanced over four domains and true/false source statements, plus 32 independent honest donors. SDR uses 64 fresh test pairs; WikiText uses 16 new article windows. Test selection uses structural metadata, never model outcomes. Freshness is relative to persisted prior exposures; rejected candidates not saved historically cannot be excluded.

## Interpretation commitments

Coherent refusal under a deception instruction counts as desired suppression and is reported separately from truthful correction. Refusal under an honest instruction is a utility loss. Reduced false-output rates accompanied by ambiguity or incoherence cannot be credited as clear suppression. Paired losses and gains must accompany net accuracy changes.

This is a comparison of intervention behavior for particular discovered masks. A favorable result does not establish that necessity-based discovery generally dominates sufficiency-based discovery: the methods, circuit sizes and optimization histories differ. Nor does instructed-lying transfer alone establish a mechanism of autonomous strategic deception. Components may mediate answer selection, instruction handling or donor-content substitution. Mechanistic claims require subsequent controlled interventions.

The 32 native pairs are an exploratory transfer sample, not a high-powered benchmark. Report counts, domain/truth strata, baseline-capable denominators, and uncertainty without searching test outcomes for a better mask. Reused development validation and one seed limit generalization claims.

## Completed validation search (October20)

All four fits completed 1,536 updates and 24 validation checkpoints. The audit checked runtime source, immutable run identities, checkpoint exports, receipts and complete coverage. Independent Astra review 100 recomputed the prospective selection over all 96 checkpoints: 48 satisfy the WT tier, none satisfy the joint H/WT tier. Root froze the two masks below before any heldout evaluation.

| Selected mask | Heads | D surrogate reduction | H previously correct lost / previously incorrect gained | WT validation PPL rise | WT KL |
|---|---:|---:|---:|---:|---:|
| union-W at update 1344 |13|58.99%|11 /5|0.843%|0.02103|
| all-W at update 1536, unconstrained comparison |28|65.27%|5 /4|5.556%|0.06963|

Baseline H correctness is 86/119; these masks yield 80/119 and 85/119 respectively. The all-head mask fails both frozen WT limits (PPL rise≤5%, KL≤0.05), but the magnitude should be reported rather than described as catastrophic damage. The13-head mask preserves generic LM behavior under the validation criterion while still losing honest SDR cases. Neither approaches the 90% or 95% suppression-loss target. This is evidence about these four configurations, not an impossibility result.

Longer restricted training improves the previous 55% result only modestly; the all-head runs spend more updates before producing nonempty binary masks and then reach stronger suppression with increased WT damage. Candidate-set size changes the per-gate initialization under the fixed expected-removal count, so equal optimizer updates do not imply equal progress through the binary-threshold transition. Reused validation and a single seed remain limitations.

The selected comparison is intact, original sufficient D69, original necessary W9, new W13, and new all-W28. Native deception effects remain unmeasured at this checkpoint. Frozen selection receipt: `.scratch/selective-deception/sparse-extension-v3/comparison/selection-receipt.json`; complete figure: `sparse-extension-v3/figures/extension-frontier.png`.

The union-W run exactly reproduces the original W9 head set at update 512. Of the selected all-head mask's 28 heads, 24 are outside the original 103-head union. This identifies new candidate components for follow-up; it does not establish that they are deception-specific.


## Completed heldout comparison (October 20)

All four fits, heldout evaluation, blind annotation, and independent scientific review are complete. No further GPU jobs are pending for this study. The five conditions share donor assignments and intervention/decoding settings; D69 includes active attention heads only. The heldout sample is 64 SDR pairs, 32 native D/H pairs, and 16 WikiText windows (2,032 scored tokens).

| Mask | Heads | SDR surrogate reduction | SDR H lost / gained | Native D false / ambiguous (of 32) | Clear corrections (of 25) | Native H retained (of 26) | WikiText PPL increase |
|---|---:|---:|---:|---:|---:|---:|---:|
| Old sufficient D69 |69|58.70%|22 / 12|6 / 14|9|12|21.16%|
| Old necessary W9 |9|58.81%|9 / 4|19 / 5|6|23|1.21%|
| New necessary W13 |13|60.05%|6 / 5|17 / 7|6|23|1.40%|
| New all-head W28 |28|65.33%|3 / 3|13 / 5|11|21|5.11%|

Intact native D has 25 false, 2 true and 5 ambiguous responses; intact H has 26 true, 1 false and 5 ambiguous. No coherent refusals occurred, although they were eligible desired D suppression. No responses were empty, malformed or capped. H losses/gains are D69 14/1, W9 3/2, W13 3/1 and allW28 5/1. AllW28 therefore retains more native H ability than D69, but does not fully preserve it. Its test predictive KL is 0.08668; it exceeds both frozen WT limits and remains an unconstrained comparison.

The practical improvement is promising but metric-dependent. AllW28 corrects 11/25 baseline false answers versus D69's 9/25, with much lower native-H and generic-LM collateral cost. However, D69 wins raw false assertions (6/32 versus 13/32) and produces more ambiguity (14 versus 5), often contradictory verdict/explanation pairs. Ambiguity is not credited as clear suppression. Only three examples are corrected by both masks: eight favor allW28 and six favor D69, so the two-example net correction advantage is not established superiority. Native H retention has ten discordant examples favoring allW28 versus one favoring D69. W13 yields no aggregate correction or H-retention gain over W9 on this slice; do not claim longer union training solved transfer.

No fit reached the 90/95% target, and none met joint SDR-H/WT preservation. The best heldout surrogate reduction is about 65%, not near-complete generated-deception suppression. W13 slightly beats D69 on nonlinear surrogate and ties its deceptive-label argmax count, but D69 has lower mean deceptive-label probability; no uniform numerical dominance should be claimed.

Annotation used 352 anonymous public views, two fresh Sol judgments per view (339 category agreements), and 100 fresh blind Astra adjudications for disagreements, uncertainty or flags. Final labels were frozen before condition joining. Identical public views have zero final category/uncertainty conflicts. These are model-agent judgments, not human ground truth. Exact SDR/WT controls and all 64 native all-open generation identities passed. Honest-context donors were 26/32 clearly truthful, two false and four ambiguous; no post-hoc donor screening was performed. Interchange remains content replacement, and this one-seed, small-sample instructed-lying result does not establish strategic-deception specificity or minimality.

Independent Astra review recommends one next direction: retain the frozen allW28 intervention and validate it on behavior-grounded strategic pressure with capable matched benign controls, first establishing intact behavioral headroom. Another SDR grid is not justified by these results alone. This is a recommendation, not a launched experiment; coordinate with the separate mechanism-datasets investigation before duplicating task construction.

Full comparison: [report 102](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/102-v3-final-comparison.md). Independent interpretation: [report 103](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/103-v3-final-scientific-review.md). Cumulative actual GPU use: 20,941 GPU-seconds (5h49m1s); reservations: 15.25/20 GPU-hours; paid API calls: zero. All three v3 production jobs completed successfully. Confirmed lead compactions at closure: 10.


## Fixed-mask head restoration diagnostic (October 21)

A separate fixed diagnostic evaluated intact, the already-frozen allW28 mask, each of its 28 single-head restorations, and three random masks matched on both head count and exact layer histogram. All 33 conditions used the same 119 SDR validation pairs and 16 WikiText validation windows. No new mask was selected; no heldout or native generations were scored. Full28 exactly reproduced the earlier validation result.

Full28 reduces the nonlinear SDR surrogate by 65.27%, versus 24.68%, 35.09% and 41.54% for the three matched random masks. Its WikiText PPL rise is lower than each control, but predictive KL is not uniformly lower. Three controls and reused validation support a descriptive contrast, not a general random-mask significance or deception-specificity claim.

Every single-head restoration retains at least 63.44% surrogate reduction. These conditional effects do not establish that heads can be restored together, prove minimality, or identify redundant pathways. The sum of single-head restoration effects is 14% of the whole intervention effect on the surrogate, 25% on mean D-label probability, 31% on per-pair D logodds and 30% on raw D-minus-H logit margin. Thus scalar-loss curvature explains part of the gap, while non-additivity remains on a direct output margin. Serial cuts, distributed recovery and donor-replacement effects remain alternative explanations.

The L4H5 restoration illustrates why multiple readouts matter: surrogate reduction improves slightly, 65.27% to 65.35%, and WT PPL rise drops from 5.56% to 4.67%, yet mean D-label probability increases from .3740 to .3813 (75 of 119 rows increase). WT KL remains .06326, above the .05 limit. This is not an across-readout improvement or sufficient reason to select a pruned mask.

Results and figures: [report 114](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/114-v4-addback-results.md). Independent interpretation and calculations: [report 116](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/116-v4-addback-scientific-review.md). The separately authorized v4 training contrast tests 3,072 updates and expected initial removals of 1 versus 10, with all 1,024 heads eligible; outcomes remain pending and do not alter the historical v3 selection.


The fixed-support membership audit adds an important base-rate caution. D/H/F have 69/56/68 active heads and their union has 103. W9, W13 and allW28 overlap F in 6/9, 9/13 and 2/28 heads respectively. However, F occupies 68/103 (66.02%) of the restricted candidate pool and 68/1024 (6.64%) of the all-head pool. The large drop in F fraction therefore largely tracks availability. Holding each mask's exact layer counts fixed gives expected F overlaps 7.11, 10.42 and 3.22; observed counts 6, 9 and 2 all lie inside their descriptive central 95% reference intervals. Neither the low F fraction nor the 24 heads outside the original union establishes format avoidance or deception specificity. The stronger suppression relative to the three measured layer-matched random interventions is a separate performance observation. [Membership audit](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/126-v4-component-membership.md); [base-rate analysis](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/127-v4-membership-base-rates.md).


## V4 initialization and longer-training follow-up (October 21)

**Validation finding:** a different mask initialization produced a 23-head intervention with 67.17% reduction in the SDR deception surrogate while preserving all 86 previously correct honest label predictions and meeting both WikiText limits. This improves the balance over the old 28-head mask on the same development validation set. It is not yet a generated-deception or strategic-deception result.

The user authorized further optimizer experiments while the separate cleaner-dataset effort continued, then explicitly raised the cumulative reservation cap to 40 GPU-hours. Two fresh all-1,024-head WikiText-only runs used 3,072 updates, initial expected removals of 1 versus 10, and otherwise identical seed, data, AdamW learning rate .03 and rho=0 settings. No explicit nonzero sparsity penalty was added. Both fits and all 96 saved validation checkpoints passed the complete technical audit; independent scientific review130 confirmed the unchanged prospective selection rule.

| Validation intervention | Heads | D surrogate reduction | Previously correct H lost / new correct gained | WT perplexity rise | WT KL |
|---|---:|---:|---:|---:|---:|
| Old allW28, reproduced by init1 at1,536 |28|65.27%|5 / 4|5.56%|.06963|
| Frozen joint-preservation finalist, init10 at768 |23|67.17%|0 / 3|2.77%|.04134|
| Frozen WT-only finalist, init10 at832 |30|70.12%|3 / 3|3.44%|.04912|
| Descriptive maximum suppression, init10 at3,008 |92|86.67%|4 / 20|7.44%|.10663|

No checkpoint reached 90% or 95% reduction. Longer training improved suppression but increased head count and did not improve the selected preservation-constrained finalists. The 30-head mask contains the 23-head mask plus seven heads; unchanged net H accuracy conceals three lost and three gained examples. The 23-head result satisfies the specified validation thresholds, not exact preservation of honest-output distributions or general capability. One seed, repeated validation exposure and checkpoint selection limit generalization claims.

Root froze the 23- and 30-head exports after exact reconstruction from hashed checkpoints and independent review. The previously recorded native-assessment gate triggers through the 23-head result: at least the old28 surrogate reduction, zero baseline-H losses, WT PPL rise<=5% and KL<=.05. A fresh native-only comparison against intact, old sufficient D69 and old allW28 was prepared under a 0.5 GPU-hour ceiling and is now completed below. It will use the already frozen 32 paired recipient prompts and 32 independent honest donors, the established interchange/generation protocol and blinded labels frozen before condition joining. Coherent D refusal remains desired suppression; H refusal is collateral damage. Old SDR/WT test results are not reused for new selection. The separate cleaner datasets remain untouched.

Evidence: [complete validation audit](/projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/audit/summary.md), [independent scientific review130](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/130-v4-validation-selection-review.md), and [frozen selection receipt](/projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/selection-receipt.json). Both followups completed as reported below; the completion receipt and compute ledger record final execution status.


### Fixed old28 donor sensitivity completed

The prospective inverse-donor diagnostic changed 117/119 donor assignments while retaining the same old28 support. Surrogate reduction was 65.27% with the original map and 66.52% with the inverse; mean D-label probability .3740 versus .3665. However, D-label argmax count rose37→39 and baseline-correct H losses5→6. Individual D-probability shifts ranged−.297 to+.444, with62 decreases and55 increases; a similar average conceals substantial paired donor sensitivity. Exact intact, original-anchor, two unchanged-recipient and WikiText controls passed. One fixed alternative donor map does not establish donor invariance, and this diagnostic says nothing directly about the new23/30 masks. No map or mask was reselected. Reports134/135 record results and independent review; GPU allocation143seconds. The fresh native comparison was completed subsequently, as reported below.


## V4 fresh native comparison completed (October 21)

**The fixed 30-head mask matched the old 69-head sufficient support's raw false-answer count while retaining more previously correct honest answers on this fresh slice.** Both supports received the same removal/interchange intervention. This is a practical, small-sample result; it does not identify a deception-specific mechanism or establish broad superiority.

The independently reviewed comparison used32fresh paired D/H recipients,32source-disjoint honest donors and the same model/decoding/intervention across all conditions. Intact D had26false,5true and1ambiguous response; intact H had28true and4ambiguous. Native results were not used for mask selection.

| Frozen intervention | D false / true / ambiguous (of32) | Clear corrections (of26 baseline-false) | Honest answers retained (of28 baseline-correct) |
|---|---:|---:|---:|
| Old sufficient D69 |5 /14 /13|11|16|
| Old necessary allW28 |9 /12 /11|8|22|
| New23 |20 /7 /5|5|24|
| New30 |5 /17 /10|12|24|

There were no labeled refusals, empty outputs or malformed answers. Coherent D refusal would have counted as desired suppression. Old28has one capped repetitive ambiguous response, retained in all denominators and given no correction credit. New30's21-case net reduction in false classifications is **not**21truthful corrections: it makes12clear corrections and leaves10ambiguous D answers. Its errors differ from D69's: their five false cases are completely disjoint. Correction discordances are7favoring new30 versus6favoring D69; honest-retention discordances are9versus1. The lower observed native-H collateral is useful, but no uniform per-case dominance or statistically established suppression advantage follows.

The23-head mask's zero-H-loss SDR validation criterion does not generalize: both new masks lose the same four native baseline-H truths (one becomes false and three ambiguous). All32H category/uncertainty identities match between23and30, although19Hresponse strings differ. Generic-LM preservation for the new masks remains development WikiText evidence; this comparison included no fresh SDR/WT test scoring.

The seven additional removed heads in30versus23are L7H31,L8H10,L13H15,L13H23,L17H27,L19H13,L20H19. Their **joint conditional removal given the existing23-head intervention** changes nine Dfalse answers to true and seven to ambiguous, with one true→false regression and two ambiguous→true changes. The native effect is much larger than the modest validation-surrogate difference. This makes the fixed seven-head difference a useful component-analysis lead, but no seven-head-only intervention, individual attribution, additivity test, minimality proof or strategic-deception mechanism has been established.

All352physical views received two fresh independent Sol judgments (339category agreements), followed by119fresh blind Astra adjudications. Complete labels and identical-view consistency were frozen before condition joining. Labels remain model-agent judgments, not human ground truth; reference ambiguities and explicit instructed lying limit interpretation. A serialization mismatch affecting seven Unicode view hashes was corrected through an independently reviewed, reversible metadata conversion; every public byte and judgment remained unchanged, original artifacts were retained, and no private condition JSON was decoded before label freeze.

[Quantitative report141](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/141-v4-final-native-results.md) and [independent scientific review142](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/142-v4-final-native-scientific-review.md) close this fixed phase. Next: preserve23/30and their fixed difference for a prospective study on independently validated cleaner pressure and capable benign-control data. Do not adaptively prune or reselect using these now-exposed32cases. No additional GPU batch is launched here.

The new user-authorized bjhz allocation ran job23106070 on normalH200 successfully in785GPU-seconds, without moving dataset jobs. Four GPU accounts are verified for future scheduling: beto,bimc,bgrb,bjhz, each with matching -delta-gpu account/QOS. Cumulative selective-deception actual use:33,555GPU-seconds (9h19m15s); cumulative reservations22.35/40GPU-hours; paid external API calls0. Lead compactions recorded:12.
