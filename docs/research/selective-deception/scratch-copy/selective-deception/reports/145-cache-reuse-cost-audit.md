# Cache reuse and grader cost audit — 2026-10-24

Scope: CPU-only source/JSON metadata audit. No API/network/model calls, jobs, changes to datasets/caches/code, or new experiment outcomes. Only this report written. This follows the user's $20 approval and request for proportional preparation; it does not consume that allowance.

## Answer

Skipping deterministic grader fixes does not inherently save OpenRouter spend: the existing raw verdicts can be parsed again for **$0**. Cost comes from obtaining missing generations/verdicts or silently triggering a new screen. For a descriptive fixed-cohort pilot, use existing selected items and their saved full-model outputs; repair deterministic labels offline, exclude selected MASK D cases, and explicitly retain a smaller cohort rather than refilling it. A broad shared-cache feature is unnecessary: one fresh matched suite already shares a judge cache.

A complete repaired replay of the original candidate-screening process is **not** recoverable from the documented artifacts alone. Missing rejected/overflow candidate records prevent exact reselection/refilling, even though the original judge cache may retain their opaque verdicts. Defer that comprehensive rescreen unless a confirmatory claim requires it.

## What is saved

`evaluation/benchmark_eval.py:351` Screen saves selected items/prompts/full token blocks/full label rows, plus limited honest reference items/token streams. It does not save all candidate records. `run_screen` (`:650`–`:809`) retains individual deceptive rows only until the target fills and honest references only until the pool fills. Rejected/unparsed/overflow candidates survive as aggregate `screen_labels`/`screen_raw` counts, not an ID → prompt → generation → verdict mapping. `screen_cache.py:478` serializes that Screen, not a separate candidate ledger.

Safe JSON checks of existing four-cell format suites:

* `Deception-Circuit/outputs/eval5_format_sdr_coarse/cells/D_hko__leaf/sdr/interchange/benchmarks.json` (also H_hko, F_hko, D_minus_F_hko): per dataset `items`, `prompts`, `configs.full.generations`, and `configs.full.labels` with `{label,raw,judge_prompt,judge_text,judge_error}`. These contain the **selected** screen cohort, not every screened candidate. Every selected MASK row has saved judge text.
* `Deception-Circuit/outputs/eval5_format_sdr_coarse_lb/cells/D_hko__leaf/sdr/interchange/benchmarks.json` (same other cells): selected LB cohort and same label schema. Existing full output rows =50 per LB dataset; screened/judged counts instructed100/97, harm-pressure300/300, convincing191/191.

MASK coverage from that historical full row (one cell, all four cells reuse the same screen):

| split | screened/judged | saved selected | selected raw D | retained if D excluded |
|---|---:|---:|---:|---:|
| continuations |132|28|0|28|
| disinformation |97|12|1|11|
| doubling_down_known_facts |70|29|0|29|
| known_facts |125|38|1|37|
| provided_facts |274|50|0|50|
| statistics |93|16|0|16|
| total |791|173|2|171|

`provided_facts` aggregate screen reports134 deceptive candidates but saves50 selected; this alone demonstrates missing overflow records. One D exists in that aggregate but none among selected, so dropping selected D rows cannot reconstruct all original screen decisions. Disinformation/known_facts D exclusions can be applied exactly to the retained cohort without buying any verdicts or filling replacements. Do not infer that a refusal or D should be credited as truthful correction; report refusal/nonassertion separately.

## Screen sidecars and hardware

Existing `outputs/_screens` contains26 JSON sidecars: LB9 (three per dataset), MASK12 (two per split), sandbagging5. Every LB and MASK sidecar is **NVIDIA A40**; only sandbagging has H200 entries. n50 MASK sidecars (paired .pt files share these stems):

* `outputs/_screens/mask__continuations/68f1cf29ee8bc0fb940dea0d.json`
* `outputs/_screens/mask__disinformation/4084c098d1e56b0cb098e30b.json`
* `outputs/_screens/mask__doubling_down_known_facts/f2bf6ade8708557c9b112503.json`
* `outputs/_screens/mask__known_facts/f06bb347408f33ebdc5f8b45.json`
* `outputs/_screens/mask__provided_facts/8b1ae7bb3ee1f94f0d19a7af.json`
* `outputs/_screens/mask__statistics/86a2b1a5270de4a4a55d8320.json`

These n50 MASK sidecars specify torch2.11.0+cu128 / transformers5.13.0, honest reference pool, OpenRouter judge `openai/gpt-4o` (binary) / `openai/o3-mini` (statistics). Other older n40 sidecars use unprefixed gpt-4o/o3-mini, so they are different request identities. LB sidecars list `anthropic/claude-haiku-4.5` and `anthropic/claude-sonnet-4.5`; saved dataset judge specs disambiguate harm-pressure=Haiku, instructed/convincing=Sonnet.

