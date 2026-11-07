# Hand-back: Direction selection independent review

Agent: Codex review worker. Ticket: Unit D of the direction integration plan. Status: handed-back.

## What changed

Review only; no application or test source edits and no git commands. Final scoped closure: all three reported Unit D blockers are closed. The per-axis reader now requires exactly the four fitted axis fields before loading arrays and merges only those named fields; shared projection/image/inverse data comes exclusively from the validated geometry mapping. Unit D is accepted within this review scope; production admission still depends on the remaining integration work.

Orchestrator-owned worktree report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/94-direction-selection-review-handback.md`. Identical primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/94-direction-selection-review-handback.md`.

**Standards:** No separate documented-style violation identified in the scoped code.

**Original spec finding one — closed by scoped re-review. Historical reproduction:** In `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_pipeline.py`, `_loaded_fit_axis` at `_loaded_fit_axis` checks `pinv @ v == pullback` for learned and fitted nuisance directions, while `_read_selection_fits` checks only the projection against the source capture. With a legitimately unfitted nuisance, replacing the shared pseudoinverse by `pinv + 2*outer(perp(v),perp(v))` and publishing a fresh byte-correct fit bundle passes selection. The null producer recomputes correct geometry internally, but selection attaches each null to the altered stored geometry. The selected bundle then contains nulls with `stored_pinv @ null_v != stored_pullback`. This violates Unit D's self-contained retained image geometry requirement. Validate the full retained geometry against `image_geometry(source_projection)` or its equivalent algebra, including shapes, rank/cutoff, orthonormal image basis, spectrum and Moore–Penrose inverse; do not infer full correctness from one axis.

**Original spec finding two — closed by scoped re-review. Historical reproduction:** `_loaded_fit_axis` reads `id_weights` without checking them against the independently derived train layout/bootstrap. `freeze_selection` at `_freeze_null_axes` then uses those unchecked weights to freeze all null H statistics. Replacing seed 42's original `[.25,.25,.25,.25]` weights with `[.5,.5,0,0]` in a fresh byte-correct fit bundle passes. Validation axis hashes remain unchanged because `axis_identity` excludes weights. The resulting nulls use substituted weights while the copied learned H statistics, nuisance/probe receipts and original bootstrap receipt describe the original draw. This violates the requirement to use the DOM fit's frozen bootstrap consistently. Derive expected weights/receipt from trusted cluster IDs, instance order and seed; compare all relevant receipts and weights, and check retained H center/variance against the linked train H values. Unknown numerical learned axes can remain loaded data after identity validation.

Both reproductions updated validation shard fit-reference links and completion hashes to the new fit bundle; rejection was not bypassed through stale file hashes. Neither changed the frozen design/protocol or validation outcome rows.

**Schema-shadowing blocker — closed by final scoped re-review. Historical reproduction:** In `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_pipeline.py:451`, `_loaded_fit_axis` loads validated shared geometry and then calls unrestricted `axis.update` from the fitted receipt's array dictionary. A fresh byte-correct fit bundle can add `projection` and `pinv` references inside DOM `arrays`, pointing to `2*W` and `pinv/2`, and halve each DOM pullback. The canonical shared geometry, frozen bootstrap receipts/weights, H centers and variance remain unchanged. Updating validation row axis hashes and exact fit/shard byte links lets `freeze_selection` publish status `selected`. Its stored learned descriptor was hashed against the shadow projection, but the selected axis attaches to the canonical shared geometry; reconstruction gives a different axis digest and fails `W @ pullback == v`.

The additional semantic H validator uses its canonical geometry argument, so it does not expose the shadow projection loaded by `_loaded_fit_axis`. This remains a source/schema and self-contained selected-axis failure. Reject any fitted DOM/nuisance array mapping whose exact key set differs from `{'v','pullback','h_center','id_weights'}` before merging or loading it. Require geometry only through the validated shared geometry mapping. Consider similarly explicit owning schemas for diagnostic probe arrays; no new numerical learned-fit expectations are necessary.

