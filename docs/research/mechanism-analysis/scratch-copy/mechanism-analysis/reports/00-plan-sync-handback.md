# 00 plan sync hand-back (plan-01, 2026-10-25)

Task: sync every plan document to rulings R0-R17 and `reports/00-plan-review.md`, with nothing stated two ways.
Writes only under `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/`. No git, no runs, no Slurm. One CPU
read of the repo (`component_analysis/sampling.py`, `dataset/clause_surgery.py`, `dataset/contingency.py`,
`dataset/deception_v2.py`) to ground tickets 02a and 08. Pre-sync copies are in `/u/swong2/.claude/jobs/1c836bb8/tmp/`
(`spec.pre-sync.md`, `issues.pre-sync/`, `agent-brief.md`, `00-plan-draft.md`).

## What changed, per document

**`spec.md`** (regenerated except §9, which is verbatim plus one dated sync note):

- Status line: synced, awaiting review-00's re-check. Worktree recorded as created.
- §2 opens with R17's calibrated-vs-convention sentence. §2.1: outcome B reworded to what is measured (R11(f));
  outcome A's second half decided by RQ-B/C.
- §2.2: test sets D, H, F, I; selection sample (seed 0) and held-out sample (seed 1, ids excluded); "post-clause"
  positions defined; R-cls on signed d with "opposes" first and the upper-95%-bound clause (R16).
- §2.3 R-AB rewritten per R11: S2p ranking at post-clause positions, layer-0 MLP excluded, S2 descriptive; single and
  greedy selectors; k grid {1,2,3,5,10,20,40,80}; held-out tests; 20-draw layer-matched null; per-instance bootstrap
  CIs; (i) as ratio of means and beating every null draw; readings renamed "pressure mediators"; deciding set;
  routing check (a)-(c); exhaustive A′ adjudication with five sub-readings and the 0.25 routing condition.
- §2.4 new rule R-inv (R15).
- §2.5 R-A1 per R13: no-pressure column decided under zero, variant-matched mean bank as robustness, R-A1 read for
  sets 3-6 only.
- §2.6: B-selector rewritten to the four categories with the KV-group caveat; B-reader with the binomial test;
  R-lens exploratory with the clause-form table and clustered bootstrap (R12).
- §2.7: C1 and C-own read from phase-1 sweeps with U bound (R16); C-own defined with its low power.
- §2.8 ticket 07 conditional (R5). §2.9 adds the pre-clause sanity assertion.
- §3: tickets 01, 02a, 02b, 08; the variant-matched bank in 01; the range form of `--knockout-positions` in 02a.
- §4 recosted (below). §5: one gate rule, R9's wording verbatim; every "user says go" removed; the criteria
  constraint per R10; Delta fallback H200-only for phases 2-3. §6: per-ticket table, ledger lock, records (R6, R16).
- §7: 23 limitations, the review's list and the B4/B5 caveats included. §8 trimmed to what is still the builder's.
- §10: no open questions; a question-to-ruling table.

**Tickets:**

- `02-v2-component-analysis-prerequisites.md` deleted; replaced by `02a-v2-prerequisites-for-phase-1b.md` and
  `02b-neutral-twin-attention-path-patching-and-criteria.md`.
- `08-instructed-inversion-control-condition.md` new.
- Every ticket: `**Status:** ready-for-agent` (07 marked conditional), Type, Blocked by, GPU allocation, Facts,
  Acceptance criteria, Hand-back with R9 verbatim. No "HARD STOP" left.
- 01: no longer blocked by user approval; adds the variant-matched mean bank (R13), the 36-cell 1A set with per-task
  packing, and writing the baseline failures file first.
- 02a: v2 ids including the I condition; `response_line` Segment (R7); the `neutral_prompt` trap with a test;
  held-out sampling with id exclusion (the sampler has none today, `sampling.py:217`); knockout schemes,
  counterfactual, positions with the range form, the groups JSON format, in-process greedy selection, the layer-0
  exclusion; DLA twin and lens summary; the clause-form table; drift inputs verified in the manifest.
- 02b: attention and path patching under the twin; the per-head receiver category; the amendment written to a
  report, then applied after the orchestrator's go (R10), with a starting proposal for the pressure-reader criteria.
- 03: allocation 19.5; the 1C flow (R-inv and routing computed for every candidate set, so no second pass); flip-audit
  paths; groups-file script; C1, C-own and C-MLP moved here from 04; the R5 statement; curated copies.
- 04: no single-knockout passes; an I cell per task; the pre-clause sanity assertion; H200-only fallback.
- 05: A′ adjudication; routing condition; R14's 32-MLP grid outside the allocation; H200-only fallback.
- 06: records under `docs/research/mechanism-analysis/`; the k-grid mediation curve with null; the cell move before
  worktree removal.
- 07: conditional per R5; all on Delta H200, 6.0 GPU-h.

**`agent-brief.md`:** the ticket list; the review as a must-read; `docs/component-roles.md` edited only by 02b under
R7/R10; the R9 gate verbatim with the agent-level hand-back triggers separated from it; the ledger lock procedure
(literal-path `mkdir` lock); a Records section (R6, R16); Delta fallback by phase; heredocs refused by the hook.
Commit footer unchanged.

**`reports/00-plan-draft.md`:** Questions section removed; "Decisions I made for you" lists the ten rulings; R-AB
presented with the held-out sample, the null and the "pressure mediators" name; the inversion control in two
sentences; R9 verbatim; new cost table. Still one page.

