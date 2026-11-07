"""CPU-only contract tests; never import the model/training stack."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import twin_training as tw



def execution_plan(*args, **kwargs):
    return tw.plan_run(*args, execution_commit='e'*40, **kwargs)


def canonical(value):
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


@pytest.fixture(scope='module')
def stored_template(tmp_path_factory):
    """Real Arrow trees with the current materializer's source/proof contract."""
    import hashlib
    from datasets import Dataset, DatasetDict
    from tests.test_twin_training import sources
    root = tmp_path_factory.mktemp('wrapper-stored-cohort')
    ids = {s: [s+str(i) for i in range(n)] for s, n in [('train', 205), ('validation', 3), ('test', 4)]}
    originals = sources()
    source_rows, meta = {}, {}
    conditions = {'D': 'deceptive', 'H': 'honest', 'I': 'user_inversion', 'I_neutral': 'user_neutral'}
    for kind, condition in conditions.items():
        source_rows[kind] = {split: [dict(originals[0 if kind in ('D', 'I') else 1][split][0],
            instance_id=ident, condition=condition) for ident in identifiers] for split, identifiers in ids.items()}
        path = root/'sources'/kind
        DatasetDict({split: Dataset.from_list(rows) for split, rows in source_rows[kind].items()}).save_to_disk(str(path))
        cfg = dict(task='far_v2', condition=condition, model='llama-8b-instruct',
                   margin_thresh=.5 if kind == 'I' else .7)
        (path/'dataset_config.json').write_text(json.dumps(cfg))
        files = {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(path.rglob('*')) if p.is_file()}
        meta[kind] = dict(path=str(path), config=cfg, file_hashes=files,
                          content_hash=canonical(files), row_hash=canonical(source_rows[kind]))
    manifest = dict(schema_version=1, cohort='matched', fleet_ready=True, source_commit='a'*40,
        max_seq_length=120, tasks={'far_v2': dict(split_ids=ids,
        counts={split: len(v) for split,v in ids.items()}, sources=meta)})
    manifest['build_hash'] = canonical(manifest)
    for condition, donor in [('D', 'H'), ('I', 'I_neutral')]:
        built, proofs = {}, {}
        for split in ids:
            built[split], proofs[split] = [], {}
            for recipient, reference in zip(source_rows[condition][split], source_rows[donor][split]):
                ident = recipient['instance_id']
                proof = dict(recipient_prompt_hash=canonical(recipient['clean_prompt']),
                             reference_prompt_hash=canonical(reference['clean_prompt']))
                proofs[split][ident] = proof
                built[split].append(dict(recipient, corrupt_prompt=reference['clean_prompt'],
                    source_recipient=recipient, source_reference=reference, orientation='clean',
                    corruption_kind='neutral_twin_same_item', recipient_condition=conditions[condition],
                    donor_identity=dict(instance_id=ident, condition=conditions[donor], stream='clean'), token_proof=proof))
        path = root/condition/'far_v2'
        DatasetDict({split: Dataset.from_list(rows) for split,rows in built.items()}).save_to_disk(str(path))
        private = dict(meta[condition]['config'], recipient_condition=conditions[condition],
            corruption_kind='neutral_twin_same_item', cohort='matched', fleet_ready=True,
            source_commit=manifest['source_commit'], max_seq_length=120, split_ids=ids,
            train_samples=205, val_samples=3, test_samples=4, token_proofs=proofs,
            source_provenance={condition: meta[condition], donor: meta[donor]})
        (path/'dataset_config.json').write_text(json.dumps(private))
    (root/'build_manifest.json').write_text(json.dumps(manifest))
    return root


@pytest.fixture
def inputs(tmp_path, stored_template):
    import shutil
    root = tmp_path/'data'
    shutil.copytree(stored_template, root)
    for path in [root/'build_manifest.json'] + list(root.glob('[DI]/far_v2/dataset_config.json')):
        path.write_text(path.read_text().replace(str(stored_template), str(root)))
    manifest = json.loads((root/'build_manifest.json').read_text())
    manifest['build_hash'] = canonical({k:v for k,v in manifest.items() if k != 'build_hash'})
    (root/'build_manifest.json').write_text(json.dumps(manifest))
    config = json.loads(tw.FROZEN_CONFIG.read_text())
    config.update(data_root=str(root), output_root=str(tmp_path/'runs'))
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
    provenance = execution_plan(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=None)
    assert provenance['selected_ids']['train'] == manifest['tasks']['far_v2']['split_ids']['train'][:200]
    assert provenance['purpose'] == 'scientific-seed'
    assert provenance['recipient_condition'] == 'deceptive'
    assert provenance['legacy_deception_condition'] == 'deceptive'
    other = command(inputs, seed=1)
    assert {i for i, (a,b) in enumerate(zip(argv, other)) if a != b} == {argv.index('--seed')+1, argv.index('--output-dir')+1}


