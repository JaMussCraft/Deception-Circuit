# Code review — ticket 03, attention patterns by Segment

Fixed point: `917474d` (tip of `component-analysis` when the block C parallel
wave was cut). Branch: `ca/03-attention-patterns`.

Under review: `component_analysis/attention_patterns.py` (new),
`tests/test_attention_patterns.py` (new) and the one line of
`component_analysis/registry.py` that registers the analysis. The
cherry-picked `004d916` ("Let the readout take a shared scale, expose o_proj,
and pin the empty registry") comes from the orchestrator and is **not** part of
this review.

`mattpocock-skills:code-review` was run with both axes as parallel sub-agents.
Both ran to completion — 22 and 24 tool calls each — and both failed to hand
their reports back, which is the failure mode the brief and tickets 01, 02 and
02b all describe. They were asked by `SendMessage` to deliver; the outcome of
that request is recorded in "Independent axes" below. The author's own pass on
both axes is recorded first, as the brief's fallback allows, and it was done
before the sub-agents were asked again.

## Standards (author's pass)

Sources: `CONTEXT.md` "Prompt anatomy (component analysis)",
`docs/adr/0001-component-analysis-on-raw-hf-model.md`, and the neighbouring
modules `hooks.py`, `dataloaders.py`, `registry.py`, `segmentation.py`.

**Hard, fixed.**

1. **`control` is a reserved word.** `tests/test_attention_patterns.py` called
   the unforced head in the forced-attention test `control`. `CONTEXT.md`'s
   Honest Condition entry says to avoid "control" because the random-circuit
   null is also one, and ticket 02b's review had already taken the same finding
   in `tests/stub_analysis.py`. Renamed to `unforced`, with the reason at the
   docstring so the next reader does not rename it back.

2. **`# noqa` on the wrong line.** The mid-file fixture import carried
   `# noqa: E402` on the statement and `# noqa: F401` on its continuation, so
   flake8 saw only the first. Both codes now sit on the statement, which is
   what `tests/test_analyze_components_registry.py` does.

**Judgement calls, fixed.**

3. **`Slice` was a hand-written class** where `dataloaders.Batch` and
   `HonestPair` — the carriers it sits beside and is built from — are
   dataclasses. Now a dataclass, so the three aligned-row carriers in this
   package look alike.

**A real bug, found after the axes and fixed.** In `Profiles.add`, a query
Segment absent from *every* instance of a batch added the whole batch size to
every level's absent count, so under `--split designation` both `identity` and
`inversion` would each have been told they lost all of it. Correct is each
level counting its own rows. Unreachable from either GPU run, since `readout`
is present on every instance, but reachable on the saved FAR run, whose
`designation_suffix` is absent everywhere. Fixed with a test that pins the
per-level counts.

**Judgement calls, considered and kept, with the reason.**

4. **Data clump: `head_keys, names, query_names, split, heads_by_layer`**
   travel together from `_plan` through `collect_condition` as `**shared`.
   That is a type wanting to be born. Kept because the same five values are
   also what `estimate` needs individually for its cost line, and because
   ticket 02b's review considered and kept the identical clump through the
   `dataloaders` signatures. If a second analysis ever wants them, the type
   should be born then, in one place, rather than twice.

5. **`run` is long and its three condition blocks rhyme.** They are not
   duplicates: each differs in loader, in slicer, in what it reports and in
   whether it can be skipped and why. Extracting a fourth abstraction over
   three callers with three different failure modes would hide the one thing
   the reader of this function needs to see, which is that the honest twin is
   unpaired and the honest instruction is not. `collect_condition` and
   `_condition_json` already hold everything the three genuinely share.

6. **`Profiles` keeps its sums in dicts keyed by `(level, query)`** rather than
   in one tensor indexed by level. The levels are not known until the last
   instance is read (a factor level can be absent from the first hundred
   batches), so the dict is the honest structure.

**Hard rules checked and holding.** No module of `component_analysis/` other
than `hooks.py` imports nnsight: `attention_patterns` imports `hooks` inside
`batch_masses`, `collect_condition` and nowhere at module scope, and
`test_this_analysis_module_does_not_import_nnsight` proves it in a fresh
interpreter. nnsight's private `_model` handle does not appear; the module
reaches the model only through `hooks.attention_weights` and
`hooks.device_and_dtype`. ADR-0001's "eager attention is switched on only for
pattern extraction" is satisfied by construction, since the switch lives inside
`hooks.attention_weights` and this module never touches
`config._attn_implementation`; `test_sdpa_is_left_in_place_after_the_masses_are_read`
asserts the model handed to the next analysis is still on SDPA.

## Spec (author's pass)

Sources: `issues/03-attention-patterns.md` (the checkboxes), `spec.md`
(Implementation Decisions "Attention patterns" and "Outputs"; user stories 7,
8, 10, 27, 31, 38, 39, 43), and ticket 02b's seam notes.

Every checkbox is implemented; the evidence per box is in the ticket's
`## Comments`. Three findings worth recording rather than fixing:

1. **"when a reference task is bound" is implemented as "when the honest-twin
   dataset exists".** The ticket says the honest-twin column appears "when a
   reference task is bound", but `--reference` binds a reference *circuit* (a
   run directory), not a dataset, and ticket 02b's seam note is explicit that
   "the honest twin is a second dataset directory, not a flag". So the
   condition runs when `<task dataset>_honest` is on disk, and
   `--attention-honest-twin auto|off|DIR` makes that explicit and overridable.
   A skipped condition names its reason in `patterns.json`. The researcher
   should confirm this reading; it is the only one that matches the data
   layout.

