# 215 — V7 frozen position bridge results

**Broader New30 replacement lowers requested-answer margins on both deceptive instructions and benign inversion.** Its additional D drop is 0.821055 and I drop 0.748975; the paired increment difference is 0.072080 [−0.397680, 0.516062]. The exposed small panel does not establish a differential position effect or deception-specific mechanism. The interval also does not establish equivalence. Some first-token choices change under prompt support, alongside I/F capability costs and two native/fp32 boundary disagreements.

Acquisition is complete: sixteen frozen SDR internal-validation scenarios × D/H/F/I × seven states = 448 unique rows. Smoke repeats are excluded. Root confirmed independent 216 audit PASS: all 448 unique rows,240 exact main proof flags,192 historical anchors and112 smoke rows reproduced exactly, and all 64 intact recipient and 64 repeated donor capability records requested-correct in native/fp32. There are15 unique donors. The audit combines source review and saved scalar/proof evidence; full-vocabulary activation/logit arrays were not retained.

## Frozen definitions and intervals

Llama-3.1-8B-Instruct, A40/BF16/SDPA, same V6 manifest, original honest donors and head slices at `o_proj` input. Final support writes donor-final to recipient-final. Prompt support replaces the right-aligned actual-token suffix; unmatched recipient prefix stays untouched. Natural release removes L17H27 from the replaced set and lets it recompute in the perturbed context. It is neither cached-clean rescue nor a distinct mask search.

Let m be fp32 requested-minus-alternative logit margin. Drop E=intact−condition. The primary position increment is E(New30 prompt)−E(New30 final)=m(final)−m(prompt). Restoration is m(release)−m(New30). Single-head drop is m(intact)−m(single). Every position difference below is prompt−final. Positive D/I drops weaken a false/alternative requested answer; positive H/F drops weaken truth. Positive D/I restoration strengthens the false/alternative answer.

All intervals are descriptive 95% paired scenario-bootstrap percentile intervals, 10,000 draws, seed 1729, linear interpolation at (B−1)p. The 16 scenario indices carry all variants and conditions together; D−I is calculated inside each scenario before resampling. Four-cell summaries are descriptive, without subgroup selection or significance gates. Exact full-precision means/intervals and raw records are retained in [analysis JSON](../component-analysis-v7/analysis-001/position-summary.json).

| Fixed margin estimand | D | I | H | F | Paired D−I |
|---|---:|---:|---:|---:|---:|
| New30 position increment | 0.821055 [0.384877, 1.300347] | 0.748975 [0.377967, 1.130778] | 0.385958 [0.023952, 0.764540] | 0.569992 [0.287705, 0.875027] | 0.072080 [-0.397680, 0.516062] |
| Release restoration, final | 1.332758 [0.989605, 1.701940] | 0.798952 [0.565380, 1.067908] | 0.328424 [0.109879, 0.600771] | 0.307148 [0.110236, 0.506755] | 0.533806 [0.258907, 0.810062] |
| Release restoration, prompt | 0.788966 [0.516756, 1.108073] | 0.414851 [0.226759, 0.611082] | 0.271537 [0.078052, 0.468497] | 0.291938 [0.107008, 0.480896] | 0.374115 [0.150378, 0.607833] |
| Release restoration, prompt−final | -0.543792 [-0.739459, -0.360414] | -0.384101 [-0.543784, -0.235535] | -0.056887 [-0.196830, 0.065695] | -0.015210 [-0.107654, 0.066770] | -0.159691 [-0.380396, 0.047405] |
| Single17 drop, final | 1.459625 [1.089544, 1.869576] | 0.918259 [0.672594, 1.196656] | 0.332495 [0.126583, 0.588014] | 0.300520 [0.115739, 0.491797] | 0.541367 [0.238446, 0.857040] |
| Single17 drop, prompt | 1.456772 [1.097715, 1.846905] | 0.901907 [0.648730, 1.183294] | 0.385943 [0.149069, 0.670797] | 0.386073 [0.169645, 0.607103] | 0.554865 [0.262327, 0.857367] |
| Single17 drop, prompt−final | -0.002854 [-0.056916, 0.053793] | -0.016352 [-0.062334, 0.028935] | 0.053448 [-0.001535, 0.105665] | 0.085553 [0.016587, 0.152826] | 0.013498 [-0.024757, 0.046206] |

L17H27 retains positive shared D/I restoration under both supports. Its restoration is smaller under prompt support: D −0.543792 and I −0.384101 relative to final. This is context-dependent release behavior under broader intervention, not a mediated fraction. Single-head D/I effects remain large under either support; their measured position increments are small with intervals spanning zero. That does not establish all earlier positions are irrelevant.

![Individual scenario effects, means and descriptive intervals](../component-analysis-v7/analysis-001/paired-position-effects.png)

[Standalone SVG](../component-analysis-v7/analysis-001/paired-position-effects.svg). Dots show each individual scenario; the fifth column shows its paired D−I difference. Panels have separate vertical scales.

## Requested choices and distributions

Each cell is mean fp32 requested margin / native requested-correct count / fp32 requested-correct count, all counts out of16. D/I request the false alternative; H/F request truth. Intact and all final-support states retain 16/16 requested choices in every variant.