def test_timing_only_provisional_and_production_gate(inputs):
    config, manifest = inputs
    manifest.update(cohort='timing-d-only', fleet_ready=False)
    manifest['build_hash'] = tw.digest({k:v for k,v in manifest.items() if k != 'build_hash'})
    path = Path(config['data_root'])/'D/far_v2/dataset_config.json'
    private = json.loads(path.read_text())
    private.update(cohort='timing-d-only', fleet_ready=False)
    path.write_text(json.dumps(private))
    with pytest.raises(ValueError, match='fleet_ready'):
        command(inputs)
    argv = command(inputs, timing_epochs=20)
    assert argv[argv.index('--node-epochs')+1] == '20'
    plan = execution_plan(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=20)
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


def fake_child(tmp_path, argv, *, missing=None, fail=False, mismatch=False, semantic=None):
    """A real short Python child writes the same artifact shapes as train.py."""
    out = Path(argv[argv.index('--output-dir')+1])
    cfg = tw.expected_config(argv)
    if mismatch: cfg['batch_size'] = 99
    if semantic == 'wrong-margin': cfg['deception_margin_loss'] = .5
    code = ['import json, pathlib', 'out=pathlib.Path('+repr(str(out))+')', 'out.mkdir(parents=True)']
    config_text = json.dumps(cfg)
    private_path = Path(argv[argv.index('--data-dir')+1])/argv[argv.index('--task')+1]/'dataset_config.json'
    import hashlib
    native = dict(schema='run-manifest/1', model=cfg['model'], seed=cfg['seed'],
        config_sha256=hashlib.sha256(config_text.encode()).hexdigest(),
        dataset_files={str(private_path): hashlib.sha256(private_path.read_bytes()).hexdigest()},
        git_fingerprint_error='disabled')
    native['manifest_hash'] = tw.digest(native)
    epochs = cfg['node_epochs']
    artifacts = {'config.json': cfg, 'active_nodes.json': {'active_heads': {'0': [1]}, 'active_mlps': [5]},
                 'results.json': dict(model=cfg['model'], task=cfg['task'], seed=cfg['seed'], edge_pruning=False,
                                      baseline={'accuracy': 1.0}, node_eval={'accuracy': 0.9}, edge_eval=None),
                 'history.json': {'node': {'epochs': list(range(1, epochs+1)), 'evals': [{'epoch': 0}, {'epoch': 10}]}},
                 'run_manifest.json': native}
    if semantic == 'empty-results': artifacts['results.json']['node_eval'] = {}
    if semantic == 'wrong-seed': artifacts['results.json']['seed'] = 123
    if semantic == 'short-history': artifacts['history.json']['node']['epochs'].pop()
    if semantic == 'no-validation': artifacts['history.json']['node']['evals'] = [{'epoch': 0}]
    if semantic == 'bad-nodes': artifacts['active_nodes.json']['active_mlps'] = [32]
    if semantic == 'bad-native-hash': native['manifest_hash'] = '0'*64
    if semantic == 'bad-native-config':
        native['config_sha256'] = '0'*64
        native['manifest_hash'] = tw.digest({k:v for k,v in native.items() if k != 'manifest_hash'})
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
    plan = execution_plan(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=20)
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
        assert json.loads((out/'run_manifest.json').read_text())['orchestrator_source_commit'] == 'e'*40
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


