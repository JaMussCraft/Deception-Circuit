# 03 — Pilot rounds 1 to 3 (GPU) and the pilot selection

**What to do:** run a smoke round, then at least three pilot rounds with the 01 harness on the 02 scaffold,
adapting framings between rounds from each round's report, until every task has a passing cell under one
suffix policy or three rounds have failed for some task. Write one report per round and, on success, the
pilot selection that ticket 04 builds from.

**Status:** resolved (2026-10-20, final ruling: reports/pilot-selection.json = FAR r8_far_strong_on + SDR r9_sdr_unified_on + SER r9_ser_unified_on_B (original predicates), family rule_instructed, suffix on, 2.69 GPU-h; residual wording-style confound in CONTEXT.md; round 10 unused; ticket 04 may start)
**Type:** task
**Blocked by:** 01, 02
**GPU allocation:** 15 reserved GPU-h total, at most 4 h reserved per round (spec §11). Inference only.

## Facts to build on

- Harness: `dataset/pilot_v2.py`, `scripts/pilot_v2.sbatch`, verdicts from `dataset/contingency.py` (01).
- Scaffold, framings, screens, neutral pool, `dataset/check_v2_scaffold.py` (02).
- Acceptance rule and pass definition: spec §6. Allowed adaptations and the three-round minimum: spec §7.
- Throughput planning figure only: about 40 forwards/s on one A40 at batch 32 (format-control job 22878917);
  H200 roughly 5x an A40 (memory `interactive-partitions`). Use the measured `seconds_per_forward` once round
  0 has run.
- A cell is about 9,000 forwards (1,000 instances x (1 prior + 4 conditions x 2 streams)). Round 1 is 32
  cells, about 290k forwards.

## Acceptance criteria

### Round 0 (smoke)
- [x] One cell per task (`r1_consequence`, suffix off, SER wording B), n = 200, one job on an `-interactive`
      partition, after the `--no-model` dry path through the wrapper and `sbatch --test-only`. Ledger entry
      before submission. Check: reports have every schema key, `seconds_per_forward` is plausible, survivors
      files exist, no over-length abort. Fix-forward only in the harness's own files. Exception (spec
      §14.G3): a user-turn fix identical across all three tasks may be made without a hand-back if it is
      logged in `reports/pilot-round-0.md` with the reason; any task-specific change, and anything else
      structural, goes back to the orchestrator.

### Round 1
- [x] `reports/pilots/round1/cells.json`: the 4 round-1 framings x suffix {off, on} for FAR and SDR, x SER
      wording {A, B} for SER (32 cells), n = 1,000 each, seed 42.
- [x] Packed into as few jobs as the queues allow (spec §7); outputs under
      `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/pilots/round1/`.
- [x] `insufficient_n` cells are rerun at 3,000 instances (about 27,000 forwards each) in the same round,
      at most 4 reruns per round and always inside the round's 4 h; any further `insufficient_n` cells carry
      over to the next round's cell list.
- [x] `reports/pilot-round-1.md` written from the template below.

### Rounds 2 and 3 (and the stop rule)
- [x] Stop after any round in which every task has a passing cell under one shared suffix policy and the
      three best passing cells clear the three-task cost line. Otherwise run the next round. Never stop for
      failure before round 3.
- [x] Each later round keeps each task's best framing from the previous round and runs >= 3 distinct framings
      per task. Every new framing is a new file
      `dataset/deception_pools/v2/framings/r<k>_<name>.json` with its hypothesis and predicted metric change
      written BEFORE submission, passes both 02 screens, the length constraints and
      `dataset/check_v2_scaffold.py`, and gets its `reports/02-clause-screen.json`-style screen record in
      `reports/pilots/round<k>/clause-screen.json`.
- [x] Adaptation follows the report's diagnosis, one binding factor per new framing:

