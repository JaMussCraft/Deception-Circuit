"""Pure paired specificity estimates; no model calls or dataset filtering.

Canonical margins are opposite-minus-honest throughout. Mechanism rows require
both streams; IOI/MMLU use the clean assessment only (corruption is a donor).
Missing/unsupported primary observations block a gate rather than changing its
sample. Bootstrap units are source pressure IDs, preserving all paired arms.
"""
from __future__ import annotations

from collections import defaultdict
import math
import numpy as np

MECHANISM = ('D', 'H', 'F', 'I', 'user_neutral')


def _mean(values):
    return float(np.mean(values)) if len(values) else None


def _paired(rows):
    by = defaultdict(list)
    for row in rows:
        by[(row['condition'], row['instance_id'])].append(row)
    result = {}
    for key, records in by.items():
        required = {'clean'} if key[0] in ('IOI', 'MMLU') else {'clean', 'corrupt'}
        streams = [r['stream'] for r in records]
        if set(streams) != required or len(streams) != len(required):
            raise ValueError(f'missing or duplicate assessment stream for {key}')
        result[key] = records
    return result


def _estimate(paired, ids, epsilon):
    result = {}
    for condition, neutral in [('D', 'H'), ('I', 'user_neutral')]:
        gap, drop = [], []
        stream_gaps = defaultdict(list)
        stream_drops = defaultdict(list)
        for rid in ids:
            rows = paired[(condition, rid)]
            twins = {r['stream']: r for r in paired[(neutral, rid)]}
            gaps = [r['intact_margin']-twins[r['stream']]['intact_margin'] for r in rows]
            gap.append(_mean(gaps))
            drop.append(_mean([r['intact_margin']-r['patched_margin'] for r in rows]))
            for row, one in zip(rows, gaps):
                stream_gaps[row['stream']].append(one)
                stream_drops[row['stream']].append(row['intact_margin']-row['patched_margin'])
        denominator, numerator = _mean(gap), _mean(drop)
        per_stream = {s: _mean(v) for s,v in stream_gaps.items()}
        valid = (denominator is not None and math.isfinite(denominator) and denominator > epsilon
                 and all(math.isfinite(v) and v > epsilon for v in per_stream.values())
                 and numerator is not None and math.isfinite(numerator))
        result[condition] = dict(gap=denominator, drop=numerator,
                                 fraction_removed=numerator/denominator if valid else None,
                                 stream_gaps=per_stream,
                                 streams={s:dict(gap=v,drop=_mean(stream_drops[s]),fraction_removed=_mean(stream_drops[s])/v if math.isfinite(v) and v>epsilon else None) for s,v in per_stream.items()},
                                 interpretable=valid)
    return result


def _accuracy(records):
    intact = _mean([float(r['intact_correct']) for r in records])
    patched = _mean([float(r['patched_correct']) for r in records])
    return dict(intact_accuracy=intact, patched_accuracy=patched,
                accuracy_shift=_mean([float(r['patched_correct'])-float(r['intact_correct']) for r in records]),
                nontrivial=bool(records) and all(r.get('gate_valid', True) and not r.get('degenerate',False) for r in records))


def _seed_average(rows):
    """Average independent donors inside recipient before paired estimates."""
    by=defaultdict(list)
    for row in rows:
        by[(row.get('task','mechanism'),row['condition'],row['instance_id'],row['stream'])].append(row)
    result=[]
    seed_sets=set()
    for records in by.values():
        seeds=[r.get('donor_seed') for r in records]
        if len(set(seeds))!=len(seeds) or None in seeds:
            raise ValueError('independent resample requires unique explicit donor seeds')
        seed_sets.add(tuple(sorted(seeds)))
        record=dict(records[0])
        for field in ('intact_margin','patched_margin','intact_correct','patched_correct'):
            record[field]=_mean([float(r[field]) for r in records])
        record['supported']=all(r.get('supported',True) for r in records)
        record['gate_valid']=all(r.get('gate_valid',True) for r in records)
        record['donor_seed_range']=[min(r['patched_margin'] for r in records), max(r['patched_margin'] for r in records)]
        result.append(record)
    if len(seed_sets)!=1: raise ValueError('independent donor seed coverage differs between recipients')
    return result


