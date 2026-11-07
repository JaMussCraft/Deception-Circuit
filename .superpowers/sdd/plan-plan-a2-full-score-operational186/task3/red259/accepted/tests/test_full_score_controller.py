"""T1 behavioral contracts. Missing implementation fails in bodies, never collection.

No torch/model/native loader import. External boundaries are fake process and
clock/allocation observations; filesystem hashes, config and policy stay real.
"""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile

import pytest

SDD = Path(__file__).resolve().parents[3]
PACKET = SDD / 'plan-plan-a2-full-score-operational186/task1'
GPU = Path(__file__).resolve().parents[1] / 'gpu'
W = '/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder'
S = W + '/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
MAIN = W + '/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
COMMIT = '50e947bb852613e3a270082651f2bd1b7bb0c525'
NAME = 'NVIDIA H100 80GB HBM3'
MISSING = 'FULL_SCORE_IMPLEMENTATION_MISSING'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    return str(path)


def require_module(name, monkeypatch, c):
    """Assertion deliberately occurs only when an individual test executes."""
    path = GPU / (name + '.py')
    assert path.is_file(), MISSING + ': ' + str(path)
    config = Path(c['evidence_root']) / 'bound-config.json'
    save(config, c)
    monkeypatch.setenv('A2_FULL_SCORE_BOUND_CONFIG', str(config))
    monkeypatch.setenv('A2_FULL_SCORE_BOUND_CONFIG_SHA256', sha(config))
    monkeypatch.setenv('A2_FULL_SCORE_EXECUTION_OUTPUT', c['evidence_root'])
    monkeypatch.setenv('A2_FULL_SCORE_RELEASE_DIRECTORY', c['release_directory'])
    monkeypatch.setenv('A2_FULL_SCORE_INITIAL_END_EPOCH', '10000')
    monkeypatch.setenv('A2_FULL_SCORE_FIXED_END_EPOCH', '9000')
    monkeypatch.setenv('SLURM_JOB_ID', c['actual_job_id'])
    monkeypatch.syspath_prepend(str(GPU))
    # Common is configuration-bound; isolate each fixture's module globals.
    sys.modules.pop('common', None)
    spec = importlib.util.spec_from_file_location('t1_' + name.replace('-', '_'), str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def need(module, name):
    value = getattr(module, name, None)
    assert callable(value), MISSING + ': callable ' + name
    return value


@pytest.fixture
def c(tmp_path):
    # Fixture is prospective, deliberately not a real bound/admitted config.
    value = json.loads((PACKET / 'fixtures/config.json').read_text())
    value['main_root'] = str(tmp_path / 'MAIN')
    value['evidence_root'] = str(tmp_path / 'evidence')
    value['release_directory'] = str(tmp_path / 'releases')
    for key in ('main_root', 'evidence_root', 'release_directory'):
        Path(value[key]).mkdir()
    bank = Path(value['main_root']) / 'bank'
    bank.mkdir()
    for filename in ('banks.json', 'run_manifest.json'):
        (bank / filename).write_bytes((PACKET / 'fixtures' / filename).read_bytes())
    (Path(value['main_root']) / 'groups.json').write_bytes(b'fixture-G3\n')
    value.update(bank_file=str(bank / 'banks.json'), bank_manifest=str(bank / 'run_manifest.json'),
                 bank_file_sha256=sha(bank / 'banks.json'), bank_manifest_sha256=sha(bank / 'run_manifest.json'),
                 groups=str(Path(value['main_root']) / 'groups.json'), groups_file_sha256=sha(Path(value['main_root']) / 'groups.json'))
    for key in ('packet_manifest', 'snapshot', 'input_manifest', 'model_cache_proof',
                'resource_proof', 'capacity_proof', 'mapping_origin', 'operational_admission',
                'protection_proof', 'image', 'delta_G3_receipt', 'bridges_G3_receipt'):
        value[key] = save(tmp_path / 'refs' / (key + '.json'), {'fixture': key, 'complete': True})
        value[key + '_sha256'] = sha(value[key])
    value['launch_packet_manifest_sha256'] = value['packet_manifest_sha256']
    return value


def release(c):
    value = dict(phase='full_score', actual_job_id=c['actual_job_id'], source_commit=COMMIT,
                 issued_at=1000.0, expires_at=1300.0, full_scoring_admitted=True,
                 bound_config_sha256=sha(Path(c['evidence_root']) / 'bound-config.json'), main_root=c['main_root'],
                 catalogues=[], minimum_entry_seconds=c['resources']['minimum_entry_seconds'])
    value.update({key: copy.deepcopy(item) for key, item in c.items() if key.endswith('_sha256')})
    value['resources'] = copy.deepcopy(c['resources'])
    value['_release_path'] = save(Path(c['release_directory']) / (c['actual_job_id'] + '-full_score.json'), value)
    value['_release_sha256'] = sha(value['_release_path'])
    return value


def common(c, monkeypatch):
    return require_module('common', monkeypatch, c)


def test_config_accepts_only_complete_reviewed_full_score(c, monkeypatch):
    m = common(c, monkeypatch)
    checked = need(m, 'validate_config')(c)
    assert checked['phase'] == 'full_score'
    assert checked['resources']['GPU_count'] == 1


@pytest.mark.parametrize('phase', ['bank', 'prefix4', 'score', 'summarize', '', None])
def test_old_timing_authority_cannot_enter_full_score(c, monkeypatch, phase):
    m = common(c, monkeypatch)
    c['phase'] = phase
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_config')(c)


@pytest.mark.parametrize('field', ['duration_seconds', 'CPUs', 'RAM_bytes', 'GPU_count',
                                  'minimum_entry_seconds', 'finish_margin_seconds', 'child_cap_seconds'])
def test_each_unbound_resource_blocks_execution(c, monkeypatch, field):
    m = common(c, monkeypatch)
    c['resources'][field] = None
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_config')(c)


@pytest.mark.parametrize('field', ['actual_job_id', 'reservation_id', 'packet_manifest_sha256',
                                  'bank_file_sha256', 'bank_manifest_sha256', 'resource_proof_sha256',
                                  'capacity_proof_sha256', 'input_manifest_sha256', 'model_cache_proof_sha256',
                                  'image_sha256', 'mapping_origin_sha256', 'operational_admission_sha256'])
def test_missing_identity_or_review_reference_blocks_execution(c, monkeypatch, field):
    m = common(c, monkeypatch)
    del c[field]
    with pytest.raises((AssertionError, ValueError, KeyError)):
        need(m, 'validate_config')(c)


@pytest.mark.parametrize('patch', [
    {'bank_and_prefix4_only': True}, {'independent160_accepted': True},
    {'full_scoring_admitted': False}, {'unknown_authority': True}, {'pilot_root': MAIN + '-timing-limit4'},
])
def test_closed_config_rejects_old_flags_and_unexpected_fields(c, monkeypatch, patch):
    m = common(c, monkeypatch)
    c.update(patch)
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_config')(c)


@pytest.mark.parametrize('seconds', [3600, 17100])
def test_old_one_hour_and_provisional_475h_are_not_resource_proofs(c, monkeypatch, seconds):
    m = common(c, monkeypatch)
    c['resources']['duration_seconds'] = seconds
    c['resource_proof_sha256'] = None
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_config')(c)


def test_existing_bank_identity_is_observed_without_resigning(c, monkeypatch):
    m = common(c, monkeypatch)
    before = {p.name: p.read_bytes() for p in Path(c['bank_file']).parent.iterdir()}
    result = need(m, 'verify_existing_bank')(c)
    assert result['bank_file_sha256'] == c['bank_file_sha256']
    assert result['bank_manifest_sha256'] == c['bank_manifest_sha256']
    assert result['bank_internal_payload_sha256'] == c['bank_internal_payload_sha256']
    assert before == {p.name: p.read_bytes() for p in Path(c['bank_file']).parent.iterdir()}


@pytest.mark.parametrize('target', ['bank_file', 'bank_manifest', 'groups'])
def test_stale_bank_manifest_or_G3_rejected_without_adopting_bytes(c, monkeypatch, target):
    m = common(c, monkeypatch)
    Path(c[target]).write_bytes(Path(c[target]).read_bytes() + b' ')
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'verify_existing_bank')(c)


