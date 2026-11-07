"""Task 2 CPU contracts; missing helpers fail within cases, never collection.

These fixtures exercise operational policy with tiny data and a native-boundary
spy. They confer no authentic bank, scientific-domain, resource or GPU authority.
Mutations caught: omitted native bank reader/contract validation; limit4 args;
wrong numerical environment; missing aliases/current catalogue witnesses;
count-only domain checks; and promotion of late, terminated or partial children.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

CPU = Path(__file__).resolve().parents[1] / 'cpu'
W = '/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder'
S = W + '/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
MAIN = W + '/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
SOURCE = '50e947bb852613e3a270082651f2bd1b7bb0c525'
MISSING = 'FULL_SCORE_CPU_IMPLEMENTATION_MISSING'
CATALOGUES = tuple(root + '/docs/research/' + name for root in (
    '/projects/beto/swong2/Alignment/Deception-Circuit', W)
    for name in ('held_out.json', 'directions.json'))


def module(name):
    path = CPU / (name + '.py')
    assert path.is_file(), MISSING + ': ' + str(path)
    spec = importlib.util.spec_from_file_location('t2_' + name.replace('-', '_'), str(path))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def need(m, name):
    function = getattr(m, name, None)
    if not callable(function):
        pytest.fail(MISSING + ': callable ' + name)
    return function


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def parameters():
    return dict(phase='full_score', accepted_runtime=S, accepted_source_commit=SOURCE,
                new_g3_output=MAIN, design=W + '/outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json',
                selected=W + '/outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json',
                registry=W + '/docs/research/held_out.json')


def test_full_score_arguments_are_original_without_limit():
    m = module('validate-phase')
    assert need(m, 'score_arguments')(parameters()) == [
        '--stage', 'score', '--design', parameters()['design'], '--selected', parameters()['selected'],
        '--commit', SOURCE, '--batch-size', '8', '--registry', parameters()['registry'], '--work-dir', MAIN]


@pytest.mark.parametrize('phase', ['bank', 'prefix4', 'score', 'summarize', None])
def test_owning_args_reject_historical_and_unknown_phases(phase):
    m = module('validate-phase'); p = parameters(); p['phase'] = phase
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'score_arguments')(p)


def native_boundary(fail=None, numeric_mismatch=False):
    """Only heavyweight native boundary is replaced; no native modules imported.

    Real native APIs and side effects were read directly from source50e. All
    model, freeze, scoring and weight boundaries explode if called. Calls below
    are precise assertions about this wrapper's native orchestration contract.
    """
    events = []
    prepared = dict(model='fixture-model', model_revision='fixture-model-rev',
                    tokenizer_revision='fixture-tokenizer-rev', injected=False)
    receipt = dict(model_geometry={'layers': 2}, injected=False, independent_donor_seeds=[],
                   groups={str(n): {} for n in range(9)}, receipt_sha256='fixture-receipt')
    numeric = dict(python='fixture-python', torch='fixture-torch', transformers='fixture-transformers',
                   cuda_matmul_allow_tf32=False)
    banks = dict(kind='a2_h_banks', injected=False, receipt_sha256='fixture-receipt',
                 execution_provenance=dict(dtype='torch.bfloat16', device='cuda:0',
                                           gpu_name='NVIDIA H100 80GB HBM3', gpu_uuid='GPU-bank'),
                 banks={task: dict(contract={'numeric_environment': copy.deepcopy(numeric)})
                        for task in ('far', 'sdr', 'ser')})
    if numeric_mismatch:
        banks['banks']['ser']['contract']['numeric_environment']['torch'] = 'wrong'
    def event(name):
        events.append(name)
        if fail == name:
            raise ValueError('native failure: ' + name)
    def parser():
        p = argparse.ArgumentParser()
        for flag in ('stage', 'design', 'selected', 'commit', 'registry', 'work-dir'):
            p.add_argument('--' + flag)
        p.add_argument('--batch-size', type=int)
        p.add_argument('--limit', type=int, default=0)
        return p
    def load_context(args):
        assert args.stage == 'score' and args.limit == 0 and args.batch_size == 8
        event('context'); return prepared, {'fixture': 'selection'}, {'fixture': 'sidecar'}
    def artifact(path):
        assert Path(path) == Path(MAIN) / 'groups.json'
        event('groups'); return receipt
    def live(args, rec, prep):
        assert rec is receipt and prep is prepared
        event('live')
    def geometry(prep):
        assert prep is prepared; event('geometry'); return {'layers': 2}
    def read_stage(path, filename, stage, args, rec):
        assert Path(path) == Path(MAIN) / 'bank' and filename == 'banks.json' and stage == 'bank'
        assert args.stage == 'score' and args.limit == 0 and rec is receipt
        event('bank-read'); return banks
    def validate_banks(rec, prep, bank):
        assert rec is receipt and prep is prepared and bank is banks
        event('bank-contract')
    tokenizer = object()
    def load_tokenizer(args):
        assert (args.model, args.model_revision, args.tokenizer_revision) == (
            'fixture-model', 'fixture-model-rev', 'fixture-tokenizer-rev')
        event('tokenizer'); return tokenizer
    def tokenization(prep, actual):
        assert prep is prepared and actual is tokenizer; event('saved-layout')
    def forbidden(*args, **kwargs):
        raise AssertionError('CPU guard attempted model/freeze/score/weights')
    p = SimpleNamespace(parser=parser, _load_context=load_context, _validate_live=live,
                        model_geometry_receipt=geometry, read_stage=read_stage,
                        validate_banks=validate_banks, numeric_environment=lambda: copy.deepcopy(numeric),
                        TASKS=('far', 'sdr', 'ser'), freeze=forbidden, score=forbidden,
                        collect_banks=forbidden, load_model=forbidden,
                        a1=SimpleNamespace(read_artifact=artifact, validate_tokenization=tokenization,
                                           common=SimpleNamespace(load_tokenizer=load_tokenizer,
                                                                  load_model=forbidden)))
    return p, events


def test_cpu_full_bank_native_validation_and_guard_order():
    m = module('validate-phase'); p, events = native_boundary()
    result = need(m, 'validate_native_context')(parameters(), p)
    assert events == ['context', 'groups', 'live', 'geometry', 'bank-read', 'bank-contract',
                      'tokenizer', 'saved-layout', 'live']
    assert result['numeric_environment']['torch'] == 'fixture-torch'
    assert result['model_loaded'] is False and result['freeze_executed'] is False
    assert result['GPU_admitted'] is False


@pytest.mark.parametrize('failure', ['context', 'groups', 'live', 'geometry', 'bank-read',
                                     'bank-contract', 'tokenizer', 'saved-layout'])
def test_each_native_bank_or_owning_failure_propagates(failure):
    m = module('validate-phase'); p, events = native_boundary(fail=failure)
    with pytest.raises(ValueError, match='native failure: ' + failure):
        need(m, 'validate_native_context')(parameters(), p)
    assert events[-1] == failure


def test_actual_numeric_environment_must_match_every_native_bank_task():
    m = module('validate-phase'); p, _ = native_boundary(numeric_mismatch=True)
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_native_context')(parameters(), p)


@pytest.fixture
def export(tmp_path):
    runtime = tmp_path / 'runtime'; runtime.mkdir()
    source = {}
    for n in range(511):
        name = 'module%03d.py' % n; raw = ('# fixture %d\n' % n).encode()
        (runtime / name).write_bytes(raw); source[name] = digest(raw)
    targets = tmp_path / 'targets'; targets.mkdir(); links = {}
    for n in range(4):
        target = targets / ('input%d' % n); target.write_text('input')
        name = 'input%d' % n; (runtime / name).symlink_to(target); links[name] = str(target)
    return runtime, dict(source_commit=SOURCE, runtime_root=str(runtime), source_sha256=source,
                         input_links=links, source_code_symlinks=False)


def test_exact_source_511_and_four_literal_links(export):
    m = module('validate-phase'); runtime, snapshot = export
    result = need(m, 'verify_source_export')(runtime, snapshot)
    assert result['source_count'] == 511 and result['input_link_count'] == 4


@pytest.mark.parametrize('fault', ['source-change', 'extra-source', 'missing-source', 'changed-link',
                                  'extra-link', 'absolute-key', 'parent-key', 'source-symlink'])
def test_source_closure_rejects_drift_and_nonrelative_keys(export, fault):
    m = module('validate-phase'); runtime, snapshot = export
    if fault == 'source-change': (runtime / 'module000.py').write_text('changed')
    elif fault == 'extra-source': (runtime / 'extra.py').write_text('extra')
    elif fault == 'missing-source': (runtime / 'module000.py').unlink()
    elif fault == 'changed-link':
        (runtime / 'input0').unlink(); (runtime / 'input0').symlink_to('input1')
    elif fault == 'extra-link': (runtime / 'extra').symlink_to('input0')
    elif fault in ('absolute-key', 'parent-key'):
        h = snapshot['source_sha256'].pop('module000.py')
        snapshot['source_sha256'][str(runtime / 'module000.py') if fault == 'absolute-key' else '../module000.py'] = h
    elif fault == 'source-symlink':
        (runtime / 'module000.py').unlink(); (runtime / 'module000.py').symlink_to('module001.py')
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'verify_source_export')(runtime, snapshot)


@pytest.fixture
def closure(tmp_path):
    """Exact lexical catalogue routes map to temporary fixture files only.

    The reader is an external filesystem boundary; identities/hashes/closure
    checks are production logic. No real catalogue or ordinary input is edited.
    """
    files = {}; rows = {}; current = {}
    for n in range(418):
        path = str(tmp_path / ('data%03d' % n) / ('state.json' if n == 0 else 'data.json'))
        raw = ('ordinary%d' % n).encode(); files[path] = raw
        rows[path] = dict(path=path, bytes=len(raw), sha256=digest(raw))
    for n, path in enumerate(CATALOGUES):
        raw = ('current catalogue%d' % n).encode(); files[path] = raw
        rows[path] = dict(path=path, bytes=1, sha256='0' * 64)  # historical provenance remains stale
        physical = '/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment' + path[len('/projects/beto/swong2/Alignment'):]
        current[path] = dict(virtual=path, physical=physical, bytes=len(raw), sha256=digest(raw))
        for label, cluster, route, when in [('delta_capture', 'delta', path, 1000.), ('remote', 'bridges2', physical, 1001.), ('delta_reread', 'delta', path, 1002.)]:
            current[path][label] = dict(cluster=cluster, path=route, bytes=len(raw), sha256=digest(raw), observed_unix=when)
    aliases = {str(tmp_path / ('alias%d' % n)): str(tmp_path / 'data000/state.json') for n in range(5)}
    for path, target in aliases.items(): Path(path).symlink_to(target)
    Path(next(iter(rows))).parent.mkdir(parents=True)
    Path(next(iter(rows))).write_bytes(files[next(iter(rows))])
    return dict(ordinary_files=rows, namespace_aliases=aliases), current, files


def test_exact_input_closure_uses_current_four_witnesses_and_preserves_history(closure):
    m = module('validate-phase'); manifest, current, files = closure
    original = copy.deepcopy(manifest)
    result = need(m, 'verify_input_closure')(manifest, current, read_bytes=lambda p: files[str(p)])
    assert result == dict(ordinary_count=422, immutable_original_count=418,
                          current_catalogue_count=4, alias_count=5)
    assert manifest == original, 'historical422 must never be re-signed'


@pytest.mark.parametrize('fault', ['ordinary-state-change', 'catalogue-change', 'missing-current',
                                  'extra-current', 'missing-input', 'changed-alias', 'missing-alias'])
def test_no_basename_exemption_or_implicit_alias_or_catalogue_adoption(closure, fault):
    m = module('validate-phase'); manifest, current, files = closure
    ordinary = next(p for p in files if p.endswith('/state.json'))
    if fault == 'ordinary-state-change': files[ordinary] += b'changed'
    elif fault == 'catalogue-change': files[CATALOGUES[0]] += b'changed'
    elif fault == 'missing-current': current.pop(CATALOGUES[0])
    elif fault == 'extra-current': current[ordinary] = current[CATALOGUES[0]]
    elif fault == 'missing-input': manifest['ordinary_files'].pop(ordinary)
    elif fault == 'changed-alias':
        alias = Path(next(iter(manifest['namespace_aliases']))); alias.unlink(); alias.symlink_to('absent')
    elif fault == 'missing-alias': Path(next(iter(manifest['namespace_aliases']))).unlink()
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'verify_input_closure')(manifest, current, read_bytes=lambda p: files[str(p)])


@pytest.fixture
def domain():
    # Synthetic full cardinality tests audit policy, not biological/scientific facts.
    rows = [('far', 'r%05d' % n, 'F', 'clean', 'far_seed1_DminusI', 'h_twin', None)
            for n in range(59652)]
    controls = [('far', 'far', 'c%04d' % n, 'D', 'clean') for n in range(3396)]
    mask = {key: (False, 'F has no H twin') if n == 0 else (True, None)
            for n, key in enumerate(rows)}
    # Reference digest follows proof181's published canonical mask layout.
    raw = json.dumps([[list(k), list(mask[k])] for k in sorted(mask)], separators=(',', ':'), ensure_ascii=True).encode()
    reference = dict(rows=59652, positive_controls=3396, reconstructed_rows=59652,
                     reconstructed_controls=3396, support_reason_mask_sha256=digest(raw))
    return rows, controls, mask, reference


def test_full_domain_preserves_legitimate_unsupported_reason(domain):
    m = module('validate-phase'); rows, controls, mask, reference = domain
    result = need(m, 'validate_domain_identity')(rows, controls, mask, controls, reference)
    assert result['rows'] == 59652 and result['positive_controls'] == 3396
    assert result['support_reason_mask_sha256'] == reference['support_reason_mask_sha256']
    assert mask[rows[0]] == (False, 'F has no H twin')


@pytest.mark.parametrize('fault', ['duplicate-row', 'wrong-row-same-count', 'missing-row', 'duplicate-control',
                                  'wrong-control-same-count', 'missing-control', 'reason', 'support', 'mask-key'])
def test_full_domain_rejects_count_preserving_identity_or_support_drift(domain, fault):
    m = module('validate-phase'); rows, controls, mask, reference = domain
    reconstructed_controls = list(controls)
    if fault == 'duplicate-row': rows[-1] = rows[0]
    elif fault == 'wrong-row-same-count': rows[-1] = ('wrong',) + rows[-1][1:]
    elif fault == 'missing-row': rows.pop()
    elif fault == 'duplicate-control': controls[-1] = controls[0]
    elif fault == 'wrong-control-same-count': reconstructed_controls[-1] = ('wrong',) + controls[-1][1:]
    elif fault == 'missing-control': controls.pop()
    elif fault == 'reason': mask[rows[0]] = (False, 'different reason')
    elif fault == 'support': mask[rows[0]] = (True, None)
    elif fault == 'mask-key': mask[('foreign',) + rows[-1][1:]] = mask.pop(rows[-1])
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_domain_identity')(rows, controls, mask, reconstructed_controls, reference)


def window():
    c = dict(phase='full_score', standing_CPU_job_id='123', packet_manifest_sha256='1' * 64,
             source_commit=SOURCE, frozen_G3_sha256='2' * 64, bank_file_sha256='3' * 64,
             bank_manifest_sha256='4' * 64, GPU_packet_manifest_sha256='5' * 64,
             child_cap_seconds=240, CPU_finish_margin_seconds=20, publication_margin_seconds=15)
    r = dict(phase='full_score', standing_CPU_job_id='123', standing_packet_manifest_sha256='1' * 64,
             accepted_source_commit=SOURCE, frozen_G3_sha256='2' * 64, bank_file_sha256='3' * 64,
             bank_manifest_sha256='4' * 64, GPU_packet_manifest_sha256='5' * 64,
             actual_future_GPU_job_id='456', final_GPU_bound_config_sha256='6' * 64,
             root_trigger_issued_at=1005.0, GPU_WAITING_requested_at=1000.0)
    waiting = dict(phase='full_score', job_id='456', source_commit=SOURCE,
                   bound_config_sha256='6' * 64, packet_manifest_sha256='5' * 64,
                   groups_file_sha256='2' * 64, bank_file_sha256='3' * 64,
                   bank_manifest_sha256='4' * 64, requested_at=1000.0, deadline_unix=1300.0)
    return c, r, waiting


def test_fresh_full_score_request_binds_actual_waiting_and_packet():
    m = module('supervisor'); c, r, waiting = window()
    result = need(m, 'validate_request')(c, r, waiting, now=1010.0)
    assert result['phase'] == 'full_score' and result['actual_future_GPU_job_id'] == '456'


@pytest.mark.parametrize('field,value', [('phase', 'prefix4'), ('standing_CPU_job_id', '999'),
    ('standing_packet_manifest_sha256', '0' * 64), ('accepted_source_commit', '0' * 40),
    ('frozen_G3_sha256', '0' * 64), ('bank_file_sha256', '0' * 64), ('bank_manifest_sha256', '0' * 64),
    ('GPU_packet_manifest_sha256', '0' * 64), ('actual_future_GPU_job_id', '999'),
    ('final_GPU_bound_config_sha256', '0' * 64), ('root_trigger_issued_at', 994.0),
    ('root_trigger_issued_at', 1011.0), ('GPU_WAITING_requested_at', 999.0)])
def test_stale_or_wrong_request_never_authorizes_cpu_child(field, value):
    m = module('supervisor'); c, r, waiting = window(); r[field] = value
    with pytest.raises((AssertionError, ValueError, TimeoutError)):
        need(m, 'validate_request')(c, r, waiting, now=1010.0)


@pytest.mark.parametrize('now,initial,current,cap,want', [
    (1010., 2000., 1900., 240., 1250.),
    (1010., 1200., 1900., 240., 1180.),
    (1010., 2000., 1150., 240., 1130.),
    (1010., 2000., 1900., 720., 1285.),
    (1010., 2000., 9999., 720., 1285.)])
def test_child_deadline_is_minimum_cpu_and_fixed_gpu_window(now, initial, current, cap, want):
    m = module('supervisor'); c, _, waiting = window(); c['child_cap_seconds'] = cap
    result = need(m, 'child_deadline')(c, waiting, initial_end=initial, current_end=current, now=now)
    assert result == want, '720s/historical CPU settings cannot override finite GPU publication window'


@pytest.mark.parametrize('fault', ['expired', 'extended-window', 'negative-margin', 'null-cap'])
def test_invalid_or_missed_window_fails_without_renewal(fault):
    m = module('supervisor'); c, _, waiting = window()
    if fault == 'extended-window': waiting['deadline_unix'] = 1720.0
    elif fault == 'negative-margin': c['publication_margin_seconds'] = -1
    elif fault == 'null-cap': c['child_cap_seconds'] = None
    with pytest.raises((AssertionError, ValueError, TimeoutError)):
        need(m, 'child_deadline')(c, waiting, initial_end=2000., current_end=1900.,
                                 now=1300. if fault == 'expired' else 1010.)


def completion():
    identities = dict(source='a', groups='b', bank='c', bank_manifest='d',
                      input_manifest='e', aliases={'alias': 'target'},
                      catalogues={name: str(n) for n, name in enumerate(CATALOGUES)})
    child = dict(exit_code=0, term_sent_at=None, started_unix=1010., finished_unix=1200.,
                 deadline_unix=1285., request_sha256='a' * 64, guard_result_sha256='b' * 64)
    result = dict(phase='full_score', complete=False, status='GUARDS_PASSED_AWAIT_SUPERVISOR',
                  source_commit=SOURCE, actual_CPU_job_id='123', actual_future_GPU_job_id='456',
                  request_sha256='a' * 64, rows=59652, positive_controls=3396,
                  source_before=copy.deepcopy(identities), source_after=copy.deepcopy(identities),
                  model_loaded=False, GPU_admitted=False, freeze_executed=False)
    return child, result


def test_cpu_complete_requires_normal_child_and_stable_exact_catalogues():
    m = module('supervisor'); c, r, _ = window(); child, result = completion()
    value = need(m, 'validate_child_completion')(c, r, child, result, now=1201.)
    assert value['complete'] is True and value['phase'] == 'full_score'
    assert result['complete'] is False, 'immutable child receipt is separate from supervisor COMPLETE'


@pytest.mark.parametrize('fault', ['term', 'exit', 'late-reaped-zero', 'at-deadline', 'partial',
                                  'old-phase', 'wrong-GPU', 'wrong-CPU', 'request-hash', 'wrong-rows',
                                  'wrong-controls', 'source', 'groups', 'bank', 'bank_manifest',
                                  'input_manifest', 'aliases', 'catalogues', 'missing-catalogue', 'model'])
def test_partial_mutated_terminated_or_late_child_cannot_be_complete(fault):
    m = module('supervisor'); c, r, _ = window(); child, result = completion(); now = 1201.
    if fault == 'term': child['term_sent_at'] = 1100.
    elif fault == 'exit': child['exit_code'] = 7
    elif fault == 'late-reaped-zero': child['finished_unix'] = 1286.; now = 1286.
    elif fault == 'at-deadline': now = child['deadline_unix']
    elif fault == 'partial': result['status'] = 'PARTIAL'
    elif fault == 'old-phase': result['phase'] = 'prefix4'
    elif fault == 'wrong-GPU': result['actual_future_GPU_job_id'] = '999'
    elif fault == 'wrong-CPU': result['actual_CPU_job_id'] = '999'
    elif fault == 'request-hash': result['request_sha256'] = '0' * 64
    elif fault == 'wrong-rows': result['rows'] = 2484
    elif fault == 'wrong-controls': result['positive_controls'] = 144
    elif fault == 'missing-catalogue':
        result['source_before']['catalogues'].pop(CATALOGUES[0]); result['source_after']['catalogues'].pop(CATALOGUES[0])
    elif fault == 'model': result['model_loaded'] = True
    else: result['source_after'][fault] = 'changed'
    with pytest.raises((AssertionError, ValueError, TimeoutError)):
        need(m, 'validate_child_completion')(c, r, child, result, now=now)


def test_relocated_cpu_wrapper_uses_absolute_packet(tmp_path):
    wrapper = CPU / 'launch.sh'
    assert wrapper.is_file(), MISSING + ': ' + str(wrapper)
    moved = tmp_path / 'spool/slurm_script'; moved.parent.mkdir(); moved.write_bytes(wrapper.read_bytes())
    bindir = tmp_path / 'bin'; bindir.mkdir(); capture = tmp_path / 'captured.json'
    interceptor = '#!' + sys.executable + '\nimport json,os,sys\nopen(os.environ["CAPTURE"],"w").write(json.dumps(sys.argv[1:]))\n'
    for name in ('python3', 'python'):
        path = bindir / name; path.write_text(interceptor); path.chmod(0o755)
    done = subprocess.run(['bash', str(moved), '--config', 'unbound', '--config-sha256', '0' * 64],
        env=dict(os.environ, PATH=str(bindir) + ':' + os.environ['PATH'], CAPTURE=str(capture),
                 A2_FULL_SCORE_CPU_PACKET=str(CPU)), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    assert done.returncode == 0, done.stderr.decode()
    assert json.loads(capture.read_text()) == [str(CPU / 'supervisor.py'), '--config', 'unbound', '--config-sha256', '0' * 64]


@pytest.mark.parametrize('fault', [None, 'request', 'marker'])
def test_request_and_actual_waiting_bytes_are_immutable(tmp_path, fault):
    m = module('supervisor')
    request = tmp_path / 'request.json'; marker = tmp_path / 'WAITING.json'
    request.write_bytes(b'{"phase":"full_score"}\n'); marker.write_bytes(b'{"job_id":"456"}\n')
    request_sha, marker_sha = digest(request.read_bytes()), digest(marker.read_bytes())
    if fault == 'request': request.write_bytes(b'{"phase":"prefix4"}\n')
    elif fault == 'marker': marker.write_bytes(b'{"job_id":"999"}\n')
    function = need(m, 'verify_request_files')
    if fault:
        with pytest.raises((AssertionError, ValueError)):
            function(request, request_sha, marker, marker_sha)
    else:
        observed = function(request, request_sha, marker, marker_sha)
        assert observed['request_sha256'] == request_sha and observed['marker_sha256'] == marker_sha


@pytest.mark.parametrize('now,exit_code', [(1200., 0), (1285., 0), (1286., 0), (1200., 7)])
def test_reaped_child_is_checked_against_clock_before_promotion(monkeypatch, now, exit_code):
    m = module('supervisor')
    class Child:
        pid = 42
        returncode = exit_code
        def poll(self): return self.returncode
        def wait(self, timeout=None): return self.returncode
    monkeypatch.setattr(m.time, 'time', lambda: now)
    function = need(m, 'observe_child')
    if now >= 1285. or exit_code:
        with pytest.raises((AssertionError, ValueError, RuntimeError, TimeoutError)):
            function(Child(), deadline=1285., recheck=lambda: 1285.)
    else:
        observed = function(Child(), deadline=1285., recheck=lambda: 1285.)
        assert observed['exit_code'] == 0 and observed['term_sent_at'] is None
        assert observed['finished_unix'] < observed['deadline_unix']


@pytest.mark.parametrize('fault', [None, 'wrong-job', 'wrong-packet', 'missing-route', 'extra-route',
                                  'wrong-physical', 'wrong-role-count', 'remote-hash', 'out-of-order',
                                  'historical-instead-current', 'witness-bytes', 'duplicate-key'])
def test_current_catalogue_witness_is_fresh_job_packet_bound_and_same_buffer(closure, tmp_path, fault):
    m = module('validate-phase'); _, current, _ = closure
    witness = dict(complete=True, adapter_manifest_sha256='1' * 64, actual_job_id='123',
                   source_files=511, ordinary_inputs=422, immutable_original_inputs=418,
                   current_catalogue_inputs=4, literal_source_links=4,
                   catalogues_are_snapshots_not_continuous_Delta=True, current_catalogues=current)
    if fault == 'wrong-job': witness['actual_job_id'] = '999'
    elif fault == 'wrong-packet': witness['adapter_manifest_sha256'] = '0' * 64
    elif fault == 'missing-route': current.pop(CATALOGUES[0])
    elif fault == 'extra-route': current['/unrelated/directions.json'] = copy.deepcopy(current[CATALOGUES[0]])
    elif fault == 'wrong-physical': current[CATALOGUES[0]]['physical'] = '/other/place'
    elif fault == 'wrong-role-count': witness['immutable_original_inputs'] = 417
    elif fault == 'remote-hash': current[CATALOGUES[0]]['remote']['sha256'] = '0' * 64
    elif fault == 'out-of-order': current[CATALOGUES[0]]['delta_reread']['observed_unix'] = 999.
    elif fault == 'historical-instead-current': witness['complete'] = False
    path = tmp_path / 'witness.json'; raw = canon(witness)
    if fault == 'duplicate-key': raw = b'{"complete":false,' + raw[1:]
    path.write_bytes(raw); ref = dict(path=str(path), sha256=digest(raw))
    if fault == 'witness-bytes': path.write_bytes(raw + b' ')
    function = need(m, 'catalogue_expectations')
    if fault:
        with pytest.raises((AssertionError, ValueError)):
            function(ref, '1' * 64, '123')
    else:
        assert function(ref, '1' * 64, '123') == current
