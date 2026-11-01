# Native SDR controls operational ledger

New phase authorized by continued investigation and standing permission to use additional GPU resources as needed. Scientific design PASS; source review and explicit root allocation release remain required. Lead compactions: **4**. Sparse polling preferred.

Prior SDR routing/completion phase is CLOSED and immutable: 7800 reserved GPU-sec,595 actual A100 GPU-sec,$0 API. Those reservations are retained; no borrowing or refunds. This ledger starts independently at zero and does not impose an inherited4-hour cap.

| Phase | Job ID | GPUs | Requested seconds | Reserved GPU-sec | Actual GPU-sec | State |
|---|---|---:|---:|---:|---:|---|
| Fresh sharding calibration | 23102317 | 1 | 600 | 600 | 112 | COMPLETED0:0;64rows/256bitwisecontrolsPASS |
| Main | 23101635 | 1 | 39600 | 39600 | 0 | CANCELLED whilePENDING/held;zeroattempts,fullreservationretained |
| Calibration | 23101432 | 1 | 600 | 600 | 111 | COMPLETED0:0;64rows/256controlsPASS;fullcapforecast38257.45sec |
| Shard 000 | 23102435 | 1 | 3600 | 3600 | 202 | COMPLETED; reservation retained |
| Shard 001 | 23102471 | 1 | 3600 | 3600 | 221 | COMPLETED; reservation retained |
| Shard 002 | 23102510 | 1 | 3600 | 3600 | 204 | COMPLETED; reservation retained |
| Shard 003 | 23102542 | 1 | 3600 | 3600 | 202 | COMPLETED; reservation retained |
| Shard 004 | 23102589 | 1 | 3600 | 3600 | 278 | COMPLETED; reservation retained |
| Shard 005 | 23102629 | 1 | 3600 | 3600 | 224 | COMPLETED; reservation retained |
| Shard 006 | 23102676 | 1 | 3600 | 3600 | 235 | COMPLETED; reservation retained |
| Shard 007 | 23103061 | 1 | 3600 | 3600 | 252 | COMPLETED; reservation retained |
| Shard 008 | 23103396 | 1 | 3600 | 3600 | 270 | COMPLETED; reservation retained |
| Shard 009 | 23103724 | 1 | 3600 | 3600 | 251 | COMPLETED; reservation retained |
| Shard 010 | 23103989 | 1 | 3600 | 3600 | 272 | COMPLETED; reservation retained |
| Shard 011 | 23104611 | 1 | 3600 | 3600 | 132 | COMPLETED; reservation retained |
| Preparation | none | 0 | 0 | 0 | 0 | Read-only scheduler/account/design preflight; no allocation |

New phase reserved used: **84000 GPU-sec**. Actual used: **2966 A100 GPU-sec**. API spend: **$0**.

Operator alone owns numeric rows and operator receipts. Reserve full walltime×GPU count BEFORE submission; failed/pending reservations retained, no refunds, retries, or automatic expansion. Root releases reviewed frozen source and each allocation. Prospective initial calibration: oneH200≤600sec,64 fixedrows/eight batches, excluded main/labels. Main allocation must fit measured FULL64-token-cap forward/control forecast with startup/I/O/shutdown buffers, bound to identical scientific payload/source/import/model/tokenizer/config/software/B/L and exact actual GPU identity; no automatic hardware transfer. Operational JSON hashes budgets/deadlines separately from science.

Submit only new scripts/jobs/run_sdr_native_controls.sh from absolute pilot worktree with explicit --chdir and command-line --time, after actual-wrapper CPU dry-run. No model on login, paid API, notebooks, git/source changes or unrelated-job mutations. Prior selective-v4 jobs are outside this phase; leave their settings/resources untouched. Fresh scheduler/account projection required at actual release; sparse polling during execution.

Nativecalibrationreservation 20261021T162227Z:oneA100600sec BEFOREsubmission, newphase600reserved/0actual, previousphasesuntouched. Rootexplicitrelease; source15603235/science52f38609/prov0f6b9d50/protocolSHA0a222b15 verifiedCPUincludingcachedependencies; actualwrappercal/mainCPUdryrunsPASS, shape8x224,64fixedcalrows/3072main. Betotiedearliestfreshprojection11:22:02local; explicitcwd/--chdir/CLI10min/nvidia_a100. Operationsproposalhash preserved; wrapperbindsactualallocationend, internalstopminus90shutdownonce. Noauto retry/main. Receipt operator/calibration-reserved-launch-15603235.json.

Nativecalibrationacceptedjob23101432;600reservedbefore submit; receiptoperator/calibration-submission-receipt.json.

