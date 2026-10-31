# 11 — Parameterized review notebook

**What to build:** One notebook whose first cell holds the results directory and a `LIVE` flag. View-only sections render every analysis from the cell directory: head table with role columns, attention patterns in circuitsvis, DLA and path-patching heatmaps and the logit lens in plotly, knockout rankings, segmentation and sample summaries. With `LIVE=True` a final section loads the model once through the same library and offers single-instance attention for one head, DLA on a hand-typed prompt, and one off-grid patch. The researcher runs it; agents do not execute it.

**Blocked by:** 06 — Paired honest-instruction columns; 07 — Per-Component knockout; 09 — Path patching extensions.

**Status:** resolved

- [x] Every section reads only JSON and CSV from the results directory; a missing analysis renders a note, not an error.
- [x] circuitsvis and plotly are added to the environment; the notebook renders them inline.
- [x] Live section imports the analysis library, loads the model once, and exposes the three drill-down calls with the same signatures the CLI uses.
- [x] Notebook correctness verified by reading cell logic, imports and variable references against the output schemas, per the project rule; no execution by an agent.
- [x] A short README section documents the results layout, the CLI, the Slurm script and the notebook.
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

**What was built.** One module and one notebook.
`component_analysis/review.py` is the data seam: it turns a written cell into
four plain shapes (`Table`, `Heatmap`, `Bars`, `Lines`, plus `Scatter` and a
`Group` that holds several), and returns a falsy `Missing` carrying a sentence
for any analysis the cell does not contain. It reads the figure twins rather
than the data of record wherever both exist, so the notebook draws what the
PNG of record drew. It imports no nnsight, torch, plotly or circuitsvis, which
a test asserts in a fresh interpreter, because the login-node base suite has to
import it under Python 3.9.

`review_components.ipynb` sits at the repository root beside
`analyze_components.py` (the repo keeps no notebooks directory). Its first code
cell holds `RESULTS_DIR`, `LIVE`, `REPO_ROOT` and the live section's
instance/head/sender/receiver choices. Sections 1 to 6 render the head table
with the role triple brought forward, attention by Segment as plotly heatmaps
and as circuitsvis coloured Segments, DLA as bars and as a Component-by-
condition heatmap, the paired DLA scatter, the logit lens, the knockout
ranking, both path-patching passes over both counterfactuals, the completeness
sweep, the segmentation and the sample. Section 7 is the live drill-down.

**Files touched.** New: `component_analysis/review.py`, `tests/test_review.py`
(37 tests), `tests/fixtures/review/**` (about 460 KB of trimmed real cells),
`review_components.ipynb`. Modified, both additive: `README.md` (a
"Component-level analysis" section covering the CLI, the results layout, the
Slurm script and the notebook) and `requirements.txt` (three lines plus the
comment explaining why they are `mgnp`-only).

**Environment.** `circuitsvis 1.43.3`, `plotly 7.1.0` and `ipykernel 7.3.0`
went into `mgnp` only; the login base env was not touched. circuitsvis was
installed with `--no-deps` because it pins torch, which then needed
`importlib_metadata 9.0.1` installed explicitly (circuitsvis imports it without
declaring it). plotly brought `narwhals 2.26.0`; ipykernel brought comm,
debugpy, jupyter_client, jupyter_core, nest-asyncio2, platformdirs, pyzmq,
tornado and zipp. Thirteen packages added in all, **none upgraded or removed**:
`pip list --format=freeze` before and after differ only by additions, torch
2.11.0, transformers 5.13.0, numpy 2.5.1 and nnsight 0.7.0 are unchanged, and
`pip check` is clean. ipykernel is one package beyond the ticket's two: without
it the `mgnp` environment cannot be selected as a kernel at all, so
"the notebook renders them inline" would have been unverifiable.

**Tests.** Base env (Python 3.9, with the three BLAS thread variables):
`8 failed, 835 passed, 43 skipped`. mgnp: `8 failed, 948 passed, 19 skipped`.
Both failure sets are the same eight pre-existing names as on the branch base
(one in `test_benchmarks.py`, six in `test_deception_common.py`, one in
`test_deception_tasks.py`), compared by name against baselines taken on
`19f1fb1` before any edit. No new failures. The branch adds 37 passing tests to
each env.

**Slurm.** None. Nothing in this ticket needs a GPU: the notebook is the
researcher's to run, and the project rule forbids an agent executing it. The
live section was verified by reading it against the real signatures of
`hooks.attention_weights`, `dla.measure_batch` and `path_patching`'s three
calls, and against `dataloaders.Batch`.

**How the notebook was verified without running it.** Parsed as nbformat v4
JSON with no stored outputs; every code cell's source joined into one program
and `ast.parse`d; pyflakes run over that program (clean, so no undefined name
and nothing bound only inside `if LIVE:` and read outside it); and every JSON
key the code reaches for checked against the real outputs of record in the
`component-analysis` worktree. pyflakes was installed into `mgnp` for that
check and uninstalled afterwards.

