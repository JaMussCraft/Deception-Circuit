# 06 — Paired honest-instruction columns for the descriptive analyses

**What to build:** Attention patterns, DLA and the logit lens gain a paired condition: the same instances under their Matched Honest Instruction. The head table gains differential DLA (pressure minus honest, per Component), a paired attention column, and the honest-condition logit lens, so a Component that flips sign is separable from a mover that does not know it is lying.

**Blocked by:** 03 — Attention patterns by Segment; 04 — Direct logit attribution and logit lens; 05 — Matched Honest Instruction pool.

**Status:** resolved

- [x] `--honest-counterfactual` loads the paired dataset from ticket 05 and runs the descriptive analyses on both prompts of each pair.
- [x] Head-table columns: dla_honest_instruction, dla_differential, top Segment under honest instruction; the columns are labelled paired, distinct from the descriptive honest-twin columns.
- [x] PNG: paired DLA scatter (pressure vs honest) with Components labelled; logit lens with both conditions overlaid.
- [x] Test: CLI seam run with a synthetic paired dataset produces the paired columns and JSON.
- [x] Verified by a short Slurm run on SDR; differential column non-trivial for at least some Components.
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

Five commits on `ca/06-paired-honest-columns`, base `a74d54b`:

    c7b4d37  Pair the honest-instruction columns to the same instances
    57bbf24  Give the paired scatter a second panel so every Component is readable
    e1a8520  Say how many batches the paired condition has, not how many reads
    6d1c5dd  Address the independent code review of ticket 06
    07bbe43  Let the flag say what it refused and what it would accept

**No shared file was touched.** Not `registry.py`, `hooks.py`, `dataloaders.py`,
`analyze_components.py`, `scripts/analyze_components.sbatch`, nor any existing
test file. The two new test files are new. The rebase should be clean.

`component_analysis/attention_patterns.py` gains:

    --attention-conditions NAME[,NAME]   default pressure,honest_instruction,honest_twin
    wanted_conditions(cli)               validated by name, like dla's
    PRESSURE_PAIRED                      a derived condition, not selectable
    paired_rows(batch, known)            the one row selector both sides use
    pressure_paired_slices(...)          the paired contrast's left term
    COLUMN_PREFIXES                      condition -> head-table column prefix

`component_analysis/dla.py` gains:

    dla/dla_paired_scatter.json / .png   the paired contrast, one point per Component
    dla/logit_lens_paired.json / .png    the lens over the two paired conditions only
    paired_scatter_payload / paired_lens_payload / paired_lens_figure_payload
    plot_paired_scatter / zoom_limit / _scatter_panel
    plot_lens(..., title=, empty_message=)   two additive keyword arguments

### The one decision worth arguing about: `pressure_paired` on the attention side

**This is beyond the ticket's literal scope and the researcher can reject it.**

Ticket 03 already computed the paired `honest_instruction` attention condition
into `patterns.json` and left its head-table column to this ticket. Adding the
column alone would have put `attention_patterns.honest_instruction_top_segment`
(71 instances) in the same CSV row as
`attention_patterns.pressure_top_segment` (1000 instances), with nothing
between them to say the two are not comparable. A reader comparing them would
be doing the population-versus-causal comparison **spec user story 27 exists to
prevent**, and the block C rule that *"paired" means the same instance ids on
both sides* would be false of the only paired column in the analysis.

DLA had the same problem in ticket 04 and solved it with `dla.pressure_paired`.
This does the same thing: the Pressure Clause on exactly the rows that have an
Honest-Instruction Counterfactual. It costs one extra pass over 13 batches,
about 20 seconds of the run's 10:45. Both sides pick their rows through one
function, `paired_rows`, and a test asserts both that they read the same ids and
that the left side carries the *pressure* prompt — the bug that would otherwise
make every paired difference zero and look like a finding.

### The three deviations from the orchestrator's wording

1. **The flag is `--attention-conditions`, not `--honest-counterfactual`.** The
   block C rule says every analysis flag carries its analysis prefix, with a
   carve-out only for a dataset choice shared by several analyses. This is not
   one: DLA already selects the paired condition with `--dla-conditions
   honest_instruction`, and the attention side now does the same with
   `--attention-conditions`. Semantics are identical between the two, on
   purpose. **No unprefixed flag was added.**
2. **The namespace is `attention_patterns.`, not `attention.`.** The
   orchestrator's brief said `attention.<bare name>`, but the namespace is the
   module's `NAME`, which ticket 03 fixed as `attention_patterns` and which the
   `ca03-attention` outputs of record already use. `attention` is the `SUBDIR`.
   Renaming `NAME` would break the block C outputs the researcher kept. Not
   done; flagged here.
