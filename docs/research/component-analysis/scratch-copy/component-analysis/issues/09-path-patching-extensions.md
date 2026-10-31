# 09 — Path patching extensions: honest counterfactual, position-specific pass, completeness sweep

**What to build:** Path patching runs over the Honest-Instruction Counterfactual through the same code path as the item-swap pair, and a second, position-specific pass by Segment runs only for sender-receiver pairs whose position-agnostic effect clears a threshold flag (default five percent of the gap). An optional sweep patches every head and MLP block in the model into the Readout so a strong direct-effect Component the pruning missed becomes visible.

**Blocked by:** 05 — Matched Honest Instruction pool; 08 — Path patching, position-agnostic.

**Status:** resolved

- [x] `--counterfactual {item_swap,honest_instruction,both}` selects the pair; the honest pair uses the paired dataset from ticket 05 and its clause-span alignment. *(Spelled `--path-counterfactual` per the block C flag rule.)*
- [x] `--position-threshold` (default 0.05) selects pairs for the Segment pass; Q and MLP receivers take the patch at the configured query positions and K and V receivers at the Segment's key positions; results in `path_patching/segments.json`. *(Spelled `--path-position-threshold`.)*
- [x] `--completeness-sweep` patches all heads and MLPs into the Readout and writes a ranked list with circuit membership marked. *(Spelled `--path-completeness-sweep`; opt-in, see the Comments on the budget.)*
- [x] Head-table columns per counterfactual; a column flagging non-circuit Components that clear the threshold in the sweep.
- [x] PNG: per-pair Segment heatmaps for the selected pairs; sweep bar chart with circuit Components highlighted.
- [x] Test: on the tiny model, the Segment pass over all Segments sums to the position-agnostic cell; the honest counterfactual through the same function reproduces the corrupt logits when every sender is patched. *("Sums to" is asserted as the union of every Segment's positions reproducing the position-agnostic cell; see the Comments.)*
- [x] Verified by a Slurm run on SDR within the short-job budget; the pre-registered mid-layer Q-versus-V question is answerable from the outputs.
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

One module changed, `component_analysis/path_patching.py`, and its three test
modules. **No shared file was touched** — not `analyze_components.py`, not
`dataloaders.py`, not `hooks.py`, not `registry.py`, not the sbatch, not a
shared test. Branch `ca/09-path-patching-extensions`, base `a74d54b`.

**The counterfactual is one parameter, not a second implementation.**
`counterfactual_pair(batch, counterfactual)` is the only function that knows
which pair is which; it returns the rows of the batch that have that pair and
the two aligned tensors, and everything below it takes two captured streams and
does not care where they came from. That is user story 24's "same code path",
and it is the one signature ticket 08's comments predicted it would be. The
honest pair exists only for the instances that survived ticket 05's
clean-stream filter, so its pass covers a subset of the causal sample; the
instances it left out are named in the file rather than filled in with zeros,
and a counterfactual with no instance at all writes a file that says so
(an absent file and a crash look the same).

**The position-specific pass.** `--path-position-threshold` (default 0.05)
selects the cells whose position-agnostic effect clears it, strongest first. K
and V receivers are swept Segment by Segment at the Segment's key positions; Q,
MLP and Readout receivers take **one** patch at the query positions, which is
the spec's rule and not a saving — their input is read at the position the
model answers from, so a Segment sweep over them would sweep positions the
receiver does not read. Pass 1 is shared across a cell's Segments: what the
receiver reads while the sender carries its counterfactual value does not
depend on where that value is later written in.

**The completeness sweep** (`--path-completeness-sweep`, opt-in) patches every
head and MLP block of the whole model into the Readout, ranks them and marks
circuit membership. It is one forward per sender per batch rather than two: a
replacement at the Readout receiver is written into the final norm's input and
saved straight back out of it, so pass 2 would rewrite the value pass 1 already
read. `test_the_sweep_shortcut_is_the_same_number_as_the_two_pass_direct_effect`
asserts the two are **bit-identical** (`torch.equal`, not `allclose`). That
halving is what brings the pass inside an A100 hour.

### Deviations from the ticket's literal wording

1. **The flags carry the analysis prefix.** The ticket writes
   `--counterfactual`, `--position-threshold`, `--completeness-sweep`; the
   block C rule says every analysis flag carries its analysis prefix, so they
   are `--path-counterfactual`, `--path-position-threshold` and
   `--path-completeness-sweep`.
2. **The honest columns are suffixed `_honest_instruction`,** not the
   orchestrator's illustrative `_honest`. `dla` already has both a
   `honest_instruction` column and a `honest_twin_descriptive` one, and
   `_honest` would not say which of the two this is. So the columns are
   `path_patching.direct_effect` and
   `path_patching.direct_effect_honest_instruction`, and likewise for
   `strongest_incoming`, `strongest_outgoing` and their `_effect` and `_se`
   partners. The item-swap names are unchanged, so a head table written before
   this ticket still reads.
3. **"The Segment pass over all Segments sums to the position-agnostic cell"
   is asserted as a union, not an arithmetic sum.** The Segments partition the
   prompt, so patching the receiver at the union of every Segment's positions
   must reproduce the position-agnostic cell — that is a true invariant and it
   is what the tests assert, at the library seam
   (`test_patching_every_segment_at_once_is_the_position_agnostic_cell`) and
   again at the CLI seam on every K and V cell of the tiny model. The
   arithmetic sum of the per-Segment effects is **not** expected to equal the
   cell, because a receiver's forward is not linear in its input; it is
   recorded as `sum_of_segments` beside `union` and `agnostic` in every row so
   the researcher can see the size of the gap rather than be told about it.
4. **The sweep runs once,** on the item-swap pair when that is selected and on
   the single selected pair otherwise, rather than once per counterfactual. It
   asks whether pruning missed a Component, which is a question about the
   circuit's own Corruption, and running it twice does not fit the hour.
   `sweep.json` records which pair it ran on.
5. **Two Slurm jobs, not one.** The counterfactual and Segment passes together
   with the sweep do not fit one 55-minute A100 job (see the budget below), and
   the ticket's own escape clause says to make the sweep opt-in and say so. It
   is opt-in by flag, and the verification is split accordingly.

### Sign convention

Unchanged and stated in every file this analysis writes. A cell is
`(patched - clean) / (clean - counterfactual)`, so **negative means the path
carries the counterfactual** — the opposite of knockout's positive drop. Each
JSON's `metric` block spells it out and names knockout as the opposite, per the
researcher's block D decision; ticket 10 settles one vocabulary.

### K and V coverage

Unchanged from ticket 08 and recorded per receiver: `covers_heads` is every
query head a patch at that KV group reaches, circuit member or not, and
`circuit_heads` is the subset in the circuit. A K or V cell is not attributable
to one circuit head alone, and the honest-counterfactual Q-versus-V reading
below carries that caveat.

### Tests

This ticket contributes 25 tests. Both suites were re-derived on the branch
base `a74d54b` first and judged by failure **name**, not count.

| env | baseline on `a74d54b` | final | new failures |
|---|---|---|---|
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 836 passed, 19 skipped | 8 failed, 859 passed, 19 skipped | none, the same 8 names |
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 751 passed, 42 skipped | 8 failed, 760 passed, 42 skipped | none, the same 8 names |

The 8 are ticket 01's list, identical by name in both environments. No
`core.claude*` dump was produced.

The split follows ticket 08's: `tests/test_path_patching.py` (both envs, no
model — the counterfactual selection, the filename rule, threshold selection,
Segment masks, and a drift check that this module's `DEFAULT_QUERY_POSITION`
still equals ticket 03's), `tests/test_path_patching_cli.py` (both envs —
`--dry-run` sizing every new pass and writing nothing), and
`tests/test_path_patching_passes.py` (nnsight 0.7.0 only — the honest
counterfactual through `capture_streams` and `patched_readout`, the union
invariant, the sweep shortcut, and the CLI runs).