| symptom in the round report | binding factor | adaptation |
|---|---|---|
| inversion contingent rate near 0, identity fine | the clause does not make naming the non-designated item the cheap move | stronger or different inducement family at the task's flavor level |
| pressure-deceptive high but nopressure honest low (both polarities) | scaffold default, designation copying (audit §0.3) | suffix policy, user wording |
| honest-instruction item_2 share outside band, or accuracy < 0.80 | positional or ill-defined honest label (audit §2c1) | SER wording, suffix on |
| neutral-twin honest rate far below nopressure rate | neutral sentences act as cues | replace neutral sentences (rescreen) |
| prior-balance keep low for specific pairs | lexical bias | item-pair subset (record dropped pairs) |
| top-5 item pairs > 50% of a task's survivors (round-1 report) | pair-driven collapse | trial `item_pairs_og.json` as a factor (spec §13.2); not allowed otherwise |
| a task's inversion rate is its failing criterion | predicate pair does not support the inversion | vary that task's predicate pair (spec §13.4), hypothesis recorded; not allowed otherwise |
| unexpected argmax tokens above 5% in any condition | answer-format compliance | question/stem wording, same for all tasks |
| copying persists (identity fine, inversion near 0) across clause families | the designating sentence carries the copy cue | vary the designating sentence identically in all tasks (spec §14.G2), hypothesis recorded |

  Thresholds, the readout, the corruption and the instructing-framing ban are never changed.
- [x] Suffix policy, user-turn/stem wording and item-pool or item-subset changes apply to all three tasks at
      once. A predicate-pair change applies to the one task whose inversion rate failed (spec §13.4).
- [x] `reports/pilot-round-<k>.md` for every round.

### Outcome
- [x] A cell passes only if its cost projection, which covers the full-build constraints (binding stratum
      over designation x item polarity x template variant, clause/pair cap applied; spec §14.G1), is within
      budget. Quote `cap_used` for every passing cell.
- [x] SER wordings (spec §14.G4): `pilot-selection.json` lists, for SER, every wording with a passing cell
      under the chosen suffix and framing, marked `preferred: B` when B passed. Ticket 04 judges them all.
- [x] Success: `reports/pilot-selection.json` = `{suffix, per task: {cell_id, framing path, ser_wording,
      contingent rates per polarity, full-build rate per stratum, projected GPU-h}, framing families used,
      family-difference note if the tasks use different families}`. Selection follows spec §13.6: if any
      single framing family has a passing cell for all three tasks, use it for all three even when another
      family yields more on one task. Otherwise take each task's best passing family and record the family
      difference as a confound in CONTEXT.md (worktree file, add it to your commit list) and in the round
      report.
- [x] Failure after round 3 for any task: HARD STOP (spec §10 (i)). Write `reports/pilot-hard-stop.md` with
      the per-round evidence for that task and what was tried; do not propose a two-way result yourself.
- [x] Budget overrun or a round needing more than 4 h: stop and hand back with the numbers.
- [x] Ledger reconciled for every job.

## Round report template (`reports/pilot-round-<k>.md`)

```
# Pilot round <k> (<date>)
Jobs: <ids, partitions, elapsed>; GPU-h this round reserved/actual; cumulative.
## Cells
| cell | task | framing | suffix | SER wording | n | inv rate | id rate | full-build min stratum | HI acc | item_2 share | survivors | proj. GPU-h | verdict |
## Per task: best cell and why; per suffix policy: tasks with a passing cell
## Diagnosis (symptoms from the table above, with numbers)
## Next round: framings kept, framings added (hypothesis, binding factor, predicted change), or stop
## Ledger delta
```

## Hand-back

Hand back to the orchestrator after the pilot selection is written or at a hard stop. Ticket 04 is not
started by you.

## Comments

Interim notes after round 1 (impl-03, 2026-10-19). The ticket stays open: rounds 2 and 3 have not started and
wait for the orchestrator.
- **Round 0.** The harness smoke passed, but the readout argmax was a non-item token in 52-98% of rows.
  Four format-probe sets were run. The orchestrator ruled to adopt a cross-task-identical response line,
  recorded as spec §14.G5. `dataset/deception_v2.py` and `tests/test_deception_v2.py` were updated. The six v2
  test files pass in both envs (224 each). The scaffold check passes with a maximum of 110 tokens. Details are
  in `reports/pilot-round-0.md`.
- **Round 1 insufficient_n box.** It is ticked because no cell was `insufficient_n`, so no 3,000 reruns were
  needed.
- **Round 1 verdict.** All 32 cells fail. SDR role_goal with the suffix on clears both floors but has empty
  audit-identity full-build strata, so its cost is infinite. FAR and SER produce 0 survivors. See
  `reports/pilot-round-1.md`.
