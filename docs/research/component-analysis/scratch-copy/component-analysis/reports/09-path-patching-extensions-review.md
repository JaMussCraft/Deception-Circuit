# Code review — ticket 09, path-patching extensions

Fixed point: `a74d54b` (the `component-analysis` tip at the start of block D).
Branch: `ca/09-path-patching-extensions`.
Diff: `git diff a74d54b...HEAD` over four files, none of them shared —
`component_analysis/path_patching.py`, `tests/test_path_patching.py`,
`tests/test_path_patching_cli.py`, `tests/test_path_patching_passes.py`.

Two axes were run as separate sub-agents per the `mattpocock-skills:code-review`
skill, plus the implementer's own pass. The sub-agent sections below are their
reports; the implementer's pass is marked as such and is not a substitute for
them.

## Implementer's own pass — Standards

Checked against `CONTEXT.md`, `docs/adr/0001-component-analysis-on-raw-hf-model.md`,
`component_analysis/registry.py`'s protocol, and the block C conventions in the
shared brief.

| | |
|---|---|
| no nnsight or `hooks` import at module scope | holds — every `from component_analysis import hooks` is inside a function; `grep` of the module's module-level imports shows `math`, `os`, `time`, `dataclasses`, `typing` and `head_table.row_key` only |
| flags carry the analysis prefix | holds — `--path-counterfactual`, `--path-position-threshold`, `--path-completeness-sweep` |
| head-table columns are `<namespace>.<bare name>` with no analysis prefix inside | holds — `direct_effect`, `direct_effect_honest_instruction`, `sweep_direct_effect`, `sweep_flagged` |
| ranking metrics read fp32 through `hooks.readout_logits` | holds — every new path goes through `_readout_of`, which reads `capture.outputs[READOUT_KEY]`, never `Capture.residual[:, -1]` and never `replace_forward`'s logits |
| every figure has a JSON twin | holds — `segments_heatmap.png`/`.json`, `sweep_bars.png`/`.json`, and the two ticket 08 figures now per counterfactual |
| `--dry-run` writes no analysis output and touches no GPU | asserted by `test_dry_run_still_writes_nothing_with_every_extension_asked_for` with every new flag on |
| glossary vocabulary | Segment, Component, Readout, Corruption, Pressure Clause, Matched Honest Instruction used throughout; no drift to avoided terms |

Judgement calls the implementer raised against itself:

1. **Mysterious name, fixed.** `_named` was a private helper that the tests had
   to reach through to assert a filename contract. Renamed `output_name` and
   documented, in `dbbbe40`.
2. **Duplicated code, accepted.** Three figure functions share matplotlib
   boilerplate (figure, imshow or bar, ticks, title, savefig, close). They
   differ in axes, colour rule and legend enough that a shared helper would
   take more parameters than it saves; ticket 08 already had two of them.
3. **Data clump, accepted.** `(name, mask, present)` travels together through
   `segment_entries` into `segment_pass`. A `PositionEntry` type would be
   honest but is three fields used in one loop.
4. **Overloaded flag, recorded not fixed.** `--path-position-threshold` serves
   two jobs: it selects the cells for the Segment pass and it decides which
   sweep Components are flagged. A value chosen to quiet one silently changes
   the other, which cost one cancelled Slurm job here. Splitting them is a
   flag-vocabulary decision and belongs to ticket 10; the ticket's Comments
   name it for the researcher.
5. **`_Tally.unpaired` is meaningful for one counterfactual only.** Under the
   item swap every row has a counterpart, so the field is always empty there.
   Accepted: one tally type for both passes is simpler than two.

## Implementer's own pass — Spec

Every checkbox of the ticket is covered; the two deviations that a reader could
trip over are stated in the ticket's `## Comments` rather than only here:
the flags carry the analysis prefix, and "the Segment pass over all Segments
sums to the position-agnostic cell" is asserted as the **union** of every
Segment's positions reproducing the cell, with the arithmetic sum recorded
beside it as information.

No scope creep found beyond three head-table columns the ticket did not name
(`sweep_rank`, `sweep_in_circuit`, `sweep_direct_effect_se`), which are the
numbers behind the flag the ticket did name.

Both sub-agents ran to completion but their `SubagentHandback` failed with
"the agent that spawned you is no longer running"; both reports arrived by
`SendMessage` instead, which is the behaviour the shared brief records for
block C. They are reproduced below as sent.

## Standards axis (sub-agent)

