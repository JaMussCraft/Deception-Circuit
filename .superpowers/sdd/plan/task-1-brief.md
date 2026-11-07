### Task 1: Exact-format transport and phase snapshot

**Owner/model:** Sol; independent Sol review of data/provenance semantics. No parallel writer in these hunks.

**Files:** Modify only private prepared-transport helpers in candidate `component_analysis/a3_direction_runtime.py`; create `tests/test_a3_prepared_pilot_target.py`. Do not modify generic `publish_object`, `read_object`, `object_reference`, `_FileWitness` or workload functions.

**Interfaces:** `_publish_prepared_target_object`, `_prepared_namespace_identity` and `_read_prepared_target_object` as defined in `contracts.json`. Reader returns the frozen value, immutable entry refs, namespace identity, phase witness and observed I/O; no authority. Phase witness uses resolved artifact roots and is never inserted into existing per-operation numeric forests.

- [ ] Write T1 tests first using existing publisher artifacts as fixtures; new helpers are called in test bodies so missing functionality yields attributable RED calls, not collection/setup errors. Include floats/Unicode/frozen containers/default JSON separators and final LF, actual byte hashing, re-signed-file races and exact child/marker semantics. Do not add unreviewed stricter JSON/schema policy.
- [ ] Prepare root-only bounded dual-environment RED packet; assert candidate/oracle module origins and source pins before/after. Root observes the intended missing-transport failures before code edits.
- [ ] Implement only the declared codec/namespace/reader helpers. Bind the writer-emitted bytes; use one target byte buffer for hash+parse; freeze once. Mint the existing phase witness and check exact entry hashes/identities. Approved pre-entry materialization and in-phase replacement policies remain distinct.
- [ ] Root runs T1 GREEN on both interpreters. Exercise the lower reader (two reads/SHA passes: same-buffer read and entry witness mint) plus its explicit final phase-witness recheck (one): total target reads/SHA passes `3`, parse/freeze `1`, receiver target writes `0`. T3 places that last recheck in the real final barrier. Never add a redundant startup scan to force the count; these are verified via actual observers, not source-text assertions. If the correct implementation needs more passes, stop and report the real count for root cost review rather than hiding it.
- [ ] Freeze the task's source/test hashes, raw diffs and results for independent review. No commit/publication by workers; Task 2 starts only after this source-pinned run is terminal and root accepts the handoff.

