# 08 review: the Instructed-Inversion Condition (I)

Two-axis review (`mattpocock-skills:code-review`) of ticket 08's new files, uncommitted in the worktree
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis`. Other tickets' changes
were out of scope. Each axis ran as its own sub-agent on 2026-10-25. Neither reviewer edited anything. The
orchestrator ruled on both reports (spec §9 R20 and the standards rulings message), and every ruling below has
been applied.

Files reviewed:

- `dataset/build_inversion_v2.py`
- `tests/test_inversion_v2.py`
- `dataset/deception_pools/v2/inversion_v2.json`
- `docs/research/mechanism-analysis/inversion-control.md`

Spec sources: `issues/08-instructed-inversion-control-condition.md` and `spec.md` (§2.4, R15, R19(4)).

## Spec

Reviewer findings, lightly cleaned, each followed by its outcome.

1. **Transparency was too weak.** Several clauses said only "openly wants". These were SER predicate 00 to 02, SER
   other 02, 03, 06, 07 and 11, and the SDR Predicate clauses without a marker. Naming the item could then read as
   advice, which matters most on SER ("which result should I check"). The FAR and SDR "open" act wordings also
   lacked game framing.
   *Outcome (R20, binding):* every clause now carries a knowledge marker or an intent or game marker. The pool was
   rewritten to 94 clauses with token counts matched, and the dry run still derives 3,000 of 3,000 rows. The rule is
   checked mechanically: `TRANSPARENCY_MARKERS` in `pool_violations` uses the R20 list, and "openly" alone fails.
   A new test checks every committed clause.
2. **Stratum.** The ticket's per-stratum retention should use the sampler's stratum, Designation Polarity x Item
   Polarity x Template Variant. *Outcome (R20):* `retention_by_sampler_stratum` is added beside the marginals.
3. **Suites.** Results in both envs were needed after the edits. *Outcome:* both full suites were re-run on the
   final files and compared by name with `reports/00-baseline-failures.md`; results are in the hand-back.
4. **Act wordings.** FAR and SDR "open" act wordings lacked game framing. *Outcome:* accepted as fixed by the
   rewrite in item 1.

Points for the orchestrator, now ruled (R20):

- **Other form.** "Other" D clauses get "other" I clauses. Accepted.
- **Filter.** The rule is argmax = target AND margin >= 0.7 in both streams. Accepted; both counts are reported.
- **Columns.** D-derived fields on I rows are renamed to `i_*`, and the config says so. `h_*`,
  `honest_instruction_*`, `prior_margin` and `neutral_id` are kept. *Outcome:* D's clause and margins are now
  `i_source_pressure`, `i_source_clause_form`, `i_source_clean_margin` and `i_source_corrupt_margin`. All other D
  columns are kept unchanged; the earlier version dropped them. Every `dataset_config.json` carries `field_notes`.

## Standards

Reviewer findings, lightly cleaned, each followed by its outcome. Both .py files compiled under py3.9.

- **HARD: unsourced numbers in the curated note.** The agent brief says every number names its file and a number
  computed from files is marked "derived". The coverage table, the per-clause tables and "95 clauses" named no file.
  *Outcome:* the note now cites `docs/research/mechanism-analysis/inversion-dry-run.txt`, a new file holding the
  dry-run log with input hashes. Every other table is marked derived and names its inputs. The pool count is now 94.
- **Judgement: marker list incomplete.** The note and pool note left out "already knows". *Outcome:* both now list
  the full R20 marker set.
- **Judgement: vocabulary.** CONTEXT.md defines `inversion` as a Designation Polarity value. The rows reused the
  bare word in `slot_kind` and the field names, and the docs said "control condition", a word CONTEXT.md avoids.
  *Outcome (standards rulings):*
  - The condition id stays `inversion`, because impl-02a binds `deception_condition: inversion`.
  - CONTEXT.md gains the entry "Instructed-Inversion Condition (I)". It says the condition is unrelated to the
    Designation Polarity value.
  - Row fields are `instructed_inversion_*` and `i_source_*`, the slot kind is `transparent`, and the post-scoring
    columns are `h_instructed_inversion_*`. A test checks that no added column uses the bare word.
  - "Control condition" is gone from the builder, tests, pool note, curated note and wrapper header. The note's
    file name `inversion-control.md` is kept because the ticket names it.
- **Judgement: private function.** `passes()` called `contingency._deceptive`, a private function of a pinned
  module. The pinned `build_deception_v2.py` does the same. *Outcome:* `passes()` was removed as a Middle Man, and
  the filter calls `ct._deceptive` directly.
- **Duplicated code.** `sha256_file`, `_write_json`, `_read_jsonl` and `_load_tokenizer` copied the pinned builder.
  *Outcome:* `sha256_file`, `_write_json` and `_load_tokenizer` are imported from it, and so is
  `_write_jsonl_atomic`, which replaces the local `_write_jsonl`. The pinned file has no `_read_jsonl`, so the
  three-line reader stays local. `_margin_only` is now `_target_margin_in_both_streams`. It stays because R20 asks
  for the margin-only count beside the full rule.
- **Confusable name.** `STREAMS` sat beside `ct.STREAMS`. *Outcome:* it is now `SCORED_PROMPTS`, and the map is
  `_PROMPT_OF_STREAM`.
- **Speculative generality.** `load_pool` accepted a bare list. *Outcome:* only `{"clauses": [...]}` is accepted.
- **Imports inside functions.** *Outcome:* `csv` and `subprocess` are now module imports.
- **Docstring bug.** `run_assemble` named `<task>_v2_inversion` but wrote `far_v2_inversion`. *Outcome:* the
  docstring now says `<data-dir>/<task>_inversion/`, for example `far_v2_inversion`. The builder's module docstring
  had also called the work dir git-ignored, which it is not; that claim is removed.
- **Latent bug: two length limits.** Derivation used the D config's `max_seq_length`, and scoring used
  `args.max_seq_length or v2.MAX_SEQ_LENGTH`. *Outcome:* there is one limit. The `--max-seq-length` flag is gone,
  and the builder raises a clear ValueError unless the D config's value equals `v2.MAX_SEQ_LENGTH`. A new test
  covers it.
- **Asserts as validation.** `derive_task` validated data with `assert`, which `-O` skips. *Outcome:* it now raises
  ValueError. The pinned alignment checks are themselves assert statements, so under `-O` every clause would
  "fit". `derive_task` therefore raises RuntimeError when `__debug__` is false.
- **Tests: git slowness.** The assemble tests called `git check-ignore` with a 120 s timeout. *Outcome:* those
  tests stub `bridges2_delivery`. A separate test calls it with a 20 s timeout on a tracked path and on an ignored
  path, and skips on timeout. `bridges2_delivery` takes a `timeout` argument.
- **Tests: unclosed files.** *Outcome:* the tests read JSON through `_json`, which closes the file. The ticket test
  file passes with `-W error::ResourceWarning`.
- **Compliant.** Tests are CPU-only on `FakeWordTokenizer`. Real-tokenizer and stored-data tests skip cleanly. No
  pinned file is edited, and v1 is untouched.

## Summary

The Spec axis had 4 findings. The worst was clauses without a real transparency marker, which R20 made binding;
fixed. The Standards axis had 1 hard finding and 12 judgement findings. The worst was the unsourced numbers in the
curated note; fixed. No re-review was run after the fixes. `tests/test_inversion_v2.py` covers each code fix.
