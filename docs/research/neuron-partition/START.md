# Deception-specific, honest-specific and shared MLP neurons

Starting prompt for direction `neuron-partition`. Written Tue 3 Nov 2026 by synthesis session claude-3f6d6db2.
Approved by the user on Tue 3 Nov 2026 with three amendments: neutral-twin interchange at neuron level as a supported
ablation option, Bridges-2 as the first-choice cluster, and the usage cap on the all-models weekly reading. Follow
`docs/agents/research-session.md` in the Alignment repository.

1. **Goal.** Which MLP neurons of Llama-3.1-8B-Instruct matter only for instructed deception, which only for the
   honest answer, and which for both, when deception is contrasted with its neutral twin and with a transparent
   inversion control; and does deception bypass the honest-answer neurons or suppress them.

2. **Directions.** Three directions, deliberately open about method. The controls, the ablation reference, the id
   policy and the nulls in item 10 are frozen; the ranking method and layer scope are the session's to choose, with
   attribution-then-ablate as the default.
   - **N1. The causal neuron map and the partition.** Score every MLP hidden neuron (32 layers by 14,336, the
     down-projection input after the SwiGLU gate) for its causal effect on the readout under three conditions:
     D against its neutral twin H, and the user-turn transparent inversion I against its user-neutral twin. The
     default scorer is attribution patching at the readout logit difference between target and distractor, at the
     readout position and at the pressure or request clause positions; activation-contrast ranking is the comparison.
     Partition neurons into D-only, D-and-I shared, H-only and all-shared, then validate each class by set ablation
     against size-and-layer-matched random sets. Fallback: if attribution is too noisy to rank (the AtP false-negative
     problem), rank by activation contrast and cut by ablation on a top-k ladder; if the user-turn I pool cannot be
     read, use the merged operator-turn `*_v2_inversion` pool and state the operator-instruction confound; if the
     neuron-level neutral-twin wiring is not working within the first six hours, run mean and zero ablation first and
     add the twin interchange when it is ready.
   - **N2. Honest bypass or suppression.** Take the H-only set from N1 and ablate it under H, D and F. If H accuracy
     falls while D's deceptive rate stays, deception bypasses the honest-answer neurons; if D's deceptive rate also
     moves, the neurons are shared answer machinery; report which, with the F-mech-010 sign-flip result as the head-level
     reference. Fallback: restrict N2 to the late writers mlp.30 and mlp.31 and the layers where the H-only set is
     densest.
   - **N3. Stability and the attention unit (descriptive).** Split-half stability of every class by pressure
     cluster, with a same-condition split-half ceiling and the IOI floor. Heads, not attention neurons, are the
     attention unit; if time allows, a single rotation test (rotate V and the head's slice of W_O by a random
     orthogonal matrix and recount) on the September "2,508 shared attention neurons" claim, recorded as descriptive.
     Fallback: drop the rotation test; stability is mandatory.

3. **Why it is promising.** No FINDINGS row has intervened below the head or MLP block, and the only sub-head claim
   (the 3,894-leaf shared core with honest-only neurons inside 50 of 51 shared heads) is descriptive and may be a
   basis artifact. No published paper tests whether deception has dedicated MLP neurons against a matched
   non-deceptive control; the neuron sets that exist (Truth Neurons, H-Neurons, safety neurons) were picked by
   truthfulness or safety contrasts and turned out shared where overlap was measured. At head level this project's
   D-leaning set was cue-routing machinery (F-comp-001, F-mech-005, F-rte-008). A neuron set that passes the ladder
   rule would be the project's first deception-specific unit; a null closes the "maybe it is below the head" reading
   of those rows outside the Codex A3 cell. The user wants preliminary results for an advisor meeting within 24 hours.

