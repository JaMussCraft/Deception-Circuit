"""Exact serial edge profiles, scientific coverage and measured cost/capacity.

Physical work is distinct from scientific slots: three bootstrap rankings reuse
one immutable attribution cache, and duplicate learned/null memberships reuse
one exact panel. Every alias remains in coverage. No reservations are written.
Receipts are pure inputs here; production loads byte-complete producer objects
and binds their references through independently anchored root admission.
"""
from __future__ import annotations
import copy
import math
from collections import defaultdict
from component_analysis.a3_edge_pipeline import (
    digest,require,SEEDS,CONDITIONS,STREAMS,edge_key,source_width,
    _membership,_row,supported_edges,source_pair,rank_edges,ancestral_bank_sources,
)


def canonical(edges):
    return sorted(copy.deepcopy(edges),key=edge_key)


def profile(identity,operation,task,source,width,*,edges=(),condition=None,steps=0):
    numeric=identity.get('numeric_profile') or {}
    return dict(operation=operation,analysis_task=task,source=source,padded_width=width,
        physical_batch_size=1,mask_class='right padded by at least one masked token; own readout retained',dtype=numeric.get('dtype','unspecified'),
        backend=numeric.get('backend','unspecified'),edges=canonical(edges),condition=condition,
        integration_nodes=steps,source_identity_sha256=digest(identity))


def _candidate_sets(design,graphs,stage,fit,selected,identity):
    sets={t:[] for t in design['tasks']};aliases=[];blocked=[]
    if stage=='select':
        require(fit and fit.get('kind')=='a3_edge_fit_complete' and fit.get('complete'),'completed fit required to freeze exact validation workload')
        require(fit.get('identity')==identity and set(fit['tasks'])==set(design['tasks']),'stale/incomplete fit inventory ancestry')
        for task,item in fit['tasks'].items():
            require([r['seed'] for r in item['fits']]==list(SEEDS),'three fit seeds required')
            for row in item['fits']:
                for condition in ('D','I'):
                    records=row['rankings'][condition]
                    if any(x.get('supported') is False for x in records):
                        blocked.append([task,row['seed'],condition]);continue
                    ordered=rank_edges(records,graphs[task]['edges'])
                    for budget in (1,4,16):
                        if len(ordered)<budget:continue
                        members=canonical(ordered[:budget]);key=digest(members)
                        if not any(x['set_id']==key for x in sets[task]):sets[task].append(dict(set_id=key,edges=members))
                        aliases.append(dict(task=task,seed=row['seed'],ranking_condition=condition,budget=budget,set_id=key))
    elif stage=='assess':
        require(selected and selected.get('kind')=='a3_edge_selection_complete' and selected.get('complete'),'completed selection required before assessment inventory')
        require(selected.get('identity')==identity and set(selected['tasks'])==set(design['tasks']),'stale/incomplete selection inventory ancestry')
        from component_analysis.a3_edge_pipeline import validate_selection
        for task,item in selected['tasks'].items():
            validate_selection(item,graphs[task])
            for family in item['families']:
                if family['status']=='blocked':
                    blocked.append([task,family['seed'],family['ranking_condition']]);continue
                for index,members in enumerate([family['edges']]+family['nulls']['sets']):
                    members=canonical(members);key=digest(members)
                    if not any(x['set_id']==key for x in sets[task]):sets[task].append(dict(set_id=key,edges=members))
                    aliases.append(dict(task=task,seed=family['seed'],ranking_condition=family['ranking_condition'],null_index=index,set_id=key))
    return sets,aliases,blocked


