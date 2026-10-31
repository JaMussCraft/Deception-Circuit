# Code review — 07 per-Component knockout ranking

Fixed point: `917474d` (the block C scaffold tip). Branch
`ca/07-per-component-knockout` in
`Deception-Circuit/.claude/worktrees/ca-07`, reviewed at `053f8bb`.

`mattpocock-skills:code-review` was run with both axes as parallel sub-agents,
against the two source sets (Standards: `CONTEXT.md`, `docs/adr/0001`,
`docs/research/interp-tooling.md`, the neighbouring modules, plus the Fowler
smell baseline; Spec: the ticket, `spec.md`, and ticket 02b's seam notes).

**Both handbacks failed and both reports arrived later by `SendMessage`,** as
ticket 02b's comments predict. The author had begun a fallback pass in the
meantime and had already fixed the "baseline" finding and two of the smells
before the reports landed; where that happened it is said so below.
**The findings themselves are the sub-agents', so this review is independent of
the author.** Agent ids: `a7768dd0bf20a6cb2` (Standards), `a1252d62af3eb8251`
(Spec).

## Standards — 1 hard violation, 7 judgement calls

**1. Hard: `baseline` is a term the glossary reserves. Fixed (`b6c8ead`).**
`CONTEXT.md`, *Honest Condition*: "_Avoid_: control, baseline (ambiguous — the
random-circuit null is also a baseline)". The first commit had
`def baseline(effects)`, a published `"baseline"` block in `knockout.json`,
"+2 baseline passes per batch" in the `--dry-run` estimate, and a test name.
The reviewer pre-empted the counter-argument: `evaluation/context.py` and
`interp-tooling` use the word, but they predate the glossary, and this would
have been the first use in `component_analysis/` — in a JSON key agents read.
Renamed to `clean_run` throughout. (Found independently by the author first;
the reviewer's version is the fuller one and is what the fix is written
against.)

**2. Speculative Generality — the scheme flag. Kept, and the reviewer said
why to.** `FUTURE_SCHEMES`, `UnsupportedScheme`, `resolve_scheme` and five
tests exist for schemes that do not. The reviewer could not read `.scratch/`
from the worktree and wrote "suppress if your ticket specifies the flag". It
does: checkbox 3 is "`--knockout-scheme` accepts `interchange` and rejects
others with a message naming them as future work". Suppressed.

**3. Speculative Generality — dead parameters. Fixed (`f69aeb5`).**
`knockout_effects` took `device=None` and `log=None`; no caller passed either.
Both removed. The device is now always `hooks.device_and_dtype`, which is also
the correct answer: `ctx.device` is what `--device` *asked* for, and the CLI
seam test runs the tiny model on a CPU under the default `--device cuda`.

**4. Duplicated Code — `knockout._key`. Fixed (`f69aeb5`).** It re-implemented
`head_table.row_key`, and `head_table` is in the no-nnsight probe, so the
login-node rule did not force a copy. Two coercions can disagree about what
names a Component, and the head table is where they would disagree. Deleted;
`row_key` is used at all three sites.

**5. Duplicated Code in tests — the leak test. Fixed (`f69aeb5`); the Spec
axis raised it too.** `test_a_knockout_does_not_leak_into_the_other_components`
never called `knockout`: its three calls were `hooks.capture_forward`, and it
re-tested an invariant `tests/test_component_hooks.py` already holds, asserting
on captured tensors against the Testing Decisions' "never the intermediate
tensors or hook wiring". Deleted.

**6. Doc drift in `hooks.py`. Not fixed here — reported to the orchestrator.**
`replace_forward`'s docstring says "This is *the* interchange primitive …
Knockout replaces one Component … neither re-implements it", but a knockout
uses `capture_forward(..., replacements=...)`, because `replace_forward`
returns only bf16 logits and ADR-0001 requires the fp32 residual. The Spec axis
reached the same conclusion from the other side and noted ticket 08's metric
will hit the same wall. `hooks.py` is another ticket's file on this branch, so
this goes to the orchestrator as a correction to 02b's seam note rather than an
edit.

**7. Naming. Fixed (`f69aeb5`), and overtaken by the orchestrator.**
`knockout.knockout_logit_diff_drop` double-prefixed, and the module mixed
`clean_logit_diff` / `knockout_logit_difference` / `mean_logit_difference`. The
orchestrator then ruled on the columns: `knockout.logit_diff_drop`,
`knockout.rank`, `knockout.standard_error`, `knockout.accuracy`, which ticket 03
will look up. The module now spells "logit difference" one way, and `COLUMNS`
names the four strings in one place.

**8. `interp-tooling` §6 asks for `knockout.csv` and a layer-by-head heatmap;
only the bar chart ships. Kept.** The reviewer graded it "mostly satisfied, not
hard" for the right reason: `head_table.csv` carries the columns and
`registry.py` supersedes that document's outputs layout. The ticket asks for a
ranked bar chart, and a layer-by-head heatmap of a circuit that has one
Component in most layers would be mostly empty cells.

**Clean, per the reviewer:** no module-scope nnsight, no `model._model`, the
fp32 readout per ADR-0001, the registry placeholder replaced exactly as its
docstring prescribes. The `Agg` preamble duplication is suppressed as
convention (five existing copies).

## Spec — verdict "ship", all 8 checkboxes met in substance

The reviewer ran both suites under `mgnp` itself (27 tests at that commit) and
cross-checked the artefacts of the first GPU run: 18 ranked rows with mean
drop, standard error and accuracy each; 100 instance ids; head table populated
with ranks 1 to 18 and no gaps; JSON and CSV agreeing exactly; the PNG a ranked
horizontal bar chart with a light-to-dark layer colorbar and standard-error
bars.

**(a) Missing or partial**

1. *Process:* the ticket was still `claimed`, every box unticked, and had no
   `## Comments` recording the GPU verification. Done now: comments, the ranked
   table of all 18 Components, and the boxes.
2. *Not a ticket 07 gap:* user story 29's in-circuit mode (complement
   interchange-ablated) exists nowhere in the package. Cross-cutting and
   unbuilt; passed to the orchestrator.

**(b) Scope creep**

1. The leak test — deleted, see Standards 5.
2. Two head-table columns beyond the two the ticket names. Kept; the
   orchestrator has since named all four, so they are now specified rather than
   extra.
3. `knockout.json` carried the loader's `n_with_honest` / `without_honest`,
   which a knockout never uses. **Fixed (`f69aeb5`):** the `sample` block is
   trimmed to the item-swap fields, because "71 of 100 paired" printed beside a
   knockout number invites the reader to think it used them.

**(c) Implemented but wrong:** none. Two notes from the reviewer, both kept as
findings for the researcher rather than defects: the accuracy rule `logit
difference > 0` matches `evaluation/metrics.py`, so user story 16's
comparability with the circuit-level knockouts holds; and on this sample that
column has no variance to speak of (clean 1.00, every knockout 0.98 to 1.00),
which is data, not a defect.

## Summary

Standards: 8 findings — 1 hard (fixed), 5 judgement calls taken, 2 suppressed
with reasons. Spec: 0 missing requirements, 0 wrong implementations, 3 pieces
of scope creep of which 1 was deleted, 1 trimmed and 1 overtaken by the
orchestrator's decision. The one finding not actioned on this branch is the
`hooks.py` docstring, which belongs to another ticket's file and has gone to
the orchestrator with ticket 08's name on it.
