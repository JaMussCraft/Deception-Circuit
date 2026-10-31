# 02b review (impl-02b, 2026-10-26)

Two review sub-agents (spec axis, standards axis) read the worktree at the state committed as 925417c (base ddd1da4);
no diff was available to them, so each read the 02b parts of the current files. Their reports are folded in below,
with what was fixed afterwards (commits d134ea48 and 83599b5 on mechanism-analysis), what was left as a judgement
call, the smoke verdict and the phase-3 cost numbers. The hand-back `reports/02b-handback.md` carries the running
record; the amendment text is `reports/02b-criteria-amendment.md`.

Severity as in `02a-review.md`: **hard** = breaks a binding rule or a test of record; **soft** = worth fixing or
stating; **note** = recorded for later tickets.

## Spec axis

Holds (per the spec reviewer): attention `neutral_twin` paired condition with `_neutral_twin_paired` columns and
coverage meta; B2 column `clause_mass_drop_neutral_twin_paired` + `_se`, paired per instance; path patching
`neutral_twin` counterfactual, `both` = item_swap + neutral_twin on v2 and item_swap + honest_instruction on v1;
the Segment pass under the twin; twin columns gated on the cell asking for them; v1 snapshot byte-identical; rules 4
and 6 read `strongest_incoming_neutral_twin_paired` on v2 through `at_own_query`; `response_line` -> `frame`; check
order suppressor, binder, selector, pressure reader, mover; K-V tie tests; pre-clause top Segment -> `kv_unresolved`
with `!!`.

