# Execution ledger — selective-deception

Spec: `.scratch/selective-deception/spec.md`. Scientific plan: `project_context/research_notes/Deception specificity and shared circuits/next_steps.md`.

## Current checkpoint — diagnostic phase closed

2026-10-18: Stage1, the frozen SDR wrapper check, native instructed-lying feasibility, and the fixed-zero comparison are complete. Both SDR generation and the shared-core selective-transfer route stopped under prespecified criteria. No mask trained. Core coherent D suppression3/14 vs random14/14; Hretention12/15 vs14/15; optimistic core suppression remains<=9/14. See reports48/49/50 and the scientific diagnostic note.

All8 research jobs terminal. Reserved4.0/20GPUh; actual2434GPUseconds (40m34s); zero paidAPI. Lead compactions5confirmed. Both worktrees have clean tracked status; main untouched. Current concise recovery instructions are in RESUME.md. Earlier paragraphs below are historical run logs, not pending actions. Report49's benign recoding control is a costed future proposal, not a submitted job or released optimization stage.

## Historical task log

- Reconnaissance: diagnostic_map (existing APIs/gaps), current_artifacts (data/masks/runtime/scoring state), execution_adviser (Astra design/budget review). Read-only; reports in /tmp/selective-*.md to be copied here.
- Baseline tests: pending worktree creation.
- Implementation brief: pending recon; keep scope to first diagnostic stage.
- Independent review, dry-run, GPU run, analysis: pending.

## Decisions

- Flat team, no depth/settings increase, bounded fresh worker briefs.
- Only root submits jobs; reserve maximum time before submission; no automatic retries.
- Keep paid judging out of stage 1 because current scoring is known to have a credit failure and new spend has no agreed cap.
- Coherent refusal remains success. Synthetic task-label metrics are diagnostic proxies, not raw benchmark deception.

## Recovery

Read this ledger, spec, current task reports and compute-ledger.json before acting. Check actual worktree HEAD/status and sacct for recorded jobs. Never resubmit on squeue absence alone. Advance the first unfinished task; do not repeat completed experiments. Root transcript is not the authoritative run-state record.

2026-10-18 user budget amendment: up to 20 cumulative GPU-hours and parallel jobs authorized. Root sets max 2 concurrent jobs; initial diagnostic still targets ~2 hours, remainder available for justified pilot. No reservations or launches yet. Paid API cap unchanged at zero.

Worktree creation completed; HEAD 9d9c2a9. CPU baseline pytest launched offline in both supported environments (mgnp exec93095, base exec70532); logs reports/baseline-{mgnp,base}.log. Astra preflight report saved reports/00-execution-advice.md; its 2h cap paragraph predates user budget amendment and is now only a stage1 target. Scientist caveat: same-record deceptive donor is identity/no-op, not independent evidence; planned designation/policy cross must test response content separately.

Task1 manifest_impl dispatched fresh Sol with issues/01-manifest.md; owns only pure manifest helper/tests. No code commits yet. Plan saved plan.md. Base-env baseline finished: 7failed/1343passed/77skipped, 216.81s; failures include known worktree MASK-path and six task fixtures, length-matching now passes. mgnp baseline still running. Fresh budget20h, no reservations.

Preparatory sparse-pilot audit found a critical reuse hazard: matched_honest_survivors.json describes the test split, while existing loader can filter arbitrary requested IDs against it without split guard. Stage2 must build aligned honest train/validation pairs without consuming stage1 test data/survivor sidecar; validate split and semantic-cluster disjointness. Native corrupt donor is designation/item swap, not inherently honest. Existing keep-gate sparsity loss cannot simply be reused for sparse deletions (sign/quantity differs). Audit is preparatory; no training started.

Baseline mgnp completed: 8failed/1514passed/19skipped in654.94s; known worktree MASK-path +7 historical fixture names including length-matching. Base baseline7failed/1343passed/77skipped differs only length-matching pass and environment skip counts. Logs retain exact failure names; don't treat them as new feature regressions. Task1 real cached-tokenizer preflight reports64clusters,0structural exclusions,1088scores,320target+84donor=404generations at96tokens (38784max new tokens), first16cluster slice2/stratum. Verification/review pending; no GPU reservations.

