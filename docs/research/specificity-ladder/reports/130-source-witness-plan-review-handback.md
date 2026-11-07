# Independent fresh-witness batching plan review

Status: handed-back

## What changed

**Plan verdict: ACCEPT as a narrow measured experiment, with the binding implementation conditions below.** Reviewed exact plan SHA `d9b00f4aca92f55da44693aca86648046b3013a11665bdd20fa3b032f178eba8` against frozen source `f5a5687ec12091f0d148b38b301598e9c7cb98cd`. This is no implementation, performance or model-admission acceptance. [Review binding](130-source-witness-plan-review-evidence/run_manifest.json), [exact reviewed plan](130-source-witness-plan-review-evidence/reviewed-repair-plan.txt).

The proposed scope is appropriately small: source helper and focused tests, original witness/authority APIs unchanged, shared path observations only within one fresh scan, every original file occurrence fully hashed, and current registry/grader/authority cadence preserved. Recorded profiles support investigating repeated path work. They do not show that this experiment will solve the existing pilot-cap problem. [Raw profile facts](130-source-witness-plan-review-evidence/residual-profile-summary.json).

## How verified

Inspected actual frozen witness row construction, metadata fields, directory ordering, symlink handling, source-state mint/refresh and memory accounting. Compared the plan with the earlier source-safety closures and genuine source-cost findings. Author report prose was excluded. No broad suite or heavy data measurement was needed.

The implementation must preserve these conditions:

- **Authenticate the compiled proof.** Use a private sealed process/owner-bound plan tied to the exact owner-minted witness object and immutable copies of its original nonempty roots, identity rows and order. Reject raw, empty, wrong-process, altered, replaced or reinitialized witness/plan objects. Type, PID and the witness's current `_sealed` flag alone do not establish mint provenance. No caller-provided subset or current mutable witness fields may replace the original expected proof.
- **Compile under the existing stable mint boundary.** Keep the early artifact-envelope witness spanning first artifact comparison, dependency discovery and full semantic validation. Bind the full root/row graph, lexical aliases, relative link literals, intermediate target aliases and canonical targets without normalizing away provenance. Preserve overlapping-root row order and every repeated file occurrence. Original full witness checks around compilation can provide the unchanged initialization oracle; inconsistent or incomplete route plans reject.
- **Keep observations fresh and scopes exact.** Pre-scan and closing phases must obtain independent fresh metadata, links and memberships. Compare all actual witnessed file/directory/symlink rows with their original identities and child lists. Route-only regular ancestors need fresh routing/coherence checks, without introducing mint-frozen parent content timestamps or membership requirements that would reject unrelated atomic catalog updates. Newly referenced protected files remain on the current dynamic validator path.
- **Bind the bytes to opened files and closing paths.** Require the opened descriptor to be the expected regular file, compare all expected identity fields with `fstat` before and after reading, read/hash the complete expected byte count through EOF for every occurrence, and close descriptors on errors. Fresh closing file-path, directory and full route checks must reject replacement after open, after an earlier file was hashed, or after a shared prefix was first inspected. A cached pre-scan resolution or descriptor alone cannot authenticate the closing lexical path.
- **Preserve failure and accounting behavior.** Do not rebase expected rows, silently regenerate a graph after failure or fall back to a weaker acceptance check. Keep missing dependencies, New30 absence, full grader glob membership, actual protection/grader calls and all live authority checks/cadence. Include every new graph/index allocation in actual retained-size traversal and consumed initialization/host-peak fields; a new private class must not disappear from the existing size walk.

These are concrete implementations of the plan's stated invariants, not permission to broaden the authority implementation or skip byte obligations.

## Execution evidence

Tiny temporary baseline-contract probes confirmed why the authentication condition matters: the original exact witness checker accepts an empty raw exact-type/PID object, and ordinary deletion of the seal followed by reinitialization can replace its roots/rows with empty values. Binding immutable initial roots/rows in the new owner-held plan detects that alteration. The probe did not mint an operational source context or confer authority. [Tiny contract evidence](130-source-witness-plan-review-evidence/tiny-contract-clarifications.json), [exact frozen witness AST](130-source-witness-plan-review-evidence/exact-frozen-witness-ast.txt).

A separate tiny temporary atomic catalog update changed shared parent directory metadata while the original static file witness remained valid. This grounds the distinction between actual witnessed directory membership and route-only normal-parent observations. It is not a request to relax symlink, file or source-directory checks. The earlier genuine-input registry update/overlap behavior remains a required regression.

## What is NOT done

No implementation, source edits, heavy real-input profiling, model/weight/GPU work, remote access, git, research-session/reservation/scheduler mutation, notebooks or subagents. The separately running native tiny case is outside this review. No feasibility claim, cap change or authority exception is made.

## Open questions

No fundamental blocker to the bounded experiment remains if root carries the conditions into implementation acceptance. Focused tests must compare exact original versus batch rows and byte occurrence counts, including overlapping trees, duplicate aliases, completions, relative/chained links and cycles. Force changes after prefix observation and after an earlier file read: same-size content, rename/replacement, same-byte leaf/ancestor retarget, membership/disappearance, and descriptor/path disagreement must reject. Preserve raw-new/empty/reinitialization/forged-proof, valid unrelated registry update, overlap/stale-grader and unchanged B1/B2 tests.

Run the focused suites in both interpreters before root freezes an exact candidate. Then prepare genuinely new artifacts and compare original versus batched observations on the same candidate inputs, preserving every file occurrence and actual byte count; new source file sizes need not equal the previous freeze. Record real initialization, retained/transient RAM, clean refreshes, path-call changes and separate-copy negatives. Any residual cap or mandatory IO problem remains a separate practical-readiness decision.
