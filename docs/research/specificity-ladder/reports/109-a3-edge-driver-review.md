# A3 edge driver independent review

Status: handed-back

## What changed

Independent review of the four-file edge-driver package against accepted plan-a3 Tasks 1, 4 and 6, the prospective edge ruling, and root progress rulings. No implementation files changed. Both independent verdicts are **request changes**: spec compliance and code quality. One consolidated high-severity blocker remains, B1. No other concrete blocker was found in the reviewed owned scope. This is not production admission. Evidence: [accepted plan](../plan-a3.md).

**B1 — Native H-bank integrity is not enforced at cache reuse, intervention, or report intake.** In `component_analysis/a3_edge_pipeline.py:1349`, cached_h_bank checks its key, source ID list, and the set of decoded sender keys. It does not require unique serialized sender records, exact independently known native residual width, finite decoded values, or full ancestral source/representation/profile provenance. The dict comprehension silently discards duplicate sender entries. `_utility_floor` at `component_analysis/a3_edge_pipeline.py:500` then uses ordinary tensor arithmetic, so a malformed one-value vector broadcasts across the native residual width instead of rejecting the bank. All projected additive head and whole-MLP senders here require the model hidden size, independently of the supplied bank values.

Independent counterexample `/tmp/report109_oracles.py::test_cached_bank_scalar_duplicate_and_provenance_are_accepted` starts from actual tiny native model geometry and genuine ancestral source metadata. It publishes a byte-complete operational bank under the correct cache key with every sender value `[0.125]`, one duplicate sender record, and provenance.source_sha256 changed to 64 zeros. Cache reuse accepts all three defects. A real MMLU h-mean clamp produces finite logits equal to those from explicitly expanding each scalar to eight residual coordinates. The correct outcome is rejection before intervention, not an invented constant residual donor. This repeats on both interpreters.

The same bank-integrity boundary is absent from reporting. `cached_assessment_panel` records bank_reference, but `_run_summary` at `component_analysis/a3_edge_pipeline.py:943` and recompute_panel at `component_analysis/a3_edge_pipeline.py:1283` do not resolve or validate that link. After the complete positive tiny path, `/tmp/report109_intake.py` temporarily moves the entire banks directory away. Every panel's bank_reference then points to an absent path. Summary intake with resume still accepts runtime_identity.complete=true and all 120 logical assessment slots. The bank directories are restored in a finally block. This repeats on both interpreters. Injection correctly remains nonfinal; the demonstration concerns complete scientific intake and the same missing bank check remains on the subsequent production-final branch.

Required closure: introduce one strict bank contract shared by production, cache reuse, utility intervention and summary/final intake. Check the exact unique full required sender union before constructing a dict; exact one-dimensional hidden-size geometry derived independently from native model/frozen preparation; finite values after conversion; exact task/base/source/ID order, both streams, original train-plus-validation unpadded-token weighting, additive representation and numeric profile. Resolve every completed linked bank object and its exact byte reference at report intake, including resume. Regress malformed shape, duplicate/missing/extra support, source/profile mismatch and absent/changed bank links. Preserve genuine variable-length equal-token means and all frozen scientific choices.

## How verified

Read actual sources, exact supplied diff, package SHA inventory, operational ruling and root rulings. Independently hashed the four owned files before and after testing; all match the review package. The independently matched SHA256 values are:

```text
pipeline a89077e530694ee86930752bc76e96312408152ce43295c1c198f63a195f9b6a
workload 400c98aea4881a3cac0c5fbbc6498824be938b48a5d1f3ff30745691e87b53aa
tests abac2f68d6c0030306544da23e132a794f7d9fa2396a379732ca742a744f74bf
wrapper 41e3856a903e2e235f33ca229ecea2022915b4d6fa683239c7d88a989df20be1
shared-runtime 691c258d8a46140eef0c4407cf8f06a8f36890d475fe3320fdb19fe2326d9871
```

 Author report `106` and its handoff prose were not read.

Authenticated the real ladder-5f450dc design, selected artifact and mandatory completion sidecar using a3_pipeline.load_a1_parents with original A1 identity. Original A1 commit is 5f450dc93dac707af649dee8c8ca60888b2831db. Completion sidecar SHA256 is 50cf8feef06ecb661ecb8bc76d7ddbeaac7cf29002e947ddf21201e955add20c. Original H banks contain 400 train-plus-validation IDs per task and selected provenance preserves their order. Real original stream records have no attention_mask. Read the matched build manifest and actual D/I FAR train Arrow records: each has 177 rows and the first source ID is 0014c828a92b. Evidence: `/tmp/report109-sources.log` and `/tmp/report109-matched.log`.

