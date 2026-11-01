"""Frozen A2 twin-training launcher. Dry-run is the default; never submits jobs.

Importing this module uses only the standard library. Dataset construction and
model loading belong to their existing entry points, not this wrapper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Optional

REPO = Path(__file__).resolve().parents[1]
# Direct script execution starts with scripts/ on sys.path.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
FROZEN_CONFIG = REPO/'scripts/jobs/specificity_ladder_a2.json'
PROTECTED_REGISTRIES = (Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/held_out.json'),
                        REPO/'docs/research/held_out.json')
GATE_FLAGS = ['--no-edge-pruning', '--prune-attention-heads', '--prune-mlp-blocks',
              '--no-prune-attention-neurons', '--no-prune-attention-blocks',
              '--no-prune-mlp-hidden', '--no-prune-mlp-output',
              '--no-prune-full-layers', '--no-prune-embedding']
SAFE_ENV = ('SLURM_JOB_ID', 'SLURM_JOB_NAME', 'SLURM_JOB_NODELIST', 'SLURM_CLUSTER_NAME',
            'SLURM_JOB_PARTITION', 'SLURM_GPUS_ON_NODE', 'SLURM_JOB_GPUS',
            'SLURM_CPUS_PER_TASK', 'CUDA_VISIBLE_DEVICES', 'DC_CLUSTER',
            'DC_RUN_MANIFEST_GIT', 'RESEARCH_DIRECTION', 'OMP_NUM_THREADS',
            'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _registry_hashes(task, selected):
    """Refresh the union of primary/worktree protected sets before any scoring.

    Standard-library equivalent of user_inversion_pipeline.check_registry; paths
    are fixed in production and may only be monkeypatched by CPU tests.
    """
    _require(isinstance(task, str) and bool(task) and isinstance(selected, dict) and
             set(selected) == {'train', 'validation', 'test'}, 'invalid protected registry candidate')
    for ids in selected.values():
        _require(isinstance(ids, list) and bool(ids) and
                 all(isinstance(i, str) and bool(i) for i in ids), 'invalid protected registry candidate ids')
    candidates = {i for ids in selected.values() for i in ids}
    hashes = {}
    for registry_path in dict.fromkeys(PROTECTED_REGISTRIES):
        registry_path = Path(registry_path)
        _require(registry_path.is_file(), 'missing required protected registry: '+str(registry_path))
        raw = registry_path.read_bytes()
        registry = json.loads(raw)
        _require(isinstance(registry, dict) and type(registry.get('schema')) is int and
                 registry['schema'] == 1 and isinstance(registry.get('sets'), list), 'invalid protected registry')
        hashes[str(registry_path)] = hashlib.sha256(raw).hexdigest()
        root = registry_path.parent.parent.parent.resolve()
        for entry in registry['sets']:
            _require(isinstance(entry, dict), 'unknown protected registry entry')
            if 'path' in entry:
                _require(isinstance(entry['path'], str) and bool(entry['path']), 'invalid protected registry path')
                path = (root/entry['path']).resolve()
                _require(path.is_relative_to(root), 'escaped protected registry path')
                _require(path.is_file(), 'protected set file missing')
                content = path.read_bytes()
                _require(hashlib.sha256(content).hexdigest() == entry.get('sha256'), 'protected set file hash mismatch')
                rows = json.loads(content)
                if isinstance(rows, dict):
                    rows = rows.get('instance_ids', rows.get('ids', rows.get('rows')))
                _require(isinstance(rows, list), 'unsupported protected id file')
                ids = [r.get('instance_id') if isinstance(r, dict) else r for r in rows]
                _require(type(entry.get('n')) is int and len(ids) == entry['n'], 'protected set count mismatch')
            else:
                ids = entry.get('instance_ids', entry.get('ids'))
            _require(isinstance(ids, list) and all(isinstance(i, str) and bool(i) for i in ids) and
                     len(set(ids)) == len(ids), 'invalid protected ids; review required')
            _require(entry.get('task') is None or isinstance(entry['task'], str), 'invalid protected registry task')
            _require(entry.get('task') not in (None, '', task) or not candidates.intersection(ids),
                     'protected registry id overlap')
    return hashes


def _private_configs(config, manifest, task):
    """Check the current materializer contract without importing Arrow or models."""
    _require(manifest.get('schema_version') == 1, 'unsupported build schema')
    body = {k: v for k, v in manifest.items() if k != 'build_hash'}
    build_hash = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False,
        separators=(',', ':')).encode()).hexdigest()
    _require(manifest.get('build_hash') == build_hash, 'build hash mismatch')
    hashes = {}
    for condition in (('D', 'I') if manifest['fleet_ready'] else ('D',)):
        path = Path(config['data_root'])/condition/task/'dataset_config.json'
        raw = path.read_bytes()
        private = json.loads(raw)
        _require(private.get('model') in (config['model'], 'meta-llama/Llama-3.1-8B-Instruct'),
                 'private dataset model mismatch')
        expected = dict(task=task,
            condition='deceptive' if condition == 'D' else 'user_inversion',
            recipient_condition='deceptive' if condition == 'D' else 'user_inversion',
            corruption_kind='neutral_twin_same_item', cohort=manifest['cohort'],
            fleet_ready=manifest['fleet_ready'], source_commit=manifest['source_commit'],
            max_seq_length=manifest['max_seq_length'], split_ids=manifest['tasks'][task]['split_ids'])
        for split, field in [('train', 'train_samples'), ('validation', 'val_samples'), ('test', 'test_samples')]:
            expected[field] = manifest['tasks'][task]['counts'][split]
        _check_subset(private, expected, condition+'.dataset_config.')
        hashes[condition] = hashlib.sha256(raw).hexdigest()
    return hashes


def _canonical(value):
    # Match build_twin_training._hash, including non-ASCII prompts.
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def _stored_rows(config, manifest, task, selected):
    """Authenticate Arrow prefixes and labels from hashed source rows, on CPU.

    Imports are lazy: importing the wrapper still uses only the standard library.
    No tokenizer, model, or behavioral admission runs here.
    """
    from datasets import load_from_disk
    info = manifest['tasks'][task]
    source_cache = {}

    def source_rows(kind):
        if kind not in source_cache:
            meta = info['sources'][kind]
            root = Path(meta['path'])
            files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(root.rglob('*')) if p.is_file()}
            _require(files == meta['file_hashes'] and _canonical(files) == meta['content_hash'],
                     'source file hash mismatch: '+kind)
            stored = load_from_disk(str(root))
            records = {split: [dict(row) for row in stored[split]] for split in config['sample_caps']}
            _require(_canonical(records) == meta['row_hash'], 'source row hash mismatch: '+kind)
            indexed = {}
            for split, rows in records.items():
                indexed[split] = {r['instance_id']: r for r in rows}
                _require(len(indexed[split]) == len(rows), 'duplicate source ids: '+kind)
            source_cache[kind] = indexed
        return source_cache[kind]

    for condition in (('D', 'I') if manifest['fleet_ready'] else ('D',)):
        donor = 'H' if condition == 'D' else 'I_neutral'
        root = Path(config['data_root'])/condition/task
        private = json.loads((root/'dataset_config.json').read_text())
        _require(private.get('source_provenance') == {k: info['sources'][k] for k in (condition, donor)},
                 'private source provenance mismatch: '+condition)
        recipients, references = source_rows(condition), source_rows(donor)
        stored = load_from_disk(str(root))
        for split, expected_ids in info['split_ids'].items():
            rows = [dict(row) for row in stored[split]]
            _require(len(rows) == info['counts'][split], 'stored split count mismatch: '+condition+'/'+split)
            ids = [r.get('instance_id') for r in rows]
            _require(ids == expected_ids, 'stored split id/order mismatch: '+condition+'/'+split)
            _require(ids[:len(selected[split])] == selected[split], 'stored selected prefix mismatch')
            proofs = private['token_proofs'][split]
            _require(set(proofs) == set(expected_ids), 'private prompt-proof ids mismatch')
            for row in rows:
                ident = row['instance_id']
                recipient, reference = recipients[split].get(ident), references[split].get(ident)
                _require(recipient is not None and reference is not None, 'missing authoritative source id')
                _require(row.get('source_recipient') == recipient and row.get('source_reference') == reference,
                         'stored row source provenance mismatch: '+ident)
                for key in ('target', 'distractor', 'clean_prompt'):
                    _require(row.get(key) == recipient.get(key), 'stored recipient field mismatch: '+key)
                _require(row.get('corrupt_prompt') == reference.get('clean_prompt'), 'stored reference prompt mismatch')
                proof = proofs[ident]
                _require(row.get('token_proof') == proof, 'stored token proof mismatch')
                _require(_canonical(row['clean_prompt']) == proof['recipient_prompt_hash'] and
                         _canonical(row['corrupt_prompt']) == proof['reference_prompt_hash'],
                         'stored prompt hash mismatch: '+ident)
                _require(row.get('orientation') == 'clean' and
                         row.get('corruption_kind') == 'neutral_twin_same_item' and
                         row.get('recipient_condition') == recipient['condition'] and
                         row.get('donor_identity') == dict(instance_id=ident, condition=reference['condition'], stream='clean'),
                         'stored twin metadata mismatch: '+ident)


def _selection(config, manifest, task):
    info = manifest['tasks'][task]
    selected, seen = {}, set()
    for split, cap in config['sample_caps'].items():
        ids = info['split_ids'][split]
        _require(isinstance(ids, list) and ids and all(isinstance(x, str) and x for x in ids), 'invalid split ids')
        _require(len(set(ids)) == len(ids) and not seen.intersection(ids), 'duplicate/cross-split ids')
        _require(info['counts'][split] == len(ids), 'manifest counts mismatch')
        seen.update(ids)
        selected[split] = ids[:cap]
    return selected


def build_command(config: dict, manifest: dict, *, task: str, condition: str,
                  seed: int, timing_epochs: Optional[int] = None) -> list:
    frozen = json.loads(FROZEN_CONFIG.read_text())
    for key, value in frozen.items():
        if key != 'output_root':
            _require(config.get(key) == value, 'frozen configuration mismatch: '+key)
    # These have no train.py switches; fail if the resolved source defaults drift.
    from config import NodePruningConfig
    defaults = NodePruningConfig()
    _require(defaults.init_value == config['init_value'] and
             defaults.sparsity_warmup_steps == config['sparsity_warmup_steps'], 'gate defaults drifted')
    _require(task in config['tasks'] and task in manifest['tasks'], 'unknown/unbuilt task')
    _require(condition in config['conditions'] and seed in config['seeds'], 'unknown condition/seed')
    _require(re.fullmatch('[0-9a-f]{40}', manifest.get('source_commit') or '') is not None, 'full source commit required')
    _require(isinstance(manifest['max_seq_length'], int) and manifest['max_seq_length'] > 0, 'invalid max length')
    if timing_epochs is not None:
        _require(type(timing_epochs) is int and 10 <= timing_epochs <= config['node_epochs'],
                 'timing epochs must include at least one periodic validation (10 epochs)')
    else:
        _require(manifest.get('fleet_ready') is True and manifest['cohort'] == 'matched', 'production requires matched fleet_ready')
    if condition == 'I':
        _require(manifest.get('fleet_ready') is True and manifest['cohort'] == 'matched', 'I requires matched A1 inputs')
    _private_configs(config, manifest, task)
    selected = _selection(config, manifest, task)
    actual_epochs = timing_epochs or config['node_epochs']
    cohort_hash = digest({'build': manifest['build_hash'], 'ids': selected, 'config': config})[:16]
    purpose = 'timing'+str(actual_epochs) if timing_epochs is not None else 'full'
    output = Path(config['output_root'])/f'{task}_{condition}_seed{seed}_heads-mlp_{cohort_hash}_{purpose}'
    values = [('model', config['model']), ('task', task), ('deception-condition', 'deceptive'),
              ('data-dir', str(Path(config['data_root'])/condition)),
              ('node-lambda-sparsity', config['node_lambda_sparsity']), ('node-epochs', actual_epochs),
              ('lr', config['lr']), ('batch-size', config['batch_size']),
              ('faithfulness-weight', config['faithfulness_weight']),
              ('deception-margin-loss', config['deception_margin_loss']),
              ('train-samples', len(selected['train'])), ('val-samples', len(selected['validation'])),
              ('test-samples', len(selected['test'])), ('max-seq-length', manifest['max_seq_length']),
              ('seed', seed), ('output-dir', str(output))]
    return [sys.executable, str(REPO/'train.py')] + [x for key, value in values for x in ('--'+key, str(value))] + GATE_FLAGS


def expected_config(command):
    """Subset of actual run_io.resolved_run_config frozen by this command."""
    expected = {'edge_pruning': False, 'deception_runtime_filter': False,
                'std_runtime_filter': False, 'skip_node_pruning': False}
    numeric = {'node_lambda_sparsity': float, 'node_epochs': int, 'lr': float, 'batch_size': int,
               'faithfulness_weight': float, 'deception_margin_loss': float, 'train_samples': int, 'val_samples': int,
               'test_samples': int, 'max_seq_length': int, 'seed': int}
    for i, arg in enumerate(command):
        if arg.startswith('--') and i+1 < len(command) and not command[i+1].startswith('--'):
            key = arg[2:].replace('-', '_')
            if key != 'output_dir':
                expected[key] = numeric.get(key, str)(command[i+1])
    expected['node_config'] = dict(init_value=0.5, sparsity_warmup_steps=1000,
        **{flag.removeprefix('--no-').removeprefix('--').replace('-', '_'): not flag.startswith('--no-')
           for flag in GATE_FLAGS if 'prune-' in flag})
    return expected


def plan_run(config, manifest, *, task, condition, seed, timing_epochs=None, execution_commit=None):
    if execution_commit is not None:
        _require(isinstance(execution_commit, str) and re.fullmatch('[0-9a-f]{40}', execution_commit) is not None,
                 'full execution commit required')
    command = build_command(config, manifest, task=task, condition=condition, seed=seed, timing_epochs=timing_epochs)
    selected = _selection(config, manifest, task)
    registry_hashes = _registry_hashes(task, selected)
    _stored_rows(config, manifest, task, selected)
    source_hashes = {name: hashlib.sha256((REPO/name).read_bytes()).hexdigest()
                     for name in ('train.py', 'config.py', 'pruning.py', 'run_io.py',
                                  'dataset/build_twin_training.py', 'scripts/twin_training.py')}
    return dict(task=task, condition=condition, seed=seed, model=config['model'],
                purpose='timing-only' if timing_epochs is not None else 'scientific-seed',
                actual_epochs=timing_epochs or config['node_epochs'], planned_epochs=config['node_epochs'],
                fleet_ready=manifest['fleet_ready'], cohort=manifest['cohort'],
                source_commit=manifest['source_commit'], execution_commit=execution_commit, build_hash=manifest['build_hash'],
                build_manifest_sha256=digest(manifest), source_hashes=source_hashes,
                frozen_config_sha256=digest(config), resolved_config_sha256=digest(expected_config(command)),
                dataset_config_sha256=_private_configs(config, manifest, task),
                selected_ids=selected, counts={s: len(v) for s,v in selected.items()},
                registry_sha256=registry_hashes,
                train_under_200_requires_lead_review=len(selected['train']) < 200,
                max_seq_length=manifest['max_seq_length'], granularity='heads-mlp',
                recipient_condition='deceptive' if condition == 'D' else 'user_inversion',
                legacy_deception_condition='deceptive', argv=command)


def _check_subset(actual, expected, prefix=''):
    for key, value in expected.items():
        if isinstance(value, dict):
            _check_subset(actual.get(key, {}), value, prefix+key+'.')
        elif actual.get(key) != value:
            raise ValueError('resolved config mismatch: '+prefix+key)


def _validate_artifacts(out, command, provenance):
    """Reject syntactically valid but unfinished or unrelated training outputs."""
    results = json.loads((out/'results.json').read_text())
    expected = expected_config(command)
    _check_subset(results, {key: expected[key] for key in ('model', 'task', 'seed', 'edge_pruning')})
    for key in ('baseline', 'node_eval'):
        _require(isinstance(results.get(key), dict) and bool(results[key]), 'empty evaluation: '+key)
    _require(results.get('edge_eval') is None, 'unexpected edge evaluation')
    history = json.loads((out/'history.json').read_text())
    node = history.get('node', {})
    epochs = expected['node_epochs']
    _require(node.get('epochs') == list(range(1, epochs+1)), 'incomplete node history')
    _require(any(isinstance(e, dict) and isinstance(e.get('epoch'), int) and
                 10 <= e['epoch'] <= epochs for e in node.get('evals', [])), 'missing periodic validation')
    active = json.loads((out/'active_nodes.json').read_text())
    heads, mlps = active.get('active_heads'), active.get('active_mlps')
    _require(isinstance(heads, dict) and isinstance(mlps, list), 'invalid active nodes')
    _require(all(str(k).isdigit() and 0 <= int(k) < 32 and isinstance(v, list) and
                 len(v) == len(set(v)) and all(type(h) is int and 0 <= h < 32 for h in v)
                 for k, v in heads.items()), 'invalid active heads')
    _require(len(mlps) == len(set(mlps)) and all(type(m) is int and 0 <= m < 32 for m in mlps),
             'invalid active MLPs')
    native = json.loads((out/'run_manifest.json').read_text())
    _require(native.get('schema') == 'run-manifest/1', 'invalid native manifest schema')
    _require(native.get('manifest_hash') == digest({k:v for k,v in native.items() if k != 'manifest_hash'}),
             'native manifest hash mismatch')
    _check_subset(native, dict(model=expected['model'], seed=expected['seed'],
        config_sha256=hashlib.sha256((out/'config.json').read_bytes()).hexdigest()))
    config_path = Path(expected['data_dir'])/expected['task']/'dataset_config.json'
    datasets = {str((REPO/Path(k)).resolve()): v for k,v in native.get('dataset_files', {}).items()}
    _require(datasets.get(str(config_path.resolve())) ==
             provenance['dataset_config_sha256'][provenance['condition']], 'native dataset hash mismatch')
    return native


def run_timed(command: list, *, receipt_path: str, provenance: dict,
              runner=None, clock=None) -> dict:
    """Run once inside Slurm, retaining a receipt even for launch/artifact failure.

    runner/clock injection is exclusively for CPU child-process tests. Production
    CLI never supplies them and always enforces allocation/hardware checks.
    """
    receipt_file = Path(receipt_path)
    _require(not receipt_file.exists(), 'receipt already exists')
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    log = receipt_file.with_suffix('.stdout-stderr.log')
    _require(not log.exists(), 'log already exists')
    out = Path(command[command.index('--output-dir')+1])
    env = dict(os.environ, DC_RUN_MANIFEST_GIT='0')
    injected_clock = clock is not None and clock is not time.monotonic
    receipt = dict(provenance, status='failed', errors=[], exit_code=None,
                   test_runner_injected=runner is not None or injected_clock,
                   test_clock_injected=injected_clock,
                   stdout_stderr_log=str(log), output_dir=str(out),
                   environment={k: env[k] for k in SAFE_ENV if k in env},
                   started_utc=datetime.now(timezone.utc).isoformat(), artifacts={})
    tick = clock or time.monotonic
    started = tick()
    try:
        _require(not out.exists(), 'stale output directory exists')
        if runner is None:
            _require(bool(env.get('SLURM_JOB_ID')), 'real run requires approved Slurm allocation')
            gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                                 check=True, capture_output=True, text=True)
            devices = [v.strip() for v in gpu.stdout.splitlines() if v.strip()]
            _require(len(devices) == 1 and any(g in devices[0] for g in ('A40', 'H100', 'H200')),
                     'require one allocated A40/H100/H200 GPU')
            receipt['gpu_devices'] = devices
            receipt['gpu_count'] = len(devices)
        else:
            receipt['test_runner_injected'] = True
        execution_commit = provenance.get('execution_commit')
        _require(isinstance(execution_commit, str) and re.fullmatch('[0-9a-f]{40}', execution_commit) is not None,
                 'full execution commit required')
        receipt['registry_sha256'] = _registry_hashes(provenance.get('task'), provenance.get('selected_ids'))
        with log.open('x') as stream:
            result = (runner or subprocess.run)(command, stdout=stream, stderr=subprocess.STDOUT,
                                                 env=env, cwd=str(REPO), check=False)
        receipt['exit_code'] = result.returncode
        _require(result.returncode == 0, 'training subprocess failed: '+str(result.returncode))
        for name in ('config.json', 'active_nodes.json', 'results.json', 'history.json', 'run_manifest.json'):
            path = out/name
            _require(path.is_file() and path.stat().st_size > 0, 'missing/empty artifact: '+name)
            json.loads(path.read_text())
            receipt['artifacts'][name] = str(path)
        _check_subset(json.loads((out/'config.json').read_text()), expected_config(command))
        commit = provenance.get('source_commit', '')
        _require(re.fullmatch('[0-9a-f]{40}', commit) is not None, 'missing full source commit')
        native = _validate_artifacts(out, command, provenance)
        native['orchestrator_source_commit'] = execution_commit
        native['execution_commit'] = execution_commit
        native['build_source_commit'] = commit
        # Rehash the augmented native manifest, retaining native provenance fields.
        native.pop('manifest_hash', None)
        native['manifest_hash'] = digest(native)
        (out/'run_manifest.json').write_text(json.dumps(native, indent=2)+'\n')
        receipt['artifact_sha256'] = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                      for name, path in receipt['artifacts'].items()}
        receipt['status'] = 'success'
    except Exception as error:
        receipt['errors'].append(type(error).__name__+': '+str(error))
    finally:
        text = log.read_text() if log.exists() else ''
        durations = re.findall(r'Node pruning time:\s*([0-9.]+)s', text)
        receipt['pruning_seconds'] = float(durations[-1]) if durations else None
        peaks = re.findall(r'Overall peak:\s*([0-9.]+) GB', text)
        receipt['peak_memory_gb'] = float(peaks[-1]) if peaks else None
        receipt['total_seconds'] = tick()-started
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        receipt_file.write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # Delegate project parsing unchanged so both entrypoints use identical gates.
    stage_parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    stage_parser.add_argument('--stage')
    stage, remaining = stage_parser.parse_known_args(argv)
    if stage.stage == 'project':
        from scripts.twin_training_projection import main as project_main
        return project_main(remaining)
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--stage', choices=('dry-run', 'run', 'project'), default='dry-run')
    parser.add_argument('--config', required=True)
    parser.add_argument('--build-manifest', required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--condition', choices=('D', 'I'), required=True)
    parser.add_argument('--seed', type=int, choices=(42, 1, 123), required=True)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--timing-epochs', type=int)
    parser.add_argument('--commit', help='Full execution revision supplied by the orchestrator; required for run')
    args = parser.parse_args(argv)
    if args.stage == 'run':
        _require(isinstance(args.commit, str) and re.fullmatch('[0-9a-f]{40}', args.commit) is not None,
                 'full execution commit required for run')
    config = json.loads(Path(args.config).read_text())
    manifest = json.loads(Path(args.build_manifest).read_text())
    config.setdefault('data_root', str(Path(args.build_manifest).resolve().parent))
    plan = plan_run(config, manifest, task=args.task, condition=args.condition,
                    seed=args.seed, timing_epochs=args.timing_epochs, execution_commit=args.commit)
    plan['config_file_sha256'] = hashlib.sha256(Path(args.config).read_bytes()).hexdigest()
    plan['build_manifest_file_sha256'] = hashlib.sha256(Path(args.build_manifest).read_bytes()).hexdigest()
    if args.stage == 'dry-run':
        print(json.dumps(dict(plan, receipt_path=args.receipt), indent=2))
        return 0
    receipt = run_timed(plan['argv'], receipt_path=args.receipt, provenance=plan)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'success' else 1


if __name__ == '__main__':
    raise SystemExit(main())
