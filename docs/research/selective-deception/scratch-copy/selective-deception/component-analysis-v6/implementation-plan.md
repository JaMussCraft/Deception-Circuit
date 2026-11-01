# V6 component-analysis implementation plan

> For agentic workers: use subagent-driven-development or executing-plans task by task. Ownership below is exclusive; do not revert other workers. Root alone commits and launches.

Goal: produce a frozen matched-control panel, a validated readout-head intervention runner, and a bounded GPU pilot before selecting targeted paths.
Architecture: two new small component_analysis modules consume existing frozen JSON/dataset artifacts and existing HF/nnsight hooks. No changes to old study sources, core model code or the six-coarse-circuit project. A manifest boundary separates CPU data preparation from GPU execution.
Tech stack: Python, existing torch/nnsight/transformers, existing mgnp and base environments; no installs.
Spec: .scratch/selective-deception/component-analysis-v6/spec.md (read before work).

Global constraints: base c24b5d9; no notebook execution, pretrained model on login, API calls, automatic jobs or worker git mutations. Only root can reserve/submit within remaining2.9 GPU-hours. Do not call previously exposed data untouched test data. Distinguish conditional release from cached-clean rescue and first-token routing from free-generation behavior.

## Review focus
- Last nonpad indices must be computed independently for recipient/donor; padding changes must not alter intervention meaning.
- Opposite-answer target I must use requested-label correctness, not be scored as real-world deception.
- Scenario split and donor exclusions must remain intact; no post-effect eligibility/refill.
- Frozen mask support must be heads only, correct shape, exact New30/New23 difference and original random comparator.
- Actual runner backend identity and full-vocabulary scoring must be tested; eager attention drift is a separate check.

## Task1: CPU frozen panel (manifest worker)
Files: new component_analysis/selective_v6_manifest.py and tests/test_selective_v6_manifest.py only; study outputs panel.candidate.json and manifest-preparation.md only.
Interface: `build_manifest(...) -> dict` and CLI `python -m component_analysis.selective_v6_manifest --output PATH` with explicit source path options. Schema1 contains `sources` path→sha256, `masks` name→list of[layer,head], `added_heads`, `cases` and provenance/exposure/selection metadata. Each case is one scenario/variant with stablecaseid, scenario_key, family, split, variant, recipient token IDs, donor token IDs, requested target ID, alternate answer ID, truthful ID, and original ID/donor provenance. Preserve prompt text when available. Finalize fieldnames with runtime worker BEFORE implementing, no unilateralinterfacechanges.
- [ ] Test deterministic balanced scenario-disjoint selection; exact joins, missing/duplicate source IDs and label mismatch rejection; sourcehash binding; mask subset/difference; per-variant identical donor; exposed-data metadata.
- [ ] Implement minimal safe JSON/CSV/dataframe readers; no unrestricted pickle loading. Build candidate32 SDR+16FAR (see spec) without new outcomes.
- [ ] Run tests and CPU build; report actual cell counts, exclusions and token/label alignment. Root freezes after independent review.

## Task2: causal pilot runner (runtime worker)
Files: new component_analysis/selective_v6.py and tests/test_selective_v6.py only. Read existing component_analysis/hooks.py/path_patching.py; don't modify those or manifestworkerfiles. Study outputs runtime-preparation.md and launch.template.sbatch allowed. No real pretrainedmodel run byworker.
Interface: CLI consumes --manifest PATH --output-dir PATH --mode dry-run|smoke|discovery|validation; dry-run does not load pretrainedmodel or callAPI. Artifact header binds manifest/source/backend; JSONL rows identify scenario/variant/condition/head/donor/metrics and controls. Add source/budget execution receipt checks before live GPU work, coordinatedroot.
- [ ] Read/run focused existing pure/toy baseline tests, preserving known failures.
- [ ] Test final-nonpad replacement, unchangedotherpositions/heads, donor-row independence, exact conditioncounts/release semantics, metric signs/probability/KL and no-op identity with small random toy model ifneeded.
- [ ] Implement fixed42conditions (intact+4whole+30single+7release) for SDR discovery; whole5 only on SDRvalidation and FAR. Do not acquire validation candidate-head effects until root freezes candidate receipt. Capture clean/donor head banks once perbatch with existing hooks; no all-position borrowing.
- [ ] Smoke mode includes actualbackend baseline/noop and self-activation identity controls, selectedhead-write isolation, finite metrics, 4balanced SDR discovery scenarios×4variants and representative whole/single/release conditions. Report measuredtime/memory and untouchedvalidationproof.
- [ ] Optional attention extraction only after causalrunner stable, samebackend/eagerdrift proof; no wholegrid. Targeted path runner is a later bounded task after discovery, not silently included now.
- [ ] CPU tests both environments where supported; actual CLI dryrun; report command/outputcost estimate. Root independent review then15min H200smoke.

## Task3: root integration and independent review
- [ ] Astra scientific review198; independent code/data review ofTasks1/2; fix blockers beforeGPU.
- [ ] Root sourcefreeze and reviewed receipt, reserve≤0.25h, actualwrapperCPUdryrun, scheduler test-only, submit once.
- [ ] Audit smoke, decide measureddiscoveryreservation≤1h; commit byexplicitfilelist only.
- [ ] Run discovery+whole-maskcontrols; independent causalinterpretation; freeze≤3paths/candidates for validation, with explicitalternativehypotheses.
- [ ] Reserve further≤0.75h onlyafter measuredtiming; retain contingency. Request largerbudget with concreteproposal ifneeded. Save concise sharedreport and exact resumestate.
