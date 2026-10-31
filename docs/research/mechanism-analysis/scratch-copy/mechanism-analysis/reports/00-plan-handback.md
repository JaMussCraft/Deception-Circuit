# 00 plan hand-back (plan-01, 2026-10-25)

Planner: plan-01. Read-only on the repo (main checkout `Deception-Circuit` at c24b5d9). No git, no Slurm, no
GPU, no `analyze_components.py` or `evaluate_circuit.py` run. CPU checks ran with
`/sw/external/python/anaconda3/bin/python -I` from scripts in `/u/swong2/.claude/jobs/1c836bb8/tmp/`
(`peek_v2*.py`, `hi_align.py`, `headsets.py`, `intro_check.py`, `seg_check.py`).

Files written:

- `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/spec.md` (status draft)
- `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/issues/01..07-*.md`
- `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/agent-brief.md`
- `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/00-plan-draft.md` (one page for the user)
- this file

Paths below are repo-relative to `/projects/beto/swong2/Alignment/Deception-Circuit` unless absolute.

Note (2026-10-25 sync): the verified facts (a)-(g) and the cost model stand. Plan numbers, ticket names ("ticket 02"
is now 02a and 02b), questions and rules quoted here are superseded by spec.md after its sync to rulings R0-R17;
see `reports/00-plan-sync-handback.md`.

## (a) Ablation schemes

**Component analysis is interchange-only, and interchange means the item-swap stream.**

- `component_analysis/knockout.py:9-15` (docstring): "The knockout is an interchange ablation ... Mean and zero
  ablation are not built". `:70-71` `SCHEME = "interchange"`, `FUTURE_SCHEMES = ("mean", "zero")`.
  `:95-107` `resolve_scheme` refuses anything else by name. `:988` `--knockout-scheme` flag.
- The single pass (`knock_out_groups`, `:328`), the family pass (`family_effects`, `:459`) and the whole-model
  sweep (`sweep_effects`, `:608`) all take `scheme=SCHEME`. So the 1,056-Component sweep is interchange too.
- The counterfactual stream is fixed to the item-swap Corruption (`knockout.py:9-12`). A Component that only
  reads the Pressure Clause carries the same value in the clean and the item-swapped stream, so **its item-swap
  knockout is about zero by construction.** Item-swap knockout cannot see a pure pressure reader. This is the
  reason the spec adds a neutral-twin counterfactual and mean/zero schemes to component knockout (ticket 02).

**`evaluate_circuit.py --ablation mean|zero` works on leaf-composed circuits, with one caveat.**

- `evaluate_circuit.py:108-112`: `--ablation {interchange,zero,mean}`, `--mean-source pooled|clean|corrupt`.
- `evaluation/ablation.py:44` `ABLATION_SCHEMES`; `:189-204` `make_hook`. The hook fills every gated site, so it
  is mask-agnostic: a composed leaf mask such as `(X) - m` is just a mask.
- `evaluation/context.py:350-373`: the mean bank is per task, collected over that task's test loader (both
  streams pooled by default), circuit-independent, cached per process. `:623-627` `hook_for`.
- Precedent: `outputs/_suites/cross-task-matrix-nls0.3-delta-leaf/` ran `--ablation zero` and `mean` with
  `compose_granularity: leaf` on composed v1 fine delta circuits (`suite.json`, created 2026-09-06; evals sanity,
  knockout, null, pressure). On `cells/delta_far__leaf/far/`:

  | scheme | circuit-alone acc | knockout acc |
  | --- | --- | --- |
  | interchange | 0.000 | 0.485 |
  | mean | 0.495 | 0.690 |
  | zero | 0.497 | 0.607 |

  Mean and zero leave a lone circuit at chance rather than at zero, and their knockouts are milder. That is the
  calibration the pre-registered mean/zero reading in spec §2 uses.
- Caveat 1: **sanity (eval 1) cannot pass under mean or zero**, because the in-run `node_eval` it reproduces was
  trained under interchange (help text at `evaluate_circuit.py:109-110`). Mean/zero cells run `--evals knockout`
  only, which is what ticket 06's KO cells already ran (`mv2_cells.py:69-70`).
