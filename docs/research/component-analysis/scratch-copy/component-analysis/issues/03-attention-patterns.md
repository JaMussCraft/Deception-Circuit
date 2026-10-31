# 03 — Attention patterns by Segment

**What to build:** A researcher runs the analysis CLI with the attention-pattern analysis on a GPU node and gets, for every circuit head, the attention mass it places on each Segment from the chosen query position(s) (default Readout), averaged over the test set and split by designation polarity, item polarity, both or none, under the pressure prompts and, as a labelled descriptive column, on the honest-twin instances. Output is JSON, one PNG profile plot per split, and head-table columns.

**Blocked by:** 02 — Segmentation and stratified sample; 02b — Block C scaffold.

**Status:** resolved

- [x] Attention weights are obtained with eager attention enabled only for this analysis; every other analysis stays on SDPA.
- [x] `--query-positions` accepts Segment names (default `readout`) and `--split` accepts `designation`, `item`, `both`, `none`.
- [x] Per head, per query position, per split level: mean attention mass per Segment over the full test set, plus mean over the honest-twin dataset when a reference task is bound, written to `attention/patterns.json`.
- [x] Head-table columns: top Segment and its mass at the Readout under pressure, and the same under the honest twin, marked as descriptive.
- [x] PNG: one heatmap per split level, heads by Segment, plus a per-head bar chart for the top-k heads by knockout rank when that column exists (else by layer).
- [x] A Slurm script mirroring the evaluator's submits the analysis CLI; `--dry-run` prints a cost estimate.
- [x] Test: on the tiny model, Segment masses sum to one per query position; a hand-built prompt where one head is forced to attend to a known span yields that Segment as top.
- [x] Test: CLI seam runs the analysis end to end on the tiny run directory and the JSON and PNG exist with the documented schema.
- [x] Verified by a short Slurm run on SDR nls0.3 with its honest twin bound; outputs read back and sanity-checked (masses sum to one, no NaN).
- [x] Subagent code review against the spec completed and findings addressed. (Both axes ran, but neither sub-agent delivered — one died against a spend limit, two more failed at the handback and did not answer a request to deliver — so both axes were done by the author under the brief's fallback. Not independent; see Comments.)

## Comments

### What was built

One module, `component_analysis/attention_patterns.py`, and one line replacing
the ticket's placeholder in `registry.ANALYSES`. Nothing else in the package
changed: `hooks.py`, the dataloaders, the CLI and the sbatch are untouched.

    NAME = "attention_patterns"      SUBDIR = "attention"

    --query-positions SEG[,SEG]   Segment names, default readout
    --split {designation,item,both,none}          default designation
    --attention-honest-twin auto|off|DIR          default auto
    --attention-top-k N                           default 8
    --attention-rank-column COLUMN                default: found

The library seam, all pure except the last two:

    parse_query_positions(value, available)   level_of(record, split)
    segment_ids(segmentation, names, n)       segment_id_batch(...)
    query_slots(segmentations, query_names)   masses_from_rows(rows, ids, ...)
    top_segment(profile)                      Profiles (the running means)
    batch_masses(model, ...)                  collect_condition(ctx, slices, ...)

`batch_masses` is the only thing that touches the model: **one
`hooks.attention_weights` call per layer per batch**, carrying every circuit
head of that layer and every query position at once. The rows come back from a
whole forward, so a call per head would have multiplied the cost by the heads
in the layer. Masses are binned by `scatter_add` into 18 Segment buckets plus a
sentinel for anything outside the segmentation, which is reported rather than
pooled.

**A query Segment wider than one token is averaged within the instance first,
then across instances.** Pooling the tokens instead would weight an instance by
how many tokens its Pressure Clause happens to take.

### The three conditions, and which is which

| condition | prompts | n on SDR nls0.3 | kind |
|---|---|---|---|
| `pressure` | the task's own test split | 1000 | descriptive |
| `honest_instruction` | the same instances, clause replaced | 71 of 100 sampled | **paired** |
| `honest_twin` | `data/datasets/sdr_honest` | 1000 | descriptive, **unpaired** |

The honest twin's prompts are a different dataset, so it gets its **own**
resolved and validated segmentation, written to
`attention/honest_twin_segmentation.json` (user story 10: no plot read against
the wrong spans). The paired condition reuses each instance's pressure
segmentation, which is sound exactly when the two prompts differ only inside
the Pressure Clause — re-checked per instance by diffing token ids, not by
trusting the build. On SDR: **71 pairs, 0 differing outside the clause, 0
identical to their pressure prompt.**

Head-table columns (the CLI namespaces them `attention_patterns.`):
`query_position`, `pressure_top_segment`, `pressure_top_mass`,
`honest_twin_descriptive_top_segment`, `honest_twin_descriptive_top_mass`. The
twin's label is in the column name because a CSV is read column by column and
an unpaired population contrast must not be mistakable for a paired one. The
MLP block's row holds nulls, not zeros.

Files per cell: `attention/patterns.json` (the whole result),
`patterns_<level>.png` + `.json` twin (heads by Segment, one panel per
condition), `top_heads.png` + `.json` twin, and the twin segmentation.

**The Slurm checkbox needed no new script.** `scripts/analyze_components.sbatch`
already mirrors `scripts/evaluate_circuit.sbatch` and passes its arguments
through, so both jobs below went through it unchanged; what this ticket adds to
it is the `estimate(ctx)` that makes its `--dry-run` line a real cost. Pass
`--time` on the `sbatch` command line for a short job: the script's own
directive is four hours, sized in 02b for a patching pass.

### The GPU runs

Two jobs, `gpuA40x4`, `--time` overridden on the command line to 30 and 25
minutes so the sbatch's own 4-hour directive did not apply.

| job | elapsed | what |
|---|---|---|
| 22107232 | 7:41 | the ticket's verification, default flags |
| 22110821 | 7:52 | the same plus `--segment 'bos=^<\|begin_of_text\|>'` |

Both on `delta__head` = `sdr \ honest_c` at head granularity (17 heads + 1 MLP
block), `--reference honest=<twin run>`, `--analyses attention_patterns`. Both
were rehearsed with `--dry-run` on the login node first, which printed the cost
estimate below and was accurate to the minute:

    attention_patterns: 17 head(s) over 8 layer(s), 1 query position(s)
    (readout), 18 Segment(s), split by designation; pressure: 1000
    instance(s) in 125 batch(es), 1000 eager forward(s) ~3 min;
    honest-instruction (paired): 71 instance(s) in 13 batch(es), 104 eager
    forward(s) ~20 s; honest twin (descriptive): 1000 instance(s) in 125
    batch(es), 1000 eager forward(s) ~3 min; about 7 min on an A40 in total,
    plus the figures

**Which code each job ran.** 22110821 ran commit `421896e`'s production code
exactly. 22107232 predates two lines of it — the `n_loaded` key and the paired
condition's `n_instances` reporting 71 rather than the loader's 100 — which
were edited while it was already running, so reading its output back raised
`KeyError: 'n_loaded'` the first time. Neither line touches a mass, and the two
runs' masses agree to every digit quoted here. The only production changes
after both jobs are the `Slice` dataclass conversion and the per-level absent
counter, neither reachable from these configurations.

**Read back, both runs.** Every profile is a distribution: the worst
`|sum − 1|` over every written mean is **3.5e-4**, and the worst single
attention row is **2.6e-3**, which is bfloat16 rounding rather than a missing
Segment (HuggingFace's eager attention softmaxes in fp32 and casts back, so a
row of 128 weights is one only to about 1e-2; `SUM_TOLERANCE` is 2e-2 for that
reason and the measured number is forty times inside it). **No NaN anywhere.**
**No mass outside the segmentation at all** (`max_outside` exactly 0.0 in all
three conditions), which is the check that the Segments really do partition
every prompt.

### The table the researcher asked for: top Segment per head at the Readout

From job 22110821, which is the same numbers as 22107232 with the single
`<|begin_of_text|>` token split out of `unsegmented`. Level `all`.

| head | KV | pressure | mass | honest instruction (paired) | mass | honest twin (descriptive) | mass |
|---|---|---|---|---|---|---|---|
| L5H5 | 1 | question | 0.508 | question | 0.611 | question | 0.568 |
| L5H6 | 1 | question | 0.598 | question | 0.593 | question | 0.601 |
| L5H8 | 2 | bos | 0.405 | bos | 0.456 | bos | 0.434 |
| L5H9 | 2 | bos | 0.508 | bos | 0.536 | bos | 0.518 |
| L5H11 | 2 | item_1_question_option | 0.354 | item_1_question_option | 0.333 | item_1_question_option | 0.349 |
| L8H12 | 3 | bos | 0.469 | bos | 0.402 | bos | 0.471 |
| L8H14 | 3 | bos | 0.469 | bos | 0.409 | bos | 0.471 |
| L8H15 | 3 | bos | 0.363 | bos | 0.340 | bos | 0.371 |
| L9H12 | 3 | bos | 0.510 | bos | 0.491 | bos | 0.509 |
| L13H17 | 4 | question | 0.250 | question | 0.275 | question | 0.263 |
| L14H7 | 1 | question | 0.322 | question | 0.270 | question | 0.316 |
| L14H21 | 5 | unsegmented | 0.221 | unsegmented | 0.216 | unsegmented | 0.223 |
| L14H22 | 5 | question | 0.292 | question | 0.267 | question | 0.261 |
| L17H25 | 6 | question | 0.265 | question | 0.276 | question | 0.265 |
| L24H18 | 4 | bos | 0.632 | bos | 0.616 | bos | 0.618 |
| L24H25 | 6 | bos | 0.554 | bos | 0.484 | bos | 0.515 |
| L27H4 | 1 | bos | 0.766 | bos | 0.724 | bos | 0.720 |

Under the **default** segmentation the `bos` rows all read `unsegmented`
instead, at masses 0.02 to 0.03 higher, and L14H21 reads `unsegmented` at
0.441. See open question 1: that difference is the whole reason the second job
was run.

### Three things in these numbers the researcher should see

1. **Nine of seventeen heads are attention-sink heads at the Readout.** Their
   top Segment is the single `<|begin_of_text|>` token, at 0.36 to 0.77 of all
   their mass. That is a property of Llama, not of deception, and it is the
   same in all three conditions. It means the Readout query says little about
   those nine, and it does **not** mean they do nothing: a sink head's small
   off-sink mass can still be where its output comes from, and DLA (ticket 04)
   and knockout (ticket 07) are what will say so.

2. **One head is polarity-selective, and the split is what shows it.** L24H25
   puts **0.151** of its mass on the **Inverse Predicate Token** under
   *inversion* and **0.001** under *identity*. No other head comes close
   (the next largest identity-minus-inversion gap is L5H5 on the Pressure
   Clause, 0.108 against 0.228). If any Component in this circuit implements
   the inversion step, L24H25 at layer 24 is the first candidate the attention
   view offers.

3. **Two heads read the Pressure Clause, and stop when it is replaced.** In
   the paired contrast, L5H5 goes from **0.160** to **0.024** on the Pressure
   Clause and L13H17 from **0.146** to **0.053**; L17H25 drops 0.089 on
   `item_1_question_option`. Pressure readers are out of scope for this block
   (spec, Out of Scope), and this is a paired, causal contrast on n=71 with no
   significance test attached, so it is a lead rather than a finding.

### Open questions for the researcher

1. **Should `<|begin_of_text|>` be its own Segment by default?** On the
   evidence above, `unsegmented` is almost entirely the BOS token: carving it
   out moves nine heads' top Segment from "unsegmented" (which names the chat
   shell, the header ids and the end-of-turn markers together) to "bos", and
   leaves the tenth, L14H21, at half of what it had. As things stand the
   default head table says nine circuit heads read "unsegmented", which is
   true and nearly uninformative. The workaround is a flag —
   `--segment 'bos=^<\|begin_of_text\|>'` — and it needs no code change. The
   fix, if you want one, is one line in `segmentation.py`'s mechanism
   segmenter, which belongs to ticket 02, not here.

