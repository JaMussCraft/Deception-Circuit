# Code review — 02b, block C scaffold

Fixed point: `2cbcac4` (tip of `component-analysis`). Branch
`ca/02b-block-c-scaffold`, four commits:

    575d612  Give block C one scaffold so four analyses can be built in parallel
    f126890  Say plainly that the causal loaders do not cover STD
    0b02cdc  Give each blocked ticket its own line in the registry
    917474d  Take both code reviews: receivers, the fp32 readout, and two real bugs

`mattpocock-skills:code-review` against `575d612`, both axes as parallel
sub-agents. Both ran to completion without handing a report back; both were
resumed by message and **both delivered**, late, after the first report to the
orchestrator — the same pattern ticket 02 saw. **This review is independent of
the author.** Their reports are reproduced verbatim below, then the author's
own parallel pass, then every finding with its outcome.

---

## Standards (sub-agent, verbatim)

> Standards review of 575d612 (block C scaffold): one hard ADR breach —
> nnsight's private `_model` handle is read at four sites outside hooks.py —
> plus 4 softer standard issues and 9 baseline smells.
>
> ### Hard documented-standard violation
>
> **`_model` escapes `hooks.py`.** ADR-0001 Consequences: *"The hook surface is
> confined to one module so a migration touches one file."* `__init__.py`:
> *"Only `hooks.py` imports nnsight."* nnsight's private `LanguageModel._model`
> is read at:
> - `analyze_components.py:381` — `next(iter(model._model.parameters()))`
> - `scripts/verify_block_c.py:58,64,66` — incl. `model._model.config._attn_implementation`
> - `tests/stub_analysis.py:99,170` — same chain, twice
>
> Letter-wise no other module imports nnsight, but a 0.8 migration now touches
> four files. Also Duplicated Code / Message Chain / Feature Envy. `hooks._hf()`
> already exists unexported — fix is a rename plus `hooks.device_and_dtype(model)`.
>
> ### Softer standard issues
>
> - **`load_analysis_model(attn_implementation=...)`** — ADR: *"Eager attention
>   is switched on only for attention-pattern extraction."* Its docstring
>   invites the opposite ("callers that only ever want one of the two").
>   `attention_weights` already switches in try/finally, so the knob is
>   Speculative Generality against the ADR.
> - **No fp32 readout seam** — ADR: *"Ranking metrics are read through an fp32
>   final norm and unembedding."* `Capture.logits`/`.residual` are bf16 and no
>   fp32 norm+`lm_head` primitive exists, so tickets 03/04/07/08 will each
>   reimplement it.
> - **`stub_analysis.py`** — "The control the replace-all error is read
>   against". CONTEXT.md lists `control` under Honest Condition's `_Avoid_`.
> - **`hooks.py` docstring** — "Ticket 01 fills in only the model loading" is
>   stale; this commit added the three passes below it.
>
> ### Baseline smells (judgement calls)
>
> - **Data Clump** — `task, split, batch_size, max_length, pools_dir,
>   honest_streams` through five `dataloaders.py` signatures.
> - **Duplicated Code** — `AnalysisContext.causal_batches`/`descriptive_batches`
>   differ only in `ids=`; `run()` re-walks `dry_run()`'s circuit×task grid; the
>   6-line nnsight skip preamble is byte-identical in `test_component_hooks.py`
>   / `test_nnsight_hooks.py` (`tests/helpers.py` is the home).
> - **Mysterious Name** — `_traced_forward` binds `_num_heads` then uses it
>   (`range(_num_heads)`); the underscore is this repo's "ignored" marker.
> - **Overloaded name** — `positions` means three things in `hooks.py`; rename
>   `Replacement.positions` → `where`.
> - **Speculative Generality** — `run(..., model=None)` has no caller passing
>   `model=`; `find_checks`'s second recursive-glob fallback.
> - **Primitive Obsession** — `Capture`/`Replacement`/`AnalysisContext` type
>   every field `object`; verified not house style (zero `: object` hits in the
>   five sibling modules; `dataloaders.Batch` in this same commit uses
>   `torch.Tensor`).
> - Minor: `hooks.py`'s mid-file `# noqa: E402` dataclass import is layout-only
>   in production code.
>
> ### Clean
>
> Vocabulary on-glossary throughout; no `_Avoid_` terms in added lines.
> `item-swap pair` is pre-existing. Wrapper never instantiated, per-head output
> read at the `o_proj` input, eager confined to `attention_weights` with
> `finally` restore — all per ADR-0001.

## Spec (sub-agent, verbatim)

