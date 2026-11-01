# Sparse WikiText amendment implementation plan

> Execution: bounded workers with explicit ownership, test-first, independent review, root integration. User has already authorized execution; do not add a new approval gate.

Goal: run the user-requested three-arm necessary-mask comparison on SDR readouts, with WikiText and optional all-head candidates, regardless of benign-control outcome.
Architecture: extend the reviewed trainer in an isolated continuation worktree; preserve original failed-gate artifacts and old worktree. Pure WikiText manifest/cache/loss module feeds the existing gated model loop. Native generation is held-out evaluation, not the training objective.
Spec: amendment-2026-10-19.md and final reports/52-sparse-amended-design.md (science authoritative over audit51 where they differ).
Worktree: Deception-Circuit/.claude/worktrees/selective-wikitext, base08c032f49b2cd83848105d0681c9636bb66174ff.

## Global constraints

Root-only git/GPU submissions. No model inference outside Slurm, no notebooks, no network/API/package installs. Python3.9 and3.12 environments, frozen base weights, allMLPs/noncandidate gates hard-open. No edits to previous frozen worktrees/data/results. Original119train/119validation SDRpairs preserved, no test outcome filtering. Legacy manifests and receipts remain factual; new amendment-v2 receipt never asserts failed behavioral gates passed. Usercontrol outcome never vetoes optimizer. Technical correctness/numerics/resource bounds remain required.20reservedGPUh ceiling currently4used; max2GPUjobs. No implicit increase.

## Task A — WikiText primitives

Ownership: evaluation/selective_wikitext.py;tests/test_selective_wikitext.py. APIs exactly audit51 Workerboundarycontract. Updated data preprocessing from52 supersedes concat-all-split: one128tokenwindow pereligible article, first32train/16validation/16test articles; noheading-only/empty material; within-document windows, different-document split-local donors, root-reviewed deterministic parser and selected-crosssplit duplicate checks. Buildmanifest validates localArrowSHA and tokenizeridentity; CPU-only cache fullvocabFP32 reference logprobs on127predictivepositions with digest/immutableatomicwrites. block_loss returns differentiable KLsum/NLLsum/n_tokens. Runner owns hinges/weights/gating/forwards. Tests must demonstrate meaningful KL/NLL/gradients, offbyone rejection, nonselfdifferentdoc pairing, source/split/cache integrity and CPUdetachedrefs.

## Task B — trainer integration

Ownership: train_selective_mask.py,evaluation/selective_mask_runner.py,evaluation/selective_mask.py,scripts/selective_mask.sbatch and associated selective_mask tests only. ConsumeA API; noA-fileedits. Preserve legacy default behavior/tests where practical; new explicit amendment policy activates new schedule/objectives/candidate-space. No broadframework/refactor.

