# Hand-back 58: Scoped A3 plan closure review

Agent: Codex independent reviewer. Ticket: revised A3 plan against report 52. Status: handed-back.

## What changed

Report only. The substantive design blockers in report 52 are closed in the revised plan. One small prerequisite-interface amendment remains before implementation: validate the A1 selected artifact with its completion manifest rather than its generic hash wrapper alone.

- Worktree file for orchestrator commit: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/58-a3-plan-rereview-handback.md`.
- Primary copy: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/58-a3-plan-rereview-handback.md`.

### Remaining prerequisite: use the completed A1 selection reader

Task 1 still says to consume both prepared and selected artifacts through `ladder_pipeline.read_artifact`. The current code provides the stronger `ladder_pipeline.read_selection(args, prepared)` contract and requires `selection_run_manifest.json`. The generic reader checks only the payload hash; it does not establish completed selection, raw evidence/counts, bank identity, execution provenance, source/code identity or the completion marker's link to the exact artifact file.

Smallest concrete plan amendment:

> Read the prepared payload through `read_artifact`. Read the selected artifact through `read_selection(selection_args, prepared)`, passing the frozen A1 identity and the complete selected A1 task scope. Require and preserve the digest of its standalone `selection_run_manifest.json` alongside parent artifact digests. Missing, malformed, incomplete or stale completion evidence blocks A3 preparation/scoring. Tests must reject these cases. Do not substitute A3's new commit identity for the A1 selection identity or validate only a subset of the selected task scope; select the A3 analysis subset after the complete parent validation.

This is a narrow compatibility correction, not a new scientific requirement or a request to repeat selection. It can be closed by editing that Task 1 bullet and its test checklist. No other blocker remains in this scoped review.

### Closure of the original design concerns

**Joint edge estimand.** The plan now fixes simultaneous intact-delta receiver clamping. Every clamp is built from intact/donor caches; incoming deltas are summed before each norm/projection, branches merge deterministically, duplicates fail, and unselected slices remain live. A selected chain does not recurse through changed senders, and downstream/readout clamps may block upstream effects. Those consequences are explicitly part of the estimand. Multi-receiver/chain/readout/permutation tests and single-receiver agreement cover the ambiguity raised previously. Donor endpoint recovery is confined to a complete toy graph; production requires replay and constructed receiver-tensor agreement. This closes the blocker without extending the search universe. Results remain exact-clamp selectivity rather than a recursively altered-edge circuit.

**Full-cohort mask objective.** The exact two-pass strategy now computes the global hinge derivative from a no-grad D pass, restores per-chunk CPU/CUDA RNG states and unchanged parameters for immediate chunk backpropagation, streams additive I terms, applies candidate-only regularization once, and steps the optimizer once. Gate-sample/margin assertions, retained-graph gradient/update comparison, active/inactive/kink tests and resume identity explicitly protect the estimand. Base model eval and eligible gate training modes are separated. Both D passes and validation are charged to admission. This closes the graph-retention/minibatch-hinge blocker at the plan level; actual gradient equality remains an implementation acceptance test.

**Native gate/export contract.** Eligibility forces noncandidates exactly open; only candidate head and whole-MLP gates train. Removed probability is the complement of native open probability over eligible candidates. Binary export uses the actual native eval forward, not `get_num_active()` or a probability threshold, and tests exercise the cutoff disagreement, tie, twin-donor parity and single-stream wrapper bypass. Head and whole-MLP support are preserved. These changes close the native-semantics concern.

**Scope and ancestry.** Root's prospective FAR-only constrained family and seeds 42, 1, 123 are recorded as accepted. The literal wrong-answer/transparent-control rationale is independent of A3 effects. New30 remains an SDR-origin historical reference transferred onto the same FAR rows/conventions, with no optimizer-superiority claim or closed-assay repetition. Training-convention neutral-twin assessment is secondary to opposite-designation primary assessment. The accepted direction-null fallback retains bounded edges and the mask comparison while explicitly deferring unrun neurons.

**Confirmatory family and power.** Exactly two hypotheses, FAR and SER DOM directions, receive Holm correction. Other families are descriptive/exploratory and cannot enlarge a discovery claim. The revised triplet gate, strict quantile/tie rule, failed-null counts, conditional orientation-null interpretation and canonical-pressure linkage are explicit. The power generator now defines effect/noise injection, intact-denominator resampling, cluster-linked collateral flips, asymmetric task alternatives, the paired null approximation and the exact Holm decision. It also names the limited calibration panel, its bootstrap expansion, and conditional treatment of the MMLU guard when no disjoint validation set exists. This is executable conditional sensitivity analysis with stated assumptions, not unconditional discovery power. That distinction is sufficient; no extra panel is requested.

**Geometry, interpretation and resources.** The unit-axis versus realized-energy distinction and pseudoinverse cutoff are corrected. Nuisance ablation is bounded and cannot select sites or support unique deceptive-intent representation. The resource inventory now includes calibration, nuisance panels, both D passes, validation and references. The GPU-hour ceilings remain conditional admission bounds; no new runtime promise follows from plan approval. No additional scope or stricter scientific threshold is needed to close this review.

## How verified

Read the revised plan and the current A1 selection interface directly; the author follow-up handback was not read. The exact relevant source inspections were:

```bash
sed -n '95,148p' docs/research/specificity-ladder/plan-a3.md
sed -n '405,510p' component_analysis/ladder_pipeline.py
sed -n '30,65p' component_analysis/ladder_pipeline.py
```

Observed: the plan defines the power generator and fixed-cache receiver-clamp semantics; `read_selection` requires the completion manifest and checks its identity, evidence, counts and exact-file links, while `read_artifact` checks only the payload hash. The complete revised mask and resource sections were also read. These are source observations, not model-run results.

Both report copies passed research-session lint with no diagnostics. The report-number checker exited zero and listed eight unresolved occurrences: handback identifiers 58/52, Task 1 references, and the accepted seed settings 42/1/123. Each was checked against the report filenames or revised plan. Its cited-but-not-found completion-manifest basename names the required interface artifact, not an assertion that a completed A1 artifact currently exists; the source reader defines and requires this filename. No unresolved token is a new efficacy/runtime claim.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No production implementation, plan edits, tests, GPU/model/API calls, notebook execution, jobs, git, subagents, protected-set scoring or closed-assay repetition. The A1 selection run and A3 workload fit were not audited. Plan-level closure does not assert that future acceptance tests pass.

## Open questions

- Root should make the single A1 reader/sidecar amendment before implementation. Default: adopt the quoted replacement and require missing/stale completion-manifest tests. All original substantive blockers are otherwise closed; no further scope decision is requested.
