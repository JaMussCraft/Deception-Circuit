# Ticket 05 review: spec and standards

Two independent read-only reviews, spawned by impl-05 on 2026-10-26 (model opus, one per axis). Each was briefed with
the ticket, the spec sections, the code, the raw cells and the deliverables, not with the reading's conclusions.
Neither found a blocker, and neither moves a pre-registered call. Every finding below has a disposition. Fixes were
made test-first: 60 tests pass in both environments (`tests/test_mechanism_analysis_p3.py`,
`tests/test_receiver_category.py`). The results, the curated tables and the reading were rebuilt afterwards.

## Spec review

Verdict: far and ser stay A′-clause-reader, and B-selector stays refuted on its second clause. The reviewer
recomputed the A′ shares independently from the agnostic and segments files and the phase-1 S2p mean drops, with
zero category mismatches (far kv_clause 0.738; sdr q 0.638; ser kv_clause 0.835).

| # | severity | finding | disposition |
|---|---|---|---|
| 1 | should-fix | sdr (R-AB reading B) carried the sub-reading "A'-selector" in the results, JSON and curated tables; §2.3 names sub-readings for A′ tasks only | **Fixed.** A non-A′ task now gets `sub_reading = "descriptive: <call>-dominated"` and the shape in `shape` (`p3_results.task_results`; test `test_a_b_task_gets_a_descriptive_label_not_a_sub_reading`) |
| 2 | should-fix | K/V cells read kv_unresolved have top Segment `unsegmented`. Those template tokens are pre- or post-clause, and pre-clause positions carry nothing, so the weight is post-clause. B4's post-clause K/V share is 16.5 / 44.1 / 20.7 %, not 3 / 4 / 8 %; sdr's L15H8 and L15H11 read L14H5 through V there (mover-shaped) | **Fixed (wording and a B4 column).** `p3_logic.entry_points` places an `unsegmented` K/V split as `post_clause_unsegmented`, with its own column in the results (test `test_unsegmented_kv_arrivals_are_post_clause_by_construction`). The pre-registered receiver category is unchanged (R25's categoriser). The reading's B4 section, the verdicts table and the sdr paragraph were rewritten. The reading also states that placing those heads as post-clause moves no call |
| 3 | should-fix | Role counts included the rows the completeness sweep appended outside C_t (unknown 57 / 63 / 75 vs 55 / 59 / 71 for C_t) | **Fixed.** Results carry `roles.counts_C_t` and `roles.outside_C_t`, and the markdown and the reading show C_t-only counts with the appended rows listed apart (test `test_role_counts_are_over_c_t_with_the_sweep_rows_apart`) |
| 4 | nit | The before/after paragraph named only L17H24; it omitted L24H27 as a selector (sdr) and L14H4 (sdr) and L17H26 (ser) as binders | **Fixed** in reading §5 |
| 5 | nit | "L7-13" excluded ser's kv_clause L14H24 | **Fixed** ("L7-14") |
| 6 | nit | "C_t's heads act through them" is inference; the reading did not say that (c) is a joint total-effect knockout while the sweep sums single direct effects with cancellation | **Fixed** in reading §4 (labelled EXPLORATORY; the absolute against signed sums and the negative mlp.30 are stated) |
| 7 | nit | Decision 2 should say "Q-category": only L17H24 holds the selector role, and L17H26 is a binder on ser | **Fixed** |
| 8 | nit | sdr statements that something is absent rest on C_t paths with (c) = 0.297 | **Fixed**: caveat added beside the 0.02-floor one (§1, decision 3) |
| 9 | nit | Ledger wording: 8.5 GPU-h reserved by walltime, 7.25 charged | **Fixed** in the reading header |
| 10 | nit | `05-review.md` not yet written | **Done** (this file) |

Checks the reviewer reported as passing:
- **A′ rule.** The A′ inputs and rule are right: MLP members counted, S_k equal to the phase-1 groups, the path sample
  equal to the S2p sample, the > 50 % rule, and the routing gate on mover and unresolved only.
- **Robustness.** The re-readings reproduce.
- **sdr.** It is treated as descriptive.
- **B-selector.** Both clauses are read with KV group 6 as one test. Refuting the conjunction is correct.
- **Positions.** The 1C and sweep position claim is verified (`after=pressure_clause,exclude=readout` on all 9 1C
  lines).
- **R14 for sdr.** It is handled correctly.
- **Roles.** The rule-4b roles, lost lists and cross-task counts reproduce.
- **Figures.** The B4, completeness and job figures match.

## Standards review

Verdict: no blockers. On the real phase-3 cells every input that the gaps below concern is present, so the delivered
readings were not wrong. Tests passed in both environments before the fixes and pass after them.

| # | severity | finding | disposition |
|---|---|---|---|
| 1 | should-fix | Silent fallbacks: a missing twin segments file reads every K/V path as `no_split`; a missing L17 or core-L24 category reads "not q"; sweep senders with a None mean drop out unseen; `"category": None` passes `adjudicate` | **Fixed.** The twin segments file is now required (FileNotFoundError). `b_selector` raises on any L17H24-27 or core-L24 head without a category. `completeness` reports `unmeasured_inside` and `unmeasured_outside`. `adjudicate` refuses any category outside the five. Tests: `test_results_refuse_a_missing_twin_segment_pass`, `test_b_selector_refuses_a_missing_l17_or_core_l24_category`, `test_completeness_counts_unmeasured_senders_and_drops_the_direct_sum_ratio`, `test_adjudicate_refuses_a_head_whose_category_is_null` |
| 2 | should-fix | `outside_share_of_signed_total` divided by the sum of direct paths, not the gap, unguarded near zero | **Fixed.** Dropped. The signed sums are already shares of the gap, and the columns now say so |
| 3 | should-fix | Raw path means were read as signs without checking ADR-0002's convention marker | **Fixed.** `require_convention` refuses any twin agnostic, sweep or item-swap agnostic file whose `metric.convention` is not `positive_helps_deception` (test `test_results_refuse_a_legacy_sign_file`) |
| 4 | should-fix | A kv_unresolved majority printed `**None**` and its note reached only the JSON; all-negative weights gave a misleading note | **Fixed.** The markdown prints "needs a researcher ruling" and every non-empty call note. Zero total weight has its own note (test `test_no_positive_weight_has_its_own_note`) |
| 5 | should-fix | `p3_roles.py` was untested, and its retry with `--roles-allow-missing-views` fired on any SystemExit | **Fixed.** The retry fires only on the CLI's missing-view refusal (`has no column at all for`) and prints a DOWNGRADE line. Any other refusal or non-zero exit is a failure. Tests `test_roles_argv_merges_the_three_sources_in_order` and `test_roles_retry_only_on_the_missing_view_refusal` |
| 6 | should-fix (low) | `--tasks` subset would compute cross-task outputs on the subset and leave curated files stale | **Fixed.** `p3_results.main` refuses anything but all three tasks (test `test_the_report_refuses_a_task_subset`) |
| 7 | should-fix | `receiver_category` (a8a9b63): the head-table coverage uses the measured ids, but the category JSON's `sample.n_instances` still counts the used ids, so the two disagree when the gap excludes instances | **Deferred.** No instance was excluded by the gap in phase 3 (0 on every task), so every delivered number agrees. The fix belongs to 02b's module and its tests. Recorded for the orchestrator as a follow-up: compute the measured ids once in `categorize_cell` and pass them to both payload and write |
| 8 | should-fix | `same_role` was True when every task's role was None | **Fixed.** None is not comparable (test `test_same_role_is_not_claimed_when_no_role_was_proposed`) |
| 9 | should-fix | Tests: the no-row-added merge test would pass for an identity restriction; floor_x2 dropped the same head as positive_path_only | **Fixed.** Added the unrestricted-merge control (2 rows) and `test_a_positive_path_under_twice_the_floor_drops_only_at_floor_x2` |
| 10 | nit | Hard-coded "n = 100, seed 0" | **Fixed.** n is read from the cells; the seed is named as the default causal sample's |
| 11 | nit | A local `top` was a function, then rebound to a string | **Fixed** (`call_text`, `top_out`) |
| 12 | nit | Hard-coded role list | **Fixed.** It is ordered from `roles.ROLES_V2` |
| 13 | nit | Duplication: `_sha256` in five launch modules; `p3_merge.build_ko` copies `p2_merge`'s loop; `p3_logic.incoming` reimplements `receiver_category.incoming_receivers` | **Deferred.** It follows the sibling builders' pattern, and a shared-helper refactor across launch modules is outside the ticket |
| 14 | nit | Pointless `role_rows` copy; dead `outside_C_t` branch in `cross_task_roles`; sdr printed a bold A'-selector | **Fixed** the copy and the sdr label (finding 1). The `outside_C_t` branch is kept as a guard: the table is C_t-only today, and the branch keeps `n_tasks_in_C_t` honest if that changes |

## Not changed by the reviews

The four pre-registered results are unchanged: far and ser A′-clause-reader; B-selector clause 1 holds and clause 2
fails; completeness 0.80 / 0.81 / 0.77; and the R14 recommendation for sdr (do not run).
