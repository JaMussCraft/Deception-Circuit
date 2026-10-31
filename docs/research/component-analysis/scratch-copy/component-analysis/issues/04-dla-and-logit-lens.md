# 04 — Direct logit attribution and logit lens

**What to build:** A researcher gets, for every circuit head and MLP block, its direct contribution at the Readout to logit(Target) minus logit(Distractor), read through an fp32 final norm and unembedding, plus a suppression flag for Components that favour the Distractor, and a layer-by-layer logit lens of the cumulative residual. Pressure prompts over the full test set; honest-twin instances as a labelled descriptive column. JSON, PNG, and head-table columns.

**Blocked by:** 02 — Segmentation and stratified sample; 02b — Block C scaffold.

**Status:** resolved

- [x] Per-Component DLA uses the actual final-RMSNorm scale at the Readout position of each instance, in fp32.
- [x] `dla/dla.json` holds per-Component mean and standard error over instances, per split level as in ticket 03; `dla/logit_lens.json` holds the cumulative residual logit difference per layer.
- [x] Head-table columns: dla_pressure, dla_honest_twin (descriptive), suppression flag (true when dla_pressure is negative beyond a documented margin).
- [x] PNG: DLA bar chart by Component ordered by layer; logit-lens line plot with the layer where the sign flips marked.
- [x] Test: on the tiny model with the circuit set to every head and MLP block, DLA over all Components plus the embedding sums to the residual logit difference at the Readout within tolerance.
- [x] Test: CLI seam run produces the JSON and PNG with the documented schema.
- [x] Verified by a short Slurm run on SDR nls0.3; late-layer Components carry the bulk of the mass and the logit lens flips sign at some layer.
- [x] Subagent code review against the spec completed and findings addressed. (Both sub-agents were killed mid-run by a spend limit, were resumed, and both delivered late. The review is independent of the author; see Comments.)

## Comments

### What was built

Three commits on `ca/04-dla-and-logit-lens`, base `917474d`, plus the
orchestrator's seam commit cherry-picked in the middle:

    abe7b26  Say what each Component writes at the Readout, and when the answer flips
    7b9e2de  Let the readout take a shared scale, expose o_proj, and pin the empty registry  (cherry-pick of 8a8cb9e)
    9ca5fc5  Take the shared readout scale, and let the rules run without a model
    1e863e6  Stack the lens flip labels so they can be read
    af0d579  Test the two flags that had no test

**`component_analysis/dla.py`** is the whole analysis, plus one line in
`registry.ANALYSES`. Nothing else in the package changed.

    NAME = "dla"   SUBDIR = "dla"

    component_contributions(model, capture, keys)      what each key wrote
    fixed_scale_readout(model, contributions, residual)  fp32, one shared scale
    component_logit_difference(...)   [batch, k] DLA onto Target - Distractor
    lens_logit_difference(...)        [batch, num_layers + 1] cumulative lens
    sum_check(model, batch, keys)     the invariant, on the real model

    Tally / paired_difference         per-instance values, per split level
    measure_condition / measure_paired
    mean_and_se / is_suppressing / sign_flip_layer / sign_changes / stratum_of
    direction_sign / dataset_of / honest_twin_dir / condition_batches
    dla_payload / lens_payload / columns / plot_components / plot_lens

Flags, all prefixed per the orchestrator's rule: `--dla-conditions`,
`--dla-split`, `--dla-suppression-margin`, `--dla-honest-twin-dir`,
`--dla-max-batches`, `--dla-sum-check`.

Files per cell: `dla/dla.json`, `dla/logit_lens.json`, `dla/dla.png`,
`dla/logit_lens.png`.

### The two things that were worth getting right

**1. The fixed scale.** RMSNorm is not linear, so a per-Component contribution
only means something once a scale is chosen, and only one choice makes the
parts add up to the whole: the scale the final norm actually applied to the
full residual at that instance's Readout. `hooks.readout_logits` normalizes by
the RMS of whatever it is handed, which is right for a whole residual and wrong
for one Component's share of it.

