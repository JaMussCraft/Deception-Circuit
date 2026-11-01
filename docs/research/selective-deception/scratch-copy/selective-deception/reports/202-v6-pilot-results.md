# 202 — V6 frozen pilot: local answer-routing results

New30 paired D−I margin-drop contrast is -0.107 in development and 0.455 in internal validation. The largest observed single-head D effect is L17H27: ΔD1.016, ΔI1.099, ΔH0.305, ΔF0.382. Its similar D/I changes motivate a shared routing hypothesis rather than a free-generation/refusal claim.

Complete coverage:2688 discovery rows,560 aggregate-validation rows and720 attention rows. All176 causal case/variant rows pass exact actual-backend identities in44 batches; raw margin signs and source/donor joins are checked. This is readout-only honest-donor replacement, not V5 all-position transfer. Development and internal validation scenarios were previously exposed.

## Aggregate effects

Values are scenario-mean intact-minus-condition requested-margin drops (logits). Positive D lowers the false target; positive I impairs benign inversion; positive H/F costs truthful capability. D−I intervals use10,000 paired scenario bootstrap draws, seed2026, percentile95% with linear interpolation. These are exploratory intervals, not p-values or fresh holdout evidence.

| SDR split / condition | n | ΔD | ΔI | ΔH | ΔF | ΔD−ΔI [95% CI] |
|---|---:|---:|---:|---:|---:|---:|
| discovery / new23 | 16 | 0.231 | 0.303 | -0.026 | -0.023 | -0.072 [-0.156,0.015] |
| discovery / new30 | 16 | 1.245 | 1.352 | 0.274 | 0.328 | -0.107 [-0.316,0.093] |
| discovery / oldD69 | 16 | 4.341 | 4.677 | 1.751 | 2.131 | -0.336 [-0.670,-0.020] |
| discovery / random30 | 16 | -0.067 | 0.038 | 0.088 | 0.021 | -0.105 [-0.237,0.033] |
| validation / new23 | 16 | 0.308 | 0.316 | -0.027 | -0.021 | -0.008 [-0.119,0.130] |
| validation / new30 | 16 | 1.709 | 1.254 | 0.301 | 0.265 | 0.455 [0.079,0.856] |
| validation / oldD69 | 16 | 5.550 | 4.544 | 1.423 | 1.762 | 1.005 [0.337,1.697] |
| validation / random30 | 16 | -0.065 | 0.218 | 0.019 | -0.062 | -0.283 [-0.462,-0.101] |

Raw requested margins, intact margins, drops, probabilities, requested/truthful full-vocabulary argmax counts and gains/losses, KL(intact||condition), and four polarity/position strata for every condition are in [pilot-summary.json/raw_tables](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/analysis-002/pilot-summary.json). Every denominator is retained. FAR D/H/F is supplementary, with no matched-I claim.

| Panel / variant | Intact fp32 requested argmax | New30 fp32 requested argmax | New30 mean raw margin | New30 mean KL |
|---|---:|---:|---:|---:|
| far supplementary / D | 16/16 | 6/16 | -0.203 | 0.420 |
| far supplementary / F | 16/16 | 16/16 | 4.950 | 0.010 |
| far supplementary / H | 16/16 | 16/16 | 6.052 | 0.008 |
| sdr discovery / D | 16/16 | 16/16 | 2.140 | 0.052 |
| sdr discovery / F | 16/16 | 16/16 | 3.186 | 0.009 |
| sdr discovery / H | 16/16 | 16/16 | 2.892 | 0.010 |
| sdr discovery / I | 16/16 | 16/16 | 2.456 | 0.052 |
| sdr validation / D | 16/16 | 16/16 | 2.965 | 0.034 |
| sdr validation / F | 16/16 | 16/16 | 2.801 | 0.012 |
| sdr validation / H | 16/16 | 16/16 | 2.436 | 0.008 |
| sdr validation / I | 16/16 | 16/16 | 2.571 | 0.049 |

Supplementary FAR whole-mask drops (n16; no matched I):

