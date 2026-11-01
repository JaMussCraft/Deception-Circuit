# Bounded native assessment caller

2026-10-19. CPU implementation only, in `Deception-Circuit/.claude/worktrees/selective-native-replay`. Owned files: `evaluate_native_sparse.py`, `scripts/native_sparse.sbatch`, `tests/test_native_sparse.py`. No real weights loaded, model outputs inspected/generated, GPU jobs submitted, APIs called or git operations performed. Synthetic tiny-model tests generate only arbitrary vocabulary IDs.

## Execution contract

`--dry-run` without receipt validates the corrected 16 final pairs and exposed 16 prior H donors structurally, checks semantic/twin disjointness and eight/eight truth counts, freezes a deterministic structural bijection using every donor once and exactly four assignments per recipient-truth/donor-truth cell. It reads no response, model-belief or deception field. The prior ambiguous donor remains eligible. The corrected source JSONs remain unchanged. It prints the caller source identity and 192/336 target bounds, without loading tokenizer or weights or creating output artifacts.

`--prepare --receipt SELECTION.json --model-path LOCAL_SNAPSHOT` validates all three/six finalists, their exact head-only binary exports, and their checkpoint, training manifest and run identity hashes. It loads only the local tokenizer, retaining exact manual native Llama-3 prompt bytes without injected date, and freezes actual D/H/R and H donor text/token IDs, mapping, EOS IDs, 256-token greedy cap, source hashes, Python/package/runtime/dtype/backend identity and SHA256 of actual local weight/tokenizer/config files. Weight hashing streams bytes and does not instantiate model weights. Every preparation has a content fingerprint. Snapshot hashing can be I/O intensive and is deliberately separate from model loading.

Shared selection receipt, coordinated with the WikiText final evaluator:

```json
{
  "version": 1,
  "finalists_frozen": true,
  "expansion_decision": "union_only",
  "selection_basis": "SDR_WikiText_validation_only",
  "no_test_based_selection": true,
  "finalists": [
    {
      "arm": "H",
      "space": "union",
      "status": "admissible",
      "export_path": "/absolute/path/selected-mask.json",
      "export_sha256": "...",
      "checkpoint_path": "/absolute/path/validation-NNNNNN.pt",
      "checkpoint_sha256": "...",
      "manifest_path": "/absolute/path/training-manifest.json",
      "manifest_sha256": "...",
      "run_identity_path": "/absolute/path/run-identity.json",
      "run_identity_sha256": "..."
    }
  ]
}
```

The example lists one entry for readability; the implementation requires exactly H/W/HW union entries, or all six union/all entries when `expansion_decision` is `all_heads_complete`. Every entry preserves its own-arm `admissible` or `failed_frontier` status, so an unsuccessful arm is still assessed. The shared selection receipt does not bind just one evaluator's source; each evaluator freezes its own execution identity.

`--run` additionally requires the exact existing prepared `OUTPUT/manifest.json` and `--run-receipt EXECUTION.json`:

```json
{
  "assessment_authorized": true,
  "manifest_fingerprint": "prepared fingerprint",
  "manifest_sha256": "SHA256 of OUTPUT/manifest.json",
  "finalist_receipt_sha256": "SHA256 of SELECTION.json",
  "estimated_gpu_seconds": 60,
  "reserved_gpu_seconds": 120
}
```

Numbers above illustrate the schema, **not a runtime estimate or reservation**. Root supplies measured estimate and reservation; estimate must be positive and fit reservation. This gate occurs before loading weights or producing any donor/target response. Real execution requires CUDA and a local original safetensors snapshot. All runtime/model/source/data/export/checkpoint/receipt changes invalidate preparation or resumption. The run receipt copy and its raw hash are recorded in the output directory.

## Bounded replay and persistence

The caller uses `capture_donor` and `generate_with_replay` from the new native helper without changing existing model/training paths. It captures each of 16 genuine H donors once, stores CPU banks on disk, and keeps only one bank active while executing that donor's recipient, all three domains and every finalist plus intact. Every target is individually unpadded. Intact runs through the same replay engine with an all-one mask. Exactly 16 donor completions plus 192 targets (three finalists) or 336 targets (six) are scheduled, at most 53,248/90,112 generated tokens. Physical costs still require measurement; this implementation alone grants no GPU allocation.

Results include prompt mapping and coverage, unmapped prefix, query indices, terminal-held steps, EOS/cap, recipient/donor source truth, encoded-target value for R, and finalist frontier status. Source-truth agreement is expressly metadata; actual donor judgment remains pending later blind annotation against its own statement and is never inferred from source labels. No SDR readout donor scoring occurs.

