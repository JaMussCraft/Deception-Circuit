# Independent scientific design review

2026-10-21. Reviewed `design-options.md`, `data-audit.md`, the completed `project_context/reports/SDR routing pilot findings.md`, and its final scientific review. This review owns only this file. No code, models, notebooks, jobs, git operations, paid APIs, or v2 assets were used.

**Verdict: REVISE BEFORE IMPLEMENTATION.** The factorial design is scientifically useful and substantially improves the completed pilot. The fixes below are concrete and do not require expanding the main factorial. After they are frozen in the protocol/manifest, the design can pass as a controlled validation of perturbation pathways. It cannot uniquely identify a latent pressure representation or a deception mechanism.

## Loadbearing fixes

### 1. Fix the intervention support across donor axes

The instruction to omit changed stakes/record clauses from common maps risks comparing different interventions: an S-only donor might preserve and patch factual-record positions, whereas a T donor changes that record and loses those positions. Larger S versus T effects would then mix information content with intervention-position coverage. This is particularly consequential because earlier key effects depended on common-position rather than readout-only injection.

Before inference, derive a **single shared position-support mask** for every matched story panel, taking the intersection of valid maps across S/T/F donors and both directions. Use that same recipient support for all primary S/T/F comparisons, all four primary routes, their matched sender/receiver controls, and the ordinary sender union. Preserve a map manifest with recipient and donor positions, token strings, semantic role, mapping rule, omitted spans and their reasons. Hash this support before scoring. Self/empty controls must use this support too.

This intersection may leave primarily readout positions. That is an informative design limitation, not grounds to silently loosen support after seeing effects. An additional role-mapped record-position diagnostic is permissible only if its rules are frozen before scoring and identify whether tokens are matched by named identity or by grammatical role. Those conventions are different counterfactuals when truth flips; neither should be described as automatically correct. It must remain a distinct estimand from the common-support comparison. Axis-specific broader maps may be reported descriptively, with explicit position counts, but cannot support a direct claim that the route preferentially carries stakes rather than content.

Common-position and readout-only scope may become identical on some records. Report that equivalence and do not count the rows as independent mechanistic replications. Keep position support identical across the reporting and retrieval comparison too, at least by semantically corresponding span definitions; disclose any unavoidable instruction-span differences.

### 2. Freeze formulas, directions and the actual multiplicity family

“Four primary routes/three-factor contrasts” is not a four-test family. Factor direction, task interaction and incentive alignment can multiply the claims further. Define each confirmatory statistic explicitly, including weighting, recipient truth orientation and sign, before model baselines.

One tractable choice is **12 primary confirmation statistics**, four routes times the following three contrasts:

1. **Stakes × task:** recipient S1, donor S0, conflicting favored identity; patched-minus-intact recipient-truth margin in reporting minus the corresponding effect in retrieval. Average truth identities within each story first. This asks whether the specified stakes-dependent perturbation affects the two readout tasks differently.
2. **Truth perturbation:** T-flipped donor patched-minus-intact margin, always oriented to recipient truth, averaged with equal factorial-cell and story weights. Retain its full directional/task/alignment breakdown beside the summary.
3. **Favored-identity perturbation:** analogous F-flipped donor effect, oriented to recipient truth, again retaining all cell breakdowns. Cancellation in this aggregate is possible; a null summary is not evidence that the path ignores favored identity.

Use Holm correction across these 12 confirmation tests, or a justified simultaneous bootstrap procedure covering exactly these 12. A simpler all-axis formal family is acceptable if the protocol instead freezes every included statistic and adjusts its actual size. Neither choice permits uncorrected significance claims for the additional reverse-S, task, alignment, template or scope contrasts. Those additional cells remain exploratory effect estimates unless the confirmatory family is enlarged prospectively. A nonzero T/F effect does not automatically establish that it exceeds or explains an S effect.

For every outcome define `margin = logit(recipient's damaged unit) − logit(recipient's intact unit)` and `delta = patched margin − intact recipient margin`. Positive delta supports the recipient's factual answer. Never relabel the outcome using the donor's truth. Under T flips this orientation intentionally differs from the donor's factual answer. Preserve S1→S0 and S0→S1 separately; averaging reciprocal signed effects can erase the phenomenon. Show raw constituent cells before an interaction. Do not equate a nominally significant interaction with a uniquely identified computational role.