| State | D | I | H | F |
|---|---:|---:|---:|---:|
| intact | 4.673156 / 16 / 16 | 3.825060 / 16 / 16 | 2.737090 / 16 / 16 | 3.065878 / 16 / 16 |
| new30_final | 2.964643 / 16 / 16 | 2.571461 / 16 / 16 | 2.436005 / 16 / 16 | 2.801228 / 16 / 16 |
| new30_prompt | 2.143588 / 14 / 13 | 1.822486 / 15 / 15 | 2.050048 / 16 / 16 | 2.231236 / 15 / 15 |
| release17_final | 4.297401 / 16 / 16 | 3.370413 / 16 / 16 | 2.764429 / 16 / 16 | 3.108376 / 16 / 16 |
| release17_prompt | 2.932554 / 14 / 14 | 2.237337 / 15 / 15 | 2.321585 / 16 / 16 | 2.523174 / 15 / 15 |
| single17_final | 3.213530 / 16 / 16 | 2.906801 / 16 / 16 | 2.404595 / 16 / 16 | 2.765359 / 16 / 16 |
| single17_prompt | 3.216384 / 16 / 16 | 2.923153 / 16 / 16 | 2.351147 / 15 / 16 | 2.679806 / 16 / 16 |

New30 prompt D truthful choices are 2/16 native and 3/16 fp32; I truthful choices are 1/16 in each. Release prompt D truthful choices are 2/16 in each; I truthful choices 1/16 in each. H/F truthful counts equal requested counts. No recorded switch is to an answer outside the requested/truth pair; a first-token truth correction is not a coherent-refusal or free-generation outcome.

| Support | Variant | Mean requested probability | Mean truthful probability | Mean KL(intact ∥ condition) |
|---|---|---:|---:|---:|
| new30_final | D | 0.898314 | 0.093136 | 0.034269 |
| new30_final | I | 0.870800 | 0.124271 | 0.048944 |
| new30_final | H | 0.855187 | 0.855187 | 0.007890 |
| new30_final | F | 0.874972 | 0.874972 | 0.011787 |
| new30_prompt | D | 0.792627 | 0.199988 | 0.202609 |
| new30_prompt | I | 0.793824 | 0.200584 | 0.148281 |
| new30_prompt | H | 0.808352 | 0.808352 | 0.061523 |
| new30_prompt | F | 0.808509 | 0.808509 | 0.054028 |

All condition-level requested/truthful/alternative probabilities, KL, numerical native margins, native-minus-fp32 differences and native/fp32 choices are retained in JSON. The two argmax disagreements occur at zero native requested margin: `sdr:01c5363a3672:D` under New30 prompt (native requested, fp32 truth; fp32 margin −0.069708), and `sdr:37cccc89f347:H` under Single17 prompt (native error, fp32 truth; fp32 margin +0.018879). Native and fp32 answer counts are both reported; neither is substituted for the other.

Every transition from intact is listed below. All D/I transitions go requested→truth; all H/F transitions go truth→the alternative error.

| Condition | Case ID | Readout(s) | Transition |
|---|---|---|---|
| new30_prompt | `sdr:01c5363a3672:D` | fp32 | requested_to_truth |
| new30_prompt | `sdr:0a9ff886140d:D` | fp32 + native | requested_to_truth |
| new30_prompt | `sdr:148521ddc468:F` | fp32 + native | truth_to_error |
| new30_prompt | `sdr:18da46e3fde8:D` | fp32 + native | requested_to_truth |
| new30_prompt | `sdr:18da46e3fde8:I` | fp32 + native | requested_to_truth |
| release17_prompt | `sdr:06c09e898970:F` | fp32 + native | truth_to_error |
| release17_prompt | `sdr:0a9ff886140d:D` | fp32 + native | requested_to_truth |
| release17_prompt | `sdr:18da46e3fde8:D` | fp32 + native | requested_to_truth |
| release17_prompt | `sdr:18da46e3fde8:I` | fp32 + native | requested_to_truth |
| single17_prompt | `sdr:37cccc89f347:H` | native | truth_to_error |

## Construction cells and alignment

| Designation / item polarity (4 scenarios each) | D increment | I increment | H increment | F increment | Paired D−I |
|---|---:|---:|---:|---:|---:|
| identity / 1 | 0.783713 | 0.670604 | 0.156137 | 0.885477 | 0.113109 |
| identity / 2 | 0.032310 | 0.689816 | 0.261970 | 0.368591 | -0.657506 |
| inversion / 1 | 1.880626 | 1.444692 | -0.043430 | 0.052586 | 0.435934 |
| inversion / 2 | 0.587572 | 0.190789 | 1.169155 | 0.973314 | 0.396783 |

D/H/I have identical per-scenario mapping support, mean 99.391259% coverage and 0–3 untouched prefix tokens. F is shorter and 100% covered; its counts and donor correspondence differ. These are positional, not semantic alignments. Equal D/I mapped counts do not establish equal semantic correspondence; F is a descriptive control without token-normalized specificity claims. Full tensor indices and actual-token ordinals are retained. All recipient and donor capability failures are retained by policy; none occurred here. Repeated capability rows represent 15 unique donors, not 64 independent donor samples.

## Scope and accounting

Prompt-minus-final estimates the total incremental earlier-aligned-position intervention in the presence of the final write, including nonlinear interactions. It neither locates a critical earlier token nor isolates donor information or an additive contribution. The sixteen scenarios were previously exposed and component choices were selected in V6; there is no pristine holdout, mask superiority, minimality, semantic circuit, coherent refusal or free-generation claim. The study bridges V6 intervention support and does not reproduce V5 EVAL5 donor response packing/decoding. No new contrast, mask, donor, generation or exclusion was selected from these outcomes.

Root accounting: smoke 87s + main 99s = 186 actual GPU-seconds; 20min reserved; cumulative 38.35/40 reserved GPU-hours; no new API calls. Root compaction count 16. These scheduler totals differ from the internal Python acquisition timer and include job overhead. Scientific review217 is complete and supports the bounded interpretation.

[Independent technical audit216](216-v7-main-artifact-audit.md) verifies the acquisition gate.