@pytest.mark.parametrize('entry', [['scripts/twin_training.py'], ['-m', 'scripts.twin_training']])
def test_subprocess_dry_run_both_entrypoints(inputs, tmp_path, entry):
    config, manifest = inputs
    cp, mp = tmp_path/'config.json', tmp_path/'build_manifest.json'
    cp.write_text(json.dumps(config)); mp.write_text(json.dumps(manifest))
    before = sorted(str(p) for p in tmp_path.rglob('*'))
    env = dict(os.environ, PYTHONPATH='', PYTHONDONTWRITEBYTECODE='1', HF_TOKEN='SECRET')
    result = subprocess.run([sys.executable]+entry+['--config', str(cp), '--build-manifest', str(mp),
        '--task', 'far_v2', '--condition', 'D', '--seed', '42', '--receipt', str(tmp_path/'receipt.json')],
        cwd=tw.REPO, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['counts']['train'] == 200
    assert 'SECRET' not in result.stdout
    assert before == sorted(str(p) for p in tmp_path.rglob('*'))


def test_actual_train_parser_resolves_frozen_command(inputs):
    import train
    from run_io import resolved_run_config
    args = train.build_parser().parse_args(command(inputs)[2:])
    node, edge = train.resolve_args(args)
    tw._check_subset(resolved_run_config(args, node, edge), tw.expected_config(command(inputs)))


@pytest.mark.parametrize('case', ['build_hash', 'missing', 'ids', 'count', 'length', 'condition', 'commit', 'peer'])
def test_private_build_consistency(inputs, case):
    config, manifest = inputs
    path = Path(config['data_root'])/('I' if case == 'peer' else 'D')/'far_v2/dataset_config.json'
    private = json.loads(path.read_text())
    if case == 'build_hash': manifest['build_hash'] = '0'*64
    elif case == 'missing': path.unlink()
    else:
        if case in ('ids', 'peer'): private['split_ids']['train'][0] = 'other'
        if case == 'count': private['train_samples'] = 1
        if case == 'length': private['max_seq_length'] = 1
        if case == 'condition': private['recipient_condition'] = 'honest'
        if case == 'commit': private['source_commit'] = 'b'*40
        path.write_text(json.dumps(private))
    with pytest.raises((ValueError, FileNotFoundError)):
        command(inputs)


def test_private_hashes_recorded_for_both_conditions(inputs):
    config, manifest = inputs
    plan = execution_plan(config, manifest, task='far_v2', condition='D', seed=42)
    assert set(plan['dataset_config_sha256']) == {'D', 'I'}
    assert all(len(value) == 64 for value in plan['dataset_config_sha256'].values())


@pytest.mark.parametrize('case', ['empty-results', 'wrong-seed', 'short-history', 'no-validation', 'bad-nodes',
                                  'bad-native-hash', 'bad-native-config'])
def test_reject_semantically_incomplete_artifacts(inputs, tmp_path, case):
    config, manifest = inputs
    argv = command(inputs, timing_epochs=20)
    plan = execution_plan(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=20)
    ticks = iter([10., 1210.])
    receipt = tw.run_timed(argv, receipt_path=str(tmp_path/'receipt.json'), provenance=plan,
        runner=fake_child(tmp_path, argv, semantic=case), clock=lambda: next(ticks))
    assert receipt['status'] == 'failed'
    assert receipt['errors']


def test_private_configs_accept_canonical_hub_model(inputs):
    config, manifest = inputs
    for condition in ('D', 'I'):
        path = Path(config['data_root'])/condition/'far_v2/dataset_config.json'
        private = json.loads(path.read_text())
        private['model'] = 'meta-llama/Llama-3.1-8B-Instruct'
        path.write_text(json.dumps(private))
    assert command(inputs)


def test_actual_materializer_output_launch_contract(tmp_path):
    from tests.test_twin_training import sources, write_sources
    from tests.fakes import FakeWordTokenizer
    from dataset.build_twin_training import materialize
    d, h = sources()
    roots = write_sources(tmp_path/'sources', d, h)
    for kind in ('D', 'H'):
        path = Path(roots[kind])/('far_v2' if kind == 'D' else 'far_v2_honest')/'dataset_config.json'
        cfg = json.loads(path.read_text())
        cfg['model'] = 'meta-llama/Llama-3.1-8B-Instruct'
        path.write_text(json.dumps(cfg))
    manifest = materialize(root_d=roots['D'], root_h=roots['H'], root_i=None, root_i_neutral=None,
        output_root=str(tmp_path/'materialized'), tasks=['far_v2'], cohort='timing-d-only',
        tokenizer=FakeWordTokenizer(), max_length=30, commit='a'*40)
    config = json.loads(tw.FROZEN_CONFIG.read_text())
    config.update(data_root=str(tmp_path/'materialized'), output_root=str(tmp_path/'runs'))
    plan = execution_plan(config, manifest, task='far_v2', condition='D', seed=42, timing_epochs=20)
    assert plan['counts'] == {'train': 1, 'validation': 1, 'test': 1}
    assert plan['train_under_200_requires_lead_review'] is True
    assert plan['selected_ids'] == manifest['tasks']['far_v2']['split_ids']
    assert plan['fleet_ready'] is False


def test_training_margin_shared_despite_historical_screening(inputs):
    import train
    from dataset.deception_common import resolve_margin
    from run_io import resolved_run_config
    config, manifest = inputs
    observed = []
    for condition, screening in [('D', .7), ('I', .5)]:
        path = Path(config['data_root'])/condition/'far_v2/dataset_config.json'
        private = json.loads(path.read_text()); private['margin_thresh'] = screening
        path.write_text(json.dumps(private))
        argv = command(inputs, condition=condition)
        args = train.build_parser().parse_args(argv[2:])
        node, edge = train.resolve_args(args)
        observed.append(resolve_margin(args, private))
        assert resolved_run_config(args, node, edge)['deception_margin_loss'] == .7
        assert tw.expected_config(argv)['deception_margin_loss'] == .7
        assert json.loads(path.read_text())['margin_thresh'] == screening
    assert observed == [.7, .7]


def test_margin_artifact_mismatch_fails(inputs, tmp_path):
    argv = command(inputs, timing_epochs=20)
    plan = execution_plan(*inputs, task='far_v2', condition='D', seed=42, timing_epochs=20)
    execute = fake_child(tmp_path, argv, semantic='wrong-margin')
    ticks = iter([10., 1210.])
    receipt = tw.run_timed(argv, receipt_path=str(tmp_path/'receipt.json'), provenance=plan,
        runner=execute, clock=lambda: next(ticks))
    assert receipt['status'] == 'failed'
    assert 'deception_margin_loss' in ' '.join(receipt['errors'])


def test_margin_frozen_value_rejected(inputs):
    config, manifest = inputs
    config['deception_margin_loss'] = .5
    with pytest.raises(ValueError, match='deception_margin_loss'):
        command(inputs)


@pytest.mark.parametrize('case', ['id', 'order', 'count', 'clean', 'reference', 'target', 'distractor',
                                  'forged-source-label', 'forged-prompt-proof', 'source-file'])
def test_rejects_stale_saved_rows_before_launch(inputs, tmp_path, case):
    import shutil
    from datasets import Dataset, DatasetDict, load_from_disk
    config, manifest = inputs
    path = Path(config['data_root'])/'D/far_v2'
    private = json.loads((path/'dataset_config.json').read_text())
    rows = {split: data.to_list() for split, data in load_from_disk(str(path)).items()}
    row = rows['train'][0]
    if case == 'id': row['instance_id'] = 'stale-id'
    elif case == 'order': rows['train'][201], rows['train'][202] = rows['train'][202], rows['train'][201]
    elif case == 'count': rows['train'].pop()
    elif case == 'clean': row['clean_prompt'] += ' changed'
    elif case == 'reference': row['corrupt_prompt'] += ' changed'
    elif case == 'target': row['target'] = 'changed'
    elif case == 'distractor': row['distractor'] = 'changed'
    elif case == 'forged-source-label':
        row['target'] = row['source_recipient']['target'] = 'changed'
    elif case == 'forged-prompt-proof':
        row['clean_prompt'] += ' changed'
        row['source_recipient']['clean_prompt'] = row['clean_prompt']
        private['token_proofs']['train'][row['instance_id']]['recipient_prompt_hash'] = canonical(row['clean_prompt'])
        row['token_proof'] = private['token_proofs']['train'][row['instance_id']]
    elif case == 'source-file':
        source = Path(manifest['tasks']['far_v2']['sources']['D']['path'])/'dataset_config.json'
        source.write_text(source.read_text()+' ')
    replacement = tmp_path/'replacement'
    DatasetDict({split: Dataset.from_list(data) for split,data in rows.items()}).save_to_disk(str(replacement))
    (replacement/'dataset_config.json').write_text(json.dumps(private))
    shutil.rmtree(path)
    replacement.rename(path)
    with pytest.raises(ValueError):
        execution_plan(config, manifest, task='far_v2', condition='D', seed=42)


@pytest.mark.parametrize('clock_kind', ['custom', 'explicit-monotonic', 'default'])
def test_clock_only_injection_is_marked_before_allocation_failure(inputs, tmp_path, monkeypatch, clock_kind):
    import time
    monkeypatch.delenv('SLURM_JOB_ID', raising=False)
    clock = (lambda: 10.) if clock_kind == 'custom' else time.monotonic if clock_kind == 'explicit-monotonic' else None
    receipt = tw.run_timed(command(inputs), receipt_path=str(tmp_path/'clock-receipt.json'),
                           provenance={}, clock=clock)
    assert receipt['status'] == 'failed'
    assert 'allocation' in ' '.join(receipt['errors'])
    assert receipt.get('test_runner_injected', False) is (clock_kind == 'custom')
    assert receipt.get('test_clock_injected', False) is (clock_kind == 'custom')


@pytest.fixture
def protected_registries(tmp_path, monkeypatch):
    paths = [tmp_path/name/'docs/research/held_out.json' for name in ('primary','branch')]
    for path in paths:
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'schema':1, 'sets':[]}))
    monkeypatch.setattr(tw, 'PROTECTED_REGISTRIES', tuple(paths), raising=False)
    return paths


