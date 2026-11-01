# Specificity ladder, pressure-mediating circuits and below-the-head specificity

Starting prompt for direction `specificity-ladder`. Written Sun 1 Nov 2026 by synthesis session claude-0ab0a0b3.
Approved by the user on Sun 1 Nov 2026. Follow `docs/agents/research-session.md` in the Alignment repository.
This is the heavier of the two approved sessions and is meant for a Codex orchestrator.

1. **Goal.** Build a specificity test that can fail, then use it to ask whether any component, direction or
   feature of Llama-3.1-8B-Instruct is necessary for pressured deception and not for a transparent inversion in
   which nobody is misled.

   The yardstick for the whole session: a part of the model is deception-specific when it is necessary in D (the
   pressure clause), not necessary under a user-turn transparent inversion, not necessary in H or F, and inert on an
   unrelated task. The earlier null (F-mech-003, F-mech-005) used an I control in which both D and I were hidden
   operator instructions with the same user turn, so the user was misled in both and the test could not fail.

2. **Directions.** Three directions, deliberately open about method. A3 starts only after A1 delivers the control.
   - **A1. The control and the ladder.** Build a user-turn transparent inversion condition (the user asks, for
     example, "Quiz me: tell me the wrong one") on FAR, SDR and SER, filter it with the same margin rule as I
     (target wins by at least 0.7 in both streams), and rebuild pools above 300 ids on FAR and SER. Then score the
     ladder unrelated task (IOI, GP or GT from `tasks/`) / H / F / user-turn I / D with a positive control (a
     component set known to carry the answer) and an MMLU floor at a small fixed n. Run the collateral question
     (why clause-reader knockout harms honest accuracy) as the ladder baseline with a crossed design: ablation
     type (zero, mean over H, same-item resample from H, item swap) by set (full deciding set, set minus the answer
     movers). Fallback: if the user-turn pool stays under 300 ids at margin 0.7, lower the margin to 0.5 and
     record it; if still under 300, build a response-turn transparent control instead and report both pool sizes.
   - **A2. Pressure-mediating circuits from a twin corruption.** Train masks whose corruption swaps the pressure
     clause for its neutral-clause twin with items and question fixed, and matched masks for the user-turn I
     versus its twin, 3 seeds each, heads plus MLP. Pre-register the MLP prediction: MLPs 5 to 8 and 11 for
     clause reading on FAR and SER, and 11, 13 and 16 on SER alone. Pre-register that "the D mask sits inside the
     I mask" is a result worth reporting, not a failure. Run a timing dry-run of one mask before reserving the
     phase. Fallback: if a single 8B mask exceeds 6 GPU-hours, train heads-only masks and defer the MLP prediction
     to the A3 neuron work.
   - **A3. Below the head.** Build the probe, direction and feature harness the repository lacks. Fit difference-
     of-means directions for D minus user-turn I inside L17H24 to L17H27 and the clause readers; ablate them on
     held-out ids over 3 seeds against a random-direction null and a steering baseline. Apply range-restricted
     ablation to MLP neurons only, where the basis is privileged, not to head-output coordinates. Test whether the
     shared nodes carry condition-specific edges with position-aware edge attribution (PEAP or EAP-IG) on the
     deciding set and the quartet, with a cross-condition transfer test, without edge-pruning training. Replace
     the New30 re-analysis with one twin-trained mask that is necessary for D and constrained to preserve I.
     Fallback: if no direction beats the null, report the null with its power and stop at the edge test.

3. **Why it is promising.** No published deception circuit uses a transparent control, and the current
   corruption edits only the designation site, which is why 13 of 18 FAR and 11 of 19 SER deciding heads lie
   outside the trained masks (F-mech-013). Li and Subramani (arXiv 2605.08348) put specificity, if it exists, at
   neuron level (a gap of 27 to 29 points against 0.7 at head level). The descriptive within-head split (50 of 51
   shared heads hold honest-only neurons) may be a basis artifact, and directions test the same idea properly. A
   positive result names deception-specific machinery; a clean negative under a control that can fail is the
   methods paper the October 28 survey recommended.

4. **What exists.**
   - Findings: F-mech-001 to F-mech-013 (mediating sets, clause readers, the confounded inversion contrast, the
     shared core as answer machinery), F-mds-002 and F-mds-003 (coarse v2 circuits and exclusive heads),
     F-fmt-003 (overlaps are the necessary parts), F-sel-006 and F-sel-007 (L17H27 and New30 are not selective).
   - Synthesis and limitations: `docs/research/mechanism-analysis/synthesis.md`, sections 5 (L1 to L25) and 6.
   - Survey and recommendation: Alignment `.claude/worktrees/survey-deception-circuits/project_context/surveys/
     deception_circuits/` (`recommendation.md`, `intervention_bar.md`, `novelty_assessment.md`).
   - Critic reviews behind this prompt: Alignment `.scratch/synthesis-20261101/review-B.md` (A2), `review-C.md`
     (A3), `review-D.md` section M8 (the collateral baseline), and `merged-scored.md`.
   - Data: `data/datasets/{far,sdr,ser}_v2` with `_honest`, `_nopressure`, `_inversion` twins; splits 200/200/1000;
     I pools 210 (FAR), 788 (SDR), 249 (SER). Instance ids are shared across twins.
   - Code: `train.py` (node pruning, heads plus MLP; `--edge-pruning` exists but has not run on 8B v2),
     `evaluation/ablation.py` (interchange, zero, mean), `component_analysis/knockout.py`,
     `component_analysis/path_patching.py` (not position-resolved), `component_analysis/dla.py`,
     `train_selective_mask.py`, `tasks/ioi.py`, `tasks/gp.py`, `tasks/gt.py` for the unrelated-task floor.
   - Start from the Deception-Circuit `main` checkout; work in a worktree under
     `Deception-Circuit/.claude/worktrees/specificity-ladder`.
   - Finding short name to add to the INDEX.md table: `lad`.