The first implementation got the fixed scale out of the existing seam by an
identity — rescale the contribution to carry the residual's RMS exactly, read,
divide back — which is exact and needs no epsilon. The orchestrator preferred
the seam to carry it, so `7b9e2de` added `scale_from` to `readout_logits` and
`o_proj_weight` to `hooks.py`, and `9ca5fc5` moved onto both. **The two
implementations agree on the real model to five decimal places** (the GPU run
was repeated across the change), which is worth recording: two independent
routes to the same number is a check neither one gives alone.

**2. The Honest Twin's answers are labelled the other way round.**
`dataset.deception_common.harvest_honest_twins` swaps `target` and `distractor`
when it harvests the honest split, because on those instances the model gave
the honest answer. Verified in the data: on `data/datasets/sdr` the `target` is
the designated item under identity polarity and the other item under inversion;
on `data/datasets/sdr_honest` it is exactly the reverse, 629 inversion and 371
identity of 1000.

So every condition here is reported in **one direction — logit(deceptive
answer) minus logit(honest answer)** — and the honest-twin condition is negated
into it (`direction_sign`). Without that, a mover would read as a suppressor on
the twin column and the two columns could not be compared at all. The metric
line in `dla.json` says so, and the CLI-seam test builds a twin split with the
two answers swapped and asserts the column comes out *equal* to the pressure
column rather than its negative.

### The GPU verification

Job **22110737**, `gpuA40x4`, **2:27** elapsed, submitted with
`--time=00:30:00` on the command line so the script's own four-hour default did
not apply (the sbatch itself is untouched). Command, after the same one was
rehearsed with `--dry-run` on the login node:

    sbatch --time=00:30:00 scripts/analyze_components.sbatch \
      --circuit sdr=<nls0.3 run> --circuit honest_c=<honest twin run> \
      --reference honest=<honest twin run> --expr "delta=sdr \ honest_c" \
      --compose-granularity head --task-from <nls0.3 run> \
      --analyses dla --dla-split designation \
      --suite-name dla-verify2 --output-dir outputs/_analyses/dla-verify2

(Job **22107311**, 2:17, ran the same thing before the seam change; its numbers
agree, as noted above. Job **22111601** re-runs it once more after the review
fixes, whose only effect on the outputs is the renamed columns and lens keys —
no measured quantity changed — so the numbers below are 22110737's until that
job is read back.)

**Top five Components by |dla.pressure|**, over the full 1000-instance test
split:

| Component | dla.pressure | se | dla.honest_instruction | dla.honest_twin | dla.differential (se) |
|---|---|---|---|---|---|
| L31 MLP | **+0.1795** | 0.0603 | −0.5677 | −0.2932 | **+0.3253** (0.0828) |
| L24H18 | +0.0444 | 0.0221 | −0.0087 | −0.0383 | +0.0703 (0.0207) |
| L24H25 | +0.0405 | 0.0196 | +0.0489 | −0.0240 | +0.0849 (0.0261) |
| L17H25 | +0.0310 | 0.0014 | +0.0002 | +0.0084 | +0.0347 (0.0027) |
| L27H4 | −0.0045 | 0.0070 | −0.0003 | −0.0182 | −0.0032 (0.0037) |

**Late-layer Components carry the bulk, as the ticket expected.** The thirteen
Components in layers 5 to 14 have |mean| at most 0.0011 each; everything
measurable is at layer 17 and above. The layer-31 MLP block's +0.1795 is most
of the circuit's summed +0.2869 on its own.

**Suppression-flagged Components: none.** At the default margin of 0.05 logits
nothing is flagged, and **the margin is not the reason**: the most negative
Component is L27H4 at −0.0045 ± 0.0070, which is inside its own standard error,
and the next two are −0.0011 ± 0.0012 and −0.0011 ± 0.0010. At any margin down
to zero this circuit has no Component that reliably favours the honest answer.
That is a finding about the head-granularity SDR delta, not about the rule.
Worth knowing: the Components that *do* change sign do it between conditions,
not within one — see L31 MLP above.

**The logit lens flips, but read the flip with its crossings.**

