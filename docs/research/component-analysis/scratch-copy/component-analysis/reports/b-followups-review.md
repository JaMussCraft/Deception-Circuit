# Code review — block B follow-ups (`ca/b-followups`)

Fixed point: `b6943b6` (tip of `component-analysis`). Diff: `git diff
b6943b6...HEAD`. Six commits, 9 files, +320 / −103 before the review fixes.

```
fc5b9f2  Take the review's findings on the balanced allocation and the mention split
0eaec19  Record the shared ".T"/"HE" token where the tie-break happens
3dc17e3  Let the glossary say "template piece", and count four Item Mentions
95234b1  Spread the causal sample evenly over the strata instead of proportionally
a09c3c5  Split the two question mentions of each item into their own Segments
ad6fed9  Read the Honest-Instruction Counterfactual off the clean stream by default
```

## How the review was run

`mattpocock-skills:code-review` against `b6943b6`. Its two sub-agents were
spawned in parallel with the skill's own Standards and Spec briefs, including
the full Fowler smell baseline. **Both ended without delivering a report
through the handback channel** — the same failure ticket 02 and ticket 05 both
hit on this feature — and both were then asked to deliver by `SendMessage`.

Under the agent brief's fallback the author did both axes in one pass in the
meantime. **That part of the review is therefore not independent of the
author**, and the orchestrator may want a fresh reviewer on this diff, exactly
as ticket 02 recommended for its own. Anything the sub-agents delivered late is
recorded under "Late independent review" at the end; if that section says they
did not deliver, no independent eye has been on this diff.

## Standards

Sources: `CONTEXT.md` (binding glossary), `docs/adr/0001-...`, the agent brief's
"Design rules that apply to every ticket", plus the Fowler smell baseline.

### Hard — fixed in `fc5b9f2`

1. **Unreachable branch documented as a case.** `sampling.allocate`'s
   redistribution loop carried

   ```python
   room = [i for i in live if counts[i] < sizes[i]]
   if not room:                    # every stratum is full
       break
   ```

   which cannot be reached. `n` is capped at `sum(sizes)`, so if every stratum
   were full `counts` would already sum to the total and `remaining` would not
   be positive. Ticket 02's own review caught the identical mistake in the
   proportional version — a documented shortfall path the code never takes —
   and the fix there was to correct the documentation rather than keep the
   claim. Now an `assert` stating the invariant, with the reasoning in a
   comment. `assert` is stripped under `-O` exactly as `dc.assert_aligned_pair`
   is, which is the repo's existing position.

2. **`sample.json` buried the allocation name in prose.** `"allocation"` read
   `"balanced (equal share per stratum, capped by ...)"`, so a reader — or a
   later script — had to parse a sentence to learn which allocation produced
   the file. That is the opposite of the reason the field exists. Split into
   `"allocation": "balanced"` and `"allocation_rule": "<sentence>"`; the test
   now pins the name exactly rather than by prefix.

### Judgement calls — fixed in `fc5b9f2`

3. **Duplicated vocabulary (Duplicated Code).** `QUESTION_MENTIONS` named the
   two question mentions for `validate_segmentation`, but `segment_mechanism`
   spelled `_question_pair` and `_question_option` out again. The segmenter now
   builds both names from the constant by zipping it against `(spans[:1],
   spans[1:])`. `MECHANISM_SEGMENTS` still lists the four names literally,
   which is right: that tuple is the declared order the written file uses and
   reads better spelled out.

4. **`Stratum` did not say why `target` and `achieved` are two numbers.** Under
   the old proportional allocation they always agreed; under balanced they
   diverge whenever a stratum is capped. The class docstring now says so, since
   that is the field pair a reader of `sample.json` will ask about first.

### Judgement calls — considered and kept

- **`allocate` returning a tuple rather than one list.** It is the one place
  where the two numbers are produced, and hiding one of them behind a second
  call would mean recomputing the equal share. The alternative — an `Allocation`
  dataclass — is a type for two parallel lists consumed by one caller, which is
  Speculative Generality at this size.
- **The `"clean"` / `"both"` criterion as a bare string** (Primitive Obsession).
  `HONEST_STREAM_CHOICES` already validates it, it is a CLI choice and a JSON
  field, and an enum would have to be serialised back to these strings at both
  boundaries. `dataset/` uses bare strings for every neighbouring choice.
- **`load_survivors(..., honest_streams=None)` keeping its "as built" meaning**
  alongside the new default. It is the reading the build script's own summary
  reports, so the three-valued parameter is carrying a real third case, not a
  speculative one. Documented in the docstring.
- **`segmentation.py`'s module docstring grew a third section.** It is long, but
  the "Known dataset quirks" note is exactly the thing a next reader needs
  before trusting a Designation Suffix plot, and a separate file would be
  further from the tie-break it explains. Flagged as Divergent Change risk if a
  fourth section arrives.

### Glossary check

Both `CONTEXT.md` edits are additive and local: three sentences on the Scaffold
entry's `_Avoid_` line and a reworded Item Mention entry. No other entry moved.
The code matches them — the new Segment names use "Item Mention" vocabulary, and
nothing in the diff uses a term an `_Avoid_` line forbids. No module in
`component_analysis/` imports nnsight; `tests/test_component_analysis.py`'s
fresh-interpreter probe already covers `segmentation` and `sampling` and still
passes.

## Spec

Source: the agent brief's "Researcher decisions so far", 2026-09-15 "after
block B" entry, plus the two tickets' `## Comments`.

