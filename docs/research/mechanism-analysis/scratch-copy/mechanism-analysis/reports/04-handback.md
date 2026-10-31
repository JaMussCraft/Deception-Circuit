# 04 hand-back (impl-04): running record

Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis`, branch
`mechanism-analysis` (built against HEAD 925417c; impl-02b's amendment is live in the shared tree). No git run by this
agent. Scratch: `/u/swong2/.claude/jobs/1c836bb8/tmp/impl04/`.

## Status

**claimed** (2026-10-25). Orientation done: brief, spec (§2, §4 phase 2, §9 R1/R7/R10/R16/R19/R25/R26), ticket,
phase-1 reading and 1C results, 02a/02b hand-backs and dry-run tables, the amendment (applied in
`docs/component-roles.md`), the CLI, `roles.py`, `components.py`, `algebra.py`, the operand recipe, the p1b/p1c
generators, the cell of record.

## Design (before any code)

- **U' per task (R26)** = `((Df|Hf|Ds|Hs|De|He)-m) | X_t` at leaf, where `X_t` is a new operand run dir
  `outputs/_launch_mechanism_analysis/operands/skct_<t>/` (same recipe as `build_allmlp.py`: the far D run's mask
  keys; the deciding `S_k`'s heads open with every neuron; the ten `C_t` MLP blocks open with every unit; everything
  else closed). `S_k` and `C_t` come from `docs/research/mechanism-analysis/phase1/p1c_readings.json` (deciding set
  members; `routing.<t>.C_t_mlps`). `S_k`'s own MLPs are among the ten by construction (checked). Operands must share
  mask keys (`evaluation/algebra._operand_keys`), so a compact operand is not possible; one operand per task.
- **Membership**: the six atomic runs as `--reference`, plus `--reference x_<t>=<operand>`; core, excl_t, D_t-H_t,
  (D_t-H_t)-core, H_t-D_t, late H-D (layers 18/22/30), U, S_k, C_t derived on CPU and written as `membership.*`
  columns into each cell's head table and into the curated CSVs.
- **Cells per task, one job, one model load**: (U',D) attention (pressure, neutral twin paired, honest twin
  descriptive) + DLA + composition-set family knockout (item swap, all positions); (U',D) family knockout under the
  twin post-clause; segment-resolved neutral-twin knockout of the S2p top 20 (singletons + joint), one line per
  Segment, pre-clause Segments as the zero assertion; (U',H), (U',F) attention + DLA + family knockout (item swap;
  sign = supports the honest answer); (U',I) attention + DLA paired with the twin + family knockout under the twin.
- **Roles pass (CPU, after fetch)**: `roles <cell> --roles-merge-from <sweep tables> --roles-allow-missing-views`,
  where the sweep tables are head tables rebuilt on CPU from the phase-1 `sweep.json` files (S1 and S2p for D, S5
  for H, S6 for F, S7 for I) so that the `S_k` heads outside U get their knockout columns too.
- **Readings**: C-reads (Fisher exact RxC, own implementation checked against scipy where available), B-reader
  (one-sided binomial against 10/32), C-honest (late H-D heads' DLA on H/F and pressure vs twin on D), RQ-A's
  component part, the I-vs-D comparison per deciding-set head, families, segments, roles counts, proposed `C_t` with
  the path-patching `--dry-run` cost on the real operand-backed `C_t`.
- **Cost**: estimate about 35-40 min per task job on an H100 (02a rates), `--time 01:00:00` each, 3.0 of 3.5 GPU-h.

(Progress sections are appended below as work lands.)

## Progress 1 (2026-10-25, late evening): operands, groups, job files, login dry-runs, builders

Design changes against the section above:
- The D cell's attention runs `pressure, neutral_twin` only (the honest-twin descriptive condition is the H cell's
  job; about 2.5 min saved per task).
- The roles pass merges straight from the phase-1 single-knockout cells (`outputs/_analyses/mechanism-analysis-p1/
  {s1,s2p}|s5|s6|s7/U__leaf/<t>_v2`, which carry exactly the columns `roles.py` reads, verified) instead of tables
  rebuilt from `sweep.json`. Consequence: the `S_k` heads outside U (far 13, sdr 3, ser 11) have no single-knockout
  column and get `unknown/insufficient` on the "depends, whether" view; their group-level evidence is phase 1C's.
  Rehearsed with `--dry-run` on the 02a DLA smoke cell (v2 variant detected, two merges accepted, missing views named).
- The criteria gap I reported (v2 DLA differential column) is closed by impl-02b as R27 in `roles.py`
  (`Variant.differential_column`), so the roles pass runs under the amended criteria as planned.
- `--roles-allow-missing-views` is required on every phase-2 cell (no path patching before phase 3); roles.json
  records the missing view and every role here is read "without the where-clause".

Built (all tests green, mgnp, `tests/test_mechanism_analysis_p2.py`, 19 tests):
- `outputs/_launch_mechanism_analysis/p2_operands.py` -> `operands/skct_{far,sdr,ser}/` (provenance pinned to
  `p1c_readings.json` sha256 c94a210c...). U' = far 136 heads + 10 MLPs (146), sdr 126 + 10 (136), ser 134 + 10 (144).
- `p2_jobs.py` -> `docs/research/mechanism-analysis/phase2/groups/{<t>_families,<t>_top20,meta}.json` and
  `docs/research/mechanism-analysis/jobs/04-p2-<t>.batch` (23 lines each: d, d_twinko, h, f, i, 18 seg_<Segment>).
  Family sizes: far core 31 / excl 8 / D-H 26 / (D-H)-core 15 / H-D 28 / late H-D 12; sdr 31/14/21/15/19/7;
  ser 31/10/19/19/33/8 (ser's D-H holds no core head, R21). No empty family.
- `p2_roles.py` (the 12 roles commands), `p2_results.py` (membership, Freeman-Halton exact test and binomial upper
  tail by hand, C-reads, B-reader, C-honest, I-vs-D, family table with R-cls at family level, segment matrix with the
  pre-clause exact-zero check, C_t proposal, curated CSV/JSON writers, markdown). Loaders rehearsed on phase-1 cells.
- Proposed C_t sizes from the rule alone (phase-2 data may still move the MLP list): far 62 heads + 10 MLPs = 72,
  sdr 56 + 10 = 66, ser 68 + 10 = 78 (spec: 55-80). The MLP sets equal the operands' C_t sets.

Login `batch --dry-run` of the three job files: 23/23 ok per task (far 2 min 50 s, sdr 2 min 55 s, ser 2 min 50 s
wall). Estimates per task job (the CLI's A40 attention rate; H100 about 4-5x faster):

| cell | far | sdr | ser |
|---|---|---|---|
| d attention (pressure + twin x2) | 3 x 2,125 eager fwd (~21 min A40) | same | same |
| d DLA | 125 + 2 x 125 batches | same | same |
| d / d_twinko families | 6 groups, 104 fwd each | 6, 104 | 6, 104 |
| h, f attention + DLA | 2,125 fwd + 125 batches each | same | same |
| i attention + DLA + families | 210 rows: 459 x 3 fwd | 788 rows: 1,683 x 3 fwd | 249 rows: 544 x 3 fwd |
| 18 seg lines | 21 groups, 299 fwd each (5,382) | same | same |

Expected on H100: about 35-45 min per task (sdr the longest). Plan: `--time 01:00:00` x 3 = 3.0 GPU-h reserved,
0.5 rerun held. Walltime is re-checked against 02b's smoke timings (the first measured v2 attention rate on H100)
before submission.

Commit file list sent to the orchestrator (see below). Waiting on: the push, 02b's smoke (job 49841165) passing and
the orchestrator's go before any GPU submission.

## Progress 2 (2026-10-25, night): advisor review applied; sweep-built merge tables; checkpoint

Advisor review of the checkpoint, applied:
- **Roles merge source changed** (supersedes the Progress 1 bullet): the phase-1 head tables have 123 heads-only
  rows, so the ten C_t MLP blocks and the S_k heads outside U would have had no knockout view. New
  `p2_merge.py` builds one table per (task, head cell) from the phase-1 `sweep.json` + `sweep_instances.json`
  (R16: the sweeps are the measurement of record, all 1,056 Components, one sample) over the U' rows:
  `outputs/_analyses/mechanism-analysis-p2/_merge/<t>_{d,h,f,i}/head_table.json` (d <- s1 + s2p, h <- s5, f <- s6,
  i <- s7). Built: 146/136/144 rows, no nulls, coverage meta per column with the sweep's instance ids; the instance
  set id equals the phase-1 head table's (`causal_sample:b656033b44` on far), and the numbers are identical on the U
  rows (head.17.24: 1.89075 +- 0.09799 in both). A groups-only knockout pass writes no `knockout.*` columns
  (checked on rinv_d), so the merge cannot collide with the phase-2 cells' own tables. `p2_roles.py` now merges
  only from these tables. Rehearsed `--dry-run` on the 02a DLA smoke cell: v2 variant, merge accepted.
- **The I cell has no plain knockout view** (no phase-1 I item-swap sweep): s7 carries the twin post-clause columns
  only, so on I only rule 4b can fire; roles.json records the missing view and the reading will say so.
- **Dry-run stubs removed**: the login `batch --dry-run` wrote stub head tables under the real output root
  `outputs/_analyses/mechanism-analysis-p2/` (276 files, all mine, all newer than the job files); deleted before any
  fetch (`b2.sh fetch` never deletes and would have left `.pre-b2fetch` backups beside them). The fetch glob
  `mechanism-analysis-*` covers the p2 root.
- `membership.S_k` is read from the operand's `members` (the set's MLPs count as S_k); B-reader reports U''s own
  layer-8-17 share and a p against it beside the pre-registered 10/32 test; C-honest's "writes honest" needs >= 2 SE
  where the SE column exists (sign-only flagged otherwise).
- Tests: 21 passed in mgnp and in base (thread pins).

**HOLDING FOR USAGE (orchestrator's instruction, 2026-10-25 night).** Weekly usage is at the user's cap; the
orchestrator will message to resume after the weekly reset (about 2026-10-28 07:00 CDT) or earlier. State at the
hold: the phase-2 file list (plus `p2_merge.py`) is committed and pushed by the orchestrator on
`mechanism-analysis`; R27 (twin DLA differential in the v2 roles clauses) is in as 83599b5, so the roles passes
can run on that commit; 02b's smoke verdict is still pending. Nothing synced to Bridges-2, no GPU job submitted,
no full suites run. Note for the resume: the local `_merge/` tables and the operands were built from the worktree
at this HEAD; rebuild nothing unless `p1c_readings.json` or the phase-1 sweeps change. Flag changes from 02b that
phase 3 (not phase 2) uses: `--path-twin-position-threshold` and `--path-category-floor`.

## Progress 3 (2026-10-26, midday): resumed on the orchestrator's go; jobs submitted

- 02b's smoke PASSED (load 585 s, attention <= 0.057 s/fwd, path 0.036 s/fwd); files pushed through a0fae76;
  R27 in at 83599b5. Usage after the weekly reset: 6 % / 1 %. New hold rule: five-hour >= 70, seven-day >= 74.
- `b2.sh sync-code --branch mechanism-analysis`: clone HEAD a0fae76 = origin. Bridges-2 login dry-run of the three
  batch files (`tmp/impl04/b2_dry.sh`): 23/23 ok each, exit 0. `submit --test-only` accepted (49871328).
- Walltime on the measured basis: load 10 min + attention (far 12,002 fwd x 0.057 = 11 min; sdr +4 min for the
  788-row I cell) + knockout (5,906 fwd x 0.036 = 3.5 min) + DLA (~2 min) + per-line overhead (~8 min) = 35-40 min;
  x 1.5 < 60 min, so `--time 01:00:00` each.
- Ledger (under the lock, `tmp/impl04/ledger_tool.py`): reservations 04-p2-far-2026-10-26T12:04:42,
  04-p2-sdr-...T12:05:04, 04-p2-ser-...T12:05:05, 1.0 GPU-h each; in flight 3.0, committed 14.0 GPU-h (28 SU).
- Submitted 12:05 CDT: far 49876003, sdr 49876005, ser 49876008 (GPU-shared, h100-80:1). Job ids sent to the
  orchestrator. Waiter: `tmp/impl04/wait_jobs.sh` (polls squeue every 90 s, log `tmp/impl04/wait_jobs.log`).
- The Bridges-2 login dry-run left stub cells under the p2 root on Bridges-2; the jobs overwrite every one of them
  (same cell paths, same four files), so nothing was deleted there.

## Progress 4 (2026-10-26, afternoon): fetched, reconciled, roles, results, reading

- Jobs COMPLETED: far 49876003 35:31, sdr 49876005 36:21, ser 49876008 37:57, exit 0:0 (timings: invocations
  1,829 / 1,901 / 2,013 s of which the first line holds the model load). Fetched with `b2.sh fetch`
  (`outputs/_analyses/mechanism-analysis-p2/`, 23 cell roots x 3 tasks + `timings/`). Ledger reconciled under
  the lock: 0.5921 + 0.6058 + 0.6325 GPU-h actual, booked 0.25 each at the quarter-hour rounding (0.75 of the 3.5
  allocated), in flight 0, reconciled 13.25 GPU-h / 26.5 SU.
- `scripts/check_cell.py` on the 12 head cells: no BROKEN view (the "Missing" lines are the views phase 2 does not
  run: single knockout, sweep, path patching, and the honest-instruction paired scatter).
- Roles passes (`p2_roles.py`, 12 cells, R27 criteria, `--roles-allow-missing-views`): pressure reader D 32/16/16,
  I 30/19/19, H and F none; the rest unknown/insufficient (one disagree on sdr D). The I cells lack the plain
  knockout view (no phase-1 I item-swap sweep) and roles.json says so.
- `p2_results.py` -> `reports/04-phase2-results.{md,json}`, curated `docs/research/mechanism-analysis/phase2/`
  (12 head tables with membership columns, families.csv, segments.csv, roles/<t>_<cell>.json, p2_readings.json).
  Two builder fixes on the real data: patterns.json's `levels` is a list keyed by `level`; an MLP member of the
  deciding set was being added as a head (membership total 148 -> 146); plus the sink-free C-reads variant
  (exploratory) and the B-reader control against U''s own layer-band share. 22 tests green.
- Headline reading (`reports/04-phase2-reading.md`): pre-clause assertion PASS x3; core shared x3; far's
  exclusives and (D-H)-core the one deception-specific family (negative on H/F); sdr/ser exclusives shared;
  B-reader PASS x3 (p <= 1e-12; L13H5 only on sdr); C-honest held and stronger (late H-D heads flip sign under
  pressure); deciding sets identical on I and D (instructed-inversion machinery); C-reads FAIL (p 0.65, sink
  dominated; sink-free p 0.15). C_t proposal 72/66/78 Components, phase-3 cost ~110/95/125 min per task.
- Phase-3 cost probe: `tmp/impl04/ct_probe/` (login `--dry-run` of path patching on the proposed C_t, both
  counterfactuals, sweep, twin Segment pass at 0.01).
- Full suites: base env 8 failed = the 8 baseline names, 2147 passed, 66 skipped (519 s); mgnp: see Progress 5.

The remaining steps, in order (steps 1-4 done as of Progress 4):
1. `scripts/remote/b2.sh sync-code --branch mechanism-analysis`; on the Bridges-2 login node
   `python analyze_components.py batch docs/research/mechanism-analysis/jobs/04-p2-<t>.batch --dry-run` for the
   three files; `b2.sh submit --test-only ...` for each.
2. Walltime from 02b's smoke timings (measured H100 attention rate) x 1.5; expected `--time 01:00:00` x 3. Reserve
   under the ledger lock (bridges2 section, owner impl-04, 3 jobs; the 0.5 rerun stays unreserved until needed),
   then `b2.sh submit --time HH:MM:SS --script scripts/analyze_components.sbatch --job-name p2-<t> -- batch
   docs/research/mechanism-analysis/jobs/04-p2-<t>.batch --timings outputs/_analyses/mechanism-analysis-p2/timings/<t>.json`.
3. `b2.sh status`; `b2.sh fetch outputs/_analyses/mechanism-analysis-p2`; reconcile the ledger (actual GPU-h);
   `scripts/check_cell.py` on the 12 head cells (and spot-check seg cells).
4. `python outputs/_launch_mechanism_analysis/p2_roles.py` (CPU; 12 roles passes), then
   `python outputs/_launch_mechanism_analysis/p2_results.py` -> `reports/04-phase2-results.{md,json}` and the curated
   `docs/research/mechanism-analysis/phase2/` files; write `reports/04-phase2-reading.md` (C_t proposal + the
   path-patching `--dry-run` cost on the proposed C_t operand); `reports/04-review.md`; full suites both envs;
   tick the ticket; final hand-back.

## Progress 5 (impl-04o, 2026-10-26 afternoon): reviewer fixes finished, reading rewritten, ticket resolved

impl-04o (Opus) took over from the on-disk state after the 14:00 session restart. Scratch:
`/u/swong2/.claude/jobs/1c836bb8/tmp/impl04o/`. No git, no GPU, ledger untouched.

- **Reviewer fixes (a)-(l)**: impl-04 had applied (a), (c), (d), (h) and most of (e), (f), (g), (i), (j), (k) in code
  before the restart. impl-04o finished them: twin DLA column names built from `dla.TWIN_COLUMN_SOURCES` (e);
  check_cell table per head cell in the results (j, `cell_check`); C2 over every D-H head with a core column (j);
  an `EXPLORATORY` list in the results markdown/JSON and `p2_readings.json`, and `b_reader_I` in the markdown (k);
  phase 1's per-head R-cls quoted in the results (i); C-honest `holds` (both clauses on one head). Removed a
  redundant exploratory C-reads table (twin-paired top Segment = the pressure top Segment over the whole split).
  Fixed `cell_check` to take the absolute cell path. Tests added first: 27 in the ticket file, green in mgnp and base.
  Dispositions per finding: `reports/04-review.md`.
- **Rebuilt** `reports/04-phase2-results.{md,json}` and the curated `docs/research/mechanism-analysis/phase2/` files.
- **Reading rewritten** from the rebuilt JSON (`reports/04-phase2-reading.md`). The first reading had re-graded two
  phase-1 verdicts from family knockouts (core answer machinery "held"; C-confound "survives") and quoted stale
  numbers (C-reads p 0.65); both fixed. Phase 1's verdicts stand; family knockouts are descriptive (C3).
- **Correction to Progress 4**: the ledger books 0.75 GPU-h per job (2.25 of 3.5; 1.83 actual), not 0.25 each.
  The ledger itself is right (reconciled 13.25 GPU-h / 26.5 SU, 0 in flight).
- **Phase-2 verdicts**: pre-clause zero PASS x3; B-reader (i) binomial holds x3, (ii) named heads hold on sdr only
  (L13H5 fails far/ser); C-honest holds on most heads (9/12, 5/7, 7/8), every reduction a sign flip, none merely
  suppressed; C-reads fails (p 0.58, 12 of 32 heads with an established read, almost no power); RQ-A per-head and
  C-confound: phase 1's verdicts stand. I cells: descriptive overlap consistent with phase 1's R-inv.
- **C_t proposal**: far 72 (62 heads + 10 MLPs), sdr 66 (56 + 10), ser 78 (68 + 10). Phase-3 cost from impl-04's
  login dry-run (`tmp/impl04/ct_probe/`): about 110 / 95 / 125 min per task at 0.036 s/fwd; x1.5 walltimes 2.75 /
  2.5 / 3.25 h = 8.5 of the 9.25 GPU-h allocation. ser's walltime exceeds the spec's 2.75 h per-task reserve.
- **Tests**: ticket file 27 passed in both envs. Full suites: base by impl-04 (8 baseline names, 2147 passed);
  mgnp by impl-04o: 8 failed = the 8 baseline names (compared by name), 2347 passed, 19 skipped (1420 s); started before the last p2_results edits, after which the ticket file was rerun green in both envs.
- **Commit list** (relative to the worktree): the four `p2_*` scripts and the test file, plus the curated phase2/
  files (head tables, families.csv, segments.csv, p2_readings.json, roles/*.json; roles/ is 4.7 MB). Not
  `outputs/_launch_mechanism_analysis/eval_jobs.txt` or `outputs/_suites/*`, which are not ticket 04's.
