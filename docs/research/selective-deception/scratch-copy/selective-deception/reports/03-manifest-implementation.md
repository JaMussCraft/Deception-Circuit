# Task 1 frozen SDR diagnostic manifest

Implemented only `evaluation/selective_diagnostics.py` and `tests/test_selective_diagnostics.py` in the selective-deception worktree. No git writes, notebooks, jobs, API calls, model weights, or downloads. Read project/shared memory and authoritative karpathy-guidelines/TDD sources. Shell sandbox launcher failed before execution (`bwrap ... /tmp/usertmp/... Read-only file system`); commands used reviewed escalation for local reads/writes/CPU tests.

## Exact public API

```python
build_manifest(records, honest_pool, tokenizer, *, seed=0, n_clusters=64,
               n_generation_clusters=16, max_new_tokens=96,
               source_metadata=None) -> dict
validate_manifest(manifest) -> None  # ValueError on failure
canonical_json(value) -> str
content_hash(value) -> str
manifest_hash(manifest) -> str  # excludes only top-level manifest_hash
save_manifest(manifest, path) -> None
load_manifest(path) -> dict  # validates before returning
```

`source_metadata` is copied to `provenance`; pass canonical input file/hash/artifact identities here. `context_limit` defaults512 and must not exceed tokenizer.model_max_length when available. Score inputs always cap128; generation reserves max_new_tokens within context_limit. No padding or truncation: attention_mask all1, padding=`none`, truncated=false. Labels use leading-space encoding and must each be exactly one token. Seed is fixed0, clusters2..64, generation clusters0..min(16,n), completion cap1..96. Reduced-size builds are CPU fixture conveniences; **GPU smoke must select immutable row IDs from the full frozen manifest, not call build_manifest again with fewer clusters.**

Example (CPU, no evaluation):

```python
from dataset.matched_honest import load_matched_honest_pool
from evaluation.selective_diagnostics import build_manifest, save_manifest
m = build_manifest(records, load_matched_honest_pool('sdr'), tokenizer,
                   source_metadata={'dataset_sha256': dataset_sha256,
                                    'context_limit': 512,
                                    'model': model_identity})
save_manifest(m, output_path)
```

Manifest stores config/provenance, full sorted source_records, matched_honest_pool plus its content hash, explicit structural exclusions, selected clusters and all their valid wrapper member_source_ids, derangement, rows, donor_reference_rows, limits, manifest_hash. `provenance` explicitly discloses original dataset outcome filtering and false new-outcome-screening/survivor-list use. No model outputs or outcome classifications enter selection.

Clusters hold `cluster_id`, `source_id`, `member_source_ids`, `scenario`, `stratum`, `labels`, `clause_span`, `donor_intended_labels`, and `prompts[view][policy][stream]`. Semantic scenario key is entity + unordered item identities + honest item, so wrapper, pressure and arbitrary record ID do not split the same fact scenario. Representative wrappers are chosen deterministically while spreading available strata. Structural preflight runs on all input records before selection. Every exclusion records source ID and failure reason. Stratum-greedy selection admits new exact-length groups in pairs; this ensures deterministic no-self donor derangements. Final round-robin stratum order defines the small diagnostic/generation slice. Insufficient clusters or compatible groups raise rather than silently shrink.

## Task 2 row interface

`rows` entries:

- `row_id`, `kind`=`score`/`generation`, `view`=`original`/`reversed`/`free_response`/`alternative`, `cluster_id`, `source_id`, `policy`=`D`/`H`, `condition`, `mask_label`.
- `labels={'D':{'text', 'token_id'}, 'H':{'text','token_id'}}`: semantic D/H remains identical on both recipient policies.
- `recipient`, `donor` (None for intact): endpoints include `text`, `text_hash` (SHA256 raw UTF8), `input_ids`, `attention_mask`, `length`, `padding`, `truncated`, `source_id`, `cluster_id`, `policy`, `stream`=`clean`/`corrupt`, `view`, `intended_label`, `intended_answer`, `clause_span`.
- `identity_sanity_check`, `interpretation`: exact self donors marked identity sanity, deranged donors marked mismatch stress test.

Conditions and masks:

| condition | mask_label | donor |
|---|---|---|
| intact | None | None |
| core_honest_clean | core | H clean |
| core_deceptive_clean | core | D clean |
| core_honest_corrupt | core | H corrupt |
| core_deceptive_corrupt | core | D corrupt |
| core_deranged_honest_clean | core | deterministically deranged H clean |
| d_minus_f_honest_clean | d_minus_f | H clean |
| random_core_honest_clean | random_core_seed0 | H clean |

