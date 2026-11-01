# Original SDR position follow-up cost ledger

2026-10-25. Lead compactions7. Current state: calibration23194317 completed403s. Main23194944 completed1109s. Phase4500GPUseconds reserved,1512actual (403cal+1109main); independentfinal4224-rowauditpending.

| Phase | Proposed GPU seconds | Reserved GPU seconds | Actual GPU seconds | Paid API USD | Job IDs |
|---|---:|---:|---:|---:|---|
| Calibration | 1200 root-selected A100x4 | 1200 | 403 | 0.00 | 23194317 COMPLETED |
| Main/resume | 3300 root-released | 3300 | 1109 | 0.00 | 23194944 COMPLETED |
| Total this follow-up | both allocations complete | 4500 | 1512 | 0.00 | cal23194317; main23194944 |

Root-selected calibration proposal is one A100 on gpuA100x4-interactive for1200s,4CPUs/64G, underbeto with matchingQOS. Calibration was subsequently root-released and completed; the table above records actual/reserved cost. Main3300s was subsequently root-released and completed as23194944 in1109s; phase final accounting is4500reserved/1512actualGPUseconds,$0API. See [resource proposal](operator/resource-proposal-selected-a100x4-1200.json) and [operator procedure](operator/preparation.md). Only the released calibration has run in this follow-up. Historical parent calibration663s and main1186s belong to the completed prior phase and are not charged here.

Before each released submission, append its exact reservation, account/QOS, requested seconds, source/protocol/operations hashes and argv; write reservation before sbatch and preserve it on rejection/cancellation. After completion append final sacct elapsed/state/exit/restarts and multiply elapsed by allocatedGPUcount for actualGPUseconds. Record wasted operational attempts separately without removing original reserved cost. Record every resumed invocation and only its remaining fixed batches. Other agents own their jobs and costs; job23191980 is excluded.

2026-10-25 sizing correction from root: target600s after final-source actual-wrapper dry-run, optionally900s when measured preflight/control cost warrants it. Initial20min suggestion is superseded; no reserved/actual cost changed. New forced P/P-repeat suites have roughly800–1000forwards, versus5460 in the old14arm calibration; the old44GBIO benchmark is absent. Expected2–5min is provisional rather than a fit claim.

2026-10-25 hardware selection: after14successful non-submitting scheduler projections, root selected A100x4-interactive1200scalibration underbeto. NoGPUrelease/reservation/submission. User A100x4 interactive ownership must be rechecked immediately before release/submission; noA100x8 concurrentjob and noH200job/controller changes. Main remains unselected until fresh sameexactA100class calibration; observedwork×1.5 plus reasonablefixedcost must fit3600s or separatelyreleased durable resume. ParentH200full replay is explicitly hardwarechanged rather than a bitwise expectation.

2026-10-25 implementation count correction: workerreport relayed by root gives263physicalforwards per forcedarm,1578total across6arms,134checks perforcedrow, plus7naturalbatches and2familyE-systemnullchecks. This supersedes the historical rough800–1000estimate; independentcode review still pending. Provisionalselectedoperator mgnpCPUwrapperdryrun is running with1200s operations and360s explicitbuffers. NoGPUreservation/submission or inference; costs remain0.

2026-10-25 provisional operator v1 CPUwrapper result:112.82s,exit1,~1.09GiBRSS, fail-closed frozen-source mismatch during expected concurrent workerfix (testsource changed). Protocol unchanged and dryrun output absent; preserved intermediate evidence in operator/provisional-wrapper-a100x4-1200-20261025T155404Z. This is not readinessPASS and did not reach operationsvalidation. No more expensiveverification until root finalv2/committedfreeze. GPUreserved/actual/API remain0.

2026-10-25 final committed operatorCPU readinessPASS at2949214: one actualmgnpabsolutewrapper call100.906s,exit0,allfrozen-source/protocol/ops hashes unchanged,13calibrationbatches planned and nooutput/runmutation. Exacttestedops1200sA100 plus60/180/60/60sbuffers with48hadmissionhorizon (2026-10-27T16:31:25UTC), actualSlurmEnd bindsruntime; expiryneedsfreshrootrelease. Once-refreshed A100x4 userownershipempty and beto1200stest-onlyimmediate. See operator/final-calibration-readiness-2949214.json. CPUreadiness is not GPUrelease or numericalcalibration; independentfinalmanifest gate/rootrelease/immediateslotrecheck remain. Reserved/actualGPU/API remain0.

