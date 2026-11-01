# Independent review packet preparation

Implemented the standard-library CPU utility `analysis/prepare_review.py` and synthetic-only `analysis/test_prepare_review.py`. No actual outcome or annotation files were opened. No model/GPU/API/job/git/notebook operations were performed. Root must independently review this utility before real use.

API: `prepare(packet_dir, packet_receipt, label_paths, labels_sha256, output_dir) -> receipt_dict`. `packet_dir` is the original blinded package root containing `public/` and `private_mapping.jsonl`; `packet_receipt` is the trusted original `hash_manifest.json`. `label_paths` contains every **first-pass** annotation JSONL. `labels_sha256` uses the report12 version1 freeze contract:

```json
{
  "version": 1,
  "labels": {"first-chunk-00.jsonl": "SHA256_OF_EXACT_FILE_BYTES"},
  "packet_receipt_sha256": "SHA256_OF_TRUSTED_ORIGINAL_hash_manifest.json_BYTES"
}
```

Root must save that receipt before any private mapping access. Hashes establish byte consistency; they cannot establish chronology, independent custody, or reviewer independence. Preserve all original first-pass labels. This utility neither changes labels nor adjudicates them.

Root-only command, after independent source review and first-pass hash freeze:

```bash
/sw/external/python/anaconda3/bin/python3.9 -B \
  .scratch/selective-deception/analysis/prepare_review.py \
  --packet-dir /ABSOLUTE/ORIGINAL_BLIND_PACKET \
  --packet-receipt /ABSOLUTE/ORIGINAL_BLIND_PACKET/hash_manifest.json \
  --labels /ABSOLUTE/FIRST_PASS/first-chunk-00.jsonl /ABSOLUTE/FIRST_PASS/first-chunk-01.jsonl \
  --labels-sha256 /ABSOLUTE/FROZEN/first-pass-freeze.json \
  --output-dir /ABSOLUTE/NEW_REVIEW_PACKET
```

Validation reuses `summarize_labels.py`'s strict JSON/JSONL, label schema, exact-ID and private-mapping validators, plus the canonical serializer from `prepare_blind.py`. It checks first-pass byte hashes and annotation schemas, pinned packet receipt bytes, complete Stage1 receipt counts (404/320/84 with1848 full records), all seven public chunk byte hashes/sizes and expected64×6+20 lengths, exact404 unique public IDs, public schema/redaction, and exact first-pass ID coverage **before calling the private-mapping reader**. Artifact names and public directory contents must match the original seven-chunk contract. The private map then must match its pinned hash/size, exact IDs, 320/84 kind counts, unique row IDs and the complete balanced20 target cells over the same16 semantic clusters, as validated by the existing helper. No input-error path creates an output directory.

Sampling is fixed and reproducible: initialize `random.Random(0)`; iterate target `(view,policy,condition)` cells in sorted tuple order and sample two from each cell's sorted IDs, yielding40 target rows; sample eight from sorted donor-reference IDs using the same RNG; union every first-pass row with category `ambiguous`, boolean `uncertain=true`, **or membership in a disputed exact-input duplicate group**; deduplicate. Finally sort the union and shuffle using the same RNG before chunking. First-pass file/shard order does not affect the sample. The48 baseline rows remain included, with an additional0–356 forced rows. Baseline overlap with forced rows is counted explicitly. The resulting sample oversamples ambiguity/disputes and is not an unbiased population agreement estimate.

Before any annotations, the rubric's existing "all disputed rows" instruction is operationalized as follows: canonically group the public `(prompt, ground_truth, output)` triple; ignore anonymous ID and generic quality metadata. If a group contains more than one distinct first-pass primary category, force **every** ID in that group into independent review, including consistently labeled members within the conflicting group. Exact prompt/output text is preserved; no whitespace or answer normalization is performed. A group with one distinct primary category contributes no duplicate dispute. This only selects independent review rows: categories/endpoints, first-pass labels and freeze receipts remain unchanged. The grouping consumes no random draws, preserving the original48-row baseline and RNG sequence. Public review files retain the original record bytes and disclose no dispute reason.

