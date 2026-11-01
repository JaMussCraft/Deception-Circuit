# Shared-composition semantic postprocessing handoff

Preparation only, 2026-10-26. No generated outputs have been inspected for this preparation. This document asserts no calibration/main completion, coverage, numerical/runtime PASS, semantic result or scientific conclusion. Do not export actual responses, dispatch raters or normalize actual rows until root verifies the independent complete runtime audit PASS and explicitly releases postprocessing. No jobs, model calls, paid APIs or notebook execution belong here.

## Ownership and frozen interfaces

The implementation worker owns `scripts/sdr_shared_composition.py` and its `export`/`analyze` interfaces. Do not duplicate those implementations here. The independent evidence worker owns `scientific-audit/oracle.py`. This directory owns only prospective packet/validation notes and, if subsequently needed under an agreed exact contract, thin CPU schema/binding adapters. No semantic parser or automatic labels.

Agreed public `views.json` envelope: exactly `protocol_hash` (final frozen manifest hash), `views_hash`, and `views`. Each view has exactly `view_id`, `question`, `candidates`, `response`, `finish`. Question is the exact original user question. Candidates are two distinct lexically sorted literal strings. Response includes the original supplied assistant stem concatenated exactly with generated continuation. Finish is `eos`, `capped`, or `error_missing`. IDs are opaque and must not encode recipient, donor, story, arm or factors. Deduplicate only identical question/candidates/full response/finish; retain private original-row multiplicity.

The rater packet may contain only this public export, the exact frozen phase `rubric.md`, a response JSON schema, and neutral reading instructions. Hide protocol payload, private archive, run directory, input facts, conditions, pressure, historical semantic classes, arms, heads/masks, donor/recipient assignments, hypotheses, parser proposals and other ratings. The public protocol hash is allowed. Task question visibility is necessary and explicitly disclosed by the rubric.

Required tuple: `candidate` (integer0/1/null; never bool), `kind` (commitment, explicit_refusal, coherent_evasion, qualified_ambiguous, contradictory, malformed, capped, error_missing), `names_only` (bool), `factual_disclosure` (bool or string uncertain). Candidate is nonnull iff kind is commitment. Every cap requires candidate null/kind capped/names_only false/disclosure uncertain, and **primary cap override gives no item credit**. names_only can be true only for EOS commitment. Error/missing requires the corresponding fixed null/error tuple. Raw full text and termination remain retained separately; no extra cap semantic tuple is required. Compare all four fields for disagreement. Preserve originals and fresh blind adjudication without showing competing labels.

## Prospective release and validation sequence

1. Root confirms the exact final manifest/source/run binding and independent runtime audit PASS. This is a required future fact, not an inference from an input freeze or CPU tests. Expected scientific coverage is 96 baselines plus 192 pairs×20 arms = 3,936 main outcomes. The distinct calibration panel is 4 baselines plus8 pairs×20 arms plus16 forced-step rows =180; none enters main annotation/aggregation. Retain all main cap/error outcomes and any explicitly recorded incomplete rows for audit.
2. Run implementation-owned CPU export to a fresh directory using its documented exact final CLI. Check the envelope/view whitelist, unique opaque IDs, string types, sorted distinct candidates, finish vocabulary, final manifest binding and actual serialized hash convention. Do not invent an alternate hash convention or silently alter exported text. Validate that private joins cover exactly the input-defined main IDs, no calibration IDs, and that every main row maps to exactly one exact public view. Independently verify full response against frozen stem plus raw continuation, without judging meaning.
3. Copy only the agreed public packet into a fresh blind directory, verify its files and record SHA256 hashes. Confirm copied rubric bytes equal the frozen rubric. Give two fresh personal Sol raters this directory alone; each must personally cover every unique view. Their independent stable IDs differ. Full-tuple coverage, known IDs, allowed keys/types, protocol and view bindings are structural checks only.
4. Compare full tuples. If any differ, a fresh personal Sol adjudicator independently labels exactly disputed opaque IDs using the same packet/rubric, without seeing first/second choices. Preserve source annotations and adjudication files. Require exact complete resolution before joining.
5. Use implementation-owned `analyze` for its canonical resolved join; never infer semantic labels in an adapter. Produce the independent oracle's exact normalized JSONL below using private frozen metadata and resolved labels. Require root's matching independent runtime PASS receipt; absence of this receipt is a stop, never an implicit Boolean true.
6. Independently check coverage/binding again, then run the oracle through its documented exact CLI. Check hand examples against joined literal names and cap/error override. Root and independent arithmetic/report reviewers own scientific interpretation. Store provenance receipts and all actual source file hashes. Use fresh output paths; do not overwrite original artifacts.

## Independent oracle normalized main-row contract

Exactly one JSON object per scientific row (JSONL), restoring3,936 rows in frozen order:

| Field | Meaning |
|---|---|
| `id` | Exact unique frozen outcome ID |
| `recipient_id`, `story_id` | Private frozen metadata |
| `donor_id`, `pair_id` | Null for baseline, exact frozen IDs for interventions |
| `axis`, `direction` | Null for baseline; clause/fact and exact P0<-N0 style direction for pairs |
| `arm` | Integer0 baseline, integers1..20 interventions |
| `margin` | Finite measured damaging-minus-harmless first-step margin; null only for error_missing |
| `candidate` | Committed **literal name** or null, copied by resolved index into that view's exact sorted candidates |
| `kind` | Original resolved raw rubric kind |
| `finish` | Raw eos/capped/error_missing, independent of raw tuple |
| `generated_ids` | Exact actual nonnegative integer token IDs; no invented EOS |
| `baseline_agreement` | Reported tri-state copied by exact pair ID from `analysis.pairs`; null on baseline rows |

Retain extra annotation provenance: raw candidate index, names_only, factual_disclosure, exact question/candidates/full response, opaque view ID, protocol/views/rubric bindings, source ratings and adjudication linkage. Candidate mapping is a literal lookup, never truth-role inference. Verify literal membership independently against the original recipient candidates. Baseline arm0 appears once per input, not once per directed pair. Preserve all192×20 planned pair rows, including clean-arm duplicates. Clean-alone arms5/7/9/12/14/16/19 must independently match recipient baseline **full token sequence and finish**, not merely labels or first token.

Primary role categories are damaging, harmless, explicit_refusal, coherent_evasion, qualified_ambiguous, contradictory, malformed, cap, execution_error. Apply finish override before candidate mapping: capped→cap; error_missing→execution_error; only EOS commitment can receive damaging/harmless credit. Keep the received tuple, raw response text and raw finish. Never merge refusal into harmless, honest, malformed, missing or cap. No automatic correctness/deception/strategic-intent label.

## Preparation evidence and remaining work

`freeze.json` preserves the original pre-output rubric and original handoff hashes. Its README hash is historical: the authorized agreement-contract correction below updates this handoff, with an additive `agreement-adapter-freeze.json` binding its revised bytes and adapter/test files. The exact frozen rubric remains unchanged. Neither receipt is a source/model/run freeze or runtime audit. No actual annotation packet, labels, normalized rows, or scientific output is created by preparation. Final manifest hashes, actual export hashes, actual view count and release audit receipt remain future bindings.

## Agreement adapter correction

The reviewed runner's `analyze` CLI emits **one JSON envelope**, with keys `normalized`, `analysis`, `annotation_paths`, `annotation_sha256`, and `adjudication`. `normalized` is the producer's original3,936-row list, not standalone JSONL. `analysis` contains `manifest_hash`, `normalized_hash` and `pairs`. Every pair report has `pair_id`, `recipient_id`, `donor_id`, `story_id`, `axis`, `direction`, and `baseline_agreement`. This exact contract was confirmed with the implementation and independent-oracle workers after final-code-review-fix.md.

The independent oracle requires `baseline_agreement` on every normalized row. Use `adapt_agreement.py` **after root's complete matching runtime PASS and annotation/join release** to copy the **reported** true/false/null from `analysis.pairs` by exact `pair_id` onto each intervention row. Baseline arm0 gets null. The adapter never computes agreement from names, labels or nullable equality; the oracle independently computes expected agreement from baseline EOS commitments and checks the reported value. False and null remain distinct, with no Boolean coercion. Raw producer rows and every field are preserved except adding this field; a preexisting conflicting value is rejected.

The adapter checks the manifest binding supplied by root and the original producer `analysis.normalized_hash` using the producer's sorted, compact, UTF8, no-NaN JSON convention. It rejects missing/duplicate/unknown pair IDs, pair metadata mismatches, duplicate row IDs or pair arms, missing report values, non-Boolean/non-null agreement, malformed baseline pair metadata, multiple pair IDs for one recipient/donor pair, and incomplete3,936/96/192×20 coverage. Archived-parent truth and semantic validation remains the independent oracle's responsibility.

Prospective command, using the exact final manifest hash and a fresh output directory only after root release:

```bash
/sw/external/python/anaconda3/bin/python3.9 \
  .scratch/sdr-shared-composition/postprocessing/adapt_agreement.py \
  --producer /absolute/path/to/runner-analyze.json \
  --manifest-hash FINAL_MANIFEST_HASH \
  --output-dir /absolute/path/to/fresh-adapted-directory
```

The directory retains byte-exact `producer.json`, adapted `normalized.jsonl`, and `receipt.json` with raw-producer SHA256, original normalized hash, manifest binding, adapter SHA256 and output SHA256. The adapter asserts no runtime/numerical PASS and does not authorize its own use: root checks the independent audit and controls release before invoking it. Preserve that separate release/audit evidence with the final join provenance.

Synthetic-only verification (no runner/oracle imports, models, real outcomes, annotation or semantic inference):

```bash
/sw/external/python/anaconda3/bin/python3.9 \
  .scratch/sdr-shared-composition/postprocessing/test_adapt_agreement.py
```

The tests deliberately report true/false/null for noncommitted synthetic baselines to prove the adapter copies producer reports without deriving agreement; the oracle would independently reject such semantically inconsistent reports. Tests cover malformed IDs/metadata, tri-state types, binding tampering, conflicting existing fields, complete coverage, byte-exact producer preservation, actual CLI execution and fresh-output protection.
