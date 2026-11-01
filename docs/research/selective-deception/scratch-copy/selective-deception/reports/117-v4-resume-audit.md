# V4 terminal-segment continuation auditor — 2026-10-21

Implementation ready for independent root review. No production checkpoint was inspected, no job polled or acted on, and no continuation, selection, reservation or authorization was issued. Scope is the new scratch auditor, its CPU tests, and this report. Runtime source remains frozen at4247c54d24f277de863abf8a7b9a462470276f45.

The partial checkpoint format contains only a run fingerprint, gates, optimizer, cursor and RNG. It does not persist full provenance until final export. The auditor therefore reconstructs provenance from the trusted historical v3 all-W export, changing only known frozen v4 source/manifest/amendment/receipt/settings/optimizer fields. Both reconstructed baseline fingerprints matched the immutable actual v4 receipts before any production checkpoint read. This verifies the unchanged model inventory, packages, hardware, fixed artifacts and other runtime fields without inventing them.

Root independently froze those identities in `sparse-optimization-v4/expected-run-identities.json`; its SHA256 is443854ea083fb8411ff978dd98dbce6e30d9b80c79f4f1fc8843f8b4ef6c6b04. The helper pins this SHA and checks full reconstructed provenance, run fingerprint, manifest SHA, original receipt SHA, template SHA and source-freeze SHA against it before loading latest.pt.

| Run | Frozen baseline fingerprint | Expected run fingerprint |
|---|---|---|
| all-W-init1 | 0cccfdcd3136e1f28026a5e7c285ee6ebaed22ee9a27165d47cb9098057040ae | 067a7b176b6cd1b207a9487b794b044ceb5a9f2b9a6c5012fa678873a773239f |
| all-W-init10 | 572e9a74305b6a381b09f710d714c1a8facaec200c2f4946e438ff2930b24be3 | 9b5a057a3fab6d862e74d3ac62a9e48b4b8281295e09788c3790e12d85b2310c |

Template: `.scratch/selective-deception/sparse-extension-v3/runs/all-W-rho0/selected-mask.json`, SHA256 b2103a8598cf46a183aecc4b86e6d53dc58d4cc05dd3f0f0423198864a4eb302. Source-freeze SHA256 d189629ca8f813213fc38ca8fc0cec2a656c55fde2ed59dd42b8c314dc39ca1d.

After the submitted job becomes terminal, root can run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/analysis/optimization_v4_resume_audit.py --job-id 23100323 --study .scratch/selective-deception/sparse-optimization-v4
```

Prefer an absolute study path if invoking outside Alignment. `--output PATH` optionally writes a fresh exclusive JSON file; otherwise the only output is stdout JSON. For a later segment supply its original `--stage-authorization PATH`. Existing files are never overwritten. The helper never submits, cancels, resumes, writes receipts, changes checkpoints, initializes CUDA or constructs a model.

It requires terminal sacct parent and step records, exactly two allocated GPUs and at most3600elapsed seconds, then binds the job to the single-use pair launch claim and original stage authorization. It verifies original receipt SHA, runtime source inventory, protocol/manifests, calibration evidence, both baseline caches, all WT cache payload/inventory bindings, actual model snapshot SHA inventory and fixed circuit artifacts. It uses the existing runner `_load_tensor` / `_tensor_digest` and baseline-fingerprint helpers; all deserialization uses map_location CPU. Each latest checkpoint and every historical validation checkpoint must have exact cursor coverage, optimizer moments/step/settings, finite values, source-constant gate distributions/shapes/eligibility, valid Python/NumPy/CPU/CUDA RNG state bytes, fixed schedule and WT block ordering, and matching reconstructed binary export. The latest SHA must stay constant during inspection. A failure marker rejects continuation pending root investigation.

Per run JSON reports completed/remaining updates, checkpoint path/SHA, run fingerprint, original receipt SHA and remaining-work estimates using measured update, per-update checkpoint, validation and reload timings. A separate conservative estimate adds15% plus60seconds; queue and contention remain outside that estimate. Partial3072-horizon fits are valid continuation candidates only. A3072-complete run gets a distinct status and still requires the separate full-grid selection audit. Every result sets continuation_authorized=false and selection_allowed=false.

CPU verification:28 tests passed in mgnp;28 passed in base (one existing pandas/bottleneck version warning). Tests cover the actual frozen dual identity reconstruction, trusted helper corruption/fingerprint rejection, optimizer/gate/RNG/loss/schedule/history failures, complete3072 and partial/zero fixtures, active Slurm refusal before input reads, terminal steps and exclusive output. A trusted historical actual v3 validation64 checkpoint passed the same state/schema checker; no production latest.pt was read. No notebooks executed. Independent review remains a root gate before live use.