@pytest.mark.parametrize('split', ['train','validation','test'])
@pytest.mark.parametrize('which', [0,1])
def test_dry_run_rejects_protected_overlap_in_either_registry(inputs, protected_registries, split, which):
    path = protected_registries[which]
    ident = inputs[1]['tasks']['far_v2']['split_ids'][split][0]
    path.write_text(json.dumps({'schema':1,'sets':[{'task':'far_v2','ids':[ident]}]}))
    with pytest.raises(ValueError, match='protected registry id overlap'):
        execution_plan(*inputs, task='far_v2', condition='D', seed=42)


def test_runtime_refreshes_registry_before_injected_child(inputs, tmp_path, protected_registries):
    plan = execution_plan(*inputs, task='far_v2', condition='D', seed=42, timing_epochs=20)
    protected_registries[0].write_text(json.dumps({'schema':1,'sets':[{'ids':['test0']}]}))
    calls = []
    receipt = tw.run_timed(plan['argv'], receipt_path=str(tmp_path/'receipt.json'), provenance=plan,
                          runner=lambda *a,**kw: calls.append(a))
    assert receipt['status'] == 'failed' and not calls
    assert 'protected registry id overlap' in str(receipt['errors'])


@pytest.mark.parametrize('case', ['missing','malformed','schema','entry','ids','count','hash','escape'])
def test_registry_failures_block_plan(inputs, protected_registries, case):
    path = protected_registries[1]
    if case=='missing':
        path.unlink()
    elif case=='malformed':
        path.write_text('{')
    else:
        registry = {'schema':1,'sets':[]}
        if case=='schema': registry['schema'] = True
        elif case=='entry': registry['sets'] = ['unknown']
        elif case=='ids': registry['sets'] = [{'ids':['x','x']}]
        else:
            data = path.parents[2]/'protected.json'
            data.write_text(json.dumps(['unrelated']))
            entry = {'path':'protected.json','sha256':tw.hashlib.sha256(data.read_bytes()).hexdigest(),'n':1}
            if case=='count': entry['n'] = 2
            elif case=='hash': entry['sha256'] = 'a'*64
            else: entry['path'] = '../escaped.json'
            registry['sets'] = [entry]
        path.write_text(json.dumps(registry))
    with pytest.raises((ValueError, OSError), match='protected|Expecting'):
        execution_plan(*inputs, task='far_v2', condition='D', seed=42)