5. **Do not redo.**
   - The mechanism-analysis phases 0 to 3 and their verdicts (`docs/research/mechanism-analysis/README.md`).
   - The confounded D-versus-I contrast as a specificity test (F-mech-003); use it only as a comparison row.
   - Coarse v2 D and H masks under the designation-site corruption (F-mds-002).
   - New30 training and the v5 to v7 selective-deception assays (F-sel-003 to F-sel-008).
   - The format-control verdicts (F-fmt-001, F-fmt-002).
   - The closed SDR gates: native controls, named-consequence probe and routing validation (F-sdr-007, F-sdr-008,
     F-sdr-015). Motive-driven pressure gave 0 contingent survivors in 58 cells; do not rebuild it here.
   - The GPU gotcha: 8B node-pruning training runs out of memory on 40 GB A100s; train on A40, H200 or H100.

6. **Do not touch.** SESSIONS.md at Sun 1 Nov 2026, 9:28 am EST shows no claimed direction. The paused and open
   directions keep these protected paths (from `directions.json`): `.scratch/sdr-*` and `outputs/_analyses/sdr-*`
   (sdr-mechanism); `.scratch/selective-deception` and `outputs/_studies/selective-deception`
   (selective-deception); `.scratch/eval5-grader-fixes` (eval5-grader-fixes). The parallel Claude session owns
   `docs/research/instructed-route/`; read it, never write to it.

7. **Budgets.** GPU: 125 reserved GPU-hours in total across Delta and Bridges-2, phase-gated as 25 for A1, 60 for
   A2 after the timing dry-run and 40 for A3; at most 2 concurrent GPU jobs. Bridges-2 goes offline about
   2026-11-09; after that, Delta only. OpenRouter: $10. Usage: pause at 80% of the Codex weekly reading (the
   five-hour window does not apply). Reserve walltime at the observed runtime plus a reasonable buffer; record
   reserved and actual hours in the ledger.

8. **Oversight.** Review checkpoint every 25 session points of weekly usage on Codex (16 if run on Claude). A
   checkpoint is a freeze: no new agents, no new Slurm jobs and no messages to workers except HOLD until the user
   replies "continue". Stall alarm at 60 minutes without progress. Milestone trigger: any direction that passes or
   fails its pre-registered gate gets a worklog entry, and a checkpoint if it changes the plan.

9. **Always ask before.** Merging to main, any EVAL 5 run (the full five-suite benchmark evaluation), dropping a
   direction, raising any cap, and any run that scores a set listed in `docs/research/held_out.json`.

10. **Exit criteria.**
    - **A1 done** when FAR and SER user-turn pools have at least 300 ids at the recorded margin and the ladder is
      scored for the deciding sets of F-mech-001 on held-out ids. **Pre-registered rule:** a component set is
      deception-specific when its knockout removes at least 50% of the D pressure effect, removes under 25% of the
      user-turn I effect, and moves H, F and unrelated-task accuracy by under 5 points each. **Stop** A1 when both
      fallbacks leave a pool under 300 ids; report the sizes and run the ladder on the existing I with the caveat.
    - **A2 done** when 3 seeds of D-twin and I-twin masks exist per task. **Pass:** the set difference D-twin minus
      I-twin is seed-stable (Jaccard at least 0.5 across seeds) and passes the A1 rule. **Null, reported as a
      result:** at least 90% of the D-twin heads lie inside the I-twin mask on every seed. **Stop** when the timing
      dry-run shows one mask above 6 GPU-hours and the heads-only fallback also exceeds the phase cap.
    - **A3 done** when the direction, neuron-range and edge tests have run on 3 seeds. **Pass:** a D-minus-I
      direction whose ablation satisfies the A1 rule and beats the 95th percentile of the random-direction null.
      **Fail:** no direction, neuron range or edge set does. Either way, the twin-trained mask is reported against
      New30 on the same rows.
    - No benchmark run uses an unfrozen grader; record the grader hash in `spec.md` and `directions.json` before
      any benchmark run. Never score a held-out set from `held_out.json`; the "held-out ids" above are the
      mechanism-analysis held-out sample (n=100, seed 1) or fresh samples drawn the same way.

11. **Files.** Directory `docs/research/specificity-ladder/` in Deception-Circuit. `WORKLOG.md` is the human log,
    written only through `research-session worklog-append`. `RESUME.md` is the machine narrative, at most 150
    lines. `state.json`, `worklog.json` and `ledger.json` are written only by the research-session tool. Hand-backs
    go to `reports/` with the headings of `_templates/handback.md`. Run `research-session lint <file>` after every
    write to a Markdown file under `docs/research/` or `.agents/memory/`.

12. **Registration.** Before branching, the orchestrator runs `research-session claim specificity-ladder` on the
    main checkout and commits the claim. Before its first spawn it runs `research-session register
    specificity-ladder`; only a registered session gets checkpoints.

13. **Models.** Orchestrator: Codex. Subagents: Sol on Codex, named explicitly on every spawn. If the session runs
    on Claude instead, the orchestrator is Fable and every spawn passes `model: "opus"`; when the Fable weekly row
    is more than 5 points above the all-models row, reading, analysis and review go to Opus agents.
