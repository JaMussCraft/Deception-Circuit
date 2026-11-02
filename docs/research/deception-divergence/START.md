# Where deception and transparent inversion come apart: listener knowledge, the second turn and a learned partition

Starting prompt for direction `deception-divergence`. Written Mon 2 Nov 2026 by synthesis session claude-ecd31ee4.
D1 to D4 were approved by the user on Mon 2 Nov 2026; the user's two directions U1 and U2 were merged in after an
Opus critic pass and a literature check (Alignment `.scratch/synthesis-20261102/`) and the merged form awaits the
user's confirmation before launch. Follow
`docs/agents/research-session.md` in the Alignment repository. This session runs on Claude.

1. **Goal.** Find a readout on which deceiving an unaware user and a transparent inversion actually differ in
   Llama-3.1-8B-Instruct, then say what carries that difference, as components, a stored state or a learned
   partition.

   Why this framing: every first-token test so far says "shared" (F-mech-003, F-mech-005, F-rte-004, F-rte-008,
   and Codex's A1 result F2 in `docs/research/specificity-ladder/WORKLOG.md`). At the first answer token the
   pressured condition D and a transparent inversion I emit the same item, so a "D-only" part there is at most
   who-said-the-clause machinery. The user-turn I control that Codex uses also moves the instruction from the
   operator turn to the user turn (compliance on D-selected rows 89/95/84 percent for FAR/SDR/SER under user-turn
   I against 21/79/25 under the operator-turn I), so a first-token positive could be system-prompt machinery.
   This session builds role-matched controls and looks downstream of the first token.

2. **Directions.** Six items in two phases, deliberately open about method. Phase 0 runs before the Fable weekly
   reset (Tue 4 Nov 2026, about 7 am EST); the code-heavy items of phase 1 start after it.
   - **D1. Listener-knowledge and role-matched controls (gate, phase 0, 3 to 4 GPU-h).** Keep the operator clause
     identical and toggle one sentence, "The user can see these instructions" against "The user cannot see these
     instructions"; also score the operator-turn transparent I (the existing `invd_` clauses) on the same
     unselected prior-kept candidate ids of each task, stratified by clause id and designation polarity; a
     stratified sample per clause and polarity (a few hundred ids per cell) is enough, the full prior-kept pools
     are not required. Rescore
     the dropped D ids, since their per-id records were deleted on 2026-11-01 (the instance lists are seeded, seed
     42, and `dataset/build_deception_v2.py` is the builder). Report, per task: does the first-token choice
     condition on the listener's knowledge, and does operator-D compliance sit below role-matched transparent
     compliance on matched ids (an honesty override)? Report the matched-pool counts. Either null is a result.
     Document the pools under this direction's outputs; the user decides whether Codex consumes them. Fallback: if
     the visibility sentence is ignored, try two further phrasings (one naming the user's belief, one naming the
     consequence of being found out) and report all three before calling it null.
   - **D2. Lie maintenance: the second-turn state (phase 1, 1 GPU-h premise, then 8 to 15 GPU-h).** Teacher-force
     the same first answer in D, transparent I and H, then add follow-ups whose correct response the instruction
     does not dictate: Pacchiardi-style unrelated elicitation questions with a classifier refit on this model on D
     against H and tested on I, and a "user acts on it" turn ("I'll tell my boss it's X"). Do not use "Is that
     right?" alone: an "Are you sure?" follow-up by itself makes this model waver (Zhang 2412.14959), and self-report
     runs partly through refusal machinery (Nguyen 2606.23671), so add a refusal-direction control. Pre-register
     an R2-style reading: "I patterns like H" means a deception state, "I patterns like D" means a falsity state.
     If D and I separate, the mechanistic payload is position-resolved patching on the second-turn readout: does it
     read the clause tokens, or a state stored at the model's own prior answer tokens? Fallback: report the
     maintenance and reveal rates as a behavioral null.
   - **D3. The honesty override (phase 1, 8 to 12 GPU-h, only if D1 shows one).** Fit a graded resistance direction
     on resisted-versus-complied D (margin 0 to 0.7 against honest, clause-stratified), test it against an Arditi
     refusal direction (fit on a harmful/harmless prompt set, which the repository lacks) and a persona direction,
     and patch the resisted state from a resisted D id into a complied one with I and H held fixed. Fallback: D1's
     null is the result; do not fit the direction.
   - **D4. Closure riders and the static read of the quartet (phase 0, about 4.5 GPU-h).** (a) Capture the
     layer-17 quartet's attention patterns under D versus its neutral twin on the B1 held-out ids
     (`component_analysis/attention_patterns.py`, `neutral_twin` condition, never run in B1), to settle whether
     the query-side signal of F-rte-006 changes which positions are attended. (b) The "after the cue window only"
     arm of J4 (F-rte-008 caveat; one new position mask in `spontaneous/patching.py`). (c) SDR key-versus-query with
     the B1 route-closure code and the R9 offline estimator on `sdr_v2` held-out ids, so the SDR-against-FAR/SER
     contrast (F-sdr-012 against F-rte-006) rests on one code path; inputs exist (`phase1/groups/sdr_heldout_D.json`,
     `phase3/ct.json`, `jobs/05-p3-sdr.batch`). (d) U2 as approved: a static QK/OV read of L17H24 to L17H27 with
     the rule in section 10 (P1, P2); note the four heads share one key/value group under grouped-query attention.
     Fallback for any rider: report what ran; none gates anything else.
   - **U1. A learned three-way partition (phase 1, gated; 6 GPU-h build and pilot, then 12 to 15 GPU-h).** One
     training run over the frozen model that learns three node masks, deception-only, opposite-only and shared,
     with sufficiency terms (shared plus own set reproduces each behavior) and, because sufficiency alone makes
     "everything shared" optimal, an own-necessity hinge and a cross non-necessity hinge per specific set, using the
     A1 thresholds of the specificity-ladder START verbatim (knocking out a specific set removes at least 50 percent
     of its own effect and under 25 percent of the other's, with the effect measured against each condition's own
     neutral twin and knocked-out gates taking the twin activation). The contrast is D against listener-visible D
     from D1 (identical clause, one sentence differs), not D against H (no honesty signal under twin corruption,
     F-rte-004; answer machinery under the default corruption, F-mds-002) and not D against user-turn I (Codex A2
     and A3). Needs a mutually exclusive four-way gate in `l0.py` (`HardConcreteGate` is an independent Bernoulli
     per gate), paired two-condition loaders and a four-pass objective; clause-twin corruption exists only on
     Codex's branch. Reuse Codex's reviewed plan-a3 Task 5 constrained-mask driver rather than building a second
     one, after the user has coordinated with Codex (section 9). Positive control: the same partition on IOI
     against GP from `tasks/` (GT does not support Llama). A visible-D training dataset paired with its own neutral
     twin is required code, because D1 produces scored prompts, not a dataset. Run FAR with 3 seeds first; SER and
     SDR are deferred. Premise test in phase 0
     (about 1 GPU-h): node-level attribution patching of the D effect and the visible-D effect (and the
     operator-turn I effect) with split-half reliability; U1 is built only if at least one component's difference
     clears the split-half noise. Fallback: if D1 is null, the partition is predicted empty by construction and U1
     dies; if the positive control fails, the deception run is not read.
   - **U2 remainder, deferred.** Weight masking, parameter decomposition (APD/SPD; no 8B application beyond IOI,
     infeasible in this budget) and LoRA diffing (with identical D and I targets the two updates cancel; a
     listener-conditioned LoRA can key on the sentence's words) are not run here. Keep a rank-1 to rank-4
     separability LoRA (honest in visible-D, compliant in D, held-out clauses, label-shuffled control) only as a
     reserve check if D1 passes and points remain, under the reserve in section 7.

3. **Why it is promising.** Lie maintenance is measured behaviorally (Pacchiardi 2309.15840, Vaugrante
   2502.08301) but nobody has patched the second turn; no paper ablates a refusal direction and measures compliance
   with a lie instruction; no paper learns a shared and behavior-specific circuit partition in one run (CURE
   2604.04982 and CLUE 2509.20977 split separate circuits afterwards; the necessity term exists only one-sided,
   Bayazit 2310.03084, SafeSeek 2603.23268); nobody has projected the quartet's OV circuits onto the item
   unembeddings. Independent runs sample an equivalence class, so set differences between them are noise (Bayat
   Makou 2606.06267); a joint run forces the shared part to be literally shared. A pass on D1 or D2 is the first
   place a deception-specific part is definable without the by-construction confound; a clean double null is the
   answer to "does this 8B condition its behavior on the listener's knowledge". Literature verdicts above are
   mostly abstract-level reads (`.scratch/synthesis-20261102/lit-check.md`, `lit-check-2.md`).

4. **What exists.**
   - Findings: F-mech-001 to F-mech-013, F-rte-001 to F-rte-008, F-mds-002, F-sel-006, F-sel-007, F-fmt-003.
     An independent Opus review of the raw JSON on 2026-11-02 confirms F-rte-005 and F-rte-006 and finds two
     provenance gaps in F-rte-008 that this session should correct in its first findings pass: the supplement run
     behind the heads-only, FAR-set and SER-set numbers ran at commit c32627e (parity at a6ae1a6), not 21bc397,
     with identical code hashes; the subject-clustered interval 0.669 to 0.770 is in no listed file and reproduces
     from `margins.json` and the item file at seed 1. Also loose: the 25 largest outside senders sit in layers 22
     to 31, not 18 to 31; the key-arm dispersion "0.21 and 0.17 against 0.02" is in raw logits. Report in
     `.scratch/synthesis-20261102/evidence-review.md`.
   - Working files of this synthesis: Alignment `.scratch/synthesis-20261102/` (proposal, candidates, the user's
     directions, two critic reviews with the role-confound table and the U1 objective analysis, two literature
     checks, the data locator with exact paths).
   - Data: `data/datasets/{far,sdr,ser}_v2` with `_honest`, `_nopressure`, `_inversion`, and `sdr_v2_inversion_reported`
     (618 rows); builder `dataset/build_deception_v2.py` (gates: prior, D margin 0.7, no-pressure honest,
     neutral-twin honest, capped selection; funnel FAR 86,457 passed prior, 12,514 passed margin; SDR 19,315 and
     10,314; SER 36,893 and 7,213); the held-out sample `docs/research/mechanism-analysis/phase1/groups/*_heldout_D_sample.json`
     (n=100, seed 1). Codex's user-turn I pools live only in their worktree under
     `outputs/_analyses/specificity-ladder/a1-control-77b6487-m07/` (read for comparison rows, never write).
   - Code: `component_analysis/route_closure.py` (`offline_direct_effects`, `quartet_path_patching`,
     `feeder_path_patching`), `scripts/route_closure_readings.py`, `component_analysis/path_patching.py`
     (`receiver_inputs`, `positioned_effects`, position-resolved), `component_analysis/attention_patterns.py`,
     `spontaneous/patching.py` and `scripts/b3_patch.py` (J4 arms), `scripts/falsity_probe.py` (residual probe),
     `evaluation/benchmark_eval.py` (general message renderer; MASK doubling-down builds a four-turn history),
     `train.py` and `pruning.py` (MGNP node masks; loss `(1 - lambda) * (w * KL + task) + lambda * L0`),
     `train_selective_mask.py` (preserve/suppress objective), `l0.py`, `tasks/ioi.py`, `tasks/gt.py`.
     Batch files: `docs/research/instructed-route/jobs/B1-{far,ser}.batch`, `B2-p2.batch`,
     `docs/research/mechanism-analysis/jobs/05-p3-sdr.batch`. Outputs: `outputs/_analyses/instructed-route-b{1,2}/`,
     `outputs/_studies/b3/`.
   - Missing: a two-turn row builder (closes the first answer, appends a follow-up, defines the readout at the
     second answer, segments the prior answer and the follow-up); a harmful/harmless prompt set for a refusal
     direction; any refusal-direction or difference-of-means code on main (Codex's `a3_directions.py` is head-space
     and theirs; `persona_vectors/activation_steer.py` in Alignment is a residual steerer).
   - Start from the Deception-Circuit `main` checkout; work in a worktree under
     `Deception-Circuit/.claude/worktrees/deception-divergence`. Finding short name to add to the INDEX.md table:
     `div`.

5. **Do not redo.**
   - Any first-token "necessary in D, not in user-turn I" test at head, mask, direction, neuron or edge level on
     FAR/SDR/SER: Codex A1 to A3 (`docs/research/specificity-ladder/START.md`). Do not rebuild the user-turn I pool.
   - The instructed-route tests B1, B2, B3 and their verdicts (`docs/research/instructed-route/README.md`): the
     quartet bypass, query-side entry, the falsity probe, the SDR wish, the SER MLPs, the alignment-faking premise
     (N2, a second elicitation, is not proposed) and the sycophancy transfer.
   - The mechanism-analysis phases 0 to 3, the confounded D-versus-I contrast, the coarse v2 D and H masks, New30
     and the v5 to v7 assays, the format-control verdicts, the closed SDR gates (F-sdr-007, F-sdr-008, F-sdr-015;
     their refusals come from a closed gate and cannot seed D3's resisted pool).
   - The named parallel route from the deciding set to mlp.30, mlp.31 and L31H0 (F-rte-005): supported by the
     per-sender numbers (quartet-mediated shares 0.35, 0.70, 0.47 on FAR and 0.45, 0.44, 0.55 on SER) but left to
     Codex A3's edge attribution unless the user says A3 excludes the late writers.
   - U1 with H as the opposite behavior, and U1 against user-turn I.
   - The GPU gotcha: 8B node-pruning training runs out of memory on 40 GB A100s and A40s; train on H100 or H200.

6. **Do not touch.** SESSIONS.md at Mon 2 Nov 2026, 8:23 am EST shows one claimed direction, `specificity-ladder`
   (codex-01a1987e, running, nothing listed). Treat `docs/research/specificity-ladder/`, the worktree
   `Deception-Circuit/.claude/worktrees/specificity-ladder` and branch `specificity-ladder` as read-only, including
   their uncommitted records in the main checkout. Protected paths from `directions.json`: `.scratch/sdr-*` and
   `outputs/_analyses/sdr-*` (sdr-mechanism); `.scratch/selective-deception` and
   `outputs/_studies/selective-deception` (selective-deception); `.scratch/eval5-grader-fixes`. Do not write to
   `docs/research/instructed-route/` except the F-rte-008 row correction in FINDINGS.md.

7. **Budgets.** GPU: 55 reserved GPU-hours in total, phase-gated as 10 for phase 0 (D1, D4, the U1 premise), 40 for
   phase 1 (D2 up to 16, D3 up to 12, U1 up to 21 with at most 6 before its positive control passes) and 5 in
   reserve; no limit on concurrent GPU jobs, so parallelise whenever the queue allows (the ledger cap is set to 99
   because the tool needs a number). Check the Bridges-2 SU balance before reserving there; it was near 500 SUs on
   1 Nov and has not been verified since. Budget rule: the phase upper bounds add to about 63 GPU-h, so the cap of
   55 binds; if both D3 and the full U1 run qualify, run D3, hold D2 at 8 GPU-h, then run U1 on FAR only, and if
   the full U1 run would cross 55, defer it with its spec and pilot already done. Use Bridges-2 (allocation cis260361p, `--gpus-per-node=h100-80:1`,
   `--export=ALL,DC_CLUSTER=...`, model load about 460 s) first so Delta's fair share is spared; it goes offline
   about 2026-11-09, after which Delta only (beto and bimc fair share is poor; bgrb or bjhz start sooner). Run
   8B mask training on H100 or H200 only. OpenRouter: $20 for the D2 judge and classifier labels. Usage: pause at
   80% of the weekly reading (the larger of the all-models and Fable rows; Fable was 46% on Mon 2 Nov, reset Tue
   4 Nov about 7 am EST), so expect about 30 points before the reset and plan the code-heavy phase 1 after it.
   Reserve walltime at the observed runtime plus a reasonable buffer; record reserved and actual hours in the
   ledger.

8. **Oversight.** Review checkpoint every 16 session points of weekly usage on Claude. A checkpoint is a freeze: no
   new agents, no new Slurm jobs and no messages to workers except HOLD until the user replies "continue". Stall
   alarm at 60 minutes without progress. Milestone trigger: any direction that passes or fails its pre-registered
   gate gets a worklog entry, and a checkpoint if it changes the plan; D1's verdict is such a checkpoint.

9. **Always ask before.** Merging to main, any EVAL 5 run (the full five-suite benchmark evaluation), dropping a
   direction, raising any cap, any run that scores a set listed in `docs/research/held_out.json`, and writing any
   U1 trainer code (the user coordinates with Codex first so the two sessions do not build the same driver).

10. **Exit criteria.**
    - **D1 done** when the visibility toggle and the operator-turn I are scored on the same unselected candidate ids
      for all three tasks, stratified by clause and polarity, with matched-pool counts. **Pre-registered rule:**
      behavior conditions on listener knowledge when compliance differs between the two visibility arms by at
      least 10 points on matched ids (paired bootstrap interval excluding zero, clustered by clause); an honesty
      override exists when operator-D compliance sits at least 10 points below role-matched transparent
      compliance on matched ids. **Stop** D1 after the three phrasings; a null on all three is reported as a result
      and kills D3 and U1.
    - **D2 done** when the premise and, if it passes, the patching have run on the three tasks. **Premise rule:** D
      and I separate when the undictated-follow-up classifier (fit D against H, tested on I) or the acts-on-it
      maintenance rate differs between D and I by at least 15 points with the refusal control not explaining it
      (refusal-direction ablation changes the gap by under half). **Mechanism rule:** the state is "stored at the
      lie" when patching the prior answer tokens from the twin moves at least 50 percent of the second-turn
      effect while patching the clause tokens alone moves under 25 percent, on held-out ids, against 20 random
      position sets. **Stop** at the premise if it fails; report the rates.
    - **D3 done** when the resistance direction has been ablated and patched on held-out ids over 3 seeds.
      **Pass:** the direction's ablation raises operator-D compliance by at least 20 points on matched ids while
      moving I and H by under 5 points, and it beats the Arditi refusal direction and the 95th percentile of 20
      random directions. **Fail:** otherwise, with the refusal direction's share reported.
    - **D4 rules.** (a) and (b) report their numbers; (c) replicates F-rte-006's rule (query share minus key share
      against 0.15) on SDR. (d) **P1, query side:** Q-composition scores of each layer 7 to 16 head's OV into the
      quartet's W_Q are computed for every layer 7 to 16 head; head.15.8 and head.14.4 must each rank in the top 5
      percent of those scores, and the layer 14 and layer 15 sums must exceed every other layer from 7 to 16 (the B1
      readings store query-side path effects only as layer totals plus those two heads, so no full ranking exists
      for a rank correlation). **P2,
      copy:** at least 2 of the 4 quartet heads reach an OV copy score of at least 0.5 against the item unembeddings
      with the final-norm-scaled W_U. A P1 fail means the routing is activation-dependent, which supports the
      distributed parallel route; neither outcome bears on specificity.
    - **U1 done** when 3 seeds of the FAR partition and the IOI-against-GP positive control exist. **Pass:** on the
      held-out sample, every seed's D-only set removes at least 50 percent of the D effect and under 25 percent of
      the visible-D effect, moves H, F and IOI accuracy by under 5 points each, has Jaccard at least 0.5 across
      seeds, and beats 20 layer-matched random sets of equal size; the positive control recovers task-specific
      components. **Null, reported as a result:** the D-only set is empty or infeasible (positive hinge residual)
      on every seed while the positive control passes. **Uninterpretable:** the positive control fails; the
      deception run is not read. **Stop** U1 at the timing pilot if one run exceeds 5 hours.
    - No benchmark run uses an unfrozen grader; record the grader hash in `spec.md` and `directions.json` before
      any benchmark run. Never score a held-out set from `held_out.json` (it is empty on 2026-11-02); the "held-out
      ids" above are the mechanism-analysis sample (n=100, seed 1) or fresh samples drawn the same way.

11. **Files.** Directory `docs/research/deception-divergence/` in Deception-Circuit. `WORKLOG.md` is the human
    log, written only through `research-session worklog-append`. `RESUME.md` is the machine narrative, at most 150
    lines. `state.json`, `worklog.json` and `ledger.json` are written only by the research-session tool. Hand-backs
    go to `reports/` with the headings of `_templates/handback.md`. Run `research-session lint <file>` after every
    write to a Markdown file under `docs/research/` or `.agents/memory/`.

12. **Registration.** Before branching, the orchestrator runs `research-session claim deception-divergence` on the
    main checkout and commits the claim by explicit file list (the main checkout carries Codex's uncommitted
    specificity-ladder records; never add them). Before its first spawn it runs
    `research-session register deception-divergence`; only a registered session gets checkpoints.

13. **Models.** Orchestrator: Fable. Subagents: Opus on Claude, passed explicitly as `model: "opus"` on every spawn.
    When the Fable weekly row is more than 5 points above the all-models row, reading, analysis and review go to
    Opus agents. Workers never run git; the orchestrator commits by explicit file list.
