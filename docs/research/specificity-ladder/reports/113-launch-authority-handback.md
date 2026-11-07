# Mask initial launch authority recipe and constructor review

Status: handed-back

## What changed

Read-only launch assistance. **No additional constructor/schema/path blocker found** in root's `/tmp/a3-mask-root-launch.py` and `root-mask-m1/launch-config.json` at the hashes recorded in `113-mask-readiness-evidence/launch-constructor-review.json`. This supplements accepted bounded readiness report113; root still owns every authority/RS/job write and live admission.

The concrete config correctly distinguishes scheduler checkout `B` from fresh output `O/mask-pilot-1`, keeps `O/mask/inventory-pilot` as upper pilot inventory, and passes `O/mask/inventory-full` separately as the target. The completed prepared artifact is passed explicitly from `O/mask/prepared`. Original contract/request values are internally consistent: one H200, `4` CPUs, `64 GiB` RAM, `56 GiB` declared host capacity, `45` requested minutes / `0.75` original GPU-hours, `300`-second finish reserve and `60`-second minimum shard allowance. The duration is explicitly an exploratory maximum, not an invented measured forecast.

Minimal constructor expressions below describe actual required fields; they are not published artifacts. Here `P` is the validated pilot payload, `E` the actual canonical RS row after root registers the real job, and `A_PATH`/`SNAPSHOT_PATH` are root-owned immutable destinations. Use the frozen modules' `publish_object`, `object_reference` and `workload.digest` rather than hand-computing completion metadata.

```python
CONTRACT = dict(
    kind='a3_allocation_contract_v1',
    scheduler_work_dir=str(B), source_commit=C,
    cpus=actual_requested_cpus, memory_bytes=actual_requested_memory_bytes,
    gpus=1, gpu_type='h200',
)
A = dict(
    kind='a3_root_pilot_admission_v1', id=unique_admission_id,
    identity=P['identity'], upper_inventory_sha256=P['inventory_sha256'],
    max_gpu_hours=0.75, reservation_ids=[E['id']],
    allocation_contract=CONTRACT,
)
A['admission_sha256'] = workload.digest(A)
# Root publishes A_PATH as a completed object before constructing its reference.
R = dict(
    kind='a3_root_execution_reservation_v1',
    identity=P['identity'], inventory_sha256=P['inventory_sha256'],
    reservation_id=E['id'],
    actual_entry={k: E.get(k) for k in authority.RESERVATION_FIELDS},
    admission_path=str(A_PATH),
    admission_reference=authority.object_reference(A_PATH),
    admission_sha256=A['admission_sha256'],
    upper_inventory_path=str(O/'mask/inventory-pilot'),
    allocation_contract=CONTRACT, minimum_shard_seconds=60,
)
```

Do not add an injected allocation adapter or rely on an immutable submit-time end timestamp. Contract memory must cover the declared host capacity; current Slurm memory must cover the contract. Original reservation output must resolve to the CLI work directory, while `scheduler_work_dir` must resolve to the frozen module's actual checkout. Other reservation identity fields, including manifest hash, must be copied from the actual RS row without invention or truncating its original charge.

The external mapping covers **every** live canonical RS row, including prior A1/A2 work. Each historical item needs `reservation_id`, `experiment`, `actual_entry` projected through `RESERVATION_FIELDS`, and `original_reserved_gpu_hours`. The new mask item additionally needs the fields below. Phase/admission fields belong to this mapping, not the canonical RS schema.

```python
MASK_ITEM = dict(
    reservation_id=E['id'], experiment='A3', phase='M1', subphase='masks',
    inventory_sha256=P['inventory_sha256'],
    actual_entry={k: E.get(k) for k in authority.RESERVATION_FIELDS},
    original_reserved_gpu_hours=E['reserved_gpu_hours'],
    reservation_lineage=dict(
        admission_id=A['id'], admission_sha256=A['admission_sha256'],
        max_gpu_hours=A['max_gpu_hours'],
        upper_inventory_sha256=P['inventory_sha256'],
        reserved_gpu_hours=E['reserved_gpu_hours'],
    ),
)
M = dict(
    kind='a3_root_ledger_mapping_v1',
    ledger_path=str(authority.CANONICAL_LEDGER),
    ledger_snapshot_path=str(SNAPSHOT_PATH),
    ledger_sha256=authority.common.file_hash(SNAPSHOT_PATH),
    expected_entry_ids=[row['id'] for row in exact_preserved_snapshot['reservations']],
    entries=all_root_classified_items_including_MASK_ITEM,
    original_admission_paths=[str(A_PATH)],
    original_admission_references={str(A_PATH): authority.object_reference(A_PATH)},
    storage_capacities=CAPACITIES,
    contingency_gpu_hours=6, max_age_seconds=900,
    generation=0, successor_directory=str(SUCCESSORS), refresh_wait_seconds=60,
)
```

