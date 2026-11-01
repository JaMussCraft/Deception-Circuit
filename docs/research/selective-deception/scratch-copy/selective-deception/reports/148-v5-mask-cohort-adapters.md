# V5 frozen masks and historical fixed cohort adapters

CPU preparation only, October 24, 2026. No GPU, model-weight loads, API calls, jobs, notebook execution, git mutations, or new experiment outcomes. Tiny randomly initialized CPU models are used exclusively in unit tests. Historical sources, receipts, checkpoints, suites and caches remain unchanged. This report is implementation evidence, not a new-run receipt.

## Interfaces and exact semantics

New repository modules:

- `evaluation.frozen_head_masks.prepare_frozen_masks(alignment_root, output_path)` and `load_frozen_masks(path) -> {label: mask_dict}`.
- `evaluation.fixed_benchmark_cohort.prepare_fixed_cohort(alignment_root, output_path, cache_output_path=None)` and `load_fixed_cohort(path, dataset) -> dataset_dict`.

CPU CLIs:

```bash
python -m evaluation.frozen_head_masks --alignment-root /projects/beto/swong2/Alignment --output /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/frozen-masks.json
python -m evaluation.fixed_benchmark_cohort --alignment-root /projects/beto/swong2/Alignment --output /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/fixed-cohort.json --judge-cache-output /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/judge-cache-import.jsonl
```

The mask loader returns standard numpy uint8 circuit-to-remove masks. Runtime must apply `knockout_masks(mask, 'finest')`, and use interchange. Gate keys are exactly `attention_blocks`, `attention_heads`, `attention_neurons`, `mlp_hidden`, `mlp_output`; build the model with exactly these pruning gates enabled. Full layers, MLP blocks, embedding gates disabled. Every selected query head has all 128 attention-neuron leaves active. All MLP leaves in the removal circuit are zero. The finest complement opens all MLP support and every nonselected query-head leaf; coarse gates stay open. Four removals plus the shared intact state produce five states.

Geometry is 32 layers, 32 query heads, 128 dimensions/head, 4096 hidden, 14336 intermediate. Old D69 comes from the exact historical `active_heads`, ignoring its misleading ungated `active_mlps` list. Receipt SHA `3b095b5774e7521080de92a7af94243acd76e4df9725541f8ce61f55ff23f525` pins new23/new30 head lists, exports, manifests, identities and checkpoint bytes. Checkpoints are streamed through SHA256, never deserialized. Old-D source SHA `110a7a87bd2bf5dc9abdffa6d0efed20549b0dd4b2319ebfb0f57cdc8126c536` is pinned independently. Required bindings, exact selected sets, whole-head effective support and geometry are checked at load.

Random30 uses Python `random.Random(20261024).sample(range(32), count)` separately for sorted observed new30 layers, without replacement within each layer. All 32 heads are eligible, including original target heads; there is one draw and no effect-based resampling. Actual draw:

```
[[0,11],[2,4],[2,19],[4,1],[6,12],[7,3],[7,5],[7,21],[7,22],[7,25],[8,10],[9,11],[9,27],[9,30],[10,17],[10,31],[12,16],[12,21],[12,23],[13,4],[13,18],[14,2],[16,26],[17,3],[18,9],[19,19],[20,10],[21,8],[24,17],[30,5]]
```

## Historical cohort, safe donor recovery and limits

Sources are exactly the named `D_hko__leaf/sdr/interchange/benchmarks.json` files in `outputs/eval5_format_sdr_coarse` and `outputs/eval5_format_sdr_coarse_lb`. Import version is `format-control-D_hko__leaf-selected-v1`. Safe JSON provides selected items, complete messages/meta/belief, rendered prompts, historical full generations/verdicts, and exact partner IDs. It does not provide every reference-pool item or every screened candidate.

All actually-used donor prompts were recovered through existing offline local CSV/parquet source loaders, plus the instructed-deception honest-twin method. Every historical selected source prompt matched the safe source reconstruction exactly. Every retained recipient's original partner ID was recovered and preserved. The derivative pool is compacted to used donors with an explicit per-recipient partner index; runtime agreed that this is sufficient because this path is interchange only. The full unused historical pool is explicitly marked unrecovered, with original pool size retained. No claim is made to reconstruct all candidate-screen records or the full original pool.

Recipient beliefs and metadata remain exactly the saved historical records. Donor source metadata/messages are preserved; absent donor beliefs remain absent, and donors are not judged. Marking a donor honest documents its historical selection policy, not a new H200 outcome. Runtime must regenerate every intact response and every used donor response on the same H200/model/source/prompt/decoding path, keeping the frozen historical cohort even if new intact outcomes differ. Original native partner selection is retained; this is not the v4 independent replay donor protocol.

The prepared manifest has 371 items, without refill:

| Dataset | Retained |
|---|---:|
| sandbagging | 50 |
| MASK continuations | 28 |
| MASK disinformation | 11 |
| MASK doubling-down known facts | 29 |
| MASK known facts | 37 |
| MASK provided facts | 50 |
| MASK statistics | 16 |
| LB instructed-deception | 50 |
| LB harm-pressure-knowledge-report | 50 |
| LB convincing-game | 50 |

Exact two corrected historical intact exclusions:

- `disinformation/677677c195d3988ad659db48`
- `known_facts/677d5543183c9fbe073aaac5_dup`

Both become `unparsed/evasive:D` through the repaired existing parser. Historical label rows, judge text/errors, generations, corrected labels, exact exclusion reasons, source row indices and full-request fingerprints are retained for every old selected row, including exclusions. No masked-output eligibility filter is applied. Selection provenance explicitly says historical NVIDIA A40; a fresh H200 intact baseline is a separate execution condition. The manifest is not a stock screen cache and has no forged screen key. Row closure, duplicate IDs, absent source donors, prompt drift, historical judge errors and self donors fail closed.

## Versioned cache copy

Original caches remain immutable. Import policy follows existing `JudgeCache` last-write-wins **within each of the two explicitly named files**, and excludes conflicting texts across the named sources. There are zero cross-source conflicts in these copies.

| Named source | SHA256 | Rows | Unique keys | Differing duplicate occurrences |
|---|---|---:|---:|---:|
| format sm | `fce8c5efeee95b8ab7d372df7afd513bc00e4ff7c28f9d4135694c3eaf72fd3f` | 4717 | 4717 | 0 |
| format lb | `feb9bff86df90cb16e0ac205644afe526548a67fc21cb596d39a17019a8900ec` | 3221 | 3168 | 52 |

Imported cache SHA `c1a4c31f3113c029c77700c7f728d3398b32b32f9c2516eb5939b53e19acea42`. Exact full-request fingerprints use the official request key contract including messages, provider, model, kwargs and schema, with `ensure_ascii=False`. The immutable original source copies and the import policy are recorded in the cohort manifest.

Among the 323 original selected nonlocal full-row requests (173 MASK plus 150 LB), 81 exact keys are present in these copies and 242 are absent. Of the 81 hits, 80 cache verdict strings differ from saved historical full-row verdict strings. These include rejudged paraphrases; text difference alone does not imply label disagreement. Eligibility always uses the saved full-row judge text, while prospective cache reuse uses the declared imported last-write policy. Thus this cache import does not pretend to recover a unique original judgment. Historical usage/cost are absent and are never inferred from counts.

## Verification

Assigned focused tests: **31 passed in base Python 3.9 and 31 passed in mgnp Python 3.12**. Tests cover full consumer mask application, real tiny-model all-open full-vocabulary logit identity, exact post-application support, no MLP ablation, whole heads, malformed geometry, missing layers, frozen receipt/checkpoint/source binding tampering, deterministic full-layer random sampling, Unicode metadata and official request fingerprints, exact donor mapping, row closure, error rejection, historical-source drift, derivative tampering and named-cache duplicate/conflict policy.

Both public preparation CLIs completed successfully against real immutable artifacts and local source data. They validate the produced manifests through the actual runtime loader interfaces. No full-suite claim is made here; root/runtime own integration checks. The pre-existing MASK path-location failure is outside this ownership.

Optional V2 CPU scenario preparation has not been added yet; no V2 GPU driver is introduced. Core adapter review and runtime integration take priority. No new scientific outcome claim is made.

## Append-prefix receipt hardening

Runtime/review follow-up added `judge_cache_import.imported_bytes` as the exact byte count of the frozen imported cache. The direct cohort loader checks the nonnegative integer field, rejects aliases of immutable historical source caches, and verifies SHA256 of exactly that prefix, permitting subsequent study-cache appends. Runtime owns validation of appended JSONL entries and exact CLI cache-path binding. Unicode-byte sizing, missing/invalid lengths, altered prefix and valid append have regression coverage. Updated focused suites: **37 passed base and 37 passed mgnp**. The public cohort preparation CLI was rerun successfully against the real source artifacts; 371 selected items and all original exclusions/pairings remain unchanged. No paid calls occurred.

Importer source SHA256: `25183765aa4dccb2f1a1226a662fe1b3a933a208e6eb11cdf862398b6fd8cd43`.

- `fixed-cohort.json`: 4088972 bytes, SHA256 `99add00302460c8df9775177d6d283c3ca10906a1af05d1334bf8cfca052f57e`.
- `judge-cache-import.jsonl`: 5982474 bytes, SHA256 `c1a4c31f3113c029c77700c7f728d3398b32b32f9c2516eb5939b53e19acea42`.
- Frozen imported prefix: 5982474 bytes.