def _physical_requirements(design,graphs,stage,identity,steps,sets,banks):
    collected={}
    def add(p,count,token_bound=1):
        if count<=0:return
        key=digest(p)
        if key not in collected:collected[key]=dict(profile_id=key,profile=p,count=0,token_bound=0)
        collected[key]['count']+=count
        collected[key]['token_bound']=max(collected[key]['token_bound'],token_bound)
    if stage in ('fit','select','pilot'):
        split='train' if stage=='fit' else 'validation'
        for task,graph in graphs.items():
            ids=_membership(design,task,split)
            if stage=='pilot':
                require(len(ids)>=8,'eight fixed validation identities required for pilot')
                ids=ids[:8]
            for condition in ('D','I'):
                for rid in ids:
                    for stream in STREAMS:
                        pair=source_pair(design,task,split,rid,condition,stream,purpose='attribution')
                        supported,_=supported_edges(pair,graph['edges'])
                        for receiver in sorted({tuple(e['receiver']) for e in supported}):
                            edges=[e for e in supported if tuple(e['receiver'])==receiver]
                            tokens=sum(len(pair['batch']['positions'][e['position']][0]) for e in edges)
                            for nodes in ((8,16) if stage=='pilot' else (steps,)):
                                add(profile(identity,'attribute_receiver',task,task,source_width(design,task),edges=edges,condition=condition,steps=nodes),1,tokens)
    if stage in ('select','assess'):
        split='validation' if stage=='select' else 'test'
        for task,items in sets.items():
            for item in items:
                edges=item['edges'];ids=_membership(design,task,split)
                for condition in CONDITIONS:
                    count=0;bound=0
                    for rid in ids:
                        for stream in STREAMS:
                            pair=source_pair(design,task,split,rid,condition,stream,purpose='validation' if split=='validation' else 'assessment')
                            _,missing=supported_edges(pair,edges)
                            if not missing:
                                count+=1;bound=max(bound,sum(len(pair['batch']['positions'][e['position']][0]) for e in edges))
                    add(profile(identity,'exact_mechanism',task,task,source_width(design,task),edges=edges,condition=condition),count,bound)
                if all(e['position_spec']['semantic_bin']=='assistant_readout' for e in edges):
                    utility=design if split=='validation' else design['utility']
                    for source,operation in (('ioi','IOI'),('mmlu','MMLU_floors')):
                        rows=utility.get(source+'_validation',[]) if split=='validation' else utility.get(source,[])
                        if rows:add(profile(identity,operation,task,source,source_width(design,source),edges=edges,condition=source.upper()),len(rows),len(edges))
            # One complete sender-union bank per native profile. No archived
            # coordinates and no train-only/readout-only bank substitution.
            if items and (design.get('mmlu_validation') if split=='validation' else design['utility'].get('mmlu')):
                rows=banks[task]['rows'];width=1+max(len(s['tokens']) for r in rows for s in r['streams'].values())
                add(profile(identity,'H_bank',task,'H_bank:'+task,width,edges=graphs[task]['edges'],condition='H'),2*len(rows),max(len(s['tokens']) for r in rows for s in r['streams'].values()))
    return sorted(collected.values(),key=lambda r:r['profile_id'])