### 3. Bound bootstrap inference to its real sampling units

The 1,024 fresh cells, 3,072 donor pairs and 44,544 path rows are repeated interventions on **64 constructed base records**, not independent observations. Confirmation has only **32 base records, 16 per template**. The native bridge has 32 different historically filtered story groups. Bootstrap complete story panels, retaining every factorial variant and donor in the resampled unit; stratify by template/split where the estimator assumes those fixed weights. Do not resample path rows as independent trials or pool discovery and confirmation for the primary test.

Freeze the actual entity, unit-pair, template and record tuples before stating an effective sample size. The local pool has only 41 unit pairs. Repeated pairs or entity bundles induce shared lexical structure; distinct hashes or entity names do not guarantee independent mechanisms. Report unique counts and pair/entity overlap across templates and splits. Require disjoint pair/entity bundles between discovery and confirmation where the chosen vocabulary permits, and state what remains reused. If labels are reused within a split, include a prespecified leave-one-pair/bundle-out or pair-block sensitivity summary; if this creates very few blocks, show the instability rather than presenting a second precise population interval.

Two fixed templates cannot support uncertainty over a population of templates. Story-bootstrap intervals describe stability within this designed fixture and its declared sampling model, not naturally occurring deceptive situations, new wording families, or unseen item vocabularies. Deterministic model outcomes supply no independent within-row noise. Two thousand bootstrap draws are adequate as a proposed numerical procedure but do not create extra semantic sample size. Keep native and fresh results separate; the native story exclusions reduce direct reuse without making the source historically unexposed.

## Definitive design choices

**Include the four-sender ordinary replacement union as mandatory.** Freeze L13H20, L13H21, L12H6 and L13H5 together, with the stated 1,280 S/pressure-flip rows, for 45,824 scientific rows before controls. This gives a small free-evolving comparator for the frozen direct-edge tests and is worth its limited added cost. Its magnitude is not the denominator for a mediated fraction and cannot validate direct-path completeness. If an operator cannot fit mandatory rows, return an incomplete study with reasons rather than silently changing this design to optional after results. Numerical controls, map validity and the primary grid take precedence over extra exploratory coverage.

**Do not add 32-token completions to this protocol.** The fixed assistant answer stem already puts the model inside a constrained answer. Continuing it is not a clean assay of spontaneous refusal, and adds a new outcome rubric without resolving the causal question. Record full-vocabulary first-token logits/probabilities, candidate tokens and non-item argmax. Label the latter **other/non-item**, not coherent refusal. A future unforced-generation audit would be a separate task and readout; none is needed for this validation.

## What the protocol does and does not identify

**Pressure versus goal/content.** The S donor holds the record, favored unit and readout task fixed, correcting the original changed-truth donor confound. T/F donors supply valuable competing perturbations. Nevertheless S1 versus S0 changes the relation between bonus and submitted answer, including lexical and semantic content. A route may process goal-relevant answer planning and therefore respond to S without constituting an abstract pressure variable. Identical support and controlled contrasts strengthen identification of this clause replacement, not a text-free concept.

**Benign reuse.** Holding full stakes context in retrieval is appropriate. It avoids deleting all relevant context from the control, but the stakes explicitly concern the submitted review: reporting/retrieval differences may reflect ordinary instruction relevance. A stakes×task interaction therefore supports context-conditioned use of the tested route under these instructions. It does not by itself show dishonest computation, strategic intent, harmful intent, or selective suppression. Similar retrieval effects argue against reporting specificity under this task, not against any pressure-sensitive mechanism elsewhere.

**Ground truth and capability.** Damaged-unit truth is stipulated consistently and remains independent of favored identity. Schema fields should distinguish factual truth, favored target, requested answer and actual argmax, even if the first and requested answer coincide here. Include coherent truth flips, no contradictory sponsor references, actual continuation-token validity and exact final prompt audits in the CPU gate. The proposed ≥80% neutral factual-retrieval gate per template×truth stratum is a reasonable fixed control check. It cannot validate reporting competence: display neutral reporting accuracy in the same strata. If neutral reporting is poor, retain the planned sensitivity diagnostic but withhold reporting-policy/deception interpretation. Do not rescue it by selecting successful stories or changing wording.