Nativecalibration23101432 COMPLETED0:0,111SlurmA100GPU-sec;64/64fixedrows/eightbatches,256repeat/empty/fullcomponentbaseline/selfreplacementreceiptsALLPASS/bitwise/maxerror0,102forwards; exactA100-SXM4-40GBcap8.0memory42405855232,count1;peakallocated19206646784/reserved21011365888. Full64cap25344forward+49920activecheckpoint+772panelcheckpointx48forecast38257.4523sec; maxforward0.500118654,maxactivecheckpoint0.257943348,maxpanelcheckpoint0.332820781. ProposedSAMExactA100main39600sec(11h) regularpartition ONLY, notreserved/submitted. Newphasetotals600reserved/111actual,$0API; oldledgersuntouched. Receiptoperator/calibration-completion-23101432.json.

Native mainreservation 20261021T162933Z:oneSAMExactA10039600sec(11h) BEFOREsubmit; prior600/newphase40200reserved,actual111; oldphaseledgersuntouched. Rootexplicitrelease/completecal23101432PASS; frozen15603235/science52f38609/B8L224. ActualmainwrapperCPUdryrun verified calibrationstaticbindingandforecast38257.4523fits39600; actualGPUidentity correctlypendingallocation. BestaccountbimcprojectedOct31 09:41:44local anomalous but rootrequests singlesubmit; regularA100x4only/CLI11h/explicitcwd/nvidia_a100. Denominator3072/max64/fullIObound preserved; noauto cancel/retry/sourcechange. Receiptoperator/main-reserved-launch-15603235.json.

Native mainacceptedjob23101635;39600main/40200phaseGPU-sec reservedBEFOREsubmission;receiptoperator/main-submission-receipt.json.

Native main23101635 conditionalrootcancellation:verifiedPENDING/RunTime0/nooutput,heldsuccessfully,reverifiedPENDING/RunTime0/nooutput,scancel--state=PENDINGonly succeeded. sacctterminalCANCELLED,ElapsedRaw0,StartNone,AllocTRESempty;0modelattempts/0actualGPU-sec. FULL39600reservation retained, newphasetotal40200reserved/111actual,$0API. Nootherjobs/artifactstouched. Explicitzeroattemptsourceunlockevidence operator/main-conditional-cancel-23101635.json; no newjobs released.

Freshnativecalibrationreservation 20261021T170942Z:oneexactA100600sec BEFOREsubmit; prior40200/new40800reserved,actual111; canceled39600fullyretained, oldphasesimmutable. Rootexplicitrelease/source1eb79892science52f38609prov05c1d8b8/protocolSHA1196d156/currentdependenciesverified; actualwrapperCPUdryrunPASS64rowsB8L224. Bimcearliestfresh12:09:27local; CLI10min/explicitcwd/nvidia_a100/allcompatibleA100partitions. Leadcompactions4; oldreceiptsremainhistorical. Noautoretry/main. Receiptoperator/calibration-reserved-launch-1eb79892.json.

Freshnativecalibrationacceptedjob23102317;40800phaseGPU-secreservedbefore submit; receiptoperator/calibration-sharding-submission-receipt.json.

Freshshardingcal23102317 COMPLETED0:0,112SlurmA100GPU-sec;64unique/EOS/8fixedbatches,256controlsallbitwisePASS/maxabs0,102forwards,source1eb79892/science52f38609/prov05c1d8b8/exactA100/B8L224. Premodel50.354322sec measuredactualSlurmStart, maxforward0.423913434sec; fullpanel33554.964338s conservativebound beforefuturefixedrangeplanning. Newphase40800reserved/223actual,$0API; old39600canceledreservationretained. Receiptoperator/calibration-completion-23102317.json.

All12fixedshardsCOMPLETE/validated,strictCPUmergePASS /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-native-controls/merged-1eb79892-20261021T182825Z:all384physicalbatches/3072uniqueoriginalrowsattempted/completedonce,6144repeat/emptycontrolsPASS; exactplan1e72decf/source1eb79892/science52f38609/B8L224/actualA100binding retained. ShardSlurmactual2743GPU-sec plus223prior=2966nativeactual;43200shards+40800prior=84000reserved,including39600cancelledretained,$0API. Independentintegrityauditpending; noannotationexport. Completionauditoperator/main-completion-audit.json,allterminalaccountingoperator/all-shards-slurm-accounting.txt,mergeinvocationoperator/strict-merge-receipt.json.

## Terminal closure (supersedes pending downstream status above)

Nativephase COMPLETE; independentfull-runintegrityPASS (`main-integrity-review.md`),332uniqueviewfreshdoubleblindannotations+6thirdblindadjudicationscoverall3072rows; frozenbehavioranalysisFAIL30/105. Finalreportreview closurePASS reportedbyroot; no causalnextstage and no furtherjobsplanned. Earlierpendingannotation/integrityentriesremainhistorical. Leadcompactions4. FinalnativeaccountingUNCHANGED:84000reservedGPU-sec,2966actualA100GPU-sec,$0API; allfailed/pending/cancelledreservationsretainedincluding39600zeroattemptcancellation. Priorphases/source/artifactsimmutable.
