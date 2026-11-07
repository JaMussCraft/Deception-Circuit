"""File-backed CPU audit and prospective typed A2 mask algebra.

No torch/model imports, diagnostic-logit thresholding, or assessment outcomes. ``compare_masks`` fails closed unless all 18 sources
pass. Paths relative to a training execution root are resolved against the
explicit record field, never the analyst's working directory. Canonical hashes
bind returned JSON (including memberships); callers must persist it immutably.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

from scripts.twin_training import (
    GATE_FLAGS, _check_subset, _private_configs, _selection, _stored_rows, expected_config,
)
from scripts.twin_training_projection import _cohort_ruling_digest

TASKS = ('far_v2', 'sdr_v2', 'ser_v2')
SEEDS = (42, 1, 123)
EXECUTION_COMMIT = '6bd8bf5334f2e83613a129d2fcfeacf83e762191'
SNAPSHOT_SHA256 = 'eb5ca854a7157529095ab820252a246f114250144120c6fc66de98bed9733918'
ARCHIVE_SHA256 = '1a4e6397bb5924f22fc548fb8899a925a58f0b3640730a2602300e7e8c045ac6'
FLEET_PLAN_SHA256 = 'b424e10e7d13e7c7686df9753f08f45fc84da37bce44bb99ae4df270c4395ae8'
MODEL_REVISION = '0e9e39f249a16976918f6564b8830bc894c89659'
BUILD_HASH = 'c79830a14f94a6f8a7bce937dba8d2444abfc911676f7f71016b37ca6463781f'
RULING_SHA256 = '42c385f1d7d99adddc7b01be19389b2645be6445593abb5254ba4b1cbead8603'
SOURCE_HASHES = {
    'train.py': 'feb6c279db3862e5367315cb044959d4f0dee5d3bb4525dab1d7b49fb2ed7b35',
    'config.py': 'ecc71842f723dd012e9f7de77c15f518c76df4e8775da63dfd1dc2a6535943ee',
    'pruning.py': '52588f0a29fccbff2c11b57f84ba7f35b0f47eecaf2df0708e7873e0a9ec9f1e',
    'run_io.py': '0987540b88283c73bb815f3859aa3b9943520908460bd23f0954aad4609709fe',
    'dataset/build_twin_training.py': '381e8d9a0221caf6b16c594e94a8056a673f3167d35da5df6e1fa686f8f62367',
    'scripts/twin_training.py': '6707caff04a961d7848031d412c139a33918d902d1e8ba87c0c3dbd2df85a341',
}
FROZEN_CONFIG = dict(model='llama-8b-instruct', tasks=list(TASKS), conditions=['D','I'],
    seeds=list(SEEDS), node_lambda_sparsity=.3, node_epochs=500, lr=.03, batch_size=7,
    faithfulness_weight=1, deception_margin_loss=.7, init_value=.5,
    sparsity_warmup_steps=1000, sample_caps=dict(train=200, validation=200, test=1000),
    output_root='outputs/_training_specificity_ladder/a2-h200')


def digest(value):
    """Wrapper-compatible canonical JSON content hash (not a file hash)."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, 'duplicate JSON object key: '+key)
            result[key] = value
        return result
    value = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    _require(isinstance(value, dict), 'expected JSON object: '+str(path))
    return value


def _resolve(root, path):
    _require(isinstance(path, str) and bool(path), 'missing file path')
    return (root / path).resolve()


def _binary(values, width, label):
    _require(isinstance(values, list) and len(values) == width and
             all(type(v) in (int, float) and v in (0, 1) for v in values),
             'invalid binary mask dimension/value: '+label)
    return values


