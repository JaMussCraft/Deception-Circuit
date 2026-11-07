# A2 post-training CPU comparison and prospective freeze proposal

Status: handed-back

## What changed

**Ready for root CPU submission only; no analysis was executed by this review.** The exact packet compares every canonical full scientific source, then freezes all prospective A2 groups using accepted APIs and original A1 context. It performs no bank collection, assay scoring, model loading or GPU reservation. [Final manifest](final-manifest.json), [job proposal](job-proposal.json).

Reuse immutable execution bundle `40fe57289405fd53a3fce02e5d4e47a0ebf78b64`. Its A2 comparison code matches accepted Task1 revision `01f8638`; A2 pipeline matches the accepted group/bank/assay implementation revision `bc596eb`. Training records independently retain execution `6bd8bf5334f2e83613a129d2fcfeacf83e762191`, matched-build source `77b6487b08b4410a4e5a9995c6ff5e46834a5ce3`, and A1 ancestor `5f450dc93dac707af649dee8c8ca60888b2831db`. No W HEAD/index change or new snapshot is necessary. [Byte bindings](source-binding.json).

## How verified

The exact all18 input is [source-records.json](source-records.json): only the required five path fields per record, in task/condition/seed order. Every canonical receipt exists. No receipt/result/mask outcome payload was inspected; the future APIs will re-audit actual files, export parity, original source/archive/fleet/config/build/ruling, full schedule and matched rows rather than trust caller success flags.

Checked accepted used-path bytes against the immutable bundle and existing full-source CPU verification. The closure includes A1 validators/runner/metrics/model helpers, both A2 modules, twin-training/projection helpers, config, wrapper/profile and complete grader sources. `scripts` is a namespace package; actual imported project files must still resolve inside the immutable runtime. The future job checks every snapshot source and declared link before and after work. [Source closure](source-binding.json).

Original context is `ladder-5f450dc/design.json`, `selected.json`, and `selection_run_manifest.json`. The owning freeze validates the A1 selection sidecar and exact exclusion/assessment/utility ancestry; its internal A1 args keep the ancestor commit distinct from analysis `--commit`. Geometry uses only pinned offline model-config JSON. Explicit hub-cache root follows the existing flat local model reference, and the driver checks config bytes/hash plus the resulting geometry reference. No weight read is proposed.

## Execution evidence

No execution result is claimed. Existing six-source CPU audit completion metadata reports success; native outcomes were not opened. Work sizing uses that observed audit duration: two serial all-source passes scale to about the recorded pre-cache estimate, plus A1 context and publication. The proposed request is four CPUs, thirty-two GiB, fifteen minutes, no GPU, on normal CPU allocation `beto-delta-cpu`. Root must refresh scheduler test-only evidence before submission. [Measured sizing basis](job-proposal.json).

The [driver](comparison-freeze-driver.py) calls `compare_masks(records)` and `write_comparison`, then the immutable wrapper with `--stage freeze`, original design/selected, exact comparison/source-record files and full analysis commit. The owning CLI independently recomputes the comparison before publishing `groups.json`. Default required operations remain item-swap, zero, H-mean, H-twin, self-replay and empty; optional independent donors are not newly enabled. Empty or unstable groups remain present. No efficacy filter or assessment-dependent selection is added.

## What is NOT done

No local heavy test, source re-audit, comparison, freeze, model/GPU work, scheduler/RS/git mutation, code change or assessment-outcome inspection. Source descriptors, static hashing and syntax inspection only. Existing audit results are prerequisites, not replacements for the future complete source checks. Native training-test metrics retained by the accepted comparator are not ladder assessment results or new efficacy gates.

## Open questions

No identified source/input-path blocker remains for this CPU-only packet. Root owns exact submission. The target output namespace must remain absent; artifacts publish without replacement, partial failures are retained, and no automatic rerun is allowed. A final completion marker appears only after comparison/group validation and unchanged source checks.

Successful CPU freeze grants no scientific specificity result or GPU admission. Subsequent original-H union-bank collection, all required per-seed assays, controls, coverage and MMLU floors need their existing independently measured cost/authority gates within unchanged A2/global caps. Preserve all original A1 and training artifacts and all hardware/account migration appendices.
