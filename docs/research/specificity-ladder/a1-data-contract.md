# Scored user-control dataset contract

This contract joins A1 assembly to A2 matched materialization. A raw derivation is not scored data. It supplements plan-a1 Task 3 and plan-a2 Task 1 before either produces a training-ready matched cohort.

## Dataset configurations

Each assembled inversion and neutral dataset keeps normal task, model, condition and margin metadata. Inversion condition is `user_inversion` with margin threshold exactly 0.7 or 0.5; neutral condition is `user_neutral` with its diagnostic honest threshold 0.3. Both record `baseline_kind=matched_frame_neutral_request` and the same `scoring_provenance` object with `path: scoring_provenance.json` and `sha256`, the digest of that file's bytes. Paths must resolve inside their dataset root.

Model identities must agree across D, H, I and user-neutral configurations. The new producer records the actual tokenizer identity, revision, scoring code commit, precision and model revision before scoring; missing provenance cannot be replaced by a readiness flag.

## Scoring receipt

`scoring_provenance.json` has these required fields:

- `schema_version`: 1.
- `kind`: `user_inversion_scored`.
- `source_commit`: full 40-hex scoring code commit.
- `model`: the same canonical model identifier as the dataset configurations.
- `model_revision`: the recorded model revision or local snapshot digest.
- `tokenizer`: the actual tokenizer `name_or_path` string (fall back to its class name only for injected test tokenizers).
- `tokenizer_revision`: the recorded tokenizer revision or local snapshot digest.
- `request_pool_hash`: canonical JSON SHA-256 of the frozen request-pool content.
- `scorer`: `dataset.deception_common.score_prompts`.
- `dtype`: recorded execution dtype.
- `score_files`: mapping train/validation/test to an object with dataset-relative `path` and byte `sha256`.

Copy this receipt and its referenced score files into each arm's dataset root so datasets are self-contained. Both arms must have identical receipt content and score-file hashes. Never synthesize a receipt for unscored rows. It may cover all scored source rows, including rejected rows; every retained row must have exactly one matching score record. The scoring CLI's complete run manifest remains separate and is linked in assembly provenance.

## Score records and verification

Each score JSONL record has `instance_id`, plus `inversion` and `baseline`, each with `clean` and `corrupt` native score dictionaries. Every score includes `choice`, `margin`, `argmax_id`, `argmax`, native logits, `expected_honest`, `expected_opposite`, and `prompt_hash`. Here choice `b` is the opposite full-vocabulary argmax; margin is honest minus opposite. `prompt_hash` uses the constructor's canonical JSON hash of the exact prompt string, not an unspecified byte convention.

Before setting a matched dataset ready for training, the materializer checks:

1. Receipt byte digest, required fields, model/tokenizer agreement, source-commit format and all score-file byte digests. Reject a missing or escaped file path.
2. No duplicate score ids in a split, no score id crossing splits, and exactly one record for each retained source id. Extra scored-but-rejected ids are permitted.
3. Both arm/stream prompt hashes match the corresponding assembled row prompts. Canonical words match D's honest/opposite orientation and reverse in the designation-swapped stream. All required numeric score values are finite.
4. Inversion choice is `b` and opposite-minus-honest margin is at least the declared 0.7 or 0.5 threshold in both streams. Baseline competence is diagnostic and does not change membership.
5. Each new row's `source_row_hashes` for D and H matches the actual original joined row under the constructor's canonical JSON hashing. This prevents an unrelated raw derivation from borrowing source ids.

No check can establish that a malicious author really ran inference, but these checks ensure that ordinary raw derivations, stale caches, wrong-model records and mismatched prompts cannot silently qualify as measured controls. The scorer and assembler must write evidence from actual execution, not merely satisfy a schema.