Task1 independent Sol review completed: one Important validator gap, no Critical. Frozen metadata allowed rehashed contradictory complement/heads/leaf/seed/mapping declarations. Fix round1 sent to original manifest_impl; requirement exact fixed-contract validation and after-rehash rejection tests, focused both environments. Review report reports/03-manifest-review.md; no GPU spend. Runner Task2 awaits scoped review of fix.

Ruling (Astra confirmed): self-H donor on H recipient is identity, making apparent benign retention vacuous. Change existing D−F/random comparator donor conditions to shared derangedH; use same nonself policy for small reordered/alternative comparisons; keep paired core conditions only routing/sanity. No target-row count expansion. Stage2 preservation must use nonself donor intervention consistent with target suppression; never optimize identity H retention. If wrong, the comparison is donor-policy-specific and must be revised, not called generic deletion. Task1 worker requested bounded amendment/tests/preflight; review both metadata and design changes together before runner.

Task1 complete: commit a842b7a, scoped re-review clean. git diff --check clean. Live branch selective-deception. Task2 claimed; use final appended API/science descriptions. No GPU spend.

Task2 runner_impl active from a842b7a. Approved optional small metrics.py per-example probability/logit extension to avoid duplicating evaluator or extra forwards. Exact added fields in Task2 brief. No GPU reservations.

Lead compaction tracking started at user request: 1 confirmed compaction. Durable authoritative count in compaction-ledger.json; increment on each subsequent lead compaction and report at session end.

Task2 review started in parallel with final worker CPU checks: fresh Astra runner_review, final verdict awaits stable worker handoff. Fresh Sol pilot_data_feasibility audits train/val semantic disjointness and aligned nonself donors using CPU/tokenizer only; no training implementation or inference. Current squeue empty and budget untouched. Donor generation annotation added to frozen rubric before GPU outputs; separate from recipient denominator.

Pilot structural feasibility preliminary: exact Stage1 semantic precedence leaves122 unique train/126 validation clusters (127/133 records before representative dedup), candidate union103heads. Actual clean D/instructed-H/H-clean donor endpoints have zero cross-split/test overlap. Train lacks inversion/item1/lab; inversion/item2/lab has1. No silent rebalance; category reporting required. Native corrupt-stream overlaps are outside proposed pilot endpoint scope; details forthcoming reports/07-pilot-data-feasibility.md.

Task2 frozen; independent Astra spec/quality/whole-branch interfaces PASS with no Critical/Important finding. Focused77pass bothenvs, fullsuite running base exec4955/mgnp26172, logs final-{base,mgnp}.log. Root gitstatus exec22671 is slow on Lustre; scoped diffcheck exec92701 and metricsdiff39929 bounded60s. No GPU reservation. Full1848outputrecords=1444scorepasses+404completions; smoke116records=64scores+52completions,4992max newtokens.

Final full suites complete: base7failed/1420passed/77skipped in164.89s; mgnp8failed/1591passed/19skipped in594.39s. Exact failure-name sets equal baselines; zero new failures. Scoped diffcheck clean, only approved metrics.py tracked change plus4owned new files. Explicit-file stage succeeded; commit in progress exec29661. Production manifest must be prepared with mgnp AFTER commit. Next reserve0.25h H200-interactive smoke after prepare/dry-run and scheduler test-only; same hardware type required for full resume.

Smoke22994018 still pending Resources; root widened its partition list in place to H200-interactive,A100x4-interactive after A100 test-only accepted. Same job/reservation0.25h, no extra job. Evaluation uses single shared8B model and rowwise inference; A100 training-OOM prohibition does not apply to this bounded eval. Record actualGPUtype and keep it fixed for full resume.