| decision | asked for | built | verified by |
|---|---|---|---|
| clean-stream honest criterion by default | yes | yes | real SDR load, 629 / 364 |
| question mentions split into two Segments | yes | yes | SDR, FAR, SER dry runs |
| glossary mention count is four | yes | yes | `CONTEXT.md` Item Mention |
| ".T"/"HE" accepted, sentence wins | yes | recorded | ticket 02 Q1, module docstring |
| stratification balanced, not proportional | yes | yes | real SDR dry run, seed 0 |
| "template piece" carve-out | yes | yes | `CONTEXT.md` Scaffold |

### Missing or partial

None found. Every checkbox in the five-item list is covered, including the
secondary asks that are easy to drop: the ticket 02 Segment list and
open-question entries, the ticket 05 description of the default, and the
per-stratum counts recorded beside the old proportional ones.

### Not asked for (scope)

1. **Validation refuses a question mention of two spans, not just an empty
   one.** The instruction says "Validation must refuse an empty one". The rule
   implemented is `len(spans) != 1`, the same rule the four Designation
   Positions already carry. The extra half catches a *third* mention being
   pooled into `_option`, which is the precise failure the split exists to
   prevent — refusing only the empty case would have left the split silently
   defeatable. Deliberate, and called out here rather than buried.
2. **`scripts/build_matched_honest.sbatch`'s usage comment changed.** Its
   example read `--honest-streams clean`, which is now the default and so no
   longer an example of anything. Two comment lines; no behaviour.
3. **`filter_matched_honest`'s default changed too**, not only the loader's.
   The instruction named `load_matched_honest` / the loader and added "and
   `build_matched_honest.py` if it has a default too". The build CLI takes its
   default from the module constant, so the filter's default had to move with
   it for the two to agree. A build rerun is not needed and none was done.

### Implemented but possibly wrong

1. **"First occurrence is the pair naming" is an ordering assumption.** It is
   true of every Template Variant of all three mechanism tasks — the question
   names the pair before either quoted option — and it was checked on the saved
   FAR (1000), SDR (1000) and SER (24) prompts by dry run, plus asserted in
   `test_each_question_mention_of_an_item_is_its_own_segment`. A future variant
   that quotes the options first would mislabel the two Segments without
   failing, since both would still be one span each. Worth knowing; not worth
   guarding against a template that does not exist.
2. **No stratum was capped on the real SDR split.** The smallest stratum holds
   15 and the equal share is 12, so the capping-and-redistribution path is
   exercised only by `test_a_tiny_stratum_is_capped_and_its_surplus_goes_to_the_others`
   and not by any real data in the repo. That is a property of the split, not a
   gap in the code, but it means the first real dataset to exercise it will be
   the first real check of it.

## Summary

Standards: 4 findings, all fixed in `fc5b9f2`; worst was the unreachable
redistribution branch. Spec: 0 missing requirements, 3 scope notes and 2
caveats; worst is the ordering assumption behind pair-versus-option, which is
verified on all 2024 saved mechanism prompts but not structurally guaranteed.

## Late independent review

Both sub-agents did deliver, after the author's own pass and after the
orchestrator's window: their handbacks failed because the spawning agent had
exited, so the reports reached the orchestrator and the author by
`SendMessage`. The diff has therefore had an independent two-axis review.
Note: the branch was rewritten while taking the findings, so the commit that
carried the author's own fixes is now `c48b4ae`, not `fc5b9f2`.

Spec axis, five findings:

1. **Wrong — CONTEXT.md Item Mention "which makes five for it".** Off-by-one:
   the enumeration already reached four including the Designation Site.
   Fixed: the entry now says four mentions for the designated item and three
   for the other; the same slip in ticket 02's open question 2 is corrected.
2. **Wrong (docs) — `allocate` claimed the surplus absorbers end "within one
   of each other".** False under index-order redistribution
   (`allocate([100,100,2], 10)` gave counts `[5,3,2]`). Fixed by handing the
   surplus to the smallest stratum with room, ties by index, so the claim is
   now true (`[4,4,2]`), with a test on exactly that fixture.
3. **Scope — `load_survivors` default changed `None` -> `"clean"`.** Kept: the
   loader forwards its default through it, and an older survivors file now
   fails with a message that says to rebuild rather than silently returning
   the wrong criterion. Tested.
4. **Minor — the carve-out is more than one sentence.** Kept.
5. **Partial — `sample.json`'s allocation field was a prose sentence.** Fixed
   in `c48b4ae`: it is the bare name `"balanced"`.

Standards axis, two hard findings and five smells:

1. **Hard — the same Item Mention contradiction.** Fixed as above.
2. **Hard — `load_survivors` docstring asserted a call path that does not
   exist** (the build script never calls it) and read "whichever" for
   "regardless of". Fixed: the docstring now says what the code does.
3. Smells (mention names spelled three ways, `allocate` returning two parallel
   lists, `None` as a sentinel for "as built", `FileNotFoundError` beside
   `KeyError`, the balanced rule restated in four places): recorded, not acted
   on. The parallel lists are deliberate, so that `target` and `achieved` stay
   distinguishable in `sample.json`.

## Test results confirming the reviewed state

Run on `fc5b9f2`, the commit that carries the review fixes. Baselines
re-derived on `b6943b6` rather than taken from ticket 02's note; the failing set
is the same 8 names in all four columns, so the follow-up introduced none.

| env | baseline on `b6943b6` | on `fc5b9f2` |
|---|---|---|
| login-node base (py3.9, transformers 4.57.3) | 8 failed, 652 passed, 21 skipped | 8 failed, 655 passed, 21 skipped |
| `mgnp` (py3.12, transformers 5.13.0) | 8 failed, 658 passed, 19 skipped | 8 failed, 661 passed, 19 skipped |

The SDR dry run was rerun on `fc5b9f2`: 1000 instances, 18 Segments, the same
100 drawn instance ids as before the review fixes, and `sample.json` now reads
`"allocation": "balanced"`.
