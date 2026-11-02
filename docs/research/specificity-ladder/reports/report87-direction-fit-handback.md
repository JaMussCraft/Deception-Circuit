# Direction CPU fitting hand-back

Agent: Codex worker. Work unit C. Status: handed-back.

## What changed

Owned files in the specificity-ladder worktree:

- `component_analysis/a3_direction_pipeline.py`: new CPU-only `fit_from_cache` and private fit helpers. No dispatch, selection or evaluation entry points were added.
- `tests/test_a3_direction_fit.py`: synthetic complete scientific captures, train-only fit/probe checks, mutation rejection and retained-failure checks.
- `docs/research/specificity-ladder/reports/report87-direction-fit-handback.md`: this hand-back, mirrored to the primary research directory.

The fit cache contract is documented in the module. `protocol.fit_cache.capture_identity` freezes the complete source ancestry and physical numeric profile before capture; it excludes membership and design/protocol digests. `_fit_contract(design, protocol)` computes those expectations independently from the actual frozen train source rows, IDs, stream order and candidate sites. It returns complete expected scientific metadata and the array layout. No expected identity is read from loaded cache claims. Strict `read_bundle` plus `capture_reference` binds the capture's exact completion and manifest bytes. Production reads still require the current complete runtime closure; injected fixtures retain explicit injected provenance.

The capture arrays are `geometry{union_site_index}_projection` and `t{task_index}_s{task_site_index}_{condition}` for conditions D, I, H and user_neutral, shaped `[ordered train ID, clean/corrupt stream, head width]`. Coverage must exactly match this layout. The array values and their shapes are covered by the artifact writer's descriptors and completion marker. The source-row digest covers frozen source records, including prompt/token/readout/label fields when present. The stage does not align D/I token positions.

Output is an immutable scientific `a3_direction_fit` numeric bundle with `fit_schema_version=1`, inherited capture ancestry/profile and a strict capture reference. `fit_records` contains each frozen task/site/seed, `valid` and `status`, shared `geometry` reference, `dom`, `nuisance`, `nuisance_cosine`, `image_probe` and `metadata_probe`. Each axis receipt retains bootstrap draws, integer multiplicities, instance/cluster IDs, expanded/unique/effective sizes, array references, raw norm, rank, H center, pullback, variance and fit sigma when fitted. Failed fits retain their reason and bootstrap receipt without an axis. `blocked_task_seeds` records every task/seed without any finite DOM candidate; output status is blocked and downstream stages must refuse incomplete inference. Nuisance fits never add candidate sites or replace failed DOM.

`geometries` references one persisted projection/U/pseudoinverse/spectrum set per unique projection content, reused across axes and seeds. Train activations are referenced by the original complete cache and never copied into the fit bundle. The reviewed fitting functions still own their internal geometry calculation; this module deduplicates persisted geometry, without modifying or monkeypatching those reviewed cores.

Both ridge diagnostics use exactly the recorded integer cluster multiplicities, paired D/I labels and equal stream weight. They retain train-only center, scale, coefficient, unpenalized intercept and regularization of one. Role/length/position features follow the existing frozen six-feature confound definition. Existing multicondition centroid diagnostics remain separate. Expansion is CPU-only and one diagnostic at a time, with a conservative byte preflight from actual cohort dimensions, bootstrap size, dtype and the small head-to-image transform. The image map is associated before row projection to avoid a residual-width row intermediate. Overflow, nonfinite input or byte-limit failure remains a failed diagnostic, never chance accuracy. Validation and assessment scoring do not occur here.

## How verified

Initial owning tests observed fifteen failures at the absent module import. A later rank-deficient transform preflight test observed a missing-keyword failure before the accounting fix; its log is `/tmp/a3-fit-preflight-red.log`. Frozen operational mismatch tests observed five failures before explicit task/stream/seed/site/design consistency guards; log `/tmp/a3-fit-contract-red.log`.

Final commands, from the worktree, were:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_a3_direction_fit.py tests/test_a3_directions.py -k 'not tiny_llama' -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_a3_direction_fit.py tests/test_a3_directions.py -k 'not tiny_llama' -q
```

Both exited zero with 54 passed and two deselected. The suite contains owning fit tests and pure direction-core tests. Logs: `/tmp/a3-unit-c-mgnp-final.log` and `/tmp/a3-unit-c-base39-final.log`. The base interpreter retains its existing pandas/bottleneck dependency warning. The earlier unfiltered core run also passed and incidentally included two existing tiny random CPU Llama forward tests; those used no production weights or GPU and were not rerun. Root explicitly accepted that bounded verification after it was reported.

The owning tests reject validation/assessment split substitutions, IDs, stream order, sites, matched-source fingerprints, numeric-profile drift, missing arrays, and disagreement between the frozen operational protocol and design. Tests check shared DOM/nuisance/probe bootstrap receipts, train-only probe centers against weighted train coordinates, retained zero-DOM/nuisance/projection failures, nonfinite/overflow diagnostics, deduplicated persisted geometry and byte-preflight failure without replacing a valid DOM candidate.

## Execution evidence

No production fitting, model loading, cluster jobs, GPU work, Slurm submission, API calls, notebook execution, scientific scoring or RS changes occurred. These are synthetic CPU software checks; no scientific result or baseline reproduction is claimed, so there is no scientific run manifest or job receipt. The incidental tiny CPU model tests are recorded above.

## What is NOT done

Unit D selection/axis freeze, Unit E inference/statistics, Unit F stage adapter/CLI/wrapper, model captures and production fitting are outside this change. Current canonical preparation does not yet emit `fit_cache`. Root accepted this contract and requires Unit F to freeze its operational extension through canonical prepare into a new artifact lineage; no old protocol or artifact is amended. That future adapter must validate exact runner sink row coverage, gather own-readout heads into the documented array layout, preserve projections/profile/source identity and publish a complete scientific capture. Transient runner sink payloads cannot be passed directly to this fit stage. Runtime profile and source identity must be inherited from the actual frozen capture contract, never fabricated.

The full repository suite was not run. Validation/assessment probe balanced accuracy remains future evaluation using these frozen transforms. No commit was made; the orchestrator owns explicit-file integration.

## Open questions

No new scientific decision is required. The future selection/workload consumers must honor `blocked_task_seeds`, use only `valid` DOM candidates from the frozen sites, treat `nuisance.status == 'fitted'` as nuisance eligibility, and preserve failed probe diagnostics. The workload owner received the exact record and array schemas. Production execution remains blocked until the remaining runtime files and reviewed integration exist.