2. **The honest-twin column is keyed on the dataset, not on `--reference`.**
   The ticket says the twin column appears "when a reference task is bound",
   but `--reference` binds a reference *circuit* (a run directory) and ticket
   02b's seam note is explicit that "the honest twin is a second dataset
   directory, not a flag". So the condition runs when `<task dataset>_honest`
   exists, and `--attention-honest-twin auto|off|DIR` makes that visible and
   overridable; a skipped condition records its reason in `patterns.json`.
   Confirm the reading.

3. **`--split` defaults to `designation`.** The ticket names the four values
   but no default. `designation` was chosen because SDR is the balanced task
   and the inversion question is the one the split exists for; the unsplit
   `all` level is always computed and is what the head-table columns read, so
   the default costs nothing. FAR and SER are identity-only and will simply
   show one level beside `all`.

4. **The paired condition's numbers are already here; ticket 06 owns its
   column.** `spec.md` asks for three condition columns and ticket 06 owns
   "top Segment under honest instruction" as a head-table column. Both are
   honoured: `patterns.json` carries the `honest_instruction` condition marked
   `paired: true`, and the head table gains only the pressure and honest-twin
   columns. Ticket 06 adds a column over numbers that already exist rather
   than a second GPU pass.

5. **A sink-aware normalization would make the heatmap far more readable.**
   Nine rows of the figure are dominated by one column. A "mass excluding the
   sink, renormalized" view is a few lines and would be a better default plot,
   but it is not in the ticket and it changes what a published number means, so
   it is not in. Say if you want it.