def test_registry_hashes_retained_and_task_scope_respected(inputs, tmp_path, protected_registries):
    protected_registries[0].write_text(json.dumps({'schema':1,'sets':[{'task':'sdr_v2','ids':['test0']}]}))
    plan = execution_plan(*inputs, task='far_v2', condition='D', seed=42, timing_epochs=20)
    expected = {str(p):tw.hashlib.sha256(p.read_bytes()).hexdigest() for p in protected_registries}
    assert plan['registry_sha256'] == expected
    execute = fake_child(tmp_path, plan['argv'])
    receipt = tw.run_timed(plan['argv'], receipt_path=str(tmp_path/'receipt.json'), provenance=plan, runner=execute)
    assert receipt['status'] == 'success'
    assert receipt['registry_sha256'] == expected


def test_real_run_cli_requires_explicit_execution_commit_before_launch(inputs, tmp_path, monkeypatch):
    cp, mp = tmp_path/'config.json', tmp_path/'build_manifest.json'
    cp.write_text(json.dumps(inputs[0]))
    mp.write_text(json.dumps(inputs[1]))
    calls = []
    monkeypatch.setattr(tw, 'run_timed', lambda *a,**kw: calls.append(a))
    with pytest.raises(ValueError, match='execution commit'):
        tw.main(['--stage','run','--config',str(cp),'--build-manifest',str(mp),
                 '--task','far_v2','--condition','D','--seed','42','--receipt',str(tmp_path/'receipt.json')])
    assert not calls


