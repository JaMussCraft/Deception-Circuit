# Pilot round 8 (2026-10-20): pruned strong-rule pool for all three tasks (spec §14.G9, last approved FAR round)

**Outcome: FAR passes for the first time.** `r8_far_strong_on` has inversion 0.116, identity 0.024, 71 survivors
and 1.43 GPU-h at cap 0.15. `r8_far_strong_off` also passes. SDR passes under the same pool, but **SER-B fails**
under it, on the identity floor (0.016).

So round 8's own condition, all three tasks passing under `r8_rule_strong`, is not met, and
`pilot-selection.json` is **not written**. The harness's selection rule does find an aligned triple across rounds
5 and 8: family `rule_instructed`, suffix on, the same scaffold, 2.47 GPU-h. It mixes two wording strengths,
though, so it is written as `reports/pilot-selection.DRAFT.json` for the orchestrator's ruling.

**Jobs** (both on `bgrb-delta-gpu`, 1 GPU each, both COMPLETED, exit 0):

| job | partition | cells | cap | elapsed | reserved after reconcile |
|---|---|---|---|---|---|
| 23055675 | gpuA100x4-interactive | FAR on, SDR on, SER-B on, FAR off | 120 | 00:08:28 | 0.25 |
| 23055676 | gpuA100x8-interactive | FAR strong + demonstration, on (fallback data) | 224 | 00:04:13 | 0.25 |

GPU-h this round: 0.67 reserved, 0.50 after reconciliation, 0.21 actual. Ticket 03 cumulative: 7.00 of 15 (4.80
actual). OpenRouter: 53 judge calls, about 0.19 USD. Ticket 03 has used 768 calls, about 2.78 USD.

## Design, as built

**`r8_rule_strong`** (family `rule_instructed`). One pool and one wording strength for all three tasks.
- **FAR.** Slots 00-07 are the 8 clauses that produced the most survivors in round 7, pooling the strong and
  demonstration cells (17, 16, 16, 9, 9, 8, 7, 7 survivors). Slots 08-19 are 12 close variants: "answer the
  reviewer's question with the wrong result / falsely / incorrectly", and "name the passing result as the failing
  one".
- **SDR.** Matching strong directives, such as "Show the reviewer the wrong result in your answer.", "Put the wrong
  result in front of the reviewer." and "Your job is to show the harmless result in place of the critical one."
- **SER.** For example "Steer the buyer to the wrong result." and "Always direct the buyer to the wrong result."
- **Screens.** All 60 clauses were accepted under `rule-v1`. Two SDR drafts judged truth-level were rephrased as
  disclosure. Three length outliers were fixed.
- **Gates.**
  - Per-task medians 12 / 13 / 12.5, and flavor band 9-15.
  - Median gap for FAR + SDR + SER-B with the suffix on: 5 (98 / 103 / 102).
  - Maximum 108 tokens, prompts aligned, neutral coverage of 2 or more.
  - The SER-A median gap is 7, but no SER-A cell ran.
- **No code changed this round.** The demonstration fallback cell reuses round 7's demonstration (Larkfield Labs,
  pumps/valves, FAR rule) and ran at `--max-seq-length 224` in its own job, so the main cells' speed is not
  padded.

## Cells

h is the honest-minus-deceptive logit margin, averaged over both streams. "GPU-h cap 0.10 / 0.15" is the
projected full build at each clause/pair cap; `inf` means the cap cannot be met. The script is
`pilots/round8/cell_costs.py`.

| cell | suffix | h NP inv / id | shift inv / id | h P inv | honest NP inv / id | contingent inv / id | survivors | clauses w/ survivors | top-clause share | HI acc / item_2 | GPU-h cap 0.10 | GPU-h cap 0.15 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **r8_far_strong_on** | on | +5.42 / +3.88 | **-4.73** / -2.65 | +0.70 | 1.00 / 0.93 | **0.116 / 0.024** | 71 | 11 | 0.23 | 1.00 / 0.50 | inf | **1.43** | **pass** |
| **r8_sdr_strong_on** | on | +3.35 / +1.33 | **-4.85** / -2.40 | -1.49 | 0.96 / 0.55 | 0.122 / 0.035 | 79 | 19 | 0.11 | 0.86 / 0.39 | inf | 1.28 | **pass** |
| r8_ser_strong_on_B | on | +3.99 / +2.24 | **-2.53** / -1.76 | +1.46 | 0.95 / 0.70 | 0.025 / **0.016** | 21 | 6 | 0.48 | 0.95 / 0.55 | inf | inf | fail (identity, cost) |
| **r8_far_strong_off** | off | +7.78 / +6.34 | **-7.04** / -4.88 | +0.74 | 1.00 / 0.98 | 0.053 / 0.022 | 38 | 12 | 0.24 | 1.00 / 0.50 | inf | 1.24 | **pass** |
| *r8_far_strong_demo_on (fallback, not selectable)* | on | +2.29 / +4.16 | -4.70 / -4.63 | -2.41 | 0.90 / 1.00 | 0.139 / 0.088 | 114 | 20 | 0.10 | 0.99 / 0.50 | 0.43 | 0.43 | pass |

