# Membership base rates and layer-matched reference

October21,2026. **The lower discovered-F fraction of oldallW28 does not, by itself, show avoidance of discovered F.** F occupies68/103=66.02% of the restricted search space but only68/1024=6.64% of the all-head search space. Observed F fractions are oldW9:6/9=66.67%, oldW13:9/13=69.23%, and oldallW28:2/28=7.14%—all slightly **above** their respective global availability fractions. The roughly tenfold fraction change primarily tracks the candidate-pool change.

Used only the frozen support/export identities in `sparse-optimization-v4/component-membership-reference.json`, SHA256 `26a1fec572fc04a48832b9f2a63fc02ead10a362d277c728ca53f495486247f0`. Reference and source remain unchanged. No performance, checkpoints, model, GPU, job or selection was accessed or modified.

## Matched reference calculations

For a fixed mask size n sampled uniformly without replacement from its actual candidate pool, expected overlap with support S is `n·|S∩pool|/|pool|`. OldW9/W13 use the exact103-head union; oldallW28 uses all1024query heads.

The layer-matched reference additionally fixes **each mask's exact observed removed-head count n_l per layer**. Within each layer, sample uniformly without replacement from the applicable pool's N_l heads. The overlap distribution is the convolution across layers of `Hypergeom(N_l,K_l,n_l)`, where K_l is the number of candidate heads in S. Its expectation is `Σ_l n_l K_l/N_l`. The table's interval is the exact discrete2.5th–97.5th percentile interval of that convolution, computed with combinatorial probabilities; no Monte Carlo, p-values or performance data were used.

| Mask / support | Observed overlap | Global expected | Layer-matched expected | Layer-matched central95% interval |
|---|---:|---:|---:|---|
|oldW9 / D|9|6.029|5.831|3–8|
|oldW9 / H|5|4.893|2.867|1–5|
|oldW9 / F|6|5.942|7.110|5–9|
|oldW9 / union|9|9.000|9.000|9–9|
|oldW13 / D|11|8.709|8.743|6–11|
|oldW13 / H|5|7.068|5.057|3–7|
|oldW13 / F|9|8.583|10.418|8–12|
|oldW13 / union|13|13.000|13.000|13–13|
|oldallW28 / D|4|1.887|2.875|0–6|
|oldallW28 / H|2|1.531|2.188|0–5|
|oldallW28 / F|2|1.859|3.219|1–6|
|oldallW28 / union|4|2.816|4.500|1–8|

All three masks use layers with greater discovered-F availability than their global pool. After holding those layer counts fixed, their F overlaps are below expectation by1.110,1.418 and1.219heads respectively. Observed/expected ratios for F are0.844,0.864 and0.621under this conditional reference. However, **each observed F count lies inside its layer-matched central95% interval**. These small count differences describe relative underrepresentation against a specified layer reference; they do not establish deliberate or reliable avoidance of discovered F.

Equivalently, oldallW28's26heads outside discovered F compare with26.141expected under all-head sampling and24.781under layer-matched sampling. Calling26/28a format-avoidance result without these base rates would be misleading. Its24heads outside the discovered D/H/F union compare with25.184globally expected and23.500layer-matched expected—also unremarkable as a membership count alone.

D overlap is above its layer-matched expectation in all three masks; oldW9's9Dheads exceed that reference's central interval. H overlap changes interpretation after conditioning on layers: oldW13's5Hheads are essentially its layer-matched expectation5.057, despite being below the global expectation7.068. These are descriptive comparisons of historically selected masks, not independent confirmatory findings about convergent discovery or behavioral selectivity.

## Interpretation limits

The masks were optimized and selected, not randomized draws from these reference distributions. Layers are themselves selected by optimization; conditioning on them is a useful structural adjustment, not an experimentally justified null. D/H/F memberships overlap, so their intervals are neither independent nor simultaneous. This analysis supplies no causal or confirmatory p-value claim, and does not change a mask or selection criterion.

“Outside discovered F” remains only a support-membership statement. The coarse sufficient F support does not exhaust format machinery. Neither low F overlap, D enrichment nor leaving the original union establishes absence of format effects, deception specificity, necessity or strategic-deception generalization. Future frozen v4masks should receive the same **actual-pool and exact-layer-count** reference alongside raw composition, rather than treating cross-search-space fractions as directly comparable.

Verification: stdlib exact combinatorial arithmetic; checked every convolved probability distribution sums to1within1e−12 and its computed mean matches the layer-sum expectation within1e−12. No original reference or source file was edited.
