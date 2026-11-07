# Diagnosis 209 — concrete root ruling requested

Status: handed-back. Diagnosis/proposals only; no active candidate, failed source/result bytes, RAM limit, job or production implementation changed. Prior HOLD note is retained in `HOLD-checkpoint-original.md`.

Recommend the selected-only **domain-only** fixture proposal plus the narrow child-status runner proposal. Both diffs are reviewable here. Then authorize one fresh, staged CPU preflight under the existing limit; do not claim the smaller fixture fits until its original validators and actual RAM observations complete. No automatic retry.

## Evidence and localization

Root job 23616760 was OUT_OF_MEMORY 0:125 after 384 seconds, MaxRSS 8383100 KiB in eight GiB. Prefit completed in 5.5538 seconds; selected never produced a completion result. The selected backing itself had already been published: nine records, 2,097 axes, 8,392 array files; declared total backing size 6,847,970 bytes, including the 4,319,943-byte manifest. In contrast, the fixture emitted a 549,578,211-byte **selected-pilot** inventory and another identical declared-hash payload as `authority/upper`. No remaining/M2 target was materialized.

The stored selected-pilot host envelope was 32,305,594,882 bytes (30.09 GiB). This is an existing conservative full-retention bound, not a measurement of required RAM. The eight-GiB request was not justified by selected-fixture sizing. Actual OOM proves the executed path exceeded its request; it does not prove numeric selected backing intrinsically needs that amount.

The last published constructor artifacts are `admission-1`, `mapping-1`, and `reservation-1`. After these, the preflight independently calls `_validate_inventory`, then `c.guard`. The latter performs another upper-inventory read/reconstruction, original admission/ledger/allocation checks, and `_AuthorityContext` retained-graph walk/freeze plus canonical inventory readback and full witness reads. Multiple original/decoded/rebuilt/frozen graphs and JSON buffers may overlap. **The old log cannot identify which exact call OOMed:** it stores only `active_case=selected`, no substage checkpoint. Report the interval, not an invented exact function.

## Narrow selected fixture correction

`fixture-domain-only.diff` / `fixture.py.proposed` changes only the new injected fixture helper:

- Selected-only synthetic mechanism validation: one ID per task instead of two; retain all five conditions and both streams.
- Selected-only assessment IOI: one item; assessment MMLU: two different questions, using original donor-map factories.
- Keep validation IOI at two, mandatory validation MMLU at thirty-two, four training IDs/two clusters, all three tasks/seeds/nine records, 199 assessment and 32 calibration axes per record, fitted nuisance and all operation families.
- Keep original microbatch, axis tiles and padding policy. No production/native/workload algorithm or registered scientific row count changes.
- Regenerate protocol/source/utility bindings and all selected backing through the original factories. Never relabel the old selected artifact.

The tiny probe executes the original grouping and selection-source/map functions: failed fixture 84,366 keys/63 packed invocations; recommended dimensions 45,315 keys/63 invocations. Its failed-fixture count exactly matches the stored authority-key proof. It validates source membership and donor-map minima, **not** full inventory validation or a RAM upper bound. Every existing test assertion/case remains; no test bodies need changing. Alternative probes producing fifty-four invocations or changing microbatch/padding are explicitly NOT recommended.

## Narrow runner correction

`runner-child-status.diff` / `run_packet.py.proposed` persists the started row and raw child return code/stdout/stderr before source checks/XML parsing, reports absent JUnit explicitly, preserves timeout output, and accepts RED only through the unchanged complete count/assertion checks. A killed/partial run never becomes RED.

The exact original observer block was executed with a tiny self-killed child: return -9 led to FileNotFoundError before any result row. The proposed block persists return -9/signal nine and an explicit MISSING_JUNIT failure with RED unaccepted. Each probe took about two seconds, with no runtime/model/fixture build.

## Next bounded CPU step after root ruling

Apply accepted test/runner deltas only in a distinct revision/packet, retaining all failed evidence. Before any full combined RED attempt, persist per-step checkpoints and actual process/cgroup observations around constructor completion, independent `_validate_inventory`, `live_guard`, `make_authority_context`, `validate_reservation`, `_AuthorityContext.__init__`, `_retained_json_bytes`, and `_freeze_json`. Call each original function unchanged; do not retain its input graph in logs. This is test-only diagnostics, not a new production injection seam or resource admission record.

One root-authorized compact selected preflight can establish actual bytes, all nine/199/32/63 counts, original validation success and peak/event evidence under the existing limit. If it still exceeds the limit, the last durable stage supplies the missing substage. Root then chooses a measured resource revision or further lawful synthetic-domain reduction explicitly; no guessed RAM increase. The full coherent GREEN matrix and genuine final-source resource/numerical/admission gates stay required.

## Preservation and artifacts

`forensic-evidence.json`, `scalar-selected-domain-result.json`, `observer-repro-result.json`, `observer-proposal-result.json`, and `run_manifest.json` contain the bounded evidence. Candidate and failed-packet source pins still match. A diagnostic import briefly created a bytecode cache; it was timestamp-identified and removed, subsequent probes disable bytecode, and `bytecode-side-effect.json` records the directory-mtime caveat. Original source/result bytes were not changed. No A2-worker files were touched.
