# SDR routing validation ledger

User authorization2026-10-21: “Good, please continue. Feel free to use more GPU resources as needed.” This phase is separate from the completed immutable pilot.

Initial INTERNAL operational envelope: **14400 additional reserved H200 GPU-seconds (4GPU-hours)**. This is not a user total cap. Zero paid APIs. Lead compactions: **2**. No old-pilot unused reservations are borrowed; all old-pilot artifacts/ledger remain immutable.

| Phase | Job ID | GPUs | Requested seconds | Reserved GPU-sec | Actual GPU-sec | State |
|---|---|---:|---:|---:|---:|---|
| Completion main | 23099381 | 1 | 3600 | 3600 | 252 | COMPLETED0:0;1280checksumPASS,1280EOS,709forwards |
| Completion calibration | 23098326 | 1 | 600 | 600 | 152 | COMPLETED0:0;1280checksumPASS; fullcapforecast3207.80>3000, no main |
| Preparation | none | 0 | 0 | 0 | 0 | Read-only scheduler/protocol preflight; no allocation |
| Baselines A100 attempt2 | 23094295 | 1 | 1800 | 1800 | 191 | Reserved BEFORE sbatch; commitcda2160/reviewPASS/v6manifestPASS |
| Baselines H200 attempt1 | 23093790 | 1 | 1800 | 1800 | 0 | CANCELLED while PENDING by lead instruction; never allocated; reservation retained |

Reserved used: **7800/14400 GPU-sec**. Remaining internal envelope: **6600 GPU-sec**. Actual used: **595 A100 GPU-sec**. API spend: **$0**.

Operator alone owns numeric rows and operator receipts. Atomically record allocation time×GPU count BEFORE submission; pending jobs and failed allocations count, actual runtime never refunds reservations. No automatic retries, expansion or source changes. Lead must explicitly release reviewed frozen source/protocol before first submission. Baseline/validity and path allocations require their written gates; forecast insufficient for the full mandatory grid stops rather than dropping cells. Any contingency requires explicit receipt/lead instruction.

New output root: outputs/_analyses/sdr-routing-validation/<run-id>/. Actual new-wrapper CPU dry-run, frozen manifest/source/tokenizer/model hashes, exact counts and forward forecast are required before submission. Submit from the absolute pilot worktree and use explicit sbatch --chdir to the same path (Slurm spool-path failure in old pilot). Command-line --time is mandatory. One H200, no paid inference/network downloads/notebooks/training/v2 evaluation.

Protocol hierarchy: frozen spec.md controls over design-options.md when they differ. In particular the1280-row ordinary union is MANDATORY; full45824 scientific-row grid cannot be silently dropped or pruned for time. Baseline1280 rows and whole-panel neutral retrieval>=80% pertemplate×truth gate precede paths. Zero minimum stakes/patch/emission threshold; failed gate ends protocol without prompt edits/top-ups.

Baseline reservation 20261021T131953Z:oneH200×1800sec,prior0,newphasecumulative1800/14400internalenvelope,remaining12600. Leadexplicitrelease; sourcecommitd81f529clean; actualwrapperCPUv4exit0 andmanifesthashd3a405daec52bfa07ee20f1cf6de222dda780c33c1991b72d739abbbbb3dd608 verifiedcanonically. All42source+14code+6tokenizer+6modeldependencyhashesandsoftwareverified. Freshschedulerbgrbearliest09:16:57local; allocatedtimeCLI30min,explicitsubmissioncwd/--chdirsameworktree,offlineflags. Output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-validation/baseline-d81f529-20261021T131953Z. Noautomaticretry/paths.

Baselineacceptedjob23093790,bgrb/oneH200/30min,prior0; ledgerreserved1800BEFOREsubmission. Receiptoperator/baseline-submission-receipt.json.

Hardware scheduling decision: leadauthorizesA100forBOTHvalidationstages subjectreviewedminimalhardwaregatepatch+reboundmanifest. Job23093790verifiedPENDING,thenconditional `scancel --state=PENDING 23093790` succeeded. sacctterminalCANCELLEDby78031,ElapsedRaw0,StartNone,AllocTRESempty,End2026-10-21T08:23:26local. Reserved1800H200GPU-sec remainsconsumed(no refund),actual0. NextproposedA1001800secwouldbringcumulative3600/14400; NOTyetreserved/submitted. Otherjobsuntouched.

A100baseline reservation 20261021T133612Z:oneA100×1800sec,prior1800cancelledH200reservationretained,total3600/14400internalGPU-seconds,remaining10800. Hardwareweightedcostsarenotpooled; reservedwallGPUtime isunweighted,actualdeviceclass/name/capabilityrecorded. Leadexplicitrelease; sourcecommitcda2160clean; all42source14code6tokenizer6modelhashes/softwareverified; v6actualwrapperCPUexit0; manifestinternalhashee1e5e279e5f7880a90f9e42ab663ee2da17acd8f02ef77dd7b4bb825ed632dc andscientificpayloadsamev4. CorrectGRESnvidia_a100,explicitcwd/--chdir,CLI30min. Output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-validation/baseline-cda2160-20261021T133612Z. BaselineandfuturepathsMUSTuseA100classwithstrictnumerics. Noautoretry/paths.