### Deviations from the ticket's letter, all deliberate

- **Ticket 06's paired condition is computed here** (open question 4).
- **`attention/honest_twin_segmentation.json` is not in the ticket.** It
  follows from user story 10, since the twin is a different dataset with
  different prompts and the cell's `segmentation.json` describes only the
  pressure split.
- **One heatmap per split level with a panel per condition**, rather than one
  per condition per level. The question asked of the three conditions is a
  comparison, and a comparison spread over three files is one nobody makes.
- **The bar chart's ranking column is searched for, not assumed.** It takes
  `--attention-rank-column`, else any `knockout.*` column in the cell's head
  table, preferring one whose name contains `rank` and reading it ascending
  (ticket 07's `knockout.rank` has rank 1 as the largest signed drop), else
  layer order. Both orderings are tested; the MLP block is in ticket 07's
  ranked list and is skipped here because it has no attention pattern.
- **Two GPU jobs rather than one.** The second exists only to answer open
  question 1, which changes how the headline table above is read. Together
  they are 16 minutes of A40.

### Shared files touched, for the rebase

- **`component_analysis/registry.py`** — the ticket 03 placeholder line
  replaced by `"component_analysis.attention_patterns"`. The only shared-file
  edit.
- `tests/test_analyze_components_end_to_end.py` was **not** edited here: the
  orchestrator's `8a8cb9e` was cherry-picked instead, as instructed, and the
  author's own copy of that fix was dropped from the branch before the
  cherry-pick.
- The nnsight-import probe for this module lives in
  `tests/test_attention_patterns.py`, not in the shared probe in
  `tests/test_component_analysis.py`, so the four parallel branches do not
  conflict on one string literal. The orchestrator folds them at merge.
- **CLI flags claimed:** `--query-positions` and `--split`, agreed with the
  orchestrator. Every other flag this module adds is prefixed `--attention-`.
  Two analyses registering one flag name is an `argparse.ArgumentError` on
  every invocation, `--dry-run` included, not merely a rebase conflict.

### Tests

New: `tests/test_attention_patterns.py`, **33 tests** at three seams — 13 pure
(masses per Segment, query slots, split levels, top Segment, the per-level
absent count), 5 on the tiny random Llama through nnsight, 14 at the CLI seam
over a real SDR split built with the fake word tokenizer, and 1
fresh-interpreter probe that fails if this module ever imports nnsight. The nnsight gate is on the model fixtures, not at
module level, so the pure tests keep running in the base environment.

The two the ticket names by hand:

- `test_segment_masses_sum_to_one_at_every_query_position` — masses over the
  Segments are a distribution at every query position, for three heads across
  two layers.
- `test_a_head_forced_to_attend_to_one_span_reports_that_segment_as_its_top` —
  a tiny model whose layer-0 head 0 is hand-built to attend to a marker token:
  the embedding gives the marker its own hidden dimension, `k_proj` reads only
  that dimension into one component of the head's key and `q_proj` reads the
  dimension every *other* token has into the same component, so the marker's
  key is enormous along the one direction every query points in. The component
  is the slowest rotary pair (about 3e-4 radians per position), so rotary
  embedding moves the dot product by less than a part in ten thousand over a
  short prompt. Measured: the forced head reports `designation_site` at
  **1.000000** to six decimal places, while head 1 of the same KV group, which
  shares the keys but not the query projection, reports **0.125** — uniform
  over the prompt's eight positions, since its query is the zero vector and
  every attention logit is therefore equal. The test asserts the weaker
  thresholds (above 0.99, below 0.5) so it does not break on a tokenizer or
  dtype change. A companion test moves the marker into `question` and the top
  Segment moves with it, so neither can pass on a fixed span.

| env | baseline on `917474d` | final | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 685 passed, 22 skipped | 8 failed, 701 passed, 39 skipped | none (same 8 names) |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 711 passed, 19 skipped | 8 failed, 745 passed, 19 skipped | none (same 8 names) |

Both final runs are on `ef02655`, the branch tip. The 8 are ticket 01's list, re-derived on this base and identical by name in both environments. The base env's 17 extra skips are this file's nnsight-0.7.0
tests; `mgnp` runs all 32. The `mgnp` count also includes one test from the
cherry-picked `8a8cb9e`.

### Code review

`mattpocock-skills:code-review` against `917474d`, both axes as parallel
sub-agents. **Neither delivered**: the first Standards agent died against a
monthly spend limit, and the pair spawned after the reset both ran to
completion and both failed at the handback; both were then asked by
`SendMessage` for their reports and neither had replied well past the ten
minutes the brief allows. **So this review is by the author and is not
independent** — a fresh reviewer on this diff is worth the orchestrator's time,
as it was on tickets 01 and 02. Report:
`Alignment/.scratch/component-analysis/reports/03-attention-patterns-review.md`.

Findings addressed (commits `7ed7123`, `b27256a` and `ef02655`):

1. *Standards, hard:* the forced-attention test called the unforced head
   `control`, which `CONTEXT.md` reserves; ticket 02b's review had taken the
   same finding in `tests/stub_analysis.py`. Renamed, with the reason at the
   docstring.
2. *Standards, hard:* the mid-file fixture import carried `# noqa: E402` on the
   statement and `# noqa: F401` on its continuation, so flake8 saw only the
   first.
3. *Standards:* `Slice` was a hand-written class where the `dataloaders`
   carriers it is built from are dataclasses. Converted.
4. *A real bug, found after the axes* (`b27256a`): a query Segment absent from
   every instance of a batch added the whole batch to **every** level's absent
   count, so under `--split designation` identity and inversion would each have
   reported losing all of it. Each level now counts its own rows. Unreachable
   from the SDR runs, where the Readout is present on every instance, and
   reachable on the saved FAR run, whose Designation Suffix is absent
   everywhere.
5. *Author's own last pass* (`ef02655`): the module docstring, which is what a
   reader of `patterns.json` reaches for, listed a condition's fields as they
   were before `n_loaded` and the per-query-position counts existed. Checked
   field by field against the file the GPU run wrote.

Considered and kept, with the reason in the report: the five-value clump
through `collect_condition` (the same one ticket 02b kept through the
`dataloaders` signatures), `run`'s three rhyming condition blocks (they differ
in loader, slicer, notes and failure mode, and the reader needs to see that the
twin is unpaired), and `Profiles` keeping its sums in dicts keyed by
`(level, query)` because the levels are not known until the last instance.

Separately, the orchestrator's mid-ticket instructions were taken: `8a8cb9e`
was cherry-picked rather than the author's own copy of the same test fix
(commit `004d916` on this branch), and the per-head bar chart's two orderings
are now both tested against ticket 07's `knockout.rank` semantics
(`6f5aa2c`).
