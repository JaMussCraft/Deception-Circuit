# Approved mask replacement policy implementation

Status: handed-back

## What changed

Implemented the approved N5 amendment only in the new isolated candidate `mask-replacement-policy-source-r2`, derived from immutable `40fe57289405fd53a3fce02e5d4e47a0ebf78b64`. Active worktree code, old runtimes, original artifacts and original charges were preserved. The candidate is ready for root freezing and independent review; it grants no production admission or fresh preparation. [Exact tested source hashes](149-mask-replacement-policy-evidence/source-post.json), [raw diff](149-mask-replacement-policy-evidence/candidate-diff-r2.txt)

The existing shared workload module owns a fixed policy body bound to the actual approved-policy hash, exact cancelled original reservation and original admission lineage. No new source module or general policy configuration was added. The helper counts every additional mask M1 reservation, including failed/cancelled attempts and zero actual runtime, and permits at most one. New source/job/output and admission/policy lineage are checked; original source/output/phase/requested charge cannot be rewritten or refunded. [Approved provenance](149-mask-replacement-policy-evidence/approved-provenance-binding.json), [policy body](149-mask-replacement-policy-evidence/expected-policy.json)

All affected consumers are synchronized: global budget and live reservation checks, shared ledger contingency floor, direction cost's independent all-M1 predicate, mask context limits and completed-pilot cost intake. Only actual approved replacement hours expand aggregate M1 headroom; the maximum approved mask share is used by mask context mint/validation. Other subphase/milestone caps and the total remain unchanged. [Source diff](149-mask-replacement-policy-evidence/candidate-diff-r2.txt)

## How verified

Tests were written before source implementation. A tiny stdlib probe executed the exact original budget function and observed its refusal of the approved cumulative share. After implementation, exact-source pure checks covered prospective old-only construction, the actual single replacement, the total boundary and a third-attempt refusal. All substantive tests ran in root-submitted CPU allocations, with separate interpreter temporary directories and no cache provider. [Red evidence](149-mask-replacement-policy-evidence/red-stdlib-budget.json), [pure green evidence](149-mask-replacement-policy-evidence/green-stdlib-budget.json)

The construction-order integration starts with only the authentic cancelled original mapped. The new prospective admission check is explicitly nonauthorizing and needs no fabricated new mapped reservation. It then publishes an actual software-fixture reservation and append-only successor, binds the completed admission and exercises the existing full live validator with an explicit software allocation fixture. The canonical path rejects that adapter. Separate tests cover genuine completed-pilot cost intake, original charge retention and failed-pilot refusal. [Exact selected tests](149-mask-replacement-policy-evidence/round2/pytest-selectors.json)

Boundary tests cover the exact total, unchanged direction/edge/other milestone ceilings, contingency underflow, overall overflow, multiple smaller attempts, original anchor changes, wrong policy/source/output/admission/anchors, and retained charges in every terminal state. Existing actual-job/resource, lease, context mutation, registry-independent authority and mapping-successor checks remain exercised. The corrected actual A1 schema test reads the unchanged original artifact through its existing explicit environment binding. No numerical path or guard was relaxed.

## Execution evidence

The first packet was too broad for its time bound and had two test-setup mistakes. Its mgnp run passed the other cases; base remained partial when the CPU job timed out. Both failures were preserved: the isolated-copy default A1 artifact path was absent, and the new software lease used distinct clocks, producing a duration slightly beyond the accepted bound. Root authorized only a new-copy single-clock fixture correction and the existing A1 artifact environment binding. Production module bytes did not change. [First attempt diagnosis](149-mask-replacement-policy-evidence/round2/attempt1-diagnosis.json), [first raw log](149-mask-replacement-policy-evidence/mgnp-pytest.log), [first terminal accounting](149-mask-replacement-policy-evidence/attempt1-terminal-accounting.txt)

| [Retained first attempt](149-mask-replacement-policy-evidence/run_manifest.json) quantity | Value |
|---|---:|
| mgnp passed | 280 |
| mgnp test-setup failures | 2 |
| mgnp test seconds | 458.16 |
| Job timeout elapsed seconds | 605 |

The corrected packet includes all new N5 tests, both earlier failures and directly affected existing cost/cap/ledger/admission/reservation/context/lease/successor tests. It omits unrelated expensive workload-generation and unchanged numerical scheduling coverage. Both interpreters passed; actual project imports and all ordinary source/link bindings remained candidate-bound and unchanged. [Exact commands/results](149-mask-replacement-policy-evidence/round2/cpu-test-results.json), [terminal accounting](149-mask-replacement-policy-evidence/round2/terminal-accounting.txt), [completion](149-mask-replacement-policy-evidence/round2/cpu-test-completion.json)

| [Corrected CPU run](149-mask-replacement-policy-evidence/run_manifest.json) quantity | Value |
|---|---:|
| mgnp passed | 105 |
| mgnp test seconds | 43.93 |
| Base passed | 105 |
| Base test seconds | 70.99 |
| Base upstream warnings | 3 |
| Skips | 0 |
| Job elapsed seconds | 135 |
| Ordinary source files verified | 511 |
| Declared input links verified | 4 |
| Changed production files | 4 |
| Changed test files | 3 |

The CPU allocation had no GPU. Selected software tests may construct tiny injected fixture models; no pretrained weights or production model were loaded. The base warnings concern Pandas dependency compatibility and Transformers/TensorFlow deprecations and are retained in the log. [Base raw output](149-mask-replacement-policy-evidence/round2/base-pytest.log)

## What is NOT done

No canonical ledger, budget state, source admission, original artifact, active worktree or scheduler state was changed by this implementation. Root's prior approved cancellation/reconciliation is provenance, not an action performed here. No model allocation, practical runtime forecast, complete native pilot or scientific result is claimed. The complete-work plan and original unknown native/live cost limitations remain; tests do not establish a fit within the exploratory pilot ceiling.

## Open questions

Root must freeze the exact tested candidate, obtain independent source/policy acceptance, regenerate source-bound prepared/inventory artifacts on CPU and separately review actual admission/allocation/capacity/lease before launch.

For the new root constructor, set `admission.mask_replacement_policy = workload.mask_replacement_policy()` and bind `reservation_lineage.mask_replacement_policy_sha256 = workload.digest(admission.mask_replacement_policy)`. Retain the existing admission ID/hash, upper inventory, ceiling and original reserved-hours lineage fields. `validate_mask_replacement_admission` checks a prospective draft without execution authority; an empty draft anchor list must not be published as model authority. Bind the actual single reservation, recompute the final admission digest and publish its immutable successor metadata before using the unchanged production validator. No new RS ledger schema or phase relabelling is introduced.
