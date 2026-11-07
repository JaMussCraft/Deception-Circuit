"""Mechanical r7 packaging checks only; never import application/model modules."""
import ast
import hashlib
import json
import os
from pathlib import Path

PACKET = Path(__file__).resolve().parents[1]
SDD = PACKET.parents[1]
OLD = SDD/'plan/task23-green-r6-r2-sharded'
CANDIDATE = SDD/'plan-a3/direction-preallocation-candidate282'
OLD_CANDIDATE = SDD/'plan-a3/direction-preallocation-candidate183'
CORRECTION = SDD/'plan-a3/validation-correction282'
RUNTIME = '1d6c3886a7634641a8a4ad64135adeef34dcdac7ce6b388e8441df1bf2cea116'
SUITE = '2f89de3edb0ac5d513b98c018c6ab1393179b73d9ee67c64d725a064eaa09fb3'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def transformed(text):
    for old, new in [('direction-preallocation-candidate183', 'direction-preallocation-candidate282'),
                     ('task23-green-r6-r2-sharded', 'task23-green-r7-sharded'),
                     ('r6-r2-sharded', 'r7-sharded')]:
        text = text.replace(old, new)
    return ast.dump(ast.parse(text), include_attributes=False)


oldpins = read(OLD/'source-pins.json'); pins = read(PACKET/'source-pins.json')
assert set(pins) == set(oldpins)
assert pins['baseline'] == oldpins['baseline'] and pins['oracle'] == oldpins['oracle']
assert set(pins['candidate']) == set(oldpins['candidate'])
assert set(pins['packet']) == set(oldpins['packet'])
changed_candidate = [name for name in pins['candidate'] if pins['candidate'][name] != oldpins['candidate'][name]]
assert sorted(changed_candidate) == ['component_analysis/a3_direction_runtime.py', 'tests/test_a3_prepared_pilot_target.py']
for name, digest in oldpins['candidate'].items():
    assert sha(OLD_CANDIDATE/name) == digest, 'active candidate changed: '+name
for name, digest in oldpins['packet'].items():
    assert sha(OLD/name) == digest, 'active packet changed: '+name
for group, root in [('candidate', CANDIDATE), ('packet', PACKET),
                    ('baseline', PACKET/'baseline-source'), ('oracle', SDD/'plan-a3/direction-metadata-optionA-candidate')]:
    for name, digest in pins[group].items():
        assert sha(root/name) == digest, (group, name)
assert sha(CANDIDATE/'component_analysis/a3_direction_runtime.py') == RUNTIME
assert sha(CORRECTION/'component_analysis/a3_direction_runtime.py') == RUNTIME
assert sha(CANDIDATE/'tests/test_a3_prepared_pilot_target.py') == SUITE
assert sha(PACKET/'suite/test_a3_prepared_pilot_target.py') == SUITE
assert sha(CORRECTION/'tests/test_a3_prepared_pilot_target.py') == SUITE
workload = 'component_analysis/a3_direction_workload.py'
assert sha(CANDIDATE/workload) == oldpins['candidate'][workload] and oldpins['candidate'][workload].startswith('765b')
mechanical = ['aggregate.py', 'run_packet.py', 'fixture_preflight.py', 'bridges/host.py',
              'bridges/transport229.py', 'test_packet.py']
for name in mechanical:
    assert transformed((OLD/name).read_text()) == ast.dump(ast.parse((PACKET/name).read_text()), include_attributes=False), name
for name in ['selector.py', 'supervisor.py', 'test_review272.py', 'baseline_red.py', 'suite/conftest.py',
             'baseline-suite/conftest.py', 'baseline-suite/test_a3_prepared_pilot_target.py',
             'bridges/inner.py', 'bridges/launch.sh']:
    assert (OLD/name).read_bytes() == (PACKET/name).read_bytes(), name
for name in ['supervisor.py', 'bridges/host.py', 'bridges/transport229.py', 'bridges/inner.py']:
    ast.parse((PACKET/name).read_text(), feature_version=(3, 6))
