# V5 independent runtime review — 2026-10-24

Final verdict: PASS for reviewed source and actual cache/cohort contract. Root retains execution approval. No execution authorization. Reviewed report147, guard/client/CLI/benchmark runtime and focused tests. CPU mocked tests only; no live judge/model/GPU/notebook/git work.

## Findings sent to runtime owner

1. Frozen CLI accepts any explicit judge-cache path but does not tie it to the manifest's declared imported copy. Passing an original historical cache allows runtime append; passing an unrelated cache silently changes the recorded reuse policy. Bind the CLI path to the declared import, reject historical source paths and verify the initial import hash, with an explicit append-aware lineage rule if resuming.
2. Guarded structured requests still take the legacy fallback when the SDK lacks `.parse`: this adds a user prompt and omits the numerical schema/reasoning setting while preserving the original request fingerprint. Fail closed in guarded mode; leave ordinary unguarded behavior alone.

## Confirmed behavior

Before transport, a process-safe flock/fsync ledger reserves full supported input context and bounded output; every retry obtains a new reservation. Pending and unknown-charge attempts retain their reservation. Successful authoritative finite `usage.cost` replaces the reservation; no token-count-derived refund is invented. Separate clients share the ledger; SDK retries are disabled. Hidden startup health checks use the same ledger. Guarded identical concurrent requests share one paid task. Paid tasks drain and settle before a propagated stop. Conservative bounds intentionally can stop early if cost is unavailable or concurrency is too high.

