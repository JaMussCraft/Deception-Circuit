# Hand-back 52: Independent A3 prospective design review

Agent: Codex reviewer. Ticket: prospective A3 design critique. Status: handed-back.

## What changed

Report only; no production files changed. Verdict: the plan is scientifically useful and conditionally bounded, but amend the joint-edge and streaming-mask contracts before implementation. No new assay or protected-set access is requested.

- Worktree file for orchestrator commit: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/52-a3-design-review-handback.md`.
- Primary copy: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/52-a3-design-review-handback.md`.

### Blocker B1: Define the exact multi-receiver edge intervention

Task 4 correctly sums selected sender deltas before each receiver norm/projection. It does not yet define what happens when selected receivers lie at different depths and one receiver's output supplies another selected path. Independently capturing their values against intact senders and replaying absolute downstream receiver values can erase effects induced at upstream selected receivers. This is a defined intervention once specified, but is not automatically the recursive circuit obtained by changing those edges.

Smallest fix: choose and name one estimand before coding. A bounded option is a simultaneous frozen-delta receiver intervention: cache intact and donor sender contributions; for each receiver compute its intact incoming residual plus the sum of selected donor-minus-intact contributions, transform the chosen branch, and replay those explicitly fixed receiver values on one recipient forward. Document that downstream selected receiver clamps can block upstream consequences. Alternatively implement a recursive edge graph, with live sender contributions and explicit reference values on excluded edges; that is materially more work. Do not call these two constructions equivalent.

Tests must include two incoming edges to one receiver, two receiver depths with a selected chain, a selected readout plus an upstream receiver, shared GQA branches, edge-list permutation invariance, identity deltas, and comparison with the existing single-receiver path patch. Report joint measured effects, never sums of single-edge effects.

The proposed all-node endpoint recovery cannot mean whole-model recovery to the neutral prompt inside the deciding-set/quartet universe: omitted nodes, embeddings, unsupported positions and prompt edits prevent that claim. Restrict donor endpoint recovery to a complete toy graph with all required sources, or expand only the diagnostic graph explicitly. For production require intact replay and recovery of the explicitly constructed receiver tensors; do not demand an impossible global endpoint.

### Blocker B2: Make the full-cohort mask hinge streamable and reproducible

The baseline-adjusted threshold is correct: suppression hinge is `relu(mu_D_patched - (mu_D_intact - 0.5*G_D_fit))`. Task 5's examples correctly preserve the honest offset. Count-weighted accumulation alone cannot evaluate this hinge's derivative before the full mean is known. Retaining every cohort graph defeats the proposed memory bound; per-minibatch hinges change the objective.

Smallest exact strategy per optimizer update:

1. Hold parameters fixed. Run D chunks without autograd, recording weighted patched margins and the gate RNG state/sample for every chunk. Compute the full-cohort hinge argument and its detached derivative indicator, using the chosen zero subgradient at the kink.
2. Replay each D chunk with autograd and the identical gate sample, chunk order, dropout state and numerical path. Backpropagate `indicator * weighted_D_margin` immediately and discard its graph. Stream the additive I preservation/KL terms with their full-cohort weights; they need no global hinge replay. Accumulate the removal regularizer once per update.
3. Take exactly one optimizer step after all contributions; checkpoint RNG and optimizer state. Compare gradients and one update against a tiny all-at-once reference, including active/inactive/kink hinges and unequal final chunks.

`l0.py` samples new hard-concrete noise on each training forward. A fresh second-pass draw gives the wrong gradient for the first pass's objective. Common gate samples across chunks are also acceptable, but freeze that choice. Model evaluation mode and gate training mode must be set independently: eval-mode gates are hard thresholds with no useful training derivative. The pilot must charge both D passes, I backward, validation and checkpoints.

### Blocker B3: Freeze root scope and native gate/export semantics

The accepted null fallback is internally coherent: report direction null and conditional power, run bounded edges, defer unrun neurons explicitly, retain the mask/reference comparison. No user reapproval is needed for that already accepted interpretation. The FAR-only constrained family remains a root proposal, not a resolved START commitment. Its literal wrong-answer semantics justify it prospectively; record the choice before new efficacy results. If root instead chooses more task families, rebuild the entire cost inventory before implementation/reservation.

