# Operator preparation — no allocation released

2026-10-26. Ratified `../spec.md`, independent scientific review, `../plan.md`, root decisions and latest Slurm job/account/interactive policies read. Worktree and all command paths resolve from `/projects/beto/swong2/Alignment`. Source/protocol freezes are still forthcoming. This document does not release any model execution, job or reservation.

## Prospective calibration

Provisional request: one A100-SXM4-40GB,600seconds,4CPUs,64GB host memory, `gpuA100x4-interactive`, account/QOS `beto-delta-gpu`. Fresh projections favor this local option; hardware identity must be verified by the model process. No H200/Bridges-2 transfer or other-job changes. Recheck all live admission facts immediately before dispatch; historical test-only start predictions are not guarantees.

Freeze inputs by the lexicographically first original discovery `story_id`, independently of outcomes. Include its four primary native P/N×truth prompts and all eight directed pairs. Main is all24historical-confirmation stories,96inputs,192pairs and3,936outcomes; calibration remains separate and excluded from all scientific aggregates. All20natural operator batches are mandatory. Two forced64 stress operators are pinned: arm10 U5+clean jointQK and arm18 induced quartet output. No post-calibration arm, cap, prompt or scientific-row changes.

A convenient exact calibration schedule is one B8physical baseline batch with4unique inputs plus4dummies,20B8natural pair batches, and two B8forced batches:164natural rows plus16stress rows,180calibration-only row records. The implementation manifest is authoritative for its explicit IDs/counts; repeat controls are separately counted. Force stress token selection prospectively rather than using semantic outcomes to construct a path. Required numerical checks still cover every operator/mask, not just the two stress arms.

Time the exact released runner behavior, including model/cache preflight and load; recipient/donor/natural-U5 setup forwards; compact clone/remapping/immutability checks; state norms; each arm's firsttoken scoring; every repeat/empty/self/control forward; greedy continuation; CPU transfers; canonical encode/parse/hash; file write/fsync/atomicpublication; audit/readback; and shutdown. Store signature, cold/warm maximum, count and summed elapsed for forwards. Store distinct setup/packing/publication elapsed and bytes. Calibration must include actual atomic writes at the same filesystem destination/class used by main. Do not infer IO from an old unrelated benchmark or omit compact-bank descriptor costs.

Prefer one batch-local recipient/donor/U5 setup shared across the pending arms for that8pair batch, with per-arm atomic acceptance. Resume reconstructs setup banks from the same frozen prompts. Rebuilding setup per arm is acceptable for a simpler correct implementation, but the forecast must charge the measured rebuild every time; the prior seam note's72setup-forward estimate assumed cross-arm reuse and is not valid for480independent setup triples.

Numerical release criteria: finite full FP32 vocabulary; tolerance≤1e−5 and exact full-vocabulary argmax for repeat/empty/self/reference comparisons; retained bitwise/max-error flags; original-prefix/dummy/padding/generated masks validated at forced first/last steps; correct head versus group keys and immutable bank hashes/versions. Firsttoken scoring uses B8/L224 and the exact arm's mixed bank. Its full logits checksum and argmax must match decoder step0. Baseline versus every clean-clamp-only outcome must match complete generated token IDs and finish through EOS/cap. This remains necessary even if all firststeps agree. No numeric success is inferred from plausible text, old H200/L128 checksums or another arm.

Calibration600s is a proposal, not a fit claim. Fresh600s wrapper CPUdryrun must expose the exact full-cap guard and reserve. If calibration stops before all required operators/controls/receipts, main remains unreleased; preserve partial attempts and return the measured operational reason. Do not silently skip controls or enlarge the allocation.

## Forecast and next-batch admission

Initial main sizing uses actual natural timing **by arm** and the fixed main batch composition. Main has12baseline batches and24eight-pair groups×20operator batches=480intervention batches. Multiply observed natural per-arm elapsed plus measured publication/audit by those fixed counts; charge shared setup once per group or rebuilt setup once per arm according to actual implementation. Add model/software/cache/startup overhead and shutdown reserve **once**. Add a declared reasonable uncertainty multiplier, e.g.1.3–1.5 on measured variable work. Report raw measured work, uncertainty, fixed cost, expected total, requested allocation, and cap64 ceiling separately. Round a proposed request to convenient minutes after inspecting queue projections. No predetermined1,800/2,400/3,600s promise and no automatic inflation to the fullcap panel ceiling.

After main admission, whole-panel remaining forecasts are **advisory**. They are logged, not a reason to stop useful checkpointed progress. Before each physical arm batch, enforce a hard bounded-next-batch guard. A concrete conservative form is:

```
forward_bound = max(matching_calibration_max_forward, current_run_max_forward)
next_arm_bound = known_remaining_fullcap_forward_count * forward_bound * safety_factor
                 + setup_if_needed_bound + packing_descriptor_bound
                 + atomic_publication_audit_bound
admit iff now + next_arm_bound + shutdown_reserve < actual_Slurm_EndTime
```

Use the implementation's exact known maximum call count: a natural patched arm commonly needs128decode forwards for64steps×patch/repeat, plus any separately scored step0/control/setup calls that cannot be reused; baseline commonly needs66but extra controls must also be counted. Count the complete setup triple if banks need rebuilding. A prospective safety factor1.25–1.5 is reasonable; pin the exact formula/defaults in operations/protocol before calibration. Use maxima from the new matching hardware/software/shape and refresh from actual forwards, including slow cold/setup calls. A measured forced64 whole-arm elapsed bound is an additional check, not permission to ignore a slower fresh forward. Include measured serialization/publication bounds and shutdown reserve even when kernels are fast. Measure real Slurm deadline from scheduler start/end rather than assume job starts at wrapper entry.

At a failed next-batch guard, record a normal partial-stop terminal invocation, accepted IDs, exact remaining IDs, measured guard inputs and actual remaining time; publish/seal before exiting. Do not mark the entire scientific panel complete. Do not change the frozen guard midrun. Root can release an exact resume after verifying unchanged bindings and coverage; reservations are separately charged. Long panels can use multiple modest resumable allocations without shrinking science or reserving the extreme worst case upfront.

## Atomic acceptance and exact resume

Use a run lock and immutable run metadata: scientific hash, provenance/source closure, cache/config/tokenizer/shards, software, geometry/B8L224/BF16/SDPA/use_cacheFalse, input/mask/20arm/grid hashes, batch ordering and operations identity. Each invocation has a distinct allocation/JobID/start/end/reservation record; allocation/deadline fields belong to the invocation, while science/source/run identity remains fixed.

For each physical batch/arm, write an exclusive attempt record before inference. Write full terminal generations, firsttoken metrics, compact bank descriptors, controls and timings to a unique temporary file, serialize/validate/hash, fsync and atomically publish a content-bound terminal. Publish acceptance only after schema/source/control/row-ID/count validation and reference it by terminal hash. Never overwrite an accepted result. Retain failed/interrupted attempts and their bounded errors; acceptance and completeness derive from independently read/validated records, not the existence of a progress summary. On restart, handle terminal-without-acceptance crash gaps by deterministic validation/promotion or explicit interruption; never silently rerun a valid accepted outcome. The exact chosen rule must be covered by a regression test.

Before resuming, scan accepted terminals and verify all immutable hashes, exact disjoint planned IDs, controls, EOS/cap/error state, descriptor dimensions and generations. Require an explicit resume flag and same run/protocol; fail on unexpected files, mismatches, duplicate accepted IDs or missing dependencies. Rebuild all needed donor/recipient/U5 banks from frozen inputs, then execute only genuinely incomplete fixed arms. Keep accepted old bytes unchanged. Error/partial evidence is retained even when its incomplete arm is later rerun by an explicitly reviewed operational resume; no favorable-outcome retry or science inclusion change.

## Release/readiness evidence

Before root release: final exact-file commit and source closure; final protocol source/cache/software binding; independent task+whole-change review PASS; targeted base+mgnp tests and shell/ruff checks; actual absolute jobwrapper CPUdryrun against the final protocol and exact600s calibration operations; independently checked input counts/maps/masks/capfit and output-record size bounds; fresh read-only account/QOS/user-collision/test-only snapshot; absent output destination; writable log destination; and exact proposed reservation/argv. A changed source/protocol invalidates an old readiness receipt. A CPUdryrun never loads the model or claims numerical calibration PASS.

On root calibration release, append reservation to `../ledger.md` before one actual sbatch call. Save exact stdout/stderr/argv/time; record JobID only if truly submitted. Main release is separate, after complete numerical/timing calibration, independent receipts and a fresh measured walltime proposal. User's standing GPU permission does not override root's current no-submission delegation.

Suggested future receipt names under this operator directory: `final-source-binding.json`, `calibration-operations.json`, `calibration-cpu-readiness.json`, `calibration-reservation.json`, `calibration-submission.json`, `calibration-slurm-final.json`, `calibration-completion-audit.json`, then corresponding `main-*` and explicit `resume-N-*`. These are prospective filenames; no release/readiness success is asserted here. Use actual runner CLI fields once documented, not fabricated positional options.

No user confirmation is needed for the authorized preparation. No submitted jobs, reservations, GPU inference, model/notebook execution, paid API or other-job mutation occurred. Claude usage policy is service-specific; this worker runs Codex Sol.