The cache key hashes adapter source (`screen_cache.py:101`–`:140`), hardware, software versions and generation settings. A parser fix invalidates a stock screen; merely rerunning the evaluator can therefore **spend money unnecessarily** despite an offline reuse path. Do not silently relabel a cache hit under its old provenance or bypass its key. A narrow reviewed importer should preserve original artifact hashes, record parser revision and exact excluded row IDs, and mark a fixed-cohort derivative explicitly. If moving to H200, generate an H200 intact baseline on the frozen prompts; mark A40-based cohort/donor selection as historical and do not claim an identical historical protocol. This still costs GPU time and possibly new judgment if intact capability is rechecked. An A40 matched run more directly preserves the stored screen hardware.

## Which corrections need calls

* Empty-generation guard: $0 deterministic, inspect saved generation before the judge verdict. It may also avoid paying a new API call for a fresh empty response. Full harm-pressure selected deceptive cohort is not admitted through this honest-empty bug, but honest reference-bank empties/labels deserve checking before claiming complete screen repair.
* MASK D treatment: $0 reparse from `raw`/`judge_text`, exclude the two saved selected D rows prospectively. Recompute every config denominator on the identical reduced cohort. Complete repair/refill of all candidate decisions is unavailable from saved selected rows.
* LB “correct” guard: $0 reparse saved successful judge text/generation. This can affect old rejected candidates absent from selected outputs, so selected-cohort repair cannot establish that the full screen was rebuilt correctly.
* Judge noise: one matched invocation already uses `benchmark_eval.py:1436` cache above the cells. Freeze that cache; no cross-project service or broad shared-cache feature required. If importing historical caches, choose a single documented source/precedence and refuse or explicitly resolve conflicting keys; do not concatenate arbitrary suites and pretend that recovers a unique original judgment.

Existing `rejudge_benchmarks.py` is **not** an offline parser-fix tool: its target is failed API rows and it may buy missing verdicts (`evaluation/rejudge.py:1`–`:30`). Do not run its non-dry mode to accomplish deterministic corrections. The needed narrow operation is parsing existing text and recomputing summaries on copies, without invoking JudgeClient.

## Actual dollars cannot be recovered

`outputs/eval5_format_sdr_coarse/judge_cache.jsonl`:4717 rows/4717 unique keys, no differing duplicate texts. `outputs/eval5_format_sdr_coarse_lb/judge_cache.jsonl`:3221 rows/3168 unique keys,52 occurrences where the duplicate key's text differs from the previous value. This is consistent with historical repeated judging/rejudging; freeze one known cache version rather than treating append order as a scientifically unique verdict.

Both caches store **only `{key,text}`** (`benchmarks/judge.py:141`–`:154`). Their keys hash the full request (`:98`); the cache omits readable request, model, usage, cost, response ID and timestamp. Model IDs can be recovered for saved dataset entries/sidecars, but cannot generally be assigned to every opaque orphan cache key.

All eight saved `benchmarks.json` files in these two four-cell suites were recursively inspected for `usage`, `cost`, `total_cost`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `response_id`: **none present**. JudgeClient `_call` discards the provider completion after extracting text (`judge.py:196`–`:208`); `stats` records cache hits/writes/path/concurrency only (`:322`). Therefore no actual-dollar estimate follows from cache counts. A current quote would need new pricing lookup and token counts, while actual historical dollars need provider accounting; neither was accessed here. The user's $20 cap remains usable, but it should be enforced prospectively with small batches and recorded usage/cost rather than inferred from GPU authorization or lookup counts.

## Proportional next step

Keep preparation narrow: deterministic fixes + mocked parser tests + CPU-only derivative-cohort audit, no paid rescreen. Use one frozen common cohort/cache for intact/new30/oldD69/new23, with171 historical selected MASK items if accepting the described pilot limitation. Judge only genuinely new nonempty generations whose exact request misses the chosen cache. Preserve raw verdicts alongside corrected labels. Broader candidate rescreen/refill and confirmatory screening can wait; skipping the parser fixes would retain known scoring errors without being the source of meaningful API savings.

Audit limitation: safe JSON/source inspection establishes schema/coverage; .pt Screen objects were not deserialized. Automatic approval review rejected unrestricted pickle deserialization (`torch.load(weights_only=False)`) because it can execute embedded code, and rejected an initial broad sidecar-print command due to possible content exposure. Both were replaced by safe schema/count-only JSON/source checks; no requested conclusion remains blocked and no additional approval is needed.
