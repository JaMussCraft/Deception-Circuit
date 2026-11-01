# Clause-choice compute ledger

2026-10-26. Independent original SDR baseline study. This ledger does not consume or alter another thread's budget.

| Entry | State | Resource | Reserved GPU seconds | Actual GPU seconds | API USD |
|---|---|---|---:|---:|---:|
| Operator read-only preparation | Complete | Delta queue/config queries | 0 | 0 | 0 |
| Prospective placement checks | Complete | 20 `sbatch --test-only` cases; no jobs submitted | 0 | 0 | 0 |
| Baseline32preflight+640main | 23218707 terminal admission stop;32preflight+296main retained;remaining completed by explicit resume | 1A100/4CPU/64G/15min, beto-delta-gpu + gpuA100x4-interactive | 900 | 259 | 0 |
| Explicit resume001 | 23218994 COMPLETED0:0;344newmain;final640main+32preflight acquired | Same checkpoint/source/manifest/A100 class; --resume | 900 | 287 | 0 |
| Conditional original-head assay | Unreleased | Separate later phase; no reservation | 0 | 0 | 0 |
| **Total booked/used** | | | **1800** | **546** | **0** |

The pending baseline proposal would reserve900GPU-seconds (0.25GPU-h) when and only when root explicitly releases it. Expected4–8min is an orientation from archived unchanged-kernel runs, not a runtime claim. Cap64 controls and all640main denominators remain fixed. Deadline guard/atomic accepted batches support an explicitly released later resume if necessary; no automatic submission or retry.

Evidence: `operator/availability-20261026T1500Z.json`, `operator/test-only-20261026T1500Z.json`, `operator/preparation-summary.json`, `operator/proposal.md`. Exact timestamps inside receipts are authoritative. Test-only output IDs are scheduler test identifiers, not actual jobs; do not book or query them as submitted jobs.

Before booking/submission: final committed source/review, frozen manifest/masks/maps, actual-wrapper CPU dry-run/deadline checks, one fresh collision/ownership check and chosen test-only forecast, then root release. Append the actual job ID, source/manifest/invocation hashes, accepted invocation reservation, allocation StartTime/EndTime/AllocTRES and terminal elapsed/exit receipt. Keep reserved versus actual charges separate; do not subtract an unused reservation unless root's stated accounting policy allows it. Re-read this file before any update to preserve concurrent edits.


## Final committed CPU readiness — 2026-10-26

Operator readiness PASS against source `4f0278487b0285dd27cbc34d20d88c911dc5562a`; manifest `10e2e8a7c2cc1f397b02d6b917533459d7dc242478d81212ed015eab56f01070`, science unchanged. Actual absolute-wrapper mgnp CPU dry-run exited0 in51.4303s,640main/32preflight,max-prefix125,model_loaded=false,output_mutated=false; unused output path remains absent. `bash -n` and three CPU-only numeric/fallback/invalid-interval wrapper probes PASS. Receipt/source/manifest hashes are recorded in `operator/readiness-final-4f02784.json`.

**Still0reservedGPU-seconds,0actualGPU-seconds,$0API; no job submitted.** Independent final source/input review and final chosen queue/collision check remain root release gates. The prospective invocation is recorded as argv only, not executed. Actual implementation is fixed900s; if main admission fails, retain measured preflight and report to root, with no automatic identical-job retry. Explicit amendment/resume requires root decision.


## Root single-allocation release and reservation — 2026-10-26T15:44:20.567137+00:00

All final review/CPU gates released by root. Fresh source/manifest/fresh-output/queue-collision check PASS; no user jobs; single chosen test-only forecast immediate. **900GPU-seconds (0.25GPU-h) booked before sbatch** in `operator/reservation-final-4f02784-001.json`. Invocation SHA256 `65e4f4f717a7e61d1f874bb29287df3f48fd9ac490185fbbc911efb38848bbba`. Exactly one submission attempt is authorized and its guard is consumed. No automatic retry, requeue, resume or identical follow-up. Source4f02784 and all scientific inputs/gates stay frozen. Prior zero-reservation sections above are historical CPU checkpoints.