**`reports/00-plan-handback.md`:** a dated note at the top and SUPERSEDED banners on "Open questions" and "Revisions
after review". Facts (a)-(g) and the cost model untouched.

Not touched: `RESUME.md`, `compute-ledger.json` (orchestrator files).

## New cost table (Bridges-2 H100 GPU-h)

For the orchestrator to copy into the ledger's allocations.

| ticket | reserve | expected | change vs pre-review |
| --- | --- | --- | --- |
| 01 | 0 | 0 | - |
| 02a | 1.0 | 0.5 | was "02" 1.0 |
| 02b | 0.5 | 0.25 | new |
| 08 | 0.5 | 0.25 | new |
| 03 (phase 1) | 19.5 | 12.1 | +2.25 / +1.1 |
| 04 (phase 2) | 3.5 | 2.0 | -0.5 / 0 |
| 05 (phase 3) | 9.25 | 5.3 | - |
| 06 | 0 | 0 | - |
| holdback | 0.75 | - | was 3.5 |
| **total** | **35.0 (70 SU)** | **~20.4** | |
| 07 (Delta H200, conditional) | 6.0 Delta | 3.9 Delta | was 6 Delta + 2.5 H100 |

Phase 1 by block: 1A 7.5 / 4.7 (36 cells, one job per task); 1B 9.0 / 5.5 (7 sweeps + L per task); 1C 3.0 / 1.9
(one job, three tasks). Arithmetic per block is in spec §4.

## Calls I made where the rulings did not close

1. **Greedy depth.** R11(d) says greedy over the top 50 and a k grid to 80. Greedy runs to k = 20 (the deciding
   range); k = 40 and 80 come from the single selector only.
2. **R-A1 sets.** R13 decides the no-pressure column under zero. To stay in the cap, zero cells run for sets 3-6
   (set 5 added for C-confound); sets 1, 2 and 7 get only the mean D-test column, as calibration rows with no R-A1
   reading. Adding zero for them costs about +1.5 reserve.
3. **Ticket 08 before 1C.** 1C is blocked by 08; 08 runs in parallel with 01 and 02a. I's clause must match D's
   clause token count per instance, so `<t>_v2_honest` pairs with I by id; unmatched rows are dropped and counted.
   Behaviour filter: target margin >= 0.7 in both streams (`contingency.MARGIN`); fewer than 300 kept per task
   triggers a hand-back. R-inv's factor of 0.5 is a convention, like R-cls's.
4. **U in 1B** is the 123 heads at leaf; the flagged MLPs join U only in phase 2. Ticket 03 writes the U operand.
5. **R-cls signs.** `max(d(H), d(F))` floors negatives at 0 (a convention). "opposes" is checked first.
6. **Routing condition.** R11(h) names A′-mover only. I applied it to every sub-reading that rests on where or
   whether grid paths arrive: A′-mover and A′-unresolved. A′-selector and A′-clause-reader rest on a positive path
   and do not need it.
7. **A′ categories.** R11(g)'s "post-clause item or question positions" became "any post-clause position" (item
   mentions, question, response line, stem, Readout), so the four categories are exhaustive.
8. **`C_t`** holds every head of the deciding set (up to 20) plus at most 10 MLP blocks; grid sizes may reach about
   80 Components. The `--dry-run` decides the cost; over the allocation, ticket 05 hands back.
9. **Clustered bootstrap scope.** Applied to between-task CIs on instance-level quantities; C-own and C-reads are
   head-level tests and are not clustered.
10. **Ledger lock** is a `mkdir` lock directory beside the ledger; a lock older than 15 minutes triggers a hand-back,
    never a break.

## Disagreements and things I could not place

- **Holdback.** R17 says the phase-1 rise fits within the 3.5 h holdback. The recost uses more than that: phase 1
  +2.25 reserve, plus 02b and 08 (+1.0). At the 35 h cap the holdback is 0.75. Expected use is about 20.4, so about
  14 h is freed as reservations reconcile, and §6 lets the orchestrator move reconciled savings between tickets
  inside the cap. If you want a larger holdback instead, two cuts raise it to 2.75: run 1A's mean cells of sets 1,
  2 and 7 only if budget remains (-1.5), and drop phase 2's rerun (-0.5). I recorded this in the §9 sync note rather
  than changing R17.
- **Ticket 07's GPU type.** R5 says Delta "H200/A40". On A40, six training runs alone cost about 15 GPU-h, beyond
  R5's 6. The ticket says H200 only and names the cap raise A40 would need.
- **R2's scope.** R2 covers tickets 01-06; ticket 08 (R15) also draws on the Bridges-2 cap. Noted in the §9 sync
  note.
- **"ticket 02" in R4, R7, R10** now means 02a (R4's smoke and drift gate) and 02b (R7, R10's amendment). Noted in the
  §9 sync note; the ruling text is unchanged.
- **The pressure-reader criteria text** is a starting proposal in ticket 02b, not a final text. R10 has it reported to
  the user before it is applied.
- **Two selectors** give each task more than one chance at reading A; the null controls each test, not the family.
  Stated in §7 item 10. If you want a stricter rule, the cheap fix is to make the single selector decide and the
  greedy selector descriptive.
- **R11(a)'s "or S2 minus S3"** alternative is not used. S2p is a separate sweep (13 min per task), because S2 minus
  S3 is not a knockout of the post-clause positions.
