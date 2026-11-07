"""Exact A3 mask operation inventory and measured-only cost proposals.

A proposal grants no execution authority. Root runtime admission validates live
RS reservations and always charges their original reserved GPU-hours.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math

SEEDS=(42,1,123)
ARMS=('constrained','unconstrained')
CONDITIONS=('D','I','H','F','user_neutral')


def require(value,message):
    if not value: raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def inventory_digest(inventory):
    return digest({k:v for k,v in inventory.items() if k!='inventory_sha256'})


def _keys(scope,chunk_size):
    keys=[]; fit=scope['tasks']['far_v2']['fit_ids']
    chunks=[fit[i:i+chunk_size] for i in range(0,len(fit),chunk_size)]
    for seed in SEEDS:
        for arm in ARMS:
            for condition in ('D','I','H'):
                for number,ids in enumerate(chunks):
                    for replay in (0,1):keys.append(['targets',seed,arm,condition,number,ids,replay])
            for update in range(1,201):
                for number,ids in enumerate(chunks):
                    for operation in ('D_no_grad','D_replay_backward','I_backward'):
                        keys.append(['update',seed,arm,update,number,ids,operation])
                keys.append(['regularizer_Adam',seed,arm,update])
                keys.append(['checkpoint',seed,arm,update])
                if update%20==0:
                    for condition in CONDITIONS:
                        for rid in scope['tasks']['far_v2']['selection_ids']:
                            for stream in ('clean','corrupt'):
                                for operation in ('primary','self_replay','all_sender_positive'):
                                    keys.append(['validation',seed,arm,update,condition,rid,stream,operation])
                    for rid in scope['ioi_validation']:
                        for operation in ('primary','self_replay','all_sender_positive'):
                            keys.append(['validation',seed,arm,update,'IOI',rid,'clean',operation])
                    for condition in ('D','I'):
                        for rid in fit:
                            for stream in ('clean','corrupt'):
                                for operation in ('dual_native_eval','export_hook_native_eval'):
                                    keys.append(['binary_parity',seed,arm,update,condition,rid,stream,operation])
                    keys.append(['validation_publication',seed,arm,update])
            keys.append(['selection',seed,arm,200])
    for task in sorted(scope.get('hbank_sources',{})):
        domain=scope['hbank_sources'][task]
        for rid in domain['ids']:
            for stream in ('clean','corrupt'):
                keys.append(['H_bank',task,rid,stream])
    # Every required A1 crossed operation remains on the exact assessment cohort.
    groups=['intact','all_candidates','New30']+[f'{arm}:{seed}:{control}' for seed in SEEDS for arm in ARMS for control in ('selected',)+tuple(f'random:{i}' for i in range(19))]
    for task in scope['task_order']:
        settings=scope['tasks'][task]
        for group in groups:
            if group=='New30' and task!='far_v2': continue
            for rid in settings['assessment_ids']:
                for condition in CONDITIONS:
                    for stream in ('clean','corrupt'):
                        for operation in ('item_swap','h_twin','zero','h_mean','self_replay','empty','positive_control'):
                            keys.append(['assessment',group,task,condition,rid,stream,operation])
            for rid in scope['ioi']:
                for operation in ('item_swap','zero','h_mean','self_replay','empty','positive_control'):
                    keys.append(['assessment',group,task,'IOI',rid,'clean',operation])
            for rid in scope['mmlu']:
                for operation in ('zero','h_mean','self_replay','empty','positive_control'):
                    keys.append(['assessment',group,task,'MMLU',rid,'clean',operation])
    return keys



def _pilot_keys(scope,chunk_size):
    ids=scope['tasks']['far_v2']['selection_ids'];keys=[]
    for arm in ARMS:
        for condition in ('D','I','H'):
            for rid in ids:
                for replay in (0,1):keys.append(['pilot_targets',arm,condition,rid,replay])
        for number in range(0,len(ids),chunk_size):
            for operation in ('D_no_grad','D_replay_backward','I_backward'):
                keys.append(['pilot_update',42,arm,1,number//chunk_size,ids[number:number+chunk_size],operation])
        for condition in CONDITIONS:
            for rid in ids:
                for stream in ('clean','corrupt'):
                    keys.append(['pilot_validation',arm,condition,rid,stream])
        for rid in scope['ioi_validation']:keys.append(['pilot_validation',arm,'IOI',rid,'clean'])
        keys.append(['pilot_regularizer_Adam',arm,1])
        keys.append(['pilot_checkpoint',arm,1])
        keys.append(['pilot_selection_restore_serialization',arm,1])
        for condition in ('D','I'):
            for rid in ids:keys.append(['pilot_binary_parity',arm,condition,rid])
    for task in scope['task_order']:
        settings=scope['tasks'][task]
        for rid in settings['selection_ids']:
            for stream in ('clean','corrupt'):keys.append(['pilot_H_bank',task,rid,stream])
        for condition in CONDITIONS:
            for rid in settings['selection_ids'][:100]:
                for stream in ('clean','corrupt'):
                    for operation in ('item_swap','h_twin','zero','h_mean','self_replay','empty','positive_control'):
                        keys.append(['pilot_assessment',task,condition,rid,stream,operation])
        for utility,ids,operations in [('IOI',scope['ioi_validation'],('item_swap','zero','h_mean','self_replay','empty','positive_control')),
                ('MMLU',scope['mmlu_validation'],('zero','h_mean','self_replay','empty','positive_control'))]:
            for rid in ids:
                for operation in operations:keys.append(['pilot_assessment',task,utility,rid,'clean',operation])
    keys.append(['pilot_complete_target_proof'])
    return keys

def build_inventory(design,*,identity,chunk_size,finish_reserve_seconds,hbank_sources=None,stage="full",widths=None,new30=None):
    require(type(chunk_size) is int and chunk_size>0,'invalid mask chunk size')
    require(math.isfinite(finish_reserve_seconds) and finish_reserve_seconds>0,'positive finish reserve required')
    scope=dict(tasks={t:{k:copy.deepcopy(v[k]) for k in ('fit_ids','selection_ids','assessment_ids')} for t,v in design['tasks'].items()},
        ioi_validation=[r['instance_id'] for r in design['ioi_validation']],
        mmlu_validation=[r['instance_id'] for r in design.get('mmlu_validation',[])],
        ioi=[r['instance_id'] for r in design['utility']['ioi']],mmlu=[r['instance_id'] for r in design['utility']['mmlu']])
    scope['task_order']=list(design['tasks'])
    scope['hbank_sources']=copy.deepcopy(hbank_sources or {})
    scope['widths']=copy.deepcopy(widths or {})
    scope['new30_reference']=copy.deepcopy(new30 or {'status':'not_frozen'})
    require(set(scope['tasks'])=={'far_v2','ser_v2','sdr_v2'},'complete FAR/SER/SDR scope required')
    require(stage in ('full','pilot'),'unknown mask inventory stage')
    result=dict(kind='a3_mask_inventory_v1',identity=copy.deepcopy(identity),phase='M1' if stage=='pilot' else 'M5',stage=stage,scope=scope,
        chunk_size=chunk_size,finish_reserve_seconds=finish_reserve_seconds,expected_keys=(_pilot_keys(scope,chunk_size) if stage=='pilot' else _keys(scope,chunk_size)),
        operation_accounting='explicit complete cohort updates and rows, including both D passes/I backward/Adam, every native validation/parity/publication and all crossed/utility/control cells',
        primitive_recipes=dict(targets='two dual native forwards per D/I/H chunk; detached readouts',
            update='D no-grad then identical D graph/backward plus I graph/backward; candidate regularizer and one Adam step',
            validation='primary score and self replay each use intact+donor+patched; positive uses intact+donor+patched all-sender readout; IOI duplicates clean only in physical execution',
            binary_parity='native dual eval versus donor+patched single-stream exported hooks',
            assessment='each supported cell: intact+donor+patched for interchange/replay/empty, intact+patched for zero/H-mean; one three-forward all-sender positive per row',
            checkpoint='hash intact base and complete safe gate/Adam/RNG boundary; largest10-record immutable validation-reference history',
            H_bank='one native forward per source stream, original unpadded token pooling, full numeric/base proof and immutable publication'),
        execution_jobs=dict(fit=6,assessment=3,assessment_policy='all groups for one task in a durable job; resume exact complete groups'),
        geometry=dict(mechanism_physical_batch=2*chunk_size,utility_primary_physical_batch=2,utility_execution_duplicate='clean only, excluded from scientific rows',
            H_bank_physical_batch=1,MMLU_positive_physical_batch=1))
    result['counts']=operation_counts(scope,chunk_size)
    result['storage_requirements']=storage_requirements(result)
    result['inventory_sha256']=inventory_digest(result)
    return result


def validate_inventory(inventory):
    require(inventory.get('kind')=='a3_mask_inventory_v1','mask inventory required')
    require(inventory.get('inventory_sha256')==inventory_digest(inventory),'changed mask inventory bytes')
    require(inventory['expected_keys']==(_pilot_keys(inventory['scope'],inventory['chunk_size']) if inventory['stage']=='pilot' else _keys(inventory['scope'],inventory['chunk_size'])),'incomplete/reordered mask operation inventory')
    require(inventory.get('counts')==operation_counts(inventory['scope'],inventory['chunk_size']),'incomplete operation prices')
    require(inventory.get('storage_requirements')==storage_requirements(inventory),'changed full target storage requirements')
    require(inventory['phase']==('M1' if inventory['stage']=='pilot' else 'M5'),'invalid mask phase')
    return inventory


def operation_counts(scope,chunk_size):
    groups={'far_v2':123,'ser_v2':122,'sdr_v2':122}
    counts=dict(guard_initial=9,base_proof=9,targets=6,update=1200,validation=60,binary_parity=60,checkpoint=1200,selection=6)
    for task,number in groups.items():
        counts['assessment:'+task]=number
        counts['H_bank:'+task]=2*len(scope.get('hbank_sources',{}).get(task,{}).get('ids',[]))
    counts['guard']=6*204+3*2+sum(counts['H_bank:'+t] for t in groups)+41*sum(groups.values())-9
    return counts


def storage_requirements(inventory):
    """Conservative full-retention bounds, independently of pilot cache size."""
    def host(value):
        # Deliberately count aliases repeatedly: completed JSON readers recreate them.
        if isinstance(value,dict):return 256+72*len(value)+sum(host(k)+host(v) for k,v in value.items())
        if isinstance(value,(list,tuple)):return 128+16*len(value)+sum(host(v) for v in value)
        if isinstance(value,str):return 128+8*len(value)
        return 128
    raw={k:v for k,v in inventory.items() if k not in ('storage_requirements','inventory_sha256')}
    metadata=len(json.dumps(raw,separators=(',',':')).encode())
    scope=inventory['scope'];counts=inventory['counts'];profile=inventory['identity'].get('numeric_profile',{})
    vocab=profile.get('vocab_size',128256)
    fit=len(scope['tasks']['far_v2']['fit_ids'])
    logits=2*fit*vocab*4
    widths=scope.get('widths',{}).get('far_v2',{})
    train_data=5*logits+2*fit*(17*sum(widths.get(c,1) for c in ('D','I','H'))+3*40)
    assessment_rows=sum(v for k,v in counts.items() if k.startswith('assessment:'))*(
        max(len(v['assessment_ids']) for v in scope['tasks'].values())*5*2*6+len(scope['ioi'])*5+len(scope['mmlu'])*4)
    validation_rows=60*(len(scope['tasks']['far_v2']['selection_ids'])*10+len(scope['ioi_validation']))
    # Each compact scalar row is bounded by its schema, support lists and hash references.
    row_bytes=4096+len(json.dumps(inventory['identity']).encode())
    rows=(assessment_rows+validation_rows)*row_bytes
    # Native snapshots include every hard-open gate tensor, never model weights.
    layers=profile.get('num_layers',32);hidden=profile.get('hidden_size',4096);intermediate=profile.get('intermediate_size',14336);heads=profile.get('num_heads',32)
    gate_elements=layers*(heads+2*hidden+intermediate+3)
    checkpoint_bound=gate_elements*16+65536+10*row_bytes
    checkpoints=1200*checkpoint_bound+6*65536
    banks=3*1056*4096*32+3*65536
    scratch=max(metadata,row_bytes*max(1,len(scope['tasks']['far_v2']['assessment_ids']))*70,10*row_bytes)
    return dict(schema='a3_mask_target_storage_bound_v1',tiers=dict(
        host_ram=host(raw)+logits+2*scratch,cache_disk=banks,output_disk=rows+checkpoints+metadata,
        scratch_disk=scratch),components=dict(target_I_logits=logits,target_fixed_GPU_data=train_data,binary_parity_logit_caches=4*logits,scientific_scalar_rows=rows,
        checkpoint_retention=checkpoints,native_gate_elements=gate_elements,H_banks=banks,metadata=metadata),
        policy='full source/row/inventory retention, all1200 boundaries, immutable validation artifacts and largest atomic publication; measured host peak added separately')


def project_cost(receipts,inventory,ledger):
    """Completed measured pilots yield a proposal; only root RS can authorize it."""
    validate_inventory(inventory)
    require(inventory['stage']=='full','full scientific inventory required for M5 cost proposal')
    require(inventory['scope']['new30_reference'].get('status')=='available','blocked: missing required New30 reference comparison')
    require(receipts,'completed measured mask pilots required')
    identity=inventory['identity'];measurements={};base_ids=[];startups=[];host_peak=0;gpu_peak=0;gpu_capacity=[];boundaries=[]
    for receipt in receipts:
        require(receipt.get('kind')=='a3_mask_pilot_v2' and receipt.get('complete') is True and receipt.get('exit_code')==0
            and receipt.get('identity')==identity and receipt.get('injected') is False,'failed/stale/injected/unbound mask pilot')
        completed=[entry for entry in ledger['entries'] if entry['id']==receipt.get('reservation_id')]
        require(len(completed)==1 and completed[0]['state']=='completed' and completed[0]['phase']=='M1' and completed[0]['subphase']=='masks',
            'failed/unreconciled/non-mask pilot reservation cannot admit scientific work')
        actual=completed[0]['actual_entry']
        require(str(actual['job_id'])==str(receipt.get('allocation_job_id')) and actual['source_commit']==identity['commit']
            and actual['output_dir']==receipt.get('output_dir') and completed[0]['inventory_sha256']==receipt.get('pilot_inventory_sha256'),
            'pilot receipt is not linked to its actual completed source-bound RS reservation')
        require('H200' in receipt.get('hardware','') and receipt.get('arms')==list(ARMS),'both objective arms on H200 required')
        require(receipt.get('purpose')=='validation_timing' and receipt.get('timing_only') is True and receipt.get('final') is False
            and receipt.get('validation_measured') is True and receipt.get('two_D_passes_measured') is True,'complete disposable timing purpose required')
        require(receipt.get('widths')==inventory['scope']['widths'],'changed measured/target physical profile')
        require({a['arm'] for a in receipt.get('arm_measurements',[])}==set(ARMS)
            and all(a['source_split']=='validation' and a['purpose']=='validation_timing' and a['chunks']>0 for a in receipt['arm_measurements']),
            'actual full validation-only objective-arm coverage required')
        require(receipt.get('target_inventory_sha256')==inventory['inventory_sha256'],'pilot is not bound to exact complete target inventory')
        require(isinstance(receipt.get('base_identity'),str) and len(receipt['base_identity'])==64,'actual measured model hash required')
        base_ids.append(receipt['base_identity'])
        startups.append(receipt['startup_seconds']);host_peak=max(host_peak,receipt['host_peak_bytes'])
        gpu_peak=max(gpu_peak,receipt['peak_memory_bytes']);gpu_capacity.append(receipt['gpu_capacity_bytes']);boundaries.append(receipt['boundary_bytes'])
        for operation,samples in receipt['measurements'].items():
            require(isinstance(samples,list) and samples,'actual measured operation samples required')
            for sample in samples:
                require(math.isfinite(sample['seconds']) and sample['seconds']>0 and type(sample['rows']) is int and sample['rows']>0,'invalid timing or row count')
                require(sample.get('numeric_profile')==identity['numeric_profile'] and sample.get('widths')==inventory['scope']['widths']
                    and sample.get('source_split')=='validation','changed measured numeric/source profile')
                measurements.setdefault(operation,[]).append(sample)
    require(all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in startups+[host_peak,gpu_peak]+gpu_capacity+boundaries),'nonfinite startup/memory/storage observation')
    require(len(set(base_ids))==1,'changed model computation between pilots')
    counts=inventory['counts'];require(set(counts)<=set(measurements),'missing measured bank/control/transfer/validation/checkpoint classes')
    scope=inventory['scope'];fit_chunks=math.ceil(len(scope['tasks']['far_v2']['fit_ids'])/inventory['chunk_size'])
    val_chunks=math.ceil(len(scope['tasks']['far_v2']['selection_ids'])/inventory['chunk_size'])
    require(fit_chunks>0 and val_chunks>0,'complete fit/validation cohorts required')
    require(len(scope['tasks']['far_v2']['fit_ids'])%inventory['chunk_size']==0
        and len(scope['tasks']['far_v2']['selection_ids'])%inventory['chunk_size']==0,
        'unmeasured partial physical chunk; freeze a compatible chunk size or extend exact-shape pilot')
    prices={}
    for operation,count in counts.items():
        samples=measurements[operation]
        if operation in ('targets','update','binary_parity','selection'):
            factor=max(1,len(scope['tasks']['far_v2']['fit_ids'])/len(scope['tasks']['far_v2']['selection_ids'])) if operation=='update' else 1
            # The reviewed update rehashes the entire cohort per callback.
            prices[operation]=max(s['seconds']*max(1,fit_chunks/s['rows'])*factor for s in samples)*count
        elif operation=='checkpoint':
            factor=max(1,len(scope['tasks']['far_v2']['fit_ids'])/len(scope['tasks']['far_v2']['selection_ids']))
            prices[operation]=max(s['seconds'] for s in samples)*factor*count
        elif operation.startswith('H_bank:'):
            prices[operation]=max(s['seconds']*max(1,count/s['rows']) for s in samples)
        elif operation.startswith('assessment:'):
            task=operation.split(':',1)[1]
            factor=max(1,len(scope['tasks'][task]['assessment_ids'])/min(100,len(scope['tasks'][task]['selection_ids'])))
            prices[operation]=max(s['seconds'] for s in samples)*factor*count
        else:prices[operation]=max(s['seconds'] for s in samples)*count
    # Six independent fits plus one durable all-group assessment job per source task.
    repeat=prices['guard']/counts['guard'];initial=prices['guard_initial']/9;base=prices['base_proof']/9
    job_proposals=[]
    fit_work=base+initial+203*repeat+math.fsum(prices[k]/6 for k in ('targets','update','validation','binary_parity','checkpoint','selection'))
    for seed in SEEDS:
        for arm in ARMS:
            seconds=max(startups)+1.25*fit_work+inventory['finish_reserve_seconds']
            minutes=math.ceil(seconds/60)
            job_proposals.append(dict(stage='fit',seed=seed,arm=arm,seconds=seconds,requested_minutes=minutes,reserved_gpu_hours=round(minutes/60,4)))
    for task in scope['task_order']:
        guards=1+counts['H_bank:'+task]+41*counts['assessment:'+task]
        work=base+initial+guards*repeat+prices['H_bank:'+task]+prices['assessment:'+task]
        seconds=max(startups)+1.25*work+inventory['finish_reserve_seconds'];minutes=math.ceil(seconds/60)
        job_proposals.append(dict(stage='assess',task=task,group='all',seconds=seconds,requested_minutes=minutes,reserved_gpu_hours=round(minutes/60,4)))
    seconds=math.fsum(j['seconds'] for j in job_proposals)
    require(math.isfinite(seconds),'nonfinite full cost proposal')
    from component_analysis.a3_direction_workload import _ledger,_storage_admission
    sums=_ledger(ledger,identity)
    storage=_storage_admission(inventory,ledger,measured_host_peak=host_peak)
    target_data=inventory['storage_requirements']['components']['target_fixed_GPU_data']
    pilot_data=target_data*len(scope['tasks']['far_v2']['selection_ids'])/len(scope['tasks']['far_v2']['fit_ids'])
    needed_gpu=gpu_peak+max(0,target_data-pilot_data)
    require(gpu_capacity and min(gpu_capacity)>=needed_gpu,'full target GPU-memory capacity underflow')
    require(max(boundaries)*1200<=inventory['storage_requirements']['components']['checkpoint_retention'],'checkpoint storage schema bound exceeded')
    entries=ledger['entries'];m5=sum(e['reserved_gpu_hours'] for e in entries if e.get('phase')=='M5' and e.get('subphase')=='masks')
    m1=sum(e['reserved_gpu_hours'] for e in entries if e.get('phase')=='M1' and e.get('subphase')=='masks')
    hours=math.fsum(j['reserved_gpu_hours'] for j in job_proposals)
    require(m5+hours<=10 and m1<=.75+sums['mask_retry_gpu_hours'] and sums['M1']<=2+sums['mask_retry_gpu_hours'] and sums['all']+hours+sums['contingency_remaining']<=40,
        'original reserved-hour milestone/global cap exceeded')
    return dict(kind='a3_mask_cost_proposal_v2',identity=identity,inventory_sha256=inventory['inventory_sha256'],
        requested_seconds=seconds,requested_gpu_hours=hours,execution_authorized=False,counts=counts,operation_seconds=prices,
        storage_admission=storage,GPU=dict(required_bytes=needed_gpu,available_bytes=min(gpu_capacity)),
        measured_base_identity=base_ids[0],jobs=9,job_proposals=job_proposals,reuse_policy='frozen right-padded shapes; at least one measured cohort with exact count ratios and extra whole-cohort hash factor; union-support inference; fixed25percent buffer; every job rounded to requested minutes',
        accounting='M1 and M5 additive; every reservation keeps its original reserved hours; actual spend separate')
