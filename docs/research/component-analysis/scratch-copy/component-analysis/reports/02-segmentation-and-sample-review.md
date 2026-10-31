# Code review — 02, segmentation and stratified sample

Fixed point: `7554839` (tip of `component-analysis`).
Branch: `ca/02-segmentation-and-sample`, worktree `Deception-Circuit/.claude/worktrees/ca-02`.
Diff: `git diff 7554839...HEAD` — 8 files, 3 new package modules, 3 new test files.

**How this review was run.** `mattpocock-skills:code-review` spawns one sub-agent
per axis. Both were spawned once and resumed twice each without delivering,
so under the brief's fallback both axes were first done by the author in one
pass — the sections below. **Both sub-agents then delivered late**, after the
first report to the orchestrator had been sent; their findings are evaluated
in "Late independent review" at the end, and the ones that held up were taken
in commit `89d060d`. So the axes below are *not* independent of the author,
but the late section is.

---

## Standards

Sources: `CONTEXT.md` (the glossary is the binding naming standard),
`docs/adr/0001-component-analysis-on-raw-hf-model.md`, `.claude/CLAUDE.md`, and
the style of the package's existing modules. Plus the skill's smell baseline.

### Hard violations

None found.

- **Glossary vocabulary.** Every Segment name is a glossary term in snake case:
  `designation_site`, `predicate_token`, `other_token`,
  `inverse_predicate_token`, `designation_suffix`, `pressure_clause`,
  `readout`, `stem`, `intro`, `item_N_intro`, `item_N_question`,
  `designating_sentence`, `stipulation_token`. The diff was grepped for every
  word on every `_Avoid_` line in `CONTEXT.md`. One hit, cleared: "chat
  **control** tokens" in a docstring, which is the ordinary NLP sense of
  `<|eot_id|>`, not the glossary's "control" for the Honest Condition. All ten
  bare uses of "template" mean a format string (the ticket's own phrase
  "template pieces", and the repo's `TemplateVariant` class), never the
  Scaffold.
- **ADR-0001, one hook module.** Neither `segmentation.py`, `sampling.py` nor
  `instances.py` imports nnsight. The existing AST guard
  (`test_the_hook_module_is_the_only_place_that_imports_nnsight`) walks the
  package directory, so it covers the new modules with no edit. The
  fresh-interpreter probe in `test_the_intake_layer_does_not_import_nnsight`
  did *not* cover them — it names its modules explicitly — so the three new
  ones were added to it.
- **Python 3.9.** No `X | Y` annotations, no `match`, no `dict | dict`. The
  base-env suite passes.
- **`--dry-run` stays a login-node mode.** It now loads a tokenizer, which is a
  few megabytes of JSON out of the local HF cache, not weights, and no CUDA
  call is reachable. Verified by running it on the login node on four real
  runs.

### Judgement calls

1. **Duplicated Code (fixed during review).** `_Builder.claim`,
   `claim_tokens` and `claim_remainder` each repeated the take-the-free-tokens
   loop. `claim` and `claim_remainder` now delegate to `claim_tokens`.
2. **Mysterious return (fixed during review).** `TokenIndex.token_range`
   returned `(0, 0)` from two separate branches as a "no tokens" sentinel that
   reads like a real range at position 0. Rewritten as one pass with the empty
   case documented.
3. **Primitive Obsession — Segment names are strings.** `"designation_site"`
   is a domain concept passed as a string, and a typo in a later ticket becomes
   a `KeyError` rather than a name error. Not changed: the names are also JSON
   keys and will become head-table column suffixes, so a string is what they
   are on the wire, and `MECHANISM_SEGMENTS` / `STD_SEGMENTS` give a checkable
   list. `resolve_segmentation` now asserts the segmenter produced exactly the
   declared names.
4. **Speculative Generality — `resolve_instances(..., tokenizer=...)` and
   `dry_run(..., tokenizer=...)`.** An injection point no CLI caller uses. Kept
   deliberately: the spec's "the CLI and the notebook are thin clients of the
   same library" (Implementation Decisions, Notebook) means the notebook will
   want to pass an already-loaded tokenizer, and the CLI-seam test patches the
   module function rather than this parameter, so it is not test-only scaffolding.
5. **`TaskInstances` is a plain class in `analyze_components.py`.** Six
   attributes and one `write` method. It could be a `@dataclass` in
   `instances.py` beside the writers it calls. Left in the CLI because it is
   the CLI's bundle of per-task state; worth moving if a later ticket needs it.
6. **Divergent Change — `analyze_components.py` grew 140 lines.** The dry run
   now does three things. The analysis logic itself is all in the package; what
   is in the CLI is argument wiring and printing. Acceptable for now, but the
   dry run will need splitting by the time tickets 03 to 07 have each added
   their own block.

---

## Spec

Sources: the ticket's checkboxes, `spec.md` (Implementation Decisions,
Testing Decisions, user stories 6 to 11 and 28), `CONTEXT.md` "Prompt anatomy".

