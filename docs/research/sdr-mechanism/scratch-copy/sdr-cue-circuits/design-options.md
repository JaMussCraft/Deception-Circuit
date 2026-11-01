# Direct original-mask cue-selection study: design options

2026-10-24. Proposal only; lead compactions **5**. No model/GPU/jobs/APIs/notebooks/git/source/ledger changes. Root owns design selection, review and release. Preserve all prior evidence and concurrent work.

**Recommend a single named-form causal panel with independently reversed permitted-example order integrated now.** Another stand-alone behavioral search would postpone the original D/H/F question. Conversely, intervening while example order remains fixed leaves a major causal variable unidentified. This study concerns reference/answer selection and factual collateral under neutral context; it cannot identify deception, pressure, intent or psychological D/H/F modules.

## Three concrete options

1. **Original-mask neutral interchange without example crossing:** reuse256 named-form rows, transplant same-fixture truth-flipped states. Cheapest code/prompt change, but donor-fact transfer cannot distinguish lexical identity from the permitted-example default. Large full-mask effects may simply overwrite answer content. Insufficient advance over existing content-confounded pilot.
2. **Integrated example/content transplantation: selected by root.** New example-order baselines and the same frozen ordinary family interventions distinguish context-example sensitivity from factual-content sensitivity. Measure both tasks, with every input-defined agreeing/discordant cell. Seven original families and matched controls answer a bounded shared-versus-exclusive question directly. The full384-row scope and family selection below are root decisions under delegated authority, not details explicitly specified by the user.
3. **Readout-only or teacher-forced attribution pilot:** fewer forwards, but static donor injection at the moving readout is a different intervention from prompt-context replacement. First-token or teacher-forced results could again disagree with complete answers; they cannot establish selection or factual preservation. Useful only as secondary diagnostics after ordinary full-completion effects, not as the primary next study.

## Recommended prompts and manifest

Use all eight frozen cue fixtures, four/template, in original rank order; retain their identities, entities and pairs. **Named form only is an explicit new input-defined scope**, motivated by prior capability results, not a subset of successful individual baselines. Do not claim full-panel, new-population or OOD coverage.

Archive exact cue literal norm, intro, named record, favored sentence, neutral wording A, `.THE`, manual shell and task stems. Independently cross record order, question order, truth and favored identity exactly as before. Reporting adds `example_order=0/1`: change only the order of the two quoted permitted answers, retaining interrogative options independently. For example, after the unchanged question, switch `Only respond with "The result I will show you is bonds" or "The result I will show you is stocks".` to the reversed examples. Lab uses `reading`. Retrieval has no permitted examples and is unchanged; **do not fabricate a duplicate example factor for retrieval**.

Reporting:8×2record×2question×2truth×2favored×2example=256 rows. Retrieval:8×2record×2question×2truth×2favored=128. **384 unique baseline prompts.** The runtime seam's tokenizer audit verifies report-example reversal changes exactly two token IDs, preserves length and fits B8/L224 with cap64. Independently audit truth-flip positional alignment before freeze; no silently dropped token-mismatched pairs.

Each reporting recipient has two natural intact donors from this same panel: (E) reverse examples only, or (T) reverse truth only. Each retrieval recipient has T only. Both directions occur automatically, with no emitted-answer matching or success filtering: **512 reporting plus128 retrieval directed recipient/donor pairs=640**. Favored, order, task and example factors are fixed on each T pair. E preserves all facts. Do not cross tasks or stories as donors. Retrieval has no nontrivial E counterfactual; do not report identical-prompt self replacement as evidence of factual selectivity under E.

## Original families and controls

Resolve original seed42 head masks from the reviewed format-control suite, pin their file hashes and explicit layer/head lists; verify D69/H56/F68 and union103. Compose at leaf granularity excluding every MLP.

Targets: **D69, H56, F68, S=D∩H∩F32, A=D−(H∪F)22, B=(D∩H)−F11, J=D−F33=A∪B**. A and B are disjoint. Shared32 contains candidate6 and selector2. These candidates and conditional grouped-K/head-specific-Q paths are context, not additional tested families or established roles.

For each target, choose one outside-union family with identical head count **in every layer**: SHA256 rank eligible heads by `["cue-circuit-outside",20261024,target_symbol,layer,head]`, select the required count/layer, tie-break head ID. Root's strengthened choice selects C_A first, C_B excluding C_A within each layer, and C_J as their union; the other four controls are independent fixed draws. Freeze selections before outputs; exact feasibility is verified, with no fallback. Reuse across other families is documented. One draw supplies a comparator, not a null distribution or significance claim. **14 intervention families total.**

Parents test original masks directly; S and A/B/J connect shared membership to the strong native D−F versus weak fully-exclusive comparison. H-only2, F-only21, DF-only4 and HF-only11 are not separately tested. No exhaustive decomposition, additive attribution or inference that parent differences equal exclusive effects follows.

## Ordinary full-completion intervention

Capture each donor's natural, unpatched post-attention head outputs at all original prompt positions. Replace the selected recipient family's outputs at those same aligned prompt positions, leaving every other component—including all MLPs—and every generated-token position natural. All selected layers receive their frozen donor states; this is ordinary family interchange, not isolated-edge mediation or removal.

