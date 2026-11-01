# Closing the instructed deception route and testing it on spontaneous deception

Starting prompt for direction `instructed-route`. Written Sun 1 Nov 2026 by synthesis session claude-0ab0a0b3.
Approved by the user on Sun 1 Nov 2026. Follow `docs/agents/research-session.md` in the Alignment repository.
This is the lighter of the two approved sessions and is meant for a Claude orchestrator.

1. **Goal.** Turn the partial causal account of pressured deception on FAR and SER (clause readers in layers 8 to
   17, the query-fed layer-17 quartet L17H24 to L17H27, late writers) into a closed, adjudicated algorithm, and
   test whether the same route carries deception that nobody instructed.

   The yardstick shared with the parallel session: a part of the model is deception-specific when it is necessary
   in D, not necessary under a transparent inversion in which nobody is misled, not necessary in H or F, and inert
   on an unrelated task. This session does not build that control; it uses the existing I pools as comparison rows
   and states the confound (F-mech-003) wherever it matters.

2. **Directions.** Three directions, deliberately open about method.
   - **B1. Close the loop.** About 0.8 of the twin gap reaches the output directly from components outside the
     analysed grid (synthesis limitation L12), mostly mlp.30, mlp.31 and L31H0. Two pre-registered tests on the
     mechanism-analysis held-out sample: is that outside share mediated by the L17H24 to L17H27 outputs or by a
     bypass; and is the pressure carried at option-token keys, as Sun (arXiv 2605.09314) reports, or at the
     final-token query, as our path patching found? Make path patching position-resolved for this. Fallback: if
     position-resolved patching cannot be built within the phase, run the two tests with segment-restricted
     knockouts (`--knockout-positions`) and report them as such.
   - **B2. The falsity signal and the cross-task question.** Does the model's internal falsity signal track literal
     falsity or misleadingness? Train a probe (or read direct logit attribution) at the answer position on FAR D
     versus H, then test it on SER D, where both options are literally true; read the two answer logits separately,
     because a target-minus-distractor margin cannot separate suppression from promotion. Test the SDR
     preference-following reading on the 618 reported-wish ids (F-mech-012): does knocking out the quartet remove
     the wish effect? Replicate the SER deception-leaning MLPs 11, 13 and 16 (F-mech-009) on held-out ids with a
     second seed. Fallback: if the probe does not reach 0.75 AUROC on FAR itself, report the per-logit DLA
     comparison alone.
   - **B3. Spontaneous deception through the instructed route.** Premise test first: reproduce alignment faking on
     Llama-3.1-8B-Instruct (Mehta, arXiv 2607.13346: compliance rises 24.4 points under monitoring) with a
     first-token or refusal-token proxy checked against a judge. Use sycophancy as the positive control, since Gupta
     (arXiv 2610.22937) confirms L17H24, L15H8 and L15H11 on this model. Then transfer: patch the FAR and SER
     deciding sets and the quartet on the spontaneous contrast. Run circuit discovery on the spontaneous setting
     only if transfer fails. A pre-answer intent representation is tested here, where a real scratchpad exists.
     Fallback: if the premise test fails, run B3 on sycophancy alone and report the elicitation failure with its
     numbers.

3. **Why it is promising.** F-mech-001 and F-mech-002 replicate the published cue-routing route on a deception task
   without closing the loop; B1 completes it and settles a named disagreement with Sun. Knows-versus-says is done
   for factual falsehood (Universal Motif, Campbell, Huan, Long), but nobody has asked it where both options are
   true, which is what SER and SDR provide. No component-level test of a shared route between instructed and
   spontaneous deception exists on any model; a shared result makes the route the deception story, and a divergent
   result locates spontaneous machinery.

4. **What exists.**
   - Findings: F-mech-001, F-mech-002, F-mech-007 (the quartet is query-fed), F-mech-009, F-mech-010 (late honest
     heads flip sign), F-mech-012 (the reported wish moves SDR only), F-mech-013; F-sdr-001, F-sdr-002 (quartet
     restoration on SDR), F-sdr-014; F-mds-003.
   - Synthesis: `docs/research/mechanism-analysis/synthesis.md` sections 3, 5 and 6, with the costed held-out path
     patching (about 5.25 H100 GPU-hours) and the per-instance lens follow-up.
   - The paused sdr-mechanism handoff `docs/research/sdr-mechanism/README.md`, verdict "a partial conditional
     causal explanation, not a complete mechanism"; its next questions (which heads or queries account for the
     quartet contribution) overlap B1 and B2 and may be cited, not resumed.
   - Critic reviews behind this prompt: Alignment `.scratch/synthesis-20261101/review-A.md` (knows-versus-says,
     intent), `review-D.md` (B1, B2, B3), `lit-report.md`, `merged-scored.md`.
   - Data: `data/datasets/{far,sdr,ser}_v2` and twins; the mechanism-analysis selection sample (n=100, seed 0) and
     held-out sample (n=100, seed 1); the SDR reported-wish split of 618 test ids.
   - Code: `component_analysis/path_patching.py` and `receiver_category.py`, `component_analysis/knockout.py`
     (`--knockout-positions`), `component_analysis/dla.py`, `evaluation/ablation.py`, `scripts/sdr_*.py`
     (head-output transplant and rescue), `evaluation/native_interchange.py`. No probe or steering code exists in
     Deception-Circuit; the Alignment root notebooks and `persona_vectors/activation_steer.py` hold older probes.
   - Start from the Deception-Circuit `main` checkout; work in a worktree under
     `Deception-Circuit/.claude/worktrees/instructed-route`.
   - Finding short name to add to the INDEX.md table: `rte`.

