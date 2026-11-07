# Hand-back: A3 direction runner

Agent: Codex direction runner worker. Status: handed-back. Scope: integration-plan Work unit B only.

## What changed

Owned files in the specificity-ladder worktree:

- `component_analysis/a3_direction_runner.py`
- `tests/test_a3_direction_runner.py`
- `docs/research/specificity-ladder/reports/report82-direction-runner-handback.md`

The runner streams bounded union-site captures through the existing no-grad hooks and flushes CPU readout vectors, projection blocks, scalar canonical/native outcomes, labels, source records and exact geometry. It releases sequence captures, residuals and vocabulary logits before calling the chunk sink. Optional own-clause means use each stream's frozen semantic record and remain diagnostic; absent spans are unsupported and never replace readouts.

The direction evaluator uses the reviewed CPU algebra for one-head readout interchange, subspace zero, centered-H removal and both signed steering modes. It explicitly gathers each donor's own readout, including unequal source widths, and prohibits native MMLU interchange. Mechanism donors retain the same ID/condition and opposite stream; IOI donors require clean recipients and frozen corrupt donors. Full-vocabulary FP32 correctness and canonical margins remain separate from native and binary diagnostics; MMLU option metrics are retained through the existing statistics adapter.

Every cache key contains `(profile_id, task, condition, stream, instance_id)`. The shared numeric profile binds padded width, physical batch size, axis tile size, dtype, backend, model/revision and source digest. Dtype is the string representation of a torch dtype, such as `torch.bfloat16`; backend must equal the current hooks backend. Capture lookup is either a callable or mapping. Heads/projections are lists of `{site: list, value: CPU tensor}` records. The synchronous `sink(payload)` is caller-owned and must serialize numeric tensors through Work unit A; this runner does not publish bundles or completion markers.

Each axis tile includes fixed dummy lanes and matched intact, empty, actual-head self-replay and zero-coefficient replay forwards. Dummy lanes produce no scientific row keys. Packing requires structured measured equivalence evidence: matching serial/packed source and geometry, cohort/donor/axis digests, full tile and dummy coverage, repeated intact agreement, numerical errors, exact argmax agreement and all three controls. Incomplete or failed evidence blocks; geometry never changes automatically. Actual model projection blocks, cached source records, labels, choice labels and readout values must match. `axis_identity` binds the exact FP32 numeric axis and rejects conflicting supplied hashes.

`run_positive_controls` delegates the existing all-sender shared-width calibration separately. Scientific scoring requires valid, source-bound calibration before candidate forwards. Only an explicitly injected, diagnostic-only identity may retain missing calibration as invalid rows. Raw rows carry compact calibration references rather than sender arrays. Replay errors use the existing absolute/relative tolerances and exact argmax agreement. The return receipt gives the maximum error and epsilon; the downstream complete-panel packer must propagate the maximum task/seed epsilon across all shards.

`direction_point_metrics` computes one seed/site/axis directly without inventing additional seeds. It checks complete paired mechanism streams and IDs, separate D/H and I/user-neutral denominators in both streams, exact strict collateral gates, IOI accuracy, and both fixed 32-prompt MMLU floors with common intact outcomes. It rejects duplicate, extra or mismatched cells and keeps coverage validity separate from the numerical gates.

## How verified

TDD began with the missing-module import failure. Later RED tests exposed missing exact profile hashes, incomplete packing evidence, implicit missing positive controls, differing MMLU floor baselines, extra utility operations, unsupported clause means, backend drift, stale cached labels, wrong model projection blocks and missing axis hashes. Their final counterparts pass.

Final scoped commands, with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` and working directory set to the worktree:

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_runner.py tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py -p no:cacheprovider -q -rs --tb=short
/sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_runner.py tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py -p no:cacheprovider -q -rs --tb=short
ruff check component_analysis/a3_direction_runner.py tests/test_a3_direction_runner.py
```

Observed final outcomes: mgnp **65 passed in 10.90 seconds**; base Python **52 passed, 2 skipped in 15.28 seconds**; Ruff reports **All checks passed**. Logs are `/tmp/a3-direction-runner-mgnp.log`, `/tmp/a3-direction-runner-py39.log` and `/tmp/a3-direction-runner-ruff.log`.

The actual tiny random CPU Llama test executed under mgnp with pinned NNsight. It compares cached vectors directly to the existing hook capture, runs directional zero/centered-H/positive/negative steering with replay controls, and checks that a neighboring head and every nonreadout position are unchanged. Six synthetic scenarios compare the single-seed estimator against one seed of an existing genuinely three-seed synthetic reviewed-statistics panel, including invalid denominators and failed MMLU/collateral/coverage gates. The runner itself never fabricates other seeds to invoke statistics. Serial/packed tests include a partial final axis tile and compare exact row identities and outcomes.

## Execution evidence

- Execution type: CPU unit/integration tests on the login workspace; no Slurm job, cluster allocation, GPU, API call, notebook or downloaded model weights.
- Final command exit codes: both pytest commands and Ruff exited zero.
- Observed test coverage: 65 passing mgnp tests; 52 passing base tests and the two documented NNsight compatibility skips. The actual pinned-hook runner test executed in mgnp and skipped only in base, whose installed NNsight is 0.5.12 rather than 0.7.0.
- Baseline/control comparison: synthetic intact readout `[3, 6]` matches the cached readout `[3, 6]`; all three same-shape synthetic replay margin errors are zero and therefore produce epsilon `1e-6`. The actual tiny model replay assertions require maximum margin error below `1e-5`; this is numerical test evidence, not a production-model calibration measurement.
- No scientific row cohort or `run_manifest.json` was produced. Source integration and production execution identity remain root-owned and uncommitted by this worker. No scientific finding or final gate is claimed.
- Live Codex usage at the closing checkpoint was 22 percent spent and 78 percent remaining, resetting November 6 at 16:07:41 UTC. No stop threshold was supplied to that read-only lookup.

