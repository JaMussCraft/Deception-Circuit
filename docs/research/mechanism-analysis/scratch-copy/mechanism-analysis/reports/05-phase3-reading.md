# Phase-3 reading (ticket 05): path patching on C_t, the A′ adjudication, B-selector, where the pressure enters

Written by impl-05 on 2026-10-26 from `reports/05-phase3-results.{md,json}` (builder
`outputs/_launch_mechanism_analysis/p3_results.py`), after both reviews (`reports/05-review.md`). Curated copies:
`docs/research/mechanism-analysis/phase3/` (R6). Cells: `outputs/_analyses/mechanism-analysis-p3/{d,d_is}/Ct__leaf/
<t>_v2/` on Delta, fetched from Bridges-2 jobs 49896838 (far, 02:19:20), 49896843 (sdr, 01:51:03) and 49896848 (ser,
02:37:42), all exit 0. Ledger: 8.5 GPU-h reserved by walltime (02:45 / 02:30 / 03:15), 7.25 charged after
reconciliation (2.5 / 2.0 / 2.75 at quarter-hour rounding) of the 9.25 allocated; no rerun was needed.

**What ran.** Per task, the grid circuit C_t of ticket 04 (far 72 / sdr 66 / ser 78 Components; R28), at leaf:
a neutral-twin invocation (position-agnostic grid, Segment pass at `--path-twin-position-threshold 0.01`, receiver
categories, completeness sweep) into cell `d`, then an item-swap invocation (grid, Segment pass at the default 0.05)
into cell `d_is`. Twin first so a wall-clock kill could not cost the twin outputs. Phase-2 D views (attention, DLA)
and the phase-1 knockout sweeps were merged into the roles pass from restricted copies (`_merge/<t>_{p2d,ko}`), so the
merge added no row. C_t equals the complement of phase 1C's routing group on every task, so 1C's routing shares apply
unchanged (far 0.163, sdr 0.297, ser 0.006).

**Sample.** Every path number is on the selection sample (n = 100, seed 0), the sample the S_k were chosen on. The
A′ adjudication therefore describes the deciding sets on the sample that chose them. The generalisation claim is
R-AB's held-out verdict (phase 1), not this reading.

**Sign.** Normalized effect against the Neutral-Clause Twin, (clean - patched) / (clean - twin): positive means the
path helps the pressured (deceptive) answer. Floor 0.01. The builder refuses any path file without this convention
marker.

**What decides.** Pre-registered rules decide: the §2.3 categories and > 50 % weighted call, the R11(h)/R14 routing
gate, B-selector's two clauses, R25's rule 4b. Everything labelled EXPLORATORY (the robustness re-readings, the
placement of unsegmented arrivals, the before/after role diff, the cross-task role table, the route description) is
description, not a verdict.

## Verdicts

| prediction or rule (spec section) | phase-3 outcome |
|---|---|
| A′ adjudication, far (2.3, R11(g)) | **A′-clause-reader**: kv_clause holds 0.74 of the deciding set's head weight (13 of 18 heads); clause-reader is not routing-gated |
| A′ adjudication, ser (2.3, R11(g)) | **A′-clause-reader**: kv_clause holds 0.83 (14 of 19 heads) |
| sdr (R-AB reading B) | no sub-reading (§2.3 names them for A′ tasks only). Descriptive shape of the single selector's S_20: **Q-dominated** (0.64, 7 of 14 heads) |
| B-selector clause 1: some L17H24-27 head is Q on >= 2 tasks (2.6) | **holds**: all four heads are Q on all three tasks |
| B-selector clause 2: the core's L24 heads are K/V post-clause movers (2.6) | **fails on every task**: they are Q or none; no K/V cell into an L24 group reaches 0.003 |
| B-selector as pre-registered (a conjunction) | **refuted on its second clause** |
| B4: where the pressure enters K/V (2.6) | the clause span carries most of the K/V weight on far and ser (post-clause 17 % and 21 %); on sdr post-clause K/V carries 44 % |
| Completeness: share of the twin gap on direct paths from outside C_t | far 0.80, sdr 0.81, ser 0.77 (direct writes into the Readout, led by mlp.31, mlp.30, L31H0) |
| Roles rerun (R7, R25 rule 4b with path data) | pressure readers far 16, sdr 4, ser 5, all with receiver category kv_clause; L17H24 is a selector on all three tasks |

## 1. The A′ adjudication (spec §2.3)