**Selection/collider limits.** Retaining all frozen factor cells and not screening on emitted-answer changes addresses the major collider problem of the earlier same-false-donor stratum. Keep baseline argmax strata descriptive; conditional patch effects among baseline-false or donor-agreement subsets are post-outcome selected and cannot become primary mechanistic evidence. A global prospectively fixed capability gate is acceptable as a task-validity endpoint, but report the gate, all rows and any failure rather than presenting only successful templates. Freeze story hashes and exclusions before model inference and never top up failed stories. A small S effect or universally truthful pressured baseline is a valid negative result, not a failure requiring prompt search.

**Maps, numerical validity and full-model limits.** Causal prompt order is well chosen for fresh record-position tests. Native early positions may precede pressure and must retain their accessibility caveat. Grouped K interventions serve four query heads and differ in size from one Q-head intervention; numerical equality and matched controls do not eliminate that structural difference. The outside-mask sender is not a guaranteed null, and a null sender/receiver does not prove all untested routes irrelevant. MLPs remain active, direct paths freeze other components during capture, and ordinary union replacement permits compensation. Their effects cannot establish autonomous heads-only computation or a complete path decomposition.

## Acceptance checklist for the next protocol revision

1. One frozen comparable support definition and hashed maps; axis-specific variants explicitly separate.
2. Exact primary formulas, recipient-oriented signs, confirmation family size and correction fixed.
3. All four sender-union rows mandatory; no 32-token completion audit or inferred refusal labels.
4. Tuple-level split manifest, true story/pair/entity counts, conditional bootstrap interpretation and bundle sensitivity specified.
5. Capability/negative-outcome rules retained, neutral reporting competence displayed, and no outcome-based top-up or new prompt search.

After these edits, **PASS for implementation within the bounded controlled-pathway claim**. Runtime forecasts remain operator planning estimates until calibration; this scientific review adds no GPU authorization, grants no v2 circuit-evaluation approval and does not change the zero-API requirement.

## Final scoped re-review of frozen specification and plan

2026-10-21. **PASS. No remaining must-fix findings in the requested scope.** Re-read the updated `spec.md` and `plan.md` after the coordinator/planner corrections; no implementation or inference was performed.

- Primary common sender support now intersects valid S/T/F maps and corresponding report/retrieval support by semantic named role before inference. Native P/T support is likewise intersected. Extra axis-specific maps cannot enter the primary comparison, and receiver replay support is explicitly separate from sender support.
- A/B/C are defined with recipient-oriented truth margins. A is the conflict-cell S1→S0 reporting-minus-retrieval effect; B retains the sign of T-flip effects; **C now sign-aligns F-flip effects to donor-favored truth versus other**. This C definition supersedes the raw F-flip average proposed earlier in this review and avoids reciprocal cancellation. The four routes × three statistics form an explicit 12-statistic confirmation family with simultaneous max-centered bootstrap bands. Remaining cells are exploratory.
- Both templates hold named-unit record order fixed and flip only damaged/intact predicates. Correct truth is counterbalanced across first/second mentions; the plan explicitly tests this shortcut prevention.
- Complete-story bootstrap, realized unique entity/item-pair counts, lexical split-overlap audits and item-pair-block sensitivity are explicit. Claims remain conditional on the designed fixture and two fixed templates; path-row count is not treated as independent sample size.
- All 1,280 ordinary four-sender-union rows are mandatory in the 45,824-row grid. No free-generation extension is authorized, and non-item argmax is not called coherent refusal. Baseline factual capability and negative-result/stop rules remain prospective without survivor selection.

The earlier revise verdict is resolved by this frozen spec/plan. This is approval of the bounded scientific design for implementation under the existing authorization, not validation of future hook/mapping code, numerical receipts, task capability, or model results. Those remain the stated implementation and baseline gates. There is no expansion to v2 circuit evaluation, new pressure search, paid APIs, or a uniquely identified pressure/deception representation.