3. **The paired columns carry no `_paired` in their names.** Block C's binding
   rule distinguishes paired from descriptive by putting `_descriptive` on the
   twin columns and leaving paired ones bare, which is what
   `dla.honest_instruction` does. Putting `_paired` on the attention columns
   alone would make the two analyses inconsistent inside one CSV, and renaming
   `dla.honest_instruction` and `dla.differential` would change shipped,
   reviewed columns with GPU outputs behind them. **This is ticket 04's open
   question 2 and it is carried forward, not settled** — see below.

### The head-table columns this ticket adds

    attention_patterns.pressure_paired_top_segment / _top_mass
    attention_patterns.honest_instruction_top_segment / _top_mass

Beside ticket 03's `pressure_*` and `honest_twin_descriptive_*`. Every condition
now gets its columns whether or not it ran, empty rather than absent, so head
tables from different cells still line up.

### The GPU verification

Job **22123694**, `gpuA40x4`, **10:45**, `COMPLETED`, and job **22124402**,
**10:48**, `COMPLETED`, which re-runs the same command on the final code because
the review fixes changed the JSON schema (`instance_ids` per condition, `zoom`
and `panel` in the scatter twin). **No measured quantity differs between the
two**; the numbers below are 22124402's and the outputs of record are under
`outputs/_analyses/ca06-paired2/`. Both were submitted with `--time=00:45:00` on
the command line so the script's four-hour default did not apply (the sbatch
itself is untouched), and both were rehearsed with `--dry-run` on the login node
first:

    sbatch --time=00:45:00 --partition=gpuA40x4 scripts/analyze_components.sbatch \
      --circuit sdr=<nls0.3 run> --circuit honest_c=<honest twin run> \
      --reference honest=<honest twin run> --expr "delta=sdr \ honest_c" \
      --compose-granularity head --task-from <nls0.3 run> \
      --analyses attention_patterns,dla --dla-split designation \
      --suite-name ca06-paired2 --output-dir outputs/_analyses/ca06-paired2

**The pair is a pair, and the file says so by id.** `patterns.json` reports
`pressure_paired` and `honest_instruction` at **71 instances each of 100
loaded**, both `paired: true`, with **identical `instance_ids` lists** and split
levels matching exactly — 30 identity and 41 inversion on both sides. The
full-split `pressure` condition's 1000 ids are a different list, which is the
point of keeping the two apart. The alignment check found **71 pairs, none identical to its pressure
prompt and none differing outside the Pressure Clause**, so every honest prompt
legitimately reuses its pressure prompt's Segments.

**The differential column is non-trivial, and it reproduces ticket 04 exactly.**
This ticket touched no DLA measurement code, so agreement is the correct result
and a drift would have been a regression:

| Component | dla.pressure_paired | dla.honest_instruction | dla.differential | se |
|---|---|---|---|---|
| L31 MLP | −0.2424 | −0.5677 | **+0.3253** | 0.0828 |
| L24H25 | +0.1338 | +0.0489 | **+0.0849** | 0.0261 |
| L24H18 | +0.0616 | −0.0087 | **+0.0703** | 0.0207 |
| L17H25 | +0.0348 | +0.0002 | **+0.0347** | 0.0027 |

**Six of the eighteen Components** have `|dla.differential|` above two standard
errors: L31 MLP, L24H25, L24H18, L17H25, L14H22 and L5H9. The checkbox asked for
"at least some"; this is a third of the circuit.

**Two of the seventeen heads move their top Segment between the paired
conditions**, which is the attention-side version of the same question:

| head | under pressure | under the honest instruction |
|---|---|---|
| L14H7 | question (0.33) | unsegmented (0.27) |
| L17H25 | question (0.29) | unsegmented (0.28) |

L17H25 is also the fourth-largest differential DLA, so the same head both
changes what it reads and changes what it writes. The other fifteen keep their
top Segment and mostly shed a little mass, the largest shift being L8H12 at
−0.075. **Worth the researcher's eye:** on L17H25 the unpaired Honest Twin agrees
with the paired honest condition, and on L14H7 it does not — the twin still says
`question` there. That is exactly the kind of place where a population contrast
and a causal one part company, and it is the reason both columns exist.

**The paired lens is the clearest picture in the run.** `logit_lens_paired.png`
overlays the two conditions over the same 71 instances: they track each other to
within a tenth of a logit until about row 15, then separate hard — pressure
climbing to about +3.6 by row 25, the Honest-Instruction Counterfactual falling
to about −4.1 by row 28. `pressure_paired` settles positive at row 18 (layer 17)
and `honest_instruction` settles negative at row 15 (layer 14).

### What the author's own pass found first, before the sub-agents delivered