One test-seam limitation, shared with ticket 04: the CLI fixture's dataset has
no Matched Honest pool, and the loaders take their pool directory from the repo
default rather than from a flag, so the **CLI-seam** honest run exercises the
skipped path. The honest pass's real behaviour — its own file, its own
counterfactual field, its row selection and its unpaired report — is asserted
at the library seam through `agnostic_pass` with a small stub context. Giving
`dataloaders` a `pools_dir` passthrough would fix it and is a shared-file
change this ticket deliberately did not make.

### Commits

    52f94f2  Drop --path-instances: a prefix of a stratified sample is not stratified
    1408b5a  Run both counterfactuals through one cell function
    58b5536  Say where in the prompt a strong path carries its effect
    8a2283c  Ask whether the pruning missed a Component, with a completeness sweep
    af1d65a  Fix the Segment column list once per pass, not once per batch
    dbbbe40  Name the per-counterfactual filename rule in public

`52f94f2` is the researcher's ruling, taken as its own commit as asked:
`--path-instances` and both of its tests are gone (one in
`tests/test_path_patching_cli.py`, one in `tests/test_path_patching_passes.py`),
and the estimate and the run now size themselves from the loader.

### The code review, and what it changed

Both axes ran as sub-agents against the fixed point `a74d54b`. Their
handbacks failed — the `SubagentHandback` path reports "the agent that spawned
you is no longer running" — but both reports arrived by `SendMessage`, as the
brief said they would. The full review, including the implementer's own pass,
is at `reports/09-path-patching-extensions-review.md`.

