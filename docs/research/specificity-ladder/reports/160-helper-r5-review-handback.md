# Independent usage-reset helper review

Status: blocked on complete captured-reset parsing

## What changed

Reviewed the immutable reset successor against the accepted design. One blocker remains: the exception regex accepts a numeric prefix from malformed captured-reset tokens. No author files were changed. [Verdict and actual probes](160-host-split-operational-review-evidence/helper-r5-review/verdict.json).

## How verified

Rehashed manifest members and compared predecessor/successor bytes. All helper content outside `validate_usage` is identical. Read the original tests, new matrix and raw RED/GREEN logs. Ran the brief pure tests in both supported environments and probed malformed reset tokens and reset-epoch wobble without operational actions. [Provenance](160-host-split-operational-review-evidence/helper-r5-review/run_manifest.json), [raw helper](160-host-split-operational-review-evidence/helper-r5-review/helper.py).

## Execution evidence

No Slurm job: metadata-only pure tests ran locally. Base observed 46 passing cases against 46 expected; mgnp observed 46 against 46 expected, both exit 0. The original 42 cases remain present. These fixtures do not constitute scientific baseline replication or model execution. [Observed counts and baseline scope](160-host-split-operational-review-evidence/helper-r5-review/verdict.json), [execution provenance and scientific source identity](160-host-split-operational-review-evidence/helper-r5-review/run_manifest.json).

The raw RED log contains 7 expected errors: 5 behavioral reset-equality rejections and 2 absent-route telemetry errors. The completed GREEN logs pass, but omit the malformed full-token cases independently found here. [RED interpretation](160-host-split-operational-review-evidence/helper-r5-review/verdict.json), [raw RED](160-host-split-operational-review-evidence/helper-r5-review/red-base.log).

## What is NOT done

No operational acceptance, release, remote access, scheduler or usage-infrastructure mutation. No scientific source change or broader suite rerun.

## Open questions

Publish a separate immutable correction that validates the complete exception/reset line or token and rejects fractional, exponent and suffix text. Add focused negative cases before returning for review. All existing projection, cap, freeze, freshness and phase guards must remain unchanged.