Each completed output is atomically persisted with execution fingerprint and record hash. Bank files have raw SHA256 bindings. Exact completed tasks resume without generation or file mutation. An in-flight marker prevents automatic re-generation after an interrupted donor or recipient call; root must reconcile budget before permitting a retry. This avoids silently exceeding completion bounds after a crash. Completed rows remain reusable.

## Validation and handoff

The actual `scripts/native_sparse.sbatch --dry-run` succeeded in mgnp on the corrected frozen final/prior JSONs, printing 16 recipients, 16 donors, `[192,336]` target bounds, `weights_loaded:false` and `structural_only:true`. No output directory was created. No weightful smoke, model-output inspection or readiness claim is implied. The shell wrapper enforces offline settings, limits CPU threads, unsets paid API credentials and loads mgnp through the established guarded initialization pattern.

Focused tests cover response-independent structural selection, semantic overlaps and duplicates, exact balanced mapping, complete selected-set/checkpoint/manifest/run-identity binding, failed-frontier inclusion, no test selection, real trainer export hash and MLP guards, frozen prompt/weight/runtime/source identity, stale/corrupt stores, interrupted generation budgeting, and tiny-model helper integration shared across all domains/masks with exact resume. Final verification: `tests/test_native_sparse.py` has **12 passed** in base Python 3.9/Transformers 4.57 (20.68 s) and **12 passed** in mgnp Python 3.12/Transformers 5.13 (18.02 s), CPU only. Exact selected-export provenance is also checked against the receipt-bound run identity JSON.

Root handoff: finish source review/helper edits before preparing a real manifest; freeze actual selected sets only after validation/any authorized all-head expansion; measure native replay/capture/storage runtime; create shared selection receipt, then prepare in the same mgnp/backend configuration as execution; freeze root execution receipt with measured cost; only then allocate/run within the ledger. All native outputs remain pending. This caller's completion/failure does not gate sparse fits. Annotation/export and scientific synthesis remain root work, including denominators, intact-capability limits, ambiguity/refusal/damage and donor mismatch interpretation under reports 58/61.

## Independent review hardening

The caller review identified a real gap: hashing an arbitrary checkpoint/manifest did not establish that its deterministic gate values produced the selected export, that it belonged to the declared arm/space/protocol, or that its base snapshot matched the model to be loaded. A RED tiny trainer-checkpoint test reproduced the missing validation before implementation.

Preparation now reads only the gate-only CPU checkpoint using the existing completed-record payload/fingerprint validator. It recomputes exact binary keep values from actual checkpoint logits, eligibility, gamma and zeta, compares exported logits/eligibility/keep values, enforces hard-open nonhead eligibility, validates candidate identity/geometry and the frozen 103-head union or complete all-head set, and requires a completed scheduled validation update in 64..512 at step64. It checks canonical manifest identity, exact export/run provenance, arm/space/settings, canonical frozen protocol/WikiText identities, and the512/64/8 amendment schedule for production geometry. Actual freshly hashed local weight/tokenizer/config files and snapshot path must match the original training provenance. No base weights are instantiated by these checks.

The final run holds an exclusive flock from execution-receipt checks through model loading and every generation; individual in-flight markers use exclusive file creation. Concurrent writers therefore fail before duplicate generations. Runtime setup now enforces deterministic algorithms, CUBLAS `:4096:8`, disabled matmul/cuDNN TF32 and records NumPy as well as torch/Transformers/Python. Package/runtime identity in the prepared manifest is distinct from hardware identity: the root execution receipt additionally requires `hardware` exactly matching the allocated device's `{"gpu": "device name", "cuda": "torch CUDA build", "capability": [major, minor]}`. The execution receipt itself is immutable across resume, including hardware/budget; CPU preparation never claims that it has observed the future GPU. Root must populate hardware from measured/calibrated allocation when creating the execution receipt.

The shared finalist-selection receipt schema is unchanged. These checks affect only the new caller and focused tests; frozen training sources and native helper remain unchanged. Focused suite grows to14 tests, including wrong arm/candidates/protocol/weights, unscheduled checkpoint, divergent checkpoint gates, writer exclusion and deterministic runtime enforcement. Final verification is recorded below after completion.

Final post-review verification on frozen caller source: **14 passed** in mgnp (13.47s) and **14 passed** in base (17.82s), CPU only. Independent reviewer notified for its final caller/wrapper check. No real weights loaded or native outputs generated.
