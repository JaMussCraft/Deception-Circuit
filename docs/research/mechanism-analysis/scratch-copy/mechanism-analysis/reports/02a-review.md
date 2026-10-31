# 02a review (impl-02ar, 2026-10-25)

Both axes done by hand by impl-02ar. The previous agent stalled spawning review sub-agents, so none were spawned.
Scope: every 02a file in the worktree. Each was diffed against the main checkout, which is the branch base for these
files. Read against the ticket's checkboxes, its R19 Comments, spec §2 / §9 (R1, R7, R11, R12, R16, R19), review-00
B1-B3 and Pile 2 items 2-5 and 13, and the brief's design rules.

Severity: **hard** = breaks a binding rule or a test of record (fixed before hand-back); **soft** = worth fixing or
stating, not binding; **note** = recorded for later tickets.

## Spec axis

| # | item | verdict | evidence |
| --- | --- | --- | --- |
| S1 | v2 ids in loaders, segmentation, knockout, DLA; never skipped silently | holds | `dataloaders.V2_TASKS` in `MECHANISM_TASKS`; `analyze_components.py` refuses an unsegmentable mechanism task by name (test `..._cli.py::test_a_mechanism_task_that_cannot_be_segmented_is_refused_not_skipped`) |
| S2 | v1 segmentation byte-identical (snapshot) | holds, independently verified | `tmp/impl02ar/verify_v1_snapshot.py` recomputed far/sdr/ser digests with the UNMODIFIED main-checkout segmenter: equal to the fixture (1000 rows each) |
| S3 | v2 scheme with `response_line` carved from `question` | holds | `segmentation.MECHANISM_V2_SEGMENTS`; tests in `..._segmentation.py` |
| S4 | `response_line` in the `frame` group | **handed to 02b** | `roles.SEGMENT_GROUPS` has no entry. R7 puts "the `response_line` Segment in `frame`" inside the criteria amendment that R10 lets the user veto until 02b applies it. Adding it here would pre-apply a gated criteria change. Until 02b, a v2 read on `response_line` is `unestablished`, and no v2 roles pass runs before 02b anyway |
| S5 | `neutral_twin` paired kind: id join, kind and `pressure_id` asserted, `assert_clause_aligned_pair` on both streams, D's labels, span recorded | holds | `dataloaders._neutral_twins_by_id`; refusal tests for wrong kind, wrong `pressure_id` and misalignment |
| S6 | twin from `<t>_v2_honest`, never `neutral_prompt` (R16 trap) | holds | `..._dataloaders.py::test_the_twin_is_the_honest_split_row_and_never_the_neutral_prompt_column` compares token ids with the H row and against the `neutral_prompt` column |
| S7 | dry-run reports n paired (100/100 causal, 1000/1000 descriptive) | holds | `02a-dryrun-tables.md`; test `test_the_whole_split_pairs_one_thousand_of_one_thousand` |
| S8 | held-out exclusion; no option = byte-identical draw | holds, independently verified | `tmp/impl02ar/verify_sample_snapshot.py`: the golden file reproduces from the unmodified `draw_sample` on 8 of 8 task/seed keys |
| S9 | R19(3) `--include-ids` | holds | `sampling.draw_sample(include_ids=)`; CLI flag; `test_an_inclusion_file_fixes_the_sample`; exclusion wins over inclusion (stated and tested) |
| S10 | `--knockout-scheme` mean with the evaluator's semantics, zero | holds | `collect_mean_bank` follows `evaluation/ablation.py` `MeanCollector`: per site, unpadded positions of both streams pooled, fp32 sums / token count. Hand-computed-mean test on the tiny model |
| S11 | `--knockout-counterfactual {item_swap, neutral_twin}` | holds | copies from the twin's CLEAN prompt with D's labels; identical-streams test gives zero drop |
| S12 | positions incl. `after=pressure_clause,exclude=readout` | holds | `parse_positions` / `position_mask`; the range is `max(clause token) + 1 .. readout - 1` per row; model test against a hand mask; pre-clause twin knockout exactly 0 (test) |
| S13 | `--knockout-groups` JSON `{name: [[kind, layer, index]]}`, joint | holds | `load_groups` / `check_groups`; joint test against `replace_forward` |
| S14 | greedy in-process, layer-0 MLP out of the pool, order + joint drop per step | holds | `greedy_pool` / `greedy_select`; scripted-table tests; CLI test |
| S15 | sweep can exclude named Components from ranking | holds | `--knockout-sweep-exclude`; rank None, never flagged, numbers kept (test) |
| S16 | `knockout.json` / `sweep.json` record every choice | holds | `plan` block (scheme, counterfactual, positions, column suffix) on v2 / non-default plans; non-default plans write suffixed head-table columns, so no neutral-twin drop can be read as an item-swap one |
| S17 | R19(1) per-instance clean / knocked / twin margins for every group knockout and sweep | **fixed** | before: sidecars carried clean, knocked and the counterfactual stream's margin; the twin's own margin only under a neutral-twin plan; the family pass wrote none. Now `Effects.neutral_twin_logit_difference` is filled under every plan when a batch carries a twin, and the family pass writes `knockout_families_instances.json`. Tests added |
| S18 | DLA neutral-twin paired condition, `_neutral_twin_paired` columns, coverage meta | holds | `measure_paired_neutral_twin`; `TWIN_COLUMN_SOURCES`; `PAIRED_NEUTRAL_TWIN` instance set; v1 cells gain no column (test) |
| S19 | lens crossing: first layer in 8..28 with margin < -0.5, final sign, last sign change, `dla/logit_lens.json` | holds | `lens_crossing` / `lens_crossing_summary` (v2 cells only); each condition read in the deception direction; unit tests incl. the boundary -0.5 and layer 29 |
| S20 | clause-form table, act-naming checked first (R19) | holds | `clause_forms.clause_form` checks the act patterns first; table committed at fc9e614 |
| S21 | login dry-runs of 1B and 1C | holds (impl-02a) | 48 of 48 exit 0, `02a-dryrun-tables.md`; I on a fixture (ticket 08 not built) |
| S22 | Bridges-2 smoke, drift, cost basis, ledger | open | needs ticket 01 committed and the branch pushed (R3); job plan in the hand-back |

