# Ticket 03 review: round-3 code changes (self-review, two axes)

Reviewer: the ticket-03 implementer (impl-03), 2026-10-19. This is a self-review; no separate review subagent
was run. Scope: the uncommitted diff of `dataset/deception_v2.py` and `dataset/pilot_v2.py`, plus the new
tests. Rounds 0 and 2 were committed by the orchestrator as fc9b0c4 and bd1f9aa.

## What changed

- **`make_spec(task, suffix, ser_wording, overrides=None)`.** The override keys are `desig_inversion` +
  `desig_identity`, `question` + `stem`, and `frame`.
  - It returns a `SpecV2` built from a `dataclasses.replace` copy of the registry pieces, so `SPECS_V2` is never
    mutated.
  - A SER question/stem override needs a new wording label (not A or B).
  - A predicate override must not leave the registry's old predicate words in the question or stem.
- **`SpecV2` gains `frame` and `overrides`.** `build_prompt` joins the frame first in the system turn. `realize`
  records `frame` and `overrides`.
- **SER literal-truth check.** It now anchors on `SER_PREDICATE_PAIRS` (favorable word, unfavorable word)
  instead of hard-coding favorable/unfavorable. A spec with swapped roles is still rejected; that is tested.
- **`ser_wording_flags`** accepts override question/stem text.
- **`FAMILIES`** gains `altruistic` and `fiction` (and `persona`, from round 2).
- **`pilot_v2.parse_cells`** accepts an `overrides` object and allows a non-A/B SER label only with a
  question/stem override. `prepare_cell` passes overrides only when present, so the fakes' 3-argument
  `make_spec` keeps working. Reports carry `overrides`.

## Axis 1: Standards (brief and repo rules)

- **Additive only, no v1 change.** No edit to `dc.SPECS`, v1 builders, v1 data, `DECEPTION_TASKS` or task ids.
  `SPECS_V2` is not mutated, which `test_predicate_override_renders_everywhere_and_leaves_the_registry` checks.
  Pass.
- **No git writes and no worktree changes.** Only read-only `git status`/`diff`/`log` were used. Pass.
- **Tests.** 10 new tests, 9 in `test_deception_v2.py` and 1 in `test_pilot_v2.py`. The full suite fails only
  the 8 baseline names in both envs: base 1583 passed, mgnp 1736 passed. Pass.
- **Style.** `import dataclasses` was out of order; fixed, and the two v2 files re-run with 85 passed in both
  envs. Line length is within 120. Pass.

## Axis 2: Spec (§13.4, rulings of 2026-10-19)

- **"Per-cell predicate override, do not edit the old registries."** Satisfied: the overrides live in
  `cells.json` and the registry is untouched.
- **SER literal truth stays automated for the new pair.** Satisfied by the registered-pairs anchor. The C
  wording's stem lexicon check is clean, and the row-level assertion ran on every realized round-3 record in the
  dry path and in the jobs.
- **The fiction frame is cross-task-identical and kept in every condition.** Satisfied, and tested. The frame
  string is identical in all 6 fiction cells.

## Findings

1. **Should-know, not fixed.** The mechanical clause screen's `PREDICATE_WORDS` covers only the registry
   predicates. Nothing automatic stops a clause used under an override predicate from containing that
   predicate word (questionable, reliable, concerning, reassuring).
   - For round 3 this was checked by grep over every pool used under an override, and over the neutral pool: no
     clause or neutral sentence contains those words.
   - If ticket 04 builds under an override predicate, it should add the override words to the screen for that
     build.
2. **Should-know.** `dataset/check_v2_scaffold.py` does not apply overrides or frames.
   - The round-3 pilot gates for fiction cells were covered two ways. The harness dry path ran on the real
     cells, checking alignment, the 120-token limit and literal truth; its longest prompt was 120 tokens.
   - The frame adds the same 12 tokens to every task, so the medians, median gap and band are unchanged.
3. **Nit, left.** `getattr(spec, "frame", "")` in `build_prompt`/`realize` tolerates a plain `dc.TaskSpec`. That
   is defensive but harmless.

No blocking findings.