@pytest.mark.parametrize('symlink', [False, True])
def test_existing_or_dangling_symlink_score_rejects(c, monkeypatch, symlink):
    m = common(c, monkeypatch)
    score = Path(c['main_root']) / 'score'
    if symlink:
        score.symlink_to(Path(c['main_root']) / 'absent-score')
    else:
        score.mkdir()
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'verify_existing_bank')(c)


def test_full_score_argv_is_original_single_entry(c, monkeypatch):
    m = common(c, monkeypatch)
    c['main_root'] = MAIN
    assert need(m, 'full_score_command')(c) == [
        'bash', S + '/scripts/jobs/specificity_a2.sh', '--design',
        W + '/outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json', '--selected',
        W + '/outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json', '--commit', COMMIT,
        '--batch-size', '8', '--registry', W + '/docs/research/held_out.json', '--stage', 'score', '--work-dir', MAIN]


@pytest.mark.parametrize('suffix', [['--limit', '0'], ['--limit', '4'], ['--limit=0'],
                                  ['--stage', 'bank'], ['--stage', 'summarize'], ['--model-loader', 'fake']])
def test_external_argv_policy_rejects_limit_and_alternate_stage(c, monkeypatch, suffix):
    m = common(c, monkeypatch)
    command = need(m, 'full_score_command')(c) + suffix
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_score_command')(c, command)


