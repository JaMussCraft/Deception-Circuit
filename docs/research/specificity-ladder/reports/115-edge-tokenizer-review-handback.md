# Edge tokenizer factory repair independent review

Status: handed-back

## What changed

**Scoped spec verdict: PASS. Scoped code quality verdict: PASS.** No remaining blocker was found in the narrow edge tokenizer factory repair. The repaired caller uses the exact existing canonical `common.load_tokenizer` with the original parent model and tokenizer revision. It preserves the independent strict tokenizer validation and subsequent actual parent/source/token/map/cohort checks. No science, settings, membership, source-closure policy or model-execution guard changed.

Reviewed candidate: `.superpowers/sdd/plan-a3/edge-tokenizer-fix-source-v2`, relative to baseline commit `74efb4d0481968a1d0138eb1a79b97f302fd3c3b`. Candidate pipeline SHA256 is `4be709a243fa603e285efd5a4f10e2e26252f06c8410718a6d6fe15bce019d71`; candidate test SHA256 is `832f01e2f18faa00f24567e3565a9a2e8a60b2251905bab299ca869750e98d68`. The candidate changes are uncommitted; the baseline commit is not presented as their execution commit. Root owns the subsequent immutable source freeze and actual preparation.

## How verified

Independently hashed the candidate against all ordinary baseline source files: only the declared pipeline and test file differ. Rechecked candidate bytes after the review. The production diff substitutes the canonical factory and its minimal argument namespace. The source admission still authenticates original parent evidence, original streams, actual deterministic preparation, exact compared cohorts/maps/utilities and the matched-build hash. The edge code-hash closure includes its own pipeline, so the repair does not make old prepared artifacts valid under new source.

Read the new tests and raw executable evidence without author handback prose. The tests retain the real production signature guard at the producer boundary, use actual fast tokenizers and reject changed padding configuration. Independent execution goes further: it runs the actual repaired `admit_parent_sources` on the real existing canonical design and invokes the real canonical producer with `output=None`, without mocking that producer or publishing preparation. That complete source/token/map/cohort comparison succeeds on both supported interpreters.

The independent script loads only the pinned local tokenizer at revision `0e9e39f249a16976918f6564b8830bc894c89659`. It checks every original parent mechanism prompt stream against both raw-local and canonical tokenization and the saved tokens. Canonical logical tokenizer identity matches the parent on both interpreters. The base transformer generation uses the already accepted local-snapshot compatibility path while retaining the logical model identifier. EOS padding is added by the canonical loader, without changing prompt tokens.

Negative controls still reject raw-factory missing-padding configuration, changed padding side, removed pad token, changed chat template, instance-level encode override and a wrong requested revision. Factory/cache wrappers require `local_files_only=True`; socket connections are blocked and none are attempted. Offline flags and pinned host threads remain explicit. All project imports resolve within the isolated candidate; the running mask source bundle and its root authority are untouched.

## Execution evidence

CPU tokenizer/source checks only; scheduler job and allocated cluster are not applicable. Both independent commands exit successfully. Expected parent prompt-stream coverage is `40,164` and observed coverage is `40,164` per interpreter; expected saved token coverage is `4,323,124` and observed coverage is `4,323,124` per interpreter. Parent prompt digest and the actual resulting source-admission digest agree across interpreters. All modified-configuration controls reject and network connection count is zero. Exact counts, source hashes and baseline/candidate distinction are in `115-edge-tokenizer-review-evidence/run_manifest.json`, with raw results in `115-edge-tokenizer-review-evidence/mgnp.json` and `115-edge-tokenizer-review-evidence/base.json`.

Commands use `/u/swong2/.conda/envs/mgnp/bin/python` and `/sw/external/python/anaconda3/bin/python3.9` with `-B`, candidate-only `PYTHONPATH`, offline local cache settings and BLAS/OMP/MKL threads pinned. The executable independent check is `115-edge-tokenizer-review-evidence/check_real_tokenizer.py`; raw logs are `115-edge-tokenizer-review-evidence/mgnp.log` and `115-edge-tokenizer-review-evidence/base.log`. Source scope/before-and-after hashes are in `115-edge-tokenizer-review-evidence/pre-source.json` and `115-edge-tokenizer-review-evidence/post-source.json`. Baseline assertion: raw-local, canonical and saved parent tokens match exactly in both environments, while the raw factory fails the unchanged strict configuration guard and the repaired actual source-admission replay succeeds. These are source-integrity checks, not scientific observations or model effect estimates.

## What is NOT done

No application edits, git, RS writes, scheduler access/submission, GPU/large weights, APIs, notebooks or subagents. No broad already-passed edge suite or numerical direction test was duplicated. No edge graph/inventory/prepared artifact was published, no new source commit was created and no model work was admitted. The canonical producer was replayed in memory only. Author handback prose was excluded. The admitted mask pilot runtime, source and authority were not modified.

## Open questions

No unresolved repair-scope question. Root can accept the exact candidate pipeline/test hashes, create its new immutable source revision and perform fresh source-bound canonical/edge preparation as appropriate. Actual edge preparation readiness, measured pilot/cost/resource evidence, root admission and any job submission remain separate from this tokenizer repair acceptance. Preserve the original raw-factory failure and the source-specific review evidence.
