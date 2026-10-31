# 02a — Component analysis on v2 for phase 1: loaders, segmentation, neutral-twin pairing, knockout schemes, positions, groups and greedy selection, held-out sampling, DLA lens

**What to do:** make `analyze_components.py` run the phase-1 analyses (knockout sweeps and group knockouts, DLA and
logit lens) on `far_v2`, `sdr_v2` and `ser_v2`, on their D, H, F and I test sets (spec §2.2). Add the paired
Neutral-Clause Twin counterfactual for knockout and DLA, the knockout extensions R-AB needs (R11), and the held-out
sample. Then prove the package runs on Bridges-2 with a smoke job and a component-analysis drift control. Attention
patterns and path patching under the twin, and the criteria amendment, are ticket 02b.

**Status:** resolved (Bridges-2 job 49824729: smoke 8/8 ok, drift control PASSED; the `frame` mapping of `response_line` is handed to 02b)
**Type:** task
**Blocked by:** nothing for the code. The Bridges-2 smoke needs ticket 01 (b2.sh branch, analyze_components profile)
and the branch pushed (R3).
**GPU allocation:** 1.0 H100 GPU-h on Bridges-2 (one smoke + drift job). Delta: 0 without the orchestrator's approval.

## Facts to build on

- Every v1-only place is listed in `reports/00-plan-handback.md` (b) items 1-11, with file:line references.
- `component_analysis/dataloaders.py:72` `MECHANISM_TASKS` is v1-only (`tasks.DECEPTION_TASKS_V2` is the v2 list).
  `<t>_v2_inversion` (ticket 08) is a new condition; it may not exist yet, so its loader support is tested on a
  fixture.
- `segmentation.py:534-541` registries; `:338` `_mechanism_intro` reads `dc.SPECS` and raises `KeyError` on v2. The
  v1 intros equal the v2 ones on 9,000 of 9,000 rows. Dispatched to the v1 segmenter, every v2 row resolves and
  validates. On `_honest` rows `pressure_clause` is the neutral sentence; on `_nopressure` it is absent.
  `item_N_question_option` is the response-line mention on v2. The Pressure Clause is the last sentence of the
  system turn (review §0).
- `analyze_components.py:345` silently skips non-segmentable tasks.
- Neutral-Clause Twin: `data/datasets/<t>_v2_honest` has the same ids, row order and `pressure_id` as D. Its labels
  are swapped: target = the honest item. Each clause is replaced by a sentence of identical token count; 1,000 of
  1,000 rows are aligned and honest in both streams per task. The pair keeps D's Target/Distractor, as
  `matched_honest.instructed_counterpart` does.
- **Column trap (R16).** D rows carry `neutral_prompt` and `neutral_text`. `neutral_prompt` is the Prior-Balance
  prompt: the Designating Sentence is neutralized and the clause is kept. It is NOT the Neutral-Clause Twin.
- Knockout today: interchange only (`knockout.py:70-71,95-107`); single, family and sweep share one loop
  (`knock_out_groups` `:328`, `family_effects` `:459`, `sweep_effects` `:608`); replacement is at every position, from
  an unmodified corrupt-stream forward. Mean semantics to match: `evaluation/ablation.py` `MeanCollector` (per site,
  task test split, clean + corrupt pooled, fp32 accumulation).
- Sampling: `component_analysis/sampling.py` `draw_sample(records, n, seed)` has no id exclusion.
- DLA counterfactual plumbing to mirror: `dla.py:121-124,172,728-788`; `head_table.py:70-72` (instance-set ids).
  Column naming: "paired" goes in the name (`docs/component-roles.md`, 2026-10-13); here `_neutral_twin_paired`.
- Hooks: nnsight 0.7.0, imported inside functions only (`hooks.py:2-20,80-81`); ADR-0001. The login base env has
  nnsight 0.5.12, so nnsight tests skip there.
- Drift reference: `outputs/_analyses/sdr-dh-core-kosweep/` (main checkout, untracked), Delta H200 job 22899543,
  9:33. Its argv is in the cell's head-table meta. Its inputs: v1 `sdr` data, the v1 coarse SDR D and H runs, the
  all-MLP operand. Ticket 06's drift cells did not need the H run, so verify it is in the Bridges-2 manifest
  (`b2_manifest.txt`) and add it if not (R16).
- Clause forms (R12): 49 test clauses (12 / 20 / 17), 1 to 150 rows each.

## Acceptance criteria

- [x] v2 ids (D, H, F, and the I condition) are covered by the loaders, segmentation and the knockout and DLA
      analyses. A v2 cell is never skipped silently (test). The v1 segmentation of a saved v1 SDR record is
      byte-identical before and after (snapshot test).