def summarize_ladder(rows: list[dict], *, bootstrap_seed: int = 1, n_boot: int = 2000) -> dict:
    """Ratio of means, exact START gates and paired cluster percentile CIs.

    Returns one cell per mechanism task/group/operation. Utility rows with the
    same group/operation are attached to each native task, never pooled into its
    pressure denominator. Independent donor seeds are resampled at the outer
    bootstrap level; deterministic twins have no seed variation.
    """
    if n_boot < 1: raise ValueError('n_boot must be positive')
    memberships={}
    for row in rows:
        if 'group_members' not in row:
            raise ValueError('group membership provenance required')
        members=tuple(sorted(tuple(k) for k in row['group_members']))
        if row['group'] in memberships and memberships[row['group']]!=members:
            raise ValueError('group label has conflicting membership')
        memberships[row['group']]=members
    grouped=defaultdict(list)
    utility=defaultdict(list)
    for r in rows:
        if r.get('task') not in ('far_v2','sdr_v2','ser_v2','ioi','mmlu'):
            raise ValueError('explicit supported native task required')
        if (r['condition']=='IOI' and r['task']!='ioi') or (r['condition']=='MMLU' and r['task']!='mmlu'):
            raise ValueError('utility condition/task mismatch')
        if r['condition'] in MECHANISM and r['task'] not in ('far_v2','sdr_v2','ser_v2'):
            raise ValueError('mechanism condition/task mismatch')
        if r['condition']=='MMLU' and r['operation'] not in ('zero','h_mean','empty','self_replay'):
            raise ValueError('MMLU has no native donor operation; only zero/H-mean floor and replay controls apply')
        if r['condition'] in ('IOI','MMLU'): utility[(r['group'],r['operation'])].append(r)
        else: grouped[(r.get('task','mechanism'),r['group'],r['operation'])].append(r)
    cells=[]
    for (task,group,operation), source in sorted(grouped.items()):
        original=source+utility[(group,operation)]
        coverage=dict(total=len(original),unsupported=sum(not r.get('supported',True) for r in original),
                      invalid=sum(not r.get('assay_valid',True) for r in original),
                      degenerate=sum(r.get('degenerate',False) for r in original),
                      requested_positions=sum((r.get('donor_provenance') or {}).get('requested_positions',0) for r in original),
                      covered_positions=sum((r.get('donor_provenance') or {}).get('covered_positions',0) for r in original))
        coverage['by_condition']={c:dict(total=sum(r['condition']==c for r in original),
            unsupported=sum(r['condition']==c and not r.get('supported',True) for r in original))
            for c in MECHANISM+('IOI','MMLU')}
        independent=operation=='independent_resample'
        if independent and {r.get('donor_seed') for r in original}!={101,102,103}:
            raise ValueError('independent resample requires donor seeds 101, 102, 103')
        # Validate the frozen sample before selecting diagnostic support. Unsupported
        # rows may lack outcomes; never average their absent values or change the
        # assessment denominator invisibly.
        for seed in (101,102,103) if independent else (None,):
            frozen=_paired([r for r in original if not independent or r['donor_seed']==seed])
            frozen_ids={rid for c,rid in frozen if c=='D'}
            if any({rid for c,rid in frozen if c==condition}!=frozen_ids for condition in MECHANISM):
                raise ValueError('required primary conditions must contain the same paired ids')
        if independent:
            seed_keys=defaultdict(set)
            for r in original: seed_keys[(r['condition'],r['instance_id'],r['stream'])].add(r['donor_seed'])
            if any(seeds!={101,102,103} for seeds in seed_keys.values()):
                raise ValueError('independent donor seed coverage differs between recipients')
        assessment_ids=sorted({r['instance_id'] for r in source if r['condition']=='D'})
        by_key=defaultdict(list)
        for r in original:
            by_key[(r['condition'],r['instance_id'])].append(r)
        supported_keys={key for key,records in by_key.items() if all(r.get('supported',True) for r in records)}
        needed=MECHANISM if independent else ('D','H','I','user_neutral')
        supported_ids=[rid for rid in assessment_ids if all((c,rid) in supported_keys for c in needed)]
        diagnostic=[r for r in original if (r['condition'],r['instance_id']) in supported_keys
                    and (r['condition'] not in MECHANISM or r['instance_id'] in supported_ids)]
        subset=dict(ids=supported_ids,n_ids=len(supported_ids),diagnostic_only=bool(coverage['unsupported']),
                    required_conditions=list(needed),required_donor_seeds=[101,102,103] if independent else [],
                    by_condition={c:dict(n_assessment_ids=len({r['instance_id'] for r in original if r['condition']==c}),
                        n_supported_ids=len({r['instance_id'] for r in diagnostic if r['condition']==c}))
                        for c in MECHANISM+('IOI','MMLU')})
        if not supported_ids:
            cells.append(dict(task=task,group=group,group_members=[list(k) for k in memberships[group]],
                operation=operation,coverage=coverage,n_assessment_ids=len(assessment_ids),
                supported_subset=subset,assessment_sample_changed=False,
                interpretable=False,point_pass=False,strong=False,status='unsupported'))
            continue
        averaged=_seed_average(diagnostic) if independent else diagnostic
        paired=_paired(averaged)
        by_condition={c:{rid for (condition,rid) in paired if condition==c} for c in MECHANISM}
        ids=sorted(by_condition['D'])
        if not ids or any(by_condition[c]!=set(ids) for c in ('D','H','I','user_neutral')):
            raise ValueError('required primary conditions must contain the same paired ids')
        errors=[abs(r.get('self_replay_margin_error',0)) for r in original]
        epsilon=max(1e-6,10*max(errors,default=0))
        effect=_estimate(paired,ids,epsilon)
        collateral={c:_accuracy([r for r in averaged if r['condition']==c]) for c in ('H','F','IOI')}
        utility_rows=[r for r in averaged if r['condition']=='MMLU']
        mmlu=_accuracy(utility_rows)
        mmlu['additional_errors']=sum(float(r['intact_correct'])-float(r['patched_correct']) for r in utility_rows)
        mmlu['pass']=len(utility_rows)==32 and mmlu['additional_errors']<=1 if utility_rows else None
        clusters=defaultdict(list)
        for rid in ids:
            labels={str(r.get('pressure_id',rid)) for c in MECHANISM for r in paired.get((c,rid),[])}
            if len(labels)!=1: raise ValueError('pressure cluster differs across paired arms')
            clusters[labels.pop()].append(rid)
        rng=np.random.default_rng(bootstrap_seed)
        intervals={c:[] for c in ('D','I')}
        collateral_draws={c:[] for c in collateral}
        mmlu_draws=[]
        cluster_names=sorted(clusters)
        seeds=sorted({r['donor_seed'] for r in original}) if independent else []
        for _ in range(n_boot):
            sample=[rid for cluster in rng.choice(cluster_names,len(cluster_names),replace=True) for rid in clusters[cluster]]
            boot_paired=paired
            boot_rows=averaged
            if independent:
                drawn=rng.choice(seeds,len(seeds),replace=True).tolist()
                # Repeated seed observations are weighted, then averaged.
                weighted=[]
                for index,seed in enumerate(drawn):
                    for r in diagnostic:
                        if r['donor_seed']==seed: weighted.append(dict(r,donor_seed=index))
                boot_rows=_seed_average(weighted); boot_paired=_paired(boot_rows)
            estimate=_estimate(boot_paired,sample,epsilon)
            for c in intervals:
                v=estimate[c]['fraction_removed']
                if v is not None: intervals[c].append(v)
            for c in collateral_draws:
                if c in ('H','F'):
                    values=[r for rid in sample for r in boot_paired.get((c,rid),[])]
                else:
                    uids=sorted({rid for condition,rid in boot_paired if condition==c})
                    values=[r for rid in rng.choice(uids,len(uids),replace=True) for r in boot_paired.get((c,rid),[])] if uids else []
                shift=_accuracy(values)['accuracy_shift']
                if shift is not None: collateral_draws[c].append(shift)
            mids=sorted({rid for condition,rid in boot_paired if condition=='MMLU'})
            if mids:
                sampled=[r for rid in rng.choice(mids,len(mids),replace=True) for r in boot_paired[('MMLU',rid)]]
                mmlu_draws.append(_accuracy(sampled)['accuracy_shift'])
        mmlu['shift_interval']=np.percentile(mmlu_draws,[2.5,97.5]).tolist() if mmlu_draws else None
        mmlu['additional_errors_interval']=np.percentile([-v*len(utility_rows) for v in mmlu_draws],[2.5,97.5]).tolist() if mmlu_draws else None
        for c,values in intervals.items():
            effect[c]['fraction_interval']=np.percentile(values,[2.5,97.5]).tolist() if len(values)==n_boot else None
            effect[c]['valid_bootstrap_draws']=len(values)
        for c,values in collateral_draws.items():
            collateral[c]['shift_interval']=np.percentile(values,[2.5,97.5]).tolist() if values else None
        interpretable=all(effect[c]['interpretable'] for c in effect) and not coverage['invalid']
        point=bool(not coverage['unsupported'] and interpretable and effect['D']['fraction_removed']>=.5 and effect['I']['fraction_removed']<.25
                   and all(v['nontrivial'] and v['accuracy_shift'] is not None and abs(v['accuracy_shift'])<.05-1e-12 for v in collateral.values())
                   and mmlu['pass'] is not False)
        strong=point and effect['D']['fraction_interval'] is not None and effect['I']['fraction_interval'] is not None
        strong=bool(strong and effect['D']['fraction_interval'][0]>=.5 and effect['I']['fraction_interval'][1]<.25
                    and all(v['shift_interval'] is not None and v['shift_interval'][0]>-.05 and v['shift_interval'][1]<.05 for v in collateral.values()))
        raw={c:dict(intact_margin=_mean([r['intact_margin'] for r in averaged if r['condition']==c]),
                    patched_margin=_mean([r['patched_margin'] for r in averaged if r['condition']==c]),
                    **_accuracy([r for r in averaged if r['condition']==c])) for c in MECHANISM}
        cells.append(dict(task=task,group=group,group_members=[list(k) for k in memberships[group]],operation=operation,coverage=coverage,
                          D=effect['D'],I=effect['I'],collateral=collateral,MMLU=mmlu,
                          raw=raw,epsilon=epsilon,n_ids=len(ids),n_assessment_ids=len(assessment_ids),
                          supported_subset=subset,assessment_sample_changed=False,n_clusters=len(clusters),
                          donor_seeds=seeds,donor_seed_rows=original if independent else [],
                          donor_averages=averaged if independent else [],
                          warnings=['few pressure clusters; limited bootstrap precision'] if len(clusters)<20 else [],
                          interpretable=interpretable,point_pass=point,strong=strong,
                          status='unsupported' if coverage['unsupported'] else 'strong' if strong else 'uncertain' if point else 'fails' if interpretable else 'uninterpretable'))
    # Coverage readiness is separate from any local operation's scientific gate.
    # MMLU is assessed only by its fixed zero/H-mean utility cells, never by an
    # invented item swap. These cells are joined by group and frozen row ids.
    for cell in cells:
        task,group=cell['task'],cell['group']
        expected={r['instance_id'] for r in grouped[(task,group,cell['operation'])] if r['condition']=='D'}
        missing=[]
        for op in ('item_swap','zero','h_mean','h_twin'):
            records=grouped.get((task,group,op),[])
            required=MECHANISM if op!='h_twin' else ('D','H','I','user_neutral')
            complete=all({r['instance_id'] for r in records if r['condition']==c}==expected for c in required)
            complete=complete and bool(records) and all(r.get('supported',True) and r.get('assay_valid',True)
                for r in records if r['condition'] in required)
            if not complete: missing.append(op)
        floors={}
        for op in ('zero','h_mean'):
            records=utility.get((group,op),[])
            records=[r for r in records if r['condition']=='MMLU']
            ids=[r['instance_id'] for r in records]
            complete=(len(ids)==32 and len(set(ids))==32 and all(r['stream']=='clean'
                and r.get('supported',True) and r.get('assay_valid',True)
                and r.get('gate_valid',True) and not r.get('degenerate',False) for r in records))
            errors=sum(float(r['intact_correct'])-float(r['patched_correct']) for r in records) if complete else None
            floors[op]=dict(n_rows=len(records),complete=complete,ids=ids,
                           additional_errors=errors,passed=complete and errors<=1)
        same_ids=set(floors['zero']['ids'])==set(floors['h_mean']['ids'])
        mmlu_complete=all(v['complete'] for v in floors.values()) and same_ids
        mmlu=dict(complete=mmlu_complete,same_ids=same_ids,operations=floors,
                  missing_operations=[op for op,v in floors.items() if not v['complete']],
                  passed=mmlu_complete and all(v['passed'] for v in floors.values()))
        ioi=[r for r in utility.get((group,'item_swap'),[]) if r['condition']=='IOI']
        ioi_complete=bool(ioi) and len({r['instance_id'] for r in ioi})==len(ioi) and all(
            r['stream']=='clean' and r.get('supported',True) and r.get('assay_valid',True)
            and r.get('gate_valid',True) and not r.get('degenerate',False) for r in ioi)
        ready=not missing and mmlu_complete and ioi_complete
        cell['assay_readiness']=dict(complete=ready,missing_crossed_operations=missing,
                                    MMLU=mmlu,IOI=dict(complete=ioi_complete,n_rows=len(ioi)))
        cell['complete_assay_ready']=ready
    return dict(cells=cells,bootstrap=dict(seed=bootstrap_seed,n_boot=n_boot,confidence=.95,
                                         unit='source pressure id; paired id for utility',donor_seed_outer='independent_resample only'))
