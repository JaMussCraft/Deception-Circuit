"""A3 semantic edge orchestration; production execution is separately admitted.

The graph is frozen before attribution. Source adapters derive native singleton
batches and builder maps from A3 parents; no caller token/position assertion is
accepted. Attribution is a token SUM. Exact interventions use simultaneous
intact-delta receiver clamping; downstream clamps can mask upstream effects.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import numpy as np
import torch
from component_analysis import a3_edges as core
from component_analysis import a3_directions
from component_analysis import a3_design
from component_analysis import a3_direction_runtime as authority
from component_analysis import a3_direction_artifacts as artifacts
from component_analysis import ladder_design
from component_analysis import ladder_pipeline as ladder
from dataset import user_inversion_pipeline as common

require=common.require
SEEDS=(42,1,123)
CONDITIONS=('D','H','F','I','user_neutral')
STREAMS=('clean','corrupt')
BUDGETS=(1,4,16)
BINS=a3_design.BINS
ESTIMAND='simultaneous intact-delta receiver clamping; downstream/readout clamps may mask upstream effects'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


def _membership(design,task,split):
    require(task in design['tasks'],'unknown task')
    spec=design['tasks'][task]
    fields={'train':'fit_ids','validation':'selection_ids','test':'assessment_ids'}
    require(split in fields,'unknown source split')
    groups=[spec[f] for f in fields.values()]
    require(all(isinstance(x,list) and x and len(set(x))==len(x) for x in groups),'invalid source membership')
    require(sum(map(len,groups))==len(set(sum(groups,[]))),'split membership overlap')
    return spec[fields[split]]


def _row(design,task,split,rid,condition):
    require(rid in _membership(design,task,split),'requested ID outside frozen split membership')
    rows=[r for r in design['access_rows'][task] if r['instance_id']==rid and r['condition']==condition and r['split']==split]
    require(len(rows)==1,'missing/duplicate canonical source row')
    return rows[0]


def _batch(row,stream,*,physical_width=None):
    require(stream in STREAMS,'invalid stream')
    s=row['streams'][stream]; tokens=s['tokens']; sem=s.get('semantic')
    require(tokens and all(type(x) is int and x>=0 for x in tokens),'invalid parent tokens')
    mask=s.get('attention_mask',[1]*len(tokens))
    require(mask==[1]*len(tokens) and s['readout']==len(tokens)-1,'changed source mask/readout')
    require(isinstance(sem,dict) and sem['prompt_utf8_hex']==s['prompt'].encode().hex(),'semantic prompt bytes changed')
    require(set(sem['sites'])==set(BINS),'missing semantic metadata')
    positions={}
    for name,indices in sem['sites'].items():
        require(isinstance(indices,list) and len(set(indices))==len(indices) and all(type(p) is int and 0<=p<len(tokens) for p in indices),'invalid parent semantic positions')
        positions[name]=[list(indices)]
    require(positions['assistant_readout']==[[s['readout']]],'changed semantic readout')
    result=dict(input_ids=torch.tensor([tokens]),attention_mask=torch.tensor([mask]),readout=torch.tensor([s['readout']]),
        opposite_token=torch.tensor([s['opposite_token']]),honest_token=torch.tensor([s['honest_token']]),expected_token=torch.tensor([s['expected_token']]),
        instance_ids=[row['instance_id']],condition=row['condition'],stream=stream,positions=positions,
        position_cells={x['key']:x for x in position_cells()})
    if physical_width is not None:
        require(type(physical_width) is int and physical_width>=len(tokens),'physical width would truncate source')
        padding=physical_width-len(tokens)
        result['input_ids']=torch.nn.functional.pad(result['input_ids'],(0,padding),value=0)
        result['attention_mask']=torch.nn.functional.pad(result['attention_mask'],(0,padding),value=0)
    return result


def position_cells():
    # Each semantic span is one cell; its token contractions are summed.
    return [dict(key=b,semantic_bin=b,receiver_kinds=['q','k','v','mlp_in','readout'] if b=='assistant_readout' else ['q','k','v','mlp_in']) for b in BINS]


def source_pair(design,task,split,rid,condition,stream,*,purpose):
    require(purpose in ('attribution','validation','assessment'),'unknown source purpose')
    require(not (purpose=='attribution' and split=='test'),'assessment forbidden for attribution')
    require(purpose!='validation' or split=='validation','selection must use validation')
    require(purpose!='assessment' or split=='test','assessment must use frozen test')
    row=_row(design,task,split,rid,condition)
    batch=_batch(row,stream,physical_width=source_width(design,task))
    if purpose=='attribution':
        require(condition in ('D','I'),'only D/I attribution')
        peer='H' if condition=='D' else 'user_neutral'
        donor=_row(design,task,split,rid,peer); donor_stream=stream
        records=[m for m in design['semantic_twin_maps'][task] if m['instance_id']==rid and m['recipient_condition']==condition and m['stream']==stream]
        require(len(records)==1,'missing/duplicate authenticated twin map')
        mapping=copy.deepcopy(records[0])
        require(mapping['donor_condition']==peer,'wrong authenticated neutral donor condition')
    else:
        donor=row; donor_stream=STREAMS[1-STREAMS.index(stream)]
        mapping=ladder_design.donor_plan(row,[],operation='item_swap',stream=stream,seed=1)
        # Unsupported ancestry is retained for explicit blocked rows.
    mapping.update(recipient_id=rid,donor_id=donor['instance_id'],recipient_stream=stream,donor_stream=donor_stream)
    return dict(batch=batch,neutral=_batch(donor,donor_stream,physical_width=source_width(design,task)),maps={'rows':[mapping]})


def prepare_graph(design,task,geometry):
    """Freeze graph and explicit unsupported bins from source coverage only."""
    rows=design['access_rows'][task]
    needed=set(sum([_membership(design,task,s) for s in ('train','validation','test')],[]))
    supported=set(BINS); reasons={}
    for row in rows:
        if row['instance_id'] not in needed: continue
        for stream in STREAMS:
            b=_batch(row,stream)
            for name in BINS:
                if not b['positions'][name][0]:
                    supported.discard(name); reasons[name]='missing own-condition exact semantic span'
            # Overlapping bins must never count one residual token twice.
            for a in BINS:
                for c in BINS:
                    if a<c and set(b['positions'][a][0])&set(b['positions'][c][0]):
                        supported.discard(a);supported.discard(c)
                        reasons[a]=reasons[c]='overlapping semantic cells'
    cells=position_cells()  # Unsupported rows never change the prospective graph.
    require(cells,'no supported semantic graph')
    geom=dict(geometry,position_cells=cells)
    edges=core.edge_grid(design['tasks'][task],geom)
    require(edges,'empty causal graph')
    return json.loads(json.dumps(dict(task=task,geometry=geom,edges=edges,unsupported_bins=reasons,
        token_aggregation='sum',estimand=ESTIMAND,source_sha256=digest(rows),padded_width=source_width(design,task))))


def bootstrap(design,task,seed):
    require(seed in SEEDS,'unsupported bootstrap seed')
    ids=_membership(design,task,'train')
    clusters=[a3_design._pressure(_row(design,task,'train',rid,'D')) for rid in ids]
    _,receipt=a3_directions._cluster_weights(clusters,ids,len(ids),seed)
    receipt['id_weights']=receipt['id_weights'].tolist()
    return receipt


def _move(item,model):
    device=next(model.parameters()).device
    return {k:({x:(y.to(device) if torch.is_tensor(y) else y) for x,y in v.items()} if k in ('batch','neutral') else v) for k,v in item.items()}


def fit_rankings(model,design,task,graph,*,steps=8,guard):
    require(steps in (2,8,16) and (steps!=2 or design.get('injected')),'unsupported integration nodes')
    require(graph['source_sha256']==digest(design['access_rows'][task]),'changed graph sources')
    result=[]
    for seed in SEEDS:
        receipt=bootstrap(design,task,seed); rankings={}
        for condition in ('D','I'):
            totals={edge_key(e):0. for e in graph['edges']}; unsupported={}
            for rid,weight in zip(receipt['instance_ids'],receipt['id_weights']):
                for stream in STREAMS:
                    guard()
                    item=_move(source_pair(design,task,'train',rid,condition,stream,purpose='attribution'),model)
                    supported,missing=supported_edges(item,graph['edges'])
                    for e in missing:unsupported.setdefault(edge_key(e),[]).append([rid,stream])
                    if supported:
                        scores=core.attribute_edges(model,[item],edges=supported,steps=steps)
                        for record in scores:totals[edge_key(record['edge'])]+=weight*.5*record['score']
            values=[dict(edge=e,score=None if edge_key(e) in unsupported else totals[edge_key(e)],
                supported=edge_key(e) not in unsupported,unsupported_rows=unsupported.get(edge_key(e),[]),
                steps=steps,token_aggregation='sum within cell; cohort-weighted across rows') for e in graph['edges']]
            rankings[condition]=values
        result.append(dict(seed=seed,bootstrap=receipt,rankings=rankings))
    return dict(kind='a3_edge_fit',split='train',fits=result,graph_sha256=digest(graph),steps=steps,injected=design.get('injected',False))


def execute(inventory,root,producer,*,guard,resume=False):
    """Immutable exact-coverage singleton shards; source refresh before every read."""
    root=Path(root); expected=inventory['expected_keys']
    require(expected and len({digest(k) for k in expected})==len(expected),'duplicate/empty coverage')
    identity=digest(inventory)
    index=root/'inventory'
    guard()
    if index.exists():
        require(resume and authority.read_object(index)==inventory,'immutable restart inventory changed')
    else:
        require(not root.exists() or not list(root.iterdir()),'unindexed partial output')
        authority.publish_object(index,inventory)
    observed=[]
    for key in expected:
        guard(); path=root/digest(key)
        if path.exists():
            require(resume,'existing immutable shard requires resume')
            row=authority.read_object(path)
        else:
            row=dict(inventory_sha256=identity,key=key,result=producer(key))
            authority.publish_object(path,row)
        require(row['inventory_sha256']==identity and row['key']==key,'changed shard identity')
        observed.append(row)
    require({p.name for p in root.iterdir()}=={'inventory'}|{digest(k) for k in expected},'unexpected shard coverage')
    return observed


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('design','commit','work-dir'):p.add_argument('--'+name,required=True)
    p.add_argument('--stage',required=True,choices=('prepare','pilot','fit','select','assess','summarize'))
    for flag in ('dry-run','resume','final'):p.add_argument('--'+flag,action='store_true')
    p.add_argument('--registry',action='append',default=[])
    p.add_argument('--steps',type=int,choices=(8,16),default=8)
    p.add_argument('--measure-stage',choices=('fit','select','assess'),default='fit')
    p.add_argument('--measurement',action='append',default=[])
    for name in ('ledger-snapshot','reservation','inventory','selection','prepared','pilot-evidence','integration-admission','model-control','packing-control','toy-evidence','geometry','fit-evidence'):
        p.add_argument('--'+name)
    return p


RULES=dict(rank='descending signed canonical opposite-minus-honest contribution; retain zero and negative scores',
    ties='canonical edge key',budgets=[1,4,16],seeds=[42,1,123],
    selection='same D-specific gates for D-ranked and I-ranked; passing maximize D_fraction; fallback maximize D_fraction-I_fraction; ties fewer edges then canonical keys',
    null_rng='torch CPU seed10000+seed reset per task/rank family, canonical strata,19 sequential draws without replacement within strata; selected eligible; duplicate draws retained',
    null_support='at least two possible matched full sets; no redraw',
    attribution_donors='D/H and I/user_neutral own authenticated neutral maps',exact_donors='same-condition opposite-designation; IOI frozen item-swap map',
    edge_inference='exploratory resolution1/20; outside direction Holm; no recursive circuit or unique deceptive-intent claim')


def edge_key(edge):
    return tuple(edge['sender']),tuple(edge['receiver']),edge['position']


def rank_edges(records,grid):
    require(len(records)==len(grid) and {edge_key(r['edge']) for r in records}=={edge_key(e) for e in grid},'ranking coverage differs')
    require(len({edge_key(r['edge']) for r in records})==len(records),'duplicate ranking')
    frozen={edge_key(e):e for e in grid}
    require(all(r['edge']==frozen[edge_key(r['edge'])] for r in records),'ranking semantic metadata differs from frozen graph')
    require(all(math.isfinite(r['score']) for r in records),'nonfinite ranking')
    return [r['edge'] for r in sorted(records,key=lambda r:(-r['score'],edge_key(r['edge'])))]


def choose_budget(candidates):
    require([c['budget'] for c in candidates]==list(BUDGETS),'all exact validation budgets required')
    eligible=[c for c in candidates if c.get('complete') and c.get('interpretable') and all(type(c.get(k)) in (int,float) and math.isfinite(c[k]) for k in ('D_fraction','I_fraction'))]
    if not eligible:return dict(status='blocked',reason='no complete interpretable validation candidate',candidates=candidates)
    passing=[c for c in eligible if c['point_pass']]
    pool=passing or eligible
    winner=min(pool,key=lambda c:(-c['D_fraction'] if passing else -(c['D_fraction']-c['I_fraction']),c['budget'],tuple(edge_key(e) for e in c['edges'])))
    return dict(winner,status='selected' if passing else 'validation_failure',candidates=candidates)


def _stratum(edge):
    sender,receiver=tuple(edge['sender']),tuple(edge['receiver'])
    return receiver[0],sender[1],receiver[1] if receiver[0]!='readout' else -1,edge['position_spec']['semantic_bin']


def matched_nulls(grid,selected,*,seed):
    require(seed in SEEDS and selected,'invalid null seed/set')
    require({edge_key(e) for e in selected}<={edge_key(e) for e in grid},'selected outside graph')
    require(len({edge_key(e) for e in grid})==len(grid) and len({edge_key(e) for e in selected})==len(selected),'duplicate graph/selection')
    strata={s:sorted([e for e in grid if _stratum(e)==s],key=edge_key) for s in sorted({_stratum(e) for e in selected})}
    counts={s:sum(_stratum(e)==s for e in selected) for s in strata}
    support=math.prod(math.comb(len(strata[s]),counts[s]) for s in strata)
    rng=torch.Generator(device='cpu').manual_seed(10000+seed)
    sets=[]
    for _ in range(19):
        draw=[]
        for s,values in strata.items():
            draw.extend(values[i] for i in torch.randperm(len(values),generator=rng)[:counts[s]].tolist())
        sets.append(sorted(draw,key=edge_key))
    return dict(sets=sets,possible_sets=support,informative=support>=2,duplicate_draws=19-len({digest(x) for x in sets}),seed=10000+seed,
        rng_state_hex=bytes(rng.get_state().tolist()).hex(),strata=[dict(key=list(s),available=len(strata[s]),selected=counts[s]) for s in strata])


def _observation(out,batch):
    logits=out['fp32_logits'].detach();native=out['logits'].detach().float();op=batch['opposite_token'];h=batch['honest_token'];expected=batch['expected_token']
    margin=float((logits[0,op[0]]-logits[0,h[0]]).cpu());native_margin=float((native[0,op[0]]-native[0,h[0]]).cpu())
    sign=1. if bool(expected[0]==op[0]) else -1.
    return dict(margin=margin,raw_margin=sign*margin,native_margin=native_margin,native_raw_margin=sign*native_margin,
        binary_correct=sign*margin>0,native_binary_correct=sign*native_margin>0,
        correct=bool(logits.argmax(-1)[0]==expected[0]),native_correct=bool(native.argmax(-1)[0]==expected[0]),
        native_argmax=int(native.argmax(-1)[0]),fp32_argmax=int(logits.argmax(-1)[0]))


def score_mechanism(model,design,task,split,selected,*,guard,instance_ids=None,conditions=None,streams=None):
    from component_analysis.a3_native import native_forward
    require(selected,'empty patches cannot establish preservation')
    require(split in ('validation','test'),'exact scoring source must be validation/test')
    purpose='validation' if split=='validation' else 'assessment'
    rows=[]
    ids=_membership(design,task,split)
    if instance_ids is not None:
        require(instance_ids and len(set(instance_ids))==len(instance_ids) and set(instance_ids)<=set(ids),'unknown exact-scoring source membership')
        ids=instance_ids
    active_conditions=CONDITIONS if conditions is None else conditions
    active_streams=STREAMS if streams is None else streams
    require(set(active_conditions)<=set(CONDITIONS) and set(active_streams)<=set(STREAMS),'unknown exact-scoring condition/stream')
    for rid in ids:
        for c in active_conditions:
            for s in active_streams:
                guard(); item=_move(source_pair(design,task,split,rid,c,s,purpose=purpose),model)
                batch=item['batch'];donor=item['neutral']
                _,missing=supported_edges(item,selected)
                blocked=[e['position'] for e in missing]
                base=dict(task=task,split=split,condition=c,stream=s,instance_id=rid,pressure_id=a3_design._pressure(_row(design,task,split,rid,'D')),estimand=ESTIMAND)
                if blocked:
                    rows.append(dict(base,supported=False,blocked_bins=blocked,donor_provenance=item['maps'],reason=item['maps']['rows'][0].get('unsupported_reason') or 'unsupported own semantic position/map'));continue
                intact=native_forward(model,batch,capture_sites=[])
                a=_observation(intact,batch);intact_vector=intact['fp32_logits'].detach();del intact
                patched=core.exact_edge_patch(model,batch,donor,edges=selected,maps=item['maps'])
                b=_observation(patched,batch);clamp_evidence=verify_effective_clamps(model,patched);del patched
                # Nonempty fixed-cache identity replay measures actual numerical epsilon.
                identity=copy.deepcopy(item['maps'])
                for m in identity['rows']:
                    m.update(donor_id=rid,donor_condition=c,donor_stream=s,donor_positions=m['recipient_positions'])
                replay=core.exact_edge_patch(model,batch,batch,edges=selected,maps=identity)
                r=_observation(replay,batch);replay_valid=bool(torch.allclose(replay['fp32_logits'],intact_vector,atol=1e-5,rtol=1e-5) and r['fp32_argmax']==a['fp32_argmax']);del replay,intact_vector
                rows.append(dict(base,supported=True,intact_margin=a['margin'],patched_margin=b['margin'],intact_correct=a['correct'],patched_correct=b['correct'],
                    intact_raw_margin=a['raw_margin'],patched_raw_margin=b['raw_margin'],intact_native_margin=a['native_margin'],patched_native_margin=b['native_margin'],intact_binary_correct=a['binary_correct'],patched_binary_correct=b['binary_correct'],intact_native_correct=a['native_correct'],patched_native_correct=b['native_correct'],self_replay_margin_error=abs(r['margin']-a['margin']),gate_valid=bool(item['maps']['rows'][0].get('gate_valid',True)),degenerate=bool(item['maps']['rows'][0].get('degenerate',False)),replay_valid=replay_valid,effective_clamps=clamp_evidence,native_argmax=a['native_argmax'],fp32_argmax=a['fp32_argmax'],donor_provenance=item['maps']))
    return rows


def summarize_rows(rows,*,expected_ids,utility_rows=(),n_boot=2000,bootstrap_plan=None,task=None):
    from component_analysis import ladder_metrics
    require(len(expected_ids)==len(set(expected_ids)),'duplicate expected assessment IDs')
    expected={(c,rid,s) for c in CONDITIONS for rid in expected_ids for s in STREAMS}
    actual=[(r['condition'],r['instance_id'],r['stream']) for r in rows]
    require(len(actual)==len(set(actual)) and set(actual)==expected,'exact complete paired coverage required')
    blocked=sorted({r['condition'] for r in rows if not r.get('supported')})
    utilities={name:[r for r in utility_rows if r.get('condition')==name] for name in ('IOI','MMLU_zero','MMLU_h_mean')}
    required={'IOI':100,'MMLU_zero':32,'MMLU_h_mean':32}
    for name,count in required.items():
        if len(utilities[name])!=count or len({r.get('instance_id') for r in utilities[name]})!=count or any(not r.get('supported') or r.get('stream')!='clean' for r in utilities[name]):blocked.append(name)
    if {r.get('instance_id') for r in utilities['MMLU_zero']}!={r.get('instance_id') for r in utilities['MMLU_h_mean']}:blocked.append('MMLU_floor_membership')
    result=dict(complete=not blocked,blocked_cells=blocked,point_pass=False,interpretable=False,D_fraction=None,I_fraction=None,
        estimand=ESTIMAND,required_readiness='exact full IDs/streams,IOI100,MMLU32 zero/H-mean, replay and baseline floors')
    if any(not r.get('supported') for r in rows):return result
    paired=ladder_metrics._paired(rows)
    epsilon=max(1e-6,10*max(r['self_replay_margin_error'] for r in rows))
    effects=ladder_metrics._estimate(paired,expected_ids,epsilon)
    collateral={c:ladder_metrics._accuracy([r for r in rows if r['condition']==c]) for c in ('H','F')}
    collateral['IOI']=ladder_metrics._accuracy([r for r in utilities['IOI'] if r.get('supported') and 'intact_correct' in r])
    mmlu={name:(sum(float(r['intact_correct'])-float(r['patched_correct']) for r in values) if len(values)==32 and all(r.get('supported') for r in values) else None) for name,values in utilities.items() if name.startswith('MMLU')}
    interpretable=all(v['interpretable'] for v in effects.values())
    point=interpretable and effects['D']['fraction_removed']>=.5 and effects['I']['fraction_removed']<.25 and all(v['accuracy_shift'] is not None and abs(v['accuracy_shift'])<.05-1e-12 for v in collateral.values())
    control_ready=all(r.get('replay_valid') is True and r.get('gate_valid') is True and r.get('degenerate') is not True and r.get('effective_clamps') and all(x.get('equal') is True for x in r['effective_clamps']) for r in list(rows)+list(utility_rows))
    if not control_ready:blocked.append('native_replay_or_effective_clamps')
    result['complete']=not blocked
    result['native_control_ready']=bool(control_ready)
    result['edge_assay_ready']=bool(not blocked and control_ready)
    result.update(interpretable=interpretable,D_fraction=effects['D']['fraction_removed'],I_fraction=effects['I']['fraction_removed'],effects=effects,collateral=collateral,mmlu_additional_errors=mmlu,
        raw_transfer={c:dict(intact_margin=float(np.mean([r['intact_margin'] for r in rows if r['condition']==c])),patched_margin=float(np.mean([r['patched_margin'] for r in rows if r['condition']==c])),**ladder_metrics._accuracy([r for r in rows if r['condition']==c])) for c in CONDITIONS},primary_point_pass=bool(point),exact_clamp_specificity=bool(point and not blocked and all(x<=1 for x in mmlu.values())),point_pass=bool(point and not blocked and all(x<=1 for x in mmlu.values())),epsilon=epsilon)
    # Paired canonical-pressure cluster bootstrap; multiplicities expand all IDs.
    clusters={}
    for rid in expected_ids:
        words={r['pressure_id'] for r in rows if r['instance_id']==rid}
        require(len(words)==1,'canonical pressure cluster differs across paired arms')
        clusters.setdefault(words.pop(),[]).append(rid)
    rng=np.random.default_rng(9001);intervals={c:[] for c in ('D','I')}
    accuracy_intervals={c:[] for c in ('H','F','IOI')};floor_intervals={c:[] for c in ('MMLU_zero','MMLU_h_mean')}
    utility_index={c:{r.get('instance_id'):r for r in values if r.get('supported')} for c,values in utilities.items()}
    draws=bootstrap_plan if bootstrap_plan is not None else [None]*n_boot
    for planned in draws:
        ids=planned[task] if planned is not None else [rid for name in rng.choice(sorted(clusters),len(clusters),replace=True) for rid in clusters[name]]
        values=ladder_metrics._estimate(paired,ids,epsilon)
        for c in intervals:
            if values[c]['fraction_removed'] is not None:intervals[c].append(values[c]['fraction_removed'])
        for c in ('H','F'):
            accuracy_intervals[c].append(float(np.mean([float(r['patched_correct'])-float(r['intact_correct']) for rid in ids for r in paired[(c,rid)]])))
        utility_draws={}
        for source,condition in (('IOI','IOI'),('MMLU','MMLU_zero')):
            uids=sorted(utility_index[condition])
            utility_draws[source]=planned[source] if planned is not None else rng.choice(uids,len(uids),replace=True).tolist() if uids else []
        for c in ('IOI','MMLU_zero','MMLU_h_mean'):
            sampled=utility_draws['IOI' if c=='IOI' else 'MMLU']
            if sampled and all(rid in utility_index[c] for rid in sampled):
                changes=[float(utility_index[c][rid]['patched_correct'])-float(utility_index[c][rid]['intact_correct']) for rid in sampled]
                if c=='IOI':accuracy_intervals[c].append(float(np.mean(changes)))
                else:floor_intervals[c].append(-sum(changes))
    count=len(draws)
    result['fraction_intervals']={c:np.percentile(v,[2.5,97.5]).tolist() if len(v)==count else None for c,v in intervals.items()}
    result['accuracy_shift_intervals']={c:np.percentile(v,[2.5,97.5]).tolist() if len(v)==count else None for c,v in accuracy_intervals.items()}
    result['mmlu_additional_error_intervals']={c:np.percentile(v,[2.5,97.5]).tolist() if len(v)==count else None for c,v in floor_intervals.items()}
    def interval_ok(values,lower=None,upper=None):
        return values is not None and (lower is None or values[0]>=lower) and (upper is None or values[1]<upper)
    confident=interval_ok(result['fraction_intervals']['D'],lower=.5) and interval_ok(result['fraction_intervals']['I'],upper=.25)
    confident=confident and all(v is not None and v[0]>-.05 and v[1]<.05 for v in result['accuracy_shift_intervals'].values())
    confident=confident and all(v is not None and v[1]<=1 for v in result['mmlu_additional_error_intervals'].values())
    result['confidence_gate_support']=bool(confident)
    result['specificity_status']='strong_point_and_interval_support' if result['point_pass'] and confident else 'uncertain_point_pass' if result['point_pass'] else 'fails' if result['interpretable'] and result['complete'] else 'blocked_or_uninterpretable'
    result['n_pressure_clusters']=len(clusters)
    result['warnings']=[] if len(clusters)>=20 else ['few canonical pressure clusters; limited precision']
    result['uncertainty']='paired canonical D-pressure clusters with unequal-cluster multiplicities; common utility prompt draws; seeds/sets are not resampled as independent datasets'
    return result


def select_from_fit(fit,graph,*,evaluator,injected=False,_native=False):
    """Freeze both ranked families and null memberships before assessment access.

    Custom evaluators are test-only and leave a permanent injected identity.
    Production uses select_native, which measures exact joint interventions.
    """
    require(injected or _native,'caller evaluator forbidden for production')
    require(fit.get('kind')=='a3_edge_fit' and fit.get('split')=='train','fit ranking must originate on train')
    require(fit['graph_sha256']==digest(graph),'changed frozen fit graph')
    require([f['seed'] for f in fit['fits']]==list(SEEDS),'exact three fit seeds required')
    families=[]
    for f in fit['fits']:
        require(set(f['rankings'])=={'D','I'},'both ranking conditions required')
        for c in ('D','I'):
            if any(r.get('supported') is False for r in f['rankings'][c]):
                families.append(dict(seed=f['seed'],ranking_condition=c,status='blocked',reason='incomplete attribution semantic support',candidates=[],ranking_diagnostics=f['rankings'][c]))
                continue
            ranking=rank_edges(f['rankings'][c],graph['edges']);candidates=[]
            for budget in BUDGETS:
                if len(ranking)<budget:
                    candidates.append(dict(budget=budget,edges=[],complete=False,interpretable=False,point_pass=False,reason='graph smaller than frozen budget'))
                    continue
                selected=ranking[:budget]
                result=evaluator(selected)
                require(not {'edges','budget'}&set(result),'evaluator cannot change membership')
                candidates.append(dict(result,budget=budget,edges=selected))
            winner=choose_budget(candidates)
            family=dict(seed=f['seed'],ranking_condition=c,**winner)
            if winner['status']!='blocked':family['nulls']=matched_nulls(graph['edges'],winner['edges'],seed=f['seed'])
            families.append(family)
    body=dict(kind='a3_edge_selection',split='validation',fit_sha256=digest(fit),graph_sha256=digest(graph),rules=copy.deepcopy(RULES),families=families,injected=bool(injected),memberships_frozen=True)
    body['selection_sha256']=digest(body)
    return body


def validate_selection(selected,graph):
    require(selected.get('kind')=='a3_edge_selection' and selected.get('split')=='validation' and selected.get('memberships_frozen') is True,'completed frozen validation selection required')
    require(selected['graph_sha256']==digest(graph) and selected['rules']==RULES,'changed graph or scientific rules')
    require(selected['selection_sha256']==digest({k:v for k,v in selected.items() if k!='selection_sha256'}),'changed selection hash')
    families=selected['families']
    require([(f['seed'],f['ranking_condition']) for f in families]==[(s,c) for s in SEEDS for c in ('D','I')],'exact three seeds/two families required')
    for f in families:
        require(f['status'] in ('selected','validation_failure','blocked'),'invalid selection status')
        if f['status']=='blocked':
            require('nulls' not in f and 'edges' not in f,'blocked selection cannot invent null/winner')
            continue
        require(f['budget'] in BUDGETS and len(f['edges'])==f['budget'],'changed selected budget')
        require(f['nulls']==matched_nulls(graph['edges'],f['edges'],seed=f['seed']),'changed nineteen null memberships/RNG')
    return selected


def _utility_batch(row,stream,*,physical_width=None):
    raw=copy.deepcopy(row);s=raw['streams'][stream]
    for name in ('opposite_token','honest_token','expected_token'):
        if name not in s:s[name]=raw[name]
    s['semantic']=dict(prompt_utf8_hex=s['prompt'].encode().hex(),sites={b:([s['readout']] if b=='assistant_readout' else []) for b in BINS})
    return _batch(raw,stream,physical_width=physical_width)


def h_mean_bank(model,design,task,selected,*,guard,bank_sources=None,observer=None):
    """Ancestral A1 original-H train+validation, both streams, equal-token fp32.

    Head contributions are actual projected additive residual outputs. This bank
    is recollected in the native profile; archived coordinate means are not mixed.
    """
    from component_analysis.a3_native import native_forward
    if bank_sources is None:
        require(design.get('injected') is True,'authenticated ancestral H bank sources required')
        bank_sources=ancestral_bank_sources(design)[task]
    rows=bank_sources['rows'];ids=bank_sources['source_ids']
    require(rows and [r['instance_id'] for r in rows]==ids and len(ids)==len(set(ids)),'changed/duplicate H bank membership')
    require(bank_sources['source_sha256']==digest(rows),'changed H bank source bytes')
    require(all(r['condition']=='H' and r['split'] in ('train','validation') for r in rows),'H bank must exclude all assessment rows')
    sources=sorted({tuple(e['sender']) for e in selected});totals={};tokens=0
    width=bank_sources.get('padded_width',1+max(len(s['tokens']) for r in rows for s in r['streams'].values()))
    for row in rows:
        require(set(row['streams'])==set(STREAMS),'H bank needs both streams')
        for stream in STREAMS:
            guard();b=_move({'batch':_utility_batch(row,stream,physical_width=width)},model)['batch']
            call=lambda:native_forward(model,b,capture_sites=sources)
            out=observer('H_bank',b,sources,call) if observer else call()
            mask=b['attention_mask'].bool();tokens+=int(mask.sum())
            for site in sources:
                value=out['additive'][site][mask].detach().float().sum(0).cpu()
                totals[site]=totals.get(site,torch.zeros_like(value))+value
            del out
    require(tokens>0,'empty H token bank')
    values={s:v/tokens for s,v in totals.items()}
    return dict(values=values,provenance=dict(task=task,source_ids=ids,source_sha256=bank_sources['source_sha256'],
        splits=sorted({r['split'] for r in rows}),streams=list(STREAMS),unpadded_tokens=tokens,
        representation='native projected additive head residual and whole-MLP additive residual',
        accumulation_dtype='torch.float32',native_dtype=str(next(model.parameters()).dtype),
        padded_width=width,weighting='equal unpadded token; both streams'))


def _utility_floor(model,batch,selected,mode,bank):
    from component_analysis.a3_native import native_forward,ResidualPatch
    receivers=sorted({tuple(e['receiver']) for e in selected});sources=sorted({tuple(e['sender']) for e in selected})
    out=native_forward(model,batch,capture_sites=receivers+sources)
    patches={};position=int(batch['readout'][0])
    for receiver in receivers:
        value=out['incoming'][receiver].clone()
        for edge in sorted(selected,key=edge_key):
            if tuple(edge['receiver'])!=receiver:continue
            site=tuple(edge['sender']);intact=out['additive'][site][0,position]
            donor=torch.zeros_like(intact) if mode=='zero' else bank['values'][site].to(intact)
            value[0,position]+=donor-intact
        mask=torch.zeros(batch['input_ids'].shape,dtype=torch.bool,device=value.device);mask[0,position]=True
        patches[receiver]=ResidualPatch(value,mask)
    del out
    result=native_forward(model,batch,capture_sites=receivers,patches=patches)
    return dict(result,clamps={r:p.value for r,p in patches.items()},patch_positions={r:p.positions for r,p in patches.items()},receiver_outputs=result['outputs'])


def score_utilities(model,design,task,split,selected,*,guard,bank=None,bank_sources=None,only_ids=None,timing_only=False):
    from component_analysis.a3_native import native_forward
    require(split in ('validation','test'),'utility source must be validation/test')
    require(selected,'empty patch cannot establish utility preservation')
    if any(e['position_spec']['semantic_bin']!='assistant_readout' for e in selected):
        output=[]
        for condition,source in (('IOI','ioi'),('MMLU_zero','mmlu'),('MMLU_h_mean','mmlu')):
            records=design.get(source+'_validation',[]) if split=='validation' else design['utility'].get(source,[])
            if not records:records=[{'instance_id':None}]
            output.extend(dict(condition=condition,instance_id=r['instance_id'],stream='clean',split=r.get('split'),source_split=r.get('split'),analysis_split='validation' if split=='validation' else 'assessment',supported=False,reason='utility adapter supports own readout only; selected semantic bin inapplicable') for r in records)
        return output
    rows=[]
    ioi=design.get('ioi_validation',[]) if split=='validation' else design['utility'].get('ioi',[])
    mmlu=design.get('mmlu_validation',[]) if split=='validation' else design['utility'].get('mmlu',[])
    maps=design.get('ioi_validation_maps',[]) if split=='validation' else design['utility'].get('ioi_maps',[])
    if only_ids is not None:
        require(set(only_ids)<={'ioi','mmlu'},'unknown utility timing source')
        ioi=[r for r in ioi if r['instance_id'] in only_ids.get('ioi',[])]
        mmlu=[r for r in mmlu if r['instance_id'] in only_ids.get('mmlu',[])]
        require({r['instance_id'] for r in ioi}==set(only_ids.get('ioi',[])) and {r['instance_id'] for r in mmlu}==set(only_ids.get('mmlu',[])),'unknown utility source membership')
    if mmlu and bank is None:bank=h_mean_bank(model,design,task,selected,guard=guard,bank_sources=bank_sources)
    for source,records in (('IOI',ioi),('MMLU',mmlu)):
        for raw in records:
            guard();batch=_move({'batch':_utility_batch(raw,'clean',physical_width=source_width(design,source.lower()))},model)['batch']
            intact=native_forward(model,batch,capture_sites=[]);a=_observation(intact,batch);intact_vector=intact['fp32_logits'].detach();del intact
            modes=('item_swap',) if source=='IOI' else ('zero','h_mean')
            for mode in modes:
                condition='IOI' if source=='IOI' else 'MMLU_'+mode
                base=dict(condition=condition,source_condition=raw['condition'],instance_id=raw['instance_id'],source_id=raw.get('source_id'),source_hash=raw.get('source_hash'),stream='clean',split=raw.get('split'),source_split=raw.get('split'),analysis_split='validation' if split=='validation' else 'assessment')
                if source=='IOI':
                    records_map=[m for m in maps if m['recipient_id']==raw['instance_id'] and m['operation']=='item_swap']
                    require(len(records_map)==1,'missing/duplicate authenticated IOI map')
                    if not records_map[0]['supported']:
                        rows.append(dict(base,supported=False,reason='unsupported frozen IOI donor'));continue
                    donor=_move({'batch':_utility_batch(raw,'corrupt',physical_width=source_width(design,source.lower()))},model)['batch']
                    patched=core.exact_edge_patch(model,batch,donor,edges=selected,maps={'rows':records_map})
                else:patched=_utility_floor(model,batch,selected,mode,bank)
                b=_observation(patched,batch);clamps=verify_effective_clamps(model,patched);del patched
                replay_map=dict(supported=True,recipient_id=raw['instance_id'],donor_id=raw['instance_id'],recipient_condition=batch['condition'],donor_condition=batch['condition'],recipient_stream='clean',donor_stream='clean',recipient_positions=[int(batch['readout'][0])],donor_positions=[int(batch['readout'][0])])
                replay=core.exact_edge_patch(model,batch,batch,edges=selected,maps={'rows':[replay_map]})
                replay_valid=bool(torch.allclose(replay['fp32_logits'],intact_vector,atol=1e-5,rtol=1e-5) and torch.equal(replay['fp32_logits'].argmax(-1),intact_vector.argmax(-1)))
                del replay
                rows.append(dict(base,supported=True,timing_only=bool(timing_only),replay_valid=replay_valid,effective_clamps=clamps,gate_valid=True,degenerate=False,intact_correct=a['correct'],patched_correct=b['correct'],intact_margin=a['margin'],patched_margin=b['margin']))
    return rows


def select_native(model,design,task,graph,fit,*,guard):
    def evaluate(selected):
        rows=score_mechanism(model,design,task,'validation',selected,guard=guard)
        utility=score_utilities(model,design,task,'validation',selected,guard=guard)
        return summarize_rows(rows,expected_ids=_membership(design,task,'validation'),utility_rows=utility)
    return select_from_fit(fit,graph,evaluator=evaluate,injected=design.get('injected',False),_native=True)


def pilot_stability(model,design,task,graph,*,guard,cache_root=None,identity=None,resume=False):
    if cache_root is not None:return cached_pilot_stability(model,design,task,graph,guard=guard,root=cache_root,identity=identity,resume=resume)
    ids=_membership(design,task,'validation')
    require(len(ids)>=8,'eight fixed validation identities required')
    reports={}
    for condition in ('D','I'):
        results=[]
        for nodes in (8,16):
            def batches():
                for rid in ids[:8]:
                    for stream in STREAMS:
                        guard();yield _move(source_pair(design,task,'validation',rid,condition,stream,purpose='attribution'),model)
            results.append(core.attribute_edges(model,batches(),edges=graph['edges'],steps=nodes))
        reports[condition]=dict(core.integration_stability(*results),eight=results[0],sixteen=results[1])
    return dict(kind='a3_edge_stability',instance_ids=ids[:8],split='validation',conditions=reports,stable=all(r['stable'] for r in reports.values()),
        continuation='eight requires agreement;16 requires separate measured root decision; retain single disagreement and block full claim; no automatic retry')


def code_hashes():
    paths=set(artifacts.code_hashes())|{'component_analysis/a3_edge_pipeline.py','component_analysis/a3_edge_workload.py','component_analysis/a3_native.py','component_analysis/a3_edges.py','scripts/jobs/specificity_a3_edges.sh','tests/test_a3_edges.py'}
    return {name:common.file_hash(ladder.REPO/name) for name in sorted(paths)}


def ruling_reference():
    path=ladder.REPO/'docs/research/specificity-ladder/a3-edge-operational-ruling.json'
    content=json.loads(path.read_text())
    require(content.get('kind')=='a3_edge_operational_ruling_v1' and content['budget_selection']['among_passing']=='maximize D_fraction' and content['attribution']['discard_zero_or_negative_scores'] is False,'frozen root edge ruling required')
    return dict(path=str(path.resolve()),sha256=common.file_hash(path),content=content)


def prepare(design,geometry,*,commit,registry_paths,output=None,design_path=None):
    require(re.fullmatch('[0-9a-f]{40}',commit) is not None,'full source commit required')
    require(design['direction_protocol']['commit']==commit,'source protocol execution commit differs')
    live=artifacts.validate_live(design,design['direction_protocol'],registry_paths=list(registry_paths))
    require(design_path is not None or design.get('injected') is True,'original canonical A3 file-byte reference required')
    design_reference=None
    if design_path is not None:
        path=Path(design_path).resolve()
        require(_read_design(path)==design,'A3 parent file differs from admitted payload')
        design_reference=dict(path=str(path),sha256=common.file_hash(path),nbytes=path.stat().st_size)
    graphs={task:prepare_graph(design,task,geometry) for task in design['tasks']}
    result=dict(kind='a3_edge_prepared',design_reference=design_reference,design_sha256=digest(design),commit=commit,graphs=graphs,source_admission=admit_parent_sources(design,registry_paths=registry_paths),rules=copy.deepcopy(RULES),ruling=ruling_reference(),code_hashes=code_hashes(),injected=bool(design.get('injected')),source_evidence=live,bank_sources=ancestral_bank_sources(design))
    result['prepared_sha256']=digest(result)
    if output is not None:authority.publish_object(output,result)
    return result


def validate_prepared(prepared,design,*,registry_paths):
    live=artifacts.validate_live(design,design['direction_protocol'],registry_paths=list(registry_paths))
    require(prepared['kind']=='a3_edge_prepared' and prepared['design_sha256']==digest(design),'changed prepared source')
    reference=prepared.get('design_reference')
    require(reference is not None or design.get('injected') is True,'missing original A3 file-byte identity')
    if reference is not None:
        path=Path(reference['path'])
        require(path.is_file() and common.file_hash(path)==reference['sha256'] and path.stat().st_size==reference['nbytes'] and _read_design(path)==design,'changed original A3 parent file bytes')
    require(prepared['ruling']==ruling_reference() and prepared['rules']==RULES,'changed frozen root ruling')
    require(prepared['code_hashes']==code_hashes(),'changed edge runtime closure')
    require(prepared['prepared_sha256']==digest({k:v for k,v in prepared.items() if k!='prepared_sha256'}),'changed prepared metadata')
    require(prepared['injected']==bool(design.get('injected')),'changed injected identity')
    require(prepared.get('bank_sources')==ancestral_bank_sources(design),'changed ancestral A1 H bank sources')
    require(prepared.get('source_admission',{}).get('source_sha256')==source_rows_digest(design),'changed admitted source/token/semantic/map memberships')
    if not (design.get('injected') and not design.get('parent_evidence')):
        from component_analysis.a3_pipeline import load_a1_parents
        parent,_,_=load_a1_parents(design['parent_evidence']['prepared_path'],design['parent_evidence']['selected_path'])
        validate_original_streams(design,parent)
    extended=copy.deepcopy(design)
    for task,bank in prepared['bank_sources'].items():extended['access_rows'][task]+=bank['rows']
    a3_design.validate_access(extended,list(registry_paths))
    for task,graph in prepared['graphs'].items():
        geom={k:graph['geometry'][k] for k in ('num_hidden_layers','num_attention_heads','num_key_value_heads')}
        require(graph==prepare_graph(design,task,geom),'changed frozen graph/semantic coverage')
    return live


def native_pilot_checks(model,batch,receivers):
    """Actual native autograd readout plus local residual VJP finite differences.

    Fixed fp32 diagnostic tolerance mirrors the reviewed tiny adapter tests.
    Low-precision native runs which cannot meet it remain blocked, never waived.
    """
    from component_analysis.a3_native import native_forward,ResidualPatch
    from component_analysis.hooks import readout_logits
    readout=('readout',0,0)
    out=native_forward(model,batch,capture_sites=[readout])
    residual=out['incoming'][readout][torch.arange(len(batch['instance_ids']),device=batch['input_ids'].device),batch['readout']]
    expected=readout_logits(model,residual)
    error=float((expected-out['fp32_logits']).abs().max().cpu())
    require(torch.allclose(expected,out['fp32_logits'],atol=1e-5,rtol=1e-5),'native/inference fp32 readout mismatch')
    argmax=bool(torch.equal(expected.argmax(-1),out['fp32_logits'].argmax(-1)))
    require(argmax,'native/inference argmax mismatch')
    reference=out['fp32_logits'].detach().clone();reference_margin=float(core._margin(out,batch).sum().detach().cpu())
    del out,residual,expected
    vjps=[];value_comparisons=[]
    for site in receivers:
        site=tuple(site)
        out=native_forward(model,batch,capture_sites=[site],grad=True)
        margin=core._margin(out,batch).sum();leaf=out['leaves'][site]
        ratio=float(((out['fp32_logits'].detach()-reference).abs()/(1e-5+1e-5*reference.abs())).max().cpu())
        observed_argmax=int(out['fp32_logits'].argmax(-1)[0]);expected_argmax=int(reference.argmax(-1)[0])
        require(ratio<=1 and observed_argmax==expected_argmax,'gradient-enabled native readout value/argmax differs from intact inference')
        value_comparisons.append(dict(receiver=list(site),max_scaled_error=ratio,expected_margin=reference_margin,observed_margin=float(margin.detach().cpu()),expected_argmax=expected_argmax,observed_argmax=observed_argmax))
        gradient,=torch.autograd.grad(margin,leaf)
        # Deterministic nonzero residual direction, no model or selection RNG.
        direction=torch.arange(leaf.numel(),device=leaf.device,dtype=torch.float32).reshape_as(leaf).sin().to(leaf.dtype)
        position=int(batch['readout'][0]);mask=torch.zeros(batch['input_ids'].shape,dtype=torch.bool,device=leaf.device);mask[0,position]=True
        direction*=mask[...,None]
        analytic=float((gradient*direction).sum().detach().cpu());values=[]
        for sign in (-1,1):
            probe=native_forward(model,batch,capture_sites=[],patches={site:ResidualPatch(leaf.detach()+sign*.001*direction,mask)})
            values.append(float(core._margin(probe,batch).sum().detach().cpu()));del probe
        measured=(values[1]-values[0])/.002
        passed=math.isclose(measured,analytic,abs_tol=5e-5,rel_tol=.02)
        vjps.append(dict(receiver=list(site),analytic=analytic,finite_difference=measured,passed=passed))
        del out,leaf,gradient,margin,direction
    require(all(v['passed'] for v in vjps),'local native receiver VJP diagnostic failed')
    return dict(argmax_equal=argmax,max_readout_error=error,vjps=vjps,gradient_value_comparisons=value_comparisons,parameters_frozen=all(not x.requires_grad and x.grad is None for x in model.parameters()))


def supported_edges(item,edges):
    batch=item['batch'];mapping=item['maps']['rows'][0]
    if mapping.get('supported') is not True:return [],list(edges)
    valid=set(mapping['recipient_positions']);supported=[];missing=[]
    overlaps={name for a in BINS for b in BINS if a<b and set(batch['positions'][a][0])&set(batch['positions'][b][0]) for name in (a,b)}
    for edge in edges:
        positions=batch['positions'][edge['position']][0]
        (supported if positions and edge['position'] not in overlaps and set(positions)<=valid else missing).append(edge)
    return supported,missing


def final_guard(identity):
    require(identity.get('injected') is False and identity.get('pilot') is False and identity.get('complete') is True,'pilot/partial/injected outputs cannot finalize')
    require(re.fullmatch('[0-9a-f]{40}',identity.get('source_commit','')) is not None,'full production commit required')


def _read_design(path):
    design=ladder.read_artifact(path)
    require(design.get('kind')=='specificity_ladder_a3_design','authenticated A3 design required')
    return design


def execution_guard(design,prepared,args,inventory):
    from component_analysis import a3_edge_workload as workload
    context=None
    def guard():
        nonlocal context
        live=validate_prepared(prepared,design,registry_paths=args.registry)
        require(args.ledger_snapshot and args.reservation,'fresh root reservation/ledger required before model access')
        ledger=authority.normalize_ledger(args.ledger_snapshot,identity=inventory['identity'],injected=design.get('injected',False))
        if context is None:
            context=authority.make_authority_context(args.reservation,ledger=ledger,inventory=inventory,work_dir=args.work_dir,injected=design.get('injected',False),subphase='edges',inventory_validator=workload.validate_inventory,subphase_limits={'M1':.75,'M4':9},requested_scope=inventory.get('stage'),inventory_path=getattr(args,'inventory',None))
        live['reservation']=authority.validate_reservation(args.reservation,ledger=ledger,inventory=inventory,work_dir=args.work_dir,
            injected=design.get('injected',False),subphase='edges',inventory_validator=workload.validate_inventory,subphase_limits={'M1':.75,'M4':9},authority_context=context,requested_scope=inventory.get('stage'),inventory_path=getattr(args,'inventory',None))
        live['storage_capacities']=ledger.get('storage_capacities')
        live['authority_retained_bytes']=getattr(context,'retained_bytes',0)
        return live
    return guard


def _native_loader(design,prepared,args):
    import os
    from types import SimpleNamespace
    from transformers import AutoModelForCausalLM
    require(os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available(),'native edge execution requires Slurm CUDA allocation')
    require('H200' in torch.cuda.get_device_name(),'edge native gradients initially require H200')
    a1=design['a1_identity'];snapshot=common.resolve_model_snapshot(SimpleNamespace(model=a1['model'],model_revision=a1['model_revision']))
    profile=design['direction_protocol']['numeric_profile']
    require(profile['dtype']=='torch.bfloat16' or profile['dtype']=='bfloat16','frozen native dtype required')
    model=AutoModelForCausalLM.from_pretrained(snapshot,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation=profile['backend']).eval().requires_grad_(False).to('cuda')
    for task,graph in prepared['graphs'].items():
        require(all(getattr(model.config,k)==v for k,v in graph['geometry'].items() if k!='position_cells'),'loaded native geometry differs from frozen graph')
    return model


def _stage_identity(design,prepared):
    return dict(commit=prepared['commit'],prepared_sha256=prepared['prepared_sha256'],code_hashes=prepared['code_hashes'],ruling_sha256=prepared['ruling']['sha256'],
        a1_identity=design.get('a1_identity'),runtime_signature=runtime_signature(),numeric_profile=design['direction_protocol'].get('numeric_profile'),geometry={t:g['geometry'] for t,g in prepared['graphs'].items()},injected=bool(design.get('injected')))


def _stage_write(path,value,*,resume=False):
    if Path(path).exists():
        require(resume and authority.read_object(path)==value,'immutable stage result changed or already exists')
    else:authority.publish_object(path,value)
    return value


def _stability_admission(args,identity,design=None,prepared=None):
    require(args.pilot_evidence,'completed actual edge pilot required before nonpilot model access')
    pilot=authority.read_object(args.pilot_evidence)
    require(pilot.get('kind')=='a3_edge_pilot_complete' and pilot.get('identity')==identity and pilot.get('complete') is True,'changed/incomplete native pilot')
    require(pilot.get('independent_controls') is True,'independent loading/serial controls missing')
    if design is not None and prepared is not None:validate_pilot(pilot,design,prepared,identity)
    require(all(c.get('status')!='unsupported_source' for t in pilot['tasks'].values() for c in t['conditions'].values()),'unsupported semantic source cannot be rescued by16 nodes')
    stable=all(x['stable'] for x in pilot['tasks'].values())
    if args.steps==8:
        require(stable,'failed8/16 diagnostic blocks model work without explicit measured16 continuation')
    else:
        require(args.integration_admission,'16-node continuation requires separate measured root decision')
        accepted=authority.read_object(args.integration_admission)
        require(accepted.get('kind')=='a3_edge_integration_admission_v1' and accepted.get('identity')==identity and accepted.get('steps')==16 and accepted.get('measured') is True and accepted.get('continuation_authorized') is True,'invalid explicit measured16-node decision')
        require(accepted.get('pilot_reference')==authority.object_reference(args.pilot_evidence),'16-node decision names a different pilot')
        # The original root admission independently anchors this decision and
        # measured16 profile references before execution. No automatic fallback.
    pilot=copy.deepcopy(pilot)
    pilot['approximation_qualification']='validated8/16 agreement' if stable else 'single8/16 disagreement; validation unresolved/unreliable; authorized16 causal diagnostics only; full edge-specificity claim blocked'
    pilot['full_claim_allowed']=stable
    return pilot


def _assessment_panel(model,design,task,selected,*,guard,bank_sources=None,bank=None):
    rows=score_mechanism(model,design,task,'test',selected,guard=guard)
    utility=score_utilities(model,design,task,'test',selected,guard=guard,bank_sources=bank_sources,bank=bank)
    return dict(rows=rows,utility_rows=utility,summary=summarize_rows(rows,expected_ids=_membership(design,task,'test'),utility_rows=utility))


def _run_fit(model,design,prepared,args,guard,identity):
    # Each source row/receiver has a durable scalar cache; no full cohort graph.
    expected=[]
    for task,spec in design['tasks'].items():
        receivers=sorted({tuple(e['receiver']) for e in prepared['graphs'][task]['edges']})
        expected.extend([task,c,rid,stream,list(receiver)] for c in ('D','I') for rid in spec['fit_ids'] for stream in STREAMS for receiver in receivers)
    inventory=dict(kind='a3_edge_fit_cache',identity=identity,steps=args.steps,expected_keys=expected)
    def producer(key):
        task,c,rid,stream,receiver=key
        item=_move(source_pair(design,task,'train',rid,c,stream,purpose='attribution'),model)
        edges=[e for e in prepared['graphs'][task]['edges'] if tuple(e['receiver'])==tuple(receiver)]
        supported,missing=supported_edges(item,edges)
        records=core.attribute_edges(model,[item],edges=supported,steps=args.steps) if supported else []
        records.extend(dict(edge=e,score=None,supported=False,reason='unsupported own-source semantic/map cell') for e in missing)
        return dict(records=records)
    chunks=execute(inventory,Path(args.work_dir)/'fit-cache',producer,guard=guard,resume=args.resume)
    tasks={}
    for task in design['tasks']:
        graph=prepared['graphs'][task];fits=[]
        for seed in SEEDS:
            boot=bootstrap(design,task,seed);weights=dict(zip(boot['instance_ids'],boot['id_weights']));rankings={}
            for c in ('D','I'):
                totals={edge_key(e):0. for e in graph['edges']};missing={}
                for chunk in chunks:
                    t,condition,rid,stream,_=chunk['key']
                    if (t,condition)!=(task,c):continue
                    for r in chunk['result']['records']:
                        key=edge_key(r['edge'])
                        if r['score'] is None:missing.setdefault(key,[]).append([rid,stream])
                        else:totals[key]+=float(r['score'])*weights[rid]/2
                rankings[c]=[dict(edge=e,score=None if edge_key(e) in missing else totals[edge_key(e)],supported=edge_key(e) not in missing,unsupported_rows=missing.get(edge_key(e),[]),token_aggregation='sum') for e in graph['edges']]
            fits.append(dict(seed=seed,bootstrap=boot,rankings=rankings))
        tasks[task]=dict(kind='a3_edge_fit',split='train',fits=fits,graph_sha256=digest(graph),steps=args.steps,injected=bool(design.get('injected')))
    result=dict(kind='a3_edge_fit_complete',identity=identity,injected=bool(design.get('injected')),complete=True,tasks=tasks,cache_reference=authority.object_reference(Path(args.work_dir)/'fit-cache'/'inventory'))
    return _stage_write(Path(args.work_dir)/'fit',result,resume=args.resume)


def _run_selection(model,design,prepared,args,guard,identity):
    fit_path=Path(args.fit_evidence) if args.fit_evidence else Path(args.work_dir)/'fit'
    fitted=authority.read_object(fit_path)
    require(fitted['kind']=='a3_edge_fit_complete' and fitted['identity']==identity and fitted['complete'],'completed source-bound train fit required')
    tasks={}
    validation_diagnostics={};created=set()
    for task,graph in prepared['graphs'].items():
        bank=cached_h_bank(model,design,prepared,task,identity=identity,root=Path(args.work_dir)/'banks',guard=guard) if design.get('mmlu_validation') else None
        attrpath=Path(args.work_dir)/'validation-attribution'/task
        guard()
        if attrpath.exists():
            require(args.resume,'existing validation attribution requires resume')
            diagnostic=authority.read_object(attrpath)
            require(diagnostic['identity']==identity and diagnostic['graph_sha256']==digest(graph),'changed validation attribution identity')
        else:
            diagnostic=dict(identity=identity,graph_sha256=digest(graph),**validation_attribution(model,design,task,graph,steps=args.steps,guard=guard))
            authority.publish_object(attrpath,diagnostic)
        validation_diagnostics[task]=authority.object_reference(attrpath)
        def evaluate(selected):
            key=digest(dict(task=task,edges=selected));path=Path(args.work_dir)/'validation-cache'/key
            guard()
            if path.exists():
                require(args.resume or str(path) in created,'existing validation cache requires resume');item=authority.read_object(path)
                require(item['identity']==identity and item['edges']==selected and item['task']==task,'changed validation cache')
            else:
                rows=score_mechanism(model,design,task,'validation',selected,guard=guard)
                utility=score_utilities(model,design,task,'validation',selected,guard=guard,bank_sources=prepared['bank_sources'][task],bank=bank)
                item=dict(identity=identity,task=task,edges=selected,rows=rows,utility_rows=utility,summary=summarize_rows(rows,expected_ids=_membership(design,task,'validation'),utility_rows=utility))
                authority.publish_object(path,item);created.add(str(path))
            return item['summary']
        tasks[task]=select_from_fit(fitted['tasks'][task],graph,evaluator=evaluate,injected=bool(design.get('injected')),_native=True)
        validate_selection(tasks[task],graph)
    result=dict(kind='a3_edge_selection_complete',identity=identity,injected=bool(design.get('injected')),complete=True,tasks=tasks,fit_reference=authority.object_reference(fit_path),validation_attribution=validation_diagnostics)
    return _stage_write(Path(args.work_dir)/'selection',result,resume=args.resume)


def _run_assessment(model,design,prepared,args,guard,identity):
    selection_path=Path(args.selection) if args.selection else Path(args.work_dir)/'selection'
    selected=authority.read_object(selection_path)
    require(selected.get('kind')=='a3_edge_selection_complete' and selected['identity']==identity and selected['complete'],'completed frozen selection required')
    keys=[];memberships={}
    for task,item in selected['tasks'].items():
        validate_selection(item,prepared['graphs'][task])
        for family in item['families']:
            if family['status']=='blocked':continue
            sets=[family['edges']]+family['nulls']['sets']
            for index,edges in enumerate(sets):
                key=[task,family['seed'],family['ranking_condition'],index]
                keys.append(key);memberships[digest(key)]=edges
    if keys:
        inv=dict(kind='a3_edge_assessment_cache',identity=identity,selection_reference=authority.object_reference(selection_path),expected_keys=keys)
        def producer(key):
            return cached_assessment_panel(model,design,prepared,key[0],memberships[digest(key)],identity=identity,root=Path(args.work_dir),guard=guard)
        chunks=execute(inv,Path(args.work_dir)/'assessment-cache',producer,guard=guard,resume=args.resume)
    else:chunks=[]
    result=dict(kind='a3_edge_assessment_complete',identity=identity,injected=bool(design.get('injected')),pilot=False,complete=bool(keys) and all(f['status']!='blocked' for t in selected['tasks'].values() for f in t['families']),
        selected=selected,selection_reference=authority.object_reference(selection_path),expected_keys=keys,chunks=chunks,interpretation=ESTIMAND,execution_evidence=guard(),
        pilot_reference=authority.object_reference(args.pilot_evidence) if args.pilot_evidence else None)
    return _stage_write(Path(args.work_dir)/'assessment',result,resume=args.resume)


def _metadata_geometry(design,args):
    from huggingface_hub import hf_hub_download
    if args.geometry:
        require(design.get('injected') is True,'caller geometry forbidden for production')
        cfg=json.loads(Path(args.geometry).read_text())
    else:
        a1=design['a1_identity']
        path=hf_hub_download(a1['model'],'config.json',revision=a1['model_revision'],local_files_only=True)
        cfg=json.loads(Path(path).read_text())
        require(cfg.get('model_type')=='llama' and cfg.get('hidden_size')==4096 and cfg.get('intermediate_size')==14336,'unsupported frozen native geometry')
    return {k:cfg[k] for k in ('num_hidden_layers','num_attention_heads','num_key_value_heads')}


def _require_independent_controls(args,identity,design):
    require(args.pilot_evidence,'completed native pilot required')
    pilot=authority.read_object(args.pilot_evidence)
    refs=pilot.get('control_references')
    require(isinstance(refs,dict) and set(refs)=={'model_loading','serial_geometry','complete_toy_endpoint'},'actual pilot control objects required')
    for name,reference in refs.items():
        require(reference==authority.object_reference(reference['path']),'changed pilot control bytes')
        validate_control(authority.read_object(reference['path']),design,identity)
    for path,name in ((args.model_control,'model_loading'),(args.toy_evidence,'complete_toy_endpoint')):
        if path:require(authority.object_reference(path)==refs[name],'CLI control differs from actual pilot producer')
    require(not args.packing_control,'serial batch1 pipeline has no packed operation; do not substitute packing evidence')
    return refs


def _run_pilot(model,design,prepared,args,guard,identity,controls,*,baselines=None):
    from component_analysis import a3_edge_workload as workload
    import time
    start=time.monotonic();tasks={};checks={}
    controls=produce_pilot_controls(model,design,identity,baselines,guard=guard,root=Path(args.work_dir)/'controls')
    if torch.cuda.is_available() and next(model.parameters()).is_cuda:
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
    for task,graph in prepared['graphs'].items():
        rid=_membership(design,task,'validation')[0]
        guard();batch=_move(source_pair(design,task,'validation',rid,'D','clean',purpose='attribution'),model)['batch']
        receivers=[]
        for kind in ('q','k','v','mlp_in','readout'):
            candidates=sorted({tuple(e['receiver']) for e in graph['edges'] if e['receiver'][0]==kind})
            if candidates:receivers.append(candidates[0])
        checks[task]=native_pilot_checks(model,batch,receivers)
        tasks[task]=pilot_stability(model,design,task,graph,guard=guard,cache_root=Path(args.work_dir)/'pilot-attribution'/task,identity=identity,resume=args.resume)
    if next(model.parameters()).is_cuda:torch.cuda.synchronize()
    elapsed=time.monotonic()-start
    target_inventory=args.measurement_target
    require(target_inventory is not None,'frozen producer benchmark target required before model load')
    measured=collect_profile_measurements(model,design,prepared,target_inventory,guard=guard,root=Path(args.work_dir),startup_seconds=args.startup_seconds)
    measurement_references=[authority.object_reference(measured['artifact_path'])]
    result=dict(kind='a3_edge_pilot_complete',identity=identity,complete=True,pilot=True,injected=bool(design.get('injected')),
        tasks=tasks,native_checks=checks,independent_controls=bool(controls),control_references=controls,measurement_references=measurement_references,target_inventory=target_inventory,
        measurements=dict(elapsed_seconds=time.monotonic()-getattr(args,'stage_started',start),compute_before_measurement_seconds=elapsed,inference_load_seconds=getattr(args,'baseline_load_seconds',None),native_load_seconds=getattr(args,'native_load_seconds',None),batch_size=1,hardware=torch.cuda.get_device_name() if next(model.parameters()).is_cuda else 'CPU tiny',
            peak_allocated_bytes=torch.cuda.max_memory_allocated() if next(model.parameters()).is_cuda else 0,
            peak_reserved_bytes=torch.cuda.max_memory_reserved() if next(model.parameters()).is_cuda else 0),
        producer='a3_edge_pipeline',startup_seconds=getattr(args,'startup_seconds',None),exit_state='completed')
    return _stage_write(Path(args.work_dir)/'pilot',result,resume=args.resume)


def _run_summary(design,prepared,args,identity):
    assessment=authority.read_object(Path(args.work_dir)/'assessment')
    require(assessment['kind']=='a3_edge_assessment_complete' and assessment['identity']==identity,'changed assessment source identity')
    require(assessment['selection_reference']==authority.object_reference(assessment['selection_reference']['path']),'changed immutable selection bytes')
    expected=assessment['expected_keys'];chunks=assessment['chunks']
    require(len(chunks)==len(expected) and [x['key'] for x in chunks]==expected,'partial or duplicate final assessment coverage')
    pilot=authority.read_object(assessment['pilot_reference']['path']) if assessment.get('pilot_reference') else None
    if pilot is not None:
        require(assessment['pilot_reference']==authority.object_reference(assessment['pilot_reference']['path']),'changed native pilot bytes')
        validate_pilot(pilot,design,prepared,identity)
    plan=paired_bootstrap_plan(design);hydrated={}
    for chunk in chunks:
        task=chunk['key'][0];reference=chunk['result'].get('panel_reference')
        require(reference==authority.object_reference(reference['path']),'changed assessed panel bytes')
        key=digest(reference)
        if key not in hydrated:
            panel=authority.read_object(reference['path'])
            require(panel['identity']==identity and panel['task']==task,'changed panel source/profile identity')
            panel['summary']=recompute_panel(design,task,panel,bootstrap_plan=plan)
            approximation=bool(pilot and pilot['tasks'][task]['stable'])
            panel['summary']['approximation_validated']=approximation
            panel['summary']['edge_assay_ready']=bool(panel['summary'].get('edge_assay_ready') and approximation)
            panel['summary']['full_edge_specificity_claim_allowed']=bool(panel['summary']['edge_assay_ready'] and panel['summary']['point_pass'] and panel['summary'].get('confidence_gate_support') and not design.get('injected'))
            panel['summary']['exact_clamp_specificity']=bool(panel['summary'].get('point_pass') and panel['summary']['edge_assay_ready'])
            panel['summary']['approximation_qualification']='validated8/16 agreement' if approximation else 'approximation unresolved/unreliable; exact causal quantities descriptive; no full edge-specificity claim'
            hydrated[key]=panel
        family=next(f for f in assessment['selected']['tasks'][task]['families'] if f['seed']==chunk['key'][1] and f['ranking_condition']==chunk['key'][2])
        members=family['edges'] if chunk['key'][3]==0 else family['nulls']['sets'][chunk['key'][3]-1]
        require(sorted(hydrated[key]['edges'],key=edge_key)==sorted(members,key=edge_key),'assessment alias changed frozen learned/null membership')
        chunk['result']=hydrated[key]
    reports=[]
    for task,item in assessment['selected']['tasks'].items():
        validate_selection(item,prepared['graphs'][task])
        for c in ('D','I'):
            families=[f for f in item['families'] if f['ranking_condition']==c]
            if any(f['status']=='blocked' for f in families):
                reports.append(dict(task=task,ranking_condition=c,status='blocked_selection',families=families));continue
            panels={(key[1],key[3]):row['result']['summary'] for row in chunks for key in [row['key']] if key[0]==task and key[2]==c}
            require(set(panels)=={(seed,index) for seed in SEEDS for index in range(20)},'complete three-seed/nineteen-null coverage required')
            def stat(index):
                values=[panels[(seed,index)] for seed in SEEDS]
                return float(np.mean([v['D_fraction'] for v in values])) if all(v['complete'] and v['point_pass'] for v in values) else -math.inf
            learned=stat(0);nulls=[stat(i) for i in range(1,20)]
            informative=all(f['nulls']['informative'] for f in families)
            rank=1. if learned==-math.inf else (1+sum(x>=learned for x in nulls))/20
            reports.append(dict(task=task,ranking_condition=c,selected_seeds=[panels[(s,0)] for s in SEEDS],
                status='reported' if informative else 'uninformative_null_support',learned_statistic=None if learned==-math.inf else learned,
                null_statistics=[None if x==-math.inf else x for x in nulls],null_failed_gate=[x==-math.inf for x in nulls],
                p_value=rank if informative else None,null_inference='exploratory;resolution1/20;not in direction Holm',confirmatory=False,null_support=[dict(seed=f['seed'],possible_sets=f['nulls']['possible_sets'],duplicate_draws=f['nulls']['duplicate_draws'],informative=f['nulls']['informative']) for f in families],descriptive=bool(design['tasks'][task].get('descriptive',task=='sdr_v2')),
                seed_interpretation='three bootstrap fits share paired data; not independent datasets',estimand=ESTIMAND))
    complete=assessment['complete'] and all(row['result']['summary']['complete'] for row in chunks)
    runtime_identity=dict(injected=bool(design.get('injected')),pilot=False,complete=complete,source_commit=prepared['commit'])
    if args.final:
        final_guard(runtime_identity)
        require(args.ledger_snapshot,'fresh root ledger mapping required for production finalization')
        ledger=authority.normalize_ledger(args.ledger_snapshot,identity=identity,injected=False)
        proof=assessment.get('execution_evidence',{}).get('reservation',{}).get('reservation',{})
        matches=[e for e in ledger['entries'] if e['id']==proof.get('reservation_id')]
        require(len(matches)==1 and matches[0]['state']=='completed' and matches[0]['actual_gpu_hours'] is not None,'actual completed assembling job/runtime evidence required')
        require(all(matches[0]['actual_entry'].get(k)==proof.get('actual_entry',{}).get(k) for k in authority.RESERVATION_FIELDS),'changed actual assembling job source/output identity')
        require(set(design['tasks'])=={'far_v2','ser_v2','sdr_v2'} and all(len(s['assessment_ids'])==100 for s in design['tasks'].values()),'full unchanged A1 assessment scope required')
        require(all(row['result']['summary'].get('edge_assay_ready') is True for row in chunks),'full edge source/control/utility/approximation readiness required')
    result=dict(kind='a3_edge_summary',identity=identity,runtime_identity=runtime_identity,reports=reports,finalized=bool(args.final),
        assessment_reference=authority.object_reference(Path(args.work_dir)/'assessment'),rules=RULES,interpretation=ESTIMAND,
        qualification='operator-instructed behavior and source SDR qualifications retained; no unique deceptive-intent or recursive pruned-circuit claim')
    return _stage_write(Path(args.work_dir)/'summary',result,resume=args.resume)


def main(argv=None,*,model_loader=None):
    from component_analysis import a3_edge_workload as workload
    import time
    stage_started=time.monotonic()
    args=parser().parse_args(argv)
    args.stage_started=stage_started
    require(not args.final or args.stage=='summarize','--final is only valid for completed summary intake')
    require(re.fullmatch('[0-9a-f]{40}',args.commit) is not None,'full execution commit required')
    if args.dry_run:return dry_run(args)
    design=_read_design(args.design)
    require(design['direction_protocol']['commit']==args.commit,'execution commit differs from frozen design')
    if args.stage=='prepare':
        prepare(design,_metadata_geometry(design,args),commit=args.commit,registry_paths=args.registry,output=Path(args.work_dir)/'prepared',design_path=args.design)
        return
    prepared=authority.read_object(args.prepared or Path(args.work_dir)/'prepared')
    validate_prepared(prepared,design,registry_paths=args.registry)
    identity=_stage_identity(design,prepared)
    if args.stage=='summarize':return _run_summary(design,prepared,args,identity)
    fitted=authority.read_object(Path(args.fit_evidence) if args.fit_evidence else Path(args.work_dir)/'fit') if args.stage=='select' else None
    selected_input=authority.read_object(Path(args.selection) if args.selection else Path(args.work_dir)/'selection') if args.stage=='assess' else None
    measurement_target=None
    if args.stage=='pilot':
        target_fit=authority.read_object(args.fit_evidence or Path(args.work_dir)/'fit') if args.measure_stage=='select' else None
        target_selected=authority.read_object(args.selection or Path(args.work_dir)/'selection') if args.measure_stage=='assess' else None
        measurement_target=workload.freeze_inventory(design,prepared['graphs'],stage=args.measure_stage,identity=identity,steps=args.steps,bank_sources=prepared['bank_sources'],fit=target_fit,selected=target_selected)
    args.measurement_target=measurement_target
    inventory=workload.freeze_inventory(design,prepared['graphs'],stage=args.stage,identity=identity,steps=args.steps,bank_sources=prepared['bank_sources'],fit=fitted,selected=selected_input,measurement_target=measurement_target)
    if args.inventory:
        require(authority.read_object(args.inventory)==inventory,'changed original edge workload inventory')
    guard=execution_guard(design,prepared,args,inventory);admitted=guard()
    injected_loader=model_loader is not None
    require(not injected_loader or design.get('injected') is True,'injected model loader forbidden for production')
    if not injected_loader and args.stage!='pilot':
        controls=_require_independent_controls(args,identity,design)
        root_admission=bind_root_evidence(admitted,controls)
        if args.stage!='pilot':
            pilot=_stability_admission(args,identity,design,prepared)
            measurement_refs=[authority.object_reference(path) for path in args.measurement] if args.measurement else pilot.get('measurement_references',[])
            require(measurement_refs and root_admission.get('edge_measurement_references')==measurement_refs,'measurement files are not anchored in original root admission')
            measurements=[]
            for reference in measurement_refs:
                receipt=authority.read_object(reference['path'])
                validate_measurement_receipt(receipt,design,prepared,identity)
                measurements.append(receipt)
            ledger=authority.normalize_ledger(args.ledger_snapshot,identity=identity,injected=False)
            for receipt in measurements:validate_producer_jobs(receipt,ledger,identity)
            proposal=workload.project_cost(inventory,measurements,capacities=admitted['storage_capacities'])
            require(torch.cuda.is_available(),'allocated native CUDA device required')
            names={r['hardware'] for r in measurements}
            require(names=={torch.cuda.get_device_name()},'target GPU model differs from actual producer; no cross-device forecast')
            require(torch.cuda.mem_get_info()[0]+torch.cuda.memory_reserved()>=proposal['gpu_peak_reserved_bytes'],'current allocated device lacks measured target capacity')
            require(root_admission.get('edge_pilot_reference')==authority.object_reference(args.pilot_evidence),'edge pilot is not anchored in original root admission')
            if args.steps==16:require(root_admission.get('edge_integration_reference')==authority.object_reference(args.integration_admission),'16-node evidence not anchored in original root admission')
    else:controls={}
    baselines=None;baseline_load_seconds=0.
    if args.stage=='pilot':
        baseline_started=time.monotonic()
        baseline_model=(model_loader or _native_loader)(design,prepared,args)
        baseline_load_seconds=time.monotonic()-baseline_started
        baselines=pilot_baselines(baseline_model,design,guard=guard)
        del baseline_model
        import gc
        gc.collect()
        if torch.cuda.is_available():torch.cuda.empty_cache()
    startup=time.monotonic();model=(model_loader or _native_loader)(design,prepared,args)
    args.native_load_seconds=time.monotonic()-startup
    args.baseline_load_seconds=baseline_load_seconds
    args.startup_seconds=args.native_load_seconds+baseline_load_seconds
    guard()
    if args.stage=='pilot':return _run_pilot(model,design,prepared,args,guard,identity,controls,baselines=baselines)
    if args.stage=='fit':return _run_fit(model,design,prepared,args,guard,identity)
    if args.stage=='select':return _run_selection(model,design,prepared,args,guard,identity)
    if args.stage=='assess':return _run_assessment(model,design,prepared,args,guard,identity)
    raise ValueError('unsupported edge stage')





def verify_effective_clamps(model,result):
    """Compare actual selected receiver outputs with explicit fixed x-star values."""
    from component_analysis.a3_native import _native_norm
    records=[]
    cfg=model.config;dim=getattr(cfg,'head_dim',None) or cfg.hidden_size//cfg.num_attention_heads
    for site,value in result['clamps'].items():
        kind,layer,index=site;mask=result['patch_positions'][site]
        if kind=='readout':expected=value
        elif kind=='mlp_in':expected=_native_norm(model.model.layers[layer].post_attention_layernorm,value)
        else:
            block=model.model.layers[layer];projection=getattr(block.self_attn,kind+'_proj')
            full=torch.nn.functional.linear(_native_norm(block.input_layernorm,value),projection.weight,projection.bias)
            expected=full[...,index*dim:(index+1)*dim]
        observed=result['receiver_outputs'][site]
        error=float((expected[mask]-observed[mask]).abs().max().detach().cpu())
        passed=bool(torch.equal(expected[mask],observed[mask]))
        require(passed,'effective receiver does not equal explicitly constructed intact-delta clamp')
        records.append(dict(receiver=list(site),selected_positions=int(mask.sum()),max_error=error,equal=passed))
    require(records,'unsupported empty clamp cannot establish readiness')
    return records


def validation_attribution(model,design,task,graph,*,steps,guard):
    """Outcome-isolated validation attribution diagnostic; never refits ranking."""
    values={};missing={};ids=_membership(design,task,'validation')
    for condition in ('D','I'):
        totals={edge_key(e):0. for e in graph['edges']};blocked={}
        for rid in ids:
            for stream in STREAMS:
                guard();item=_move(source_pair(design,task,'validation',rid,condition,stream,purpose='attribution'),model)
                supported,unsupported=supported_edges(item,graph['edges'])
                for edge in unsupported:blocked.setdefault(edge_key(edge),[]).append([rid,stream])
                if supported:
                    for record in core.attribute_edges(model,[item],edges=supported,steps=steps):
                        totals[edge_key(record['edge'])]+=record['score']/(2*len(ids))
        values[condition]=[dict(edge=e,score=None if edge_key(e) in blocked else totals[edge_key(e)],supported=edge_key(e) not in blocked,unsupported_rows=blocked.get(edge_key(e),[])) for e in graph['edges']]
    return dict(split='validation',rank_selection_use=False,records=values)








def bind_root_evidence(guard_evidence,control_references):
    admission=authority.read_object(guard_evidence['reservation']['reservation']['admission_path'])
    require(admission.get('edge_control_references')==control_references,'independent control files differ from original root admission')
    return admission





def batch_facts(batch):
    return {name:batch[name].detach().cpu().tolist() for name in ('input_ids','attention_mask','readout','opposite_token','honest_token','expected_token')}|dict(
        instance_ids=batch['instance_ids'],condition=batch['condition'],stream=batch['stream'],physical_batch_size=int(batch['input_ids'].shape[0]),physical_width=int(batch['input_ids'].shape[1]))


def plain_inference_observation(model,batch):
    """Independent ordinary-HF inference path; never used for gradients."""
    from component_analysis.hooks import readout_logits
    rows=torch.arange(batch['input_ids'].shape[0],device=batch['input_ids'].device);captured=[]
    def final_input(module,args):captured.append(args[0][rows,batch['readout']].detach().clone())
    handle=model.model.norm.register_forward_pre_hook(final_input)
    try:
        with torch.no_grad():
            forward=model(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],use_cache=False)
            fp32=readout_logits(model,captured[0]);native=forward.logits[rows,batch['readout']]
            observation=_observation({'fp32_logits':fp32,'logits':native},batch)
            observation['readout_sha256']=hashlib.sha256(fp32.detach().float().cpu().numpy().tobytes()).hexdigest()
    finally:handle.remove()
    return dict(observation,**batch_facts(batch))


def pilot_source_cases(design):
    """Fixed eight validation identities, all primary condition/stream shapes."""
    cases=[]
    for task in design['tasks']:
        ids=_membership(design,task,'validation')
        require(len(ids)>=8,'eight fixed validation identities required')
        for rid in ids[:8]:
            for condition in CONDITIONS:
                for stream in STREAMS:
                    cases.append(dict(source=task,instance_id=rid,condition=condition,stream=stream))
    for source in ('ioi','mmlu'):
        for row in design.get(source+'_validation',[])[:8]:
            cases.append(dict(source=source,instance_id=row['instance_id'],condition=source.upper(),stream='clean'))
    return cases


def pilot_case_batch(design,case):
    task=case['source']
    if task in ('ioi','mmlu'):
        rows=[r for r in design[task+'_validation'] if r['instance_id']==case['instance_id']]
        require(len(rows)==1,'missing/duplicate pilot utility source')
        return _utility_batch(rows[0],case['stream'],physical_width=source_width(design,task))
    return _batch(_row(design,task,'validation',case['instance_id'],case['condition']),case['stream'],physical_width=source_width(design,task))


def pilot_baselines(model,design,*,guard):
    baseline=[]
    for case in pilot_source_cases(design):
        guard();batch=_move({'batch':pilot_case_batch(design,case)},model)['batch']
        baseline.append(dict(case=case,observation=plain_inference_observation(model,batch)))
    return baseline


def produce_pilot_controls(model,design,identity,baselines,*,guard,root):
    require(baselines and [r['case'] for r in baselines]==pilot_source_cases(design),'independently loaded fixed validation inference baselines required')
    comparisons=[];geometry=[]
    for saved in baselines:
        guard();case=saved['case'];batch=_move({'batch':pilot_case_batch(design,case)},model)['batch'];facts=batch_facts(batch)
        native=core.native_forward(model,batch,capture_sites=[]);actual=_observation(native,batch)
        actual['readout_sha256']=hashlib.sha256(native['fp32_logits'].detach().float().cpu().numpy().tobytes()).hexdigest();del native
        expected=saved['observation']
        require(all(expected[k]==v for k,v in facts.items()),'independent model control source/physical shape differs')
        require(math.isclose(expected['margin'],actual['margin'],abs_tol=1e-5,rel_tol=1e-5) and expected['fp32_argmax']==actual['fp32_argmax'] and expected['native_argmax']==actual['native_argmax'], 'independent inference/native readout values or argmax differ')
        comparisons.append(dict(case=case,input_sha256=digest(facts),expected={k:expected[k] for k in actual},observed=actual))
        geometry.append(dict(case=case,facts=facts,packed=False))
    toy=complete_toy_control()
    values={
        'model_loading':dict(comparisons=comparisons,independent_loads=2),
        'serial_geometry':dict(rows=geometry,physical_batch_size=1,packed=False),
        'complete_toy_endpoint':toy,
    }
    refs={}
    for name,raw in values.items():
        body=dict(kind='a3_edge_execution_control_v1',control=name,identity=identity,producer='a3_edge_pipeline',actual_execution=True,
            source_code_hashes=code_hashes(),runtime=authority.runtime_environment(model),raw=raw,passed=True,complete=True)
        _stage_write(Path(root)/name,body,resume=True)
        refs[name]=authority.object_reference(Path(root)/name)
    return refs


def complete_toy_control():
    """Execute the reviewed complete linear software fixture and retain raw values.

    This isolated CPU check temporarily routes the edge core to that explicit
    analytic toy seam and always restores it. It does not assert donor endpoint
    recovery for the incomplete production deciding/quartet graph.
    """
    import runpy
    import pytest
    source=ladder.REPO/'tests/test_a3_edges.py'
    namespace=runpy.run_path(str(source))
    check=namespace['test_complete_linear_toy_causal_dead_ig_ranking_and_full_endpoint']
    original=namespace['LinearCircuit'];calls=[];scores=[]
    class RecordedToy(original):
        def forward(self,batch,**kwargs):
            result=super().forward(batch,**kwargs)
            calls.append(dict(condition=batch['condition'],patched=bool(kwargs.get('patches')),grad=bool(kwargs.get('grad')),margin=float(result['fp32_logits'][0,1].detach())))
            return result
    original_attribute=core.attribute_edges
    def record_scores(*args,**kwargs):
        result=original_attribute(*args,**kwargs);scores.extend(float(r['score']) for r in result);return result
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(check.__globals__,'LinearCircuit',RecordedToy)
        patch.setattr(core,'attribute_edges',record_scores)
        check(patch)
    intact=[r['margin'] for r in calls if r['condition']=='D' and not r['patched']][-1]
    donor=[r['margin'] for r in calls if r['condition']=='H' and not r['patched']][-1]
    clamped=[r['margin'] for r in calls if r['condition']=='D' and r['patched'] and not r['grad']][-1]
    require(clamped==donor and intact-clamped==sum(scores),'complete toy endpoint/IG control failed')
    return dict(software_control=True,source=str(source.resolve()),source_sha256=common.file_hash(source),check=check.__name__,
        scores=scores,intact_margin=intact,donor_margin=donor,clamped_margin=clamped,endpoint_equal=clamped==donor,raw_calls=calls,
        production_claim='none; complete analytic toy only')





def validate_control(body,design,identity):
    require(body.get('kind')=='a3_edge_execution_control_v1' and body.get('identity')==identity and body.get('complete') is True and body.get('actual_execution') is True and body.get('producer')=='a3_edge_pipeline','actual completed source-bound edge producer control required')
    require(body.get('source_code_hashes')==code_hashes(),'changed producer code closure')
    raw=body['raw'];name=body['control']
    if name!='complete_toy_endpoint':
        observed=body.get('runtime');require(isinstance(observed,dict),'actual producer runtime facts required')
        target=identity.get('numeric_profile') or {}
        require(observed['dtype'].removeprefix('torch.')==target.get('dtype',observed['dtype']).removeprefix('torch.') and observed['backend']==target.get('backend',observed['backend']),'changed actual native runtime profile')
    if name=='complete_toy_endpoint':
        source=ladder.REPO/'tests/test_a3_edges.py'
        require(raw.get('software_control') is True and raw.get('source')==str(source.resolve()) and raw.get('source_sha256')==common.file_hash(source),'changed complete toy software source')
        require(raw.get('scores')==[10.,0.] and raw.get('intact_margin')==14. and raw.get('donor_margin')==4. and raw.get('clamped_margin')==4. and raw.get('endpoint_equal') is True,'actual complete toy endpoint/IG comparisons failed')
    elif name=='model_loading':
        comparisons=raw['comparisons'];require(raw.get('independent_loads')==2 and [r['case'] for r in comparisons]==pilot_source_cases(design),'incomplete independent loading scope')
        for row in comparisons:
            facts=batch_facts(pilot_case_batch(design,row['case']))
            require(row['input_sha256']==digest(facts),'changed producer source/input scope')
            a,b=row['expected'],row['observed']
            require(all(type(x['margin']) in (int,float) and math.isfinite(x['margin']) for x in (a,b)),'nonfinite native comparison')
            require(math.isclose(a['margin'],b['margin'],abs_tol=1e-5,rel_tol=1e-5) and a['fp32_argmax']==b['fp32_argmax'] and a['native_argmax']==b['native_argmax'],'raw independent readout comparisons failed')
    elif name=='serial_geometry':
        rows=raw['rows'];require(raw.get('physical_batch_size')==1 and raw.get('packed') is False and [r['case'] for r in rows]==pilot_source_cases(design),'actual serial source geometry missing')
        for row in rows:
            require(row['facts']==batch_facts(pilot_case_batch(design,row['case'])) and row.get('packed') is False,'changed serial source tensors/mask/labels/geometry')
    else:raise ValueError('unsupported edge control producer')
    return body





def recompute_panel(design,task,result,*,bootstrap_plan=None):
    ids=_membership(design,task,'test');rows=result['rows'];utilities=result['utility_rows']
    for row in rows:
        require(not row.get('timing_only') and not row.get('pilot'),'pilot/timing-only observations cannot finalize')
        source=_row(design,task,'test',row['instance_id'],row['condition'])
        require(row['split']=='test' and row['pressure_id']==a3_design._pressure(_row(design,task,'test',row['instance_id'],'D')),'changed assessment row split/cluster provenance')
    for condition,source in (('IOI','ioi'),('MMLU_zero','mmlu'),('MMLU_h_mean','mmlu')):
        actual=[r for r in utilities if r['condition']==condition and r.get('supported')]
        require(all(not r.get('timing_only') and not r.get('pilot') for r in actual),'pilot utility observations cannot finalize')
        if actual:
            expected=[r['instance_id'] for r in design['utility'][source]]
            require(len(actual)==len(expected) and {r['instance_id'] for r in actual}==set(expected),'changed original utility assessment membership')
            original={r['instance_id']:r for r in design['utility'][source]}
            require(all(r.get('source_split')==original[r['instance_id']]['split'] and r.get('analysis_split')=='assessment' for r in actual),'changed original utility source split or assessment role')
    return summarize_rows(rows,expected_ids=ids,utility_rows=utilities,bootstrap_plan=bootstrap_plan,task=task)


def paired_bootstrap_plan(design,*,n_boot=2000):
    from component_analysis.a3_statistics import draw_pressure_clusters
    require(type(n_boot) is int and n_boot>0,'positive paired bootstrap count required')
    tasks={task:dict(instance_ids=_membership(design,task,'test'),pressure_texts=[a3_design._pressure(_row(design,task,'test',rid,'D')) for rid in _membership(design,task,'test')]) for task in design['tasks']}
    rng=np.random.default_rng(9001);plan=[]
    utility={name:[r['instance_id'] for r in design['utility'].get(source,[])] for name,source in (('IOI','ioi'),('MMLU','mmlu'))}
    for _ in range(n_boot):
        draw=draw_pressure_clusters(tasks,rng)
        row={task:[tasks[task]['instance_ids'][i] for i in draw[task]['indices']] for task in tasks}
        for source,ids in utility.items():row[source]=rng.choice(ids,len(ids),replace=True).tolist() if ids else []
        plan.append(row)
    return plan





def source_width(design,source):
    rows=(design.get(source+'_validation',[])+design.get('utility',{}).get(source,[])) if source in ('ioi','mmlu') else design['access_rows'][source]
    require(rows,'missing source geometry rows')
    return 1+max(len(s['tokens']) for row in rows for s in row['streams'].values())





def ancestral_bank_sources(design):
    if design.get('injected') is True and not design.get('parent_evidence'):
        return {task:dict(source_ids=[r['instance_id'] for r in rows if r['condition']=='H' and r['split'] in ('train','validation')],
            rows=[copy.deepcopy(r) for r in rows if r['condition']=='H' and r['split'] in ('train','validation')],
            source_sha256=digest([r for r in rows if r['condition']=='H' and r['split'] in ('train','validation')])) for task,rows in design['access_rows'].items()}
    from component_analysis.a3_pipeline import load_a1_parents
    evidence=design['parent_evidence'];parent,selected,current=load_a1_parents(evidence['prepared_path'],evidence['selected_path'])
    require(current==evidence,'changed A1 bank parent completion bytes')
    banks={}
    for task in design['tasks']:
        ids=parent['designs'][task]['bank_ids']
        require(selected['banks'][task]['provenance']['source_ids']==ids,'changed original-H A1 bank convention')
        indexed={r['instance_id']:r for r in parent['rows'][task]['H']}
        require(len(indexed)==len(parent['rows'][task]['H']) and len(ids)==len(set(ids)),'duplicate original-H bank source')
        rows=[copy.deepcopy(indexed[rid]) for rid in ids]
        require(all(r['split'] in ('train','validation') and r['condition']=='H' for r in rows),'assessment row in ancestral H bank')
        banks[task]=dict(source_ids=list(ids),rows=rows,source_sha256=digest(rows),a1_parent_sha256=digest(parent),a1_selection_sha256=digest(selected))
    return banks





def cached_h_bank(model,design,prepared,task,*,identity,root,guard):
    contract=prepared['bank_sources'][task];sources=sorted({tuple(e['sender']) for e in prepared['graphs'][task]['edges']})
    key=dict(identity=identity,task=task,sources=[list(s) for s in sources],source_sha256=contract['source_sha256'])
    path=Path(root)/digest(key);guard()
    if path.exists():
        body=authority.read_object(path)
        require(body['key']==key and body['provenance']['source_ids']==contract['source_ids'],'changed source/profile H bank')
        values={tuple(r['site']):torch.tensor(r['value'],dtype=torch.float32) for r in body['values']}
        require(set(values)==set(sources),'incomplete full sender-union H bank')
        bank=dict(values=values,provenance=body['provenance'])
    else:
        bank=h_mean_bank(model,design,task,prepared['graphs'][task]['edges'],guard=guard,bank_sources=contract)
        body=dict(kind='a3_edge_H_bank',key=key,values=[dict(site=list(s),value=bank['values'][s].tolist()) for s in sources],provenance=bank['provenance'])
        authority.publish_object(path,body)
    bank['reference']=authority.object_reference(path)
    return bank


def cached_assessment_panel(model,design,prepared,task,selected,*,identity,root,guard):
    """Exact same model/source/set outcomes may serve duplicate frozen null draws.

    Draw memberships/indices remain distinct scientific slots. No receiver or
    selected-set intervention is approximated, summed or treated as a replicate.
    """
    key=dict(identity=identity,task=task,edges=selected);path=Path(root)/'panels'/digest(key);guard()
    if path.exists():
        panel=authority.read_object(path)
        require(panel['identity']==identity and panel['task']==task and panel['edges']==selected,'changed exact panel membership/source')
    else:
        bank=cached_h_bank(model,design,prepared,task,identity=identity,root=Path(root)/'banks',guard=guard) if design.get('utility',{}).get('mmlu') else None
        panel=dict(identity=identity,task=task,edges=selected,**_assessment_panel(model,design,task,selected,guard=guard,bank_sources=prepared['bank_sources'][task],bank=bank))
        panel['bank_reference']=bank.get('reference') if bank else None
        authority.publish_object(path,panel)
    return dict(panel_reference=authority.object_reference(path),summary=panel['summary'])





def _synchronize(model):
    if next(model.parameters()).is_cuda:torch.cuda.synchronize(next(model.parameters()).device)


def observe_native_operation(model,call):
    """Measure actual native forwards and local VJPs; restore all seams on error.

    Instrumentation is serial and process-local. It never changes computation,
    data, graph memberships or parameters, and records no vocabulary arrays.
    """
    from component_analysis import a3_native
    import time
    forwards=[];backwards=[]
    original_module=a3_native.native_forward;original_core=core.native_forward;original_grad=torch.autograd.grad
    def forward(*args,**kwargs):
        _synchronize(model);start=time.perf_counter();out=original_module(*args,**kwargs);_synchronize(model)
        forwards.append(time.perf_counter()-start);return out
    def backward(*args,**kwargs):
        _synchronize(model);start=time.perf_counter();out=original_grad(*args,**kwargs);_synchronize(model)
        backwards.append(time.perf_counter()-start);return out
    if next(model.parameters()).is_cuda:torch.cuda.reset_peak_memory_stats()
    a3_native.native_forward=forward;core.native_forward=forward;torch.autograd.grad=backward
    _synchronize(model);started=time.perf_counter()
    try:
        result=call();_synchronize(model);elapsed=time.perf_counter()-started
    finally:
        a3_native.native_forward=original_module;core.native_forward=original_core;torch.autograd.grad=original_grad
    cuda=next(model.parameters()).is_cuda
    capacity=(torch.cuda.mem_get_info()[0]+torch.cuda.memory_reserved()) if cuda else 2**63-1
    return result,dict(seconds=elapsed,forward_calls=len(forwards),backward_calls=len(backwards),
        forward_seconds=sum(forwards),backward_seconds=sum(backwards),cache_contract_seconds=max(0.,elapsed-sum(forwards)-sum(backwards)),
        peak_allocated_bytes=torch.cuda.max_memory_allocated() if cuda else 0,
        peak_reserved_bytes=torch.cuda.max_memory_reserved() if cuda else 0,device_available_bytes=int(capacity))


def _profile_case_batch(design,prepared,p,case):
    source=p['source']
    if source.startswith('H_bank:'):
        task=p['analysis_task'];rows=[r for r in prepared['bank_sources'][task]['rows'] if r['instance_id']==case['instance_id']]
        require(len(rows)==1 and rows[0]['split']=='validation','timing bank source must be ancestral original-H validation')
        return _utility_batch(rows[0],case['stream'],physical_width=p['padded_width'])
    return pilot_case_batch(design,case)


def _measurement_cases(design,prepared,p):
    source=p['source'];task=p['analysis_task'];operation=p['operation']
    if source.startswith('H_bank:'):source=task
    cases=[c for c in pilot_source_cases(design) if c['source']==source and c['condition']==p['condition']]
    if operation in ('attribute_receiver','exact_mechanism'):
        supported=[]
        for c in cases:
            pair=source_pair(design,task,'validation',c['instance_id'],c['condition'],c['stream'],purpose='attribution' if operation=='attribute_receiver' else 'validation')
            _,missing=supported_edges(pair,p['edges'])
            if not missing:supported.append(c)
        return supported
    if p['source'].startswith('H_bank:'):
        ids=set(prepared['bank_sources'][task]['source_ids']);cases=[c for c in cases if c['instance_id'] in ids]
    return cases


def collect_profile_measurements(model,design,prepared,inventory,*,guard,root,startup_seconds=None,max_samples=1):
    """Actual validation-only profile producer; CPU injection cannot authorize GPUs.

    A later fit/select/assessment inventory may reuse these exact physical
    profiles across IDs under the frozen serial policy. Token contraction work
    is conservatively scaled by actual source-derived occupancy bounds.
    """
    from component_analysis import a3_edge_workload as workload
    import resource
    import time
    import uuid
    workload.validate_inventory(inventory);identity=inventory['identity']
    require(type(max_samples) is int and 1<=max_samples<=16,'bounded fixed validation timing samples required')
    startup_measured=startup_seconds is not None
    if startup_seconds is None:
        require(identity.get('injected') is True,'actual model-load timing required for production producer')
        start=time.perf_counter();model=copy.deepcopy(model).eval().requires_grad_(False);startup_seconds=time.perf_counter()-start
        startup_measured=True
    runtime=authority.runtime_environment(model)
    runtime['vocabulary_size']=int(model.config.vocab_size)
    runtime['dtype_bytes']=int(next(model.parameters()).element_size())
    target=identity.get('numeric_profile') or {}
    require(runtime['dtype'].removeprefix('torch.')==target.get('dtype',runtime['dtype']).removeprefix('torch.') and runtime['backend']==target.get('backend',runtime['backend']),'producer native dtype/backend differs from frozen serial profile')
    measurements=[];guards=[];guard_evidence=[];banks={};scalar_records=[]
    root=Path(root);run_root=root/'measurement-runs'/uuid.uuid4().hex
    def fresh():
        t=time.perf_counter();proof=guard();guards.append(time.perf_counter()-t)
        if proof is not None:guard_evidence.append(proof)
    for requirement in inventory['requirements']:
        p=requirement['profile'];cases=_measurement_cases(design,prepared,p)
        require(cases,'no supported validation identity for required shape '+requirement['profile_id'])
        cases=cases[:max_samples];samples=[];hashes=[];forward_calls=0;backward_calls=0;fwd=0.;bwd=0.;cache=0.;peak_allocated=0;peak_reserved=0;available=2**63-1;tokens=0
        for case in cases:
            fresh();batch=_move({'batch':_profile_case_batch(design,prepared,p,case)},model)['batch'];hashes.append(digest(batch_facts(batch)))
            operation=p['operation'];task=p['analysis_task'];edges=p['edges']
            if operation=='attribute_receiver':
                pair=_move(source_pair(design,task,'validation',case['instance_id'],case['condition'],case['stream'],purpose='attribution'),model)
                call=lambda:core.attribute_edges(model,[pair],edges=edges,steps=p['integration_nodes'])
                tokens=max(tokens,sum(len(pair['batch']['positions'][e['position']][0]) for e in edges))
            elif operation=='exact_mechanism':
                call=lambda:score_mechanism(model,design,task,'validation',edges,guard=lambda:None,instance_ids=[case['instance_id']],conditions=[case['condition']],streams=[case['stream']])
                tokens=max(tokens,sum(len(batch['positions'][e['position']][0]) for e in edges))
            elif operation=='H_bank':
                sources=sorted({tuple(e['sender']) for e in edges})
                def call():
                    result=core.native_forward(model,batch,capture_sites=sources);mask=batch['attention_mask'].bool()
                    return [dict(site=list(s),sum_norm=float(result['additive'][s][mask].float().sum(0).norm().detach().cpu()),tokens=int(mask.sum())) for s in sources]
                tokens=max(tokens,int(batch['attention_mask'].sum()))
            elif operation in ('IOI','MMLU_floors'):
                source='ioi' if operation=='IOI' else 'mmlu'
                if operation=='MMLU_floors' and task not in banks:
                    original=prepared['bank_sources'][task]
                    rows=[r for r in original['rows'] if r['instance_id'] in set(_membership(design,task,'validation')[:8]) and r['split']=='validation']
                    require(rows,'no ancestral H validation rows for timing-only mean bank')
                    timing_sources=dict(source_ids=[r['instance_id'] for r in rows],rows=rows,source_sha256=digest(rows),padded_width=1+max(len(s['tokens']) for r in original['rows'] for s in r['streams'].values()))
                    banks[task]=h_mean_bank(model,design,task,prepared['graphs'][task]['edges'],guard=fresh,bank_sources=timing_sources)
                    banks[task]['provenance']['timing_only']=True
                call=lambda:score_utilities(model,design,task,'validation',edges,guard=lambda:None,bank=banks.get(task),only_ids={source:[case['instance_id']]},timing_only=True)
                tokens=max(tokens,len(edges))
            else:raise ValueError('unsupported measurement primitive')
            output,observed=observe_native_operation(model,call)
            # Outputs are scalar diagnostic rows only; native vocab arrays never
            # enter receipts. Keep a real payload for serialization/CPU overhead.
            scalar_records.extend(output if isinstance(output,list) else [])
            samples.append(observed['seconds']);forward_calls+=observed['forward_calls'];backward_calls+=observed['backward_calls'];fwd+=observed['forward_seconds'];bwd+=observed['backward_seconds'];cache+=observed['cache_contract_seconds']
            peak_allocated=max(peak_allocated,observed['peak_allocated_bytes']);peak_reserved=max(peak_reserved,observed['peak_reserved_bytes']);available=min(available,observed['device_available_bytes'])
        source_splits=sorted({measurement_source_split(design,prepared,p,c) for c in cases})
        measurements.append(dict(profile_id=requirement['profile_id'],profile=p,analysis_split='validation',source_split=source_splits[0] if len(source_splits)==1 else 'mixed',source_splits=source_splits,source_cases=cases,input_hashes=hashes,batch_seconds=samples,tokens_measured=tokens,
            forward_calls=forward_calls,backward_calls=backward_calls,forward_seconds=fwd,backward_seconds=bwd,cache_contract_seconds=cache,
            peak_allocated_bytes=peak_allocated,peak_reserved_bytes=peak_reserved,device_available_bytes=available))
    require(scalar_records,'actual scalar producer output required for overhead timing')
    fresh();payload=dict(identity=identity,source_split='validation',records=scalar_records)
    t=time.perf_counter();authority.publish_object(run_root/'serialization',payload);serialization_seconds=time.perf_counter()-t
    serialized_bytes=sum(p.stat().st_size for p in (run_root/'serialization').iterdir())
    # Execute the actual scalar operations used by fit aggregation and ranking
    # on genuine measured validation scores. No fake fit/assessment is published.
    values=[float(r.get('score',r.get('patched_margin',r.get('sum_norm',0.)))) for r in scalar_records if r.get('score',0.) is not None]
    t=time.perf_counter()
    for seed in SEEDS:
        for task in design['tasks']:
            ids=_membership(design,task,'validation')[:8]
            clusters=[a3_design._pressure(_row(design,task,'validation',rid,'D')) for rid in ids]
            a3_directions._cluster_weights(clusters,ids,len(ids),seed)
        sorted(values);sum(values)
    cpu_seconds=time.perf_counter()-t
    bootstrap_calibrations=[]
    if inventory['overhead']['cpu_summaries']:
        for task,graph in prepared['graphs'].items():
            probe=[min((e for e in graph['edges'] if e['receiver'][0]=='readout' and e['position']=='assistant_readout'),key=edge_key)]
            ids=_membership(design,task,'validation')[:8]
            if task not in banks:
                original=prepared['bank_sources'][task];source_rows=[r for r in original['rows'] if r['split']=='validation' and r['instance_id'] in set(ids)]
                contract=dict(source_ids=[r['instance_id'] for r in source_rows],rows=source_rows,source_sha256=digest(source_rows),padded_width=1+max(len(s['tokens']) for r in original['rows'] for s in r['streams'].values()))
                banks[task]=h_mean_bank(model,design,task,graph['edges'],guard=fresh,bank_sources=contract)
            def capture():
                rows=score_mechanism(model,design,task,'validation',probe,guard=fresh,instance_ids=ids)
                utilities=score_utilities(model,design,task,'validation',probe,guard=fresh,bank=banks[task],timing_only=True)
                return rows,utilities
            captured,observed=observe_native_operation(model,capture)
            rows,utilities=captured;t0=time.perf_counter()
            summarize_rows(rows,expected_ids=ids,utility_rows=utilities,n_boot=2000)
            seconds=time.perf_counter()-t0
            bootstrap_calibrations.append(dict(task=task,seconds=seconds,rows=len(rows)+len(utilities),bootstrap_nodes=2000,capture_evidence=observed,validation_ids=ids,timing_only=True))
        worst=max(bootstrap_calibrations,key=lambda r:r['seconds']/r['rows'])
        cpu_seconds=worst['seconds'];values=[None]*worst['rows']
    cuda=next(model.parameters()).is_cuda
    result=dict(artifact_path=str((run_root/'receipt').resolve()),kind='a3_edge_measurements_v1',producer='a3_edge_pipeline',identity=identity,injected=bool(identity.get('injected')),code_hashes=code_hashes(),
        complete=True,exit_state='completed',runtime=runtime,hardware=torch.cuda.get_device_name() if cuda else 'CPU tiny',
        startup_seconds=float(startup_seconds),startup_measured=startup_measured,measurements=measurements,
        guard_seconds=guards,guard_evidence=guard_evidence,serialization=dict(seconds=serialization_seconds,bytes=serialized_bytes,reference=authority.object_reference(run_root/'serialization')),
        cpu_summary=dict(seconds=cpu_seconds,rows=max(1,len(values)),bootstrap_calibrations=bootstrap_calibrations),host_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024,
        producer_inventory_sha256=inventory['inventory_sha256'],source_scope='fixed first eight validation IDs only; utility validation rows; no assessment outcomes',
        reused_means='timing-only validation-H bank values never enter actual floor artifacts')
    authority.publish_object(run_root/'receipt',result)
    return result





def validate_measurement_receipt(receipt,design,prepared,identity):
    require(receipt.get('kind')=='a3_edge_measurements_v1' and receipt.get('identity')==identity and receipt.get('code_hashes')==code_hashes() and receipt.get('complete') is True and receipt.get('exit_state')=='completed','actual completed producer/source/runtime receipt required')
    for measured in receipt['measurements']:
        p=measured['profile']
        allowed=_measurement_cases(design,prepared,p)
        require(measured['source_cases'] and all(c in allowed for c in measured['source_cases']),'timing must use fixed supported validation identities only')
        expected=[digest(batch_facts(_profile_case_batch(design,prepared,p,c))) for c in measured['source_cases']]
        require(measured['input_hashes']==expected,'changed actual producer tokens/masks/labels/positions or physical shape')
        splits=sorted({measurement_source_split(design,prepared,p,c) for c in measured['source_cases']})
        require(measured.get('analysis_split')=='validation' and measured.get('source_splits')==splits,'changed producer original source split or analysis role')
        require(p['source_identity_sha256']==digest(identity),'changed model/profile source identity')
    return receipt





def validate_pilot(pilot,design,prepared,identity):
    require(pilot.get('identity')==identity and set(pilot['tasks'])==set(design['tasks']),'pilot source/task coverage differs')
    for task,report in pilot['tasks'].items():
        require(report['instance_ids']==_membership(design,task,'validation')[:8] and len(report['instance_ids'])==8 and report['split']=='validation','eight fixed validation identities required')
        require(set(report['conditions'])=={'D','I'},'both attribution conditions required in pilot')
        stable=True
        for condition,raw in report['conditions'].items():
            if raw.get('status')=='unsupported_source':
                require(raw.get('stable') is False and any(r.get('score') is None for r in raw['eight']+raw['sixteen']),'unsupported source must remain explicit')
                stable=False
                continue
            actual=core.integration_stability(raw['eight'],raw['sixteen'])
            for key,value in actual.items():require(raw.get(key)==value,'changed raw8/16 approximation comparison')
            require({edge_key(r['edge']) for r in raw['eight']}=={edge_key(e) for e in prepared['graphs'][task]['edges']},'changed pilot graph')
            require(all(r['steps']==nodes and r['row_count']==16 for nodes,records in ((8,raw['eight']),(16,raw['sixteen'])) for r in records),'partial pilot integration/source coverage')
            stable=stable and actual['stable']
        require(report['stable']==stable,'pilot task stability flag differs from raw values')
        checks=pilot['native_checks'][task]
        require(checks['argmax_equal'] is True and math.isfinite(checks['max_readout_error']) and checks['max_readout_error']<=1e-5 and checks['parameters_frozen'] is True,'actual native readout/parameter checks missing')
        receivers=[]
        for kind in ('q','k','v','mlp_in','readout'):
            candidates=sorted({tuple(e['receiver']) for e in prepared['graphs'][task]['edges'] if e['receiver'][0]==kind})
            if candidates:receivers.append(candidates[0])
        require([tuple(r['receiver']) for r in checks['vjps']]==receivers,'incomplete native VJP kinds')
        require([tuple(r['receiver']) for r in checks.get('gradient_value_comparisons',[])]==receivers,'missing gradient-enabled inference agreement')
        for comparison in checks['gradient_value_comparisons']:
            require(math.isfinite(comparison['max_scaled_error']) and 0<=comparison['max_scaled_error']<=1 and comparison['expected_argmax']==comparison['observed_argmax'] and math.isclose(comparison['expected_margin'],comparison['observed_margin'],abs_tol=1e-5,rel_tol=1e-5),'raw gradient-enabled readout comparison failed')
        for row in checks['vjps']:
            require(math.isfinite(row['analytic']) and math.isfinite(row['finite_difference']) and math.isclose(row['analytic'],row['finite_difference'],abs_tol=5e-5,rel_tol=.02),'raw local VJP comparison failed')
    for reference in pilot['control_references'].values():
        require(reference==authority.object_reference(reference['path']),'changed actual pilot control bytes')
        validate_control(authority.read_object(reference['path']),design,identity)
    return pilot





def runtime_signature():
    import platform
    import importlib.metadata
    return dict(python=platform.python_version(),packages={name:importlib.metadata.version(name) for name in ('torch','transformers','numpy')},cuda_build=torch.version.cuda)





def cached_pilot_stability(model,design,task,graph,*,guard,root,identity,resume):
    ids=_membership(design,task,'validation')[:8]
    require(len(ids)==8,'eight fixed validation identities required')
    receivers=sorted({tuple(e['receiver']) for e in graph['edges']})
    keys=[[c,n,rid,stream,list(receiver)] for c in ('D','I') for n in (8,16) for rid in ids for stream in STREAMS for receiver in receivers]
    inventory=dict(kind='a3_edge_midpoint_cache',identity=identity,task=task,graph_sha256=digest(graph),expected_keys=keys)
    def produce(key):
        condition,nodes,rid,stream,receiver=key
        pair=_move(source_pair(design,task,'validation',rid,condition,stream,purpose='attribution'),model)
        edges=[e for e in graph['edges'] if tuple(e['receiver'])==tuple(receiver)]
        supported,missing=supported_edges(pair,edges)
        if supported:
            records,observed=observe_native_operation(model,lambda:core.attribute_edges(model,[pair],edges=supported,steps=nodes))
        else:records=[];observed=dict(forward_calls=0,backward_calls=0,seconds=0.)
        records.extend(dict(edge=e,score=None,supported=False,steps=nodes,row_count=0,token_count=0) for e in missing)
        return dict(records=records,observed=observed)
    chunks=execute(inventory,root,produce,guard=guard,resume=resume)
    reports={}
    for condition in ('D','I'):
        tables=[];missing_any=False
        for nodes in (8,16):
            totals={edge_key(e):0. for e in graph['edges']};tokens=dict.fromkeys(totals,0);rows=dict.fromkeys(totals,0);missing=set()
            for chunk in chunks:
                c,n,*_=chunk['key']
                if (c,n)!=(condition,nodes):continue
                for record in chunk['result']['records']:
                    key=edge_key(record['edge'])
                    if record['score'] is None:missing.add(key);continue
                    totals[key]+=record['score']/16;tokens[key]+=record['token_count'];rows[key]+=1
            missing_any=missing_any or bool(missing)
            tables.append([dict(edge=e,score=None if edge_key(e) in missing else totals[edge_key(e)],steps=nodes,
                row_count=rows[edge_key(e)],token_count=tokens[edge_key(e)],token_aggregation='sum within cell; paired16-row mean') for e in graph['edges']])
        comparison=dict(status='unsupported_source',stable=False,top16_overlap=None,normalized_l1=None) if missing_any else core.integration_stability(*tables)
        reports[condition]=dict(comparison,eight=tables[0],sixteen=tables[1])
    return dict(kind='a3_edge_stability',instance_ids=ids,split='validation',conditions=reports,stable=all(r['stable'] for r in reports.values()),
        cache_reference=authority.object_reference(Path(root)/'inventory'),continuation='explicit measured root16-only decision; no automatic retry or graph change; failed comparison retains full-claim block')





def validate_original_streams(design,parent):
    """Check every admitted split, ID, label and original stream byte against A1."""
    require(bool(design.get('injected'))==bool(parent.get('injected',design.get('injected'))),'changed original parent injection status')
    for task,rows in design['access_rows'].items():
        indexed={(condition,r['instance_id']):r for condition,values in parent['rows'][task].items() for r in values}
        require(len({(r['condition'],r['instance_id']) for r in rows})==len(rows),'duplicate admitted row identity')
        for row in rows:
            key=(row['condition'],row['instance_id']);require(key in indexed,'source row absent in authenticated A1 parent')
            original=indexed[key]
            for field,value in original.items():
                if field=='streams':
                    require(set(row['streams'])==set(value),'changed original source streams')
                    for stream,record in value.items():
                        require(all(row['streams'][stream].get(k)==v for k,v in record.items()),'changed original A1 prompt/token/readout/label bytes')
                elif field not in ('pressure','pressure_text','pressure_clause','request_text','question','designation_text','semantic_source'):
                    require(row.get(field)==value,'changed source ID/split/condition/provenance')
    return True


def source_rows_digest(design):
    fields=('tasks','access_rows','semantic_twin_maps','utility','ioi_validation','mmlu_validation','ioi_validation_maps','mmlu_validation_maps','selection_exclusion_ids')
    return digest({k:design.get(k) for k in fields})


def admit_parent_sources(design,*,registry_paths):
    """M0 replays the authenticated CPU producer; no model weights or new draw.

    Reconstructing the existing deterministic preparation proves semantic/source
    enrichment, complete eligible cohorts and utility rows. Runtime uses this
    immutable proof plus fresh original-parent/file/registry checks.
    """
    if design.get('injected') is True and not design.get('parent_evidence'):
        return dict(kind='a3_edge_source_admission',injected=True,source_sha256=source_rows_digest(design),scope='explicit software fixture; no production authority')
    from component_analysis import a3_pipeline
    from transformers import AutoTokenizer
    evidence=design['parent_evidence'];parent,selected,current=a3_pipeline.load_a1_parents(evidence['prepared_path'],evidence['selected_path'])
    require(current==evidence,'changed actual A1 parent evidence')
    validate_original_streams(design,parent)
    protocol=design['direction_protocol'];cfg=protocol['workload']
    settings={k:copy.deepcopy(cfg[k]) for k in ('microbatch_size','axis_tile_size','head_width','hidden_size','num_layers','vocabulary_size','dtype_bytes','hardware','warmup_batches','serialization_batches','finish_reserve_seconds','jobs')}
    settings.update(probe_max_bytes=protocol['fit_cache']['probe_max_bytes'],dtype=protocol['numeric_profile']['dtype'],backend=protocol['numeric_profile']['backend'])
    if 'axis_tile_sizes' in cfg:settings['axis_tile_sizes']=copy.deepcopy(cfg['axis_tile_sizes'])
    history=list(design['historical_source_hashes']);require(len(history)==1,'single frozen historical clause-head source required')
    tokenizer=AutoTokenizer.from_pretrained(parent['model'],revision=parent['tokenizer_revision'],local_files_only=True)
    rebuilt=a3_pipeline.prepare(a1_design=evidence['prepared_path'],a1_selected=evidence['selected_path'],matched_root=Path(design['matched_build_path']).parent,
        historical_csv=history[0],root_ruling=design['root_ruling'],tokenizer=tokenizer,registry_paths=list(registry_paths),output=None,
        a1_repo_root=design['a1_repo_root'],commit=protocol['commit'],execution_settings=settings)
    fields=('tasks','access_rows','semantic_twin_maps','utility','ioi_validation','mmlu_validation','ioi_validation_maps','mmlu_validation_maps','selection_exclusion_ids')
    require(all(design.get(k)==rebuilt.get(k) for k in fields),'A3 source/token/map/cohort differs from actual authenticated CPU preparation')
    return dict(kind='a3_edge_source_admission',injected=bool(design.get('injected')),source_sha256=source_rows_digest(design),
        parent_evidence=current,matched_build_file_sha256=common.file_hash(design['matched_build_path']),tokenizer_identity=parent['tokenizer_identity'],
        scope='actual original A1 rows and deterministic matched-source/tokenizer/semantic/utility producer replay; no model weights')





def validate_producer_jobs(receipt,ledger,identity):
    """Reconcile actual completed M1 jobs independently of producer flags."""
    if identity.get('injected'):return []
    entries={e['id']:e for e in ledger['entries']};observed={}
    for proof in receipt.get('guard_evidence',[]):
        reservation=proof.get('reservation',{}).get('reservation',{})
        rid=reservation.get('reservation_id');require(rid in entries,'measured producer job missing from actual RS ledger')
        entry=entries[rid];actual=entry['actual_entry']
        require(entry['phase']=='M1' and entry['subphase']=='edges' and entry['state']=='completed' and entry['actual_gpu_hours'] is not None,'actual successful completed edge calibration job required')
        require(all(actual.get(k)==reservation.get('actual_entry',{}).get(k) for k in authority.RESERVATION_FIELDS),'producer actual job/source/output identity differs')
        require(actual['source_commit']==identity['commit'] and Path(receipt['artifact_path']).resolve().is_relative_to(Path(actual['output_dir']).resolve()),'producer receipt outside actual source/output scope')
        observed[rid]=dict(reservation_id=rid,job_id=actual['job_id'],cluster=actual['cluster'],original_reserved_gpu_hours=entry['reserved_gpu_hours'],actual_gpu_hours=entry['actual_gpu_hours'])
    require(observed,'independently reconciled actual M1 producer evidence required')
    return list(observed.values())





def dry_run(args):
    """Static source/inventory check; never loads weights, CUDA or allocation."""
    require(Path(args.design).is_file(),'missing prepared design')
    try:design=_read_design(args.design)
    except (ValueError,KeyError,json.JSONDecodeError):
        raw=json.loads(Path(args.design).read_text())
        require(raw.get('injected') is True,'canonical authenticated A3 artifact required for production dry-run')
        result=dict(stage=args.stage,dry_run=True,model_loaded=False,writes=False,execution_authorized=False,
            source_admitted=False,input_class='explicit injected planning fixture',live_allocation_admission='deferred',
            required='canonical A3 source artifact and edge preparation before any production model access')
        print(json.dumps(result));return result
    require(design['direction_protocol']['commit']==args.commit,'dry-run execution commit differs from source')
    if args.stage=='prepare':
        prepared=prepare(design,_metadata_geometry(design,args),commit=args.commit,registry_paths=args.registry,output=None,design_path=args.design)
        result=dict(stage=args.stage,dry_run=True,source_admitted=True,graph_edges={t:len(g['edges']) for t,g in prepared['graphs'].items()})
    else:
        prepared=authority.read_object(args.prepared or Path(args.work_dir)/'prepared')
        validate_prepared(prepared,design,registry_paths=args.registry)
        result=dict(stage=args.stage,dry_run=True,source_admitted=True,prepared_sha256=prepared['prepared_sha256'])
    result.update(model_loaded=False,writes=False,execution_authorized=False,live_allocation_admission='deferred; actual current Slurm lease required for model work',
        required='original root admission/reservation, complete source-bound measured shapes and applicable control references')
    print(json.dumps(result));return result





def measurement_source_split(design,prepared,p,case):
    source=p['source']
    if source.startswith('H_bank:'):
        rows=prepared['bank_sources'][p['analysis_task']]['rows']
    elif source in ('ioi','mmlu'):
        rows=design[source+'_validation']
    else:rows=design['access_rows'][source]
    matching=[r for r in rows if r['instance_id']==case['instance_id'] and r['condition']==case['condition']]
    require(len(matching)==1,'ambiguous actual source split')
    return matching[0]['split']


if __name__=='__main__':main()
