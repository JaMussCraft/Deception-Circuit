"""CPU-only contract tests; never import the model/training stack."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import twin_training as tw


@pytest.fixture
def inputs(tmp_path):
    config = json.loads((Path(__file__).parents[1]/'scripts/jobs/specificity_ladder_a2.json').read_text())
    config.update(data_root=str(tmp_path/'data'), output_root=str(tmp_path/'runs'))
    ids = {s: [s+str(i) for i in range(n)] for s, n in [('train', 205), ('validation', 3), ('test', 4)]}
    manifest = dict(cohort='matched', fleet_ready=True, source_commit='a'*40,
                    max_seq_length=120, build_hash='b'*64,
                    tasks={'far_v2': dict(split_ids=ids, counts={s: len(v) for s, v in ids.items()})})
    return config, manifest


def command(inputs, **kwargs):
    return tw.build_command(*inputs, task='far_v2', condition=kwargs.pop('condition', 'D'),
                            seed=kwargs.pop('seed', 42), timing_epochs=kwargs.pop('timing_epochs', None), **kwargs)


def test_frozen_exact_command_and_selected_ids(inputs):
    config, manifest = inputs
    argv = command(inputs)
    assert argv[:3] == [sys.executable, str(tw.REPO/'train.py'), '--model']
    pairs = {'--model': 'llama-8b-instruct', '--task': 'far_v2', '--deception-condition': 'deceptive',
             '--data-dir': config['data_root']+'/D', '--node-lambda-sparsity': '0.3', '--node-epochs': '500',
             '--lr': '0.03', '--batch-size': '7', '--faithfulness-weight': '1', '--train-samples': '200',
             '--val-samples': '3', '--test-samples': '4', '--max-seq-length': '120', '--seed': '42'}
    for flag, value in pairs.items():
        assert argv[argv.index(flag)+1] == value
    assert set(tw.GATE_FLAGS).issubset(argv)
    assert not any('runtime-filter' in a for a in argv)
    provenance = tw.plan_run(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=None)
    assert provenance['selected_ids']['train'] == manifest['tasks']['far_v2']['split_ids']['train'][:200]
    assert provenance['purpose'] == 'scientific-seed'
    assert provenance['recipient_condition'] == 'deceptive'
    assert provenance['legacy_deception_condition'] == 'deceptive'
    other = command(inputs, seed=1)
    assert {i for i, (a,b) in enumerate(zip(argv, other)) if a != b} == {argv.index('--seed')+1, argv.index('--output-dir')+1}


def test_timing_only_provisional_and_production_gate(inputs):
    config, manifest = inputs
    manifest.update(cohort='timing-d-only', fleet_ready=False)
    with pytest.raises(ValueError, match='fleet_ready'):
        command(inputs)
    argv = command(inputs, timing_epochs=20)
    assert argv[argv.index('--node-epochs')+1] == '20'
    plan = tw.plan_run(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=20)
    assert (plan['purpose'], plan['planned_epochs'], plan['actual_epochs'], plan['fleet_ready']) == ('timing-only', 500, 20, False)
    with pytest.raises(ValueError):
        command(inputs, condition='I', timing_epochs=20)


@pytest.mark.parametrize('mutation', ['seed', 'length', 'ids', 'counts', 'config', 'commit'])
def test_rejects_invalid_plan(inputs, mutation):
    config, manifest = inputs
    kwargs = {}
    if mutation == 'seed': kwargs['seed'] = 2
    if mutation == 'length': manifest['max_seq_length'] = 0
    if mutation == 'ids': manifest['tasks']['far_v2']['split_ids']['train'][1] = 'train0'
    if mutation == 'counts': manifest['tasks']['far_v2']['counts']['train'] = 999
    if mutation == 'config': config['batch_size'] = 8
    if mutation == 'commit': manifest['source_commit'] = 'short'
    with pytest.raises(ValueError): command(inputs, **kwargs)


def fake_child(tmp_path, argv, *, missing=None, fail=False, mismatch=False):
    """A real short Python child writes the same artifact shapes as train.py."""
    out = Path(argv[argv.index('--output-dir')+1])
    cfg = tw.expected_config(argv)
    if mismatch: cfg['batch_size'] = 99
    code = ['import json, pathlib', 'out=pathlib.Path('+repr(str(out))+')', 'out.mkdir(parents=True)']
    artifacts = {'config.json': cfg, 'active_nodes.json': {'0': [1]}, 'results.json': {'node_eval': {}},
                 'history.json': {'node': [1]}, 'run_manifest.json': {'git_fingerprint_error': 'disabled'}}
    for name, data in artifacts.items():
        if name != missing:
            code.append('(out/'+repr(name)+').write_text('+repr(json.dumps(data))+')')
    code.extend(['print("Node pruning time: 600.0s")', 'raise SystemExit('+str(3 if fail else 0)+')'])
    child = tmp_path/'fake_child.py'
    child.write_text('\n'.join(code))
    def execute(command, **kwargs):
        return subprocess.run([sys.executable, str(child)], **kwargs)
    return execute


@pytest.mark.parametrize('case', ['success', 'failure', 'missing', 'mismatch', 'stale'])
def test_run_receipts_and_whole_process_clock(inputs, tmp_path, case):
    config, manifest = inputs
    argv = command(inputs, timing_epochs=20)
    plan = tw.plan_run(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=20)
    execute = fake_child(tmp_path, argv, missing='history.json' if case == 'missing' else None,
                         fail=case == 'failure', mismatch=case == 'mismatch')
    out = Path(argv[argv.index('--output-dir')+1])
    if case == 'stale': out.mkdir(parents=True)
    ticks = iter([10., 1210.])
    receipt = tw.run_timed(argv, receipt_path=str(tmp_path/'receipt.json'), provenance=plan,
                           runner=execute, clock=lambda: next(ticks))
    assert receipt['status'] == ('success' if case == 'success' else 'failed')
    assert receipt['total_seconds'] == 1200
    assert receipt['source_commit'] == 'a'*40
    assert json.loads((tmp_path/'receipt.json').read_text()) == receipt
    if case == 'success':
        assert receipt['pruning_seconds'] == 600
        assert Path(receipt['stdout_stderr_log']).read_text().strip().endswith('600.0s')
        assert json.loads((out/'run_manifest.json').read_text())['orchestrator_source_commit'] == 'a'*40
    else: assert receipt['errors']


def test_real_runner_requires_allocation(inputs, tmp_path, monkeypatch):
    monkeypatch.delenv('SLURM_JOB_ID', raising=False)
    argv = command(inputs)
    receipt = tw.run_timed(argv, receipt_path=str(tmp_path/'failed.json'), provenance={})
    assert receipt['status'] == 'failed'
    assert 'allocation' in ' '.join(receipt['errors'])
    assert not Path(argv[argv.index('--output-dir')+1]).exists()


def test_default_dry_run_has_no_writes_or_secret_dump(inputs, tmp_path, monkeypatch, capsys):
    config, manifest = inputs
    cp, mp = tmp_path/'config.json', tmp_path/'build_manifest.json'
    cp.write_text(json.dumps(config)); mp.write_text(json.dumps(manifest))
    monkeypatch.setenv('HF_TOKEN', 'TOPSECRET')
    before = sorted(str(p) for p in tmp_path.rglob('*'))
    assert tw.main(['--config', str(cp), '--build-manifest', str(mp), '--task', 'far_v2', '--condition', 'D',
                    '--seed', '42', '--receipt', str(tmp_path/'receipt.json')]) == 0
    text = capsys.readouterr().out
    assert 'TOPSECRET' not in text
    assert 'scientific-seed' in text
    assert before == sorted(str(p) for p in tmp_path.rglob('*'))
