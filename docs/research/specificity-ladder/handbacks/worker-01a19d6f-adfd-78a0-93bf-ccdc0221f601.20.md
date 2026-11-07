# Last message of worker 01a19d6f-adfd-78a0-93bf-ccdc0221f601 (2026-11-03T12:26:33-05:00)

Design161 is ready; no production edits.

Use one A2-only helper at `_validate_live` and `_manifest`. It must call the original grader validation, enforce canonical routes, and retain frozen catalogue hashes as provenance.

Tradeoff: non-grader metadata changes, including on the specificity entry, become permissible. Tests will cover both positive paths and grader, route, protected-data, source and artifact invalidations.

Design hash: `cf8c6bf8…`. Awaiting root acceptance.
