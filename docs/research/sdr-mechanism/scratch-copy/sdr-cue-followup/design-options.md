# Bounded follow-up to the original D/H/F cue-circuit study

2026-10-25. Decision advice only; no source changes, model use, GPU work or git operations. Completed source `ca41bfdb2fd4e4c4c784eabd321ea75e41a45299` and its results remain immutable. Original masks only; the separate v2 project and earlier failed gates/stopped grids remain outside this follow-up.

## Recommendation

**Localize S32's replacement effect between the pre-answer context and the supplied assistant prefix.** Reuse the exact 384 neutral prompts, 640 directed E/T pairs, S32 and frozen C_S32. Run early-only, tail-only and their full-prefix union, with intact baselines. This gives a complete two-block factorial at **4,224 scientific completions** and a same-pair joint contrast without head search or new wording. Root selected this bounded design after comparing alternatives.

The ca41 hook replaces **head outputs at query positions** (o_proj-input slices). These are effective intervention sites along the prefix, not attention key/value source positions. This experiment cannot identify which tokens a head reads. Use “prompt-position localization” and “early/tail replacement”; do not infer a reading circuit or selector.

## Options compared

S32 already largely reproduces D/H/F: E donor-example choices rise from 46 to 208/256; T reduces recipient-truth reporting from 170 to 86/256 and retrieval from 128 to 28/128, with each direction present in every fixture. Three actual answer changes in S32 same-answer E pairs reject universal emitted-donor-answer copying; latent answer preference remains possible. A22/B11's opposite E effects motivate later decomposition but do not identify functions.

| Option | New causal question | Approximate main completions | Assessment |
| --- | --- | ---: | --- |
| **S32 early/tail factorial** | Can influence enter through pre-answer context, through unchanged assistant-prefix tokens, or chiefly through their joint replacement? | **4,224** = 384 + 2 families × 3 scopes × 640 pairs | Best next information gain: new causal axis, exact complementary blocks, same-pair interaction and small Boolean-mask extension. |
| Factorial donor example × truth | How do changed donor examples and facts combine, including both changed together? | 2,176 = 384 + 2 × (3 nonself report donors × 256 + 128 retrieval T) | Cheapest, but chiefly identifies combined-content effects. It does not independently manipulate emitted answer or latent answer preference; ET does not itself establish cue-specific representation. |
| Split A22/B11 into fixed components | Is each signed E effect concentrated in a prospectively defined half? | About 3,328 = 256 + 12 target/comparator full-or-half families × 256 E pairs | Useful later. Smaller influential sets alone provide less functional discrimination; arbitrary splitting, replacement occlusion and binary readout constrain interpretation. Freeze any halves without using outcomes. |

Counts exclude calibration/numerical forwards and annotation views. These are alternatives, not an experimental menu. Recommend one fixed early/tail study.

A system-only/user-only/tail-only/full alternative uses 5,504 completions. It separates direct system-record sites from propagated user sites for T, a real extra distinction. But isolated blocks plus full do not give the exact early/tail joint comparison without further unions. The chosen design gives up system-versus-user separation to answer the pre-answer-context versus assistant-prefix question with fewer cells. Neither version identifies attention-source pathways.

## Exact causal question and panel

Keep ca41's renderer, eight named fixtures, r/q/t/f/e crossing, full-response endpoint, donor rules, identity positional alignment, greedy decoding and natural MLPs. Keep all 256 reporting E, 256 reporting T and 128 retrieval T directed pairs; no favorable baseline, fixture or emitted-answer filtering. Use original S32 and its exact C_S32 comparator, not reselected outsiders.

For both families, replace selected head slices at every decode forward in one of three scopes:

1. **Early:** BOS through the final separator after the user turn, ending immediately before the assistant-role header.
2. **Tail:** the complete assistant-role header plus supplied answer stem, ending at the original prefix boundary.
3. **Full:** the exact disjoint union of early and tail, reproducing the ca41 operation.

Intact is the fourth factorial arm, shared across families. Both donor axes change literal tokens only in early: E changes two permitted-example tokens in the user turn; T changes two record-status tokens in the system turn. Tail literal tokens are unchanged within each donor/recipient pair, but natural tail head outputs can carry either difference. The question is whether donor-conditioned influence can be introduced by replacing early outputs, tail outputs or both.

**Canonical boundary:** use the unique assistant-role header in the archived literal CHAT_SHELL, starting at its start-header special token, not the first stem-content token. Include every token of that header (assistant role text, end-header token and subsequent header whitespace) in tail, together with the entire supplied stem. Every original token before that start-header token, including the user end-of-turn separator, belongs to early. Locate this unique structural header in the rendered prompt and bind the exact resulting token boundary per row. Independently verify the special-token IDs/header sequence against the cached tokenizer and manual shell; never infer the boundary by a decoded substring in arbitrary content. Freeze a deterministic boundary rule before model access; ambiguous/missing/non-token-aligned boundaries stop freeze rather than dropping rows.

Independently prove early/tail are nonempty, disjoint, exhaustive over all original valid tokens and identically aligned within each donor pair. Every header/separator/BOS token belongs to exactly one scope. Generated/padding/dummy positions remain false. Capture donors naturally and reapply frozen original-prefix values throughout decoding, as in ca41.

## Controls and frozen descriptions