> Standards-axis review of `a74d54b...HEAD`: no documented-standard violations;
> seven judgement-call smells.
>
> **(a) Documented-standard violations: none, hard or judgement.** Verified:
> analysis flag prefixes (`--path-position-threshold`, `--path-counterfactual`,
> `--path-completeness-sweep`; the `--path-instances` removal leaves no
> stragglers); head-table columns `<namespace>.<bare name>` with no analysis
> prefix in the bare name; fp32 readout — `sweep_readout` and
> `positioned_effects` both go through `_readout_of`, which uses
> `capture.outputs[READOUT_KEY]` and `hooks.readout_logits`, with no
> `replace_forward` and no `Capture.residual[:, -1]`; no module-scope nnsight
> or hooks import, and `estimate()` reads only `ctx.intake.geometry`, built
> model-free by `geometry_from_masks`; `--dry-run` pinned by
> `test_dry_run_still_writes_nothing_with_every_extension_asked_for`; PNG plus
> JSON twin for `sweep_bars` and `segments_heatmap`, twin written before the
> early return; no `CONTEXT.md` avoided terms; test assertions on written JSON,
> head-table columns and returned tensors.
>
> **(b) Baseline smells** (judgement calls), all in `path_patching.py`:
> 1. **Duplicated Code** — `agnostic_pass`, `completeness_sweep` and
>    `segment_pass` each repeat the same batch preamble. Extract one streaming
>    generator.
> 2. **Repeated Switches**, contradicting the module docstring's
>    "`counterfactual_pair` is the only function that knows which is which":
>    `_named`, `COLUMN_SUFFIX` and `sweep_counterfactual` all dispatch on it.
> 3. **Speculative Generality** — `Streams.counterfactual` and `Streams.rows`
>    are written and read by no production code; likewise the unused fourth
>    slot in the entries tuple.
> 4. **Duplicated magic number** — `0.05` in `add_arguments` and in both
>    `getattr` fallbacks.
> 5. **Dead constants** — `SEGMENTS_FILE`/`SWEEP_FILE` added but production
>    writes literal stems; the two new figures get no constant at all.
> 6. **Divergent convention vs `dla.py`** — `dla` names the column
>    `honest_instruction`; this suffixes `_honest_instruction`.
>    `DEFAULT_QUERY_POSITION` is pinned cross-module by a test;
>    `HONEST_INSTRUCTION` is not.
> 7. **Estimate undercount** — `estimate()` omits the two re-capture forwards
>    per batch that `segment_pass` and `completeness_sweep` each pay.

### What was done about them

Fixed in `91754f9` on the orchestrator's ruling: 1, 4, 5, 7, and the
cross-module pin half of 6. Also fixed, though not on the list: `union` and
`query_positions` are now refused as Segment names, because they are rows of
the position-specific table that are not Segments and a `--segment` override
could have overwritten one silently.

Not changed, recorded as judgement calls: 2 (the docstring's claim is about
*which pair a stream holds*, which `counterfactual_pair` alone decides; the
three other sites dispatch on presentation — a filename, a column suffix,
which pair the sweep runs on — and folding those into one dispatcher would
hide three unrelated decisions behind one name); 3 (`Streams.counterfactual`
is read by `test_the_honest_counterfactual_reproduces_the_honest_logits_...`,
which is how a caller tells which pair a stream holds, and `rows` is the same
fact for the batch; the entries tuple's fourth slot is gone with the
`stream_batches` extraction); the column-suffix half of 6, which the spec
reviewer accepted.

## Spec axis (sub-agent)

> Spec-axis review of ticket 09 — nothing blocks.
>
> **Verdicts on the six stated deviations.** (1) `--path-*` prefixes: not a
> deviation, the brief mandates them. (2) `_honest_instruction` suffix:
> defensible, matches ticket 04's `dla.honest_instruction` versus
> `honest_twin_descriptive`. (3) Union rather than arithmetic sum: correct —
> `segmentation.py` says "The default Segments of one prompt are pairwise
> disjoint and together cover every token, `unsegmented` holding the chat
> control tokens", so union is the honest reading of the ticket's "sums to the
> position-agnostic cell", and the seam test asserts it on real K and V cells
> through `segment_entries`. (4) Sweep runs once: defensible against the spec's
> "provided a job is short: on the order of an hour"; about 1057 senders over
> 13 batches is roughly 22 minutes at ticket 08's A100 rate. (5) One-forward
> Readout shortcut: **confirmed** — `hooks.py` replaces
> `final = model.model.norm.input` before `saved[READOUT_KEY] = final.save()`,
> and `_readout_of` reads that site. (6) Q, MLP and Readout single entry: not a
> deviation; the ticket specifies Q and MLP, the Readout is unspecified and the
> query positions are the only sensible reading.
>
> **(a) Missing or partial.** The ticket's "per-pair Segment heatmaps" is one
> combined heatmap with a row per pair — equivalent, but undeclared. The
> deviations lived only in docstrings and `--help`; ticket 08's precedent puts
> them in `## Comments`. And at the default 0.05 threshold ticket 08's SDR data
> selects only `mlp.31.0 -> readout`, a Readout receiver, so the verification
> run would exercise zero K and V Segment sweeps; use about 0.004. The
> pre-registered mid-layer Q-versus-V question is answered by the
> honest-instruction **position-agnostic** pass, per the spec's Further Notes,
> not by the Segment pass.
>
> **(b) Scope creep.** None material. The embedding in `sweep_senders` is
> declared in the docstring and never becomes a head-table row.
>
> **(c) Implemented wrongly.** `query_segment_names` bypasses ticket 03's
> validation. A typo yields an all-false mask, `n_absent = n`, null means, no
> error; under `--analyses path_patching` alone nothing validates it.

### What was done about them

The validation defect is fixed in `91754f9`, on the login node during
`--dry-run` as well as in the pass. The combined heatmap, the deviations, the
Q-versus-V route and the differing sample sizes of the two column sets are all
declared in the ticket's `## Comments`. The verification run uses
`--path-position-threshold 0.0035` rather than 0.004, because ticket 08's
`head.13.17 -> k.17.6` is +0.00396 and would fall just outside 0.004; at
0.0035 four K and V cells are swept rather than one.
