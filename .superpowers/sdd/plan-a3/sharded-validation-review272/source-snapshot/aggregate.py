"""Pure fail-closed evidence verifier. Root authenticates bindings independently."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ENVS = {'base': '/sw/external/python/anaconda3/bin/python3.9',
        'mgnp': '/u/swong2/.conda/envs/mgnp/bin/python'}
BASELINE_COUNTS = {
    'test_prepared_anchored_cgroup_scope_mismatch_rejects_before_loader': 2,
    'test_prepared_anchored_cold_warm_cgroup_scope_disagreement_rejects': 1,
    'test_prepared_completed_intake_rejects_anchored_cgroup_scope_mismatch': 2}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def validate_partition(p):
    nodes = p['full_collection']
    require(len(nodes) == len(set(nodes)) == 223, 'original collection must be unique 223')
    require(dict(Counter(n.split('::')[1].split('[')[0] for n in nodes)) == p['per_function_counts'], 'parameter multiplicities')
    require(set(p['shards']) == {'0', '1'}, 'two shards required')
    for i in (0, 1):
        row = p['shards'][str(i)]
        require(row['members'] == nodes[i::2], 'original ordinal parity')
        ordered = sorted(row['members'], key=lambda n: n.split('::')[1].split('[')[0] not in p['repaired_families'])
        require(row['execution_order'] == ordered, 'repaired-family-first original order')

def read_ref(ref, root=None, raw=False):
    path = Path(ref['path'])
    require(path.is_absolute() and not path.is_symlink() and path.resolve() == path, 'noncanonical evidence path')
    if root is not None:
        require(path.is_relative_to(Path(root)), 'artifact escaped bound output')
    require(digest(path) == ref['sha256'], 'evidence hash changed: ' + str(path))
    return path.read_text() if raw else json.loads(path.read_text())

def verify_events(events, nodes, collected, python):
    require(events and events[0]['event'] == 'start' and events[-1]['event'] == 'finished', 'normal event boundaries')
    require(events[0]['collected'] == collected and events[0]['requested'] == nodes, 'event collection or selection')
    require(events[0]['python'] == events[0]['executable'] == python, 'event interpreter identity')
    require(events[-1]['requested_count'] == len(nodes), 'finished item count')
    expected = []
    for node in nodes:
        expected.append(('item-start', node, None))
        expected.extend(('phase-report', node, phase) for phase in ('setup', 'call', 'teardown'))
        expected.append(('item-finish', node, None))
    require([(e['event'], e.get('nodeid'), e.get('when')) for e in events[1:-1]] == expected, 'missing, extra or reordered item phases')
    require(all(e['outcome'] == 'passed' for e in events if e['event'] == 'phase-report'), 'failed/error/skipped phase')

def verify_junit(text, nodes):
    cases = ET.fromstring(text).findall('.//testcase')
    # Single-module filenames are part of this frozen suite. Parameter strings
    # remain verbatim: compare XML identities, never a count of function names.
    actual = [c.attrib['classname'] + '.py::' + c.attrib['name'] for c in cases]
    require(actual == nodes, 'JUnit exact identities/order')
    require(all(c.find(k) is None for c in cases for k in ('failure', 'error', 'skipped')), 'JUnit failure/error/skip')

def verify_controls(artifacts, output):
    baseline = read_ref(artifacts['baseline'], output)
    require(baseline['status'] == 'CORRECTION_RED_EXPECTED' and baseline['normal_completion'] is True and baseline['exit_code'] == 0,
            'baseline normal completion')
    require(baseline['pytest_exit_code'] == 1 and baseline['observed_cases'] == baseline['expected_cases'] == baseline['failures'] == 5
            and baseline['errors'] == baseline['skipped'] == 0 and baseline['per_function_case_counts'] == BASELINE_COUNTS,
            'original named five-failure baseline')
    oracle = read_ref(artifacts['oracle'], output)
    require(oracle['complete'] is True and oracle['exit_code'] == 0 and oracle['model_loaded'] is False and oracle['execution_authorized'] is False, 'oracle proof')
    fixture = read_ref(artifacts['preflight'], output)
    require(fixture['status'] == 'FIXTURE_PREFLIGHT_COMPLETE' and fixture['normal_completion'] is True and fixture['exit_code'] == 0
            and fixture['source_pins_before_after_equal'] is True, 'original fixture preflight')

def verify_shards(records, expected_partition, expected_source, expected_bindings):
    """Refs and expected_bindings must come from root, never constructed from children.

    Each binding keys exact interpreter then shard; includes authenticated terminal
    manifest/config/host/accounting refs plus actual job, cluster and output.
    Root must authenticate the complete map before calling this pure function.
    """
    validate_partition(expected_partition)
    require(expected_source['revision'] == 'r6-sharded', 'wrong packet revision')
    observed = {}; jobs = set(); outputs = set()
    for ref in records:
        m = read_ref(ref)
        env = m['environment']; py = ENVS[env]; shard = str(m['shard']); key = (env, shard)
        require(key not in observed and shard in ('0', '1'), 'duplicate shard')
        bound = expected_bindings[py][shard]
        require(ref == bound['manifest'], 'manifest not independently bound')
        require(all(bound[k] is not None for k in ('job_id', 'cluster', 'output', 'manifest', 'config', 'host', 'accounting')), 'unbound deployment')
        require(m['job_id'] == bound['job_id'] and m['cluster'] == bound['cluster'] and m['output'] == bound['output'], 'actual binding mismatch')
        require((bound['cluster'], bound['job_id']) not in jobs and bound['output'] not in outputs, 'reused job/output')
        jobs.add((bound['cluster'], bound['job_id'])); outputs.add(bound['output'])
        require(bound['cluster'] == ('delta' if env == 'base' else 'bridges2'), 'native environment cluster')
        require(m['python'] == m['executable'] == py, 'exact interpreter')
        require(m['status'] == 'SHARD_GREEN' and m['full_suite_accepted'] is False and m['execution_authorized'] is False
                and m['model_loaded'] is False and m['normal_completion'] is True and m['exit_code'] == 0, 'normal nonauthorizing shard')
        require(m['source_before'] == m['source_after'] == expected_source, 'source/fixture/partition identity changed')
        require(m['child_exit_code'] == 0 and m['child_normal_completion'] is True
                and m['child_started'] < m['child_finished'] < m['child_deadline'], 'late/nonzero/incomplete child')
        nodes = expected_partition['shards'][shard]['execution_order']
        require(m['collected'] == expected_partition['full_collection'] and m['executed'] == nodes, 'whole collection/executed identity')
        artifacts = m['artifacts']; output = bound['output']
        events = [json.loads(line) for line in read_ref(artifacts['events'], output, raw=True).splitlines()]
        verify_events(events, nodes, expected_partition['full_collection'], py)
        verify_junit(read_ref(artifacts['junit'], output, raw=True), nodes)
        verify_controls(artifacts, output)
        config = read_ref(bound['config']); host = read_ref(bound['host']); accounting = read_ref(bound['accounting'])
        for value in (config, host, accounting):
            require(value['job_id'] == bound['job_id'] and value['cluster'] == bound['cluster'], 'host/config/accounting binding')
        require(config['environment'] == env and config['shard'] == int(shard) and config['cpus'] == (2 if env == 'base' else 18)
                and config['memory_gib'] == 32 and config['allocation_seconds'] == 4800, 'actual resource tuple')
        require(host['status'] == 'HOST_COMPLETE' and host['normal_completion'] is True and host['exit_code'] == 0
                and host['output'] == output and host['source_checks_complete'] is True and host['allocation_checks_complete'] is True
                and host['config_sha256'] == bound['config']['sha256'], 'normal host completion')
        require(set(host['stages']) == {'baseline', 'oracle', 'suite'}, 'all actual stage terminals')
        for stage, terminal_ref in host['stages'].items():
            terminal = read_ref(terminal_ref, Path(bound['host']['path']).parent)
            require(terminal['normal_completion'] is True and terminal['exit_code'] == 0
                    and terminal['started'] < terminal['finished'] < terminal['deadline']
                    and not terminal.get('error') and not terminal.get('cleanup_error'), 'actual stage failed/late')
            if stage == 'suite':
                require(terminal['started'] <= m['child_started'] < m['child_finished'] <= terminal['finished']
                        and m['child_deadline'] <= terminal['deadline'], 'child outside actual host bounds')
        require(accounting['state'] == 'COMPLETED' and accounting['exit_code'] == '0:0' and accounting['gpus'] == 0, 'terminal accounting')
        observed[key] = nodes
    complete = []
    for env in ENVS:
        if all((env, shard) in observed for shard in ('0', '1')):
            union = observed[(env, '0')] + observed[(env, '1')]
            require(len(union) == len(set(union)) == 223 and set(union) == set(expected_partition['full_collection']), 'exact disjoint union')
            require(dict(Counter(n.split('::')[1].split('[')[0] for n in union)) == expected_partition['per_function_counts'], 'whole parameter multiplicities')
            complete.append(env)
    return dict(full_suite_accepted=complete == ['base', 'mgnp'], complete_environments=complete,
        status='COMPLETE_VALIDATION_METADATA' if len(complete) == 2 else 'PARTIAL_VALIDATION_METADATA',
        execution_authorized=False, model_loaded=False, shard_count=len(observed))