def probe(c):
    return dict(gpu_name=NAME, gpu_uuid='GPU-new-job', device='cuda:0', dtype='torch.bfloat16',
                numeric_environment=copy.deepcopy(c['bank_numeric_environment']),
                total_memory_bytes=84900610048, free_memory_bytes=80000000000,
                compute_capability=[9, 0], no_model_loaded=True)


def test_changed_uuid_preserves_bank_contract(c, monkeypatch):
    m = common(c, monkeypatch)
    result = need(m, 'validate_gpu_identity')(c, probe(c))
    assert result['bank_gpu_uuid'] == 'GPU-old-bank-job'
    assert result['actual_gpu_uuid'] == 'GPU-new-job'


@pytest.mark.parametrize('key,value', [('gpu_name', 'NVIDIA H100 PCIe'), ('device', 'cpu'),
                                      ('dtype', 'torch.float16'), ('gpu_name', 'NVIDIA H100 80GB HBM3 MIG 1g')])
def test_matching_H100_label_cannot_hide_wrong_numeric_identity(c, monkeypatch, key, value):
    m = common(c, monkeypatch)
    p = probe(c)
    p[key] = value
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_gpu_identity')(c, p)


def test_bank_numeric_environment_is_exact(c, monkeypatch):
    m = common(c, monkeypatch)
    p = probe(c)
    p['numeric_environment']['cuda_matmul_allow_tf32'] = True
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'validate_gpu_identity')(c, p)


def test_postactivation_environment_keeps_original_offline_namespaces(c, monkeypatch):
    m = common(c, monkeypatch)
    env = need(m, 'environment')()
    expected = dict(DC_CLUSTER='bridges2', DC_B2_ALLOC='cis260361p', DC_PYTHON=c['python'],
                    DC_RUN_MANIFEST_GIT='0', PYTHONPATH=S, PYTHONDONTWRITEBYTECODE='1',
                    HF_HOME='/ocean/projects/cis260361p/swong2/hf', HF_HUB_CACHE='/work/nvme/beto/swong2',
                    TRANSFORMERS_CACHE='/work/nvme/beto/swong2', HF_HUB_OFFLINE='1',
                    TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1', WANDB_MODE='disabled',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    assert {key: env.get(key) for key in expected} == expected


def test_effective_deadlines_shorten_after_costly_checks_and_never_extend(c, monkeypatch):
    m = common(c, monkeypatch)
    calc = need(m, 'effective_deadlines')
    # min(initial=4000,current=3500,fixed=3900), minus reviewed reserve=120.
    first = calc(c, initial_end=4000, current_end=3500, fixed_end=3900, now=1000)
    assert first == {'run_deadline': 3500, 'work_deadline': 3380, 'remaining_work_seconds': 2380}
    late = calc(c, initial_end=4000, current_end=3200, fixed_end=3900, now=3100)
    assert late == {'run_deadline': 3200, 'work_deadline': 3080, 'remaining_work_seconds': -20}
    extension = calc(c, initial_end=4000, current_end=9000, fixed_end=3900, now=3100)
    assert extension['run_deadline'] == 3900


def test_entry_release_is_once_only(c, monkeypatch):
    m = common(c, monkeypatch)
    r = release(c)
    monkeypatch.setattr(m.time, 'time', lambda: 1100.0)
    # Only external/allocation observation is replaced; release hash/consume real.
    monkeypatch.setattr(m, 'allocation', lambda **kw: {'facts': {'EndTime': '2099-01-01T00:00:00'}})
    need(m, 'entry_release')(r, 'full_score')
    with pytest.raises((AssertionError, ValueError, FileExistsError)):
        m.entry_release(r, 'full_score')


def test_late_release_mutation_before_first_entry_rejects(c, monkeypatch):
    m = common(c, monkeypatch)
    r = release(c)
    monkeypatch.setattr(m.time, 'time', lambda: 1100.0)
    Path(r['_release_path']).write_text('{}')
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'entry_release')(r, 'full_score')
    assert not list(Path(c['evidence_root']).glob('CONSUMED*'))


