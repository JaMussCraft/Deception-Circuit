# Shared-composition task review

2026-10-26. **REQUEST CHANGES — two P2 findings before inference release.** Independent Codex Sol spec and quality review of the frozen initial three-file package, against base `4f0278487b0285dd27cbc34d20d88c911dc5562a`. No models, notebooks, jobs, git operations or additional tests were run by this reviewer. No scientific redesign is requested.

Package SHA256: `8502f7520c932ef44fe05b751f8b69ff3ec1353abe8b27f0fdaf27c0c750c788`. Root's package/hash manifest and all three source-file hashes were independently verified against the reviewed bytes:

- Runner `scripts/sdr_shared_composition.py`: `e3265dc5800a1ecd7f68d97b32bbf3c183edce180c328385e757e950d3e4026f`.
- Wrapper `scripts/jobs/run_sdr_shared_composition.sh`: `8239a864a4725c3bd4ab15f0d38e50eed22cd9afd931ffc6b801b4d5cf527c8a`.
- Tests `tests/test_sdr_shared_composition.py`: `c4dd83aff5ee9a73b2503e12ca312170c253572eea4afa71602bc1afbf6122ac`.

Read the finalized `implementation-report.md`, including actual-wrapper CPU closure; its reported SHA256 is `f8425bdd18698c02e1f15f863d65da84a05b70145db22c4a9fe8f29abc44e8a7`. The immutable-input checks and detailed review checklist are in `task-review-preparation.md`.

## Findings

### P2 — Persist the failing numerical receipt and its current attempt context before stopping

Runner **lines235–241,297–305,539–556,580–582**; unchanged helper context `sdr_cue_circuits.compare_full` lines222–225.

`compare_rows` invokes the inherited `cc.compare_full`, which raises on a failed comparison before returning a receipt. Even if it returned a failed receipt, `compare_rows` would raise before its local list is extended into the decoder's durable `state['controls']`. A failure in a later physical slot also loses the successful comparisons already collected locally for the current control. The outer failure file retains the bounded raw exception and prior token/control/runtime state, but lacks the failed comparison's row/control/step and expected/observed vector hashes. Thus a numerical hard stop cannot be audited against the specified full-vocabulary evidence. A nonfinite result rejected by `forward` similarly has only the generic finite/shape error, without the active readout context.

There is an additional context hazard on a new group's setup failure: `state` is reset only at line556, after setup/control work. On any group after the first, failure at lines541–553 can publish the preceding accepted arm's rows as the current attempt's `partial` evidence. This does not incorrectly accept a failed arm, but associates failure evidence with the wrong work.

**Required repair:** in the additive runner, collect structured comparison diagnostics independently of the helper's raise-on-failure behavior, attach them to the current attempt before raising, and preserve the bounded raw error as well. Include row/physical slot, control, step, finite/bitwise/argmax/max-error fields and both vector hashes whenever the vectors exist. Give forward finite/geometry rejection actionable current-forward context. Initialize the current attempt's state before setup and retain setup diagnostics under that attempt rather than borrowing a preceding decode state. Keep the existing hard failure/nonresumable behavior and reject acceptance; no old helper changes are needed.

**Minimum nonduplicative regression evidence:** inject a late finite vocabulary mismatch after at least one emitted token, drive it through the run failure publisher, then verify the failure file contains the exact failed row/control/step, both hashes, numerical flags/error, prior partial tokens and raw error; no accepted file for that arm exists and resume rejects the hard failure. Also inject a setup failure after a preceding arm has been accepted, verifying that the new failure references the current batch and does not claim the preceding arm's rows as its partial decode. A small parametrized nonfinite case may share the first harness to check forward rejection context. No real model is required.

### P2 — Check natural donor and U5 setup readouts against their independent same-path readouts

Runner **lines249–259,541–553,555–556**.

The natural donor setup capture produces `donor_logits` at line251 and returns them at line258, but nothing consumes them. The freely evolving U5 capture's logits are discarded at line254. The setup controls compare only natural **recipient** setup logits with recipient repeat/empty/self forwards. Decoder repeats compare the readout-only path against itself. Consequently all current runtime controls can pass while the donor/source setup capture path disagrees numerically with the readout path used for the actual scientific arm. The protocol/seam requires natural donor/source setup-capture agreement in addition to recipient and per-arm repeats; this part is missing.

**Required repair:** retain and compare the natural donor setup readout with an independent donor readout using the same B8/L224 IDs, attention mask, backend and FP32 scoring. Retain the U5-induced setup readout and compare it with arm01's independent actual first score on the same mapped U5 bank. A directly equivalent same-geometry source-only readout control is acceptable if retaining the existing arm01 first score would complicate lifetime management. Compare full vectors at ≤1e−5 and exact argmax, retain structured receipts, and hard-stop on failure. Do not compare historical B8/L128 outputs or transplant receiver coordinates. Update recorded forward/setup costs and cold/warm admission allowances for any added actual calls.

