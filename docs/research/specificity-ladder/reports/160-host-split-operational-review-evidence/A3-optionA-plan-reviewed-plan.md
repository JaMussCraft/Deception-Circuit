# A3 Metadata Option A Implementation Plan

> **For agentic workers:** Use the executing-plans workflow after independent plan acceptance. The assigned worker implements tasks in this isolated candidate; root alone runs git, RS and scheduler actions.

**Goal:** Remove discarded metadata work while preserving identical outputs, errors, bounds, control scope and live guards for identical frozen inputs.

**Architecture:** Keep every existing public API and canonical encoding. Add local source lookups and a length-only target view inside the builder; reuse unchanged local storage-calculation constants. Retained timing records remain independent deep copies. Runtime reconstruction and validation are untouched.

**Tech Stack:** Existing Python, pytest and standard-library profiling/hashing; both supported interpreters.

**Spec:** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-cost-design/design.json`, restricted to option A by root. Machine-readable resources and oracle contract: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-plan/plan.json`.

## Global Constraints

- Original runtime `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-861f84a3938a/runtime` and the active worktree source stay untouched. Candidate `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-candidate` is a new ordinary copy, not a git operation.
- Only candidate `component_analysis/a3_direction_workload.py` and `tests/test_a3_direction_workload.py` may change. Preserve all other copied source bytes and input aliases.
- Keep `digest`, `_source_rows`, `_validate_inventory`, runtime post-model rebuild and all live authority/source/protection checks unchanged. No global or cross-call cache, retained record sharing, GC/model/clock injection, authority change or cap increase.
- Failed partial payloads are unusable as oracles. A reference must finish the original build and the complete byte-stream traversal with successful postguards and a final receipt.
- For identical frozen inputs, whole serialized bytes, canonical hashes, row/requirement/control domains, every storage integer and documented error type/message remain exact. New genuine source publication later requires fresh source-bound artifacts.

## Review Focus

- Tail padding and dummy aliases must preserve ordered deduplication and repeated first-row lengths; Task 1 tests this.
- Retained timing source records must remain independently mutable without changing another record or the original design; Task 1 tests this.
- Source/ID/condition/stream/readout failures must reject with the original exception and message; Task 1 compares errors.
- Caches must end with one builder/storage call and must not mask a changed input on a later call; Task 2 tests this.
- Conservative host/disk/control accounting must be byte-identical even when local constants are reused; Tasks 1 and 3 test complete output and bounds.

---

### Task 1: Establish the red semantic and work-elimination tests

**Files:** Modify candidate `tests/test_a3_direction_workload.py` only; original fixture entrypoints are `fixture()` and `inventory(stage='fit-select')`.

**Interfaces:** The unchanged API is `build_inventory(design, protocol, *, stage, fits=None, selected=None) -> dict`. Load the original workload module by its pinned absolute file path under a distinct oracle name; normal project imports must resolve only to the candidate.

- [ ] After plan acceptance, copy and fingerprint the original source/export into the new candidate. Assert the original snapshot and all frozen native files are unchanged; do not run git.
- [ ] Add `test_option_a_whole_output_matches_original` over every original stage and padding/tail geometry. Assert recursive API container/scalar types, entire original-format JSON bytes, canonical digest, counts and storage requirements equal the original module.
- [ ] Add `test_option_a_retained_timing_records_are_independent`, `test_option_a_target_lengths_preserve_padding_and_deduplication` and `test_option_a_invalid_sources_match_original_errors`; mutate one retained token list and assert all other records/design remain unchanged. Cover missing/duplicate source membership, malformed readout/width, utility donors and no-padding/singleton branches.
- [ ] Add red performance contracts using test-only observers: `test_option_a_never_copies_target_only_rows_for_lengths`, `test_option_a_source_rows_scanned_at_most_three_times_per_group` and `test_option_a_sender_constant_encoded_and_bounded_once`. The observers distinguish top-level row-copy calls from the legitimate frozen-input deep copy. Exact whole-output tests prevent a false pass from omitting accounting.
- [ ] Prepare a root-submit red CPU packet for both interpreters using the red-subset resource request in `plan.json`. Pin module origins before/after, use `--confcutdir` at the candidate and importlib mode, disable bytecode/cache, and record failed node IDs.
- [ ] Root runs the packet. Expect the new work-elimination contracts to fail on the unchanged original algorithm while semantic equality tests pass. Preserve red evidence; do not edit production before this result.

### Task 2: Implement the minimal local metadata changes

**Files:** Modify candidate `component_analysis/a3_direction_workload.py`; extend the same focused test file. No runtime or grader file changes.

