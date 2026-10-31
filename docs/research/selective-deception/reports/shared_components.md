# Shared components, format controls, and behavioral necessity

## Has the shared-core-versus-exclusive necessity pattern been observed directly?

### Takeaway
Li and Subramani directly compare intersection and exclusive-set knockouts in nondeception tasks. [Paper, v3](https://arxiv.org/html/2605.08348v3)

### Cited Findings
- **Li and Subramani, “How Much Do Circuits Tell Us?”** Submitted May 8, 2026; v3 October 7, 2026. [Submission history](https://arxiv.org/abs/2605.08348)
- **Methods:** six tasks (Addition, Boolean, IOI, CopyColors, ARC Easy/Challenge); EAP-IG/RelP attribution selection, not SDR; 1,000 discovery/200 evaluation examples. §3.4 partitions A∩B, A−B, B−A; Fig.5: components, K=10%, P=100% occurrence. [§§3–5](https://arxiv.org/html/2605.08348v3#S3)
- **Result, averaged across models:** shared-core knockout gives the largest drop except Addition. A-only generally damages other tasks similarly/more; Addition loses 95% own accuracy versus 25% others. [§5, Fig.5](https://arxiv.org/html/2605.08348v3#S5)
- **Qualifications:** zero primary; Appendix E replicates main necessity/specificity findings with position-wise corrupted-input means, not interchange. §3.4 gives A-only a capacity-conserved random control. Partition sizes differ. [§3.4; Appendix E](https://arxiv.org/html/2605.08348v3#A5)
- Llama’s six-task intersection: 14 MLPs/three heads; one sink, two attending task content. [§5.1; Appendix I](https://arxiv.org/html/2605.08348v3#A9)

### Inferences
- The closest claim supported by this precedent is **“components shared with other tasks can dominate the knockout effect attributed to a behavior circuit.”** That matches the logical form of D∩F being more necessary than D−F. It does not identify the shared operation as formatting.
- The distinction between membership and mechanism matters even if the numerical result replicates: an intersection of task circuits is an operationally defined set; assigning it a computational role needs separate evidence.
- This paper supports treating the present result as an extension to deception, honest/pressure controls, heads-only SDR circuits, and donor-based interventions. Those differences should remain explicit when claiming novelty.

### Gaps
- No exact precedent located for the complete combination **deception D, honest H, no-pressure format control F, D∩H∩F knockout, and transferred reduction of deception on naturalistic out-of-task benchmarks**.
- The paper does not establish that shared components encode pure formatting. It tests broad task sharing, and its strongest component overlap includes entire MLP blocks. That limitation matters for comparison with heads-only analyses.
- Do not use v1 results interchangeably with v3: their model panels, methods, and selective-ablation conclusions differ. Current v3 is the source summarized above.

## What do earlier circuit reuse and explicit format studies actually establish?

### Takeaway
Merullo et al. provide concrete reusable copying machinery across different tasks. “Judge Circuits” gives a more direct distinction between shared semantic computation and format-specific output routing. Neither alone demonstrates the user's exact D/H/F finding.

### Cited Findings
- **Merullo, Eickhoff, and Pavlick, “Circuit Component Reuse Across Tasks in Transformer Language Models,” first posted October 12, 2023.** In GPT-2 Medium, IOI and Colored Objects share 25/32 important heads (78%). The shared heads include movers and duplicate/induction heads; copying is reused, while information-selection pathways differ. [Date](https://arxiv.org/abs/2310.08744); [§§3–4, Fig.3](https://arxiv.org/html/2310.08744v3#S4)
- They intervene on four heads identified through the IOI analysis to repair Colored Objects, raising accuracy to 93.7% from approximately 49.6–49.7%; downstream mover changes match the proposed inhibition/copying pathway. This is causal cross-task reuse, not merely overlap. It is **not** a comparison showing shared-core knockout dominates exclusive-core knockout. [§5, Fig.5](https://arxiv.org/html/2310.08744v3#S5)
- **Feldhus et al., “Judge Circuits,” first posted May 15, 2026.** They trace matched rating and classification tasks, defining the intersection as a Latent Evaluator and differences as Task Formatters. The functional claim is supported with additional causal tests, not intersection alone. [Paper date](https://arxiv.org/abs/2605.16023); [§4.1](https://arxiv.org/html/2605.16023v1#S4.SS1)
- Shared evaluator ablation disrupts judging while largely preserving factual controls in four models, with family-dependent failures in Gemma-3-12B. Llama-3.1-8B's head-only MMLU control is vacuous because its shared evaluator has no heads; its meaningful MLP controls are StrategyQA/CREAK. [§4.2, Table 1 and footnote](https://arxiv.org/html/2605.16023v1#S4.SS2)
- Cross-format activation transfer is strongly model-dependent; abstract judgment can remain steerable while wholesale transferred activation patterns fail to trigger the recipient formatter. [§5, Table 2; Appendix D](https://arxiv.org/html/2605.16023v1#S5)

### Inferences
- A head that copies whichever answer downstream selection supplies can be indispensable for both honest and deceptive outputs without itself computing an intention to deceive. Its task role can nevertheless be causally important for deception; these descriptions are compatible.
- “Judge Circuits” supplies a useful alternative interpretation of F membership: circuitry shared by two formats may perform the **semantic task**, while circuitry differing across formats performs formatting. Conversely, two conditions sharing a format can also reuse output routing. Set overlap alone cannot choose between these accounts.
- For the present study, call F a “no-pressure task control” or “format-control condition” when describing how it was constructed. Reserve “formatting mechanism” for a tested computational hypothesis.

### Gaps
- No evidence located that Merullo's shared 78% as a group was more necessary than its task-exclusive complement.
- No matched shared-versus-format-exclusive necessity ranking located in “Judge Circuits” that reproduces D∩F > D−F. It establishes a decomposition and format-transfer effects; it should be cited as a mechanistic comparison, not an exact replication.

## How should out-of-task transfer constrain the interpretation?

### Takeaway
Transfer is evidence against an effect restricted to SDR's exact prompt template. It does not, by itself, separate a transferable deception-related policy from reusable selection, instruction response, suppression, or answer-production machinery.

### Cited Findings
- Relevant cross-task evidence: own-versus-other-circuit knockout (Li and Subramani, §3.4/Fig.4), and predictable IOI→Colored Objects intervention effects (Merullo et al., §5). [Li and Subramani](https://arxiv.org/html/2605.08348v3#S5); [Merullo et al.](https://arxiv.org/html/2310.08744v3#S5)
- The project’s experiment interpretation is supplied by the assignment and shared project memory: raw deception rate is the headline, interchange is primary, coherent refusal/evasion can be successful suppression of deception, and increased honesty is not required. [Local project framing](/projects/beto/swong2/Alignment/.agents/memory/deception-eval-framing.md)

### Inferences
The following are competing explanations, not facts established by the literature:

1. **Shared semantic selection:** honest, deceptive, and no-pressure tasks all require tracking the underlying answer, available options, and instruction. A common selector or mover can therefore mediate all three conditions and remain useful outside SDR.
2. **Shared output production:** the common set supports turning a selected policy into an answer. Out-of-task transfer weakens a narrowly SDR-specific formatting explanation, but broad response routing or answer suppression can transfer across templates.
3. **Transferable behavioral control:** the components support following pressure or selecting deception versus refusal across contexts. A real reduction in raw deception with coherent refusal is evidence of useful causal control even if it does not produce honest answers.
4. **Donor-dependent overwrite:** interchange changes values, not merely node availability. Honest-pool donors can install different task/policy/content states into a shared component; a large effect need not mean removal of deception-specific information. This alternative remains possible even when the donor and recipient are individually on-manifold.
5. **Granularity and context:** a shared head can carry different information at different positions or in different residual subspaces. Whole-head membership can merge a shared primitive with behavior-selective computations. D−F can also be less necessary because of redundant routes or discovery omissions, rather than because it lacks behavior-relevant computations.
6. **Broad disruption:** coherent refusal/evasion should count as success, as requested. Output collapse or unrelated incoherence is a different causal explanation; it should be assessed separately rather than redefining refusal as failure or conditioning deception on parsed answers.

These alternatives suggest a precise evidential ladder: current knockouts can establish a **transferable intervention effect**; control membership establishes **sharing across conditions**; a claim about **the shared computation's identity** requires discriminating the alternatives. Useful distinctions include transfer across output vocabularies/templates, content-preserving versus policy-preserving donor contrasts, matched-set controls, and localized path/subspace analyses. These are interpretive implications, not a request to run new experiments in this research task.

### Gaps
- The literature located does not decide which explanation fits the user's eval5 behavior; that requires the actual intervention definitions, donor distributions, responses, controls, and uncertainty estimates.
- Transfer to eval5 is stronger than “this only formats SDR,” but insufficient for “this specifically computes deception” or “this is merely format machinery.” Neither extreme follows from overlap plus transfer alone.
