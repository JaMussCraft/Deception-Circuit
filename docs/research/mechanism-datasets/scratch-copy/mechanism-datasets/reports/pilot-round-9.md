# Pilot round 9 (2026-10-20): one unified pool for all three tasks (user-authorized, spec §14.G10)

**Outcome: the fallback path was taken.** Under the single pool `r9_rule_unified`, SDR passes, and both SER-B cells
pass with the strongest SER rates of the pilot. FAR fails narrowly: identity contingent 0.018 against the 0.02
floor.

Per the orchestrator's ruling, `reports/pilot-selection.json` is therefore written from the provisionally accepted
cross-round triple:
- FAR `r8_far_strong_on`
- SDR `r5_sdr_rule_on`
- SER `r5_ser_rule_on_B`

All are family `rule_instructed`, suffix on, the same scaffold, 2.47 GPU-h. The wording-strength confound is
recorded in `CONTEXT.md`. Round 10 stays in reserve.

**Job.** 23057565 on `bgrb-delta-gpu`, gpuA100x4-interactive, 1 GPU, 30-minute limit, cap 120, COMPLETED, exit 0,
00:10:29. GPU-h: 0.5 reserved, 0.25 after reconciliation, 0.17 actual. Ticket 03 cumulative: 7.25 of 15 (4.97
actual). OpenRouter: 1 new judge call; ticket 03 totals 769 calls, about 2.78 USD.

## Design, as built

**`r9_rule_unified`** (family `rule_instructed`). Every task has 20 clauses:
- Slots 00-09: the 10 best strong forms from `r8_rule_strong`, ranked by survivor yield in that task.
- Slots 10-19: the 10 best relational forms from `r5_rule_instructed`, ranked by yield, skipping any form already
  among the strong ten.
- The yields count every non-demonstration cell that used each pool, with override-pool survivors mapped back by
  slot (`pilots/round9/rank_forms.py` and `rank_forms.json`). Ties keep slot order.
- The same 10/10 split and the same two styles apply in every task.
- FAR's relational half is thin: only 6 relational forms produced FAR survivors outside the demonstration cells,
  so the remaining 4 are zero-yield fills.

**`r9_rule_unified_alt`** holds the same clauses with SER written in concerning/reassuring words, for the
predicate-override cell.

**Screens and gates.** All 120 clauses were accepted under `rule-v1`; every text but one was already judged.
- Per-task medians 12 / 12.5 / 12.5, and flavor band 9-15.
- Median gap with the suffix on: 6 for FAR + SDR + SER-A, 3 for SER-B.
- Maximum 107 tokens, prompts aligned, neutral coverage of 2 or more.

**Cells.** Suffix on, cap 120, the round-2 neutral pool, seed 42. FAR and SDR at n = 1,000; the two SER-B cells at
n = 1,500.

## Cells

| cell | n | h NP inv / id | shift inv / id | h P inv | honest NP inv / id | contingent inv / id | survivors | clauses w/ survivors | top-clause share | HI acc / item_2 | GPU-h cap 0.10 | GPU-h cap 0.15 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r9_far_unified_on | 1000 | +5.42 / +3.88 | **-4.35** / -2.23 | +1.07 | 1.00 / 0.93 | 0.094 / **0.018** | 57 | 9 | 0.23 | 0.99 / 0.49 | inf | inf | **fail** (identity 0.018; cost) |
| r9_sdr_unified_on | 1000 | +3.35 / +1.33 | **-5.87** / -3.52 | -2.51 | 0.96 / 0.55 | 0.204 / 0.059 | 133 | 20 | 0.11 | 0.87 / 0.39 | 0.57 | 0.57 | **pass** |
| r9_ser_unified_on_B | 1500 | +3.99 / +2.28 | **-3.46** / -2.61 | +0.53 | 0.95 / 0.69 | 0.046 / 0.048 | 70 | 15 | 0.29 | 0.94 / 0.56 | inf | 0.69 | **pass** |
| r9_ser_cr_unified_on_B | 1500 | +5.03 / +3.38 | **-4.78** / -3.75 | +0.26 | 0.99 / 0.65 | 0.052 / 0.044 | 72 | 14 | 0.21 | 0.94 / 0.56 | inf | 0.51 | **pass** |

`round_verdict` gives: suffix on passes SDR and SER; no selection.

What the cells show:
- **FAR loses ground against round 8.** Round 8's all-strong pool gave 0.116 / 0.024; the unified pool gives
  0.094 / 0.018. Half of FAR's clauses are now relational, and relational rules move FAR little (shift -4.35,
  against -4.73 in round 8). Survivors come from 9 clauses, so the projection is infeasible at both caps.
- **SER is much stronger than in any earlier round.** Original predicates give 0.046 / 0.048 with 70 survivors.
  Concerning/reassuring gives 0.052 / 0.044 with 72 survivors and 0.51 GPU-h. Round 5's selected SER cell gave
  0.025 / 0.057 with 41 survivors.
- **SDR is the strongest SDR cell of the pilot:** 0.204 / 0.059, 133 survivors, 0.57 GPU-h, feasible at cap 0.10.

## Path taken and the selection written

Round 9 does not give a single-pool triple, so `reports/pilot-selection.json` is written from the cross-round
triple, following the ruling:

| task | cell | round | pool / wording | contingent inv / id | survivors | proj. GPU-h | cap_used | cap 0.10 / 0.15 feasible |
|---|---|---|---|---|---|---|---|---|
| FAR | r8_far_strong_on | 8 | r8_rule_strong / act-naming | 0.116 / 0.024 | 71 | 1.43 | 0.15 | no / yes |
| SDR | r5_sdr_rule_on | 5 | r5_rule_instructed / relational | 0.188 / 0.094 | 142 | 0.34 | 0.10 | yes / yes |
| SER | r5_ser_rule_on_B | 5 | r5_rule_instructed / relational | 0.025 / 0.057 | 41 | 0.69 | 0.15 | no / yes |

- Suffix on; family `rule_instructed`; SER wording B with the original predicates. Total 2.47 GPU-h, within the 14
  GPU-h line.
- **Confound:** wording strength differs within the family (act-naming for FAR, relational for SDR and SER). It is
  recorded in `CONTEXT.md` ("Pilot Selection (v2) and its wording confound") and in the selection file.
- **Caveats in the file:**
  - The SER cell is marginal: inversion 0.025, 41 survivors, pair-collapse flag.
  - Ticket 04 must use cap 0.15 for FAR and SER.
  - Round 9's stronger SER and SDR cells exist but were not used, because the ruling names the round-5 + round-8
    triple. Substituting `r9_ser_cr_unified_on_B` or `r9_ser_unified_on_B` for SER would be a different selection
    and needs the orchestrator's word.

## Ledger delta

`03-r9-unified` (job 23057565) was reserved at 0.5 and reconciled to 0.25, with 629 s actual. The OpenRouter entry
is 1 call. Ticket 03 is at 7.25 GPU-h reconciled, 4.97 actual.
