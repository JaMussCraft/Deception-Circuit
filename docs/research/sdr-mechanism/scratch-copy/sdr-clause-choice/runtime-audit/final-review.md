# Independent final generation-integrity audit

2026-10-26. **PASS — complete generation integrity, no material finding.** The exact frozen 640 main + 32 excluded preflight acquisition is complete across the original invocation and one explicitly released resume. This verdict permits downstream export/independent annotation under root's release; it does not establish semantic correctness or pass any scientific continuation gate.

Machine-readable handoff: `final-integrity-receipt.json`, SHA256 `83e44a397e09ad1dc46371e120779be98d729984dac140add2cb0533a24e409e`. It has `status="pass"`, bound manifest, 84 accepted batches, 672 unique rows, 640 main / 32 preflight, zero errors, zero missing rows/IDs, preserved original evidence and no semantic-gate claim.

## Independently checked result

Ran the local raw-file checker with the supported mgnp interpreter after both invocations were terminal and their shared output directory was static. It imports no study runner/assembler and completed 18,728 assertions with zero errors. All 84 expected frozen batches have exactly one accepted terminal and one attempt; all 672 planned row IDs occur once. Main has 639 EOS and 1 cap64; all 32 excluded preflight rows reach EOS. All 10,486 generated tokens and 2,333 physical forwards reconcile with the saved histories/timers. The capped row is retained and remains capped for annotation; it is not converted into capability evidence.

Every external first-step receipt's frozen input hash, slot, true final-prefix readout, full-vector hash and argmax matches the actual decoder control expected hash and first generated ID/readout. All 1,344 recorded controls (672 repeat + 672 empty) are finite, identical-greedy, within 1e-5 and bitwise, maximum absolute error 0. Minimum recorded top-two gap is 0.0037841796875. Cached-tokenizer CPU decoding independently matches every normal/raw continuation and full response; all EOS/cap sequences, token bounds and logical readout histories pass.

The final archive matches the independently reconstructed terminal rows exactly, has 640 main / 32 preflight completion coverage, and preserves the original forecast-stop history. No row is omitted, duplicated, replayed or replaced. All 41 accepted files from the first-job snapshot remain byte-identical. A further comparison against the partial audit's file hashes proves all 127 prior immutable JSON files remain unchanged, including their attempts, timings, run/protocol, stopped summary and failure record. The sole historical failure is the already-reviewed inactive resumable forecast stop; there are no new failure records, orphan attempts or stranded temporary publications.

## Provenance, allocations and bounded resume

The run protocol exactly equals released freeze `freeze-final-4f02784.json` (file SHA256 `64397945b882e2b0e35a91fea2dcc8f9f290c3e6bfeaef8d5c409cdee82d5c0f`). Manifest is `10e2e8a7c2cc1f397b02d6b917533459d7dc242478d81212ed015eab56f01070`; scientific payload is `d22cb1edbb8ed2b3109c3142d74460da9aa360b4cfb4615e6b05d21e6ed94d7c`; committed source is `4f0278487b0285dd27cbc34d20d88c911dc5562a`. All 66 source hashes, original Arrow hash, embedded document hashes, cached tokenizer/config hashes and software metadata match. Both bound invocations record the same NVIDIA A100-SXM4-40GB hardware class, torch 2.11.0+cu128 / CUDA 12.8, B8/L224/cap64 and declared BF16-backbone/full-FP32-readout policy.

Separately compared the actual raw operator-owned sacct/scontrol receipts and their hash links against both run allocations. First job 23218707 FAILED 1:0 after 259 seconds on gpua001 at its reviewed remaining-main guard; second job 23218994 COMPLETED 0:0 after 287 seconds on gpua064. Both had a 900-second limit, one GPU / 4 CPU / 64G, 0 restarts and no requeue. Scheduler starts equal the bound allocation starts; planned ends remain start+900 while actual scheduler ends record each early termination. The second submission contains the explicit `--resume` invocation with the unchanged final protocol.

Every actual attempt passes independent reconstruction of the per-batch full-cap and remaining-main admission guards. The first resumed main037 requires 781.0188053260208 seconds against 827.4201674461365 seconds remaining; no policy relaxation was needed. Minimum reconstructed margins across both jobs are 373.7819 seconds for per-batch admission and 1.4934 seconds for remaining-main admission. Operator accounting is independently consistent with 259 + 287 = 546 actual A100 GPU-seconds and 1,800 reserved GPU-seconds,$0API. No ledger or scheduler state was changed by this reviewer.

## Evidence and limits

- Raw result `final-raw-check-results.json`: SHA256 `d7c20e7375864c54d7d62355a400d5bef33de8ff3a6dabe3bcb3b0f71c21f1b1`.
- Independent scheduler/link result `final-scheduler-check.json`: SHA256 `5138d82f111ee07533382ccc169e3fe5579ab75b92cc41fe19b9d5f0c7d91760`.
- Final archive: SHA256 `48196fcca8a577bce3a0fdb6849e0dfc2e28338435598d43e7564cb8503936f0`.
- Checker source `check_raw_run.py`: SHA256 `f3472d70142bd5f97513a0acc05411c12d326cbd8912f9c4c6583db7d15d5459`; mgnp syntax compilation and focused Ruff F checks pass.

Reproduction command uses `check_raw_run.py --prior-snapshot runtime-audit/partial-snapshot-23218707.json` with the final accounting and both raw scheduler receipt paths and a fresh result path under this review directory. The prior partial review/snapshot are retained unchanged.

This checks full-vocabulary comparisons from recorded receipts, not independent model recomputation. Later-step finiteness is enforced by the exact reviewed decoder source rather than individual saved tensors. Large weight shards remain bound through the frozen/runtime input checks; this audit rehashed source/software and tokenizer/config files rather than reloading/rehashing weights. Admission is reconstructed at saved attempt timestamps with 1 second marker allowance; exact pre-check/per-forward wall-clock instants are not separately serialized. No model/GPU execution, new generation, Git/source edit, semantic annotation, or behavioral gate calculation was performed. Only this audit directory was written.
