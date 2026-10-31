# Shared brief for ticket-implementing subagents (component-analysis)

You are implementing one ticket of the component-analysis feature in the
`Deception-Circuit` repo. The orchestrator will tell you the ticket path, the
worktree path and the branch. Read this whole file before starting.

## Implement instructions (from /mattpocock-skills:implement, passed verbatim)

> Implement the work described by the user in the spec or tickets.
>
> Use /tdd where possible, at pre-agreed seams.
>
> Run typechecking regularly, single test files regularly, and the full test
> suite once at the end.
>
> Once done, use /code-review to review the work.
>
> Commit your work to the current branch.

Invoke the `mattpocock-skills:tdd` skill via the Skill tool before writing
code, and `mattpocock-skills:code-review` at the end (fixed point: the branch
base commit the orchestrator gives you). If the code-review skill cannot spawn
its own sub-agents from where you run, do both axes (Standards, Spec) yourself
in one pass and say so in the report.

## Must-read files (in this order)

1. The ticket file (path given by the orchestrator). Its checkboxes are the
   acceptance criteria.
2. `Alignment/.scratch/component-analysis/spec.md` (Implementation Decisions
   and Testing Decisions sections are binding).
3. `Deception-Circuit/CONTEXT.md`, section "Prompt anatomy (component
   analysis)" and the task-structure terms. Use the glossary's vocabulary in
   code names, test names and docs; do not drift to the terms it says to
   avoid.
4. `Deception-Circuit/docs/adr/0001-component-analysis-on-raw-hf-model.md`.
   If your work would contradict it, say so explicitly in the ticket comments
   rather than silently overriding.
5. `Deception-Circuit/docs/research/interp-tooling.md` (nnsight 0.7.0 facts,
   GQA layout, memory constraints under eager attention).
6. Prior art named in the spec's Testing Decisions: `tests/helpers.py`,
   `tests/fakes.py`, `tests/test_end_to_end.py`, `tests/test_evaluation.py`,
   `tests/test_deception_common.py`.

## Where you may work

- Only inside the worktree path the orchestrator gives you, plus the ticket
  file and `Alignment/.scratch/component-analysis/reports/`.
- Never edit the main checkout at `Alignment/Deception-Circuit` (the
  researcher runs live experiments there) or any other worktree.
- Commit to the current branch of your worktree. Do not push. Do not rebase or
  merge; the orchestrator does that.
- Small, well-described commits. Commit message: imperative subject that says
  why, a body if needed, ending with
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Data and run directories

- The SDR nls0.3 run is `outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414`
  and its honest twin is `outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525`.
  Their tracked files (config, active_nodes, results) and the `data/datasets/sdr*`
  datasets are in git, so your worktree has them. If a file you need is
  untracked (e.g. a mask tensor), reference it by absolute path into the main
  checkout `/projects/beto/swong2/Alignment/Deception-Circuit/...`; never copy
  large files into the worktree and never modify the main checkout.
- Analysis outputs go under your worktree's `outputs/_analyses/<suite>/<circuit>/<task>/`.
  Do not commit analysis outputs, logs or core dumps. Delete any `core.*` file.

## Environments (two, both matter)

| | login-node base | `mgnp` (Slurm jobs, and nnsight) |
|---|---|---|
| python | `/sw/external/python/anaconda3/bin/python` (3.9) | `conda activate mgnp` (3.12) |
| transformers / torch | 4.57.3 / 2.8.0 | 5.13.0 / 2.11.0 |
| nnsight | **0.5.12 is present** (for the parent Alignment repo) | 0.7.0 (installed by ticket 01) |

- Activate mgnp with `source /sw/external/python/anaconda3/etc/profile.d/conda.sh && conda activate mgnp`.
- The base env has nnsight 0.5.12, so `pytest.importorskip("nnsight")` does
  NOT skip there. Gate nnsight tests on the version being exactly 0.7.0 (see
  how `tests/test_nnsight_hooks.py` does it) so 0.7.0 assertions never run
  against 0.5.12. Pure-Python parts (segmentation, sampling,
  coarsening, head-table IO) must not import nnsight at module import time.
