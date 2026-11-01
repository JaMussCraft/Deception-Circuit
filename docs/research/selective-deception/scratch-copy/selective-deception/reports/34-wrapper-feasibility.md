# Intact-only wrapper feasibility preparation

2026-10-18. CPU-only ticket05 preparation is complete; no model forward, pretrained weight read, job, API call, notebook, package install, git operation or nested delegation was performed by this worker. Root owns production preparation, source review, actual job-wrapper dry-run, reservation and execution. Optimizer remains held under report32 and the canonical protocol-v2-feasibility.json.

The standalone `analysis/wrapper_feasibility.py` provides positional modes `prepare`, `dry-run`, and `run`. Its 213-line implementation reuses the pilot's manifest/provenance validator, `_exposure`, tokenizer/prompt helper, original context construction, `sr.execute`, `ResultStore`, generation/decode and blind exports. Existing masks/configs are required only by established context initialization; execution receives `masks={}`, every row selects `intact`, and generation opens all gates. There are no score passes, donor references, donor diagnostics or model interventions.

Preparation pins the canonical protocol's file SHA256 `e5f6d58d6524ecad59338b4fdd6c36ff9e6444e3e50ab0ef06c5b6f986aa68b0` and persisted pilot file SHA256. It validates actual Stage1 endpoint provenance through `_exposure`, including corrupt-stream fact flips; the pilot validator verifies its exposure hash, source records, exclusions and training/validation reservations. It independently rejects validation semantic IDs intersecting training or exposed scenarios and text/token collisions with Stage1 endpoints. The fixed 16 validation IDs have two representatives per each of eight strata.

All 32 original D/H rows precede all 32 repaired D/H rows in fixed protocol cluster order. Repaired text inserts only the exact protocol repair plus two newline characters immediately after the existing system header. Both rows retain the same scenario and labels; original tokenization, refusal permission and empty assistant start are checked. Cached-tokenizer preparation produced 90–138 prompt tokens. Exactly 64 generations at 96 tokens imply a 6,144-token maximum, with all denominators retained and fresh `wrapper-v2-*` row IDs.

The immutable manifest binds 93 source files, including the standalone script, root-owned sbatch wrapper, runtime root Python and all evaluation/models/dataset/tasks Python. It also binds pilot/protocol/Stage1 input files, snapshot metadata and tokenizer content, initialization mask/config content and canonical primary SDR data directory. Run identity adds SHA256 of every model snapshot file, hardware/CUDA, package/Python versions, dtype, tokenizer settings, fixed policy, deterministic settings, decoding implementation and seed. Weight contents are read only in `run`, after Slurm/CUDA checks. Changed source refuses reuse; explicit `--resume` accepts only the identical ResultStore fingerprint. An exclusive writer lock prevents concurrent writers; failures propagate without retry. Completed runs require all 64 records before anonymous response export. The final summary explicitly identifies intact-only feasibility and makes no causal-intervention claim.

Verification: nine focused CPU/stub tests passed in both supported environments with BLAS/OpenMP threads pinned to one. Base Python3.9: 9 passed in 11.07s, with existing pandas bottleneck and TRANSFORMERS_CACHE warnings. mgnp Python3.12: 9 passed in 13.30s. Tests cover immutable persistence, exact prompt surgery and ordering, counts, train/exposure/endpoint intersections, empty-assistant preservation, fixed cap refusal, changed-source refusal, intact-only generic execution, exact resume and 64 anonymous exports. Root is independently running the full pilot suites; this worker did not duplicate them.

Actual CPU cached-tokenizer preparation in base Python and `dry-run` in mgnp both succeeded using `/tmp/wrapper-feasibility-final-manifest.json`. Temporary evidence:

- Manifest content hash: `fd0f30dc4bac32c75b04381366fe44ebd58dd9df7a28f979e7fc088eff3775b5`.
- Combined source-files hash: `d70c01e1b5c895ac9387a1a13170d78f6f3ff72f35aa696666d6f34761ba86ee`.
- Standalone script SHA256: `b385cfef5132dddd3df59168e6c22268bf76f005d8f131e89b5c7b5f0c8c9272`.
- Root-owned wrapper SHA256: `6184ed2c8d313a1609ef842020c56e4274f7a24725f0da8e027ecf9dea7fb666`.
- Cached model revision: `0e9e39f249a16976918f6564b8830bc894c89659`.

Root production commands, run from Alignment (the sbatch wrapper takes the same positional CLI arguments):

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/analysis/wrapper_feasibility.py prepare --manifest /ABSOLUTE/NEW/manifest.json
bash .scratch/selective-deception/analysis/wrapper_feasibility.sbatch dry-run --manifest /ABSOLUTE/NEW/manifest.json
```

The standalone `run` additionally requires `--output-dir`, Slurm CUDA and `CUBLAS_WORKSPACE_CONFIG=:4096:8` before startup; root's wrapper already exports it. Production manifests must be newly prepared if any frozen source byte changes.

Runtime planning uses root-reported same-A100 evidence: corrected r2 smoke had 52 completions plus 64 scores and model load in 245 seconds; full r2 had 404 completions plus 1,444 scores (resuming 116 records) in 1,161 seconds. Scaling the deliberately heavier smoke by 64/52 gives about 302 seconds before fingerprint/prefix allowance. Root's conservative planning estimate is roughly 10 minutes; a single 30-minute reservation charges at most 0.5 GPU-hours and includes startup/failure. This is a planning estimate, not a measured wrapper runtime. No automatic retry or budget expansion is implemented.

Root must freeze exported response/mapping file hashes and complete fresh blinded annotation before unblinding. Apply report32's independent 8/16 D-deceptive and 8/16 H-truthful/usable floors per wrapper, including ambiguity adjudication, all paired changes and quality failures. Both passing retains original; repaired-only passing routes to v2; neither passing stops generation-based pilot. A pass authorizes later preparation, never training automatically.