## What is NOT done

No production captures, model fitting, site selection, null-panel execution, timing admission, CLI orchestration, artifact publication, GPU job or final scientific inference was performed. No core algebra/statistics, artifact module, design, pipeline or other worker-owned source was edited. No git command was run.

Packing receipt validation is structural and numerical; Work unit E must validate its actual immutable measured provenance and admission before passing it to this runner. The runner cannot authenticate a caller-supplied receipt by itself. The complete-panel consumer must enforce frozen membership, exact inventory counts, current source/registry/admission validity and maximum replay epsilon over all chunks. Output receipts deliberately have `complete=False`; they cannot stand in for durable shard completion.

Base native-hook compatibility remains unsupported by its known pinned-NNsight mismatch. The passing mgnp actual-hook execution supplies the required CPU integration evidence. This does not establish production BF16 or GPU serial/packed equivalence.

## Open questions

None for Work unit B. Root should independently review the three owned files before any model-stage implementation or admission. Units C–F must supply profile-bound cache adapters, measured packing receipts, source-bound positive calibration rows and whole-panel epsilon propagation. The report is mirrored to the primary research directory at the same relative path.

### Follow-up: report85 high-priority fixes

Status: handed-back after addressing both review blockers. This follow-up supersedes the original assertion-only packing receipt and permissive positive-control backing descriptions above. Only the same runner, owning tests and this report were edited; the frozen shared A1 helper was not changed.

`measure_packing_equivalence` now executes the exact requested cohort and operations in distinct serial and packed profiles. It requires distinct numeric axes, complete populated tiles, nonzero axis-specific perturbations and actual readout donor maps for mechanism/IOI scopes. It runs intact, empty, actual-head self-replay and zero-coefficient controls through both paths, and separately executes a one-axis tile with dummy lanes. The receipt records actual paired row margins/argmaxes, replay errors, realized head perturbations and axis digests. It hashes the complete concrete recipient identities, tokens, masks, readouts, labels, records, donor maps, cached donor rows, axes, source closure and numeric profiles. Its content and scope hashes are recomputed on consumption. Every measured comparison key, including dedicated dummy coverage, must be present exactly; removing a comparison and recomputing only the outer digest still blocks. Consumption checks actual requested recipient/map/donor/axis coverage before forwards, and requires at least two distinct nonzero measured axes. The review's injected packing-sensitive backend now fails specifically on patched-margin disagreement while its no-op controls remain exact.

`run_positive_controls` validates actual dtype/backend and the supplied source profile before running the existing reviewed `specificity_ladder.positive_control` once per singleton. There are still **three calibration forwards per singleton**, with no additional measurement pass. The producer binds that helper's complete returned record: measured full-vocabulary maximum absolute recovery error, its result under fixed `atol=rtol=1e-5`, full sender-key coverage and explicit donor provenance. Its backing record also binds original recipient/donor snapshots and their separately shared-width padded calibration snapshots. The consumer recomputes the full backing content hash and validates source/profile, current recipient identity, donor/readout provenance, exact complete sender keys, calibration geometry, fixed tolerances and the complete reviewed return before generating the existing four-field compact references. Changing any measured field under an old digest rejects before candidate forwards. Fabricated compact assertions do not substitute for backing measurements. Full vocabulary logits remain transient inside the reviewed helper; no logits are stored in these records.

Final scoped commands used the same three test files and thread limits listed above. Updated evidence:

- mgnp: **82 passed in 20.68 seconds**, exit zero. Both actual random tiny-Llama runner tests executed, including the new tile-two, distinct-axis, nonzero donor-interchange/zero/steering case with dummy lanes and actual all-sender positive backing.
- Base Python: **68 passed, 3 skipped in 22.22 seconds**, exit zero. All three skips are the documented NNsight 0.5.12 versus pinned 0.7.0 incompatibility: the existing model-hook module and the two runner native-hook tests.
- Ruff: **All checks passed**, exit zero.
- Logs: `/tmp/a3-direction-runner-review85-mgnp.log`, `/tmp/a3-direction-runner-review85-py39.log`, `/tmp/a3-direction-runner-review85-ruff.log`.
- TDD evidence: both report85 attacks and runtime mislabeling failed first. Additional RED tests exposed missing measured-comparison coverage before its correction. Regression cases cover stale inputs, axis values, donor cache bytes, donor maps, requested cell coverage, every measured positive-field mutation under an old digest, rehashed missing comparison coverage and rehashed incomplete sender coverage.
- CPU only; no Slurm job, GPU, API, large model, notebook, git operation, production cohort or scientific artifact. No production `run_manifest.json` exists for this work. The original fake full-vocabulary baseline remains `[3, 6]` versus `[3, 6]` with replay margin error zero; packing faults are now rejected rather than counted as a scientific result.
- Closing live Codex reading: **24 percent spent, 76 percent remaining**, resetting November 6 at 16:07:41 UTC.

The measured packing receipt currently authorizes only its exact tested cohort/map/axis scope. It does not silently transfer a validation timing receipt to different assessment IDs or donors. Any later M1-to-assessment profile transfer requires a separately reviewed explicit workload authorization consistent with the prohibition on assessment IDs in M1; otherwise packing remains blocked and callers may use only an independently admitted serial profile. Receipt hashes authenticate content consistency, not the truth of a caller-invented execution: stage consumers must still obtain backing receipts from the measured producer and validated immutable artifacts. There is no implicit model-stage admission in this implementation. Root should independently re-review the two fixes before closing Work unit B.