**Spec axis: nothing blocking.** All six stated deviations were accepted, and
the reviewer confirmed the one-forward Readout shortcut against
`hooks.py` line by line (`final = model.model.norm.input` is replaced *before*
`saved[READOUT_KEY] = final.save()`). One real defect found and **fixed**:

- `query_segment_names` read `--query-positions` without ticket 03's
  validation, and with `--analyses path_patching` ticket 03's own check never
  runs. A misspelled Segment gave an all-false mask, so every Q, MLP and
  Readout entry came back with a null mean and no error — a typo
  indistinguishable from a path that carries nothing. It is now refused by
  name, during `--dry-run` on the login node as well as in the pass.

**Standards axis: no documented-standard violation, hard or judgement**, and
seven smells. Fixed on the orchestrator's ruling:

- `--dry-run` omitted the two forwards per batch that the position-specific
  pass and the sweep each spend re-capturing the streams. The estimate is what
  a job is sized by and ticket 08 verified it against the measured rate, so it
  counts them now and uses the run's own Segment count rather than a
  hand-waved one.
- The threshold default was spelled three times; it is one constant.
- Production wrote filenames as literal stems while the tests read constants,
  so a renamed file could have passed its own test. Both sides go through one
  stem constant now, and the two new figures have the filename constants the
  older two already had.
- `union` and `query_positions` are rows of the position-specific table that
  are **not** Segments. A `--segment` override using either name would have
  overwritten one silently; it is refused.
- The three passes each repeated the same batch preamble. `stream_batches`
  holds it once.
- The honest-instruction string is pinned against `dla`'s spelling by a
  cross-module test, as the default query position already was.

Recorded as judgement calls and **not** changed, per the orchestrator: the
`_honest_instruction` column suffix stays (the spec reviewer accepted it);
`Streams.counterfactual` and `Streams.rows` are written and not read by
production code; `_Tally.unpaired` is meaningful for the honest pair only.

### Deviation the spec reviewer asked to be declared

**One Segment heatmap, not one per pair.** The ticket line reads "per-pair
Segment heatmaps for the selected pairs"; what is written is a single
`segments_heatmap.png` with **one row per selected pair** and one column per
Segment, plus the trailing `query_positions` column for the receivers that are
not swept by Segment. It is information-equivalent to a stack of one-row
heatmaps and readable as one figure; the JSON twin carries every number
per pair either way. Say so if the researcher wants them separated.

### The two column sets cover different samples

`path_patching.direct_effect` and its siblings are computed over the **100**
instances of the causal sample; `path_patching.direct_effect_honest_instruction`
and its siblings over the **71** of them that have a Matched Honest survivor
under the clean-stream criterion. The JSON records
`sample.n_without_a_counterpart` and names the instances, but the CSV column
names do not, so a reader comparing the two column sets across a row is not
comparing the same sample. Ticket 10 may want the column name to carry it.

### The threshold is now two flags

The orchestrator's ruling, after a queued verification job made the problem
concrete. `--path-position-threshold` decided two unrelated things: which cells
earn the position-specific pass, and which Components outside the circuit the
completeness sweep calls strong. A job had been submitted with the threshold
raised to 1.0 to quiet the Segment pass, which would also have flagged nothing
in the sweep and left the head-table flag column with no evidence behind it,
with nothing in the output to say so. That job was cancelled before it ran.

`--path-sweep-threshold` now names the second question. It defaults to
`--path-position-threshold`'s value, so an existing command line means what it
used to, and `sweep.json` records which flag its threshold came from. Ticket 10
may want to fold both into the roles vocabulary.

### The default threshold, and what the verification used

The code default stays at **0.05**, which is what the ticket fixes. On SDR
nls0.3 that selects exactly **one** cell — `mlp.31.0 -> readout` at -0.0944 —
and it is a Readout receiver, so at the default the Segment pass has no K or V
cell to sweep and produces one `query_positions` entry and nothing else. The
researcher may want to reset the default in ticket 10; the number to reset it
against is in ticket 08's cell table.

