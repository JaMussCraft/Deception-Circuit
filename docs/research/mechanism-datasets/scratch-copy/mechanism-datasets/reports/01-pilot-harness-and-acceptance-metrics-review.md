# Review: ticket 01, pilot harness and acceptance metrics

Reviewed 2026-10-19. The `code-review` skill reviews by git diff, and this ticket forbids git, so two
reviews were run on an explicit file list. The first was an independent read-only reviewer agent,
covering both axes. The second was the implementer's own pass, made while the agent's report was late.
The orchestrator ruled on the agent's findings, and every disposition below follows that ruling.

Files reviewed (worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`):

- dataset/contingency.py
- dataset/pilot_v2.py
- scripts/pilot_v2.sbatch
- tests/test_contingency.py
- tests/test_pilot_v2.py
- tests/fakes_v2.py

## Bugs (both fixed, each with its repro as a test)

| # | finding | fix |
|---|---|---|
| B1 | The round selection picked the shared framing family by min rate only and never checked the 14 GPU-h three-task budget. The reviewer's repro has role_goal at 5+5+5 GPU-h with rate 0.20, and consequence at 2+2+2 with rate 0.05. The old code picked role_goal at 15 GPU-h, so the round failed. | The selection now enumerates candidates: one passing cell per task, either all from one shared family or from any families. Ordering is within budget first, then shared family, then highest min rate, then lower cost. If nothing fits, it falls back to the best shared family, flagged over budget. Tests cover the repro, an in-budget mix without a shared family, and the fallback. |
| B2 | The cost greedy filled strata one at a time, so early strata used up a shared clause budget that later strata needed. A fillable cell could project infinite cost, or record a 15% cap when 10% was feasible. | A joint fill was added: event-driven progressive filling, where all strata draw at once and spread evenly over their cells. The projection takes the better of the joint and the scarcest-first sequential fill. Each is a valid capped selection, and neither dominates the other. Test: three strata sharing clause c0 give G = 102,667, a hand-computed figure that the sequential fill reports as infinite. |

## Spec-axis points (ratified by the orchestrator)

| # | point | ruling |
|---|---|---|
| S3 | A cell with 3,000 or more instances and fewer than 30 survivors is a `fail`, not `insufficient_n`. | Ratified as implemented. |
| S4 | The SER wording-B preference also decides `best_cell` and the family choice (spec 14.G4). | Ratified as implemented. |
| S5 | Strata came from the variants present in the data. | Fixed. The strata are now pinned to audit and lab, so a missing variant is an empty stratum with infinite cost. Tested. |
| S6 | Honest-instruction accuracy and item_2 share are pooled over both streams of every survivor. | The reviewer judged this not a deviation but the plain reading of the spec. |

## Standards and nits

| # | finding | disposition |
|---|---|---|
| N7 | A stale report or abort record from an earlier run in the same out-dir survived a re-run, so `--summarize` showed it. | Fixed. Each write first removes that cell's other files. Tested both ways. |
| N9 | The model loaded even when every cell had aborted. | Fixed. Tested. |
| N14 | `prepare_cell` caught only a few error types, so any other error ended the job. | Fixed. Any exception aborts only that cell. |
| N8 | `--summarize` drops the run-level extras: instance count, dropped item pairs and partition. | Not fixed (optional). The per-run summary written by the job keeps them. |
| N10 | The harness builds the instance list and the item-pair gate itself, not through ticket 02's `generate_instances_v2` and `load_item_pairs_v2`. | Not fixed (optional). The calls are identical: `dc.generate_instances` with 25 slots, audit and lab, and the same seed. Ticket 04's build should call the same function so ids match. |
| N11 | CONTEXT.md lacks Contingent Survivor, Pilot Cell, Neutral-Clause Twin and Suffix Policy. | Owned by ticket 02, whose criteria include those entries. |
| N12 | `_rate_table` duplicates `report_utils.pass_rate_by`, and `cell_report` recomputes `classify_all`. | Not fixed (optional, cosmetic). |
| N13 | Infinite costs are written as `Infinity`, which is non-standard JSON. | Documented in the ticket report. Load reports with Python. |
| own | A framing, spec or pool that failed to load killed the whole job. | Fixed earlier. Tested. |
| own | The honest-instruction block lacked the designation x item polarity breakdown that spec 7 asks for. | Fixed earlier. Tested. |

The reviewer listed test gaps: the pair cap binding alone, relaxation after a finite over-budget cost at
10%, and the instance-id prefix across cells of different sizes. All three are now tests.

## No bugs found in

- The classify boundaries, rate denominators, the margin-1.0 recheck, and the honest and deceptive word
  per stream.
- The forwards and GPU-h formula, the relaxation trigger, and `cell_verdict` precedence.
- Harness behaviour: one model load, a shared instance list, and alignment and length asserted before
  the model loads. Abort exits 1 and never truncates. Files are written before the next cell, seconds
  per forward are measured, `--no-model` loads no weights, and the report schema is complete.
- The sbatch wrapper and Python 3.9 compatibility.

## Unresolved

- No real-model scoring ran (no GPU in this ticket). The real-tokenizer `--no-model` dry run passed on
  four cells once ticket 02's pools landed (see the ticket report).
- The joint-or-sequential fill is still a heuristic, not an exact optimum. The exact problem is a small
  linear program, and mgnp has no scipy. The projection is therefore an upper bound on the generated
  count a perfect selection would need.
