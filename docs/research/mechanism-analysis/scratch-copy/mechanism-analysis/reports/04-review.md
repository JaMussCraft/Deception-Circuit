# Ticket 04 review (phase 2)

Two reviewers ran on impl-04's first build at 13:42 and 13:50 CDT on 2026-10-26: a standards review and a spec review.
Their full texts were lost with impl-04's session. The findings below are the orchestrator's list of them (its message
to impl-04o, items (a)-(l)) and the RESUME.md summaries. impl-04 applied part of them before the session ended;
impl-04o finished the rest on 2026-10-26 afternoon and did its own review of the final diff (both axes, by hand; no
reviewer sub-agents were spawned, to keep usage down after the session restart).

Files: `outputs/_launch_mechanism_analysis/p2_results.py`, `p2_roles.py`, `p2_jobs.py`, `p2_merge.py`,
`tests/test_mechanism_analysis_p2.py`, `reports/04-phase2-results.{md,json}`, `reports/04-phase2-reading.md`.

## Standards review (13:42)

| # | finding | disposition |
|---|---|---|
| (a) | `c_honest` divided the unpaired `dla.pressure` by the paired `dla.neutral_twin_paired`: two different instance sets | **Fixed** by impl-04 in `p2_results.py` (`c_honest` reads `dla.pressure_neutral_twin_paired` against `dla.neutral_twin_paired`); test `test_c_honest_reads_the_late_h_minus_d_heads_in_the_honest_direction` gives the two pressure columns different values |
| (b) | The H/F sign sentence cited ADR-0002; the sign comes from each cell's `target_direction` | **Fixed**: results markdown by impl-04 (`markdown()` header); the reading's sign paragraph by impl-04o. Follow-up by impl-04o: the first fix named knockout.json, which no phase-2 cell has; both now name `knockout/groups.json` (deceptive on D and I, honest on H and F) and say the DLA's fixed "deceptive" metric text is honest-positive on H and F (it reads the same target/distractor fields, direction_sign 1; the far H cell's whole-model margin is +7.2) |
| (c) | `p2_jobs.py` ignored `--groups-dir` (job lines always named the default directory) | **Fixed** by impl-04 in `p2_jobs.main`; impl-04o added `test_main_writes_the_groups_dir_it_was_given_into_the_job_lines` and `test_committed_job_files_are_what_the_generator_writes_by_default` (the committed job files still equal the generator's default output) |
| (d) | `p2_roles.py` docstring said "without the where-clause"; in CONTEXT.md's vocabulary path patching is "what it depends on" | **Fixed** by impl-04 (docstring); `MERGE` renamed `HEAD_CELLS`, unused `p2_jobs` import dropped. The reading uses the same wording (section 6) |
| (e) | Column-name constants should come from `roles` and friends; the comment "taken from the roles pass so they cannot drift" was false for the twin DLA columns | **Fixed**: impl-04 took `DLA_DIFF_TWIN(_SE)` from `roles.DLA_DIFFERENTIAL_TWIN(_SE)` and replaced the comment; impl-04o builds the two remaining names from `component_analysis/dla.py`'s `TWIN_COLUMN_SOURCES` (`_twin_dla_column`, which raises on an unknown name); test `test_twin_dla_column_names_are_the_dla_analysis_own_names` |

## Spec review (13:50)

Nothing blocked. Presentation and reading fixes:

| # | finding | disposition |
|---|---|---|
| (f) | Split the B-reader headline into the binomial clause and the named-heads clause | **Fixed**: results markdown (impl-04) gives clauses (i) and (ii) per task; the reading's verdict table grades them apart: (i) holds 3/3, (ii) holds on sdr only (L13H5 0.021 far, 0.037 ser, under the 0.05 floor) |
| (g) | Drop `unestablished` from the C-reads Fisher table (it is the absence of a group in docs/component-roles.md); keep the sink-free re-read exploratory; state the verdict on the faithful table | **Fixed**: impl-04 changed `c_reads` (unestablished counted beside the table, not in it; p 0.65 became 0.58); impl-04o's reading states the verdict on that table (fails), says it has almost no power (12 of 32 heads, all but one "frame"), and labels the sink-free p 0.15 exploratory |
| (h) | C-honest must count "suppressed" (>= 50 % smaller, same sign) apart from "flipped" (sign change) | **Fixed** by impl-04 (`suppressed`, `flipped`, `reduced_at_least_half`; test). impl-04o added `holds` (both clauses of C-honest on one head) and grades the prediction per head on it: 9/12, 5/7, 7/8; 0 suppressed, every reduction a flip |
| (i) | Family-level R-cls is descriptive; grade the pre-registered per-head R-cls prediction on per-head classes | **Fixed**: impl-04 labelled the family column descriptive in the markdown; impl-04o's markdown quotes phase 1's per-head grading (`03-phase1-results.json` rqa) and the reading defers to it. The first reading had graded "core is answer machinery: held" from family R-cls, against phase 1's per-head verdict (refuted on far and ser) |
| (j) | Surface the per-layer clause-mass table, the check_cell results and the D-H heads' reads table | **Fixed**: clause mass and C2 tables by impl-04; impl-04o added the check_cell table per head cell (`cell_check`, test) and widened C2 from (D-H)-core to every D-H head with a core column, so far's 11 core heads in D-H are shown too |
| (k) | Keep the unrequested extras (d_twinko, the I-cell family knockout, b_reader_I, sink-free C-reads) but mark them exploratory | **Fixed**: impl-04 marked d_twinko, I families and the sink-free C-reads; impl-04o added an `EXPLORATORY` list to the markdown header, the results JSON and `p2_readings.json`, and surfaced `b_reader_I` in the markdown as exploratory |
| (l) | Tone the reading's section 4 down to what the descriptive S7-type overlap supports; "instructed inversion" rests on phase 1's R-inv | **Fixed** in the reading (section 4): the I-vs-D overlap is described as consistent with phase 1's R-inv, which is the claim of record |

## impl-04o's own review of the final diff

Spec axis:

- **The first reading re-adjudicated two phase-1 verdicts** (core answer machinery "held"; C-confound "far's D-H reading survives") from family knockouts, which are not the pre-registered rules for either. Fixed: the reading's verdict table lists phase 1's verdicts as standing and explains why the family numbers are compatible with C-confound refuted (removing the core keeps two thirds of the D drop and none of the H/F cost, yet R-A1 set 6 and the held-out f_D 0.105 show that remainder neither flips the answer nor mediates the pressure).
- **The first reading was stale** against the 13:54 rebuild (C-reads p 0.65 vs 0.58; one C-honest column instead of suppressed/flipped). Rewritten from the current JSON; every number was checked against `reports/04-phase2-results.json`.
- **A redundant exploratory table** (C-reads on `pressure_neutral_twin_paired_top_segment`) duplicated the faithful table exactly: that column is the pressure side of the twin pairing over the whole split. Removed from the builder.
- **Phase-3 cost**: ser's walltime at x1.5 (about 3.25 h) exceeds the spec's 2.75 h per-task reserve. The three together (8.5 h) fit the 9.25 GPU-h allocation. Flagged for ticket 05; no cap raise.

Standards axis:

- `cell_check` was called with a repo-relative path, so a run from another directory would report every view missing. Now passed the absolute path; rebuilt from the scratch directory with the same table.
- The module docstring listed the old C-honest rule; updated with the new readings.
- No v1 behaviour or shared module was touched; changes stay in the ticket's own launch scripts and test file.

Left as is:

- The roles pass and the merge tables were not rerun: none of the fixes changes their inputs or code paths that write them.
- The base-env full suite was impl-04's run (8 baseline failure names, 2147 passed), from before today's reviewer fixes. The fixes touch only `p2_*` and their test file, which pass in both envs.

## check_cell (scripts/check_cell.py on the 12 head cells)

No BROKEN view on any cell. Per cell (d, h, f, i on each task): present = head table, attention patterns, attention top
heads, dla, dla heatmap, logit lens, segmentation, sample. Missing = the analyses phase 2 does not run: dla paired
scatter (the honest-instruction condition, not run on v2), knockout (single Component; phase 1), family knockout (the
role-family pass; the composition-set groups pass writes `knockout/groups.json` instead), knockout sweep (phase 1),
path patching and completeness sweep (phase 3). Table: `reports/04-phase2-results.md`, one per task.

## Tests

| run | result |
|---|---|
| `tests/test_mechanism_analysis_p2.py`, mgnp | 27 passed |
| `tests/test_mechanism_analysis_p2.py`, base (thread pins) | 27 passed |
| full suite, base (impl-04, Progress 4) | 8 failed = the 8 baseline names, 2147 passed, 66 skipped |
| full suite, mgnp (impl-04o) | 8 failed = the 8 baseline names of 00-baseline-failures.md, by name; 2347 passed, 19 skipped (1420 s). It started before the last p2_results edits (abspath, docstring, table removal, sign text, two p2_jobs tests); the ticket file was rerun after them, 27 passed in both envs |