- **Slurm jobs.** 23022250, 23022445, 23022706, 23022938, 23023097 (round 0) and 23023884, 23023885 (round 1)
  all completed. 2.50 GPU-h is reconciled in the ledger.

Interim notes after round 2 (impl-03, 2026-10-19).
- **Changes.** Rulings G2 (the "came back" audit designation), G6 (the length band is build-time) and the persona
  family were applied. Four new framings were written, with hypotheses before submission; both screens accept
  all 245 clauses (291 OpenRouter calls, about 1.06 USD). `neutral_candidates_r2.json` was added. The two jobs
  were 23026148 and 23026149, both completed, 1.00 GPU-h reconciled. Ticket 03 is at 3.50 of 15.
- **Verdict.** SDR passes in 4 cells, all suffix on. The best is `r2_sdr_belieftarget_on` at 0.60 GPU-h, cap
  0.10. FAR has 0 survivors in 6 of 6 cells and SER in 11 of 11. See `reports/pilot-round-2.md`.
- **Next.** Round 3 is pending the orchestrator. It is the last round before the §10(i) hard-stop rule for FAR
  and SER.

Final notes (impl-03, 2026-10-19): HARD STOP under §10(i) after round 3.
- **Verdict.** FAR has 0 contingent survivors in 21 cells, SER in 37 cells, across rounds 1-3. SDR passes in
  rounds 2 and 3. The best SDR cells are `sdr_rolegoal_on` at 0.80 GPU-h and `sdr_belieftarget_on` at 0.61
  GPU-h, both cap 0.10. Evidence is in `reports/pilot-hard-stop.md`; the round reports are
  `reports/pilot-round-{0,1,2,3}.md`.
- **Unticked boxes.** "SER wordings" and "Success" stay unticked, because the success condition was not met;
  no `pilot-selection.json` was written. The box "Budget overrun or a round needing more than 4 h" is ticked
  because it never triggered. The largest round reservation was 2.0 GPU-h, and the total is 4.75 of 15.
- **Code (worktree), in the commit list:**
  - `dataset/deception_v2.py`: G5 user turn; G2 "came back" designation; FAMILIES gains persona, altruistic and
    fiction; per-cell overrides (predicate pair, question/stem, frame); `SER_PREDICATE_PAIRS` in the
    literal-truth check; `ser_wording_flags` takes override text.
  - `dataset/pilot_v2.py`: parses and passes `overrides`, and records them in reports.
  - `tests/test_deception_v2.py` and `tests/test_pilot_v2.py`.
  - Framings `r2_{belieftarget,commitment,commission,persona}.json` and `r3_{altruistic,fiction}.json`.
  - `neutral_candidates_r2.json`.
- **Docs:** spec §14.G5 and §14.G6; the ticket-04 note; the ledger; reports and `reports/pilots/round{0..3}/`.
- **Tests (final code).** Base env: 8 failed, 1583 passed, 58 skipped. mgnp: 8 failed, 1736 passed, 19
  skipped. The failures are exactly the 8 baseline names in both envs, with no new failures.
- **Slurm jobs, all COMPLETED.** Round 0: 23022250, 23022445, 23022706, 23022938, 23023097. Round 1: 23023884,
  23023885. Round 2: 23026148, 23026149. Round 3: 23027971, 23027973.
- **Ledger.** Ticket 03 is at 4.75 GPU-h reconciled and 3.18 actual. OpenRouter: 419 calls, about 1.52 USD.
- **Review.** No separate /code-review subagent was run this session. The scaffold and harness changes are
  covered by the new tests: 9 in `test_deception_v2.py` and 1 in `test_pilot_v2.py`.

Round 4 notes (impl-03, 2026-10-20; user decision §14.G7):
- **What ran.** The `instructed` and `instructed_reason` families: 13 cells, jobs 23046347 and 23046348, both
  completed on A100s, 0.50 GPU-h reconciled. The screen took 146 calls, about 0.53 USD. All 120 clauses were
  accepted under the G7 judge rule (prompt `instructed-v1`).
- **Verdict.** FAR has 0 survivors in 5 cells and SER 0 in 6. SDR passes in 2 cells: `r4_sdr_instr_on` at 0.68
  GPU-h and `r4_sdr_instrreason_on` at 1.27 GPU-h. No family passes all tasks, so no `pilot-selection.json` is
  written and the hard stop stands. See `reports/pilot-round-4.md` and section 6 of `reports/pilot-hard-stop.md`.