**Minimum nonduplicative regression evidence:** inject readout drift specifically on the donor capture path and specifically on the U5 receiver-capture path while leaving ordinary repeat/empty/self paths consistent. Each must stop with the correctly named persisted setup/source comparison receipt, without accepted outcomes. A matching-path case must retain both controls with full-vocabulary coverage. Existing actual tiny-NNsight natural-propagation proof remains useful and need not be duplicated.

## Verified implementation behavior

- Input-only freeze matches the independent original-manifest oracle:24historical confirmation stories,96original P/N inputs,192directed pairs,3,936science rows,492B8 batches. Main/calibration IDs are disjoint; discovery calibration is the first lexical immutable story,4inputs/8pairs,20natural operators plus forced64arms10/18. Saved prompts/IDs/stems/maps and original parent hashes remain bound.
- U5 excludes L17H26; U6 is its disjoint union with H26. S32 is the frozen parent list. Group6 is correctly reported as H24–27; Q24, grouped K/V and pre-o_proj outputs use the established hook sites. All20arm definitions match the spec.
- Induced receivers are captured under U5 alone in a freely evolving model. No old full-freeze direct-edge helper is called. Recipient receiver banks are never donor-remapped; source masks use only exact common mappings. Distinct per-key masks exclude generated/pad/dummy positions; compact banks are cloned and version checked.
- Decoder uses fixed B8/L224, cap64, no cache, declared EOS union and actual FP32 norm/unembedding readout. Actual decoder step0 checksum/argmax/generated ID must match its independent first score. Clean-only arms must reproduce baseline full token sequences and finish, plus their firststep record. Source/clamp/rescue repeats are full vocabulary and finite. Norm definitions and denominators match the protocol, without attention tracing.
- Per-arm accepted files are the atomic durable terminal, so no separate progress-journal gap can cause an already valid accepted arm to be rerun. Resume audits exact batch/protocol/run/result/mask receipts and skips accepted arms even if optional timing publication was interrupted. Unclosed attempts require an interruption receipt; hard numerical/provenance failures remain nonresumable. The inherited atomic hard-link publisher fsyncs file and directory.
- Source/cache/software/protocol binding is fail-closed before execution. Wrapper fixes original path/cwd, offline mgnp and BLAS threads and binds actual Slurm start/end. The reported actual absolute-wrapper CPU dry-run returned3936rows/492batches,180calibrationrows/23batches, no model load/output mutation, with an absent destination. Read receipt `implementation/wrapper-cpu-dry-run.json`.
- Existing operation counts are coherent: three setup captures plus recipient repeat/empty/self =six setup forwards/group; at most67baseline or129patched decoder forwards/arm. Cold allowances are charged once around each arm/group, not on every generated token. Per-arm measured elapsed time includes decoder scoring/comparison/hashing; forecast separately adds setup and measured accepted publication/read-hash costs. Any fix-added forwards must update these counts.
- Analysis formulas preserve all clean-only terms, source interaction, QK interaction adjustment, rescue and group/comparator contrasts. It retains direction strata and equal story weights, fixed shared bootstrap draws/linear percentiles, caps/refusals and complete blind-view deduplication. No behavioral correctness or deception-specificity gate was added.

## Evidence and remaining runtime obligations

Accepted the worker's recorded exact-source verification: base23passed/1pinned-NNsight skip; mgnp24passed, including actual tiny Llama/NNsight natural-source propagation versus MLP freezing; ruff F and shell syntax PASS. Preparation baselines were122passed/2skipped in base and161passed in mgnp. Tests were read for meaningful coverage; already passed suites were not rerun.

Calibration `--resume` is deliberately rejected. That is a conservative operational restriction, not an implementation safety defect or reason to expand this patch: an interrupted calibration must return to root for explicit handling, preserving the original selection and attempts rather than silently starting a second calibration. Main verified resume is implemented. Root may choose a narrowly reviewed calibration-resume path later if interruption occurs.

The next-arm guard currently reserves a fixed10seconds for packing/publication beyond modeled calls; real calibration must verify that this covers observed nonforward costs and root/operator must raise it or make it measured if necessary. Its whole-panel forecast already uses measured accepted publication/read-hash times and is advisory after admission. Real BF16/A100 parity, memory/runtime, exact committed rebind, source-specific new comparison receipts, finalized calibration and all3,936science outcomes remain acquisition obligations. No GPU release is granted by this review.

Scope remains the ratified original-SDR composition study. No attention traces, L24/new heads/doses, prompt changes, behavioral success selection, paid judges, notebooks, old-source edits or resumed stopped assay are requested.
