"""Pure, exact direction inventories and read-only measured-cost admission.

The canonical direction protocol must additionally freeze ``workload`` before
model access: microbatch_size, axis_tile_size, widths[task][analysis_split],
hardware, head_width, hidden_size, vocabulary_size, dtype_bytes, finish_reserve_seconds,
warmup_batches, serialization_batches, jobs; dtype/backend come from its
numeric_profile. Widths include positive-control donor padding. No shape fallback
or inferred device-speed ratio exists. Injected small designs remain explicit.

Inventory requirements name each operation/profile, deterministic batch count,
target row scope, validation timing scope and axis scope. Each scoring tile costs
five forwards in the reviewed runner; positive calibration costs three singleton
forwards per recipient, never a microbatch division. A job is one startup plus
its assigned requirement counts and finish reserve. ``jobs`` partitions shards
round-robin; warmup and actual capture/shard/control/completion serialization
work are explicit per job. Serialization shape IDs and one observed timing per
payload shape are mandatory; serialization_batches only adds extra finalization
work and cannot remove required publications. Each pilot
part is one atomic timing job. Optional axis_tile_sizes maps individual stages
to separately frozen tiles. Short target chunks receive their own validation
profile; a physical target batch larger than the timing cohort blocks.

Receipts: kind=a3_direction_timing_v1, completed/exit_code=0/complete=True,
identity, hardware, inventory_sha256, startup_seconds, measurements. Each
measurement has profile, operation, batch_seconds (synchronized observed samples),
expected_keys/observed_keys (actual validation scope), axis_ids, source_split,
synchronized, timing_inputs, donor_convention, axis_scope, cache_fit and numeric
memory/cache capacities, cache_bytes, peak_allocated_bytes, peak_reserved_bytes.
Receipts also require measured host_peak_bytes; this is added to independently
bounded target host retention, rather than treating GPU memory as host capacity.
Packed measurements reference packing_evidence[packing_id], wrapping the
accepted runner_receipt and exact per-batch recipient-digest snapshots. Complete
coverage and timing-vs-target reuse are checked independently. Packed proposals
remain conditional until Unit F provides a separately reviewed reuse adapter;
the runner continues to demand exact measured input/map/axis scope. Hashes are content
integrity, not proof of measurement; callers must load completed byte-checked
artifacts through the accepted artifact reader before passing these dictionaries.

Ledger: root snapshot identity/current digest/age, entries with unique id,
phase, subphase, state and actual or reserved GPU hours, expected_entry_ids,
contingency_gpu_hours, expected_identity. EVERY entry charges reserved_gpu_hours
in every state, including completed/failed; unused reservations are not refunded.
Actual GPU hours are validated/reported separately, never used as cap credit. The expected-entry manifest is supplied
by root's fresh ledger reader, not inferred from surviving receipts. This module
never writes reservations or authorizes execution; admission is a proposal.
Postfit normalized input references a separately hashed fit_validation_envelope
(kind a3_fit_validation_envelope_v1, identity, upper_inventory, max_gpu_hours,
entry_ids, envelope_sha256). This is not a change to RS ledger.json. Completed
capture reservations reduce this envelope before later validation jobs are proposed.
The fresh root reader independently loads original_admissions and normalized
reservation_lineage records from completed admission/reservation artifacts; an
envelope self-hash is not authorization. Original source, upper inventory,
ceiling, nonempty anchor IDs and every consumed/active reservation must agree.

Full storage_requirements are independently derived from frozen target data,
not pilot cache bytes. Fresh root storage_capacities supplies each tier
{pool,available_bytes}; tiers sharing one physical pool are summed. Host object
retention, source text/tokens, numeric arrays/projections, optional summaries,
complete outcome/control rows, manifests and atomic temporary publications are
bounded separately. Measured GPU peaks/capacity remain separate checks.

Selected metadata supplies inventory_identity alongside its scientific identity,
and selected_records with task/seed/site, learned_axis {reference,sha256}, ordered
assessment_axes[199]/calibration_axes[32] {axis_index,reference,sha256}, nuisance
{status,axis} or {status,reason,fit_receipt}. Axis sha256 uses the runner numeric
axis identity, not merely an individual array file digest.
"""
from __future__ import annotations

STARTUP_REFERENCE_BYTES=8192

from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
import re

SEEDS = (42, 1, 123)
CONDITIONS = ('D', 'H', 'F', 'I', 'user_neutral')
STAGES = ('prefit', 'fit-select', 'selected-pilot', 'remaining')
KEY_FIELDS = ('panel','analysis_task','source_task','split','seed','site','family',
              'axis_index','operation','instance_id','condition','stream')
REPLAYS = ('intact','empty','head_self','zero_coefficient','patched')
PROFILE_REUSE_POLICY = dict(
    kind='a3_direction_profile_reuse_v1',
    authority='root reviewed two-pass operational ruling',
    assumptions=['independent examples; no cross-example state',
                 'no data-dependent execution path',
                 'unchanged kernels, model, source and projection site',
                 'identical operation, donor convention and physical geometry'],
    prefit_axis_class='validated nonzero attainable-image timing axis',
    selected_axes='all 199 actual frozen assessment null axes plus named other operations',
    measured_split='validation',target_rows_are_measured=False,
    target_controls='own source-bound positive and replay controls remain required',
    buffer=1.25,packed_execution_requires='Unit F reviewed reuse adapter')


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
                                     allow_nan=False).encode()).hexdigest()


def _finite(value, label, *, positive=False):
    _require(type(value) in (int,float) and math.isfinite(value)
             and (value>0 if positive else value>=0), 'invalid '+label)
    return value


def _integer(value, label, *, positive=True):
    _require(type(value) is int and value >= (1 if positive else 0), 'invalid '+label)
    return value


def _freeze(value):
    return tuple(_freeze(x) for x in value) if isinstance(value,(list,tuple)) else value


def _chunks(values, n):
    return [values[i:i+n] for i in range(0,len(values),n)]


def _records(value, field):
    if value is None:
        return None
    return value.get(field, value.get('metadata',{}).get(field))


def inventory_identity(design, protocol):
    identity=copy.deepcopy(protocol.get('identity'))
    if identity is None:
        parent=design.get('a1_identity',{})
        identity={k:protocol.get(k) for k in ('commit','code_hashes')}
        identity.update({k:parent.get(k) for k in ('model','model_revision','tokenizer_revision','tokenizer_identity','grader_sha256')})
    _require(isinstance(identity,dict) and re.fullmatch('[0-9a-f]{40}',str(identity.get('commit'))) is not None,
             'full frozen source identity required')
    _require(isinstance(identity.get('code_hashes'),dict) and identity['code_hashes']
             and all(re.fullmatch('[0-9a-f]{64}',str(x)) for x in identity['code_hashes'].values()),'complete source hashes required')
    for key in ('model','model_revision','tokenizer_revision'):
        _require(isinstance(identity.get(key),str) and identity[key],'missing '+key)
    identity.update(design_sha256=digest(design),protocol_sha256=digest(protocol))
    return identity


# Backwards compatibility for injected test fixtures; integrations use public name.
_identity = inventory_identity

def _source_rows(design, task, split):
    if task in ('ioi','mmlu'):
        return design[task+'_validation'] if split=='validation' else design['utility'][task]
    field={'train':'fit_ids','validation':'selection_ids','assessment':'assessment_ids'}[split]
    ids=design['tasks'][task][field]
    conditions=('D','I','H','user_neutral') if split=='train' else CONDITIONS
    result=[r for r in design['access_rows'][task] if r['instance_id'] in set(ids) and r['condition'] in conditions]
    _require(len(result)==len(ids)*len(conditions),'incomplete mechanism source rows')
    index={(r['condition'],r['instance_id']):r for r in result}
    _require(len(index)==len(result),'duplicate source rows')
    return [index[(c,i)] for c in conditions for i in ids]


def _length(row, stream):
    data=row['streams'][stream]
    tokens=data.get('tokens',data.get('input_ids'))
    _require(isinstance(tokens,list) and tokens,'frozen tokens required')
    _require(data.get('readout',len(tokens)-1)==len(tokens)-1,'invalid unpadded readout')
    return len(tokens)


def _timing_ids(rows):
    lengths={}
    for row in rows:
        lengths[row['instance_id']]=max(lengths.get(row['instance_id'],0),
            *[_length(row,s) for s in row['streams']])
    return sorted(lengths,key=lambda i:(-lengths[i],i))[:4]


def _host_bound(value, memo=None):
    """Portable conservative CPython object bound, not a runtime measurement.

    Count repeated references as copies. Scalars/strings, dictionary slots and
    list slots are bounded separately; never equate serialized JSON with RAM.
    The supported runtimes use far less than these per-object/slot allowances.
    """
    if memo is None: memo={}
    key=id(value)
    if key in memo: return memo[key]
    if isinstance(value,dict):
        size=512+128*len(value)+sum(_host_bound(k,memo)+_host_bound(v,memo) for k,v in value.items())
    elif isinstance(value,(list,tuple)):
        size=256+16*len(value)+sum(_host_bound(v,memo) for v in value)
    elif isinstance(value,str): size=256+4*len(value.encode('utf-8'))
    elif value is None or type(value) in (int,float,bool): size=256+len(str(value))*4
    else: raise ValueError('unsupported retained storage value')
    memo[key]=size
    return size