- **Fresh full-prefix S/C_S arms** anchor the scopes to the known operation, with fresh intact baselines. Do not splice old outcomes into new main denominators. Full-prefix discrepancies must be reported/investigated before localization conclusions, without automatic wording or mask rescue.
- **C_S in every scope** supplies the existing fixed layer/count-matched outside comparison, not a random-null distribution or activation-importance match.
- **Numerical controls for every scope** exercise intact repeat, empty map, captured-self and genuine-patch repeat through generated histories, using actual full-vocabulary finite/tolerance/greedy checks and assignment/mask audits. Unselected coordinates remain untouched by assignment; later natural propagation may differ.
- **System-only E numerical no-op:** on fixed disjoint calibration fixtures, include a diagnostic mask ending before the user header. E changes only later user tokens, so natural donor/recipient system-prefix states must be identical under causal attention. Verify equality through the actual decoding/readout path, including generated contexts. Failure triggers numerical/mapping diagnosis. This is numerical validation, not a new main scientific cell or labeled hypothesis family. Freeze exact slots and forward costs in the specification.
- **Complete donor/recipient/patched triples** retain ca41 semantic/residual categories, raw responses, directions, input alignment cells and all eight fixtures. Every planned row remains in its denominator; calibration is excluded. Same-answer output diagnostics remain descriptive and never control eligibility.

Report patched-minus-intact indicators: E/report donor-first-example and recipient-truth commitments; T/report and T/retrieval recipient/donor truth; every residual category separately. Show scope × axis × task × family components, per-fixture and reciprocal-direction results before differences. Equal fixture weighting remains fixed.

For each pair-anchored identity or residual indicator Y, report:

`I_S = Y(S_full) - Y(S_early) - Y(S_tail) + Y(intact)`

and the identical contrast I_C for C_S, all four component means, and I_S−I_C. This is well-defined because early/tail are exact complements and all arms use the same donor/recipient pair. Binary readout, floor/ceiling, natural propagation and multilayer replacement occlusion prevent treating the contrast as natural redundancy or neural competition. One C_S contrast is not an interaction null distribution.

No scientific success threshold, donor-baseline normalization, significance rescue, fitted model or post-hoc scope refinement. Compare S/C_S on identical pairs. Early/tail differ in length/location and exposure to changed input; amplitudes cannot rank encoding, importance or efficiency. E/T input changes and intact responsiveness differ too.

## Distinguishable outcomes and next inference

| Full-prefix effect reproduced, then… | What this resolves under replacement | What remains unresolved |
| --- | --- | --- |
| Early-only approaches full; tail-only near intact | Influence can enter upstream of assistant prefix and propagate through a naturally recomputed tail. | Which system/user sites or attended tokens matter; natural necessity; content versus latent answer representation. |
| Tail-only approaches full; early-only near intact | An unchanged-input assistant prefix contains donor-conditioned head states sufficient to carry influence. | Cue summary, fact content, latent answer preference and broad context remain possible; no selector is identified. |
| Both isolated scopes approach full | Multiple replacement locations can independently impose the influence. | Does not establish natural redundancy; binary saturation affects the joint contrast. |
| Both isolated scopes are small; full remains strong | The effect depends on the combined early/tail replacement at this partition. | Not proof of naturally distributed coding; replacement consistency, propagation and occlusion remain alternatives. |
| Scopes have opposing signs or a large joint departure | Full replacement obscures distinct conditional contributions across the partition. | Operational interaction is not proof of competition or backup. |
| E and T favor different scopes consistently by fixture | Example-only and contradictory-fact replacements have different effective entry loci here. | Not encoding selectivity: changed input sites/spans and intact responsiveness differ. |
| No coherent localization, large residuals or fixture variation | A uniform locus account is unsupported on this fixed panel. | Preserve the null/heterogeneity; no automatic finer-position search. |

“Approaches,” “small” and “large” describe patterns, not new cutoffs or gates; publish actual counts/components. A null isolated-scope effect does not establish naturally irrelevant heads. T still transplants contradictory content, so recipient errors can be overwrite. No outcome establishes intent, deception-specific function, clean suppression, pressure mediation, reporting-time latent knowledge, OOD or v2 effects. No automatic head/path escalation follows any outcome.

## Engineering and runtime boundary

ca41 records token offsets/roles and changed positions; Replacement.positions already accepts a B×L Boolean mask. Add a study-specific frozen scope manifest, scope-aware IDs/schedule, independent partition oracle and analysis tables. Reuse capture/decode/control machinery. No Q/K/V grid, moving readout injection, donor-generated suffix, head search or new scheduler framework. Preserve old source/results and use separate provenance/outputs.

Main has 480 intervention batches at B8 plus 48 baseline batches, versus ca41's 1,120 + 48; maximum family size is 32 rather than 69. This suggests a modest run, not a runtime forecast. Fresh calibration must cover six family/scope combinations, generated-position exclusion, memory/numerical paths, the system-E no-op and actual I/O. ca41 main observed 1,186 H200 seconds, calibration 663 seconds; use observations plus a reasonable measured buffer, subject to fresh operator review. Do not copy the old seven-hour reservation or assert a new allocation here.

Next: write and independently review this bounded specification, then implement/calibrate under standing authorization. No automatic subsequent experiment or reopened gate.

## Local sources read

- project_context/reports/SDR cue-circuit transplant findings.md
- project_context/reports/SDR mechanism investigation status.md
- .scratch/sdr-cue-circuits/{spec,design-review,final-report-review,analysis,runtime-seam}.md
- Original renderer/position-mask interface in Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/sdr_cue_circuits.py and documented Replacement.positions seam.
- Shared project guidance and relevant SDR/communication memory. No external literature claim was needed.