@pytest.mark.parametrize('phase', ['bank', 'prefix4', 'summarize'])
def test_release_wait_only_supports_full_score(c, monkeypatch, phase):
    m = common(c, monkeypatch)
    with pytest.raises((AssertionError, ValueError)):
        need(m, 'gpu_release')(phase)
    assert list(Path(c['release_directory']).iterdir()) == []


def test_atomic_score_mount_policy(c, monkeypatch, tmp_path):
    host = require_module('host-launch', monkeypatch, c)
    c['physical_Alignment_root'] = str(tmp_path / 'physical/Alignment')
    c['virtual_Alignment_root'] = '/projects/beto/swong2/Alignment'
    c['main_root'] = c['virtual_Alignment_root'] + '/MAIN'
    physical_main = Path(c['physical_Alignment_root']) / 'MAIN'
    physical_main.mkdir(parents=True)
    (physical_main / 'bank').mkdir()
    (physical_main / 'bank/banks.json').write_text('immutable')
    (physical_main / 'groups.json').write_text('G3')
    (physical_main / 'existing-metadata.json').write_text('protected')
    command = need(host, 'build_container_command')(c, {})
    binds = [command[i + 1] for i, arg in enumerate(command) if arg == '--bind']
    assert c['physical_Alignment_root'] + ':' + c['virtual_Alignment_root'] + ':ro' in binds
    assert str(physical_main) + ':' + c['main_root'] + ':rw' in binds
    for leaf in ('bank', 'groups.json', 'existing-metadata.json'):
        assert str(physical_main / leaf) + ':' + c['main_root'] + '/' + leaf + ':ro' in binds
    assert not any(x.endswith(':rw') and x.split(':')[1] == c['virtual_Alignment_root'] for x in binds)
    assert not any(x.split(':')[1] == c['main_root'] + '/score' for x in binds)
    assert c['physical_HF_cache'] + ':/work/nvme/beto/swong2:ro' in binds
    assert '--writable-tmpfs' in command
    # Native publication creates MAIN/.score-*/ then rename to MAIN/score;
    # parent binding, rather than absent leaf binding, must accommodate both.
    assert not (physical_main / 'score').exists()
    # Execute the actual pinned native publisher's two stdlib functions in
    # isolation; this is not an invented imitation of its temporary behavior.
    native = Path(S) / 'dataset/user_inversion_pipeline.py'
    tree = ast.parse(native.read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('require', 'publish')]
    namespace = dict(Path=Path, tempfile=tempfile, shutil=shutil)
    isolated = ast.Module(body=functions, type_ignores=[])
    exec(compile(ast.fix_missing_locations(isolated), str(native), 'exec'), namespace)
    before = (physical_main / 'bank/banks.json').read_bytes()
    def writer(directory):
        assert directory.parent == physical_main
        assert directory.name.startswith('.score-')
        assert not (physical_main / 'score').exists()
        (directory / 'run_manifest.json').write_text('fixture-only')
    namespace['publish'](physical_main / 'score', writer)
    assert (physical_main / 'score/run_manifest.json').read_text() == 'fixture-only'
    assert (physical_main / 'bank/banks.json').read_bytes() == before


def allocation_capture(c):
    facts = dict(JobId=c['actual_job_id'], JobState='RUNNING', Account=c['expected_account'],
                 Partition='GPU-shared', QOS=c['expected_qos'], Requeue='0', Restarts='0',
                 NumCPUs='2', NumNodes='1', TimeLimit='02:00:00', NodeList='fixture-host',
                 EndTime='2099-01-01T00:00:00', AllocTRES='cpu=2,mem=32G,node=1,gres/gpu=1,gres/gpu:h100-80=1',
                 TresPerNode='gres:gpu:h100-80:1')
    return dict(actual_job_id=c['actual_job_id'], host='fixture-host', actual_hostnames=['fixture-host'],
                raw_scontrol=' '.join(key + '=' + value for key, value in facts.items()),
                fields=facts, captured_unix=1000.0)