def audit_export(active, node_config):
    """Check native lists against eval-binary masks and finalized hierarchy.

    Ungated heads are absent from extract_active_nodes (its native convention),
    while ungated MLP blocks are listed as active. Neither is learned evidence.
    Ancestors use masks, never get_num_active's distinct L0 statistic cutoff.
    """
    masks = active.get('masks')
    _require(isinstance(masks, dict), 'missing native masks')
    allowed = {'embedding', 'layers', 'attention_blocks', 'mlp_blocks', 'attention_heads',
               'attention_neurons', 'mlp_hidden', 'mlp_output'}
    _require(set(masks) <= allowed, 'unknown native mask kind')
    for key, flag in [('attention_neurons','prune_attention_neurons'),
                      ('mlp_hidden','prune_mlp_hidden'), ('mlp_output','prune_mlp_output')]:
        _require(not node_config.get(flag) and key not in masks,
                 'finer-grained gate representation mismatch: '+key)
    for key, flag in [('embedding','prune_embedding'), ('layers','prune_full_layers'),
                      ('attention_blocks','prune_attention_blocks'), ('mlp_blocks','prune_mlp_blocks'),
                      ('attention_heads','prune_attention_heads')]:
        _require((key in masks) == bool(node_config.get(flag)), 'gate/config mismatch: '+key)
    embedding = _binary([masks['embedding']], 1, 'embedding')[0] if 'embedding' in masks else 1
    layers = _binary(masks['layers'], 32, 'layers') if 'layers' in masks else [1]*32
    attention = _binary(masks['attention_blocks'],32,'attention_blocks') if 'attention_blocks' in masks else [1]*32
    mlps = _binary(masks['mlp_blocks'],32,'mlp_blocks') if 'mlp_blocks' in masks else [1]*32
    heads = masks.get('attention_heads', {})
    if 'attention_heads' in masks:
        _require(isinstance(heads, dict) and set(heads) == {str(l) for l in range(32)},
                 'attention head layer dimension mismatch')
        for layer, values in heads.items():
            _binary(values,32,'heads/'+layer)
    for l in range(32):
        if 'attention_blocks' in masks and str(l) in heads and not any(heads[str(l)]):
            _require(not attention[l], 'bottom-up inconsistency: attention block')
        if 'layers' in masks and 'attention_blocks' in masks and 'mlp_blocks' in masks:
            if not attention[l] and not mlps[l]:
                _require(not layers[l], 'bottom-up inconsistency: full layer')
    # Finalization forces descendants of inactive ancestors to zero. Omitted
    # child gates have no vector to audit; they remain explicit background.
    for l in range(32):
        ancestor = bool(layers[l])
        if not ancestor:
            if 'attention_blocks' in masks:
                _require(not attention[l], 'ancestor inconsistency: attention block')
            if 'mlp_blocks' in masks:
                _require(not mlps[l], 'ancestor inconsistency: MLP block')
        if str(l) in heads and not (ancestor and attention[l]):
            _require(not any(heads[str(l)]), 'ancestor inconsistency: heads')
    reconstructed_heads = {str(l):[h for h,v in enumerate(heads.get(str(l), [])) if v]
                           for l in range(32) if attention[l] and any(heads.get(str(l), []))}
    reconstructed_mlps = [l for l in range(32) if mlps[l]]
    raw_heads, raw_mlps = active.get('active_heads'), active.get('active_mlps')
    _require(isinstance(raw_heads, dict) and isinstance(raw_mlps, list), 'invalid native active lists')
    for layer, values in raw_heads.items():
        _require(layer in {str(l) for l in range(32)} and isinstance(values,list) and bool(values)
                 and len(set(values)) == len(values) and all(type(h) is int and 0<=h<32 for h in values),
                 'invalid/duplicate native head key')
    _require(len(set(raw_mlps)) == len(raw_mlps) and
             all(type(l) is int and 0<=l<32 for l in raw_mlps), 'invalid/duplicate native MLP key')
    normalized_heads = {k:sorted(v) for k,v in raw_heads.items()}
    _require(normalized_heads == reconstructed_heads and sorted(raw_mlps) == reconstructed_mlps,
             'native list/export mask parity discrepancy')
    selected = {('head',int(l),h) for l,hs in reconstructed_heads.items() for h in hs}
    if 'mlp_blocks' in masks:
        selected |= {('mlp',l,0) for l in reconstructed_mlps}
    background = dict(heads=[l for l in range(32) if str(l) not in heads],
                      mlps=reconstructed_mlps if 'mlp_blocks' not in masks else [])
    return selected, dict(status='pass', native_active_heads=normalized_heads,
        reconstructed_active_heads=reconstructed_heads, native_active_mlps=raw_mlps,
        reconstructed_active_mlps=reconstructed_mlps, dimensions=dict(layers=32, heads_per_layer=32),
        ancestor_consistency=True, implicit_active_background=background,
        membership_semantics='eval_binary_export_with_finalized_ancestors',
        count_diagnostic=active.get('statistics'), selected_counts=_group(selected)['counts'])


