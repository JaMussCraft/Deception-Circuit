# 209 — V6 follow-up: exposed validation routing contrasts

Cached-clean L17H27 rescue increases requested-answer margins for both deceptive D (+1.476) and benign inversion I (+0.879), with H/F truth-margin increases +0.340/+0.304. The matched Q27-versus-Q26 path-drop differences are +0.082 D and +0.069 I, with much smaller H/F differences. Ordinal agree/disagree truth-margin intervals include zero in all four variants. Every state retains16/16 requested argmax answers per variant in both native and fp32 readouts; these are margin effects without observed answer changes on this panel.

Complete main acquisition only:64 case variants from16 scenarios ×10 states =640 rows. The earlier four smoke scenarios reappear here and are counted once through main rows only. These are local readout interventions on previously exposed internal validation data, not free-generation/refusal measurements. All raw condition rows, margins/probabilities/KL and native/fp32 argmaxes are retained in the analysis JSON. No filtering, new labels or reselection is performed.

## Three frozen contrasts

Rescue is requested margin(clean recipient L17H27 rescue)−margin(original New30). Ordinal sensitivity is recipient-truth margin(agree)−margin(disagree); D/I requested margins are negated to orient toward truth, H/F are unchanged. Path contrast is requested-margin drop(Q27)−drop(Q26), where each drop=intact−path. Q26 is a matched comparator, not a null.

| Variant | Clean rescue − New30 [95% CI] | Ordinal agree − disagree, truth [95% CI] | Q27 drop − Q26 drop [95% CI] |
|---|---:|---:|---:|
| D | 1.476 [1.095,1.879] | 0.031 [-0.227,0.277] | 0.082 [0.042,0.122] |
| I | 0.879 [0.623,1.159] | -0.044 [-0.256,0.152] | 0.069 [0.045,0.095] |
| H | 0.340 [0.126,0.607] | 0.095 [-0.101,0.295] | 0.003 [-0.009,0.014] |
| F | 0.304 [0.106,0.505] | 0.110 [-0.096,0.334] | -0.005 [-0.015,0.006] |

All intervals use10,000 paired scenario-cluster draws, seed2026, percentile95% with linear interpolation; they are exploratory on exposed validation, not fresh holdout or p-values. Full per-scenario and four-stratum effects and native/fp32 gain/loss counts are retained for every contrast.

## Raw requested margins and answer choices

Each cell is mean requested margin / fp32 requested-correct count / native requested-correct count, all out of16. D/I request the false alternative; H/F request truth. Native probabilities/margins were not saved; the numerical logits/probabilities/KL here are the recorded fp32 readout, not reconstructed native values.

| State | D | I | H | F |
|---|---:|---:|---:|---:|
| intact | 4.673 / 16 / 16 | 3.825 / 16 / 16 | 2.737 / 16 / 16 | 3.066 / 16 / 16 |
| original_New30 | 2.965 / 16 / 16 | 2.571 / 16 / 16 | 2.436 / 16 / 16 | 2.801 / 16 / 16 |
| release_17 | 4.297 / 16 / 16 | 3.370 / 16 / 16 | 2.764 / 16 / 16 | 3.108 / 16 / 16 |
| clean_rescue_17 | 4.441 / 16 / 16 | 3.450 / 16 / 16 | 2.776 / 16 / 16 | 3.106 / 16 / 16 |
| self_rescue_17 | 2.965 / 16 / 16 | 2.571 / 16 / 16 | 2.436 / 16 / 16 | 2.801 / 16 / 16 |
| ordinal_agree_New30 | 2.887 / 16 / 16 | 2.567 / 16 / 16 | 2.508 / 16 / 16 | 2.816 / 16 / 16 |
| ordinal_disagree_New30 | 2.918 / 16 / 16 | 2.523 / 16 / 16 | 2.413 / 16 / 16 | 2.707 / 16 / 16 |
| total_sender_13 | 4.591 / 16 / 16 | 3.647 / 16 / 16 | 2.735 / 16 / 16 | 3.060 / 16 / 16 |
| path_Q27 | 4.588 / 16 / 16 | 3.747 / 16 / 16 | 2.730 / 16 / 16 | 3.065 / 16 / 16 |
| path_Q26 | 4.670 / 16 / 16 | 3.816 / 16 / 16 | 2.732 / 16 / 16 | 3.060 / 16 / 16 |

