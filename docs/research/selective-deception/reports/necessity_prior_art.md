# Necessity masks, selective behavior removal, and defensible deception-mechanism claims

## 1. Is suppressing deception with preservation and sparsity a new objective?

### Takeaway
No. The proposed three terms substantially reproduce Li, Davies, and Nadeau's 2023 targeted edge ablation objective. A defensible contribution must come from the deception-specific causal question, unusually strong contrastive controls, generalization, and a mechanistic account of the resulting intervention—not from combining necessity, collateral preservation, and sparsity.

### Cited Findings
- **Exact citation:** Maximilian Li, Xander Davies, Max Nadeau, *Circuit Breaking: Removing Model Behaviors with Targeted Ablation*, first submitted September 12, 2023; v2 January 29, 2024. Section 3.3, Eq. 2 minimizes `L(G_-E, D_train) − α L(G_-E, D_behavior) + λ R(E)`, with R penalizing the removed-edge set's size. Eq. 3 uses keep gate w in [0,1]: `w v + (1−w) μ`; gates start at one and are thresholded after fitting. Section 1 explicitly frames the result as causal cuts; section 5 contrasts necessary horizontal cuts with sufficient circuits. Section 4.1 prints `R(W)=Σw` with a positive coefficient, apparently inconsistent with its intended few-ablation regularization. This is a notation/sign issue, not grounds to claim a new objective. — [Paper, §§1, 3.3, 4.1, 5](https://arxiv.org/html/2309.05973v2); [dates](https://arxiv.org/abs/2309.05973).
- The released training code rewards preserved gate mass: `penalty += max(0, p.sum() * (epochs_trained-20) / 10000)` and `loss = -1 * (penalty + alpha * tox_loss) + owt_loss`. Thus the operative sign encourages keeping edges while increasing toxic loss. — [Author code, train_mask.py](https://github.com/xanderdavies/circuit-breaking/blob/main/toxicity/train_mask.py).
- **Very close selective pruning precedent:** Shengming Zhang, Le Zhang, Jingbo Zhou, Zhi Zheng, Hui Xiong, *LLM-Eraser: Optimizing Large Language Model Unlearning through Selective Pruning*, KDD 2025. Section 4.2.2 Eq. 10 learns a soft parameter mask by minimizing retain loss minus scaled undesired-knowledge loss plus `β||m||₁`. Here m is a keep mask and the positive L1 term promotes sparse *retention*, differing from sparse *deletion*. Section 4.3 prunes and adds selective post-training, divergence preservation, and contrastive disentanglement. It is parameter unlearning rather than identification of an intact model's deception mechanism. — [Author-hosted paper, §§4.2.2–4.3, Eqs. 10–14](https://zhoujingbo.github.io/paper/2025LLMEraserKDD.pdf).
- **Do not conflate the two circuit-breaking papers:** Andy Zou and colleagues' *Improving Alignment and Robustness with Circuit Breakers* appeared June 2024. Its Representation Rerouting method fine-tunes representations, using ReLU of cosine similarity to original harmful representations plus L2 preservation on retain examples (Algorithm 1). It does not discover Li-style sparse edge cuts. — [2024 paper, §3 and Algorithm 1](https://arxiv.org/html/2406.04313v4); [citation and dates](https://arxiv.org/abs/2406.04313).
- **Necessary and sufficient masks jointly are also established:** Lei Yu, Jingcheng Niu, Zining Zhu, Gerald Penn, *Functional Faithfulness in the Wild: Circuit Discovery with Differentiable Computation Graph Pruning* (2024). DiscoGP combines faithfulness of the retained circuit (Eq. 3), near-uniform target outputs of its complement (Eq. 4), and sparsity (Eq. 5), in Eq. 6. This preserves target function in a circuit and disables that same function in its complement; it does not preserve an explicitly matched set of benign behaviors in the edited full model. — [Paper, §3, Eqs. 3–6](https://arxiv.org/html/2407.03779v1).
- **Current October 2026 prior art matters:** Vaidyanathan, Urbaniak, Bunnapradist, Naim, Waxman, *Slaying the Hydra: Interaction-Aware Circuit Discovery in Language Models*, submitted October 2, 2026. Section 4.1 measures necessity by patching the candidate circuit and task specificity via `Net = min(1, Kill_target) − mean_j max(0, Kill_j)`. The target cap avoids rewarding extra destruction; the per-control floor prevents improvements on one task cancelling damage on another. JuntaLearner learns rankings using set-level causal effects and accounts for backups. Merely introducing collateral-aware circuit evaluation would therefore also be an insufficient novelty claim. — [Paper, §§3–5](https://arxiv.org/html/2610.04017v1).

### Inferences
- Describe the method as **contrastive, preservation-constrained targeted ablation applied to deception**, with attribution to these precedents. Evaluate the scientific claim that the selected communication or computation is more involved in deceptive use of a capability than in matched benign use.
- Replacing generic retain perplexity with matched task controls strengthens the empirical identification argument; it is not automatically a novel optimizer.
- Avoid claiming “first necessary circuit,” “first sparsity plus preservation objective,” or “deception circuitry discovered because removal lowers deception.” Search results establish clear precedents against the first two, and the last requires additional evidence below.

### Gaps
- This is a targeted primary-source review, not an exhaustive proof that no earlier deception-specific selective-mask paper exists.
- No implementation claim about the local pipeline is made here; no experiments or notebooks were run.

## 2. What does a sparse destructive mask identify, and how do redundancy and interventions change the claim?

### Takeaway
The immediate result is an intervention-dependent set whose joint removal suppresses the measured behavior on a specified distribution. It may be a useful causal cut or a shared bottleneck; it is not automatically the mechanism implementing deception, a uniquely necessary set, or a sufficient deception circuit.

### Cited Findings
- Shi, Beltran-Velez, Nazaret, Zheng, Garriga-Alonso, Jesson, Makar, and Blei's *Hypothesis Testing the Circuit Hypothesis in LLMs* (NeurIPS 2024), §3.2 Eq. 7, tests **partial necessity** by asking whether candidate-circuit knockout damages faithfulness more than reference-circuit knockouts. Their framework separately evaluates sufficiency, independence, and minimality. Random reference distributions are part of the estimand rather than an afterthought. — [Paper, §§3.1–3.2](https://papers.nips.cc/paper_files/paper/2024/file/abccb8a90b30d45b948360ba41f5a20f-Paper-Conference.pdf).
- *Rethinking Circuit Completeness in Language Models: AND, OR, and ADDER Gates* (NeurIPS 2025), §3.1 and Figure 1, demonstrates why faithfulness and completeness under sparsity select different subsets: one side of an OR can preserve function, whereas disabling an OR requires hitting both; disabling one side of an AND suffices, whereas executing it requires both. Its toy gate framework is useful evidence against a universal necessary-versus-sufficient size ordering, not a complete characterization of arbitrary transformer computations. — [Paper, §3.1, Figure 1, Corollary 2, Appendix B](https://arxiv.org/html/2505.10039v1).
- Miller, Chughtai, and Saunders' *Transformer Circuit Faithfulness Metrics Are Not Robust* (COLM 2024) identifies six intervention choices: granularity, component type, replacement value, token positions, direction, and circuit versus complement. Existing scores change substantially with these choices. — [Paper, §§2–3, Table 1](https://arxiv.org/html/2407.08734v1).
- Li and Janson's *Optimal Ablation for Interpretability* (NeurIPS 2024) replaces a component by a learned constant minimizing expected ablated-model loss, motivated in part by distinguishing lost information from adverse effects of the replacement value itself. This underscores that arbitrary zero/mean replacement is a substantive intervention choice. — [Primary paper](https://openreview.net/pdf?id=opt72TYzwZ).
- Lee, Hwang, Lim, and Kim, *Does Localization Inform Unlearning?* (EMNLP 2025), compare selected and equally sized random parameter regions and a controlled oracle region where target information was learned. Across their tested models and unlearning losses, oracle localization offers only marginal benefit over random regions. Successful output modification does not by itself locate stored knowledge; their result concerns trainable parameter updates, so it is an analogy and caution, not direct evidence that fixed activation cuts are arbitrary. — [Paper, §§3–4, Tables 1–2](https://arxiv.org/html/2505.16252v1).

### Inferences
- **Joint necessity is not individual necessity.** A set S can suppress deception when removed even if each member's isolated removal has little effect, because redundant routes compensate. Conversely, several serial components may each be individually necessary, making many equally small destructive sets possible.
- **Inclusion-minimal versus minimum:** inclusion-minimal means no strict subset meets the suppression and preservation criteria; minimum means smallest among all feasible sets. Gradient mask search plus thresholding establishes neither without additional checks. Test leave-one-out add-backs for local irreducibility and report optimizer/seed dependence.
- **“Cut” is functional unless proven structural.** Calling a mask a graph-theoretic min-cut would require a defined source/sink and a separation property. Behavioral optimization through a nonlinear network need not find such a cut.
- **No general size ordering:** a long serial chain has a one-edge disabling cut and a long sufficient path; many short parallel routes can require many cuts but only one sufficient route. Do not assert necessary circuits are always smaller.
- **Interchange can overwrite rather than remove.** An honest donor can directly supply a competing answer or instruction state. If only a matched honest donor works, report that as counterfactual redirection, not ablation-independent destruction of a deception mechanism. Compare donors with independent content and preserve only relevant matched factors.
- A mechanism claim needs a causal narrative—e.g., transmission of an incentive signal, belief-to-message selection, or pressure-conditioned response policy—and predictions about which source information, receiver computation, token position, and task manipulation should change the effect. Generic label production or response-format heads remain plausible explanations until tested.

### Gaps
- Neither knockout effect nor low structural overlap alone establishes unique localization. Distinct masks can identify alternative bottlenecks or alternative representations of the same process.
- A finite set of paraphrases, donors, and benchmarks can support a bounded generalization claim; it cannot establish removal of all possible deception.

## 3. Which concrete approach, controls, and stop/go criteria support an ACL mechanism paper?

### Takeaway
Rank the program as: (1) fit a simple selective deletion mask with explicit matched preservation constraints; (2) test it on untouched task families and formats plus intervention controls; (3) only after selective suppression survives, explain a small set of paths causally. Frame the contribution around what enables deceptive use of shared capabilities, and accept coherent refusal/evasion as successful suppression.

### Cited Findings
- Existing feature-level work shows that behavioral editing can be embedded in an interpretability program: Marks et al., *Sparse Feature Circuits: Discovering and Editing Interpretable Causal Graphs in Language Models*, discovers feature graphs and uses targeted feature ablation to alter a classifier relying on a spurious feature. This is relevant precedent for “understand then edit,” rather than evidence that sparse editing alone identifies the target mechanism. — [Primary paper](https://arxiv.org/abs/2403.19647).
- Model pruning can hide concentrated failures behind stable aggregate utility: Hooker, Courville, Dauphin, and Frome's *Selective Brain Damage* reports systematically disparate pruning effects across examples and classes. This motivates local controls in addition to aggregate retention. — [Authors' institutional publication page](https://research.google/pubs/selective-brain-damage-measuring-the-disparate-impact-of-model-pruning/).

### Inferences
The following is a proposed design, not a published method or an empirical finding.

**Objective, with unambiguous signs.** Let z_i=1 mean remove component/edge i; f_{−z,a} denotes deletion under a prespecified donor/replacement scheme a. Fit the unchanged base model's mask only:

\[
\min_{z\in\{0,1\}^{d}}\quad
\widehat R_D(f_{-z,a})
+\lambda\|z\|_0
+\sum_{k}\beta_k[\widehat L_{B_k}(f_{-z,a})-\widehat L_{B_k}(f)-\epsilon_k]_+.
\]

Here R_D is deception risk on target prompts, B_k are separate benign-control strata, and epsilon_k is each stratum's allowed degradation. A constrained version (`min |z| subject to target risk ≤ τ and each benign drop ≤ ε_k`) makes the scientific target especially clear. A sigmoid/hard-concrete relaxation can fit masks; always evaluate the final binary intervention. Use sparsity of removed mass, not kept mass.

A practical differentiable target can be an existing deceptive-answer likelihood or logit surrogate, but label it a surrogate. Where answer classes are enumerable, minimize total probability of deceptive alternatives rather than maximize the likelihood of one designated honest answer. For free generation, the headline endpoint must be independently graded generated deception, because teacher-forced likelihood can shift mass into a different lie. Do not force a uniform output distribution as the desired target behavior.

**Success semantics.** Headline raw deception rate is deceptive/n over every target example, not deception among parsed or truthful responses. Coherent refusal and evasion are legitimate successes and need not make honesty rise. Separately report empty output, incoherence, malformed output, and excessive refusal on benign prompts. A refusal saying “I cannot disclose that” can be success; random characters or premature EOS are damaged outputs. Use an explicit output audit to distinguish those cases rather than treating every unparsed answer as damage or every empty answer as safety.

**Preservation strata beyond general language-model KL.** Keep these separate to prevent easy tasks hiding damage in the task's actual machinery:

1. Same facts/entities and same answer choices with deceptive incentive removed; checks knowledge, reading, and task solution.
2. Same answer format, arbitrary labels/permutations, entity order, length, and token positions on benign tasks; checks format and answer mapping.
3. Honest prompts under comparable pressure or conflicting instructions; checks pressure comprehension and general instruction following.
4. Benign persuasion, strategic planning, belief attribution, negation, and roleplay as appropriate to the hypothesized mediator; checks neighboring reusable capabilities.
5. Broad instruction utility/perplexity and harmless refusal rate; checks global damage but cannot replace 1–4.

Avoid applying retain KL to the original deceptive response distribution on target prompts; it would penalize the change being sought. Counterfactual benign prompts are the preservation control. If auxiliary target-side constraints are needed, constrain coherence rather than copying the original harmful continuation.

**Decisive evaluation package, ranked.**

1. **Specificity frontier:** plot held-out raw deception reduction against each matched utility drop, over deletion budgets. Compare to size-, layer-, position-, and intervention-matched random masks; an unconstrained suppression mask; generic high-impact heads; the existing sufficient-circuit knockout; and the honest/format control circuit. Compare utility-matched points, not one hand-picked threshold. Use an untouched final test set, multiple seeds, paired bootstrap intervals, and report every benign stratum.
2. **Distribution transfer:** freeze masks, prompts, thresholds, and graders before evaluating new deception families and unseen templates. Hold out entity/fact content, label vocabulary and mapping, free-form versus multiple-choice response, incentive wording, and task family. A leave-one-family-out matrix is more convincing than within-template random splits.
3. **Intervention robustness:** primary interchange with donor pools independent of scored test labels; repeat with new donor samples, neutral/content-matched donors and honest donors, then mean and zero as secondary sensitivity analyses. Mean/zero incoherence should be shown explicitly. Repeat over token windows and graded intervention strength. Donor dependence is an interpretable result, not something to average away.
4. **Mechanistic follow-up:** choose a few stable paths; selectively patch pressure/incentive or belief information into recipients, test content swaps and token windows, and predict how true-versus-false answer choice changes. Restore selected clean activations after knockout to test rescue; require matched benign rescue controls. A reversal by reinstating the entire knocked-out block is a basic implementation check; narrow, hypothesis-specific rescue is stronger mechanism evidence.
5. **Redundancy and minimality:** add back each removed member or groups to establish local irreducibility; test combinations that expose backups. Vary granularity or resample training data to distinguish stable functional roles from unstable individual gates. Structural stability is useful, but functional replication can matter when masks differ.

**Proposed stop/go rules (choose numerical tolerances before testing).**

- **Go for a mechanism paper:** selective target effect beats matched random and shared-task controls at comparable benign utility; survives untouched task/format transfer; coherent suppression persists under declared donor variation; and targeted patch/rescue experiments support a specific mediator over generic output damage.
- **Go for an empirical evaluation paper, narrow claim:** multiple standard discovery methods reliably find shared task/format infrastructure and fail the above specificity tests, with strong matched controls and a reproducible correction. This needs a contribution beyond the already-published general observation of shared circuitry.
- **Stop the deception-specific mechanism claim:** target gains disappear under label remapping, only the trained format works, matched benign solution/format collapses comparably, or honest donors merely overwrite outputs and neutral interventions fail. These outcomes may still be useful selective control results, but do not identify a dedicated deception mechanism.
- **Do not gate on more honesty or target compliance.** Coherent refusal/evasion is accepted by design. Benign utility and refusal are evaluated on their own control distributions.

### Gaps
- Numerical go/no-go tolerances depend on sample size, baseline deception rate, grader noise, and user-chosen practical effect sizes; no literature-derived universal threshold is warranted.
- Whether a deception-specific mediator exists in the studied model remains an empirical question. The preservation constraints can legitimately make the feasible sparse mask set empty at a chosen utility tolerance.