The verification therefore ran at `--path-position-threshold 0.0035`, not the
0.004 the orchestrator suggested: ticket 08 measured `head.13.17 -> k.17.6` at
**+0.00396**, which falls just outside 0.004 and would have left the pass with
a single V receiver. At 0.0035 four K and V cells are swept
(`v.9.3`, `k.17.6`, `k.13.4`, `k.24.6`) alongside the Q, MLP and Readout cells.

### Slurm read-back (2026-09-20)

Read back by the close-out agent from the files the two jobs wrote; nothing
was rerun. Both jobs were submitted at 14:06:13 on 2026-09-16 with
`--time=00:55:00` and both COMPLETED **on `gpuA40x4`**, one A40 each — not
the A100 that ticket 08's job 22111541 ran on. That card change is the one
fact that shapes the regression check below.

| job | pass(es) | card | elapsed | limit |
|---|---|---|---|---|
| 22124442 | `--path-counterfactual both`, `--path-position-threshold 0.0035`, 100 instances | A40 (gpub004) | 39:11 | 55:00 |
| 22124443 | `--path-completeness-sweep` at the default 0.05, 64 instances | A40 (gpub008) | 41:28 | 55:00 |

Every file the module names exists under the two suites: for 22124442 the
item-swap and honest `agnostic*.json`, `segments*.json`, the `heatmap*`,
`direct_effect*` and `segments_heatmap*` PNG/JSON twins, the head table,
`sample.json` and `segmentation.json`; for 22124443 the same item-swap set plus
`sweep.json` and the `sweep_bars` twin. No file is malformed, no cell is
without a mean, no instance was excluded by the gap in any pass.

#### a. Regression check against ticket 08 (item-swap, position-agnostic)

Same 100 instance ids in the same order, 393 cells in both files, 13 batches
of 8. The check ticket 08 invites — bit-identity — **could not be run as
posed**, because ticket 08's cells came off an A100 and these off an A40, and
a bf16 forward is not the same number on the two cards. What the comparison
does show:

| | |
|---|---|
| cells bit-identical | 2 of 393 (the two `embed` cells that are exactly 0) |
| max absolute difference | 0.0050 (`head.5.11 -> v.9.3`, +0.0048 on the A100, -0.0003 on the A40) |
| median absolute difference | 0.0007 |
| cells whose sign changed | **159**, every one with \|mean\| < 0.005 in **both** runs |
| clean-minus-corrupt gap | 3.3391 (A100) versus **3.2585** (A40), same instances |

The strong cells reproduce. Every cell ticket 08 measured at or above 0.006
agrees to within 6% relative:

| cell | ticket 08 (A100) | ticket 09 (A40) | se (A40) |
|---|---|---|---|
| `mlp.31.0 -> readout` | -0.0944 | -0.0951 | 0.0161 |
| `head.24.25 -> readout` | -0.0194 | -0.0193 | 0.0047 |
| `head.17.25 -> readout` | -0.0191 | -0.0192 | 0.0014 |
| `head.17.25 -> mlp_in.31.0` | -0.0166 | -0.0161 | 0.0014 |
| `head.24.18 -> readout` | -0.0156 | -0.0159 | 0.0037 |
| `head.14.22 -> q.17.25` | -0.0070 | -0.0066 | 0.0018 |
| `embed -> q.5.11` | +0.0061 | +0.0022 | 0.0026 |
| `head.5.11 -> v.9.3` | +0.0048 | -0.0003 | 0.0016 |
| `head.17.25 -> q.24.18` | -0.0043 | -0.0032 | 0.0011 |
| `head.13.17 -> k.17.6` | +0.0040 | +0.0043 | 0.0011 |

**Attribution.** The unpatched gap itself moved on identical instances, and
the unpatched forwards go through `hooks.py`, which this ticket did not touch.
Ticket 07's knockout job 22110635 ran on an A40 over the same 100 ids and
recorded the scaffold's clean-minus-corrupt gap as **+3.2585** — this run's
number to four decimals. So the A40 forward is reproduced exactly at the gap
level, and the cell differences are the cross-card bf16 floor, about 0.005 of
the gap (a cell of 0.003 is 0.01 logits per instance, under one bf16 ulp of a
logit near 16). Same-card reproducibility is demonstrated inside job 22124442:
on all nine K and V cells of the Segment pass across both counterfactuals,
`union` (a forward recomputed after re-capturing the streams) reproduces
`agnostic` with `union_minus_agnostic` **exactly 0.0**, and every Readout and
`mlp_in.31.0` `query_positions` entry equals its agnostic cell exactly (the
Q entries do not, and are not expected to; see c).

