# V6 causal runner preparation

Implemented only `component_analysis/selective_v6.py`, its focused test file, this receipt and `launch.template.sbatch`. No pretrained model execution, Slurm submission, API or network call was performed by the runtime worker. Attention extraction and path tests are deferred. Root must freeze the reviewed candidate manifest and source before GPU execution.

The runner calls existing `capture_forward`, `Replacement` and `readout_logits`. Each bank value comes from the assigned donor row's own last nonpad token and is written only at its recipient row's own last nonpad token, at the selected `o_proj` input head slices. Masks are explicit boolean position masks, with no sequence alignment or all-position borrowing. A conditional release simply omits that head from the New30 replacement set: its value follows the currently perturbed computation. No cached-clean rescue is implemented.

Exact fixed-panel counts on the candidate: smoke16case/variant rows from4balanced SDR discovery scenarios,7representative conditions each=112metric rows; discovery64case/variant rows×42conditions=2688metric rows; validation64SDR+48FAR case/variant rows×5whole conditions=560metric rows. The dry-run enumerates all176case/variant rows and3248planned metric rows, while constructing no model. Validation mode has no single-head, conditional-release or candidate-head effects; a later follow-up needs a new reviewed implementation/receipt. All rows remain exposed mechanism development/internal validation data.

Identity controls on every live batch require exact full-vocabulary equality between a plain unwrapped HF SDPA native forward and the traced unmodified forward, then native no-op and self-activation-patched forwards. The corresponding existing fp32 readout must independently match exactly for no-op/self patching. Native-versus-fp32 values are not conflated. Smoke additionally captures every head at each condition's earliest patched layer and checks every position against its unpatched capture with only the selected final-token writes applied; no upstream patch confounds this site. Successful checks are saved in controls.jsonl. A failed identity/write/finite-metric check aborts with partial artifacts retained; there is no tolerance widening or automatic retry.

Each metric row retains its case/scenario/stratum/variant, source and independent donor provenance, requested/alternate/truthful token IDs, condition and exact replaced-head list, hashes and raw requested margin, intact margin, signed intact-minus-condition margin drop, requested/alternate/truthful full-vocabulary probabilities, logits, full-vocabulary argmax and correctness, and KL(intact || condition). D targets are explicitly instructed false answers; I targets are transparent requested answers; H/F targets are truthful. KL uses all vocabulary logits. Full vocabulary arrays are used for calculation and identity proofs rather than serialized per condition.

The deciding aggregate is paired New30 D-margin drop minus I-margin drop, accompanied by each raw effect and H/F truthful-margin losses. Head singles/releases are exploratory. This runner stores raw rows and does not produce a specificity verdict or choose validation candidates.

The model is loaded from `manifest.model_identity.snapshot`, which must agree with the tokenizer path and frozen revision. All10frozen model/tokenizer/config files, including all4weight shards, are hashed once per process before load. CPU streaming verification of those10files took17.91seconds and all matched. Dry-run verifies the16manifest source hashes but does not read/hash the weight shards or construct the model. Live outputs bind the model identity and actual model config, geometry, device, backend, package versions, Slurm job and execution receipt. Dependency hashes cover the runner, shared hooks and manifest validator.

Use the existing `/u/swong2/.conda/envs/mgnp/bin/python` with nnsight0.7.0. CPU/toy tests also support the base environment; real nnsight toy checks skip there because its installed version is0.5.12. Existing focused hook/knockout/model regression suites passed. No whole-repository claim is made.

Root command from the pinned worktree:

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m component_analysis.selective_v6 \
  --manifest /absolute/path/panel.frozen.json \
  --output-dir /absolute/path/new-smoke-output \
  --mode smoke --execution-receipt /absolute/path/reviewed-smoke-receipt.json \
  --batch-size 4
```

The actual wrapper supports a CPU-only dry-run, and has been exercised successfully:

```bash
bash /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/launch.template.sbatch \
  dry-run /absolute/path/panel.frozen.json /absolute/path/new-dry-run-output
```

For live scheduling, root alone supplies the account/partition, `--time=00:15:00`, output/error paths and reservation/ledger update. Template arguments then are `smoke MANIFEST OUTPUT RECEIPT`. Absolute Python avoids fragile interactive shell initialization. Offline environment flags prevent hub network access.

Minimal reviewed receipt (replace placeholders with exact final dry-run `plan.json` fields):

```json
{
  "manifest_sha256": "final manifest hash",
  "runner_sha256": "final runner hash",
  "code_hashes": {"absolute runner path": "hash", "absolute hooks path": "hash", "absolute manifest module path": "hash"},
  "mode": "smoke",
  "review_status": "approved",
  "reserved_gpu_hours": 0.25,
  "remaining_gpu_hours_before": 2.9,
  "reservation_id": "root ledger reservation identifier",
  "output_dir": "/absolute/path/new-smoke-output"
}
```

The exact dependency hashes and output directory are mandatory. An atomic exclusive `<receipt>.consumed.json` claim prevents reuse, including under a different output directory. All output files/directories are created exclusively; partial output is never overwritten. New attempts require a new root-reviewed reservation/receipt and output directory. The runner checks finite numeric budgets, per-stage ceilings0.25h/1h/0.75h and the remaining2.9h envelope. The ledger remains root's authority for cumulative reservations.

GPU timing is unmeasured and must come from the bounded root smoke. At batch4, smoke uses4batches and68forwards (including plain/no-op/self/donor and selected-write checks); discovery uses16batches and736forwards; validation/whole-mask supplements use28batches and252forwards. Smoke is deliberately control-heavy, so a simple row-count multiplier is misleading. Completion receipts separate integrity, model loading, identity/donor, condition scoring, total elapsed and peak CUDA allocation. Root should scale the measured condition/control costs and add measured startup plus a reasonable buffer, with stage ceilings as caps rather than default reservations. CPU hash timing is not GPU scoring throughput.

Final frozen verification: mgnp `tests/test_selective_v6.py tests/test_nnsight_hooks.py tests/test_knockout_model.py tests/test_knockout.py`:50passed in32.81seconds. Base `tests/test_selective_v6.py tests/test_knockout.py`:24passed,1expected pinned-nnsight skip in17.00seconds. CPU source-checking CLI-equivalent dry-run took0.156seconds excluding Python startup; actual module CLI and actual wrapper dry-run both exited0. Frozen runner SHA256: `9aef47a1448e858902b7ca8a661ac86abe2139665773fbe386aa3ad4a12fe061`. Generate a fresh dry-run plan after root's final manifest/dependency freeze to obtain exact receipt hashes.
