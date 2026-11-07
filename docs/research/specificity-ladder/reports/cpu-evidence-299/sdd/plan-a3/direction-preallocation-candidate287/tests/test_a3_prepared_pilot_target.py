"""Private prepared transport contracts; artifacts are data, never admission.

Each test names the break it catches. Missing helpers are resolved inside test
bodies, outside expected-rejection contexts, so RED is attributable to transport.
"""
import builtins
import copy
from types import SimpleNamespace
import time
from tests.test_a3_direction_runner import fake
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil

import pytest


def runtime():
    from component_analysis import a3_direction_runtime
    return a3_direction_runtime


def object_case(tmp_path, payload=None, *, work_dir=None, aliases=()):
    r = runtime()
    work = work_dir or tmp_path / 'work'
    target = work / 'pilot-target-inventory' / 'prefit'
    preparation = work / 'pilot-target-preparation' / 'prefit'
    payload = {'expected_keys': [['far_v2', 42]], 'ratio': -0.0, 'text': 'λ雪'} if payload is None else payload
    r.publish_object(target, payload)
    target_ref = r.object_reference(target)
    r.publish_object(preparation, dict(kind='a3_pilot_target_preparation_v1',
        part='prefit', target_reference=target_ref, model_loaded=False,
        execution_authorized=False))
    policy = dict(work_dir=str(work.absolute()), target_root=str(target.absolute()),
        preparation_root=str(preparation.absolute()), allowed_aliases=tuple(aliases),
        expected_resolved=dict(work_dir=str(work.resolve()), target_root=str(target.resolve()),
            preparation_root=str(preparation.resolve())))
    return target, preparation, target_ref, r.object_reference(preparation), policy


def resign(path):
    (path / 'COMPLETE.json').unlink(missing_ok=True)
    runtime().artifacts._finish(path)


