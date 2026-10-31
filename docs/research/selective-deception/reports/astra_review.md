# Independent strategy review: deception specificity and shared circuits

Research advice only, 2026-10-17. No experiments were run. Evidence handoffs: [project evidence](project_evidence.md), [necessity prior art](necessity_prior_art.md), [shared components](shared_components.md).

## Recommendation

Build the paper around **when intervention on shared machinery selectively suppresses deception, and what information that intervention changes**. A new sparse necessity objective is useful engineering, but is not by itself the novelty. First diagnose the current fixed masks with a small matched-control pilot; then run a bounded selective-intervention search using those controls; only scale a promising result and investigate a few causal paths. This is one sequence, not three parallel large projects.

The strongest possible conclusion is that a shared computational substrate contains a selectively controllable pathway mediating deceptive use of retained knowledge. A sound alternative is that apparent deception-circuit necessity arises substantially from donor-dependent intervention on shared answer routing. Both require causal discrimination. Neither follows from overlap, transfer, or a low deception rate alone. ACL acceptance cannot be forecast from the present evidence; an identified computation and persuasive matched controls would strengthen the work more than another large mask inventory.

## What already supports the direction

The artifact audit verifies coarse SDR D∩F and D∩H∩F knockout accuracy of .002, with much higher size-matched null lower tails. D−F also has a substantial effect; D−H−F does not beat its reported null. Thus, the result is not that all exclusive components are irrelevant. It is that large necessity effects reside in shared components and that the most exclusive set is weak under the tested intervention.

D∩H transfer on EVAL 5 is verified; the triple-core EVAL 5 claim is user-reported and was not located in the bounded artifact audit. Current format-wave EVAL 5 results are partial. Do not promote those missing comparisons to completed evidence.

The existing component analysis gives a tractable hypothesis: many core heads support both tasks, while a smaller subset is deception-leaning; L17H24/L24H27 could implement selection or movement. These are candidates, not established roles. Attention patterns and direct logit attribution do not resolve the ambiguity.

The earlier fine-grained donor comparison is an especially useful warning: changing honest to deceptive donors greatly weakened suppression in that historical analysis. However, its approximate 80% figure used an old parsed-row metric and is not a measured effect size for the current coarse circuits. Re-evaluate donor dependence using raw deceptive/n on fixed recipients before making a coarse-circuit claim.

## Novelty assessment