def freeze_inventory(design,graphs,*,stage,identity,steps=8,bank_sources=None,fit=None,selected=None,measurement_target=None):
    require(stage in ('pilot','fit','select','assess'),'unsupported inventory stage')
    require(steps in (8,16),'frozen gradient nodes required')
    banks=bank_sources or ancestral_bank_sources(design)
    sets,aliases,blocked=_candidate_sets(design,graphs,stage,fit,selected,identity)
    tasks={task:dict(fit_ids=list(s['fit_ids']),selection_ids=list(s['selection_ids']),assessment_ids=list(s['assessment_ids']),
        edge_keys=[[list(e['sender']),list(e['receiver']),e['position']] for e in graphs[task]['edges']],
        source_sha256=graphs[task]['source_sha256'],padded_width=source_width(design,task),bank_source_ids=banks[task]['source_ids'],bank_source_sha256=banks[task]['source_sha256']) for task,s in design['tasks'].items()}
    requirements=_physical_requirements(design,graphs,stage,identity,steps,sets,banks)
    geometry=design.get('direction_protocol',{}).get('workload',{})
    numeric=identity.get('numeric_profile') or {}
    body=dict(kind='a3_edge_inventory_v2',stage=stage,phase='M1' if stage=='pilot' else 'M4',identity=copy.deepcopy(identity),
        seeds=list(SEEDS),null_count=19,budgets=[1,4,16],steps=steps,gradient_nodes=[8,16],tasks=tasks,
        sets=sets,aliases=aliases,blocked_families=blocked,requirements=requirements,
        hidden_size=geometry.get('hidden_size'),vocabulary_size=geometry.get('vocabulary_size'),dtype_bytes=geometry.get('dtype_bytes'),
        model_loads=2 if stage=='pilot' else 1,finish_reserve_seconds=300,
        reuse_policy='same frozen source/receiver/sender/operation/width/dtype/backend; serial batch1; measured same-hardware validation; conservative token-occupancy scaling',
        bank_policy='exact ancestral A1 H train+validation IDs; both streams; all unpadded tokens; fp32 mean of native additive contributions',
        source_bytes=len(__import__('json').dumps(design,sort_keys=True).encode()),
        bank_source_bytes=sum(len(__import__('json').dumps(b,sort_keys=True).encode()) for b in banks.values()))
    body['input_fit_sha256']=digest(fit) if fit is not None else None
    body['input_selection_sha256']=digest(selected) if selected is not None else None
    if stage=='pilot':
        from component_analysis.a3_edge_pipeline import pilot_source_cases
        cases=pilot_source_cases(design)
        receivers={t:sorted({tuple(e['receiver']) for e in g['edges']}) for t,g in graphs.items()}
        vjp_counts={t:len({r[0] for r in values}) for t,values in receivers.items()}
        body['control_inventory']=dict(independent_inference_cases=cases,ordinary_inference_forwards=len(cases),native_value_forwards=len(cases),model_loads=2,
            local_vjp_backward_calls=sum(vjp_counts.values()),local_value_and_fd_forwards=sum(1+3*v for v in vjp_counts.values()),
            complete_toy_endpoint=dict(count=1,scope='complete analytic CPU software control only'),
            serial_geometry=dict(physical_batch_size=1,packed=False),
            midpoint_checkpoint_cells=sum(2*2*8*2*len(r) for r in receivers.values()))
        body['measurement_target']=copy.deepcopy(measurement_target)
        if measurement_target is not None:
            validate_inventory(measurement_target)
            require(measurement_target['identity']==identity,'pilot target source identity differs')
            body['control_inventory']['profile_benchmark_calls']=len(measurement_target['requirements'])
            body['control_inventory']['profile_shapes']=[r['profile_id'] for r in measurement_target['requirements']]
            body['control_inventory']['paired_bootstrap_calibrations']=measurement_target['overhead']['cpu_summaries']>0
    body['expected_keys']=_keys(body)
    body['overhead']=_overhead(body)
    body['storage_requirements']=_storage_requirements(body['overhead'])
    body['inventory_sha256']=digest(body)
    return body


def _keys(inv):
    keys=[]
    if inv['stage'] in ('fit','pilot'):
        for task,s in sorted(inv['tasks'].items()):
            ids=s['fit_ids'] if inv['stage']=='fit' else s['selection_ids'][:8]
            for seed in SEEDS if inv['stage']=='fit' else (None,):
                keys.extend([task,seed,c,rid,stream] for c in ('D','I') for rid in ids for stream in STREAMS)
    elif inv['stage']=='select':
        for row in inv['aliases']:keys.append([row['task'],row['seed'],row['ranking_condition'],row['budget']])
    else:
        for row in inv['aliases']:keys.append([row['task'],row['seed'],row['ranking_condition'],row['null_index']])
    return keys or [['blocked',inv['stage']]]


def _overhead(inv):
    calls=sum(r['count'] for r in inv['requirements']);unique_sets=sum(len(v) for v in inv['sets'].values())
    publications=(calls if inv['stage']=='fit' else unique_sets+len(inv['expected_keys']))+len(inv['tasks'])+4
    # Bounds derive from the declared scalar-cache schemas and actual edge/ID
    # byte lengths.32 bytes bounds each finite JSON float; token/hidden arrays
    # are counted separately. This is capacity planning, not measured cache size.
    edge_bytes=sum(len(__import__('json').dumps(s['edge_keys'])) for s in inv['tasks'].values())
    numeric_rows=calls+unique_sets*164
    scalar_bytes=(numeric_rows*(edge_bytes+4096)+inv['source_bytes']+inv['bank_source_bytes']+
        len(__import__('json').dumps({k:v for k,v in inv.items() if k not in ('overhead','storage_requirements','inventory_sha256')},sort_keys=True).encode())*2)
    hidden=inv.get('hidden_size') or 0
    bank_bytes=sum(len(s['edge_keys']) for s in inv['tasks'].values())*hidden*32
    return dict(refreshes=calls+publications+4,publications=publications,scalar_rows=numeric_rows,
        serialization_bytes=scalar_bytes+bank_bytes,host_retained_bytes=2*(scalar_bytes+bank_bytes),
        disk_peak_bytes=2*(scalar_bytes+bank_bytes),cpu_summaries=unique_sets)