def test_allocation_matches_reviewed_tuple_instead_of_historical_defaults(c, monkeypatch):
    host = require_module('host-launch', monkeypatch, c)
    monkeypatch.setattr(host.time, 'time', lambda: 1001.0)
    monkeypatch.setattr(host.socket, 'gethostname', lambda: 'fixture-host')
    result = need(host, 'validate_allocation')(c, allocation_capture(c))
    assert result['facts']['NumCPUs'] == '2'
    assert result['facts']['TimeLimit'] == '02:00:00'


@pytest.mark.parametrize('field,value', [
    ('JobState', 'PENDING'), ('Account', 'wrong'), ('QOS', 'wrong'), ('Requeue', '1'),
    ('Restarts', '1'), ('NumCPUs', '4'), ('TimeLimit', '01:00:00'),
    ('AllocTRES', 'cpu=2,mem=32G,node=1,gres/gpu=1'),
    ('AllocTRES', 'cpu=2,mem=32G,node=1,gres/gpu=2,gres/gpu:h100-80=2'),
    ('AllocTRES', 'cpu=2,mem=1G,node=1,gres/gpu=1,gres/gpu:h100-80=1')])
def test_bad_actual_allocation_blocks_entry(c, monkeypatch, field, value):
    host = require_module('host-launch', monkeypatch, c)
    monkeypatch.setattr(host.time, 'time', lambda: 1001.0)
    monkeypatch.setattr(host.socket, 'gethostname', lambda: 'fixture-host')
    captured = allocation_capture(c)
    captured['fields'][field] = value
    # Keep raw/facts self-consistent: rejection must be the unsafe resource,
    # not accidentally a malformed duplicate representation.
    if field == 'AllocTRES' and 'h100-80' not in value:
        captured['fields']['TresPerNode'] = 'gres:gpu:1'
    captured['raw_scontrol'] = ' '.join(key + '=' + item for key, item in captured['fields'].items())
    with pytest.raises((AssertionError, ValueError)):
        need(host, 'validate_allocation')(c, captured)


def test_timeout_escalation_kills_and_reaps_group_without_retry(c, monkeypatch):
    controller = require_module('controller', monkeypatch, c)
    events = []
    class StubbornChild:
        pid = 321
        returncode = None
        def poll(self):
            return self.returncode
        def wait(self, timeout=None):
            events.append(('wait', timeout))
            if len([x for x in events if x[0] == 'wait']) == 1:
                raise subprocess.TimeoutExpired('fixture-child', timeout)
            self.returncode = -9
            return self.returncode
    monkeypatch.setattr(controller.os, 'killpg', lambda pid, sig: events.append(('killpg', pid, sig)))
    need(controller, 'terminate_process_group')(StubbornChild(), timeout_seconds=10)
    assert events == [('killpg', 321, controller.signal.SIGTERM), ('wait', 10),
                      ('killpg', 321, controller.signal.SIGKILL), ('wait', 10)]


@pytest.mark.parametrize('fault', ['bad-bank', 'bad-G3', 'score-exists', 'old-phase', 'unbound-resource', 'expired-release'])
def test_preentry_rejection_makes_zero_cli_processes(c, monkeypatch, fault):
    controller = require_module('controller', monkeypatch, c)
    calls = []
    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError('original CLI entered despite failed pre-entry guard')
    monkeypatch.setattr(controller.subprocess, 'Popen', forbidden)
    r = release(c)
    if fault == 'bad-bank': Path(c['bank_file']).write_text('{}')
    elif fault == 'bad-G3': Path(c['groups']).write_text('changed')
    elif fault == 'score-exists': (Path(c['main_root']) / 'score').mkdir()
    elif fault == 'old-phase': c['phase'] = 'prefix4'
    elif fault == 'unbound-resource': c['resources']['duration_seconds'] = None
    elif fault == 'expired-release': r['issued_at'], r['expires_at'] = -1000.0, -700.0
    with pytest.raises((AssertionError, ValueError, TimeoutError)):
        need(controller, 'run_full_score')(c, r)
    assert calls == [], 'rejected entry must never start original CLI'