- **Code changes, uncommitted.** `dataset/deception_v2.py` gains the `instructed` and `instructed_reason`
  families. New files: `dataset/deception_pools/v2/framings/r4_instructed.json` and `r4_instructed_reason.json`.
- **Tests (final code).** Base: 8 failed, 1583 passed. mgnp: 8 failed, 1736 passed. The failures are exactly the
  8 baseline names.
- **Ledger.** Ticket 03 is at 5.25 GPU-h reconciled, 3.60 actual. OpenRouter: 565 calls, about 2.05 USD.

Round 5 notes (impl-03, 2026-10-20; orchestrator ruling §14.G8, final in-scaffold round):
- **What ran.** The `rule_instructed` family in two pools (registry predicates, and the override-predicate alt
  pool): 10 cells with the suffix as a factor, jobs 23046832 and 23046834, both completed, 0.50 GPU-h
  reconciled. The judge took 108 calls, about 0.39 USD. All clauses were accepted under the G8 rule (prompt
  `rule-v1`).
- **Verdict.**
  - SER passes with wording B: `r5_ser_cr_rule_off_B` at 0.73 GPU-h, and `r5_ser_rule_on_B` at 0.69 GPU-h with a
    pair-collapse flag.
  - SDR passes: `r5_sdr_rule_on` at 0.34 GPU-h.
  - FAR fails, with at most 3 survivors.
  - No family and suffix setting passes all three tasks, so no `pilot-selection.json` is written and the hard
    stop stands for FAR. See `reports/pilot-round-5.md` and section 7 of `reports/pilot-hard-stop.md`.
- **The optional STD cell was not run.** The harness accepts only v2 tasks and would need new code.
- **Code changes, uncommitted.** `dataset/deception_v2.py` gains the `rule_instructed` family. New files:
  `dataset/deception_pools/v2/framings/r5_rule_instructed.json` and `r5_rule_instructed_alt.json`.
- **Tests (final code).** Base: 8 failed, 1583 passed. mgnp: 8 failed, 1736 passed. The failures are exactly the
  8 baseline names.
- **Ledger.** Ticket 03 is at 5.75 GPU-h reconciled, 3.95 actual. OpenRouter: 673 calls, about 2.44 USD.

Round 6 notes (impl-03, 2026-10-20; user decision §14.G9, FAR rounds 6-8):
- **What ran.** 7 FAR cells: rule combined with fiction and persona frames, and a question swap via a role-swap
  predicate override with the mirrored pool `r6_rule_swap`. Job 23053380 completed, 0.25 GPU-h reconciled. The
  judge took 16 calls.
- **Verdict.** All 7 fail. The best is `r6_far_swap_rule_off` at inversion 0.010 with 5 survivors. Mean inversion
  h under pressure stays at +2.6 to +4.5. See `reports/pilot-round-6.md`. Rounds 7 and 8 are proposed there and
  await the orchestrator.
- **Code, uncommitted.** `dataset/deception_v2.py`: `make_spec` accepts a role swap of the registry predicate
  pair and requires the question to name the new inversion word. `tests/test_deception_v2.py`: 2 tests. New
  file: `dataset/deception_pools/v2/framings/r6_rule_swap.json`.
- **Tests.** Base: 8 failed, 1585 passed. mgnp: 8 failed, 1738 passed. The failures are exactly the baseline names.

Round 7 notes (impl-03, 2026-10-20; §14.G9):
- **What was built.** A multi-turn in-context demonstration shell: `overrides["demo"]` and `demo_exchange()` in
  `dataset/deception_v2.py`, with 11 CPU tests. Also the strong-rule pool `r7_rule_strong`. Job 23054197 ran at
  `--max-seq-length 224`, because demonstration prompts run 178-212 tokens. It completed, 0.50 GPU-h reconciled.
  The judge took 26 calls.
- **Verdict.** No passing cell.
  - `r7_far_rule_demo_on` clears both FAR floors (0.086 / 0.022, 55 survivors) but fails on cost: clause-cap
    infeasible, about 1.12 GPU-h uncapped.
  - The demonstration leaks into SDR's and SER's nopressure twins (honesty 0.00 / 0.01).
  - Strong wording with the suffix on gives FAR 0.088 / 0.010.
  - See `reports/pilot-round-7.md`. The v2 `max_seq_length` is unchanged; it is a config value and would need to
    be about 224 for any demonstration cell.
