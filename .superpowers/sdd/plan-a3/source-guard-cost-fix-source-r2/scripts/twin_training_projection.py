"""Offline A2 reservation gate; consumes receipts and never runs training.

Pure plan input: config, build_manifest, hardware (gpu_devices/gpu_count/cluster),
source_hashes, and optional granularity ('heads-mlp' or 'heads-only'). Seed-only
reuse is permitted; task/condition/build/shape/hardware reuse is not. No implicit
conservative bounds are supported. Pilot reservation is the ledger's aggregate
reserved GPU-hours, including failed pilots, supplied explicitly by the caller.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

from scripts.twin_training import GATE_FLAGS, expected_config

CONFIG = Path(__file__).resolve().parent/'jobs/specificity_ladder_a2.json'
ARTIFACTS = ('config.json', 'active_nodes.json', 'results.json', 'history.json', 'run_manifest.json')
SPLITS = ('train', 'validation', 'test')
SOURCES = ('train.py', 'config.py', 'pruning.py', 'run_io.py',
           'dataset/build_twin_training.py', 'scripts/twin_training.py')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def build_digest(value):
    """Match the materializer's Unicode-preserving build hash convention."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _number(value, name, minimum=0, positive=False):
    _require(type(value) in (int, float) and math.isfinite(value) and
             (value > minimum if positive else value >= minimum), 'invalid '+name)
    return value


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _hashes(value):
    return isinstance(value, dict) and bool(value) and all(_hash(v) for v in value.values())


def _validate_plan(plan):
    config, manifest = plan['config'], plan['build_manifest']
    if 'execution_commit' in plan:
        _require(isinstance(plan['execution_commit'], str) and
                 re.fullmatch('[0-9a-f]{40}', plan['execution_commit']) is not None, 'full execution commit required')
    for key, expected in dict(tasks=['far_v2','sdr_v2','ser_v2'], conditions=['D','I'], seeds=[42,1,123]).items():
        _require(config.get(key) == expected, 'plan requires complete 18 cells: '+key)
    for key, value in dict(model='llama-8b-instruct', node_epochs=500, node_lambda_sparsity=.3,
                           lr=.03, batch_size=7, faithfulness_weight=1, deception_margin_loss=.7,
                           init_value=.5, sparsity_warmup_steps=1000).items():
        _require(config.get(key) == value, 'frozen plan mismatch: '+key)
    _require(plan.get('granularity', 'heads-mlp') in ('heads-mlp','heads-only'), 'invalid granularity')
    _require(manifest.get('schema_version') == 1, 'invalid build schema')
    _require(manifest.get('build_hash') == build_digest({k:v for k,v in manifest.items() if k != 'build_hash'}),
             'build hash mismatch')
    _require(isinstance(manifest.get('source_commit'), str) and
             re.fullmatch('[0-9a-f]{40}', manifest['source_commit']) is not None, 'full source commit required')
    _require(type(manifest.get('max_seq_length')) is int and manifest['max_seq_length'] > 0, 'missing padded length')
    _require(bool(manifest.get('tokenizer')), 'missing tokenizer identity')
    _require(_hashes(plan.get('source_hashes')), 'missing expected source hashes')
    hardware = plan.get('hardware', {})
    _require(hardware.get('gpu_count') == 1 and bool(hardware.get('cluster')) and
             isinstance(hardware.get('gpu_devices'), list) and len(hardware['gpu_devices']) == 1 and
             isinstance(hardware['gpu_devices'][0], str) and
             any(name in hardware['gpu_devices'][0] for name in ('A40','H100','H200')), 'missing/unsupported hardware')
    for task in config['tasks']:
        info = manifest['tasks'][task]
        for split in SPLITS:
            ids = info['split_ids'][split]
            _require(isinstance(ids,list) and len(ids)>0 and len(ids)==len(set(ids)) and
                     info['counts'][split] == len(ids), 'invalid manifest ids/counts')
            _require(type(config['sample_caps'][split]) is int and config['sample_caps'][split]>0, 'invalid count cap')
        needed = ('D','H','I','I_neutral') if manifest.get('fleet_ready') is True else ('D','H')
        for source in needed:
            cfg = info['sources'][source]['config']
            _number(cfg.get('margin_thresh'), 'source screening threshold')
        if manifest.get('fleet_ready') is True:
            _require(manifest.get('cohort') == 'matched' and bool(info.get('a1_scoring')), 'missing matched A1 provenance')
            for source in ('I','I_neutral'):
                _require(info['sources'][source]['config'].get('baseline_kind') == 'matched_frame_neutral_request',
                         'missing A1 control identity')
    return config, manifest