- Run the base-env suite with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`
  (otherwise BLAS can segfault during collection).
- Before editing, record the baseline failing test names on your branch base
  (both envs) and judge "no new failures" by name, not count. Known
  pre-existing failures include `test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py`
  (fails only because of worktree location) and several
  `test_deception_common`/`test_deception_tasks` failures; re-derive the list
  rather than trusting this note.
- No GPU on the login node. GPU work goes through Slurm on `gpuA100x4` or
  `gpuA40x4` (account `beto-delta-gpu`), mirroring `scripts/evaluate_circuit.sbatch`.
  You may submit jobs and read their outputs; since 2026-10-13 there is no
  one-hour cap, and multi-hour jobs, `gpuA100x4` and `gpuH200x8` are all
  allowed when they make a run simpler or faster (pick the partition by queue
  length; put `--time` on the command line). Run `--dry-run` on the login
  node before every submission. Submit from your worktree root so relative
  paths resolve there. Wait for jobs by polling `squeue -u $USER` with sleeps
  in the background, not by blocking.

## Ticket bookkeeping

- At start: set the ticket's `**Status:**` line to `claimed`.
- Tick each checkbox (`- [x]`) as you verify it. Leave unticked anything you
  could not do and explain why under `## Comments`.
- At the end: append a `## Comments` section (or extend it) with: what was
  built, files touched, test results by env (counts plus any new failure
  names), Slurm job ids and what their outputs showed, open questions for the
  researcher, and the code-review outcome. Then set `**Status:**` to
  `resolved` (or leave `claimed` with a clear blocker note if incomplete).
- Write the code-review output to
  `Alignment/.scratch/component-analysis/reports/<NN>-<slug>-review.md`
  and state in the ticket which findings you addressed and which you did not.

## Design rules that apply to every ticket

- The package is `component_analysis/` (ticket 01): `components.py`
  (Component dataclass, `circuit_components`, `is_component_of`),
  `head_table.py` (`rows_from_components`, `merge_columns(rows, updates, *,
  namespace)`, `write_head_table(cell_dir, rows, *, meta)`,
  `load_head_table(cell_dir)`, `row_key`, `columns_of`), `intake.py`
  (`resolve_intake(cli)`, `analyses_root`, `cell_dir`) and the single nnsight
  hook module `component_analysis/hooks.py` (`load_analysis_model` only so
  far). CLI is `analyze_components.py`. Read ticket 01's `## Comments` for the
  API details and two nnsight 0.7.0 gotchas (execution-order Envoy access;
  saving `self_attn.output[1]` under SDPA).
- All nnsight access goes in `component_analysis/hooks.py` as small functions;
  a test fails if any other module in the package imports nnsight. Do not add
  a second hook path. Do not instantiate the prunable wrapper.
- Head table: one row per Component keyed by (kind, layer, index); each
  analysis adds namespaced columns via `merge_columns`; `role_confirmed` is
  protected.
- The first ticket that loads the real model on a GPU must make a successful
  `load_analysis_model` call its first assertion; it is untested so far.
- Every figure: matplotlib PNG plus a JSON twin. `--dry-run` never touches a
  GPU and never writes analysis outputs beyond what the ticket says.
- Tests assert at seams the caller sees (written files, returned numbers),
  never hook wiring. Invariant tests that require the circuit to be the full
  model must set it so explicitly.
- Keep shared files (CLI registration, hook module, head-table helper, sbatch)
  changes minimal and additive: other tickets are being implemented in
  parallel on sibling branches and the orchestrator will rebase them linearly.
  Put new analyses in their own module under the analysis package.

## Final report to the orchestrator

Reply with: ticket status, commits (hashes and subjects), test results per env
(with new-failure names if any), Slurm jobs run and their verdict, shared files
you changed (so merges can be planned), unresolved review findings, and any
decision the researcher must make.

## Researcher decisions so far

- 2026-09-15: the first GPU analyses target the SDR nls0.3 circuit at **head
  granularity delta** (`sdr \ honest` coarsened at the head level, 17 heads
  + 1 MLP), not the leaf delta, because at nls0.3 the leaf delta equals the
  atomic circuit. Bind `sdr` and `honest` as circuits and use the head-level
  delta expression ticket 01 verified; keep `honest` as the reference circuit.
- Worktrees stay under `Deception-Circuit/.claude/worktrees/`.
- 2026-09-15 (after block B): the Honest-Instruction Counterfactual uses the
  **clean-stream-only** honest criterion by default (629 SDR instances over 14
  clauses); both-streams stays available as a robustness subset. The two
  question mentions of each item are **separate Segments** (pair-naming
  mention vs quoted-option mention); the glossary's mention count is four.
  The ".T"/"HE" token shared by the Designating Sentence and the Designation
  Suffix in the saved SDR prompts is accepted with the sentence winning; the
  researcher plans to regenerate FAR/SDR/SER datasets later with the space
  fixed. Stratified sampling is **as balanced as possible across strata**,
  not proportional. CONTEXT.md gets a carve-out so "template piece" may name
  a TemplateVariant field. Co-author lines naming the model that did the
  work are fine.
