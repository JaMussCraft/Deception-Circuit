# Independent compute-account amendment source review

Status: handed-back

## What changed

**Source/spec and quality verdict: PASS for the account-only amendment mechanism. Actual applied amendment validation remains required before release.** Exact new authorizer SHA is `220b0888a23ad5d0f7c77b64deb80ef5bc1a80b5ae02f4a8e533aa71c25c9c4f`; immutable original placement SHA remains `fed51952deb8a1237a26edbb02083d6fc9bc3aa9f40f142009e9d56c99b311fd`. The user-authorized billing change affects only the named pending jobs; original running job `50148389` retains its original account. [Bindings](133-account-amendment-review-evidence/run_manifest.json).

The original application, outer launcher, job script, source/config, numerical environment, storage/cache paths, logical cells, job IDs and original reservation charges remain unchanged. The new immutable amendment supplements the original placement; it does not rewrite original ledger account facts. The candidate authorizer derives expected live billing account from the independently validated amendment while preserving original ledger identity checks. [Exact delta](133-account-amendment-review-evidence/authorizer-delta.diff), [original placement](133-account-amendment-review-evidence/scientific-placement.json).

## How verified

Inspected the exact old/new authorizer delta and parent placement. The amendment validator binds original/new authorizer hashes, parent/source, named cell/reservation IDs, old/new accounts and genuine scheduler-record structure. Applied records must show pending zero-runtime jobs with the post-change hold, preserving essential resource, command and work-directory fields. Live authorization separately rechecks actual billing, typed GPU count, CPU/RAM, time limit, account/partition, command/workdir, original ledger/caps, cancellations, source preflight and current catalogs.

Executed exact amendment and live-allocation AST predicates using genuine before-records and explicitly synthetic after-records. The five-job positive and amended/original live-account positives pass. Seventeen negative mutations reject, including unknown job, wrong account/resource/source/cell/reservation, parent/hash mismatch, unapplied/unheld status and nonzero runtime. Actual scheduler changes were not performed or inferred from fixture success. [Predicate evidence](133-account-amendment-review-evidence/predicate-check.json), [synthetic transport fixture](133-account-amendment-review-evidence/synthetic-amendment-fixture.json).

Sourced the actual frozen Bridges profile in an isolated local environment with scheduler billing account `cis260372p` while retaining `DC_B2_ALLOC=cis260361p`. It exits successfully: `DC_ACCOUNT`, packed environment and cache paths remain the original storage profile. The actual frozen wrapper/training path has no account-versus-Slurm equality refusal. This path launches no nested scheduler submission that would use legacy `DC_ACCOUNT` as a new billing request. [Actual profile probe](133-account-amendment-review-evidence/profile-check.json).

## Execution evidence

The proposed change distinguishes actual compute billing from legacy storage/profile configuration. `SLURM_JOB_ACCOUNT` can propagate through the unchanged outer launcher, but the native training receipt's frozen `SAFE_ENV` does **not** persist it. Therefore actual billing provenance must remain in actual scheduler before/after records, the immutable applied amendment and new authorization's `actual_compute_account`/amendment hash. The new authorizer records those fields; do not claim the native receipt alone proves the billing account. [Recorded environment contract](133-account-amendment-review-evidence/profile-check.json).

The original running job's expected-account branch remains the original placement account, and the pending-job branch accepts only the validated new account. No source, storage or numerical change is needed to use the proposed billing allocation. Fair-share/test-only scheduling observations motivate the change but are not completion or start-time guarantees.

## What is NOT done

No remote calls, Slurm/account updates, job release/cancellation/resubmission, ledger writes, git, source edits, models, GPU work or subagents. This review does not validate a future synthetic after-record as an actual scheduler observation. Existing scientific and publication gates remain those already reviewed.

## Open questions

Root must publish the actual append-only applied amendment after changing only the five still-pending, held, zero-runtime jobs; validate its actual before/after records against the original placement and exact new authorizer; and run the live checks before release. Keep original reservation fields/charges and the already-running job untouched. Retain actual billing provenance at completion and in the eventual scientific placement audit. No concrete source blocker remains in the reviewed mechanism.