def _audit_execution(root, record, task, condition, seed, cache):
    """Authenticate the entire approved archive/snapshot and exact fleet cell."""
    key = ('execution', str(root))
    if key not in cache:
        snapshot_path = root.parent/'snapshot.json'
        archive_path = root.parent/'application.tar'
        fleet_path = root/'outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json'
        _require(_sha(snapshot_path) == SNAPSHOT_SHA256, 'frozen snapshot file hash mismatch')
        _require(_sha(archive_path) == ARCHIVE_SHA256, 'frozen source archive hash mismatch')
        _require(_sha(fleet_path) == FLEET_PLAN_SHA256, 'frozen fleet plan hash mismatch')
        snapshot, fleet = _read(snapshot_path), _read(fleet_path)
        _check_subset(snapshot, dict(application_commit=EXECUTION_COMMIT, archive_sha256=ARCHIVE_SHA256))
        _require(Path(snapshot['runtime_root']).resolve() == root, 'snapshot execution root mismatch')
        _check_subset(fleet, dict(application_commit=EXECUTION_COMMIT, snapshot_manifest_sha256=SNAPSHOT_SHA256))
        _require(Path(fleet['snapshot_manifest']).resolve() == snapshot_path.resolve(), 'fleet snapshot identity mismatch')
        dependencies = snapshot.get('source_files_sha256')
        _require(isinstance(dependencies, dict) and len(dependencies) == 207, 'incomplete frozen dependency inventory')
        _require(set(SOURCE_HASHES) <= set(dependencies), 'missing launch dependency')
        for name, value in dependencies.items():
            relative = Path(name)
            _require(not relative.is_absolute() and '..' not in relative.parts, 'invalid dependency path')
            path = root/relative
            _require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
                     'missing/redirected frozen dependency: '+name)
            _require(_sha(path) == value, 'frozen dependency file hash mismatch: '+name)
        for name, value in SOURCE_HASHES.items():
            _require(dependencies[name] == value, 'launch/snapshot source identity mismatch: '+name)
        links = snapshot.get('live_links')
        _require(isinstance(links,dict) and set(links) == {'outputs','data','logs','docs/research/held_out.json'},
                 'unexpected live-link contract')
        for name, target in links.items():
            path = root/name
            _require(path.is_symlink() and path.resolve() == Path(target).resolve(), 'snapshot live-link mismatch: '+name)
        cells = fleet.get('cells')
        _require(isinstance(cells,list) and len(cells) == 18 and
                 {(c.get('task'),c.get('condition'),c.get('seed')) for c in cells} ==
                 set(itertools.product(TASKS,('D','I'),SEEDS)), 'incomplete frozen fleet domain')
        cache[key] = dict(snapshot_manifest_sha256=SNAPSHOT_SHA256, archive_sha256=ARCHIVE_SHA256,
                          fleet_plan_sha256=FLEET_PLAN_SHA256, source_files_sha256=dependencies,
                          live_links=links, cells=cells)
    audit = cache[key]
    cell = next(c for c in audit['cells'] if (c['task'],c['condition'],c['seed']) == (task,condition,seed))
    _require(cell.get('epochs') == 500 and Path(cell['cwd']).resolve() == root and
             Path(cell['receipt']).resolve() == _resolve(root,record['receipt_path']), 'frozen fleet cell mismatch')
    argv = cell.get('argv',[])
    for flag, expected in [('--config',record['frozen_config_path']), ('--build-manifest',record['build_manifest_path']),
                           ('--receipt',record['receipt_path'])]:
        _require(flag in argv and _resolve(root,argv[argv.index(flag)+1]) == _resolve(root,expected),
                 'frozen fleet input identity mismatch: '+flag)
    return {k:v for k,v in audit.items() if k!='cells'}


def _expected_scientific_config(argv):
    """Full run_io config under the approved config.py/train.py defaults.

    Explicitly frozen instead of importing model/training code. Every structural
    lambda and both edge defaults remain part of the identity even when unused.
    """
    cfg = expected_config(argv)
    cfg.update(family='llama', std_variant='azaria', std_margin_loss=None, joint_tasks=None,
               joint_scale_epochs=True, edge_epochs=300, edge_lambda_sparsity=.95,
               edge_config=dict(sparsity_warmup_steps=500, include_output_edges=True))
    cfg['node_config']['depth_penalty_scaling'] = 0.
    for kind in ('attention_heads','attention_neurons','attention_blocks','mlp_hidden',
                 'mlp_output','mlp_blocks','full_layers','embedding'):
        cfg['node_config']['lambda_'+kind] = 1.
    return cfg