**Interfaces:** Public signatures and output schemas do not change. Nested helpers inside `build_inventory` may be `source_rows(task, split)`, `source_row(task, split, condition, instance_id)` and `target_unmasked_lengths(keys, profile)`; their caches live only for that invocation.

- [ ] Reuse original `_source_rows` results through one local builder index while preserving its validation and ordering. Do not change the standalone helper or memoize across calls.
- [ ] Derive discarded target lengths directly from checked source rows and the existing padding/deduplication rules. Continue to deep-copy every retained timing source record exactly as before.
- [ ] Reuse the unchanged local sender-list wire/host bound and existing extra-envelope wire/host values inside `derive_storage_requirements`; cache local profile sizes only with the existing full profile identity. Keep every conservative charge and numeric value unchanged.
- [ ] Add `test_option_a_changed_input_between_calls_not_cached`; change IDs/tokens/profiles between calls and require the original changed result or rejection, never a stale cache.
- [ ] Root runs the red subset again on both interpreters, then the full focused workload suite and affected inventory caller tests under the bounded request in `plan.json`. Expect all new and original tests to pass; failures stop the stage without automatic retries.
- [ ] Save exact two-file hashes/diffs and independent import/source checks for peer review. Root alone may commit or publish later.

### Task 3: Produce a complete original oracle and honest genuine comparison

**Files:** Create CPU-only comparison/profiling wrappers outside the candidate under this plan directory. They are not production source or admission adapters.

**Interfaces:** Each environment writes a new `COMPLETE_ORACLE.json` binding full original source, genuine input hashes, complete original `inventory_sha256`, full original-publisher UTF-8 byte-stream SHA and length, exact bounds/counts and actual CPU/peak evidence. Candidate comparison consumes only that complete receipt.

- [ ] Prepare one bounded original-oracle CPU job per interpreter. Run fresh original source/input/protection guards, load the genuine frozen design/protocol, call the unchanged original builder, and stream the complete original publisher encoding into a hash-and-byte-count sink through the final newline. Write the final oracle receipt only after successful stream completion and all postguards. Do not read any part of the failed payload as a reference.
- [ ] Record builder time separately from whole-stream time and source/readiness time. Collect actual job cgroup peak/events and child CPU, source/module origins and allocation/CPU model. The high-memory terminal evidence justifies the request; it does not guarantee completion.
- [ ] After independent two-file source review, prepare one candidate comparison CPU job per interpreter with identical frozen inputs and resource/measurement boundaries. This is a pure algorithm equivalence harness with explicit original and candidate module paths, not a production run under a false source identity.
- [ ] Require exact full-stream hash and byte count, canonical inventory hash, every conservative bound/count and all row/control domains to match the complete original oracle. Candidate success cannot be inferred from a prefix, decoded partial, tiny fixture, equal row count alone or an unfinished receipt.
- [ ] Keep genuine runs unprofiled for fair measurements. Use complete small four-stage fixtures for standard CPU profiler/call-count diagnosis; do not extrapolate their timing into admission. If genuine evidence still needs deeper profiling, return a separately bounded proposal rather than altering a running job.

### Task 4: Review correctness, cost and remaining readiness

**Files:** Final evidence and handback only; no additional production edits.

- [ ] Independently review the exact source diff, both-environment tests and complete genuine oracle comparisons. Confirm retained-record independence, unchanged validators/runtime callers and no hidden authority or bound change.
- [ ] Compare actual builder/stream CPU and cgroup peak against the original using recorded hardware/measurement scope. Report any timeout or incomplete oracle as incomplete; do not claim a speedup from failed runs.
- [ ] Root separately sizes and runs required original readiness/independent inventory validation after candidate cost and artifact sizes are known. Its reconstruction and simultaneous-retention peak are not waived or assumed equal to creation. No blind memory or time request is made for that later phase here.
- [ ] Recompute the complete paired M1 allowance including both startups, pilot reads/rebuilds, post-model target rebuilds, all forwards/proofs/publication and finish reserves. Correct metadata alone does not establish H200 feasibility or authorize a GPU reservation.

## Root resource packets

Use the exact resource objects in `plan.json`; root chooses placement and dependencies. Red tests, focused suites and the complete genuine per-environment oracles are distinct bounded jobs. Original and candidate genuine runs use the same conservative envelope. A failed bound produces a checkpoint, not an automatic extension or rerun. Root schedules these CPU tasks around the separately admitted standing A2 helper.

## Plan review and execution gate

This plan is ready for independent review. No candidate, production edit, profiler, CPU job or model execution has been started by this plan. Root already chose inline worker execution after plan acceptance; do not ask the user to choose an execution method again.
