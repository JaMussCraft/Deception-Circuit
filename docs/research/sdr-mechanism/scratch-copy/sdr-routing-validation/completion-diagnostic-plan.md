# Completion Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. One additive code/run/annotation task, separate from stopped validationTask2; user already authorized continued research and extraGPU.

**Goal:** Measure whether existing first-token non-item failures resolve to correct named items during unchanged forced-prefix completions.

**Architecture:** New standalone runner verifies immutable parent baselines, replays everyfirststep through identical uncached scoring, then produces a single bounded greedy trajectory per frozenprompt. Blinded identity/format annotation precedes joining truth; all outcomes retained. Existing hook/readout primitives reused without editing oldmodules.

**Tech Stack:** Local A100/Llama3.1-8B BF16, NNsight/PyTorch uncachedhooks, tokenizer, pytest, Slurm, JSON/JSONL; internal agents for blinded labels, no external paidAPIs.

**Spec:** `/projects/beto/swong2/Alignment/.scratch/sdr-routing-validation/completion-diagnostic-spec.md`.

## Global Constraints

- All1280parentprompts unchanged, exactlyone greedytrajectory each,32newtokens maximum includingfirststep; physical8×192 A100, original batchorder/ownmasks/readouts, no cache/HFgenerate/truncation.
- All1280firststep fullvocab checksums must match originalbaseline before scientificcontinuations; mismatchendsrun.
- OriginalvalidationgateFAILimmutable; Task2notimplemented/notrun, no rescue/path/patchgeneration/pressuresearch.
- Atmost3600additionalA100reservedsec initial; prior3600/prospective7200 onlyuponoperatorreceipt; no refunds/automaticretry,zeroAPIs/notebooks; leadcompactions1.
- Oldsource/artifacts unchanged; rootgit/operatorbudget; independent review and wrapperCPUdryrun before release.

## Review Focus

- Prefix lengths/readouts differ and EOSrows end independently: firststep exact replay, append/mask/dummy invariants and32token bounds tested.
- A different generation scoringpath can silently change BF16 argmax: only same uncachedhooks/fp32READOUT, fullvocabchecksum allrows.
- Early item mention may be negated/later contradicted or capped: no semantic stopping, conservative parsing/manualblinds, unresolvedcap retained.
- Blinded labels must not contain truth/stakes/oldoutcomes: opaque shuffled IDs and separate identity→truth join, independent labels.
- Runtime and annotation missingness cannot shrink denominator: exhaustive1280records with stopped/error/cap states and unresolveddisagreements.

### Task 1: Separate completion runner, blinded annotation and report

**Files:** Create `scripts/sdr_completion_diagnostic.py`, `tests/test_sdr_completion_diagnostic.py`, `scripts/sdr_completion_diagnostic.sbatch`. Output labeling/rubric manifests only in separate diagnostic namespace; no existingcode edits.

**Interfaces:**
- `build_completion_manifest(parent_dir: Path, tokenizer, *, seed: int = 20261021) -> dict`: verify parent1280IDs/inputvectors/mask/order/model/tokenizer/sources, sourceprefix<=115,32cap<192; freeze output plan/calibrationfirst8batches, labels/rubric doubleSol ALLunique exact(response,unorderedoptions,cap/finish) views with1280rowjoin, hashes/code/device/budget/forwardceilings.
- `replay_first_steps(model, manifest: dict) -> list[dict]`: uncached physical8×192 originalbatches reconstructed via first8groupIDs sort, verified againstbaseline.jsonl order, initialcaptureall_component_keys+READOUT, unchangedscore_capture→fp32logits; compareoriginalchecksum everyrow, savefullreceipts+cachedfirsttoken. Any mismatchthrowsstopreceipt beforecontinuing.
- `greedy_complete_batch(model, variants: list[dict], first_steps: list[dict], *, max_new_tokens: int = 32) -> list[dict]`: subsequentREADOUTonly uncachedhookpath+capture_logits appendownpositions, activeEOSmask usingconfig+generation_config union[128001,128008,128009], one trajectory, finalstem+continuation/tokens/stopreason. Cachedfirsttoken counts step1. Keep EOSterminatedrows/dummies physicallystable,scoreonlyactive logicalrows.
- `propose_literal_identity(text: str, candidates: tuple[str,str], stop_reason: str) -> dict`: conservative lexical singleton only, otherwiseflagmanual; cap/errorsunresolved, wordboundaries/negation/contradictions/quotesrubric.
- `blind_label_rows(generations: list[dict], manifest: dict) -> list[dict]`: shuffledopaqueIDs/fullassistanttext/ unorderedcandidates only; no factors/truth/baselineoutcome/hypotheses. `join_labels(label_a, label_b, adjudication, private_join) -> list[dict]`: identity and responsekind/format separated; unresolveddisagreementambiguous, then jointruth.
- `summarize_completions(rows: list[dict], parent_baselines: list[dict]) -> dict`: all1280denominator, subgroupoldnonitemdescriptive, exhaustivefactor/nativefresh/split breakdowns, EOS/cap/error/unresolved/format; no gatechange/pathstat claims.

