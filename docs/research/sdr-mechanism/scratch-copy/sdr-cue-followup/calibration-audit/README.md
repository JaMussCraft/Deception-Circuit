# Independent calibration audit preparation

Prepared against final source `29492146127f56c05a4087b1bfdeea0e63a4d24a` and protocol file SHA `b2c7fd65ccb67e93f463553044569248fe85a80b8e1bd72ffef28df2cb3b5fa0`. This directory is auditor-owned. **No actual runtime PASS or job completion is asserted.** Await root's completion notification; do not poll the output directory.

`independent_calibration.py` imports no production runner/validator. Its independent oracle constructs exact B8/L224 Boolean mask bytes and forward-signature hashes, complete per-row controls and token/logical-index schedules. It checks all 13 ordered terminal/attempt/measurement records, six forced arms (263 forwards and 8x134 controls each), seven natural batches, both family system-E controls with all three frozen E slots, selected head/mask/current-history receipts, immutable hashes and runtime bindings. `--decode` additionally uses only the cached tokenizer to verify every natural/forced continuation and raw continuation. The checker reads no weights and opens no model/CUDA path.

Preparation verified the final scientific/provenance hashes, all 63 source files, and cached non-weight metadata against the frozen protocol. Existing independent manifest review remains the authoritative full scientific-input comparison. All model weight hashes stay bound through frozen protocol/runtime identity; this audit deliberately does not repeat the expensive weight reads.

Verification:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-cue-followup/calibration-audit/test_independent_calibration.py
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-cue-followup/calibration-audit/independent_calibration.py --output .scratch/sdr-cue-followup/calibration-audit/preparation.json
```

The self-check ran six focused synthetic tests in 15.088s, all PASS. Besides a complete synthetic 13-batch example and hand-calculated forecast, deliberate corruptions cover missing/duplicate/Boolean controls, wrong forced tokens, wrong physical call signature/count, wrong frozen mask, stale self history, foreign donor/head, missing terminal, forged timing measurement, pass-only causal-null objects, and H200/software drift. This is checker verification, not a rerun of production suites or an actual calibration result.

After root sends the exact completed runtime directory and approved calibration operations path, run once with the mgnp interpreter:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/sdr-cue-followup/calibration-audit/independent_calibration.py --run EXACT_RUNTIME_DIRECTORY --operations APPROVED_CALIBRATION_OPERATIONS --decode --output .scratch/sdr-cue-followup/calibration-audit/actual-artifact-audit.json
```

Then separately reconcile operator final `sacct`/accounting with the bound job, exact requested/start/end/elapsed time, state/exit/restarts, nodes, single A100, UUID/device class, reservations and actual GPU-seconds. Read the retained wrapper/time/log metadata for process startup/preflight and model-load coverage. Recompute main size from observed seven-cell natural elapsed+seal+publication, fixed 528-batch counts, 50% uncertainty and explicit startup/premodel/audit/shutdown/safety buffers. Compare the independent `forecast()` arithmetic with the operator's exact proposed main operations/forecast before any main release. Preserve forced64 safe batch admission and note how much each allocation must reserve for startup and final all-row audit; a proposed single allocation need not fit all remaining rows when separately released durable resumes are planned.

The checker's artifact PASS is explicitly pending scheduler closure. It does not prove raw activation/logit values beyond the stored checksums/numerical receipts and independently reviewed source; it does not replay the model, infer scientific labels/effects, demand H200-to-A100 bitwise reproduction, or release main work. All calibration completions remain excluded from scientific inference.