- Caveat 2: the ticket-06 launcher hard-codes interchange: `outputs/_launch_mechanism_v2/evals/mv2_cells.py:72`
  `COMMON_ARGS = ["--ablation", "interchange", ...]`. Ticket 01 adds an ablation parameter.
- Heads-only `X - m` cells under mean or zero were never run before (the v1 precedent was fine circuits). The
  code path is the same; the first job of ticket 03 is the check.

## (b) v2 task ids in the component-analysis package

Every place that needs a v2 extension:

1. `component_analysis/dataloaders.py:72` `MECHANISM_TASKS = ("far", "sdr", "ser")`; `:147-155`
   `uncovered_reason`; `:236-238` raises `LoaderUnavailable` for any v2 id. Callers that inherit the refusal:
   `dla.py:803` (honest_instruction condition), the causal loaders used by knockout and path patching.
2. `component_analysis/segmentation.py:534-541` `_SEGMENTERS` and `_SCHEMES` list only far/sdr/ser/std. Today
   `resolve_segmentation("sdr_v2", ...)` raises `SegmentationError: task 'sdr_v2' has no default segmentation`
   (checked on CPU).
3. `segmentation.py:338` `_mechanism_intro` reads `deception_common.SPECS[record["task"]]`. `dc.SPECS` holds only
   far/sdr/ser, so a v2 record gives a `KeyError`, not a `SegmentationError`. The v2 intros are byte-identical to
   v1's: 9,000 of 9,000 v2 rows (3 tasks x D/H/F test) start with the v1 intro, and also with
   `deception_v2.make_spec(task, suffix, ser_wording)`'s. So the fix is a dispatch to `deception_v2` for v2 ids.
4. `analyze_components.py:345` keeps only tasks with `is_segmentable`, and `resolve_instances` skips the others
   **silently** (docstring `:336-343`). A v2 cell today would run with no segmentation and no sample. Ticket 02
   needs a test that a v2 cell is not skipped.
5. Regex coverage of the v2 Scaffold. I applied the v1 segmenter to every v2 row by passing the v1 task name
   (dispatch-only simulation, real Llama tokenizer, CPU). Result: **9,000 of 9,000 rows resolve and validate**.
   - The Suffix Policy `on` sentence is joined as its own sentence and lands in `designation_suffix` (e.g.
     `' The failing result is the one that matters most here.'`). No ".T" token straddle in v2.
   - The G5 response line stays inside `question`. On far_v2 that Segment decodes as
     `'Which result is failing, or? Only respond with "The result that is failing is X", where X is or.'`.
   - Each item is named exactly twice in every v2 user turn (0 exceptions in 3,000 D rows): the pair naming and
     the response line's `where X is A or B`. So `item_N_question_option` is the **response-line mention**, not a
     quoted option as CONTEXT.md describes. Naming caveat, not a bug.
   - On `_honest` rows the `pressure_clause` Segment holds the neutral sentence (e.g. `' The facility employs
     around sixty people across two shifts.'`). On `_nopressure` rows it is absent (1,000 of 1,000), which
     `validate_segmentation` allows.
   - FAR's user turn names the Predicate twice (`Which result is failing ... "The result that is failing is X"`);
     SDR and SER do not. That lands in `question` and `stem` on FAR only. A cross-task "reads the question"
     comparison carries this asymmetry. The spec proposes an optional `response_line` Segment for v2.
6. `component_analysis/sampling.py`: task-agnostic. It stratifies over designation polarity x item polarity x
   template variant; v2 test sets are exactly 250 per (designation, item) cell and 500/500 audit/lab, so all
   three factors are active (8 strata). No change.
7. `component_analysis/intake.py`: task resolution goes through `evaluation/circuits.resolve_tasks`, which already
   accepts v2 (`evaluation/circuits.py:317`, `evaluation/context.py:161`). The nopressure stand-ins in
   `outputs/_launch_mechanism_v2/evals/standins/` bind `<task>_v2_nopressure` the same way. No change.
