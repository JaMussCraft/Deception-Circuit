"""Pure A3 inference and validation-conditional power, without fitting or I/O.

Normalized input schema (numpy arrays or nested lists), version 1:
  seeds: exactly [42, 1, 123]; axis_ids: ['learned', 0, ..., K-1].
  tasks: exactly far_v2 and ser_v2, each with unique instance_ids, exact canonical
    pressure_texts (one per ID), conditions D/H/F/I/user_neutral, and utilities.
  Each condition has intact_margin/intact_correct [3,N,2] and
    patched_margin/patched_correct [K+1,3,N,2]; streams are clean,corrupt.
  Each utility has unique prompt_ids, intact_correct [3,P], and
    patched_correct [K+1,3,P]. IOI is required. MMLU_zero and MMLU_h_mean
    must both exist or both be absent; when present each has the same 32 IDs.
    They mean subspace zero and centered-H replacement, NOT whole-head removal.
  Task epsilon is a scalar or [3] replay-derived denominator tolerance >=1e-6;
    optional gate_valid [K+1,3] encodes supported/nondegenerate assay coverage.
  kind='a3_direction_outcomes',split='assessment',K=199 for assessment;
    kind='a3_direction_calibration',split='validation',K=32 for power.
  Power additionally requires assessment_ids per task and assessment_utility_ids
    for IOI/MMLU, used ONLY to reject overlap; never supply assessment outcomes.

All seeds, axes, conditions and streams share ID and cluster draws. A bootstrap
cluster occurrence expands every member, giving equal ID weights within each
resampled task, not equal cluster weights. Utility prompt draws are paired across
seeds/tasks/axes and both MMLU operations. These seeds are robustness fits, never
independent datasets. No independent row/seed bootstrap is performed.

Missing assessment MMLU cannot pass. Absent validation MMLU yields explicitly
conditional power. Public reports are strict-JSON-safe: failed triplets remain
-inf internally, but serialize as None with separate failure flags/counts.
"""
from __future__ import annotations

from collections import defaultdict
import itertools
import math
import numpy as np

