# 02b — hand-back (running record)

Agent impl-02b. Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis`,
branch `mechanism-analysis`, base ddd1da4. Ticket
`/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/issues/02b-neutral-twin-attention-path-patching-and-criteria.md`.

## Progress

- 2026-10-25 — ticket claimed. Orientation done (spec, ticket, 02a/03 hand-backs, roles doc, path_patching,
  attention_patterns, head_table, dataloaders, roles, tests).
- Slips to record: two read-only `git status` / `git log` calls were run from the worktree at the start of
  this session before the "never run git" rule was re-applied, and a third read-only `git status --short`
  (output discarded) slipped into a shell line that checked the Bridges-2 SSH masters after the dry-runs.
  Nothing was changed by any of them. No git otherwise.
- **v1 byte-identity snapshot taken BEFORE any edit** (advisor's order): `tests/test_v1_snapshot_02b.py` runs the
  real CLI on the tiny model over the v1 SDR fixture (attention patterns under the three v1 conditions, path
  patching under `both`, then the roles pass with `--roles-allow-missing-views`) and compares every text output
  under `tests/fixtures/v1_snapshot_02b/` byte for byte after scrubbing the tmp dir, the instance-set digests
  (which hash the dataset path) and the wall-clock fields. Written at ddd1da4 under mgnp, verified twice
  (deterministic); the base env skips the module (nnsight 0.5.12).
- Amendment DRAFT written to `reports/02b-amendment-draft.md` (also the ticket's named path
  `reports/02b-criteria-amendment.md`, same text) and sent to the orchestrator. **Not applied** (R10).

## Dry-run tables

Login dry-runs of the phase-2 cells (spec section 4) on U and of the phase-3 path grids on the provisional C_t, all three tasks, run in-process on 2026-10-25 from the worktree with the 02b code (neutral-twin attention and path patching, `both` resolving to the twin on v2). The tables are also `reports/02b-dryrun-tables.md`; the driver, the grid script, the captured rows and the 21 logs are copied to `reports/02b-dryrun/` (the job tmp dir they ran from is deleted with the job).

### Phase-2 cells on U (123 heads, leaf; 1,000-row split; causal sample n = 100 in 13 batches of 8)

All 21 login dry-runs passed (`reports/02b-dryrun/logs/`, driver `reports/02b-dryrun/dryrun_driver.py`, grids `reports/02b-dryrun/grid_tables.py`). The forward counts are the CLI's own estimates; minutes are at 02a's measured H100 rate of 0.0389 s per forward unless the line says A40 (the attention estimate is the analysis's own eager-forward figure, A40-based).

| task | cell | segmentation | twin | attention_patterns | dla | knockout |
|---|---|---|---|---|---|---|
| far_v2 | P2 (U,D) attention+DLA+families | 1000 instance(s), 19 Segment | on 100 of 100 | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin 1000 instance(s) in 125 batch(es) read 2x, 4250 eager forward(s) ~13 min; total ~27 min A40 | pressure 1000 instance(s) in 125 batch(es); twin 1000 paired instance(s) of 1000 | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); all / item_swap |
| far_v2 | P2 (U,D) segment-resolved twin KO (clause) | 1000 instance(s), 19 Segment | on 100 of 100 |  |  | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); pressure_clause / neutral_twin |
| far_v2 | P2 (U,H) attention+DLA | 1000 instance(s), 19 Segment | n/a: the H split is the twin itself | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| far_v2 | P2 (U,F) attention+DLA | 1000 instance(s), 19 Segment | n/a: no Pressure Clause under nopressure | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| far_v2 | P2 (U,I) attention+DLA (twin) | 210 instance(s), 19 Segment | on 100 of 100 | pressure 210 instance(s) in 27 batch(es), 459 eager forward(s) ~87 s; twin 210 instance(s) in 27 batch(es) read 2x, 918 eager forward(s) ~3 min; total ~4 min A40 | pressure 210 instance(s) in 27 batch(es); twin 210 paired instance(s) of 210 |  |
| sdr_v2 | P2 (U,D) attention+DLA+families | 1000 instance(s), 19 Segment | on 100 of 100 | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin 1000 instance(s) in 125 batch(es) read 2x, 4250 eager forward(s) ~13 min; total ~27 min A40 | pressure 1000 instance(s) in 125 batch(es); twin 1000 paired instance(s) of 1000 | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); all / item_swap |
| sdr_v2 | P2 (U,D) segment-resolved twin KO (clause) | 1000 instance(s), 19 Segment | on 100 of 100 |  |  | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); pressure_clause / neutral_twin |
| sdr_v2 | P2 (U,H) attention+DLA | 1000 instance(s), 19 Segment | n/a: the H split is the twin itself | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| sdr_v2 | P2 (U,F) attention+DLA | 1000 instance(s), 19 Segment | n/a: no Pressure Clause under nopressure | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| sdr_v2 | P2 (U,I) attention+DLA (twin) | 788 instance(s), 19 Segment | on 100 of 100 | pressure 788 instance(s) in 99 batch(es), 1683 eager forward(s) ~5 min; twin 788 instance(s) in 99 batch(es) read 2x, 3366 eager forward(s) ~11 min; total ~16 min A40 | pressure 788 instance(s) in 99 batch(es); twin 788 paired instance(s) of 788 |  |
| ser_v2 | P2 (U,D) attention+DLA+families | 1000 instance(s), 19 Segment | on 100 of 100 | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin 1000 instance(s) in 125 batch(es) read 2x, 4250 eager forward(s) ~13 min; total ~27 min A40 | pressure 1000 instance(s) in 125 batch(es); twin 1000 paired instance(s) of 1000 | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); all / item_swap |
| ser_v2 | P2 (U,D) segment-resolved twin KO (clause) | 1000 instance(s), 19 Segment | on 100 of 100 |  |  | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); pressure_clause / neutral_twin |
| ser_v2 | P2 (U,H) attention+DLA | 1000 instance(s), 19 Segment | n/a: the H split is the twin itself | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| ser_v2 | P2 (U,F) attention+DLA | 1000 instance(s), 19 Segment | n/a: no Pressure Clause under nopressure | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| ser_v2 | P2 (U,I) attention+DLA (twin) | 249 instance(s), 19 Segment | on 100 of 100 | pressure 249 instance(s) in 32 batch(es), 544 eager forward(s) ~2 min; twin 249 instance(s) in 32 batch(es) read 2x, 1088 eager forward(s) ~3 min; total ~5 min A40 | pressure 249 instance(s) in 32 batch(es); twin 249 paired instance(s) of 249 |  |

Notes: (U,H) and (U,F) have no twin by construction (the H split *is* the twin; F has no clause), so their attention and DLA run the `pressure` and `honest_twin` conditions only. (U,I) runs on the inversion stand-in's filtered split (far 210, sdr 788, ser 249 rows) and pairs every row with its twin. The honest-instruction condition is `none` on every v2 cell (no Matched Honest pool, R1). The phase-2 knockout lines use the 02a placeholder family groups file (5 groups); the real family groups come from phase 2 itself.

### Phase-3 path grids on the provisional C_t = core | excl_t | ((D_t - H_t) - core)

`--path-counterfactual both` resolves to `item_swap` + `neutral_twin` on every v2 cell (the dry-run line prints `counterfactual(s): item_swap, neutral_twin`). The twin pairs 100 of 100 sampled instances on each task. The dry-run grid is heads-only (the expression's `- m` strips MLP leaves and no operand names single blocks); the MLP rows below are analytic through `path_patching.build_grid`/`cost` with the same batching.

| task | C_t variant | heads | MLPs | senders | receivers | cells | K/V cells | forwards per counterfactual | H100 min per cf | both cfs | position pass, every cell selected (worst) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | heads only (dry-run) | 47 | 0 | 48 | 110 | 2367 | 1292 | 31,421 | 20.4 | 40.7 | 380,692 fwd = 247 min |
| far_v2 | + 10 placeholder MLPs | 47 | 10 | 58 | 120 | 3224 | 1614 | 42,692 | 27.7 | 55.4 | 482,508 fwd = 313 min |
| far_v2 | + S_k heads (single_k20) + 10 MLPs = ticket 03's C_t | 58 | 10 | 69 | 145 | 4559 | 2312 | 60,190 | 39.0 | 78.0 | 689,624 fwd = 447 min |
| sdr_v2 | heads only (dry-run) | 48 | 0 | 49 | 105 | 2291 | 1168 | 30,446 | 19.7 | 39.5 | 348,088 fwd = 226 min |
| sdr_v2 | + 10 placeholder MLPs | 48 | 10 | 59 | 115 | 3068 | 1400 | 40,677 | 26.4 | 52.7 | 425,594 fwd = 276 min |
| sdr_v2 | + S_k heads (single_k20) + 10 MLPs = ticket 03's C_t | 56 | 10 | 67 | 133 | 4067 | 1910 | 53,768 | 34.9 | 69.7 | 577,538 fwd = 374 min |
| ser_v2 | heads only (dry-run) | 51 | 0 | 52 | 116 | 2793 | 1516 | 37,011 | 24.0 | 48.0 | 447,096 fwd = 290 min |
| ser_v2 | + 10 placeholder MLPs | 51 | 10 | 62 | 126 | 3728 | 1876 | 49,296 | 32.0 | 63.9 | 560,326 fwd = 363 min |
| ser_v2 | + S_k heads (single_k20) + 10 MLPs = ticket 03's C_t | 63 | 10 | 74 | 150 | 5302 | 2684 | 69,914 | 45.3 | 90.7 | 800,826 fwd = 519 min |

- far_v2: placeholder MLP blocks (single_k20 rule, S2p rank, layer 0 never) = layers [4, 6, 7, 8, 9, 11, 13, 14, 15, 16]; S_k adds 11 head(s) beyond the named union.
- sdr_v2: placeholder MLP blocks (single_k20 rule, S2p rank, layer 0 never) = layers [4, 6, 7, 8, 12, 13, 14, 15, 16, 19]; S_k adds 8 head(s) beyond the named union.
- ser_v2: placeholder MLP blocks (single_k20 rule, S2p rank, layer 0 never) = layers [1, 5, 6, 7, 11, 13, 14, 15, 16, 19]; S_k adds 12 head(s) beyond the named union.

Position-specific pass (the receiver category's input): per selected K or V cell 273 forwards (19 Segments + union check, 13 batches), per selected Q/MLP/Readout cell 26 forwards, plus 26 to re-capture the streams. The worst case above assumes every cell is selected. Under R25 decision A the two counterfactuals run at different thresholds: the item-swap pass keeps `--path-position-threshold 0.05` and the neutral-twin pass runs at `--path-twin-position-threshold 0.01` (the receiver category's floor; the flag added in the review fixes so that the item swap is not dragged down with it). The threshold changes nothing but the selected fraction f of the K/V cells, so the cost is tabulated per selected share, at ticket 03's full C_t (third row of each task) and 0.0389 s per forward:

| task | K/V cells at C_t | forwards per 1 % of K/V cells selected | item_swap at 0.05, f = 3 % (v1 grids selected a few percent) | neutral_twin at 0.01, f = 10 % | neutral_twin at 0.01, f = 25 % | neutral_twin at 0.01, f = 100 % (worst) |
|---|---|---|---|---|---|---|
| far_v2 | 2312 | 6,312 fwd = 4.1 min | 12.3 min | 40.9 min | 102 min | 409 min |
| sdr_v2 | 1910 | 5,214 fwd = 3.4 min | 10.1 min | 33.8 min | 85 min | 338 min |
| ser_v2 | 2684 | 7,327 fwd = 4.8 min | 14.3 min | 47.5 min | 119 min | 475 min |

(The Q/MLP/Readout cells add 26 forwards each and the stream re-capture 26 per pass; both are small beside the K/V term and are left out of the per-share column.) Which share clears 0.01 is not knowable before the agnostic pass: the smoke's selected fraction at 0.01 on its 307-cell grid, and its measured path and Segment forward rates on the H100, are the planning numbers ticket 05 reads off this table. If the fraction lands near 25 % the twin's Segment pass alone is 1.4 to 2 H100 h per task, which is the number decision A's "provided the cost fits ticket 05" turns on.

Completeness sweep (dry-run line, item_swap only): 1,057 senders into the Readout, 13,767 forwards per task = 8.9 H100 min.

Per task at ticket 03's full C_t (third row), both counterfactuals plus the sweep and a 10 percent position pass: far_v2 ~132 min; sdr_v2 ~116 min; ser_v2 ~152 min on an H100 before the 8 min model load, if a path forward costs what a knockout forward does. The path forwards capture every sender and run a patched receiver, so the smoke's measured path rate replaces 0.0389 here (it is what the smoke is for).

## Bridges-2 smoke

**HOLDING for the usage reset (2026-10-25, before the submit step).** The orchestrator's push message said usage was
at 77 percent and asked for sync-code + reserve + submit; the pre-step read of `/u/swong2/.claude/usage.json` that
the usage rule requires showed `five_hour.used_percentage = 100` (resets 22:10 CDT), so under that rule the step was
not started. Nothing was synced, reserved or submitted. State at the hold:

- Code is committed and pushed by the orchestrator to origin/mechanism-analysis (on top of 5e266a7); the Bridges-2
  clone has NOT been synced yet. Bridges-2 queue was empty (`b2.sh status`, all jobs COMPLETED, 49830654 included);
  SSH masters for `bridges2` and `b2dtn` were open on this login node. `sync-data -n --what runs` showed only
  mtime-flagged (`<f..t......`) differences on the six v2 runs, i.e. nothing new to copy.
- Smoke job file `docs/research/mechanism-analysis/jobs/02b-smoke.batch` (one line, 15-head `((Ds-Hs)-(Df&Ds&De))-m`
  on sdr_v2 D, n = 8, `--attention-conditions pressure,neutral_twin`, `--path-counterfactual both`,
  `--path-twin-position-threshold 0.01` (was `--path-position-threshold 0.01` before the review fixes; re-dry-run ok after
  the change), suite `mechanism-analysis-02b-smoke-twin`), login `batch --dry-run` ok.
- Source sha256 for the ledger entry are in `tmp/impl02b/smoke_sha.json` (job file dbec76c6..., sbatch 2e504b7a...,
  batch.py 6502da67..., path_patching.py ec75af57..., attention_patterns.py 39db84c4..., receiver_category.py
  7453c97d..., bridges2.env 04fb02e3...); recompute at submit if any of these files change.
- Ledger script `tmp/impl02b/ledger_reserve.py` (lock protocol; `reserve <job_id> <submitted_at> <sha_json>`,
  `reconcile <job_id> <ended_at> <elapsed_s>`; reservation id `b2-02b-smoke-twin-1`, 0.5 GPU-h, 00:30:00).

**Resume sequence (on the orchestrator's resume message):**

1. read usage.json (below 80);
2. `scripts/remote/b2.sh sync-code --branch mechanism-analysis`; check `remote_head` equals origin's head of
   mechanism-analysis (GitHub list_commits on JaMussCraft/Deception-Circuit, or the orchestrator's sha) and the
   clone's `status --short` is clean;
3. `scripts/remote/b2.sh submit --test-only --time 00:30:00 --script scripts/analyze_components.sbatch
   --job-name ma-02b-smoke -- batch docs/research/mechanism-analysis/jobs/02b-smoke.batch
   --timings outputs/_analyses/mechanism-analysis-02b-smoke-timings/timings.json`;
4. ledger reserve under the lock (job id from the real submit; the script takes it after), then the same submit
   without `--test-only`; one message to the orchestrator with the job id;
5. after COMPLETED: `b2.sh fetch`, reconcile from sacct elapsed, record the path-forward and Segment-forward rates
   (`agnostic*.json` and `segments_neutral_twin.json` `cost`), the selected fraction at 0.01, the attention wall,
   the B2 columns and the receiver categories; run `analyze_components.py roles <cell> --roles-allow-missing-views`
   and `receiver-category` on the fetched cell (first v2 roles pass on real columns); re-project the phase-3 table
   with the measured rates, at 0.01 and at 0.05 side by side (R25 A).

**Also pending at the hold (not started, per the orchestrator's instruction):** applying the amendment to
`docs/component-roles.md` (R25 released it; apply on resume, with the dated change-log entry naming it an
orchestrator ruling under the user's standing go), reading the mgnp full-suite result
(`reports/02b-suite-mgnp.txt`; the base result is in: the 8 baseline names only, 2115 passed, 509 s), and the
two code-review reports (received; to be written up in `reports/02b-review.md`). Review findings to act on at
resume: (1) `receiver-category` CLI on a cell whose twin pass was skipped writes category `none` instead of
refusing, so roles would read `twin_paths_measured=True` — make the skipped-file case write nothing / refuse;
(2) `--path-position-threshold` is one flag for both counterfactuals, so at 0.01 the item_swap Segment pass
widens too — cost both in the table and say so to the orchestrator (ticket 05 may want a twin-only threshold);
(3) `print_decisions` tallies `ROLES` only (pressure readers missing from the console count); (4) `lean_of`
counts rule 4b's vacuous `where`; (5) `receiver_category.py` `--floor` flag lacks the analysis prefix and its `q`
docstring says "selector"; (6) stale "There is one" subcommand text in analyze_components.py; (7) tie-break order
between `strongest()` and `_rank_key`; (8) `attention_token_level.regenerate` hint uses `wanted_conditions(cli)`
not `wanted_conditions_for(ctx)`; (9) the hard-coded "0.05 and 2 SE" B2 note in patterns.json.

## Suites

(to come)


## Review fixes applied (2026-10-25, after R25 and the two review reports)

Order and scope set by the orchestrator's resume message. None renames an existing head-table column or JSON key;
the v1 snapshot test is unchanged and green in both envs. Flag changes, both in the standalone surface or additive:

- **New flag `--path-twin-position-threshold`** (path_patching.py `add_arguments`; default unset = the shared
  `--path-position-threshold`). `position_threshold(ctx, counterfactual=ITEM_SWAP)` returns it for `neutral_twin` only;
  `segment_pass` passes its counterfactual. This is R25 decision A made precise: item_swap stays at 0.05, the twin's
  Segment pass runs at the category floor. The smoke batch and `docs/component-roles.md` name the new flag. Phase 3's
  job files must use it (the old spelling would also pull the item-swap pass down to 0.01).
- **Renamed standalone flag** `analyze_components.py receiver-category --floor` -> `--path-category-floor` (the job's
  name for the same number). No job file used the old spelling.
- **Skipped twin pass is refused, never `none`.** `receiver_category.categorize_cell` raises the new
  `TwinPassSkipped` when `agnostic_neutral_twin.json` carries `skipped`; `write` writes nothing (no JSON, no columns, so
  the roles pass reads the category as unmeasured); the CLI exits with the reason. The in-job path was already guarded
  (the run skips `_receiver_categories` when the pass is skipped), so job output is unchanged.
- **Tie-break aligned with `strongest_incoming`.** `_rank_key` is now `-|mean|` alone over the incoming list in grid
  order (head's q receiver, then its group's k and v, senders in run order), which is the stable sort
  `path_patching.strongest` uses, so the category's path and the `strongest_incoming` column name the same cell on a
  tie. Before, a tie between two senders into the same receiver went to the alphabetically smaller sender name
  (`head.10.0` before `head.9.1`). Note text and the doc's tie sentence updated.
- `roles.print_decisions(decisions, variant=V1)` tallies `variant.roles`, so a v2 cell's console shows the pressure
  reader count; `main` passes its variant.
- `attention_token_level.regenerate(ctx, ...)` uses `ap.wanted_conditions_for(ctx)`, so the rerun hint on a v2 cell
  with the default conditions includes `neutral_twin` as the run did.
- Vocabulary and stale text: `SEGMENT_GROUPS` comment ("CONTEXT.md's Segment entry"); receiver_category docstring no
  longer calls the `q` arrival "a selector"; `pressure_reader_signature` docstring says "on a v1 cell ... noted, never
  assigned" and points to rule 4b on v2; attention_patterns' B2 note names `--roles-b2-floor` and `--roles-z` instead
  of hard-coding 0.05 and 2 SE; `analyze_components.py` docstring lists the three subcommands.
- Left as judgement calls (standards review, Fowler baseline): the `Variant` dataclass carrying the v2 columns, the
  `views`/`criteria` dict shapes, `_v2_evidence` length.

Red tests first (7, all failed before the fixes): `tests/test_receiver_category.py` (skipped pass refused + no file
or columns; `--path-category-floor` parses and `--floor` is rejected; sender tie follows list order),
`tests/test_path_patching_neutral_twin.py` (threshold per counterfactual; flag parses, off by default),
`tests/test_roles_v2.py` (v2 console tally), `tests/test_attention_patterns_neutral_twin.py` (v2 rerun hint).

Targeted runs after the fixes, 2026-10-25 evening:

| env | files | result |
|---|---|---|
| mgnp (py3.12) | test_receiver_category, test_path_patching_neutral_twin, test_roles_v2, test_roles, test_attention_patterns_neutral_twin, test_attention_token_level, test_v1_snapshot_02b, test_component_analysis_v2_cli | 206 passed, 259.6 s |
| base (py3.9, BLAS threads pinned) | the same less test_component_analysis_v2_cli | 167 passed, 20 skipped, 49.3 s |

Smoke batch re-dry-run with the new flag: identical plan (15 heads, 16 x 40 = 307 cells, 325 forwards per
counterfactual, 8 of 8 twins); the dry-run suite directory was removed again afterwards.

## Suites (both envs, full, before the review fixes)

Both envs show exactly the 8 names of `reports/00-baseline-failures.md` and nothing else: base 2115 passed / 509 s
(`reports/02b-suite-base.txt`), mgnp 2311 passed / 1450 s (`reports/02b-suite-mgnp.txt`). The review fixes touched
the targeted files above only; the full suites are not re-run for them (the orchestrator may ask).

**State 2026-10-25 late evening:** review fixes applied and reported to the orchestrator with the commit file list; `tmp/impl02b/smoke_sha.json` recomputed for the changed sources (batch 5161f512..., path_patching 088ba000..., attention_patterns 219ede64..., receiver_category 0a79539d...). Waiting for the push message before sync-code, reserve and submit.

## R27 applied (2026-10-25, after the smoke submit)

Found by impl-04 on the first real v2 cell: a v2 DLA pass writes `dla.differential_paired`/`_se` as null and the paired differential in `dla.differential_neutral_twin_paired`/`_se`, but `roles.views_of` read the v1 pair on both variants, so no v2 Component could be a selector and rule 6 differential clause was vacuous. The `v2()` test helper had kept the v1 column filled, which hid it. Fix: `Variant.differential_column`/`differential_se_column` (V1 = the instruction pair, V2 = the twin pair), read in `views_of`; doc columns-table row, rule 4 and 6 sentences, change-log item 5; the fixture now carries what a v2 cell writes (14 existing v2 tests went red on that alone) plus 4 new tests. mgnp 139 passed (roles, roles_v2, v1 snapshot, v2_cli); base 130 passed, 1 skipped; v1 snapshot byte-identical. Files: component_analysis/roles.py, docs/component-roles.md, tests/test_roles_v2.py; sent to the orchestrator as a separate commit. Smoke job 49841165 submitted 22:41 CDT (clone HEAD d134ea48 = origin), ledger reservation b2-02b-smoke-twin-1 written (in flight 0.5 GPU-h).

## Smoke verdict: PASS (job 49841165, 2026-10-26)

Bridges-2 job 49841165 (ma-02b-smoke, GPU-shared h100-80:1, -t 00:30:00) COMPLETED: 1273 s wall (23:41:11 to 00:02:24 ET, node w002); batch status ok in 807.2 s of which model load 584.8 s. Fetched with `b2.sh fetch` into `outputs/_analyses/mechanism-analysis-02b-smoke-twin/dmh__leaf/sdr_v2/` (+ `mechanism-analysis-02b-smoke-timings/timings.json`, log `logs/bridges2/analyze_components_49841165.out`, no error or `!!` line). Ledger: reservation b2-02b-smoke-twin-1 reconciled under the lock (actual 0.3536 GPU-h, booked at the quarter-hour rounding 0.5; in flight 0, reconciled 11.0 GPU-h).

**Present and sane (all 15 heads):** attention twin columns (`attention_patterns.pressure_neutral_twin_paired_top_segment`/`_top_mass`, `neutral_twin_paired_top_segment`/`_top_mass`, `clause_mass_drop_neutral_twin_paired` + `_se`, 1000 paired instances, 8 of 8 causal twins); twin path columns (`path_patching.strongest_incoming_neutral_twin_paired` + support, `strongest_outgoing_neutral_twin_paired` + support, `direct_support_neutral_twin_paired` + `_se`); receiver category + `_path`/`_support`/`_se`/`_segment`. Categories: q 1 (L7H4), kv_clause 4 (L5H4, L5H5, L5H19, L10H31), kv_post_clause 1 (L9H23, item_2_question_option), kv_unresolved 0, none 9; no pre-clause `!!`. B2 drop positive on 13 of 15 heads; largest L5H5 0.155 +/- 0.003 and L14H24 0.128 +/- 0.002 (clause read under D, not under the twin: pressure-reader candidates); L4H13 and L7H4 slightly negative. Caveat: n = 8 for paths, so the category supports sit at the floor (e.g. L5H5 kv_clause support -0.0103 +/- 0.0066, not significant at z = 2); phase 3 runs at n = 104 where that is not the case.

**Measured H100 rates (phase-3 cost basis, replaces the 0.0389 A40 knockout rate):**

| pass | forwards | wall s | s per forward |
|---|---|---|---|
| path agnostic, item_swap (first pass, includes warm-up) | 325 | 32.5 | 0.0999 |
| path agnostic, neutral_twin | 325 | 11.8 | 0.0364 |
| position-specific (Segment) pass, neutral_twin at 0.01 | 94 | 3.7 | 0.0392 |
| attention patterns, pressure + twin both sides (3000 eager forwards, batch 8) | 3000 | ~170 (= 222 s analysis time less ~50 s of path passes, incl. figures) | <= 0.057 |
| model load | - | 585 | - |

**Selected fraction at 0.01 (neutral twin):** 8 of 307 cells = 2.6 %; K/V cells 4 of 188 = 2.1 % (at 0.05: 0 of 307). item_swap at its 0.05 threshold selected 0 of 307 (2 cells >= 0.01). On the dry-run cost table per 1 % of K/V cells selected (far 4.1 / sdr 3.4 / ser 4.8 H100 min), f ~ 2.6 % puts the twin Segment pass at about 9-13 min per task at the full C_t, far below the 25 % case; with the steady-state path rate 0.036-0.039 s per forward equal to the assumed 0.0389, the dry-run table stands as the ticket-05 projection (both counterfactuals + sweep + Segment pass ~ 2-2.6 H100 h per task before the ~10 min model load). The first pass of a job pays a warm-up (0.10 s per forward over 325 forwards here, ~20 s), negligible at phase-3 sizes.

`reports/02b-review.md` deferred to after the weekly usage reset (orchestrator instruction 2026-10-26).

**Closed 2026-10-26:** `reports/02b-review.md` written (both review axes folded in with dispositions, R27, smoke verdict, phase-3 cost numbers); ticket boxes ticked and Status set to resolved. Uncommitted in the code worktree: only the fetched smoke outputs (`outputs/_analyses/mechanism-analysis-02b-smoke-twin/`, `outputs/_analyses/mechanism-analysis-02b-smoke-timings/`) and the job log `logs/bridges2/analyze_components_49841165.out`; every code, doc and test change is pushed (d134ea48, 83599b5).