Reuse native gate eligibility to force every noncandidate contribution exactly retained. Train only candidate gate logits; keep every base weight frozen. Compute removed probability as the complement of native open probability over eligible candidates, rather than reusing native keep-density regularization with its original sign or averaging across all model nodes. Export removals from the actual deterministic binary gate forward; do not infer them from `get_num_active()`, whose probability cutoff differs from the eval binary forward in `l0.py`. Require exact masked-forward/export parity and all-retained/all-candidate-removed controls. Head and MLP removals must both survive export.

### Refinements: scientific interpretation and inference

**Identifiability.** The paired D-minus-I contrast still mixes deception with role, framing, length and absolute position. The proposed nuisance table/probes and neutral-frame direction are useful diagnostics, but cosine and steering do not remove the confound. A passing intervention supports D selectivity under these controls, not unique representation of deceptive intent. Small addition: assess the already proposed neutral-frame nuisance direction under the same primary ablation at the selected site, with its status and cost frozen in advance. A nuisance direction also passing the gate makes the semantic ambiguity especially clear. No diagnostic licenses rebuilding pools or changing thresholds.

**Isolation.** Train fitting, validation selection and immutable A1 assessment are cleanly separated; historical selection exclusions, utility prompt-level overlap checks and actual protected IDs are appropriately explicit. The operational fitting/validation minimums are not power guarantees. Preserve source pressure clusters across conditions, streams, all seeds and both task tests when resampling. State whether identical pressure wording across tasks is jointly resampled. A1 artifacts are still prerequisites; do not treat their existence as completed ladder evidence.

**Head geometry.** Using an orthonormal basis of the image of each output-projection block and pseudoinverse pullback is appropriate, including rank deficiency and orthogonal reparameterization. Normalized output axes do not yield equal realized perturbation norms: `abs(v^T W(z_donor-z))` varies by axis. Correct Task 2's phrase implying identical intervention norm; report recipient-level norms and fit-only projection variance alongside the null. Equal axis norms are sufficient for the stated isotropic-orientation benchmark, but do not describe it as energy matching. Handle numerical effective rank and pseudoinverse tolerance consistently.

**Pooled seed/null statistic.** The frozen triplet statistic, every-seed gate requirement, paired bootstrap and task Holm adjustment avoid selecting a lucky seed or site on assessment. Three bootstrap fits are robustness checks, not independent replication. Negative-infinity failed nulls are coherent for the constrained statistic, but report their count and unconstrained effects so a passing rank cannot hide a weak null. The random-direction rank probability is conditional on the frozen trained/selected pipeline and isotropic orientation benchmark; it is not a label-permutation test of absence of a deception mechanism. Freeze quantile interpolation and tie rules.

**Multiplicity and power.** Before opening assessment, list the exact family of confirmatory hypotheses and alpha allocation, including whether neuron continuation is a prespecified gatekeeping procedure or part of one correction family. Merely promising a future union correction is insufficient for a final 'some family passed' claim. Direction task correction is otherwise sensible. The edge null panel has minimum attainable rank probability `1/20`, so it cannot support a two-task Holm-confirmatory rejection at family alpha `0.05`; keeping edges exploratory is the correct bounded choice. This does not prevent reporting START point gates.

The proposed power simulation is not yet an executable generative specification. State exactly how D/I margin changes and collateral correctness flips are injected jointly at pressure-cluster level, what null-panel outcomes are held fixed or regenerated, and how both tasks enter Holm in each replicate. Preserve intact denominators and their weakness; report attainable power across the injected grid and a detectable effect only when bracketed. Validation-conditioned simulation cannot establish unconditional discovery power after site selection. Avoid spending a full assessment-sized null panel on every validation candidate just to simulate power; use measured/cache-based calibration and label approximation explicitly.

**Privileged neuron ranges.** Hooking the SwiGLU intermediate immediately before `down_proj` is the right privileged basis. Head-output coordinates and MLP output coordinates remain excluded. Quantiles, constant-neuron handling, recipient-interval membership, tie rules and outer bounds are adequately prospective. Record how bootstrap seeds alter neuron fitting and quantiles. Equal-cardinality neuron nulls are not equal-energy nulls; coverage/norm reporting is necessary. A direction-null stop leaves this question deferred.