- 2026-09-15 (entering block C): block B follow-ups and the ticket 01
  independent-review fixes are merged (`component-analysis` at 2cbcac4).
  Block C runs as one serial scaffold ticket (02b: shared forward passes in
  the hook module, analysis registration seam, causal dataloader joined by
  instance id, Slurm script, first GPU model load) followed by tickets 03,
  04, 07 and 08 in parallel on sibling branches cut from the scaffold's tip.
- 2026-09-16 (block C parallel wave): the scaffold (ticket 02b) is merged;
  `component-analysis` is at 917474d. Tickets 03, 04, 07 and 08 run in
  parallel on branches cut from that tip. Each adds one module under
  `component_analysis/` and replaces only its own placeholder line in
  `registry.ANALYSES`; none touches `hooks.py` (receivers, the fp32
  `readout_logits` seam, `geometry`, `device_and_dtype` already exist there),
  the dataloaders, or another ticket's files. The seam notes and A40 timings
  are in ticket 02b's `## Comments`. Causal loaders cover FAR, SDR and SER
  only (STD refused by name; separate ticket if wanted). The independent
  review sub-agents' handbacks fail when the parent has exited, but their
  reports do arrive by SendMessage: check the inbox before declaring a
  review non-independent, and do not wait more than about ten minutes.
- 2026-09-16 (block C merged): tickets 03, 04, 07 and 08 are on
  `component-analysis` (tip a74d54b) with the scaffold. Conventions settled
  during the wave, binding for later tickets: every analysis flag carries its
  analysis prefix (ticket 03 owns `--query-positions` and `--split`); head-table
  columns are `<namespace>.<bare name>` with no analysis prefix inside the
  name; columns computed on the unpaired honest-twin dataset end in
  `_descriptive`; "paired" columns are computed over the same instance ids
  on both sides; ranking metrics are read through `readout_logits` from
  `capture_forward(..., replacements=...)`, never `replace_forward`'s bf16
  logits; a Readout-receiver replacement must be read from
  `capture.outputs[READOUT_KEY]`. Open code items carried into block D:
  remove `--path-instances` (ticket 08); the path-patching sign convention
  (negative = helps deception) versus knockout's positive drop should be
  reconciled or documented in the roles vocabulary (ticket 10).

- 2026-09-16 (entering block D): the researcher accepted all five block C
  proposals. (1) Sign conventions: knockout keeps positive = helps deception
  and path patching keeps negative = helps deception for now; every JSON
  states its convention in its meta, and ticket 10 settles one convention in
  the roles vocabulary. (2) Remove `--path-instances` from
  `component_analysis/path_patching.py` (ticket 09 does it; a small, separate
  commit). (3) Ticket 06 shrinks: ticket 04 already built
  `dla.honest_instruction`, `dla.pressure_paired`, `dla.differential` and the
  paired DLA condition; 06 keeps the flag that selects the paired condition
  for the descriptive analyses (reuse ticket 04's mechanism where one
  exists), the paired DLA scatter PNG, the two-condition logit-lens overlay,
  and the paired attention side (attention column plus top Segment under the
  honest instruction). (4) STD stays out of the causal analyses; a separate
  ticket if wanted. (5) K/V receivers stay per KV group and cover non-circuit
  heads; the JSON records the coverage. Block C outputs of record were copied
  into the `component-analysis` worktree under `outputs/_analyses/`
  (`ca03-attention`, `ca03-attention-sink`, `dla-verify3`, `ca07-knockout`,
  `ca08-path-patching`) before the block C worktrees were removed. Tickets
  06 and 09 run in parallel on `ca/06-paired-honest-columns` and
  `ca/09-path-patching-extensions`, both cut from a74d54b; ticket 06 owns
  `attention_patterns.py` and `dla.py`, ticket 09 owns `path_patching.py`;
  changes to shared files (`analyze_components.py`, `dataloaders.py`,
  `hooks.py`, `registry.py`, the sbatch, the shared tests) stay minimal and
  additive so the orchestrator can rebase them linearly.