@pytest.mark.parametrize('child_code', [0, 7])
def test_one_original_cli_after_costly_checks_and_final_entry_no_retry(c, monkeypatch, child_code):
    controller = require_module('controller', monkeypatch, c)
    events = []
    monkeypatch.setattr(controller.time, 'time', lambda: 1100.0)
    # These are external owning checks, exercised by the other unit/native
    # suites. Keep the runner's entry, process command and retry policy real.
    def preflight(config, acquired):
        events.extend(['packet/source/bank/input/cache/protection/budget/allocation', 'activation/imports/GPU-probe'])
        return dict(environment={'PYTHONPATH': S}, work_deadline=2000.0,
                    bank_before={'bank_file_sha256': c['bank_file_sha256']}, source_before={'source_commit': COMMIT})
    def entry(acquired, phase):
        assert events[-1] == 'activation/imports/GPU-probe'
        assert phase == 'full_score'
        events.append('final-entry')
    def popen(command, **kwargs):
        assert events[-1] == 'final-entry'
        assert kwargs['cwd'] == c['runtime'] or str(kwargs['cwd']) == c['runtime']
        assert kwargs['start_new_session'] is True
        assert kwargs['env']['PYTHONPATH'] == S
        assert command == ['bash', S + '/scripts/jobs/specificity_a2.sh', '--design', c['a1_design'],
                           '--selected', c['a1_selected'], '--commit', COMMIT, '--batch-size', '8',
                           '--registry', c['registry'], '--stage', 'score', '--work-dir', c['main_root']]
        events.append('Popen')
        class Child:
            pid = 456
            returncode = None
            def wait(self, timeout=None):
                assert 0 < timeout <= 900
                self.returncode = child_code
                return child_code
            def poll(self):
                return self.returncode
        return Child()
    def audit(config):
        assert child_code == 0
        events.append('native-completion-audit')
        return dict(complete=True, counts={'rows': 59652, 'expected': 59652, 'positive_controls': 3396},
                    domain_audit={'complete': True}, support_mask_audit={'complete': True})
    for name, function in [('preflight_full_score', preflight), ('entry_release', entry), ('audit_score_result', audit)]:
        need(controller, name)
        monkeypatch.setattr(controller, name, function)
    monkeypatch.setattr(controller.subprocess, 'Popen', popen)
    if child_code:
        with pytest.raises((AssertionError, ValueError, RuntimeError)):
            need(controller, 'run_full_score')(c, release(c))
        assert 'native-completion-audit' not in events
    else:
        result = need(controller, 'run_full_score')(c, release(c))
        assert result['exit_code'] == 0
        assert events[-1] == 'native-completion-audit'
    assert events.count('Popen') == 1


def test_costly_preflight_cannot_leave_stale_work_timeout_for_cli(c, monkeypatch):
    controller = require_module('controller', monkeypatch, c)
    calls = []
    monkeypatch.setattr(controller.time, 'time', lambda: 1100.0)
    need(controller, 'preflight_full_score')
    monkeypatch.setattr(controller, 'preflight_full_score', lambda config, r:
                        dict(environment={'PYTHONPATH': S}, work_deadline=1099.0))
    need(controller, 'entry_release')
    monkeypatch.setattr(controller, 'entry_release', lambda r, phase: None)
    monkeypatch.setattr(controller.subprocess, 'Popen', lambda *a, **kw: calls.append((a, kw)))
    with pytest.raises((AssertionError, ValueError, TimeoutError)):
        need(controller, 'run_full_score')(c, release(c))
    assert calls == [], 'remaining work must be recomputed after preflight'


def test_relocated_launch_wrapper_resolves_absolute_packet(c, monkeypatch, tmp_path):
    wrapper = GPU / 'launch.sh'
    assert wrapper.is_file(), MISSING + ': ' + str(wrapper)
    moved = tmp_path / 'slurm-spool' / 'slurm_script'
    moved.parent.mkdir()
    moved.write_bytes(wrapper.read_bytes())
    binpath = tmp_path / 'bin'
    binpath.mkdir()
    capture = tmp_path / 'captured.json'
    interceptor = '#!' + sys.executable + '\nimport json,os,sys\nopen(os.environ["CAPTURE"],"w").write(json.dumps(sys.argv[1:]))\n'
    for name in ('python3', 'python'):
        p = binpath / name
        p.write_text(interceptor)
        p.chmod(0o755)
    env = dict(os.environ, PATH=str(binpath) + ':' + os.environ['PATH'], CAPTURE=str(capture),
               SLURM_JOB_ID=c['actual_job_id'], A2_FULL_SCORE_PACKET=str(GPU))
    done = subprocess.run(['bash', str(moved)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    assert done.returncode == 0, done.stderr.decode()
    assert json.loads(capture.read_text()) == [str(GPU / 'host-launch.py')]
