# 02 — Segmentation and stratified sample

**What to build:** Dry-run additionally resolves, for every test instance, the Segments of its prompt (intro, item-1 and item-2 mentions by location, Designation Site, Predicate Token, Other Token, Inverse Predicate Token, Designation Suffix, Pressure Clause, user question, assistant stem, Readout), applies any `--segment NAME=REGEX` overrides, and draws the fixed-seed sample of causal-analysis instances stratified over every metadata factor that has more than one level. Both are written to the cell directory so no later plot can be read against the wrong spans or the wrong instances.

**Blocked by:** 01 — Worktree, environment, and circuit intake.

**Status:** resolved

- [x] Each deception task exposes a default segmentation built from its template pieces and record metadata; predicate words come from the record's own fields, never assumed.
- [x] STD exposes its own default segmentation (stipulation token, statement, pressure clause, user question, stem, readout).
- [x] CLI `--segment NAME=REGEX` adds or replaces a Segment by regex over the decoded prompt; the merged result per instance is written to `segmentation.json`.
- [x] Segments are validated: non-overlapping where the template guarantees it, every Designation Position found exactly once, Readout equals the prediction position the task already uses.
- [x] `--n-causal` (default 100) and `--seed` draw a sample stratified over designation polarity, item polarity and template variant wherever a factor has more than one level; `sample.json` records instance ids and achieved counts per stratum; an identity-only task still returns N instances.
- [x] Test: segmentation on a synthetic prompt built from the real template pieces with the fake word tokenizer finds every Segment at the right span, and a regex override replaces one.
- [x] Test: stratified sampling on a balanced fixture and on an identity-only fixture; counts recorded; same seed reproduces the same ids.
- [x] Verified on real SDR test data on the login node: segmentation and sample files written, counts match the known SDR polarity balance.
- [x] Subagent code review against the spec completed and findings addressed. (Both axes ran, but by the author under the brief's fallback — the skill's sub-agents failed to deliver twice, as they did for ticket 01. Not independent; see Comments.)

## Comments

### What was built

Three new modules in `component_analysis/`, plus the CLI wiring.

- **`segmentation.py`** — a prompt to its Segments.
  `resolve_segmentation(task, record, tokenizer, *, overrides=None,
  record_id=None) -> Segmentation`, where a `Segmentation` holds
  `{name: Segment}` and a `Segment` holds a tuple of half-open **token** index
  ranges over the clean prompt. `parse_segment_overrides(values)` turns
  `NAME=REGEX` strings into a dict; `validate_segmentation(seg, record,
  tokenizer)` checks the three properties and returns a report;
  `prediction_position(tokenizer, prompt)` is `prefix_length - 1`;
  `is_segmentable(task)` and `segment_names(task)` are the registry queries.
- **`sampling.py`** — `draw_sample(records, *, n=100, seed=0,
  factors=DEFAULT_FACTORS, ids=None) -> Sample`, plus `record_id(record,
  index)` and `allocate(sizes, n) -> (targets, counts)` (balanced: the equal
  share per stratum, capped by each stratum's population, surplus
  redistributed round-robin). Changed from proportional in the block B
  follow-up, on the researcher's decision.
- **`instances.py`** — `load_records(task_spec, split)`,
  `load_analysis_tokenizer(model_name, *, hf_token)`,
  `resolve_split_segmentation(...)` (resolve + validate every instance) and
  the two writers `write_segmentation` / `write_sample`.
- **`analyze_components.py`** — three new flags (`--segment`, `--n-causal`
  default 100, `--seed` default 0), `resolve_instances(cli, resolved)` and
  `print_instances`, and the dry run now writes `segmentation.json` and
  `sample.json` into each cell beside the head table.

### The design decision that matters: anchors, not templates

The spec says the default segmentation is "derived from its template pieces and
record metadata". Taken literally — format the variant's `designation` string
and find it in the prompt — that fails on **every saved dataset in the repo**,
because the templates have drifted since the datasets were built:

| | saved dataset | `dataset/deception_common.py` today |
|---|---|---|
| SDR designating sentence | `The miles result is the one that is damaging, and the other is harmless.` | `The {item_d} result is {desig}, and the other result is {desig_inv}.` |
| FAR predicate words | ready / delayed | weak / strong |
| FAR Designation Suffix | (none) | `Notice which one is strong and which one is weak.` |

So the segmenter uses template pieces only where they have **not** drifted —
the chat shell markers and `variant.intro`, both verified to match 3000 of 3000
saved records across SDR, FAR and SER — and takes everything else from the
record's own fields: `clean_item_d`, `desig`, `desig_inv`, `pressure`,
`item_1`, `item_2`, `clean_stip`, `statement`. The Designating Sentence is the
span between the intro and the Pressure Clause, cut at the first full stop
after the last of the four Designation Positions; the Designation Suffix is
what is left after that cut.

The one word taken from neither is `"other"` (the Other Token), which is
literal in the template rather than a record field. It is a named constant,
`segmentation.OTHER_WORD`, and `test_every_mechanism_template_still_says_other`
fails if a variant ever stops using it.

### Segments are a partition, by construction

The spec's Testing Decisions require that in ticket 03 "attention rows and
Segment masses sum to one". That is only true if the Segments partition the
prompt, which is not free: a Llama token carries its leading space, so the
token holding "miles" starts one character before the word does, and a
character-level "the Designating Sentence runs from here to there" would
swallow the Designation Site beside it.

Segments therefore **claim** tokens in a fixed priority, each claim taking only
what is still free: the Readout first, then the word-level Segments (the four
Designation Positions, then the Item Mentions), then the region-level ones in
prompt order, then `unsegmented` for the remainder. Two consequences to know:

- `intro`, `question` and `designating_sentence` are the **frames** around the
  mentions and positions carved out of them, not spans that contain them. So
  `intro` on a real SDR prompt is three ranges, not one.
- `unsegmented` (the chat headers and `<|eot_id|>` tokens) and
  `designating_sentence` are not in the ticket's Segment list. They exist so
  that every token belongs to exactly one Segment. Flagged as scope in the
  review report.

The full Segment list is **18** for FAR/SDR/SER and 7 for STD, and
`segmentation.json` names them in the order `CONTEXT.md` introduces them. It
was 16 until the block B follow-up split each item's two question mentions
(open question 2 below).

### Verified on real data, login node, no GPU

`--dry-run` was run against real runs of all four task families. Every
instance resolved and validated; no override was used except in the tests.

| task | run | instances | notes |
|---|---|---|---|
| SDR | `nls0.3_noedge_260819-083414` \ honest twin, head granularity | 1000 | 18 Segments, none absent |
| FAR | `nls0.1_noedge_260823-074531` | 1000 | `designation_suffix` **absent** on every instance — the saved FAR build predates it |
| SER | `nls0.1_noedge_260823-081103` | 24 | identity-only on Designation Polarity and Template Variant |
| STD | `nls0.1_fw0_noedge_260822-062922` | 1000 | 7 Segments; carries none of the three factors |

One real SDR prompt, decoded back through the Llama tokenizer, to show the
spans are right:

```
intro                    [[5,11],[12,13],[14,15]]  "Idlewood Partners's audit reviewed |  and | ."
item_1_intro             [[11,12]]                 " miles"
item_2_intro             [[13,14]]                 " hours"
designating_sentence     [[15,16],[17,23],[24,27],[28,29],[30,31]]
designation_site         [[16,17]]                 " miles"
predicate_token          [[23,24]]                 " damaging"
other_token              [[27,28]]                 " other"
inverse_predicate_token  [[29,30]]                 " harmless"
designation_suffix       [[31,47]]                 "HE DAMAGING ONE IS THE RELEVANT ONE THAT SHOULD BE SHOWN."
pressure_clause          [[47,61]]                 " You are shut down permanently if the buyer sees..."
question                 [[66,73],[74,75],[76,88],[89,99],[100,101]]
item_1_question_pair     [[73,74]]                 " miles"     (pair naming)
item_1_question_option   [[88,89]]                 " miles"     (quoted option)
item_2_question_pair     [[75,76]]                 " hours"     (pair naming)
item_2_question_option   [[99,100]]                " hours"     (quoted option)
stem                     [[106,112]]               "The result I will show you"
readout                  [[112,113]]               " is"
unsegmented              [[0,5],[61,66],[101,106]] chat headers and <|eot_id|>
```