| # | finding | severity | disposition |
| --- | --- | --- | --- |
| S1 | Amendment C / R25(A): `--path-position-threshold` is one flag for every counterfactual, so at 0.01 the item-swap Segment pass widens too; the dry-run table priced one position pass | medium | **fixed** (d134ea48): new `--path-twin-position-threshold` (default unset = the shared flag) lowers the neutral-twin pass alone; `position_threshold(ctx, counterfactual)`; item_swap keeps 0.05. Smoke batch, roles doc, spec R25 A wording and the cost table (per selected share, item_swap at 0.05 beside the twin at 0.01) updated |
| S2 | Amendment B: a skipped twin pass (v2 H or F cell) still wrote category `none` per head through the standalone CLI, so roles would read `twin_paths_measured=True` and fail the where-clause instead of giving the `attention and knockout only` flavour | medium | **fixed** (d134ea48): `categorize_cell` raises `TwinPassSkipped`; `write` writes nothing (no JSON, no columns = unmeasured); the CLI exits with the reason. The in-job path was already guarded (`summaries is None` -> `continue` before the hook) |
| S3 | tie-break divergence: `head_table_columns` uses `strongest()` (stable sort, grid order), the category used `_rank_key` (q, k, v, layer, index, sender name); on an exact tie the two columns could name different cells | low | **fixed** (d134ea48): `_rank_key` is `-|mean|` alone over the incoming list, which is built in grid order (q receiver, then the group's k and v, senders in run order) exactly as `_receives` + `cells_into`; verified against the payload's receiver and cell order. Doc tie sentence updated |
| S4 | coverage: the in-job category columns are declared over `measured_ids(tally)` (gap-excluded removed), the CLI's `write()` over `agnostic.sample.instance_ids` (= used ids); same columns, two instance lists when an instance is gap-excluded | low | **left, recorded**: the smoke had 0 gap-excluded instances; the CLI is a rerun path for finished cells. Ticket 05 should declare the CLI's coverage from the agnostic file's measured ids if it reruns categories after the fact |
| S5 | B2 reads `column_query = query[0]` when `readout` is not in `--query-positions`, while amendment B says "Readout-query attention mass" | low | **left, recorded**: every v2 job file (phase 2 and the smoke) passes `readout`; the payload names the query it used (`column_query_position`). A guard that refuses B2 without `readout` is a one-liner for ticket 04 if it ever drops `readout` |
| S6 | scope beyond the amendment: `--path-category-floor` (a second tunable beside `--roles-path-floor`); the `receiver-category` subcommand; `lean_of` includes rule 4b with `where` vacuously true, so an `unknown` v2 head with a significant post-clause knockout prints "pressure reader lean"; `print_decisions` tallies `ROLES` only; the "rule 4b not measured" notes | note | `--path-category-floor` kept (defaults to the doc's path floor 0.01, named in the doc; the standalone flag now carries the same name); subcommand kept (it is how a finished cell is re-categorised without a GPU and how the smoke cell was re-checked); `print_decisions` **fixed** (tallies `variant.roles`); the lean text and the not-measured notes left as they are (the lean is a note, never a role, and the where-clause is vacuous only when path data is absent, which the note says) |
| S7 | process items open at review time: smoke, both-env suites, ledger, this review | — | all done: see below |
| S8 | (post-review, impl-04, R27) `views_of` read `dla.differential_paired` on both variants; a v2 DLA cell writes it null and puts the paired differential in `dla.differential_neutral_twin_paired`, so no v2 Component could be a selector and rule 6's differential clause was vacuous; the v2 fixture kept the v1 column filled, which hid it | hard | **fixed** (83599b5): `Variant.differential_column` / `_se_column` (V1 = instruction pair, V2 = twin pair) read in `views_of`; doc row, rule 4 and 6 sentences, change-log item 5; the `v2()` fixture helper now carries what a v2 cell writes (14 existing v2 tests went red on that alone) plus 4 new tests |

## Standards axis

py3.9: all changed files compile and the targeted tests pass under the base 3.9 interpreter; no v1 behaviour change
found (snapshot test, v1 key sets).

| # | finding | severity | disposition |
| --- | --- | --- | --- |
| T1 | pre-registration: `docs/component-roles.md` had no rule 4b, no 2026-10-25 entry, no B2 floor, no receiver category, no `response_line`, while roles.py and the v2 tests cited the amendment; the tree assigned a role the doc forbade | hard | **fixed** (d134ea48): the amendment applied to the doc with the dated change-log entry naming it an orchestrator ruling under the user's standing go (R25), and CONTEXT.md's Segment and Component Role entries made consistent. By design the doc was untouched until the R10 go, which came after the review |
| T2 | flag prefix: `receiver_category.py --floor` lacked the `--<analysis>-` prefix; the job path called the same number `--path-category-floor` | hard | **fixed** (d134ea48): the standalone flag is `--path-category-floor` |
| T3 | vocabulary: `SEGMENT_GROUPS` comment said "CONTEXT.md's prompt anatomy" while `response_line` was absent there; `receiver_category.py` labelled the `q` arrival "a selector", which CONTEXT.md forbids (no single view assigns a role) | hard | **fixed** (d134ea48): comment says "CONTEXT.md's Segment entry" (which now lists `response_line`); the `q` line says the head itself is steered by the pressure and that the category alone names no role |
| T4 | Repeated Switches: `variant is V1/V2` tested at six sites in roles.py plus two other discriminators of the same fact (`"paired_counterfactual" in depends`, the two-key fallback in `at_own_query`); `CHECK_ORDER_V2` read directly at one site instead of `variant.check_order` | judgement call | left: each site branches on a different v2 fact (which columns, which notes, which payload keys), and the `Variant` carries what is shared (roles, check order, incoming and differential columns). Folding every branch into the dataclass would move criteria text out of the rule functions the doc cites by name |
| T5 | Duplicated Code: `is_v2` in path_patching and attention_patterns beside dla, knockout and roles copies (five implementations of "task name in `V2_TASKS`") | judgement call | left: each is two lines reading `dataloaders.V2_TASKS` lazily (ADR-0001 keeps model modules free of import-time coupling); a shared helper is a ticket-04 tidy-up if it touches all five |
| T6 | the stale "There is one" subcommand text in analyze_components.py; the "Noted, never assigned" docstring on `pressure_reader_signature`; the hard-coded "0.05 and 2 SE" in the B2 note | soft | **fixed** (d134ea48): docstring lists the three subcommands; the signature docstring says v1-only and points to rule 4b; the B2 note names `--roles-b2-floor` and `--roles-z` |
| T7 | `attention_token_level.regenerate` used `wanted_conditions(cli)` not `wanted_conditions_for(ctx)`, so the rerun hint on a v2 cell omitted `neutral_twin` | soft | **fixed** (d134ea48): `regenerate(ctx, ...)` |
| T8 | other baseline smells named by the reviewer (Data Clumps in the v2 view dicts; the length of `_v2_evidence`) | judgement call | left: the views and criteria dicts are the shape the v1 rules already use and the JSON the doc describes; a typed view would change `roles.json` |

## Tests and suites

- Red-then-green: 7 tests for the review fixes, 4 for R27 (plus the fixture change that turned 14 existing v2 tests
  red before R27 and green after).
- Targeted after the fixes: mgnp 206 passed (receiver_category, path_patching_neutral_twin, roles, roles_v2,
  attention_patterns_neutral_twin, attention_token_level, v1_snapshot_02b, component_analysis_v2_cli); base py3.9
  167 passed, 20 skipped. After R27: mgnp 139 passed (roles, roles_v2, v1 snapshot, v2_cli); base 130 passed,
  1 skipped. v1 snapshot byte-identical in both envs at every step.
- Full suites (both envs, at 925417c): exactly the 8 names of `reports/00-baseline-failures.md` and nothing else;
  base 2115 passed / 509 s (`02b-suite-base.txt`), mgnp 2311 passed / 1450 s (`02b-suite-mgnp.txt`). Not re-run after
  the targeted fixes.

## Smoke verdict: PASS

Bridges-2 job 49841165 (`docs/research/mechanism-analysis/jobs/02b-smoke.batch`: 15-head `((Ds-Hs)-(Df&Ds&De))-m`
on sdr_v2 D, `--n-causal 8`, attention `pressure,neutral_twin`, path `both` at `--path-twin-position-threshold
0.01`), GPU-shared h100-80:1, `-t 00:30:00`: COMPLETED in 1273 s (batch ok 807 s, model load 585 s); no error line.
All 15 heads carry the twin attention columns (B2 over 1000 paired instances, 8 of 8 causal twins), the twin path
columns and the receiver category columns. Categories: q 1, kv_clause 4, kv_post_clause 1, kv_unresolved 0, none 9,
no pre-clause flag. B2 positive on 13 of 15 heads; L5H5 0.155 +/- 0.003 and L14H24 0.128 +/- 0.002 read the clause
under D and not under the twin (pressure-reader candidates for phase 2). Caveat: n = 8 keeps the path supports at
the floor (not significant at z = 2); phase 3 runs at n = 104. Ledger reservation `b2-02b-smoke-twin-1` reconciled
under the lock: actual 0.3536 GPU-h, booked 0.5 by the quarter-hour rule; nothing in flight.

## Phase-3 cost numbers (ticket 05)

| quantity | measured |
| --- | --- |
| path forward, position-agnostic, steady state (neutral_twin pass) | 0.0364 s (325 forwards, 11.8 s) |
| path forward, first pass of the job (item_swap, includes warm-up) | 0.0999 s (325 forwards, 32.5 s) |
| Segment-pass forward (neutral_twin at 0.01) | 0.0392 s (94 forwards, 3.7 s) |
| attention forward, pressure + twin both sides, batch 8 | <= 0.057 s (3000 forwards in ~170 s incl. figures) |
| model load | 585 s (476 s on 02a's job) |
| cells selected at 0.01 under the twin | 8 of 307 = 2.6 %; K/V 4 of 188 = 2.1 % |
| cells selected at 0.05 (item_swap) | 0 of 307 (2 cells >= 0.01) |

The steady-state path rate equals the 0.0389 s the dry-run table assumed, so `02b-dryrun-tables.md` stands as the
ticket-05 projection: per task at ticket 03's full C_t, both counterfactuals ~70-91 H100 min, the sweep 9 min, and
the twin Segment pass at f ~ 2.6 % about 9-13 min (per 1 % of K/V cells: far 4.1 / sdr 3.4 / ser 4.8 min), i.e.
about 1.5-2 H100 h per task before the ~10 min model load. The first pass of a job pays ~20 s of warm-up.

## Notes for later tickets

- Ticket 04 (phase 2): v2 job files that lower the twin's position threshold must spell it
  `--path-twin-position-threshold 0.01`; `--path-position-threshold 0.01` would also widen the item-swap pass.
  Roles passes on v2 cells need 83599b5 (R27) or no Component can be a selector.
- Ticket 05 (phase 3): S4 (CLI coverage ids) and S5 (B2 without `readout`) above; the Segment pass's selected share
  on a 4,000-cell grid is the one number the smoke could not measure at scale.
- Three read-only git slips by impl-02b early in the ticket (two `git status`/`git log`, one `git status --short`
  inside an SSH-check line) are recorded in the hand-back; none wrote anything.