def _authenticate_rows(config, build, task, selected, cache):
    key = ('rows',config['data_root'],build['build_hash'],task)
    if key not in cache:
        for condition in ('D','I'):
            directory = Path(config['data_root'])/condition/task
            declared = []
            for split in ('train','validation','test'):
                state = _read(directory/split/'state.json')
                files = state.get('_data_files')
                _require(isinstance(files,list) and bool(files), 'missing private Arrow shard inventory')
                for item in files:
                    _require(isinstance(item,dict) and isinstance(item.get('filename'),str), 'invalid private Arrow shard entry')
                    path = directory/split/item['filename']
                    _require(path.suffix == '.arrow' and path.resolve().is_relative_to(directory.resolve()) and path.is_file(),
                             'missing/escaped private Arrow shard')
                    declared.append(str(path.resolve()))
            observed = {str(p.resolve()) for p in directory.rglob('*.arrow') if p.is_file()}
            _require(len(declared) == len(set(declared)) and set(declared) == observed,
                     'unreferenced/duplicate private Arrow shard')
        # This lazy CPU-only loader authenticates the complete source inventory,
        # row hashes, recipient/reference rows, ID order, labels and token proofs.
        try:
            _stored_rows(config,build,task,selected)
        except Exception as error:
            raise ValueError('authoritative private row authentication failed: '+str(error)) from error
        inventories = {}
        for condition in ('D','I'):
            directory = Path(config['data_root'])/condition/task
            inventories[condition] = {str(p.resolve()):_sha(p) for p in sorted(directory.rglob('*'))
                if p.is_file() and p.suffix in ('.arrow','.json','.jsonl','.csv','.tsv','.txt','.parquet')}
        cache[key] = inventories
    return cache[key]