- Extend explicit CLI/manifests/config/fingerprints: collateral_arm H|W|HW, candidate_space union|all, WTmanifest/cache, policyamendment-v2, max_updates512, checkpoint_every64, effective8pairs, fixedoneWTblock/update, lr.03wd0,seed0,rho0/.01. Candidateall=1024queryoutputheads, union=frozen103; exactnoncandidate/MLPopenness. Newmanifest mustvalidatecandidatecount/hash ratherthan weakenlegacyvalidation. Includeallnewfields inresume/source/cache identity.
- Sourcefrozen originalSDR119pairs plus exactexistingnonselfHdonor. Training512completeupdates each8pairs, wrapwithoutdroppingtail throughfixedseed119order; common4096pairpresentations. TrainingWT32blocks exactly16cycles, oneblock/update forW/HW. Commongate noise realization acrossall8SDR forwards andWTforward perupdate; keepbasefrozen, restoregatecontexts, no selfsourcedmaskedWT.
- ObjectiveT + chosenC +rhoexpectedremoved. CH=(capableHfullvocabKL+allHtruthNLLnondegradation)/2; CW=(predictivetokenWTKL+blockmeanNLLnondegradation)/2; HW=(CH+CW)/2. Normalize each observationclass separately. EmptyHcapable explicitlyKL0, reportabsence, no60/119 floor veto. Wobjective mustzeroBOTHHterms. Allarms evaluatebothH andWT. Bothunitcoefficientsrawcomponents and gradientcontributions logged in smoke.
- Amendedreceipt records priorbehaviorfailures honestly, confirmsuserauthorization, andbinds newprotocol/source/data/numericalevidence. Baseline/calibrate modes separate fromtrain. No legacygeneration-headroom requirement for amendedfit. Technical same-path A/B/C calibration H andWT, finitegradients/onlygatesupdate, deterministicexportequivalence, fullsource/cachehashes still enforced. Rootaloneissuesactualvalidreceipt aftermeasurements.
- Per-blockCPUreferencecache only, stageoneblockGPU; no giantGPUcache. Preparation onlytrain/validation references; testreference creation mustnotleaktestmetrics/checkpointselection. Freeze testtokenmanifest now, defer testscore/eval untilfinalists frozen.
- Calibration/profile report walltime/model_load/cache/referenceprep,warmed8pairupdate+WT costs, validation119pairs+16WTblocks, checkpointIO, peakmemory andunion/allheadtimings. Timeenough representativeiterations; discardoptimizer-smokestates; no productionfittinghiddenincalibration. Rootprices6*512updategrid beforelaunch; eachrunonefrozenarm/rho, noarrays/retries/automaticgrid.
- Deterministicevalevery64updates; storefullD/H/Wfrontier. Armadmissibility nonzerohardmask andDsurrogatereduction; Hno netallH/capableHloss; W NLLdelta<=log1.05 andKL<=.05; HWboth. SelectgreatestDsurrogatereductionthenfewestheads thenearliestupdate thenfixedrhoorder; ownarmconstraints only. Ifnoadmissible reportbestDcheckpointasfailedfrontier, do nothidearm. Test/nativegeneration neverselectcheckpoints.
- Usefulcompactrestrictedresult criterion BEFOREoutcomes:1..16heads,>=10% lowerintactvalDsurrogate, ownarmH/Wpreservation. Anyarm qualifiesincludingWT-onlywithHloss. Ifnoneaftervalidfullruns, oneallheadexpansion ofsamegrid authorizedsubjectbudget. Global selectivebehaviorclaim stricter H/W/recoding/generation rules are evaluation/claimcriteria, notfit/armresultveto.
- Export hardbinarymask withzeroMLPremoval andexactliveforwardequivalence. Native generation andrecoding assessment usefresh structurallyfrozenclusters disjointprevious16, no training/selectiononthose16. Rootownsfinalassessmentprotocol andannotations.

## Tests and review

ForB: RED tests policyamendmentacceptsactualfailedbehaviorwithoutfalsifyinglegacy; legacygateunchanged; H/W/HWanalyticloss includingzeroH/emptycapableset; correctaccumulation/sharednoise/512schedule/WTcycles; all1024eligibilityandMLPhardopen; changedarm/WT/schedule/candidatesrejectresume; strictcache/provenance/refgradientdetachment; arm-specificselectiondoesnotvetoWforHloss; exacttinyresume/exports; dryrunneverloadsweights; actualwrapperdryrun. Runfocused bothenvs. Root integratedsuiteonceafterstablechangesvsbaselineknownfailurenames. Independentreviewbeforecommit/realmodel. Nochangedtestonlytolaundererror.

## Execution checkpoints

Ainprogress. Bdispatchafterfinal52. Rootownscontrolprotocol/adapterreview/launch andatomicresearchledgers. Actualproductionbudgetnotyetestimated: oldgenerationtimingcannotpricebackprop. Usergetsmeasuredcostbeforeover20h orlargeexpansion. No productionjob yet.