def validate_inventory(inv):
    require(inv.get('kind')=='a3_edge_inventory_v2' and inv.get('seeds')==list(SEEDS) and inv.get('null_count')==19 and inv.get('budgets')==[1,4,16] and inv.get('gradient_nodes')==[8,16],'incomplete edge science inventory')
    require(inv['expected_keys']==_keys(inv),'incomplete exact inventory coverage')
    if inv['stage']=='pilot':
        controls=inv.get('control_inventory',{})
        cases=controls.get('independent_inference_cases',[])
        require(cases and controls.get('ordinary_inference_forwards')==len(cases) and controls.get('native_value_forwards')==len(cases) and controls.get('model_loads')==2 and controls.get('serial_geometry')=={'physical_batch_size':1,'packed':False},'incomplete actual pilot control/geometry inventory')
        if inv.get('measurement_target') is not None:
            validate_inventory(inv['measurement_target'])
            require(controls.get('profile_shapes')==[r['profile_id'] for r in inv['measurement_target']['requirements']],'changed pilot benchmark shape scope')
    require(inv['overhead']==_overhead({k:v for k,v in inv.items() if k not in ('inventory_sha256','overhead','storage_requirements')}),'changed checkpoint/storage/overhead inventory')
    require(inv.get('storage_requirements')==_storage_requirements(inv['overhead']),'changed full target storage tiers')
    require(inv['inventory_sha256']==digest({k:v for k,v in inv.items() if k!='inventory_sha256'}),'changed edge inventory hash')
    require(all(r['profile_id']==digest(r['profile']) and type(r['count']) is int and r['count']>0 and r['token_bound']>0 for r in inv['requirements']),'incomplete physical operation profiles')
    return inv