The complete independent reproducer is `/tmp/test_review94_closure.py::test_extra_axis_arrays_cannot_override_geometry`. It starts with a legitimate unfitted nuisance, publishes altered fit bytes through the normal artifact writer, updates validation fit references/completion hashes, and rewrites validation hashes to the actual shadow axis. It then reconstructs the published learned axis and asserts both the descriptor mismatch and the invalid pullback. The attack does not alter the frozen design/protocol, train capture or validation numerical outcomes.

## How verified

Final scoped closure inspected `_loaded_fit_axis` directly: it requires a dictionary with exactly `v`, `pullback`, `h_center`, and `id_weights` before reading references, then merges only those names. Shared geometry cannot be shadowed by an extra per-axis field. Independent attack file `/tmp/test_review94_final.py` reconstructs the previously accepted unsafe axis solely in the attack fixture, updates validation row hashes and every completion/fit byte link, then requires the production freeze to reject with `invalid fit-axis arrays schema` and publish no selected directory. It covers DOM and nuisance separately, alongside both original attacks.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/test_review94_final.py tests/test_a3_direction_selection.py -k 'original_blockers_are_rejected or extra_axis_arrays_cannot_override_geometry or resigned_fit_axis_arrays_cannot_shadow_shared_geometry or fitted_axis_array_schema_requires_all_four_fields or equivalent_orthonormal_basis_preserves_legitimate_geometry' -p no:cacheprovider -q
```

Final observed: 9 passed, 38 deselected in 29.84 seconds. Evidence: `/tmp/review94-final-mgnp.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest /tmp/test_review94_final.py tests/test_a3_direction_selection.py -k 'original_blockers_are_rejected or extra_axis_arrays_cannot_override_geometry or resigned_fit_axis_arrays_cannot_shadow_shared_geometry or fitted_axis_array_schema_requires_all_four_fields or equivalent_orthonormal_basis_preserves_legitimate_geometry' -p no:cacheprovider -q
```

Final observed: 9 passed, 38 deselected in 24.77 seconds, with the existing bottleneck warning. Evidence: `/tmp/review94-final-base.log`.

The nine selected checks comprise the original inverse and weight attacks, independent DOM/nuisance shadow attacks, owning DOM/nuisance shadow regressions, missing-field schema checks for both families, and legitimate equivalent-basis acceptance. No broad new review or implementation edits were performed.

Closure review read the implementation changes directly: `_validate_shared_geometry` recomputes geometry from the linked train projection, checks complete inverse/spectrum and an orthonormal equivalent image basis; `_validate_fit_bootstrap_h` derives the original cluster draw and weights from trusted layout/seed, checks all four receipts, and recomputes learned/nuisance H center/variance. Equivalent orthonormal image bases remain allowed. These checks now reject both original independent attacks. The subsequent exact receipt-array allowlist and explicit field merge close the remaining schema-shadowing path without changing source identity, scientific counts, selection gates or null RNG rules.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_selection.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_selection.py -p no:cacheprovider -q
```

Closure observed: 39 passed in 72.35 seconds in mgnp; 39 passed in 68.95 seconds in base, with the existing bottleneck warning. Evidence: `/tmp/review94-evidence.txt`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/test_review94_closure.py -p no:cacheprovider -q -s
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest /tmp/test_review94_closure.py -p no:cacheprovider -q -s
```

Closure observed: 3 passed in 16.65 seconds in mgnp; 3 passed in 14.28 seconds in base, with the existing warning. Two checks assert rejection of the original pseudoinverse/weight attacks; the third asserts the remaining erroneous schema-shadowing acceptance. Evidence: `/tmp/review94-evidence.txt`.

Historical first-pass evidence follows. Ran the assigned selection file independently in both supported environments:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_selection.py -p no:cacheprovider -q
```