> **Spec-axis review — 02b Block C scaffold** (`575d612`, worktree `ca-02b`).
>
> ### (c) Implemented but wrong
>
> **1. The dataloader's join silently loses every task whose records carry no
> `instance_id` (STD).** `component_analysis/dataloaders.py:_batches` builds
> `by_id` from `sampling.record_ids` (which documents the `index%06d` fallback)
> but then `kept = {item["instance_id"]: item for item in
> dataset.processed_data if "instance_id" in item}`. Confirmed:
> `data/datasets/std_azaria` test records have no `instance_id`, so `kept` is
> empty, `items` is empty, and every id lands in `dropped_by_tokenization`,
> which `summarize` prints as "dropped because an answer word is not a single
> token" — a false diagnosis. Ticket: "from `sample.json`'s instance ids (never
> the split indices; see ticket 02's `join_on`)". This loader is shared by all
> four sibling tickets.
>
> **2. `--dry-run` aborts on any task with no default segmentation once a causal
> analysis is registered.** `analyze_components.dry_run` calls
> `print_estimates(analysis_context(..., task_instances=None))`; ctx.sample is
> None, so `estimate` → `causal_batches()` raises. Reproduced on the repo's own
> `tinystd` fixture: `RAISED ValueError task 'tinystd' has no causal sample, so
> a causal analysis cannot run on it`, immediately after printing "no causal
> loader". Ticket: "`--dry-run` on the login node prints each registered
> analysis's estimate." Untested because the registry tests use only the
> segmentable `sdr_run`.
>
> ### (a) Missing / partial
>
> **3. Ticket 08 cannot be "one new module plus one registry line".** Its
> receivers are "every circuit head's Q, K and V inputs (K and V per KV group),
> every circuit MLP block's input, and the Readout"; the three primitives reach
> only Component *outputs* (`o_proj` input, `mlp.output`, embedding). No q/k/v
> or mlp-input write exists, so 08 must edit `hooks.py` — the shared file 02b
> exists to keep off parallel branches. Ticket 07 composes cleanly (single-head
> interchange = `replace_forward` fed a corrupt capture). Decide now: add a
> receiver-side write here, or accept 08 touching `hooks.py`.
>
> **4. Ticket `## Comments` is empty and no checkbox is ticked.** The GPU
> checkbox requires the "wall time per forward pass" be recorded in the ticket
> comments; ticket 08 sizes its grid from it. The verification facts (model
> load, +3.2588 gap positive 100/100, 1057-sender replace at max abs error 0.0)
> are not in the ticket.
>
> ### (b) Scope creep
>
> Only `scripts/verify_block_c.{py,sbatch}` (192 lines), unasked but serving the
> GPU checkbox; note `scripts/` importing `tests/` and monkeypatching
> `analyze_components.load_model`. Acceptable. Everything else in the diff maps
> to a checkbox; the `Replacement` position mask, the residual stack and the
> stub under `tests/` are all explicitly requested.
>
> Fix 1 and 2 before the sibling branches cut; 3 is an orchestrator decision; 4
> before the ticket closes.

---

## The author's parallel pass

Done while the sub-agents were being resumed, and kept separate so a reader can
tell the two apart. It found one thing neither reviewer did and three untested
seams.

**Checked and clean.** ADR-0001's one-hook-module property (enforced by a
source-parsing test and a fresh-interpreter probe, both extended to the two new
modules); the prunable wrapper never instantiated; eager confined to
`attention_weights` with a `finally` restore, tested against a raising trace;
per-head output read at the `o_proj` input, never a slice of its output; every
`_Avoid_` term in `CONTEXT.md` grepped across the new files; `--dry-run`
rehearsed in the base environment against the real SDR circuit.

**Found.**

- **The dry run had regressed on STD**, and would have shipped. `dry_run` now
  builds the causal loader for every segmentable task, and STD is segmentable.
  It did not crash: it went through the mechanism dataset class, which dropped
  all 1000 instances and printed a data-shaped diagnosis. The real answer is
  that both pairs these loaders build are mechanism-task properties. Fixed in
  `f126890` by refusing an uncovered task by name with the reason; re-verified
  on the real STD, FAR and SER runs. **This is the same defect the Spec
  reviewer's finding 1 describes from the other end**: the reviewer found the
  broken join, the author found the wrong task. Both fixes are in.
- `ctx.descriptive_batches()`, the only loader tickets 03 and 04 use, had no
  test. Now covered, including the memoization two analyses in a cell rely on.
- The `[batch, seq]` position mask ticket 08 needs had no test; only an
  all-false 1-D mask was covered.
- A single MLP-block replacement had no test of its own — inside the
  replace-everything invariant a write landing one module away would still have
  reproduced the corrupt logits.

---

## Every finding, and what happened to it

The orchestrator ruled on each. Fixes are in `917474d` unless noted.