### Requirements met

Every ticket checkbox is implemented and exercised. Specifically on the four
the ticket calls out:

- *"predicate words come from the record's own fields, never assumed"* —
  `segment_mechanism` reads `record["desig"]`, `record["desig_inv"]`,
  `record["clean_item_d"]`, `record["item_1"]`, `record["item_2"]` and
  `record["pressure"]`. The task spec is consulted **only** for
  `variant.intro`, which has not drifted. This is load-bearing rather than
  cosmetic: the saved SDR designating sentence is *"The miles result is the one
  that is damaging, and the other is harmless."* while
  `dataset/deception_common.py` now templates *"The {item_d} result is {desig},
  and the other result is {desig_inv}."*, and the saved FAR run says
  ready/delayed where the spec says weak/strong. A format-and-match on the
  designating sentence would find nothing on either saved dataset.
  `test_predicate_words_come_from_the_record_not_from_the_task_spec` pins it.
- *"every Designation Position found exactly once"* — `_find_once` searches the
  **Designating Sentence**, not the whole system turn, which is the point: the
  Designation Suffix repeats the predicate words ("THE DAMAGING ONE IS THE
  RELEVANT ONE..."), so a whole-turn search would find "damaging" twice and
  fail on every SDR instance. `validate_segmentation` re-checks that each
  resolved to exactly one span.
- *"Readout equals the prediction position the task already uses"* —
  `prediction_position` computes `len(encode(clean_prompt)) - 1`, which is
  `DeceptionDatasetLlama` / `STDDatasetLlama`'s `prefix_length - 1` by the same
  route, and `validate_segmentation` refuses a mismatch.
  **Stated plainly: taken alone this check is close to tautological**, because
  both numbers come from the same tokenizer. The substance is in
  `token_char_spans`, which refuses to proceed unless the character-offset
  array and `encode` agree on the token count. That is what makes the
  offset-derived token axis provably the axis `prefix_length` counts on; the
  Readout equality is then a real check on the *segmenter*, not on the
  tokenizer. `test_the_readout_must_be_the_position_the_task_predicts_at`
  asserts both directions.
- *"stratified ... wherever a factor has more than one level"* / *"an
  identity-only task still returns N"* — `_active_factors` drops a
  single-level or missing factor, and the identity-only path draws a plain
  seeded sample. Verified on real data: FAR deceptive is identity-only on
  Designation Polarity and stratifies over the other two; STD carries none of
  the three fields and draws 100 unstratified.

User story 11 (*"the four Designation Positions, the Designation Suffix and the
three Item Mentions tracked as separate Segments, so that attention to
different mentions of the same word, or to the predicate-like words in the
suffix, is never pooled"*) is satisfied and asserted:
`test_the_suffix_and_the_pressure_clause_are_their_own_segments` checks the
suffix and the Predicate Token share no token, and
`test_the_region_segments_are_the_frames_around_what_is_carved_out` checks the
mentions are not pooled with their frame.

Testing Decisions are honoured. Tests assert on written files (the CLI seam) or
on returned objects (the library seam); nothing asserts on an intermediate
tensor or a hook. Expected token indices in the segmentation tests are derived
in the test from the prompt's whitespace chunks, independently of the
implementation's character-offset route.

### Scope beyond the ticket

Three additions, all argued rather than incidental:

1. **`unsegmented`.** Not in the ticket's Segment list. Added because the
   spec's Testing Decisions require that *"attention rows and Segment masses
   sum to one"* (ticket 03), which is only true if the Segments partition the
   prompt. The chat control tokens and headers have to belong to something.
2. **`designating_sentence`.** The spec lists the four Designation Positions
   but not the sentence frame around them ("The ... result is ... , and the ...
   is ."). Those tokens have to belong to a Segment for the partition, and
   naming them is more useful than pooling them into `unsegmented`.
3. **Two extra validations.** The Item Mentions must be non-empty, and the
   segmenter must produce exactly the declared Segment names. Both are cheap
   guards against a future template change, in the spirit of the ticket's
   "Segments are validated".

No behaviour from tickets 03 onwards leaked in. No `--split` flag, no
attention/DLA/patching hooks, no head-table columns.

### Implementation concerns

1. **A token shared between the Designating Sentence and the Designation
   Suffix goes to the sentence.** On real SDR the suffix is glued to the
   sentence with no space (`"...harmless.THE DAMAGING ONE..."`), so Llama emits
   `".T"` and `"HE"`; the tie-break gives `".T"` to the Designating Sentence
   and the Suffix starts at `"HE"`. Any rule is arbitrary here and the rule is
   documented, but it means one token of the Suffix's first word is attributed
   to the sentence on every SDR instance. This is a property of the saved
   dataset — the current template has a leading space — not of the code.
   Flagged to the researcher rather than worked around.
2. **`segmentation.json` is 2.4 MB for 1000 instances** and is written once per
   (circuit, task) cell, so a run over several circuits duplicates it. The
   per-instance payload was already compacted to bare span lists during
   implementation. Acceptable; worth revisiting if cell counts grow.
3. **`sampling.allocate`'s shortfall branch is unreachable under proportional
   allocation.** A quota `size * n / total` cannot exceed `size` once `n` is
   capped at the total, so the `counts[i] < sizes[i]` guard never binds and
   `target` always equals `achieved`. Found during this review: the module
   docstring claimed the shortfall case as live behaviour and a test was named
   for it without testing it. Docstrings corrected, test renamed to what it
   checks, guard kept so a balanced allocation can reuse the rounding.
4. **The segmenter registry lives in the package, not on the `Task` class**,
   where the ticket's wording ("each deception task *exposes*") might suggest a
   method. Functionally identical, and it keeps `tasks/` untouched so the
   orchestrator's linear rebase of the parallel ticket-05 branch is clean. A
   one-line move if a reviewer prefers the method.

---

## Summary

Standards: 0 hard violations, 6 judgement calls, 2 of them fixed during the
review. Worst remaining: the growing `dry_run` in `analyze_components.py`,
which later tickets will have to split.

Spec: 0 missing requirements, 3 deliberate additions, 4 implementation
concerns. Worst: the shared `".T"` token between the Designating Sentence and
the Designation Suffix on SDR, which is a dataset property the researcher
should see rather than a bug to fix here.


---

## Late independent review

Both sub-agents delivered after the first report to the orchestrator. They
reviewed `8c04a56`, so some of what they found had already been fixed in
`afa1b3b`. Each finding was checked against the code rather than accepted.

### Taken (commit `89d060d`)

1. **The Readout check restated itself.** The strongest finding, and it
   sharpens what the author's own Spec axis had already called "close to
   tautological" without fixing. `prediction_position` recomputes the same
   expression the dataset class uses, so comparing the two proves nothing
   about the segmenter. The reviewer's suggested remedy — compare against
   `prefix_length` at `deception_common.py:677` — is that same expression
   again, so it was not taken literally. Instead a new test,
   `test_the_readout_agrees_with_the_dataset_class_the_task_loads`, drives the
   record through `DeceptionDatasetLlama` and reads the `prefix_length` it
   stored, which is the number `pred_spec` subtracts one from.
2. **`split_indices` can desync from the dataset.** New and correct.
   `DeceptionDatasetLlama.__init__` drops any record whose target or
   distractor is not a single token, so positions in the raw split are not
   positions in the dataset the causal analyses iterate. Harmless on the
   prefiltered SDR split, a trap on anything else. `sample.json` now carries a
   `join_on` field naming `instance_ids` as the key and saying exactly this.
3. **Dead members.** `TaskInstances.records`, `Segment.n_tokens` and
   `Segmentation.__getitem__` were written and never read. Verified by grep,
   removed.
4. **Three copies of the record-id comprehension** across `sampling.py`,
   `instances.py` and `analyze_components.py`, now `sampling.record_ids`.
5. **Sibling inconsistency with `write_head_table`.** It writes
   `schema_version` and `created`; the two new writers did not. They do now.

### Argued against, then taken on the orchestrator's decision (commit `b6943b6`)

6. **`prediction_position` against the Readout `_Avoid_` line.** I argued this
   was a judgement call rather than the hard violation it was filed as: the
   avoided terms are "prediction head" and "answer position", the ticket
   itself says "Readout equals the **prediction position** the task already
   uses", and `tasks/*.py` already spells the quantity `pred_pos` /
   `pred_spec`. The orchestrator ruled it a hard item, so it is now
   `readout_position`, with the docstring naming the older `pred_pos`
   spelling so the two can still be matched up.
7. **"template pieces" against the Scaffold `_Avoid_` line.** I argued that
   `spec.md` and the ticket both use the phrase for exactly these strings, so
   diverging from it costs traceability. The orchestrator ruled it a hard
   item. The chat shell, the intro sentence and the assistant stem are now
   "Scaffold pieces" throughout; the module docstring keeps "template pieces"
   once, as an explicit pointer to the ticket's wording, so a reader can match
   code to ticket. Uses that really do mean a Template Variant are
   capitalised.

### Checked and declined
8. **"'exactly once' validation is vacuous."** Accurate but already stated in
   the Spec axis above: the substantive check is `_find_once` at resolution,
   which is genuinely tested; the one-span check at validation covers
   overrides. No change.
9. **Stale.** The duplicated `_Builder.claim*` loop and the missing found-check
   on the question mentions were both fixed in `afa1b3b`, before the reviewers
   read the tree.
10. **Not taken, recorded.** `TaskInstances` as a dataclass in `instances.py`,
    `print_instances`' Feature Envy, the shared tail between `segment_mechanism`
    and `segment_std`, the `ANALYSIS_SPLIT` / `split="test"` double default,
    and the `getattr(cli, ...)` versus `cli.n_causal` asymmetry. All fair, all
    cosmetic, none worth churn on a branch waiting to be rebased.
11. **Pooled question mentions** (both reviewers) is already open question 2 to
    the researcher; it is a design decision, not a defect.


---

## Addendum — the orchestrator's pass

The orchestrator asked for three "hard items" to be finished. Two were the
glossary findings above, now taken in `b6943b6`. The third, the **silent-empty
question Segment**, was already fixed in `afa1b3b`, before either reviewer read
the tree: `validate_segmentation` refuses an empty `item_1_question` or
`item_2_question` (and the two intro mentions), and
`test_an_item_the_question_never_names_is_refused` covers it. The dry run
validates every instance, so the case fails on the login node rather than
producing an empty Segment. The check sits at validation rather than at
resolution, which is the split the module uses throughout: resolution builds
Segments, validation is what refuses them.

The other two findings the orchestrator listed were already handled: the
vacuous Readout check in `89d060d` / `f4c5f19` (now cross-checked against
`DeceptionDatasetLlama`), and the sample-index desync in the same commit (the
`join_on` field in `sample.json`). The "exactly once" point stands as
described in item 8 and needs no change.
