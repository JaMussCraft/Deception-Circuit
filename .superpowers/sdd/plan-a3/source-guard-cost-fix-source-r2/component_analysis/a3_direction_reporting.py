"""Pure CPU normalization and diagnostic reporting for frozen A3 directions.

No filesystem/model/CLI access. Callers must read completed immutable artifacts
through the artifact readers first. ``pack_statistics_panel`` accepts combined
panels, but selects only primary interchange and the two MMLU floors. Provenance
and secondary diagnostics never enter the strict statistics schema. Final run
admission/completion belongs to the runtime adapter, not to these pure functions.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections import defaultdict

import numpy as np

from component_analysis import a3_statistics as statistics

SEEDS = statistics.SEEDS
CONDITIONS = statistics.CONDITIONS
STREAMS = ('clean', 'corrupt')
KEY_FIELDS = ('panel', 'analysis_task', 'source_task', 'split', 'seed', 'site',
              'family', 'axis_index', 'operation', 'instance_id', 'condition', 'stream')


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _key(row):
    try:
        return tuple(tuple(row[k]) if k == 'site' else row[k] for k in KEY_FIELDS)
    except (KeyError, TypeError) as error:
        raise ValueError('incomplete raw row key') from error


def _ids(values, label):
    _require(isinstance(values, list) and values and all(isinstance(v, str) and v for v in values)
             and len(values) == len(set(values)), 'missing/duplicate '+label)
    return values


def _aliases(row):
    ids = {row[k] for k in ('instance_id','source_id','donor_id','donor_source_id')
           if isinstance(row.get(k), str)}
    prompts = {row['prompt'].encode()} if isinstance(row.get('prompt'), str) else set()
    for data in row.get('streams', {}).values():
        if isinstance(data.get('prompt'), str):
            prompts.add(data['prompt'].encode())
    for name in ('donor','source_reference','source_recipient'):
        if isinstance(row.get(name), dict):
            more_ids, more_prompts = _aliases(row[name])
            ids |= more_ids; prompts |= more_prompts
    return ids, prompts


def _source_record(source, stream, source_task):
    # Same adapter as a3_direction_pipeline._selection_source_record, without
    # importing the fitting module or torch into this pure reporting module.
    record = copy.deepcopy(source)
    saved = record['streams'][stream]
    if source_task not in ('ioi', 'mmlu'):
        for name in ('expected_token','honest_token','opposite_token'):
            if name in saved:
                record[name] = saved[name]
    record.update(tokens=copy.deepcopy(saved['tokens']), layout=copy.deepcopy(saved.get('layout')),
                  utility_assessment=stream == 'clean')
    return record


def _sources(design, task, split):
    if task in ('ioi', 'mmlu'):
        rows = design[task+'_validation'] if split == 'validation' else design['utility'][task]
        _ids([r['instance_id'] for r in rows], task+' IDs')
        _require(len(rows) == 32 if task == 'mmlu' else
                 (design['injected'] or len(rows) == 100), 'fixed utility membership required')
        _require(all(r.get('condition') == task.upper() and 'clean' in r.get('streams', {}) for r in rows),
                 'invalid utility condition/stream')
    else:
        spec = design['tasks'][task]
        ids = _ids(spec['selection_ids' if split == 'validation' else 'assessment_ids'], 'mechanism IDs')
        if not design['injected'] and split == 'assessment':
            _require(len(ids) == 100, 'fixed 100 original assessment IDs required')
        rows = [r for r in design['access_rows'][task] if r['instance_id'] in set(ids)]
        indexed = {(r['condition'],r['instance_id']):r for r in rows}
        _require(len(rows) == len(indexed) == len(ids)*5 and
                 set(indexed) == {(c,i) for c in CONDITIONS for i in ids}, 'incomplete mechanism source membership')
        _require(all(set(r.get('streams', {})) == set(STREAMS) for r in rows), 'paired source streams required')
        rows = [indexed[(c,i)] for c in CONDITIONS for i in ids]
    if split == 'validation':
        _require(all(r.get('analysis_split', r.get('split')) == 'validation' for r in rows),
                 'validation source split required')
    else:
        allowed_splits = ({'generated','test'} if design['injected'] else {'generated'}) if task=='ioi' else {'test'}
        _require(all(r.get('split') in allowed_splits for r in rows), 'original source split required')
    return rows


def _validate_exclusions(design):
    banned_ids, banned_prompts = set(design.get('selection_exclusion_ids', [])), set()
    for task in design['tasks']:
        for row in _sources(design, task, 'assessment'):
            ids, prompts = _aliases(row); banned_ids |= ids; banned_prompts |= prompts
    for task in ('ioi','mmlu'):
        for row in _sources(design, task, 'assessment'):
            ids, prompts = _aliases(row); banned_ids |= ids; banned_prompts |= prompts
    for task in list(design['tasks'])+['ioi','mmlu']:
        for row in _sources(design, task, 'validation'):
            ids, prompts = _aliases(row)
            _require(not ids & banned_ids and not prompts & banned_prompts,
                     'validation/original assessment source/ID/prompt exclusion collision')
        if task in design['tasks']:
            spec = design['tasks'][task]
            _require(not set(spec['selection_ids']) & set(spec['fit_ids']), 'fit/validation ID collision')


def _selection(design, selected):
    _require(design.get('seeds') == list(SEEDS), 'all frozen seeds/order required')
    _require(type(design.get('injected')) is bool and selected.get('injected') is design['injected'],
             'explicit matching injected provenance required')
    _require(selected.get('kind') == 'a3_direction_selection' and selected.get('selection_split') == 'validation'
             and not selected.get('blocked_task_seeds'), 'frozen unblocked validation selection required')
    inventory_identity = selected.get('inventory_identity')
    if inventory_identity is not None or not design['injected']:
        _require(isinstance(inventory_identity,dict) and
                 inventory_identity.get('design_sha256') == _digest(design),
                 'changed selected design binding')
        protocol = selected.get('protocol')
        _require(isinstance(protocol,dict) and protocol == design.get('direction_protocol')
                 and inventory_identity.get('protocol_sha256') == _digest(protocol),
                 'changed selected protocol binding')
    index = {}
    for record in selected.get('selected_records', []):
        key = (record['task'],record['seed'])
        _require(key not in index and key[0] in design['tasks'] and key[1] in SEEDS, 'duplicate/unknown selected seed')
        _require(record['site'] in design['tasks'][key[0]]['direction_sites'], 'selected site outside frozen candidates')
        descriptors = [record['learned_axis']]
        for name, count in (('assessment_axes',199),('calibration_axes',32)):
            axes = record.get(name, [])
            _require(len(axes) == count and [a.get('axis_index') for a in axes] == list(range(count)),
                     'complete ordered frozen '+name+' required')
            _require(len({a.get('reference') for a in axes}) == count, 'duplicate frozen axes')
            descriptors += axes
        for axis in descriptors:
            _require(isinstance(axis.get('reference'),str) and axis['reference'] and
                     re.fullmatch('[0-9a-f]{64}', str(axis.get('sha256'))) is not None,
                     'invalid frozen axis identity')
            receipt = selected.get('axes', {}).get(axis['reference'], {})
            _require(receipt.get('sha256') == axis['sha256'], 'axis descriptor/bundle receipt mismatch')
        index[key] = record
    _require(set(index) == {(t,s) for t in design['tasks'] for s in SEEDS}, 'complete selected task/seed coverage required')
    return index


def _finite(value, name):
    _require(type(value) in (int,float) and math.isfinite(value), 'nonfinite/missing '+name)
    return value


def _validate_row(row, expected, axis, *, injected):
    _require(row.get('axis_hash') == axis['sha256'], 'changed frozen numeric axis hash')
    _require(row.get('source_provenance') == expected, 'changed source tokens/readout/prompt/labels')
    for name in ('expected_token','honest_token','opposite_token'):
        _require(type(row.get(name)) is int and row[name] == expected[name], 'changed native '+name)
    for name in ('intact_margin','patched_margin','epsilon','head_norm','residual_norm'):
        _finite(row.get(name),name)
    _require(row['epsilon'] >= 1e-6 and row['head_norm'] >= 0 and row['residual_norm'] >= 0, 'invalid epsilon/norm')
    for prefix in ('intact','patched'):
        correct = row.get(prefix+'_correct'); argmax = row.get(prefix+'_argmax')
        _require(type(correct) in (bool,int) and correct in (0,1) and type(argmax) is int and argmax >= 0
                 and bool(correct) == (argmax == row['expected_token']), 'invalid full-vocabulary correctness')
    _require(all(row.get(k) is True for k in ('supported','replay_valid','gate_valid'))
             and row.get('positive_control', {}).get('valid') is True, 'unsupported/invalid replay or positive control')
    # replay_valid is the reviewed runner's matched-batch proof: allclose
    # with atol=rtol=1e-5 AND exact full-vocabulary argmax equality. Stored
    # errors are batch maxima, so neither an absolute-only ceiling nor a
    # relative comparison against this individual row preserves that proof.
    # Completed artifact/source lineage must attest the producing runner.
    errors = row.get('replay_errors', {})
    _require(set(errors) == {'empty','head_self','zero_coefficient'} and
             all(type(v) in (int,float) and math.isfinite(v) and v >= 0 for v in errors.values()),
             'missing/failed measured replay controls')
    _require(row['epsilon'] >= max(1e-6, 10*max(errors.values())), 'epsilon below measured replay tolerance')
    if not injected:
        control = row['positive_control']
        _require(all(re.fullmatch('[0-9a-f]{64}', str(control.get(k))) is not None
                     for k in ('control_id','profile_id','recipient_sha256')),
                 'production positive control byte references required')
        _require(control['profile_id'] == row.get('profile_id') and isinstance(row.get('numeric_profile'),dict),
                 'production numeric profile linkage required')
        profile = {k:v for k,v in row['numeric_profile'].items() if k != 'profile_id'}
        _require(row['profile_id'] == _digest(profile), 'changed production numeric profile digest')
        mapping = row.get('donor_mapping')
        if row['operation'] == 'interchange':
            donor_stream = 'corrupt' if row['stream'] == 'clean' else 'clean'
            donor = expected.get('streams', {}).get(donor_stream)
            recipient = expected['streams'][row['stream']]
            _require(isinstance(mapping,dict) and isinstance(donor,dict), 'production primary donor map required')
            _require(mapping.get('supported') is True and
                mapping.get('recipient_id') == mapping.get('donor_id') == row['instance_id'] and
                mapping.get('recipient_condition') == mapping.get('donor_condition') == row['condition'] and
                mapping.get('recipient_stream') == row['stream'] and mapping.get('donor_stream') == donor_stream and
                mapping.get('recipient_positions') == [recipient.get('readout',len(recipient['tokens'])-1)] and
                mapping.get('donor_positions') == [donor.get('readout',len(donor['tokens'])-1)] and
                bool(mapping.get('donor_source_hash')) and
                mapping['donor_source_hash'] == expected.get('source_hash') and
                bool(mapping.get('donor_profile_id')), 'changed primary own-readout/opposite-stream donor map')
        else:
            _require(mapping is None, 'MMLU floors cannot use donor interchange')


def _validate_frozen_profile(row, selected, *, injected):
    """Bind every production observation to the same frozen model/source."""
    if injected:
        return
    profile = row.get('numeric_profile', {})
    identity = selected['inventory_identity']
    _require(all(profile.get(k) == identity.get(k) for k in ('model','model_revision'))
             and profile.get('source_sha256') == _digest(identity.get('code_hashes')),
             'changed production model/source profile')


def _pack_tasks(design, selected, rows, *, split, task_names):
    _require(split in ('assessment','validation'), 'invalid analysis split')
    selections = _selection(design, selected)
    if split == 'validation':
        _validate_exclusions(design)
    n_null = 199 if split == 'assessment' else 32
    panel_name = 'assessment' if split == 'assessment' else 'calibration'
    null_family = 'assessment_null' if split == 'assessment' else 'calibration_null'
    # Duplicates reject even when they are diagnostics. Primary replacement is
    # determined by operation/source, never by a caller-supplied expected set.
    indexed = {}
    for row in rows:
        _require(row.get('split') == split and row.get('panel') == panel_name,
                 'mixed/pilot analysis panel or assessment leakage')
        key = _key(row)
        _require(key not in indexed, 'duplicate raw row')
        indexed[key] = row
    relevant = {k:r for k,r in indexed.items() if r['analysis_task'] in task_names and
        r['family'] in ('learned', null_family) and
        r['operation'] in (('zero','h_mean') if r['source_task']=='mmlu' else ('interchange',))}
    expected_rows = []
    sources = {t:_sources(design,t,split) for t in list(task_names)+['ioi','mmlu']}
    source_records = {(t,r['condition'],r['instance_id'],stream):_source_record(r,stream,t)
        for t,values in sources.items() for r in values
        for stream in (STREAMS if t in task_names else ('clean',))}
    for task in task_names:
        for seed in SEEDS:
            rec = selections[(task,seed)]
            descriptors = [rec['learned_axis']]+rec['assessment_axes' if split=='assessment' else 'calibration_axes']
            for a, axis in enumerate(descriptors):
                for source_task in (task,'ioi','mmlu'):
                    for src in sources[source_task]:
                        for stream in (STREAMS if source_task==task else ('clean',)):
                            for op in (('zero','h_mean') if source_task=='mmlu' else ('interchange',)):
                                key = (panel_name,task,source_task,split,seed,tuple(rec['site']),
                                       'learned' if a==0 else null_family, 0 if a==0 else a-1,
                                       op,src['instance_id'],src['condition'],stream)
                                _require(key in relevant, 'missing primary row/axis/seed/stream/utility')
                                row = relevant.pop(key)
                                _validate_row(row,source_records[(source_task,src['condition'],src['instance_id'],stream)],
                                              axis,injected=design['injected'])
                                _validate_frozen_profile(row,selected,injected=design['injected'])
                                expected_rows.append((task,a,seed,source_task,src,stream,op,row))
    _require(not relevant, 'unexpected primary row/panel/axis/split')
    output = {}
    for task in task_names:
        spec = design['tasks'][task]; ids = spec['assessment_ids' if split=='assessment' else 'selection_ids']
        d_sources = {r['instance_id']:r for r in sources[task] if r['condition']=='D'}
        words = []
        for rid in ids:
            src = d_sources[rid]
            word = next((src[k] for k in ('pressure_text','pressure_clause','pressure')
                         if isinstance(src.get(k),str) and src[k]), None)
            _require(word is not None, 'canonical source D wording required'); words.append(word)
        conds = {c:dict(intact_margin=np.empty((3,len(ids),2)), intact_correct=np.empty((3,len(ids),2)),
            patched_margin=np.empty((n_null+1,3,len(ids),2)), patched_correct=np.empty((n_null+1,3,len(ids),2))) for c in CONDITIONS}
        utilities = {}
        for name,src_task in (('IOI','ioi'),('MMLU_zero','mmlu'),('MMLU_h_mean','mmlu')):
            uids = [r['instance_id'] for r in sources[src_task]]
            utilities[name] = dict(prompt_ids=uids,intact_correct=np.empty((3,len(uids))),
                                  patched_correct=np.empty((n_null+1,3,len(uids))))
        output[task] = dict(instance_ids=list(ids),pressure_texts=words,conditions=conds,utilities=utilities,
                            epsilon=np.full(3,1e-6),gate_valid=np.ones((n_null+1,3),dtype=bool))
    baselines = {}
    for task,a,seed,src_task,src,stream,op,row in expected_rows:
        out = output[task]; si = SEEDS.index(seed); rid = src['instance_id']
        # Intact results must be common across every orientation, both MMLU
        # operations, seeds and task-selected utility sites.
        baseline_key = (src_task,src['condition'],rid,stream)
        baseline = (row['intact_margin'],row['intact_correct'],row['intact_argmax'])
        _require(baseline_key not in baselines or baselines[baseline_key] == baseline,
                 'inconsistent common intact baseline')
        baselines[baseline_key] = baseline
        out['epsilon'][si] = max(out['epsilon'][si],row['epsilon'])
        if src_task == task:
            j = out['instance_ids'].index(rid); k = STREAMS.index(stream); c = out['conditions'][src['condition']]
            c['intact_margin'][si,j,k] = row['intact_margin']; c['intact_correct'][si,j,k] = row['intact_correct']
            c['patched_margin'][a,si,j,k] = row['patched_margin']; c['patched_correct'][a,si,j,k] = row['patched_correct']
        else:
            name = 'IOI' if src_task=='ioi' else 'MMLU_'+op
            u = out['utilities'][name]; j = u['prompt_ids'].index(rid)
            u['intact_correct'][si,j] = row['intact_correct']; u['patched_correct'][a,si,j] = row['patched_correct']
    return output


def pack_statistics_panel(design, selected, rows, *, split):
    """Normalize complete primary FAR/SER panels; return the strict schema only."""
    tasks = _pack_tasks(design,selected,rows,split=split,task_names=statistics.TASKS)
    power = split == 'validation'
    result = dict(schema_version=1,kind='a3_direction_calibration' if power else 'a3_direction_outcomes',
        split=split,seeds=list(SEEDS),axis_ids=['learned']+list(range(32 if power else 199)),tasks=tasks)
    if power:
        result['assessment_ids'] = {t:list(design['tasks'][t]['assessment_ids']) for t in statistics.TASKS}
        result['assessment_utility_ids'] = {name:[r['instance_id'] for r in design['utility'][task]]
                                          for name,task in (('IOI','ioi'),('MMLU','mmlu'))}
    statistics._prepare(result,power=power)
    return result


def summarize_descriptive_sdr(design, selected, rows, *, n_boot=2000, seed=9001):
    """Same paired seed/axis gates, ranks and CIs, with no Holm decision."""
    _require(type(n_boot) is int and n_boot > 0, 'n_boot must be positive')
    task = _pack_tasks(design,selected,rows,split='assessment',task_names=('sdr_v2',))['sdr_v2']
    # Reuse the reviewed strict schema preparation, then evaluate SDR only. The
    # duplicate aliases are solely a schema adapter; they never enter inference.
    adapter = dict(schema_version=1,kind='a3_direction_outcomes',split='assessment',seeds=list(SEEDS),
                   axis_ids=['learned']+list(range(199)),tasks={t:task for t in statistics.TASKS})
    prepared,utility_ids,_ = statistics._prepare(adapter,power=False)
    prepared = {'sdr_v2':prepared['far_v2']}; task = prepared['sdr_v2']
    rng = np.random.default_rng(seed)
    draws = defaultdict(list)
    utility = statistics._utility_draws(utility_ids,rng,bootstrap=False)
    point = statistics._evaluate(task,list(range(len(task['instance_ids']))),utility)
    result = dict(descriptive_only=True,seeds=statistics._seed_reports(point,0),
        null_seeds=[statistics._seed_reports(point,a) for a in range(1,200)],
        comparison=statistics.compare_triplets(point['statistics'][0],point['statistics'][1:]))
    for _ in range(n_boot):
        pressure = statistics.draw_pressure_clusters(prepared,rng)
        utility = statistics._utility_draws(utility_ids,rng,bootstrap=True)
        metrics = statistics._evaluate(task,pressure['sdr_v2']['indices'],utility)
        for name in ('D_fraction','I_fraction','contrast'):
            draws[name].append(metrics[name][0])
        for name in ('H','F','IOI','MMLU_zero','MMLU_h_mean'):
            draws[name+'_shift'].append(metrics['collateral_shifts'][name][0])
    intervals,counts = {},{}
    for name,values in draws.items():
        intervals[name],counts[name] = statistics._interval(values,n_boot)
    result.update(intervals=intervals,valid_bootstrap_draws=counts,
        bootstrap=dict(seed=seed,n_boot=n_boot,unit='canonical SDR wording; paired utility prompts',seed_resampling=False),
        interpretation='Descriptive only; conditional on frozen site/fit and isotropic orientation benchmark.')
    return statistics._json(result)


def _probe_summary(design, selected, probe_results):
    """Validate explicit completed CPU probe observations and train ancestry.

    Each record names task/seed/site/probe ('image_probe' or 'metadata_probe'),
    exact selected fit_receipt, original ordered assessment instance_ids,
    conditions ['D','I'], streams ['clean','corrupt'], and binary correctness
    [2,N,2]. balanced_accuracy must equal its mean. Failed train fits instead
    require status='unavailable', their unchanged fit receipt and a reason.
    """
    if probe_results is None:
        return dict(status='incomplete',reason='completed assessment probe results not supplied')
    _require(probe_results.get('kind') == 'a3_direction_probe_results' and
             probe_results.get('complete') is True and probe_results.get('split') == 'assessment' and
             isinstance(selected.get('fit_reference'),dict) and selected['fit_reference'] and
             probe_results.get('fit_reference') == selected['fit_reference'],
             'completed probes require exact train fit byte ancestry')
    expected = {(r['task'],r['seed'],tuple(r['site']),p):r
                for r in selected['selected_records'] for p in ('image_probe','metadata_probe')}
    reports = []
    for record in probe_results.get('records', []):
        key = (record.get('task'),record.get('seed'),tuple(record.get('site',[])),record.get('probe'))
        _require(key in expected, 'unexpected/duplicate probe result')
        selection = expected.pop(key); receipt = selection.get(key[3])
        _require(isinstance(receipt,dict) and record.get('fit_receipt') == receipt,
                 'changed probe train fit receipt')
        if receipt.get('status') != 'fitted':
            _require(record.get('status') == 'unavailable' and record.get('reason') and
                     receipt.get('status') in ('failed','unfitted'), 'failed probe fit requires unavailable reason')
            reports.append(copy.deepcopy(record)); continue
        ids = design['tasks'][key[0]]['assessment_ids']
        correct = np.asarray(record.get('correct'),dtype=float)
        _require(record.get('status') == 'completed' and record.get('instance_ids') == ids and
                 record.get('conditions') == ['D','I'] and record.get('streams') == list(STREAMS) and
                 correct.shape == (2,len(ids),2) and np.isfinite(correct).all() and np.isin(correct,(0,1)).all(),
                 'probe requires exact paired assessment correctness coverage')
        accuracy = _finite(record.get('balanced_accuracy'),'probe balanced accuracy')
        _require(abs(accuracy-float(correct.mean())) <= 1e-12, 'probe balanced accuracy/correctness disagreement')
        reports.append(copy.deepcopy(record))
    _require(not expected, 'missing complete task/seed/probe coverage')
    return dict(status='complete',fit_reference=copy.deepcopy(selected['fit_reference']),
                records=reports,descriptive_only=True)


def _raw_diagnostic_table(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['source_task'],row['condition'],row['operation'])].append(row)
    result = []
    for (source,condition,operation), values in sorted(grouped.items()):
        # Every mechanism ID has two streams. Utility IDs have one stream.
        result.append(dict(source_task=source,condition=condition,operation=operation,n_ids=len({r['instance_id'] for r in values}),
            n_rows=len(values),intact_margin=float(np.mean([r['intact_margin'] for r in values])),
            patched_margin=float(np.mean([r['patched_margin'] for r in values])),
            margin_shift=float(np.mean([r['patched_margin']-r['intact_margin'] for r in values])),
            intact_accuracy=float(np.mean([r['intact_correct'] for r in values])),
            patched_accuracy=float(np.mean([r['patched_correct'] for r in values])),
            accuracy_shift=float(np.mean([int(r['patched_correct'])-int(r['intact_correct']) for r in values])),
            mean_head_norm=float(np.mean([r['head_norm'] for r in values])),
            mean_residual_norm=float(np.mean([r['residual_norm'] for r in values]))))
    return result


def summarize_direction_diagnostics(design, selected, rows, *, probe_results=None):
    """Separate exact-coverage nuisance/secondary/signed-steering observations.

    Uses the reviewed scalar point estimator for primary nuisance and secondary
    mechanism operations. Secondary operation names are adapted to interchange
    solely at that estimator's interface; reports retain their actual operation
    and never substitute them into primary inference. Steering reports raw signed
    tables only. No diagnostic enters Holm or a confirmatory null panel.
    """
    from component_analysis.a3_direction_runner import direction_point_metrics
    selections = _selection(design,selected)
    indexed = {}
    for row in rows:
        _require(row.get('split') == 'assessment' and row.get('panel') == 'assessment',
                 'diagnostics require assessment-only completed rows')
        key = _key(row)
        _require(key not in indexed, 'duplicate diagnostic raw row')
        # Includes primary baseline observations and reused same-axis MMLU
        # floors as well as nuisance, secondary and signed steering rows.
        _validate_frozen_profile(row,selected,injected=design['injected'])
        indexed[key] = row
    sources = {t:_sources(design,t,'assessment') for t in list(design['tasks'])+['ioi','mmlu']}
    provenance = {(t,r['condition'],r['instance_id'],stream):_source_record(r,stream,t)
                  for t,values in sources.items() for r in values
                  for stream in (STREAMS if t in design['tasks'] else ('clean',))}
    baseline = {}
    for row in rows:
        if row['family']=='learned' and (row['operation']=='interchange' or row['source_task']=='mmlu'):
            key = (row['source_task'],row['condition'],row['instance_id'],row['stream'])
            value = (row['intact_margin'],row['intact_correct'],row['intact_argmax'])
            _require(key not in baseline or baseline[key] == value, 'inconsistent primary diagnostic baseline')
            baseline[key] = value
    groups, allowed = [], set()
    for (task,seed),selection in selections.items():
        nuisance = selection.get('nuisance', {})
        has_nuisance = nuisance.get('status') == 'fitted'
        nuisance_reason = nuisance.get('reason') or 'explicit nuisance fit status/receipt missing'
        if has_nuisance:
            axis = nuisance.get('axis', {})
            _require(selected['axes'].get(axis.get('reference'), {}).get('sha256') == axis.get('sha256')
                     and re.fullmatch('[0-9a-f]{64}',str(axis.get('sha256'))) is not None,
                     'changed nuisance axis receipt')
        obligations = [('nuisance','primary'),('learned','zero'),('learned','h_mean'),
                       ('nuisance','zero'),('nuisance','h_mean')]
        obligations += [(family,op) for family in ('steering_learned','steering_nuisance','steering_random')
                        for op in ('steer_negative','steer_positive')]
        for family,operation in obligations:
            report = dict(task=task,seed=seed,site=selection['site'],family=family,operation=operation,
                          descriptive_only=True)
            if family in ('nuisance','steering_nuisance') and not has_nuisance:
                unavailable = nuisance.get('status') == 'unfitted' and bool(nuisance.get('reason')) and bool(nuisance.get('fit_receipt'))
                report.update(status='unavailable' if unavailable else 'incomplete',reason=nuisance_reason,
                              fit_receipt=copy.deepcopy(nuisance.get('fit_receipt')))
                groups.append(report); continue
            axis = (nuisance['axis'] if family in ('nuisance','steering_nuisance') else
                    selection['assessment_axes'][0] if family=='steering_random' else selection['learned_axis'])
            expected = []
            for source in (task,'ioi','mmlu'):
                if source=='mmlu' and operation in ('zero','h_mean'):
                    continue
                ops = ('zero','h_mean') if source=='mmlu' and operation=='primary' else (
                    'interchange' if operation=='primary' else operation,)
                for src in sources[source]:
                    for stream in (STREAMS if source==task else ('clean',)):
                        for op in ops:
                            key = ('assessment',task,source,'assessment',seed,tuple(selection['site']),family,0,
                                   op,src['instance_id'],src['condition'],stream)
                            expected.append(key)
            allowed.update(expected)
            observed = [indexed[key] for key in expected if key in indexed]
            report.update(expected_rows=len(expected),observed_rows=len(observed),expected_keys_sha256=_digest(expected))
            if len(observed) != len(expected):
                report.update(status='incomplete',reason='missing frozen diagnostic row/seed/stream/operation coverage')
                groups.append(report); continue
            for row in observed:
                pkey = (row['source_task'],row['condition'],row['instance_id'],row['stream'])
                _validate_row(row,provenance[pkey],axis,injected=design['injected'])
                _require(pkey in baseline and baseline[pkey] ==
                    (row['intact_margin'],row['intact_correct'],row['intact_argmax']),
                    'diagnostic requires common primary intact baseline')
            report.update(status='complete',tables=_raw_diagnostic_table(observed))
            if not family.startswith('steering_'):
                metric_rows = observed
                if operation != 'primary':
                    # Same axis's existing two MMLU floors complete this
                    # secondary diagnostic. No extra MMLU forward is implied.
                    floors = [r for r in rows if r['analysis_task']==task and r['seed']==seed and
                              r['family']==family and r['source_task']=='mmlu' and r['operation'] in ('zero','h_mean')]
                    floor_keys = {('assessment',task,'mmlu','assessment',seed,tuple(selection['site']),family,0,
                                   op,src['instance_id'],'MMLU','clean')
                                  for op in ('zero','h_mean') for src in sources['mmlu']}
                    if {_key(r) for r in floors} != floor_keys:
                        report.update(status='incomplete',reason='secondary diagnostic missing same-axis MMLU floors')
                        groups.append(report); continue
                    for row in floors:
                        pkey = ('mmlu','MMLU',row['instance_id'],'clean')
                        _validate_row(row,provenance[pkey],axis,injected=design['injected'])
                    metric_rows = [dict(r,operation='interchange') for r in observed]+floors
                metrics = direction_point_metrics(metric_rows,seed=seed,require_mmlu=True)
                report['point_metrics'] = statistics._json(metrics)
                if family=='nuisance' and operation=='primary':
                    report['role_framing_ambiguity'] = bool(metrics['point_pass'])
                    report['interpretation'] = ('Nuisance axis also meets point gates: role/framing ambiguity.'
                        if metrics['point_pass'] else 'Nuisance axis does not meet all point gates.')
                elif operation != 'primary':
                    report['interpretation'] = 'Secondary intervention only; cannot replace a failed primary gate.'
            else:
                report['interpretation'] = 'Signed steering diagnostic; no necessity or MMLU floor verdict.'
            groups.append(report)
    diagnostic_keys = {_key(r) for r in rows if r['family'] in ('nuisance','steering_learned','steering_nuisance','steering_random')
                       or (r['family']=='learned' and r['source_task']!='mmlu' and r['operation'] in ('zero','h_mean'))}
    _require(diagnostic_keys <= allowed, 'unexpected diagnostic axis/site/operation/source coverage')
    probes = _probe_summary(design,selected,probe_results)
    return statistics._json(dict(groups=groups,probes=probes,descriptive_only=True,
        complete=all(g['status'] in ('complete','unavailable') for g in groups) and probes['status']=='complete'))


def assemble_direction_summary(design, selected, rows, *, input_references, calibration_rows=None,
                               final=False, n_boot=2000, seed=9001, n_rep=2000, power_seed=19001, probe_results=None):
    """Pure diagnostic summary with exact canonical JSON byte identities.

    References contain sha256/nbytes of canonical JSON input bytes (sorted keys,
    compact separators, UTF-8, finite numbers). Optional ``artifact_reference``
    stores the runtime reader's marker/child-file byte evidence unchanged. This
    function cannot attest files, protected registries or execution completion;
    production --final therefore requires a separately reviewed runtime gate.
    """
    _require(final is False, 'pure reporting cannot finalize: runtime complete inventory/source/registry gate required')
    inputs = dict(design=design,selected=selected,rows=rows)
    if calibration_rows is not None:
        inputs['calibration_rows'] = calibration_rows
    if probe_results is not None:
        inputs['probe_results'] = probe_results
    _require(set(input_references) == set(inputs), 'exact summary input byte references required')
    for name,value in inputs.items():
        ref = input_references[name]; data = _bytes(value)
        _require(ref.get('sha256') == hashlib.sha256(data).hexdigest() and type(ref.get('nbytes')) is int
                 and ref['nbytes'] == len(data), 'stale summary input bytes '+name)
    panel = pack_statistics_panel(design,selected,rows,split='assessment')
    result = dict(kind='a3_direction_summary',schema_version=1,finalized=False,
        input_references=copy.deepcopy(input_references),
        confirmatory=statistics.summarize_direction_outcomes(panel,n_boot=n_boot,seed=seed),
        descriptive_sdr=summarize_descriptive_sdr(design,selected,rows,n_boot=n_boot,seed=seed),
        diagnostics=summarize_direction_diagnostics(design,selected,rows,probe_results=probe_results),
        continuation_authorized=False)
    if calibration_rows is not None:
        calibration = pack_statistics_panel(design,selected,calibration_rows,split='validation')
        result['conditional_power'] = statistics.simulate_conditional_power(calibration,n_rep=n_rep,seed=power_seed)
    result['diagnostic_readiness'] = result['diagnostics']['complete']
    return statistics._json(result)