def _cohort_ruling_digest(plan):
    """Bind explicit lead review to a cohort, without authenticating signatures."""
    if 'cohort_ruling' not in plan:
        return None
    ruling = plan['cohort_ruling']
    fields = {'schema_version', 'ruling_id', 'decision', 'session', 'build_hash',
              'selected_ids_sha256', 'counts', 'conditions', 'selection_rule', 'scope', 'rationale'}
    _require(isinstance(ruling, dict) and set(ruling) == fields, 'invalid cohort ruling schema')
    _require(type(ruling['schema_version']) is int and ruling['schema_version'] == 1,
             'invalid cohort ruling schema version')
    for key in ('ruling_id', 'session', 'rationale'):
        _require(isinstance(ruling[key], str) and bool(ruling[key].strip()), 'invalid cohort ruling '+key)
    for key, value in dict(decision='accept_exact_matched_cohort', scope='cohort_size_only',
                          conditions=['D','I'],
                          selection_rule='all_matched_survivors_no_baseline_competence_filter').items():
        _require(ruling[key] == value, 'invalid cohort ruling '+key)
    config, manifest = plan['config'], plan['build_manifest']
    _require(manifest.get('fleet_ready') is True and manifest.get('cohort') == 'matched',
             'cohort ruling requires matched fleet-ready data')
    selected = {t:{s:manifest['tasks'][t]['split_ids'][s][:config['sample_caps'][s]]
                   for s in SPLITS} for t in config['tasks']}
    counts = {t:{s:len(ids) for s,ids in splits.items()} for t,splits in selected.items()}
    _require(_hash(ruling['build_hash']) and ruling['build_hash'] == manifest['build_hash'],
             'cohort ruling build mismatch')
    _require(_hash(ruling['selected_ids_sha256']) and ruling['selected_ids_sha256'] == digest(selected),
             'cohort ruling selected IDs mismatch')
    # JSON equality alone admits bool/float values as integer counts.
    _require(isinstance(ruling['counts'], dict) and set(ruling['counts']) == set(counts),
             'cohort ruling counts mismatch')
    for task in counts:
        values = ruling['counts'][task]
        _require(isinstance(values, dict) and set(values) == set(SPLITS) and
                 all(type(values[s]) is int and values[s] == counts[task][s] for s in SPLITS),
                 'cohort ruling counts mismatch')
    return digest(ruling)


