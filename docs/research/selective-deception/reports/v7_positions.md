# Prompt-position bridge: broader effects remain shared

**Expanding New30 from the final token to the aligned prompt suffix further weakens both deceptive and benign-inversion answer preferences.** The added D drop is 0.821 and I drop 0.749; their paired difference is 0.072 [−0.398,0.516]. This small exposed panel does not establish a differential position effect or deception specificity; the interval does not establish equivalence.

V7 holds the V6 model/runtime, 16 SDR internal-validation scenarios, original honest donors and three masks fixed. Each scenario has D/H/F/I variants; seven states yield 448 unique rows. D/I request false alternatives under different instructions; H/F request truth. Final support replaces the last prompt-token head outputs, while prompt support replaces each mapped token of the right-aligned donor/recipient intersection. Unmatched recipient prefixes remain untouched. [Independent 216 artifact audit](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/216-v7-main-artifact-audit.md) passed, including exact historical anchors and repeated smoke rows.

| Additional New30 margin drop, prompt−final | Mean [descriptive 95% interval] |
|---|---:|
| D | 0.821055 [0.384877, 1.300347] |
| I | 0.748975 [0.377967, 1.130778] |
| H | 0.385958 [0.023952, 0.764540] |
| F | 0.569992 [0.287705, 0.875027] |
| D-I | 0.072080 [-0.397680, 0.516062] |

Intervals use 10,000 paired 16-scenario bootstrap draws, seed 1729, with all variants/states carried together. These scenarios were previously exposed and component choices came from V6.

All final-support states retain 16/16 requested choices in every variant. Under New30 prompt support, requested choices become D 14/16 native versus 13/16 fp32, I 15/16 in both, H 16/16, F 15/16. D departures select truth, while the I departure is a benign-inversion task failure. F also loses a truthful choice. Two native/fp32 boundary disagreements are explicitly retained in the detailed report, including one native-only H error under Single17 prompt. First-token changes do not establish coherent refusal or generated deception suppression.

L17H27 remains a shared local causal lever: natural release restores D/I requested margins by 1.333/0.799 at final support and 0.789/0.415 under prompt support. Releasing means letting the head recompute inside the perturbed network, rather than cached-clean rescue. Its restoration is smaller with the broader intervention. Single-head D/I drops remain 1.460/0.918 final and 1.457/0.902 prompt; their position increments have descriptive intervals spanning zero. Neither result establishes mediation percentages or earlier-position irrelevance.

![Paired scenario effects](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v7/analysis-001/paired-position-effects.png)

D/H/I mapping coverage is matched within each scenario, averaging 99.391% with 0–3 untouched prefix tokens. F is shorter and 100% mapped, with different donor correspondence. Alignment is positional rather than semantic. All 64 intact recipient and 64 repeated donor records are capable in native/fp32; the donor records represent 15 unique donors.

Prompt-minus-final measures the total earlier-position increment while retaining the final write, including nonlinear interactions. It does not locate a critical token or isolate donor content. V7 is a readout-support bridge and does not recreate V5 EVAL5 donor response packing or free generation. No outcomes justify a deception-specific circuit, broad utility preservation or a new adaptive mask.

[Detailed results and transition case IDs](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/215-v7-position-results.md), [full arithmetic/raw summary](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v7/analysis-001/position-summary.json), [standalone SVG](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v7/analysis-001/paired-position-effects.svg). [Independent scientific review217](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/217-v7-final-scientific-review.md) is complete and supports these bounded claims.

V7 used 186 actual GPU-seconds and 20 reserved minutes, no new API calls. Cumulative reserved GPU usage is 38.35/40h.
