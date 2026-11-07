# Direction M1 dependency scope

Status: handed-back

## What changed

Read-only tracing distinguishes the two direction M1 timing parts from downstream scoring. A scoped independent readiness review is justified without automatically waiting for calibration, assessment or final summaries. This is a review recommendation, not an admission decision. [Source-backed trace](m1-dependency-trace.json), [direct static call graph](source-call-graph.json).

## How verified

The actual wrapper delegates through the canonical pipeline and direction runtime parser into `dispatch`. For `stage=pilot`, dispatch validates the frozen stage inventory and live source/protection/reservation/allocation, loads the exact model, and calls `run_pilot`. The pilot branch never calls scoring intake/index construction, assessment preflight, runtime-row readers or summary functions. [Dispatch excerpt](source-evidence/a3_direction_runtime--dispatch.py), [CLI delegation](source-call-graph.json).

Both pilot parts build a target workload inventory for complete timing/serialization/cost coverage. Prefit targets fit/validation metadata; selected timing targets the frozen remaining workload and loads actual selected numeric axes. Those metadata paths are dependencies and still require verification. The pilot does not read completed calibration or assessment shards, conditional-power output or a final summary. Timing batches explicitly require validation membership. [Producer](source-evidence/a3_direction_runtime--run_pilot.py), [target builder](source-evidence/a3_direction_workload--build_inventory.py), [split guard](source-evidence/a3_direction_runtime--_batch_for_timing.py).

## Execution evidence

Saved prefit native aggregation completed all 9 original cases, replaying the separately saved 1,863 original-case forwards while executing 153 new reconciliation forwards in 98.80 seconds. Current selected-case coverage is 63, while selected aggregation and calibration scoring remain unexecuted. These software observations are injected and cannot authorize production. [Preserved raw prefit path and digest](m1-dependency-trace.json), [current scope](m1-dependency-trace.json).

The full selected aggregation still exercises directly relevant new proof publication, complete target reconciliation, serialization and full dependency-union work; it must not be called verified merely because cases authenticated. Conversely, calibration scoring introduces the separate completed-source index, target profile-reuse, startup-record and shard-publication path. Assessment later adds conditional-power preflight; summaries consume complete raw rows. Those future paths are not reached by an M1 producer. [Aggregation](source-evidence/a3_direction_native_scenario--aggregate_pilot_cases.py), [scoring](source-evidence/a3_direction_runtime--run_scoring.py), [assessment preflight](source-evidence/a3_direction_runtime--assessment_preflight.py), [index](source-evidence/a3_direction_runtime--_completed_pilot_index.py).

## What is NOT done

No model execution, source change, gate relaxation, new scientific result or GPU admission occurred. Root/reviewer must still assess exact frozen source, actual inputs and all genuine live protection, reservation, allocation, control, footprint and time/cost requirements. A metadata target naming later work does not establish that later outcomes ran. Full CPU verification remains incomplete. [Limits and decisions](m1-dependency-trace.json).

## Open questions

Initial prefit M1 may receive its own independent readiness review based on the paths it actually uses. Later selected M1 additionally needs actual production fit/selection/axis lineage and review of its selected aggregation/reconciliation seams. Root decides readiness and any release. Full calibration/assessment verification continues separately; it must not be mistaken for an implicit prerequisite to every limited timing pilot.
