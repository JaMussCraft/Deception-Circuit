# Final whole-feature code and scientific-execution review

2026-10-26. **REQUEST CHANGES — one P2 analysis finding.** The two initial task-review P2 findings are resolved in fix1. No further must-fix acquisition/intervention defect was found in the complete additive feature. The new finding concerns the scientific meaning of a derived descriptive field, not a change to the frozen scientific panel.

## Exact scope and evidence

Reviewed all 751 runner lines, the complete wrapper and 489 test lines, relevant unchanged hook/readout/batching/annotation/publication primitives, ratified spec and root decisions, plan, initial task review, scoped fix review, and the completed implementation report. This is a whole-feature review against base `4f0278487b0285dd27cbc34d20d88c911dc5562a`, not merely a review of the fix1 diff.

Independently verified package SHA256 `585f597e151451a0e17aedbd04decc948d66b39646495fa919b4cc91d88a3970` and all three live-source hashes against `implementation/review-whole-fix1-hashes.json`:

- Runner: `d18c0ae989e386a1c637a4d7234b4a557d5083cf09bcbc9c080785244bd027b6`.
- Wrapper: `8239a864a4725c3bd4ab15f0d38e50eed22cd9afd931ffc6b801b4d5cf527c8a`.
- Tests: `0c0da3ef07fe29e0ee35820bffea28f192261ae77a93e77eef96138b63d3126c`.

The package contains precisely three new files; no modifications to old helpers/runners/artifacts are in this reviewed package. No git commands, tests, jobs, model execution, notebooks, paid APIs or production edits were performed by this reviewer. This review owns only this document.

Read and independently hashed final `implementation-report.md` (`30e4f0052f4b7df3e9066ed5be64e97f59ee97d664f1eed69b84d58066015d2e`) and the fix1 absolute-wrapper CPU receipt (`2b33e2b1ddf137e7c201d0706279be9be5f897e6688642a295a2bb38f37d346b`). Accepted the recorded exact-source base31pass/1skip, mgnp32pass, lint and shell checks. The mgnp suite includes actual tiny Llama/NNsight natural propagation. Already passed suites were not rerun. The wrapper receipt is exit0 with3,936science rows/492batches and180calibration rows/23batches, no model load or output mutation, destination absent.

Independently compared the entire v2/v3 scientific payloads: identical, scientific hash `1a29813fea112f713b66a673619afa25687a70527d832323159c92e9c4364412`. V3 manifest `67689e8ad232734d531ef484a5ae1b288c20030a65705d5c0543595bb025df72` remains provisional/UNCOMMITTED.

## P2 — Do not classify absent emitted identities as baseline agreement

**Location:** `scripts/sdr_shared_composition.py:689–691`, specifically line690's `baseline_agreement=base['candidate']==donor['candidate']`.

The validated annotation contract assigns `candidate=None` to every noncommitment and every cap. Consequently, a recipient refusal and donor evasion yield `baseline_agreement=True`; so do two capped responses. One noncommitment paired with a committed item yields `False`, which also conflates undefined item agreement with actual disagreement between two emitted item identities. These are valid planned outcomes, not malformed inputs.

The spec calls for agreement/disagreement of actual EOS identities and for agreement-conditioned copying counts, while explicitly retaining refusal as its own behavior. The current Boolean can therefore put rows with no jointly defined emitted-item comparison into either descriptive copying stratum. The normalized rows preserve enough information to recover the correct classification, but the published pair field itself is wrong. Primary category contrasts, margin contrasts and acquisition are not affected by this finding.

**Required correction:** define item agreement only when both baselines are EOS commitments with non-null lexical candidates. Return `true` for equal candidates and `false` for distinct candidates in that eligible subset; use `null` or an explicit unavailable status otherwise. Preserve all pair rows and the existing candidate/category fields. A separate explicit comparability field is acceptable but unnecessary if the tri-state contract is documented clearly. Do not convert undefined comparisons to disagreement or filter these rows from the scientific panel.