| condition | settles at row | which is layer | every crossing row |
|---|---|---|---|
| pressure | 1 | 0 | 1 |
| honest_instruction | 15 | 14 | 1, 4, 5, 7, 15 |
| pressure_paired | 18 | 17 | 1, 4, 5, 7, 14, 18 |
| differential | 16 | 15 | 3, 5, 10, 11, 12, 14, 16 |
| honest_twin | 13 | 12 | 1, 6, 8, 10, 12, 13 |

**A row is not a layer**, which both reviewers caught: row 0 is the embedding's
output and row `l+1` is the residual after layer `l`, so the model has 33 rows
and the layer is one less than the row. Both numbers are written to
`logit_lens.json` now, as `sign_flip_row` and `sign_flip_layer`. **"pressure settles at row 1" is true and misleading on its
own**, which is why `sign_changes` was added beside `sign_flip_layer`: the
pressure lens crosses once, very early, and then sits within a tenth of a logit
of zero until about row 17 before climbing to +3. The honest conditions cross
the other way in the same band. The picture in `logit_lens.png` is that
**nothing is decided before roughly layer 16, and the two conditions separate
hard between rows 17 and 25** — pressure to about +3, the Honest-Instruction
Counterfactual to about −4, with the unpaired Honest Twin tracking the paired
honest condition closely the whole way down. That agreement between a paired
causal contrast and an unpaired population contrast is the most reassuring
thing in the run.

**The circuit writes little of the answer directly.** Mean over the split:

| | model's logit difference | the 18 Components' sum | the embedding | everything else |
|---|---|---|---|---|
| pressure (n=1000) | +1.7454 | +0.2869 | +0.0001 | +1.4585 |
| honest_instruction (n=71) | −2.3468 | −0.5287 | +0.0002 | −1.8182 |
| honest_twin (n=1000) | −2.1120 | −0.3629 | −0.0002 | −1.7489 |
| differential (n=71, paired) | +3.9325 | +0.5067 | +0.0002 | +3.4255 |

The head-granularity delta's Components write **16% of the Readout logit
difference directly**. That is not a fault — a circuit found by node pruning is
selected for causal necessity, not for direct effect, and most of its influence
should arrive at the Readout through other Components — but it means a role
proposal must not be read off DLA alone, and it is the number that makes ticket
08's path patching the interesting one.

**The sum invariant on the real model.** With `--dla-sum-check on` the run
records, on one batch, DLA over all **1057 senders** (32 layers x 32 heads, 32
MLP blocks, the embedding) against the model's own Readout logit difference:
**max absolute error 0.0163, mean 0.0070, against a mean |logit difference| of
1.543** — about one percent, which is the bfloat16 captures being summed in
fp32 rather than an error in the attribution. The exact version of the same
invariant is asserted in fp32 on the tiny model.

**Split by designation polarity.** `--dla-split designation` was on, so every
level is in `dla.json`. The one that stands out: **L31 MLP writes +0.3168 under
inversion and +0.0755 under identity**, four times as much when the deceptive
answer is the item the Designating Sentence did *not* name. That is a
pre-registered-hypothesis-shaped result and the researcher should look at it.

The two PNGs in `outputs/_analyses/dla-verify2/.../dla/` were re-rendered from
that run's own JSON after the label-stacking fix; the numbers are the job's,
the layout is the final code's.

### Deviations, and what ticket 06 still owns

- **`dla.honest_instruction` and `dla.differential` land here**, on the
  orchestrator's explicit instruction, although ticket 06's checkboxes list
  them. **Ticket 06 therefore shrinks** to `--honest-counterfactual` as a flag,
  the paired DLA scatter PNG, the overlaid two-condition lens plot, and the
  whole attention side.
- **Column names carry no analysis prefix**, per the orchestrator's rule, and
  **every column computed on the unpaired Honest Twin dataset ends in
  `_descriptive`**, per the rule that followed the spec review. So the ticket's
  `dla_pressure` is the column `dla.pressure` and its `dla_honest_twin` is
  `dla.honest_twin_descriptive`. The nine columns:

      dla.pressure                     full test split, the pressure prompts
      dla.pressure_se
      dla.pressure_paired              the paired subset's left term
      dla.honest_instruction           paired, the same instance ids
      dla.differential                 per-instance, paired
      dla.differential_se
      dla.honest_twin_descriptive      a different population, unpaired
      dla.honest_twin_descriptive_se
      dla.suppression