| Condition | ΔD | ΔH | ΔF |
|---|---:|---:|---:|
| new23 | 0.488 | 0.086 | 0.059 |
| new30 | 2.502 | 1.664 | 1.251 |
| oldD69 | 4.271 | 4.352 | 3.134 |
| random30 | 0.192 | -0.394 | -0.393 |

## All30 singles and seven conditional releases

[Single-head signed D/I/H/F map](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/analysis-002/single-head-effects.png). Every single head and its scenario interval is retained in `pilot-summary.json/single_head_effects`; the map reports all30, with no ranking-based omission.

Release effect = margin(release)−margin(New30) = Δ(New30)−Δ(release). The released head computes in the perturbed context. This is not cached-clean rescue, an additive contribution, unique necessity or minimality.

| Released head | D release | I release | H release | F release |
|---|---:|---:|---:|---:|
| L7H31 | -0.007 | -0.004 | 0.005 | 0.001 |
| L8H10 | -0.005 | -0.003 | 0.003 | 0.004 |
| L13H15 | 0.011 | -0.002 | 0.003 | -0.018 |
| L13H23 | 0.132 | 0.128 | -0.009 | -0.012 |
| L17H27 | 0.824 | 0.865 | 0.304 | 0.403 |
| L19H13 | -0.016 | -0.016 | -0.026 | -0.015 |
| L20H19 | 0.010 | -0.007 | 0.001 | 0.007 |

Frozen development-only nomination: **L17H27, D release0.824 [95%CI0.511,1.209]**. Rule: largest strictly positive D-release mean across all seven, ties by ascending numeric(layer,head). No positive mean means no nomination. No validation head/rescue/path effect has been acquired or selected by this script.

## Attention and backend boundary

Attention covers8 predeclared development scenarios ×D/H/I ×all30 heads =720 rows. Only the predeclared first two attended scenario keys get raw-token-row charts. Exact key indices, tokenizer strings and weights are preserved in the JSON. Verified semantic segment boundaries are absent: no clause/fact summary is inferred. All30 heads have descriptive entropy/final-key-mass summaries.

First two scenarios: `["[\"Alcove Property\",[\"client\",\"server\"]]", "[\"Alcove Property\",[\"glass\",\"steel\"]]"]`.

SDPA/eager maximum absolute full-vocabulary logit drift is 0.437500 native and 0.463084 fp32; maximum requested-margin drift is 0.250000/0.236446 respectively, with 0/24 native and 0/24 fp32 argmax changes. Both backends separately pass actual clean/no-op/self identity; that does not make their logits identical. Attention is descriptive and does not establish causal mediation or deception processing.

Figures: [example1](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/analysis-002/attention-example-1.png), [example2](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/analysis-002/attention-example-2.png). Raw drift/control rows and all90(head×variant) summaries are in the JSON.

The fixed random comparator is one descriptive mask, not a null distribution; OldD69 has69 heads versus New30’s30. This pilot does not establish New30 superiority, preserved general utility, a refusal circuit or deception specificity. Effects are conditional on this fixed donor and readout correspondence. Independent artifact/scientific review remains separate.

## Reproduction and verification

Standalone CPU entry point: `component-analysis-v6/summarize-pilot.py --output-dir NEW_DIRECTORY --report REPORT_PATH`; it requires all three completion markers before analysis and never polls or launches work. The frozen analysis header was saved before this worker read intervention or attention outcomes. Final artifacts are in `component-analysis-v6/analysis-002/`; earlier rendering version001 is preserved and has identical numerical results. Both attention examples and the single-head map were visually inspected.

`--self-test` passed under base Python3.9 and mgnp Python3.12 with BLAS/OMP/MKL threads fixed to1. Toy checks cover paired D−I means and deterministic percentile intervals, raw margin-drop sign, conditional-release sign, positive-only nomination, and numeric layer/head ties. Final script SHA256: `8350ce1ea05d0cb059c941c7ac8c07985c821b37347a657c341d8a213d74e482`, matching the final analysis JSON's source provenance. Raw inputs, masks, receipts, labels and model code were not edited.