## Standards axis

| # | finding | severity | disposition |
| --- | --- | --- | --- |
| T1 | v1 `knockout.json`, `sweep.json` and `knockout_families.json` gained `plan`, `target_direction`, `counterfactual_run` and `unpaired_instance_ids` under the default plan. The brief requires v1 behaviour to stay byte-identical | hard | fixed: `payload(record_plan=)` writes them only for a v2 cell or a non-default plan (`records_more`, or a sweep exclusion). `test_the_default_plan_writes_v1s_keys_sign_and_ablation_sentence` pins v1's key set, sign sentence and ablation sentence by hand |
| T2 | on H and F cells the v1 sign sentence ("positive helps deception") is wrong: the Target is the honest item there (ADR-0002, spec §2.2) | soft | fixed with T1: a recorded plan states the sign in the cell's target direction and names `target_direction` |
| T3 | `tests/test_knockout.py`, `tests/test_knockout_model.py`, `tests/test_knockout_families_model.py` were attributed to ticket 01 | hard (commit list) | they test `component_analysis.knockout` and only flip "mean/zero refused" to "built". 02a's code change forces them. On 02a's commit list |
| T4 | unused imports in three new test files | soft | fixed (ruff F401). Remaining pyflakes hits in 02a files are the repo's fixture re-import idiom (F811) and pre-existing string annotations in `dla.py` / `registry.py`, both present on main |
| T4b | two of impl-02a's DLA CLI tests were red on mgnp (`..._cli_model.py::test_dla_measures_the_neutral_twin_pair_and_the_lens_crossing`, `::test_dla_on_a_nopressure_cell_reads_the_crossing_in_the_deception_direction`): they expected 40 rows, the fixture's `test_samples`, but DLA's descriptive loaders read the whole 1,000-row split, as on v1 and as the spec's "1,000 paired rows" wants | hard (red tests) | fixed in the tests (`WHOLE_SPLIT = 1000`); the code was right. Both pass |
| T5 | nnsight imported inside functions only (ADR-0001) | holds | no module-level nnsight import added |
| T6 | v1 code paths: default plan runs the forwards v1 ran (test); v1 loader report gains no key (test); v1 DLA conditions and columns unchanged (tests) | holds | |
| T7 | under the mean scheme every swept key's `[n, seq, dim]` fill is built per batch | note | about 0.6 GB per batch on the 8B model at batch 8; fine on an h100-80 |
| T8 | non-twin plans on D / I cells now run one more forward per batch (the twin's own margin, S17) | note | about 0.1% of a sweep (13 of 13,754 forwards); the dry-run estimate does not count it |

## Notes for later tickets (not 02a defects)

- **Which S2p ranking feeds the selectors (ticket 03).** `greedy_pool` takes the top N by SIGNED `mean_drop`:
  a mediator removes the deceptive margin, so a large negative drop is not one. `sweep.json`'s `rank` is by |drop|
  (v1 convention). Its `signed_rank` is the signed order. The single selector's `S_k` should be read from
  `signed_rank` (layer-0 MLP excluded) so both selectors rank the same way. Ticket 03 decides and states it.
- **Response-line group.** 02b adds `"response_line": "frame"` to `roles.SEGMENT_GROUPS` with the amendment (S4).
- **I condition.** Loader and binding are fixture-tested only; the first real I dry-run comes after ticket 08 builds
  `<t>_v2_inversion`.

## Verdict

No open hard finding. Ticket 02a's CPU scope passes on both axes after the fixes above. Full suites after the
fixes: mgnp shows exactly the 8 baseline failures. Base shows the 8 plus 3 in ticket 01's
`test_mechanism_analysis_infra.py`, where ticket 01 is still editing `b2.sh`. Details are in `02a-handback.md`.
A further fix outside the axes: `batch --timings` now creates its directory (test-first). The Bridges-2 smoke and drift
control (S22) remain, gated on ticket 01's commit and the branch push.