Startup diagnosis CPU: current standalone source exits1/no marker/no stderr; existing guarded source&&conda pattern and guarded source&&conda||exit both exit0 and identify mgnpPython. Scoped workerfix to wrapper+regression only; nofullsuite repeat needed aftershellonlychange. New commit/freshmanifest required before retry because source identity frozen. Original0.25h reservation remainscharged. No GPU/model outcomes produced.

## Recovery checkpoint: numerical path probe
Lead compaction confirmed count2. Smoke22994204 completed274sec on A10040 gpua025; all116 records present. Two score identities miss0.02 threshold; all4 generation identities exact. Astra report10 confirms single/dual SDPA dispatch mismatch;24-forward A100 probe planned before any source correction/full run. Reserved total0.50/20GPUh. Pilot worktree creation completed; verify before workers use.

Pilot isolation ready: selective-mask-pilot branch/worktree verified clean at ef8cc2a. Ticket03 reviewed and released to fresh Sol worker for CPU-only primitives; ticket04 remains held. Analysis-table utility under synthetic-only implementation; primary free_response endpoint, fixed pairedcluster bootstrap10,000/seed0, all denominators retained. Standalone24forward numerical probe in preparation; no new GPU reservation/submission yet.

Numerical24forward probe reviewedPASS byroot/Astra, actualwrapperdryrun andbothenv7tests passed. Job22994714 submitted A100x8interactive15min1GPU; reservedtotal0.75/20GPUh. X4interactive occupiedby unrelateduserjob, no interference. Probe output .scratch/selective-deception/probes/score-paths-001; immutableStage1sourceef8cc2a. Probe uses exact0/-infmask and recordsfullvectors; reviewS/C logit reproduction, nottinyCPU/GPUsoftmax differences.

Probe22994714 completed77sec onA100gpuc02,24forwards. All4 prompts B=C=E andB/Crepeats bitwisefullvocab; B/Emaskmetadataequal; savedS/Clabel logits reproducedexact. S/Bmaxabs0.140625,0.25,0.25,0.12890625. Firstpredeclaredreport10branch supports runner-only samepathbaselinecorrection. Root released minimalfix to runner_impl; no tolerance changes. Newsourcecommit/manifest/outputrequired; preserve r1/probeartifacts. Reserved0.75, actualGPUelapsed355sec totalinclfailed4sec.

Correctedsourcefaa4109b253579a363a6ddf366ec3f6b899219b2 rootreview/commit complete. Actualwrapperprepare/dryrun passed, correctedmanifest7c0918edd8cfd877729d00ece65fb1c70ec9be64207c0e68930625a20e4157ce atStage1outputs/selective-sdr-stage1-r2; allmanifest contentexceptprovenance/hash exactequalr1 (report17-successor-lineage.json). Correctedsmoke22994903 submitted15minA100x8interactive,116records4992maxnewtokens. Reservedtotal1.00/20GPUh. Do not mutateStage1sourcewhilejoborresumedfullactive.

FullStage1job22994983 submitted60minA100x8interactive, exactr2store resumes116toward1848 outputs; maxfull38784newtokens; reservedtotal2.0/20GPUh. Correctedsmoke245sec8/8identitiesPASS,6caphits0empty, nonselfcore changed8score/7generation comparisons.
Pilot03 independentlyPASSreport19, committed76baea9 andscoringfixcherrypicked10b6c2a. PilotHEAD10b6c2a; CPU-only04runner releasedfreshSolpilot_runner, sourceownershipticket04, productionheld. Report18prefitgate rulesrootaccepted beforeoutcomes; copied03evidenceinto reports/13-artifacts.

Analysispreparationcompleteandrootreviewed: report22scoretables(stdlib,7synthetictestsbothenvs); report23independentreviewpackettool(7bothenvs) extendedbeforeannotations toforceexact-public-inputcategorydisputes(report26), inaddition48balanced+allambiguous/uncertain. No actualsemanticlabels yet. Report25Astra accepted identicaljointpairgeometry andlabel-only0.02+argmax/finitecalibrationgate; fullvocab/KLfloordiagnosticsseparate. pilot_runner implementing~770lines withsharedreferencecache tokeep<=16donorreferencesacrossfourfinalists. FullStage1stillrunning; lastcheck15:28elapsed994/1848 including274/320targetgenerations.


