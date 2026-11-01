# Fixed old28 donor-sensitivity diagnostic

October 21, 2026. The same frozen old allW28 intervention retains a similar average effect under one prospectively fixed alternative honest-donor permutation, but individual examples are donor-sensitive. This does not establish donor invariance or deception specificity.

The diagnostic reverses the original within-length-signature rotation: 117 of 119 recipients change donor, two remain identical controls. Four conditions are original/inverse mapping crossed with intact/full28. All inputs, head support, source and WikiText donor mapping remain fixed. It runs only on development validation and changes no mask selection.

| Readout | Original donor mapping | Inverse mapping |
|---|---:|---:|
| SDR D surrogate reduction |65.2652%|66.5172%|
| Mean D-label probability |.3739974|.3664948|
| D-label argmax count /119 |37|39|
| Baseline-correct H lost / newly correct gained |5 /4|6 /5|
| WT perplexity rise |5.5558%|5.5558%|
| WT KL |.0696323|.0696323|

The intact baselines are exactly identical across mappings. Original-full28 exactly reproduces the source-bound earlier addback-panel anchor. Both unchanged-donor rows and every WikiText field are exactly equal across mappings. All four condition records and paired means were revalidated from saved outputs; audit receipt is `sparse-optimization-v4/donor-result-audit.json`.

Mean surrogate reduction improves by 1.252 percentage points under inverse mapping, and mean D-label probability decreases by .00750. Yet D argmax count increases by two and baseline-H losses increase by one. At the example level, D probability decreases on62 cases, increases on55 and is unchanged on the two controls; shifts range from−.29704 to+.44414. Similar averages therefore conceal substantial paired donor effects, and the different readouts need not rank mappings identically. No new donor map is chosen from these results.

This is one deterministic alternative mapping using the same honest donor pool, not a distributional robustness estimate. Honest activation replacement is a content intervention, not neutral deletion. The result concerns old28 only, not the new23/30 finalists. Native donor quality remains separately descriptive and cannot screen evaluation cases.

Job23105342 completed with exit0:0,143 allocated GPU-seconds on one H200, within the reserved0.1 GPU-hour ceiling. The measured conservative runtime guard passed at196.90seconds<=360. Cumulative completed actual allocation is32,770 GPU-seconds (9h6m10s); cumulative reservations remain21.85/40 GPU-hours before the fresh native assessment. No paid API calls.