2026-10-25T16:37:38.652593+00:00 ROOT RELEASE calibrationonly: immediateuserownership/source/protocol/ops/output checksPASS. Reserved1200GPUseconds before exactONEsbatch; retainreservation eveniffailure. Source2949214, protocolb2c7fd65, ops2ee7ae1b. Actualcost pendingfinalsacct; mainunreleased. See operator/calibration-reservation-2949214.json.

2026-10-25T16:37:41.458717+00:00 Submission result: SUBMITTED job23194317;1200GPUseconds reserved,actualpendingfinalsacct,noautomaticretry,nomainrelease.

2026-10-25T16:47:58.284548+00:00 Calibration terminal accounting: job23194317 COMPLETED0:0,restarts0,403actualA100GPUseconds,1200reserved,$0API. Independentoperator sealedjournal/control/mask/provenance/timing auditPASS:13batches104calrows,6432forcedchecks, allnumericalchecksbitwise, systemnoopsPASS. ExacthardwareNVIDIAA100-SXM4-40GB; peak18504303616bytes. See operator/calibration-completion-summary-2949214.json. Mainunreleased,noautomaticretry/extrajob.

2026-10-25T16:51:39.264410+00:00 Mainproposal only:3300sA100x4-interactive55min,0mainreservation. Actualfinalpositionsrunnerforecast andindependentauditor agree1897.595770s naturalelapsed+seal+publication work×1.5+360.380435sfixedcost=3206.774090sbufferedexpectation; safe-batchguard188.889931s. Correctedearlieroperatorcopyformula omitting0.244004sseal; no source/measurementchange. SingleactualmainCPUwrapperdryrunactive; actualSlurmdeadline/preflight/resumegatesremain, mainnotreleased.

2026-10-25T16:53:25.328131+00:00 MainoperatorCPUreadinessPASS: exactactualmgnpabsolutewrapper88.705s,exit0,528remaining/4224rows,0accepted,nooutput/runmutation,allfrozenhashesunchanged. Proposed3300s55minA100x4/beto,expected3206.774swith50%bufferandfixedcost,safebatch188.890s. Actualpositionsrunnerforecastmatchesindependentaudit. Rootmainrelease/immediateslot+hashchecksremainrequired; mainreserved/actual0, phase1200reserved/403actual/$0API. See operator/main-readiness-3300-2949214.json.

2026-10-25T16:55:29.846874+00:00 ROOTMAINRELEASE: immediateownership/source/protocol/fullcalintegrity/ops/admission/outputchecksPASS. Reserved3300GPUseconds beforeexactONEmainsbatch, phase4500reserved/403actualplusmainpending. Noautomaticsecondjob/retry/substitution. Mainpartialstop permitted; accepted/remainingstate mustbesummarizedforroot. See operator/main-reservation-3300-2949214.json.

2026-10-25T16:55:30.006315+00:00 Mainsubmission result SUBMITTED job23194944;3300mainGPUsecondsreserved,phase4500reserved,actualmainpendingfinalsacct; noautomaticretry/extrajob.

2026-10-25T17:20:36.901965+00:00 Mainterminalaccounting:23194944 COMPLETED0:0,restarts0,1109actualA100GPUseconds,3300reserved. Phase4500reserved/1512actual/$0API. Operatorretainedcoverage/control/provenancecheckPASS:528accepted/528planned,4224uniquerows,0remaining/incomplete/interruptions/failures,all15411numericalchecks bitwise,maxerror0. Peak18311262208bytes. NoextraGPUjob. Finalindependent4224-rowacceptance remainswithroot/taskreviewer. Receipts operator/main-final-slurm-receipt-2949214.json,main-operator-completion-summary-2949214.json,main-accepted-coverage-2949214.json.
