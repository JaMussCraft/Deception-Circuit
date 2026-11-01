# Draft native SDR shared-component composition spec

2026-10-26. Proposed exact contrasts for root decision and independent critique. No implementation/run/reservation claim. Companion [design-options.md](design-options.md) records rationale and alternative explanations. Only these two draft files are owned by this design contribution.

## Inputs and interventions

Freeze original Stage1 manifest `stage1-retry-f7cb49f-20261021T002501Z/manifest.json`, its source/mask/prompt hashes and its 24 historical confirmation story IDs. Select all valid primary-pressure P and N prompts at both truth values by **input metadata**, four/story; no H or alternative-P prompts. Require exact 24×4=96 unique inputs and 24×8=192 directed pairs from the companion. Do not reuse the old restricted one-truth-per-story patch schedule: both fixed-fact truth variants are explicitly included here. Preserve historical source exposure and semantic audit categories. Missingness or integrity errors are reported, not fixed by outcome-based substitution.

Use local original Llama3.1-8B-Instruct, cached model/tokenizer identity, BF16, eval, use_cache=False/full recomputation, actual final RMSNorm/unembedding in FP32 for same-path deterministic full-vocabulary greedy scoring, fixed physical B8 padding/dummies. Freeze actual attention backend, software versions and geometry. Preserve original prompt text/token IDs and supplied answer stem; this is completion under that stem, not unconstrained conversation. Cap64 includes EOS; record EOS union. Generated tokens are never patched.

Donor source family bank B_D contains natural donor prefix head outputs. Recipient bank B_0 contains natural recipient prefix receiver inputs/outputs. In an ordinary recipient pass, replace source head slices with mapped B_D only at original `common` mapped coordinates; every unselected component and unmapped token evolves freely. Call this source intervention A. Capture induced receiver bank B_A in that same freely evolving pass; **do not** invoke the old helper that freezes every nonsender output. B_A is already in recipient coordinates and must not be remapped.

The prefix-only clean receiver operator C_R replaces receiver R at every nonpadding original recipient prefix position with B_0[R]. The induced rescue operator T_R inserts B_A[R] into a baseline recipient with no source replacement. For all decode forwards, banks remain fixed to the original prefix, and current generated positions are false. Pre-RoPE Q/K receiver values are inserted before recipient-position RoPE. No donor attention weights or generated suffixes are transplanted. QK means simultaneous Q24 and Kgroup6 input replacement, not attention-pattern replacement. Output means the pre-o_proj per-head slice, preserving all other head slices.

The clean clamp-alone arm is a scientific and numerical control: its generated response should equal baseline when all original prefix states are deterministic. Verify this directly; do not assume it from first-step equality. Same-path self/empty/clean-only failures are integrity failures, not evidence of a mechanism.

## Frozen 20 arms per directed pair

| ID | Source heads replaced | Receiver replacement | Purpose |
|---|---|---|---|
| 01 | U5 | none | Ordinary early-candidate effect; captures B_A |
| 02 | H26 only | none | Same-layer candidate single |
| 03 | U6=U5∪H26 | none | Source factorial joint |
| 04 | S32 | none | Shared-core benchmark on exact same P/N/fact axes |
| 05 | none | clean Q17H24 | Clamp-alone control |
| 06 | U5 | clean Q17H24 | Head-specific query blocking |
| 07 | none | clean K17group6 | Clamp-alone control |
| 08 | U5 | clean K17group6 | Grouped-key blocking |
| 09 | none | clean joint Q24/Kgroup6 | Clamp-alone control |
| 10 | U5 | clean joint Q24/Kgroup6 | Joint blocking |
| 11 | none | induced joint Q24/Kgroup6 from B_A | Conditional receiver-state rescue |
| 12 | none | clean V17group6 | Clamp-alone control |
| 13 | U5 | clean V17group6 | Matched KV-group content-interface comparison |
| 14 | none | clean output17H24 | Clamp-alone control |
| 15 | U5 | clean output17H24 | Nominated head-output blocking |
| 16 | none | clean output17H24–27 | Clamp-alone control |
| 17 | U5 | clean output17H24–27 | Whole-GQA-group output blocking |
| 18 | none | induced output17H24–27 from B_A | Conditional output-state rescue |
| 19 | none | clean K17group0 | Fixed outside-group clamp-alone control |
| 20 | U5 | clean K17group0 | Fixed outside-group blocking comparator |