def audit_source(record, *, _cache=None):
    """Admit one full source from real files and frozen trust anchors.

    Arrow/source rows load lazily on CPU; module import stays standard-library-only.

    Required fields: receipt_path, execution_root, frozen_config_path,
    build_manifest_path, ruling_path. Absolute native paths stay absolute;
    relative native paths resolve against execution_root, including snapshot
    roots with data/output symlinks. No caller-provided success flags are used.
    """
    _require(isinstance(record, dict), 'invalid source record')
    cache = {} if _cache is None else _cache
    root = Path(record['execution_root'])
    _require(root.is_absolute() and root.is_dir(), 'explicit absolute execution root required')
    root = root.resolve()
    paths = {k:_resolve(root,record[k]) for k in ('receipt_path','frozen_config_path','build_manifest_path','ruling_path')}
    receipt = _read(paths['receipt_path'])
    _require(receipt.get('purpose') == 'scientific-seed' and receipt.get('actual_epochs') == 500
             and receipt.get('planned_epochs') == 500, 'require scientific full500 source; timing excluded')
    _check_subset(receipt, dict(status='success', exit_code=0, errors=[], test_runner_injected=False,
        test_clock_injected=False, execution_commit=EXECUTION_COMMIT, model='llama-8b-instruct',
        fleet_ready=True, cohort='matched', build_hash=BUILD_HASH, granularity='heads-mlp', max_seq_length=256))
    task, condition, seed = receipt.get('task'), receipt.get('condition'), receipt.get('seed')
    _require(task in TASKS and condition in ('D','I') and type(seed) is int and seed in SEEDS,
             'unknown task/condition/seed')
    _check_subset(receipt, dict(recipient_condition='deceptive' if condition=='D' else 'user_inversion',
                                legacy_deception_condition='deceptive'))
    config, build, ruling = (_read(paths[k]) for k in ('frozen_config_path','build_manifest_path','ruling_path'))
    _require(config == FROZEN_CONFIG, 'frozen scientific configuration mismatch')
    _require(receipt.get('config_file_sha256') == _sha(paths['frozen_config_path']), 'frozen config file hash mismatch')
    _require(receipt.get('build_manifest_file_sha256') == _sha(paths['build_manifest_path']), 'build manifest file hash mismatch')
    _require(build.get('build_hash') == BUILD_HASH and receipt.get('build_manifest_sha256') == digest(build),
             'frozen build identity mismatch')
    _require(_sha(paths['ruling_path']) == RULING_SHA256, 'frozen ruling identity mismatch')
    _require(build.get('source_commit') == receipt.get('source_commit'), 'build source identity mismatch')
    selected = _selection(config,build,task)
    config = dict(config, data_root=str(paths['build_manifest_path'].parent))
    _require(receipt.get('frozen_config_sha256') == digest(config), 'frozen config content hash mismatch')
    _require(receipt.get('selected_ids') == selected and
             receipt.get('counts') == {s:len(ids) for s,ids in selected.items()}, 'selected IDs/count mismatch')
    ruling_hash = _cohort_ruling_digest(dict(config=config,build_manifest=build,cohort_ruling=ruling))
    execution_audit = _audit_execution(root,record,task,condition,seed,cache)
    private_hashes = _private_configs(config,build,task)
    private_inventories = _authenticate_rows(config,build,task,selected,cache)
    _require(receipt.get('dataset_config_sha256') == private_hashes, 'private config hash mismatch')
    _require(receipt.get('source_hashes') == SOURCE_HASHES, 'frozen source hash mismatch')
    for name, value in SOURCE_HASHES.items():
        _require(_sha(root/name) == value, 'execution source file hash mismatch: '+name)
    cohort_hash = digest(dict(build=build['build_hash'], ids=selected, config=config))[:16]
    expected_out = Path(config['output_root'])/f'{task}_{condition}_seed{seed}_heads-mlp_{cohort_hash}_full'
    out = _resolve(root,receipt['output_dir'])
    _require(out == (root/expected_out).resolve(), 'output identity mismatch')
    artifacts, file_hashes = {}, {}
    for name in ('config.json','active_nodes.json','results.json','history.json','run_manifest.json'):
        path = _resolve(root,receipt.get('artifacts',{}).get(name))
        _require(path == (out/name).resolve(), 'artifact path identity mismatch: '+name)
        file_hashes[name] = _sha(path)
        _require(file_hashes[name] == receipt.get('artifact_sha256',{}).get(name), 'stale artifact hash: '+name)
        artifacts[name] = _read(path)
    argv = receipt.get('argv')
    _require(isinstance(argv,list) and argv[-len(GATE_FLAGS):] == GATE_FLAGS,
             'native gate argv mismatch')
    values = [('model','llama-8b-instruct'), ('task',task), ('deception-condition','deceptive'),
        ('data-dir',str(Path(config['data_root'])/condition)), ('node-lambda-sparsity',.3), ('node-epochs',500),
        ('lr',.03), ('batch-size',7), ('faithfulness-weight',1), ('deception-margin-loss',.7),
        ('train-samples',len(selected['train'])), ('val-samples',len(selected['validation'])),
        ('test-samples',len(selected['test'])), ('max-seq-length',256), ('seed',seed), ('output-dir',str(expected_out))]
    expected_argv = [x for k,v in values for x in ('--'+k,str(v))]+GATE_FLAGS
    _require(argv[2:] == expected_argv and _resolve(root,argv[1]) == (root/'train.py').resolve(),
             'frozen training command mismatch')
    expected = expected_config(argv)
    cfg, native, results = (artifacts[k] for k in ('config.json','run_manifest.json','results.json'))
    _require(cfg == _expected_scientific_config(argv), 'full resolved configuration differs from frozen scientific defaults')
    _require(receipt.get('resolved_config_sha256') == digest(expected), 'resolved config identity mismatch')
    _check_subset(native,dict(schema='run-manifest/1', model='llama-8b-instruct', seed=seed,
        execution_commit=EXECUTION_COMMIT,build_source_commit=build['source_commit'],
        config_sha256=file_hashes['config.json'],argv=argv[1:]))
    _require(native.get('model_revision') == MODEL_REVISION, 'missing/wrong approved native model revision')
    _require(native.get('code_sha256',{}).get('train.py') == SOURCE_HASHES['train.py'], 'native train source identity mismatch')
    _require(native.get('manifest_hash') == digest({k:v for k,v in native.items() if k!='manifest_hash'}),
             'native manifest content hash mismatch')
    _require(bool(native.get('code_sha256')) and bool(native.get('dataset_files')), 'missing native file provenance')
    for field in ('code_sha256','dataset_files'):
        for name, value in native[field].items():
            _require(_sha(_resolve(root,name)) == value, 'native file hash mismatch: '+name)
    dataset_file = (Path(config['data_root'])/condition/task/'dataset_config.json').resolve()
    dataset_hashes = {str(_resolve(root,k)):v for k,v in native['dataset_files'].items()}
    _require(dataset_hashes.get(str(dataset_file)) == private_hashes[condition], 'native dataset config identity mismatch')
    _require(len(dataset_hashes) == len(native['dataset_files']) and dataset_hashes == private_inventories[condition],
             'incomplete/foreign native private dataset inventory')
    _check_subset(results,{k:expected[k] for k in ('model','task','seed','edge_pruning')})
    _require(results.get('edge_eval') is None, 'unexpected edge evaluation')
    for key in ('baseline','node_eval'):
        _require(isinstance(results.get(key),dict) and bool(results[key]), 'missing native evaluation')
        outputs = results[key].get('outputs')
        _require(isinstance(outputs,list) and [r.get('instance_id') for r in outputs] == selected['test'],
                 'native test IDs/count mismatch: '+key)
    history = artifacts['history.json'].get('node',{})
    _require(history.get('epochs') == list(range(1,501)), 'incomplete500 node history')
    _require(any(isinstance(e,dict) and type(e.get('epoch')) is int and 10<=e['epoch']<=500
                 for e in history.get('evals',[])), 'missing periodic validation')
    selected_keys, parity = audit_export(artifacts['active_nodes.json'],cfg['node_config'])
    diagnostics = results.get('node_granularity') or {}
    discrepancies = {}
    for kind, native_name in [('head','attention_heads'), ('mlp','mlp_blocks')]:
        count = diagnostics.get(native_name,{}).get('active')
        exported = _group(selected_keys)['counts'][kind]
        discrepancies[kind] = dict(diagnostic_active=count, export_active=exported,
            difference=count-exported if type(count) in (int,float) else None)
    return dict(task=task, condition=condition, seed=seed, members=_group(selected_keys),
        provenance=dict(execution_root=str(root),execution_commit=EXECUTION_COMMIT,
            source_commit=receipt['source_commit'],source_hashes=SOURCE_HASHES.copy(),build_hash=BUILD_HASH,
            execution_snapshot=execution_audit, authenticated_private_inventory=private_inventories[condition],
            selected_ids=selected, counts=receipt['counts'], under_200=len(selected['train'])<200,
            ruling_sha256=ruling_hash, file_sha256={k:_sha(v) for k,v in paths.items()},
            artifact_sha256=file_hashes, native_manifest=native, resolved_config=cfg,
            frozen_config=config, dataset_config_sha256=private_hashes),
        export_parity=parity, native_results=results, raw_active_nodes=artifacts['active_nodes.json'],
        metric_scope='native_training_test_cohort_not_ladder_assessment100',
        diagnostic_counts=dict(native_node_granularity=diagnostics, discrepancy=discrepancies,
            policy='retained_only_never_membership_or_acceptance'))