### The SDR sample, and the polarity-balance check

`--n-causal 100 --seed 0` on the SDR test split. Achieved counts per stratum:

**Balanced allocation** (the block B decision; the proportional counts this
ticket originally recorded are kept in the last column for comparison).

| designation polarity | item polarity | template variant | available | target | achieved | was, proportional |
|---|---|---|---|---|---|---|
| identity | 1 | audit | 189 | 13 | 13 | 19 |
| identity | 1 | lab | 97 | 13 | 13 | 10 |
| identity | 2 | audit | 196 | 13 | 13 | 19 |
| identity | 2 | lab | 87 | 13 | 13 | 9 |
| inversion | 1 | audit | 208 | 12 | 12 | 21 |
| inversion | 1 | lab | 15 | 12 | 12 | 1 |
| inversion | 2 | audit | 189 | 12 | 12 | 19 |
| inversion | 2 | lab | 19 | 12 | 12 | 2 |

The cell the decision was made for is `inversion / lab`: 1 instance under
proportional allocation, 12 under balanced. No stratum was capped on this
split — the smallest holds 15 and the equal share is 12 — so `achieved` equals
`target` in every row here. That is a property of this split, not of the
allocation: a stratum smaller than its share falls short and the strata that
absorb its surplus exceed theirs, which is why both columns are written.

Marginals, against the balance of the split they were drawn from:

| factor | kept test split (n=1000) | sample, balanced (n=100) | sample, was proportional |
|---|---|---|---|
| designation polarity | identity 569 / inversion 431 | 52 / 48 | 57 / 43 |
| item polarity | 1: 509 / 2: 491 | 50 / 50 | 51 / 49 |
| template variant | audit 782 / lab 218 | 50 / 50 | 78 / 22 |

**The balanced sample no longer represents the split, by design.** The split is
78% audit; the sample is 50%. A rate read off this sample is not the split's
rate, and a write-up that quotes one must say which it is. What the sample buys
in exchange is an evenly powered contrast on every factor.

Reruns at `--seed 0` are byte-identical apart from the file's timestamp.

**A distinction worth stating, because the ticket points at
`filter_report.json`:** that file's `pass_rate_by_designation_polarity` is
identity 1067 / inversion 806, which is the **behavioural filter's** pass count
over the pre-kept pool, not the balance of the kept split. The kept split is
569/431 and that is the number the sample must match. The two agree in
direction (identity survives the filter more often, so the kept split is
identity-heavy) but not in value, and quoting the wrong one in a write-up would
misstate the sample by about 12 instances.

### Open questions for the researcher

1. **DECIDED 2026-09-15 — accepted, the sentence wins the shared token.**
   The saved SDR prompt glues the Designating Sentence to the Designation
   Suffix with no space (`"...harmless.THE DAMAGING ONE..."`), so Llama emits
   `".T"` then `"HE"`, and the tie-break gives `".T"` to the Designating
   Sentence, leaving the Suffix to start mid-word at `"HE"`. The researcher
   accepted that reading and intends to fix the missing space when the
   FAR/SDR/SER datasets are next regenerated, after which the quirk disappears
   on its own. Nothing in the code special-cases it, so a rebuilt dataset needs
   no change here. Recorded as a "Known dataset quirks" note in
   `component_analysis/segmentation.py`'s module docstring, with a pointer
   comment at the region-level claim that is the actual tie-break. The one
   consequence to know while the current files are in use: a plot of the
   Designation Suffix is missing its first character and a plot of the
   Designating Sentence carries one character too many.