- [ ] A v2 segmentation scheme with a `response_line` Segment carved from `question`, in the `frame` group (R7).
      v1's `MECHANISM_SEGMENTS` is unchanged. *(impl-02ar: the Segment and the v2 scheme are built and tested, and
      v1's list is unchanged. The `frame` mapping in `roles.SEGMENT_GROUPS` is left to 02b: R7 puts it inside the
      criteria amendment that R10 lets the user veto until 02b applies it. See Comments.)*
- [x] `neutral_twin` paired kind in `dataloaders.py` for D and for I as the pressure stream: joined by id,
      `honest_twin_kind == neutral_clause`, same `pressure_id`, `assert_clause_aligned_pair` on both streams, D's
      labels, the clause span recorded. A test asserts the twin comes from `<t>_v2_honest` and never from the
      `neutral_prompt` column. The `--dry-run` loader summary reports n paired (expect 100 of 100 causal, 1,000 of
      1,000 descriptive).
- [x] Held-out sampling: an id-exclusion option (a file of ids, or the selection cell's sample file) so that seed 1
      with the seed-0 ids excluded gives a disjoint stratified balanced sample. Without the option the draw is
      byte-identical to today's (test).
- [x] Knockout, for the single pass, the family pass, the sweep and named groups; `knockout.json` / `sweep.json`
      record every choice:
  - [x] `--knockout-scheme {interchange, mean, zero}`, mean with the evaluator's semantics;
  - [x] `--knockout-counterfactual {item_swap, neutral_twin}`;
  - [x] `--knockout-positions {all, readout, <Segment>}` plus the range form `after=<Segment>[,exclude=readout]`
        (R11(a)); "post-clause" in the spec is `after=pressure_clause,exclude=readout`;
  - [x] `--knockout-groups FILE`: JSON `{name: [[kind, layer, index], ...]}` in `head_table.row_key` order (R16),
        each set knocked out jointly, sign convention unchanged;
  - [x] greedy selection in-process: from a pool (the top N of a given sweep file, layer-0 MLP excluded), add at
        each step the Component that maximizes the joint drop, up to a k_max; writes the order and the joint drop
        per step;
  - [x] the sweep can exclude named Components from ranking (the layer-0 MLP, R11(a)).
  CPU tests on the tiny model in `tests/helpers.py`: the mean bank matches a hand-computed mean; zero writes zeros;
  neutral twin with identical streams gives zero drop; neutral twin at pre-clause positions gives exactly zero; a
  position restriction touches only the named tokens; the range form selects exactly the post-clause non-Readout
  tokens; greedy on a scripted effect table returns the expected order.
- [x] DLA: the `neutral_twin` paired condition and the per-instance differential over all 1,000 rows, with
      `_neutral_twin_paired` columns and coverage meta. DLA's `honest_twin` stays descriptive on v1 and gains the
      paired form on v2. The per-instance lens crossing summary for R-lens: per instance, the first layer in 8..28
      with margin < -0.5 and the final sign, written to `dla/logit_lens.json`. Unit-tested.
- [x] Clause-form table (R12): `docs/research/mechanism-analysis/clause-forms.csv` with task, `pressure_id`, clause
      text, n test rows and form by the text rule (Predicate-naming iff the clause contains a Predicate word;
      act-naming iff it says wrong, incorrect, false or not true; otherwise other), applied by a script and checked by
      hand. Handed to the orchestrator for commit before any 1B job.
- [x] Login `--dry-run` of every phase-1B cell and of the 1C invocations (3 tasks x D/H/F, I on a fixture if 08 is
      not done) prints segmentation, sample, pairing and cost with no error.
- [x] Both envs: full suites, failures compared by name with `reports/00-baseline-failures.md`. nnsight-dependent
      tests skip on base and run on mgnp.
- [x] Bridges-2 smoke (through ticket 01's b2.sh and profile):
  - [x] on the login node, `python -c "import nnsight; print(nnsight.__version__)"` prints 0.7.0 in the unpacked env;
  - [x] a v2 `--dry-run` passes on the login node;
  - [x] one GPU job runs a tiny v2 cell (`--n-causal 8`, knockout under every scheme, counterfactual and position
        form, a groups file, greedy to k = 3, DLA with the twin) and the v1 `sdr-dh-core-kosweep` rerun.
- [x] Drift tolerance, pre-registered, against Delta job 22899543 over the 1,056 Components:
      - max |Δ drop| <= 0.05 logits;
      - 99th percentile <= 0.02;
      - Spearman >= 0.99;
      - the same flagged set at 0.4, except Components within 0.02 of the threshold.
      Report the numbers. If it fails, hand back before any phase-1B job.
- [x] The smoke job's elapsed time per sweep and per group knockout becomes the phase-1 cost basis in the hand-back.
- [x] Ledger `bridges2` entries reconciled with sacct. Review in `reports/02a-review.md`; progress in
      `reports/02a-handback.md`.

## Hand-back

The file list to commit (with the clause-form table), tests per env, smoke and drift numbers, the measured H100
sweep and group-knockout times, and the dry-run tables. Phase 1B starts when the smoke and drift control pass (R4).

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

### Orchestrator addition 2026-10-25 (R19(1), R19(3), from review-00's re-check)
- Every group knockout and every sweep writes PER-INSTANCE values: clean margin, knocked margin, and the Neutral-Clause
  Twin's own margin on the same instance (ids aligned). `knockout.json` / `sweep.json` today keep ids and summaries
  only; R-AB's denominator f_D and the per-instance bootstrap CIs need the rows. Keep summaries as they are; add the
  per-instance arrays (or a sidecar file named in the JSON).
- Sampling gains an id-INCLUSION option beside the exclusion option: a file of ids the sample must be drawn from.
  R-inv is paired (spec R19(3)): the I condition is a filtered subset of D's ids, so f_D and f_I are computed on D's
  held-out ids that survived I's filter.
- Lens summary: also record the layer of the last sign change per instance. Clause-form rule precedence: act-naming
  checked first, then Predicate-naming, then other.

### impl-02ar hand-back (2026-10-25)

**Status:** resolved-pending-gpu. The full record is in `reports/02a-handback.md`: the commit list, per-env tests,
the job plan and the cost table. The review is `reports/02a-review.md`.

- **Built (impl-02a), verified and finished (impl-02ar).** The v2 loaders and segmentation (with `response_line`),
  the Neutral-Clause Twin pairing, held-out `--exclude-ids` and R19(3) `--include-ids`, and knockout schemes,
  counterfactuals and positions (incl. `after=pressure_clause,exclude=readout`). Also named groups, greedy (layer-0
  MLP out), sweep exclusion, DLA twin pairing with the lens crossing summary (incl. the last sign change), the
  `batch` runner (one model load per job) and the drift comparator. The clause-form table was committed at fc9e614
  with act-naming checked first.
- **Verified independently with the unmodified main-checkout code.** The v1 segmentation snapshot (far/sdr/ser,
  1000 rows each) and the no-option sample draws (8 task/seed keys) reproduce bit for bit.
- **Fixed by impl-02ar.** v1 JSONs are byte-identical again under the default plan. R19(1): the twin's own margin
  is recorded per instance under every plan, and the family pass writes its sidecar. Two red DLA tests had a wrong
  row count. `batch --timings` now creates its directory. Unused test imports are removed.
- **Commit list.** It includes `tests/test_knockout.py`, `tests/test_knockout_model.py` and
  `tests/test_knockout_families_model.py`. These are 02a's, not ticket 01's.
- **Tests.** mgnp shows the 8 baseline names only. Base shows the 8 plus 3 ticket-01 infra tests, from `b2.sh`
  being edited during the run.
- **Jobs and ledger.** None yet; 1.0 H100 GPU-h untouched. Plan: one GPU-shared h100-80 job, `--time 01:00:00`,
  expected about 0.5 h.
- **Left open on purpose.** The `frame` mapping of `response_line` is 02b's (R7, R10). The smoke, drift, cost
  basis and ledger boxes wait for ticket 01's commit and the push.
- **For ticket 03.** Build the single selector from `sweep.json`'s `signed_rank`, the order greedy's pool uses.

### impl-02ar GPU results (2026-10-25)

**Status:** resolved. The full record is in `reports/02a-handback.md` § Results.

- **Job.** Bridges-2 job 49824729 COMPLETED in 00:23:51. All 8 smoke lines were ok.
- **Drift control PASSED.** The comparison is in `reports/02a-drift.json`. Max delta 0.0, p99 0.0, Spearman 1.0,
  and an identical flagged set over 1,056 Components. The H100 rerun is bit-identical to the H200 cell of record.
- **Cost basis.** A sweep at n = 100 takes 535 s (0.0389 s per forward). A group knockout takes 0.78 s (named)
  or 0.49 s (greedy). Model load takes 476 s.
- **Ledger.** 1.0 GPU-h reserved, reconciled to 0.5 (actual 0.3975).
- The remaining unticked box is the `frame` mapping, which is 02b's.