Per head of the deciding set, the strongest neutral-twin incoming path at or above 0.01 is placed by receiver type
and, for K/V, by the Segment that carries most of the split (02b's `receiver_category`). Weight is the head's S2p
single effect. MLP members are counted, never called: far 2 (mlp.6, mlp.7), sdr 6, ser 1 (mlp.5). The spec reviewer
recomputed every share from the raw cells and the phase-1 S2p sweep with no mismatch.

| task | status | heads | q | kv_clause | kv_post_clause | kv_unresolved | none | call | sub-reading |
|---|---|---|---|---|---|---|---|---|---|
| far | pre-registered | 18 | 0.20 | **0.74** | 0.00 | 0.03 | 0.04 | kv_clause | **A′-clause-reader** |
| ser | pre-registered | 19 | 0.03 | **0.83** | 0.10 | 0.00 | 0.03 | kv_clause | **A′-clause-reader** |
| sdr | descriptive (B) | 14 | **0.64** | 0.22 | 0.00 | 0.11 | 0.03 | q | none (shape: Q-dominated) |

**Reading.** On far and ser, most of the deciding set's weight sits on heads at L7-14 whose strongest twin input
arrives through their keys or values from the clause span. The senders are the early MLPs (far: mlp.6, 8, 9; ser:
mlp.5, 6, 7, 11), so these heads read a clause representation the MLPs wrote. That is a positive mechanism result per
§2.3: the lie signal enters at these heads. Clause-reader is not a routing-gated sub-reading, so the result does not
lean on routing share (c), though (c) is small on both (0.163, 0.006).

On sdr the single selector's S_20 is Q-dominated: L14H4, L14H5, L14H20, L14H24, L13H18, L14H23 and L17H24 receive
the pressure at their queries, mostly from L12H4, L13H18 and mlp.12-13. Its two kv_unresolved heads, L15H8 and L15H11,
read L14H5 through their shared V group at post-clause template tokens (0.088; section 3), which is mover-shaped.
sdr's R-AB reading is B, so all of this is description: no small set mediates sdr's pressure. Two caveats apply to
every sdr statement that something is absent: the Q shape weakens to mixed at a 0.02 floor, and sdr's routing share
(c) is 0.297, so more than a quarter of its post-clause pressure routes outside C_t, where these paths cannot see.

**Robustness (EXPLORATORY).** The same cells, re-read three ways (`05-phase3-results.md`):

| task | pre-registered | strongest path must help the lie | floor 0.02 | Q vs K+V totals | kv_clause heads / KV groups |
|---|---|---|---|---|---|
| far | kv_clause 0.74 | kv_clause 0.70 | kv_clause 0.58 | K/V 0.80 | 13 / 10 |
| ser | kv_clause 0.83 | kv_clause 0.69 | kv_clause 0.77 | K/V 0.94 | 14 / 10 |
| sdr | q 0.64 | q 0.64 | **mixed** (q 0.38) | Q 0.64 | 4 / 3 |

far's and ser's calls survive every re-reading. Heads of one KV group share their K/V cells, so the 13 and 14
clause-reading heads are 10 independent tests on each task. Placing the kv_unresolved heads as post-clause (section
3) moves no call: far's kv_clause stays 0.74, sdr's q stays 0.64.

Where the strongest path is negative (far L10H9; ser L8H15, L10H9, L11H14, L11H15, L11H24, L11H27), the head's
largest twin input opposes the lie. The pre-registered rule places those by position all the same; the second column
shows the call does not depend on them.

## 2. B-selector (spec §2.6)

| head | far | sdr | ser |
|---|---|---|---|
| L17H24 | Q (L14H4 → q, 0.154) | Q (L14H4 → q, 0.256) | Q (L15H8 → q, 0.207) |
| L17H25 | Q | Q | Q |
| L17H26 | Q | Q | Q |
| L17H27 | Q | Q | Q |
| L17 KV group 6 (one test) | strongest K/V cell -0.008 (under floor) | +0.011 (at floor; Q path 23x larger) | +0.006 (under floor) |
| L24H17 | none | Q | none |
| L24H20 | none | none | Q |
| L24H26 | Q (L17H24 → q) | Q (L17H24 → q) | Q (L17H24 → q) |
| L24H27 | Q (L17H24 → q, 0.072) | Q (L17H24 → q, 0.099) | Q (L17H24 → q, 0.071) |

Clause 1 holds on every task, for every L17 head. Clause 2 fails on every task, under an "all" or a "majority"
reading: no core L24 head is a post-clause mover, and the largest K/V cell into any L24 group is 0.002 in magnitude.
The pre-registered prediction is a conjunction, so **B-selector is refuted on its second clause**.

What the paths show instead (EXPLORATORY description): the L24 heads take the pressure at their queries, from
L17H24. The v1 picture of L24 heads as movers that read pressure-modulated items through K/V does not hold on C_t.
Every Q-category L24 head has a Q sum of 0.01-0.17 over the floor and a K+V sum of 0.

## 3. Where the pressure enters (B4)

Neutral-twin paths into C_t's receivers at or above the floor: far 302, sdr 195, ser 361. A K/V path is placed by
its split's top Segment.

A split whose top Segment is `unsegmented` lands on template tokens. Those tokens sit either before the clause or
after it, and pre-clause positions are identical in D and its twin, so they carry nothing. On every such cell the
pre-clause Segments sum to exactly 0, so the arrival is post-clause. The pre-registered receiver category still calls
these heads kv_unresolved (R25's categoriser); B4 is description, so it places them (EXPLORATORY).

Q, MLP-in and Readout receivers sit at the query positions by construction. Their column records the receiver type,
not where the pressure arrived.

| task | K/V clause span (n / sum abs) | K/V post-clause, named Segment | K/V post-clause, template tokens | post-clause share of K/V | Q / MLP / Readout receivers |
|---|---|---|---|---|---|
| far | 117 / 2.84 | 6 / 0.08 | 19 / 0.48 | 0.17 | 160 / 5.10 |
| sdr | 39 / 0.79 | 2 / 0.03 | 15 / 0.59 | 0.44 | 139 / 4.40 |
| ser | 147 / 3.60 | 17 / 0.31 | 20 / 0.63 | 0.21 | 177 / 5.10 |

No split's top Segment lies before the clause on any task. Every K/V cell above the floor had a split, so nothing is
unplaced.

**Across the three tasks (EXPLORATORY).**
- **far and ser.** The strongest senders are the early and middle MLPs: far mlp.6, 8, 7, 9 and ser mlp.5, 6, 7, 11.
  Between 36 % and 83 % of each one's path weight goes into keys and values on the clause span. Most K/V arrivals
  are on the clause, about a fifth post-clause.
- **sdr.** The strongest senders are heads (L14H4, L15H8, L14H5, L17H24) and mlp.13. None of those heads sends weight
  to clause-span keys or values, and sdr's clause-span K/V weight is 0.28 of far's. Of what sdr does carry through
  K/V, 44 % arrives post-clause, mostly at template tokens. That weight is spread over mlp.13 (0.17), mlp.14
  (0.14), L14H5 (0.09), L13H18 (0.05) and L14H4 (0.05).
- **Shared downstream route.** It is the same on all three tasks. L14H4 (far, sdr) or L15H8 (ser) gives L17H24 its
  strongest query input; L15H8's own strongest input is L14H5 through its values. L17H24 then feeds the L24 queries,
  which write to the Readout.

## 4. Completeness (neutral-twin sweep, direct paths into the Readout)

Each sender's mean is already a share of the clean-minus-twin gap, so the sums are shares of the gap. They are sums
of single direct effects and cancel: the outside absolute sums are 1.68 / 1.79 / 1.76 against signed 0.80 / 0.81 /
0.77, and mlp.30 is negative on every task.

| task | C_t direct (signed) | outside C_t direct (signed) | C_t + outside | largest outside |
|---|---|---|---|---|
| far | +0.095 | +0.803 | 0.90 | mlp.31 +0.20, mlp.30 -0.11, L31H0 +0.05, L27H7 +0.04 |
| sdr | +0.191 | +0.811 | 1.00 | mlp.31 +0.21, mlp.30 -0.11, L31H0 +0.06, L22H28 +0.05 |
| ser | +0.200 | +0.774 | 0.97 | mlp.30 -0.13, mlp.31 +0.08, L31H0 +0.06, L27H7 +0.06 |

About four fifths of the twin gap reaches the Readout on direct writes from outside C_t. The writers are the last
layers (L30-31 MLPs, L31H0), downstream of C_t. That C_t's heads act through them is an inference: the grid has no
L30-31 receivers, so it is EXPLORATORY.

This does not contradict routing share (c), because the two measure different things at different positions:
- **(c), phase 1C.** A joint total-effect knockout of everything outside C_t at post-clause positions **excluding
  the Readout** (`after=pressure_clause,exclude=readout` in every 1C routing line). It says little of the pressure
  is routed outside C_t before the last position (far 0.163, ser 0.006).
- **The sweep.** Single direct effects **at** the Readout. It says the final write at the last position is mostly
  made by late Components outside C_t.

R14 is keyed on 1C's (c), not on the sweep's number, so far and ser do not trigger it.

## 5. Roles rerun (C3)

Role counts on cell `d` with the phase-2 D views, the phase-1 knockout sweeps and the item-swap cell merged, over
C_t's Components only:

| task | pressure reader | selector | binder | mover | suppressor | unknown |
|---|---|---|---|---|---|---|
| far | 16 | 1 (L17H24) | 0 | 0 | 0 | 55 |
| sdr | 4 | 2 (L17H24, L24H27) | 1 (L14H4) | 0 | 0 | 59 |
| ser | 5 | 1 (L17H24) | 1 (L17H26) | 0 | 0 | 71 |

The completeness sweep appends the outside Components it flags to the head table: mlp.30 and mlp.31 on every task,
plus L31H0 and L22H28 on sdr and L31H0 and L27H7 on ser. They have no path grid, all read unknown, and are counted
apart. The cell's own `roles.json` counts include them, giving 57 / 63 / 75 unknown.

**What the path data changed (EXPLORATORY, before/after against phase 2 on Components in both cells).**
- **Pressure readers.** Rule 4b now asks for receiver category kv_clause where path data exist. Seven phase-2
  pressure readers per task lost the role (far 7 of 23 in C_t, sdr 7 of 11, ser 7 of 12), and none gained it.
  - Of the 21 lost, 14 have category Q, 4 kv_unresolved, 2 none and 1 kv_post_clause.
  - far: L9H3, L9H16, L9H19, L11H24, L11H27, L14H5, L15H8.
  - sdr: L13H18, L14H4, L14H5, L14H20, L14H24, L15H11, L17H26.
  - ser: L11H27, L13H6, L13H18, L14H4, L15H8, L15H11, L17H26.

  Every remaining pressure reader is kv_clause.
- **Selectors and binders.** Phase 2 had none of either; the path data supplied the query clause. L17H24 is now a
  selector on all three tasks and L24H27 on sdr. L14H4 (sdr) and L17H26 (ser) are binders.

**Across tasks (EXPLORATORY).** 57 Components are in two or more C_t and 39 in all three. 35 of the 39 have the same
role on every task, but almost all of those are unknown on every task, so this is not a stability result. The
Components of all three C_t with a named role somewhere:
- **L13H21 and L13H23:** pressure reader on all three tasks.
- **L13H20:** pressure reader on far and sdr.
- **L17H24:** selector on all three tasks.
- **L14H4, L17H26 and L24H27:** a named role on one task each.

`roles_cross_task.csv` has the full table.

## 6. Checks

- The twin sweep ran under neutral_twin on the grid's sample on every task (`same_as_grid` true). There were 100 twin
  instances and none was excluded by the gap. No sweep sender is unmeasured.
- The twin Segment pass selected 302 / 195 / 361 cells (K/V share 0.056 / 0.029 / 0.061). That is well under the
  13-18 % break-even of the dry-run costing. The item-swap Segment pass selected 13 / 12 / 12 cells.
- No receiver-category note is flagged `!!`, and no top Segment lies before the clause.
- `scripts/check_cell.py` reports path patching present on all six cells. Its completeness-sweep view looks only for
  `sweep_bars.json` and so misses the twin's `sweep_bars_neutral_twin.json`. That is a review-view gap, not a data
  gap.
- The full suites match the 8 baseline failure names in both environments. The phase-3 tests pass in both.

## 7. Decisions for the researcher

1. **sdr and R14.** sdr's routing share (c) is 0.297, over R14's 0.25, so the 32-MLP grid is formally available for
   sdr with a cap raise (R14: about 2x sdr's phase-3 cost; the ticket estimates +2.75 GPU-h reserve per task).
   Recommendation: **do not run it.** R14 exists to rescue a routing-gated A′ sub-reading (§2.3: "otherwise the
   reading is 'A′, route outside C_t', and R14 applies"). sdr is read B and has no sub-reading, and no
   pre-registered verdict on sdr waits on the grid.
2. **B-selector's paper wording.** Clause 1 holds strongly and clause 2 fails cleanly. Proposed wording: "the L17
   heads take the pressure at their queries on every task (category Q; L17H24 also meets the selector role); the
   L24 heads are not movers but are fed at the query by L17H24". The second half is exploratory and should be
   labelled so.
3. **sdr's route is fragile.** It is mixed at a 0.02 floor, it has mover-shaped post-clause V reads, and (c) is 0.297.
   If the paper describes sdr's route, it should say "query-heavy, with post-clause value reads" and carry those
   caveats.

No reading here changes the phase-4 plan. Two A′ tasks have a positive mechanism result (clause-reader), and one task
is B.