5. **Do not redo.**
   - The mechanism-analysis phases 0 to 3 and their verdicts; path patching on the selection sample (L11).
   - The SDR closed gates: native controls, named-consequence probe, routing validation (F-sdr-007, F-sdr-008,
     F-sdr-009, F-sdr-015), and the stopped conditional assays listed in the sdr-mechanism README.
   - Motive-driven pressure clauses in the v2 scaffold: 0 contingent survivors in 58 cells; the reported wish keeps
     0 of 1,000 FAR ids and 7 SER ids, so B2's wish test is SDR only.
   - Shared-core replacement as a correction (F-sdr-013) and New30 or selective-mask work (F-sel-001 to F-sel-008).
   - Truth decodability and direction rotation under instructed lying on this model family (Universal Motif,
     Campbell, Huan, Long); B2 asks the misleadingness question, not the decodability question.

6. **Do not touch.** SESSIONS.md at Sun 1 Nov 2026, 9:28 am EST shows no claimed direction. Protected paths of the
   paused and open directions (from `directions.json`): `.scratch/sdr-*` and `outputs/_analyses/sdr-*`
   (sdr-mechanism); `.scratch/selective-deception` and `outputs/_studies/selective-deception`
   (selective-deception); `.scratch/eval5-grader-fixes` (eval5-grader-fixes). The parallel Codex session owns
   `docs/research/specificity-ladder/`; read it, never write to it.

7. **Budgets.** GPU: 65 reserved GPU-hours in total across Delta and Bridges-2, phase-gated as 20 for B1, 15 for
   B2 and 30 for B3 (of which at most 10 before the premise test passes); at most 2 concurrent GPU jobs. Bridges-2
   goes offline about 2026-11-09, so run B1's path patching there first if it is ready; otherwise Delta.
   OpenRouter: $20, for the alignment-faking judge. Usage: pause at 80% of the five-hour window or 80% of the
   weekly reading (the larger of the all-models and Fable rows). Reserve walltime at the observed runtime plus a
   reasonable buffer; record reserved and actual hours in the ledger.

8. **Oversight.** Review checkpoint every 16 session points of weekly usage on Claude (25 on Codex). A checkpoint
   is a freeze: no new agents, no new Slurm jobs and no messages to workers except HOLD until the user replies
   "continue". Stall alarm at 60 minutes without progress. Milestone trigger: any direction that passes or fails
   its pre-registered gate gets a worklog entry, and a checkpoint if it changes the plan.

9. **Always ask before.** Merging to main, any EVAL 5 run (the full five-suite benchmark evaluation), dropping a
   direction, raising any cap, and any run that scores a set listed in `docs/research/held_out.json`.

10. **Exit criteria.**
    - **B1 done** when both tests have run on FAR and SER on the held-out sample. **Pre-registered rule:** the loop
      closes when restoring the quartet outputs removes at least 50% of the outside-grid share; otherwise it is a
      bypass. Key-side or query-side is decided when one restoration removes at least 15 points more of the
      pressure effect than the other; otherwise "indeterminate". **Stop** B1 if position-resolved patching and the
      segment fallback both fail to run within the phase cap.
    - **B2 done** when the probe transfer, the SDR wish test and the SER replication have run. **Rules:** a FAR
      falsity probe with AUROC at least 0.75 on SER D reads as misleadingness, under 0.6 as literal falsity,
      between as indeterminate; the SDR wish effect runs through the route when quartet knockout removes at least
      50% of it on the 618 ids; the SER MLPs replicate when the deception-leaning sign holds on held-out ids in two
      seeded runs that each write a provenance file; F-mech-009 is `pre-manifest` and cannot advance, so the result
      goes in a new row eligible for `replicated` that supersedes it.
    - **B3 premise passes** when the monitored-minus-unmonitored compliance gap is at least 10 points on at least
      50 queries and the first-token proxy agrees with the judge on at least 80% of rows; otherwise B3 runs on
      sycophancy alone. **Transfer rule:** patching the deciding sets and quartet removes at least 50% of the
      spontaneous gap (shared route) or under 25% (divergent, run discovery within the remaining phase cap);
      between is reported as partial.
    - No benchmark run uses an unfrozen grader; record the grader hash in `spec.md` and `directions.json` before
      any benchmark run. Never score a held-out set from `held_out.json`; "held-out sample" above means the
      mechanism-analysis sample (n=100, seed 1).

11. **Files.** Directory `docs/research/instructed-route/` in Deception-Circuit. `WORKLOG.md` is the human log,
    written only through `research-session worklog-append`. `RESUME.md` is the machine narrative, at most 150
    lines. `state.json`, `worklog.json` and `ledger.json` are written only by the research-session tool. Hand-backs
    go to `reports/` with the headings of `_templates/handback.md`.

12. **Registration.** Before branching, the orchestrator runs `research-session claim instructed-route` on the
    main checkout and commits the claim. Before its first spawn it runs `research-session register
    instructed-route`; only a registered session gets checkpoints.

13. **Models.** Orchestrator: Fable. Subagents: Opus on Claude, passed explicitly as `model: "opus"` on every
    spawn; Sol on Codex. When the Fable weekly row is more than 5 points above the all-models row, reading,
    analysis and review go to Opus agents.