partition = read(PACKET/'partition.json'); before = read(OLD/'partition.json')
assert partition['revision'] == 'r7-sharded'
before['revision'] = 'r7-sharded'; assert partition == before
assert len(partition['full_collection']) == 223
assert [len(partition['shards'][str(i)]['members']) for i in (0, 1)] == [112, 111]
for old, new, allowed in [(OLD_CANDIDATE/'component_analysis/a3_direction_runtime.py', CANDIDATE/'component_analysis/a3_direction_runtime.py', '_completed_pilot_source'),
                           (OLD/'suite/test_a3_prepared_pilot_target.py', PACKET/'suite/test_a3_prepared_pilot_target.py', 'test_prepared_costs_and_envelope_are_charged')]:
    a = ast.parse(old.read_text()); b = ast.parse(new.read_text())
    dump = lambda n: ast.dump(n, include_attributes=False)
    assert len(a.body) == len(b.body)
    assert [getattr(x, 'name', None) for x, y in zip(a.body, b.body) if dump(x) != dump(y)] == [allowed]
    assert [dump(n) for n in ast.walk(a) if isinstance(n, ast.Assert)] == [dump(n) for n in ast.walk(b) if isinstance(n, ast.Assert)]
    decorators = lambda tree: [(n.name, [dump(x) for x in n.decorator_list]) for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    assert decorators(a) == decorators(b)
inventory = read(PACKET/'transport-inventory.json'); old_inventory = read(OLD/'transport-inventory.json')
assert len(inventory['files']) == len(old_inventory['files'])
assert len(inventory['aliases']) == len(old_inventory['aliases']) == 8
for row in inventory['files']:
    path = Path(row['virtual']); assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
for row, prior in zip(inventory['aliases'], old_inventory['aliases']):
    path = Path(row['virtual']); assert path.is_symlink() and os.readlink(path) == row['literal_target'] == prior['literal_target']
    expected = str(CANDIDATE/Path(prior['virtual']).relative_to(OLD_CANDIDATE)) if Path(prior['virtual']).is_relative_to(OLD_CANDIDATE) else prior['virtual']
    assert row['virtual'] == expected
config = read(PACKET/'bridges/config.template.json')
assert config['status'] == 'UNBOUND_NOT_RUNNABLE'
assert config['files'] == [dict(row, physical=None) for row in inventory['files']]
assert config['aliases'] == [dict(row, physical=None) for row in inventory['aliases']]
assert config['expected_file_count'] == len(inventory['files'])
assert all(config[key] is None for key in ['environment', 'shard', 'job_id', 'cluster', 'cpus', 'account', 'partition', 'qos', 'output', 'physical_root'])
control = read(PACKET/'control-staging.json')
assert len(control['additional_required_controls']) == 1
ref = control['additional_required_controls'][0]
assert ref == dict(virtual=str(PACKET/'transport-inventory.json'), sha256=sha(PACKET/'transport-inventory.json'), bytes=(PACKET/'transport-inventory.json').stat().st_size)
assert ref['virtual'] not in {row['virtual'] for row in inventory['files']}
assert control['self_hash_cycle'] is False
print(json.dumps(dict(status='MECHANICAL_UNBOUND_PACKAGING_CHECKS_PASS',
    scope='static/hash/AST only; no native imports, collection or execution',
    candidate_declared_files=len(pins['candidate']), candidate_changed_files=changed_candidate,
    declared_inventory_files=len(inventory['files']), declared_aliases=len(inventory['aliases']),
    separately_staged_controls=control['additional_required_controls'], full_collection=223,
    shard_counts=[112,111], workload_sha256=oldpins['candidate'][workload], runtime_sha256=RUNTIME,
    candidate_and_suite_sha256=SUITE, old_active_sources_unchanged=True,
    host_selector_supervisor_aggregate_logic_unchanged=True, native_acceptance=False,
    actual_jobs=None, actual_configs=None, source_publication=None, execution_authorized=False), indent=2))
