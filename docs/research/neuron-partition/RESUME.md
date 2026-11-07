# Resume: neuron-partition

Last rewritten: Sat 7 Nov 2026, 9:50 am EST by claude-5201d56c, during wrap-up (merge on hold).

## Status

The first report (`reports/05-first-report.md`, final) carries two decisions: R13 (N1 FAILED on the original
ladder, N2 UNDETERMINED) and R14 (the size-500 all-position deception-only class passed a pre-registered
confirmation on fresh ids). On Wed 4 Nov 2026 the user approved four follow-ups, pre-registered as R15 and run the
same day under a 30 GPU-hour cap (R16, user decision, need N1 resolved):

- R19, finding F8 (reviewed, review 06): the finer ladder passes every N1 bar at sizes 250, 375, 625 and 750 on
  the seed-3 sample; 750 is the largest size tested, so the class's size is not bounded above.
- R18, finding F7 (reviewed, review 05): N2 on FAR at size 2,000 on fresh data is "suppression or shared" (H minus
  21.9, rate minus 12.7); the rate clause is inside the null band, the H fall is not.
- R20, finding F9 (reviewed, review 07): SER at size 500 (predicate-naming rows, R17, need N2 resolved at its
  default) removes 0.96 of the deception margin under twin but fails N1 on collateral (H minus 15.8, F minus 6.3);
  N2 on SER is suppression or shared; 210 of the 386 class neurons lie in the Codex A3 SER layers; the lost
  H and F pairs are almost all identity rows (honest answer is the other item).
- R21, finding F10 (reviewed, review 08): the one-neuron interchange check finds the attribution ranking predicts
  single-neuron twin interchange effects in sign (40 of 40 for D, 39 of 40 for H) and in size for layers 13 to
  19; the top 20 by s_D span layers 0 to 19 and the six class members among them carry 0.21 of the class's 0.81.

Findings F1 to F10 are in `WORKLOG.md`. The follow-up results report is `reports/13-followups-4nov.md` (final,
all four results reviewed). Every GPU job is reconciled: 21.58 of 30 GPU-hours reserved,
38,632 GPU-seconds (10.7 hours) actually used. No job of this session is queued on Delta or Bridges-2.

## Branch, worktree and commit

- Branch: `neuron-partition`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`.
- Last commit on the branch: see `git log -1`; the branch starts from main at `7a020a9` (claim rendered).
- Tool-owned records (state, worklog, ledger, hook-saved hand-backs) live in the main checkout at
  `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/`; everything else is on the branch.
- Uncommitted work, if any: none.

## In-flight jobs

None. Reservations r-001 to r-017 are all reconciled (r-009 cancelled, r-010 failed on gpub001, the rest
completed).

## Next action

Wrap-up began Sat 7 Nov 2026 at the user's request. Done so far: `README.md` written; rows F-np-001 to F-np-010
added to `docs/research/FINDINGS.md` (findings-check clean); the worktree's `outputs/_analyses/neuron-partition/`
(2.2 GB) and its Slurm logs copied into the primary checkout at the same paths and verified by checksum; the
Bridges-2 ablation outputs verified identical to the Delta copies by summary hashes. On hold because another agent
is merging onto main: (1) `research-session release neuron-partition --status paused`, `render` and
`ledger-rollup`, and the commit of the tool-owned records in the primary checkout; (2) fast-forward merge of this
branch into main and push; (3) delete the branch locally and on origin and remove the worktree; (4) final worklog
entry and state Closed. The user says when main is free. Release status `paused` is proposed because the options
below are open; the user may choose `done`.

## Do not

- Do not redo the head-level D/H partition (F-comp-001), the head-level cross-task tests (F-mech-005, F-mech-008),
  the layer-17 residual probe (F-rte-004), or any residual-stream direction.
- Do not use the item-swap corrupt prompt as the neuron ablation reference (near no-op by construction).
- Do not use SAE or transcoder features, top-activating lists without ablation, raw Jaccard without ceiling and floor,
  or thresholds tuned on the evaluation ids.
- Do not read or import code from `.claude/worktrees/specificity-ladder/`, write there, or touch its Slurm jobs
  (23472894, 23474289 and later). Read its user-turn pools only, by path, and record sha256.
- Do not record a verdict in the Codex A3 cell (down-projection-input neurons at MLP layers 5 to 8 and 11, readout
  position only, D-minus-I gap over H standard deviation, top 1 percent per layer, A1's 100 assessment ids).
- Do not use A1's 100 assessment ids or the mechanism-analysis held-out samples for ranking or ablation.
- Paused directions (sdr-mechanism, selective-deception, mechanism-datasets, deception-divergence) stay paused.

## Open decisions for the user

- None pending in the WORKLOG needs section (N1 and N2 resolved on 4 Nov 2026). The next research step is the
  user's choice (report 13, section 5).