@pytest.mark.parametrize('override', [
    ['--sta','run'], ['--sta=run'], ['--stag','run'], ['--stag=run'],
    ['--sta','project'], ['--sta=project'], ['--stag','project'], ['--stag=project']])
def test_actual_launcher_rejects_abbreviated_stage_before_run_or_project(tmp_path, override):
    """Execute the real launcher, but replace all execution paths with CPU stubs."""
    marker = tmp_path/'execution-reached.txt'
    shim = tmp_path/'cpu-python'
    shim.write_text('#!'+sys.executable+'\n'+ '\n'.join([
        'import sys', 'from pathlib import Path',
        'sys.path.insert(0, '+repr(str(tw.REPO))+')',
        'from scripts import twin_training as tw',
        'from scripts import twin_training_projection as projection',
        'marker = Path('+repr(str(marker))+')',
        "tw.plan_run = lambda *a, **kw: {'argv': ['cpu-stub']}",
        'def reached(*a, **kw):',
        "    marker.write_text('execution or project reached')",
        "    return {'status':'success'}",
        'tw.run_timed = reached',
        'projection.main = lambda *a, **kw: (reached() and 0)',
        'raise SystemExit(tw.main(sys.argv[3:]))',
    ])+'\n')
    shim.chmod(0o700)
    cp, mp = tmp_path/'config.json', tmp_path/'build_manifest.json'
    cp.write_text('{}')
    mp.write_text('{}')
    env = dict(os.environ, DC_PYTHON=str(shim), DC_CLUSTER='delta', PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run(['bash','scripts/jobs/specificity_twin_training.sh','--dry-run',
        '--config',str(cp),'--build-manifest',str(mp),'--task','far_v2','--condition','D',
        '--seed','42','--receipt',str(tmp_path/'receipt.json'),'--commit','e'*40,*override],
        cwd=tw.REPO, env=env, capture_output=True, text=True)
    assert not marker.exists(), result.stdout+result.stderr
    assert result.returncode == 2, result.stdout+result.stderr
    assert 'unrecognized arguments' in result.stderr


@pytest.mark.parametrize('stage', ['dry-run','run','project'])
def test_exact_stage_names_keep_their_dispatch(tmp_path, monkeypatch, stage):
    from scripts import twin_training_projection as projection
    cp, mp = tmp_path/'config.json', tmp_path/'build_manifest.json'
    cp.write_text('{}')
    mp.write_text('{}')
    calls = []
    monkeypatch.setattr(tw, 'plan_run', lambda *a,**kw: {'argv':['cpu-stub']})
    def run(*a,**kw):
        calls.append('run')
        return {'status':'success'}
    def project(*a,**kw):
        calls.append('project')
        return 0
    monkeypatch.setattr(tw, 'run_timed', run)
    monkeypatch.setattr(projection, 'main', project)
    assert tw.main(['--stage',stage,'--config',str(cp),'--build-manifest',str(mp),
        '--task','far_v2','--condition','D','--seed','42','--receipt',str(tmp_path/'receipt.json'),
        '--commit','e'*40]) == 0
    assert calls == ([] if stage=='dry-run' else [stage])
