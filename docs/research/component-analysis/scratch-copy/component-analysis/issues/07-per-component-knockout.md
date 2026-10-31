# 07 — Per-Component knockout ranking

**What to build:** A researcher gets every circuit Component ranked by the effect of interchange-ablating it alone in the full model, measured as the change in logit(Target) minus logit(Distractor) and accuracy over the causal sample, with the ablation scheme exposed as a parameter (interchange only implemented now) so mean and zero can be added later without changing the interface.

**Blocked by:** 02 — Segmentation and stratified sample; 02b — Block C scaffold.

**Status:** resolved

- [x] Single-Component interchange ablation implemented as an nnsight intervention on the raw model using the item-swap corrupt stream, per the ADR.
- [x] `knockout/knockout.json` holds per-Component mean effect and standard error, plus accuracy under each single knockout; head-table columns knockout_logit_diff_drop and knockout_rank. (Shipped as `knockout.logit_diff_drop` and `knockout.rank`, plus `knockout.standard_error` and `knockout.accuracy`: the orchestrator dropped the prefix the namespace already supplies, for ticket 03's lookup.)
- [x] `--knockout-scheme` accepts `interchange` and rejects others with a message naming them as future work.
- [x] PNG: ranked bar chart by effect with layer colouring.
- [x] Test: on the tiny model, knocking out a Component equals replacing its output with the corrupt-run output; knocking out nothing reproduces the clean logits.
- [x] Test: CLI seam run produces the JSON, PNG and columns.
- [x] Verified by a short Slurm run on SDR nls0.3.
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

Four commits on `ca/07-per-component-knockout`, base `917474d`:

    053f8bb  Rank every Component by what knocking it out costs deception
    b6c8ead  Stop calling the clean run a baseline
    f69aeb5  Take the review, the orchestrator's column names, and the shared test fix
    b3deb4e  (cherry-picked 8a8cb9e from component-analysis, on the orchestrator's instruction)

**`component_analysis/knockout.py`** is the whole analysis, one module as the
brief requires. Public names:

    resolve_scheme(value) -> "interchange"   or raises UnsupportedScheme
    knockout_effects(model, batches, components, *, scheme) -> Effects
    summarize(effects, components=None) -> [ranked row]
    clean_run(effects) -> dict        columns(rows) -> head-table update
    payload(effects, *, circuit, task, components=None, rows=None) -> dict
    write_figure(path, rows, *, title="") -> path
    NAME  SUBDIR  JSON_NAME  PNG_NAME  SCHEME  FUTURE_SCHEMES  COLUMNS
    add_arguments(group)  estimate(ctx)  run(ctx)

A knockout is one `hooks.capture_forward` with one entry in `replacements`,
fed from the corrupt stream's capture. Nothing in `hooks.py` was re-implemented
and nothing in it was edited.

**Per batch: `len(components) + 2` forward passes.** One clean run, one corrupt
run that captures what every Component carried there, then one run per
Component with that capture written over the clean stream. On the SDR delta
that is 20 passes for 8 instances.

### The sign convention, which is the thing to get right

    drop = clean logit difference - knocked-out logit difference

**Positive means the Component helps deception**: removing it moves the model
away from the deceptive answer. Negative means it opposes deception, because
knocking a suppressor out *raises* the deceptive margin. The ranking is on the
signed drop, not its magnitude, so **rank 1 is the most deception-helping
Component and the suppressors are at the bottom**, where they read as
suppressors instead of sitting beside the mover whose effect they mirror. The
same sentence is in `knockout.json`'s `metric.sign`, in the module docstring
and on the chart's x-axis.

Everything is read through `hooks.readout_logits` — the fp32 final norm and
unembedding ADR-0001 requires — from the residual the final norm sees. That is
why a knocked-out run goes through `capture_forward` rather than
`replace_forward`: only the capture hands back that residual, while
`replace_forward` returns bf16 logits. See the open question for the
orchestrator below.

**Accuracy** is the two-way rate the metric implies: the share of sampled
instances whose Target still outscores its Distractor. Not a full-vocabulary
argmax. It matches `evaluation/metrics.py`'s rule, so it is comparable with the
circuit-level knockout numbers.

### The GPU verification

Job **22110635**, `gpuA40x4`, **1:59** elapsed, one A40, on the final tip, from
the worktree root after the same command was rehearsed with `--dry-run` on the
login node. Command: `sbatch --time=00:25:00 scripts/analyze_components.sbatch
--circuit sdr=<nls0.3 run> --circuit honest_c=<honest twin>
--reference honest=<honest twin> --expr "delta=sdr \ honest_c"
--compose-granularity head --task-from <nls0.3 run> --analyses knockout
--suite-name ca07-knockout`. Two earlier runs of the same check agree with it
number for number: **22107009** (1:54, on `053f8bb`) and **22107456** (1:36,
after the rename). The reruns were worth their four minutes because the review
fixes touched the JSON schema and the figure.

**The clean run**, over all 100 sampled instances: mean logit(Target) −
logit(Distractor) **+1.6132**, standard error 0.0886, accuracy **1.00**. The
scaffold's clean-minus-corrupt gap on the same sample was +3.2585, so the
corrupt stream sits near −1.65 and the numbers below are drops out of a gap of
about 3.26.

**The ranking of all 18 Components.** Drop and standard error are over the 100
instances; "knocked" is the mean logit difference under that one knockout.

| rank | Component | KV group | mean drop | SE | accuracy | knocked |
|---|---|---|---|---|---|---|
| 1 | L17 H25 | 6 | +0.4465 | 0.0279 | 0.99 | 1.1666 |
| 2 | L31 MLP | — | +0.3065 | 0.0649 | 0.98 | 1.3067 |
| 3 | L5 H11 | 2 | +0.1503 | 0.0197 | 1.00 | 1.4629 |
| 4 | L14 H22 | 5 | +0.1122 | 0.0312 | 1.00 | 1.5010 |
| 5 | L9 H12 | 3 | +0.0682 | 0.0136 | 1.00 | 1.5449 |
| 6 | L8 H14 | 3 | +0.0679 | 0.0151 | 1.00 | 1.5453 |
| 7 | L5 H8 | 2 | +0.0572 | 0.0112 | 1.00 | 1.5559 |
| 8 | L5 H9 | 2 | +0.0415 | 0.0102 | 1.00 | 1.5716 |
| 9 | L8 H12 | 3 | +0.0332 | 0.0080 | 1.00 | 1.5800 |
| 10 | L5 H5 | 1 | +0.0330 | 0.0185 | 1.00 | 1.5802 |
| 11 | L8 H15 | 3 | +0.0320 | 0.0093 | 1.00 | 1.5811 |
| 12 | L5 H6 | 1 | +0.0277 | 0.0144 | 1.00 | 1.5855 |
| 13 | L24 H18 | 4 | +0.0230 | 0.0038 | 1.00 | 1.5902 |
| 14 | L14 H21 | 5 | +0.0203 | 0.0385 | 0.99 | 1.5929 |
| 15 | L24 H25 | 6 | +0.0021 | 0.0034 | 1.00 | 1.6111 |
| 16 | L27 H4 | 1 | −0.0008 | 0.0024 | 1.00 | 1.6140 |
| 17 | L13 H17 | 4 | −0.0053 | 0.0269 | 1.00 | 1.6185 |
| 18 | L14 H7 | 1 | −0.0936 | 0.0283 | 1.00 | 1.7067 |

### Four things in that table the researcher may want to act on

1. **The circuit is top-heavy and thin.** L17 H25 alone is 14% of the
   clean-corrupt gap, and with L31 MLP the two carry 23% of it; the remaining
   16 Components sum to about 0.6, which is under a fifth of the gap. The
   pre-registered hypothesis expects movers late; L17 H25 is exactly where it
   expects one.
2. **L14 H7 opposes deception, by more than any but the top three help it.**
   Its knockout *raises* the deceptive margin by 0.094, four standard errors
   from zero. It is the first suppressor candidate the head table has, and it
   sits in the layer band the hypothesis assigns to selection. Its neighbour
   L14 H22 is the fourth strongest helper, so layer 14 holds both signs.
3. **Three Components are indistinguishable from zero** at this sample size:
   L24 H25, L27 H4 and L13 H17 all have drops inside two standard errors of
   zero. They were in the delta because the pruning kept their gates, not
   because a single knockout moves the Readout. Path patching may still find
   them upstream.
4. **Accuracy discriminates nothing here** and should not be read as a result.
   The clean accuracy is 1.00 and every single knockout lands between 0.98 and
   1.00, because a shift of 0.45 in a margin of 1.61 flips almost no instance.
   The logit difference is the column with the signal. Family-level knockout
   (user story 17) is the analysis that could move accuracy.

### Files touched, for the rebase

- **New:** `component_analysis/knockout.py`, `tests/test_knockout.py` (17 tests,
  both environments), `tests/test_knockout_model.py` (10 tests, nnsight 0.7.0
  only).
- **Shared, one line each:** this ticket's own placeholder line in
  `registry.ANALYSES`, and the module name added to the fresh-interpreter
  nnsight probe in `tests/test_component_analysis.py` (the orchestrator
  confirmed keeping this one).
- **Cherry-picked, not authored here:** `8a8cb9e`, which pins the empty registry
  in `tests/test_analyze_components_end_to_end.py` and adds two DLA seam
  functions to `hooks.py`. The author's own equivalent patch to that test was
  reverted first so the orchestrator's commit lands as itself.
- `hooks.py`, `dataloaders.py`, `analyze_components.py` and the sbatch are
  **untouched** by this ticket's own commits.

### Tests

| env | baseline on `917474d` | final | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 685 passed, 22 skipped | 8 failed, 702 passed, 23 skipped | none (same 8 names) |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 711 passed, 19 skipped | 8 failed, 739 passed, 19 skipped | none (same 8 names) |

The 8 are ticket 01's list, re-derived on this base in both environments. The
base environment's extra skip is `tests/test_knockout_model.py`, skipped at
module level because it holds nnsight 0.7.0 behaviours. A collected-id diff
between the base commit and this branch shows exactly the 17 new tests and
nothing removed, so "no new failures" is by name and by collection, not by
count. (One intermediate base-env run reported 695 rather than 702 passed; it
overlapped a Slurm job deleting and rewriting `outputs/_analyses`, and the
clean rerun matches.)

The mutation check, before the review: replacing the knockout's one replacement
with an empty dict fails
`test_knocking_out_a_component_is_replacing_its_output_with_the_corrupt_one`
and `test_at_least_one_knockout_actually_moves_the_metric`; flipping the sign of
the mean drop fails six of the pure tests. The equality test is not
tautological: the analysis reads its number from the residual through the fp32
readout, the test's independent value comes from `replace_forward`'s traced
logits.

### Open questions for the researcher and the orchestrator

1. **02b's seam note needs one correction, and ticket 08 needs it.** It says "a
   knockout is `replace_forward` with one entry". `replace_forward` returns
   bf16 logits and no residual, so a metric read from it is not the fp32
   ranking ADR-0001 requires. The knockout is
   `capture_forward(..., replacements={key: value})` plus `readout_logits`.
   Ticket 08's metric is the same logit difference and will hit the same wall.
   `hooks.replace_forward`'s own docstring repeats the claim; it is another
   ticket's file on this branch, so it is left to the orchestrator.
2. **Mean and zero ablation.** Refused by name today. Both would need a
   reference distribution this analysis does not compute (the mean over what
   sample, at which positions?), which is why the flag exists rather than the
   schemes.
3. **Family-level knockout** (user story 17) is not this ticket and is the
   analysis that would give the accuracy column something to show.
4. **In-circuit mode** (user story 29, the complement interchange-ablated as a
   check) exists nowhere in the package yet. The Spec reviewer noted it;
   `knockout.py` has no hook for it and needs none until it is built.

### Code review

`mattpocock-skills:code-review` against `917474d`, both axes as parallel
sub-agents. Both handbacks failed and both reports arrived by `SendMessage`
afterwards, so **the review is independent of the author**. Report:
`Alignment/.scratch/component-analysis/reports/07-per-component-knockout-review.md`.

Standards: 1 hard violation (the glossary reserves "baseline", which had reached
a published JSON key) and 7 judgement calls; fixed the hard one, the two dead
parameters, the duplicated key coercion, the duplicated test and the naming;
suppressed the scheme flag (the ticket specifies it) and the `interp-tooling`
heatmap (superseded by the head table and the ticket's bar chart); referred the
`hooks.py` docstring drift to the orchestrator.

Spec: verdict "ship", all 8 checkboxes met in substance, no requirement missing
and no implementation wrong. Its three scope-creep findings: the duplicated test
(deleted), the loader's honest-pair counts in the JSON (trimmed away), and the
two extra head-table columns (kept, and since named by the orchestrator).