Count: 96 unique baselines +192×20=3,936 scientific completions. Clamp-alone results may be duplicates across pairs, but remain planned rows with their own receipts. No effect-conditioned cell omission. Numerical controls, fixed forced-step tests and capture-only forwards are separate from these scientific outcomes and counted in runtime provenance. Do not add L24, new head subsets, doses or generated-token interventions.

U5={(12,6),(13,5),(13,20),(13,21),(14,24)}. H26={(17,26)}. U6 is original candidate6. S32 is the exact parent shared32 list/hash. All these sets are subsets of S32; never interpret S32−U6 effect size as an additive residual component. Outside K17group0 supplies H0–3, verified outside D∪H∪F by parent masks; geometry must verify32 Q heads/8 KV heads. Every intervention label and manifest records all affected query heads. Q24 is one head while K6/V6 are four-head shared inputs; do not compare raw magnitude as a size-controlled semantic preference.

## Endpoints and exact contrasts

Primary endpoint is the full-response commitment in recipient coordinates: damaging item, harmless item, both/contradictory, refusal, evasion/no commitment, other/unresolved, cap, execution error. Retain all planned rows and refusal as its own behavior; do not encode refusal as an item or as scientific failure. Preserve exact literal named identity, EOS status, generated token IDs/text/length and blinded response label provenance. Reuse the established finer nine-category annotation scheme where available; aggregate only with an explicit reversible mapping. Fresh blinded independent Sol response annotation/deduplication uses response views; no paid judge. Freeze a question-aware lexical candidate rubric using the shape of `.scratch/sdr-clause-choice/rubric.md`. Annotators see the exact task question, both lexical candidate strings, and complete assistant stem plus generated continuation; hide condition, facts, pressure, arm, masks, donor/source assignments and preferred hypothesis. Annotate lexical candidate identities before root joins recipient factual roles. Deduplicate only identical full annotation views. Use two fresh independent manual Sol raters for every unique view; disagreements retain both labels and explicit adjudication. Task-query visibility is necessary because the commitment is about what result will be shown; do not mistake an item mentioned in a rejection or negation for the committed item.

The damaging item is the instructed relevant disclosure in this native task. A harmless-item commitment can realize withholding of the relevant item, but is not automatically a false factual assertion. Strict threat-avoidance interpretations use only the archived input-defined eligible semantic subset and show its small denominator. Ordinary N reporting establishes how the same machinery operates without the pressure clause. Do not infer strategic intent or prevalence.

Secondary continuous endpoint is first-generation-step raw recipient damaging-minus-harmless logit margin m, using full-vocabulary logits with no minimum-gap filter, normalization or item-forced argmax. Also record true full-vocabulary argmax, actual generated first token ID independently, and whether each is either item. Retain other tokens; do not silently replace a generated token with the separately scored item preference.

For each pair and each endpoint Y (binary category indicators, literal-identity indicators, or m), let Y0 be fresh baseline, YA=arm01, YH=02, YAH=03, YC_R the corresponding clean-alone, YA+C_R the paired blocking arm, YT_R the rescue.

- Early-candidate effect ΔA=YA−Y0; H26 effect ΔH=YH−Y0; source interaction I_AH=YAH−YA−YH+Y0. Show all singles, joint and transitions. Negative interaction alone establishes neither competition nor redundancy.
- Conditional blocking B_R=(YA−Y0)−(YA+C_R−YC_R). Positive B_R means removal of a positive U5 effect for that signed endpoint. If ΔA is negative, report its signed blocking rather than calling the sign a benefit/harm. Never divide by ΔA or call a mediated fraction.
- Rescue ΔT_R=YT_R−Y0; show baseline→U5→rescue triples, including reversals and rescue without U5 behavioral change. This is conditional sufficiency of the induced bank, not reconstruction of a natural serial mechanism.
- Joint-QK interaction on the U5 background J_QK=YA+C_QK−YA+C_Q−YA+C_K+YA. Include clean-only factorial control JC0=YC_QK−YC_Q−YC_K+Y0 and report J_QK−JC0. This is interaction under restoration; nonlinearity/overwrite remain alternatives.
- Group attribution: compare B_output24 with B_output24:27, preserving intervention size; stronger quartet blocking means H24 alone is insufficient for the tested perturbation. It does not assign the difference solely to H26.
- Fixed comparator: B_K6−B_K0 with both singles and clean-only outcomes. Outside controls may be influential; report their effect rather than treating them as a guaranteed null.