New output directory mode0700 contains:

- `public/chunk-XX.jsonl`: at most64 records per chunk. Every record is copied from its original public packet as an identical byte line, retaining its anonymous ID. No first-pass label, selection reason, condition/cell, donor role, or added metadata is included. Deliver only these chunks to fresh independent reviewers.
- `private_selection.json`: root-only provenance and selection receipt, including ordered selected IDs, baseline/forced IDs and overlap/additional counts, `duplicate_dispute_ids` and `duplicate_dispute_count`, target-cell samples, donor sample, selected target/donor totals, all original label hashes, freeze/packet/map hashes, original run/manifest identities, and review-chunk SHA256/byte counts. It does not contain generated text or first-pass category/reason fields.

Every output file is exclusively created with mode0600. Existing output paths, including dangling symlinks, are refused. Input label and freeze files remain byte-identical. No semantic labeling, numerical condition scoring, adjudication, or real packet preparation was performed.

Verification commands (2026-10-18), restricted to the owned synthetic fixture file:

```bash
/sw/external/python/anaconda3/bin/python3.9 -B -m unittest discover \
  -s .scratch/selective-deception/analysis -p test_prepare_review.py -v
/u/swong2/.conda/envs/mgnp/bin/python -B -m unittest discover \
  -s .scratch/selective-deception/analysis -p test_prepare_review.py -v
```

Both pass **7 tests** (Python3.9:1.010s; Python3.12:0.806s). Fixtures validate exact2×20 target cells +8 donors, deterministic sample/shard-order invariance, original-byte record copying, public redaction, input preservation, SHA256/size receipts and file modes. Independent ambiguous-only, uncertain-only and overlapping flags produce a deduplicated50-row sample; all404 uncertain rows produce64,64,64,64,64,64,20 chunks. The duplicate-dispute regression first failed before implementation, then passed: a three-member conflicting group spanning target/donor roles and different quality metadata forces all three otherwise-certain, nonambiguous IDs, yielding51 total; consistent duplicate groups and conflicting labels attached to differing ground truths remain unforced, and the48 baseline IDs and frozen label bytes remain unchanged. Mocked private mapping reads confirm that label/receipt/public byte tampering, missing/unknown/duplicate labels, unknown public IDs, leaked public metadata, extra public files, and altered full-count receipts fail before private access. Separate counterexamples reject mapping byte tampering and invalid target cells. A real CLI invocation on synthetic data succeeds, then refuses overwrite without changing the first receipt; dangling symlinks are also refused.

SHA256 of owned source files:

```text
70f518374b8ee7ab9171e7217bc13cf960ef7ab27c315e8e364b2413f945db99  analysis/prepare_review.py
b4f45d9824f30236f32a9cf47463ebdd9528e69b1372f5faa5f98014cd3a7892  analysis/test_prepare_review.py
```

Reused helper versions inspected and tested:

```text
e00e1c6bf7c4ca5285e50cd5ed7730ae475b04682b5e224e43466e1afe2e6b75  analysis/summarize_labels.py
aee4649c33ffaaf78e6cce02df8caa391cb6ddf88d531eb645e16151a4b0d010  analysis/prepare_blind.py
```

Initial version root independent source review: PASS. Completepublic+firstlabelhash/schema validation precedes mappingaccess; mapping enforces20balancedtargetcells; seed0twoeach+eightdonors gives48distinctbaseline rows, unionambiguous/uncertain deduplicated; publicbytescopiedunchanged withno labels/selectionreason exposed. The preregistered duplicate-dispute extension above now awaits root's independent review before use.

Root re-review of duplicate-dispute extensionPASS: groupsexactcanonical(prompt,ground_truth,output), flagsallmembersifprimarycategoriesdiffer, ignoresquality/IDs, noextraRNGdraws, unmodified48baseline, receiptseparatesduplicate IDs. Synthetic7tests bothenvs; sourcehash70f518374b8ee7ab9171e7217bc13cf960ef7ab27c315e8e364b2413f945db99 acceptedbeforeactualannotations.
