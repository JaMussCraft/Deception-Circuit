#!/usr/bin/env python
"""Bounded offline SDR diagnostic; prepare/dry-run never load model weights."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
from types import SimpleNamespace

# Set before importing transformers/huggingface_hub (including transitive imports).
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

from evaluation.selective_diagnostics import build_manifest, content_hash, load_manifest, save_manifest, validate_manifest
from evaluation.selective_runner import (ROOT, DEFAULT_BINDINGS, FrozenTask, ResultStore,
                                         atomic_json, execute, export_blind, resolve_masks,
                                         summarize, work_plan)


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def cached_snapshot(model_path):
    path = Path(model_path)
    if path.is_dir():
        snapshot = path.resolve()
    elif model_path == 'meta-llama/Llama-3.1-8B-Instruct':
        from huggingface_hub import try_to_load_from_cache
        config = try_to_load_from_cache(model_path, 'config.json')
        if not isinstance(config, str):
            raise FileNotFoundError('original model snapshot is not cached locally')
        snapshot = Path(config).parent.resolve()
    else:
        raise FileNotFoundError('model-path must be an existing local snapshot or the canonical cached model')
    if not (snapshot / 'config.json').is_file() or not list(snapshot.glob('*.safetensors')):
        raise FileNotFoundError('cached snapshot must contain config.json and original safetensors weights')
    index = snapshot / 'model.safetensors.index.json'
    if index.exists():
        shards = set(json.loads(index.read_text())['weight_map'].values())
        if any(not (snapshot / shard).is_file() for shard in shards):
            raise FileNotFoundError('cached snapshot is missing original weight shards')
    return snapshot


def snapshot_identity(snapshot):
    snapshot = Path(snapshot).resolve()
    files = {}
    for path in sorted(snapshot.iterdir()):
        if not path.is_file():
            continue
        if path.suffix in ('.json', '.model', '.txt', '.jinja'):
            files[path.name] = {'sha256': sha256_file(path)}
        elif path.suffix == '.safetensors':
            resolved = path.resolve()
            # HF cache blobs use content-addressed names; also freeze size/mtime
            # to catch local mutable snapshot replacements without reading16GB.
            stat = resolved.stat()
            files[path.name] = {'resolved': str(resolved), 'size': stat.st_size,
                                'mtime_ns': stat.st_mtime_ns}
    return {'snapshot': str(snapshot), 'revision': snapshot.name, 'files': files}


def source_identity():
    here = Path(__file__).resolve().parent
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=here, check=True,
                              capture_output=True, timeout=20).stdout.decode().strip()
    diff = subprocess.run(['git', 'diff', '--no-ext-diff', 'HEAD', '--'], cwd=here,
                          check=True, capture_output=True, timeout=20).stdout
    paths = [here / 'evaluate_selective_deception.py', here / 'scripts/selective_deception.sbatch',
             here / 'analysis.py', here / 'config.py']
    for directory in ('evaluation', 'models', 'dataset', 'tasks'):
        paths += list((here / directory).rglob('*.py'))
    return {'revision': revision, 'dirty_diff_sha256': hashlib.sha256(diff).hexdigest(),
            'code_files': {str(p.relative_to(here)): sha256_file(p) for p in sorted(paths)}}


def prepare_identity(args):
    from transformers import AutoTokenizer
    snapshot = cached_snapshot(args.model_path)
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'  # original dataset comparison; row execution is unpadded.
    masks, mask_identity, resolved = resolve_masks(dict(args.circuit) if args.circuit else DEFAULT_BINDINGS)
    provenance = {'model': snapshot_identity(snapshot), 'source': source_identity(),
                  'dtype': 'bfloat16', 'reference': 'shared', 'ablation': 'interchange',
                  'tokenizer_settings': {'pad_token_id': tokenizer.pad_token_id,
                                         'eos_token_id': tokenizer.eos_token_id,
                                         'padding_side': tokenizer.padding_side, 'add_special_tokens': False},
                  'masks': mask_identity, 'mask_bindings': resolved[1], 'operand_configs': resolved[2],
                  'python': platform.python_version(),
                  'packages': {name: importlib.metadata.version(name) for name in ('torch', 'transformers')},
                  'decode_implementation': 'evaluation.gen_engine.generate',
                  'generation_cache': True, 'padding': 'none_per_row',
                  'continuation': 'pack_reference_continuation_only_with_eos',
                  'random_seed': 0, 'no_op_score_absolute_tolerance': 0.02}
    return provenance, tokenizer, masks, resolved


def verify_tokenization(manifest, tokenizer):
    from dataset.deception_common import DeceptionDatasetLlama
    # Verify every frozen endpoint and label, then cross-check the established
    # original SDR dataset's real prefix/readout and leading-space answer IDs.
    for row in manifest['rows']:
        for p in (row['recipient'], row['donor']):
            if p and tokenizer.encode(p['text'], add_special_tokens=False) != p['input_ids']:
                raise ValueError('cached tokenizer differs from frozen prompt tokenization')
        for label in row['labels'].values():
            if tokenizer.encode(' ' + label['text'].strip(), add_special_tokens=False) != [label['token_id']]:
                raise ValueError('cached tokenizer differs from frozen answer labels')
    by_source = {r['instance_id']: r for r in manifest['source_records']}
    clusters = manifest['clusters']
    original = DeceptionDatasetLlama([by_source[c['source_id']] for c in clusters], tokenizer, max_length=128)
    if len(original) != len(clusters):
        raise ValueError('original dataset silently dropped a frozen source')
    for i, c in enumerate(clusters):
        batch = original[i]
        p = c['prompts']['original']['D']['clean']
        n = int(batch['prefix_length'])
        if (batch['input_ids'][:n].tolist() != p['input_ids'] or n != len(p['input_ids']) or
                int(batch['target_token']) != c['labels']['D']['token_id'] or
                int(batch['distractor_token']) != c['labels']['H']['token_id']):
            raise ValueError('original SDR scoring boundary/label mismatch')


def build_context(args, provenance, tokenizer, masks, resolved):
    import torch
    from config import NodePruningConfig
    from evaluation.context import Session, resolve_train_args
    from models import ModelAdapter
    from analysis import disable_dropout
    specs, bound, configs, geometry = resolved
    config = configs['D']
    cli = SimpleNamespace(device=args.device, reference='shared', hf_token=None,
                          data_dir=args.data_dir, test_samples=None, std_variant=None,
                          null_count=1, n_random=1, null_start=0, null_seed=0, null_alloc='uniform',
                          knockout_granularity='finest', sanity_granularity='all', ablation='interchange')
    train_args, node_config = resolve_train_args(config, cli)
    session = Session(cli, bound['D'], config, train_args, node_config, geometry, specs, [])
    adapter = ModelAdapter('llama-8b-instruct')
    adapter.hf_id = provenance['model']['snapshot']  # Existing adapter loads only this absolute directory.
    session.adapter = adapter
    session.tokenizer = tokenizer
    session.node_model = adapter.build_node_model(node_config, args.device)
    disable_dropout(session.node_model)
    session._check_geometry('llama-8b-instruct')
    if session.node_model.config._name_or_path != adapter.hf_id:
        raise ValueError('loaded weights do not match frozen local snapshot')
    session._current_masks = masks['core']
    task = SimpleNamespace(args=train_args, label='frozen_sdr', build=FrozenTask, home_run_dir=None)
    return session.context_for(specs[0], task, args.output_dir)


def binding(value):
    name, sep, path = value.partition('=')
    if not sep or name not in DEFAULT_BINDINGS:
        raise argparse.ArgumentTypeError('circuit must be D=path, H=path, F=path or m=path')
    return name, path


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--data-dir', default=str(ROOT / 'data/datasets/sdr'))
    p.add_argument('--model-path', default='meta-llama/Llama-3.1-8B-Instruct')
    p.add_argument('--circuit', action='append', type=binding)
    p.add_argument('--prepare', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--run', action='store_true')
    p.add_argument('--summarize', action='store_true')
    p.add_argument('--export-blind', type=Path)
    p.add_argument('--subset', choices=('all', 'smoke'), default='all')
    p.add_argument('--device', default='cuda')
    p.add_argument('--reference', choices=('shared',), default='shared')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.run or args.summarize or args.export_blind:
        import fcntl
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with (args.output_dir / 'writer.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError('output directory has an active writer or summary/export process') from exc
            return run_cli(args)
    return run_cli(args)


def run_cli(args):
    if not any((args.prepare, args.dry_run, args.run, args.summarize, args.export_blind)):
        raise ValueError('select --prepare, --dry-run, --run, --summarize or --export-blind')
    if args.summarize or args.export_blind:
        if args.prepare or args.run:
            raise ValueError('summary/export is separate from prepare/run')
        manifest = load_manifest(args.manifest)
        frozen_run = json.loads((args.output_dir / 'run.json').read_text())
        store = ResultStore(args.output_dir, manifest, frozen_run['provenance'])
        summary = summarize(manifest, store)
        atomic_json(args.output_dir / 'summary.json', summary)
        if args.export_blind:
            export_blind(manifest, store, args.export_blind)
        print(json.dumps(summary, sort_keys=True))
        return 0
    provenance, tokenizer, masks, resolved = prepare_identity(args)
    if args.prepare:
        if args.manifest.exists():
            raise FileExistsError('manifest already exists; use --manifest with --dry-run/--run to resume')
        from dataset.deception_common import load_or_generate_deception_data
        from dataset.matched_honest import load_matched_honest_pool
        records = load_or_generate_deception_data(args.data_dir, 'test')
        manifest = build_manifest(records, load_matched_honest_pool('sdr'), tokenizer,
                                  source_metadata={'artifact_identity': provenance, 'data_dir': str(Path(args.data_dir).resolve())})
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        save_manifest(manifest, args.manifest)
    else:
        manifest = load_manifest(args.manifest)
        original_identity = manifest['provenance'].get('artifact_identity')
        if original_identity is not None and original_identity != provenance:
            raise ValueError('manifest artifact identity differs from current source/model/masks; do not reuse outcomes')
    verify_tokenization(manifest, tokenizer)
    plan = {'selected_work': work_plan(manifest, args.subset), 'full_manifest': work_plan(manifest),
            'masks': {label: value['counts'] for label, value in provenance.get('masks', {}).items()},
            'resources': {'gpu_count': 1, 'memory_gb': 64, 'cpu_count': 1,
                          'wrapper_default_minutes': 15, 'no_external_api': True},
            'provenance_hash': content_hash(provenance), 'source_revision': provenance.get('source', {}).get('revision')}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_dir / ('plan-' + args.subset + '.json'), plan)
    if not args.run:
        print(json.dumps(plan, sort_keys=True))
        return 0
    if args.device != 'cuda':
        raise ValueError('real8B execution requires root-launched Slurm CUDA; dry-run uses CPU only')
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('no GPU allocation; prepare/dry-run are available on CPU')
    provenance = dict(provenance, hardware={'gpu': torch.cuda.get_device_name(0),
                                          'capability': list(torch.cuda.get_device_capability(0)),
                                          'cuda': torch.version.cuda})
    store = ResultStore(args.output_dir, manifest, provenance)
    ctx = build_context(args, provenance, tokenizer, masks, resolved)
    summary = execute(manifest, store, ctx, masks, args.subset)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