Kept here because the commits are separate and the orchestrator may want to
rebase them separately. The independent review's findings and their dispositions
are in the section above; where the two found the same thing, it is marked.

1. **The paired scatter was illegible** on the first run (the Spec reviewer
   independently confirmed the two-panel fix serves the ticket rather than
   exceeding it): one MLP block at
   (−0.24, −0.57) set the scale and fourteen of eighteen labels landed on the
   same pixel. Commit `57bbf24` adds a second panel cut at the largest ratio gap
   in the sorted magnitudes, with the labels divided between the panels and the
   points drawn on both. On this circuit it cuts at ±0.0082 and names 4
   Components in the full panel and 14 in the zoomed one, 18 in total, which
   `dla_paired_scatter.json` now records per point. A circuit whose Components are
   all of a size gets no second panel. The figure was re-rendered from the job's
   own JSON, so the numbers are the job's and the layout is the final code's.
2. **The dry-run estimate misreported the batch count** — the Standards
   reviewer found this too, and called it caller-visible — it multiplied by two
   for the paired condition's two passes and printed the product as the number
   of batches, saying 26 where the loader has 13. Commit `e1a8520`. The forward
   count and the timing were right and are unchanged.
3. **`dla.py`'s module docstring did not list the new files.** Fixed in
   `c7b4d37`: a "What lands in the cell" section names all eight and says which
   four are the paired ones.

One finding was **kept**: the repeated condition-gating idiom in `run` and
`estimate`, because the three branches call three different functions returning
three different shapes, so a helper would have to unify them first. A second —
`--attention-conditions` validating inside `run()` rather than in the parser —
was kept by the author and then **overturned by the independent Standards review
and the orchestrator**; it is fixed, and the disposition is in the section
above. The third, the heatmap's fourth panel, is still kept.

### Tests

| env | baseline on `a74d54b` | final on `07bbe43` | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 751 passed, 42 skipped | 8 failed, 781 passed, 43 skipped | none (same 8 names) |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 836 passed, 19 skipped | 8 failed, 880 passed, 19 skipped | none (same 8 names) |

The 8 are ticket 01's list, re-derived on this base and identical by name in both
environments; the baseline and tip lists were diffed by name, not compared by
count, and came out identical in both environments. The extra skip in the base environment is
`tests/test_paired_honest_cli.py` at module level.

This ticket contributes **44 tests**:

- `tests/test_paired_honest.py` — 30, no model, both environments: the
  conditions flag, the head-table columns on hand-built payloads, the two sides
  of the pair on a hand-built `Batch`, both figure payload builders, the zoom
  rule, and a fresh-interpreter probe that neither module imports nnsight.
- `tests/test_paired_honest_cli.py` — 14, nnsight 0.7.0 only: the CLI seam over
  a **synthetic paired dataset**. It is the first CLI fixture in the repo with a
  Matched Honest pool and a survivors file; two thirds of the split survive, so
  "the paired condition reads fewer instances than the pressure condition" is an
  assertion rather than a coincidence.

Per 02b's seam note, the nnsight-import probe for these two modules lives in
`tests/test_paired_honest.py` rather than in `tests/test_component_analysis.py`,
which the orchestrator folds in at merge.

### The code review

`mattpocock-skills:code-review` against `a74d54b`, both axes as parallel
sub-agents. Both delivered — late, and by way of the orchestrator rather than
back to the author, as happened on tickets 02, 02b and 04. **The review is
independent of the author.** Report, with both agents' findings verbatim and the
disposition of each: `Alignment/.scratch/component-analysis/reports/06-paired-honest-columns-review.md`.

**Eighteen findings. Eleven fixed, seven kept or documented with reasons.**
The two the reviewers called hard or caller-visible:

1. **The scatter's JSON twin did not describe the figure it is a twin of.**
   `plot_paired_scatter`'s own docstring promises "whatever a reader finds in
   the file is what was plotted", and the zoom cut and the two-panel split
   existed only in the PNG. The twin now carries `zoom`, a `panels` note and a
   `panel` field per point, and **the plotter reads the panel assignment off the
   twin instead of recomputing it**, so the file's account is the figure's
   account rather than a parallel one.
2. **The three `*_slices` tests assert below the caller's seam.** Kept, on the
   orchestrator's stated condition, which is now met: `test_both_sides_of_the_pair_are_profiled_over_the_same_instances`
   compares the two conditions' recorded `instance_ids` in `patterns.json`. They
   stay for two reasons written into the file above them. The seam-level form
   needs a model, so it does not run on the login node at all. And the bug they
   catch is invisible at the file seam: yielding the honest prompt for both
   sides produces a **well-formed** `patterns.json` with matching ids, matching
   counts and every paired difference exactly zero — which reads as a finding,
   not a failure. Only the prompts distinguish the two.