**Verdict:** the refactor reproduces ticket 08 on every cell that is
distinguishable from zero, and reproduces the A40 forward exactly. A strict
bit-identity check against ticket 08 needs an A100 rerun, which is the
researcher's call. Ticket 08's cells ranked 7 to 9 (`embed -> q.5.11`,
`head.5.11 -> v.9.3`, `head.17.25 -> q.24.18`) shrink or flip on the A40; they
were single-card numbers.

#### b. The Honest-Instruction Counterfactual, position-agnostic

| | |
|---|---|
| instances with a Matched Honest counterpart | **71** of 100 (the 29 without are named in `agnostic_honest_instruction.json`) |
| excluded by gap | 0; cells without a mean: none |
| clean-minus-honest gap | mean **3.9325**, range [1.6519, 6.8321], positive on 71 of 71 |
| forwards / wall | 5382 / 764 s |

Sign convention on this pair: clean is the pressure prompt, the counterfactual
is the same prompt with its Pressure Clause replaced by its Matched Honest
Instruction, and a **negative** cell is a path that carries the Honest
Instruction toward the honest answer.

The strongest ten cells, with the item-swap value of the same cell beside it:

| cell | honest-instruction | se | item-swap |
|---|---|---|---|
| `mlp.31.0 -> readout` | -0.0770 | 0.0229 | -0.0951 |
| `head.24.25 -> readout` | -0.0209 | 0.0060 | -0.0193 |
| `head.24.18 -> readout` | -0.0167 | 0.0044 | -0.0159 |
| `head.8.15 -> v.9.3` | **+0.0155** | 0.0023 | -0.0017 |
| `head.17.25 -> readout` | -0.0088 | 0.0007 | -0.0192 |
| `head.17.25 -> mlp_in.31.0` | -0.0073 | 0.0008 | -0.0161 |
| `head.14.22 -> q.17.25` | **+0.0068** | 0.0013 | **-0.0066** |
| `head.5.5 -> k.8.3` | -0.0064 | 0.0022 | +0.0019 |
| `head.8.14 -> v.14.1` | -0.0060 | 0.0014 | -0.0006 |
| `head.13.17 -> q.14.7` | +0.0057 | 0.0014 | -0.0018 |

The Readout edges of the two late heads are unchanged between the pairs;
`head.17.25`'s two edges halve; `head.14.22 -> q.17.25` flips sign. The 18
Components' direct effects sum to -0.121 of the honest gap (item-swap: -0.146).

**The pre-registered mid-layer Q-versus-V question.** The circuit is 17 heads
plus `mlp.31.0` (from the head table): layer 5 heads 5, 6, 8, 9, 11; layer 8
heads 12, 14, 15; `head.9.12`; `head.13.17`; layer 14 heads 7, 21, 22;
`head.17.25`; layer 24 heads 18, 25; `head.27.4`. The mid-layer heads, layers
9 to 17, are six: `9.12`, `13.17`, `14.7`, `14.21`, `14.22`, `17.25`. For each,
the strongest single honest-instruction cell landing on its Q receiver against
its K and V receivers (K and V are per KV group and cover heads outside the
circuit; `covers_heads` is in the JSON):

| head | Q: strongest incoming | K: strongest incoming | V: strongest incoming | Q / K / V signed column sums |
|---|---|---|---|---|
| `9.12` (kv 3) | `head.5.5` +0.0027 | `head.5.11` +0.0024 | `head.8.15` **+0.0155** | +0.004 / +0.003 / +0.014 |
| `13.17` (kv 4) | `head.9.12` +0.0027 | `head.9.12` +0.0025 | `head.8.12` -0.0019 | +0.005 / -0.005 / -0.006 |
| `14.7` (kv 1) | `head.13.17` **+0.0057** | `head.8.14` -0.0028 | `head.8.14` **-0.0060** | +0.006 / +0.006 / -0.007 |
| `14.21` (kv 5) | `head.13.17` +0.0054 | `head.5.6` -0.0012 | `head.5.5` -0.0024 | +0.004 / -0.005 / -0.007 |
| `14.22` (kv 5) | `head.13.17` +0.0029 | `head.5.6` -0.0012 | `head.5.5` -0.0024 | +0.001 / -0.005 / -0.007 |
| `17.25` (kv 6) | `head.14.22` **+0.0068** | `head.14.21` -0.0032 | `head.5.5` -0.0019 | -0.005 / -0.012 / -0.013 |

Answer, by band:

- **Layers 13 to 14** (the spec's 12-to-15 band, where the circuit has four
  heads): Q and V are **level**. The strongest Q cell is +0.0057
  (`head.13.17 -> q.14.7`, 4.0 se) against the strongest V cell -0.0060
  (`head.8.14 -> v.14.1`, 4.3 se), with opposite signs. The Q cells into
  `14.7` and `14.21` are **positive**: patching the Honest Instruction into
  those queries moves the metric *away* from the honest answer. Recorded, not
  interpreted.
  The Segment pass adds that these two Q cells fall to -0.0007 and +0.0009
  when the patch is confined to the Readout query position (see c), so
  whatever enters those queries does so at positions other than the Readout.
- **Layer 9**: V dominates by **5.7x** on one cell, `head.8.15 -> v.9.3` at
  +0.0155 (6.8 se), the largest non-Readout cell of the honest grid. The
  Segment pass puts 0.0116 of it in the Pressure Clause (see c). `v.9.3` covers
  heads 12 to 15 of layer 9 and only `9.12` is in the circuit.
- **Layer 17**: Q wins on the single strongest cell (+0.0068 against K
  -0.0032, 2.1x), but the K and V columns sum to more than twice Q's
  (-0.012 and -0.013 against -0.005), because Q's cells cancel and K's and V's
  do not.

So the honest-instruction pass does **not** show the lie signal entering the
mid heads' queries in preference to their values: the largest such path enters
a V input at layer 9 from `head.8.15`, read from the Pressure Clause, and in
the 13-to-14 band the Q and V effects are the same size with opposite signs.
Every cell here is between 4 and 7 se and none exceeds 0.016 of the gap.

#### c. The Segment pass at `--path-position-threshold 0.0035`

Query positions: `readout`. No instance lacked a segmentation. The 18
Segments are those of `segmentation.json`.