Report the four fixed-fact directions separately and the four same-condition fact-flip directions separately, then balanced story-mean summaries within axis. Do not pool reciprocal signed effects before aligning the reporting target. Include recipient and donor actual EOS identities, factual truth, baseline agreement/disagreement and historical threat-semantic class in reversible row tables; agreement-conditioned copying counts are descriptive and never drive inclusion. Fact-flip P donor emissions can be fully aliased with recipient damaging identity; retain this explicit caveat. All 24 stories count equally; pair variants equally within story. Descriptive 95% story bootstrap intervals (fixed seed,2,000 replicates) may summarize these finite selected stories, with no fresh-population or multiplicity-controlled claims. Publish all arms/contrasts and per-story signs; no effect-size gate or post-hoc best path selection.

## Compact induced-state summaries; attention deferred

Root decision: do not implement a new attention path or attention-probability tracing in this study. The current helper lacks replacements and changes the backend; adding an alternate execution path and its parity gate would delay the bounded causal panel. Actual attention allocation, token-span tracing and semantic readouts are explicitly deferred, with no automatic follow-up authorized by this spec.

Use only the already captured compact natural banks B_A and B_0. For each U5 pair and receiver Q17H24, K17group6, V17group6 and each output17H24–27, store L2 norm of B_A−B_0 at the last original prefix token; prefix RMS of the same difference over all original nonpadding prefix token×feature coordinates; and the corresponding B_0 norms. Compute in FP32 from existing bank tensors before releasing them. Record exact shapes/counts and the norm definition; no extra model forwards, alternate attention backend, full attention matrices or new captures. For QK retain Q and K summaries separately; do not merge incompatible dimensions/scales. These descriptors establish that the intervention changed a receiver state, not which semantic variable it represents. Norm rankings across interfaces do not identify contextual selection, factual encoding, causal importance or mediation. Interpret routing/content contributions from the paired Q/K/V/output counterfactual contrasts and their native input axes, with these limited descriptors as a check on induced state changes.


## Integrity and execution boundaries

Freeze model/source/protocol/input/mask hashes, exact20arm grid and batch order before calibration. Calibration covers every operator, mixed-bank overlaps, both unequal-length P/N maps, fact flips, padding/dummy invariance, original-prefix-only replacement at forced step64, Q/K pre-RoPE placement, and KV-group geometry. Compare ordinary U5/H26/U6 assembly with explicit union/singles; test that U5 changes a later natural receiver on a tiny model while the old freeze would produce a different bank. Verify rescue bank is induced by U5 in a free model, not donor receiver or old frozen direct-edge output. Source/receiver overlap at H26 must use the declared input/output hook order. Check manual reference replacement equivalence and bank immutability.

Use same-path full-vocabulary finite/repeat/self/empty checks at declared tolerance, with bitwise flags and maximum differences retained. Same-path baseline/clean-only greedy completions must match through EOS or cap. Cross-hardware archived matching is descriptive, not a bitwise requirement. Numerical, provenance and geometry failures stop for repair; behavioral incorrectness/refusal/null U5 effects do not.

One numerical/timing calibration only, disjoint diagnostic slots or explicitly calibration-only outputs, never counted as science. Then run the whole immutable panel; calibration changes operational batch/reservation choices only. Preserve per-batch atomic receipt, accepted coverage, cap/error/incomplete rows, immutable input/source/run identity and safe deadline guard. Resume only genuinely incomplete fixed batches for operational interruption, keeping failed attempts. No unscheduled follow-up grid, prompt cleaning, model load on login node, notebook execution, paid API, training, merge/push or changes to other investigations.

Archived orientation:4,224EOS main1,109A100seconds; calibration403seconds. Tentative calibration request600seconds, with main sized from its measured forecast and a reasonable buffer. Prior natural EOS batches were roughly3–17tokens; mixed-bank behavior could imply roughly8–44minutesA100 before additional overhead, so neither archived row-count scaling nor a fixed1,800–2,400seconds is a guarantee. Record actual new capture/serialization costs; freeze job walltime from calibration without changing scientific row coverage/cap64, using durable incomplete-batch resume if needed. Root owns release, operator owns numeric ledger, reviewer independently checks final counterfactual arithmetic and coverage.