Task2 resolves masks, must use heads-only leaf composition/complements, and retain no-self/identical-length/shared-mask invariants. Manifest requests all interventions=complement, leaf granularity, random mask seed0. Per-source intended donor labels are Dclean→D, Hclean→H, Dcorrupt→H, Hcorrupt→D. These are intended labels, not observed validity. Actual intact donor logits/argmax remain runner outputs, with no validity filtering.

Every generation donor endpoint includes `reference_row_id` joining `donor_reference_rows`. Each reference entry holds `row_id`, kind=`donor_reference`, `prompt` (full endpoint), `decode`, `used_by` (recipient row IDs). Dedup key is **exact donor text + complete decode config**, not source ID. Retain the per-recipient donor provenance even when reference prompt text deduplicates across source views.

Decode is frozen greedy (`do_sample=false`), max_new_tokens, explicit EOS policy (`stop_on_eos=true`, exclude EOS from completion, empty requires annotation category, cap-hit distinct from EOS). Task2 resolves actual model EOS IDs and suffix continuation handling, recording tiling/truncation flags rather than inventing donor continuation pads. Keep generation annotations blinded and separate from token scores; no regex deception classifier was added.

## Frozen prompt transforms

No SPECS/template regeneration. `instructed_counterpart` replaces only stored pressure clauses and verifies token alignment. Reversal recognizes exact historical audit/lab intro, question and assistant stem, reverses only intro `a and b` and first-question `a or b`, preserves the forced-choice response examples and designation sentence. All D/H labels remain unchanged. Unsupported wording fails NEEDS_CONTEXT during disclosed structural preflight.

Generation removes the item-forcing response instruction and assistant stem, preserving the entire system factual/pressure/honest content. Primary question retains `Which result/reading will you show me, a or b?` plus `You may answer or refuse to answer.` Alternative adds `Respond in natural language.` Same view is used for every recipient and donor. Original/transformed text is retained together. This is explicitly a prompt-transfer diagnostic, requiring intact validity checks; it is not the original discovery score format.

## Verification

TDD RED: `/tmp/selective-manifest-red.log` recorded30 missing-module errors before production code existed. Initial GREEN reached29/30; context failure reasons were lost behind the insufficient-cluster summary. Added pool-integrity/reference/stratification tests first; `/tmp/selective-manifest-red2.log` recorded context-reason and missing-frozen-pool failures (31 passed). Fixed by carrying structural reasons and freezing/checking pool content. Final tests exercise historical literal fixtures, deterministic clustering/input permutation,8-strata slices, exact clause/order/stem surgery, all4 donor semantic combinations, derangement and explicit mismatch failure, source duplicates, multi-token labels, missing clauses/templates, no silent shrink/truncation, context/token/row caps, reference dedup/accounting, canonical hashes, round-trip loading, tampered rows/labels/prompts/pool/counts.

