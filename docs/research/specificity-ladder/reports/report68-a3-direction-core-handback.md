# Hand-back: A3 direction core

Agent: Codex direction worker. Status: handed-back. Scope: bounded direction-core CPU implementation; the complete direction scientific and inferential workload remains unfinished.

## What changed

Owned implementation files in the specificity-ladder worktree:

- `component_analysis/a3_directions.py`
- `tests/test_a3_directions.py`
- `docs/research/specificity-ladder/reports/report68-a3-direction-core-handback.md`

This report is mirrored to the primary checkout at the same relative research path. No other source or research record was edited.

The core fits paired D-minus-I difference-of-means axes in the retained residual image of a head projection. Its float32 singular-value decomposition and pseudoinverse use the same strict relative singular cutoff of `1e-6`, as prescribed by `plan-a3.md`. Sampling canonical pressure clusters with replacement retains every member ID; multiplicity weights normalize across the expanded ID sample, and streams average within ID. Receipts retain cluster draws, multiplicities, original ID order and weights, expanded/unique/effective sizes, spectrum/rank, raw norm, H center, pullback and H projected variance.

The core produces donor subspace interchange, centered H removal and both signed fit-standard-deviation steering replacements from intact head tensors. Boolean position masks and per-row readout indices restrict changes. The caller owns checking those positions against the attention mask. `perturbation_diagnostics` reports each selected position's realized head/residual perturbation norm and the axis's fit H variance.

`random_image_directions` draws unit axes in the retained image coordinates using the prescribed seed offset. `prepare_image_direction` attaches each frozen null axis's own H variance, center and pullback using the learned fit's ID weights. The orientation benchmark does not match realized perturbation energy.

`select_direction` accepts complete per-site validation summaries for one seed, trusts their upstream all-A1-gates `point_pass`, chooses maximal D fractional removal among passing sites, otherwise maximal D-minus-I fractional removal with failure marked, and breaks ties lexically. It rejects assessment splits and missing/duplicate candidates. It cannot calculate A1 gates itself.

Additional pure helpers fit pressure-neutral minus user-neutral nuisance axes, report cosine with the learned axis, and fit/evaluate a ridge probe with train-only standardization, regularization one and an unpenalized intercept. Probe labels must be floating tensors containing both signed classes. Probe inputs are cached image coordinates supplied by the caller; the core does not construct or filter a cohort.

The fitting tensor contract is `[id, stream, head_dim]`, with `[id, head_dim]` accepted for a single stream. D/I/H must share the same ordered paired IDs and stream shape; the interface supplies one common instance-ID/cluster list. Replacement tensors describe exactly one head as `[batch, seq, head_dim]`. The pure functions reject nonfinite data, invalid geometry and unstable or zero fitted norms.

## How verified

TDD first observed the missing module, then an empty module produced failures for the missing public functions. The initial implementation passed the synthetic contracts. Additional tests exposed acceptance of an overflowed direction norm; the correction rejects that fit and nonfinite H statistics. Null-axis preparation was added after its missing-function tests failed.