The preserved snapshot is the exact post-registration canonical ledger bytes and remains separate from the live ledger. Mapping rows and expected IDs must match both snapshots/current live membership. The initial contingency value applies before any contingency charge; later mappings must preserve the complete original accounting and remaining reserve. Do not attach direction-only envelope fields to this mask initial mapping.

Capacity entries use `{'pool': physical_pool_identity, 'available_bytes': actual_integer_bytes}` for `host_ram`, `cache_disk`, `output_disk` and `scratch_disk`; extra provenance/path fields are accepted. Disk tiers sharing a physical pool must share its pool ID: `_storage_admission` sums their requirements and uses the minimum available capacity for that pool. Root's concrete statvfs-backed projects pool and separately reserved host pool follow this rule. The source's initial authority check consumes host capacity and retained/transient proof memory; the separate full-target `_storage_admission` check is needed to establish the other planning tiers. Native peaks still require the real pilot.

## How verified

Inspected the frozen shared `normalize_ledger`, `validate_reservation`, context, mapping successor, allocation contract, live Slurm and capacity validators, plus mask CLI/guard/receipt construction and accepted fixture schemas. Read root's concrete script/config and completed preflight output without executing the script. Checked current original ledger rows directly: the root output-path heuristic correctly classifies A2 `r-004` through `r-006` and `r-010` through `r-027`; all other existing rows are A1. No differently named historical A2 exists in the inspected ledger. Every original stored charge matches the source's required per-reservation rounding. The ordinary `mapping-successors` sibling directory already exists and is outside the immutable mapping/admission/reservation bundles.

**Freshness is a fresh read, not a timestamp heartbeat.** There is no refreshed timestamp file requirement and no ledger-mtime test. Every `normalize_ledger` call reads canonical live JSON and hashes its current bytes, then sets normalized `snapshot_time=time.time()` and `age_seconds=0`. `max_age_seconds` must be positive and at most the source's allowed bound, but does not require touching a queued ledger. `ledger_sha256` in the immutable mapping binds the preserved original snapshot, not future live reconciliation bytes.

RS status and `actual_seconds` reconciliation can change in the live ledger without changing the mapping or original snapshot. Original ID/job/cluster/account/partition/GPU/minutes/reserved charge/source/output/manifest fields cannot change. A queued job may start later: actual lease start/end/time-limit is independently read at execution, and finish time is rechecked after any mapping wait.

For a newly added RS ID, keep the original mapping path passed by the job. Publish a completed `mapping-000001` successor in the already declared external directory, then subsequent consecutive generations as needed. Each successor carries an exact predecessor object reference, preserves every old entry/charge/admission reference, includes all current RS IDs and points to a newly preserved complete ledger snapshot. Do not overwrite any original evidence or switch an existing process to a different mapping path. Use atomic completed-object publication so the directory never exposes a partially written named successor. The existing bounded refresh waits for RS-add-to-successor publication, stops at the finish-time reserve and checks changed/missing old anchors before waiting.

## Execution evidence

Source/config/preflight/ledger inspection only; no new scheduler or model execution. Evidence is `113-mask-readiness-evidence/launch-constructor-review.json`, bound to the concrete script/config/runtime hashes. Existing root preflight storage requirements and available pools were read and found consistent. This review did not create any actual root admission, reservation, ledger mapping, Slurm job or execution-authorized flag. Prior CPU/tiny readiness evidence remains in report113; no scientific baseline or row result is added here.

## What is NOT done

No root artifact/config/code edits, git, RS writes, scheduler access/submission, GPU/weights, APIs, notebooks or subagents. No hold release or live allocation acceptance. Root must bind the real job/RS identifiers and preserve its exact original source/output/account/partition/resource/duration facts before releasing model execution. Future unknown ledger entries must be explicitly classified rather than silently inheriting the current historical heuristic.

## Open questions

No additional launch-constructor blocker beyond the pending real job/RS bindings, final source/capacity recheck, static authority validation and live lease. Root's static preflight should first call `_live_mask(prepared,args)` without an inventory, then normalize its genuine mapping and call `validate_reservation(..., subphase='masks', inventory_validator=mask_workload.validate_inventory, subphase_limits={'M1':0.75,'M5':10}, require_allocation=False)`. That validates source/binding/caps while explicitly returning no execution authority. Only the real job's normal mask guard may mint a live context and proceed to model loading. The parser-only mask `--dry-run` cannot substitute for that check.
