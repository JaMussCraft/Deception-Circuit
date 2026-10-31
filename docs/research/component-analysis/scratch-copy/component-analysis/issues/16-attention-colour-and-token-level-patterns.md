# 16 — Attention heatmaps readable under a blue-light filter, and token-by-token patterns

**What to build:** The attention heatmaps use a colour scheme that stays readable on a screen with a strong blue-light filter, and a segmentless token-by-token rendering of each circuit head's attention pattern is written as PNGs, with a JSON twin only where it stays small.

**Blocked by:** 13 — Paired column names, per-column coverage meta, multi-job cells, lifted job budget.

**Status:** resolved

- [x] The heatmap colormap is a single named constant, warm and perceptually ordered (no reliance on blue or purple to carry the low end; for example a yellow-orange-red sequential map, with an explicit note why), used by every attention PNG and by the review notebook's attention panels; the choice is recorded in the JSON twin's meta.
- [x] `--attention-token-level` renders, for each circuit head and each condition, the mean attention from the configured query positions to every token of the prompt (token by token, no Segments), as a PNG per head with token strings on the axis; where prompts differ in length the rendering is per template or per instance group and says so.
- [x] The JSON twin for the token-level rendering is written only if it is small (state the limit, for example a few MB per cell); above that the PNG's meta JSON records the shape, the instance ids and a pointer to how to regenerate it, and the notebook renders the PNGs inline.
- [x] Tests at the CLI seam on the tiny model: the token-level PNGs exist per head, the colormap constant is the one recorded in the meta, and a long-prompt cell writes the meta-only twin.
- [x] Verified by a short Slurm run on SDR nls0.3 at head-granularity delta; the ticket shows one token-level PNG read back (which tokens L17H25 and L5H11 attend to from the Readout).
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

Six commits on `ca/16-attention-colour-and-token-level-patterns`, base `4ba2877`, tip `4fb2c66`:

    e4c612d  Draw attention in a warm colormap and render each head's attention token by token
    7357bf2  Show attention in the recorded colormap in the notebook, and the token PNGs inline
    73166ec  Name the unclaimed run, the token-level path and the slot Segments plainly
    2b1fc85  Say so when token-level is asked for but no condition was profiled
    111a911  Move the token-level rendering into its own module, and take both reviews
    4fb2c66  Name the recorded colormap in the attention notes, not in the notebook text

**Colour.** `attention_patterns.COLORMAP = "YlOrRd"` runs from light yellow at
zero to dark red at one, and the module docstring says why. It draws every
attention PNG: the Segment heatmaps, the top-heads bars (which used to be blue
`#4c72b0`) and the token-level heatmaps. It is recorded as `colormap` in every
attention JSON twin, in `patterns.json` and in the token-level index. Missing
cells show grey hatching, because on this map zero is the palest colour and a
blank cell would read as zero. The choice is tested rather than asserted. Under
a simulated strong blue-light filter (channel gains R 1.0, G 0.8, B 0.1),
magma keeps 7% of its luminance range in its bottom third and viridis 10%,
while YlOrRd keeps 35%. A pure test refuses magma, viridis and plasma and
passes the constant. Plotly knows the same name with the same ends, also
tested.