SEEDS = (42, 1, 123)
TASKS = ('far_v2', 'ser_v2')
CONDITIONS = ('D', 'H', 'F', 'I', 'user_neutral')
UTILITY = ('IOI', 'MMLU_zero', 'MMLU_h_mean')


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _json(value):
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, np.ndarray)):
        return [_json(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    return value


def triplet_statistic(seed_results):
    """All three START gates condition a mean-D statistic; failure is -inf."""
    _require(len(seed_results) == 3, 'exactly three seed results required')
    values = [r['D_fraction'] for r in seed_results]
    if not all(r['point_pass'] and v is not None and math.isfinite(v)
               for r, v in zip(seed_results, values)):
        return -math.inf
    return float(np.mean(values))


def compare_triplets(learned_statistic, null_statistics):
    """Exact order statistic and conservative tied rank, separate from Holm."""
    nulls = np.asarray(null_statistics, dtype=float)
    _require(nulls.shape == (199,), 'exactly 199 null triplets required')
    _require(not np.isnan(nulls).any() and not np.isposinf(nulls).any(), 'invalid null statistic')
    _require(not math.isnan(learned_statistic) and learned_statistic != math.inf,
             'invalid learned statistic')
    threshold = float(np.sort(nulls)[math.ceil(.95 * 199) - 1])
    failed = learned_statistic == -math.inf
    return _json(dict(learned_statistic=learned_statistic, failed_learned_triplet=failed,
        null_95=threshold, null_95_failed_gate=threshold == -math.inf,
        strict_null_pass=not failed and learned_statistic > threshold,
        p_value=1. if failed else (1 + int(np.sum(nulls >= learned_statistic))) / 200.,
        failed_null_triplets=int(np.isneginf(nulls).sum()),
        null_statistics=nulls, null_failed_gate=np.isneginf(nulls)))


def holm_two(p_values):
    """Frozen FAR/SER-only Holm step-down; ties resolve FAR first."""
    _require(set(p_values) == set(TASKS), 'Holm family must be exactly FAR and SER')
    _require(all(math.isfinite(p_values[t]) and 0 <= p_values[t] <= 1 for t in TASKS), 'invalid p value')
    order = sorted(TASKS, key=lambda t: (p_values[t], TASKS.index(t)))
    result = dict.fromkeys(TASKS, False)
    for task, threshold in zip(order, (.025, .05)):
        if p_values[task] > threshold:
            break
        result[task] = True
    return result


def _unique_ids(values, label):
    _require(isinstance(values, (list, tuple)) and values and
        all(isinstance(x, str) and x for x in values) and len(set(values)) == len(values),
        'missing/duplicate '+label)
    return list(values)


def _cluster_layout(tasks):
    clusters = defaultdict(lambda: defaultdict(list))
    for task, source in sorted(tasks.items()):
        ids = _unique_ids(source['instance_ids'], 'instance_ids')
        words = source['pressure_texts']
        _require(len(words) == len(ids) and all(isinstance(w, str) and w for w in words),
                 'canonical pressure wording required for every ID')
        for index, word in enumerate(words):
            clusters[word][task].append(index)
    patterns = defaultdict(list)
    for word, members in clusters.items():
        patterns[tuple(sorted(members))].append(word)
    return clusters, [(pattern, sorted(words)) for pattern, words in sorted(patterns.items())]


def _draw_clusters(layout, task_names, rng):
    clusters, patterns = layout
    result = {t: dict(indices=[], occurrence_keys=[], cluster_occurrences=[]) for t in task_names}
    for pattern_index, (pattern, words) in enumerate(patterns):
        for occurrence, word_index in enumerate(rng.integers(0, len(words), len(words))):
            word = words[word_index]
            key = f'{pattern_index}:{occurrence}'
            for task in pattern:
                indices = clusters[word][task]
                result[task]['indices'].extend(indices)
                result[task]['occurrence_keys'].extend([key] * len(indices))
                result[task]['cluster_occurrences'].append(dict(pressure_text=word, occurrence=key))
    return result


def draw_pressure_clusters(tasks, rng):
    """Joint wording draw within task-incidence strata, retaining every ID."""
    return _draw_clusters(_cluster_layout(tasks), sorted(tasks), rng)


def _array(value, shape, label, *, correctness=False):
    result = np.asarray(value, dtype=float)
    _require(result.shape == shape, f'{label} requires shape {shape}')
    if correctness:
        _require(np.isfinite(result).all() and np.isin(result, (0, 1)).all(),
                 label+' correctness must be binary')
    return result


def _prepare(panel, *, power):
    allowed = {'schema_version','kind','split','seeds','axis_ids','tasks',
               'assessment_ids','assessment_utility_ids'}
    _require(not (set(panel)-allowed), 'unexpected top-level input keys')
    expected = 'validation' if power else 'assessment'
    _require(panel.get('split') == expected, expected+' split required')
    _require(panel.get('kind') == ('a3_direction_calibration' if power else 'a3_direction_outcomes'), 'invalid panel kind')
    _require(panel.get('schema_version') == 1, 'unsupported schema_version')
    _require(panel.get('seeds') == list(SEEDS), 'exact frozen seeds/order required')
    n_axes = 33 if power else 200
    _require(panel.get('axis_ids') == ['learned'] + list(range(n_axes-1)), 'missing/duplicate/reordered axes')
    _require(set(panel.get('tasks', {})) == set(TASKS), 'exact FAR/SER task family required')
    if power:
        _require(set(panel.get('assessment_ids', {})) == set(TASKS), 'assessment_ids required')
        _require(set(panel.get('assessment_utility_ids', {})) == {'IOI','MMLU'}, 'assessment_utility_ids required')
        for task in TASKS:
            _unique_ids(panel['assessment_ids'][task], 'assessment_ids')
        for condition in ('IOI','MMLU'):
            _unique_ids(panel['assessment_utility_ids'][condition], 'assessment_utility_ids')
    prepared = {}
    utility_ids = {}
    for task in TASKS:
        source = panel['tasks'][task]
        _require(not(set(source)-{'instance_ids','pressure_texts','conditions','utilities','epsilon','gate_valid'}),
                 'unexpected task input keys')
        ids = _unique_ids(source['instance_ids'], 'instance_ids')
        if power:
            _require(not(set(ids) & set(panel['assessment_ids'][task])), 'validation/assessment ID overlap')
        _require(set(source.get('conditions', {})) == set(CONDITIONS), 'missing/extra conditions')
        epsilon = np.broadcast_to(np.asarray(source.get('epsilon', 1e-6), dtype=float), (3,))
        _require(np.isfinite(epsilon).all() and (epsilon >= 1e-6).all(), 'invalid replay epsilon')
        valid = np.asarray(source.get('gate_valid', np.ones((n_axes,3), dtype=bool)))
        _require(valid.shape == (n_axes,3) and np.isin(valid, (False,True)).all(), 'invalid gate_valid')
        data = dict(instance_ids=ids, pressure_texts=source['pressure_texts'], conditions={}, utilities={},
                    epsilon=epsilon, gate_valid=valid.astype(bool))
        for condition in CONDITIONS:
            c = source['conditions'][condition]
            _require(set(c) == {'intact_margin','patched_margin','intact_correct','patched_correct'}, 'unexpected condition fields')
            out = {}
            for field in ('intact_margin','intact_correct','patched_margin','patched_correct'):
                shape = (3,len(ids),2) if field.startswith('intact') else (n_axes,3,len(ids),2)
                out[field] = _array(c[field], shape, field, correctness=field.endswith('correct'))
            # Margins stay per-stream for denominator validity. Correctness is
            # averaged inside ID, preserving the two designation streams.
            out['intact_accuracy'] = out['intact_correct'].mean(-1)
            out['patched_accuracy'] = out['patched_correct'].mean(-1)
            out['drop'] = (out['intact_margin'][None]-out['patched_margin']).mean(-1)
            data['conditions'][condition] = out
        _require('IOI' in source.get('utilities', {}), 'IOI utility required')
        _require(set(source['utilities']) <= set(UTILITY), 'unexpected utility conditions')
        mmlu_names = set(source['utilities']) & {'MMLU_zero','MMLU_h_mean'}
        _require(len(mmlu_names) in (0,2), 'both MMLU floors required together')
        for condition in UTILITY:
            if condition not in source['utilities']:
                continue
            u = source['utilities'][condition]
            _require(set(u) == {'prompt_ids','intact_correct','patched_correct'}, 'unexpected utility fields')
            prompts = _unique_ids(u['prompt_ids'], 'utility prompt_ids')
            family = 'IOI' if condition == 'IOI' else 'MMLU'
            if family == 'MMLU':
                _require(len(prompts) == 32, 'MMLU requires 32 fixed prompts')
            if family in utility_ids:
                _require(set(prompts) == set(utility_ids[family]), 'utility prompt IDs must match across tasks/operations')
            else:
                utility_ids[family] = sorted(prompts)
            if power:
                _require(not(set(prompts) & set(panel['assessment_utility_ids'][family])), 'validation/assessment utility overlap')
            data['utilities'][condition] = dict(prompt_ids=prompts,
                intact_correct=_array(u['intact_correct'],(3,len(prompts)),condition,correctness=True),
                patched_correct=_array(u['patched_correct'],(n_axes,3,len(prompts)),condition,correctness=True))
        prepared[task] = data
    return prepared, utility_ids, _cluster_layout(prepared)


def _utility_draws(utility_ids, rng, *, bootstrap):
    return {family: [ids[i] for i in (rng.integers(len(ids),size=len(ids)) if bootstrap else range(len(ids)))]
            for family,ids in sorted(utility_ids.items())}


def _utility_indices(utility, draws):
    by_id = {rid:i for i,rid in enumerate(utility['prompt_ids'])}
    # The caller supplies the utility family; no prompt-name inference is used.
    return [by_id[rid] for rid in draws]


def inject_correctness_loss(intact, uniforms, *, loss):
    """Cluster/prompt keyed uniforms; task/seed-specific A thresholds.

    Last dimension is ID/prompt, preceding dimensions identify seeds or streams.
    Public convenience helper computes baseline A over that last dimension.
    Internal mechanism usage averages streams first, which is algebraically the
    same because a single loss flag applies to both streams inside an ID.
    """
    base = np.asarray(intact, dtype=float)
    _require(base.ndim >= 1 and 0 <= loss <= 1, 'invalid correctness loss')
    _require(np.isfinite(base).all() and ((base >= 0) & (base <= 1)).all(), 'invalid intact accuracy')
    accuracy = base.mean(-1)
    _require(np.all(accuracy >= loss), 'infeasible collateral loss exceeds intact accuracy')
    threshold = np.divide(loss,accuracy,out=np.zeros_like(accuracy),where=accuracy>0)
    return base * (np.asarray(uniforms) >= threshold[...,None])


def _loss_patch(base, indices, uniforms, loss):
    """Use ORIGINAL validation A, never resampled A, for Bernoulli flags."""
    accuracy = base.mean(-1)
    losses = np.asarray(loss,dtype=float).reshape(-1,1)
    threshold = np.divide(losses,accuracy[None,:],out=np.zeros((len(losses),len(accuracy))),where=accuracy[None,:]>0)
    return base[None,:,indices] * (uniforms[None,None,:] >= threshold[:,:,None])


def _evaluate(task, indices, utility_draws, *, synthetic=None, uniforms=None, conditional_mmlu=False):
    """Vectorized axes x seed metrics; synthetic tuples label learned scenarios."""
    conditions = task['conditions']
    count = len(synthetic) if synthetic is not None else conditions['D']['drop'].shape[0]
    raw, fractions, gaps, valid = {}, {}, {}, np.ones(3,dtype=bool)
    losses = [s[2] for s in synthetic] if synthetic is not None else None
    for condition,neutral in (('D','H'),('I','user_neutral')):
        c = conditions[condition]
        gap_stream = (c['intact_margin'][:,indices,:]-conditions[neutral]['intact_margin'][:,indices,:]).mean(1)
        gap = gap_stream.mean(-1)
        ok = np.isfinite(gap_stream).all(-1) & (gap_stream > task['epsilon'][:,None]).all(-1)
        valid &= ok
        if synthetic is None:
            numerator = c['drop'][:,:,indices].mean(-1)
        else:
            original_gap = (c['intact_margin']-conditions[neutral]['intact_margin']).mean((1,2))
            residual = c['drop'][0]-c['drop'][0].mean(-1,keepdims=True)
            field = 0 if condition=='D' else 1
            injected = np.array([s[field] for s in synthetic])[:,None]
            numerator = injected*original_gap[None,:] + residual[:,indices].mean(-1)[None,:]
        fraction = np.divide(numerator,gap[None,:],out=np.full_like(numerator,np.nan),where=ok[None,:])
        fractions[condition] = fraction
        gaps[condition] = gap
        raw[condition] = dict(gap=gap,stream_gaps=gap_stream,drop=numerator,fraction_removed=fraction)
    shifts, additional_errors = {}, {}
    for condition in CONDITIONS:
        c = conditions[condition]
        intact = c['intact_accuracy'][:,indices].mean(-1)
        if synthetic is None:
            patched = c['patched_accuracy'][:,:,indices].mean(-1)
        elif condition in ('H','F'):
            patched = _loss_patch(c['intact_accuracy'],indices,uniforms[condition],losses).mean(-1)
        elif condition in ('D','I'):
            # Accuracy is not predicted by this margin noise model. Report it
            # as unavailable rather than fabricating condition-correct tokens.
            patched = np.full((count,3),np.nan)
        else:
            patched = np.broadcast_to(intact,(count,3))
        shifts[condition] = patched-intact[None,:]
        raw.setdefault(condition,{}).update(intact_accuracy=intact,patched_accuracy=patched,
            intact_margin=c['intact_margin'][:,indices,:].mean((1,2)))
        if synthetic is None:
            raw[condition]['patched_margin'] = c['patched_margin'][:,:,indices,:].mean((2,3))
        elif condition in ('D','I'):
            raw[condition]['patched_margin'] = raw[condition]['intact_margin'][None,:]-raw[condition]['drop']
    for condition,u in task['utilities'].items():
        family = 'IOI' if condition=='IOI' else 'MMLU'
        selected = _utility_indices(u,utility_draws[family])
        intact = u['intact_correct'][:,selected].mean(-1)
        if synthetic is None:
            patched = u['patched_correct'][:,:,selected].mean(-1)
        else:
            patched = _loss_patch(u['intact_correct'],selected,uniforms[family],losses).mean(-1)
        shifts[condition] = patched-intact[None,:]
        if family == 'MMLU':
            additional_errors[condition] = -shifts[condition]*32
    finite = np.isfinite(fractions['D']) & np.isfinite(fractions['I'])
    coverage = np.broadcast_to(task['gate_valid'][0],(count,3)) if synthetic is not None else task['gate_valid']
    point = finite & valid[None,:] & coverage & (fractions['D'] >= .5) & (fractions['I'] < .25)
    for condition in ('H','F','IOI'):
        # The tiny tolerance implements the exact strict 0.05 boundary under
        # floating arithmetic, matching ladder_metrics' point-gate convention.
        point &= np.isfinite(shifts[condition]) & (np.abs(shifts[condition]) < .05-1e-12)
    mmlu_complete = set(additional_errors) == {'MMLU_zero','MMLU_h_mean'}
    if mmlu_complete:
        for values in additional_errors.values():
            point &= values <= 1
    elif not conditional_mmlu:
        point[:] = False
    stats = np.where(point.all(-1),fractions['D'].mean(-1),-np.inf)
    return dict(statistics=stats,point_pass=point,denominator_valid=valid,D_fraction=fractions['D'],
                I_fraction=fractions['I'],contrast=fractions['D']-fractions['I'],gaps=gaps,raw=raw,
                collateral_shifts=shifts,MMLU_additional_errors=additional_errors,mmlu_complete=mmlu_complete)


def _identity_pressure(task):
    return dict(indices=list(range(len(task['instance_ids']))), occurrence_keys=list(task['pressure_texts']))


def _seed_reports(metrics, axis):
    result = []
    for j,seed in enumerate(SEEDS):
        raw = {}
        for condition,fields in metrics['raw'].items():
            raw[condition] = {name: values[j] if values.ndim <= 1 or name=='stream_gaps' else values[axis,j]
                              for name,values in fields.items()}
        result.append(dict(seed=seed,point_pass=metrics['point_pass'][axis,j],
            denominator_valid=metrics['denominator_valid'][j],D_fraction=metrics['D_fraction'][axis,j],
            I_fraction=metrics['I_fraction'][axis,j],D_minus_I=metrics['contrast'][axis,j],raw=raw,
            collateral_shifts={c:v[axis,j] for c,v in metrics['collateral_shifts'].items()},
            MMLU_additional_errors={c:v[axis,j] for c,v in metrics['MMLU_additional_errors'].items()},
            mmlu_complete=metrics['mmlu_complete']))
    return result


def _interval(values, n_boot):
    x = np.asarray(values, dtype=float)
    valid = np.isfinite(x).all(0)
    bounds = np.percentile(np.where(np.isfinite(x),x,0),[2.5,97.5],axis=0).T
    return [b.tolist() if ok else None for b,ok in zip(bounds,valid)], np.isfinite(x).sum(0).tolist()


def summarize_direction_outcomes(panel, *, n_boot=2000, seed=9001):
    """All gates, 199-axis comparison, Holm, and paired CIs as distinct outputs."""
    _require(type(n_boot) is int and n_boot > 0, 'n_boot must be positive')
    tasks,utility_ids,layout = _prepare(panel,power=False)
    rng = np.random.default_rng(seed)
    identity_utility = _utility_draws(utility_ids,rng,bootstrap=False)
    output = {}
    draws = {t:defaultdict(list) for t in TASKS}
    for task in TASKS:
        metrics = _evaluate(tasks[task],_identity_pressure(tasks[task])['indices'],identity_utility)
        output[task] = dict(seeds=_seed_reports(metrics,0),
            null_seeds=[_seed_reports(metrics,a) for a in range(1,200)],
            comparison=compare_triplets(metrics['statistics'][0],metrics['statistics'][1:]))
    for _ in range(n_boot):
        pressure = _draw_clusters(layout,TASKS,rng)
        utility = _utility_draws(utility_ids,rng,bootstrap=True)
        for task in TASKS:
            # Evaluate paired nulls too; retain their raw outcomes through the
            # shared draw, but do not turn interval precision into a new gate.
            metrics = _evaluate(tasks[task],pressure[task]['indices'],utility)
            for name in ('D_fraction','I_fraction','contrast'):
                draws[task][name].append(metrics[name][0])
            for condition in ('H','F','IOI','MMLU_zero','MMLU_h_mean'):
                if condition in metrics['collateral_shifts']:
                    draws[task][condition+'_shift'].append(metrics['collateral_shifts'][condition][0])
    rejection = holm_two({t:output[t]['comparison']['p_value'] for t in TASKS})
    for task in TASKS:
        intervals,counts = {},{}
        for name,values in draws[task].items():
            intervals[name],counts[name] = _interval(values,n_boot)
        output[task].update(holm_reject=rejection[task],intervals=intervals,valid_bootstrap_draws=counts)
    return _json(dict(tasks=output,confirmatory_family=['direction_FAR','direction_SER'],
        bootstrap=dict(seed=seed,n_boot=n_boot,unit='canonical wording; task-incidence strata; paired utility prompts',
                       seed_resampling=False),
        interpretation='Conditional on frozen fit/site selection and isotropic orientation benchmark; not a machinery permutation test.'))


def _mc(successes,n):
    if not n:
        return dict(probability=None,n_rejections=None,n_trials=0,mc_interval=None)
    p = successes/n
    z = 1.959963984540054
    center = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return dict(probability=p,n_rejections=int(successes),n_trials=n,
                mc_interval=[max(0.,center-half),min(1.,center+half)],mc_interval_method='Wilson 95% binomial')


def _scenarios():
    return [dict(mode=mode,D_fraction=d,I_fraction=i,collateral_loss=loss)
            for mode in ('shared','FAR_only','SER_only')
            for d,i,loss in itertools.product((0.,.25,.5,.75,1.),(0.,.2),(0.,.04))]


def _detectability(scenarios):
    output = []
    for mode,i,loss,task in itertools.product(('shared','FAR_only','SER_only'),(0.,.2),(0.,.04),TASKS):
        cells = sorted((s for s in scenarios if (s['mode'],s['I_fraction'],s['collateral_loss']) == (mode,i,loss)),
                       key=lambda s:s['D_fraction'])
        bracket = None
        for index,upper in enumerate(cells):
            hi = upper['rejections'][task]['probability']
            if hi is not None and hi >= .8:
                if index:
                    lower = cells[index-1]
                    lo = lower['rejections'][task]['probability']
                    if lo is not None and lo < .8:
                        bracket = [lower['D_fraction'],upper['D_fraction']]
                break
        output.append(dict(mode=mode,task=task,I_fraction=i,collateral_loss=loss,bracket=bracket,
                           status='bracketed' if bracket is not None else 'not bracketed'))
    return output


def simulate_conditional_power(calibration: dict, *, n_rep: int=2000, seed: int=19001) -> dict:
    """Validation-only additive-noise scenario analysis; no unconditional power.

    Original invalid denominators and infeasible collateral cells have undefined
    power. Bootstrap-invalid denominators remain in the n_rep denominator as
    nonrejections, and are counted separately. Any/both probabilities require
    BOTH task cells interpretable/feasible. Holm still includes a noninterpretable
    task with p=1, permitting the other task to reject at the first threshold.
    """
    _require(type(n_rep) is int and n_rep > 0, 'n_rep must be positive')
    tasks,utility_ids,layout = _prepare(calibration,power=True)
    rng = np.random.default_rng(seed)
    conditional = any('MMLU_zero' not in tasks[t]['utilities'] for t in TASKS)
    original_utility = _utility_draws(utility_ids,rng,bootstrap=False)
    original = {t:_evaluate(tasks[t],_identity_pressure(tasks[t])['indices'],original_utility,conditional_mmlu=True) for t in TASKS}
    original_valid = {t:bool(original[t]['denominator_valid'].all()) for t in TASKS}
    scenarios = _scenarios()
    n_scenarios = len(scenarios)
    eligible = np.ones((n_scenarios,2),dtype=bool)
    failures = np.zeros((n_scenarios,2,3),dtype=int)
    any_seed_failure = np.zeros((n_scenarios,2),dtype=int)
    all_seed_failure = np.zeros((n_scenarios,2),dtype=int)
    strict_passes = np.zeros((n_scenarios,2),dtype=int)
    rejects = np.zeros((n_scenarios,2),dtype=int)
    any_reject = np.zeros(n_scenarios,dtype=int)
    both_reject = np.zeros(n_scenarios,dtype=int)
    invalid_draws = np.zeros(2,dtype=int)
    failed_nulls = np.zeros((2,n_rep),dtype=int)
    injected = {}
    for j,t in enumerate(TASKS):
        injected[t] = [(s['D_fraction'] if s['mode']=='shared' or (s['mode']=='FAR_only' and j==0) or (s['mode']=='SER_only' and j==1) else 0.,
                        s['I_fraction'],s['collateral_loss']) for s in scenarios]
        for a,s in enumerate(scenarios):
            loss = s['collateral_loss']
            baseline_accuracies = [tasks[t]['conditions'][c]['intact_accuracy'].mean(-1) for c in ('H','F')]
            baseline_accuracies += [u['intact_correct'].mean(-1) for u in tasks[t]['utilities'].values()]
            eligible[a,j] = original_valid[t] and all((accuracy >= loss).all() for accuracy in baseline_accuracies)
    for rep in range(n_rep):
        pressure = _draw_clusters(layout,TASKS,rng)
        utility = _utility_draws(utility_ids,rng,bootstrap=True)
        # One null-axis index bank shared across every seed, task and scenario.
        null_indices = rng.integers(1,33,size=199)
        # One occurrence bank: repeated bootstrap copies have fresh uniforms,
        # while all member IDs/streams/seeds/tasks retain their linkage.
        keys = sorted({key for t in TASKS for key in pressure[t]['occurrence_keys']})
        pressure_uniform = {c:dict(zip(keys,rng.random(len(keys)))) for c in ('H','F')}
        utility_uniform = {family:rng.random(len(ids)) for family,ids in sorted(utility.items())}
        pvalues = np.ones((n_scenarios,2))
        for j,t in enumerate(TASKS):
            selected = pressure[t]['indices']
            uniforms = {c:np.array([pressure_uniform[c][k] for k in pressure[t]['occurrence_keys']]) for c in ('H','F')}
            uniforms.update(utility_uniform)
            null_metrics = _evaluate(tasks[t],selected,utility,conditional_mmlu=True)
            null_stats = null_metrics['statistics'][null_indices]
            failed_nulls[j,rep] = int(np.isneginf(null_stats).sum())
            invalid_draws[j] += not null_metrics['denominator_valid'].all()
            learned = _evaluate(tasks[t],selected,utility,synthetic=injected[t],uniforms=uniforms,conditional_mmlu=True)
            failures[:,j,:] += ~learned['point_pass']
            any_seed_failure[:,j] += (~learned['point_pass']).any(-1)
            all_seed_failure[:,j] += (~learned['point_pass']).all(-1)
            stats = learned['statistics']
            threshold = np.sort(null_stats)[math.ceil(.95*199)-1]
            strict_passes[:,j] += np.isfinite(stats) & (stats > threshold) & eligible[:,j]
            passed = np.isfinite(stats) & eligible[:,j]
            pvalues[passed,j] = (1+(null_stats[None,:] >= stats[passed,None]).sum(-1))/200
        # Vectorized exact two-family Holm; equal p-values use FAR first.
        first = np.argmin(pvalues,axis=1)
        second = 1-first
        index = np.arange(n_scenarios)
        first_pass = pvalues[index,first] <= .025
        second_pass = first_pass & (pvalues[index,second] <= .05)
        decision = np.zeros((n_scenarios,2),dtype=bool)
        decision[index,first] = first_pass
        decision[index,second] = second_pass
        rejects += decision
        any_reject += decision.any(-1)
        both_reject += decision.all(-1)
    for a,s in enumerate(scenarios):
        infeasible = []
        for j,t in enumerate(TASKS):
            if not eligible[a,j] and original_valid[t]:
                infeasible.append(t)
        s.update(original_denominator_valid=original_valid.copy(),infeasible_tasks=infeasible,
            bootstrapped_denominator_invalid=dict(zip(TASKS,invalid_draws.tolist())),
            per_seed_gate_failure_frequency={t:dict(zip(map(str,SEEDS),(failures[a,j]/n_rep).tolist())) for j,t in enumerate(TASKS)},
            all_seed_gate_failure_frequency={t:float(all_seed_failure[a,j]/n_rep) for j,t in enumerate(TASKS)},
            any_seed_gate_failure_frequency={t:float(any_seed_failure[a,j]/n_rep) for j,t in enumerate(TASKS)},
            strict_null_pass_frequency={t:float(strict_passes[a,j]/n_rep) if eligible[a,j] else None for j,t in enumerate(TASKS)},
            rejections={t:_mc(rejects[a,j],n_rep if eligible[a,j] else 0) for j,t in enumerate(TASKS)},
            any_rejection=_mc(any_reject[a],n_rep if eligible[a].all() else 0),
            both_rejections=_mc(both_reject[a],n_rep if eligible[a].all() else 0))
    return _json(dict(n_rep=n_rep,seed=seed,scenarios=scenarios,detectability=_detectability(scenarios),
        conditional_on_mmlu_guard=conditional,full_gate_power=not conditional,
        null_approximation=dict(calibration_axes=32,expanded_axes=199,shared_indices=True,
            description='Bootstrap expansion of validation axes; not finite-199 unconditional discovery power.'),
        calibration_coverage={t:dict(n_ids=len(tasks[t]['instance_ids']),n_pressure_clusters=len(set(tasks[t]['pressure_texts'])),
            n_seeds=3,n_null_axes=32,utilities={c:len(u['prompt_ids']) for c,u in tasks[t]['utilities'].items()},
            original_denominator_valid=original_valid[t],original_gaps=original[t]['gaps'],
            failed_null_triplets=dict(total=int(failed_nulls[j].sum()),minimum=int(failed_nulls[j].min()),maximum=int(failed_nulls[j].max())))
            for j,t in enumerate(TASKS)},
        interpretation='Conditional on frozen sites, validation residuals, original validation gaps and calibration orientations; additive noise, not prompt generation.',
        bootstrap=dict(unit='canonical wording within task-incidence strata; paired utility prompts',seed_resampling=False),
        denominator_policy='Original invalid/infeasible: undefined. Resampled invalid: counted nonrejection, never clipped.'))