- 2026-09-20 (block D, second wave): tickets 06 and 09 are merged;
  `component-analysis` is at 19f1fb1 (base suite 8 failed / 798 passed, the
  same 8 names). Every block C and D output of record now lives in the
  `component-analysis` worktree under `outputs/_analyses/` (`ca03-attention`,
  `ca03-attention-sink`, `dla-verify3`, `ca07-knockout`, `ca08-path-patching`,
  `ca06-paired2`, `ca09-path-patching`, `ca09-sweep`); read schemas from there.
  Tickets 10 and 11 run in parallel on `ca/10-role-vocabulary-and-proposal`
  and `ca/11-notebook`, both cut from 19f1fb1 (their blocking edges are 06, 07
  and 09 only). Ticket 10 also carries the small `--dla-conditions`
  parse-time validation fix ticket 06 left (two lines in `dla.py`, one in
  `tests/test_dla_model.py`) and settles the sign convention across analyses
  in the roles vocabulary: any sign change is a new head-table column, never
  a rewrite of an output of record. Ticket 12 follows both.

- 2026-09-20 (later): ticket 11 merged by fast-forward (shared files:
  README.md, requirements.txt pointer, new requirements-notebook.txt);
  `component-analysis` at 7e31237. The notebook is `review_components.ipynb`
  at the repo root with its seam in `component_analysis/review.py`; the mgnp
  env gained circuitsvis, plotly, nbformat and ipykernel (see
  requirements-notebook.txt). Ticket 10 rebases onto 7e31237 next
  (`git rebase --onto component-analysis 19f1fb1`); it touches
  `analyze_components.py`, `knockout.py`, `dla.py`, `tests/test_dla_model.py`,
  the shared nnsight probe and docs, none of which ticket 11 changed.
  Ticket 12 follows, cut from the tip after both are in.

- 2026-09-20 (ticket 10 merged): `component-analysis` at c0ad373 (ticket 10's
  eleven commits rebased onto d4c3186, plus the orchestrator folding
  `component_analysis.review` into the shared nnsight probe). Roles of record
  on SDR nls0.3 at head-level delta: 0 binder, 0 selector, 1 mover (L31 MLP),
  0 suppressor, 17 unknown, after the path floor moved from 0.005 to 0.01
  (twice the cross-card noise; logged in docs/component-roles.md). The
  family knockout of record is job 22238754 (`outputs/_analyses/ca10-family2`);
  roles table in `ca10-roles`. The `roles` subcommand of analyze_components.py
  runs on the login node; any analysis rerun into a cell now carries
  `role_confirmed` and `roles.*` forward. Ticket 12 is cut from c0ad373 on
  `ca/12-first-sdr-run-and-writeup`; it is the last ticket of block D.
  Researcher decisions still open from block D (for the pause): ticket 06's
  five, ticket 09's four, ticket 10's eight (listed in the tickets).

- 2026-09-21 (block D complete): ticket 12 merged by fast-forward;
  `component-analysis` at 3c66f4c. The first full SDR nls0.3 run is the cell
  of record `outputs/_analyses/sdr-first-run/delta__head/sdr/` (with
  `result_summary.md` committed there, and `scripts/check_cell.py` to
  validate a cell through the notebook seam); the sweep is
  `sdr-first-run-sweep`, staging cells `sdr-first-run-desc/-paths/-paths-hi/
  -family` (Slurm 22240028, 22240066, 22240067, 22240068, 22281702, all A40).
  Every shared value is byte-identical to the block C/D verification cells.
  Roles: 0/0/1/0/17. Scheduling lesson: shorter `--time` backfills sooner;
  A40 queue waits ran 12 min to 13 h. Researcher decisions are collected at
  the end of `result_summary.md` and in tickets 06, 09, 10, 12. Nothing is
  pushed; the branch has never been merged to main.

