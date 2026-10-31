# Ticket 15 — code review (knockout completeness sweep)

`mattpocock-skills:code-review` against the fixed point `4ba2877`, on commit
`bd8703e` ("Knock out every Component of the model to see what the circuit
misses"). Both axes ran as independent parallel sub-agents. Both handbacks
failed, as the brief predicts; both reports reached the implementer by message
after a resend request, and the orchestrator forwarded both with calls. **The
review is independent of the author.** Fixes are in `548ea61`.

## Standards

Verbatim from the Standards sub-agent:

> Ticket 15 standards review (diff 4ba2877...bd8703e): no documented standard is broken; seven judgement calls, none blocking.
>
> **Standards met:** both new flags start with `--knockout-`; `knockout.sweep_rank` and `knockout.sweep_clears_threshold` follow `<namespace>.<bare name>`, sit on circuit rows only, and declare coverage through `ctx.declare_coverage`; `sweep.png` has its JSON twin `sweep.json`; `--dry-run` writes nothing, and a test checks it; nnsight is imported only in `hooks.py` (the function-local `hooks` import follows the existing pattern); the model tests are in the version-gated `test_knockout_model.py`; tests check written files and returned numbers, not hook wiring; shared files only gain additions (README, check_cell, one notebook cell); ADR-0002: `mean_drop` keeps its native sign, the |drop| ranking is stated in `metric.ranking` with `signed_rank` beside it; no glossary words to avoid appear.
>
> **Judgement calls:**
> 1. Duplicated code: `knockout._label_of` re-implements `path_patching.label(key)`. Reuse it, or move it into `components`.
> 2. Unclear names: `_label` gives `L17 H25` and `_label_of` gives `head.17.25` in one module; `sweep.png` ticks say `L17 H25` while its JSON twin and the review view say `head.17.25`.
> 3. Repeated lookups: `resolve_scheme(getattr(ctx.cli, 'knockout_scheme', SCHEME))` three times and the sweep-flag `getattr` twice; small helpers would gather them. `sweep_threshold(ctx)` has no docstring.
> 4. Unneeded options: `sweep_payload(..., top=10)` has no caller passing it; per-row `kv_group` is not asked for and nothing reads it.
> 5. Hidden mutation: `_write_sweep(..., updates)` mutates the caller's dict.
> 6. Inconsistent forward count: help says "About 1056 forwards per batch", README and `estimate()` say 1058.
> 7. Repeated arguments (minor): `circuit`, `task`, `threshold` travel together into `sweep_payload`, as in `payload` and `family_payload`.

## Spec

Verbatim from the Spec sub-agent:

> Ticket 15 spec review (bd8703e): the code matches the ticket and the guidance, with nothing blocking and four minor gaps.
>
> (a) Missing or partial
> 1. "about 1057 Components": the sweep covers 1056 because the embedding is excluded, but `sweep.json` never says so. Suggest an `excludes` or `note` field.
> 2. "`knockout.sweep_rank` and a flag": `sweep_rank` ranks by |drop| beside `knockout.rank` (signed); only `metric.ranking` explains it. The threshold's reasoning is only in `--help` and a code comment; the JSON records just its units.
> 3. "`--dry-run` sizes the sweep": `--help` says 1056 forwards per batch, the README 1058 (correct). The `estimate()` arithmetic is right and counts nothing twice; the calibration fields are in place.
>
> (b) Not asked for (small, justified): `THRESHOLD_LADDER`/`threshold_counts`, per-row `z`, `strongest_outside_circuit`, rejecting a negative threshold, the notebook cell, the `check_cell.py` entry.
>
> (c) Weak spot
> 4. The flag ignores significance: a fixed 0.1-logit cut over 1056 Components can flag a weak head at z about 1.4, and it was calibrated on SDR nls0.3 only. Worth a sentence in the ticket's Comments.
>
> Checked and correct: the circuit's singles are read from the sweep's own forwards through `Effects.restrict` (bit-identical by construction); a test shows `knockout.json` identical with and without the flag; coverage declared and asserted at the CLI seam; sweep columns on circuit rows only, even at threshold 0; sign is knockout's; ranking by |drop| with `signed_rank` mirrors ticket 09; `sweep.json` as the PNG's twin is a reasonable reading; all four requested tests exist at seams.
>
> Low-risk note: a knockout rerun into a cell without the flag leaves the old `sweep.json` on disk, and the review view still renders it, as the path-patching sweep does.

## Dispositions (orchestrator's calls applied)

| finding | outcome |
|---|---|
| Standards 1, duplicated label | **Fixed.** `knockout` imports `path_patching.label` as `component_label`; `path_patching.py` is not edited (ticket 14 owns it). |
| Standards 2, two spellings | **Fixed.** Every sweep output, PNG ticks included, spells `head.17.25`; the circuit-only charts keep `L17 H25` under `_short_label`, whose docstring says which is which. |
| Standards 3, repeated lookups | **Fixed.** `scheme_of(ctx)`, `sweeping(ctx)`; `sweep_threshold` has a docstring. |
| Standards 4, `top` and `kv_group` | `top` became the constant `STRONGEST_OUTSIDE_TOP`. `kv_group` **kept** by ruling (the notebook may use it). |
| Standards 5, hidden mutation | **Fixed.** `_write_sweep` returns the columns and `run` merges them. |
| Standards 6 / Spec 3, forward count | **Fixed.** One count everywhere: 1056 Components + 2 shared passes = 1058 forwards per batch on Llama-3.1-8B. |
| Standards 7, data clump | **Kept** by ruling, as a judgement call; it matches `payload` and `family_payload`. |
| Spec 1, embedding exclusion | **Fixed.** `sweep.json` has `excludes`, and the dry-run line says so. |
| Spec 2, ranking and threshold reasoning | **Fixed.** `sweep.json` has `head_table_columns` (sweep_rank by \|drop\| over the model versus knockout.rank signed within the circuit) and `threshold_justification`; `docs/component-roles.md` gains a paragraph beside ticket 09's sweep note. |
| Spec 4, significance | **Recorded** in the ticket's Comments; `sweep.json` also carries `threshold_is_not_a_significance_test`, pointing at `z` and `threshold_counts`. |
| Spec (b), extras | **Kept** by ruling. |
| Spec, stale `sweep.json` | **Documented** in the README beside ticket 13's whole-namespace warning. |

Tests after the fixes: the touched base-env modules (`test_knockout_sweep`,
`test_knockout`, `test_knockout_families`, `test_review`, `test_check_cell`,
`test_component_analysis`) 120 passed; the mgnp knockout modules
(`test_knockout_model`, `test_knockout_sweep`, `test_knockout_families_model`)
52 passed. Full-suite results are in the ticket's Comments.