Independent signed-score ordering and gate-first selection oracles pass, including retained zero/negative scores, maximum D among passing budgets, and maximum D-minus-I fallback. A separately constructed null oracle reproduces all nineteen sequential CPU torch draws under seed 10042 and confirms that a fixed individual stratum does not invalidate a varying full matched set. Inspected neutral-twin attribution versus within-condition exact donors, complete four-bin graph retention, canonical weighted-cluster fitting, token-sum attribution, exact simultaneous intact-delta clamps and utility unsupported-cell handling. No outcome-based graph pruning or recursive-circuit claim was found. Evidence: [independent oracle](/tmp/report109_oracles.py).

Focused existing seam checks cover the actual local/spooled shell dry-run, injected lazy planning without CUDA, fresh shared authority consumer arguments and M1/M4 limits, durable pilot midpoint-cache resume, original stream validation, variable-length ancestral equal-token H means and measured profile/capacity failure cases. Shell syntax passes. The producer-to-cost proposal path uses actual tiny native measurements and source-bound receipt validation; it does not independently establish live allocation authority.

## Execution evidence

CPU-only on the current host; no Slurm job or GPU was used. All commands set OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1, MKL_NUM_THREADS=1 and PYTHONDONTWRITEBYTECODE=1. Pytest used `-p no:cacheprovider` and dedicated retained basetemps. Evidence: [recorded environment](109-original-evidence.json).

- mgnp: `/u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/report109_oracles.py tests/test_a3_edge_pipeline.py::test_complete_tiny_native_staged_path_reports_scientific_failure_not_missing_assay -p no:cacheprovider --basetemp=/tmp/report109-mgnp -q -s`; exit 0, four passed, 85.64 seconds; `/tmp/report109-mgnp.log`.
- Base: identical targets under `/sw/external/python/anaconda3/bin/python3.9`, basetemp `/tmp/report109-base`; exit 0, four passed, three environment warnings, 111.77 seconds; `/tmp/report109-base.log`.
- Targeted seams: `tests/test_a3_edge_pipeline.py -k 'actual_wrapper or guard_delegates or pilot_midpoint_cache or dry_run_rejects or H_bank_is_ancestral or all_source_stream_fields or shape_complete_measured_inventory'`; exit 0 in both environments, eight passed and 30 deselected each; mgnp 27.67 seconds, base 26.92 seconds with three environment warnings. Logs `/tmp/report109-mgnp-seams.log` and `/tmp/report109-base-seams.log`; basetemps use corresponding `-seams` names. Observed command exits: [original evidence index](109-original-evidence.json).
- Standalone absent-bank intake reproduction: `/tmp/report109_intake.py /tmp/report109-mgnp` and `/tmp/report109_intake.py /tmp/report109-base` under corresponding interpreters; both exit 0 and demonstrate acceptance. Logs `/tmp/report109-mgnp-intake.log` and `/tmp/report109-base-intake.log`.

Both complete tiny paths execute actual independent ordinary/native loading controls, VJPs, 8/16 diagnostics, fit, exact validation, selection, nineteen null memberships per seed/family, assessment and reporting, plus real selected/assessment profile measurement and cost projection. Each retains 120/120 logical slots, two physical panels, ten mechanism rows per panel, 100 IOI rows, and 32 rows for each MMLU floor. The baseline reproduces: ordinary and native fp32 margins are both 20735.4765625; full-vocabulary argmax is 9 for both; readout digest is identical, 5cb97ca9716f119f11d9bd7f57cdf717cc988cabb26076160c9ad3430d7e5b5b. Injected scientific failure is reported with complete=true and finalized=false. Evidence: [original intake](/tmp/report109-mgnp-intake.log), [native fixture](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_edge_pipeline.py).

Provenance is the retained byte-complete prepared/pilot/fit/selection/assessment/control objects below each `/tmp/report109-{mgnp,base}/test_complete_tiny_native_stag0`. The fixture deliberately uses synthetic source commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, not a claimed production run_manifest.json. The actual A1 source run_manifest.json remains at `outputs/_analyses/specificity-ladder/ladder-5f450dc/full/score/run_manifest.json`, naming the original full commit above. This review makes no new scientific verification or replication claim.

## What is NOT done

No source edit, git command, registry/session/ledger mutation, job submission, API call, notebook execution, GPU or large-weight loading occurred. The author broad suite was not rerun. Shared authority and process-local immutable-proof caching are independently owned by Unit F and are not accepted by this review. The tiny positive path explicitly injects source validation/execution guards and model loading; actual numerical producer and measured cost projection run, while live Slurm admission does not. Ten mechanism rows are one tiny assessment identity, not production's 100 fixed identities. Production finalization correctly rejects injection. A complete end-to-end production-shaped injected authority run remains outside this review's evidence. Required production scope: [accepted plan](../plan-a3.md).

## Open questions

Root should route one bounded B1 fix covering all bank boundaries above, then request focused independent closure against a new exact package. No scientific gate, bin, bootstrap, rank, null or workload reduction is required. Production admission remains closed pending B1 and the separate shared-runtime review. Live Codex weekly usage at handback is 39 percent, below the 80-percent pause threshold; reset is 2026-11-06 at 16:07:41 UTC.
 Historical tool-reading transcription: [evidence index](109-original-evidence.json).