- [ ] Write failing tests `test_all1280_parent_ids_and_prompt_bytes_unchanged`; `test_firststep_checksum_allrows_before_continuations`; `test_mismatch_stops_without_scoring_rescue`; `test_own_readout_append_EOS_dummy_mask_8x192`; `test_cap32_includes_cached_firsttoken_and_preserves_allrows`; `test_prefix115_no_truncation`; `test_EOS_union_includes_all_three_endings`; `test_original_baseline_batchorder_reconstructed`; `test_calibration_rows_excluded_main_and_rubric_frozen`. Tiny-model physical8×192 tests compare manual uncached fullprefix replay, verify greedyargmax fp32 and no alternativegenerate/cache invocation. Set only runtime hooks._hf(model).config.use_cache=False and assert originalfullchecksumstillmatches; oldconfigfilesunchanged.
- [ ] Write parsing/blinding tests `test_singleton_wordboundary_not_substring`; `test_negation_multiple_contradiction_refusal_require_rubric`; `test_capped_apparent_answer_unresolved`; `test_quotes_prefix_format_separate_from_correctness`; `test_blind_inputs_hide_factors_truth_oldargmax`; `test_labels_join_truth_only_after_independent_annotations`; `test_disagreement_missing_label_retains_denominator`; `test_unique_view_dedup_restores_all1280_weights`; `test_parent_numeric_pass_capability_fail_is_valid_diagnostic_entry`.
- [ ] Confirm failures then implementminimalrunner/wrapper. Reuse old digest/atomic/scoring conventions and lowlevelhooks, not old128batchadapters or generationframework. Separate<=600sec calibrationfirst8originalbatches is EXCLUDEDmaininferentialaggregation/labelselection; fresh<=3000sec full1280main onlyifmeasuredforecast+bufferfits. Freeze rubric beforecalibration, no tuning; forecast<=5120generationforwards/40960tokens pluscountedcontrols/overhead, no assumption old191secprovesfit. Internalallocationdeadline/TERM/checkpoints,actualA100assertion,parentartifactimmutability,newoutputonly; noautoresubmit.
- [ ] Run dedicated tests in base+mgnp,actualwrapperCPUdryrun,inference-freeparentpayloadhash/rubricaudit. Independentcode/scientificreview; rootexplicitfilecommit,operatorreserves<=600A100sec calibration, then<=3000main onlyafterreceipt/forecast/release, totalinitial<=3600. Firststepall1280checksumsPASS and measuredforecast required before fullgeneration; record allfailures/caps/interruption rather than rerunningselectedrows.
- [ ] Freeze blinded materials then post-maintwoindependentinternalSolannotationsALLunique exact(response,unorderedoptions,cap/finish) views includingparserclearcaseaudit; restore1280rowweights throughfrozendedupjoin, unavailablelabelsunresolved; annotators unawareotherlabels/factors/truth. Thirdblindpassonlydisagreements,irreducibleremainambiguous. NoexternalpaidAPI. Save independentlabelprovenance and capacitymissingness; no correctnessbyregex alone.
- [ ] Audit1280planned/attempted/terminated/capped/error and exactmax32/baselinechecksums, operatorreserved/actualcost; reportprefixformatvsjoinedsemanticresults with allrowdenominator and originalgatefailed. Independentfinalreportreview; retainoldTask2stopped/evidenceimmutable/noadditionaljobsunlessseparatelyauthorized.

Self-review: onecohesivecode/run/annotationunit; allreviewfocusitemsnamedtests, no new causalestimand/gaterescue, allparentdataimmutable and no model-outcome selection. Routineimplementation delegated underexistingauthorization, no reneweduserapproval.


## Superseding operational forecast/envelope ruling — before source amendment

Calibration job23098326 complete: all1280first-step full-vocabulary checksums PASS on exact parentA100; operatorSlurm152actualGPU-sec. Measured conservative5120-forward forecast **3207.80seconds** exceeds old3000secondmainceiling (including conservativeIO650.68seconds). Under user's existing “moreGPU as needed” authorization, root raises **MAIN ceiling3000→3600reservedA100sec**, and this separate diagnostic's initialenvelope **3600→4200reservedA100sec (=600calibration+3600main)**. Global heterogeneous internal14400second envelope stays unchanged. These values visibly supersede earlier3000main/3600diagnosticbudget paragraphs; history retained. Prospective cumulativephase7800only if operatorreservesmain; no newreservation or mainrelease asserted here, numericledgeroperator-only.

A3600secondallocation leaves ~392seconds beyond3207.8forecast before consideringactualdeadline/shutdownbounds; forecastunderestimation remains a risk and must produce explicit missing/error/unresolvedrows rather than selective retries, sampledropping, longercap or cachefallback. Worker may make only minimal operationalcap/forecast-reporting amendment; scopedreview+actualwrapperCPUdryrun+rootrelease required before main. No changed prompts,1280ID/order,32tokencap, labelrubric, EOS, hardware/scoring, calibration-text selection or scientificclaim. Calibration remains excludedmain; do not rerun/calibrationlabel or outcome-selectmain. OriginalpathwaystudyclosedgateFAIL/Task2stopped. Currentleadcompactions2.
