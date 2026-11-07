"""Immutable derive / score / assemble stages for transparent user controls.

Only the native scoring loader touches model weights, after the allocation and
protected-registry checks. No stage runs git or records credentials.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

from dataset import build_user_inversion_v2 as pure
from dataset import deception_common as dc

REPO = Path(__file__).resolve().parents[1]
SPLITS = ('train', 'validation', 'test')
SCORER = 'dataset.deception_common.score_prompts'
PRIMARY_REGISTRY = Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/held_out.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n' for row in rows))


def publish(target, writer):
    """Stage complete artifacts beside destination, then rename; never resume in place."""
    target = Path(target)
    require(not target.exists(), 'output exists: ' + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.' + target.name + '-', dir=str(target.parent)))
    try:
        writer(temporary)
        require(not target.exists(), 'output exists: ' + str(target))
        temporary.rename(target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true', help='CPU score preflight: validate inputs, no model or writes')
    p.add_argument('--stage', choices=('derive', 'score', 'assemble'), required=True)
    p.add_argument('--tasks', nargs='+', choices=pure.TASKS, default=list(pure.TASKS))
    p.add_argument('--splits', nargs='+', choices=SPLITS, default=list(SPLITS))
    p.add_argument('--data-dir', default=str(REPO / 'data/datasets'))
    p.add_argument('--work-dir', default=str(REPO / 'outputs/_analyses/specificity-ladder/user-control-cpu'))
    p.add_argument('--score-dir', help='Separate immutable scoring root (required for score/assemble)')
    p.add_argument('--output-dir', help='Separate immutable assembly root (required for assemble)')
    p.add_argument('--request-pool', default=pure.REQUEST_POOL_PATH)
    p.add_argument('--margin', type=float, choices=(.7, .5), default=.7)
    p.add_argument('--max-seq-length', type=int, default=256, choices=(256,))
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--model', default=dc.DEFAULT_MODEL)
    p.add_argument('--model-revision')
    p.add_argument('--tokenizer-revision')
    p.add_argument('--commit', help='Full scoring code commit supplied by orchestrator')
    p.add_argument('--registry', action='append', default=[], help='Additional protected registry, unioned with primary and worktree')
    return p


def tokenizer_identity(tokenizer, requested=None, injected=False):
    identity = getattr(tokenizer, 'name_or_path', None) or type(tokenizer).__name__
    revision = (getattr(tokenizer, 'init_kwargs', {}) or {}).get('_commit_hash')
    revision = revision or getattr(tokenizer, '_commit_hash', None)
    revision = revision or getattr(tokenizer, '_user_inversion_actual_revision', None)
    if revision is None and not injected:
        from huggingface_hub import hf_hub_download
        cached = hf_hub_download(identity, 'tokenizer_config.json', revision=requested, local_files_only=True)
        revision = Path(cached).parent.name
    if requested and revision:
        require(requested == revision, 'tokenizer revision mismatch with actual cached snapshot')
    revision = revision or (requested if injected else None)
    require(bool(revision), 'missing actual tokenizer revision')
    return {'tokenizer': identity, 'tokenizer_revision': revision}


def load_tokenizer(args):
    import transformers
    from huggingface_hub import hf_hub_download
    cached = Path(hf_hub_download(args.model, 'tokenizer_config.json', revision=args.tokenizer_revision,
                                 local_files_only=True))
    actual_revision = cached.parent.name
    require(not args.tokenizer_revision or actual_revision == args.tokenizer_revision,
            'actual tokenizer revision differs from supplied snapshot')
    # 4.57.3 unconditionally calls model_info in its Mistral regex heuristic
    # for canonical IDs, even with local_files_only and fix_mistral_regex=False.
    # Loading this same pinned snapshot avoids that unrelated online heuristic.
    normalize = transformers.__version__ == '4.57.3'
    identifier = str(cached.parent) if normalize else args.model
    tokenizer = transformers.AutoTokenizer.from_pretrained(identifier, revision=actual_revision,
                                                            local_files_only=True)
    tokenizer._user_inversion_actual_revision = actual_revision
    tokenizer._user_inversion_loading = {
        'actual_load_path': identifier, 'resolved_snapshot': str(cached.parent),
        'logical_identifier': args.model, 'identity_normalized': normalize,
        'compatibility_reason': 'transformers4.57.3 offline Mistral heuristic bypass' if normalize else None,
        'tokenizer_config_sha256': file_hash(cached)}
    if normalize:
        tokenizer.name_or_path = args.model
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def tokenizer_loading(tokenizer):
    return getattr(tokenizer, '_user_inversion_loading', {
        'actual_load_path': getattr(tokenizer, 'name_or_path', type(tokenizer).__name__),
        'logical_identifier': getattr(tokenizer, 'name_or_path', type(tokenizer).__name__),
        'identity_normalized': False, 'compatibility_reason': 'injected tokenizer'})


def sources(args):
    """Read ALL splits before selecting scope, validating within-task separation."""
    contexts = {}
    for task in args.tasks:
        config = dc.load_dataset_config(str(Path(args.data_dir) / task))
        require(config.get('model') == args.model, task + ': model differs from original dataset')
        all_rows, all_hashes = {}, {}
        for arm, suffix in (('D', ''), ('H', '_honest')):
            directory = Path(args.data_dir) / (task + suffix)
            hconfig = dc.load_dataset_config(str(directory))
            require(hconfig.get('model') == args.model, task + ': source model mismatch')
            seen = set()
            all_rows[arm], all_hashes[arm] = {}, {}
            for split in SPLITS:
                rows = list(dc.load_or_generate_deception_data(str(directory), split))
                ids = [r['instance_id'] for r in rows]
                require(len(set(ids)) == len(ids), task + ': duplicate source ids')
                require(not seen.intersection(ids), task + ': cross-split source ids')
                seen.update(ids)
                all_rows[arm][split] = rows
                all_hashes[arm][split] = pure._hash(rows)
            all_hashes[arm]['config'] = pure._hash(hconfig)
        for split in SPLITS:
            require([r['instance_id'] for r in all_rows['D'][split]] ==
                    [r['instance_id'] for r in all_rows['H'][split]], task + ': ordered D/H ids mismatch')
        contexts[task] = {'rows': all_rows, 'source_hashes': all_hashes, 'config': config}
    return contexts


def prompt_hash(pairs):
    return pure._hash([{arm: {stream: pure._hash(pair[arm][stream + '_prompt'])
                             for stream in pure.STREAMS} for arm in pure.ARMS}
                       for pair in pairs])


def derive(args, tokenizer, identity, contexts, pool):
    outputs = []
    for task, ctx in contexts.items():
        for split in args.splits:
            target = Path(args.work_dir) / task / split
            require(not target.exists(), 'output exists: ' + str(target))
            pairs, report = pure.derive_pairs(tokenizer, task, ctx['rows']['D'][split],
                                              ctx['rows']['H'][split], pool, args.max_seq_length)
            manifest = dict(schema_version=1, kind='user_inversion_derived', task=task, split=split,
                            model=args.model, **identity, tokenizer_loading=tokenizer_loading(tokenizer),
                            max_seq_length=args.max_seq_length,
                            source_hashes=ctx['source_hashes'], request_pool_hash=pure._hash(pool),
                            prompt_hash=prompt_hash(pairs), count=len(pairs),
                            ids=[pair['instance_id'] for pair in pairs])
            outputs.append((target, pairs, report, manifest))
    for target, pairs, report, manifest in outputs:
        def writer(directory):
            write_jsonl(directory / 'pairs.jsonl', pairs)
            write_json(directory / 'derivation_report.json', report)
            manifest['files'] = {name: file_hash(directory / name) for name in ('pairs.jsonl', 'derivation_report.json')}
            write_json(directory / 'derivation_manifest.json', manifest)
        publish(target, writer)
        print('{}: source={} derived={} rejected={} -> {}'.format(target, report['source_count'], len(pairs), len(report['rejected']), target))
    return 0


def verified_derivation(args, task, split, ctx, pool, identity=None, tokenizer=None):
    directory = Path(args.work_dir) / task / split
    require(directory.is_dir(), 'missing derivation scope: ' + str(directory))
    manifest = read_json(directory / 'derivation_manifest.json')
    for name in ('pairs.jsonl', 'derivation_report.json'):
        require(file_hash(directory / name) == manifest['files'][name], 'derivation file hash mismatch: ' + name)
    require(manifest['source_hashes'] == ctx['source_hashes'], 'source hash mismatch')
    require(manifest['request_pool_hash'] == pure._hash(pool), 'request pool hash mismatch')
    require(manifest['task'] == task and manifest['split'] == split and manifest['model'] == args.model,
            'derivation scope/model mismatch')
    require(manifest['max_seq_length'] == args.max_seq_length, 'sequence limit mismatch')
    if identity is not None:
        require(all(manifest[k] == v for k, v in identity.items()), 'derived tokenizer identity/revision mismatch')
    if args.tokenizer_revision:
        require(manifest['tokenizer_revision'] == args.tokenizer_revision, 'derived tokenizer revision mismatch')
    pairs = read_jsonl(directory / 'pairs.jsonl')
    ids = [r['instance_id'] for r in pairs]
    require(ids == manifest['ids'] and len(ids) == len(set(ids)) == manifest['count'], 'derived ordered ids mismatch')
    require(prompt_hash(pairs) == manifest['prompt_hash'], 'prompt hash mismatch')
    source = {arm: {r['instance_id']: r for r in ctx['rows'][arm][split]} for arm in ('D', 'H')}
    request_ids = {r['id']: r for r in pool}
    for pair in pairs:
        iid = pair['instance_id']
        require(iid in source['D'] and iid in source['H'], 'unknown source id')
        hashes = {arm: pure._hash(source[arm][iid]) for arm in ('D', 'H')}
        require(pair['source_row_hashes'] == hashes and
                all(pair[arm]['source_row_hashes'] == hashes for arm in pure.ARMS), 'pair source hash mismatch')
        require(pair['request_id'] in request_ids and pair['request_hash'] == pure._hash(request_ids[pair['request_id']]),
                'pair request hash mismatch')
        for arm in pure.ARMS:
            for stream in pure.STREAMS:
                prompt = pair[arm][stream + '_prompt']
                expected = pair['stream_metadata'][stream][arm + '_prompt_hash']
                require(pure._hash(prompt) == expected, 'pair prompt hash mismatch')
                if tokenizer is not None:
                    require(len(tokenizer.encode(prompt, add_special_tokens=False)) <= 256, 'prompt would truncate')
    return pairs, manifest, file_hash(directory / 'derivation_manifest.json')


def check_registry(args, contexts):
    """Union primary, branch and optional registries by actual frozen instance ids."""
    candidates = {task: {r['instance_id'] for split in args.splits
                        for r in ctx['rows']['D'][split]} for task, ctx in contexts.items()}
    paths = list(dict.fromkeys([Path(PRIMARY_REGISTRY), REPO / 'docs/research/held_out.json'] +
                              [Path(p).resolve() for p in args.registry]))
    digests = {}
    for registry_path in paths:
        require(registry_path.is_file(), 'missing required protected registry: ' + str(registry_path))
        registry = read_json(registry_path)
        require(isinstance(registry, dict) and registry.get('schema') == 1 and
                isinstance(registry.get('sets'), list), 'invalid protected registry')
        digests[str(registry_path)] = file_hash(registry_path)
        registry_root = registry_path.parent.parent.parent
        for entry in registry['sets']:
            require(isinstance(entry, dict), 'unknown protected registry entry')
            if 'path' in entry:
                path = (registry_root / entry['path']).resolve()
                require(path.is_relative_to(registry_root.resolve()), 'escaped protected registry path')
                require(path.is_file() and file_hash(path) == entry.get('sha256'), 'protected set file missing/hash mismatch')
                raw = read_json(path)
                if isinstance(raw, dict):
                    raw = raw.get('instance_ids', raw.get('ids', raw.get('rows')))
                require(isinstance(raw, list), 'unsupported protected id file')
                ids = [row.get('instance_id') if isinstance(row, dict) else row for row in raw]
                require(len(ids) == entry.get('n'), 'protected set count mismatch')
            else:
                ids = entry.get('instance_ids', entry.get('ids'))
            require(isinstance(ids, list) and all(isinstance(i, str) for i in ids) and
                    len(set(ids)) == len(ids), 'invalid protected ids; review required')
            tasks = [entry['task']] if entry.get('task') else list(candidates)
            require(not any(candidates.get(task, set()).intersection(ids) for task in tasks), 'protected registry id overlap')
    return digests


def resolve_model_snapshot(args):
    from huggingface_hub import hf_hub_download
    index_path = Path(hf_hub_download(args.model, 'model.safetensors.index.json',
                                    revision=args.model_revision, local_files_only=True))
    snapshot = str(index_path.parent)
    require(index_path.parent.name == args.model_revision, 'actual model revision differs from supplied snapshot')
    for filename in ['config.json'] + sorted(set(read_json(index_path)['weight_map'].values())):
        cached = Path(hf_hub_download(args.model, filename, revision=args.model_revision, local_files_only=True))
        require(cached.parent == index_path.parent and cached.is_file(), 'missing/mixed model shard revision')
    return snapshot


def native_model_loader(tokenizer):
    def load(args):
        require(bool(os.environ.get('SLURM_JOB_ID')), 'native scoring requires Slurm allocation')
        import torch
        require(torch.cuda.is_available(), 'native scoring requires allocated CUDA device')
        from dataset.pilot_v2 import load_model
        snapshot = resolve_model_snapshot(args)
        native_args = copy.copy(args)
        native_args.model = snapshot
        native_args.hf_token = None
        load_start = time.monotonic()
        torch.cuda.reset_peak_memory_stats()
        model, device = load_model(native_args)
        def score_fn(prompts, words):
            require(all(len(tokenizer.encode(p, add_special_tokens=False)) <= 256 for p in prompts), 'prompt would truncate')
            return dc.score_prompts(prompts, words, model, tokenizer, device,
                                    max_length=256, batch_size=8, desc='user inversion')
        score_fn.execution_provenance = {'dtype': str(next(model.parameters()).dtype), 'device': str(device),
                                        'model_snapshot': str(snapshot), 'model_revision': Path(snapshot).name,
                                        'model_load_seconds': time.monotonic() - load_start,
                                        'gpu': torch.cuda.get_device_name()}
        score_fn.resource_metrics = lambda: {'peak_memory_allocated_bytes': torch.cuda.max_memory_allocated(),
                                            'peak_memory_reserved_bytes': torch.cuda.max_memory_reserved()}
        return score_fn
    return load


def score(args, tokenizer, identity, contexts, pool, model_loader):
    require(args.score_dir, '--score-dir required')
    require(args.commit and re.fullmatch('[0-9a-f]{40}', args.commit), 'full 40-hex --commit required')
    require(bool(args.model_revision) and bool(args.tokenizer_revision), 'explicit model/tokenizer revisions required')
    require(args.limit == 0 or (args.limit == 32 and args.splits == ['test']), 'limited pilot requires --splits test --limit 32')
    if model_loader is None and not args.dry_run:
        require(bool(os.environ.get('SLURM_JOB_ID')), 'native scoring requires Slurm allocation')
    prepared = []
    for task, ctx in contexts.items():
        for split in args.splits:
            target = Path(args.score_dir) / task / split
            require(not target.exists(), 'output exists: ' + str(target))
            pairs, manifest, digest = verified_derivation(args, task, split, ctx, pool, identity, tokenizer)
            selected = pairs[:args.limit] if args.limit else pairs
            prepared.append((task, split, target, selected, manifest, digest))
    registry_hash = check_registry(args, contexts)  # immediately before model load
    if args.dry_run:
        snapshot = resolve_model_snapshot(args) if model_loader is None else 'injected loader'
        print(json.dumps({'kind': 'score_preflight', 'model_loaded': False, 'writes': False,
                          'command': args.command, 'model_snapshot': snapshot,
                          'model': args.model, 'model_revision': args.model_revision, **identity,
                          'tokenizer_loading': tokenizer_loading(tokenizer),
                          'registry_sha256': registry_hash,
                          'outputs': [{'task': task, 'split': split, 'rows': len(pairs),
                                       'forwards': 4 * len(pairs), 'path': str(target),
                                       'derivation_manifest_sha256': digest}
                                      for task, split, target, pairs, manifest, digest in prepared]}, sort_keys=True))
        return 0
    score_fn = (model_loader or native_model_loader(tokenizer))(args)
    execution = getattr(score_fn, 'execution_provenance', {'dtype': 'injected', 'device': 'injected'})
    require(bool(execution.get('dtype')) and bool(execution.get('device')), 'missing execution provenance')
    if 'model_revision' in execution:
        require(execution['model_revision'] == args.model_revision, 'scorer actual model revision mismatch')
    for task, split, target, pairs, derived, digest in prepared:
        start = time.monotonic()
        records = pure.score_pairs(pairs, score_fn)
        repeated, repeat_report = [], None
        if args.limit:
            prompts = [pair['baseline'][stream + '_prompt'] for pair in pairs for stream in pure.STREAMS]
            words = [pure._canonical(pair, stream) for pair in pairs for stream in pure.STREAMS]
            repeated = list(score_fn(prompts, words)) if prompts else []
            original = [record['baseline'][stream] for record in records for stream in pure.STREAMS]
            require(len(repeated) == len(original), 'baseline replay length mismatch')
            for record in repeated:
                pure._validate_score(record)
            differences = [abs(a['margin'] - b['margin']) for a, b in zip(original, repeated)]
            tolerance = .02  # prospective absolute native-margin tolerance, reported explicitly
            repeat_report = {'compared': len(original), 'expected': 2 * len(pairs),
                             'choice_agreement': sum(a['choice'] == b['choice'] for a, b in zip(original, repeated)),
                             'absolute_margin_tolerance': tolerance,
                             'within_tolerance': sum(d <= tolerance for d in differences),
                             'max_absolute_margin_difference': max(differences, default=None)}
        manifest = dict(schema_version=1, kind='user_inversion_scored', task=task, split=split,
                        source_commit=args.commit, model=args.model, model_revision=args.model_revision,
                        **identity, tokenizer_loading=tokenizer_loading(tokenizer), **{k: v for k, v in execution.items() if k != 'model_revision'},
                        scorer=SCORER, max_seq_length=256, batch_size=8,
                        source_hashes=derived['source_hashes'], request_pool_hash=pure._hash(pool),
                        prompt_hash=prompt_hash(pairs), derivation_manifest_sha256=digest,
                        derived_count=derived['count'], count=len(records), forwards=4 * len(records),
                        ids=[r['instance_id'] for r in records], limited=bool(args.limit), limit=args.limit,
                        baseline_repeat=repeat_report, baseline_repeat_forwards=len(repeated),
                        requested_tasks=args.tasks, requested_splits=args.splits,
                        command=args.command, threshold=args.margin, registry_sha256=registry_hash,
                        seconds=time.monotonic() - start, created=datetime.now(timezone.utc).isoformat(),
                        job_id=os.environ.get('SLURM_JOB_ID'), cluster=os.environ.get('DC_CLUSTER', 'delta'))
        manifest.update(getattr(score_fn, 'resource_metrics', lambda: {})())
        def writer(directory):
            write_jsonl(directory / 'scores.jsonl', records)
            manifest['files'] = {'scores.jsonl': file_hash(directory / 'scores.jsonl')}
            if args.limit:
                write_jsonl(directory / 'baseline_repeat.jsonl', repeated)
                manifest['files']['baseline_repeat.jsonl'] = file_hash(directory / 'baseline_repeat.jsonl')
            write_json(directory / 'run_manifest.json', manifest)
        publish(target, writer)
        print('{}: scored={} forwards={} -> {}'.format(task + '/' + split, len(records), 4 * len(records), target))
    return 0


def assemble(args, contexts, pool):
    require(args.output_dir and args.score_dir, '--output-dir and --score-dir required')
    require(args.splits == list(SPLITS) and args.limit == 0, 'full assembly scope requires all splits and no limit')
    require(Path(args.output_dir).resolve() not in (Path(args.work_dir).resolve(), Path(args.score_dir).resolve()),
            'assembly output root must be distinct')
    require(not Path(args.output_dir).exists(), 'output exists: ' + args.output_dir)
    all_outputs = []
    for task, ctx in contexts.items():
        splits, diagnostics, score_paths, manifests = {}, {}, {}, {}
        identity_fields = ('source_commit', 'model', 'model_revision', 'tokenizer', 'tokenizer_revision',
                           'request_pool_hash', 'scorer', 'dtype')
        receipt = None
        seen = set()
        for split in SPLITS:
            pairs, derived, digest = verified_derivation(args, task, split, ctx, pool)
            score_root = Path(args.score_dir) / task / split
            require((score_root / 'run_manifest.json').is_file(), 'missing scoring scope: ' + str(score_root))
            manifest = read_json(score_root / 'run_manifest.json')
            require(not manifest['limited'] and manifest['limit'] == 0, 'limited pilot cannot assemble full pool')
            require(manifest['requested_splits'] == list(SPLITS), 'partial scoring scope')
            require(manifest['task'] == task and manifest['split'] == split, 'score scope mismatch')
            require(manifest['derivation_manifest_sha256'] == digest, 'stale derivation manifest hash')
            require(manifest['source_hashes'] == derived['source_hashes'] and
                    manifest['request_pool_hash'] == derived['request_pool_hash'] and
                    manifest['prompt_hash'] == derived['prompt_hash'], 'stale score source/request/prompt hash')
            require(manifest['model'] == args.model and manifest['scorer'] == SCORER, 'score model/scorer mismatch')
            require(all(manifest[k] == derived[k] for k in ('tokenizer', 'tokenizer_revision')), 'score tokenizer mismatch')
            require(re.fullmatch('[0-9a-f]{40}', manifest['source_commit']) is not None, 'invalid scoring code commit')
            require(all(isinstance(manifest[k], str) and manifest[k] for k in identity_fields), 'missing score provenance')
            if args.commit:
                require(manifest['source_commit'] == args.commit, 'score code commit mismatch')
            if args.model_revision:
                require(manifest['model_revision'] == args.model_revision, 'score model revision mismatch')
            score_path = score_root / 'scores.jsonl'
            require(file_hash(score_path) == manifest['files']['scores.jsonl'], 'score file hash mismatch')
            records = read_jsonl(score_path)
            ids = [r['instance_id'] for r in records]
            require(ids == derived['ids'] == manifest['ids'] and len(ids) == manifest['count'] == derived['count'],
                    'missing/reordered score ids or partial scope')
            require(not seen.intersection(ids), 'cross-split score ids')
            seen.update(ids)
            kept, diagnostics[split] = pure.filter_pairs(pairs, records, margin=args.margin)
            derivation_report = read_json(Path(args.work_dir) / task / split / 'derivation_report.json')
            diagnostics[split].update(raw_count=len(ctx['rows']['D'][split]), derived_count=len(pairs),
                                      derivation_report=derivation_report)
            kept_ids = {p['instance_id'] for p in kept}
            competent = set(diagnostics[split]['paired_competent_ids'])
            for field, output_key in (('source_pressure_id', 'by_pressure_id'), ('request_id', 'by_request_id')):
                strata = {}
                for pair in pairs:
                    value = pair[field]
                    cell = strata.setdefault(value, {'derived': 0, 'retained': 0, 'paired_competent': 0})
                    cell['derived'] += 1
                    cell['retained'] += int(pair['instance_id'] in kept_ids)
                    cell['paired_competent'] += int(pair['instance_id'] in competent)
                diagnostics[split][output_key] = strata
            if split == 'test':
                diagnostics[split]['pool_gate'] = {'unique_ids': len(kept_ids), 'required': 300,
                    'passes': len(kept_ids) >= 300, 'margin': args.margin,
                    'scope': 'test only', 'does_not_complete_A1': True}
            splits[split] = kept
            fields = {k: manifest[k] for k in identity_fields}
            if receipt is None:
                receipt = dict(schema_version=1, kind='user_inversion_scored', **fields,
                               tokenizer_loading=manifest['tokenizer_loading'], score_files={})
            require(all(receipt[k] == value for k, value in fields.items()), 'mixed scoring provenance across splits')
            receipt['score_files'][split] = {'path': 'scores/' + split + '.jsonl', 'sha256': file_hash(score_path)}
            score_paths[split] = score_path
            manifests[split] = {'path': str(score_root / 'run_manifest.json'), 'sha256': file_hash(score_root / 'run_manifest.json')}
        all_outputs.append((task, ctx, splits, diagnostics, receipt, score_paths, manifests))
    def writer(root):
        from datasets import Dataset, DatasetDict
        for task, ctx, splits, diagnostics, receipt, score_paths, manifests in all_outputs:
            for arm, suffix, condition, threshold in (
                    ('inversion', '_user_inversion', 'user_inversion', args.margin),
                    ('baseline', '_user_neutral', 'user_neutral', .3)):
                directory = root / (task + suffix)
                # Explicit one shard preserves readable empty splits in both datasets versions.
                exemplar = next((pair[arm] for values in splits.values() for pair in values),
                                {'instance_id': '', 'clean_prompt': '', 'corrupt_prompt': ''})
                datasets = {split: (Dataset.from_list([pair[arm] for pair in splits[split]])
                                    if splits[split] else Dataset.from_list([exemplar]).select([]))
                            for split in SPLITS}
                DatasetDict(datasets).save_to_disk(str(directory), num_shards={s: 1 for s in SPLITS})
                (directory / 'scores').mkdir()
                for split, source_path in score_paths.items():
                    shutil.copyfile(source_path, directory / receipt['score_files'][split]['path'])
                write_json(directory / 'scoring_provenance.json', receipt)
                config = dict(ctx['config'], task=task, condition=condition, model=args.model,
                              margin_thresh=threshold, max_seq_length=256, filtered=True,
                              baseline_kind=pure.BASELINE_KIND, wording_confound=pure.WORDING_CONFOUND,
                              train_samples=len(splits['train']), val_samples=len(splits['validation']),
                              test_samples=len(splits['test']),
                              scoring_provenance={'path': 'scoring_provenance.json',
                                                  'sha256': file_hash(directory / 'scoring_provenance.json')})
                write_json(directory / 'dataset_config.json', config)
                write_json(directory / 'filter_report.json', diagnostics)
                write_json(directory / 'assembly_provenance.json', {
                    'run_manifests': manifests, 'request_pool_hash': pure._hash(pool),
                    'source_hashes': ctx['source_hashes'], 'threshold': args.margin,
                    'baseline_competence_is_diagnostic': True,
                    'positional_caveat': 'User-turn lengths differ from original D/H/F; maximum 256.',
                    'files': {str(p.relative_to(directory)): file_hash(p) for p in directory.rglob('*') if p.is_file()}})
    publish(args.output_dir, writer)
    for task, ctx, splits, diagnostics, receipt, score_paths, manifests in all_outputs:
        print('{}: retained={} paired_competent={} margin={} -> {}'.format(task,
              {s: len(splits[s]) for s in SPLITS}, {s: diagnostics[s]['paired_competent_count'] for s in SPLITS},
              args.margin, args.output_dir))
    return 0


def main(argv=None, tokenizer=None, model_loader=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(argv)
    args.command = [sys.executable, '-m', 'dataset.build_user_inversion_v2'] + argv
    require(not args.dry_run or args.stage == 'score', '--dry-run is score preflight only')
    require(len(args.tasks) == len(set(args.tasks)) and len(args.splits) == len(set(args.splits)), 'duplicate scope')
    require(args.limit >= 0 and (not args.limit or args.stage == 'score'), '--limit is pilot scoring only')
    # Canonical split order, regardless of caller order.
    args.splits = [s for s in SPLITS if s in args.splits]
    contexts = sources(args)
    pool = read_json(args.request_pool)
    if args.stage == 'assemble':
        return assemble(args, contexts, pool)
    injected = tokenizer is not None
    tokenizer = tokenizer if injected else load_tokenizer(args)
    identity = tokenizer_identity(tokenizer, args.tokenizer_revision, injected)
    if args.stage == 'derive':
        return derive(args, tokenizer, identity, contexts, pool)
    return score(args, tokenizer, identity, contexts, pool, model_loader)


if __name__ == '__main__':
    raise SystemExit(main())