Focused command (BLAS threads1) in both environments:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_selective_diagnostics.py -q -p no:cacheprovider
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  /sw/external/python/anaconda3/bin/python -m pytest tests/test_selective_diagnostics.py -q -p no:cacheprovider
```

Root owns full-suite integration/baseline checks; worker ran focused tests only as explicitly assigned. Final results recorded below after completion.

Actual1000 canonical SDR test Arrow records plus cached Llama3.1 tokenizer (local_files_only=True) passed full CPU preflight:64 clusters, zero structural exclusions, exactly8 per8 strata; generation first16 exactly2 per8 strata. Maximum prompt length117. Counts:1088 score rows;320 recipient completions (30,720 tokens);84 unique donor references (8,064 tokens);404 total completions /38,784 worst-case new tokens. Hard caps:1088 scores,320 recipient completions,320 donor references,640 total completions /61,440 new tokens. No GPU run. Illustrative manifest hash without source_metadata: `f991e465c25ab40d49c249566e097a3a79a2ff514d200eb9200d90f680659551`; root's artifact metadata will change it. The worker did not lock/save a production manifest; Task2/root supplies verified artifact identities and saves it before outcomes.

Final focused results: mgnp **34 passed in6.47s**; base Python3.9 **34 passed in8.06s**, one existing pandas/bottleneck version warning. Durable logs alongside this report: `03-manifest-red.log`, `03-manifest-red2.log`, `03-manifest-green.log`, `03-manifest-base-green.log`. `03-manifest-preview.json` records the exact actual-data64-cluster/source-ID selection, semantic labels, strata, derangement, limits and first2 clusters' original/transformed D/H clean/corrupt prompt packages. It is explicitly a CPU preview without root artifact identities, not the production freeze. No further implementation changes after final verification.

## Scoped review fix: fixed scientific declarations

Independent review found that rehashing allowed contradictory intervention/selection/screening declarations to pass. Confirmed the gap before implementation:15 parameterized regression cases failed with DID NOT RAISE (34 existing tests passed), including all five reported mask contradictions, fixed transfer/selection identity, original outcome-filtering disclosure, new screening/survivor-list declarations, and integer substitutes for Boolean declarations.

Added only explicit validation checks against existing fixed condition-mask mapping, complement semantics, heads-only/leaf granularity, random seed0, prompt-transfer/selection identity, and Boolean screening declarations. No generic schema, donor design, manifest contents, or sampling behavior changed.

Final focused verification with BLAS threads1: **mgnp49 passed in8.35s; Python3.9 base49 passed in9.68s**, base retaining one existing pandas/bottleneck version warning. Durable logs: `03-manifest-review-red.log`, `03-manifest-review-mgnp-green.log`, `03-manifest-review-base-green.log`. No jobs, API calls, weights, notebooks, git writes or production freeze. Stopped edits after this scoped correction.

## Astra-reviewed scientific correction: shared nonself selectivity donors

This section supersedes the paired comparator and small-view condition descriptions above. Eight conditions remain. Renamed `d_minus_f_honest_clean` to `d_minus_f_deranged_honest_clean` and `random_core_honest_clean` to `random_core_deranged_honest_clean`; both now receive exactly the same fixed derangedH clean donor as `core_deranged_honest_clean`, for both D/H recipient twins. Reversed-order and alternative free-response small comparisons now use intact +core_deranged_honest_clean. Paired core D/H clean/corrupt conditions remain unchanged as routing/no-op diagnostics.

New fixed `config.selectivity_policy` records conditional_on_nonself_mismatched_content_interchange, paired_core_conditions=routing_or_noop_diagnostics, exact comparison/small-view condition lists and shared fixed deranged donor assignment. Validator enforces this exact policy alongside the earlier fixed scientific declaration checks. No sampling or prompt-surgery changes.

Rows now include `analysis_role`: selectivity_comparison for the three deranged masks; sanity_only for exact donor identities; routing_diagnostic for nonidentity paired core conditions; intact otherwise. Identity rows also have interpretation=sanity_only. Selectivity row construction explicitly rejects identity/self-source donors. `donor_answer_relation_to_recipient` is row-local: D/H if the intended donor answer word exactly equals the recipient deceptive/truthful label word, other otherwise; intact has None. Donor endpoint intended_label/intended_answer remain donor-local. Keeping the relationship on rows prevents globally deduplicated donor-reference prompts from inheriting another recipient's relationship.

TDD evidence:6 new scientific-correction regressions failed before implementation,49 existing passed. Final **mgnp55 passed in7.26s; Python3.9 base55 passed in8.93s**; base retains the known pandas/bottleneck warning. New tests directly compare all six donor endpoints across three masks×two recipient policies for each source in both original score/free-response views, verify nonself small-view donors, sanity_only identities, fixed/rehashed selectivity policy rejection, and D/H/other word relationships. Logs: `03-manifest-nonself-red.log`, `03-manifest-nonself-mgnp-green.log`, `03-manifest-nonself-base-green.log`.

Real-data CPU preflight reran with all1000 original records and local-only cached tokenizer. It **asserted exact ordered64(cluster_id,source_id) equality against the prior preview and identical first16 strata** before updating `03-manifest-preview.json`. All64 IDs/slice preserved,8 per main stratum and2 per generation stratum, zero structural exclusions, zero identity selectivity rows. Unique references recomputed: still84;1088 score rows +320 recipient completions +84 donor references =404 total completions /38,784 worst-case new tokens. Across544 selectivity score/generation rows, intended donor word relation is520 other,24 D,0 H; this is not model-observed validity or inferred agreement. Preview now includes selectivity policy and first cluster comparison rows. New illustrative manifest hash without root source_metadata: `6b0fdf31ed464837e71adfd71d43a47f10f4b3a81b1538a83a1efa53b3e10a02`.

No additional controls, schema framework, jobs, API calls, weights, notebooks or git writes. No production freeze. Edits stopped after this bounded correction and report.