def _receipt_seconds(receipt, plan, selected):
    config, manifest = plan['config'], plan['build_manifest']
    _require(receipt.get('status') == 'success' and receipt.get('exit_code') == 0 and
             receipt.get('errors') == [] and not receipt.get('test_runner_injected'), 'failed/injected/incomplete receipt')
    execution_commit = receipt.get('execution_commit')
    _require(isinstance(execution_commit, str) and re.fullmatch('[0-9a-f]{40}', execution_commit) is not None,
             'receipt missing full execution commit')
    _require('execution_commit' not in plan or execution_commit == plan['execution_commit'],
             'receipt execution commit mismatch')
    for key, expected in dict(model=config['model'], source_commit=manifest['source_commit'],
                              build_hash=manifest['build_hash'], build_manifest_sha256=digest(manifest),
                              frozen_config_sha256=digest(config), source_hashes=plan['source_hashes'],
                              max_seq_length=manifest['max_seq_length'], selected_ids=selected,
                              counts={s:len(v) for s,v in selected.items()}, planned_epochs=500,
                              granularity=plan.get('granularity','heads-mlp'), cohort=manifest['cohort'],
                              fleet_ready=manifest['fleet_ready']).items():
        _require(receipt.get(key) == expected, 'receipt mismatch: '+key)
    _require(receipt.get('condition') in ('D','I') and receipt.get('seed') in config['seeds'], 'unplanned cell')
    _require(manifest['fleet_ready'] or receipt['condition']=='D', 'provisional I receipt')
    hardware = plan['hardware']
    _require(receipt.get('gpu_devices') == hardware['gpu_devices'] and receipt.get('gpu_count') == 1,
             'hardware mismatch')
    env = receipt.get('environment', {})
    cluster = env.get('SLURM_CLUSTER_NAME') or env.get('DC_CLUSTER')
    _require(cluster == hardware['cluster'] and bool(env.get('SLURM_JOB_ID')), 'missing/mismatched allocation')
    command = receipt.get('argv')
    _require(isinstance(command, list) and all(isinstance(v,str) for v in command), 'missing argv')
    flags = list(GATE_FLAGS)
    heads_only = plan.get('granularity','heads-mlp') == 'heads-only'
    if heads_only:
        flags[flags.index('--prune-mlp-blocks')] = '--no-prune-mlp-blocks'
    _require(all(command.count(flag)==1 for flag in flags), 'missing/duplicate gate flags')
    resolved = expected_config(command)
    if heads_only:
        resolved['node_config']['prune_mlp_blocks'] = False
    _require(receipt.get('resolved_config_sha256') == digest(resolved), 'resolved configuration hash mismatch')
    values = dict(model=config['model'], task=receipt['task'], seed=receipt['seed'],
                  node_epochs=receipt.get('actual_epochs'), train_samples=len(selected['train']),
                  val_samples=len(selected['validation']), test_samples=len(selected['test']),
                  max_seq_length=manifest['max_seq_length'], deception_condition='deceptive',
                  **{k:config[k] for k in ('node_lambda_sparsity','lr','batch_size',
                                         'faithfulness_weight','deception_margin_loss')})
    if 'data_root' in config:
        values['data_dir'] = str(Path(config['data_root'])/receipt['condition'])
    for key, expected in values.items():
        _require(resolved.get(key) == expected, 'resolved plan mismatch: '+key)
    allowed_flags = set(flags) | {'--'+k.replace('_','-') for k in values} | {'--data-dir','--output-dir'}
    actual_flags = [v for v in command if v.startswith('--')]
    _require(len(actual_flags)==len(set(actual_flags)) and set(actual_flags)<=allowed_flags,
             'unexpected/duplicate training flags')
    hashes = receipt.get('dataset_config_sha256')
    _require(_hashes(hashes) and all(k in hashes for k in (('D','I') if manifest['fleet_ready'] else ('D',))),
             'missing dataset configuration hashes')
    _require(_hashes(receipt.get('artifact_sha256')) and
             all(k in receipt['artifact_sha256'] for k in ARTIFACTS), 'missing final artifact hashes')
    epochs = receipt.get('actual_epochs')
    _require(type(epochs) is int and 10 <= epochs <= 500, 'missing periodic-validation epoch coverage')
    _require(receipt.get('purpose') == ('scientific-seed' if epochs == 500 else 'timing-only') or
             (epochs == 500 and receipt.get('purpose') == 'timing-only'), 'invalid pilot purpose')
    total = _number(receipt.get('total_seconds'), 'total duration', positive=True)
    prune = _number(receipt.get('pruning_seconds'), 'pruning duration', positive=True)
    _require(prune <= total, 'pruning exceeds process duration')
    return _number(total-prune+prune*500/epochs, 'extrapolated duration', positive=True)


