# Task 1 independent manifest review

Spec verdict: **changes required**, one important validation gap. Code-quality verdict: **changes required for that same issue**; otherwise the implementation is focused and suitable for this pure-data stage. No critical findings. No runner or donor-model-validity claims made.

## Important: fixed intervention semantics are not validated

`evaluation/selective_diagnostics.py:382-391` validates version, aggregate budgets and decode, but skips the fixed scientific configuration emitted at lines345-349. A manifest can advertise keeping masks instead of complementing them, non-head masks, block granularity, a different random seed, or an empty/mismatched condition-mask mapping and still pass `validate_manifest` after its public hash helper is used. This is a relational contract failure, not an expectation that hashing defeats malicious input: the validator already deliberately detects inconsistent inner metadata after a legitimate outer rehash. A runner consuming accepted configuration can execute the wrong intervention, while a runner using hardcoded semantics can leave its frozen metadata describing the wrong experiment.

Focused CPU reproduction using the supplied literal fixture: build the valid four-cluster fixture; separately set config `all_interventions='keep'`, `masks_heads_only=False`, `mask_granularity='block'`, `random_mask_seed=17`, or `condition_masks={}`; recompute `manifest_hash`; call `validate_manifest`. **All five contradictions were accepted.** No test suite or model was run for this reproduction.

Minimal fix: validate `condition_masks` against the actual CONDITIONS mask mapping, `all_interventions=='complement'`, `masks_heads_only is True`, `mask_granularity=='leaf'`, and `random_mask_seed==0`. Also enforce the other fixed scientific declarations already emitted (`generation_is_prompt_transfer_test is True`, selection-rule identity, original outcome-filtering disclosure true, new-outcome screening false, survivor-list use false); they belong to the same bounded invariant fix. Add parameterized tests that alter each declaration, recompute the hash, and demand rejection. Do not broaden this into a general schema framework.

## Reviewed behavior and limits

- Historical intro/question/stem literals are used for surgery; stored templates are not rebuilt from current SPECS. The full system fact/instruction content survives generation transformation. Refusal is explicitly permitted, the forced response instruction and assistant stem are removed, and the alternative wording requests natural language.
- D/H labels remain semantic labels on both recipient policies. The four paired donor intended-label mappings match designation inversion. Imported `instructed_counterpart` verifies clause-only token changes and exactly one clean/corrupt designated-item token difference. Actual intact donor validity remains Task2 measurement; no extra outcome filtering is introduced.
- Scenario grouping includes entity, unordered items and semantic honest-item assignment. Deterministic selection and same-length cyclic derangement retain explicit source identities. The saved preview independently has64 clusters,8 per each of8 strata, and2 per stratum in its first16; all reported generation/score caps agree with formulas in the builder.
- Eight primary conditions, the64 changed-order scores,320 recipient generation rows and separately deduplicated donor-reference accounting are present. Recipient and donor endpoints retain prompt text, token IDs, hashes, stream, source and intended answer. Shared-mask layout is unpadded/all-ones with exact equal lengths.
- Canonical serialization, source/pool hashes, transform checks, reconstructed row/reference identity, bounded generation tokens, explicit structural exclusions and no silent shrinking are implemented. Existing test evidence is34 passes in each environment as supplied; this review did not rerun it.
- No further important finding in the requested scope. Full production manifest/tokenizer validation and runner handling of actual EOS/short donors remain downstream, as agreed.

## Exact reviewed version

Read both live named files in full and compared the supplied diff tails. The supplied diff already contains the latest exact1088-score/320-recipient test; no missing final edit was observed.

- `evaluation/selective_diagnostics.py`: SHA256 `45b66996dae1c1715748d44c842a4092782ef4f1197fec39111fa78a69191ef4`.
- `tests/test_selective_diagnostics.py`: SHA256 `f9f9338b9195eeb5f66086f6ef6d6e93f1d1da6b5b3134d3511772c18ad39195`.


## Final scoped re-review: metadata correction and nonself scientific amendment

**Final spec verdict: PASS. Final code-quality verdict: PASS.** The earlier important finding is resolved. No remaining critical or important findings within this re-review scope. This verdict supersedes the initial changes-required verdict above.

Reviewed the appended task amendment and implementation report, final named-file diff, live relevant implementation/test sections, latest two focused test logs and updated preview. Parsed both original/final supplied diffs: final diffs exactly match both live files. The delta contains only the fixed declaration checks, nonself condition/routing metadata changes and their regression tests; cluster selection, transform surgery, alignment, hash and accounting helpers are unchanged.

- `evaluation/selective_diagnostics.py:412` now enforces the exact condition-mask map, complement/heads-only/leaf/seed declarations, generation-transfer and selection identity, and the complete fixed selectivity policy. Lines421-425 enforce original outcome-filtering disclosure and prohibit new screening/survivor-list use with strict Boolean identity. Regression cases explicitly rehash before demanding rejection.
- Conditions at lines17-35 retain eight primary cells and change D-minus-F/random plus the two small-view conditions to the approved fixed nonself H donor. Lines249-255 obtain all three comparison donors from the same derangement independent of recipient policy and reject self-source/identical content. Consequently D/H recipient twins share the donor across masks. Paired core conditions remain routing diagnostics, with identities explicitly sanity_only at lines260-269.
- Intended donor-answer relationship at lines256-268 compares the actual donor answer word to recipient D/H words and otherwise records other. It resides on each recipient row; globally deduplicated donor-reference endpoints do not inherit a recipient-specific relationship.
- Tests directly compare six endpoints per source/view across three masks and two recipient policies, exercise nonself reversed/alternative views, check identity labels and D/H/other word mapping. Existing relational reconstruction in validation also rejects inconsistent row/reference metadata.
- Latest logs confirm **55 passed** in mgnp and **55 passed** in Python3.9 base (the known environmental pandas/bottleneck warning). This review did not rerun either suite, models or jobs. Updated preview still reports1088 scores,320 recipient generations and84 references:404 total completions and38,784 maximum new tokens. The reported exact64-ID/slice preservation is consistent with the unchanged selection implementation and existing independently verified balanced preview.

Proceed to Task2 under the amended scientific interpretation: comparisons measure effects conditional on nonself mismatched-content interchange; paired core rows do not establish benign preservation. Actual donor validity, EOS/short-donor handling and execution remain Task2 responsibilities.

Final reviewed file identities:
- `evaluation/selective_diagnostics.py`: SHA256 `2c7c3d8f5714d316bedba21a13307956ed722510116143d9bfc61ce06383d127`.
- `tests/test_selective_diagnostics.py`: SHA256 `782b4b94cc26e283934718a6ccd024be411f23b4f9b052db772445d10a671a1c`.