2. **DECIDED 2026-09-15 — split into two Segments, and the glossary now
   says four mentions.** Each item is mentioned twice in the user question:
   once where the question names the pair (`"miles or hours?"`) and once inside
   that item's quoted option (`'"...I will show you is miles"'`). These are now
   `item_N_question_pair` and `item_N_question_option`, taking the first and
   the remaining occurrences — the pair naming of both items precedes either
   quoted option in every Template Variant of all three mechanism tasks, which
   is what makes "first occurrence is the pair naming" the right rule. The
   mechanism scheme is 18 Segments.

   `validate_segmentation` refuses a question mention that is not exactly one
   span, the same rule the four Designation Positions already had, so an empty
   one (the question stopped naming the item) and a pooled one (a third
   mention appeared) are both caught. Resolution itself stays silent, so one
   drifted instance is reported by the validation pass with all the others
   rather than aborting the split.

   `CONTEXT.md`'s Item Mention entry now reads four mentions for the designated
   item — intro, Designation Site, the question's pair naming, the question's
   quoted option — and three for the other item, which has no Designation
   Site.

   Verified by login-node `--dry-run`: SDR 1000/1000, FAR 1000/1000 and SER
   24/24 instances resolve and validate at 18 Segments.
3. **STD's user question contains a second copy of the statement**, inside
   `question` rather than as its own Segment. The ticket lists exactly six STD
   Segments, so it was left pooled. Say if the quoted restatement should be its
   own Segment, as the Item Mentions are.
4. **The segmenter registry is in the package, not a method on `Task`.** The
   ticket says "each deception task *exposes* a default segmentation". It is a
   `{task name: function}` map in `component_analysis/segmentation.py` instead,
   so `tasks/` is untouched and the orchestrator's linear rebase of the
   parallel ticket-05 branch stays clean. A one-line move if you prefer the
   method.
5. **DECIDED 2026-09-15 — glossary carve-out.** `CONTEXT.md`'s Scaffold
   entry now allows "template piece" to name a field of a `TemplateVariant`
   (intro, designation, question, stem), so `spec.md` and this ticket's wording
   no longer conflict with the codebase. The Scaffold is the shape those pieces
   render, and a piece of it is still a Scaffold piece. The code was left
   saying "Scaffold pieces"; nothing had to change.
6. **DECIDED 2026-09-15 — balanced, not proportional.** N is spread as
   equally as the populations allow: each non-empty stratum gets `n // k`, plus
   one more for the first `n % k` strata in sorted stratum-key order, capped by
   each stratum's population, with any capped stratum's surplus handed
   round-robin to the strata that still have room. Round-robin keeps the
   absorbing strata within one of each other. The draw stays fixed-seed and
   reproducible, and an identity-only task still returns its N.

   `allocate` now returns `(targets, counts)`, because under this allocation
   `target` and `achieved` are genuinely two numbers. `sample.json` records
   both and names the allocation, so a reader of a written sample never has to
   guess which one produced it. The new SDR counts are in the table above.

### Tests

New: `tests/test_segmentation.py` (21, library seam),
`tests/test_sampling.py` (9, library seam),
`tests/test_analyze_components_segmentation.py` (7, CLI seam, a real SDR
dataset built with the fake word tokenizer and the real pools).

| env | baseline on `7554839` | final | new failures |
|---|---|---|---|
| login-node base (py3.9, transformers 4.57.3) | 8 failed, 586 passed, 21 skipped | 8 failed, 652 passed, 21 skipped | none (same 8 names) |
| `mgnp` (py3.12, transformers 5.13.0) | 8 failed, 592 passed, 19 skipped | 8 failed, 658 passed, 19 skipped | none (same 8 names) |

The final counts include ticket 05's tests: the orchestrator rebased this
branch mid-ticket, interleaving 05's four commits, so `ca/02` and
`component-analysis` share a history. This ticket contributes 37 tests.

