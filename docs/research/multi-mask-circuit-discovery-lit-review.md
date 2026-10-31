# Literature check: joint multi-mask (target / opposite / shared) circuit discovery

Date: 2026-10-31. Compiled from three parallel web literature searches. arXiv
abstract pages were not reachable from the search session, so details come from
search snippets, ACL Anthology / OpenReview / conference pages and aggregator
summaries. Verify the 2026 preprints against full text before citing.

## Direct answer

No published method was found that learns, in one optimization run, a
target-behavior mask, an opposite-behavior mask, and a shared mask over a
frozen LLM. The pieces exist in separate literatures; the joint three-way
objective at the circuit level appears open.

## What exists (closest neighbours)

### Circuit discovery: separate runs, then set operations
- Merullo, Eickhoff, Pavlick. Circuit Component Reuse Across Tasks. ICLR 2024.
  https://arxiv.org/abs/2310.08744. IOI vs Colored Objects, ~78% head overlap.
- Bhaskar, Wettig, Friedman, Chen. Finding Transformer Circuits with Edge
  Pruning. NeurIPS 2024. https://arxiv.org/abs/2406.16778. CodeLlama-13B
  instruction vs in-context circuits share 62.7% of edges; shared core =
  post-hoc intersection.
- Mondorf, Wold, Plank. Circuit Compositions. ACL 2025.
  https://arxiv.org/abs/2410.01434. Mask-learned circuits for 10 string-edit
  ops, composed by union/intersection after training.
- Csordas, van Steenkiste, Schmidhuber. Are Neural Nets Modular? ICLR 2021.
  https://arxiv.org/abs/2010.02066. Per-subtask weight masks; shared vs
  exclusive measured post hoc. Sharing mostly at input/output layers.
- Lepori, Serre, Pavlick. Break It Down. NeurIPS 2023.
  https://arxiv.org/abs/2301.10884. One mask per subroutine; ablation should
  break that subroutine only.

### Several circuits from one pipeline, but not jointly optimized
- Rai, Geva, Yao. Data-driven Circuit Discovery (DCD). arXiv 2605.09129.
  Shows a single mask on a 50/50 task mix finds one circuit faithful to both
  (mechanisms get merged). Clusters inputs first, then one circuit per cluster.
- All Circuits Lead to Rome. arXiv 2605.12671. Overlap-aware repulsion penalty
  applied across successive runs (pushes circuits apart, no shared mask).
  Notes Lagrangian sparsity constraints make overlap penalties awkward.

### Three-way shared / A-only / B-only split, but over features not masks
- Dedicated Feature Crosscoders. arXiv 2602.11729 (plus Anthropic crosscoder
  model diffing). Dictionary partitioned by design into A-only, B-only, shared
  features, for model diffing.

### Contrastive single-mask objectives
- Bayazit et al. Discovering Knowledge-Critical Subnetworks. EMNLP 2024.
  https://arxiv.org/abs/2310.03084. One mask on frozen GPT-2 with suppression
  KL (target), maintenance KL (control knowledge + LM), density penalty.
- Wei et al. Assessing the Brittleness of Safety Alignment. ICML 2024.
  https://arxiv.org/abs/2402.05162. Safety-specific = top-k(safety) minus
  top-k(utility) via set difference + ActSVD; ~3% of params.
- Pochinkov, Schoots. Machine unlearning via selective pruning. arXiv 2403.01267.
  Neurons scored by target importance relative to general importance.

### Adjacent: joint multi-mask learning over one frozen network
- Chattopadhyay, Balaji, Hoffman. DMG. ECCV 2020.
  https://arxiv.org/abs/2008.12839. One mask per domain learned jointly with an
  overlap penalty.
- Santos et al. Budget-Aware Pruning. arXiv 2309.11464. Joint domain masks with
  an intersection loss (elementwise product, rewards sharing) and a
  differentiable union loss (budget cap).
- Serra et al. HAT. ICML 2018. https://arxiv.org/abs/1801.01423. Sequential
  per-task masks with asymmetric penalty weighted by (1 - cumulative mask).
- Wang et al. TALL-masks / Consensus Merging. ICML 2024.
  https://arxiv.org/abs/2405.07813. Weights chosen by >=2 task masks are
  "consensus" (shared), by one are "selfish" (specific). Post hoc.
- Zhang, van de Meent, Wallace. Disentangling Representations of Text by
  Masking Transformers. EMNLP 2021. https://arxiv.org/abs/2104.07155. One mask
  per attribute over frozen BERT.
