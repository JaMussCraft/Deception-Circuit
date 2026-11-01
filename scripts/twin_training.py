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
FROZEN_CONFIG = REPO/'scripts/jobs/specificity_ladder_a2.json'
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
              ('train-samples', len(selected['train'])), ('val-samples', len(selected['validation'])),
              ('test-samples', len(selected['test'])), ('max-seq-length', manifest['max_seq_length']),
              ('seed', seed), ('output-dir', str(output))]
    return [sys.executable, str(REPO/'train.py')] + [x for key, value in values for x in ('--'+key, str(value))] + GATE_FLAGS


def expected_config(command):
    """Subset of actual run_io.resolved_run_config frozen by this command."""
    expected = {'edge_pruning': False, 'deception_runtime_filter': False,
                'std_runtime_filter': False, 'skip_node_pruning': False}
    numeric = {'node_lambda_sparsity': float, 'node_epochs': int, 'lr': float, 'batch_size': int,
               'faithfulness_weight': float, 'train_samples': int, 'val_samples': int,
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


def plan_run(config, manifest, *, task, condition, seed, timing_epochs=None):
    command = build_command(config, manifest, task=task, condition=condition, seed=seed, timing_epochs=timing_epochs)
    selected = _selection(config, manifest, task)
    source_hashes = {name: hashlib.sha256((REPO/name).read_bytes()).hexdigest()
                     for name in ('train.py', 'config.py', 'pruning.py', 'run_io.py',
                                  'dataset/build_twin_training.py', 'scripts/twin_training.py')}
    return dict(task=task, condition=condition, seed=seed, model=config['model'],
                purpose='timing-only' if timing_epochs is not None else 'scientific-seed',
                actual_epochs=timing_epochs or config['node_epochs'], planned_epochs=config['node_epochs'],
                fleet_ready=manifest['fleet_ready'], cohort=manifest['cohort'],
                source_commit=manifest['source_commit'], build_hash=manifest['build_hash'],
                build_manifest_sha256=digest(manifest), source_hashes=source_hashes,
                frozen_config_sha256=digest(config), resolved_config_sha256=digest(expected_config(command)),
                selected_ids=selected, counts={s: len(v) for s,v in selected.items()},
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
    receipt = dict(provenance, status='failed', errors=[], exit_code=None,
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
        native = json.loads((out/'run_manifest.json').read_text())
        native['orchestrator_source_commit'] = commit
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('dry-run', 'run'), default='dry-run')
    parser.add_argument('--config', required=True)
    parser.add_argument('--build-manifest', required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--condition', choices=('D', 'I'), required=True)
    parser.add_argument('--seed', type=int, choices=(42, 1, 123), required=True)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--timing-epochs', type=int)
    args = parser.parse_args(argv)
    config = json.loads(Path(args.config).read_text())
    manifest = json.loads(Path(args.build_manifest).read_text())
    config.setdefault('data_root', str(Path(args.build_manifest).resolve().parent))
    plan = plan_run(config, manifest, task=args.task, condition=args.condition,
                    seed=args.seed, timing_epochs=args.timing_epochs)
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