- **"Paired" means the same instance ids on both sides, and always did.**
  `dla.differential` is the per-instance difference over the instances that
  have an Honest-Instruction Counterfactual — 71 of the 100 sampled on SDR —
  not a difference of two population means. `paired_difference` refuses two
  tallies whose id lists differ, `pressure_paired` is a named condition in
  `dla.json` with its own n and its own `instance_ids`, and a library test
  builds a pair whose honest prompt *is* the pressure prompt and asserts the
  differential is exactly zero on every Component. `dla.pressure` over the full
  split stays descriptive of the population and is reported separately for
  exactly that reason.
- **`dla.pressure_paired` is there because the differential needs a left term
  the reader can see.** `dla.pressure` is the mean over the whole split;
  subtracting `dla.honest_instruction` from it would be a difference of two
  populations. The differential is the per-instance paired difference over the
  71, and `dla.pressure_paired` is its left half. They differ: the circuit's
  summed pressure DLA is +0.287 over the split and −0.022 over the paired 71,
  because the 71 are the survivors of the Matched Honest filter and not a
  random subset.
- **`--dla-sum-check` is not in the ticket.** It costs one forward pass and
  records on the real model what the tiny-model test asserts in fp32. On by
  default; `--dla-sum-check off` turns it off.
- **The embedding is measured and reported but is not a Component**, so it
  appears in `dla.json` under `conditions.<name>.embedding` and never as a head
  table row.

### Open questions for the researcher

1. **The suppression flag is empty on this circuit, and honestly so.** Do you
   want the flag to stay an absolute margin in logits (`--dla-suppression-margin`,
   default 0.05), or to become relative — a fraction of the largest |mean| in
   the circuit, or "more than two standard errors below zero"? The standard
   errors are all in `dla.json` either way. I would leave it absolute until a
   circuit shows a real suppressor, but the default is a judgement I made, not
   one the ticket fixed.
2. **The head-table column names do not say which contrast is paired.** Spec
   user story 27 wants paired and descriptive columns "clearly labelled". The
   names distinguish them and `dla.json` records `paired` and the source
   `dataset_dir` per condition, but the CSV column header itself does not.
   Ticket 06 owns the labelling across all three descriptive analyses; say if
   you want the word in the column name instead.
3. **Only SDR has an Honest Twin *and* a Matched Honest pool.** On FAR and SER
   the paired condition will report itself skipped with a reason, and the twin
   column depends on `<dataset>_honest` existing. Both are reported in
   `dla.json` under `skipped`, not silently dropped.

### Tests

| env | baseline on `917474d` | final | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 685 passed, 22 skipped | 8 failed, 695 passed, 23 skipped | none (same 8 names) |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 711 passed, 19 skipped | 8 failed, 739 passed, 19 skipped | none (same 8 names) |

Both runs are at the branch tip, `af0d579`. The 8 are ticket 01's list,
re-derived on this base and identical by name in both environments. This ticket
contributes **27 tests**: `tests/test_dla.py` (10, no model, both environments)
and `tests/test_dla_model.py` (17, nnsight 0.7.0 only: the tiny-model library
seam and the CLI seam). The extra skip in the base environment is
`tests/test_dla_model.py` at module level. The cherry-picked seam commit adds
one more test in `tests/test_component_hooks.py`, which is the 28th of the
difference between the two `passed` columns.

**Two mutations were run to check the tests actually bite**, because both bugs
type-check and produce plausible rankings:

| mutation | tests that failed |
|---|---|
| the `o_proj` slice transposed | the sum invariant, the by-hand head check, the real-model sum check |
| the Honest Twin read in its own labels | the direction rule, the CLI-seam twin column |

### Code review

