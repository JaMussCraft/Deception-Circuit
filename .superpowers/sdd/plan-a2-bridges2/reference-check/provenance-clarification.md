# H200 launch/deployment provenance clarification

Status: handed-back; read-only reconciliation. The differing quoted digests are different hash definitions for the same deployed files, not evidence of a changed build or row population.

## Exact paths and digest definitions

All paths below are relative to the specificity-ladder worktree. Exact full paths, full hashes and copied transfer-manifest rows are in [provenance-reconciliation.json](provenance-reconciliation.json).

| Input | Raw file SHA256 | Canonical/resolved digest |
|---|---|---|
| `outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json` | `3183d1cb71a195ada89743af241db66028670b1fded65ef3bba5060cb5b879ce` | `616b660586d4bc07f3dd7a72cfb3ccce48cbc9ee8f024fb5c20f1cbb712e07a4` |
| `outputs/_analyses/specificity-ladder/a2-timing-h200-config.json` | `4321ef824036b316828564f7fc3833d508552361d370890e46be39bd1feacec8` | `be2f4e7b7c0e6cae93102bf52d63535765eac38af14f57a81bdf2816a3392f22` after the launcher adds `data_root` |

The frozen launcher's `digest()` hashes sorted compact JSON. `build_manifest_sha256` is that digest of the full build JSON, whereas `build_manifest_file_sha256` hashes its file bytes. `frozen_config_sha256` hashes the resolved outer config after `main()` supplies `data_root` from the absolute build-manifest parent; `config_file_sha256` hashes the unchanged original config file. The unaugmented config's canonical digest is `249e29ca…`, not its resolved digest. The declared `build_hash=c79830…` is another build identity field and is not a raw file hash. Both raw file hashes match the original H200 receipts and exact deployment transfer entries. No complete metadata body is being silently equated with a different body. [Reproduced using frozen code](reconcile_provenance.py), [raw reconciliation](provenance-reconciliation.json).

The archived default `scripts/jobs/specificity_ladder_a2.json` has raw hash `c91db106…`. It differs from the explicit original H200 config only in `output_root`: `a2` versus `a2-h200`. Thus the archived default and original launch config are not byte-identical; using the explicit original `--config` is necessary for the exact timing-repeat command. [Archive member, full bodies and exact diff](provenance-reconciliation.json).

## Actual SDR data and training parameters

For each arm, all native-recorded dataset-file byte hashes match both the current files and deployment manifest. The original H200 dataset bytes themselves are therefore preserved, including prompts, labels, source metadata and stored token proofs. Direct Arrow inspection reconciles all ordered IDs with the original receipt, build manifest and private dataset config: 187 train, 187 validation and 952 test rows. Every stored prompt hash, reference prompt, target/distractor source label, label-semantics flag, token-length/readout proof and row/private token proof matches. No row or cohort difference was found. [Per-file and per-split evidence](provenance-reconciliation.json).

Frozen `build_command()` reproduces both arms' original `argv[2:]` exactly, including data directory, sample counts, seed, all pruning switches and hyperparameters. Its resolved expected-config digests match the original `8ce7d85a…` and `82693365…`. Only the executable script location changes from worktree `train.py` to authenticated frozen-runtime `train.py`; script bytes and the recorded source closure match. Physical remote output isolation, host/job/time metadata and the explicit script relocation are operational distinctions, not parameter changes. [Exact command and source checks](provenance-reconciliation.json).

The actual schedule is the same timing20 schedule with cosine `T_max=20`; outer planned epochs do not turn it into a prefix of the full scientific schedule. No source, cohort or hyperparameter adjustment was made to obtain this reconciliation.

## Token evidence boundary and next gate

Legacy evaluated runtime token-ID arrays were not saved. This check does not claim a direct comparison of those unavailable arrays or newly executed H100 inputs. It verifies identical original dataset bytes and stored prompt/length/readout/token-proof metadata. Tokenization equality additionally relies on the unchanged frozen loader and admitted identical tokenizer snapshot; its stored tokenizer provenance is included in the raw evidence. Model/tokenizer transfer protections and actual remote wrapper dry-run remain root/reviewer gates.

The plan now permits the authenticated frozen script path explicitly; its numerical drift statistics, review rule and same-path tolerances are unchanged. The previous predeclaration is preserved as [predeclared-comparison-before-provenance-clarification.json](predeclared-comparison-before-provenance-clarification.json). Actual Slurm/container single-GPU visibility must be checked by the original wrapper; this note infers no visibility guarantee from an environment variable. No remote action, GPU/model forward, source/harness edit or submission occurred.
