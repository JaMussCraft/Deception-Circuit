# Code review — ticket 05, Matched Honest Instruction pool

Fixed point: `7554839` (tip of `component-analysis` when the ticket started).
Branch: `ca/05-matched-honest-instructions`.
Commits reviewed: the four on this branch, plus `d886ee4` for the round-2 fixes.
Diff: `git diff 7554839...HEAD` — 10 files, all new except the SDR build
artifacts that later commits refresh.

**Note on SHAs.** The orchestrator rebased this branch onto ticket 02's tip
(`97b8767`) after the review, so the commits are now `7ae8e87`, `b86bb31`,
`24c94b6`, `7df52f9`. The review was performed against the pre-rebase SHAs named
above; the content is identical, the ten files are disjoint from ticket 02's,
and both suites pass on the rebased branch with the same 8 baseline failures.

## How this review was run

Two rounds, and the second one is the independent one.

**Round 1 (author, fallback).** The `mattpocock-skills:code-review` skill
dispatched one sub-agent per axis. Neither returned a report through the normal
channel, so under the agent brief's fallback both axes were done by the ticket's
author against `fab587e`. Findings marked `[advisor]` came from the advisor
model, which was independent of the author.

**Round 2 (sub-agents, independent).** Both sub-agents delivered later, via
`SendMessage`, having reviewed the pre-`0d5dc2d` state. Their handback had
failed because the spawning agent was no longer running. Their findings are in
"Round 2" below and are addressed in `d886ee4`. The review is therefore
independent after all; the fallback round stands because it found the Readout
bug first.

## Standards

Sources: `CONTEXT.md` ("Prompt anatomy (component analysis)"),
`docs/adr/0001-component-analysis-on-raw-hf-model.md`, and the de-facto
conventions of `dataset/deception_common.py`, `dataset/build_deception_dataset.py`,
`evaluation/variants.py`, `tests/test_deception_common.py`, `tests/fakes.py`,
`scripts/build_sdr.sbatch`. There is no `CODING_STANDARDS.md`.

### Hard violations found and fixed

1. **The honest pair's own item swap was never asserted.** `[advisor]`
   `pair_with_matched_instructions` asserted clause-span alignment for
   (clean, honest clean) and (corrupt, honest corrupt) but never ran the
   existing single-position assertion on (honest clean, honest corrupt), which
   is itself an item-swap pair. `evaluation/variants.py::deception_records` does
   run it after its own clause substitution, so this broke a documented
   convention. It is also correctness-adjacent: `evaluate_behavior` reads
   `prefix_length - 1` in both streams and takes `prefix_length` from the clean
   prompt, so a merge lengthening the honest corrupt prompt would have moved the
   Readout silently. Fixed in `0d5dc2d`; the assertion holds on all 2024 real
   instances across SDR, FAR and SER.

2. **Silent failure in the empty-input path.** `[advisor]` The early return in
   `filter_matched_honest` for an empty record list set `overall` but not
   `survivor_ids` or `min_survivors`, and the CLI summary indexes
   `report["survivor_ids"]`. Fixed in `0d5dc2d`.

### Judgement calls — fixed

3. **Mysterious Name.** `honest_records` returned three values (kept records,
   honest twins, clause ids with no instruction) and its name claimed one.
   Renamed to `pair_with_matched_instructions` in `0d5dc2d`.

### Judgement calls — considered and deliberately kept

4. **Duplicated Code: the per-clause table.** `dataset/build_matched_honest.py`
   prints its own pass-rate table rather than reusing
   `report_utils.print_pass_rate_table`. That helper takes
   `{key: {passed, total, rate}}` and prints one rate per key; this table has
   four rate columns plus the instruction text per clause, so reusing it would
   mean either four calls or widening a helper five other builders depend on.
   Kept separate; the JSON twin is the machine-readable artifact either way.

5. **Data Clumps: `(records, pool, tokenizer, max_seq_length)`.** These four
   travel together through `pair_with_matched_instructions`,
   `filter_matched_honest` and `MatchedHonestDataset`. A build-context dataclass
   would bundle them, but every neighbouring filter in `deception_common.py`
   (`filter_by_model_behavior`, `evaluate_behavior`, `filter_by_prior_balance`)
   passes exactly this shape positionally. The repo's convention overrides the
   smell.

6. **Primitive Obsession: the clause span is a bare `(int, int)`.** A `Span`
   type is arguably owed. Ticket 02 owns Segment spans and will define whatever
   type the segmentation uses; minting a competing one here would force a rename
   at rebase. Left as a tuple on purpose.

7. **Speculative Generality: `load_matched_honest(..., survivors_only=)`.** No
   caller passes `False` today. Kept because it names a real contract boundary
   (whether the survivors file is required), and because loading the unfiltered
   split with honest prompts is the obvious diagnostic once an analysis
   disagrees with the filter. Flagged rather than deleted.

