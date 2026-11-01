# V4 completed: reviewed training, diagnostics and fresh native comparison

This fixed tranche is COMPLETE. No selective-deception GPU jobs, annotation tasks, reviews or execution approvals remain pending. Do not duplicate jobs or automatically extend/prune/reselect masks from exposed native outcomes. The earlier question about moving datasetjob23105421 was resolved by using bjhz; do not act on that stale question. Other datasetjobs were untouched.

## Outcome

Both3072-update init1/init10 all1024-head WikiText-only fits and all96checkpoints audited. Reviewed frozen23head mask:67.17% validation Dsurrogate reduction,0previous-correctHlosses,WT+2.77%PPL/KL.04134; frozen30:70.12%,Hlost3/gained3,WT+3.44%/KL.04912. No90target (max86.67% with92heads andWTfailure). Source/training/runtime remainfrozen.

Fresh32native D/H comparison after finalmaskfreeze: intactD26false/H28true. OldD69:5false,11/26clearcorrections,H16/28retained;old28:9false,8corr,H22;new23:20false,5corr,H24;new30:5false,12corr,H24. New30also has10ambiguous Danswers. No refusals/empty/malformed;old28onecap. CoherentDrefusal remainsdesired butwasnotobserved. No freshSDR/WTtestscoringthisphase. New30's lowernativeHcollateral thanD69 is sameprotocol evidence, notgeneralLM/strategicdeception specificity or broadsuperiority.

Additional7removedheads (23→30):L7H31,L8H10,L13H15,L13H23,L17H27,L19H13,L20H19. Conditionaljoint removal yields9Dfalse→true,7false→ambiguous,1true→false,2ambiguous→true; all32Hcategory/uncertaintyidentitiesmatch,though19stringsdiffer. No7-head-only/individual attribution/minimalitytest. Bothnewmaskslose4nativebaselineHtruths; zeroHlossvalidation doesnotgeneralize.

Priorold28addback/random/donor diagnostics complete114/116/134/135; oneinversedonor mapretains similaraggregate65.27→66.52%surrogate butsubstantialper-casesensitivity. No donorinvariance orformat-free claim. Newmasks mostlyoutsideoriginalD/H/Funion, butbase-rate-adjusted overlapsdo notsupportdeception specificity.

## Evidence and provenance

Study `.scratch/selective-deception/sparse-optimization-v4/`.
- `completion-receipt.json` binds completedoutputs/reviews/budget.
- `audit/summary.json`, reports129/130: completevalidation andselection.
- `comparison/selection-receipt.json` SHA3b095b5774e7521080de92a7af94243acd76e4df9725541f8ce61f55ff23f525, frozenbeforegeneration.
- `comparison/native-labels/final-freeze.json` SHAe05eb26e16c39cb64029c7c66ba5ec4eda12143bfe28b8bd4ac2ebcbcdfa1dd3, frozenBEFOREfirstprivateJSONjoin; final-labelsSHA72e12fe6c9aaecefddd891e82e9bf8d61e1e3c004917d3ea5b88426abf7c3326.
- 704freshSoljudgments,339categoryagreements,119freshblindAstraadjudications,zeroidentical-viewconflicts;352physicalviews+64exactfullgenerationcontrols. Labelsaremodel-agentjudgments, nothumangroundtruth.
- `comparison/native-analysis/native-results.json` SHA4a7f23430626379103bebfb42e02f1ecc559ca993d762c3193d6324a4ff0cd5b; derivedJSONc47b0955cfb304f940613fe16e4a698716c9da6be4a12133e63aebea887606d4. Reports141/142quantitativeandindependentscientificPASS.
- Report138/139Unicodehashrepair and140actualprovenancePASS: originalexporterASCIIhash vsconsumerUnicodehash differedon7views. Separate`native-packets-canonical` preservesallpublicbytes/IDs/text/rubric; onlyknownprivatehashslotschangedwithinversebyteproof, no privateJSONdecode beforelabel freeze. Originalartifactsretained; explicit`annotation-source-migration-bridge.json` linksactualoriginalassignments+unchangedlabels tocanonicalsidecars. Neverwaive hashes orpretendannotatorsreadnewpaths.
- Shared scientific record: `project_context/research_notes/Deception specificity and shared circuits/v3_extension.md`; figuresunderstudy/figures/. Derivedanalysis scriptpreservedinanalysis/optimization_v4_native_derived.py.

## Compute and next boundary

Native23106070 onnewbjhz normalH200 COMPLETED785GPU-sec/exit0. Cumulative actual33555GPU-sec(9h19m15s); cumulative reservations22.35/40GPUh; externalpaidAPI0. Allselectivereservations terminal; otherthreads budgetsseparate. FourverifiedGPUaccounts:beto,bimc,bgrb,bjhz,eachmatching-delta-gpuQOS. Recheckcurrentfairshare/association beforefuturelaunch. Accountchange doesnot bypassinteractiveper-user1submitted-joblimit; normalbjhzqueue resolvedplacementwithoutmovingdatasetjobs.

Rootconfirmedcompactions12. No compactiononordinaryturns; incrementonlyafteractualnewrootcompaction. Source tree selective-optimization HEAD4247c54d24f277de863abf8a7b9a462470276f45/source5f5cad941011bf73d10f83403f453d26427fdbf4b529d6ab30971c7c8c70897c remainsfrozen; mainuntouched. Defaultbwrapbroken,narrowrequire_escalatedexecworks. No pretrainedmodels onlogin/no notebookexecution.

Recommendedfuturework: prospectivefixed23/30 andconditional7-head tests on independentlyvalidatedcleanerpressure/capablebenigncontrols, coordinatedwithseparate dataset effort. Thisisnotanewlylaunchedbatch. Preservecurrentnative32asexposedassessment, neverclaimfuturetunedmaskvalidationonit. Currenttrancheiscomplete,notwaitingforautomaticrootreview.
