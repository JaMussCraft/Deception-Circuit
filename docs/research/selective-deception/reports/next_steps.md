# Experiment handoff: selective control of deceptive use of shared circuitry

**October 20 execution update:** the original proposal below is historical. The diagnostic, restricted sparse phase, and stronger all-head extension with matched old-sufficient comparison are complete; see [v3 results](v3_extension.md). The next recommended research step is a frozen-allW28 test of behavior-grounded strategic pressure with capable matched benign controls, after establishing intact headroom. Coordinate with the separate mechanism-datasets thread; do not restart closed fits, reuse final test outcomes for selection, or duplicate dataset work. No new experiment is launched by this note. Live state and budgets are in `.scratch/selective-deception/RESUME.md` and its ledgers.

Status: proposed research plan, 2026-10-17. No experiments, training, or job submissions are authorized by this document alone. The current task is a research synthesis. Begin execution only under the user's experiment authorization and project job policy. Read the [report](../../reports/Deception%20specificity%20and%20shared%20circuits.md), [evidence audit](project_evidence.md), and [independent strategy review](astra_review.md) first. Verify all dated run states and locate current artifacts again before reusing claims.

## Scientific target and measurement contract

Determine whether a small intervention in shared circuitry selectively suppresses deceptive use of otherwise usable capabilities, and identify the information the intervention changes. A necessary set is an intervention-dependent causal control point; it is not automatically a sufficient circuit, a unique mechanism, or a graph-theoretic minimum cut. Sparse removal with preservation follows [Li2023, §3.3](https://arxiv.org/html/2309.05973v2); matched controls and causal findings must supply the contribution.

**Target success:** raw generated deception rate = deceptive/n across every target example, with coherent refusal/evasion accepted. Never condition on parsed rows, truthful-plus-deceptive rows, or successful task compliance. Do not require honesty to rise. Report truthful response, coherent refusal/evasion, malformed output, empty output, and repetition/token-cap hits separately. Retain the raw denominator even when output is malformed, but do not describe malformed-driven suppression as useful coherent control. Evaluate benign utility separately, including excessive benign refusal.

**Intervention:** primary interchange, with explicit donor policy, mask granularity, token windows, alignment, decoding, and strength. Honest donors include meaningful prompt/continuation states: interchange is replacement, not neutral removal. Mean/zero are secondary sensitivities, assessed for output damage. Coherent donor-dependent refusal remains a behavioral success; it narrows an unqualified mechanism-removal claim.

**Current evidence boundaries:** completed D∩H transfer is verified; current format-suite D/H/F LB cells are partial; triple-core eval5 is user-reported without an independently located artifact in the bounded audit. The older fine-mask donor result used a parsed-row metric and does not measure donor dependence of the present coarse mask. Preserve these distinctions until new artifacts resolve them.

## Stage 1: diagnose one fixed shared-core mask

### Selection and small data package

Use D∩H (43 heads) as the default because its eval5 and component-analysis artifacts are verified; use the 32-head triple core instead if its exact composition and relevant artifact are verified before selection. Choose one existing comparator, preferably D−F if the question is shared-versus-exclusive necessity. Include intact-model and layer/size-matched random interventions. Keep every MLP intact; compose heads-only masks at **leaf granularity** to avoid admitting all ungated MLPs.

Use approximately 50–100 distinct fact/scenario clusters for a diagnostic, not confirmatory inference. Construct three small, coordinated comparisons rather than a full benchmark × mask × donor × format Cartesian product:

| Comparison | Hold fixed | Manipulate | Primary discrimination |
|---|---|---|---|
| Same-format benign versus deception | Facts, options, entity order, length/positions where possible | Pressure/objective requiring deception versus truthful benign objective | Suppression versus lost factual/choice competence |
| Changed-format deception | Facts and deceptive objective | Label mapping, option order; one alternative/free response format | Behavior transfer versus token/position default |
| Donor crossover on paired instructed deception | Recipients, mask, decoding, eligibility, judge cache | Honest twin; matched deceptive state; content-shuffled honest state | Policy transfer versus injected content/routing |

Counterbalance truth/falsehood, item position, label token, and designation. The same surface answer token must sometimes correspond to honesty and sometimes deception. Hold fact content fixed for policy contrasts and policy fixed for content contrasts. Length/position matching improves alignment without proving hybrids are on-manifold. Shuffled donors are a mismatch stress test, not a neutral ablation baseline. If an aligned content-matched policy-neutral donor is feasible, declare its construction before viewing results.

Freeze item IDs and any full-model eligibility screen **before interventions**, then reuse them for all masks and donor conditions. Do not re-screen for each result. Keep an unselected audit slice, including initially honest target responses, to detect newly induced deception. Fit/discover donor assignments without scored target outcomes; paired honest/deceptive twins are deliberate counterfactual conditions, not outcome-selected donors. Save donor IDs, pair mappings, reference generations, hashes/configs, and shared judge-cache identity.

### Validate controls and graders

Inspect a blinded sample of existing generations first. Resolve known grader problems—empty harm-pressure output labeled honest, MASK refusal-D interpretation, LB rejection guard, and stochastic judge/cache differences—before confirmatory re-screening. Record old-versus-fixed labels rather than silently replacing historical estimates. Report harm-pressure separately because claims about knowing an answer can turn an evasive response into a deceptive judgment.

A benign control must have adequate intact-model performance and require the computation at issue. Check factual/choice accuracy, correct label mapping/format, and truthful response under comparable pressure or instruction conflict. Show that label/order manipulations preserve intact-model task validity; otherwise format transfer is confounded by changed difficulty. Broad text KL/NLL is supplementary. Neither probe decodability nor fluent text alone proves usable factual knowledge.

### Deliverable and decision

Produce one compact table of paired target/benign changes, output categories, donor contrasts, and matched-random effects; include representative blinded transcripts. Analyze whether answers follow donor policy, donor content, or recipient position. Use paired intervals clustered by fact/scenario as needed. With n=50, uncertainty is broad: near 50%, a normal approximation is about ±14 percentage points; zero/50 leaves an upper 95% bound around 6%. Six random masks cannot support fine significance claims; a small null is exploratory.

**Decision:** reject specificity of the current mask if matched benign damage is comparable, or narrow its interpretation if donor content determines outputs. Proceed to the bounded Stage 2 search even after this failure: whole-set damage does not rule out a selective subset/path/position. A malformed-dominated target effect requires fixing the output-control specification before treating the search result as useful.

## Stage 2: fit a bounded selective-removal pilot

### Locked scope and objective

Use one model, one discovery family, and the validated controls. Default candidate space: coarse head groups within D∪H∪F, plus any outside supporter nominated from the existing audit **before** examining held-out outcomes. Record the candidate restriction; a negative result cannot rule out interventions outside it. Start with one granularity and declared token window. A later subspace/edge/position search is a separate decision, not an automatic expansion.

Let z_i=1 mean remove group i. Keep base weights fixed and fit only the mask under donor scheme a:

\[
\min_z\ \widehat R_D(f_{-z,a}) + \lambda\sum_i z_i
+\sum_k\beta_k[\widehat L_{B_k}(f_{-z,a})-\widehat L_{B_k}(f)-\epsilon_k]_+.
\]

Use a differentiable relaxation during fitting and evaluate the final binary mask. Sparsity penalizes **removed** mass. An equivalent constrained target is minimum deletions subject to target deception ≤τ and each benign degradation ≤ε_k. The latter makes the scientific goal clearer but does not certify a global optimum.

For enumerable answers, the target surrogate can minimize probability of all deceptive alternatives. For free generation, treat teacher-forced likelihood as a surrogate and evaluate independently graded generation: reduced likelihood of one lie can shift mass to another. Do not require a uniform output distribution or a particular honest answer. Do not apply retain KL to original deceptive continuations.

Keep retention strata separate: (1) same-fact truthful task/choice; (2) benign answer mapping and formatting; (3) truthful tasks under comparable pressure/instruction conflict; (4) a small neighboring-capability set appropriate to the hypothesis; (5) broad benign instruction utility and refusal, with text KL as auxiliary. Use labels and task scores alongside benign-distribution KL. An aggregate scalar cannot offset catastrophic failure in one stratum with improvement in another.

### Splits, bounded budget, comparators

Split by fact/scenario cluster. Use training for mask fitting; validation for regularization/threshold selection; untouched test clusters and an unseen pressure/format family for the scaling decision. Never select a threshold on the final transfer result. As an initial bounded design, choose four regularization/budget settings and two optimization seeds, with four reporting budgets such as 2/4/8/16 removed heads where feasible. These are proposed resource limits, not empirically optimal settings; lock actual settings and practical tolerances before fitting. Do not interpret failure at a tiny budget as failure of every larger mask.

Compare the entire held-out suppression–utility frontier with the original core, the preexisting deception-leaning subset when available, an unconstrained suppression mask, generic high-impact heads, and size/layer/position/intervention-matched random masks. Compare at similar benign cost and report each stratum, not only a favorable weighted average. Reuse fixed recipients/donors and decoding. If a control circuit is much larger, show its cost/effect point without implying equal budgets.

**Scaling gate:** require a reproducible held-out improvement over the existing and matched-random frontiers, acceptable malformed-output rates, and all declared benign tolerances. Choose numerical tolerances from practical needs and sample size before testing; the literature supplies no universal cutoff. If intervals cannot resolve the proposed gain, mark the pilot inconclusive and calculate the sample size needed before expansion. A failed bounded search limits this search space/optimizer/data, not the possibility of selective control.

## Stage 3: validate transfer and explain 1–3 components

Only after Stage 2 improves the frontier, freeze mask, thresholds, graders, donors, and primary endpoints for larger validation. Hold out facts, label vocabularies/order, output format, incentive wording, and at least one task family. Include new donor draws and the declared policy/content crossover. Report mean/zero sensitivities separately if they destroy output quality. Set confirmatory sample size from the smallest useful paired target gain and allowed benign loss; account for cluster dependence and judge noise.

Select 1–3 stable components or paths from the successful intervention. Current hypotheses include L13H5/H20/H21 or L12H6 transmitting information to L17H24/L24H27, but their mover/selector roles remain unproven. Do not launch the full deferred 1,920-cell grid by default. Before patching, write predictions contrasting: selected-answer content transfer; pressure/incentive policy transfer; general instruction switching; and nonspecific output damage.

Cross source information and receiver Q/K/V routes where supported; counterbalance answer identity and compare matched benign instruction changes. Restore a narrow candidate path after knockout and test whether the predicted behavior returns; include a matched alternative path/component and benign rescue control. Restoring the entire removed block is an implementation check, not a discriminating mechanism. Test add-backs for local irreducibility and interactions/backups; do not call a thresholded gradient mask globally minimal. Repeat the decisive mechanism contrast on a held-out family before broader model replication.

## Claim ladder and stopping conditions

| Outcome | Defensible claim | Claim to withhold |
|---|---|---|
| Selective frontier gain, retained same-fact ability, predictive pressure-path patch/rescue | Shared machinery contains a controllable pathway mediating deceptive use of retained knowledge, within tested contexts | Universal or unique deception mechanism |
| Coherent transfer depends predictably on donor content/policy | Conditional redirection through shared answer-routing/control machinery | Donor-independent removal of deception |
| Coarse mask damages benign tasks, sparse pilot succeeds | A narrower intervention separates uses that coarse overlap merged | Whole shared core is deception-specific |
| Bounded pilot fails selectivity | Tested discovery/intervention procedure failed under declared controls and budgets | No selective pathway exists |
| Only malformed/collapsed output suppresses deception | Raw behavioral change with broad disruption | Useful coherent suppression |

A narrower donor-routing mechanism study remains possible if selective suppression fails, but it needs predictive causal evidence beyond overlap. Neither generic shared-core dominance nor the sparsity-plus-preservation objective is sufficient novelty. Keep refusal success and benign utility separate throughout.