Provider maximum-price units and required-parameter behavior agree with [OpenRouter's primary routing documentation](https://github.com/OpenRouterTeam/docs/blob/main/guides/routing/provider-selection.mdx). Complete nonstreaming usage/cost reporting is documented in [OpenRouter usage accounting](https://github.com/OpenRouterTeam/docs/blob/main/cookbook/administration/usage-accounting.mdx). These checks support the implementation's provider assumptions; they are not a live billing test or execution receipt.

Fixed cohort bypasses screening/refill, preserves recipient beliefs and original partner IDs, regenerates fresh intact/used donors, and does not judge donors with missing beliefs. Rendered recipient prompt drift fails before generation. Exactly intact plus four named frozen masks enter `_configs`. Finest knockout preserves nonselected support, independently checked against real historical node_config in report150. Root must still freeze one suite cell/task and actual launch arguments to avoid multiplying this five-state block externally.

Generated responses are saved before judging; partial blocks and missing states are explicit. API errors/budget stops do not become successful suppression. Complete frozen blocks use predeclared new30 headline; incomplete blocks have none. Full fixed denominators retain empty/refusal/evasive categories as raw rows, distinct from confirmed truthfulness. Historical selection hardware is separate from fresh execution provenance.

## Independent tests so far

- `tests/test_frozen_head_masks.py tests/test_fixed_benchmark_cohort.py tests/test_judge_budget.py`: **43 passed in both base and mgnp**; base only known environment warnings.
- `tests/test_benchmark_eval.py`: **71 passed in mgnp**.

These results precede the two requested fixes. Final source hashes and targeted re-verification will be appended after author readiness.

## Final source re-review

Both findings resolved. Frozen runtime now checks the manifest content hash, exact declared import path, non-aliasing with historical source inodes, immutable imported byte-prefix SHA256 and complete valid appended rows on resume. Guarded numerical requests refuse an SDK without structured parse. Structured refusals preserve available billing usage/response ID before being reported as judge failures.

Independent final `tests/test_judge_budget.py tests/test_benchmark_eval.py`: **86 passed in each of base and mgnp**, base with only the three known environment warnings. An intermediate base run caught the author's concurrent RED test for structured refusal; the repaired final test is included in these86.

Final independently read source pins:

| File | SHA256 |
|---|---|
|evaluation/benchmarks/judge.py|b030d1f0fe0599509d579d12ab96d0f23f329ab7b4d616577bdd7c6018b4b6ca|
|evaluation/benchmarks/judge_budget.py|b1de56b89a5416a15db5e4e58bce3a543707f0cd9cef9e90327af6e926b6cd96|
|evaluation/benchmark_eval.py|d46c9fbf86076a4ab6f6367c882e907ea36122e0364161610655d332ff64f2f9|
|evaluate_circuit.py|83d8ee286ae5e7ec32193da4e5398b984105ee18289a7ccc5aab66caf5a325be|
|tests/test_judge_budget.py|c83534cad6099f9c20fa9fadb2d55abd4a2f8b7ca223088cd2ce6195d99f7739|
|tests/test_benchmark_eval.py|d94958cd4eac98c64d15cb91d9eded2cfec9b165da57f217d1e41b512561feb9|

## Actual artifact contract verified

Independently called `validate_study_cache` on the actual regenerated fixed-cohort.json and judge-cache-import.jsonl, then loaded sandbagging through the source-bound cohort loader: **PASS**. Initial imported bytes5,982,474, cache SHA `c1a4c31f3113c029c77700c7f728d3398b32b32f9c2516eb5939b53e19acea42`; cohort SHA `99add00302460c8df9775177d6d283c3ca10906a1af05d1334bf8cfca052f57e`. Report150 records final importer source bindings. No remaining code-review blocker. This approves code/contract review only; paid/GPU execution still requires root's frozen launch receipt, bounded calibration and budget accounting.

## Scoped final native-token and dry-run addendum

PASS. Fixed-cohort token precedence now matches existing stock screening: benchmark-native `new_tokens` takes priority, with generic CLI value used otherwise, followed by exact equality against the frozen historical token budget. Sandbagging's native1024 therefore survives a generic512 CLI setting without changing its protocol. The enriched fixed dry-run display shows per-dataset token budgets, native judges, historical selection paths, exact five states and budget/cache information. It performs no generation or paid request. Root still owns the actual public CLI dry-run against its reviewed ledger.

Independent changed test in both environments: **2 passed** (`test_fixed_cohort_regenerates_intact_and_used_native_donors_without_screen`, generic CLI matching versus smaller than native budget); base only known environment warnings. No new finding. Superseding SHA256: `evaluation/benchmark_eval.py` = `2a1653d7bb1b134daf8bd73fc1824e1fbf0a34ded5b5a4b810c79115776990b9`; `evaluate_circuit.py` = `bb797cf3d39d06fccb2b239461f4a86a8153ab1671fd1e77ecc6740db03ab3af`; `tests/test_benchmark_eval.py` = `8c355d236205d412ac52c74d5fef0111b62cb2b0a75667dcd4b2fcdb1e82d74c`. Judge/client/budget source hashes remain unchanged.

## Actual-model technical proof addendum

PASS for new `evaluation/frozen_runtime_check.py` and its integration before benchmark JudgeClient construction and recipient/donor generation. The proof checks actual model geometry and exact enabled gate families, applies full plus all four finest complements through the real mask consumer, and verifies every extracted mask including complete query heads and open MLP/coarse support. Two fixed-ID dual-stream prefills compare all last-token vocabulary logits exactly, at the already-loaded model's dtype/device, with independent fresh clean/corrupt caches. Cached kwargs match the existing generation engine's prefill path. This is a support and all-open prefill equivalence proof, not a decode-step/behavioral-outcome claim.

The function saves raw gate parameters/final modes and module training flags before mutations and restores them in `finally` on both success and validation failure. The JSON proof records state/support hashes, manifest/model/source/input identities and exact-logit evidence. It loads no second model, generates no response and calls no judge. Failure aborts the benchmark run before the new client is built. Existing root startup health checks remain separately guarded in the shared USD ledger.

Independent `tests/test_frozen_runtime_check.py`: **4 passed in mgnp and4 passed in base**, base with only known environment warnings. Coverage includes actual tiny-model support and identity/restoration, missing gates rejected before forward, injected logit mismatch rejected/restored, and integration ordering before JudgeClient. The actual H200 proof remains to be produced during root-authorized calibration; CPU review does not substitute for that artifact.

Reviewed SHA256: proof module `e4c991a7c5730eb6fef14034af7c84bc4fbc85de510fbd31b11a61fa14bd52eb`; proof tests `a86f11ae482d51535552a431d00d342cb1de09f23aee2d9ea029a8a0d6031342`; superseding `evaluation/benchmark_eval.py` `71c239975a5f8b5366d44e6256aa85b2c71d070d52c1c0d736d3083d949227ed`. No review blocker.

## Scoped screen-cache test classification addendum

PASS. Only `tests/test_screen_cache.py` changed (SHA256 `30ab3b50f6031aca5a1a516ee2c4503ea225624dbdf977b8533132f837bd5611`). The five new flags are deliberately classified: masks/config lists affect ablated passes, fixed cohort dispatch bypasses the stock loader/cache, and judge cache/ledger select verdict storage and spending authorization rather than modifying official request fingerprints. The separate frozen cache binding remains mandatory. This classification does not claim independent stochastic judges always agree; the frozen named import policy addresses that previously disclosed limitation.

The introspected argument-group/nonempty/unclassified assertions remain intact. New tests verify unchanged stock keys for all five flags, fixed-cohort dispatch rejecting all stock screening/cache calls, and BudgetExceeded after genuine partial stock-screen selection propagating without saving a truncated screen. Independent focused execution: **7 passed in each environment** (five flag cases plus dispatch plus partial-budget-stop); omission guard independently **1 passed in mgnp**. Worker reports the full66-case file passing in both environments. No production key/source change and no review blocker.