Observed: 23 passed in 46.24 seconds. Evidence: `/tmp/review94-evidence.txt`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_selection.py -p no:cacheprovider -q
```

Observed: 23 passed in 42.08 seconds; existing bottleneck warning. Evidence: `/tmp/review94-evidence.txt`.

Independent scoped reproducer: `/tmp/test_review94_selection.py`. Initial fixture development produced three failures because the nuisance correctly detected one mutation, seed 42's actual weights were already uniform, and the identity writer rejected inconsistent lineage before consumption. Corrected fixtures isolate the two findings above and preserve structural validity.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/test_review94_selection.py -p no:cacheprovider -q -s
```

Observed before the later workload-only test was appended: 9 passed in 28.13 seconds. Two tests assert the erroneous acceptance and print the inconsistent geometry/bootstrap facts. Seven independently re-signed or byte-mutated cases reject: changed fit source identity, reencoded fit manifest, reencoded validation rows, changed validation axis, omitted MMLU floor, omitted seed, and an unknown group field attempting assessment scope. Evidence: `/tmp/review94-evidence.txt`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest /tmp/test_review94_selection.py -p no:cacheprovider -q -s
```

Observed on the same nine-test version: 9 passed in 26.57 seconds, with the same two erroneous acceptances and seven rejections; existing bottleneck warning. Evidence: `/tmp/review94-evidence.txt`.

The normalized workload boundary check also ran separately in both environments:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/test_review94_selection.py::test_normalized_selected_records_consumed_by_workload -p no:cacheprovider -q
```

Observed: 1 passed in 65.73 seconds. The same command with `/sw/external/python/anaconda3/bin/python3.9` observed 1 passed in 65.99 seconds. Actual frozen axis/nuisance descriptors were accepted by both `selected-pilot` and `remaining` inventories after explicitly adapting task/site identity to the independent workload fixture. Evidence: `/tmp/review94-evidence.txt`.

Static review also checked exact finite fit candidate/seed coverage; independently derived train and validation source identities; all five validation arms and designation streams; separate utility membership and both MMLU floors; validation-only keys; gate-first/fallback ordering; blocked zero/uninterpretable DOM; no nuisance rescue; null counts 199 and 32 with RNG offsets 10000+seed and 31000+seed; random steering index 0 and both signs; source/fit/cache/protocol/shard byte links; explicit train ancestry plus `selection_split='validation'`; and the separate noninjected canonical protocol-path/envelope requirement. Existing tests cover these contracts except the findings above. The protocol file reference is outside its semantic digest, avoiding a cycle.

## Execution evidence

Local synthetic CPU tests only; no scientific run or model execution is claimed. Final focused checks passed in both environments; exact output is retained in `/tmp/review94-final-mgnp.log` and `/tmp/review94-final-base.log`. Exit codes for assigned and independent runs, including closure, were zero. Closure test counts were 39 against 39 and 3 against 3 in both environments; the latter includes the test asserting the remaining bad acceptance. Test counts were 23 against 23 in each environment and 9 against 9 in each independent run. No scientific baseline, cluster job or model provenance artifact applies. This review does not claim a verified scientific result. Evidence: `/tmp/review94-evidence.txt`.

## What is NOT done

No author implementation report was read. No model loads, scientific fits or selection, weights, GPU, Slurm, API, notebooks, broad suites, source changes, commits or subagents. The canonical Unit F selection-cache producer remains deferred. Current selection reads independent per-profile capture metadata and bytes, exact validation shard coverage, source provenance, profiles and axis identities; the fixture capture bundles contain no numeric arrays. Canonical payload coverage therefore remains an explicit Unit F integration obligation unless root requires a stricter immediate rejection.

The reported Unit D blockers are closed; production admission remains conditional on the separate integration review and canonical Unit F producer. The workload boundary check uses actual selected record descriptors with task/site identity adapted to the independent three-task workload fixture; it does not establish production lineage equivalence.

## Open questions

No open Unit D review blocker remains. Default: accept the scoped fixes and retain the separately deferred canonical Unit F integration obligations. The original geometry/bootstrap findings and the receipt-schema shadowing finding are closed by the scoped checks above. Retain the accepted scientific counts, gate policy, protocol file boundary and train-ancestry/validation-selection distinction.
