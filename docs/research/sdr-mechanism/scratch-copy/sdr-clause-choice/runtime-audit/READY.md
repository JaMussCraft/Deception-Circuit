# Independent runtime audit preparation

2026-10-26. READY for operator completion handoff. No live-run polling, scheduler queries, model loading, GPU use, generation, semantic response judgments, source edits or Git operations performed.

`check_raw_run.py` imports no study runner/helper. It independently reads raw manifest, run bindings, attempts, accepted terminals, timing receipts, failures, archive and summary JSON. It checks the released full revision/manifest,66source hashes, original Arrow hash, embedded document hashes, tokenizer/config hashes and package metadata hashes. It uses the offline cached tokenizer on CPU to reconstruct complete normal/raw response text. Model weight hashes remain cryptographically bound through the runtime's frozen verification; the checker intentionally does not rehash/reload the large weight files.

Expected complete coverage is84accepted batches,672unique rows (32excluded preflight and640main), and1344recorded repeat/empty controls. The checker checks every external input/readout/slot/argmax/hash receipt against actual decoder control expected hashes and generated first IDs; all finite/tolerance/greedy/bitwise fields and counts; all EOS/cap sequences, token bounds, logical readouts and four decoded text fields. It checks attempts/run/manifest/hardware/software links, absence of replay/orphan/failure/temp records in a clean completed run, physical forward counts, and independently reconstructed full-cap/main admission margins. It treats missing coverage as incomplete rather than assuming completion.

Preparation verification: mgnp `py_compile` PASS; focused Ruff F check PASS. A CPU smoke invocation against the intentionally nonexistent audit-owned `absent-smoke-run` path completed91manifest/source/software assertions with zero errors and correctly returned `incomplete`. Receipt is `preparation-smoke.json`. No actual output directory was read for this smoke check.

After root's completion notification, run with the supported mgnp interpreter and output confined here:

```bash
/u/swong2/.conda/envs/mgnp/bin/python \
  /projects/beto/swong2/Alignment/.scratch/sdr-clause-choice/runtime-audit/check_raw_run.py \
  --output /projects/beto/swong2/Alignment/.scratch/sdr-clause-choice/runtime-audit/raw-check-results.json
```

Add one or more `--scheduler-receipt ABS_PATH` arguments after the operator supplies final receipts; their hashes are retained by the checker. The final audit additionally compares operator-owned scheduler job/state/exit/restart/start/end/node/TRES fields against the raw run allocation/hardware binding and reservation. Receipt parsing/comparison can be completed once that actual schema is supplied; no scheduler query is delegated to this checker.

Limits to retain in the final report: numerical vectors/finiteness are verified from recorded receipts rather than independently recomputed with the model. Later-step finiteness is enforced by the exact reviewed source, not individual serialized tensors. Admission is reconstructed at saved attempt timestamps with1second allowance for marker publication; exact pre-check clock instants and per-forward wall-clock timestamps are not separately logged. Scheduler costs/live state remain operator authoritative. Semantic accuracy/gates are a separate annotation task.