The current runner disables KV cache and recomputes the full sequence each step. Therefore **reapply the fixed donor prompt-position captures on every decoding forward**, through EOS/cap. Causality makes donor prefix captures invariant to appended recipient text. A one-time patch followed by release would primarily perturb the first generated token and is rejected here. Do not replay donor-generated continuations or inject the stem state into the moving generated readout. Prompt alignment/slot masks require independent numerical tests; do not build a generalized alignment framework.

Complete every baseline and intervention greedily to EOS or64 tokens under fixed B8/L224, BF16 SDPA and actual full-vocabulary FP32 RMSNorm/unembedding readout. Full-completion semantic identity/kind is primary. First-step margins may be a labeled secondary diagnostic, never a substitute endpoint. Frozen-prefix replacement can overwrite content or block intermediate states; a causal effect is not proof of a natural encoded variable or mediated fraction.

## Fixed contrasts and predictions

Annotate complete stem+response views with two fresh independent full-coverage blinded raters and third adjudication for disagreement; restore every planned row. Preserve refusal/evasion/ambiguity/contradiction/malformed/cap/error, raw text and separate formatting. Quoted own unambiguous answers remain semantic commitments. No parser/success-conditioned denominator.

- **Behavior:** example-order paired flips versus invariant lexical identity, across truth alignment and every fixture; retain the remaining cue factors. This identifies the example manipulation within the new panel, not a universal copying rule.
- **E transplant:** change in recipient-relevant reporting rate, donor-example-first match, fixed lexical match and every residual category, relative to intact recipient; reciprocal directions separately. Input-defined agreement/conflict between example-first and truth/lexical identity are mandatory, not favorable output strata. A context-example account predicts shifts toward the donor's first example at fixed facts; a pure lexical account predicts invariance to E.
- **T transplant:** change in recipient-factual correctness, donor-factual identity match and all residuals, separately by task/example alignment. This quantifies recipient-factual disruption and donor-content following under contradictory-fact replacement. It is not a clean collateral/suppression test: donor overwrite remains an alternative, and retrieval has no nontrivial counterpart to reporting's E axis. It does not estimate utility damage from E or deception suppression.
- **Family specificity:** compare each original family effect against its exact-layer/size outside control on identical recipients/donors. Contrast shared/exclusive effects and full-parent effects without ranking by raw magnitude across unequal sizes. A shared task-bottleneck account predicts both report changes and retrieval disruption; an example-sensitive reference contribution predicts E effects at fixed facts, potentially dissociating from T effects. Neither requires psychological labels.
- **Joint interaction:** for each fixed recipient/donor and outcome indicator Y, compute `Y(J)−Y(A)−Y(B)+Y(intact)`, then average within fixture and across fixtures. Compare to the same formula for coherent C_A/C_B/C_J on all640 pairs, separately by task/axis/alignment and reciprocal direction. Binary ceiling/floor, nonlinear readout and overwriting downstream states can produce interaction; no natural redundancy, competition or additive mediated fraction follows. One coherent comparator remains a descriptive comparison, not a statistical interaction null.

Publish complete baseline→intervention category transitions, committed flips/same/residual pairs, raw counts and equal-fixture contrasts; task/template results and input-defined agreeing/discordant cells remain visible. Each family has640 planned intervention outcomes: reporting E256, reporting T256, retrieval T128. Each E direction has128 outcomes; report T directions128 each and retrieval T directions64 each. Reporting example-first/truth agreeing and conflicting cells each retain128 outcomes per axis, with lexical agreement also visible; no emitted-success subset changes a denominator. Every baseline and residual stays in its relevant planned denominator. No fitted classifier, outcome-selected stories, effect threshold, bootstrap significance, head/position search or rescue round. Already-inspected eight fixtures are explanatory scope, not fresh confirmation.

## Compact compute and release outline

| Item | Planned quantity |
|---|---:|
| Natural baselines/donor contexts |384|
| Directed donor pairs |640|
| Ordinary transplant completions |640×14=8,960|
| Main scientific completions |9,344|
| Full-cap generation bound at B8 |1,168 physical batches×64=74,752 forwards|

The generation bound excludes donor capture, repeat/empty/self controls, padding required by distinct intervention batches, loading and I/O; operator must add them explicitly. Grouping by family/axis/task can increase padding: forecast the actual frozen batch schedule, not just the minimum. Capture only required union/control heads and retain prompt tensors locally; do not download massive activations or save a new tracing platform.

Use the two disjoint original calibration fixtures. Freeze a small calibration schedule covering every family, both donor axes, both tasks and replacement/self controls before outcomes; calibration is excluded from inference. Bind exact code/import/model/tokenizer/software/hardware/shape; numerical controls compare full vocabulary, finite values,≤1e−5 and identical greedy token, with bitwise status recorded. Fresh actual patched-forward timings and **full64-cap** forecast determine one suitable H200 allocation, potentially longer than an hour. No mean-answer-length forecast or old timing receipt transfer. Independent design/source/manifest review precedes root calibration release; forecast mismatch stops for review, not automatic sharding or panel reduction.

**Root decisions selected:** option2; full384 baseline scope; sustained prompt-prefix interchange; the seven A/B/J-inclusive targets and coherent outside controls. The full `spec.md`/`plan.md` now govern exact triples, decode-wide controls, matched donor alignment and batch-journal forecast. E/T amplitudes alone do not establish preferential encoding; no donor-response normalization or output-selected denominator is allowed. Fresh calibration and a fitting allocation remain review/release steps. No implementation or inference is released by this proposal.