The rest of what changed, in `6d1c5dd` and `07bbe43`:

- **`patterns.json` records `instance_ids` per condition**, as `dla.json`
  already did (spec user stories 28 and 43). This is what turned finding 2 from
  an argument into a choice, and it is the better fix of the two on its own
  merits: "paired" is now a property a reader can check in the file.
- **The panel cut is half-open.** A Component sitting exactly on it was named in
  both panels, which would make the two panel counts sum to more than the number
  of Components while the titles said they divided them. On the real run: 4 in
  the full panel, 14 in the zoom panel, 18 total.
- **The paired lens figure is derived from its own JSON twin**, not a second time
  from `logit_lens.json`. Deriving picture and file separately from one source
  lets them drift; the test edits the twin and asserts the edit reaches the
  figure.
- **`--attention-conditions` is refused at parse time**, the way
  `registry.select` refuses an unknown analysis name, so a typo on the cluster
  costs nothing instead of an 8B model load. `UnknownCondition` subclasses both
  `ValueError` and `argparse.ArgumentTypeError`, because argparse throws away a
  plain `ValueError`'s message and would have printed "invalid parse_conditions
  value: 'honest'" — naming the function rather than the flag and listing
  nothing. **`--dla-conditions` was deliberately not changed**: it is ticket
  04's, its test pins `ValueError` from inside `run`, and altering shipped
  behaviour was not this ticket's to do. The two sibling flags therefore differ
  in *when* they reject a typo, which is the one thing the spec reviewer asked
  be said out loud.
- `dla.PAIRED_CONDITIONS` spelled once instead of three times; `twin` no longer
  means both the Honest Twin dataset and a figure's JSON companion inside one
  test file (CONTEXT.md owns "Twin"); three nits.

**Kept, with the reason in the report:** the condition constants being defined
once per module (`registry.py`'s own sibling-branch rationale); the repeated
condition-gating idiom (three different return shapes); the heatmap's fourth
panel; the N=100 sample for the paired columns (inherited from ticket 04, and
the orchestrator accepted it — see open question 3); and the naming question
below, which is the only finding neither the author nor the orchestrator can
settle.

### Open questions for the researcher

1. **Ticket 04's open question 2, unchanged and still yours — and the
   independent spec review raised it too, from the other end.** The head-table
   columns distinguish paired from descriptive by the `_descriptive` suffix on
   the twin columns, not by the word "paired" on the paired ones. The reviewer's
   sharper version: bare `pressure_top_segment` and `dla.pressure` are **also**
   unpaired and also unmarked, so `pressure` versus `honest_instruction` is
   still a population contrast that no column header warns about, which is the
   exact trap user story 27 names. **That is why `pressure_paired` exists** — it
   gives the paired column a correctly paired left term — but it does not stop a
   reader putting the wrong two columns side by side. If you want the word in
   the names, it has to go on all of them at once, `dla.honest_instruction` and
   `dla.differential` included, which renames columns with GPU outputs of record
   behind them. I did not do it unilaterally.
2. **Do you want `attention_patterns.pressure_paired_*` at all?** It is the
   scope addition described above; both reviewers read it as a documented
   deviation rather than creep, and the orchestrator let it stand. Rejecting it
   means the paired attention column has only the full-split pressure column to
   be read against, which I think is the worse of the two, but it is your call.
3. **The paired columns run over the causal sample, not the full test split**
   (71 of 100), which reads against user story 28's "descriptive analyses use
   the full test split". The orchestrator accepted this as inherited from ticket
   04. It is inherent to a paired counterfactual — only the survivors of the
   Matched Honest filter have one — and `patterns.json` now records
   `n_instances`, `n_loaded` and the `instance_ids` so the two can never be
   confused. Say if you want the Matched Honest filter applied to the whole
   split instead, which would be a much larger paired n and a much longer job.
4. **The two conditions flags now differ in when they reject a typo.**
   `--attention-conditions` is refused by argparse at parse time;
   `--dla-conditions` is refused inside `run`, after the model is loaded. I left
   ticket 04's flag alone rather than change shipped behaviour and its test. If
   you want them the same, it is a two-line change to `dla.py` and a one-line
   change to `tests/test_dla_model.py`, and ticket 10 or 11 could carry it.
5. **L14H7 is where the twin and the counterfactual disagree.** The paired
   contrast says its top Segment moves from `question` to `unsegmented` under
   the honest instruction; the unpaired Honest Twin says it stays on `question`.
   One of those is a population difference and one is a causal one, and this
   head is the cleanest example in the run of why the spec asked for both
   columns.

No analysis output, log or `core.*` file was committed; `outputs/` and `logs/`
are ignored and no `core.*` file appeared.