2. **The paired honest-instruction condition is computed here, but its
   head-table column is not.** `spec.md`'s Attention-patterns bullet asks for
   "three condition columns: pressure, honest-instruction (paired), honest twin
   (unpaired, marked descriptive)", while ticket 06 owns "top Segment under
   honest instruction" as a head-table column. Both are honoured: the numbers
   are in `patterns.json` under the `honest_instruction` condition, marked
   `paired: true`, and the head table gains only the pressure and honest-twin
   columns. Ticket 06 adds a column over numbers that already exist.

3. **Scope beyond the checkboxes, all deliberate.** `--attention-top-k`,
   `--attention-rank-column` and `--attention-honest-twin` are flags the
   checkboxes imply but do not name; `attention/honest_twin_segmentation.json`
   is not in the ticket but follows from user story 10 ("the segmentation
   actually used written to the output"), since the twin is a different dataset
   with different prompts and the cell's own `segmentation.json` describes only
   the pressure split.

## Independent axes

**Neither axis delivered, so this review is not independent of the author.**
The orchestrator may want a fresh reviewer on this diff, as it did for tickets
01 and 02.

The sequence, for the record. A first Standards sub-agent was spawned and died
mid-run against a monthly spend limit (28 tool calls in, no report). After the
limit reset, both axes were spawned again in parallel and both ran to
completion — 22 and 24 tool calls, about 110k tokens each — and both ended
without delivering through the handback, which is the failure the brief
describes. Both were then asked by `SendMessage` to reply with their reports.
Neither had replied by the time the ticket was finished, well past the ten
minutes the brief allows for waiting. If either arrives later its findings
should be checked one by one against the code, as ticket 02's late reports
were; nothing in the author's pass above depends on them.

What the author's pass cannot substitute for is an outside reading of the two
judgement calls kept above (the five-value clump through `collect_condition`,
and `run`'s three rhyming condition blocks). Those are exactly the kind of
finding an author is worst placed to make about their own diff.

## Verification that stands behind this review

Not part of either axis, but the evidence a reviewer would ask for:

- Both suites, both environments, against the branch base: 8 failed in each,
  the same 8 names as on `917474d`, no new failures. Base env 700 passed / 39
  skipped, `mgnp` 744 passed / 19 skipped.
- Two A40 jobs on the real SDR nls0.3 head-granularity delta, 22107232 and
  22110821. Every written profile sums to one within 3.5e-4, no NaN, and no
  attention mass at all outside the segmentation.
- Provenance, precisely. Job **22110821** ran commit `421896e`'s production
  code exactly. Job **22107232** predates two lines of it: the `n_loaded` key
  and the paired condition's `n_instances` reading 71 rather than the loader's
  100, both edited while that job was already running — which is why reading
  its output back raised `KeyError: 'n_loaded'` the first time. Neither line
  touches a mass, and the two runs' masses agree to the digits printed in the
  ticket. The only production change *after* both jobs is `7ed7123`'s
  conversion of `Slice` to a dataclass with the same four fields and the same
  `__len__`, plus `b27256a`'s per-level absent counter, which changes a count
  reported for a query Segment absent from a whole batch and is not reachable
  from either job's configuration (`readout` is present on every instance).