**Correction to the paragraph above** ("at 0.0035 four K and V cells are swept:
`v.9.3`, `k.17.6`, `k.13.4`, `k.24.6`"): that prediction was made from ticket
08's A100 cells. On the A40 the item-swap pass selected **14** cells — 4
Readout, 2 `mlp_in`, 3 Q, **5 K and no V**. `head.5.11 -> v.9.3` fell from
+0.0048 to -0.0003 and `head.9.12 -> k.13.4` from +0.0037 to +0.0019, both
below the threshold; `embed -> k.5.2`, `head.14.22 -> k.17.6` and
`head.5.6 -> k.8.3` rose above it. Selection at this threshold is inside the
cross-card floor, which is an input to ticket 10's default.

The Q, MLP and Readout cells take one `query_positions` entry each, the patch
confined to the Readout query position. For the Readout and `mlp_in.31.0`
receivers that entry **equals the agnostic cell exactly** (nothing downstream
of layer 31 reads another position). For the Q receivers it does not, and the
difference is how much of the cell's effect lands at positions other than the
Readout:

| cell | pair | agnostic | `query_positions` | se |
|---|---|---|---|---|
| `head.14.22 -> q.17.25` | item-swap | -0.0066 | -0.0065 | 0.0016 |
| `head.14.7 -> q.17.25` | item-swap | +0.0037 | +0.0026 | 0.0010 |
| `head.5.5 -> q.8.12` | item-swap | -0.0037 | -0.0008 | 0.0011 |
| `head.14.22 -> q.17.25` | honest | +0.0068 | +0.0053 | 0.0010 |
| `head.13.17 -> q.14.7` | honest | +0.0057 | **-0.0007** | 0.0010 |
| `head.13.17 -> q.14.21` | honest | +0.0054 | **+0.0009** | 0.0010 |

The two honest-instruction Q cells into layer 14 all but vanish at the Readout
query position: their position-agnostic effect comes from queries at other
positions. The Q input of `head.17.25` from `head.14.22` is read at the Readout
under both pairs.

Item-swap K cells:

| cell | agnostic | union | union - agnostic | Segment carrying the effect | sum of Segments |
|---|---|---|---|---|---|
| `embed -> k.5.2` | -0.0045 | -0.0045 | 0.0 | `designation_site` -0.0045, every other Segment exactly 0 | -0.0045 |
| `head.14.22 -> k.24.6` | -0.0043 | -0.0043 | 0.0 | `item_2_question_option` -0.0024, `item_1_question_option` -0.0018 | -0.0062 |
| `head.13.17 -> k.17.6` | +0.0043 | +0.0043 | 0.0 | `item_1_question_option` +0.0026 | +0.0014 |
| `head.14.22 -> k.17.6` | +0.0040 | +0.0040 | 0.0 | `question` +0.0014, diffuse | +0.0011 |
| `head.5.6 -> k.8.3` | +0.0039 | +0.0039 | 0.0 | diffuse; `inverse_predicate_token`, `other_token`, `designation_suffix` each about -0.0034 | -0.0213 |

Honest-instruction: **12** cells selected (4 Readout, 1 `mlp_in`, 3 Q, 1 K,
3 V):

| cell | agnostic | union | union - agnostic | Segment carrying the effect | sum of Segments |
|---|---|---|---|---|---|
| `head.8.15 -> v.9.3` | +0.0155 | +0.0155 | 0.0 | `pressure_clause` **+0.0116**, `question` +0.0029 | +0.0134 |
| `head.5.5 -> k.8.3` | -0.0064 | -0.0064 | 0.0 | `pressure_clause` -0.0052, `question` -0.0029 | -0.0146 |
| `head.8.14 -> v.14.1` | -0.0060 | -0.0060 | 0.0 | `question` -0.0061, the rest near 0 | -0.0085 |
| `embed -> v.8.3` | -0.0036 | -0.0036 | 0.0 | `pressure_clause` -0.0036, every other Segment exactly 0 | -0.0036 |

**The union check held on all nine K and V cells**, exactly. The two
embedding cells are built-in checks of the pass: the item-swap Corruption edits
one token, and `embed -> k.5.2` lands entirely in `designation_site`; the
honest pair differs only inside the clause, and `embed -> v.8.3` lands entirely
in `pressure_clause`. `sum_of_segments` differs from `union` by up to 5x
(`head.5.6 -> k.8.3`), which is the non-additivity the Comments predicted.

#### d. The completeness sweep (job 22124443)

Ran on the item-swap pair into the Readout, 1057 senders (32 layers x 32 heads
plus 32 MLP blocks, plus the embedding), 18 of them in the circuit, over a
**64-instance draw that is not the grid's 100**: `sample.json` records
`n_requested` 64, seed 0, balanced at 8 per stratum, 25 of the 64 ids in common with the 100, gap mean
2.9084. Threshold **0.05** — this job ran at the default, and `sweep.json`
records `threshold_flag` as `--path-sweep-threshold, defaulting to
--path-position-threshold`. Its own grid's Segment pass selected exactly the
one Readout cell the paragraph above predicts for the default. 8472 forwards,
one per sender per batch; the sweep's `mlp.31.0` value equals this draw's
position-agnostic direct effect **bit-for-bit**, so the one-forward shortcut
holds on the real model as well as the tiny one.

| rank | Component | direct effect | se | in circuit | flagged |
|---|---|---|---|---|---|
| 1 | `mlp.30.0` | **+0.1275** | 0.0175 | no | yes |
| 2 | `mlp.31.0` | -0.1137 | 0.0188 | **yes** | |
| 3 | `mlp.29.0` | +0.0937 | 0.0225 | no | yes |
| 4 | `head.31.0` | -0.0809 | 0.0035 | no | yes |
| 5 | `head.30.24` | -0.0587 | 0.0034 | no | yes |
| 6 | `head.17.24` | -0.0575 | 0.0032 | no | yes |
| 7 | `head.30.12` | -0.0543 | 0.0064 | no | yes |
| 8 | `head.27.7` | -0.0526 | 0.0052 | no | yes |
| 9 | `head.26.15` | +0.0412 | 0.0036 | no | |
| 10 | `head.27.22` | -0.0393 | 0.0088 | no | |
| 11 | `mlp.25.0` | -0.0391 | 0.0108 | no | |
| 12 | `head.27.20` | -0.0379 | 0.0084 | no | |

**Every non-circuit Component clearing 0.05**, so flagged in the head table:
`mlp.30.0`, `mlp.29.0`, `head.31.0`, `head.30.24`, `head.17.24`,
`head.30.12`, `head.27.7` — seven, all in layers 17 and 27 to 31. Two of them
(`mlp.30.0`, `mlp.29.0`) are **positive**: their corrupt-stream output pushes
the Readout against the Corruption. `head.17.24` shares KV group 6 of layer 17
with circuit head `17.25`, so the grid's `k.17.6` and `v.17.6` cells already
cover it. Circuit members' ranks: `mlp.31.0` 2, `head.24.18` 23, `head.17.25`
28, `head.24.25` 40, `head.27.4` 145, the other 13 at 175 or below.

| threshold | non-circuit Components clearing it | circuit Components clearing it |
|---|---|---|
| 0.05 | 7 | 1 |
| 0.02 | 25 | 3 |
| 0.01 | 57 | 4 |
| 0.0035 | 108 | 4 |

On this draw the direct effects of all 1057 Components sum to **-0.90** of the
gap (negatives -1.61, positives +0.71); the circuit's 18 sum to **-0.17**. That
bears on ticket 08's first open question: the six sevenths its direct edges
did not carry sit in the direct paths of Components outside the circuit,
mostly late-layer ones, rather than in multi-hop routes inside it.

#### e. Wall time and forwards against the estimate

The dry-run rate is ticket 02b's A40 constant, 0.1848 s per forward, and
these jobs ran on A40s, so this is the first direct test of that constant.
The Segment-pass estimates below are the dry-run's per-cell rates times the
cells actually selected, since the selection is not knowable before the
position-agnostic pass.

| job | pass | forwards | wall | s / forward | estimate |
|---|---|---|---|---|---|
| 22124442 | agnostic, item-swap | 5382 | 1032 s | 0.192 | 995 s |
| 22124442 | agnostic, honest-instruction | 5382 | 764 s | 0.142 | 706 s |
| 22124442 | Segment, item-swap (14 cells) | 1560 | 300 s | 0.193 | 288 s |
| 22124442 | Segment, honest-instruction (12 cells) | 1274 | 181 s | 0.142 | 235 s |
| 22124442 | **total analysis** | 13598 | **2277 s (38.0 min)** | | **2224 s (37.1 min)**, +2% |
| 22124443 | agnostic, item-swap, 64 instances | 3312 | 659 s | 0.199 | 612 s |
| 22124443 | Segment at 0.05 (1 cell) | 32 | 6 s | 0.197 | 6 s |
| 22124443 | completeness sweep | 8472 | 1752 s | 0.207 | 1566 s |
| 22124443 | **total analysis** | 11816 | **2417 s (40.3 min)** | | **2184 s (36.4 min)**, +11% |

Elapsed minus analysis is about 74 s per job for the model load. The constant
is calibrated on the A40 to within 4% for the grid passes and 12% for the
sweep. The honest pass still spends all 5382 forwards (13 batches at reduced
occupancy, 0.142 s each), so the dry-run's 71-of-100 scaling lands close for
the wrong reason. Both jobs finished 13 to 16 minutes inside the 55-minute
limit; the split into two jobs was necessary, since 4694 s of analysis does
not fit one.

#### Bookkeeping noticed, not changed

- The Commits list above stops at `dbbbe40`; the review fixes (`91754f9`) and
  the `--path-sweep-threshold` split are on the branch but not listed. The
  orchestrator is rebasing the branch, so the SHAs are theirs to settle.
- "(see the budget below)" in deviation 5 points at a section this ticket
  never got; the budget is now table e.

#### For the researcher to decide

1. Whether an A100 rerun of the item-swap grid is wanted for a strict
   bit-identity check against ticket 08. The A40 forward is reproduced
   exactly; the cross-card floor is about 0.005 of the gap.
2. Ticket 10's default for `--path-position-threshold`: 0.05 selects one
   cell, 0.0035 selects cells that change membership between cards.
3. The Q-versus-V evidence does not favour Q: the largest honest-instruction
   path into a mid head enters V of layer 9 from `head.8.15` via the Pressure
   Clause, and the 13-to-14 band is level.
4. Seven non-circuit Components clear 0.05 direct effect on the Readout, two
   with positive sign, and non-circuit direct paths carry about three quarters
   of the gap on the 64-instance draw.

### Orchestrator's close-out (2026-09-20)

The implementer was stopped during a login-node slowdown after its two
verification jobs were submitted; a fresh agent did the read-back above.
The full commit list on the branch, which the Commits section above
omits in part, was `52f94f2, 1408b5a, 58b5536, 8a2283c, af1d65a, dbbbe40,
91754f9` (both review axes), `8f28b61` (sweep threshold split). Rebased
onto ticket 06's tip 07bbe43 with no conflicts as `2c32818..19f1fb1` and
fast-forwarded into `component-analysis` (tip 19f1fb1). Suites on the tip:
base 8 failed / 798 passed, mgnp 8 failed / 911 passed, the same 8
pre-existing names in both. "(see the budget below)" in the checkbox note
refers to the cost table in the Slurm read-back. Outputs of record copied to
the `component-analysis` worktree as `outputs/_analyses/ca09-path-patching`
and `ca09-sweep`. The four researcher items from the read-back go into the
block D pause.