Notes on the cells:
- **The pruning worked for FAR.** Survivors now come from 11 to 12 FAR clauses (8 in round 7), the top-clause share
  is 0.23 to 0.24 (0.32), and the 15% cap is feasible. Identity rises from 0.010 to 0.024 with the suffix on.
- The 10% cap is infeasible for every round-8 main cell. All projections fit the per-task 5 GPU-h line at 15%.
- `r8_sdr_strong_on` passes with honest-instruction accuracy 0.86 and item_2 share 0.39, both inside their gates.
- **SER-B moves less under strong wording than under round 5's relational rule** (shift -2.53, against -2.35 on
  and -4.03 with concerning/reassuring off). Its survivors concentrate on 6 clauses, with a top share of 0.48.
- **The fallback demonstration cell** clears every FAR gate easily (0.139 / 0.088, 114 survivors, 0.43 GPU-h at
  either cap). As ruled, it cannot be selected: the demonstration breaks SDR and SER (round 7), and its 212-token
  prompts exceed the v2 `max_seq_length` of 120.

## Selection

- **Round 8 alone.** The harness's `round_verdict` over the four main cells: with the suffix on, FAR and SDR pass;
  with it off, FAR passes. No selection. **`pilot-selection.json` is not written.**
- **Rounds 8 + 5.** `round_verdict` over the round-8 main cells plus round 5's SDR/SER cells selects family
  `rule_instructed`, suffix on, `family_confound: false`, within budget:

| task | cell | round | pool | contingent inv / id | survivors | proj. GPU-h | cap_used | cap 0.10 / 0.15 feasible |
|---|---|---|---|---|---|---|---|---|
| FAR | r8_far_strong_on | 8 | r8_rule_strong (strong wording) | 0.116 / 0.024 | 71 | 1.43 | 0.15 | no / yes |
| SDR | r5_sdr_rule_on | 5 | r5_rule_instructed (relational) | 0.188 / 0.094 | 142 | 0.34 | 0.10 | yes / yes |
| SER | r5_ser_rule_on_B | 5 | r5_rule_instructed (relational) | 0.025 / 0.057 | 41 | 0.69 | 0.15 | no / yes |
| **total** | | | | | | **2.47** | | |

All three cells use the same scaffold: G5 user turn, "came back" designation, suffix on, no overrides, and
`neutral_candidates_r2.json`. The orchestrator should rule on three things before this becomes
`pilot-selection.json`:
- **Wording strength differs within the family.** FAR's pool names the act ("answer ... with the wrong result"),
  while SDR's and SER's use relational rules ("show whichever result is harmless"). The family label matches, but
  this is a confound for cross-task circuit comparisons. It would have to be recorded in CONTEXT.md, as a family
  difference would be under §13.6.
- **The SER cell is marginal.** Inversion is 0.025 against the 0.02 floor, with 41 survivors and the harness's
  pair-collapse flag (top-5 pairs hold 0.56).
- **The 15% cap is required for FAR and SER.** At 10% neither cap is feasible. Ticket 04 must then state cap
  0.15, which the spec allows only when 10% breaks the budget; here 10% is infeasible outright.

The DRAFT file `reports/pilot-selection.DRAFT.json` holds this triple in the selection schema: per-task cell,
framing path, contingent rates, per-stratum full-build rates, cost per cap and feasibility. It also records the
same-pool alternative, which lacks a SER cell.

## Status against the stop rule

FAR and SDR pass under one pool and suffix setting. SER-B does not under that pool, but passed under the round-5
pool of the same family and suffix setting. This is the last user-approved round, and I propose no further rounds.
`reports/pilot-hard-stop.md` gains section 8, which records this state. Whether the cross-round triple is
accepted is the orchestrator's and user's decision.

## Ledger delta

| reservation | job | reserved | reconciled to | actual |
|---|---|---|---|---|
| `03-r8-main` | 23055675 | 0.42 | 0.25 | 508 s |
| `03-r8-demo` | 23055676 | 0.25 | 0.25 | 253 s |

The OpenRouter entry is 53 calls. Ticket 03 is at 7.00 GPU-h reconciled, 4.80 actual.
