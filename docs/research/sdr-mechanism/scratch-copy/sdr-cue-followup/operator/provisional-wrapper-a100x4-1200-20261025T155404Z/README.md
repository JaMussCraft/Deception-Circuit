# Provisional selected A100x4 calibration operator route

This immutable v1 preparation is **superseded and not readiness PASS**. Root's worker changed a frozen test source during the single CPUwrapperdryrun while fixing resumeintegrity. Verification correctly stopped with `literal frozen inputs/source/software/cache mismatch`, exit1. The frozenprotocol stayed unchanged; postrun source audit identified tests/test_sdr_cue_positions.py drift. No dryrun output directory was created.

Measured selected actualwrapper route:112.82s walltime,1,143,396KiB maxRSS. `operations-calibration-provisional-1200.json` contains exact strictschema A100/1200s and60/180/60/60s buffers, with separate not-release sidecar. `dispatch-provisional-NOT-RELEASED.json` shows the absolutewrapper --wrap route and verified SDR_POS_PYTHON override. No sbatch was executed. The operation name reserved_seconds is a proposed runner field; actual reservation remains0.

Because verify_protocol precedes operationvalidation, this rejected v1 call establishes neither operationsadmission nor finalreadiness. Preserve alllogs/receipt and wait for root's finalv2/committedfreeze before another full117sverificationcall. All GPU/sourcefinal/code-review/inputaudit/collision gates remain pending; no calibration/main release, job or model inference. Costs0GPU/$0API.