Stage1 full22994983 COMPLETED1161sec,1848/1848 records,160/160identitychecks pass,10cap hits/0empty. Reserved2.0/20GPUh, actual0.48917GPUh inclfailed/retries/probe. Prepared404anonymous records atpackets-stage1-r2 withreviewedutility. FreshSol first-pass chunks00/01active; pilot04CPUworker finalizing, realfitheld. Leadcompaction count3 recorded. Root caught checkpoint substring matching gate_proj baseweights; scopedworkerfix+regression beforefreeze.

All404first-pass labels frozen annotations/first-freeze.json. Reviewed sampler selected52independent-review rows (48fixedsample+4forced,0exact-public-inputdisputes); freshSolreviewactive. Pilot04sourcefrozen,130focusedpassbothenvs, independentSolreport28reviewactive. Rootgate_projcheckpointbug fixed; workerflaggedmissingroot evaluator sourcehash forreview. NoadditionalGPUreservations.

Final404annotations frozen before unblinding.52/52independentreviewcategoryagreement;4uncertainAstraadjudicated,2categorychanges,noneunresolved. Reports29audit/30generation/31scores complete. Primaryfree_response intactD2/16deceptive,H1/16truthful (14/15refusals); coreD1/H1,randomD1/H1,DminusFD0/H0. This is a control/headroomproblem, not evidence of selectivegeneration suppression. Original64labelreadout: Dintact64/core24/DminusF33/random43; Htruthintact49/core43/DminusF41/random44. AlternativeintactD7/16,H2/16. Plannedpilotvalidationheadroom notmeasured; do not say itsgateactuallyfailed. Root holdingproductionpending freshAstrareport32scientificdecision. Pilotreview28requestschangesonlymissing loader sourcehash; scopedfixreleasedworker.

Protocolv2 accepted/frozen beforeoutputs: sameunrunvalidation16 original+oneexactgroundingrepair,D/H64intactgens,6144token cap,<=0.5GPUh,noadaptivevariants; stopifneitherwrapperhas8Ddeceptive+8Htruthful. Script213linesCPUimplemented/frozen b385cfef,9tests bothenvs, independentlyreviewedPASSreport35. Rootprepare+actualwrapperdryrunexactequal; manifestfd0f30dc4bac32c75b04381366fe44ebd58dd9df7a28f979e7fc088eff3775b5,sourcefilesd70c01e1... atwrapper-v2/manifest.json; scheduler test-only acceptedA100x8interactivegpuc02. Noreservation/submissionyet. Pilot04finalbasefullsuite7knownfailed/1474passed/77skipped exactfailure-setbaseline; mgnpfullsuiteongoing session76030 (~73%), log33-pilot-integrated-mgnp.log. Explicit4pilotfilesstaged; cached-diffchecksession61900. Aftermgnpverify, committhenreserve0.5andlaunchv2. V2all64doubleblindedannotationpolicy frozenprotocol-v2-annotation-policy.json.

Pilot04 committed08c032f49b2cd83848105d0681c9636bb66174ff after fullsuite base7known/1474pass/77skip,mgnp8known/1645pass/19skip (report33exactnames0new). Wrapperv2job22995722submittedA100x8interactive1GPU30min,64intactcompletions6144max tokens,nodonor/scores/optimizer; sourceallfrozenincludingpilotWT+standalonescript+wrapper. Reservedtotal2.5/20GPUh. Check sacct beforeanyretry; noautomaticretryauthorized.