- 2026-10-13 (block E, researcher decisions on the SDR first run and new
  requests): the head-granularity delta stays the object for now (the
  researcher is analysing other circuits in other sessions). The seven
  non-circuit Components the sweep flagged are evidence the circuit is
  incomplete; leave them. The Q-versus-V reading, L17H25 (unknown, selector
  lean), the suppressor carve-out, `question` as a frame, and L14H7 all stay
  as they are. No fifth role: early heads that matter on knockout alone get
  the `unknown` flavour `unknown/knockout-only` until there is reads
  evidence. No extra attention run at another query position for
  sdr-first-run now (it is the cheap experiment for later).
  `attention_patterns.pressure_paired_*` stays. **"paired" goes into every
  paired column name.** Paired columns stay on the causal sample. The
  71-versus-100 coverage goes into the head table **meta, per column** (n
  and the instance set), not into names. **Multi-job cells are the normal
  workflow: the CLI carries every analysis's columns forward** on a rerun
  into a cell; copy-then-merge is not the workflow. **The one-hour job
  budget is lifted**: multi-hour jobs, A100 and H200 are all fine when they
  make a run simpler or faster; still rehearse with `--dry-run` and still put
  `--time` on the command line. `--path-position-threshold` keeps its default
  and is tuned by hand per run. The roles pass does not write
  `role_confirmed`. No A100 bit-identity rerun. New analyses requested:
  (1) attention heatmaps in a colour scheme readable under a strong blue-light
  filter, and a segmentless token-by-token attention rendering as PNGs (JSON
  only if it stays small); (2) a knockout completeness sweep over every
  Component of the model on the same 100 instances as the single knockouts;
  (3) **path patching's sign convention flips to agree with knockout:
  positive = helps deception** (the JSON meta states it, old cells of record
  keep their old sign and are told apart by the meta); (4) the path-patching
  completeness sweep runs on the grid's own 100 instances. Block E tickets:
  13 (serial: conventions, coverage meta, carry-forward, budget), then 14,
  15, 16 in parallel; implementers run on opus.

- 2026-10-13 (ticket 13 merged): `component-analysis` at 4ba2877. The
  old-to-new column name table is in ticket 13's Comments and in
  `head_table.LEGACY_COLUMNS` (the one translation point); "paired" means
  the honest-instruction pairing only. Per-column coverage lives in
  `head_table.json` meta (`coverage`, `instance_sets`), declared through
  `ctx.declare_coverage`. `analyze_components.carry_forward` keeps every
  column of a cell except the namespaces of the analyses that run, so a cell
  is assembled by running jobs into it (a run replaces its whole namespace;
  rerun the roles pass afterwards). `unknown/knockout-only` requires the
  DLA and path views to have been measured. Tickets 14, 15, 16 run in
  parallel from 4ba2877 on `ca-14`, `ca-15`, `ca-16`; ticket 14 owns
  `path_patching.py` and applies the `<name>_paired_se` suffix order when it
  renames the sign-flipped columns, and `LEGACY_COLUMNS` must never map a
  column whose meaning changed (so the flipped columns need new names or a
  meta marker every reader checks); ticket 15 owns `knockout.py`; ticket 16
  owns `attention_patterns.py`. Pick Slurm partitions by queue length and
  accounts by fairshare (see memory `slurm-account-priority`).

- 2026-10-13 (ticket 16 merged): `component-analysis` at 4fb2c66. Attention
  figures use `YlOrRd` (one constant, recorded in every twin); the token-level
  rendering is `component_analysis/attention_token_level.py` behind
  `--attention-token-level` and `--attention-token-level-json-limit`; outputs
  of record `outputs/_analyses/ca16-token-level2` (jobs 22874579, 22875076,
  A100 under bgrb-delta-gpu). Tickets 14 and 15 rebase onto 4fb2c66
  (`git rebase --onto component-analysis 4ba2877`); the only seam file 16
  touched is the shared nnsight probe list in tests/test_component_analysis.py.

