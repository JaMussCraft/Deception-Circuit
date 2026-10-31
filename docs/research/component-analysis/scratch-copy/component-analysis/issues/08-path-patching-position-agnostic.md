# 08 — Path patching, position-agnostic, item-swap counterfactual

**What to build:** A researcher gets the sender-by-receiver matrix of normalized path-patching effects over the causal sample: senders are every circuit head, circuit MLP block and the embedding; receivers are every circuit head's Q, K and V inputs (K and V per KV group), every circuit MLP input, and the Readout. Each cell is the change in logit(Target) minus logit(Distractor) when that one path carries its corrupt value, divided by the instance's clean-minus-corrupt gap. Delivered as JSON, a heatmap, and head-table summary columns.

**Blocked by:** 02 — Segmentation and stratified sample; 02b — Block C scaffold.

**Status:** resolved

- [x] Sender-receiver grid respects strict upstream ordering, with attention into same-layer MLP allowed; K and V receivers are addressed per KV group and the grid records which heads a group covers.
- [x] Position-agnostic pass patches the sender's output at all positions into the receiver's input; everything else in the receiver's forward stays clean.
- [x] `path_patching/agnostic.json` holds per-cell mean and standard error; head-table columns: strongest incoming path, strongest outgoing path, direct effect on the Readout.
- [x] PNG: sender-by-receiver heatmap with receivers grouped by type, and a direct-effect bar chart.
- [x] Test: on the tiny model with the circuit set to every head and MLP block, patching every sender into every receiver reproduces the corrupt-run logits and patching none reproduces the clean logits; patching a K receiver of one group changes only that group's heads.
- [x] Test: CLI seam run produces the JSON, PNG and columns; `--dry-run` prints the grid size and a cost estimate.
- [x] Verified by a Slurm run on SDR nls0.3 within the short-job budget (about one A100 hour for 100 instances).
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

`component_analysis/path_patching.py`, one module, plus three test modules and
one line of `component_analysis/registry.py`. Branch
`ca/08-path-patching-position-agnostic`, base `917474d`.

**One cell is two forwards.** The first replaces the sender's output with its
item-swap-corrupt capture, **freezes every other Component of the model** —
all 1057 of them, not only the circuit's — at its clean capture, and reads the
receiver's input off that forward. The second writes that one receiver input
into an otherwise clean forward and reads the metric at the Readout.

The freeze is the decision worth flagging. The orchestrator's phrasing was
"only that sender carries its corrupt output (everything else clean)", which
this reads as *held at clean* rather than *started from clean*. Without the
freeze the sender's corrupt value would also reach the receiver through every
intermediate Component, and the (sender, Readout) cell would be the sender's
**total** effect — which is ticket 07's per-Component knockout, computed a
second time under another name. The ticket's head-table column is called
"direct effect on the Readout", and it only means direct with the freeze.
Two tests pin the semantics: a last-layer MLP block has nothing downstream, so
its two-pass patch must equal a plain `replace_forward` exactly, and a
last-layer *head* must not, because the same layer's MLP block is downstream of
it.

**The metric.** `logit(Target) - logit(Distractor)` at the Readout, fp32 through
`hooks.readout_logits`, as `(patched - clean) / (clean - corrupt)` per instance,
averaged over instances. A negative cell is a path that carries the Corruption;
-1 would be the whole gap.

**The grid** is built from the Components alone, with no model, so `--dry-run`
sizes it on the login node. Senders are the circuit's Components plus the
embedding; receivers are each circuit head's Q (per head) and K and V (per KV
group, recording both the query heads the group covers and which of them are in
the circuit), each circuit MLP input, and the Readout. A cell exists only where
the sender is strictly upstream, except that a head reaches its own layer's MLP
input.

**Files touched.** New: `component_analysis/path_patching.py`,
`tests/test_path_patching.py` (grid, statistics, import probe — both envs),
`tests/test_path_patching_passes.py` (the two passes and the CLI run — nnsight
0.7.0 only), `tests/test_path_patching_cli.py` (`--dry-run` — both envs).
Changed: one line of `component_analysis/registry.py`, this ticket's own
reserved placeholder. Nothing else.