Wrapperv2job22995722 COMPLETED217sec,64/64,0empty/0cap. Ledgerreserved2.5actual0.54944GPUh. Immutable64packets prepared wrapper-v2/packets viareviewedstdlibutility (6synthetic testsbothenvs, report36). FreshSolwrapper_labels_a/b independentlyannotateall64, no currentoutcomes unblinded. V2standalonesource/protocols archived wrapper-v2/frozen-source; runtimecommitted08c032f. NextfreezeA/B, blindAstraadjudicateuncertain/disagreements, freezefinal64, summarizewrapperfeasibility gate.

## Completed v2 feasibility and scope decision checkpoint
Both frozen wrappers FAIL joint gate: original D1/16 deceptive,H2/16 truthful; grounded D3/16,H8/16. Final64 labels frozen before unblind;63/64 independent agreement,2 uncertain/disputed Astra adjudications,0 unresolved. All64 EOS,0empty/0cap. Report37 route STOP: no optimizer, further synthetic prompt search or threshold relaxation. Root verified final analysis source SHA008662719c537baf8c75b950078a6c4b79f6478f5dcf8652823b2f40613dc92c matches frozen archive and quality fields join by anonymous ID. Report38 Astra recommends naturalistic matched-H scope versus narrower original-stem routing; report39 read-only local artifact audit in progress. No GPU jobs active at checkpoint; reserved2.5/20,actual1978seconds,paidAPI0. Lead compactions4 confirmed. Pilot04 committed08c032f and all CPU verification complete.

Next bounded diagnostic accepted within existing research authorization after Astra clarified report38 is scope advice, not a permission hold. Genuine native LiarsBench instructed-lying twins exist (report39 rootaudit; Solworker capacityfailedtwice). Root implemented standalone transfer-v1 native16pairs/32outputs cap256; model same8B, no masks/donors/training/API,<=0.5GPUh. Data structural selectionbeforeoutputs,8truth0/8truth1, truth/form confounded deliberately disclosed; development only, no fittingthese16. Frozenprotocol1ef6210e69b39152d61c6e90e4439f3c329a545c65be5407a179d5afd581eeab, pairs2102f024f83e0f6e9f09f8ba0ad67a4437842482e17b84ed287bb2114d53b0c7; rubricdf5323435cb933bd87cda8642053588fe750422d822add3d1955706ae6bf837c. Sixfocusedtestspassbothenvs; Astrareview41active; actualCPUprepare/dryruninprogress. No GPU reservation yet. Newtaskjointfloor8paired Htruth AND Dfalse, all16retained. Strategicdeceptionpaperclaimnot silentlyreplaced.

Transfer22996012 submitted afterAstra41PASS/rootCPUprepare+wrapperdryrunexact. Reserved3.0/20h. Manifest5d5381db...,source8b76df64...,sourcedfc4ca4 frozen. All32 mustfinishbeforeblindedannotation; noautomaticretry.

Transfer22996012 COMPLETED144sec gpuc02 exit0. All32EOS/0empty/0cap; immutablepacket receipt3b2722f82f7e541cf375f8b4196c6badd8af08a13c69a51abc79a9c96d410d10, public hasstatement/truth/userquestion only (systemD/Hhidden). FreshSoltransfer_labels_a/b dispatched; no outcomes unblinded. Reserved3.0actual2122seconds (~35m22s),paidAPI0.

Transfer doubleannotation complete32/32categoryagreement;2uncertain cases freshblindAstraadjudication active. First labels frozen annotations/first-freeze.json before privatejoin. Solcapacity recovered forboth annotationpasses (B retriedonce); no modeloutputregeneration.

Transfer final32labels frozen before privatejoin;32/32independentagreement,2Astraadjudicated,no categorychanges,2remainuncertain. Report42 PASS14/16paired: D14false1truth1ambiguous,H15truth1ambiguous; false-city-in6/8,true-name8/8. Developmentonly,no fit16; same strategicmainclaim retained. Astrareport43 requested minimalfixedmask+utility/donor decision withinoriginalauthorization. AllGPUsdone; reserved3.0actual2122seconds,paidAPI0.