4. **What exists.**
   - Findings: F-comp-001 (head-level D/H partition), F-mech-001/002/004/005/010 (deciding sets, clause readers, shared
     core, sign flips), F-rte-001/004/008 (mlp.13 lean, instruction-confounded probe, sycophancy non-specific),
     F-dd-001 to 009 (divergence nulls), specificity-ladder F1 and F2 (user-turn I pools; deciding sets fail the ladder
     rule), all in `docs/research/FINDINGS.md` and `docs/research/specificity-ladder/README.md`.
   - Code: leaf gates in `models/llama_node.py` (`mlp_hidden` is the neuron unit); finest-complement knockout with
     layer-matched random nulls in `evaluate_circuit.py --evals knockout --n-random`; mean ablation
     (`--ablation mean --mean-source ... --variant-mean-bank no_pressure`) and zero ablation in `evaluation/ablation.py`;
     mask schema and `heads_to_leaf_masks` in `evaluation/masks.py` and `evaluation/frozen_head_masks.py`; nnsight
     capture in `component_analysis/hooks.py` (no down-projection-input site yet; torch-hook precedent at
     `scripts/d2_premise.py` near line 596); the `neutral_twin` counterfactual in `component_analysis/knockout.py`
     near line 87 (pressure only in the clean run, the twin's activation patched in) for heads and MLP blocks, whose
     group loader accepts only the kinds head and mlp, so the neuron kind is a wiring job on that path; CPU probe utilities in `component_analysis/probe.py`; id filters in
     `component_analysis/sampling.py`; provenance in `run_manifest.py`; the capture-plus-fit pattern in
     `scripts/falsity_probe_capture.py`, `scripts/falsity_probe.py` and `scripts/jobs/run_b2_capture.sbatch`.
   - Data: `data/datasets/{far,ser}_v2` (D), `_honest` (H twin), `_nopressure` (F), `_inversion` (operator-turn I,
     test only, 210 and 249 rows). The user-turn I and user-neutral pools exist only as HF dataset dicts under the
     Codex worktree, `.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a1-control-77b6487-m07/
     {far,ser}_v2_user_{inversion,neutral}/` (FAR 177/177/891 rows). Read them only; record path and sha256 in the
     manifest and note that they are unmerged.
   - Held-out: `docs/research/held_out.json` is empty; the working held-out samples are
     `docs/research/mechanism-analysis/phase1/groups/<task>_heldout_{D,I}_sample.json` (n=100, seed 1). The ladder's 100
     assessment ids per task are in its worktree under `a1-full-77b6487-a100`.
   - Start from Deception-Circuit `main`, worktree `.claude/worktrees/neuron-partition`, branch `neuron-partition`.

5. **Do not redo.**
   - The head-level D/H partition (F-comp-001) and the head-level cross-task difference tests (F-mech-005, F-mech-008).
   - The layer-17 residual probe (F-rte-004) and any residual-stream direction; closed as instruction-confounded.
   - Interchange with the item-swap corrupt prompt as the ablation reference for neurons: the pressure clause stays in
     both streams, so it is a near no-op by construction (repo note, 2026-11-03).
   - SAE or transcoder features: three studies find SAE probes do not beat dense probes, labeled deception features
     did not stop lying when steered, and the public Llama-3.1-8B SAEs are base-model only.
   - Top-activating neuron lists without ablation, raw Jaccard without a ceiling and floor, thresholds tuned on the
     evaluation ids.

6. **Do not touch.** SESSIONS.md on Tue 3 Nov 2026, 1:12 am EST lists one claimed direction: `specificity-ladder`,
   session codex-01a1987e, running, do-not-touch "nothing listed". Rules for this session anyway:
   - Never read or import code from `.claude/worktrees/specificity-ladder/`; never write there; never touch Slurm jobs
     23472894 and 23474289 or any later job of that session.
   - The Codex A3 neuron cell belongs to that session: down-projection-input neurons at MLP layers 5 to 8 and 11 (plus
     13 and 16 on SER), readout position only, ranked by the D-minus-I gap over the H standard deviation, top 1 percent
     per layer, range-patch interchange with the opposite-designation donor, selected on A1's 100 assessment ids. This
     session records no verdict in that cell. If an all-layer set happens to pass the ladder rule, record it as a
     descriptive lead that A3 confirms with its own pre-registered design.
   - Do not use A1's 100 assessment ids or the mechanism-analysis held-out samples for ranking or ablation.
   - Paused directions (sdr-mechanism, selective-deception, mechanism-datasets, deception-divergence) stay paused.

7. **Budgets.** GPU: 20 reserved GPU-hours across Bridges-2 and Delta, at most 3 concurrent GPU jobs; expected 5 to 8.
   Bridges-2 first (allocations cis260361p and cis260372p, H100 80 GB, `--export=ALL,DC_CLUSTER=bridges2`,
   `--gpus-per-node=h100-80:1`; it has started jobs far sooner than Delta recently and goes offline about 2026-11-09;
   copy outputs and job logs back under the primary checkout on Delta at wrap-up). Delta interactive partitions (about a
   minute to start, one-hour cap) for pilots and dry-runs; Delta batch GPU queues last. Gradients and 8B activations do
   not fit on 40 GB A100s: use H100, H200 or A40. OpenRouter: $0 planned (one-token readout, no judge); ask before any judge spend. Usage: pause at 80% of
   the all-models weekly reading (`seven_day`); the Fable row is not a cap (user decision 2026-11-03). Reserve walltime
   at the observed runtime plus a reasonable buffer; record reserved and actual hours in the ledger.

8. **Oversight.** Review checkpoint every 24 session points of weekly usage (the user sets this cadence in the new
   session with the research-session cadence command; the default is 16). A checkpoint is a freeze: no new agents, no
   new Slurm jobs and no messages to workers except HOLD until the user replies "continue". Stall alarm at 60 minutes
   without progress. Milestone trigger: any direction that passes or fails its pre-registered gate gets a worklog
   entry, and a checkpoint if it changes the plan. Hand back a first report with whatever N1 has produced by
   Wed 4 Nov 2026, 12:00 pm EST, even if incomplete, so the user can present it.

9. **Always ask before.** Merging to main, any EVAL 5 run (the full five-suite benchmark evaluation), any OpenRouter
   judge spend, dropping a direction, raising any cap, scoring any held-out or ladder assessment id, and any
   generation-based readout.

10. **Exit criteria.** Frozen before the first GPU job; changes are dated rulings in `spec.md`.
    - **Tasks.** FAR primary (act-naming clauses only), SER secondary, SDR out.
    - **Ids.** Rank on the train and validation splits; ablate on a fresh test sample of at least 300 rows per
      condition drawn with seed 2, excluding A1's 100 assessment ids and the mechanism-analysis held-out samples;
      record `dataset_files` in `run_manifest.json`.
    - **Ablation.** Three references. (1) Neutral-twin interchange at neuron level, the primary: for each instance the
      chosen neurons' activations in the D run are replaced by their values from the H-twin run of the same instance
      (and in the I run by the user-neutral twin's), extending the `neutral_twin` path of `component_analysis/knockout.py`
      to the `mlp_hidden` kind with tests on both interpreters. (2) Mean ablation from the no-pressure mean bank.
      (3) Zero ablation. Report disagreement among the three. The
      effect measures are the ladder's: the D effect is p(deceptive answer under D) minus p(deceptive answer under H),
      the I effect is the same for I against user-neutral, with the one-token readout at margin 0.7.
    - **Nulls.** At least 20 random neuron sets matched on size and per-layer count, scored on every metric
      including H, F and IOI accuracy.
    - **N1 pass (deception-specific).** A D-only set of at most 2,000 neurons removes at least 50 percent of the D
      effect, under 25 percent of the I effect, moves H, F and IOI accuracy by under 5 points each, and beats the 95th
      percentile of the matched null on D-effect removal, under neutral-twin interchange and under mean ablation, in
      both split halves. **Fail.** No set meets all of these: record a reviewed null "no deception-specific MLP neuron
      set at this granularity under the ladder rule, outside the A3 cell". Partial passes (one reference, one half)
      are recorded as leads, not passes. If the twin wiring never lands, the pass needs mean and zero instead, and the
      finding says so.
    - **N2 pass (honest bypass).** Ablating the H-only set drops H accuracy by at least 20 points while D's deceptive
      rate moves under 5 points and the matched null moves H accuracy under 5 points. **Suppression or shared.**
      D's deceptive rate also falls by at least 10 points. Anything else is "undetermined at this size".
    - **N3.** Report split-half Jaccard for every class against the same-condition ceiling and the IOI floor; a class is
      called stable only if its Jaccard is at least half the ceiling. The rotation test is descriptive.
    - **Done.** N1 and N2 have run on FAR with the twin interchange and mean ablation and the stability report exists;
      SER is a bonus.
      **Stop.** The 20 GPU-hour cap, or 36 wall-clock hours from launch, whichever comes first; hand back what exists.

11. **Files.** Directory `docs/research/neuron-partition/` in Deception-Circuit. `WORKLOG.md` is the human log, written
    only through `research-session worklog-append`. `RESUME.md` is the machine narrative, at most 150 lines.
    `state.json`, `worklog.json` and `ledger.json` are written only by the research-session tool. Hand-backs go to
    `reports/` with the headings of `_templates/handback.md`. Finding ids use the short name `nrn`.

12. **Registration.** Before branching, the orchestrator runs `research-session claim neuron-partition` on the main
    checkout and commits the claim. Before its first spawn it runs `research-session register neuron-partition`; only
    a registered session gets checkpoints.

13. **Models.** Orchestrator: Fable. Subagents: Opus on Claude, passed explicitly as `model: "opus"` on every spawn.
    When the Fable weekly row is more than 5 points above the all-models row, reading, analysis and review go to Opus
    agents.