def bind_preparation_target(preparation, target_ref):
    r = runtime(); value = r.read_object(preparation)
    value['target_reference'] = target_ref
    (preparation / 'payload.json').write_text(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
    resign(preparation)
    return r.object_reference(preparation)


def unpack(result):
    assert type(result) is tuple and len(result) == 6
    value, refs, namespace, witness, observed_io, resources = result
    assert set(refs) == {'target', 'preparation'}
    assert type(namespace) is tuple
    assert type(witness) is runtime()._FileWitness
    assert resources['retained_metadata_bytes'] > 0
    assert resources['extra_transient_bytes'] >= refs['target']['files']['payload.json']['nbytes']
    assert resources['recipe'] and resources['scope']
    return value, refs, namespace, witness, observed_io, resources


@pytest.mark.parametrize('payload,expected', [
    ({'z': 1.25, 'a': -0.0}, b'{"a": -0.0, "z": 1.25}\n'),
    ({'text': 'λ雪'}, b'{"text": "\\u03bb\\u96ea"}\n'),
    ({'rows': (True, None, 7)}, b'{"rows": [true, null, 7]}\n'),
    ({'nested': [{'a': 1}]}, b'{"nested": [{"a": 1}]}\n'),
    (['plain', 2.0], b'["plain", 2.0]\n'),
])
def test_prepared_writer_matches_untouched_publisher(tmp_path, payload, expected):
    r = runtime(); publish = r._publish_prepared_target_object
    ordinary = tmp_path / 'ordinary'; actual = tmp_path / 'prepared'
    r.publish_object(ordinary, payload)
    emitted = publish(actual, payload)
    assert (ordinary / 'payload.json').read_bytes() == expected
    assert (actual / 'payload.json').read_bytes() == expected
    assert (actual / 'COMPLETE.json').read_bytes() == (ordinary / 'COMPLETE.json').read_bytes()
    reference = r.object_reference(actual)
    assert emitted == dict(reference=reference, emitted_payload_sha256=hashlib.sha256(expected).hexdigest(),
        emitted_payload_bytes=len(expected))
    assert {k: v for k, v in reference.items() if k != 'path'} == {
        k: v for k, v in r.object_reference(ordinary).items() if k != 'path'}


def test_prepared_writer_accepts_existing_frozen_json(tmp_path):
    r = runtime(); publish = r._publish_prepared_target_object
    value = r._freeze_json({'rows': ({'x': -0.0},), 'unicode': 'é'})
    emitted = publish(tmp_path / 'frozen', value)
    expected = b'{"rows": [{"x": -0.0}], "unicode": "\\u00e9"}\n'
    assert (tmp_path / 'frozen' / 'payload.json').read_bytes() == expected
    assert emitted['emitted_payload_sha256'] == hashlib.sha256(expected).hexdigest()


@pytest.mark.parametrize('value', [float('nan'), float('inf'), float('-inf')])
def test_prepared_writer_nonfinite_never_completes(tmp_path, value):
    r = runtime(); publish = r._publish_prepared_target_object
    with pytest.raises(ValueError):
        publish(tmp_path / 'rejected', {'x': value})
    assert not (tmp_path / 'rejected').exists()


@pytest.mark.parametrize('seam', ['finish', 'reference'])
def test_prepared_writer_rejects_resigned_postwrite_value(tmp_path, monkeypatch, seam):
    r = runtime(); publish = r._publish_prepared_target_object
    original = r.artifacts._finish if seam == 'finish' else r.object_reference
    def changed(root):
        if seam == 'finish':
            out = original(root)
            (Path(root) / 'payload.json').write_bytes(b'{"x": 2}\n')
            (Path(root) / 'COMPLETE.json').unlink()
            original(root)
            return out
        (Path(root) / 'payload.json').write_bytes(b'{"x": 2}\n')
        resign(Path(root))
        return original(root)
    monkeypatch.setattr(r.artifacts if seam == 'finish' else r,
        '_finish' if seam == 'finish' else 'object_reference', changed)
    with pytest.raises(ValueError):
        publish(tmp_path / 'raced', {'x': 1})


def test_prepared_same_buffer_and_marker_contract(tmp_path):
    r = runtime(); read = r._read_prepared_target_object
    target, preparation, tr, pr, policy = object_case(tmp_path)
    ordinary = r.read_object(target)
    frozen, refs, namespace, witness, observed, resources = unpack(read(tr, pr, policy))
    assert frozen == ordinary
    assert math.copysign(1, frozen['ratio']) == -1
    assert refs == {'target': tr, 'preparation': pr}
    assert namespace == r._prepared_namespace_identity(policy['work_dir'], policy['target_root'],
        policy['preparation_root'], policy['allowed_aliases'])
    assert witness.paths == (str(target.resolve()), str(preparation.resolve()))
    assert not hasattr(frozen, 'assert_scope')
    with pytest.raises(TypeError): frozen['text'] = 'changed'
    with pytest.raises(TypeError): frozen['expected_keys'][0].append(5)
    with pytest.raises(TypeError): refs['target']['files']['payload.json']['sha256'] = '0' * 64
    r._check_file_witness(witness)


@pytest.mark.parametrize('artifact', ['target', 'preparation'])
@pytest.mark.parametrize('damage', ['missing-child', 'extra-file', 'extra-directory', 'payload-link',
    'marker-link', 'root-link', 'bad-marker-kind', 'bad-marker-schema', 'bad-marker-hash',
    'bad-payload-hash', 'nonfinite', 'wrong-ref-hash', 'wrong-ref-size'])
def test_prepared_reader_rejects_exact_child_marker_and_reference_damage(tmp_path, damage, artifact):
    r = runtime(); read = r._read_prepared_target_object
    target, preparation, tr, pr, policy = object_case(tmp_path)
    if artifact == 'preparation': target = preparation
    selected_ref = tr if artifact == 'target' else pr
    if damage == 'missing-child': (target / 'payload.json').unlink()
    elif damage == 'extra-file':
        (target / 'unexpected').write_text('extra'); resign(target)
    elif damage == 'extra-directory': (target / 'unexpected').mkdir()
    elif damage in ('payload-link', 'marker-link'):
        leaf = target / ('payload.json' if damage == 'payload-link' else 'COMPLETE.json')
        external = tmp_path / 'external'; leaf.rename(external); leaf.symlink_to(external)
    elif damage == 'root-link':
        backing = tmp_path / 'target-backing'; target.rename(backing); target.symlink_to(backing, target_is_directory=True)
    elif damage.startswith('bad-marker'):
        marker = json.loads((target / 'COMPLETE.json').read_bytes())
        if damage == 'bad-marker-kind': marker['kind'] = 'other'
        elif damage == 'bad-marker-schema': marker['schema_version'] = 2
        else: marker['files']['payload.json']['sha256'] = '0' * 64
        (target / 'COMPLETE.json').write_text(json.dumps(marker))
    elif damage == 'bad-payload-hash': (target / 'payload.json').write_bytes(b'{}\n')
    elif damage == 'nonfinite':
        (target / 'payload.json').write_bytes(b'{"x": NaN}\n'); resign(target)
        if artifact == 'target':
            tr = r.object_reference(target); pr = bind_preparation_target(preparation, tr)
        else: pr = r.object_reference(target)
    elif damage == 'wrong-ref-hash': selected_ref['files']['payload.json']['sha256'] = '0' * 64
    elif damage == 'wrong-ref-size': selected_ref['files']['payload.json']['nbytes'] += 1
    with pytest.raises(ValueError): read(tr, pr, policy)


def test_prepared_reader_keeps_existing_json_semantics(tmp_path):
    r = runtime(); read = r._read_prepared_target_object
    target, preparation, tr, pr, policy = object_case(tmp_path)
    # Existing parser permits duplicate keys and arbitrary finite primitive data.
    # Do not accidentally impose an unreviewed stricter schema in private transport.
    (target / 'payload.json').write_bytes(b'{"x": 1, "x": 2, "unicode": "\\u03bb"}\n')
    resign(target); tr = r.object_reference(target); pr = bind_preparation_target(preparation, tr)
    value = unpack(read(tr, pr, policy))[0]
    assert value == r.read_object(target) == {'x': 2, 'unicode': 'λ'}


def test_prepared_reader_rejects_resigned_change_during_parse(tmp_path, monkeypatch):
    r = runtime(); read = r._read_prepared_target_object
    target, preparation, tr, pr, policy = object_case(tmp_path)
    raw = (target / 'payload.json').read_bytes(); original = json.loads
    def raced(data, *args, **kwargs):
        out = original(data, *args, **kwargs)
        if data == raw or data == raw.decode():
            leaf = target / 'payload.json'; st = leaf.stat()
            leaf.write_bytes(b'{"changed": true}\n'); resign(target)
            leaf.write_bytes(raw); os.utime(leaf, ns=(st.st_atime_ns, st.st_mtime_ns)); resign(target)
        return out
    monkeypatch.setattr(json, 'loads', raced)
    with pytest.raises(ValueError): read(tr, pr, policy)


def test_prepared_reader_declared_io_matches_actual(tmp_path, monkeypatch):
    r = runtime(); read = r._read_prepared_target_object
    target, preparation, tr, pr, policy = object_case(tmp_path)
    leaf = (target / 'payload.json').resolve(); raw = leaf.read_bytes()
    counts = dict(reads=0, read_bytes=0, hashes=0, parses=0, freezes=0, writes=0)
    hashed_buffers = []; parsed_buffers = []
    real_io_open = io.open; real_open = builtins.open; real_sha = hashlib.sha256
    real_loads = json.loads; real_freeze = r._freeze_json
    class Stream:
        def __init__(self, stream): self.stream = stream
        def __enter__(self): self.stream.__enter__(); return self
        def __exit__(self, *args): return self.stream.__exit__(*args)
        def __getattr__(self, name): return getattr(self.stream, name)
        def read(self, *args):
            data = self.stream.read(*args)
            if data:
                counts['reads'] += 1; counts['read_bytes'] += len(data.encode() if isinstance(data, str) else data)
            return data
    def observer(opener):
        def opened(file, mode='r', *args, **kwargs):
            stream = opener(file, mode, *args, **kwargs)
            if not isinstance(file, int) and Path(file).resolve() == leaf:
                if any(c in mode for c in 'wax+'): counts['writes'] += 1
                return Stream(stream)
            return stream
        return opened
    class Hash:
        def __init__(self, data=b'', *args, **kwargs):
            self.hash = real_sha(data, *args, **kwargs); self.parts = [data]
        def update(self, data): self.parts.append(data); return self.hash.update(data)
        def __getattr__(self, name): return getattr(self.hash, name)
        def hexdigest(self):
            if b''.join(self.parts) == raw:
                counts['hashes'] += 1; hashed_buffers.extend(self.parts)
            return self.hash.hexdigest()
    def loads(data, *args, **kwargs):
        if data == raw or data == raw.decode(): counts['parses'] += 1; parsed_buffers.append(data)
        return real_loads(data, *args, **kwargs)
    def freeze(value, *args, **kwargs):
        counts['freezes'] += 1
        return real_freeze(value, *args, **kwargs)
    monkeypatch.setattr(io, 'open', observer(real_io_open)); monkeypatch.setattr(builtins, 'open', observer(real_open))
    monkeypatch.setattr(hashlib, 'sha256', Hash); monkeypatch.setattr(json, 'loads', loads)
    monkeypatch.setattr(r, '_freeze_json', freeze)
    result = read(tr, pr, policy)
    assert counts == dict(reads=2, read_bytes=2*len(raw), hashes=2, parses=1, freezes=1, writes=0)
    _, _, _, witness, observed, resources = unpack(result)
    assert observed == dict(full_payload_reads=2, SHA_passes=2, parse_passes=1, freeze_passes=1, target_writes=0)
    assert isinstance(parsed_buffers[0], bytes)
    assert any(buffer is parsed_buffers[0] for buffer in hashed_buffers)
    r._check_file_witness(witness)  # Real final-phase check; never a third startup scan.
    assert counts == dict(reads=3, read_bytes=3*len(raw), hashes=3, parses=1, freezes=1, writes=0)


@pytest.mark.parametrize('scope', ['target', 'preparation', 'target-leaf', 'marker-leaf'])
def test_prepared_namespace_in_phase_identical_replacement_fails(tmp_path, scope):
    r = runtime(); read = r._read_prepared_target_object
    target, preparation, tr, pr, policy = object_case(tmp_path)
    _, _, namespace, witness, _, _ = unpack(read(tr, pr, policy))
    path = preparation if scope == 'preparation' else target
    if scope.endswith('leaf'): path = target / ('payload.json' if scope == 'target-leaf' else 'COMPLETE.json')
    replacement = path.with_name(path.name + '-replacement')
    if path.is_dir(): shutil.copytree(path, replacement); path.rename(path.with_name(path.name + '-old'))
    else: shutil.copy2(path, replacement); path.unlink()
    replacement.rename(path)
    if not scope.endswith('leaf'):
        assert r._prepared_namespace_identity(policy['work_dir'], policy['target_root'],
            policy['preparation_root'], policy['allowed_aliases']) != namespace
    with pytest.raises(ValueError): r._check_file_witness(witness)


def test_prepared_namespace_preentry_replacement_and_sibling_creation_allowed(tmp_path):
    r = runtime(); read = r._read_prepared_target_object
    target, preparation, tr, pr, policy = object_case(tmp_path)
    replacement = tmp_path / 'identical'; shutil.copytree(target, replacement)
    target.rename(tmp_path / 'old'); replacement.rename(target)
    _, _, namespace, witness, _, _ = unpack(read(tr, pr, policy))
    (Path(policy['work_dir']) / 'independent-output').mkdir()
    (target.parent / 'selected').mkdir()
    assert namespace == r._prepared_namespace_identity(policy['work_dir'], policy['target_root'],
        policy['preparation_root'], policy['allowed_aliases'])
    r._check_file_witness(witness)


@pytest.mark.parametrize('damage', ['unlisted', 'wrong-literal', 'retarget', 'wrong-resolved', 'relative-root', 'noncanonical-root'])
def test_prepared_namespace_lifetime_policy(tmp_path, damage):
    r = runtime(); read = r._read_prepared_target_object
    physical = tmp_path / 'physical'; physical.mkdir()
    alias = tmp_path / 'alias'; alias.symlink_to('physical', target_is_directory=True)
    target, preparation, tr, pr, policy = object_case(tmp_path, work_dir=alias / 'work',
        aliases=((str(alias.absolute()), 'physical'),))
    if damage == 'unlisted': policy['allowed_aliases'] = ()
    elif damage == 'wrong-literal': policy['allowed_aliases'] = ((str(alias.absolute()), './physical'),)
    elif damage == 'retarget':
        shutil.copytree(physical, tmp_path / 'other'); alias.unlink(); alias.symlink_to('other', target_is_directory=True)
    elif damage == 'wrong-resolved': policy['expected_resolved']['target_root'] += '-different'
    elif damage == 'relative-root': policy['work_dir'] = 'relative/work'
    elif damage == 'noncanonical-root': policy['target_root'] = str(target.parent) + '/unused/../prefit'
    with pytest.raises(ValueError): read(tr, pr, policy)


def test_prepared_namespace_approved_alias_entry_and_retarget_are_distinct(tmp_path):
    r = runtime(); read = r._read_prepared_target_object
    physical = tmp_path / 'physical'; physical.mkdir()
    alias = tmp_path / 'alias'; alias.symlink_to('physical', target_is_directory=True)
    target, preparation, tr, pr, policy = object_case(tmp_path, work_dir=alias / 'work',
        aliases=((str(alias.absolute()), 'physical'),))
    _, _, namespace, witness, _, _ = unpack(read(tr, pr, policy))
    assert witness.paths == (str(target.resolve()), str(preparation.resolve()))
    shutil.copytree(physical, tmp_path / 'other'); alias.unlink(); alias.symlink_to('other', target_is_directory=True)
    with pytest.raises(ValueError):
        r._prepared_namespace_identity(policy['work_dir'], policy['target_root'],
            policy['preparation_root'], policy['allowed_aliases'])


def test_prepared_native_prefit_inventory_seam_without_model(tmp_path, monkeypatch):
    r = runtime(); read = r._read_prepared_target_object
    from tests.a3_direction_native_scenario import inventory
    from tests.test_a3_direction_runtime import _real_injected_design
    # Use the unchanged native builder/publisher seam, never tiny_model/scenario_init.
    design, protocol = _real_injected_design()
    native = tmp_path / 'native'; native.mkdir()
    value = inventory(native, design, protocol, 'prefit')
    target, preparation, tr, pr, policy = object_case(tmp_path, payload=value)
    frozen, _, _, witness, _, _ = unpack(read(tr, pr, policy))
    native_target = native / 'inventory' / 'prefit'
    # Native tuples become JSON arrays in the unchanged ordinary publisher.
    assert frozen == r.read_object(target) == r.read_object(native_target)
    assert r.workload.digest(frozen) == r.workload.digest(value)
    assert (target / 'payload.json').read_bytes() == (native_target / 'payload.json').read_bytes()
    assert frozen['inventory_sha256'] == value['inventory_sha256']
    assert len(frozen['expected_keys']) == len(value['expected_keys']) > 0
    r._check_file_witness(witness)


def test_prepared_namespace_scopes_directory_identity_without_sibling_mtime(tmp_path):
    r = runtime(); identity = r._prepared_namespace_identity
    target, preparation, tr, pr, policy = object_case(tmp_path)
    before = identity(policy['work_dir'], policy['target_root'], policy['preparation_root'], ())
    assert type(before) is tuple
    (Path(policy['work_dir']) / 'independent').mkdir()
    assert identity(policy['work_dir'], policy['target_root'], policy['preparation_root'], ()) == before


# T2/T3 integration tests. New interfaces are resolved inside bodies before any
# expensive fixture is built; fixture code never supplies execution permission.
def integration_case(tmp_path, monkeypatch, **kwargs):
    from tests.a3_prepared_integration_cases import PreparedCase
    return PreparedCase(tmp_path / 'prepared-case', monkeypatch, **kwargs)


def reanchor_resource(case, update):
    from tests.a3_prepared_integration_cases import rewrite_object
    record = case.r.read_object(case.resource_path); update(record)
    rewrite_object(case.resource_path, record)
    binding = dict(case.preparation_binding,
        receiver_resources_reference=case.r.object_reference(case.resource_path))
    case._bind_original_authority(binding)
    case.resource_record = record


@pytest.mark.parametrize('part,stage', [('prefit', 'fit-select'), ('selected', 'remaining')])
def test_prepared_cpu_producer_uses_exact_builder_contract(tmp_path, monkeypatch, part, stage):
    r = runtime(); producer = r.prepare_pilot_target
    c = integration_case(tmp_path, monkeypatch, part=part, selected=(part == 'selected'))
    original_builder = r.workload.build_inventory; original_validator = r.workload._validate_inventory
    builds = []; validations = []; guards = []; original_guard = r.live_guard
    def build(design, protocol, *, stage, fits=None, selected=None):
        builds.append((stage, fits, selected))
        return original_builder(design, protocol, stage=stage, fits=fits, selected=selected)
    def validate(value):
        validations.append(value['stage']); return original_validator(value)
    def guard(*args, **kwargs):
        guards.append(len(builds)); return original_guard(*args, **kwargs)
    monkeypatch.setattr(r.workload, 'build_inventory', build)
    monkeypatch.setattr(r.workload, '_validate_inventory', validate)
    monkeypatch.setattr(r, 'live_guard', guard)
    prepare_args = copy.copy(c.args); prepare_args.stage = 'prepare'; prepare_args.action = 'pilot-target'
    r.validate_arguments(prepare_args)
    reference = producer(prepare_args, c.design, c.protocol, selected=c.selected)
    descriptor = r.read_object(reference['path'])
    # Independent validator reconstruction may invoke the same original builder;
    # each full-target invocation must retain the exact original inputs.
    target_builds = [row for row in builds if row[0] == stage]
    assert target_builds and all(row == (stage, None, c.selected) for row in target_builds)
    assert stage in validations and c.pilot_inventory['stage'] in validations
    assert len(guards) >= 2 and guards[0] == 0 and guards[-1] >= len(target_builds)
    assert descriptor['part'] == part and descriptor['target_stage'] == stage
    assert descriptor['target_reference'] == r.object_reference(c.target_path)
    raw = (c.target_path / 'payload.json').read_bytes()
    assert descriptor['emitted_payload_sha256'] == hashlib.sha256(raw).hexdigest()
    assert descriptor['emitted_payload_bytes'] == len(raw)
    assert descriptor['model_loaded'] is False and descriptor['execution_authorized'] is False
    assert c.loader_calls == []
    if part == 'selected':
        assert descriptor['selected_reference'] == r.pipeline._bundle_byte_reference(c.args.selected)


@pytest.mark.parametrize('failure', ['partial-target', 'source-change', 'post-guard', 'wrong-summary', 'missing-selected-backing'])
def test_prepared_cpu_failure_never_certifies(tmp_path, monkeypatch, failure):
    r = runtime(); producer = r.prepare_pilot_target
    c = integration_case(tmp_path, monkeypatch)
    original_guard = r.live_guard; original_publish = r._publish_prepared_target_object
    calls = []
    if failure in ('source-change', 'post-guard'):
        def guard(*args, **kwargs):
            calls.append(1)
            if len(calls) > 1:
                if failure == 'source-change': c.source_path.write_text('changed source\n')
                else: raise ValueError('injected final source guard failure')
            return original_guard(*args, **kwargs)
        monkeypatch.setattr(r, 'live_guard', guard)
    elif failure == 'partial-target':
        def partial(path, value):
            Path(path).mkdir(parents=True); (Path(path) / 'payload.json').write_text('{}\n')
            raise ValueError('partial target publication')
        monkeypatch.setattr(r, '_publish_prepared_target_object', partial)
    elif failure == 'wrong-summary':
        original_builder = r.workload.build_inventory
        def damaged(design, protocol, **kwargs):
            value = original_builder(design, protocol, **kwargs)
            if kwargs['stage'] == 'fit-select': value['inventory_sha256'] = '0' * 64
            return value
        monkeypatch.setattr(r.workload, 'build_inventory', damaged)
    else:
        c.args.pilot_part = 'selected'; c.args.selected = str(c.root / 'absent-selected')
    with pytest.raises(ValueError): c.prepare()
    assert not (c.preparation_path / 'COMPLETE.json').exists()
    assert not (c.root / 'pilot-target-preparation' / 'selected' / 'COMPLETE.json').exists()
    assert c.loader_calls == []


@pytest.mark.parametrize('damage', ['caller-flag', 'descriptor-as-reservation', 'resource-as-reservation',
    'unanchored', 'source', 'part', 'pilot', 'selection', 'work-dir', 'fake-seal'])
def test_prepared_admission_anchor_is_required(tmp_path, monkeypatch, damage):
    r = runtime(); load = r.load_prepared_pilot_target
    c = integration_case(tmp_path, monkeypatch, part='selected' if damage == 'selection' else 'prefit',
        selected=(damage == 'selection')).anchor()
    if damage == 'selection':
        path = Path(c.args.selected) / 'COMPLETE.json'; path.write_bytes(path.read_bytes() + b' ')
    elif damage == 'descriptor-as-reservation': c.args.reservation = str(c.preparation_path)
    elif damage == 'resource-as-reservation': c.args.reservation = str(c.resource_path)
    elif damage == 'caller-flag':
        c.args._prepared_target_validated = True
        c.args.reservation = None
    elif damage == 'fake-seal':
        c.args._prepared_target = {'validated': True, 'seal': object()}; c.args.reservation = None
    elif damage == 'work-dir': c.args.work_dir = str(c.root / 'another-workdir')
    elif damage == 'part': c.args.pilot_part = 'selected'
    elif damage == 'source': c.protocol = dict(c.protocol, commit='f' * 40)
    elif damage == 'pilot':
        c.pilot_inventory = copy.deepcopy(c.pilot_inventory); c.pilot_inventory['inventory_sha256'] = '0' * 64
    else:
        from tests.a3_prepared_integration_cases import rewrite_object
        mapping = r.read_object(c.mapping_path); mapping['original_admission_paths'] = []
        rewrite_object(c.mapping_path, mapping)
    with pytest.raises((ValueError, TypeError)): load(c.args, c.design, c.protocol, c.pilot_inventory)
    assert c.loader_calls == []


@pytest.mark.parametrize('damage', ['equal-graph-copy', 'equal-requirement-copy', 'wrong-pid', 'wrong-context', 'wrong-part', 'reinitialize', 'pickle', 'fork'])
def test_prepared_handle_is_one_graph(tmp_path, monkeypatch, damage):
    import pickle
    r = runtime(); load = r.load_prepared_pilot_target
    c = integration_case(tmp_path, monkeypatch).anchor(); handle = load(c.args, c.design, c.protocol, c.pilot_inventory)
    requirement = handle.inventory['requirements'][0]
    handle.assert_scope(c.args, c.design, c.protocol, c.pilot_inventory)
    assert handle.inventory['requirements'][0] is requirement
    assert handle.inventory == r.read_object(c.target_path)
    timing_rows = [row for req in handle.inventory['requirements'] for row in req.get('timing_inputs', [])]
    assert len(timing_rows) > 1 and len({id(row) for row in timing_rows}) == len(timing_rows)
    if damage == 'fork':
        import signal
        child = os.fork()
        if child == 0:
            signal.alarm(5)
            try: handle.assert_scope(c.args, c.design, c.protocol, c.pilot_inventory)
            except (ValueError, TypeError): os._exit(0)
            else: os._exit(1)
        _, status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        return
    with pytest.raises(TypeError): requirement['operation'] = 'changed'
    if damage == 'pickle':
        with pytest.raises(TypeError): pickle.dumps(handle)
        return
    if damage == 'reinitialize':
        with pytest.raises(TypeError): handle.__init__()
        return
    args = c.args
    if damage == 'equal-graph-copy': object.__setattr__(handle, 'inventory', copy.deepcopy(dict(handle.inventory)))
    elif damage == 'equal-requirement-copy':
        graph = dict(handle.inventory); graph['requirements'] = list(graph['requirements'])
        graph['requirements'][0] = dict(requirement); object.__setattr__(handle, 'inventory', graph)
    elif damage == 'wrong-pid':
        pid = os.getpid(); monkeypatch.setattr(r.os, 'getpid', lambda: pid + 1)
    elif damage == 'wrong-context': args = copy.copy(c.args); args._authority_context = object()
    elif damage == 'wrong-part': args = copy.copy(c.args); args.pilot_part = 'selected'
    with pytest.raises((ValueError, TypeError)): handle.assert_scope(args, c.design, c.protocol, c.pilot_inventory)


@pytest.mark.parametrize('capacity,accepts', [(100, True), (99, False)])
@pytest.mark.parametrize('identity_damage', [None, 'missing', 'target', 'preparation', 'reader-code', 'freeze-code', 'source', 'environment', 'recipe', 'scope', 'storage-family'])
def test_prepared_receiver_resource_identity_and_capacity(tmp_path, monkeypatch, capacity, accepts, identity_damage):
    r = runtime(); validate = r._validate_prepared_receiver_resources
    from tests.a3_prepared_integration_cases import environment_identity
    c = integration_case(tmp_path, monkeypatch).anchor()
    # Attack plain data: deepcopy intentionally preserves production frozen references.
    record = json.loads(json.dumps(c.resource_record, allow_nan=False))
    record.update(retained_metadata_bytes_bound=20, extra_transient_bytes_bound=30)
    inputs = dict(references=dict(target=c.preparation_binding['target_reference'],
        preparation=c.preparation_binding['preparation_reference']), source_identity=c.resource_record['source_identity'],
        environment=environment_identity(), actual_host_capacity=capacity, existing_host_obligations=50)
    if identity_damage == 'missing': record = None
    elif identity_damage == 'scope': record['scope'] = 'producer-only unmeasured graph'
    elif identity_damage in ('target', 'preparation'):
        record['references'][identity_damage]['files']['payload.json']['sha256'] = '0' * 64
    elif identity_damage == 'reader-code': record['reader_sha256'] = '0' * 64
    elif identity_damage == 'freeze-code': record['freeze_sha256'] = '0' * 64
    elif identity_damage == 'source': record['source_identity']['commit'] = 'f' * 40
    elif identity_damage == 'environment': record['environment']['python_version'] = 'wrong'
    elif identity_damage == 'recipe': record['recipe'] = 'wrong'
    elif identity_damage == 'storage-family': record['environment']['storage_family'] = 'wrong'
    if accepts and identity_damage is None:
        charges = validate(record, **inputs)
        assert charges['retained_metadata_bytes'] == 20 and charges['extra_transient_bytes'] == 30
        assert 50 + charges['retained_metadata_bytes'] + charges['extra_transient_bytes'] == 100
    else:
        with pytest.raises(ValueError): validate(record, **inputs)


@pytest.mark.parametrize('observation', ['retained', 'transient', 'applicable-peak', 'unavailable', 'wrong-scope'])
def test_prepared_correct_identity_understated_observed_resources_rejects(tmp_path, monkeypatch, observation):
    r = runtime(); load = r.load_prepared_pilot_target
    c = integration_case(tmp_path, monkeypatch).anchor(); calls = []; original = r._read_prepared_target_object
    if observation in ('retained', 'transient', 'applicable-peak'):
        field = {'retained': 'retained_metadata_bytes_bound', 'transient': 'extra_transient_bytes_bound',
            'applicable-peak': 'process_peak_rss_bytes_bound'}[observation]
        observed = c.observed['process_after']['process_peak_rss_bytes'] if observation == 'applicable-peak' else c.observed[
            'retained_metadata_bytes' if observation == 'retained' else 'extra_transient_bytes']
        understated = observed - 1 if observation == 'applicable-peak' else max(1, observed // 2)
        reanchor_resource(c, lambda record: record.__setitem__(field, understated))
    def reader(*args, **kwargs):
        result = original(*args, **kwargs); calls.append(result)
        if observation in ('unavailable', 'wrong-scope'):
            resources = dict(result[5])
            if observation == 'unavailable': resources['retained_metadata_bytes'] = None
            else: resources['scope'] = 'incomparable producer-only scope'
            result = (*result[:5], resources)
        return result
    monkeypatch.setattr(r, '_read_prepared_target_object', reader)
    with pytest.raises(ValueError): load(c.args, c.design, c.protocol, c.pilot_inventory)
    assert len(calls) == 1 and c.loader_calls == []


@pytest.mark.parametrize('damage', [None, 'cancel-during-reader', 'shorten-lease-during-reader', 'post-load-geometry'])
def test_prepared_dispatch_guard_and_geometry_order(tmp_path, monkeypatch, damage):
    r = runtime(); r._PreparedPilotTarget
    from component_analysis import hooks
    from tests.a3_prepared_integration_cases import rewrite_object
    c = integration_case(tmp_path, monkeypatch).anchor(); trace = []
    original_reader = r._read_prepared_target_object; original_guard = r.live_guard
    def reader(*args, **kwargs):
        trace.append('reader'); result = original_reader(*args, **kwargs)
        if damage == 'cancel-during-reader':
            c.live['reservations'][0]['status'] = 'cancelled'; c.live_path.write_text(json.dumps(c.live))
        elif damage == 'shorten-lease-during-reader':
            path = c.root / 'authority' / 'allocation'; allocation = r.read_object(path)
            allocation['end_time_unix'] = time.time(); rewrite_object(path, allocation)
        return result
    def guard(*args, **kwargs):
        trace.append('live'); return original_guard(*args, **kwargs)
    def loader(args): trace.append('loader'); c.loader_calls.append(args); return object()
    def geometry(model):
        trace.append('geometry'); return dict(head_dim=999 if damage == 'post-load-geometry' else 2, hidden_size=4, num_layers=1)
    def numeric(*args, **kwargs):
        trace.append('numeric'); assert type(kwargs['prepared_target']) is r._PreparedPilotTarget
    monkeypatch.setattr(r, '_read_prepared_target_object', reader); monkeypatch.setattr(r, 'live_guard', guard)
    monkeypatch.setattr(r.ladder, 'load_model', loader); monkeypatch.setattr(hooks, 'geometry', geometry)
    monkeypatch.setattr(r, 'run_pilot', numeric)
    if damage is not None:
        with pytest.raises(ValueError): r.dispatch(c.args)
        assert 'numeric' not in trace
        assert len(c.loader_calls) == (1 if damage == 'post-load-geometry' else 0)
    else:
        assert r.dispatch(c.args) == 0
        assert trace.index('reader') < trace.index('loader') < trace.index('geometry') < trace.index('numeric')
        assert 'live' in trace[trace.index('reader') + 1:trace.index('loader')]
        assert 'live' in trace[trace.index('geometry') + 1:trace.index('numeric')]


@pytest.mark.parametrize('damage', ['missing-preparation', 'missing-handle', 'caller-provider'])
def test_prepared_production_has_no_build_fallback(tmp_path, monkeypatch, damage):
    r = runtime(); r._PreparedPilotTarget
    c = integration_case(tmp_path, monkeypatch)
    if damage == 'caller-provider': c.args.prepared_target_provider = lambda: {'validated': True}
    monkeypatch.setattr(r.ladder, 'load_model', lambda args: c.loader_calls.append(args) or object())
    if damage == 'missing-handle':
        monkeypatch.setattr(r, '_pilot_invocation', lambda *args, **kwargs: pytest.fail('numerical entry before prepared handle'))
        with pytest.raises(ValueError):
            r.run_pilot(object(), dict(c.design, injected=False), c.protocol, c.pilot_inventory,
                root=c.root, args=c.args, guard=c.guard, startup_seconds=0)
    else:
        with pytest.raises(ValueError): r.dispatch(c.args)
    assert c.loader_calls == [] and not c.target_path.exists()


@pytest.mark.parametrize('seam', ['guard-union', 'before-publication', 'final-live-guard'])
@pytest.mark.parametrize('damage', ['target-payload-restored-mtime', 'descriptor-marker', 'identical-target-tree'])
def test_prepared_final_barrier_after_all_costly_work(tmp_path, monkeypatch, seam, damage, request):
    r = runtime(); r._PreparedPilotTarget
    request.getfixturevalue('fake')
    c = integration_case(tmp_path, monkeypatch).anchor(); handle = c.load(); writer_calls = []; phase = {'final': False, 'mutated': False, 'final_live_guard_calls': 0}
    def mutate():
        if phase['mutated']: return
        phase['mutated'] = True
        if damage == 'identical-target-tree':
            replacement = c.root / 'same-tree'; shutil.copytree(c.target_path, replacement)
            c.target_path.rename(c.root / 'old-target'); replacement.rename(c.target_path)
        else:
            path = c.preparation_path / 'COMPLETE.json' if damage == 'descriptor-marker' else c.target_path / 'payload.json'
            st = path.stat(); raw = path.read_bytes(); path.write_bytes(raw)
            os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
    original_union = r._measure_complete_guard_union; original_before = r._PilotReconciliationPass.before_publication
    original_barrier = r._PreparedPilotTarget.final_publication_barrier; original_live_guard = r.live_guard
    def union(*args, **kwargs):
        result = original_union(*args, **kwargs)
        if seam == 'guard-union': mutate()
        return result
    def before(instance):
        result = original_before(instance)
        if seam == 'before-publication': mutate()
        return result
    def barrier(instance, *args, **kwargs):
        phase['final'] = True
        try: return original_barrier(instance, *args, **kwargs)
        finally: phase['final'] = False
    def live_guard(*args, **kwargs):
        result = original_live_guard(*args, **kwargs)
        if seam == 'final-live-guard' and phase['final']:
            phase['final_live_guard_calls'] += 1
            mutate()
        return result
    monkeypatch.setattr(r, 'live_guard', live_guard)
    monkeypatch.setattr(r, '_measure_complete_guard_union', union)
    monkeypatch.setattr(r._PilotReconciliationPass, 'before_publication', before)
    monkeypatch.setattr(r._PreparedPilotTarget, 'final_publication_barrier', barrier)
    monkeypatch.setattr(r, '_publish_measured_pilot_receipt', lambda *args: writer_calls.append(args))
    with pytest.raises(ValueError):
        r.run_pilot(object(), c.design, c.protocol, c.pilot_inventory, root=c.root, args=c.args,
            guard=c.guard, startup_seconds=0, prepared_target=handle)
    if seam == 'final-live-guard': assert phase['final_live_guard_calls'] == 1
    assert phase['mutated'] and writer_calls == []


@pytest.mark.parametrize('damage', ['adopt-current-reference', 'equal-requirement-copy', 'forged-handle', 'expiry-during-final-hash', 'expiry-during-final-live-guard'])
def test_prepared_final_barrier_cannot_adopt_current(tmp_path, monkeypatch, damage):
    r = runtime(); r._PreparedPilotTarget
    c = integration_case(tmp_path, monkeypatch).anchor(); handle = c.load(); expiry_calls = []
    reconciliation = r._PilotReconciliationPass([], handle.inventory, guard=c.guard, injected=True)
    with reconciliation: pass
    reconciliation.before_publication()
    if damage == 'forged-handle':
        handle = object.__new__(r._PreparedPilotTarget)
    elif damage == 'equal-requirement-copy':
        graph = dict(handle.inventory); graph['requirements'] = list(graph['requirements'])
        graph['requirements'][0] = dict(graph['requirements'][0]); object.__setattr__(handle, 'inventory', graph)
    elif damage == 'adopt-current-reference':
        from tests.a3_prepared_integration_cases import rewrite_object
        value = r.read_object(c.target_path); value['changed'] = True; rewrite_object(c.target_path, value)
        object.__setattr__(handle, 'entry_references', dict(handle.entry_references, target=r.object_reference(c.target_path)))
    else:
        original = r._check_file_witness if damage == 'expiry-during-final-hash' else r.live_guard
        def expired(*args, **kwargs):
            result = original(*args, **kwargs); expiry_calls.append(1)
            allocation = r.read_object(c.root / 'authority' / 'allocation')
            monkeypatch.setattr(r.time, 'time', lambda: allocation['end_time_unix'] + 1)
            return result
        monkeypatch.setattr(r, '_check_file_witness' if damage == 'expiry-during-final-hash' else 'live_guard', expired)
    with pytest.raises((ValueError, TypeError)): handle.final_publication_barrier(reconciliation, {})
    if damage.startswith('expiry-'): assert expiry_calls


def test_prepared_costs_and_envelope_are_charged(tmp_path, monkeypatch, request):
    r = runtime(); r._PreparedPilotTarget
    request.getfixturevalue('fake')
    from tests.test_a3_direction_workload import ledger
    c = integration_case(tmp_path, monkeypatch).anchor(); handle = c.load()
    events = []; original_union = r._measure_complete_guard_union
    original_before = r._PilotReconciliationPass.before_publication; original_barrier = r._PreparedPilotTarget.final_publication_barrier
    original_writer = r._publish_measured_pilot_receipt
    def union(receipt, *args):
        events.append('union')
        assert receipt['origin']['target_preparation_reference'] == r.object_reference(c.preparation_path)
        assert receipt['origin']['receiver_resources_reference'] == r.object_reference(c.resource_path)
        return original_union(receipt, *args)
    def before(instance): events.append('before'); return original_before(instance)
    def barrier(instance, *args): events.append('barrier'); return original_barrier(instance, *args)
    def writer(*args): events.append('writer'); return original_writer(*args)
    monkeypatch.setattr(r, '_measure_complete_guard_union', union)
    monkeypatch.setattr(r._PilotReconciliationPass, 'before_publication', before)
    monkeypatch.setattr(r._PreparedPilotTarget, 'final_publication_barrier', barrier)
    monkeypatch.setattr(r, '_publish_measured_pilot_receipt', writer)
    receipt = r.run_pilot(object(), c.design, c.protocol, c.pilot_inventory, root=c.root, args=c.args,
        guard=c.guard, startup_seconds=7., prepared_target=handle)
    assert events[-4:] == ['union', 'before', 'barrier', 'writer']
    assert receipt['startup_seconds'] == 7. and receipt['proof_validation_seconds'] > 0
    target = handle.inventory; receipts = [receipt]; budget = ledger(target)
    budget['storage_capacities']['host_ram']['available_bytes'] = 2**44
    proofs = r._cost_packing_proofs(receipts)
    measured = r.workload.project_cost(receipts, target, budget, packing_proofs=proofs)
    baseline = copy.deepcopy(receipt); baseline['startup_seconds'] = 0.; baseline['proof_validation_seconds'] = 0.
    baseline_proofs = r._cost_packing_proofs([baseline])
    zero = r.workload.project_cost([baseline], target, budget, packing_proofs=baseline_proofs)
    assert measured['projected_seconds'] - zero['projected_seconds'] == pytest.approx(
        len(target['jobs']) * (7. + receipt['proof_validation_seconds']))
    assert not (c.root / 'new-target-after-model').exists()
    with pytest.raises(ValueError):
        r._publish_measured_pilot_receipt(c.root / 'oversize', dict(receipt, added='x' * (receipt['guard_dependency_measurement']['final_receipt_file_upper_bytes']['payload.json'] + 1)))
    assert not (c.root / 'oversize' / 'COMPLETE.json').exists()
    with pytest.raises(ValueError):
        r._publish_measured_pilot_receipt(c.root / 'nonfinite', dict(receipt, startup_seconds=float('nan')))
    assert not (c.root / 'nonfinite' / 'COMPLETE.json').exists()


def test_prepared_native_adapter_and_intake_preserve_scope(tmp_path, monkeypatch, request):
    r = runtime(); r._PreparedPilotTarget
    request.getfixturevalue('fake')
    from tests import a3_direction_native_scenario as scenario
    c = integration_case(tmp_path, monkeypatch).anchor(); handle = c.load()
    inv = c.pilot_inventory; ids = [row['invocation_id'] for row in scenario._case_invocations(c.design, inv, 'prefit')]
    assert len(ids) == 9
    binding = dict(kind='explicit_fake_cpu_case_binding', source=scenario.source_identity())
    scenario.pilot_cases(object(), c.design, c.protocol, inv, root=c.root, part='prefit', case_ids=ids, binding=binding)
    before = [r.object_reference(c.root / 'pilot-verification-cases' / 'prefit' / case_id) for case_id in ids]
    result = scenario.aggregate_pilot_cases(object(), c.design, c.protocol, inv, root=c.root,
        part='prefit', binding=binding, prepared_target=handle)
    aggregate = r.read_object(c.root / 'pilot-verification-aggregate' / 'prefit')
    assert result['complete'] and aggregate['case_order'] == ids
    assert aggregate['case_forwards_reexecuted'] is False and aggregate['new_reconciliation_work_is_actual'] is True
    assert [r.object_reference(c.root / 'pilot-verification-cases' / 'prefit' / case_id) for case_id in ids] == before


@pytest.mark.parametrize('damage', [None, 'legacy-no-preparation', 'missing-preparation', 'changed-resource',
    'unanchored-resource', 'wrong-preparation-source', 'wrong-preparation-part'])
def test_prepared_migrated_intake_and_legacy_rejection(tmp_path, monkeypatch, damage):
    r = runtime(); r._PreparedPilotTarget
    from tests.test_a3_direction_runtime import _production_cost_source_case
    from tests.a3_prepared_integration_cases import rewrite_object
    r, design, protocol, target, path, mapping, live_path, live = _production_cost_source_case(tmp_path, monkeypatch)
    value = r.read_object(path)
    if damage is None:
        receipts, sources = r._authenticated_pilot_receipts(design, protocol, target, [path], ledger_path=mapping)
        assert len(receipts) == len(sources) == 1 and sources[0].value['execution_authorized'] is False
        return
    origin = value['origin']
    if damage == 'legacy-no-preparation':
        origin.pop('target_preparation_reference', None); origin.pop('receiver_resources_reference', None)
    elif damage == 'missing-preparation': origin.pop('target_preparation_reference')
    elif damage == 'changed-resource': origin['receiver_resources_reference']['files']['payload.json']['sha256'] = '0' * 64
    elif damage == 'unanchored-resource': origin['receiver_resources_reference'] = origin['target_preparation_reference']
    else:
        prep = origin['target_preparation_reference']; descriptor = r.read_object(prep['path'])
        if damage == 'wrong-preparation-source': descriptor['source_identity']['commit'] = 'f' * 40
        else: descriptor['part'] = 'selected'
        rewrite_object(Path(prep['path']), descriptor); origin['target_preparation_reference'] = r.object_reference(prep['path'])
    rewrite_object(path, value)
    with pytest.raises((ValueError, FileNotFoundError)):
        r._authenticated_pilot_receipts(design, protocol, target, [path], ledger_path=mapping)


def test_prepared_producer_descriptor_binds_complete_inventory_summary(tmp_path, monkeypatch):
    c = integration_case(tmp_path, monkeypatch)
    reference = c.prepare(); descriptor = c.r.read_object(reference['path'])
    target = c.r.read_object(c.target_path)
    keys = ('operation_counts', 'forward_counts', 'bytes', 'jobs', 'blockers',
        'conditional_unavailable', 'fit_failures', 'finish_reserve_seconds', 'hardware', 'reuse_policy')
    assert descriptor['summary'] == {key: target[key] for key in keys}
    assert descriptor['summary']['jobs'] and descriptor['summary']['operation_counts']
    assert descriptor['storage_requirements'] == target['storage_requirements']
    assert c.loader_calls == []


@pytest.mark.parametrize('missing', ['observed_io', 'environment', 'retained_metadata_bytes_bound', 'provenance'])
def test_prepared_completed_intake_rejects_incomplete_originally_anchored_resources(tmp_path, monkeypatch, missing):
    r = runtime()
    from tests.test_a3_direction_runtime import _production_cost_source_case
    original = r.publish_object
    published = []
    def publish(path, payload):
        if payload.get('kind') == 'a3_prepared_target_receiver_resources_v1':
            payload = copy.deepcopy(payload); payload.pop(missing, None); published.append(Path(path))
        return original(path, payload)
    monkeypatch.setattr(r, 'publish_object', publish)
    r, design, protocol, target, path, mapping, _, _ = _production_cost_source_case(tmp_path, monkeypatch)
    assert len(published) == 1
    origin = r.read_object(path)['origin']
    resource = origin['receiver_resources_reference']
    admission = r.read_object(origin['admission_reference']['path'])
    assert resource == r.object_reference(published[0])
    assert admission['pilot_target_preparation']['receiver_resources_reference'] == resource
    with pytest.raises(ValueError, match='receiver resource|receiver resources'):
        r._authenticated_pilot_receipts(design, protocol, target, [path], ledger_path=mapping)


def damage_receiver_evidence(record, damage):
    if damage in ('measurement', 'deployment'): record.pop(damage)
    elif damage == 'cold-wall': record['measurement']['phases']['cold'].pop('wall_seconds')
    elif damage == 'warm-cpu': record['measurement']['phases']['warm'].pop('user_seconds')
    elif damage == 'process-scope': record['measurement']['phases']['cold']['process']['scope'] = 'unknown'
    elif damage == 'cgroup-scope': record['measurement']['phases']['warm']['cgroup'] = {}
    elif damage == 'storage-family': record['deployment']['storage']['target']['filesystem'] = 'wrong'
    elif damage == 'allocation-family': record['deployment']['allocation_family']['cpus'] += 1
    elif damage == 'cpu-family': record['deployment']['cpu_family']['model'] = 'wrong'
    else: raise AssertionError(damage)


@pytest.mark.parametrize('damage', ['measurement', 'deployment', 'cold-wall', 'warm-cpu', 'process-scope',
    'cgroup-scope', 'storage-family', 'allocation-family', 'cpu-family'])
def test_prepared_receiver_evidence_schema_rejects_originally_anchored_gaps(tmp_path, monkeypatch, damage):
    from tests.a3_prepared_integration_cases import environment_identity, rewrite_object
    c = integration_case(tmp_path, monkeypatch).anchor()
    record = copy.deepcopy(c.resource_record); damage_receiver_evidence(record, damage)
    rewrite_object(c.resource_path, record)
    binding = dict(c.preparation_binding, receiver_resources_reference=c.r.object_reference(c.resource_path))
    c._bind_original_authority(binding)
    admission = c.r.read_object(c.admission_path)
    assert admission['pilot_target_preparation']['receiver_resources_reference'] == c.r.object_reference(c.resource_path)
    with pytest.raises(ValueError, match='receiver resource'):
        c.r._validate_prepared_receiver_resources(record,
            references=dict(target=binding['target_reference'], preparation=binding['preparation_reference']),
            source_identity=c.resource_record['source_identity'], environment=environment_identity(),
            actual_host_capacity=2**44, existing_host_obligations=0)
    assert c.loader_calls == []


@pytest.mark.parametrize('damage', ['storage-family', 'allocation-family', 'cpu-family'])
def test_prepared_receiver_actual_context_rejects_originally_anchored_mismatch(tmp_path, monkeypatch, damage):
    c = integration_case(tmp_path, monkeypatch).anchor()
    record = copy.deepcopy(c.resource_record); damage_receiver_evidence(record, damage)
    from tests.a3_prepared_integration_cases import rewrite_object
    rewrite_object(c.resource_path, record)
    binding = copy.deepcopy(c.preparation_binding)
    binding.update(receiver_resources_reference=c.r.object_reference(c.resource_path), receiver_deployment=record['deployment'])
    c._bind_original_authority(binding)
    with pytest.raises(ValueError, match='receiver resource'):
        c.r.load_prepared_pilot_target(c.args, c.design, c.protocol, c.pilot_inventory)
    assert c.loader_calls == []


@pytest.mark.parametrize('damage', ['measurement', 'cold-wall', 'allocation-family'])
def test_prepared_completed_intake_rejects_originally_anchored_measurement_gaps(tmp_path, monkeypatch, damage):
    r = runtime()
    from tests.test_a3_direction_runtime import _production_cost_source_case
    original = r.publish_object; attacked = []
    def publish(path, payload):
        if payload.get('kind') == 'a3_prepared_target_receiver_resources_v1':
            payload = copy.deepcopy(payload); damage_receiver_evidence(payload, damage); attacked.append(Path(path))
        return original(path, payload)
    monkeypatch.setattr(r, 'publish_object', publish)
    r, design, protocol, target, path, mapping, _, _ = _production_cost_source_case(tmp_path, monkeypatch)
    assert len(attacked) == 1
    origin = r.read_object(path)['origin']; admission = r.read_object(origin['admission_reference']['path'])
    assert origin['receiver_resources_reference'] == r.object_reference(attacked[0])
    assert admission['pilot_target_preparation']['receiver_resources_reference'] == origin['receiver_resources_reference']
    with pytest.raises(ValueError, match='receiver resource'):
        r._authenticated_pilot_receipts(design, protocol, target, [path], ledger_path=mapping)


def test_prepared_actual_native_aggregate_route_receives_before_model(tmp_path, monkeypatch, request):
    request.getfixturevalue('fake')
    from tests import a3_direction_native_scenario as scenario
    c = integration_case(tmp_path, monkeypatch)
    r = c.r; ids = [row['invocation_id'] for row in scenario._case_invocations(c.design, c.pilot_inventory, 'prefit')]
    assert len(ids) == 9
    identity = {'explicit_synthetic_model': True}
    r.publish_object(c.root / 'scenario', {'model_identity': identity})
    binding = r.read_object(c.root / 'scenario')
    scenario.pilot_cases(object(), c.design, c.protocol, c.pilot_inventory, root=c.root, part='prefit', case_ids=ids, binding=binding)
    before = [r.object_reference(c.root / 'pilot-verification-cases' / 'prefit' / key) for key in ids]
    phase = {'received': False, 'model': False}; entry_reads = []; final_reads = []
    original_reader = r._read_prepared_target_object
    def receiver(*args, **kwargs):
        assert not phase['model']
        result = original_reader(*args, **kwargs); phase['received'] = True
        assert result[4] == dict(full_payload_reads=2, SHA_passes=2, parse_passes=1, freeze_passes=1, target_writes=0)
        entry_reads.append(result[4]); return result
    def verify(root, *, load_model=True):
        assert Path(root) == c.root
        if load_model:
            assert phase['received'], 'native aggregate loaded model before prepared reception'
            phase['model'] = True
        return c.design, c.protocol, object() if load_model else None, object() if load_model else None
    original_builder = r.workload.build_inventory; original_publish = r.publish_object; original_read = r.read_object
    def build(*args, **kwargs):
        assert not phase['model'] or kwargs['stage'] != 'fit-select', 'legacy full-target builder after model'
        return original_builder(*args, **kwargs)
    def publish(path, value):
        assert not phase['model'] or Path(path) != c.target_path, 'legacy target publication after model'
        return original_publish(path, value)
    def read(path):
        assert not phase['model'] or Path(path) != c.target_path, 'legacy target readback after model'
        return original_read(path)
    original_witness = r._check_file_witness
    def check(witness):
        if str(c.target_path) in witness.paths:
            assert phase['model']; final_reads.append(witness)
        return original_witness(witness)
    original_run = r.run_pilot
    def run(*args, **kwargs):
        assert kwargs.get('prepared_target') is not None, 'actual native route lost prepared handle'
        return original_run(*args, **kwargs)
    monkeypatch.setattr(scenario, 'verify_scenario', verify)
    monkeypatch.setattr(scenario, 'model_identity', lambda _: identity)
    monkeypatch.setattr(r, '_read_prepared_target_object', receiver)
    monkeypatch.setattr(r, '_check_file_witness', check)
    monkeypatch.setattr(r.workload, 'build_inventory', build)
    monkeypatch.setattr(r, 'publish_object', publish); monkeypatch.setattr(r, 'read_object', read)
    monkeypatch.setattr(r, 'run_pilot', run)
    result = scenario.run_phase(c.root, 'prefit-aggregate')
    aggregate = original_read(c.root / 'pilot-verification-aggregate' / 'prefit')
    assert result['complete'] and result['completed_pilot_cases'] == 9 and aggregate['case_order'] == ids
    assert aggregate['case_forwards_reexecuted'] is False and aggregate['new_reconciliation_work_is_actual'] is True
    assert [r.object_reference(c.root / 'pilot-verification-cases' / 'prefit' / key) for key in ids] == before
    assert len(entry_reads) == 1 and len(final_reads) == 1


def test_prepared_production_rejects_native_test_handle(tmp_path):
    from types import SimpleNamespace
    from tests import a3_direction_native_scenario as scenario
    r = runtime(); handle = object.__new__(scenario._InjectedPreparedPilotTarget)
    with pytest.raises(ValueError, match='injected test handles'):
        r.run_pilot(object(), {'injected': False}, {}, {}, root=tmp_path,
            args=SimpleNamespace(pilot_part='prefit'), guard=lambda: pytest.fail('model guard reached'),
            startup_seconds=0, prepared_target=handle)


def injected_cgroup_observation(applicable):
    # Explicit synthetic unit scope. These small fields are not genuine cgroup evidence.
    if applicable:
        return dict(applicable=True, scope='entire current cgroup, including other processes; lifetime peak',
            path='/explicit-synthetic-unit-cgroup', current_bytes=1, peak_bytes=1, events={'high': 0})
    return dict(applicable=False, scope='not applicable', reason='cgroup-v2-observations-unavailable')


def set_anchored_measurement_cgroup_scope(r, record, applicable, *, warm_disagrees=False):
    from tests.a3_prepared_integration_cases import rewrite_object
    for label, phase in record['measurement']['phases'].items():
        phase['cgroup'] = injected_cgroup_observation(not applicable if warm_disagrees and label == 'warm' else applicable)
    reference = record['measurement']['run_manifest_reference']
    run = r.read_object(reference['path']); run['phases'] = copy.deepcopy(record['measurement']['phases'])
    run['test_only_cgroup_scope_injection'] = True
    rewrite_object(Path(reference['path']), run)
    record['measurement']['run_manifest_reference'] = r.object_reference(reference['path'])


def inject_current_receiver_cgroup_scope(process, applicable):
    group = injected_cgroup_observation(applicable)
    process.update(cgroup_scope=group['scope'] if applicable else None,
        cgroup_path=group.get('path'), cgroup_peak_bytes=group.get('peak_bytes'),
        cgroup_current_bytes=group.get('current_bytes'), test_only_cgroup_scope_injection=True)


@pytest.mark.parametrize('measured,current', [(False, True), (True, False)])
def test_prepared_anchored_cgroup_scope_mismatch_rejects_before_loader(tmp_path, monkeypatch, measured, current):
    from tests.a3_prepared_integration_cases import rewrite_object
    c = integration_case(tmp_path, monkeypatch).anchor(); r = c.r
    record = copy.deepcopy(c.resource_record); set_anchored_measurement_cgroup_scope(r, record, measured)
    rewrite_object(c.resource_path, record)
    binding = dict(c.preparation_binding, receiver_resources_reference=r.object_reference(c.resource_path))
    c._bind_original_authority(binding)
    assert r.read_object(c.admission_path)['pilot_target_preparation']['receiver_resources_reference'] == r.object_reference(c.resource_path)
    original = r._read_prepared_target_object; readers = []
    def receiver(*args, **kwargs):
        result = original(*args, **kwargs); resources = copy.deepcopy(result[5])
        inject_current_receiver_cgroup_scope(resources['process_after'], current); readers.append(1)
        return (*result[:5], resources)
    monkeypatch.setattr(r, '_read_prepared_target_object', receiver)
    with pytest.raises(ValueError, match='measured/current cgroup applicability'):
        r.load_prepared_pilot_target(c.args, c.design, c.protocol, c.pilot_inventory)
    assert readers == [1] and c.loader_calls == []


def test_prepared_anchored_cold_warm_cgroup_scope_disagreement_rejects(tmp_path, monkeypatch):
    from tests.a3_prepared_integration_cases import rewrite_object
    c = integration_case(tmp_path, monkeypatch).anchor(); r = c.r
    record = copy.deepcopy(c.resource_record); set_anchored_measurement_cgroup_scope(r, record, True, warm_disagrees=True)
    rewrite_object(c.resource_path, record)
    c._bind_original_authority(dict(c.preparation_binding, receiver_resources_reference=r.object_reference(c.resource_path)))
    with pytest.raises(ValueError, match='cold/warm observation scopes incomparable'):
        r.load_prepared_pilot_target(c.args, c.design, c.protocol, c.pilot_inventory)
    assert c.loader_calls == []


@pytest.mark.parametrize('measured,current', [(False, True), (True, False)])
def test_prepared_completed_intake_rejects_anchored_cgroup_scope_mismatch(tmp_path, monkeypatch, measured, current):
    from tests.test_a3_direction_runtime import _production_cost_source_case
    r = runtime(); original = r.publish_object; changed = []
    def publish(path, payload):
        if payload.get('kind') == 'a3_prepared_target_receiver_resources_v1':
            payload = copy.deepcopy(payload); set_anchored_measurement_cgroup_scope(r, payload, measured); changed.append(Path(path))
        elif payload.get('kind') == 'a3_direction_timing_v1':
            payload = copy.deepcopy(payload)
            inject_current_receiver_cgroup_scope(payload['prepared_target_transport']['observed_resources']['process_after'], current)
        return original(path, payload)
    monkeypatch.setattr(r, 'publish_object', publish)
    r, design, protocol, target, path, mapping, _, _ = _production_cost_source_case(tmp_path, monkeypatch)
    assert len(changed) == 1
    origin = r.read_object(path)['origin']; admission = r.read_object(origin['admission_reference']['path'])
    assert admission['pilot_target_preparation']['receiver_resources_reference'] == r.object_reference(changed[0])
    with pytest.raises(ValueError, match='measured/current cgroup applicability'):
        r._authenticated_pilot_receipts(design, protocol, target, [path], ledger_path=mapping)
