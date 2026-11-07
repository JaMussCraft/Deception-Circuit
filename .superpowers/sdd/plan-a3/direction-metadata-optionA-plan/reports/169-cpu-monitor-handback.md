# CPU and oracle marker monitor hand-back

## What changed

No run artifacts or source were changed. Read-only marker observations:

- `original-base-r2-01`: `BUILD_FINISHED_NOT_ORACLE.json` reported `complete:false`, build time 2653.11 s, and remaining publisher-format stream/post-guards. `FAILED.json` later reported `complete:false`, `automatic_retry:false`, `exit_code:-15` at 2026-11-06 17:22:20 UTC.
- `candidate-mgnp-r2-01`: `BUILD_FINISHED_NOT_ORACLE.json` reported `complete:false`, build time 1561.58 s, and remaining publisher-format stream/post-guards. `STREAM_FINISHED_NOT_ORACLE.json` reported `complete:false`, 11,421,127,399 bytes, 734.36 s, and `postguards_still_required:true` at 17:28:12 UTC. `COMPLETE_COMPARISON.json` appeared at 17:29:42 UTC; its contents were not read because the file exceeded the 8 KiB marker limit.
- CPU support job `23606524`: `evidence/READY.json` appeared at 17:24:21 UTC, with `model_admitted:false`, config SHA `5765542bee38108f07a605452af0d3ce518fd28bfdc19921f1b504a4cb25a06c`, and accepted packet SHA `4875845ad3b728980c494657aac2935e29a8a215885ddc1b9bfd81f7ba2b13f9`.
- Root later reported Slurm `COMPLETED` for candidate job `23605794` after 2411 s.

## How verified

Polled only the assigned run directories and CPU evidence directory at roughly 30-second intervals. Read only small JSON marker content up to 8 KiB; did not open `samples.jsonl` or other large artifacts.

## Execution evidence

The monitor reported the above marker filenames and timestamps. Root was notified as each event appeared. Monitoring stopped after root confirmed all three requested outcomes had arrived.

## What is NOT done

No scientific or operational acceptance was performed. No source, run artifact, scheduler state, or reservation was changed.

## Open questions

None for the assigned marker-monitoring task; root owns any subsequent review or action.