Root acceptedAstra43:fixedzero core43 vs layer-matchedrandom43 vsintact onall16D/H,96outputs<=24576tokens,<=1reservedGPUh, nofit. Protocolfixed-zero-v1/protocol.json38d89600... frozen; separateannotationrubric frozenbeforeoutputs. Rootaudit44explicitZeroHook requirement; nativehelper sr.generate_row hasnohookargument andcliinert, so newthinadaptermustpasshookdirect. Randomoverlap4heads,identicallayercounts. CPUworkertransfer_feasibility_impl retryactive aftercapacityerror; ownsnewfixed_zero_transfer.py/tests/report45only, oldsourcesimmutable. Rootwrappercreated1h. Noreservation/job yet; totalreserved3.0actual2122seconds,compactions4.

Fixedzero22996190 SUBMITTED1h1A100x8interactive; reservedtotal4.0/20h. Canonicalmanifestb5a45df1200387dc3f9abb13d53251000b4f58b4b94a4ba3168204565659ba7d; sourcefilesdb58b4f8f3f6ad048edebece685b2733dbf8ff57616a3e4dbdc8d8d254a4890e;script9a6dcd8...,wrapperaaac58ac...,protocol38d89600...,rubricc977759f.... Bothenv5focusedtestsPASS andreview46closed noCritical/Important; actualrootprepare+wrapperdryrunexact. Sourcearchivesfixed-zero-v1/frozen-source. DoNOTmutatepriortransferhelperorWT ornewscript/wrapperwhileactive.32intactidentitybarrierfirst then64KO;96requiredforfinalpacketprepare. Noautomaticretry. Prioractual2122GPU-seconds; currentjobunreconciled. Rootanalysisprepare_fixed_zero_packets.py readyforcomplete96only; later2freshSolworkers novel64 each andblindAstraadjudication, reuse32intactlabelsafteridentity. Nextcheckactualsacct/outputcount,notrelaunch.

Fixedzero22996190 COMPLETED312sec gpuc04,96/96,32exactintactbaseline,0empty/0cap. Packetreceipt7ebb13eed999a9279bb153887f61b0f3503b54c6637ca694b50e9e401486c5fc; public96,novel64,reusedbaseline32. FreshSolzero_labels_a/b labeling64each. Rootanalysishelpers47reviewPASS after15H/14Dguard and whitelistfieldshadowfix;7tests bothenvs, sourcearchivefixed-zero-v1/frozen-analysis. Prior9finalannotationfilesaudited0metadataoverridefields, no priorresultsaffected. Rootfinaljoin summarize_fixed_zero.py exact32baseline reuse+hashchain beforeprivatemap. AllGPUjobsterminal;totalreserved4.0actual2434seconds (~40m34s),paidAPI0. Beforeunblind needboth64labelsfrozen, uncertain/disputes/exactpublicduplicateconsistency check, freshAstraadjudicate, freezefinal96 incl32unchangedreuse. No moreGPUjobs launched.


2026-10-25T23:01:28.324055+00:00: COMPLETE frozen-mask eval5 acquisition/audits under disclosed amendments. All10/371recipients/1855responses/310batches,194issues[],187scientificreview final. Last23203410completed576sec.37.1/40GPUhreserved/44379actualsec;1113APIattempts,$4.1784295known+$.66unknownreserve. Sharedv5_transfer.md and root-completion-001.json final. No newjobs/rejudging/maskselection;rootcompactions15.


2026-10-26T16:32:56.245681+00:00: V6 COMPLETE;30singlehead/sevenrelease/controls/attention plusclean17rescue,ordinaldonorassignments,13H23→Q17H27vsQ17H26 path;203/208artifact+210sciencePASS. 3888non-smokecausalmeasurementrows(includesrecomputedanchors),720attentionrows;602GPU-seconds/55minreservations,0newAPI. Fourjobsterminal,total38.0166667/40reserved;source57c53ac. Sharedroutingmechanism, noSDRanswerflips/specificityclaim.15rootcompactions.