Submission result: **SUBMITTED** job`23218707`. Receipt `operator/submission-final-4f02784-001.json`;900GPU-seconds remain booked,actual pending,$0API.


## Terminal accounting — 2026-10-26T15:52:29.972836+00:00

Job`23218707` **FAILED1:0/259s/0restarts**, gpua001 A100-SXM4-40GB; intentional reviewed TimeoutError admission stop beforemain-037 (no active partial batch),not a Slurm walltime kill. **900GPU-seconds remain reserved;259actualGPU-seconds,$0API.**41immutable accepted batches retain32excluded preflight+296/640main (295EOS,1cap64);344main/43batches remain. Independent retained JSON audit PASS_PARTIAL:656/656 numerical controls bitwise,finite,identicalgreedy,maxerror0;328firststep identities. All66source closure files and frozen manifest unchanged.

Initial main admitted at672.6802s forecast vs807.7691s remaining. At stop, updated all-remaining forecast781.0188s exceeded646.4218s available, using global maximum observed batchmain-036=10.7135s. Separate full-cap next-batch guard127.3065s would fit; the whole-remaining forecast caused the stop. Report`operator/completion-accounting-23218707.json`, audit`operator/retained-audit-23218707.json`. **No retry/resume submitted; root operational decision required.** Do not infer scientific gates from this incomplete panel or replace the capped row.


## Explicit resume001 CPU closure and second reservation — 2026-10-26T16:00:44.369701+00:00

Actual absolute-wrapper `--resume --dry-run` PASS49.0000s,model_loaded=false/output_mutated=false. Readonly committed validators accept41batches/328rows and reuse4preflight batches;43main batches/344rows remain beginningmain-037. All129oldcheckpoint file bytes,including41accepted terminals and oldfailure,unchanged against archived snapshot. Root independent partial raw audit SAFE_TO_RESUME:9159assertions/0errors. Fresh queue shows other-thread23218961onA40interactive untouched; noA100x4interactive collision; chosen test-only immediate.

Root explicitly released ONE further900s resume with unchanged code/science/guards andsameA100hardware. **Second900GPU-seconds booked before sbatch;combined1800reserved**,259actual fromfirstjob+secondactualpending,$0API. Resume guard consumed; no automatic additional retry/resume. `operator/reservation-resume-001.json` binds exactargv/checkpoint snapshot; `operator/resume-cpu-readiness-001.json` recordsCPUeligibility.

Resume001 submission **SUBMITTED_EXPLICIT_RESUME** job`23218994`. Receipt `operator/submission-resume-001.json`;1800combinedGPU-seconds reserved;259prior actual+secondpending;$0API.


## Baseline acquisition complete after explicit resume — 2026-10-26T16:07:55.568698+00:00

Resume`23218994` **COMPLETED0:0/287s/0restarts** ongpua064, same NVIDIAA100-SXM4-40GB hardware/software identity asfirstjob. Exactly43new accepted batches complete the remaining344main rows,with no repeated accepted work. Final84batches/672unique rows:640main (639EOS,1cap64) plus32excludedpreflightEOS;0remaining. Original41accepted terminals andalloldimmutablecheckpointfiles,includingoldTimeoutError failure,are byte-identical.

CPU retained audit PASS_COMPLETE:1344/1344 finite/identicalgreedy controls bitwise,maxerror0;672firststepidentities. Everyattempt admission reconstructed against itsownallocation PASS. Resumeinitialforecast781.0188s fit827.4202s remaining; guards unchanged. Finalsource66-file closure,manifest/science unchanged. **Combined1800reservedGPU-seconds (0.5GPU-h),546actualGPU-seconds (0.1516667GPU-h),$0API**;unusedreservation notsubtracted. No extra/automaticjobs,requeue,otherthreadmutation orB2.

Final archive`archive-8446ad86f988cfa00558d37b864497117359a3cb47d8d681144de4de59e4b24b.json` SHA256`48196fcca8a577bce3a0fdb6849e0dfc2e28338435598d43e7564cb8503936f0`. Receipts`operator/completion-accounting-resumed-final.json` and`operator/retained-audit-resume-23218994.json`. Acquisition/operatorcheckscomplete;semantic annotation,scientificgates andanyconditionalheadassayremain root-owned/unreleased.