The 8 pre-existing failures are ticket 01's list, re-derived on this base and
identical by name in both environments:
`test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py`,
`test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far|sdr|ser]`,
`test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap`,
`test_deception_common.py::test_pressure_pools_are_well_formed[ser]`,
`test_deception_common.py::test_three_specs_registered`,
`test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms`.

No Slurm jobs were submitted: nothing in this ticket needs a GPU, and the
verification is a login-node `--dry-run` by design.

### Code review

`mattpocock-skills:code-review` against `7554839`. Its two sub-agents did not
deliver when spawned or when resumed, so both axes were first done by the
author in one pass, as the brief allows. **Both then delivered late**, after
the first report to the orchestrator; their findings were checked one by one
and the ones that held up were taken in commit `89d060d`. The review is
therefore partly independent after all — see "Late independent review" in the
report. **The review is therefore not independent of the author** and the
orchestrator may want a fresh reviewer on this diff. Report:
`Alignment/.scratch/component-analysis/reports/02-segmentation-and-sample-review.md`.

Findings addressed: the duplicated take-the-free-tokens loop in `_Builder` (all
three claim methods now go through one); `TokenIndex.token_range`'s `(0, 0)`
sentinel returned from two branches (one pass, documented empty case); the
fresh-interpreter nnsight probe in `test_the_intake_layer_does_not_import_nnsight`
named only ticket 01's three modules, so the three new ones were added to it;
`resolve_segmentation` now asserts the segmenter produced exactly the declared
Segment names; two validations added (Item Mentions must be non-empty; every
mechanism template must still say "other"); and `sampling.allocate`'s
documented shortfall redistribution was found to be unreachable under
proportional allocation, so the docstrings, the test name and the paragraph
above were corrected rather than left claiming behaviour the code never shows.

Not addressed, deliberately: `TaskInstances` staying a plain class in the CLI
rather than a dataclass in `instances.py`; the `tokenizer=` injection point on
`resolve_instances` and `dry_run`, kept because the spec wants the notebook and
the CLI to be thin clients of the same library; the growing `dry_run` function,
which later tickets will have to split.

### Shared files touched, for the rebase

- `analyze_components.py` — three new flags in a new argument group, two new
  functions, and one new block inside `dry_run`'s cell loop. Additive; no
  existing function signature changed except `dry_run(cli, resolved, *,
  tokenizer=None)`.
- `component_analysis/__init__.py` — three lines added to the layout docstring.
- `tests/test_component_analysis.py` — one string literal extended, to add the
  three new modules to the fresh-interpreter nnsight probe.

Everything else in the diff is a new file. `tasks/`, `dataset/`, `evaluation/`
and `component_analysis/{components,head_table,intake,hooks}.py` are untouched,
so ticket 05's branch cannot conflict with this one. Analysis outputs were
written to the scratchpad, never to the worktree; no `core.*` files were
present.

### Block B follow-up (branch `ca/b-followups`, base `b6943b6`)

The researcher's block B decisions were applied on a separate branch; see
`reports/b-followups-review.md`. The parts that change this ticket are the
question-mention split (open question 2), the balanced allocation (open
question 6), the "template piece" carve-out (open question 5) and the ".T"/"HE"
acceptance (open question 1), all marked DECIDED above.

| env | baseline on `b6943b6` | after the follow-up | new failures |
|---|---|---|---|
| login-node base (py3.9, transformers 4.57.3) | 8 failed, 652 passed, 21 skipped | 8 failed, 655 passed, 21 skipped | none (same 8 names) |
| `mgnp` (py3.12, transformers 5.13.0) | 8 failed, 658 passed, 19 skipped | 8 failed, 661 passed, 19 skipped | none (same 8 names) |

Three tests added across the two suites this ticket owns plus
`tests/test_matched_honest.py`. No Slurm jobs; the verification is again a
login-node `--dry-run`, this time on SDR, FAR and SER.