def _keys(group):
    return {tuple(k) for k in group['members']}


def _group(keys):
    members = [list(k) for k in sorted(keys)]
    return dict(members=members, counts=dict(head=sum(k[0]=='head' for k in keys),
        mlp=sum(k[0]=='mlp' for k in keys),total=len(keys)), membership_sha256=digest(members))


def jaccard(a,b):
    union = a|b
    return dict(numerator=len(a&b), denominator=len(union),
                ratio=len(a&b)/len(union) if union else None,
                reason=None if union else 'both_empty')


def pairwise(values):
    return [dict(seeds=[SEEDS[i],SEEDS[j]],**jaccard(values[i],values[j]))
            for i,j in itertools.combinations(range(3),2)]


def containment(d,i,kind='head'):
    return dict(numerator=len(d&i),denominator=len(d),ratio=len(d&i)/len(d) if d else None,
        reason=None if d else ('vacuous_no_D_heads' if kind=='head' else 'vacuous_no_D_mlps'),
        exclusive_count=len(d-i), subset=d<=i, vacuous=not d)


def compare_masks(records):
    """Audit all18 sources before computing any prospective memberships.

    The returned JSON is a detached snapshot. Its canonical comparison hash and
    each group's hash allow later immutable storage/validation; no outcome,
    specificity verdict, efficacy cutoff, or file write occurs here.
    """
    _require(isinstance(records,list) and len(records)==18, 'require exactly18 source records')
    cache = {}
    sources = [audit_source(r, _cache=cache) for r in records]
    indexed = {(s['task'],s['condition'],s['seed']):s for s in sources}
    _require(len(indexed)==18, 'duplicate task-condition-seed source')
    _require(set(indexed)==set(itertools.product(TASKS,('D','I'),SEEDS)), 'incomplete source domain')
    normalized = []
    for source in sources:
        cfg = source['provenance']['resolved_config']
        normalized.append({k:v for k,v in cfg.items() if k not in
            ('task','seed','data_dir','train_samples','val_samples','test_samples')})
    _require(all(c == normalized[0] for c in normalized), 'full resolved configuration drift')
    revisions = [s['provenance']['native_manifest'].get('model_revision') for s in sources]
    _require(all(r == revisions[0] for r in revisions), 'model revision drift')
    tasks = {}
    for task in TASKS:
        seed_rows, xs = {}, []
        for seed in SEEDS:
            ds,is_ = indexed[task,'D',seed], indexed[task,'I',seed]
            _require(ds['provenance']['selected_ids']==is_['provenance']['selected_ids'], 'unmatched D/I cohort')
            d,i = _keys(ds['members']),_keys(is_['members'])
            x,y,b,u = d-i,i-d,d&i,d|i
            rows = {k:_group(v) for k,v in dict(D=d,I=i,X=x,Y=y,B=b,U=u).items()}
            rows['containment'] = {kind:containment({k for k in d if k[0]==kind},
                {k for k in i if k[0]==kind},kind) for kind in ('head','mlp')}
            rows['whole_set_subset'] = dict(subset=d<=i,vacuous=not d)
            seed_rows[str(seed)] = rows
            xs.append(x)
        pairs = {kind:pairwise([{k for k in x if kind=='mixed' or k[0]==kind} for x in xs])
                 for kind in ('mixed','head','mlp')}
        ratios = [p['ratio'] for p in pairs['mixed']]
        head_c = [seed_rows[str(s)]['containment']['head']['ratio'] for s in SEEDS]
        predicted = [5,6,7,8,11]+([13,16] if task=='ser_v2' else []) if task!='sdr_v2' else []
        prediction = [dict(layer=l,seeds={str(s):{
            k: ['mlp',l,0] in seed_rows[str(s)][k]['members'] for k in ('D','I','B','X','Y')}
            for s in SEEDS}) for l in predicted]
        tasks[task] = dict(seeds=seed_rows, pairwise=pairs,
            minimum_jaccard=min(ratios) if all(r is not None for r in ratios) else None,
            mixed_stability_pass=all(r is not None and r>=.5 for r in ratios),
            informative_head_containment=all(c is not None and c>=.9 for c in head_c),
            core=_group(set.intersection(*xs)),exclusive_union=_group(set.union(*xs)),
            mlp_prediction=prediction,
            complete_mlp_membership={str(s):{k:[m for m in seed_rows[str(s)][k]['members'] if m[0]=='mlp']
                for k in ('D','I','X','Y','B','U')} for s in SEEDS})
    result = dict(schema='a2-mask-comparison/1',status='complete_cpu_audit',
        source_kind='twin_trained_mask_difference', sources=[indexed[k] for k in itertools.product(TASKS,('D','I'),SEEDS)],
        tasks=tasks,limitations=['Native metrics describe training test cohorts, not ladder assessment.',
            'Membership does not establish causal clause reading or specificity.',
            'Task2 banks/scoring and Task3 effect verdicts are deferred.'])
    result['comparison_sha256'] = digest(result)
    return result


def write_comparison(comparison, path):
    """Publish once, refusing replacement or a mutated comparison snapshot."""
    expected = digest({k:v for k,v in comparison.items() if k!='comparison_sha256'})
    _require(comparison.get('comparison_sha256') == expected, 'comparison hash mismatch')
    payload = json.dumps(comparison, sort_keys=True, indent=2, allow_nan=False)+'\n'
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(payload)
    return dict(path=str(path.resolve()), file_sha256=_sha(path), comparison_sha256=expected)