**Decisions taken.**

1. The ticket's "DLA and path-patching heatmaps" was read as asking for a DLA
   heatmap too, so `dla_heatmap` renders every Component against every
   condition beside the per-condition bars. The bars are the analysis's own
   figure; the heatmap is new to the notebook.
2. Role columns are accepted under both spellings (`roles.role_proposed` and
   bare `role_proposed`) for all three of the triple, and a note is rendered
   when none is present. This matches what ticket 10 has since written on its
   branch: `role_confirmed` bare, `roles.role_proposed` namespaced.
3. The family knockout is read from `knockout/knockout_families.json`, the
   name ticket 10 settled on (confirmed by reading its branch), with the older
   guess kept as a fallback pattern.
4. No section was added for ticket 10's `roles/roles.json` or its wider
   `roles.*` columns beyond the triple. They render as ordinary namespaced head-
   table columns; a section devoted to them would have guessed at a schema
   still moving on a parallel branch. Carried to ticket 12.

**Open questions for the researcher.**

- The notebook's default `RESULTS_DIR` points at `ca06-paired2`, but every cell
  of record currently lives in the `component-analysis` worktree, not in the
  main checkout. Running the notebook from the main checkout needs that path
  changed, or the outputs copied across. Ticket 12's run will produce the first
  cell that fills every section at once; today no single cell does, so a
  reviewer will see notes in the sections the cell lacks. That is the intended
  behaviour, not a fault.
- The live section defaults its prompt, target and distractor to the loaded
  instance's own ids rather than to a decode-and-re-encode of them, because
  that does not round-trip through a BPE tokenizer. Typing a prompt into
  `LIVE_PROMPT` switches to the re-tokenizing path, which is what the section is
  for.

**Code review.** `reports/11-notebook-review.md`. Two independent sub-agents
were spawned, one per axis; both ran to completion and both handbacks failed in
the way the brief's 2026-09-16 note describes, and neither report had arrived
after the ten minutes the brief allows. The review recorded is therefore the
author's own pass over both axes, and it is marked as such. It found and fixed
eight things: the DLA heatmap joining its conditions by row number rather than
by Component (a mislabelling bug), an empty `Group` being falsy without a
`note`, a family-knockout glob that would not have matched ticket 10's real
filename, the live attention view drawing over padding, the hand-typed-prompt
demo measuring a re-encoded prompt, a configuration comment that mis-stated K
and V receiver indexing, and the sign conventions being hard-coded in prose
where they could go stale. Nothing was left unaddressed. The last checkbox is
left unticked because the review was not independent.

## Comments (second pass, after the independent reviews)

Both independent reviews arrived after the first pass was written: the
spec-axis one by direct message, the standards-axis one forwarded by the
orchestrator, both after their handbacks failed as the brief predicts. The
orchestrator ruled on which findings to fix. Everything it called for is fixed,
and the last checkbox is now ticked: the review was independent on both axes.

**The blocker they caught that the author's read did not.** `mgnp` had no
`nbformat`, and plotly 7.1 raises `ValueError: Mime type rendering requires
nbformat>=4.2.0` out of `figure.show()` under every notebook renderer, so the
notebook's first figure would have died in the researcher's hands. Reproduced
under `notebook_connected`, `plotly_mimetype`, `jupyterlab` and `vscode`.
`display(figure)` does bypass it, but `nbformat 5.11.1` was installed as well
and `show()` verified working, because a Jupyter environment without
`nbformat` also breaks `plotly.io.to_image` and every other notebook reader.

**The correctness bug they caught.** `mean_tokens` in the segmentation table
counted each Segment's *ranges* rather than their widths, so an eight-token
`intro` split over three ranges printed as 3.0 — in the one table that exists
so that no plot is read against the wrong spans. There is now a test on the
value, not on the column's presence.

**The hazard they caught.** The notebook's dependencies sat in
`requirements.txt`, which the README tells the reader to `pip install -r`, so
following the README would have pulled circuitsvis's torch pin into the
login-node base environment. They now live in `requirements-notebook.txt`,
which spells out the `--no-deps` install and records the verified versions;
`requirements.txt` carries a pointer saying why they are not in it.

**Also fixed:** the hard-coded `REPO_ROOT` `sys.path` insert (it named a
checkout on another branch, and would have imported library code from it);
every analysis's `skipped` entries and the DLA sum check now render as notes,
so a condition that failed no longer reads like one never asked for; a
`checks` key that is absent no longer raises `TypeError` out of a `:.2g`
format, which would have taken down the very section whose job is to print a
note instead of an error; the transpose test compares an off-diagonal cell,
the only place it could ever have disagreed with the code; role columns are
reported one at a time, since `role_confirmed` is absent by design and the
other two are not; hover text on hover rather than printed across the bars;
error bands drawn on the logit lens; the live cells render a note instead of a
traceback when the cell has no head table or no sample; the README now
describes the Slurm script's partition, account, resources, time budget, logs
and `--dry-run`.