Li, Davies, and Nadeau already optimize removal loss together with retention and sparsity, and explicitly distinguish a causal cut from a complete circuit. Renaming that objective “necessity discovery” would not establish methodological novelty. A new task-specific control construction or causal result could still be valuable. [Circuit Breaking, §§3 and 5](https://arxiv.org/html/2309.05973v2)

Li and Subramani directly compare shared and exclusive sets across nondeceptive tasks; shared components generally dominate necessity, with Addition an exception. Therefore the shared-core phenomenon alone is also insufficient novelty. The new scientific question concerns deception, its relation to honest task competence, and what the transferred intervention changes. [How Much Do Circuits Tell Us?, §5](https://arxiv.org/html/2605.08348v3#S5)

The newer Hydra paper separately evaluates recovery, removal, and task specificity, including a target-removal-minus-collateral metric. A proposed score of “deception suppression minus benign harm” is sensible but should not be sold as an unprecedented general evaluation principle. [Slaying the Hydra, §§4.1 and 5](https://arxiv.org/html/2610.04017v1)

## Minimal sequence and decisions

### 1. Diagnose existing masks with a small, fixed pilot

Choose one current shared-core mask and the most informative existing comparator, rather than all set combinations. Use identical recipients, decoding settings, baseline screens, and scoring across donor conditions. Review actual outputs with labels fixed before comparing interventions; the known grader caveats and harm-pressure noise can otherwise create apparent effects.

Use three discriminating comparisons:

| Comparison | What it tests | Interpretation of failure |
| --- | --- | --- |
| Same facts, choices, positions, and output format; deceptive pressure versus benign truthful task | Selective suppression versus loss of factual answering or choice competence | Comparable benign damage defeats selectivity of this mask; it does not prove no smaller selective intervention exists |
| Same deceptive objective and facts; different output labels/order and one different response format | Template/label dependence versus transfer of a behavioral computation | An effect following the token or position supports routing/default explanations; a failed format transfer alone does not prove the mechanism is formatting |
| Honest versus deceptive donor, plus content-shuffled honest donor, with aligned lengths/positions | Donor-policy transfer versus content overwrite or broad mismatch | Large donor dependence means the estimand is conditional on the injected state; this can still support a useful policy-transfer intervention |

These comparisons can share one compact set of examples. Do not take the full Cartesian product of every benchmark, mask, donor, and format. Use the pilot to identify the decisive ambiguity.

Donor matching needs care: honest versus deceptive donors often also change the chosen answer. Counterbalance option positions and label mappings so that the same surface answer token can occur under different truth/pressure conditions. Hold fact content constant when testing policy, and hold policy constant when testing content. Exact length matching helps positional alignment but cannot by itself equalize meaning or guarantee that the hybrid activation is on-manifold. Content-shuffled donors are a diagnostic stress test, not a neutral deletion baseline.

Include an intact-model baseline and matched random interventions. Size matching alone does not control layer distribution or activation scale; a small layer-matched null is a useful refinement. Existing whole-set effects may saturate, so identical near-zero task accuracy does not establish equal causal strength.

### 2. Run a bounded sparse-intervention pilot, then gate scaling

Once the controls and donor estimand are clear, the user's proposed search is worth a bounded test. Optimize suppression with explicit retention of same-format truthful choice, ordinary instruction following, and coherent responses; allow coherent refusal/evasion on deceptive-pressure prompts. Track broad language-model loss as an additional check.

An unsuccessful fixed-mask specificity test should stop calling that mask specific, **not** stop all subset discovery. Coarse heads can mix roles, and a narrower subset, path, position, or direction may separate them. Conversely, a search should not be assumed capable of finding selectivity merely because the objective requests it.

Limit the initial search to one model, one discovery family, and a small candidate/regularization budget chosen before viewing held-out outcomes. Use training and validation splits to choose the mask; reserve held-out items and a different pressure/format family for evaluation. Compare the suppression–utility tradeoff with the original shared core, the existing deception-leaning subset where appropriate, and matched random interventions. A single weighted scalar can conceal catastrophic failure on one retention task, so retain separate control scores or minimum-performance constraints.

Proceed to larger validation only if held-out suppression improves beyond those comparators without unacceptable benign damage or output collapse. If the bounded search fails, report that limit honestly; it does not establish universal impossibility of selective control. The alternative shared-routing/donor-dependence paper remains available if the mechanism is demonstrated convincingly.

### 3. Identify the computation in the successful or diagnostic intervention

Investigate a few nominated connections, rather than launching the entire path-patching grid. Existing L13 deception-leaning heads and L17H24/L24H27 provide hypotheses to test, but the diagnostic pilot should decide the exact targets.

The valuable explanation would distinguish: factual information remains accessible; pressure changes how the model selects or communicates an answer; intervention changes that selection or pressure response; and restoring the implicated path reinstates the predicted behavior. Probe decodability alone is insufficient evidence that usable knowledge remains. Same-fact benign answering supplies a behavioral check; targeted content/path interventions supply a stronger causal check.

Use counterbalanced answer identities and a benign instruction-switch condition to distinguish a deception-related pressure pathway from a general instruction follower. A successful downstream rescue establishes mediation under that intervention; it does not prove the rescued node uniquely computes deception. Test one alternative path or matched component to make the explanation discriminating. Replicate the key finding on a held-out family and, if feasible, another model after the first mechanism is credible.

## What would falsify or narrow the interpretation?

- **Benign choice and factual accuracy fall as much as deceptive answering:** reject functional specificity for that intervention on the tested distribution. Coherent refusal on pressured prompts remains a success, but broad refusal on ordinary benign tasks is separate collateral damage.
- **Output follows donor content, label, or option position across honesty conditions:** prefer content injection or shared answer routing over a deception-policy interpretation.
- **The effect requires honest-policy donors:** reject an unqualified deletion/removal account. A conditional policy overwrite or steering claim remains viable, and donor dependence can itself be a mechanism worth explaining.
- **Loops, empty outputs, or unrelated text account for the apparent improvement:** retain the raw deception result, but reject a claim of useful coherent suppression until those cases are separated.
- **General instruction switching is equally disrupted:** weaken the claim from deception-selective control to general response-selection control.
- **Different formats change which paths matter:** qualify the mechanism by context; this can reveal composition of shared semantic and format-dependent routes rather than invalidate all causal findings.

F membership is an operational label: membership in the no-pressure control's discovered set. It is not proof that a head's inherent purpose is formatting. Conversely, shared membership does not make selective intervention impossible. Functional specificity is a comparative intervention effect under specified tasks and donors, not a claim that a neuron possesses an exclusive semantic purpose.

## Evaluation and sample size

Keep raw deceptive/n as the headline. Report coherent refusal/evasion, truthful answers, and malformed/looping/empty outputs separately. Do not condition the denominator on parsing, and do not require honesty to rise. Measure benign utility in its own matched task condition. A fluent generic refusal can satisfy suppression while still producing unacceptable benign over-refusal; these are compatible findings.

WikiText coherence is useful but insufficient: fluent models can lose factual choice, instruction following, or task-specific response control with little change in generic text loss. The nearest benign task is the indispensable retention control.

Fifty independent examples can screen for large effects, but do not establish a tight specificity margin or broad generalization. Near a 50% rate, ordinary binomial uncertainty is approximately ±14 percentage points; zero events among 50 still leaves an upper 95% bound around 6%. Paired-difference uncertainty depends on the discordant pairs, and repeated facts/templates reduce effective sample size. Use paired intervals, cluster by shared fact/template when relevant, and freeze or adjudicate noisy judgments. Set the final sample size from the smallest practically meaningful suppression and utility changes, rather than treating n=50 as a paper-wide standard.

## Defensible paper claims

**If selectivity and mechanism succeed:** “A pathway within circuitry shared by honest and deceptive tasks mediates pressure-dependent answer selection. Targeted intervention suppresses deception while preserving matched benign task competence, with retained factual access and transfer to held-out contexts.” This is a candidate claim, not a present result.

**If donor-dependent routing is the result:** “Circuits discovered from deceptive behavior share causally important answer-routing machinery with honest and no-pressure tasks. Interchange interventions on this machinery can suppress deception across contexts, but their effects depend on donor state and do not identify a deception-exclusive mechanism.” To be substantive beyond prior art, explain and predict which donor content/policy changes cause which behavioral outcomes, rather than reporting overlap alone.

**If only broad disruption survives:** the evidence supports limitations of the tested discovery/intervention procedure. That can be a rigorous result, but current overlap plus broad disruption alone is a weaker standalone ACL paper. Avoid claiming that deception has no specific mechanism or that all circuit discovery is invalid.
