"""Read-only conditional CPU continuation gate; no model or proof construction."""
from pathlib import Path
import hashlib
import json
import subprocess
import time


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    return json.loads(Path(path).read_text())


def check_parent(worktree, scenario, expected, accounting, current_references):
    """Consume the original coordinator's existing byte-reference map once."""
    worktree, scenario = Path(worktree).resolve(), Path(scenario).resolve()
    job = expected['parent_job_id']
    rows = [line.split('|') for line in accounting.splitlines() if line.strip()]
    relevant = [row for row in rows if row[0] == job or row[0].startswith(job + '.')]
    _require(any(row[0] == job for row in relevant), 'parent accounting missing')
    _require(all(len(row) == 3 and row[1:] == ['COMPLETED', '0:0'] for row in relevant),
             'parent and reported steps must be successful COMPLETED 0:0')
    for ref in expected['pinned_files']:
        _require(_sha(ref['path']) == ref['sha256'], 'changed pinned parent/source/scenario input')
    _require({name: _sha(worktree / name) for name in expected['source_hashes']} == expected['source_hashes'],
             'changed frozen source')
    parent = Path(expected['parent_directory']).resolve()
    _require(parent == scenario / 'diagnostics' / ('cpu-next-cases32-48-job' + job),
             'parent scenario path mismatch')
    process, result, identity = [_read(parent / name) for name in
                                ('result.json', 'coordinator-result.json', 'driver-identity.json')]
    _require(process['actual_slurm_job_id'] == job and process['exit_code'] == 0
             and process['term_sent_at'] is None and process['injected_fixture'] is True
             and process['selected_case_start'] == 32 and process['selected_case_count'] == 17
             and process['scientific_execution'] is False and process['production_admission'] is False,
             'parent process incomplete or unsuccessful')
    _require(identity['actual_job_id'] == job and identity['source_hashes'] == expected['source_hashes']
             and identity['catalog_sha256'] == expected['catalog_sha256']
             and identity['driver_sha256'] == expected['parent_driver_sha256']
             and identity['start'] == 32 and identity['count'] == 17
             and identity['scientific_execution'] is False and identity['execution_authorized'] is False,
             'parent source/catalogue identity mismatch')
    ids = expected['case_ids'][32:49]
    _require(result['actual_job_id'] == job and result['actual_step_id'] == '0'
             and result['indices'] == list(range(32, 49)) and result['new_case_ids'] == ids
             and result['new_native_case_count'] == 17
             and result['preserved_case_ids'] == expected['case_ids'][:32]
             and result['preserved_case_references_unchanged'] is True,
             'parent case inventory/order/preservation mismatch')
    _require(all(result[name] is False for name in
                 ('full_pilot_complete', 'aggregate_executed', 'scientific_execution', 'execution_authorized'))
             and result['forbidden_auth_model_forwards'] == 0, 'parent authority/control mismatch')
    for name in ('native', 'authentication', 'original_case_records'):
        _require([row['case_id'] for row in result[name]] == ids, 'parent evidence coverage/order mismatch')
    _require(all(type(row['actual_forward_calls']) is int and row['actual_forward_calls'] > 0
                 for row in result['native']), 'parent forward observations missing')
    _require(sum(row['actual_forward_calls'] for row in result['native']) == result['actual_new_forward_calls']
             == sum(row['original_case_forward_calls'] for row in result['original_case_records']),
             'parent forward counts do not reconcile')
    allocation_ref = result['slurm_allocation_reference']
    _require(Path(allocation_ref['path']).resolve() == parent / 'coordinator-allocation.json'
             and _sha(allocation_ref['path']) == allocation_ref['sha256'], 'changed parent allocation')
    allocation = _read(allocation_ref['path'])
    _require(allocation['job_id'] == job and allocation['actual_GPU_count'] == 0
             and allocation['allocation_memory_bytes'] == 34359738368, 'parent allocation mismatch')
    observed = []
    for native, auth, original in zip(result['native'], result['authentication'], result['original_case_records']):
        case = native['case_id']
        _require(auth['new_model_forwards'] == 0 and native['actual_forward_calls'] == original['original_case_forward_calls'],
                 'parent per-case control/count mismatch')
        ref = current_references[case]
        _require(Path(ref['path']).resolve() == scenario / 'pilot-verification-cases/selected' / case
                 and {'COMPLETE.json', 'case.json'}.issubset(ref['files']) and ref == original['reference'],
                 'changed or partial parent case bytes')
        side_path = parent / ('slurm-case-' + case + '.json')
        side = _read(side_path)
        _require(side['actual_job_id'] == job and side['actual_step_id'] == '0'
                 and side['host'] == allocation['host'] and side['allocation_reference'] == allocation_ref
                 and side['case_reference'] == ref and side['native'] == native and side['authentication'] == auth
                 and side['scientific_execution'] is False and side['production_admission'] is False,
                 'changed parent case allocation sidecar')
        observed.append(dict(path=str(side_path), sha256=_sha(side_path)))
    return dict(parent_job_id=job, authenticated_parent_case_ids=ids, new_model_forwards=0,
                parent_only_not_whole_pilot=True, reused_existing_original_case_reference_scan=True,
                metadata_references=[dict(path=str(parent/name), sha256=_sha(parent/name)) for name in
                                     ('result.json', 'coordinator-result.json', 'driver-identity.json')],
                sidecar_references=observed, accounting_raw=accounting)


def require_parent(worktree, scenario, expected, current_references, *, runner=subprocess.run,
                   clock=time.monotonic, sleeper=time.sleep, maximum_wait_seconds=30):
    """Allow bounded accounting propagation after afterok; never retry failed jobs."""
    job = expected['parent_job_id']
    command = ['sacct', '-n', '-P', '-j', job, '--format=JobIDRaw,State,ExitCode']
    start, observations = clock(), []
    while True:
        remaining = maximum_wait_seconds - (clock() - start)
        _require(remaining > 0, 'parent accounting propagation deadline exceeded')
        proc = runner(command, capture_output=True, text=True, check=False, timeout=min(10, remaining))
        elapsed = clock() - start
        observations.append(dict(elapsed_seconds=elapsed, returncode=proc.returncode,
                                 stdout=proc.stdout, stderr=proc.stderr))
        rows = [line.split('|') for line in proc.stdout.splitlines() if line.strip()]
        relevant = [row for row in rows if row[0] == job or row[0].startswith(job + '.')]
        _require(not any(len(row) == 3 and row[1] not in ('PENDING', 'RUNNING', 'COMPLETING', 'COMPLETED') for row in relevant),
                 'parent must be successful COMPLETED; terminal failure is not retried')
        pending = not any(row[0] == job for row in relevant) or any(
            len(row) == 3 and row[1] in ('PENDING', 'RUNNING', 'COMPLETING') for row in relevant)
        if proc.returncode == 0 and not pending:
            result = check_parent(worktree, scenario, expected, proc.stdout, current_references)
            result.update(accounting_observations=observations, gate_seconds=clock()-start)
            return result
        _require(elapsed < maximum_wait_seconds, 'parent accounting propagation deadline exceeded')
        sleeper(min(2, maximum_wait_seconds-elapsed))