[Rescue/path figure](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/followup-analysis-001/rescue-and-path-effects.png); [complete JSON, all raw cases/probabilities/KL and metadata](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/followup-analysis-001/followup-summary.json). Contextual release and cached-self comparisons are in the figure/JSON. Cached-self must reproduce original New30; contextual release recomputes in the perturbed context and is not cached-clean rescue. The Q path isolates a direct residual→normalization→Q route under clamps, not all sender-mediated paths or K/V routes.

## Donor capability and composition

| Arm | Recipient assignments | Repeated capability rows | Unique donor IDs | fp32 correct repeated / unique-all-repeats | Native correct repeated / unique-all-repeats |
|---|---:|---:|---:|---:|---:|
| original | 16 | 64 | 15 | 64 / 15 | 64 / 15 |
| agree | 16 | 64 | 16 | 64 / 16 | 64 / 16 |
| disagree | 16 | 64 | 16 | 64 / 16 | 64 / 16 |

Union across original and new arms: 38 unique donor IDs and 38 unique donor scenarios. Do not sum per-arm counts as independent observations; repeated D/H/F/I records and cross-arm original/new reuse are explicit. Capability is diagnostic and never changes recipients/donors/denominators.

Frozen205 lexical composition: unordered recipient/donor answer-pair matches0/16 agree and1/16 disagree; truth-token matches0/16 in both arms. This is ordinal truth-slot assignment sensitivity with heterogeneous vocabularies, lengths, facts and donor activations, not isolated position causality or factual/lexical copying. The JSON reports arm overlap/length composition, descriptive overlap strata, and separates donor-only argmax words from recipient-option choices; full n16 primary remains unchanged.

Technical coverage: `{"cases": 64, "control_batches": 16, "control_cases": 64, "donor_capability_rows": 192, "rows": 640, "scenarios": 16}`. All complete-row source/pack/selection joins, true/requested margin signs, cached-self identity, direct path controls, Q-slice isolation and donor capability provenance are checked before aggregation. Native/fp32 agreement is checked case by case. Independent208 raw/scientific audit remains separate. No mediated fractions, additive decomposition, minimality, superiority or deception-specific mechanism claim follows.

## Additional descriptive composition and verification

New donor minus recipient neutral-H prompt-length means are −0.375 tokens for agree and +0.375 for disagree; each actual recipient variant's length and donor lexical metadata remain in the JSON. Only one recipient has any donor-answer overlap in either arm. Its D/I truth-oriented agree-minus-disagree effects are +1.271/+0.762; the other15 recipients' corresponding descriptive means are −0.052/−0.098. H/F values are −0.291/−0.244 in that single case and +0.121/+0.133 in the other15. These predeclared metadata-based comparisons are a disclosed composition sensitivity description, not powered subgroup inference or a revised endpoint: the primary denominator remains all16. No native or fp32 argmax is a donor-only answer token; donor-token/recipient-option coincidences remain separately counted, without a copying conclusion.

Contextual-release restoration D/I/H/F is +1.333/+0.799/+0.328/+0.307. Cached-clean minus contextual-release is +0.144/+0.080/+0.012/−0.003. Cached-self restoration is exactly zero. These are distinct interventions, not additive or fractional contributions to the whole mask.

The standalone CPU script passed synthetic truth-orientation, rescue/ordinal/path sign, scenario-bootstrap and invalid-mapping checks under Python3.9 and Python3.12 (BLAS/OMP/MKL fixed to1). Only the complete main run was analyzed; no smoke effect was inspected or used for selection. The standalone PNG/SVG was visually checked. No GPU/API/job/git operations or runtime-source/receipt/mask/label edits occurred.