**Token level.** The rendering lives in its own module,
`component_analysis/attention_token_level.py`, which registers nothing:
`attention_patterns` adds its two flags to the attention group and its `run`
feeds it and calls its `write` (the standards review's call). `--attention-token-level` writes, under
`attention/token_level/`, one PNG and JSON twin per circuit head, plus one
index, `token_level.json`. Each PNG shows the mean attention from the query
positions (default the Readout) to every prompt token, with no Segment
summing. There is one panel per group and one row per condition. Each panel
title says how many instances each row averages, and each row label carries
its n. The rendering is read from the same eager-attention rows as the Segment
masses, through a new optional `rows_out` argument of `batch_masses`, so it
adds **no forward pass** and `hooks.py` is untouched. Each panel title starts
with its group id (`task_prompts/audit`, `honest_twin_prompts/lab`, and `#2`
after a variant's second layout, if any). When the flag is on but every
condition was skipped, nothing is drawn and `patterns.json["token_level"]` says
why.

How tokens line up, and why it departs from "a representative instance":

- On the real SDR split there are **21 distinct span-width layouts over 1000
  instances**. Grouping by length or by variant alone aligns nothing, and the
  Segment-run order alone gives **one** group that mixes both variants.
- So instances are grouped by **template variant**, then by Segment-run order.
  On SDR that gives one group per variant: audit 782, lab 218.
- A token's place is its Segment run and its offset from the **nearer end** of
  that run. Fixed-width runs line up token for token. Within a variant only
  two runs vary in width, the intro around the entity name and the Pressure
  Clause, and they line up at both ends and are ragged only in the middle.
- Each slot is labelled with its **most common token** and, when that is not
  every instance, the share carrying it (" calcium (22%)"). One instance's
  tokens would be wrong for most instances at the varying slots.
- A slot's value is summed attention divided by the group's n. **Every row
  sums to one, and a Segment's slots sum back to its mass in `patterns.json`**:
  measured to 1.4e-7 on the GPU run, and tested at 1e-4.
- The colour scale is a square root on a fixed 0 to 1 (PowerNorm, gamma 0.5),
  the same for every head. On a linear scale the `<|begin_of_text|>` sink
  leaves every other token at the palest colour.

**The JSON limit is 5 MB per cell**, summed over the per-head twins, and is
set with `--attention-token-level-json-limit BYTES` (default
`attention_token_level.JSON_LIMIT_BYTES`). Under it, each twin carries its values and
each row's eight largest tokens. Over it, every per-head twin is meta-only:
its shape per group, the limit, the full size and the exact flags that rewrite
it in full: the run's own `--query-positions` and `--attention-conditions`, and
`--attention-token-level-json-limit <full size>`. **The instance ids are not
repeated in each per-head twin.** They are recorded once per cell in the
index, under `groups[].rows[].instance_ids`, because every head of a cell is
averaged over the same instances. Every twin says so in its `instance_ids`
field (the spec review's call: accepted, and said in the meta and here). The index is always written and holds the layout, slot
labels and Segments, `n_present` per slot, and the instance ids once per row,
rather than once per head. On SDR nls0.3 the full twins total 0.8 MB, so they
are written in full.

**Notebook.** `review.py` gains `Heatmap.colorscale` and `.value_range`, a
`Picture` shape, `token_level_views(results_dir)`, and the constants
`ATTENTION_COLORMAP`, `ATTENTION_TOP_COLOUR` and `TOKEN_LEVEL_PATH` (derived
from `ATTENTION_SUBDIR`), all pinned to the modules by a test. The attention
section's notes name the colormap the twins record, so the notebook text does
not hard-code it. Attention heatmaps take the colormap their twin
records. A cell written before this ticket falls back to the same name, with a
note saying so. The notebook drew every heatmap in RdBu, and circuitsvis draws
positive values in **blue** by default. Now:

- `show_heatmap` uses the view's sequential map over 0 to 1.
- The circuitsvis Segment panel is one `colored_tokens` line per head in the
  map's darkest colour. `colored_tokens_multi` takes no colour argument.
- The live single-instance cell passes the same colour.
- A new section 2b renders the token-level PNGs inline, with each row's
  largest tokens as notes.

The notebook was verified without running it: nbformat validation, every code
cell joined and `ast.parse`d, and pyflakes clean before and after.

### Files touched

- `component_analysis/attention_patterns.py` (owned): colormap, `rows_out`, and calls into the new module.
- `component_analysis/attention_token_level.py` (new).
- `tests/test_attention_token_level.py` (new, 20 tests).
- Shared, additive: `component_analysis/review.py`, `review_components.ipynb`,
  and one line in `tests/test_component_analysis.py` (the new module added to
  the shared nnsight probe).
- Not touched: `analyze_components.py`, `hooks.py`, `registry.py`,
  `head_table.py`, `dataloaders.py`, `roles.py`, the sbatch, docs and the
  shared tests.
- The new flag is registered by this module's `add_arguments`, as every
  `--attention-*` flag is.

### Tests

| env | baseline on `4ba2877` | final on `4fb2c66` | new failures |
|---|---|---|---|
| login-node base (py3.9, BLAS pins) | 8 failed, 964 passed, 44 skipped | 8 failed, 970 passed, 58 skipped | none, the same 8 names |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 1092 passed, 19 skipped | 8 failed, 1112 passed, 19 skipped | none, the same 8 names |

The failure lists were diffed by name. This branch adds 20 tests. In the base
env, 14 of them (the CLI and notebook-view tests) skip, because ticket 03's
fixtures gate on nnsight 0.7.0. The CLI-seam tests cover:

- one PNG and twin per head;
- the colormap in every twin;
- no output without the flag, and none when nothing was profiled;
- one group per Template Variant, with every instance in exactly one;
- rows summing to one;
- slot sums equal to the Segment masses;
- panel titles naming their group and carrying each row's n;
- meta-only twins under `--attention-token-level-json-limit 1000`, with the
  PNGs still written;
- the regenerate pointer naming the run's flags;
- the notebook views on a full cell and on a meta-only cell.

### Slurm

| job | partition | account | elapsed | code |
|---|---|---|---|---|
| **22874579** | gpuA100x4 | bgrb-delta-gpu | 5:24, COMPLETED | 7357bf2 (before the reviews) |
| **22875076** | gpuA100x4 | bgrb-delta-gpu | 5:06, COMPLETED | 4fb2c66 (the final tip) |

The second job reran the same command into `outputs/_analyses/ca16-token-level2`
after the module move. All 136 token-level rows of the 17 heads are identical
to the first job's, to the last digit, and so is `patterns.json`'s every
condition. That is the check that the refactor changed nothing measured. The
outputs of record are the second job's. The read-back below is the same in both.

Both were rehearsed with `--dry-run` first, which estimated about 7 minutes
on an A40 and said the token level adds no pass. The partition was chosen by
`sbatch --test-only` start estimates over all three accounts and partitions:
bgrb on A100 estimated about 5 hours, beto on A40 about four days. It started
within a minute; the second started within minutes too, despite estimates
of hours to days. The first job's command, submitted from the worktree root (the second differs only in
`--suite-name`/`--output-dir ca16-token-level2`):

    sbatch --account=bgrb-delta-gpu --partition=gpuA100x4 --time=00:40:00 \
      scripts/analyze_components.sbatch \
      --circuit sdr=outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414 \
      --circuit honest_c=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525 \
      --reference honest=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525 \
      --expr "delta=sdr \ honest_c" --compose-granularity head \
      --task-from outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414 \
      --analyses attention_patterns --attention-token-level \
      --suite-name ca16-token-level --output-dir outputs/_analyses/ca16-token-level

The outputs are in the ca-16 worktree, uncommitted, under
`outputs/_analyses/ca16-token-level2/delta__head/sdr/attention/` (and the
identical `ca16-token-level`). That holds 17
token-level PNGs and twins, plus the recoloured Segment heatmaps.

- Every condition's rows sum to one within 0.003, the bf16 level.
- There are no NaN values and no mass outside the segmentation.
- The groups are task_prompts/audit (782 pressure, 33 paired), task_prompts/lab
  (218, 38), honest_twin_prompts/audit (584) and honest_twin_prompts/lab (416). The 33 + 38 = 71
  paired instances match ticket 06.

**Read back from the Readout, pressure condition, audit variant (n=782).** Lab
agrees.

| head | largest tokens (mass) |
|---|---|
| **L17H25** | item 1's quoted option (" calcium", 0.259), `<\|begin_of_text\|>` 0.194, item 2's quoted option 0.095, the opening quote `"` of the answer frame 0.064 |
| **L5H11** | item 1's quoted option 0.364, item 2's quoted option 0.165, `<\|begin_of_text\|>` 0.137, the two " is" tokens of the question 0.074 and 0.073 |

- **L17H25 is a copier of the first option, not a reader of the question
  frame.** Its top Segment in ticket 03 was `question` at 0.265, but that mass
  is spread over about 30 tokens. Token by token, its single largest target
  is the quoted item-1 option token.
- **Under the Matched Honest Instruction, L17H25 moves off the option.** Item
  1's option falls from 0.265 to 0.146, and `<|begin_of_text|>` becomes its
  top token at 0.274. This is the token-level version of ticket 06's
  `question` to `unsegmented` shift, and that shift is the sink.
- **L5H11 reads both quoted options, item 1 about twice item 2.** It is the
  same under the honest instruction (0.362) and on the honest twin (0.381).
- The anchors reproduce ticket 03's table: L17H25 `question` 0.265, and L5H11
  `item_1_question_option` 0.352 against ticket 03's 0.354. Ticket 03's job
  ran with a separate BOS Segment.

### Code review

`mattpocock-skills:code-review` against `4ba2877`, both axes as parallel
sub-agents. Both handbacks failed. Both reports reached the orchestrator, who
forwarded them with calls, and later reached me directly. **The review is
independent on both axes.** Both reports, the calls and the outcome of each
are in `reports/16-attention-colour-and-token-level-patterns-review.md`.

- **Standards: no hard violations, one soft breach, eight smells.**
  - Fixed: the glossary breach ("Template Variant groups"); the token level
    moved to `attention_token_level.py` and into the shared nnsight probe;
    `TokenGroup` owns its slots, rows and most common tokens; the prompt
    families renamed away from the `pressure` string; one helper each for the
    flag lookup and the full/meta-only label; the norm read from `SCALE`; one
    font constant; review.py deriving its path; the notebook text no longer
    naming the map; the unread `n_heads` dropped.
  - Done as cheap judgement calls: `Slot` and `RowKey` named tuples, and the
    figure-size factors named.
  - Kept as judgement calls: the `tokens`/`condition` pair, `rows_out`, and the
    index fields in `patterns.json`.
- **Spec: no blocking issues.**
  - Fixed: the group id in every panel title; an exact regenerate pointer
    plus `--attention-token-level-json-limit`.
  - Accepted and stated: the instance ids by pointer to the index.
  - Kept, as the orchestrator ruled: every unasked extra and the square-root
    scale.

My own pass (`73166ec`) and the advisor's finding (`2b1fc85`) are recorded
there too.

### Open questions for the researcher

These four go into the block E pause as written; the orchestrator kept the
square-root scale and the `all` level for now.

1. **Modal labels instead of one representative instance.** The axis shows
   each slot's most common token and its share. This is the honest label for
   the varying slots, but it mixes instances in the label row. Say if you
   would rather read a single real prompt along the axis.
2. **The square-root colour scale on token-level figures only.** The Segment
   heatmaps stay linear on 0 to 1, unchanged. Say if you want one scale for
   both.
3. **Token level is computed at the `all` level only**, not per split level.
   Per-level figures would double or quadruple the PNG count.
4. **The circuitsvis Segment panel lost its head buttons.** There is now one
   line per head, because the multi-head view has no colour argument and draws
   in blue.