def project_reserved(receipts: list, plan: dict, *, pilot_reserved_gpu_hours: float,
                     buffer_fraction: float=.20) -> dict:
    """Return a conditional recommendation without file, GPU or ledger side effects.

    Receipt success means the timed wrapper checked final outputs/history. Caller
    must retain its original receipts and ledger evidence; synthetic receipt JSON
    is not independent proof of a run. Seed-only timing reuse selects the largest
    valid estimate for that task/condition. Invalid receipts never provide timing.
    """
    _number(pilot_reserved_gpu_hours, 'pilot reserved GPU-hours', positive=True)
    _number(buffer_fraction, 'buffer fraction')
    config, manifest = _validate_plan(plan)
    ruling_sha256 = _cohort_ruling_digest(plan)
    usable, rejected = {}, []
    for index, receipt in enumerate(receipts):
        try:
            task = receipt['task']
            _require(task in config['tasks'], 'unplanned task')
            info = manifest['tasks'][task]
            selected = {s:info['split_ids'][s][:config['sample_caps'][s]] for s in SPLITS}
            seconds = _receipt_seconds(receipt, plan, selected)
            key = (task, receipt['condition'])
            usable.setdefault(key, []).append((seconds,index,receipt))
        except (KeyError, TypeError, ValueError) as error:
            rejected.append(dict(index=index, reason=str(error)))
    execution_commits = {r['execution_commit'] for candidates in usable.values() for _,_,r in candidates}
    if len(execution_commits) > 1:
        rejected.append(dict(index=None, reason='mixed receipt execution commits'))
    cells, gaps = [], []
    for task, condition, seed in itertools.product(config['tasks'], config['conditions'], config['seeds']):
        identity = dict(task=task, condition=condition, seed=seed)
        candidates = usable.get((task,condition), [])
        if not candidates:
            gaps.append(identity)
            continue
        seconds, index, receipt = max(candidates, key=lambda v:v[0])
        minutes = math.ceil(_number(seconds*(1+buffer_fraction), 'buffered duration', positive=True)/60)
        cells.append(dict(identity, estimated_seconds=seconds, reserved_minutes=minutes,
                          reserved_gpu_hours=minutes/60,
                          coverage_source_receipt=dict(index=index, task=task, condition=condition,
                                                       seed=receipt['seed']),
                          seed_only_timing_reuse=seed != receipt['seed']))
    complete = not gaps and len(cells)==18
    total = pilot_reserved_gpu_hours+sum(c['reserved_minutes'] for c in cells)/60
    within = complete and total <= 60
    trigger = any(c['estimated_seconds'] > 6*3600 for c in cells)
    matched = manifest.get('fleet_ready') is True and manifest.get('cohort') == 'matched'
    under = any(len(manifest['tasks'][t]['split_ids']['train'][:config['sample_caps']['train']]) < 200 for t in config['tasks'])
    # Mixed hardware/source receipts block approval even if another receipt covers
    # the cell: a fleet recommendation must describe one comparable receipt set.
    review_required = under and ruling_sha256 is None
    allowed = complete and matched and within and not rejected and not review_required and not (
        trigger and plan.get('granularity','heads-mlp') == 'heads-mlp')
    recommendation = ('measure-heads-only-pilot' if trigger and plan.get('granularity','heads-mlp')=='heads-mlp'
                      else 'fleet-reservation-allowed' if allowed else 'hold')
    return dict(cells=cells, planned_cell_count=18, coverage_gaps=gaps, rejected_receipts=rejected,
                pilot_reserved_gpu_hours=pilot_reserved_gpu_hours, total_reserved_gpu_hours=total,
                total_is_partial=not complete, single_mask_over_6h=trigger, within_60h=within,
                matched_data=matched, train_under_200=under,
                train_under_200_requires_lead_review=review_required,
                cohort_ruling_sha256=ruling_sha256,
                execution_commit=next(iter(execution_commits)) if len(execution_commits)==1 else None,
                fleet_reservation_allowed=allowed, recommendation=recommendation,
                conditional_hardware=plan['hardware'], granularity=plan.get('granularity','heads-mlp'),
                training_margin=config['deception_margin_loss'],
                source_screening_thresholds={t:{s:v['config']['margin_thresh'] for s,v in manifest['tasks'][t]['sources'].items()}
                                             for t in config['tasks']},
                limitations=['Fixed cost is total minus printed pruning time; pruning scaling conservatively repeats periodic validation.',
                             'No extrapolation across task, condition, build, shape, hardware or granularity; only seed-only reuse.',
                             'Pilot reservation must include all allocations, including failed pilots; no ledger is mutated.',
                             'No lead conservative bounds supported; short pilots have a different cosine horizon.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--receipts', nargs='+', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--build-manifest', required=True)
    parser.add_argument('--pilot-reserved-gpu-hours', type=float, required=True)
    parser.add_argument('--commit', help='Expected full execution revision of all measured receipts')
    parser.add_argument('--cohort-ruling', help='Explicit lead cohort-size ruling JSON; does not clear timing/budget gates')
    parser.add_argument('--granularity', choices=('heads-mlp','heads-only'), default='heads-mlp')
    args = parser.parse_args(argv)
    receipts = [json.loads(Path(p).read_text()) for p in args.receipts]
    config = json.loads(Path(args.config).read_text())
    config.setdefault('data_root', str(Path(args.build_manifest).resolve().parent))
    manifest = json.loads(Path(args.build_manifest).read_text())
    candidate = next((r for r in receipts if r.get('status')=='success' and not r.get('test_runner_injected')
                      and r.get('gpu_devices') and r.get('gpu_count')==1), {})
    env = candidate.get('environment', {})
    hardware = dict(gpu_devices=candidate.get('gpu_devices'), gpu_count=candidate.get('gpu_count'),
                    cluster=env.get('SLURM_CLUSTER_NAME') or env.get('DC_CLUSTER'))
    repo = Path(__file__).resolve().parents[1]
    plan = dict(config=config, build_manifest=manifest, hardware=hardware, granularity=args.granularity,
                source_hashes={s:hashlib.sha256((repo/s).read_bytes()).hexdigest() for s in SOURCES})
    try:
        if args.commit is not None:
            plan['execution_commit'] = args.commit
        if args.cohort_ruling is not None:
            plan['cohort_ruling'] = json.loads(Path(args.cohort_ruling).read_text())
        result = project_reserved(receipts, plan, pilot_reserved_gpu_hours=args.pilot_reserved_gpu_hours)
    except (OSError, KeyError, TypeError, ValueError) as error:
        result = dict(fleet_reservation_allowed=False, recommendation='hold', error=str(error))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['fleet_reservation_allowed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