8. `component_analysis/instances.py:42-60` special-cases only `std`. No change.
9. `component_analysis/dla.py:728-736` `honest_twin_dir` = `<dataset>_honest`; `:758-788` `assert_honest_twin`
   checks `condition == "honest"`; `:172-181` `direction_sign` negates the twin because its `target` is the honest
   item. All three hold for v2: `<task>_v2_honest` rows carry `condition: honest`,
   `honest_twin_kind: neutral_clause`, and target = the honest item (D's target and distractor swapped). The
   existing descriptive `honest_twin` column therefore works for v2, and because the ids match row for row it can
   be made paired.
10. `component_analysis/path_patching.py:128-139,191,504` and `attention_patterns.py:154-164`: the paired
    counterfactual set is `{item_swap, honest_instruction}`. A v2 counterfactual needs a new name, column suffix and
    instance-set id (`head_table.py:70-72`).
11. `docs/component-roles.md` "Segment groups": any new Segment (e.g. `response_line`) must be added to a group,
    or it reads `unestablished`. That is a dated criteria amendment under the doc's own rules.

## (c) The honest counterfactual for v2

Measured on CPU over the three 1,000-row test sets:

| task | Neutral-Clause Twin token-aligned with D | stored fixed honest instruction aligned | of those, honest at h >= 0.3 (clean) |
| --- | --- | --- | --- |
| far_v2 | 1000 | 0 | 0 |
| sdr_v2 | 1000 | 234 | 211 |
| ser_v2 | 1000 | 573 | 560 |

- The Neutral-Clause Twin shares instance ids and row order with D (1,000 of 1,000 per task, D/H/F) and the same
  `pressure_id` on every row. Every D row is honest under its neutral twin in both streams at h >= 0.3 (1,000 of
  1,000 per task; `h_neutral_*` fields), by the full-build rule. Its clause is replaced by a sentence of exactly
  the clause's token count (asserted at build, re-checked above).
- The stored `honest_instruction_*` prompts use the fixed `dc.HONEST_INSTRUCTION`, not a matched one, so they move
  the Readout except where lengths happen to agree. FAR has none aligned. They are unusable as a paired
  counterfactual.

Options, with cost and what each does to the selector clause (`docs/component-roles.md` rule 4, "the
Honest-Instruction Counterfactual reaches it at its own query"):

1. **Build Matched-Honest-Instruction pools for v2.** Draft length-matched honesty instructions per v2 clause
   (`matched_honest.select_matched_instruction`, CPU) and run the honest filter (`filter_matched_honest`, four
   forwards per instance). `dataset/build_matched_honest.py` and `scripts/build_matched_honest.sbatch` are v1-only
   and need a v2 path. The v1 candidate ladder was drafted for v1 clause lengths; v2 clauses are rule directives
   of other lengths, so unmatched clauses are likely and a new ladder may be needed (FAR worst). Cost: about a day
   of code plus about 0.5 GPU-h (3 x 1,000 instances x 4 forwards, under 10 min per task on an A40 with load).
   Keeps rule 4's meaning exactly (continuity with v1 SDR roles). Coverage below 100% and unknown until drafted.
2. **Pair D with its Neutral-Clause Twin by instance id (recommended).** No GPU, 100% coverage, 1,000 paired
   rows per task for descriptive views and the full causal sample for causal ones. Code only: a second paired
   kind in `dataloaders.py` (join `<task>_v2_honest` by id, assert `honest_twin_kind`, same `pressure_id`,
   `assert_clause_aligned_pair` on both streams, keep D's labels), plus a `neutral_twin` counterfactual in
   knockout, DLA, attention and path patching with `_neutral_twin_paired` column names. Effect on rule 4: the
   query-side clause would read "the pressure-vs-neutral contrast reaches it at its own query". That is closer to
   the spec's "the lie signal enters at their queries" than an honesty instruction, because the neutral twin adds
   no competing instruction. It is still a criteria change (a different column), so it needs the dated amendment
   the doc requires and must never share a table with v1 roles. It also removes the reason the doc reserves
   **pressure reader** ("needs a dataset variant with an honest-instruction Corruption"): the neutral twin is a
   clause corruption. Whether to un-reserve it is a user decision.
3. **Both.** Option 2 primary, option 1 as a robustness subset for continuity with v1. Cost is option 1's.

Recommendation: option 2 now; option 1 only if a reviewer asks for continuity with the v1 selector criterion.
Also matches spec §13.10 of mechanism-datasets (the Neutral-Clause Twin is the primary v2 honest twin).

## (d) Comparison set

`data/datasets/comparison_set_v2.json`: intersection sizes train 5, validation 0, test 8 (ids listed there);
`shared_clause_subset` empty in every split. So **no instance-level paired cross-mechanism comparison is possible
at a useful n.** The three test sets are balanced on the same factors (designation x item polarity 250 each,
audit/lab 500/500) and draw from overlapping item pairs (39 / 39 / 33 distinct) and one generator, but their
clauses differ by task (12 / 20 / 17 distinct clause ids in test) and the populations are different survivors.
Cross-mechanism comparisons are between-group, matched on stratification marginals only. Stated as a hard
limitation in spec §7. A cross-realization option (re-render each test instance under the other two Predicates and
behaviour-filter it) is listed in spec §10 as a question, not planned.

## (e) Bridges-2 for component analysis

- Imports: ADR-0001 (`docs/adr/0001-component-analysis-on-raw-hf-model.md`) puts every analysis on the raw HF
  model **under nnsight 0.7.0**. `component_analysis/hooks.py:2-20`: every nnsight import is inside a function
  (`:80-81` `from nnsight import LanguageModel`), so the dry-run path needs no nnsight; a real run does.
- Env: mgnp has `nnsight-0.7.0.dist-info` (`/u/swong2/.conda/envs/mgnp/lib/python3.12/site-packages/`), and the
  Bridges-2 env is a conda-pack of mgnp (`/work/nvme/beto/swong2/envs/mgnp-conda-pack.tar.gz`, 5.56 GB, Oct 24).
  `requirements-bridges2.txt:73` pins `nnsight==0.7.0`. `b2.sh unpack-env` printed only torch, transformers,
  datasets and accelerate versions, so **nnsight on Bridges-2 is not verified**, nor whether nnsight touches the
  network at load under `HF_HUB_OFFLINE=1`.
- `scripts/analyze_components.sbatch` **does not honour the cluster profile**: `:62` `source ~/.bashrc && conda
  activate mgnp` (no `~/.bashrc` on Bridges-2), no `DC_CLUSTER` block, no offline flags. Compare
  `scripts/evaluate_circuit.sbatch:48-61`. Ticket 01 mirrors that block.
- `scripts/remote/b2.sh:25` `BRANCH="mechanism-datasets"` is hard-coded, so `sync-code` cannot fetch a
  `mechanism-analysis` branch. `:35` `FETCH_SUITE_ROOTS` lacks `outputs/_analyses`, which is also git-ignored
  (`.gitignore:8`), so analysis cells written on Bridges-2 come back only by an explicit fetch and are never
  committed. `scripts/cluster/delta.env:25` defaults `DC_REPO_ROOT` to the mechanism-datasets worktree
  (override `DC_DELTA_REPO_ROOT`).
- Smoke test (ticket 02): (1) on the Bridges-2 login node, `python -c "import nnsight; print(nnsight.__version__)"`
  in the unpacked env, and `analyze_components.py --dry-run` on one v2 cell (CPU, no GPU); (2) one GPU job that
  reruns the v1 cell of record `outputs/_analyses/sdr-dh-core-kosweep/` (whole-model knockout sweep, 1,056
  Components, 100 instances; Delta H200 job 22899543, 9:33) with its own argv, as the component-analysis drift
  control, plus a tiny v2 cell (`--n-causal 8`, every analysis) as the v2 smoke. Its inputs (v1 `sdr` data, the
  v1 coarse SDR D/H runs, the all-MLP operand) are tracked and already on Bridges-2 from ticket 06's drift
  control. Tolerance proposed in ticket 02.

## (f) Extra seeds of the three D circuits (option only)

- Ticket 05 timings (`reports/05-training-summary.md` of mechanism-datasets): coarse D on gpuH200x8-interactive
  29:41 (far) and 30:11 (ser); on gpuA40x4 2:25-2:27. Training needs more than 40 GB (memory
  `slurm-job-policy`); an H100 80 GB fits.
- Bridges-2: `scripts/train_deception.sbatch:35` has the same `~/.bashrc` activation and no profile block, so
  training there needs the profile block too, plus offline HF. H100 time is not measured for training; scaling the
  evaluator's ratio (H200 5.4x, H100 4.0x an A40) gives about 40 min + 10.5 min cold load per run, ~0.85 H100
  GPU-h, 1.7 SU.
- Option as costed in spec §6 and ticket 07: seeds 1 and 123 (the coarse SDR seed wave's) for D_far, D_sdr, D_ser
  = 6 runs. Delta gpuH200x8-interactive (proven path, no new code): ~3.5 GPU-h actual, 6 reserved. Then
  `postprocess_coarse.sh` (CPU), seed Jaccard (CPU), and 9 KO cells of seed exclusives on Bridges-2 (~1.5 H100
  GPU-h actual, 2.5 reserved). H seeds (needed for D-H stability) would double the training part.

## (g) Head sets, recomputed from `active_nodes.coarse.json`

Heads counted where the head gate and its attention-block gate are both 1; equals each file's `active_heads`
list in all six runs. Every run keeps all 32 MLPs (heads-only).

| task | D | H | D&H | D-H | H-D | Jaccard | exclusive | (D-H) in core | (D-H)-core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| far | 58 | 60 | 32 | 26 | 28 | 0.37 | 8 | 11 | 15 |
| sdr | 60 | 58 | 39 | 21 | 19 | 0.49 | 14 | 6 | 15 |
| ser | 55 | 69 | 36 | 19 | 33 | 0.41 | 10 | 0 | 19 |

- D core (far&sdr&ser) = **31**, union of the three D = 87, H core = 28, all six = 18, union of all six = **123**.
  Pairwise D: far&sdr 41, far&ser 40, sdr&ser 36. All match the recon and ticket 06.
- Correction to a shorthand in RESUME: the 31 core heads are not all in every H. 18 are in all three H, and every
  core head is in at least one H.
- D-H overlaps across tasks: far&sdr 5, far&ser 1, sdr&ser 0, all three 0. D-H membership is task-specific even
  though stage 2 found its knockout effect is not.
- **Confound:** far's D-H contains 11 core heads; ser's contains none. The "most deception-leaning" far D-H
  reading of ticket 06 rides partly on core heads. Phase 1 adds `(D-H)-core` cells.
- Layer distributions:
  - core: L7 3, L8 6, L9 3, L10 5, L13 4, L14 2, L17 4, L24 4
    (L7H1 L7H6 L7H29 L8H0 L8H1 L8H8 L8H9 L8H11 L8H14 L9H13 L9H26 L9H28 L10H1 L10H2 L10H3 L10H28 L10H29 L13H5
    L13H18 L13H20 L13H21 L14H4 L14H5 L17H24 L17H25 L17H26 L17H27 L24H17 L24H20 L24H26 L24H27).
  - far exclusive (8): L9H19 L11H9 L11H24 L12H22 L13H10 L14H6 L14H22 L14H27, all in layers 9-14.
  - sdr exclusive (14): L4H13 L4H16 L5H4 L5H5 L5H8 L5H9 L5H11 L5H19 L7H4 L9H12 L9H23 L13H11 L24H18 L24H25;
    8 of 14 in layers 4-5.
  - ser exclusive (10): L7H2 L12H14 L13H8 L15H3 L15H8 L15H9 L15H11 L16H1 L16H22 L16H28; 7 of 10 in layers 15-16.
  - ser D-H: 7 of 19 in layer 12, none in the core.
- Two descriptive observations the spec turns into predictions:
  - **The exclusives sit at different depths**: sdr early (L4-5), far middle (L9-14), ser later (L15-16).
  - **v1 replication candidates**: sdr's exclusives contain L5H8, L5H9, L5H11 and L9H12. The v1 SDR nls0.3
    head-delta flagged L5H8, L5H9 and L9H12 as `unknown/knockout-only` and named L5H11
    (`docs/component-roles.md`, 2026-10-13 amendment). L17H25, v1's near-selector, is in the v2 core.
  - H circuits use layers no D circuit uses: L22 (far H, 7 heads), L30 (all three H, 4-5 heads), L18 (sdr and
    ser H). These H-D late heads are a candidate "honest writer" set.

## Cost model and its sources

| quantity | value used | source |
| --- | --- | --- |
| H100 vs A40 speed, evaluator | 4.0x | drift control 49774554 / 49774563 (401 / 367 s vs 26 min A40), `mv2_cells.py` `SPEEDUP` |
| H100 cold model load, Bridges-2 | 10.5 min per job | 49774554; `mv2_cells.py` `LOAD_MIN`; smoke 458 s |
| evaluator KO cell, H100 | 6.5 min | 26 A40-min / 4.0 (`mv2_cells.py:78-81` `A40_CELL_MIN`) |
| ticket-06 actual | 7.39 H100 GPU-h for 65 cells, 11.0 reconciled | mechanism-datasets ledger, `06-handback.md` |
| knockout sweep, 1,056 Components, n=100 | 9.6 min H200 -> ~13 min H100 | job 22899543 (`sdr-dh-core` `result_summary.md`); H200/H100 ratio 5.4/4.0 |
| per-forward, batch 8 x 128 tokens | A40 0.19 s; H200 0.037 s | `knockout.py` `SECONDS_PER_FORWARD`; memory `interactive-partitions` |
| attention + DLA + single KO, 43 heads | 15.1 min A40 -> ~4 min H100 | job 22899541 |
| path patching, 43-head grid, n=100 | 25.6k forwards per counterfactual -> ~20 min H100 | memory `dh-core-component-analysis`; `path_patching.py:426-435` forward count; unmeasured, dry-run estimate only |
| path patching, ~60-component candidate grid | ~2x the 43-head grid -> ~40 min H100 per counterfactual | quadratic scaling of senders x receivers; to be replaced by `--dry-run` |
| walltime rule | estimate x 1.5, quarter hours | `mv2_cells.py:89-91`; memory `slurm-job-policy` (Oct 25: observed + buffer, not worst case) |

The component-analysis H100 rates are extrapolations; the first phase-1 job is the calibration (ticket 03).

## Open questions (SUPERSEDED 2026-10-25: answered by rulings R1-R8 in spec §9; kept as the record of what was asked)

1. Honest counterfactual: option 2 (Neutral-Clause Twin) recommended; un-reserve "pressure reader"?
2. GPU caps: Bridges-2 35 H100 GPU-h (70 SU of the 177 left; expected use about 19 GPU-h), Delta fallback
   12 GPU-h; +2.5 H100 and +6 Delta if seeds. Per-phase numbers in spec §4 and §6.
3. Push branch `mechanism-analysis` to origin (G14's approval covered mechanism-datasets only).
4. May phase 1 start right after approval, with the hard stop after its reading?
5. Seed replication yes/no.
6. What is "of record" for analysis cells, given `outputs/_analyses/` is git-ignored.
7. The `docs/component-roles.md` amendment (neutral-twin columns, a `response_line` Segment).

## Not verified

- nnsight import and offline behaviour on Bridges-2 (smoke test in ticket 02).
- Any component-analysis timing on an H100 (extrapolated).
- Whether the v1 matched-honest candidate ladder can match v2 clause lengths (only matters for option 1).
- Path-patching grid sizes for the candidate sets (needs `--dry-run`, which ticket 02 can run on the login node).
- Bridges-2 relocation date (Nov 9) is the user's information; PSC pages give no date (docs/bridges2.md).
- Prior work positioning: Campbell et al. 2023 ("Localizing Lying in Llama") and Halawi et al. 2023
  ("Overthinking the Truth") are cited from memory as the closest instructed-lying and honest-then-flip results;
  neither is in `project_context/related_papers.md`. A paper-reading agent should confirm before the paper uses them.

## Revisions after review (2026-10-25; SUPERSEDED by R11 and the sync of 2026-10-25)

R-AB is now the amended rule of spec §2.3 (post-clause ranking, held-out sample, null, greedy selector, readings
renamed "pressure mediators", exhaustive A′ adjudication). The first bullet below is kept as the record only; the
second still holds.

- R-AB has three readings, not two. **A** = separable pressure readers ((i) and (ii)). **A′** = a small set that
  mediates the pressure but also carries the item ((i) only); it is settled in phase 3 as A′-selector or A′-mover.
  **B** = no small set mediates the pressure. Updated in spec §2, ticket 03 (1C) and the plan draft.
- `--reference` binds atomic run dirs only (`component_analysis/intake.py:88-98`, `:129`). Phase 2 binds the six
  circuits as references and derives the membership of core, exclusives and D-H on CPU (spec §4, ticket 04).