Initial handback directly related test commands, run from the worktree with BLAS thread counts pinned:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_directions.py tests/test_a3_design.py tests/test_component_hooks.py -p no:cacheprovider -q -s
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_directions.py tests/test_a3_design.py tests/test_component_hooks.py -p no:cacheprovider -q -s
```

Observed outcomes: mgnp passed all 59 tests; base Python passed 39 tests with two skips. The direction file alone passed all 18 tests in mgnp and 17 with one skip in base Python. The base skips are the existing inference-hook module and the direction-to-existing-hook integration test, because its installed nnsight is not the pinned version. The independent native tiny-Llama test passed in both environments. Source: `/tmp/a3-directions-related-mgnp.log`, `/tmp/a3-directions-related-py39.log`, `/tmp/a3-directions-mgnp.log`, `/tmp/a3-directions-py39.log`.

Coverage includes unequal cluster sizes and repeated cluster draws without row truncation, stream/id weighting, strict rank tolerance, retained-image null normalization and RNG replay, orthogonal head-coordinate invariance, exact subspace formulas, centered removal, both steering signs, realized perturbation norms, no-op and padding preservation, invalid counts/shapes/nonfinite inputs, gate-first validation selection, nuisance cosine and ridge separability. A biased toy readout demonstrates that a predictive role axis can be causally inert.

Two broad repository test processes were started, then canceled at the lead's instruction to keep verification scoped. Both were terminated by SIGTERM before reporting any test outcome. They supply no pass/fail evidence. Their logs are `/tmp/a3-directions-full-mgnp.log` and `/tmp/a3-directions-full-py39.log`. No unrelated process was canceled.

Environment messages include NVML initialization warnings; base imports also emitted TensorFlow registration/protobuf messages and dependency warnings. These did not fail the scoped runs. No model weights were downloaded, and every instantiated model was a tiny random CPU model.

## Execution evidence

Scientific execution: not applicable; no scientific scoring/training run, scheduler job or assessment rows.

CPU test host: the current workspace host; no Slurm cluster/job ID. Both final related-suite commands exited zero. Test counts and skips are recorded above, with exact terminal logs. Expected direction-test collection was 18 tests; mgnp passed 18 and base Python passed 17 with its explicitly documented integration skip. Sources: `/tmp/a3-directions-related-mgnp.log`, `/tmp/a3-directions-related-py39.log`, `/tmp/a3-directions-py39.log`.

Baseline reproduction: on the random native Llama test, intact self-replay's maximum absolute logit error was `0.0` in each interpreter, against the asserted upper bound `1e-5`. The existing inference hooks also measured `0.0` against `1e-5` in mgnp. These are CPU toy replay observations, not production replay calibration. Tests also compare changed head captures to the constructed replacement and assert that adjacent heads and unselected/padded positions remain intact. Sources are the related-suite logs and `tests/test_a3_directions.py`.

Inputs: inline small synthetic tensors and fresh random tiny Llama configurations; no real cohort, protected archive, model checkpoint or frozen A3 design was loaded. Native construction uses its test-local random seed; the separate existing-hook integration test uses its own test-local seed. The full model configurations and seeds are declared in the test source. No scientific `run_manifest.json` exists because these are implementation tests. Source is the uncommitted worktree implementation; the orchestrator owns commit provenance and production manifests.

The live Codex reading at the initial handback usage checkpoint showed 19 percent spent and 81 percent remaining, below the requested 80-percent pause threshold. This did not authorize scientific spending. Source: `/tmp/a3-directions-usage.json`.

## What is NOT done

No three-seed inferential machinery, constrained triplet statistics, empirical null quantiles, rank probabilities, Holm correction, paired assessment bootstrap, calibration-panel logic or conditional-power simulation was implemented. Those belong to the separately scoped next task. No production fitting, site selection, null panel, steering assessment, nuisance assessment, dataset filtering, workload admission or efficacy claim was performed.

No pipeline integration, GPU work, API call, Slurm job, notebook execution, git command, subagent, A1/A2 change or generic-hook change was made. The complete direction task remains incomplete. Existing inference-hook integration remains untested under the base environment's legacy nnsight; its supported pinned implementation passed in mgnp. Native CPU replay passed in both environments.

## Open questions

No blocking question for this bounded core. The lead should review the public tensor/summary contracts before wiring production pipeline stages. Callers must compute every A1 point gate upstream, check actual unpadded readout positions, bind frozen cohort/provenance identities, transform cached head outputs into image coordinates for probes, and supply the same bootstrap ID weights to each null-axis preparation. Pure tensor shape checks cannot detect reordered IDs when a caller falsely labels their common ordering.

Next work must implement the deferred inferential and power contracts, freeze and persist draws/sites/provenance, perform production replay calibration, and admit the full workload before any scientific interpretation.


### Review finding correction: probe overflow

The scoped review in `report72-a3-direction-review-handback.md` found that finite extreme training coordinates could overflow the fitted center/scale and produce NaN coefficients, which thresholding then converted into a plausible balanced accuracy. The correction adds explicit finite checks on computed training center, scale, standardized design, ridge system/target and solved coefficients. Evaluation validates fitted field dimensions, positive scales, finite intercept and fixed regularization, then rejects nonfinite standardized coordinates or scores before thresholding. The prescribed regularization and train-only transforms are unchanged. The reported extreme-input case, finite score overflow and mutated invalid fields are covered by `tests/test_a3_directions.py`.

Test-first evidence: the added regression batch initially produced 12 failures and one already-correct shape rejection. After the fix, all 13 regression cases passed. Sources: `/tmp/a3-probe-overflow-red.log`, `/tmp/a3-probe-overflow-green.log`.

Final scoped commands after this correction:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_directions.py -p no:cacheprovider -q -s
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_directions.py -p no:cacheprovider -q -s
```

Observed: mgnp passed all 31 tests; base Python passed 30 with one existing-hook skip. Both commands exited zero. Native tiny-Llama replay error remained `0.0` in both environments; existing-hook replay error remained `0.0` in mgnp. These are the same synthetic/tiny-model CPU inputs described in the execution-evidence block, without scientific rows or a production run manifest. Sources: `/tmp/a3-probe-fix-mgnp.log`, `/tmp/a3-probe-fix-py39.log`.

Only the owning implementation/test files and this handback changed during the correction. This resolves the scoped numerical guard finding without an efficacy claim or new experimental threshold. No broader tests, model downloads, GPU/API/scheduler work, notebooks, git commands or agents were used during the correction.
