# Code review — 08, path patching, position-agnostic

`mattpocock-skills:code-review` against the branch base `917474d`, both axes as
independent sub-agents, one per axis, neither of which wrote any code on this
branch. Both sub-agents' handbacks failed, as ticket 02b warned they would; the
Standards report arrived by `SendMessage` and is reproduced verbatim below. The
Spec axis is recorded in its own section with its delivery status.

Branch: `ca/08-path-patching-position-agnostic`. Commits reviewed:

    9162a9c  Recover composition structure with position-agnostic path patching
    c24871c  Leave the two shared test files to the orchestrator
    0456429  Let the readout take a shared scale, expose o_proj, and pin the empty registry  (cherry-pick, not this ticket's work)
    d3ea060  Take the orchestrator's block-C rules and the standards review

The Standards axis reviewed the tree at `9162a9c`; `d3ea060` is the commit that
takes its findings.

## Standards

> Standards-axis review of ca/08: one documented-standard conflict (module-scope
> `hooks` import) plus five judgement-call smells; all five enumerated hard rules
> pass.
>
> ### Documented-standard conflict (one)
>
> **`component_analysis/path_patching.py:60`** — module-scope
> `from component_analysis import hooks`. `registry.py:24-26` states: *"Nothing
> here imports `hooks.py` or nnsight at module level, and an analysis module must
> not either"*; `dataloaders.py:41` repeats it, and this is the only module-scope
> hooks import in the package. But hooks.py's own docstring says it defers nnsight
> *"so the rest of the package imports in the login-node base environment"* — i.e.
> it is designed to be importable, and its only module-scope imports are
> `dataclasses` and `typing` (verified). So the sentence in registry.py is breached
> as written, with no real login-node cost. Either move the import inside the
> functions (matching every sibling module) or amend registry.py:24-26. What forces
> it today is the `EMBED_KEY`/`READOUT_KEY` re-export at lines 74-75.
>
> The five enumerated hard rules all pass: no nnsight and no `model._model`
> outside hooks.py; torch, matplotlib and numpy are imported inside functions so
> nothing touches a GPU at import; `run()` returns column updates and never writes
> the head table; the fp32 readout goes through `hooks.readout_logits` and K/V
> receivers are per KV group (ADR-0001); no CONTEXT.md `_Avoid_` term appears in
> the diff; the registry edit is exactly the reserved ticket-08 placeholder line.
>
> ### Judgement calls (smells)
>
> - **Speculative Generality / dead code** — `Grid.receiver_of` (l.167) and
>   `Streams.rows` (l.307) are never called, in the module or in any of the three
>   new test modules. `patched_readout` (l.425) admits it: *"A run does not call
>   this"* — production function, tests-only caller.
> - **Duplicated Code** — `_key` (l.357-360) is character-for-character
>   `hooks._key` (hooks.py:286). `covers = tuple(range(one.kv_group *
>   heads_per_group, ...))` (l.231) restates `hooks.heads_of_kv_group`, and
>   `heads_per_group(ctx)` recomputes what `hooks.geometry` already publishes under
>   that exact name. The model-free grid justifies a second path, but three
>   spellings of one GQA number is where an off-by-one hides.
> - **Primitive Obsession** — `Cell` is frozen and hashable, yet every lookup
>   round-trips a formatted string: `by_cell[cell.name]`,
>   `by_cell.get(f"{label(component.key)}->{readout}")` (l.688-697). A `Cell`-keyed
>   dict would also delete `_GridComponent`, the private mirror of
>   `components.Component` that exists only to un-parse `grid.senders`.
> - **Data Clumps** — `_payload(ctx, grid, cells, *, budget, gaps, used_ids,
>   excluded, wall, forwards, batches)`: the five tallies accumulate together in
>   `run` and always travel together.
> - **Shared-file coordination** — the probe line in
>   `tests/test_component_analysis.py` and the rewrite of
>   `test_a_run_with_no_analysis_registered_loads_no_model` are edits tickets
>   03/04/07 must each make identically: rebase conflicts in two files, the cost
>   registry.py's blank-line scheme avoids.

### Disposition

**Taken, all six** (`d3ea060`, and `c24871c` for the last one):

1. *The documented-standard conflict.* `hooks` is now imported inside the six
   functions that use it. `EMBED_KEY` and `READOUT_KEY` are spelled out in this
   module, and `test_the_two_keys_that_are_not_components_agree_with_the_hook_module`
   asserts them equal to the hook module's own where nnsight 0.7.0 is installed,
   so the two spellings cannot drift. A new test in this ticket's own file,
   `test_this_module_imports_without_nnsight_and_without_the_hook_module`, runs a
   fresh interpreter and fails if either import comes back.
2. *Dead code.* `Grid.receiver_of` and `Streams.rows` deleted. `patched_readout`
   is **kept**: it is the composition `run` performs, spelled once so that every
   invariant test asserts the real thing rather than a rehearsal of it. Its
   docstring now says that is why it exists.
3. *Duplicated `_key`.* Replaced by `head_table.row_key`, which is the public
   helper doing exactly that coercion. The GQA arithmetic in `build_grid` stays,
   because that function must run with no model on the login node and
   `hooks.heads_of_kv_group` needs one; `_check_kv_groups` now asserts, on the
   GPU before the grid is used, that every head's `kv_group` is the one
   `hooks.kv_group_of` gives, so the two spellings cannot disagree in a run.
4. *Primitive obsession.* `run` now builds `{Cell: summary}` and both the head
   table and the heatmap index it by `Cell`. `_GridComponent` is deleted.
5. *Data clumps.* The five accumulators are one `_Tally`, and `_payload` takes it.
6. *Shared-file coordination.* Both shared test edits are reverted (`c24871c`).
   The empty-registry fix comes from the orchestrator's `8a8cb9e`, cherry-picked;
   the import probe now lives in `tests/test_path_patching.py`.

## Spec

The Spec sub-agent ran to completion but its handback failed and, unlike the
Standards one, its report did not arrive by `SendMessage` within the window the
brief allows. It was asked again, directly, to deliver what it had written, and
still nothing arrived. So **the Spec axis below is the author's own pass and is
not independent**; that is stated here rather than left to be inferred.

Checked against the ticket's checkboxes, the spec's "Path patching" bullet under
Implementation Decisions, user stories 18 to 24, 28, 31 and 39, and ticket 02b's
seam notes.

### Requirements missing or partial

None of this ticket's. Four things the spec's path-patching bullet names are
**ticket 09's** by the ticket's own title and by the orchestrator's instruction,
and are absent here deliberately: the position-specific pass by Segment, the
`--path-threshold` flag defaulting to 0.05, the completeness sweep of all heads
and MLP blocks into the Readout, and the Honest-Instruction Counterfactual as a
second patching counterfactual.

### Scope creep

- `--path-top` and the `strongest` list in `agnostic.json`. Not in the ticket,
  which asks only for per-cell mean and standard error. Kept, because the ticket
  *does* ask the implementer to record "the strongest ten cells by |normalised
  effect| with standard errors" in its comments, and computing that in the
  analysis rather than in a one-off script is what makes it reproducible.
- `gap`, `cells_without_a_mean`, `n_excluded_by_gap` and the `cost` block in
  `agnostic.json`. Also unasked. Kept: the ticket asks for the wall time and any
  NaN cell in the comments, and a number a human has to retype is a number that
  goes stale.

### Implemented but possibly wrong

- **User story 24** — *"I want path patching to run over both counterfactuals
  through the same code path, so that the pressure-dependent paths among Circuit
  Components are measured without a second implementation."* Nothing here
  forecloses it, but `capture_streams` names `batch.corrupt_input_ids` and
  `batch.corrupt_attention_mask` directly. Ticket 09 has exactly one thing to
  parameterise, and it is that function's choice of second stream; every other
  function below it already takes the two streams as captured tensors.
  Recorded, not built.
- **The metric's site.** The orchestrator's broadcast says to read
  `readout_logits(model, capture.residual[:, readout])`. This module reads
  `capture.outputs[READOUT_KEY]` at the Readout position instead, and the
  deviation is load-bearing rather than stylistic: in `hooks._traced_forward` the
  residual rows are saved from each decoder layer's `block.output`, and the
  Readout receiver's replacement is written to `model.model.norm.input`
  afterwards, so a cell whose receiver *is* the Readout would be read from the
  unpatched residual and every direct effect would come out as exactly zero. The
  two sites are identical for every other receiver. The substance of the rule —
  fp32 through `hooks.readout_logits`, never `Capture.logits` — is kept.
  `test_a_last_layer_mlp_has_nothing_downstream_so_its_direct_effect_is_its_total`
  fails under the instruction as written.

## Orchestrator's addendum

Two independent Spec-axis reports did reach the orchestrator after this report
was written (the agent was stopped by a spend limit before it could take them).
Verdict: no blocking findings; both judgement calls above ruled correct. Their
findings and outcomes are recorded in the ticket's "Orchestrator's close-out"
section; the one open code item is removing `--path-instances`.