**Differentiable adapter.** Native code is genuinely required: `hooks._traced_forward` enters `torch.no_grad()` and detaches captures. The new adapter must freeze weights while setting receiver residual leaves to require gradients, include the full pre-norm Jacobian for branch residual attribution, isolate Q/K/V slice writes, and restore every hook. The proposed native/inference parity, VJP finite differences and causal toy checks are meaningful. Gradient interpolation is a local incoming-residual path, not necessarily a realizable whole-prompt interpolation; describe it as the proposed EAP-IG-style ranking until its algorithm and tests establish the intended contract. Attribution is not edge necessity. Eight-versus-sixteen-node agreement is an operational stability diagnostic, not proof of accuracy.

**Mask objective and assessment donor.** The I hinge/KL objective encourages preservation but does not guarantee the A1 I or collateral gates; binary validation/assessment must decide those. Training removes against each condition's neutral twin, whereas the declared primary A1 assessment uses its opposite-designation donor. This is permissible as a generalization test, but report the donor shift explicitly and retain the trained neutral-twin assessment as a secondary diagnostic. A failed primary cannot be replaced by a successful training-convention result. Apply identical assessment conventions to every comparison arm.

**New30 fairness.** The actual archived receipt states `SDR_WikiText_validation_only`; the exported file explicitly contains `removed_heads`. FAR training is therefore a new semantically justified test, with New30 a transferred historical reference. Same FAR rows and same intervention convention support descriptive behavior/node-count comparisons, not optimizer superiority or a matched training comparison. SER/SDR unchanged transfer is useful. The receipt/head list can be read without reopening closed assays or deserializing protected checkpoints. Three constrained and three unconstrained seeds supply the causal comparison for the new preservation penalties.

**Budget.** The phase ceilings add to the approved `40` GPU-hours, including the proposed contingency. They are admission limits, not evidence that the workload fits. Directions alone include `3 * 199` null interventions per task, each with its complete collateral panel; exact edges and six full-cohort mask runs add substantial work. Require the explicit cell inventory and same-hardware full-shape timing before admission. Reuse identical three-seed null/control interventions and intact caches where their complete keys match, while preserving indices in the report. Count two-pass mask work, every validation candidate/checkpoint, gradient-node refinement, startup, failed pilots and retries. Runtime cannot be inferred from inference speed or the failed A2 pilot. If any mandatory milestone cannot fit after exact sharding/streaming, report blocked or unexecuted and request the applicable scope decision; do not imply A3 completion.

## How verified

Read-only source inspection covered START, spec, A3/A2/ladder plans; native capture/replacement/readout and path-patching seams; native Llama head/MLP/block gates; hard-concrete sampling/eligibility/export behavior; A1 ratio-of-means metrics; and the archived New30 selection receipt and removed-head list. The author handback was not read.

The following searches identified the source contracts discussed above:

```bash
rg -n 'class HardConcreteGate' . --glob '*.py'
```

Observed: the implementation is in `l0.py`.

```bash
sed -n '374,492p' component_analysis/hooks.py
sed -n '595,710p' component_analysis/path_patching.py
```

Observed: inference capture disables gradients and detaches outputs; single-receiver path patching freezes every other component on its capture pass and replays receiver values on a clean pass. These are code observations, not model-run results.

Both required copies passed `research-session lint` with exit code zero and no diagnostics. `python scripts/check_report_numbers.py docs/research/specificity-ladder/reports/52-a3-design-review-handback.md` exited zero and listed four unresolved tokens: report identifier 52 and source-plan Task references 4, 5 and 2. Each was manually checked against the report filename or A3 task heading; none is an empirical numerical claim. Other numbers in this review are frozen START/A1/A3 proposal settings, native-source expressions, New30 archival labels, or arithmetic workload counts; none is a new efficacy/runtime measurement.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No production implementation, tests, GPU/model/API calls, notebook execution, jobs, git, subagents, protected-set scoring, or closed-assay repetition. No claim is made that the proposed workload fits its ceiling. A1 ladder completion and A2 timing were not audited. No niche literature claim or external citation is needed for this local-method review.

## Open questions

- Root decision required: adopt the FAR-only three-seed mask family or broaden it with a fresh full reservation projection. Default recommendation: adopt FAR for its prospective semantic rationale and keep transfer descriptive.
- Root decision required: choose frozen-delta simultaneous receiver clamping versus recursive edge-graph semantics. Default recommendation: use the bounded frozen-delta estimand with explicit chain limitations and complete-toy endpoint tests.
- Freeze the exact confirmatory family and power generator before assessment. Default recommendation: directions confirmatory across FAR/SER, edges exploratory, and neuron-family claims included in a prespecified overall correction or gatekeeping rule.
