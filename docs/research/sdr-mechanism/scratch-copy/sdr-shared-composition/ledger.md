# Native SDR shared-composition compute ledger

Operator-owned numeric accounting. Scope: the separately ratified3,936-outcome/20-arm shared-composition study only. Historical SDR phases and other investigations are not charged here. Root releases each allocation; proposals and `sbatch --test-only` projections are not reservations. Calibration23232031 is complete (600reserved/157actualA100GPU-seconds). Main23232370 is complete with1320reserved/795actualGPU-seconds; phase1920reserved/952actualA100GPU-seconds. Historical preparation checkpoints retain their original states.

| Phase | Proposed seconds | Reserved GPU-seconds | Actual GPU-seconds | Paid API USD | Job/state |
|---|---:|---:|---:|---:|---|
| Preparation | 0 | 0 | 0 | 0.00 | Read-only scheduler/source inspection |
| Numerical/timing calibration | 600 root released, one GPU | 600 | 157 | 0.00 | 23232031 COMPLETED0:0/Restarts0 |
| Main / exact resume | 1320 root released | 1320 | 795 | 0.00 | 23232370 COMPLETED0:0/Restarts0; no resume |
| Total this study | 1920 released | **1920** | **952** | **0.00** | Calibration and main complete; no extra job |

2026-10-26T22:50:08Z preparation snapshot: no `squeue -u swong2` rows. Four GPU accounts have matching authorized QOS. Sixteen bounded `sbatch --test-only` projections created no allocations or submitted jobs. A100x4-interactive/beto,bimc,bgrb projected immediate600s starts; bjhz projected+2minutes. H200-interactive projected the following day; normal A100/H200 projected days later. These observations are dated, not dispatch guarantees. See `operator/scheduler-snapshot-20261026T225008Z.json` and `operator/preparation.md`.

Before submission, record root release, exact source/protocol/calibration/operations hashes, approved GPU class/account/QOS/partition, GPU count/time, invocation/output, argv and reservation timestamp. Increase reserved GPU-seconds **before** the one actual sbatch call; retain the reservation on rejection, cancellation, failure or retry. Record pending jobs as reserved. Record scheduler JobID only from an actual successful submission receipt, never the synthetic IDs printed by test-only.

After terminal scheduler state, record `sacct` state/exit/restarts/AllocTRES/ElapsedRaw and actualGPU-seconds = allocatedGPUcount×ElapsedRaw. Keep Python runner elapsed separately. Record wasted/incomplete attempts and any later separately released resume allocation; actual time does not refund reservations. No automatic retry, account move or extra allocation is authorized by this ledger.

Operator workspace ownership is `operator/` plus this numeric ledger. Root owns scientific scope, final release and git; implementation worker owns runner/tests/wrapper. Claude-service usage counters do not measure this Codex Sol operator's budget.

2026-10-26T23:38:43Z final CPU readiness PASS at committed source695b126a9d5fe3045c9b5872fac7441d8fcdeec2: final nonprovisional protocol science unchanged1a29813f, manifest959824dc;66sourcefiles match filesystem+committed blobs,10cachefiles independently rehashed/softwaremetadata matched,2,797independent input checks PASS, actual absolute-wrapper calibration CPUdryrun exit0 in42.068s and destination still absent. Fresh23:37:33Z exact600sA100x4-interactive/beto test-only immediate; no user collisions. Proposed oneA100/4CPU/64G/600s, .4initialforward/40sshutdown/+10sfixednonforwardfloor,8setupcalls/9coldallowances. See operator/final-readiness-695b126.json and calibration-command-proposal-695b126.txt. Root calibration release still required. **Reserved0/actual0GPU-seconds/$0API; no job submitted.**

2026-10-26T23:40:33.056035+00:00 ROOT CALIBRATION RELEASE: reserved600GPU-seconds BEFORE the single actual sbatch call; prior0,cumulative600. OneA100/600s/beto matchingQOS/A100x4-interactive/4CPU/64G. Added --no-requeue exactly as root instructed; no source/science/protocol/guard change. Fresh user queue empty/output absent. Submission outcome follows; reservation is retained even if submission fails. No automatic retry/resume/main.

2026-10-26T23:40:33.172373+00:00 Single sbatch result: SUBMITTED job23232031;600GPU-seconds remain reserved; actual pending final scheduler accounting. See operator/calibration-submission-695b126.json.

2026-10-26T23:46:53.552331+00:00 Calibration23232031COMPLETED0:0/Restarts0 ongpua016,18:42:07–18:44:44local;157actualA100GPU-seconds versus600reserved,$0API. HardwareA100-SXM4-40GB. Producercoverage23batches180rows(164EOS+16stress),0cap. Operatorchecks23acceptedhashes,8setupcalls,allobservedcontrolsbitwise/max0; independentrawaudit separate. Actualvariablemainforecast771.821569s×1.4=1080.550197s +startup76.330006s+shutdown40s=1196.880203s; proposed1320s22minmain,notreleased. Noadditionaljob/retry/resume. See operator/calibration-final-slurm-23232031.json and calibration-operator-timings-and-main-proposal-695b126.json.

2026-10-26T23:52:06.945136+00:00 ROOT MAIN RELEASE:1320mainGPU-seconds reserved BEFORE oneactualsbatch; calibration600reserved/157actual retained separately,cumulative1920reserved. Exactly reviewed22min1A100/beto+matchingQOS/A100x4-interactive/4CPU64G/--no-requeue command; unchanged695b126/959824dcscience1a29813f. Freshqueueempty,mainoutputabsent,66sourcehashesmatch,all76calibrationfilesunchanged. No automatic retry/resume/accountmove.

2026-10-26T23:52:07.044694+00:00 Main single sbatch result: SUBMITTED job23232370;1320main/1920cumulative GPU-seconds reserved,actualmainpending. See operator/main-submission-695b126.json.

2026-10-27T00:08:01.002292+00:00 Main23232370COMPLETED0:0/Restarts0 ongpua032,start18:52:10/end19:05:25local,795actualA100GPU-seconds versus1320reserved. Phase1920reserved/952actual(157cal+795main),$0API. Operatorhashedall492acceptedrecords/3936uniqueEOSrows;0cap/error/failure,24setupgroups8calls/group,all16608checkedcontrolsbitwise/max0. All76calibrationJSONs/66sourcefiles/protocol unchanged; matchingA100hardware. Independentraw/scientificaudit separate; no additionaljob/resume/retry/accountmove. See operator/main-final-slurm-23232370.json and main-operator-completion-summary-695b126.json.