**Focused regression requirement:** exercise the actual `analyze_panel` pair output for equal committed identities, distinct committed identities, two null identities with different noncommitment kinds, a capped baseline, and one commitment paired with one noncommitment. Assert defined agreement/disagreement only for the first two cases, undefined for the remaining cases, unchanged total pair/row coverage and unchanged primary contrast values. This can extend the existing synthetic full-panel analysis test without loading any model. No additional scientific cell or broad refactor is needed.

## Verified whole-feature behavior

- Input-only selection preserves the original96P/N prompts at both truth values,192directed pairs and exact saved common maps. Main and lexicographically selected discovery calibration inputs are disjoint. The20arms, U5/H26 disjoint source factorial, U6 and S32 definitions agree with the protocol. The outside-group geometry is also independently established in the scientific-design review.
- Natural donor heads are remapped only at common coordinates. Natural recipient and freely induced U5 receiver banks use original recipient coordinates without remapping. Source replacement affects only nominated heads; intermediate MLPs and other heads evolve freely. No old full-freeze receiver helper is called. The actual hook writes Q/K/V projection outputs before RoPE and head slices before o_proj, in layer execution order. K/Vgroup6 supplies H24–27; U5 excludes same-layer H26.
- Separate per-key masks, compact cloned banks and version/mask checks exclude generated/pad/dummy positions. Forced64 tests and the actual tiny-model capture comparison cover the key semantic distinction. Norms use FP32 existing captures, original prefix length×128 denominators and the requested last-prefix L2/RMS summaries; there is no added attention backend or tracing.
- Full-vocabulary scoring uses the actual RMSNorm weights/epsilon and unembedding in FP32. All forwards reject nonfinite/incorrect readouts. Each patched decode step has a same-path repeat; actual first-step checksum/argmax/generated token identity is checked separately. Clean-only arms must match baseline full token sequences, EOS/cap finish and first-step record. Null effects/refusals do not stop science.
- Fix1 retains failed comparisons and earlier slots before raising, with current row/control/step and vector hashes. Current attempt state is initialized before setup. Donor and U5 capture readouts now have independent same-path readout controls, with eight actual setup calls including recipient repeat/empty/self. The cold allowance and calibration maximum account for those additional calls.
- Accepted terminals bind exact protocol, batch, run and result and are atomically published through the inherited fsync/hard-link primitive. Resume verifies terminal coverage, masks and run bindings, skips accepted arms, requires receipts for unclosed operational attempts and rejects recorded hard failures. Interrupted calibration deliberately returns to root rather than silently starting another calibration. This conservative restriction is acceptable for the bounded release.
- Next-batch admission charges cold setup separately from repeated decoder calls, uses actual allocation deadlines and preserves partial attempts. Forecasting includes measured setup and accepted-file IO costs and remains advisory after admission. The real calibration must still check the fixed10second nonforward allowance against observed packing/comparison/publication costs, as the task review already requires.
- Blinded views contain the exact question, sorted lexical candidates, complete stem-plus-response and finish. Deduplication includes the complete view. Two complete independent rater sets and third-party adjudication for full-tuple disagreement are enforced. Cap overrides and all-row primary categories remain separate from lexical identities.
- Source interaction, difference-in-differences blocking, rescues, clean-adjusted QK interaction, quartet-minus-H24 and K6-minus-K0 arithmetic are correct. Direction strata and equal24-story weighting remain explicit; shared stdlib bootstrap draws, linear percentiles and per-story signs preserve the prospective contract. The sole new defect is the agreement field identified above.

## Limits and release status

Conditional blocking/rescue identify effects of these controlled interface interventions, not natural mediation fractions or strategic intent. Grouped K/V and quartet effects cannot uniquely identify H24/H26 semantics; norm magnitudes do not identify represented information. Historical native selection, fact-flip donor/recipient aliasing and limited threat-semantic eligibility remain scientific limitations rather than implementation defects.

The CPU evidence does not establish real BF16/A100 parity, memory/runtime, complete scientific acquisition or semantic findings. After the focused correction passes scoped review, root must commit the exact reviewed files, independently rebind the unchanged scientific payload to committed source and repeat the actual wrapper CPU checks before explicit calibration release. No GPU release is granted by this document.