**Duplication removed.** The standards reviewer showed the duplicated
subdirectory and file-name constants were justified by a wrong reason: only
`attention_patterns.py` imports torch at module scope, verified by parsing each
module's top-level imports. They are now imported from `dla`, `knockout`,
`path_patching` and `head_table`, and the Component label delegates to
`dla.label_of` — which the reviewer noticed the copy had already drifted from.
Only `ATTENTION_SUBDIR` stays spelled out, with the narrowed reason.

**Ticket 10 alignment.** Its real outputs were read from its worktree and
copied into two new fixtures. The head-table section finds
`roles.role_proposed` and `roles.role_notes` and says, in its own note, that
`role_confirmed` is the researcher's column and no tool writes it. The family
knockout reads `knockout/knockout_families.json` and is tested against ticket
10's real file (three families: unknown, selector, mover), rendering its
`grouping` block so the reader sees which column the families came from. Its
`roles/roles.json` and the wider `roles.*` columns render as ordinary
namespaced head-table columns; no section is devoted to them, which is carried
to ticket 12.

**Environment, final.** `mgnp` only, still nothing upgraded or removed:
circuitsvis 1.43.3, importlib_metadata 9.0.1, plotly 7.1.0, nbformat 5.11.1,
ipykernel 7.3.0, plus their transitive additions. torch 2.11.0, transformers
5.13.0, numpy 2.5.1 and nnsight 0.7.0 unchanged; `pip check` clean.

**Tests, final.** Base: `8 failed, 844 passed, 43 skipped`. mgnp: `8 failed,
956 passed, 19 skipped, 1 error`. The eight names match the branch-base
baseline in both environments. The one mgnp error is **not** from this branch:
`test_paired_honest_cli.py` failed at setup because `dataset/item_pairs.json`
did not parse during that run. It parses now, the file is unmodified in this
worktree (`git status` clean for `data/` and `dataset/`), and the whole file
passes on a re-run — a shared pool file being written by something else while
the suite read it. Worth knowing for whoever merges: a concurrent write to the
shared pools can make any suite in any worktree fail at collection.

**Files touched, final.** New: `component_analysis/review.py`,
`tests/test_review.py` (46 tests), `tests/fixtures/review/**` (about 640 KB,
seven cells, trimmed copies of real outputs from tickets 03, 06, 07, 09 and
10), `review_components.ipynb`, `requirements-notebook.txt`. Modified:
`README.md` and `requirements.txt`, both additive.

**Commits.** `467e81c`, `847b29b`, `9b30968`, `a4eabab`, `1a7b4a1`, `7e31237`.
The full review, all three passes and the judgement calls left unfixed, is in
`reports/11-notebook-review.md`.

## Comments (third pass — the role-family columns)

The orchestrator's re-check found one item not yet done: ticket 10's family
knockout writes two head-table columns, and it is renaming them from
`knockout.family` to `knockout.role_family`. Both spellings are now accepted,
the two columns are ordered directly after the role triple (the family a
Component was grouped into is read with its role, not twenty columns later
among the rest of the knockout numbers), and a cell without them carries a note
naming both spellings. Tested against ticket 10's real `ca10-family` head
table, which carries the current spelling, and against a hand-built one in the
renamed spelling. Commit `d4c3186`.

Every other item on the re-check list was already on the branch, in `1a7b4a1`
and `7e31237`, both of which land after the `a4eabab` the re-check was made
against. Verified one by one: nbformat installed and in the notebook
requirements; `mean_tokens` summing half-open spans with a value test; the
`REPO_ROOT` insert gone (zero occurrences); `skipped_notes` and the DLA sum
check; the off-diagonal transpose assertion; `hovertext`; the lens error bands;
`LIVE_READY`; `_number` guarding the sum-to-one note; `render` testing falsiness
first; `requirements-notebook.txt` with the `--no-deps` command and the README
pointing at it; the constants and `label_of` imported from their owning modules
with `HEAD_TABLE_CSV` gone; the house docstring header; `ROW_AXIS`; the dead
glob filters removed; `is None`; the overlap sentence test; the fixture built
through `head_table.write_head_table` with the `__future__` import. One
correction made in passing: the requirements file recorded nbformat as 5.10.4
where the installed version is 5.11.1.

**Tests, final.** Base: `8 failed, 848 passed, 43 skipped`. mgnp: `8 failed,
961 passed, 19 skipped`. The same eight names as the branch-base baseline in
both environments, and the transient `item_pairs.json` parse error noted in the
second pass did not recur. 50 tests in `tests/test_review.py`.

**Commits, final.** `467e81c`, `847b29b`, `9b30968`, `a4eabab`, `1a7b4a1`,
`7e31237`, `d4c3186`.
