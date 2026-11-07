# A3 sharded validation review272 r2

Status: handed-back. SOURCE ACCEPTED for bounded CPU validation deployment review only. Scoped spec and quality verdicts pass; B1–B3 are addressed.

## What changed

Created only reviewer-owned r2 snapshots, checks, logs and [verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/r2/verdict.json). Exact source-pins `0028bac99907b0f44781d668d3cd97f58030ac51c493c857456a58b90b7b1833` and partition `73aa13bd780837687cc2953fe6f64cd1df60b92056d856b7aad74d0dfb8a5306` bind this successor. Original r6 and review272 remain preserved; no implementation edits or actual-job actions occurred.

## How verified

**B1 addressed:** job/child/execution separates child data from host receipts. All three stage command plans bind only child writable, with host-before/after and prior command/terminal receipts under the read-only job root. The old layout is rejected. The aggregator independently requires host-after at that job root. Inner receipt filenames remain stage-specific; fresh child directory creation leaves execution available for baseline's exclusive creation. Actual container denial/permission behavior remains a root deployment gate.

**B2 addressed:** execute_stage captures original wall and monotonic bounds before source/image validation, command construction, receipt writing and log opening. The supervisor receives both, shrinks without renewal and checks both after the final allocation query immediately before Popen. Post-reap checks remain bounded; shared cleanup and error preservation remain. Independent final-log checks verify wall-only expiry and monotonic-only expiry launch no child, while valid remaining time keeps the original deadline.

**B3 addressed:** partition and validator contain the exact two corrected-family literals. Repaired cases come first in stable original order; complete223 collection and112/111 parity membership remain unchanged. An internally consistent wrong-family partition is independently rejected. No new blocker was found in these corrections. Original34 test function ASTs, selector, conftest, baseline, preflight and corrected native fixture remain unchanged; earlier review conclusions outside this scope are reused.

## Execution evidence

Exact frozen source/member hashes and raw evidence identities match. Three fresh post-log checks pass in each supported interpreter. Additional pure checks confirm all three mount plans, legacy-layout refusal, correct/wrong literal-family handling and host-reachable Python3.6 grammar. [Fresh runs](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/r2/run_manifest.json), [mount and family checks](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/r2/mount-plan-and-family-checks.json).

Read raw twelve RED failures and forty-six GREEN passes per interpreter, including original thirty-four retained cases, with matching test-source hashes. Complete forty-six-case runs were not repeated. Source-bound observer and relocated pure-wrapper checks exit zero in both interpreters with actual job/config NULL and no scheduler calls. Known original r6 review-snapshot hashes still match. [Pins and attribution](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/r2/pins-and-correction-checks.json). Latest live usage is forty-one percent, cap eighty and cadence forty.

## What is NOT done

No native/full validation, actual host/container permission acceptance, deployment/config/job binding, held release, queue replacement, model or GPU use. Pure mount-plan checks are not kernel permission evidence. No complete-validation or scientific admission is conferred; four CPU attempts remain prospective.

## Open questions

Root may proceed to distinct actual deployment review: verify exact sources/aliases/environments, host3.6 and real container behavior, private output ownership/emptiness, actual resource/config and immutable bootstrap/spool bindings. Preserve the absolute root-bootstrap interface; cpu.sbatch is not directly submitted. Final live usage/scheduler checks are required before each reviewed job release. Keep the existing four independent CPU shard proposal, thirty-two GiB/eighty minutes each, Delta two CPUs/Bridges eighteen, caps610/90/3600, final reserve120 and one fifteen-plus-five cleanup budget, with no GPU/requeue/automatic retry. Complete exact223 normal coverage in both interpreters and trusted terminal aggregation remain required before validation completion.