- 2026-10-13 (ticket 14 merged): `component-analysis` at 201929d (ticket 14's
  nine commits rebased cleanly onto 4fb2c66). Path patching now reports
  (clean - patched)/(clean - counterfactual): **positive = helps deception**,
  the same sign as knockout. Every path-patching JSON carries
  `metric.convention = "positive_helps_deception"` (absent = legacy); the
  sign-flipped head-table columns have new `*_support` names and
  `LEGACY_COLUMNS` maps neither generation into the other; the roles pass
  reads new cells natively, negates legacy ones, and refuses a cell whose
  JSON marker disagrees with its columns. The sweep runs on the grid's
  sample. Output of record `outputs/_analyses/ca14-path-patching-2` (job
  22874991, A100, bimc-delta-gpu, 40 min; all 393 cells the exact negation of
  ticket 08's A100 cell). Cells of record written before 2026-10-13 are in
  the legacy sign and are labelled so wherever read. Ticket 15 rebases onto
  201929d (`git rebase --onto component-analysis 4ba2877`).

- 2026-10-13 (block E complete): ticket 15 merged after a rebase onto
  201929d with one README conflict (both sides kept); `component-analysis`
  at 4086e12. `--knockout-completeness-sweep` knocks out every head and MLP
  block (1056, embedding excluded) on the grid's sample through
  `knock_out_groups`; output `knockout/sweep.json` + `sweep.png`; of record
  `outputs/_analyses/ca15-knockout-sweep` (job 22874364, A100x8,
  bgrb-delta-gpu, 23 min). On knockout the circuit's best member L17H25 ranks
  20th; mlp.0.0 removes almost the whole margin; 90 outsiders clear 0.1.
  `knockout.py` imports `path_patching.label` at module scope. Every block E
  output of record is in the `component-analysis` worktree
  (`ca14-path-patching-2`, `ca15-knockout-sweep`, `ca16-token-level2`). The
  cells of record from blocks C and D are in the legacy path-patching sign
  and the pre-13 column names; the next full SDR run should be redone under
  the new conventions (not yet ticketed).

- 2026-10-14 (block E decisions): knockout sweep threshold default **0.4**
  (tune by hand later; the full ranked list stays in sweep.json). The layer 0
  MLP stays in the knockout sweep and its figures, labelled a **positive
  control**, and is left out of the outside-the-circuit count the way the
  embedding is. `--path-sweep-threshold` defaults to **0.05** and no longer
  follows `--path-position-threshold`. `unknown/knockout-only` is applied
  literally (the six early heads); L5H11, L14H7 and L14H22 are mentioned
  separately as heads with both a knockout effect and an established read.
  Token-level rendering choices accepted as they are. No SDR rerun under the
  new conventions; a caveat in the cells of record and the write-up is enough.
  Ticket 17 carries the code and doc changes.

- 2026-10-14 (ticket 17 merged, block E closed): `component-analysis` at
  fa02314. Knockout sweep default 0.4 (`DEFAULT_SWEEP_THRESHOLD_LOGITS`,
  ladder 0.02/0.05/0.1/0.2/0.4), the layer 0 MLP a labelled positive control
  (`positive_control` key, CONTEXT.md entry) outside the outsider count;
  `--path-sweep-threshold` default 0.05 on its own
  (`DEFAULT_SWEEP_THRESHOLD_GAP_FRACTION`); roles note "knockout effect with
  an established read" (L5H11, L14H7, L14H22); a legacy caveat at the top of
  the committed SDR write-up and an ignored `LEGACY.md` in each of 18 cells
  of record under the `component-analysis` worktree (ca15-knockout-sweep's
  says its flagged list was written at 0.1). Base suite on fa02314: 8 failed
  / 1024 passed, the same 8 names. Open researcher items from 17: whether to
  rerun ca15-knockout-sweep at 0.4 (23 min on an A100); POSITIVE_CONTROLS is
  keyed to any model's layer 0 MLP but measured on Llama-3.1-8B SDR only.

## Orchestrator's merge procedure (for whoever merges block D)

- Each ticket branch is rebased in its own worktree with
  `git rebase --onto component-analysis <its base commit>` and then
  fast-forwarded into the `component-analysis` worktree; never merge commits.
- Agents were told to cherry-pick orchestrator seam commits mid-ticket. On
  rebase those replays either drop as redundant or conflict on the seam files
  (`component_analysis/hooks.py`, `tests/test_component_hooks.py`,
  `tests/test_analyze_components_end_to_end.py`,
  `tests/test_component_analysis.py`); resolve those files with
  `git checkout --ours` (the integration side), and if the replay is then
  empty, `git rebase --skip`. Any other conflict is real: abort and read it.
- Run git and both suites in the background with long timeouts; Lustre can
  hang a single write for 15+ minutes (see memory).
- After the last branch of a block: fold each ticket's module into the shared
  nnsight probe in `tests/test_component_analysis.py`, run both suites on the
  tip, compare failure names to the 8-name baseline, then pause.
- Block C ended with `component-analysis` at a74d54b (51 commits over the docs
  commit). Block D order: 06 and 09 in parallel (cut from the tip), then 10,
  then 11 and 12.
- 2026-09-16: ticket 06 merged by fast-forward (no shared files touched);
  `component-analysis` at 07bbe43. Ticket 09 (`ca/09-path-patching-extensions`,
  base a74d54b, four files, none shared) is next: rebase --onto 07bbe43 a74d54b,
  then fast-forward. Ticket 06's outputs of record are `outputs/_analyses/ca06-paired2`
  (Slurm jobs 22123694 and 22124402).