A100baselineacceptedjob23094295,bgrb/oneA100/30min,prior1800; ledgerreserved3600cumulativeBEFOREsubmission. Receiptoperator/baseline-a100-submission-receipt.json.

BaselineA100completion23094295:COMPLETED0:0,sacct191actualGPU-sec;1280/1280baselines,no malformed IDs;325forwards,163numericalreceiptsALLPASS/bitwise,maxabs0. GPU NVIDIAA100-SXM4-40GB,classA100,cap8.0,total42.406GB;peak19.091GB;modelload37.443s,eightstoryforward0.39136s. FINALwholepanelvalidityFAILpaths_go=false: neutralretrieval Atruth0=38/64(59.375%),Atruth1=40/64(62.5%)below80%;Btruth0=62/64(96.875%),Btruth1=59/64(92.1875%)pass. Failedfactualcontrolstratumendsfrozenconfirmatoryprotocol;no paths/no prompt edits/top-ups/no retry. Newphasecumulative3600/14400reserved(1800cancelledH200retained+1800A100),actual191A100+0H200;10800internalunused,$0API. Output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-validation/baseline-cda2160-20261021T133612Z;gateSHAe6eebbe29f6d5ba102c89e85a4b60e24fb22e9a73f34aa3ff67d3e3c491afbbd. Fullreceiptoperator/baseline-a100-completion-23094295.json. Runtimepathforecast8966.8swasconservativeupperboundandcannotreleasefailedprotocol.

Completion calibration reservation 20261021T142417Z: one A100 x600sec reserved BEFORE submission; globalprior3600 (including canceled1800H200 retained), newglobal4200/14400, remaining10200; diagnosticprior0/new600. Frozen962cdd8, allparent/config/model/tokenizer/newsource hashes verified; exact CPUwrapper calibration/main dryruns PASS; finalreview/rootexplicitrelease. CLI10min, explicitcwd/--chdir, GRESnvidia_a100. All1280checksum replays then64first8physicalbatch continuations, excluded main; no retry/main automatically. Receipt operator/completion-calibration-reserved-launch.json.

Completion calibration accepted job23098326; oneA100600sec,4200cumulative reserved BEFORE submit; source962cdd8. Receipt operator/completion-calibration-submission-receipt.json.

Completion calibration23098326 COMPLETED0:0; actual152A100GPU-sec (runner139.22s), exactparentA100device, all1280firststepchecksPASS,160replay+23continuation=183forwards,64fixedcalibrationrows excludedmain. Full5120forward/max40960token forecast3207.800964s including audit65.129/load14.564/replay55.121/continuation1708.747/checkpointIO650.679,1.25safety+90shutdown => DOESNOTFIT3000mainbound. No main reservation/submission/retry. Cumulative4200/14400reserved (600diagnostic, canceled1800H200retained),343actualA100,10200remaining,$0API. Terminalreceipt operator/completion-calibration-completion-23098326.json.

Completion main reservation 20261021T143743Z: oneA100x3600sec BEFORE submit; globalprior4200/new7800/14400, remaining6600, diagnosticprior600/new4200. ScopedoperationalamendmentreviewPASS/rootexplicitrelease, frozenb7299d8/manifestded4970; fullparent/model/tokenizer/source/software+historicalcalibrationbinding verified. Forecast3207.800964 historicalfits3000false; actualfits3600true, scientificpayload1bea1758 unchanged. CLI1h, explicitcwd/--chdir, nvidia_a100; fresh1280checksumreplays then all1280unchangedpromptcompletions; calibrationexcluded, noauto retry. Receipt operator/completion-main-reserved-launch.json.

Completion main accepted job23099381; oneA1003600sec,7800cumulative/4200diagnostic reserved BEFORE submit; sourceb7299d8. Receipt operator/completion-main-submission-receipt.json.

Completion main23099381 COMPLETED0:0,252SlurmA100GPU-sec (runner237.542s); exactparentA100,all1280freshchecksumPASS/all1280uniqueunchangedplannedrowsattempted andcompletedEOS,0caps/errors/missing;709physicalforwards. Parentfilesimmutable,calibrationexcluded;peakmetricnotpersisted. Cumulative7800/14400reserved,diagnostic4200;595actualA100GPU-sec,6600remaininginternal,$0API. Noadditionaljobs/retry; annotationseparate. Receipt operator/completion-main-completion-23099381.json.