def _finite(value,name,positive=False):
    require(type(value) in (int,float) and math.isfinite(value) and value>0 if positive else type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid measured '+name)
    return float(value)


def project_cost(inv,receipts,*,capacities=None):
    validate_inventory(inv);require(receipts,'measured edge producer receipts required')
    require(all(type(inv.get(k)) is int and inv[k]>0 for k in ('hidden_size','vocabulary_size','dtype_bytes')),'full native geometry required for capacity admission')
    require(isinstance(capacities,dict) and capacities,'fresh independent host/disk capacity required')
    measured={};startup=[];guards=[];serialization=[];cpu=[];host=[];gpu=[]
    for receipt in receipts:
        require(receipt.get('kind')=='a3_edge_measurements_v1' and receipt.get('producer')=='a3_edge_pipeline' and receipt.get('complete') is True and receipt.get('exit_state')=='completed' and receipt.get('identity')==inv['identity'],'actual complete source-bound producer receipts required')
        require(receipt.get('injected')==bool(inv['identity'].get('injected')),'injected measurement identity mismatch')
        runtime=receipt.get('runtime',{})
        require(runtime.get('geometry',{}).get('hidden_size')==inv['hidden_size'] and runtime.get('vocabulary_size')==inv['vocabulary_size'] and runtime.get('dtype_bytes')==inv['dtype_bytes'],'measured actual model geometry/dtype differs from target capacity inventory')
        require(receipt.get('code_hashes')==inv['identity'].get('code_hashes',receipt.get('code_hashes')),'changed producer source closure')
        require(inv['identity'].get('injected') or ('H200' in receipt.get('hardware','') and receipt.get('startup_measured') is True),'same-H200 actual startup measurement required')
        startup.append(_finite(receipt['startup_seconds'],'startup_seconds'))
        guards.extend(_finite(v,'authority refresh') for v in receipt['guard_seconds'])
        serialization.append(receipt['serialization']);cpu.append(receipt['cpu_summary'])
        host.append(_finite(receipt['host_peak_bytes'],'host_peak_bytes',True))
        for m in receipt['measurements']:
            require(m['profile_id']==digest(m['profile']) and m.get('analysis_split')=='validation' and m['source_cases'] and m['input_hashes'],'real validation-only shape/input producer evidence required')
            require(m['profile']['physical_batch_size']==1,'serial batch1 timing required')
            samples=[_finite(x,'batch seconds',True) for x in m['batch_seconds']]
            require(samples and len(samples)==len(m['source_cases'])==len(m['input_hashes']),'timing/source scope mismatch')
            require(m['forward_calls']>=1 and m['backward_calls']>= (m['profile']['integration_nodes'] if m['profile']['operation']=='attribute_receiver' else 0),'missing actual native forward/VJP measurements')
            require(m['tokens_measured']>0 and m['peak_reserved_bytes']<=m['device_available_bytes'],'measured shape exceeds device capacity')
            if m['profile_id'] not in measured or max(samples)>max(measured[m['profile_id']]['batch_seconds']):measured[m['profile_id']]=m
            gpu.append(m['peak_reserved_bytes'])
    require(guards and serialization and cpu,'missing actual refresh/storage/checkpoint/CPU overhead')
    missing=[r['profile_id'] for r in inv['requirements'] if r['profile_id'] not in measured]
    require(not missing,'missing measured serial shape profiles: '+str(missing))
    compute=0
    for requirement in inv['requirements']:
        actual=measured[requirement['profile_id']]
        require(actual['profile']==requirement['profile'],'changed sender/receiver/bin/nodes/width/runtime profile')
        factor=max(1.,requirement['token_bound']/actual['tokens_measured'])
        compute+=requirement['count']*max(actual['batch_seconds'])*factor
    storage_seconds=max(_finite(r['seconds'],'serialization seconds',True)/_finite(r['bytes'],'actual serialized bytes',True) for r in serialization)*inv['overhead']['serialization_bytes']+max(r['seconds'] for r in serialization)*inv['overhead']['publications']
    cpu_seconds=max(_finite(r['seconds'],'CPU summary seconds',True)/_finite(r['rows'],'CPU summary rows',True) for r in cpu)*inv['overhead']['scalar_rows']
    refresh=max(guards)*inv['overhead']['refreshes']
    host_needed=max(host)+inv['overhead']['host_retained_bytes']
    capacity_report=_capacity(inv,capacities,max(host))
    seconds=inv['model_loads']*max(startup)+1.25*(compute+storage_seconds+cpu_seconds+refresh)+inv['finish_reserve_seconds']
    ceiling=.75 if inv['phase']=='M1' else 9
    require(seconds/3600<=ceiling,'complete edge inventory exceeds phase ceiling')
    return dict(kind='a3_edge_cost_proposal',inventory_sha256=inv['inventory_sha256'],complete=True,seconds=seconds,gpu_hours=seconds/3600,
        compute_seconds=compute,serialization_seconds=storage_seconds,cpu_summary_seconds=cpu_seconds,refresh_seconds=refresh,
        host_peak_bound_bytes=host_needed,disk_peak_bound_bytes=inv['overhead']['disk_peak_bytes'],gpu_peak_reserved_bytes=max(gpu,default=0),
        source_profile_count=len(inv['requirements']),scientific_slots=len(inv['expected_keys']),unique_exact_sets=sum(len(v) for v in inv['sets'].values()),
        capacity=capacity_report,authority=False,extrapolation='max measured same-profile validation time; conservative token occupancy;25% workload buffer; measured startup and fixed finish reserve')


def _storage_requirements(overhead):
    size=overhead['serialization_bytes']
    return dict(tiers=dict(host_ram=overhead['host_retained_bytes'],cache_disk=size,output_disk=size,scratch_disk=size),
        components=dict(authority_key_proof_host_bytes=0),policy='complete source-derived scalar caches, full-union bank, aliases, immutable rows plus atomic temporary publication; no saved vocabulary arrays')


def _capacity(inv,capacities,host_peak):
    required=dict(inv['storage_requirements']['tiers']);required['host_ram']+=host_peak
    if inv['identity'].get('injected') and 'host_bytes' in capacities:
        require(required['host_ram']<=capacities['host_bytes'] and sum(v for k,v in required.items() if k!='host_ram')<=capacities.get('disk_bytes',0),'complete inventory exceeds fresh host/disk capacity')
        return dict(required=required,injected_capacity_adapter=True)
    pools={};available={}
    for tier,need in required.items():
        cap=capacities.get(tier,{})
        require(isinstance(cap.get('pool'),str) and cap['pool'] and type(cap.get('available_bytes')) is int and cap['available_bytes']>=0,'fresh named physical storage pool capacity required')
        pool=cap['pool'];pools[pool]=pools.get(pool,0)+need;available[pool]=min(available.get(pool,cap['available_bytes']),cap['available_bytes'])
    require(all(pools[p]<=available[p] for p in pools),'complete inventory exceeds fresh host/disk shared-pool capacity')
    return dict(required=required,pool_required=pools,pool_available=available)