- **Tests.** Base: 8 failed, 1598 passed. mgnp: 8 failed, 1751 passed. The failures are exactly the baseline names.

Round 8 notes (impl-03, 2026-10-20; §14.G9, last approved round):
- **What ran.** The pruned strong-rule pool `r8_rule_strong` (all three tasks): 4 cells at cap 120, plus 1 FAR
  demonstration fallback cell at cap 224. Jobs 23055675 and 23055676 completed, 0.50 GPU-h reconciled. The judge
  took 53 calls. No code changed.
- **Verdict.** FAR passes: `r8_far_strong_on` (0.116 / 0.024, 71 survivors, 1.43 GPU-h at cap 0.15) and
  `r8_far_strong_off`. SDR passes: `r8_sdr_strong_on`. SER-B fails under this pool (identity 0.016).
- **Selection.** No single pool passes all tasks, so `pilot-selection.json` is NOT written. The harness's selection
  over rounds 5 and 8 (FAR r8 strong, SDR and SER r5 relational; family `rule_instructed`, suffix on, 2.47 GPU-h) is
  in `reports/pilot-selection.DRAFT.json` for the orchestrator's ruling. See `reports/pilot-round-8.md` and hard-stop
  section 8.
- **Ledger.** Ticket 03 is at 7.00 GPU-h reconciled, 4.80 actual. OpenRouter: 768 calls, about 2.78 USD.

Round 9 and resolution (impl-03, 2026-10-20; orchestrator ruling, user-authorized §14.G10):
- **Round 9.** The unified pool `r9_rule_unified` (+ alt): per task, the 10 best strong forms (r8) + the 10 best
  relational forms (r5). 4 cells, suffix on, job 23057565 completed, 0.25 GPU-h reconciled, 1 judge call.
  - SDR passes: 0.204 / 0.059, 0.57 GPU-h.
  - SER-B passes with original predicates (0.046 / 0.048, 0.69 GPU-h) and with concerning/reassuring
    (0.052 / 0.044, 0.51 GPU-h).
  - FAR fails: identity 0.018 < 0.02. See `reports/pilot-round-9.md`.
- **Fallback path, per the ruling.** `reports/pilot-selection.json` is written from the cross-round triple:
  - FAR `r8_far_strong_on`, 1.43 GPU-h, cap 0.15.
  - SDR `r5_sdr_rule_on`, 0.34 GPU-h, cap 0.10.
  - SER `r5_ser_rule_on_B`, wording B with original predicates, 0.69 GPU-h, cap 0.15.
  - Family `rule_instructed`, suffix on, 2.47 GPU-h.
  - The wording-strength confound is recorded in `CONTEXT.md` (worktree; in the commit list).
- **Checkboxes.** "SER wordings": only wording B passed (B preferred). "Success": the selection exists, via the
  fallback path. The one family is used for all three, with the wording-strength confound noted rather than a
  family difference.
- **Round 10** is not used and stays in reserve.
- **Ledger.** Ticket 03 is at 7.25 GPU-h reconciled, 4.97 actual, of 15. OpenRouter: 769 calls, about 2.78 USD.

Final selection (impl-03, 2026-10-20; orchestrator ruling after round 9):
- `reports/pilot-selection.json` was rewritten:
  - FAR `r8_far_strong_on`: 0.116 / 0.024, 1.43 GPU-h, cap 0.15.
  - SDR `r9_sdr_unified_on`: 0.204 / 0.059, 0.57 GPU-h, cap 0.10.
  - SER `r9_ser_unified_on_B`, original predicates, n=1500: 0.046 / 0.048, 0.69 GPU-h, cap 0.15.
  - Family `rule_instructed`, suffix on, 2.69 GPU-h.
- The fallback triple's DRAFT stays for provenance (`reports/pilot-selection.DRAFT.json`).
- The `CONTEXT.md` entry "Pilot Selection (v2) and its wording confound" now records the residual confound. SDR
  and SER use the unified pool; FAR uses the all act-naming `r8_rule_strong`, whose 10 highest-yield forms are
  FAR's act-naming half of the unified pool.
- Round 10 is unused. The only worktree change is `CONTEXT.md`; the orchestrator commits it.