def derive_storage_requirements(workload):
    """Bound the FULL retained target, including transient publication copies.

    The accepted runner emits readout tensors, optional own-clause summaries,
    padded tokens/masks, complete source records, scalar outcomes and projection
    blocks. The accepted numeric writer retains portable arrays plus descriptors;
    the row/shard reader currently materializes complete rows. Therefore host
    admission conservatively includes that full read, not merely a pilot chunk.
    JSON float placeholders bound finite scalar spellings; source text/tokens
    are independently reconstructed. Numeric fit/probe/axis geometry is bounded
    by the frozen head/model/cohort dimensions, with one probe fit at a time.
    This schema is a conservative storage bound, never a measured memory claim.
    """
    frozen=workload['frozen_inputs']; design=frozen['design']; cfg=frozen['protocol']['workload']
    h=cfg['head_width']; d=cfg['hidden_size']; huge=-1.7976931348623157e308
    def wire(value): return len(json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode())
    record_cache={}; source_index={}; source_max={}; source_host_max={}; complete_groups=set(); components=Counter(); raw_host=0; capture_host=0
    largest_capture=largest_output=largest_control=0
    stat_names=('margin','raw_margin','native_margin','native_raw_margin','argmax','native_argmax',
                'correct','binary_win','choice_margin','choice_correct')
    def record(task,split,condition,stream,rid,width):
        key=(task,split,condition,stream,rid,width)
        if key not in record_cache:
            group=(task,split)
            if group not in source_index:
                source_index[group]={(r.get('condition',task),r['instance_id']):r for r in _source_rows(design,task,split)}
            original=source_index[group][(condition,rid)]; data=original['streams'][stream]
            enriched=dict(original,tokens=data['tokens'],layout=data.get('layout'),utility_assessment=stream=='clean')
            for label in ('expected_token','honest_token','opposite_token'):
                enriched[label]=data.get(label,original.get(label,0))
            # Include both the original unpadded record and the padded arrays.
            padding=width-len(data['tokens']); _require(padding>=0,'storage profile truncates source')
            snapshot=dict(record=enriched,tokens=data['tokens']+[-9223372036854775808]*padding,
                attention_mask=[1]*len(data['tokens'])+[0]*padding,readout=data.get('readout',len(data['tokens'])-1),
                task=task,condition=condition,stream=stream,instance_id=rid,
                expected_token=enriched['expected_token'],honest_token=enriched['honest_token'],
                opposite_token=enriched['opposite_token'],choice_tokens=original.get('choice_tokens'))
            record_cache[key]=(snapshot,wire(snapshot),_host_bound(snapshot))
            source_max[group]=max(source_max.get(group,0),record_cache[key][1])
            source_host_max[group]=max(source_host_max.get(group,0),record_cache[key][2])
        return record_cache[key]
    # Capture payloads include projections in every sink call; retaining a copy
    # per chunk is safe even before the production adapter deduplicates them.
    for cap in workload['captures']:
        size=0; host=0; p=cap['profile']; sites=cap['sites']
        for rid in cap['instance_ids']:
            snapshot,source_bytes,source_host=record(cap['source_task'],cap['split'],cap['condition'],cap['stream'],rid,p['padded_width'])
            heads=[dict(site=site,value=[huge]*h) for site in sites]
            clause=dict(supported=True,diagnostic_only=True,positions=list(range(p['padded_width'])),
                heads=heads,prompt_utf8_hex=snapshot['record']['streams'][cap['stream']].get('prompt','').encode().hex(),
                semantics='own verified clause mean; never readout substitute')
            body=dict(profile_id='f'*64,**snapshot,heads=heads,stats={k:huge for k in stat_names},clause_summary=clause)
            amount=wire(body)+len(sites)*4096; size+=amount; host+=_host_bound(body)+len(sites)*4096
            components['capture_source_records']+=source_bytes
            components['capture_readout_numeric']+=len(sites)*h*4
            components['clause_summary_numeric']+=len(sites)*h*4
        if cap.get('dummy_sources'):
            factor=1+len(cap['dummy_sources'])
            size*=factor; host*=factor
            components['execution_dummy_capture_allowance']+=size
        projection=len(sites)*h*d*4
        size+=projection+1024*len(sites); host+=projection+2048*len(sites)
        components['capture_payloads']+=size; capture_host+=host; largest_capture=max(largest_capture,size)
    # Scalar/row envelopes mirror score_direction_cells' emitted fields. The
    # donor bound includes the complete source record (larger than its map).
    extra=dict(axis_hash='f'*64,profile_id='f'*64,opposite_token=huge,honest_token=huge,expected_token=huge,
        head_norm=huge,residual_norm=huge,fit_projected_variance=huge,epsilon=huge,
        replay_errors={k:huge for k in ('empty','head_self','zero_coefficient')},
        positive_control=dict(control_id='f'*64,profile_id='f'*64,recipient_sha256='f'*64,valid=False),
        replay_valid=False,supported=False,gate_valid=False,
        invalid_reason='missing/invalid separate all-sender positive calibration')
    for name in stat_names:
        extra['intact_'+name]=huge; extra['patched_'+name]=huge
    extra_wire=wire(extra); extra_host=_host_bound(extra); profile_sizes={}
    for shard in workload['shards']:
        p=shard['profile']; pid=digest(p)
        if pid not in profile_sizes: profile_sizes[pid]=(wire(p),_host_bound(p))
        size=0
        for key in shard['expected_keys']:
            panel,analysis,task,split,seed,site,family,axis,op,rid,c,stream=key
            snapshot,source_bytes,source_host=record(task,split,c,stream,rid,p['padded_width'])
            # Two source-sized donor/map allowances cover source IDs/readouts,
            # provenance and mapping fields even for differently sized donors.
            key_bytes=wire(dict(zip(KEY_FIELDS,key)))
            amount=key_bytes+3*source_bytes+profile_sizes[pid][0]+extra_wire
            size+=amount
            raw_host+=_host_bound(dict(zip(KEY_FIELDS,key)))+3*source_host+profile_sizes[pid][1]+extra_host
        components['scientific_rows']+=size; largest_output=max(largest_output,size)
    # Positive evidence keeps recipient/donor snapshots in the record AND in
    # its reviewed measurement, plus the complete head/MLP sender list twice.
    layers=cfg.get('num_layers',32); heads_per_layer=max(1,d//h)
    senders=[['head',l,i] for l in range(layers) for i in range(heads_per_layer)]+[['mlp',l,0] for l in range(layers)]
    for req in workload['requirements']:
        if req['operation']!='positive_control': continue
        task,split,c,stream,rid=req['target_keys'][0]
        _,source_bytes,source_host=record(task,split,c,stream,rid,req['profile']['padded_width'])
        # Actual donor may be a different MMLU question; bound by the longest
        # frozen question in that source split, not by the pilot recipient.
        group=(task,split)
        if group not in complete_groups:
            for row in _source_rows(design,task,split):
                for st in row['streams']: record(task,split,row.get('condition',task),st,row['instance_id'],req['profile']['padded_width'])
            complete_groups.add(group)
        donor_bytes=source_max[group]
        size=4*(source_bytes+donor_bytes)+2*wire(senders)+wire(req['profile'])+wire(extra)
        repetitions=max(1,req['batches']//3)
        size*=repetitions
        components['positive_evidence']+=size
        raw_host+=4*(source_host+source_host_max[group])+2*_host_bound(senders)+_host_bound(extra)+_host_bound(req['profile'])
        largest_control=max(largest_control,size)
    # Shared image geometry, both fitted axes and ridge probe arrays; nulls are
    # retained individually by selected outputs, never treated as just indices.
    arrays=0; array_count=0; probe_peak=0
    for task,definition in design['tasks'].items():
        n=len(definition['fit_ids']); sites=len(definition['direction_sites'])
        arrays+=sites*4*(3*d*h+h); array_count+=4*sites
        arrays+=sites*len(SEEDS)*4*(2*(d+2*h+n)+6*(h+1)); array_count+=sites*len(SEEDS)*14
        clusters=definition.get('pressure_cluster_counts',{}).get('fit',{})
        expanded=(len(clusters)*max(clusters.values())) if clusters else n*n
        metadata_width=max([6]+[len(r.get('features',[])) for r in design.get('confounds',{}).get('table',[])])
        examples=expanded*2*2; features=max(h,metadata_width)
        bound=4*(8*examples*features+8*features*features+8*examples+4*n*2*features+4*h*features)
        probe_peak=max(probe_peak,bound)
    if workload['stage'] in ('remaining','selected-pilot'):
        axes=len(design['tasks'])*len(SEEDS)*(1+199+32+1)
        arrays+=axes*(d+2*h)*4; array_count+=axes*3
    components['projection_and_fit_arrays']=arrays+array_count*1024
    # Exact frozen metadata, keys, array descriptors, identity/completion
    # manifests, and one largest fresh sibling temporary publication.
    base={k:v for k,v in workload.items() if k not in ('storage_requirements','inventory_sha256')}
    metadata=wire(base)
    descriptor=wire(dict(path='a'*4096,dtype='<f8',shape=[9223372036854775807]*3,sha256='f'*64,bytes=9223372036854775807))
    identity=wire(workload['identity'])+len(workload['captures'])*1024
    publication_count=len(workload['captures'])+len(workload['shards'])+len(workload['jobs'])
    components['publication_metadata']=metadata+array_count*descriptor+publication_count*(identity+4096)
    cache=components['capture_payloads']+components['projection_and_fit_arrays']+array_count*descriptor
    output=components['scientific_rows']+components['positive_evidence']+components['publication_metadata']
    scratch=max(largest_capture,largest_output,largest_control,metadata,arrays)+identity+4096
    # Full completed-shard reader materializes all observations. Add its source
    # objects, captures and immutable metadata independently of numeric tensors.
    components['authority_key_proof_host_bytes']=1024*len(workload['expected_keys'])+65536
    host=capture_host+raw_host+arrays+probe_peak+_host_bound(base)+2*scratch+4*(8*d*h+8*h*h)+components['authority_key_proof_host_bytes']
    return dict(schema='a3_target_storage_bound_v1',tiers=dict(host_ram=host,cache_disk=cache,
        output_disk=output,scratch_disk=scratch),components=dict(components),
        policy='full target retention plus largest atomic publication; optional summaries included; no pilot-size inference')


def _storage_admission(workload, ledger, measured_host_peak=0):
    capacities=ledger.get('storage_capacities')
    _require(isinstance(capacities,dict),'fresh target storage tier capacities required')
    required=dict(workload['storage_requirements']['tiers']); required['host_ram']+=measured_host_peak
    pools=Counter(); available={}
    for tier,need in required.items():
        entry=capacities.get(tier,{})
        _require(isinstance(entry.get('pool'),str) and entry['pool'],'storage pool identity required')
        cap=_integer(entry.get('available_bytes'),'target storage capacity',positive=False)
        pool=entry['pool']; pools[pool]+=need
        available[pool]=min(available.get(pool,cap),cap)
    _require(all(available[p]>=need for p,need in pools.items()),'full target storage capacity underflow')
    return dict(required=required,measured_host_peak_bytes=measured_host_peak,pool_required=dict(pools),pool_available=available)


def build_inventory(design: dict, protocol: dict, *, stage: str, fits=None, selected=None) -> dict:
    """Enumerate actual row keys/shards/forwards without model or filesystem I/O."""
    _require(stage in STAGES,'unknown inventory stage')
    _require(design.get('seeds')==list(SEEDS),'exact seeds 42/1/123 required')
    _require(set(design['tasks'])=={'far_v2','ser_v2','sdr_v2'},'full frozen task scope required')
    cfg=protocol.get('workload')
    _require(isinstance(cfg,dict),'frozen protocol workload execution geometry required')
    batch=_integer(cfg.get('microbatch_size'),'microbatch size')
    tile=_integer(cfg.get('axis_tile_sizes',{}).get(stage,cfg.get('axis_tile_size')),'axis tile size')
    jobs=_integer(cfg.get('jobs_by_stage',{}).get(stage,cfg.get('jobs')),'job count')
    _require(stage not in ('prefit','selected-pilot') or jobs==1,'one atomic timing job required per pilot part')
    _integer(cfg.get('num_layers',32),'model layer count')
    for key in ('head_width','hidden_size','dtype_bytes'):
        _integer(cfg.get(key),key)
    for key in ('warmup_batches','serialization_batches'):
        _integer(cfg.get(key),key,positive=False)
    _finite(cfg.get('finish_reserve_seconds'),'finish reserve')
    hardware=copy.deepcopy(cfg.get('hardware'))
    _require(isinstance(hardware,dict) and hardware.get('gpu'),'named hardware required')
    _integer(hardware.get('count'),'GPU count')
    identity=inventory_identity(design,protocol)
    numeric=protocol.get('numeric_profile',{})
    _require(design.get('injected') or numeric.get('dtype') and numeric.get('backend'),'numeric dtype/backend required')
    _require(design.get('injected') is True or 'task_order' in protocol,'production requires frozen task_order')
    task_order=protocol.get('task_order',sorted(design['tasks']))
    _require(len(task_order)==len(set(task_order)) and set(task_order)==set(design['tasks']),'changed frozen task order coverage')
    timing={t:_timing_ids(_source_rows(design,t,'validation')) for t in list(task_order)+['ioi','mmlu']}
    if 'timing_ids' in cfg:
        _require(cfg['timing_ids']==timing,'changed frozen metadata-only timing membership')
    inv=dict(schema_version=1,kind='a3_direction_inventory',stage=stage,
        phase='M1' if stage in ('prefit','selected-pilot') else 'M2',subphase='directions',
        pilot_part='prefit' if stage in ('prefit','fit-select') else 'selected',
        admission_scope='fit-validation-only' if stage in ('prefit','fit-select') else 'calibration-assessment-steering',
        identity=identity,hardware=hardware,injected=bool(design.get('injected')),
        timing_ids=timing,requirements=[],shards=[],expected_keys=[],captures=[],probe_reads=[],packing_invocations=[],
        fit_failures=[],blockers=[],conditional_unavailable=[],forward_counts={},jobs=[],
        finish_reserve_seconds=cfg['finish_reserve_seconds'],bytes={},
        reuse_policy=copy.deepcopy(cfg.get('reuse_policy')),
        frozen_inputs=copy.deepcopy(dict(design=design,protocol=protocol,fits=fits,selected=selected)))
    counters=Counter(); profile_by_id={}; captures={}; positives={}; peaks=Counter(); shard_ids=set(); source_index={}

    def profile(task,split,n,lanes,sites,*,singleton=False):
        if cfg.get('pad_tail_batches') and not singleton and split!='train': n=batch
        width=cfg['widths'][task][split]
        _integer(width,'padded width')
        return dict(source_task=task,padded_width=width,physical_batch_size=n*lanes,
            axis_tile_size=lanes,dtype=numeric.get('dtype','synthetic'),backend=numeric.get('backend','synthetic'),
            model=identity['model'],model_revision=identity['model_revision'],source_sha256=digest(identity['code_hashes']),
            sites=copy.deepcopy(sites),positive_singleton=singleton,capture_scope='all_senders' if singleton else 'requested_head_union')

    def input_scope(keys, p):
        out=[]; seen=set()
        for key in keys:
            if len(key)==12:
                task,split,c,stream,rid=key[2],key[3],key[10],key[11],key[9]
            else:
                task,split,c,stream,rid=key
            scopekey=(task,split,c,stream,rid)
            if scopekey in seen: continue
            seen.add(scopekey)
            indexkey=(task,split)
            if indexkey not in source_index:
                source_index[indexkey]={(r.get('condition',task),r['instance_id']):r for r in _source_rows(design,task,split)}
            row=source_index[indexkey][(c,rid)]; data=row['streams'][stream]
            out.append(dict(source_task=task,analysis_split=split,instance_id=rid,condition=c,stream=stream,
                record=copy.deepcopy(row),unpadded_length=_length(row,stream),
                padded_width=p['padded_width'],readout=data.get('readout',_length(row,stream)-1)))
        if cfg.get('pad_tail_batches') and out and not p.get('positive_singleton'):
            size=p['physical_batch_size']//p['axis_tile_size']
            real_ids=[x['instance_id'] for x in out]
            # Requirements are one homogeneous recipient batch; aliases are
            # execution-only duplicates and never enter scientific target keys.
            while len(out)<size:
                duplicate=copy.deepcopy(out[0]); original=duplicate['instance_id']
                alias='a3-dummy:'+digest([duplicate['source_task'],duplicate['analysis_split'],duplicate['condition'],real_ids,len(out)])
                duplicate.update(instance_id=alias,source_instance_id=original)
                duplicate['record']=dict(duplicate['record'],instance_id=alias,
                    execution_dummy=dict(duplicate_of=original,source_sha256=digest(out[0]['record'])))
                out.append(duplicate)
        return out

    def req(operation,p,keys,axes,*,batches=1,family='',timing_keys=None,axis_scope=None,job_id=None):
        item=dict(operation=operation,profile=p,batches=batches,family=family,call_index=len(inv['requirements']),declared_job_id=job_id,
            target_keys=keys,timing_keys=timing_keys if timing_keys is not None else keys,axis_ids=list(axes),axis_scope=axis_scope or [])
        item['timing_inputs']=input_scope(item['timing_keys'],p)
        item['target_unmasked_lengths']=[x['unpadded_length'] for x in input_scope(keys,p)]
        item['timing_unmasked_lengths']=[x['unpadded_length'] for x in item['timing_inputs']]
        item['axis_class']='validated_nonzero_image_axis' if inv['pilot_part']=='prefit' and axes else None
        item['donor_convention']=('frozen_cyclic_different_question_readout' if p['positive_singleton'] else 'none') if p['source_task']=='mmlu' else ('repeated_B_corrupt' if p['source_task']=='ioi' else 'same_ID_condition_opposite_stream')
        item['requirement_id']=digest(item)
        inv['requirements'].append(item)
        counters[operation]+=batches
        profile_by_id[digest(p)]=p
        n=p['physical_batch_size']; width=p['padded_width']; sites=p['sites']
        peaks['transient_capture_peak']=max(peaks['transient_capture_peak'],
            n*width*cfg['hidden_size']*len({s[1] for s in sites})*cfg['dtype_bytes'])
        vocab=cfg.get('vocabulary_size',8 if design.get('injected') else None)
        _integer(vocab,'vocabulary size')
        peaks['transient_native_logits_peak']=max(peaks['transient_native_logits_peak'],n*width*vocab*cfg['dtype_bytes'])
        peaks['transient_readout_logits_peak']=max(peaks['transient_readout_logits_peak'],n*vocab*4)
        peaks['transient_residual_peak']=max(peaks['transient_residual_peak'],n*width*cfg['hidden_size']*cfg['dtype_bytes'])
        if p['positive_singleton']:
            # The reviewed helper retains recipient+donor all-head/MLP captures,
            # replacements and patched output during its three-forward pass.
            positive_peak=8*n*width*cfg['hidden_size']*cfg.get('num_layers',32)*cfg['dtype_bytes']
            peaks['positive_calibration_transient_peak']=max(peaks['positive_calibration_transient_peak'],positive_peak)
            peaks['transient_capture_peak']=max(peaks['transient_capture_peak'],positive_peak)
        peaks['readout_chunk_peak']=max(peaks['readout_chunk_peak'],n*len(sites)*cfg['head_width']*4)
        return item['requirement_id']

    def streams(task):
        return ('clean',) if task in ('ioi','mmlu') else ('clean','corrupt')

    def groups(task,split,*,pilot=False,train=False,target_split=None):
        rows=_source_rows(design,task,split)
        chosen=timing[task] if pilot else list(dict.fromkeys(r['instance_id'] for r in rows))
        chunk_size=cfg.get('train_microbatch_size',batch) if train else batch
        _integer(chunk_size,'train microbatch size')
        chunks=_chunks(chosen,chunk_size)
        if pilot:
            target_rows=_source_rows(design,task,target_split or split)
            target_n=len({r['instance_id'] for r in target_rows})
            sizes={len(x) for x in _chunks(list(range(target_n)),batch)}
            _require(max(sizes)<=len(chosen),'validation timing cohort cannot cover physical target batch; freeze a smaller microbatch')
            for n in sorted(sizes-{len(x) for x in chunks}): chunks.append(chosen[:n])
        result=[]
        for c in (tuple(dict.fromkeys(r['condition'] for r in rows)) if task in ('ioi','mmlu') else CONDITIONS):
            if train and c=='F':
                continue
            for s in streams(task):
                rr={r['instance_id']:r for r in rows if r.get('condition',task)==c}
                for chunk in chunks:
                    _require(all(i in rr for i in chunk),'missing source condition')
                    width=cfg['widths'][task][split]
                    _require(all(_length(rr[i],s)<=width for i in chunk),'execution width truncates source')
                    result.append((c,s,chunk))
        return result

    def capture(task,split,sites,*,pilot=False,train=False,donor=False,lanes=tile,profile_split=None,invocation=None):
        # Donor IOI corrupt is a real separately captured stream.
        for c,s,ids in groups(task,split,pilot=pilot,train=train,target_split=profile_split or split):
            for stream in ((s,'corrupt') if donor and task=='ioi' else (s,)):
                p=profile(task,profile_split or split,len(ids),lanes,sites)
                if train and protocol.get('fit_cache'):
                    p=copy.deepcopy(protocol['fit_cache']['capture_identity']['numeric_profile'])
                    sites=copy.deepcopy(p['sites'])
                source={r['instance_id']:r for r in _source_rows(design,task,split) if r.get('condition',task)==c}
                _require(all(_length(source[i],stream)<=p['padded_width'] for i in ids),'capture profile truncates recipient/donor source')
                key=digest([task,split,c,stream,ids,p,invocation])
                if key in captures:
                    continue
                execution=input_scope([[task,split,c,stream,i] for i in ids],p)
                captures[key]=dict(capture_id=key,execution_ids=[x['instance_id'] for x in execution],
                    dummy_sources={x['instance_id']:x['source_instance_id'] for x in execution if 'source_instance_id' in x},source_task=task,split=split,condition=c,
                    stream=stream,instance_ids=ids,sites=sites,profile=p)
                op='capture_train' if train else ('capture_donor' if stream=='corrupt' and task=='ioi' else 'capture_intact')
                # Timing rows always refer to frozen validation membership.
                tk=[[task,'validation',c,stream,i] for i in (ids if pilot else timing[task][:len(ids)])]
                req(op,p,[[task,split,c,stream,i] for i in ids],[],timing_keys=tk)

    def score(panel,analysis,split,sites,cells,*,pilot=False,profile_split=None):
        for source in (analysis,'ioi','mmlu'):
            active=[c for c in cells if source!='mmlu' or c['operation']!='interchange']
            # Cells specify recipient source kinds; floors replace primary donor op.
            expanded=[]
            for cell in active if source!='mmlu' else cells:
                if source=='mmlu':
                    if cell.get('secondary'):
                        continue
                    ops=(cell['operation'],) if cell['operation'].startswith('steer_') else ('zero','h_mean')
                else:
                    ops=(cell['operation'],)
                for operation in ops:
                    expanded.append(dict(cell,operation=operation))
            invocation=digest([panel,analysis,source,split,sites,cells]) if pilot else None
            source_groups=groups(source,split,pilot=pilot,target_split=profile_split or split)
            if pilot and tile>1:
                _require(len(expanded)>=tile,'pilot packing invocation lacks complete physical tile; freeze smaller pilot tile')
                for n in sorted({len(x[2]) for x in source_groups}):
                    batch_groups=[dict(condition=c,stream=st,instance_ids=ids) for c,st,ids in source_groups if len(ids)==n]
                    inv['packing_invocations'].append(dict(invocation_id=digest([invocation,n]),panel=panel,analysis_task=analysis,
                        source_task=source,split=split,cells=expanded,batch_groups=batch_groups,
                        profile=profile(source,profile_split or split,n,tile,sites),
                        actual_validation_ids=list(dict.fromkeys(i for g in batch_groups for i in g['instance_ids'])),
                        captures_repeated_serial_and_packed=True))
            capture(source,split,sites,pilot=pilot,donor=True,profile_split=profile_split,invocation=invocation)
            if pilot and tile>1:
                capture(source,split,sites,pilot=True,donor=True,lanes=1,profile_split=profile_split,invocation=invocation)
            for condition,stream,ids in source_groups:
                # Floors must each be physically dispatched as distinct cells.
                execution_ids=list(ids); dummy_sources={}
                if cfg.get('pad_tail_batches'):
                    while len(execution_ids)<batch:
                        alias='a3-dummy:'+digest([source,split,condition,ids,len(execution_ids)])
                        dummy_sources[alias]=ids[0]; execution_ids.append(alias)
                for start in range(0,len(expanded),tile):
                    block=expanded[start:start+tile]
                    p=profile(source,profile_split or split,len(ids),tile,sites)
                    keys=[(panel+':batch='+str(len(ids)) if pilot else panel,analysis,source,split,c['seed'],tuple(c['site']),c['family'],c['axis_index'],c['operation'],i,condition,stream)
                          for c in block for i in ids]
                    tkeys=[(panel+':batch='+str(len(ids)) if pilot else panel,analysis,source,'validation',c['seed'],tuple(c['site']),c['family'],c['axis_index'],c['operation'],i,condition,stream)
                           for c in block for i in (ids if pilot else timing[source][:len(ids)])]
                    shard_id=digest(keys)
                    _require(keys and shard_id not in shard_ids,'duplicate scoring shard')
                    shard_ids.add(shard_id)
                    inv['shards'].append(dict(shard_id=shard_id,expected_keys=keys,profile=p,
                        panel=panel,split=split,cells=block,instance_ids=ids,
                        requirement_ids=[],control_ids=[],execution_ids=execution_ids,dummy_sources=dummy_sources,
                        dummy_positive_forward_count=3*len(dummy_sources)))
                    shard=inv['shards'][-1]
                    if p['axis_tile_size']>1:
                        shard['requirement_ids'].append(req('packing_lookup',p,keys,[c['axis_index'] for c in block],timing_keys=tkeys,
                            axis_scope=[{k:c[k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in c} for c in block]))
                    inv['expected_keys'].extend(keys)
                    axes=[c['axis_index'] for c in block]
                    for op in REPLAYS:
                        shard['requirement_ids'].append(req(op,p,keys,axes,
                            family=block[0]['family'],timing_keys=tkeys,axis_scope=[{k:c[k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in c} for c in block]))
                    if pilot and tile>1:
                        serial=profile(source,profile_split or split,len(ids),1,sites)
                        for op in REPLAYS:
                            req('equivalence_serial_'+op,serial,keys,axes,batches=len(block),
                                family=block[0]['family'],timing_keys=tkeys,axis_scope=[{k:c[k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in c} for c in block])
                        if start==0:
                            for lanes in (1,tile):
                                dummy=profile(source,profile_split or split,len(ids),lanes,sites)
                                for op in REPLAYS:
                                    req('equivalence_dummy_'+str(lanes)+'_'+op,dummy,keys[:len(ids)],axes[:1],
                                        family=block[0]['family'],timing_keys=tkeys[:len(ids)],axis_scope=[{k:block[0][k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in block[0]}])
                    if dummy_sources:
                        peaks['execution_dummy_rows']+=len(dummy_sources)*len(block)
                        pp=profile(source,profile_split or split,1,1,sites,singleton=True)
                        req('positive_control',pp,[[source,split,condition,stream,ids[0]]],[],batches=3*len(dummy_sources),
                            timing_keys=[[source,'validation',condition,stream,timing[source][0]]])
                    # Reviewed positive_control uses separately padded singleton donors.
                    for rid in ids:
                        pp=profile(source,profile_split or split,1,1,sites,singleton=True)
                        pk=digest([analysis,source,split,condition,stream,rid,pp])
                        shard['control_ids'].append(pk)
                        if pk not in positives:
                            positives[pk]=dict(profile=pp,key=[source,split,condition,stream,rid])
                            req('positive_control',pp,[[source,split,condition,stream,rid]],[],batches=3,
                                timing_keys=[[source,'validation',condition,stream,rid if pilot else timing[source][0]]])

    fit_records=_records(fits,'fit_records')
    fit_index={}
    if fits is not None:
        _require(isinstance(fit_records,list),'complete fit_records required')
        for record in fit_records:
            k=(record['task'],tuple(record['site']),record['seed'])
            _require(k not in fit_index,'duplicate fit record')
            fit_index[k]=record
    selected_records=_records(selected,'selected_records')
    sel={}
    def axis_descriptor(value, index=None):
        _require(isinstance(value,dict) and isinstance(value.get('reference'),str) and value['reference']
            and re.fullmatch('[0-9a-f]{64}',str(value.get('sha256'))) is not None,'invalid frozen axis reference/hash')
        if index is not None:
            _require(type(value.get('axis_index')) is int and value['axis_index']==index,'changed/duplicate frozen axis index')

    if stage in ('remaining','selected-pilot'):
        selected_metadata=selected.get('metadata',selected) if isinstance(selected,dict) else {}
        _require(selected_metadata.get('selection_split')=='validation','selection must be frozen on validation')
        _require(not selected_metadata.get('blocked_task_seeds'),'blocked selection task/seed')
        _require(selected.get('inventory_identity',selected.get('identity',selected.get('metadata',{}).get('inventory_identity',selected.get('metadata',{}).get('identity'))))==identity,'changed selected source/design/protocol identity')
        _require(isinstance(selected_records,list),'frozen selected_records required')
        for record in selected_records:
            k=(record['task'],record['seed'])
            _require(k not in sel,'duplicate selected seed')
            _require(len(record.get('assessment_axes',[]))==199,'exact frozen 199 assessment axes required')
            _require(len(record.get('calibration_axes',[]))==32,'exact frozen 32 calibration axes required')
            axis_descriptor(record.get('learned_axis'))
            for name in ('assessment_axes','calibration_axes'):
                for i,axis in enumerate(record[name]): axis_descriptor(axis,i)
                _require(len({digest(a) for a in record[name]})==len(record[name]),'duplicate frozen axes')
            nuisance=record.get('nuisance',{})
            _require(nuisance.get('status') in ('fitted','unfitted'),'explicit nuisance fit status required')
            if nuisance['status']=='fitted': axis_descriptor(nuisance.get('axis'))
            else:
                _require(nuisance.get('reason') and nuisance.get('fit_receipt'),'unfitted nuisance reason/receipt required')
            _require(tuple(record['site']) in map(tuple,design['tasks'][record['task']]['direction_sites']),'selected site outside frozen list')
            sel[k]=record
        _require(set(sel)=={(t,s) for t in design['tasks'] for s in SEEDS},'complete selected task/seed coverage required')
    for task in task_order:
        definition=design['tasks'][task]
        sites=definition['direction_sites']
        if not design.get('injected'):
            _require(len(definition['assessment_ids'])==100,'fixed 100 assessment IDs required')
            _require(len(design['utility']['ioi'])==100 and len(design['utility']['mmlu'])==32,'fixed utility floors required')
            _require(len(design['ioi_validation'])==100 and len(design['mmlu_validation'])==32,'separate validation utilities required')
        if stage in ('prefit','fit-select'):
            # M1 uses validation only, padded to every required train shape.
            if fits is None:
                capture(task,'validation' if stage=='prefit' else 'train',sites,pilot=stage=='prefit',train=True,lanes=1,profile_split='train')
            cells=[]
            for site in sites:
                for seed in SEEDS:
                    record=fit_index.get((task,tuple(site),seed))
                    if fit_records is not None:
                        _require(record is not None,'missing scientific fit requirement')
                        valid=record.get('dom_valid',record.get('valid',record.get('status')=='fitted'))
                        if not valid:
                            inv['fit_failures'].append(copy.deepcopy(record)); continue
                    cells.append(dict(seed=seed,site=site,family='learned',axis_index=0,operation='interchange'))
            for seed in SEEDS:
                if not any(c['seed']==seed for c in cells):
                    inv['blockers'].append(dict(task=task,seed=seed,reason='no finite valid DOM candidate'))
            # Site groups are dispatched independently: profile names exact sites.
            for site in sites:
                cc=[c for c in cells if c['site']==site]
                if cc: score('validation',task,'validation',[site],cc,pilot=stage=='prefit')
            inv['probe_reads'].append(dict(task=task,split='validation',extra_forwards=0,source='matched intact captures'))
        else:
            for seed in SEEDS:
                record=sel[(task,seed)]; site=record['site']; one=[site]
                def cell(family,index,operation='interchange',**kw):
                    if family in ('assessment_null','steering_random'): axis=record['assessment_axes'][index]
                    elif family=='calibration_null': axis=record['calibration_axes'][index]
                    elif family in ('nuisance','steering_nuisance'): axis=record['nuisance']['axis']
                    else: axis=record['learned_axis']
                    return dict(seed=seed,site=site,family=family,axis_index=index,operation=operation,
                                axis_reference=axis['reference'],axis_sha256=axis['sha256'],**kw)
                if stage=='remaining':
                    score('calibration',task,'validation',one,
                        [cell('learned',0)]+[cell('calibration_null',i) for i in range(32)])
                split='validation' if stage=='selected-pilot' else 'assessment'
                panel='selected_pilot' if stage=='selected-pilot' else 'assessment'
                pending=[]
                def dispatch(cells):
                    if stage=='selected-pilot': pending.extend(cells)
                    else: score(panel,task,split,one,cells)
                dispatch([cell('learned',0)])
                dispatch([cell('assessment_null',i) for i in range(199)])
                nuisance=record['nuisance']['status']=='fitted'
                if nuisance:
                    dispatch([cell('nuisance',0)])
                else:
                    inv['fit_failures'].append(dict(task=task,seed=seed,site=site,family='nuisance',reason=record['nuisance']['reason'],fit_receipt=record['nuisance']['fit_receipt']))
                    inv['conditional_unavailable'].append(dict(task=task,seed=seed,family='nuisance',
                        obligations=['primary/floors','secondary zero/H','both-sign steering'],
                        reason=record['nuisance']['reason'],fit_receipt=record['nuisance']['fit_receipt'],
                        interpretation='nuisance diagnostic unavailable; no nuisance interpretation gate'))
                for family in ('learned','nuisance') if nuisance else ('learned',):
                    dispatch([cell(family,0,op,secondary=True) for op in ('zero','h_mean')])
                for family in ('steering_learned','steering_nuisance','steering_random'):
                    if family=='steering_nuisance' and not nuisance: continue
                    dispatch([cell(family,0,op) for op in ('steer_positive','steer_negative')])
                if stage=='selected-pilot':
                    # One complete producer invocation, including every family;
                    # short learned/nuisance lists cannot separately prove packing.
                    score(panel,task,'validation',one,pending,pilot=True,profile_split='assessment')
                    score('calibration_pilot',task,'validation',one,
                        [cell('learned',0)]+[cell('calibration_null',i) for i in range(32)],pilot=True)
            inv['probe_reads'].append(dict(task=task,split='assessment',extra_forwards=0,source='matched intact captures'))
    inv['captures']=list(captures.values())
    inv['capture_shards']=[dict(shard_id=c['capture_id'],capture=copy.deepcopy(c)) for c in inv['captures'] if c['split']=='train']
    _require(len(inv['expected_keys'])==len(set(map(_freeze,inv['expected_keys']))),'duplicate raw row keys')
    # Guard checks are real elapsed work, not invented model forwards. The
    # bound includes model publication and complete validation-cache adaptation.
    profiles=list(profile_by_id.values())
    if cfg.get('account_runtime_guards'):
        gp=dict(profiles[0],axis_tile_size=1,physical_batch_size=1,control='root_live_guard')
        count=10*len(inv['shards'])+3*len(inv['captures'])+2*jobs
        req('guard_refresh',gp,[],[],batches=max(1,count),job_id='job-0')
    # One explicit warmup and serialization profile per job; measured independently.
    _require(profiles,'empty workload')
    for j in range(jobs):
        inv['jobs'].append(dict(job_id='job-'+str(j),shard_ids=[s['shard_id'] for i,s in enumerate(inv['shards']) if i%jobs==j]))
        if cfg['warmup_batches']:
            req('warmup',dict(profiles[0],axis_tile_size=1,physical_batch_size=profiles[0]['physical_batch_size']//profiles[0]['axis_tile_size']),[],[],batches=cfg['warmup_batches'],job_id='job-'+str(j))
        # Publication work is derived from actual payloads, never a caller's
        # optimistic row/batch total. CPU benchmark evidence covers each shape.
        shapes=[dict(kind='direction_shard',profile=s['profile'],rows=len(s['expected_keys']),
                     key_bytes=len(json.dumps(s['expected_keys']).encode()))
                for i,s in enumerate(inv['shards']) if i%jobs==j]
        shapes += [dict(kind='profile_reuse_attestation',profile=shard['profile'],rows=len(shard['expected_keys']),
                        key_bytes=len(json.dumps(shard['expected_keys']).encode()))
                   for i,shard in enumerate(inv['shards']) if i%jobs==j and shard['profile']['axis_tile_size']>1]
        if j==0:
            shapes += [dict(kind='readout_capture',profile=c['profile'],rows=len(c['instance_ids']),
                            numeric_bytes=(2*len(c.get('execution_ids',c['instance_ids']))+cfg['hidden_size'])*len(c['sites'])*cfg['head_width']*4) for c in inv['captures']]
            shapes += [dict(kind='positive_control',profile=v['profile'],rows=1) for v in positives.values()]
        shapes += [dict(kind='completion',rows=1)]
        shapes += [dict(kind='declared_extra_finalization',rows=1) for _ in range(cfg['serialization_batches'])]
        serde=dict(profiles[0],axis_tile_size=1,physical_batch_size=1,
                   serialization_shapes=shapes,serialization_shapes_sha256=digest(shapes))
        req('serialization',serde,[],[],batches=len(shapes),job_id='job-'+str(j))
    assigned={rid:'job-'+str(i%jobs) for i,shard in enumerate(inv['shards']) for rid in shard['requirement_ids']}
    for job in inv['jobs']:
        job['requirement_ids']=[r['requirement_id'] for r in inv['requirements']
            if (r['declared_job_id'] or assigned.get(r['requirement_id'],'job-0'))==job['job_id']]
        job['depends_on']=['job-0'] if job['job_id']!='job-0' else []
    inv['operation_counts']=dict(counters)
    inv['forward_counts']={op:n for op,n in counters.items() if op not in ('serialization','guard_refresh','packing_lookup')}
    inv['bytes']=dict(peaks)
    inv['bytes']['capture_disk']=sum(len(c.get('execution_ids',c['instance_ids']))*len(c['sites'])*cfg['head_width']*4 for c in inv['captures'])
    inv['bytes']['projection_blocks']=sum(len(x['direction_sites'])*cfg['head_width']*cfg['hidden_size']*4 for x in design['tasks'].values())
    inv['bytes']['row_keys_utf8']=len(json.dumps(inv['expected_keys']).encode())
    inv['storage_requirements']=derive_storage_requirements(inv)
    inv['inventory_sha256']=digest(inv)
    return inv


def _validate_inventory(workload):
    body={k:v for k,v in workload.items() if k!='inventory_sha256'}
    _require(workload.get('inventory_sha256')==digest(body),'changed inventory content/counts')
    _require(not workload.get('blockers'),'blocked scientific workload')
    frozen=workload.get('frozen_inputs',{})
    rebuilt=build_inventory(frozen['design'],frozen['protocol'],stage=workload['stage'],
                            fits=frozen.get('fits'),selected=frozen.get('selected'))
    _require(digest(rebuilt)==digest(workload),'inventory differs from independent frozen-input reconstruction')
    _require(workload.get('stage') in STAGES,'unknown inventory stage')
    keys=[_freeze(k) for s in workload['shards'] for k in s['expected_keys']]
    _require(Counter(keys)==Counter(map(_freeze,workload['expected_keys'])),'inventory shard/row coverage mismatch')
    _require(set(k[4] for k in workload['expected_keys'])==set(SEEDS),'incomplete seed coverage')
    return body


def _ledger(ledger, identity):
    _require(ledger.get('kind')=='a3_root_ledger_snapshot_v1' and ledger.get('root_supplied') is True,'fresh root ledger required')
    _require(re.fullmatch('[0-9a-f]{64}',str(ledger.get('snapshot_sha256'))) is not None
        and ledger.get('snapshot_sha256')==ledger.get('current_snapshot_sha256'),'stale ledger snapshot')
    age=_finite(ledger.get('age_seconds'),'ledger age')
    limit=_finite(ledger.get('max_age_seconds'),'ledger max age',positive=True)
    _require(age<=limit and limit<=900,'stale ledger age')
    _require(ledger.get('expected_identity')==identity,'stale ledger source identity')
    entries=ledger.get('entries'); expected=ledger.get('expected_entry_ids')
    _require(isinstance(entries,list) and isinstance(expected,list),'complete prior ledger required')
    ids=[e['id'] for e in entries]
    _require(len(ids)==len(set(ids)) and len(expected)==len(set(expected)) and set(ids)==set(expected),'duplicate/missing prior spend or reservation')
    sums=Counter()
    for e in entries:
        _require(e.get('phase') in ('M1','M2','M3','M4','M5','contingency'),'unknown prior phase')
        state=e.get('state')
        _require(state in ('completed','failed','reserved','running'),'unknown ledger entry state')
        h=_finite(e.get('reserved_gpu_hours'),'prior reserved GPU hours')
        if e.get('actual_gpu_hours') is not None:
            sums['actual_all']+=_finite(e['actual_gpu_hours'],'prior actual GPU hours')
        else: sums['actual_unknown_entries']+=1
        sums['all']+=h; sums[e['phase']]+=h
        if e.get('subphase')=='directions': sums['direction_'+e['phase']]+=h
    contingency=_finite(ledger.get('contingency_gpu_hours'),'contingency reserve')
    _require(contingency+sums['contingency']>=6,'full A3 contingency must remain counted')
    sums['contingency_remaining']=contingency
    return sums


class _FrozenJSONDict(dict):
    __slots__=('_initialized',)
    def __init__(self,*args,**kwargs):
        if getattr(self,'_initialized',False):self._immutable()
        values=dict(*args,**kwargs)
        dict.__init__(self,((key,_freeze_json(value)) for key,value in values.items()))
        object.__setattr__(self,'_initialized',True)
    def _immutable(self,*args,**kwargs):raise TypeError('validated inventory is immutable')
    __setitem__=__delitem__=clear=pop=popitem=setdefault=update=__ior__=__setattr__=__delattr__=_immutable
    def __copy__(self):return self
    def __deepcopy__(self,memo):return self


class _FrozenJSONList(list):
    __slots__=('_initialized',)
    def __init__(self,*args,**kwargs):
        if getattr(self,'_initialized',False):self._immutable()
        values=list(*args,**kwargs)
        list.__init__(self,(_freeze_json(value) for value in values))
        object.__setattr__(self,'_initialized',True)
    def _immutable(self,*args,**kwargs):raise TypeError('validated inventory is immutable')
    __setitem__=__delitem__=append=clear=extend=insert=pop=remove=reverse=sort=__iadd__=__imul__=__setattr__=__delattr__=_immutable
    def __copy__(self):return self
    def __deepcopy__(self,memo):return self


def _freeze_json(value,memo=None):
    if memo is None:memo={}
    if type(value) in (_FrozenJSONDict,_FrozenJSONList) and getattr(value,'_initialized',False):return value
    if not isinstance(value,(dict,list,tuple)):return value
    if id(value) in memo:return memo[id(value)]
    if isinstance(value,dict):out=_FrozenJSONDict({k:_freeze_json(v,memo) for k,v in value.items()})
    else:out=_FrozenJSONList(_freeze_json(v,memo) for v in value)
    memo[id(value)]=out
    return out


def _packing_evidence(evidence, measurement):
    """Validate the reviewed runner v2 receipt without importing a model runtime.

    ``snapshots`` preserve actual _recipient_digest payloads, not target rows.
    Their content digests must reproduce each tested batch scope. Source rows,
    labels, masks and lengths are then independently checked against the frozen
    validation inputs. No different-input execution authorization is emitted.
    """
    _require(isinstance(evidence,dict),'complete measured packing evidence required')
    receipt=evidence.get('runner_receipt',{}); snapshots=evidence.get('snapshots',{})
    _require(receipt.get('kind')=='measured_direction_packing_v2'
        and receipt.get('receipt_sha256')==digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
        and receipt.get('valid') is True,'invalid packing evidence content')
    scope=receipt.get('scope',{}); p=measurement['profile']
    _require(scope.get('profile')==p and scope.get('source_sha256')==p['source_sha256']
        and receipt.get('scope_sha256')==digest(scope),'packing source/profile mismatch')
    _require(receipt.get('dummy_lanes_tested') is True and receipt.get('distinct_axes',0)>=2
        and receipt.get('nonzero_patches',0)>=2,'packing lacks nonzero/dummy measurements')
    _require(set(snapshots)==set(scope.get('batches',{})) and snapshots,'packing snapshots missing measured batches')
    expected=[]; expected_axes={}; measured_rows={}; measured_specs=[]
    # Unit E freezes homogeneous source/profile invocations whose cells have no
    # per-batch selectors. The accepted producer runs cells[:1] on EVERY batch,
    # in serial and packed geometry, even for an exactly dividing main panel.
    _require(set(scope.get('dummy_cells',{}))==set(scope['batches']),
             'packing mandatory dedicated dummy batch coverage missing')
    first_cell=None
    for bid,specs in scope['batches'].items():
        rows=snapshots[bid]
        _require(len(rows)*p['axis_tile_size']==p['physical_batch_size'],'packing measured physical batch geometry mismatch')
        _require(rows and bid==digest([digest(row) for row in rows]),'packing changed measured input batch')
        recipients=[dict(source_task=r['task'],condition=r['condition'],stream=r['stream'],instance_id=r['instance_id']) for r in rows]
        _require(scope.get('recipients',{}).get(bid)==recipients,'packing recipient scope mismatch')
        _require(len(specs)>=p['axis_tile_size'],'packing lacks complete physical tile')
        common={k:specs[0][k] for k in ('site','seed','family','axis_index','operation','axis_sha256')}
        if first_cell is None: first_cell=common
        _require(common==first_cell,'packing heterogeneous first-cell selectors unsupported by frozen invocation')
        _require(scope['dummy_cells'][bid]==[specs[0]],
                 'packing dedicated dummy must measure exactly producer first cell')
        for row in rows:
            key=(row['task'],row['condition'],row['stream'],row['instance_id'])
            _require(key not in measured_rows,'packing duplicate measured input')
            measured_rows[key]=row
        for spec in specs+scope.get('dummy_cells',{}).get(bid,[]):
            _require(re.fullmatch('[0-9a-f]{64}',str(spec.get('axis_sha256'))) is not None,'packing invalid numeric axis digest')
            measured_specs.append(spec)
            if spec['operation']=='interchange':
                _require(len(spec.get('donors',[]))==len(rows),'packing lacks actual mapped donor coverage')
                for donor,row in zip(spec['donors'],rows):
                    mapping=donor.get('mapping',{})
                    _require(re.fullmatch('[0-9a-f]{64}',str(donor.get('cached_donor_sha256'))) is not None
                        and mapping.get('recipient_id')==row['instance_id'],'packing missing source-bound donor map')
                    expected_stream='corrupt' if row['task']=='ioi' or row['stream']=='clean' else 'clean'
                    _require(mapping.get('donor_id')==row['instance_id'] and mapping.get('donor_condition')==row['condition']
                        and mapping.get('donor_stream')==expected_stream,'packing donor convention mismatch')
            for recipient in recipients:
                key=dict(recipient,**{k:spec[k] for k in ('site','seed','family','axis_index','operation')})
                kid=digest(key); expected.append(kid); expected_axes[kid]=spec['axis_sha256']
    comparisons=receipt.get('comparisons',[])
    _require(Counter(expected)==Counter(digest(c['key']) for c in comparisons),'packing incomplete/duplicate comparison coverage')
    nonzero=set()
    for c in comparisons:
        axis=expected_axes[digest(c['key'])]
        _require(c['serial'].get('axis_hash')==c['packed'].get('axis_hash')==axis,'packing changed compared numeric axis')
        for side in ('serial','packed'):
            _finite(c[side].get('head_norm'),'packing perturbation norm')
        if c['serial'].get('head_norm',0)>0 and c['packed'].get('head_norm',0)>0:
            nonzero.add(axis)
        for name in ('intact_margin','patched_margin'):
            left,right=c['serial'][name],c['packed'][name]
            _require(type(left) in (int,float) and type(right) in (int,float)
                and math.isfinite(left) and math.isfinite(right)
                and abs(left-right)<=1e-5+1e-5*abs(left),'packing measured margin disagreement')
        for name in ('intact_argmax','patched_argmax'):
            _require(type(c['serial'][name]) is int and type(c['packed'][name]) is int and c['serial'][name]==c['packed'][name],'packing measured argmax disagreement')
        for side in ('serial','packed'):
            errors=c[side].get('replay_errors',{})
            _require(set(errors)=={'empty','head_self','zero_coefficient'}
                and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1e-5 for v in errors.values()),'packing measured replay invalid')
    _require(len(nonzero)>=2,'packing lacks distinct measured nonzero axes')
    _packing_measurement_scope(measured_rows,measured_specs,measurement)
    return receipt['receipt_sha256']


def _packing_measurement_scope(measured_rows,measured_specs,measurement):
    for frozen in measurement['timing_inputs']:
        k=(frozen['source_task'],frozen['condition'],frozen['stream'],frozen['instance_id'])
        row=measured_rows.get(k); data=frozen['record']['streams'][frozen['stream']]
        _require(row is not None,'packing measured inputs do not cover validation timing scope')
        width=frozen['padded_width']; length=frozen['unpadded_length']
        _require(row['tokens'][:length]==data['tokens'] and len(row['tokens'])==width
            and row['mask']==[1]*length+[0]*(width-length) and row['readout']==frozen['readout'],'packing changed frozen tokens/masks/readouts')
        _require(all(row['record'].get(k)==v for k,v in frozen['record'].items()),'packing changed source record')
        for name in ('expected_token','honest_token','opposite_token'):
            if name in frozen['record']:
                _require(row.get(name)==frozen['record'][name],'packing changed native label')
        _require(row.get('choice_tokens')==frozen['record'].get('choice_tokens'),'packing changed MMLU choices')
    for wanted in measurement.get('axis_scope',[]):
        _require(any(all(spec.get(k)==v for k,v in wanted.items() if k!='axis_reference')
                     for spec in measured_specs),'packing actual axis/site/operation coverage missing')


_PACKING_PROOF_SEAL=object()
_PACKING_AXIS_FIELDS=('site','seed','family','axis_index','operation','axis_sha256')
_PACKING_ROW_FIELDS=('source_task','condition','stream','instance_id','seed','site','family','axis_index','operation')


def _axis_selector(spec):return tuple(_freeze(spec.get(k)) for k in _PACKING_AXIS_FIELDS)


class _PackingProof:
    """Private immutable index minted only after full numeric producer validation."""
    __slots__=('_profile','_rows','_specs','_batches','_observed','source_digest','receipt_sha256','distinct_axes','_sealed')
    def __init__(self,seal,evidence):
        _require(seal is _PACKING_PROOF_SEAL,'packing proof requires independent validation')
        receipt=evidence['runner_receipt'];rows={};specs={};batches={}
        for bid,group in evidence['snapshots'].items():
            for row in group:rows[(row['task'],row['condition'],row['stream'],row['instance_id'])]=row
        for bid,values in receipt['scope']['batches'].items():
            batch=[]
            for value in values:
                spec={k:v for k,v in value.items() if k!='donors'};key=_axis_selector(spec)
                if key not in specs:specs[key]=spec
                batch.append(specs[key])
            batches[bid]=batch
        object.__setattr__(self,'_profile',_freeze_json(copy.deepcopy(receipt['scope']['profile'])))
        object.__setattr__(self,'_rows',_freeze_json(copy.deepcopy(rows)))
        object.__setattr__(self,'_specs',_freeze_json(specs))
        object.__setattr__(self,'_batches',_freeze_json(batches))
        object.__setattr__(self,'_observed',frozenset(tuple(_freeze(c['key'].get(k)) for k in _PACKING_ROW_FIELDS) for c in receipt['comparisons']))
        object.__setattr__(self,'source_digest',digest(evidence))
        object.__setattr__(self,'receipt_sha256',receipt['receipt_sha256'])
        object.__setattr__(self,'distinct_axes',receipt['distinct_axes'])
        object.__setattr__(self,'_sealed',True)
    def __setattr__(self,*args):raise TypeError('validated packing proofs are immutable')
    def __reduce__(self):raise TypeError('validated packing proofs are process-local')
    def check(self,measurement):
        _require(measurement['profile']==self._profile,'packing source/profile mismatch')
        wanted=measurement.get('axis_scope',[]);specs=[]
        for axis in wanted:
            if all(k in axis for k in _PACKING_AXIS_FIELDS):
                value=self._specs.get(_axis_selector(axis));_require(value is not None,'packing actual axis/site/operation coverage missing');specs.append(value)
            else:specs.extend(self._specs.values())
        _packing_measurement_scope(self._rows,specs,measurement)
        source=self._profile.get('source_task') or next(iter(self._rows))[0]
        convention=('none' if not self._profile.get('positive_singleton') else 'frozen_cyclic_different_question_readout') if source=='mmlu' else ('repeated_B_corrupt' if source=='ioi' else 'same_ID_condition_opposite_stream')
        _require(measurement.get('donor_convention',convention)==convention,'packing donor convention mismatch')
        return self.receipt_sha256
    def covers_axes(self,wanted):
        for axis in wanted:
            if all(k in axis for k in _PACKING_AXIS_FIELDS):
                spec=self._specs.get(_axis_selector(axis))
                if spec is None or not all(spec.get(k)==v for k,v in axis.items() if k!='axis_reference'):return False
            elif not any(all(spec.get(k)==v for k,v in axis.items() if k!='axis_reference') for spec in self._specs.values()):return False
        return True
    def observed_requirement(self,requirement):
        seen=[]
        for key in requirement['timing_keys']:
            if len(key)!=12:continue
            values=(key[2],key[10],key[11],key[9],key[4],_freeze(key[5]),key[6],key[7],key[8])
            _require(values in self._observed,'actual measured producer did not cover frozen timing key');seen.append(key)
        return seen


def _validate_packing_proof(evidence,measurement):
    _packing_evidence(evidence,measurement)
    return _PackingProof(_PACKING_PROOF_SEAL,evidence)


def _capture_lane_evidence(evidence, measurement):
    """Validate actual replicated intact capture, without asserting serial parity."""
    import struct
    _require(isinstance(evidence,dict) and evidence.get('kind')=='a3_intact_lane_equivalence_v1'
        and evidence.get('timing_inputs_sha256')==digest(measurement['timing_inputs']), 'capture lane source scope mismatch')
    profile=measurement['profile'];receipts=evidence.get('runner_receipts',[]);snapshots=evidence.get('snapshots',{})
    _require(receipts and len(receipts)==len(snapshots),'capture lane receipts/snapshots missing')
    seen={}
    for receipt in receipts:
        _require(receipt.get('kind')=='a3_intact_lane_consistency_v1' and receipt.get('valid') is True
            and receipt.get('serial_comparison_performed') is False
            and receipt.get('operation')=='readout_capture'
            and receipt.get('receipt_sha256')==digest({k:v for k,v in receipt.items() if k!='receipt_sha256'}),
            'capture lane producer kind/content mismatch')
        _require(receipt.get('numeric_profile')==profile and receipt.get('source_sha256')==profile['source_sha256']
            and receipt.get('profile_id')==digest({k:v for k,v in profile.items() if k!='profile_id'}), 'capture lane profile mismatch')
        bid=receipt['batch_sha256'];rows=snapshots.get(bid,[]);tile=profile['axis_tile_size']
        _require(rows and digest([digest(r) for r in rows])==bid and len(rows)*tile==profile['physical_batch_size']
            and receipt.get('replicated_lanes')==tile and receipt.get('physical_batch_size')==profile['physical_batch_size'],
            'capture lane actual physical geometry mismatch')
        maps=receipt.get('readout_map',[])
        _require(maps==[dict(instance_id=r['instance_id'],source_readout=r['readout'],execution_readouts=[r['readout']]*tile) for r in rows],
            'capture lane readout mapping mismatch')
        refs=receipt.get('head_references',[]);sites=profile.get('sites',list({tuple(r['site']) for r in refs}))
        wanted={(r['instance_id'],tuple(site)) for r in rows for site in sites}
        actual=[(r['instance_id'],tuple(r['site'])) for r in refs]
        _require(len(actual)==len(set(actual)) and set(actual)==wanted,'capture lane head coverage mismatch')
        vectors=evidence.get('head_vectors',{}).get(bid,[]);vector_index={(r['instance_id'],tuple(r['site'])):r for r in vectors}
        _require(len(vector_index)==len(vectors) and set(vector_index)==wanted,'capture lane head vectors missing')
        for ref in refs:
            values=vector_index[(ref['instance_id'],tuple(ref['site']))]['values']
            _require(isinstance(values,list) and values and all(type(x) in (float,int) and math.isfinite(x) for x in values),'capture lane nonfinite head')
            payload=struct.pack('<'+'f'*len(values),*values)
            descriptor=dict(dtype='torch.float32',shape=[len(values)],bytes_sha256=hashlib.sha256(payload).hexdigest())
            _require(ref['vector_sha256']==digest(descriptor) and ref['vector_shape']==[len(values)]
                and ref['dtype']=='torch.float32','capture lane numeric head bytes differ')
        comparisons=receipt.get('comparisons',[])
        expected={(rid,site,lane) for rid,site in wanted for lane in range(1,tile)}
        actual=[(r['instance_id'],tuple(r['site']),r['lane']) for r in comparisons]
        _require(len(actual)==len(set(actual)) and set(actual)==expected,'capture lane duplicate/dummy coverage mismatch')
        references={(r['instance_id'],tuple(r['site'])):r for r in refs}
        for row in comparisons:
            ref=references[(row['instance_id'],tuple(row['site']))]
            _require(row['reference_sha256']==ref['vector_sha256'] and row['readout']==ref['readout']
                and row.get('head_allclose') is True and row.get('argmax_equal') is True,'capture lane measured head/readout failure')
            for key in ('max_abs_head_error','reference_max_abs_head','max_abs_margin_error'):_finite(row[key],'capture lane '+key)
            margin=row['reference_margin'];_require(type(margin) in (int,float) and math.isfinite(margin),'nonfinite capture lane margin')
            _require(row['max_abs_head_error']<=1e-5+1e-5*row['reference_max_abs_head']
                and row['max_abs_margin_error']<=1e-5+1e-5*abs(margin),'capture lane measured disagreement')
        for row in rows:
            key=(row['task'],row['condition'],row['stream'],row['instance_id'])
            _require(key not in seen,'duplicate measured capture input');seen[key]=row
    for frozen in measurement['timing_inputs']:
        key=(frozen['source_task'],frozen['condition'],frozen['stream'],frozen['instance_id']);row=seen.get(key)
        _require(row is not None,'capture lane missing measured input')
        data=frozen['record']['streams'][frozen['stream']];n=frozen['unpadded_length'];width=frozen['padded_width']
        _require(row['tokens'][:n]==data['tokens'] and len(row['tokens'])==width and row['mask']==[1]*n+[0]*(width-n)
            and row['readout']==frozen['readout'] and all(row['record'].get(k)==v for k,v in frozen['record'].items()),
            'capture lane source tokens/masks/records differ')
    _require(len(seen)==len(measurement['timing_inputs']),'capture lane extra measured source scope')
    return digest(evidence)


def project_cost(pilot_receipts: list[dict], workload: dict, ledger: dict, *, packing_proofs=None, runtime_cost=None) -> dict:
    """Return a conservative proposal; incomplete evidence always raises ValueError."""
    _validate_inventory(workload)
    sums=_ledger(ledger,workload['identity'])
    storage=_storage_admission(workload,ledger)
    _require(isinstance(pilot_receipts,list) and pilot_receipts,'successful measured timing receipts required')
    measured=defaultdict(list); startup=[]; receipt_digests=[]; host_peaks=[]
    for receipt in pilot_receipts:
        _require(receipt.get('kind')=='a3_direction_timing_v1' and receipt.get('status')=='completed'
            and receipt.get('exit_code')==0 and type(receipt.get('exit_code')) is int
            and receipt.get('complete') is True,'failed/incomplete measured receipt')
        _require(receipt.get('identity')==workload['identity'],'stale receipt source/model identity')
        _require(receipt.get('hardware')==workload['hardware'],'changed receipt hardware')
        _require(receipt.get('inventory_sha256')==workload['inventory_sha256'],'receipt not bound to frozen target inventory')
        startup.append(_finite(receipt.get('startup_seconds'),'measured startup')+_finite(receipt.get('proof_validation_seconds',0),'measured packing proof validation'))
        host_peaks.append(_integer(receipt.get('host_peak_bytes'),'measured host peak'))
        receipt_sha=digest(receipt);receipt_digests.append(receipt_sha)
        _require(isinstance(receipt.get('measurements'),list) and receipt['measurements'],'missing measured profiles')
        packing=receipt.get('packing_evidence',{})
        checked_packing=set();validated_packing={}
        for m in receipt['measurements']:
            _require(m.get('source_split')=='validation','pilot must retain actual validation measurement scope')
            _require(m.get('synchronized') is True,'unsynchronized timing')
            _require(m.get('cache_fit') is True,'measured cache-fit failure')
            capacity=_integer(m.get('memory_capacity_bytes'),'measured memory capacity')
            cache_capacity=_integer(m.get('cache_capacity_bytes'),'measured cache capacity')
            if m.get('profile',{}).get('axis_tile_size',1)>1 and m.get('operation','').startswith('capture_') and 'capture_lane_equivalence' in m:
                _capture_lane_evidence(m['capture_lane_equivalence'],m)
            elif m.get('profile',{}).get('axis_tile_size',1)>1:
                evidence=packing.get(m.get('packing_id'))
                check_key=(m.get('packing_id'),digest(m.get('timing_inputs')),digest(m.get('axis_scope',[])))
                if check_key not in checked_packing:
                    pid=m.get('packing_id')
                    if pid not in validated_packing:
                        if isinstance(evidence,dict) and evidence.get('kind')=='a3_packing_proof_reference_v1':
                            proof=(packing_proofs or {}).get((receipt_sha,pid))
                            _require(type(proof) is _PackingProof and proof.source_digest==evidence.get('evidence_sha256'),
                                'independently validated completed packing reference required')
                        else:proof=_validate_packing_proof(evidence,m)
                        validated_packing[pid]=proof
                    validated_packing[pid].check(m)
                    checked_packing.add(check_key)
            if m.get('operation')=='serialization':
                shapes=m['profile'].get('serialization_shapes',[])
                _require(shapes and m['profile'].get('serialization_shapes_sha256')==digest(shapes)
                    and Counter(m.get('serialization_shape_ids',[]))==Counter(digest(x) for x in shapes),
                    'incomplete measured serialization shape coverage')
                _require(len(m.get('batch_seconds',[]))>=len(shapes),'short serialization timing coverage')
            samples=m.get('batch_seconds')
            _require(isinstance(samples,list) and samples,'unmeasured operation timing')
            for v in samples: _finite(v,'batch seconds',positive=True)
            expected=list(map(_freeze,m.get('expected_keys',[])))
            observed=list(map(_freeze,m.get('observed_keys',[])))
            _require(Counter(expected)==Counter(observed),'short/duplicate measured row coverage')
            for name in ('cache_bytes','peak_allocated_bytes','peak_reserved_bytes'):
                _integer(m.get(name),name,positive=False)
            _require(capacity>=m['peak_reserved_bytes']>=m['peak_allocated_bytes'],'invalid measured memory/capacity')
            _require(cache_capacity>=max(m['cache_bytes'],workload['storage_requirements']['tiers']['cache_disk']),'full target cache capacity underflow')
            measured[(digest(m.get('profile')),m.get('operation'),digest(m.get('expected_keys',[])),
                      digest(m.get('axis_ids',[])),digest(m.get('axis_scope',[])),digest(m.get('timing_inputs')),m.get('donor_convention'))].append(m)
    completed_startup=0
    if runtime_cost is not None:
        _require(runtime_cost.get('kind')=='a3_completed_host_startup_cost_v1'
            and runtime_cost.get('target_inventory_sha256')==workload['inventory_sha256']
            and runtime_cost.get('execution_authorized') is False and runtime_cost.get('conditional') is True,'completed host cost source/scope/portability differs')
        completed_startup=_finite(runtime_cost.get('seconds'),'completed authentication/index startup')
        _require(runtime_cost.get('guard_seconds') and runtime_cost.get('host_profile'),'completed host guard/profile evidence missing')
        for value in runtime_cost['guard_seconds']:_finite(value,'completed full-union guard seconds',positive=True)
        host_peaks.append(_integer(runtime_cost['peak_host_bytes'],'completed host peak'))
        capacity=_integer(runtime_cost['frozen_host_capacity_bytes'],'frozen host startup capacity')
        _require(max(runtime_cost['peak_host_bytes'],runtime_cost['construction_working_bytes'],runtime_cost['retained_bytes'])<=capacity,
            'completed startup footprint exceeds frozen admitted host capacity')
    storage=_storage_admission(workload,ledger,max(host_peaks))
    total=0; used=[]; reuse_records=[]
    requirement_jobs={rid:job['job_id'] for job in workload['jobs'] for rid in job['requirement_ids']}
    job_work=Counter()
    for requirement in workload['requirements']:
        key=(digest(requirement['profile']),requirement['operation'],digest(requirement['timing_keys']),
             digest(requirement['axis_ids']),digest(requirement['axis_scope']),digest(requirement['timing_inputs']),requirement['donor_convention'])
        good=measured.get(key,[])
        _require(good,'missing shape/operation/axis/row measured profile coverage')
        if requirement['axis_class']:
            _require(all(m.get('axis_class')==requirement['axis_class'] and m.get('nonzero_axis_count',0)>0 for m in good),
                     'prefit requires measured nonzero axis class')
        if requirement['target_keys']!=requirement['timing_keys'] or requirement['axis_class']:
            policy=workload.get('reuse_policy')
            _require(policy==PROFILE_REUSE_POLICY,'unresolved frozen profile reuse policy')
            reuse_records.append(dict(requirement_id=requirement['requirement_id'],
                measured_scope=requirement['timing_keys'],measured_inputs_sha256=digest(requirement['timing_inputs']),
                target_scope_sha256=digest(requirement['target_keys']),target_inventory_sha256=workload['inventory_sha256'],
                profile=requirement['profile'],source_identity=workload['identity'],
                target_unmasked_lengths=requirement['target_unmasked_lengths'],
                measured_unmasked_lengths=requirement['timing_unmasked_lengths'],
                assumptions=policy['assumptions'],uncertainty='target examples unmeasured; fixed 25 percent workload buffer',
                target_rows_are_measured=False))
        seconds=max(max(m['batch_seconds']) for m in good)
        if requirement['operation']=='guard_refresh' and runtime_cost is not None:seconds=max(seconds,max(runtime_cost['guard_seconds']))
        work=_integer(requirement['batches'],'required batches')*seconds
        total+=work
        job_work[requirement_jobs[requirement['requirement_id']]]+=work
        used.append(dict(requirement_id=requirement['requirement_id'],batches=requirement['batches'],batch_seconds=seconds))
    jobs=len(workload['jobs']); _integer(jobs,'job count')
    per_job_startup=max(startup)+completed_startup
    seconds=jobs*per_job_startup+1.25*total+jobs*_finite(workload['finish_reserve_seconds'],'finish reserve')
    job_projections=[dict(job_id=j['job_id'],projected_seconds=per_job_startup+1.25*job_work[j['job_id']]+workload['finish_reserve_seconds'],
        walltime_seconds=math.ceil(per_job_startup+1.25*job_work[j['job_id']]+workload['finish_reserve_seconds']),
        requirement_ids=j['requirement_ids'],depends_on=j['depends_on']) for j in workload['jobs']]
    gpu_hours=seconds*workload['hardware']['count']/3600
    phase=workload['phase']
    envelope=None; envelope_consumed=0
    matching=[e for e in ledger['entries'] if e.get('inventory_sha256')==workload['inventory_sha256']
              and e['state'] in ('reserved','running')]
    if workload['stage']=='fit-select' and workload['frozen_inputs'].get('fits') is not None:
        envelope=ledger.get('fit_validation_envelope')
        _require(isinstance(envelope,dict) and envelope.get('kind')=='a3_fit_validation_envelope_v1',
                 'original fit admission envelope required after fitting')
        _require(envelope.get('envelope_sha256')==digest({k:v for k,v in envelope.items() if k!='envelope_sha256'})
                 and envelope.get('identity')==workload['identity'],'changed original fit envelope identity/bytes')
        upper=envelope.get('upper_inventory')
        _require(isinstance(upper,dict),'original fit upper inventory required')
        _validate_inventory(upper)
        _require(upper['frozen_inputs'].get('fits') is None and upper['identity']==workload['identity']
                 and set(map(_freeze,workload['expected_keys']))<=set(map(_freeze,upper['expected_keys'])),
                 'postfit requirements exceed original fit inventory')
        ids=envelope.get('entry_ids')
        _require(isinstance(ids,list) and ids and len(ids)==len(set(ids)) and set(ids)<=set(ledger['expected_entry_ids']),
                 'missing/duplicate original envelope reservation IDs')
        originals=ledger.get('original_admissions',[])
        _require(isinstance(originals,list) and originals,'independently loaded original admission required')
        _require(len({a.get('id') for a in originals})==len(originals),'duplicate original admission IDs')
        original=[a for a in originals if a.get('id')==envelope.get('admission_id')]
        _require(len(original)==1,'original admission lineage not found')
        original=original[0]
        _require(original.get('kind')=='a3_root_fit_admission_v1'
            and original.get('admission_sha256')==digest({k:v for k,v in original.items() if k!='admission_sha256'})
            and envelope.get('admission_sha256')==original['admission_sha256'],
            'original admission content/reference mismatch')
        _require(original.get('identity')==workload['identity']
            and original.get('upper_inventory_sha256')==upper['inventory_sha256']
            and original.get('max_gpu_hours')==envelope.get('max_gpu_hours'),
            'envelope source/upper inventory/ceiling differs from original admission')
        _finite(original.get('max_gpu_hours'),'original admission ceiling',positive=True)
        anchors=original.get('reservation_ids')
        _require(isinstance(anchors,list) and anchors and len(anchors)==len(set(anchors)) and set(anchors)<=set(ids),
            'nonempty original reservation lineage required in envelope')
        linked_ids=set()
        for entry in ledger['entries']:
            lineage=entry.get('reservation_lineage',{})
            same_id=lineage.get('admission_id')==original['id']
            same_digest=lineage.get('admission_sha256')==original['admission_sha256']
            if same_id or same_digest:
                # Contradictory references are not unrelated work, regardless
                # of reservation state or a consistently recomputed self-hash.
                _require(same_id and same_digest,'conflicting original admission ID/digest in reservation lineage')
                linked_ids.add(entry['id'])
        _require(linked_ids==set(ids),'original admission reservations omitted from envelope')
        for entry in ledger['entries']:
            if entry['id'] in ids:
                _require(entry['phase']=='M2' and entry.get('subphase')=='directions','wrong fit envelope phase')
                lineage=entry.get('reservation_lineage',{})
                _require(lineage.get('kind')=='a3_reservation_lineage_v1'
                    and lineage.get('lineage_sha256')==digest({k:v for k,v in lineage.items() if k!='lineage_sha256'}),
                    'reservation lineage missing/changed')
                if entry['id'] in anchors:
                    _require(entry.get('inventory_sha256')==upper['inventory_sha256'],'original envelope anchor is not original upper inventory')
                expected=dict(reservation_id=entry['id'],admission_id=original['id'],
                    admission_sha256=original['admission_sha256'],upper_inventory_sha256=upper['inventory_sha256'],
                    inventory_sha256=entry.get('inventory_sha256'),identity=workload['identity'],
                    max_gpu_hours=original['max_gpu_hours'],reserved_gpu_hours=entry['reserved_gpu_hours'])
                _require(all(lineage.get(k)==v for k,v in expected.items())
                    and entry.get('inventory_sha256') in (upper['inventory_sha256'],workload['inventory_sha256']),
                    'unrelated reservation inventory/source/admission lineage')
                envelope_consumed+=entry['reserved_gpu_hours']
        _require({e['id'] for e in matching}<=set(ids),'current validation reservation omitted from envelope')
    _require(len(matching)<=1,'duplicate active workload reservations')
    if matching:
        _require(matching[0]['phase']==phase and matching[0].get('subphase')=='directions','wrong matching reservation phase')
    additional=max(0,gpu_hours-(matching[0]['reserved_gpu_hours'] if matching else 0))
    if envelope:
        _require(envelope_consumed+additional<=_finite(envelope.get('max_gpu_hours'),'original fit envelope budget'),
                 'remaining validation exceeds original fit admission envelope')
    m1=sums['M1']+(additional if phase=='M1' else 0)
    dm1=sums['direction_M1']+(additional if phase=='M1' else 0)
    dm2=sums['direction_M2']+(additional if phase=='M2' else 0)
    all_a3=sums['all']+sums['contingency_remaining']+additional
    _require(dm1<=.5,'direction M1 exceeds 0.5 GPU hours')
    _require(m1<=2,'all M1 exceeds 2 GPU hours')
    _require(dm2<=9,'direction M2 exceeds 9 GPU hours')
    _require(all_a3<=40,'all A3 exceeds 40 GPU hours including contingency')
    if 'deadline_remaining_seconds' in ledger:
        _require(seconds<=_finite(ledger['deadline_remaining_seconds'],'deadline remaining'),'projected jobs exceed deadline')
    return dict(kind='a3_direction_cost_proposal',admitted=True,execution_authorized=False,
        inventory_sha256=workload['inventory_sha256'],receipt_sha256s=receipt_digests,
        ledger_sha256=ledger['snapshot_sha256'],phase=phase,subphase='directions',storage_admission=storage,
        projected_seconds=seconds,projected_gpu_hours=gpu_hours,additional_gpu_hours=additional,proposed_walltime_seconds=max(j['walltime_seconds'] for j in job_projections),jobs=job_projections,
        required_job_count=jobs,startup_seconds=per_job_startup,completed_host_startup_cost=runtime_cost,measured_work_seconds=total,
        finish_reserve_seconds=workload['finish_reserve_seconds'],existing_gpu_hours=sums['all'],
        existing_reserved_gpu_hours=sums['all'],existing_actual_gpu_hours=sums['actual_all'],actual_unknown_entries=sums['actual_unknown_entries'],
        direction_m1_gpu_hours=dm1,all_m1_gpu_hours=m1,direction_m2_gpu_hours=dm2,
        all_a3_gpu_hours=all_a3,requirements=used,reuse_records=reuse_records,fit_validation_consumed_gpu_hours=envelope_consumed,
        conditional_proposal=runtime_cost is not None and runtime_cost.get('conditional') is not False or any(x['profile']['axis_tile_size']>1 for x in workload['requirements']),
        packed_execution_blocker='Unit F reviewed reuse adapter required; exact-scope runner unchanged' if any(x['profile']['axis_tile_size']>1 for x in workload['requirements']) else None,
        missing_execution_prerequisites=['matching root RS reservation','live source/registry/ledger recheck']+
            (['bounded allocated-host authentication/index startup'] if runtime_cost is not None and runtime_cost.get('conditional') is not False else []))


def execution_membership(source,split,condition,instance_ids,physical_recipients):
    """Execution aliases are shared by both streams of an authenticated source."""
    ids=list(instance_ids);dummy={}
    _require(ids and len(ids)==len(set(ids)) and len(ids)<=physical_recipients,'invalid scientific recipient chunk')
    while len(ids)<physical_recipients:
        alias='a3-dummy:'+digest([source,split,condition,list(instance_ids),len(ids)])
        dummy[alias]=instance_ids[0];ids.append(alias)
    return ids,dummy
