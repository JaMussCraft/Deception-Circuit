# Task 1: Frozen SDR diagnostic inputs
Status: resolved

Read this first; it is the task contract. Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-deception`. Base 9d9c2a9. Global contract `.scratch/selective-deception/spec.md` in Alignment. Existing API map and exact paths: `reports/01-api-map.md`, `reports/02-current-artifacts.md` in that same directory. Read relevant parts only. You own new `evaluation/selective_diagnostics.py` and `tests/test_selective_diagnostics.py`; no other implementation files without asking root. Root performs git commits. Other agents may work on reports; preserve their changes. No subagents, jobs, API calls, weights loading, or notebooks. Use TDD and karpathy-guidelines. CPU tokenizer use from cached local model is allowed; never download.

## Deliverable

Pure manifest-building and validation helpers for a fixed SDR diagnostic, plus tests. Use existing stored records and matched_honest.instructed_counterpart; never regenerate stored templates from current SPECS. Do not run evaluation. Avoid a large framework. Need canonical JSON serialization/hash, stable row IDs, explicit source records and donor provenance, deterministic selection, no silent truncation/filtering, capped counts. Export exact API and example usage in report for Task2.

## Scientific design

Root chooses 64 distinct scenario clusters from D test records, seed0, balanced over designation polarity × item polarity × template variant where possible. Cluster by semantic scenario/entity/items, not wrapper/record ID alone; all derived views stay in cluster. Disclose data were already outcome-filtered during original dataset creation. Do not further outcome-screen or use matched-honest survivor lists; construct honest twin for all selected records and fail/record structural mismatch before locking selection. Do not silently shrink selection. Use deterministic predeclared structurally valid selection rule; freeze IDs and exclusions before observing new model outputs. Same semantic D/H labels are retained on both recipient policies.

Primary score cells: 64 clusters ×2 recipient policies (stored deceptive D and token-aligned instructed honest H) ×8 conditions =1024. Conditions:
1 intact;
2 core paired honest clean donor;
3 core paired deceptive clean donor;
4 core paired honest corrupt/designation-swapped donor;
5 core paired deceptive corrupt/designation-swapped donor;
6 core deterministically deranged honest clean donor (mismatch stress test, not neutral baseline; group by alignment-compatible length/pad layout);
7 D−F paired honest clean donor;
8 layer/count-matched random-to-core paired honest clean donor (one seed0 mask, exploratory comparator).
For all donors retain original source ID, policy, clean/corrupt designation stream, intended D/H answer, text hash and alignment metadata. Paired-D on D recipient and paired-H on H recipient are identity sanity checks; do not portray as active deletion. All interventions complement composed heads-only masks at leaf granularity; this task need only define condition names and required mask labels. Task2 resolves masks.

Primary scoring uses stored prompt/stem to match circuit discovery. Include an explicitly small changed-order diagnostic: first16 selected clusters ×2policies ×intact/core-H=64 additional score rows, 1088 total. Reverse option order only in known intro and question spans, preserving semantic designation and item answer tokens. If unsafe to implement literal surgery on all actual templates, report NEEDS_CONTEXT with examples; do not generate new templates. Verify transform changed only intended spans and ground truth preserved. Existing clean/corrupt designation swap is not this order manipulation.

Free-generation slice: first16 clusters, balanced/stratified selected before outcomes, both D/H policies and all8 conditions =>256 completions; plus same16×2×intact/core-H using alternative free-response wording =>64; ceiling320 completions with96 new tokens each. Generation prompts must allow coherent refusal; remove forced-answer assistant stem and use frozen minimally changed question permitting answer or refusal. Preserve factual scenario and pressure/honest instruction; use same transformed recipient/policy templates for donors. Alternative format should request natural-language response instead of item-only output, not alter the factual task. Report this prompt transform as a transfer test with intact validity checks, not same as original scoring. Need explicit original/transformed prompt storage and context length validation. Model-mediated classifications deferred to blinded annotation, not regex deception.

## Interfaces

Prefer simple dicts/dataclasses compatible Python3.9. Export build_manifest(records, honest_pool, tokenizer, *, seed=0,n_clusters=64,n_generation_clusters=16,max_new_tokens=96, source_metadata=None) -> dict; validate_manifest(manifest) -> None raising ValueError on invalid inputs/caps/hash/row identity. Export canonical manifest hash helper and optional load/save functions. You may refine signatures only if report clearly specifies them and root approves any effect on Task2. Manifest includes version/config/cluster assignments/rows (score or generation)/limits/source hashes, no model outputs. Include matched-honest pool content hash and dataset/input hash in provenance if provided; Task2 supplies artifact identities. All encoded labels must be single tokens; record actual label IDs; no pad/truncation ambiguity. Root may reduce n for smoke but must record immutable subset rather than choose new data.

## Acceptance

Tests use small real-format fixtures plus fake tokenizer; no production weights. Prove deterministic cluster grouping/sampling; paired counterfactual touches only policy clause; D/H labels preserved; all four donor-policy/designation combinations intended mappings; derangement has no self matches, same structural alignment or explicit failure; option reorder doesn't alter semantic target; generation prompt allows refusal and strips forced stem; label encoding rejects mult-token labels; no silent row loss/truncation; bounded row and token counts; duplicate IDs/tampered metadata rejected; canonical hash stable and changes when content changes. Include meaningful adversarial inputs (missing clause, unsupported template, too few valid clusters, unequal donor lengths). Run focused tests in both envs with BLAS threads1.

Use /u/swong2/.conda/envs/mgnp/bin/python and /sw/external/python/anaconda3/bin/python. Root baseline suites already running; avoid duplicate full-suite run. Full report to `.scratch/selective-deception/reports/03-manifest-implementation.md` with RED/GREEN evidence and exact API. Return <=200 words. No git writes.

## Root amendment after Astra review (before implementation completion)

Enumerate/deduplicate donor-reference generation prompts separately from320 recipient completions, by exact prompt+decoding configuration, with stable reference IDs and per-target donor mapping. Cap donor references320, hence worst-case640 total generated completions×96tokens; dry-run reports actual unique count. Generation default context limit512 including new tokens; preserve score limit128. Carry intended donor D/H semantic labels for actual intact donor validity scores in Task2. No outcome-based filtering. The extra references are real compute and must be in the launch estimate. EOS/short-donor handling must be explicit downstream, not silently treated as equivalent.

## Scientific correction (Astra-reviewed; supersedes paired comparators above)

Self-H retention is mathematically identity, so it cannot test collateral or train preservation. Keep paired core-H/D/clean/corrupt routing conditions. Change condition7/8 to `d_minus_f_deranged_honest_clean` and `random_core_deranged_honest_clean`, using exactly the same fixed deranged donor per source as `core_deranged_honest_clean`, across both D/H recipients. Changed-order and alternative-format two-condition comparisons use intact +core_deranged_honest_clean. Eight conditions,1088scores/320recipient generations unchanged. Recompute unique references and counts; same no-self/alignment guarantees. Metadata explicitly says selectivity comparison is conditional on nonself mismatched-content interchange, while paired core conditions are routing/no-op diagnostics. Freeze donor answer identity and its relationship to recipient truth/deceptive labels so copying explanations can be checked; if words differ, say different/other rather than infer agreement.

Add direct assertions: all three comparison masks receive identical nonself donor IDs/text per source/view/policy; D/H twins share donor; no benign selectivity row uses identity; optional small-view core also nonself; identity rows remain labeled sanity_only. Run focused both envs and real-data tokenizer preflight after change, preserving same64IDs/slice. Review both this scientific correction and prior validation fix in one scoped review. No new broad controls or schemas.
