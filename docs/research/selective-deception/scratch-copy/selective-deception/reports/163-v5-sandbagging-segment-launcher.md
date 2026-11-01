# V5 bounded sandbagging segment launcher

Prepared external plumbing only under `transfer-v5`; root alone finalizes receipts, commits core follow-up, reserves/submits jobs and interprets partial status. No worker GPU/pretrained-model/API/job/budget operations. Original artifacts/global consumed guard remain untouched.

## Files and behavior

- `run-sandbagging-segment.py`: thin wrapper importing credential/GPU/digest/one-use helpers from unchanged old `run-sandbagging.py`, verifying pinned SHA before import. Verifies exact original sandbagging argv except NEW common output `eval5-sandbagging-resumed`, common checkpoint `generation-checkpoints-sandbagging`, and explicit positive new-batch limit. Requires exact byte bindings for evaluator/source/model/preprocessing code, new launcher/shell, fixed cohort/masks and argv file. Source HEAD is root-provided provenance; source BYTES are the gate.
- `launch-sandbagging-segment.sbatch`: one-H200/30-minute initial request, no requeue, absolute Python/script execution so Slurm spooling cannot alter the self-path; exports CUBLAS setting and invokes no submission/retry loop.
- `sandbagging-segment-001.argv.json`: initial N2 exact argv; CLI's historical `--benchmark-new-tokens 512` remains unchanged because native sandbagging resolves to1024. Frozen50/five states unchanged.
- `sandbagging-segment-001.receipt.template.json`: **reviewed=false; NOT execution authorization**. Initial1800s/1H200/N2. Exact source/argv bindings, immutable proof002 path, currently null proof SHA pending new source freeze/reproof. Source_commit records prior4fe baseline until root records new commit at finalization.
- `test_sandbagging_segment.py`: six CPU-only safety cases.

Mutable judge cache and USD ledger deliberately have NO whole-file hash binding; public CLI already verifies imported cache prefix and budget guard. Environment strips credential-like names via reviewed helper and sets offline flags, BLAS1, USE_TF/FLAX0 and `CUBLAS_WORKSPACE_CONFIG=:4096:8` before child execution. Production requires a reviewed root receipt and one visible H200 in Slurm. Pending proof is permitted ONLY in dry-run; production requires actual proof002 file SHA and passed exact-token/order/donor/corrupt/masked checks with8/2new-batch counts.

The one-use guard is keyed by the receipt content SHA in transfer-v5; copying identical receipt contents to another filename does not authorize another execution. Distinct root-finalized segment receipts get distinct guards. Guards are consumed once after preflight/GPU validation and are never reset automatically. Status75 passes through unchanged as intentional incomplete generation segment; status0 additionally requires a freshly written complete50-row/five-state/native1024 benchmark block. No automatic launch/retry, receipt finalization or budget mutation.

## Verification

Actual shell → new Python wrapper → actual public evaluator CPU dry-run completed0 after source-binding and provisional proof checks. Log: `transfer-v5/sandbagging-segment-001-cpu-dryrun.log`. It reports50intact +50native donors +200intervention generations and native1024; full-block estimate82.1min is informational, while this receipt bounds only2NEW batches/30min. Dry-run consumed no real receipt guard; prior `sandbagging-execution.used` remains present.

Six unit tests pass in both environments: mgnp6.04s and base4.08s, `/tmp/v5-segment-tests-{mgnp,base}-final2.log`. Covers unreviewed receipt refusal; source/argv/proof/path/scope/interpreter rejection; per-receipt distinct guards and duplicate-content guard identity; one-use collision; mocked production75 preservation and zero-without-fresh-complete rejection. Initial missing-wrapper tests were red before implementation. Base interpreter fixtures explicitly emulate required mgnp; separate wrong-interpreter case verifies refusal.

Root additionally approved a narrow core runtime alignment: only three backend setters next to existing checkpoint opt-in seed0 (deterministic=True, matmul/cuDNN TF32=False). Stock callers remain untouched. New public-main opt-in/stock regression observed expected red, and final expanded CPU suite mgnp218passed44.10s; base218passed71.66s (3 existing environment warnings; `/tmp/v5-runtime-aligned-base.log`). Updated hashes in report159. Prior immutable proof001 passed on prior sources172s but is not final authorization for this new source/settings. New bounded proof002 is required after root commits/reviews the change.

## Current hashes

| File | SHA256 |
|---|---|
| `run-sandbagging-segment.py` | `4f9d8cd2dbf7b0f9418772a28d2cab595bc05245177e07e31826e061c339fd1a` |
| `launch-sandbagging-segment.sbatch` | `3af6ce2aebb33777b5e2015e700192a37c09b72b7b002259599d67748c69e92a` |
| `sandbagging-segment-001.argv.json` | `cdff1e8ddc3c801c6b7655fef1a9c9920b2e8ab180ff30de7d739fedd3b93999` |
| `sandbagging-segment-001.receipt.template.json` | `dddd02b631e16a9f83d101448ef4c76f2505fcbb71181435ecfad381651b66cb` |
| `test_sandbagging_segment.py` | `e43b698e49dc19abf48fd38ec250b8913b739a2faf830115040372585f228a1c` |
| core `evaluate_circuit.py` | `79eba2a2aa8e6b5745feb7b30e8d47c06845d686651332744326de9d6889e324` |
| core `tests/test_generation_checkpoint.py` | `53851eed7a97751a7f88b63987be080281899f15e66f2fb252dce643ecb361f7` |

## Root finalization

After independent review/new source commit and passed proof002, root copies the provisional template to a distinct final receipt, records new source commit, proof002 SHA, reviewed=true, explicit root decision and reservation provenance. Root verifies all existing file bindings remain exact, repeats actual-shell CPU dry-run against finalized receipt, and separately reserves/submits initialN2/30min segment. Future segments need new root receipts/argv bindings and reservations, while common output/checkpoint directories remain unchanged. N/time can change only in those explicit receipts/launch limits. No claim of full block completion follows status75.

CPU command (no GPU/model inference):

```bash
bash /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/launch-sandbagging-segment.sbatch --receipt /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/sandbagging-segment-001.receipt.template.json --dry-run
```
