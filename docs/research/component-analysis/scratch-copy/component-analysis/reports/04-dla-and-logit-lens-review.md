# Code review — 04, direct logit attribution and the logit lens

Fixed point: `917474d` (the block C scaffold's tip). Branch
`ca/04-dla-and-logit-lens`. Diff: `git diff 917474d...HEAD`.

Commits reviewed:

    abe7b26  Say what each Component writes at the Readout, and when the answer flips
    7b9e2de  Let the readout take a shared scale, expose o_proj, and pin the empty registry  (cherry-picked from the integration branch)
    9ca5fc5  Take the shared readout scale, and let the rules run without a model
    1e863e6  Stack the lens flip labels so they can be read
    af0d579  Test the two flags that had no test

## How independent this review is

`mattpocock-skills:code-review` was run with both axes as parallel sub-agents.
Both were killed mid-run by a spend limit, were resumed by SendMessage once it
reset, and **both delivered** — late, after the first report to the
orchestrator, as happened on tickets 02 and 02b. **This review is therefore
independent of the author.**

The two sections below are the author's own pass, written while the sub-agents
were presumed lost; the section "Late independent review" at the end is theirs,
with every finding and its outcome. Where they disagree with the author's pass,
they are right: they found a hard violation and eight judgement calls the
author's pass had missed, and six of those were taken.

## Standards

Sources: `CONTEXT.md` (glossary), `docs/adr/0001-component-analysis-on-raw-hf-model.md`,
`docs/research/interp-tooling.md`, the conventions of `component_analysis/hooks.py`,
`registry.py` and `dataloaders.py`, plus the Fowler smell baseline.

### Hard violations

None found.

The four rules that bind this diff each hold, and each is held by a test rather
than by inspection:

1. **All nnsight access in `hooks.py`.** `component_analysis/dla.py` imports
   nnsight nowhere, reads `model._model` nowhere, and reaches the model only
   through `hooks.capture_forward`, `hooks.readout_logits`,
   `hooks.o_proj_weight`, `hooks.target_minus_distractor`,
   `hooks.device_and_dtype` and `hooks.all_component_keys`. The first draft had
   a private `_head_output_weight` that read `o_proj.weight` through the
   nnsight Envoy; the orchestrator's `8a8cb9e` replaced it with
   `hooks.o_proj_weight`, which is where it belongs.
2. **No nnsight at module import time.** `hooks` is imported inside
   `hooks_module()` and `torch` inside each function that needs it.
   `test_the_analysis_module_does_not_import_nnsight_at_module_scope` runs a
   fresh interpreter and fails if that stops being true.
3. **A PNG and a JSON twin for every figure.** `dla.png`/`dla.json` and
   `logit_lens.png`/`logit_lens.json`. `_pyplot()` selects Agg before importing
   pyplot, the same shape as `evaluation/report.py`.
4. **Tests assert at seams.** The library tests assert on returned numbers, the
   CLI tests on the written head table and the written JSON. No test reaches
   into a hook or an intermediate tensor, with one deliberate exception below.

Glossary vocabulary is used throughout (Component, Circuit Component, Readout,
Target, Distractor, Honest Twin, Matched Honest Instruction, Pressure Clause,
suppressor) and none of the avoided terms appears.

### Judgement calls, and what was done about each

- **Possible Data Clumps.** `(records, ids, per_component, lens, total)` travel
  together from `measure_batch` through `_add_batch` into `Tally.add`, which is
  a type wanting to be born. *Kept.* Five values, two call sites, and the
  alternative is a dataclass whose only job is to be unpacked one line later.
  Named here so a later ticket that adds a sixth knows where the line is.
- **Possible Duplicated Code: `measure_condition` and `measure_paired` share
  the batch loop.** *Kept.* The paired one selects the honest rows, asserts the
  Readout alignment and runs two prompts per batch; folding them together needs
  a flag that changes half the body, which is the shape the smell warns about
  rather than the one it names.
- **Possible Middle Man: `hooks_module()` only performs an import.** *Kept and
  documented at the function.* It exists so that "why is this import inside a
  function" is explained once rather than at nine call sites.
- **`run(ctx)` is long** (about fifty lines: select, measure, build, write,
  return). *Kept.* It is the protocol entry point and reads top to bottom; the
  work it delegates is already named.
- **`Tally` holds three things** — per-Component values, the lens rows and the
  per-instance totals. Arguably three responsibilities. *Kept:* they are one
  condition's per-instance values and they share the stratum assignment, which
  is the only logic in the class.
- **One test reaches through the wrapper.** `test_one_heads_contribution_matches_the_same_thing_computed_by_hand`
  reads `model._model` to recompute one head's contribution from the raw
  HuggingFace modules. *Kept deliberately.* `tests/test_component_analysis.py`'s
  probe exempts test files, and the point of the test is an independent source
  of truth: a check that shares the module's own arithmetic checks nothing.
  `tests/test_component_hooks.py` sets the precedent with
  `plain_readout_logits`.

### Verified by mutation, not by reading

Three claims that a plausible-looking wrong implementation would still satisfy
were checked by breaking the code and watching a test fail:

| mutation | tests that failed |
|---|---|
| `o_proj` slice transposed (`weight[span, :]` for `weight[:, span].T`) | the sum invariant, the by-hand head check, the real-model sum check |
| the honest twin read in its own labels (`direction_sign` returns +1) | the direction rule, the CLI-seam twin column |

Both mutations type-check and produce plausible rankings, which is why they
were worth checking rather than reading.

## Spec

Sources: `issues/04-dla-and-logit-lens.md` (the acceptance criteria),
`spec.md` (Implementation and Testing Decisions, user stories 12 to 15 and 27
to 31), `agent-brief.md`, and ticket 02b's seam notes.

### Requirements met

Every checkbox of ticket 04 is implemented and, except the GPU one, held by a
test. The spec's DLA decision — *"Per-Component contribution at the Readout
projected through fp32 final RMSNorm (using the actual scale at that position)
and unembedding onto Target minus Distractor. Columns: pressure DLA,
honest-instruction DLA, differential, suppression flag. Logit lens is the
cumulative residual version across layers."* — is implemented in full, all four
columns.

### Findings

1. **The head-table column names do not themselves say which contrast is
   paired.** Spec user story 27: *"a paired honest-instruction column and an
   unpaired honest-twin column beside every descriptive analysis, clearly
   labelled paired versus descriptive, so that I never read a population
   contrast as a causal one."* The columns were `dla.honest_instruction` and
   `dla.honest_twin`, distinct but not carrying the word. **Since fixed**, on
   the orchestrator's rule after the spec review raised the same point: every
   column computed on the unpaired Honest Twin dataset now ends in
   `_descriptive`, so `dla.honest_twin_descriptive` and
   `dla.honest_twin_descriptive_se`, while paired columns keep bare names.
2. **`dla.honest_instruction` and `dla.differential` are ticket 06's columns,
   delivered here.** On the orchestrator's explicit instruction, recorded in
   the ticket comments. Not scope creep, but ticket 06 shrinks to its flag, its
   paired scatter PNG and the attention side.
3. **Four columns beyond the ticket's list.** `dla.pressure_se`,
   `dla.honest_twin_descriptive_se`,
   `dla.differential_se` and `dla.pressure_paired`. The first two make a mean
   readable as a measurement; the third is the differential's left term, and
   without it a reader would subtract `dla.honest_instruction` from
   `dla.pressure`, which is the full-split mean over a different population and
   not what the differential is. *Kept, and named here as the addition it is.*
4. **The suppression margin is a judgement the researcher should confirm.**
   The ticket says *"true when dla_pressure is negative beyond a documented
   margin"* without fixing the number. `--dla-suppression-margin` defaults to
   0.05 logits, documented at `DEFAULT_SUPPRESSION_MARGIN` against both scales
   it sits between. On SDR nls0.3 it flags nothing — see the ticket comments,
   where the reason is that no Component on that circuit is negative by more
   than its own standard error, not that the margin is too coarse.
5. **Two flags shipped untested and were given tests during this review.**
   `--dla-max-batches` (shorten a condition for a smoke run) and
   `--dla-sum-check off` had no test; `af0d579` adds one that asserts a single
   batch is measured and that the extra forward pass is skipped, plus one that
   an unknown `--dla-conditions` name is refused rather than silently measuring
   nothing.
6. **`--dla-sum-check` is not in the ticket.** It spends one extra forward pass
   per run recording whether DLA over all 1057 senders reproduces the Readout
   logit difference on the real bfloat16 model. *Kept:* the ticket's invariant
   test runs in fp32 on a 2-layer CPU model, and whether it survives bfloat16
   at 32 layers is exactly the thing a reader of a head table needs to know. It
   is a flag and it can be switched off.

### Nothing found missing

The descriptive conditions read the full test split (1000 instances, 125
batches, checked on the real cell by `--dry-run`); the paired condition reads
the causal sample and only the 71 instances with a counterpart; the lens is the
cumulative residual per layer, 33 rows for a 32-layer model, with row 0 the
embedding; `--dry-run` writes no analysis file and loads no model, which
`test_the_dry_run_estimates_every_condition_and_writes_no_dla_files` asserts by
listing the output directory.

### One inefficiency, seen and left

`estimate(ctx)` builds the Honest Twin loader to report its instance count, and
unlike `ctx.descriptive_batches()` that loader is not memoized on the context,
so `run` tokenizes the twin's 1000 prompts a second time. Seconds, not a bug,
and the alternative is either reaching into `ctx._loaders` or widening the
context's API — a shared file this ticket may not touch. Named here so a later
reviewer knows it was seen.

## Late independent review — delivered, and it was worth waiting for

Both sub-agents were killed mid-run by a spend limit, resumed by SendMessage
once it reset, and **both delivered**, after the first report to the
orchestrator. The review is therefore **independent of the author after all**,
and the findings below are theirs. Both reviewed `7b9e2de`, so a few of their
points were already fixed in `9ca5fc5`; those are marked stale.

### Standards axis

| # | finding | outcome |
|---|---|---|
| 1 | **Hard, rule 4.** `test_the_residual_the_lens_reads_is_the_one_the_final_norm_sees` asserts hooks wiring (`readout_logits(capture.residual[:, -1]) == capture.logits`), has no DLA seam in it, and duplicates `test_component_hooks.py::test_the_fp32_readout_reproduces_the_models_own_logits`. | **Taken.** Deleted. It was written as the premise of the lens and the reviewer is right that hooks owns that premise. |
| 2 | *Mysterious Name.* `sign_flip_layer` returns a **row**, not a layer: row 0 is the embedding. The plot already said "row" while the JSON key said "layer". | **Taken**, and the spec reviewer raised it too. Renamed `sign_flip_row` and `sign_change_rows`; `layer_of_row` added; both `sign_flip_row` and `sign_flip_layer` are now written, and `logit_lens.json`'s `rows` note says a row is not a layer. |
| 3 | *Primitive Obsession.* `"pressure_paired"` and `"differential"` are bare literals while their siblings are constants. | **Taken.** `PRESSURE_PAIRED` and `DIFFERENTIAL`, documented as derived conditions that `--dla-conditions` cannot select. |
| 4 | *Implicit contract.* `_add_batch` splits on "the embedding is the last key", a convention set 250 lines away. | **Already fixed in `9ca5fc5`** (found by key, not position) — stale against `7b9e2de`. The fix is now stricter still: a tally with no embedding key is refused by name rather than reported as zero. |
| 5 | *Minor.* `plot_components` returns without writing a PNG when no condition survives, leaving JSON beside no figure and the run reporting success. | **Taken.** `_empty_figure` writes a figure saying why it is empty, for both plots. |
| 6 | *Duplicated Code.* `columns(payload)` computed twice, `lens_payload` twice. | **Taken.** The lens payload was already built once in `9ca5fc5`; the column table is now built once in `run` and handed to the figure. |
| 7 | *Duplicated Code.* `_pyplot()` is verbatim `evaluation/report.py:15`. | **Considered and kept.** That function is private to `evaluation.report`; importing it would mean reaching into another package's privates and pulling the evaluator's reporting module into the analysis package, which is a worse trade than four lines. |
| 8 | *Stale docstring.* `hooks.readout_logits` still says `residual` may be "one Component's contribution", which without `scale_from` is the wrong reading. | **Fixed by the orchestrator** in `4c9ee6b` on the integration branch, `hooks.py` being outside this ticket. The docstring now says to pass the full residual as `scale_from` for a contribution. |
| 9 | *Guard downgrade.* `hooks.o_proj_weight` uses a bare `assert` (stripped under `-O`) where its predecessor raised. | **Fixed by the orchestrator** in the same commit: it raises `NotImplementedError` on a bias. `4c9ee6b` also corrected `replace_forward`'s docstring, which claimed to be the analyses' metric path. No cherry-pick; the rebase picks it up. |

The reviewer checked the numerical core independently — the column slice and
its GQA safety, the `scale_from` broadcast, `repeat_interleave` matching the
reshape order, the lens's own-scale normalization, `paired_difference`'s id
guard — and found no defect. Vocabulary clean against CONTEXT.md's avoid lists.

### Spec axis

| # | finding | outcome |
|---|---|---|
| 1 | Checkboxes unticked, no `## Comments`, no review report. | **Stale**: all three existed by the time the report arrived. |
| 2 | Story 27's "clearly labelled paired versus descriptive" lives only in `dla.json`; the head table has bare `dla.honest_twin`. | **Taken**, on the orchestrator's rule: the descriptive column is now `dla.honest_twin_descriptive`, with `dla.honest_twin_descriptive_se` beside it. Paired columns keep their bare names. |
| 3 | Ticket 06's paired DLA scatter is absent. | **Correct, and left to 06.** Not ticked. |
| 4 | `sign_flip_layer` returns a row. | Same as Standards #2. **Taken.** |
| 5 | `_add_batch` assumes the embedding is last; the tests put it first, so a reorder would silently corrupt `circuit_components_sum`. | **Already fixed, and strengthened.** See Standards #4. |
| 6 | `direction_sign` hard-codes −1 for the twin while `--dla-honest-twin-dir` takes any directory; the records carry `condition == "honest"`, so assert it. | **Taken.** `assert_honest_twin` refuses a split whose records say anything else, with a test that points the flag at a deceptive split and asserts the condition is skipped by name rather than silently sign-flipped. |
| 7 | `condition_batches` gates the purely descriptive pressure condition on `uncovered_reason`, which is the causal-pairing gate. | **Taken.** Each condition is gated on what it needs; the mechanism-task gate now applies only to the paired condition, and the descriptive loaders raise their own reason from inside `dataloaders`. |
| 8 | Scope: `sum_check`, `--dla-max-batches`, `--dla-honest-twin-dir`, `sign_changes` were unasked but cheap; keep `sum_check` as the evidence for the GPU checkbox. | Agreed, all kept. |

The reviewer independently verified the fixed scale, the split-versus-sample
sourcing, the lens being cumulative, `--dry-run` writing nothing, and the
honest-twin swap against the data (`sdr_honest` row 0's Target is the
designated item, the base split's is the other one).

### The orchestrator's two rules, both applied

- **Descriptive columns carry the suffix**: `dla.honest_twin_descriptive` and
  `dla.honest_twin_descriptive_se`; paired columns keep bare names.
- **Paired means the same instance ids**: it already did. `dla.differential` is
  the per-instance difference over the instances that have an
  Honest-Instruction Counterfactual, `paired_difference` refuses two tallies
  whose id lists differ, and `pressure_paired` is a named condition in
  `dla.json` with its own n and its own instance ids. A new library test builds
  a pair whose honest prompt *is* the pressure prompt and asserts the
  differential is exactly zero on every Component with identical ids on both
  sides.