| # | Axis | Finding | Outcome |
|---|---|---|---|
| S1 | Standards (hard) | `_model` escapes `hooks.py` at four sites | **Fixed.** `device_and_dtype`, `attention_implementation`, `describe` added; all four sites converted; a new test in `tests/test_component_analysis.py` fails if the handle reappears |
| S2 | Standards | `load_analysis_model(attn_implementation=...)` contradicts ADR-0001 | **Fixed.** Argument removed; the model always loads under SDPA and `attention_weights` switches for one trace. No caller passed it |
| S3 | Standards | No fp32 readout seam; four tickets would each build one | **Fixed.** `readout_logits(model, residual)` and `target_minus_distractor`; the GPU check reads its own metric through them; tested against the model's own logits |
| S4 | Standards | "control" in `stub_analysis.py` is an `_Avoid_` term | **Fixed** (found independently by the author, reworded before the report landed) |
| S5 | Standards | Stale `hooks.py` docstring | **Fixed** |
| S6 | Smell | `_num_heads` uses the repo's ignored-marker | **Fixed**, and `_geometry` became the public `geometry(model)` that analyses need anyway |
| S7 | Smell | `object` on every dataclass field | **Fixed.** `Capture` and `Replacement` take `torch.Tensor` annotations, `AnalysisContext` takes `Any` where the type is genuinely polymorphic, with a comment per field |
| S8 | Smell | `causal_batches`/`descriptive_batches` differ only in `ids=` | **Fixed.** Both go through one `_batches(name, ids)` |
| S9 | Smell | Data clump through five `dataloaders` signatures | **Kept.** The clump is the dataset's identity, and the natural type for it is the dataset config the loaders already read. Bundling it would add a type whose only job is to be unpacked one line later |
| S10 | Smell | `run()` re-walks `dry_run()`'s circuit×task grid | **Kept.** The two walks do different things at each cell and `dry_run` is already flagged (ticket 02) as needing a split by a later ticket. Merging them now would make that split harder |
| S11 | Smell | Duplicated nnsight version gate in the two test modules | **Kept.** `tests/helpers.py` is imported by tests that must run where nnsight is 0.5.12, and a module-level skip has to execute before the module's own imports; a shared helper would move six lines and add an import-order constraint |
| S12 | Smell | `Replacement.positions` → `where` | **Kept.** `positions` is the vocabulary of every neighbouring function (`readout_positions`, `query_positions`), and the field is documented at its definition |
| S13 | Smell | `run(..., model=None)` has no caller | **Kept**, and the reviewer is right that nothing passes it today. The spec requires "the CLI and the notebook are thin clients of the same library", and ticket 11's notebook loads the model once in its live section and would hand it in here. If ticket 11 ends up not using it, delete it then |
| S14 | Smell | `find_checks`'s recursive-glob fallback | **Kept, and it is dead on the path that runs.** The GPU job's cell is two levels under the output directory, which the precise pattern matches, so the fallback did not fire in either job. It is there for an output directory nested differently and costs one line; a reviewer who wanted it gone would be within their rights |
| S15 | Smell | Mid-file `# noqa: E402` import | **Kept.** Deliberate: the module's contract is that nnsight is imported inside functions, and the section banner is where the shared passes begin |
| P1 | Spec | Dataloader join loses tasks with no `instance_id` | **Fixed.** The retention rule is applied here by id; `dropped_by_tokenization` holds exactly what was dropped; two tests, one on records with the ids stripped and one asserting the rule still agrees with `DeceptionDatasetLlama` |
| P2 | Spec | `--dry-run` aborts on a task with no causal sample | **Fixed.** `LoaderUnavailable` is its own class; `print_estimates` turns only that into "not applicable" and continues; tested on the tiny non-segmentable task |
| P3 | Spec | Ticket 08's receivers unreachable | **Fixed**, on the orchestrator's decision that the scaffold owns them. Receiver keys in both passes through the same traced forward; the two invariants the orchestrator specified are tests |
| P4 | Spec | Ticket comments empty, no checkbox ticked | **Fixed.** The reviewer read the ticket before the comments were written; all nine boxes are ticked and the GPU numbers, timings and seam notes are in |
| P5 | Spec | Scope: `scripts/verify_block_c.{py,sbatch}` | **Accepted** by the reviewer and kept. It serves the GPU checkbox and `scripts/` importing `tests/` is the price of the stub living under `tests/`, which the ticket requires |
| A1 | Author | STD dry-run regression | **Fixed** in `f126890`; recorded as open question 1 |
| A2–A4 | Author | Three untested seams | **Fixed** in `f126890` |

## Verification after the fixes

The fixes rewrote the core traced loop, changed the dataloader join and moved
the GPU check's metric onto the fp32 readout, so the Slurm job was rerun rather
than its earlier numbers reused.

| | before (`575d612`, job 22105822) | after (`917474d`, job 22106585) |
|---|---|---|
| elapsed | 1:17 | 0:49 |
| mean clean-minus-corrupt gap | +3.2588 | +3.2585 |
| positive | 100 of 100 | 100 of 100 |
| range | [1.5000, 6.1250] | [1.4080, 6.2471] |
| replace-all max abs logit error | 0.0 | 0.0 |
| capture / replace / eager, per batch of 8 | 0.1815 / 0.1871 / 0.1899 s | 0.1845 / 0.1909 / 0.1926 s |

The visibly quantized bfloat16 range is the ordering problem ADR-0001's fp32
requirement exists for, shown rather than argued.

Suites, judged by failure name against the baseline re-derived on `2cbcac4`:

| env | baseline | final | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 657 passed, 21 skipped | 8 failed, 685 passed, 22 skipped | none, same 8 names |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 665 passed, 19 skipped | 8 failed, 711 passed, 19 skipped | none, same 8 names |