- Lu et al. Twin-Merging. NeurIPS 2024. https://arxiv.org/abs/2406.15479.
  Shared expert + exclusive = expert minus shared, in delta space.
- Wortsman et al. Supermasks in Superposition. NeurIPS 2020.
  https://arxiv.org/abs/2006.14769. Many task masks over one frozen net.
- Panigrahi et al. Task-Specific Skill Localization. ICML 2023.
  https://arxiv.org/abs/2302.06600. ~0.01% grafted params recover >95%;
  task regions nearly disjoint, overlap tracks task similarity.

### Deception / honesty localization specifically
- Campbell, Ren, Guo. Localizing Lying in Llama. 2023.
  https://arxiv.org/abs/2311.15131. 46 heads (<1%) in Llama-2-70B flip lying to
  honest. One-sided; no shared/specific partition.
- Huan et al. Can LLMs Lie? 2025. https://arxiv.org/abs/2509.03518. ~12/1024
  heads; steering layers 10-15 raises honesty 20% -> 60%. Calls circuits
  "dedicated" but does not test against honesty circuits.
- Pandey. The Shared Sycophancy-Lying Circuit. ICML 2026.
  https://arxiv.org/abs/2604.19117. Same heads drive sycophancy, factual lying,
  instructed lying (edge effects r > 0.97, up to 87% top-K heads shared).
  Ablation changes deference, not factual accuracy. Strongest evidence that
  deception heavily reuses general machinery.
- Long et al. When Truthful Representations Flip. EMNLP 2025.
  https://arxiv.org/abs/2507.22149. SAE "honesty subspace"; deceptive
  instructions shift early-mid layers.
- Chen, Wang et al. Finding Safety Neurons. NeurIPS 2025.
  https://arxiv.org/abs/2406.14144. Safety and helpfulness neurons overlap
  heavily but with different activation patterns (alignment tax).
- Zhao et al. LLMs Encode Harmfulness and Refusal Separately. NeurIPS 2025.
  https://arxiv.org/abs/2507.11878.
- Vennemeyer et al. Sycophancy Is Not One Thing. 2025.
  https://arxiv.org/abs/2509.21305. Sycophantic vs genuine agreement share an
  early direction (cos ~0.99), diverge later.
- Goldowsky-Dill et al. Detecting Strategic Deception Using Linear Probes.
  ICML 2025. https://arxiv.org/abs/2502.03407. Detection only, no ablation.
- Makou et al. Many Circuits, One Mechanism. 2026.
  https://arxiv.org/abs/2606.06267. Shared core recovers >=99% of performance;
  "condition-specific" edges transfer to other conditions ("phantom
  specialization"). Warning for any specific-mask claim.

## Design mechanisms worth borrowing

- Partition by construction: per component, a 4-way hard-concrete / Gumbel
  softmax over {off, D, H, S}; m_D = z_D + z_S, m_H = z_H + z_S. Disjointness
  and shared-subset-of-both hold exactly, no penalty needed.
- Soft alternative: three independent hard-concrete masks d, h, s with penalty
  lambda * sum(d*h + d*s + h*s) (Budget-Aware intersection term, sign flipped;
  DMG overlap penalty).
- Sharing pressure so everything is not dumped into D/H: Budget-Aware
  intersection reward, or TAPS-style L1 on the specific parts.
- Functional objectives (Bayazit-style KL terms):
  keep s+d reproduces deceptive behavior; keep s+h reproduces honest behavior;
  ablate d hurts deception only; ablate h hurts honesty only; ablate s hurts
  both; maintenance KL on general text throughout.
- Representation orthogonality between shared and specific activations
  (Domain Separation Networks, https://arxiv.org/abs/1608.06019).
- Baselines to beat: separate runs + AND/XOR (TALL/Consensus), Wei et al. set
  difference, DiSparse unanimity (https://arxiv.org/abs/2206.04662).

## Gaps / risks

1. No joint objective for shared + specific circuit masks exists. Open.
2. Identifiability: separately found circuits are seed-unstable and "specific"
   edges often transfer (Makou et al.; arXiv 2607.18921). Need multi-seed
   stability and cross-condition ablation tests, or specific masks may be
   phantoms.
3. Prior deception evidence (Pandey; Chen et al.) predicts the shared mask will
   dominate and the deception-specific mask will be small, possibly mostly a
   different use of the same heads rather than different heads. Node masks may
   not resolve this; edge or activation-direction masks might.
4. DCD shows one mask on mixed data merges mechanisms. A target/opposite/shared
   design addresses this directly, which is a selling point.