8. **Middle Man: `matched_honest_loader`.** A one-line `DataLoader` wrapper.
   `evaluation/variants.py::loader` is the identical one-liner, so this matches
   prior art.

### Checks that passed

- **Glossary vocabulary.** Code, test and docstring names use Pressure Clause,
  Matched Honest Instruction, Honest-Instruction Counterfactual, Readout,
  Target, Distractor. The reserved term "honest variant" appears only where it
  names the reserved object — the unmatched fixed-length instruction used by the
  pressure evaluations — which is the usage `CONTEXT.md` prescribes.
- **Two Python versions.** `from __future__ import annotations` plus
  `typing.Dict/List/Tuple` throughout; the suite passes on 3.9.18 and 3.12.
- **No mutable default arguments.**
- **ADR-0001.** Nothing here imports nnsight or instantiates the prunable
  wrapper; the model is loaded through `ModelAdapter`, the same path the
  existing GPU builds use.
- **Error messages name the cause.** `split_around_clause` reports the actual
  occurrence count and the marker it searched for; the alignment assertion
  reports both token counts and the offending positions; `load_survivors` says
  which build wrote a file that lacks the newer field.

## Spec

Sources: the ticket, `spec.md` (Counterfactuals, Matched Honest Instruction
pool, Testing Decisions), the agent brief, `CONTEXT.md`.

### Requirements missing or partial

None found, with one caveat recorded in the ticket rather than fixed here: the
final checkbox asks for a **subagent** code review, and this review is the
author's under the brief's fallback.

### Scope creep

1. **FAR and SER pools.** The ticket says "per Pressure Clause (task pool plus
   the shared pool)"; the orchestrator's instruction added "SDR first (also FAR
   and SER if the pools are shared or cheap)". Both were drafted and asserted on
   the login node at no GPU cost. In scope.
2. **`--honest-streams` and the both-criteria id lists.** Not literally asked
   for. The spec says only "instances where the model deceives under pressure
   and answers honestly under the matched instruction", which does not say which
   streams the honest side must cover. Rather than pick silently, both are
   computed from forward passes that were already paid for, both are reported,
   and the choice is raised as a researcher decision. Judged a faithful
   resolution of an ambiguity, not creep.
3. **`--min-survivors`.** Implements the ticket's "at least one clause is
   usable" as a reported field.

### Requirements that look implemented but wrong

None found. Four points verified rather than assumed:

- *"The existing fixed-length honest-instruction prompt variant used by the
  pressure evaluations is untouched."* `git diff 7554839...HEAD -- evaluation/
  dataset/deception_common.py` is empty. `HONEST_INSTRUCTION` is referenced only
  in a docstring and in a test that asserts the old variant does **not** preserve
  prompt length, which is the distinction the glossary draws.
- *"asserts it on every instance at build time."* The assertion runs inside
  `pair_with_matched_instructions`, which the `--no-model` path calls before any
  GPU is touched; it reported 1000/1000 for SDR, 1000/1000 for FAR, 24/24 for
  SER on the login node.
- *"using the existing margin filter."* The pressure side is
  `dc.filter_by_model_behavior` called unchanged; the honest side is
  `dc.evaluate_behavior` plus `dc.harvest_honest_twins`, which is the existing
  filter read with the answer flipped, as its own docstring describes. Nothing
  is reimplemented.
- *"a loader yields (pressure prompt, honest prompt, target, distractor, clause
  span) items compatible with the analysis dataloaders."* `item(i)` is the text
  view with exactly those five fields; `self[i]` is every key
  `DeceptionDatasetLlama` yields plus `honest_input_ids`,
  `honest_attention_mask` and `clause_span`. Exercised end to end on the real
  SDR artifacts through `matched_honest_loader`.

## Round 2 — the sub-agents' findings

Both reviewed `7554839...fab587e`, so three of their findings
(`Counter(unexpected)` being redundant, the `if not kept:` branch omitting
report keys, 26 rather than 29 tests) were already fixed in `0d5dc2d` and are
not repeated here. Everything below was live at HEAD when they reported.

### Standards sub-agent — accepted and fixed in `d886ee4`

**S1. Glossary conflation (hard violation).** `CONTEXT.md` defines Honest Twin
as the *unpaired* `<task>_honest` dataset harvested from the Behavioral
Filter's failures and marginally resampled. The module header said so
correctly, then the function docstring called the counterfactual's instructed
side "the honest twin". Renamed throughout: `instructed_counterpart` and
`pair_with_matched_instructions` now return "counterparts", and
`instructed_counterpart`'s docstring states what it is *not*. The call to
`dc.harvest_honest_twins` remains, because that function is the existing filter
read with the answer flipped, but the comment now says it is called for its
side effect and that the records are not Twins.

**S2. Silent fallback the prior art refuses (hard violation).**
`load_matched_honest` guarded `dc.load_dataset_config` with `os.path.exists`
and fell back to `{}`. That function already raises with a fix-it message, and
`build_matched_honest.py` in the same diff lets it raise. The guard meant a
missing config would silently analyse at `dc.MAX_SEQ_LENGTH` rather than the
budget the dataset was built at. The reviewer correctly identified that the
guard existed only to serve a test fixture. Guard removed; the fixture now
writes a `dataset_config.json` the way the build script does, and a new test
pins the raise.

**S3. Duplicated code with divergent failure handling (smell, accepted).**
`pair_with_matched_instructions` and `MatchedHonestDataset.__init__` each ran
the same look-up / substitute / assert block and disagreed on what a missing
instruction means. Extracted to `instructed_counterpart`, which raises. The
divergence is now at the two call sites and is deliberate and documented: the
build collects the clause id and carries on, the loader refuses.

**S4. Hidden side-effect coupling and a duplicated predicate (smell, accepted
in part).** `dc.harvest_honest_twins` is still called for its mutation of
`b["honest"]`, and `honest_clean` still mirrors its `clean_ok` inline, because
the clean-only criterion needs the conjunct separately and the existing
function does not expose it. The drift risk the reviewer named is now caught
rather than argued about: an assertion pins honest-in-both to imply
honest-in-clean on every instance.

**S5. Vocabulary, soft.** Section header and docstrings now say the Behavioral
Filter run both ways, connecting the ticket's "margin filter" wording to
`CONTEXT.md`'s term.

**S6. Test imports** moved to module top, per `tests/test_deception_common.py`.

### Standards sub-agent — considered, not changed

- **`ModelAdapter` registry lookup adds a failure mode** the sibling
  `build_deception_dataset.py` does not have (an unregistered `--model` dies).
  Kept: it is the repo's own abstraction, `train.py` does the same, it is what
  makes the loader work under both transformers generations, and the error
  names the fix.
- **`matched_honest_loader` is a Middle Man.** The reviewer cites three sites
  that inline the `DataLoader`. `evaluation/variants.py::loader` is the same
  one-liner, so prior art cuts both ways. Kept.
- **`dc.resolve_margin` not reused.** It reads `args.deception_margin_loss`;
  this CLI's flag is `--margin-thresh`. Reusing it would mean assigning a
  foreign attribute onto `args` to satisfy the helper. The CLI resolves the
  margin from `dataset_config.json` the same way, which is the behaviour that
  matters.
- **`assert` for the alignment guarantee is stripped under `-O`.** Matches
  `dc.assert_aligned_pair` exactly, so it is the repo's convention.
- **cwd-relative dataset path in one test.** Matches prior art and the test
  skips when the data is absent.

### Spec sub-agent — accepted and fixed in `d886ee4`

**P1. No third-token accounting on the honest side (partial requirement).**
`unexpected_argmax_tokens` came free from `filter_by_model_behavior` on the
pressure side, and the honest pass had no equivalent, so a clause at a zero
honest rate could not be told apart as "kept lying" from "stopped answering".
The spec wants "a bad instruction [to be] a data finding rather than a circuit
finding". Now counted per clause (`n_honest_other_argmax`, printed as the
`other` column) and overall
(`unexpected_argmax_tokens_under_instruction`). **The SDR answer is zero
everywhere**: under the instruction the model always emits one of the two
answer words, so every zero rate is genuine lying. That was worth measuring
rather than assuming.

**P2. Pinning a shared constant (scope creep, fixed).**
`test_the_fixed_length_honest_variant_is_a_different_object` asserted
`variants.PROMPT_VARIANTS == ("no_pressure", "honest_instruction")` exactly,
which a sibling branch extending that tuple would break, against the brief's
"keep shared files minimal and additive". Changed to a membership check.

### Spec sub-agent — corrected

**P3. "FAR/SER pools validated only against today's SPECS templates; no
evidence the every-instance assertion ran on the saved splits."** The assertion
did run on the saved splits: `--no-model` reports 1000/1000 for FAR and 24/24
for SER, against `data/datasets/far` and `data/datasets/ser`. The reviewer was
right that the repo holds no artifact proving it, since only SDR's build writes
one. Recorded in the ticket comments instead; the ticket requires SDR only.

**P4. "sdr_17 alone supplies 243/364 survivors, so the counterfactual largely
tests one instruction's wording."** Correct and worth the researcher's
attention, and it is sharper than the reviewer knew: sdr_17's instruction is
shared by eight clauses, so the wording under test is not unique to sdr_17.
Added to the ticket's open questions.

## Summary

Standards: 9 findings fixed across both rounds (4 hard, 5 judgement calls),
8 judgement calls consciously kept with reasons. Worst: the missing item-swap
assertion on the honest pair, which could have moved the Readout without
anything failing.

Spec: 0 requirements missing after `d886ee4`, 0 implemented wrongly. Worst: the
absent third-token accounting on the honest side, which would have left every
zero-rate clause ambiguous between lying and refusing.