`mattpocock-skills:code-review` against `917474d`, both axes as parallel
sub-agents. Both were killed mid-run by a spend limit, were resumed by message
once it reset, and **both delivered** — late, after the first report to the
orchestrator, as happened on tickets 02 and 02b. **This review is independent
of the author.** Report:
`Alignment/.scratch/component-analysis/reports/04-dla-and-logit-lens-review.md`,
which lists every finding with its outcome.

**Taken from the independent review**, in the last commit:

1. *Standards, hard:* a test asserted hooks wiring rather than a DLA seam, and
   duplicated one in `tests/test_component_hooks.py`. Deleted.
2. *Both axes:* `sign_flip_layer` returned a **row**, not a layer — row 0 is
   the embedding — while the figure already said "row". Renamed
   `sign_flip_row`, `layer_of_row` added, both numbers written out, and
   `logit_lens.json` says a row is not a layer.
3. *Spec:* `direction_sign` negates the twin condition, but
   `--dla-honest-twin-dir` takes any directory, so pointing it at a deceptive
   split would have inverted every Component silently. `assert_honest_twin`
   refuses a split whose records do not say `condition == "honest"`, with a
   test that points the flag at an impostor.
4. *Spec:* the purely descriptive conditions were gated on the causal-pairing
   reason. Each condition is now gated on what it needs.
5. *Standards:* `"pressure_paired"` and `"differential"` were bare literals;
   now `PRESSURE_PAIRED` and `DIFFERENTIAL`, documented as derived conditions.
6. *Standards:* a cell with no measurable condition wrote JSON beside no PNG
   and reported success. `_empty_figure` writes a figure saying why.
7. *Standards:* the column table was computed twice; built once in `run` now.

**Considered and kept**, with the reason in the report: `_pyplot` duplicating
`evaluation/report.py`'s private helper, rather than reaching into another
package's privates.

**Two findings landed in `hooks.py`, which this ticket may not edit**, and were
sent to the orchestrator, who **fixed both in `4c9ee6b`** on the integration
branch: `readout_logits`'s docstring said a Component's contribution may be
passed as `residual`, which without `scale_from` is the wrong reading, and
`o_proj_weight` guarded the no-bias case with a bare `assert` that `python -O`
strips. The same commit corrected `replace_forward`'s docstring. No cherry-pick
here; the rebase picks it up.

Findings from the author's own pass, taken earlier: the pure-Python rules were
being discarded on the login node by a module-level nnsight gate (the test file
is now split in two); the embedding's column was found by position rather than
by key, and is now refused outright if absent; `dla.json` did not record which
dataset directory each condition read; the lens payload was built twice; the
lens figure's five flip labels landed on top of each other; and two flags
shipped untested.

### Shared files touched, for the rebase

- **`component_analysis/registry.py`** — ticket 04's placeholder line replaced
  by `"component_analysis.dla",`. One line, in its own paragraph.
- **`component_analysis/hooks.py`**, **`tests/test_component_hooks.py`**,
  **`tests/test_analyze_components_end_to_end.py`** — only through the
  cherry-pick of `8a8cb9e`, which the rebase should drop as redundant. The
  cherry-pick conflicted on the end-to-end test because this branch had already
  patched it; resolved by taking the integration branch's version verbatim.
- **`tests/test_component_analysis.py`** — deliberately **not** touched. 02b's
  seam notes ask each ticket to add its module to the fresh-interpreter nnsight
  probe there; the orchestrator's instruction was one shared-file edit only, so
  the equivalent probe lives in `tests/test_dla.py` and the orchestrator folds
  the four names in at merge.

### One inefficiency, seen and left

`estimate(ctx)` builds the Honest Twin loader to report its instance count, and
that loader is not memoized on the context the way `ctx.descriptive_batches()`
is, so `run` tokenizes the twin's 1000 prompts a second time. It costs seconds
and it keeps `--dry-run` honest about a dataset that may not exist. Memoizing
it means either reaching into `ctx._loaders` or widening the context's API,
which is a shared file this ticket may not touch.

Everything else is new. No analysis output, log or `core.*` file was committed;
`outputs/` is ignored and no `core.*` file appeared.
