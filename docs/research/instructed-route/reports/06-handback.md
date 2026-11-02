# Hand-back 06: B1 ticket 3, segment-union positions in knockout

Agent: ticket implementer, Claude Opus 5.5. Ticket:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B1-plan.md`,
section 5 ticket 3 (with sections 2.1, 3 and 7). Status: resolved.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/knockout.py`, adds the `--knockout-positions` union form `segments=a+b+c` to `parse_positions`, `positions_slug`, `position_mask`, `ablation_sentence` and the flag's metavar and help.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_knockout_positions_union.py`, new, 32 tests.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/06-handback.md`, this file.

Behaviour of the new form:

- Syntax is `segments=<Segment>+<Segment>[+...]`, with names matching the existing Segment-name pattern. One name is
  accepted. A repeated name, an empty part (`segments=`, `a++b`, a leading or trailing `+`) or any other separator is
  refused at parse time with an `ArgumentTypeError`. The parsed value is
  `{"form": "segments", "segments": [names in the order given], "text": text}`.
- The mask is the logical OR of the single-Segment masks. Each named Segment must exist in the row's segmentation,
  which holds every Segment its scheme declares, so an undefined name is refused with
  "instance X has no Segment 'name'". A declared Segment with no tokens on a row is refused by name, as the single
  form already does.
- The column suffix part is `at_` plus the names sorted and joined by `+`. For the plan's option union under the
  neutral twin the full suffix is
  `_neutral_twin_paired_at_item_1_question_option+item_1_question_pair+item_2_question_option+item_2_question_pair`.
  Sorting makes the same set in any order write the same columns. `+` is not a Segment-name character, so no union
  collides with a single Segment's `at_<name>`. A union of one Segment writes that Segment's own columns, which it
  equals. This is documented in the `positions_slug` docstring and the flag's help.
- Every existing form parses to the same dict and writes the same suffix as before.
- `ablation_sentence` is outside the functions the ticket listed. It indexes a dict by form and would have raised a
  KeyError on any real run of the new form, so it gained one entry that names the union's Segments.

## How verified

Baseline before the change, both interpreters:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_knockout*.py tests/test_component_analysis_v2_knockout*.py
```

Observed: 142 passed, 0 failed.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_knockout*.py tests/test_component_analysis_v2_knockout*.py
```

Observed: 92 passed, 3 skipped, 0 failed.

Red step, new file before the code change:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_knockout_positions_union.py
```

Observed: 17 failed, 15 passed. The 15 that passed cover parse-time refusals and the unchanged existing forms.

After the change, the new file alone on mgnp: 32 passed, 0 failed. The full set, whose glob includes the new file:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_knockout*.py tests/test_component_analysis_v2_knockout*.py
```

Observed: 174 passed, 0 failed.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_knockout*.py tests/test_component_analysis_v2_knockout*.py
```

Observed: 124 passed, 3 skipped, 0 failed. The 3 skips are the tiny-Llama model tests, which need nnsight and skip on
base as before. No existing test changed outcome on either interpreter.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No dry run of `analyze_components.py batch` with the new form against a real `far_v2` or `ser_v2` cell. The check
  that the four option Segments are present on all 100 held-out ids belongs to ticket 7's dry runs, through
  `check_plan`.
- The brief pointed at `tests/test_knockout.py` and `tests/test_knockout_sweep.py` for fixtures. The positions
  fixtures actually live in `tests/test_component_analysis_v2_knockout.py`. The new file rebuilds them locally with
  the real `mechanism_v2` option names instead of importing across test modules.

## Open questions

- Should a union refuse a row on which one member Segment is declared but empty? Default: yes, refuse by name,
  matching the single form. Plan section 2.1 says each option Segment is one token on the held-out ids, so the strict
  rule costs the fallback nothing.
- Is a `+` in a head-table column name acceptable to downstream readers such as pandas attribute access? Default:
  yes. Nothing in the repository validates column names, and the alternative, an underscore join, could collide with
  a single Segment's name.
