"""Private prepared transport contracts; artifacts are data, never admission.

Each test names the break it catches. Missing helpers are resolved inside test
bodies, outside expected-rejection contexts, so RED is attributable to transport.
"""
import builtins
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
