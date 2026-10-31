# Ticket 02 review (Standards and Spec axes)

**The review is two-source.** One source is the independent read-only reviewer's findings, forwarded in full by the orchestrator. The other is the implementer's own pass on both axes.

**How the review was run.** The `code-review` skill reviews a git diff, and the ticket brief forbids git. A read-only reviewer subagent was given the explicit file list and reviewed both axes. Its findings were 9 should-fix and 19 nits, with no blockers. The orchestrator ruled that all nine should-fix items be fixed before hand-back. All nine are fixed, along with most nits. The implementer's own pass found two further issues, both fixed: the `id(tokenizer)` length cache and the empty-reply handling.

## Should-fix items

| # | finding | fix | verified by |
|---|---|---|---|
| 1 | The item-word rule matched exact forms only. "weights", "user", "funding", "trust", "role", "hour" and "light" slipped through, in clauses, in shared_02 and in the neutral pool. | `clause_screen.item_forms` expands every item to plural, singular, -ing and -ed forms. 22 clauses were rewritten. shared_02 is replaced in the new `dataset/deception_pools/v2/pressure_shared.json`, with the reason recorded. 6 neutral sentences were dropped from the pool, leaving 79. Three more task-spec anchors now collide ("weights" twice, "funding"); the test records each with its single expected violation, alongside "client". | `test_item_words_match_inflections`, `test_item_forms_*`, `test_neutral_item_inflections`, anchor test; scaffold report mechanical checks |
| 2 | "flagged" appeared in 70 of 80 SDR flavor clauses, a cue word FAR and SER do not carry. | New pool rule: no referent marker in more than 25% of a task's flavor clauses (`referent_violations`). SDR now uses "flagged" in 3 to 4 of 20 clauses per framing. The rest refer to "that result", "that particular measurement", "the finding in question" and similar. | `test_referent_concentration`, `test_real_pools_spread_their_referents`; scaffold report referent checks |
| 3 | The judge was inconsistent on FAR goal-over-answer clauses. | One written rule is now in the judge prompt (`JUDGE_PROMPT_VERSION = 2`). A goal or want whose object is the assistant's own answer is instructing. A goal about the finding, and a penalty or reward conditional on an answer, are not. The three flagged clauses and three similar ones (FAR slots 01, 04, 09, 12, 14, 17) were judged instructing under the rule and rewritten. All 245 clauses were then re-judged under v2 and accepted, with decisions in `02-clause-screen.json` under `resolutions` and `judge_rule`. One anchor was rephrased because v2 read "reaches the reviewer" as disclosure-level. | `test_judge_prompt_states_the_goal_over_answer_rule`; clause screen summary 245/245 |
| 4 | A re-screen dropped the hand-written `resolutions` and `judge_notes`. | Both are now carried forward with `history`. | `test_rescreen_keeps_hand_written_resolutions` |
| 5 | The duplicate-id check was unreachable. | Duplicate id and text checks now run before the slot-id check. The tests match on "duplicate clause id" and "duplicate clause text". | two framing tests |
| 6 | The determinism test was tautological. | Two tests replace it. One derives the expected sentence independently: sha1(instance_id) mod 3 over the three six-word fixture sentences. The other uses the real tokenizer and pools: two independent generations with the same seed give identical records (prompts, clause and neutral choice), and a different seed gives different instance ids and different neutral choices. | `test_neutral_selection_follows_sha1_of_the_instance_id`, `test_realization_is_reproducible_across_independent_generations` |
| 7 | Several screen rules had no test: conditional words, disclosure phrases, and all-caps in neutral sentences. | One test case each was added. | `test_clause_screen.py` |
| 8 | The single-token gate check was hard-coded to pass. | It is now computed: every pair kept for v2 must encode to one token per item. | scaffold report |
| 9 | The suffix said "to the user", next to the item "users". | `SUFFIX` is now "... matters most here." and the alternative is "... matters most in this case." Both pass the generic clause rules apart from the inversion predicate they carry by design. Length checks were re-run. | `test_suffix_candidates_pass_the_generic_clause_rules`; scaffold report suffix check |

## Nits

Fixed:
- The dead `_hits` branch is removed.
- The duplicated `if not args.no_llm` is merged.
- `llm_label` guards `attempts >= 1`.
- The summary reports `None` mismatch and instructing counts under `--no-llm`.
- The unused `wordings` property is removed.
- `question()` and `stem()` raise on a wording for FAR and SDR.
- The literal-truth check applies to `ser_v2` only.
- The validator rejects a bool `round` and a bare-string clause.
- `None` checks replace `or` defaults in `generate_instances_v2`.
- The `SpecV2` docstring warns against the v1 builders.
- The config entries are `dict(...)` copies of the SDR entry.
- A misnamed test is renamed.

Kept, with reasons:
- `accept` keeps its explicit `label != "instructing"`, which is the spec's wording.
- Absolute Alignment paths stay in the report default and in the anchor test, which skips if the file is missing.
- The empty-input crashes in the report script stay, because it is never run without framings.

## Spec axis

All ticket checkboxes hold on the final code. The re-run scaffold report passes every check:

- D-prompt band at most 11 tokens (limit 12).
- Median gap at most 5 tokens (limit 6).
- Longest prompt 95 tokens (limit 120).
- At least 4 equal-length neutral candidates per clause (2 required).
- Referent marker share at most 20% (limit 25%).

The anchor-collision deviation now covers four anchors. Each fails the binding item-word rule only, and the test pins exactly those violations.

No unresolved findings.