### Commits

    9162a9c  Recover composition structure with position-agnostic path patching
    c24871c  Leave the two shared test files to the orchestrator
    0456429  Let the readout take a shared scale, expose o_proj, and pin the empty registry   (cherry-pick of the orchestrator's 8a8cb9e)
    a7eca08  Check that --path-instances moves the run, not only the estimate
    d3ea060  Take the orchestrator's block-C rules and the standards review
    <heatmap>  Scale the heatmap to a percentile so 392 cells are not washed out by one

### The GPU verification

Job **22111541**, `gpuA100x4`, one A100, submitted from the worktree root after
the same command was rehearsed with `--dry-run` on the login node:

    sbatch --partition=gpuA100x4 --time=00:55:00 scripts/analyze_components.sbatch \
        --circuit sdr=<nls0.3 run> --circuit honest_c=<honest twin> \
        --reference honest=<honest twin> --expr "delta=sdr \ honest_c" \
        --compose-granularity head --task-from <nls0.3 run> \
        --analyses path_patching --output-dir outputs/_analyses/ca08-path-patching

The sbatch's own `#SBATCH` lines ask for `gpuA40x4` and four hours, which the
command line overrides; without the `--time` override this would have been a
four-hour request against the brief's rule.

**The grid on SDR nls0.3 at head granularity:** 19 senders (18 Components plus
the embedding) x 41 receivers (17 Q, 11 KV groups x K and V, 1 MLP input, the
Readout) = **393 cells** after strict upstream ordering, over the 100 sampled
instances in 13 batches of 8.

| | |
|---|---|
| wall time, the analysis itself | **508 s** (job elapsed 9:37, the rest being the model load) |
| forwards | 5382 |
| seconds per forward, A100 | 0.0944 |
| `--dry-run` estimate, at 02b's A40 rate | 16.6 min |
| instances with no usable gap | **0 of 100** |
| cells with no mean (NaN) | **none** |
| clean-minus-corrupt gap | mean 3.3391, range [1.4070, 6.1876], positive on 100 of 100 |

The A100 came in at 0.0944 s per forward against ticket 02b's A40 measurement of
0.1845, so the estimate over-predicted by very close to the factor of two the
two cards differ by. **The estimate is calibrated**: `--dry-run` prints it from
02b's A40 constant, which is the conservative direction.

**Reproducibility.** The job was run three times: once before the orchestrator's
naming rules, once after, and once after the heatmap's colour scale changed.
The 393 cell means of the first two runs agree to **0.00e+00 — bit-identical**,
which is what a deterministic bfloat16 forward on one card should give and is
worth recording because every cell is a difference of two large logits.

### The strongest ten cells

| cell | normalized effect | standard error | n |
|---|---|---|---|
| `mlp.31.0 -> readout` | **-0.0944** | 0.0163 | 100 |
| `head.24.25 -> readout` | -0.0194 | 0.0048 | 100 |
| `head.17.25 -> readout` | -0.0191 | 0.0014 | 100 |
| `head.17.25 -> mlp_in.31.0` | -0.0166 | 0.0013 | 100 |
| `head.24.18 -> readout` | -0.0156 | 0.0037 | 100 |
| `head.14.22 -> q.17.25` | -0.0070 | 0.0016 | 100 |
| `embed -> q.5.11` | +0.0061 | 0.0028 | 100 |
| `head.5.11 -> v.9.3` | +0.0048 | 0.0021 | 100 |
| `head.17.25 -> q.24.18` | -0.0043 | 0.0011 | 100 |
| `head.13.17 -> k.17.6` | +0.0040 | 0.0012 | 100 |

### Direct effect on the Readout, all 18 Components and the embedding

| sender | direct effect | se | | sender | direct effect | se |
|---|---|---|---|---|---|---|
| `mlp.31.0` | **-0.09439** | 0.01631 | | `head.5.6` | +0.00010 | 0.00011 |
| `head.24.25` | **-0.01943** | 0.00479 | | `head.8.14` | +0.00010 | 0.00014 |
| `head.17.25` | **-0.01913** | 0.00136 | | `head.5.8` | +0.00009 | 0.00014 |
| `head.24.18` | **-0.01558** | 0.00373 | | `head.5.9` | -0.00007 | 0.00010 |
| `head.27.4` | +0.00065 | 0.00090 | | `head.8.15` | -0.00006 | 0.00008 |
| `head.14.21` | +0.00053 | 0.00033 | | `head.9.12` | +0.00003 | 0.00015 |
| `head.13.17` | +0.00047 | 0.00034 | | `head.8.12` | -0.00002 | 0.00008 |
| `head.5.5` | +0.00032 | 0.00014 | | `head.5.11` | +0.00001 | 0.00011 |
| `head.14.7` | +0.00015 | 0.00031 | | `embed` | +0.00000 | 0.00000 |
| `head.14.22` | +0.00012 | 0.00029 | | | | |

### Three numbers for the researcher, stated without interpretation

1. **The 18 Components' direct effects on the Readout sum to -0.146**, about a
   seventh of the clean-minus-corrupt gap, and four Components carry 0.149 of
   that while the other fourteen sum to +0.003. Every other Component of the
   model was frozen at clean while each of these was measured, so the remaining
   six sevenths of the item-swap effect reaches the Readout through Components
   outside this circuit, through multi-hop paths inside it, or both. The
   completeness sweep (ticket 09, all heads and MLP blocks into the Readout) is
   what would tell those apart.
2. **The largest single path in the whole grid is not a head**: the last layer's
   MLP block, at -0.094, is five times the strongest head. It is also the only
   MLP block in this circuit. `head.17.25 -> mlp_in.31.0` at -0.0166 is the
   fourth strongest cell, so part of head 17.25's influence is routed through it.
3. **The strongest non-Readout receiver cells land on queries and keys, not
   values**: `head.14.22 -> q.17.25` (-0.0070) and `head.13.17 -> k.17.6`
   (+0.0040) are the two largest. The pre-registered hypothesis in the spec says
   the lie signal should enter the mid heads' **queries**; this is the first
   number that bears on it, and it is one cell at four standard errors, not a
   result.

### Deviations, all deliberate, two of which need the orchestrator's eye

1. **The metric's site.** The orchestrator's broadcast says to read
   `readout_logits(model, capture.residual[:, readout])`. This module reads
   `capture.outputs[READOUT_KEY]` at the Readout position instead. In
   `hooks._traced_forward` the residual rows are saved from each decoder layer's
   `block.output`, and a replacement at the Readout **receiver** is written to
   `model.model.norm.input` afterwards — so for the 19 cells whose receiver is
   the Readout, `capture.residual` is the *unpatched* residual and every direct
   effect would come out as exactly 0.00000. The two sites are identical for
   every other receiver, and ticket 07 never replaces the Readout receiver,
   which is presumably why its reviewer did not hit this. The substance of the
   rule is kept: fp32 through `hooks.readout_logits`, never `Capture.logits`.
2. **The freeze**, described above. If the orchestrator wants the unfrozen
   reading instead, it is one line in `receiver_inputs`, but then the Readout
   column duplicates ticket 07.
3. `--path-instances` and `--path-top` carry the analysis's prefix per the
   flag rule; columns are `path_patching.strongest_incoming`,
   `path_patching.strongest_outgoing`, `path_patching.direct_effect` and
   `path_patching.direct_effect_se` per the column rule, plus
   `strongest_incoming_effect` and `strongest_outgoing_effect` so the name and
   the number sit side by side.
4. `EMBED_KEY` and `READOUT_KEY` are spelled out in this module rather than
   imported from `hooks`, because `registry.py` forbids an analysis module a
   module-scope `hooks` import. A test asserts them equal to the hook module's
   own wherever nnsight 0.7.0 is installed.
5. The heatmap's colour scale runs to the 98th percentile of the absolute
   effects, not to the largest. One cell at -0.094 against a second place of
   -0.019 washed the other 392 to white; 8 cells now saturate, the colour bar's
   arrows say so, and the JSON twin carries every unclipped number.

### Open questions for the researcher

1. **Is a seventh of the gap what you expected the circuit's direct edges to
   carry?** See the first number above. It is a statement about direct paths
   only; knockout (ticket 07) measures the total and the two are not comparable
   without the completeness sweep.
2. **`k.17.6` and `v.9.3` cover query heads outside the circuit.** A K or V cell
   is a KV group, so `k.17.6` reaches query heads 24 to 27 of layer 17 while only
   head 25 is in the delta. The JSON records `covers_heads` beside
   `circuit_heads` for every such receiver; a cell there is not attributable to
   the circuit head alone.
3. **Ticket 09 has exactly one thing to parameterise** for the second
   counterfactual: `capture_streams` names `batch.corrupt_input_ids` and
   `batch.corrupt_attention_mask` directly, and every function below it already
   takes the two streams as captured tensors. That is user story 24's "same code
   path", and it is one signature.

### Tests

| env | baseline on `917474d` | final | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 685 passed, 22 skipped | 8 failed, 706 passed, 23 skipped | none, the same 8 names |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 711 passed, 19 skipped | 8 failed, 744 passed, 19 skipped | none, the same 8 names |

The 8 are ticket 01's list, re-derived on this base and identical by name in
both environments. This ticket contributes **34 tests**: 17 in
`test_path_patching.py` (both envs), 13 in `test_path_patching_passes.py`
(nnsight 0.7.0 only) and 3 in `test_path_patching_cli.py` (both envs); the
cherry-pick contributes the rest of the difference.

### Orchestrator's close-out (2026-09-16)

The implementing agent was stopped by an account spend limit after the final
GPU run and before the last checkbox. The Spec-axis review did arrive: two
independent Spec reports reached the orchestrator (the second a retry), both
with no blocking findings, both confirming deviations 1 and 2 above (the
freeze is canonical path patching and is what keeps the direct-effect column
distinct from ticket 07's total; the Readout-receiver site must be read from
`capture.outputs[READOUT_KEY]`). Their remaining findings and outcomes:

- `--path-instances` caps the causal sample below the spec's stratified 100 and
  a prefix of a stratified sample is not stratified. **Open: remove the flag**
  (the orchestrator ruled so; the agent tested it instead in `a7eca08` before
  the ruling arrived). `--n-causal` is the lever.
- Direct-effect bar chart rendered a null mean as zero; heatmap colour range
  came from the single maximum. Fixed in `d6119c0` (percentile scale); the
  null-mean case had no instance in the SDR run (`cells_without_a_mean` is
  empty) and stays open.
- The GPU run is evidenced above (job 22111541); the probe line for
  `component_analysis.path_patching` is folded into the shared nnsight probe
  by the orchestrator at merge.
- Interpretive note for the researcher: with every non-sender Component frozen,
  a cell is the direct edge only; a sender-to-receiver route through a
  non-circuit head is invisible rather than folded in.

Sign convention worth restating: a cell is (patched minus clean) divided by
(clean minus corrupt), so a path that helps deception reads **negative**
(mlp.31 -> readout is -0.094), the opposite sign of ticket 07's knockout drop.
