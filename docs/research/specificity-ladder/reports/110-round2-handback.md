# Shared operational authority round-two closure review

Status: handed-back

## What changed

Review only; no reviewer implementation edits. **Scoped B2 spec verdict: PASS. Scoped B2 code quality verdict: PASS.** The inherited-initializer gap is addressed with no remaining finding in this bounded repair. B1 allocation binding and B3 byte witnesses remain accepted from `110-round1-closure.md`; their implementation boundaries were unchanged. This completes the scoped authority findings, not whole numerical Unit F acceptance or production admission. Original failure reports and probes remain preserved.

Exact accepted workload SHA is `7726495fb2388491f56f442dd404e151f72d4eedd3bbf1106e7d10e70ead154a`; runtime remains `bb54a6076c4edf507bed43abaa256cd2ce3a6cded85a4315b4a3c86d1f8047f1`; runtime tests are `722886ac7a2190f4ae72bbf563f3c8c252bf2715babab94ac5963ec47e8d5250`. All refreshed frozen package hashes matched independently. Full hashes and results are in `110-round2-authority-evidence/receipt.json`. Reviewed source is the amended `.superpowers/sdd/plan-a3/unit-f-review110-round2.diff` and adjacent hash manifest, superseding the earlier unamended round-two freeze.

The frozen JSON dict/list constructors now seal successful initialization in slots. Repeat initialization rejects even when the original container is empty; ordinary attribute assignment/deletion cannot reset the seal, and no mutable instance dictionary is exposed. Constructors recursively own mutable children. Ordinary dict/list subclasses are normalized. Exact frozen instances are reused only after successful initialization; uninitialized raw instances are reconstructed into separate sealed containers. JSON and copy behavior remain compatible with the cached consumers.

## How verified

Inspected the exact repair diff and revised frozen source. Kept source-dependent execution paused during the author amendment, then bound every test to the revised source/package. Author report and handoff prose were excluded.

Independent tests in `110-round2-authority-evidence/test_independent_authority_round2.py` exercise the original nested dict initializer, same-length key-list initializer, empty dict/list initializers, ordinary seal reset/deletion attempts, direct constructors, ordinary subclasses, tuple normalization, external mutable-child ownership, JSON/copy/deepcopy, top-level replacement checks and common public mutator operators. Raw uninitialized exact frozen instances become separate sealed values; changing the original raw object cannot change the consumed value.

The full cached reservation API rejects every initializer attack while retaining unchanged-context execution authority, and the validator-count sentinel shows that immutable proof reconstruction does not recur on reuse. Existing affected owning tests also cover live-ledger reconciliation and mapping successors. Tiny frozen-index/boundary tests confirm that the new container construction preserves immutable backing checks and bounded cache usage; those checks do not establish numerical packing effectiveness or whole runtime finality.

## Execution evidence

CPU fixtures only; scheduler job/cluster not applicable. Independent tests pass thirty-seven cases per interpreter. Affected owning tests pass twenty-one cases per interpreter; the separate tiny index/boundary selection passes three cases per interpreter. All commands exit successfully. Exact counts, source identity and probe digest are in `110-round2-authority-evidence/receipt.json`. Raw outputs are `110-round2-authority-evidence/mgnp.log`, `110-round2-authority-evidence/base.log`, `110-round2-authority-evidence/owning-mgnp.log`, `110-round2-authority-evidence/owning-base.log`, `110-round2-authority-evidence/index-mgnp.log` and `110-round2-authority-evidence/index-base.log`.

Commands use `/u/swong2/.conda/envs/mgnp/bin/python` and `/sw/external/python/anaconda3/bin/python3.9`, pinned BLAS/OMP/MKL threads, disabled bytecode, `-m pytest -q -p no:cacheprovider` and dedicated basetemp directories. Independent target: the preserved probe file. Owning target: `tests/test_a3_direction_runtime.py` filtered by `public_reinitialization or frozen_construction or validated_inventory or mapping_successor or full_authority_context or context_mint_reconstructs`. Index/boundary filter: `completed_packing_proof_reuses or atomic_reconciliation_rechecks`.

Baseline assertion: unchanged inventories remain equal after JSON serialization and authorize unchanged cached reuse; the previously accepted initializer attacks now raise without changing contents. Original external mutable child changes do not alter constructed frozen values. Raw uninitialized input mutation does not alter the normalized consumed value. These are authority fixture assertions, not scientific effect estimates. No scientific row panel or scientific `run_manifest.json` exists for this review; the receipt records the exact source files.

## What is NOT done

No source edits, git, RS writes, scheduler reads/submission/mutation, GPU/large weights/API work, notebooks or subagents. No broad suite or long native numerical run was repeated. B1/B3 were not broadly rerun because this repair leaves their boundaries unchanged; the scoped affected tests cover the repaired shared JSON container seam. No production admission is granted. Numerical proof effectiveness/cost, full-count native execution, fit/selection/power/reporting finality and consumer science remain separately owned review work.

## Open questions

No remaining B2 repair-scope blocker. Root can combine this scoped closure with prior B1/B3 acceptance and independently completed numerical runtime evidence. A fresh full numerical run and its separate review remain required before combined Unit F acceptance. Preserve all earlier failed-source evidence and this exact accepted-source package; root alone coordinates commits and production admission.
