"""Staged direction orchestration. Scientific algebra remains in reviewed cores.

All model access is behind fresh source, protection and root-reservation checks.
Completed objects are byte-linked immutable directories. CPU proposals never grant
execution authority. Runtime callbacks are explicit test injection, not final runs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
_PROCESS_START_TIME=time.time()
from collections import Counter
from dataclasses import replace

import numpy as np
import torch
from component_analysis import a3_direction_artifacts as artifacts
from component_analysis import a3_direction_pipeline as pipeline
from component_analysis import a3_direction_runner as runner
from component_analysis import a3_direction_workload as workload
from component_analysis import ladder_pipeline as ladder
from dataset import user_inversion_pipeline as common

require=artifacts.require


def publish_object(path, payload):
    """Byte-complete nonnumeric operational evidence, using the shared publisher."""
    def writer(root):
        with (root/'payload.json').open('w') as stream:
            json.dump(payload,stream,sort_keys=True,allow_nan=False);stream.write('\n')
        artifacts._finish(root)
    common.publish(Path(path),writer)
    return payload


def read_object(path):
    root=Path(path); artifacts._complete(root)
    require({p.name for p in root.iterdir()}=={'payload.json','COMPLETE.json'},'unexpected operational artifact children')
    return artifacts._strict_json(root/'payload.json')


def object_reference(path):
    root=Path(path); artifacts._complete(root)
    return dict(path=str(root.resolve()),files={p.name:dict(sha256=common.file_hash(p),nbytes=p.stat().st_size)
        for p in root.iterdir() if p.is_file()})


def read_bundle(path):
    root=Path(path); artifacts._complete(root)
    manifest=artifacts._strict_json(root/'manifest.json')
    return artifacts.read_bundle(path,expected=manifest['metadata'])


def source_batches(design, source, split, ids, condition, stream, profile, *, dummy_sources=None):
    """Resolve ONLY requested source IDs/split; pad to the frozen physical width."""
    from component_analysis.ladder_tasks import task_batches
    rows=workload._source_rows(design,source,split)
    indexed={r['instance_id']:r for r in rows if r.get('condition',source)==condition}
    dummy_sources=dummy_sources or {}
    require(len(ids)==len(set(ids)) and all(dummy_sources.get(i,i) in indexed for i in ids),'unknown/duplicate requested source membership')
    require(all(i.startswith('a3-dummy:') and i in ids and original in ids for i,original in dummy_sources.items()),'invalid execution-only dummy aliases')
    selected=[]
    for rid in ids:
        original=dummy_sources.get(rid,rid); row=dict(copy.deepcopy(indexed[original]),task=source)
        if rid in dummy_sources:
            row.update(instance_id=rid,execution_dummy=dict(duplicate_of=original,source_sha256=workload.digest(indexed[original])))
        selected.append(row)
    base=profile['physical_batch_size']//profile['axis_tile_size']
    require(base>0 and len(ids)==base,'requested batch differs from actual frozen physical geometry')
    if source in ('ioi','mmlu'):
        batches=task_batches(selected,batch_size=base,stream=stream)
    else:
        batches=ladder.batches(selected,stream,batch_size=base)
    result=[]
    for batch in batches:
        require(batch.input_ids.shape[1]<=profile['padded_width'],'frozen width truncates source')
        padding=profile['padded_width']-batch.input_ids.shape[1]
        result.append(replace(batch,input_ids=torch.nn.functional.pad(batch.input_ids,(0,padding),value=0),
            attention_mask=torch.nn.functional.pad(batch.attention_mask,(0,padding),value=0)))
    return result


def capture_fit_cache(model, design, protocol, *, output, batch_resolver=source_batches, guard=None):
    """Convert bounded runner sinks to the exact complete train-cache schema.

    Fit capture uses explicit singleton physical geometry across every condition,
    task and site; no short batch is mislabeled. All capture values are CPU fp32.
    """
    metadata,layout=pipeline._fit_contract(design,protocol)
    profile=metadata['identity']['numeric_profile']; arrays={}; seen=set(); projections={}
    for item in layout:
        width=protocol.get('workload',{}).get('head_width')
        if width is not None:
            for name in item['activations'].values():
                arrays[name]=np.empty((len(item['instance_ids']),2,width),dtype=np.float32)
    expected={(item['task'],tuple(item['site']),c,rid,s) for item in layout
        for c in pipeline.CONDITIONS for rid in item['instance_ids'] for s in pipeline.STREAMS}
    def sink(chunk):
        require(chunk['identity']==metadata['identity'],'changed actual capture identity')
        for projection in chunk['projections']:
            site=tuple(projection['site']); value=projection['value'].detach().float().cpu().numpy().copy()
            require(site not in projections or np.array_equal(projections[site],value),'projection changed during capture')
            projections[site]=value
        for row in chunk['rows']:
            for head in row['heads']:
                site=tuple(head['site']); key=(row['task'],site,row['condition'],row['instance_id'],row['stream'])
                if site not in {tuple(x) for x in design['tasks'][row['task']]['direction_sites']}: continue
                require(key in expected and key not in seen,'duplicate/unexpected train capture coverage')
                seen.add(key)
                item=next(x for x in layout if x['task']==row['task'] and tuple(x['site'])==site)
                value=head['value'].detach().float().cpu().numpy()
                name=item['activations'][row['condition']]
                if name not in arrays: arrays[name]=np.empty((len(item['instance_ids']),2,len(value)),dtype=np.float32)
                require(arrays[name].shape[-1]==len(value),'changed train head width')
                arrays[name][item['instance_ids'].index(row['instance_id']),pipeline.STREAMS.index(row['stream'])]=value
    for task,spec in design['tasks'].items():
        batches=[]
        for c in pipeline.CONDITIONS:
            for s in pipeline.STREAMS:
                for rid in spec['fit_ids']:
                    batches.extend(batch_resolver(design,task,'train',[rid],c,s,profile))
        if guard: guard()
        runner.capture_readouts(model,batches,sites=metadata['identity']['sites'],sink=sink,identity=metadata['identity'])
    require(seen==expected,'incomplete train capture coverage')
    for item in layout:
        require(tuple(item['site']) in projections,'missing train projection')
        arrays[item['projection']]=projections[tuple(item['site'])]
    artifacts.write_bundle(output,metadata,arrays)
    return metadata


def load_selected_axes(path, selected=None):
    metadata,arrays=read_bundle(path)
    if selected is not None: require(metadata==selected,'changed selected metadata')
    require(metadata['kind']=='a3_direction_selection' and metadata['selection_split']=='validation','completed validation selection required')
    axes={}
    for name,receipt in metadata['axes'].items():
        geometry=metadata['geometries'][receipt['geometry']]
        require(geometry['status']=='fitted','unfitted selected geometry')
        axis={k:torch.from_numpy(np.array(arrays[v],dtype=np.float32,copy=True)) for k,v in geometry['arrays'].items()}
        axis.update({k:torch.from_numpy(np.array(arrays[v],dtype=np.float32,copy=True)) for k,v in receipt['arrays'].items()})
        axis.update(rank=geometry['rank'],sigma_fit=receipt['sigma_fit'],projected_variance=receipt['projected_variance'])
        require(runner.axis_identity(axis)==receipt['sha256'],'selected numeric axis identity mismatch')
        axes[name]=axis
    return axes


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment',required=True,choices=('directions',))
    p.add_argument('--stage',required=True,choices=('prepare','pilot','fit','select','assess','summarize'))
    for name in ('design','commit','work-dir'): p.add_argument('--'+name,required=True)
    p.add_argument('--action'); p.add_argument('--panel',choices=('calibration','assessment'))
    p.add_argument('--pilot-part',choices=('prefit','selected'))
    p.add_argument('--inventory-stage',choices=workload.STAGES)
    for name in ('a1-design','a1-selected','matched-root','historical-csv','root-ruling','execution-settings',
                 'inventory','ledger-snapshot','admission','reservation','fit-cache','fits','validation-root','selected','shard-id'):
        p.add_argument('--'+name)
    p.add_argument('--pilot-receipts',nargs='+'); p.add_argument('--registry',action='append',default=[])
    p.add_argument('--finish-reserve-seconds',type=float)
    p.add_argument('--dry-run',action='store_true'); p.add_argument('--resume',action='store_true'); p.add_argument('--final',action='store_true')
    return p


def validate_arguments(args):
    allowed={'prepare':('freeze','inventory','admit'),'fit':('capture','solve'),'select':('score','freeze')}
    if args.stage in allowed:
        if args.stage=='prepare' and args.action is None: args.action='freeze'
        require(args.action in allowed[args.stage],'unknown stage/action combination')
    else: require(args.action is None,'action forbidden for this stage')
    require((args.stage=='assess')==(args.panel is not None),'panel only and always required for assess')
    require((args.stage=='pilot')==(args.pilot_part is not None),'pilot part only and always required for pilot')
    require(not args.final or args.stage=='summarize','final only valid for summarize')
    require((args.stage=='prepare' and args.action=='inventory')==(args.inventory_stage is not None),'inventory stage only required for prepare inventory')
    require(re.fullmatch('[0-9a-f]{40}',args.commit) is not None,'full immutable execution commit required')


def main(argv=None, *, tokenizer=None, model_loader=None):
    args=parser().parse_args(argv); validate_arguments(args)
    return dispatch(args,tokenizer=tokenizer,model_loader=model_loader)



def freeze_operational_contract(design, protocol, settings):
    """Freeze metadata-derived widths and concrete physical settings before access.

    ``settings`` comes from a root-supplied local configuration, not CLI count
    overrides. Fit singletons share a global train/timing width; scores retain
    task/split widths and explicitly describe physical axis replication.
    """
    cfg=copy.deepcopy(settings)
    require(design.get('injected') is True or 'task_order' in protocol,'production requires explicit frozen task_order')
    protocol.setdefault('task_order',sorted(design['tasks']))
    require(all(not str(r['instance_id']).startswith('a3-dummy:') for rows in design['access_rows'].values() for r in rows),'scientific IDs collide with execution alias namespace')
    required={'microbatch_size','axis_tile_size','head_width','hidden_size','num_layers','vocabulary_size',
              'dtype_bytes','hardware','warmup_batches','serialization_batches','finish_reserve_seconds',
              'probe_max_bytes','dtype','backend','jobs'}
    optional={'axis_tile_sizes'}
    require(required<=set(cfg) and set(cfg)<=required|optional,'exact validated execution settings fields required')
    for k in required-{'hardware','dtype','backend','finish_reserve_seconds'}:
        require(type(cfg[k]) is int and cfg[k]>= (0 if k in ('warmup_batches','serialization_batches') else 1),'invalid execution '+k)
    require(cfg['hidden_size']%cfg['head_width']==0,'invalid model geometry')
    require(all(site[1]<cfg['num_layers'] and site[2]<cfg['hidden_size']//cfg['head_width'] for spec in design['tasks'].values() for site in spec['direction_sites']),'frozen site outside concrete model geometry')
    require(design['injected'] or cfg['jobs']>=2,'production must count separate GPU job startups around CPU fitting and power')
    tiles=cfg.get('axis_tile_sizes',{})
    require(isinstance(tiles,dict) and set(tiles)<=set(workload.STAGES) and all(type(v) is int and v>0 for v in tiles.values()),'invalid frozen stage axis tiles')
    for a,b in (('prefit','fit-select'),('selected-pilot','remaining')):
        require(tiles.get(a,cfg['axis_tile_size'])==tiles.get(b,cfg['axis_tile_size']),'pilot/target physical tiles must match')
    cfg['jobs_by_stage']={stage:(1 if stage in ('prefit','selected-pilot') else cfg['jobs']) for stage in workload.STAGES}
    require(type(cfg['finish_reserve_seconds']) in (int,float) and math.isfinite(cfg['finish_reserve_seconds']) and cfg['finish_reserve_seconds']>=0,'invalid finish reserve')
    require(set(cfg['hardware'])=={'gpu','count'} and isinstance(cfg['hardware']['gpu'],str) and cfg['hardware']['gpu']
        and type(cfg['hardware']['count']) is int and cfg['hardware']['count']==1,'one explicitly named device required')
    require(cfg['dtype'] in ('torch.float32','torch.bfloat16','torch.float16') and isinstance(cfg['backend'],str) and cfg['backend'],'invalid dtype/backend')
    require(cfg['dtype_bytes']=={'torch.float32':4,'torch.bfloat16':2,'torch.float16':2}[cfg['dtype']],'dtype byte width mismatch')
    require(design['injected'] or (cfg['dtype']=='torch.bfloat16' and cfg['backend']=='sdpa'),'production uses the frozen native BF16 SDPA loader')
    tasks=list(design['tasks'])+['ioi','mmlu']; widths={}
    for task in tasks:
        widths[task]={}
        for split in ('train','validation','assessment'):
            if task in ('ioi','mmlu') and split=='train': continue
            rows=workload._source_rows(design,task,split)
            require(rows,'empty frozen source membership '+task+' '+split)
            widths[task][split]=1+max(workload._length(r,s) for r in rows for s in r['streams'])
    train_width=max(widths[t][s] for t in design['tasks'] for s in ('train','validation'))
    for t in design['tasks']: widths[t]['train']=train_width
    for t in tasks:
        score_width=max(widths[t]['validation'],widths[t]['assessment'])
        widths[t]['validation']=score_width; widths[t]['assessment']=score_width
    cfg['train_microbatch_size']=1; cfg['pad_tail_batches']=True;cfg['account_runtime_guards']=True
    cfg['widths']=widths; cfg['reuse_policy']=copy.deepcopy(workload.PROFILE_REUSE_POLICY)
    probe=cfg.pop('probe_max_bytes'); dtype=cfg.pop('dtype'); backend=cfg.pop('backend')
    protocol['numeric_profile'].update(dtype=dtype,backend=backend)
    protocol['workload']=cfg
    parent=design['a1_identity']
    source=dict(commit=protocol['commit'],code_hashes=copy.deepcopy(protocol['code_hashes']),
        a1_identity=copy.deepcopy(parent),parent_evidence=copy.deepcopy(design['parent_evidence']),
        matched_source_hashes=copy.deepcopy(parent['source_hashes']),
        **{k:copy.deepcopy(parent[k]) for k in ('grader_sha256','model','model_revision','tokenizer_revision','tokenizer_identity')})
    def profile(width,n=1,tile=1):
        return dict(padded_width=width,physical_batch_size=n*tile,axis_tile_size=tile,dtype=dtype,backend=backend,
            model=parent['model'],model_revision=parent['model_revision'],source_sha256=ladder.design._hash(protocol['code_hashes']))
    union=[]
    for task in protocol['task_order']:
        spec=design['tasks'][task]
        for site in spec['direction_sites']:
            if site not in union: union.append(copy.deepcopy(site))
    source['numeric_profile']=dict(profile(train_width),source_task='mechanism_train_union',sites=union,
        positive_singleton=False,capture_scope='requested_head_union')
    protocol['fit_cache']=dict(capture_identity=source,probe_max_bytes=probe,
        execution_policy='singleton captures; common train and validation-timing padded width; no scientific dummy rows')
    groups=[]
    # Groups own singleton recipient execution profiles. Axis packing is scored
    # under the separately enumerated workload profile and checked on publication.
    for ti,task in enumerate(protocol['task_order']):
        spec=design['tasks'][task]
        for si,site in enumerate(spec['direction_sites']):
            for source_task in (task,'ioi','mmlu'):
                groups.append(dict(group_id=f't{ti}s{si}_{source_task}',analysis_task=task,source_task=source_task,
                    site=copy.deepcopy(site),numeric_profile=dict(profile(widths[source_task]['validation'],cfg['microbatch_size'],tiles.get('fit-select',cfg['axis_tile_size'])),
                        source_task=source_task,sites=[copy.deepcopy(site)],positive_singleton=False,capture_scope='requested_head_union'),
                    rows_per_shard=cfg['axis_tile_size']*len(pipeline.STREAMS)*len(pipeline.CONDITIONS)))
    protocol['selection_cache']=dict(groups=groups)
    if not design['injected']:
        from huggingface_hub import hf_hub_download
        model_config_path=Path(hf_hub_download(parent['model'],'config.json',revision=parent['model_revision'],local_files_only=True))
        require(model_config_path.parent.name==parent['model_revision'],'local model config revision differs')
        validate_model_metadata(artifacts._strict_json(model_config_path),cfg)
        protocol['model_config_identity']=dict(path=str(model_config_path.absolute()),sha256=common.file_hash(model_config_path),
            snapshot=str(model_config_path.parent.absolute()),model_revision=parent['model_revision'])


CANONICAL_LEDGER=ladder.PRIMARY/'docs/research/specificity-ladder/ledger.json'
RESERVATION_FIELDS=('id','job_id','cluster','account','partition','gpus','requested_minutes',
                    'reserved_gpu_hours','source_commit','output_dir','manifest_hash')


def normalize_ledger(mapping_path, *, identity, injected=False, include_envelope=True, refresh_deadline=None):
    """Read RS's real schema and independently byte-checked root phase mapping.

    Root mappings bind immutable original reservation facts. RS reconciliation
    may change status and actual_seconds; those live facts never refund budget.
    A newly unknown entry blocks until root publishes a new complete mapping.
    """
    origin_path=Path(mapping_path);mapping,active_path,chain,waited=_current_root_mapping(origin_path,injected=injected,refresh_deadline=refresh_deadline)
    require(mapping.get('kind')=='a3_root_ledger_mapping_v1','completed root ledger mapping required')
    live_path=Path(mapping['ledger_path']).resolve()
    require(injected or live_path==CANONICAL_LEDGER.resolve(),'canonical live RS ledger required')
    snapshot_path=Path(mapping.get('ledger_snapshot_path',live_path))
    require(snapshot_path.is_file() and common.file_hash(snapshot_path)==mapping['ledger_sha256'],'original ledger snapshot bytes changed')
    original=artifacts._strict_json(snapshot_path); live=artifacts._strict_json(live_path)
    require(type(mapping['max_age_seconds']) in (int,float) and 0<mapping['max_age_seconds']<=900,'invalid live ledger freshness bound')
    require(injected or 'ledger_snapshot_path' in mapping and snapshot_path.resolve()!=live_path,'production requires preserved original ledger snapshot')
    expected=mapping['expected_entry_ids']; originals=original['reservations']; current=live['reservations']
    require(len(expected)==len(set(expected)) and len({r['id'] for r in originals})==len(originals)
        and len({r['id'] for r in current})==len(current)
        and set(expected)=={r['id'] for r in originals}=={r['id'] for r in current},'unknown/missing RS reservation mapping')
    mappings=mapping['entries']; require(len(mappings)==len(expected) and {r['reservation_id'] for r in mappings}==set(expected),'incomplete phase mapping')
    original_index={r['id']:r for r in originals}; live_index={r['id']:r for r in current}; entries=[]
    for item in mappings:
        rid=item['reservation_id']; old=original_index[rid]; now=live_index[rid]
        require(all(old.get(k)==now.get(k)==item['actual_entry'].get(k) for k in RESERVATION_FIELDS),'changed immutable actual reservation identity')
        hours=now['reserved_gpu_hours']
        require(type(hours) in (int,float) and math.isfinite(hours) and hours>=0
            and hours==round(now['gpus']*now['requested_minutes']/60,4)
            and hours==item['original_reserved_gpu_hours'],'original reserved GPU hours mismatch')
        require(item['experiment'] in ('A1','A2','A3'),'unmapped experiment ownership')
        if item['experiment']!='A3': continue
        require(item.get('phase') in ('M1','M2','M3','M4','M5','contingency'),'unmapped A3 phase')
        status=str(now['status']).lower()
        aliases={'completed':'completed','failed':'failed','cancelled':'failed','timeout':'failed','out_of_memory':'failed',
                 'reserved':'reserved','pending':'reserved','running':'running'}
        require(status in aliases,'unsupported live RS reservation status')
        seconds=now.get('actual_seconds')
        require(seconds is None or type(seconds) in (int,float) and math.isfinite(seconds) and seconds>=0,'invalid actual seconds')
        entries.append(dict(id=rid,phase=item['phase'],subphase=item.get('subphase'),state=aliases[status],
            reserved_gpu_hours=hours,actual_gpu_hours=None if seconds is None else seconds*now['gpus']/3600,
            inventory_sha256=item.get('inventory_sha256'),reservation_lineage=copy.deepcopy(item.get('reservation_lineage',{})),actual_entry=now))
    admission_refs=mapping.get('original_admission_references')
    require(injected or isinstance(admission_refs,dict),'production mapping must bind original admission file bytes')
    if admission_refs is not None:
        require(set(admission_refs)==set(mapping['original_admission_paths']) and all(object_reference(p)==admission_refs[p] for p in admission_refs),'original admission byte references changed')
    admissions=[read_object(p) for p in mapping['original_admission_paths']]
    require(len({x['id'] for x in admissions})==len(admissions),'duplicate original admission paths')
    for admission in admissions:
        require(admission['admission_sha256']==workload.digest({k:v for k,v in admission.items() if k!='admission_sha256'}),'original admission bytes/content mismatch')
    digest=common.file_hash(live_path)
    result=dict(kind='a3_root_ledger_snapshot_v1',root_supplied=True,snapshot_sha256=digest,current_snapshot_sha256=digest,
        snapshot_path=str(live_path),original_snapshot_path=str(snapshot_path.resolve()),snapshot_time=time.time(),age_seconds=0,max_age_seconds=mapping['max_age_seconds'],
        expected_identity=identity,entries=entries,expected_entry_ids=[e['id'] for e in entries],
        original_admissions=admissions,storage_capacities=copy.deepcopy(mapping['storage_capacities']),
        contingency_gpu_hours=mapping['contingency_gpu_hours'],original_mapping_reference=object_reference(origin_path),active_mapping_reference=object_reference(active_path),
        mapping_lineage_references=chain,mapping_refresh_wait_seconds=waited)
    if include_envelope and 'fit_validation_envelope_path' in mapping: result['fit_validation_envelope']=read_object(mapping['fit_validation_envelope_path'])
    return result


def packing_evidence(receipt, batches):
    snapshots={}
    for batch in batches:
        rows=[]
        for i,rid in enumerate(batch.ids):
            rows.append(dict(tokens=batch.input_ids[i].tolist(),mask=batch.attention_mask[i].tolist(),
                readout=int(batch.readout[i]),record=batch.records[i],task=batch.task,condition=batch.condition,
                stream=batch.stream,instance_id=rid,expected_token=int(batch.expected_token[i]),
                honest_token=int(batch.honest_token[i]),opposite_token=int(batch.opposite_token[i]),
                choice_tokens=None if batch.choice_tokens is None else batch.choice_tokens[i].tolist()))
        snapshots[runner._digest([runner._digest(r) for r in rows])]=rows
    return dict(runner_receipt=copy.deepcopy(receipt),snapshots=snapshots)


def _mask_branch(row):
    mask=row['mask']; n=sum(mask)
    require(mask==[1]*n+[0]*(len(mask)-n),'reuse requires validated right padding')
    return 'unmasked' if n==len(mask) else 'right-padded'


def freeze_profile_reuse(output, *, measured_path, batch, cells, axes, capture_index, policy, axis_class=False,runtime_profile=None,validated_proof=None):
    """Attest distinct target scope without re-signing any measured receipt.

    This is an equivalence contract, not model execution authority. Admission and
    actual target positive/replay controls remain separate mandatory checks.
    Reuse deliberately rejects mask branches not exercised by the calibration.
    """
    require(policy==workload.PROFILE_REUSE_POLICY,'unreviewed profile reuse policy')
    if validated_proof is None:measured=_validated_measurement(measured_path)
    else:
        require(type(validated_proof) is _CompletedPackingProof and validated_proof.pid==os.getpid()
            and Path(validated_proof.path).resolve()==Path(measured_path).resolve(),'validated measured proof/path mismatch')
        measured=validated_proof.metadata
    require(measured.get('runtime_profile')==runtime_profile and (runtime_profile is not None or measured.get('injected') is True),'measured/target runtime kernel profile differs')
    receipt=measured['evidence']['runner_receipt']; profile=receipt['scope']['profile']
    require(profile['physical_batch_size']==len(batch.ids)*profile['axis_tile_size']
        and profile['padded_width']==batch.input_ids.shape[1],'reuse actual target geometry mismatch')
    source_specs=[c for specs in receipt['scope']['batches'].values() for c in specs]
    target=[runner._cell_scope(batch,c,axes,capture_index) for c in cells]
    for cell in target:
        wanted=('site','operation') if axis_class else ('site','seed','family','axis_index','operation','axis_sha256')
        require((validated_proof.proof.covers_axes([{k:cell[k] for k in wanted}]) if validated_proof is not None
            else any(all(spec[k]==cell[k] for k in wanted) for spec in source_specs)),'reuse target axis/site/operation not measured')
        require(not axis_class or bool(torch.linalg.vector_norm(axes[next(c['axis'] for c in cells if runner.axis_identity(axes[c['axis']])==cell['axis_sha256'])]['v'])>0),'zero prefit timing axis')
    rows=packing_evidence(dict(),[batch])['snapshots']; bid=next(iter(rows))
    measured_rows=[row for group in measured['evidence']['snapshots'].values() for row in group]
    require({(r['task'],_mask_branch(r)) for r in rows[bid]}<={(r['task'],_mask_branch(r)) for r in measured_rows},'reuse target backend mask branch was not measured')
    body=dict(kind='calibrated_direction_profile_reuse_v1',policy=copy.deepcopy(policy),numeric_profile=profile,
        measured_reference=(object_reference(measured_path) if validated_proof is None else validated_proof.reference),measured_path=str(Path(measured_path).resolve()),
        measured_receipt_sha256=receipt['receipt_sha256'],target_batch_sha256=bid,target_scope=target,
        target_snapshots=rows[bid],target_rows_are_measured=bid in receipt['scope']['batches'],
        target_execution_is_pilot=False,axis_class=bool(axis_class),runtime_profile=copy.deepcopy(runtime_profile),
        measured_lengths=[sum(r['mask']) for r in measured_rows],target_lengths=[sum(r['mask']) for r in rows[bid]],
        uncertainty='target examples unmeasured; preserve fixed 25 percent workload buffer',
        controls='target source-bound positives and replay measurements required')
    publish_object(output,body)
    return body


def _validated_reuse_body(identity,batch,body,measured,*,proof=None):
    require(body.get('kind')=='calibrated_direction_profile_reuse_v1' and type(body.get('target_rows_are_measured')) is bool and body.get('target_execution_is_pilot') is False
        and body.get('policy')==workload.PROFILE_REUSE_POLICY,'invalid target profile reuse attestation')
    require(body['numeric_profile']==identity['numeric_profile'],'reuse target numeric profile changed')
    require(body.get('runtime_profile')==identity.get('runtime_profile'),'reuse actual runtime kernel profile changed')
    require(measured['evidence']['runner_receipt']['receipt_sha256']==body['measured_receipt_sha256'],'reuse measured receipt changed')
    require(measured.get('runtime_profile')==body.get('runtime_profile'),'reuse measured runtime kernel profile changed')
    snapshots=packing_evidence({},[batch])['snapshots']; bid=next(iter(snapshots))
    require(body['target_batch_sha256']==bid and body['target_snapshots']==snapshots[bid],'reuse target inputs changed')
    require(body['target_rows_are_measured']==(bid in measured['evidence']['runner_receipt']['scope']['batches']),'measured versus target input label changed')
    # Recompute producer invariants; COMPLETE only binds bytes, not semantics.
    profile=measured['evidence']['runner_receipt']['scope']['profile']
    require(profile==identity['numeric_profile'],'reuse measured/target physical profile differs')
    specs=[c for values in measured['evidence']['runner_receipt']['scope']['batches'].values() for c in values]
    wanted=('site','operation') if body['axis_class'] else ('site','seed','family','axis_index','operation','axis_sha256')
    if proof is not None:
        require(type(proof) is _CompletedPackingProof and proof.proof.covers_axes([{k:cell[k] for k in wanted} for cell in body['target_scope']]),'reuse target numeric scope not measured')
    else:
        for cell in body['target_scope']:require(any(all(spec[k]==cell[k] for k in wanted) for spec in specs),'reuse target numeric scope not measured')
    measured_rows=[r for values in measured['evidence']['snapshots'].values() for r in values]
    require({(r['task'],_mask_branch(r)) for r in snapshots[bid]}<={(r['task'],_mask_branch(r)) for r in measured_rows},'reuse target mask branch changed')
    return body['target_scope']


def execute_shards(inventory, shard_root, *, identity, producer, guard, resume=False, shard_id=None):
    """Atomic exact-key publication with refresh-before-resume semantics."""
    shards=inventory['shards']
    require(shard_id is None or any(s['shard_id']==shard_id for s in shards),'unknown inventory shard ID')
    completed=[]
    for shard in shards:
        if shard_id is not None and shard['shard_id']!=shard_id: continue
        guard()
        target=Path(shard_root)/shard['shard_id']
        actual_identity=identity(shard) if callable(identity) else identity
        if target.exists():
            require(resume,'existing output requires explicit resume')
            artifacts.read_completed_shards(dict(shards=[shard]),shard_root,identity=actual_identity)
            completed.append(dict(shard_id=shard['shard_id'],reused=True,reference=object_reference(target)))
            continue
        rows,execution=producer(shard)
        guard()
        artifacts.publish_shard(target,identity=actual_identity,expected_keys=shard['expected_keys'],rows=rows,execution=execution)
        completed.append(dict(shard_id=shard['shard_id'],reused=False,reference=object_reference(target)))
    return completed


def validate_reservation(path, *, ledger, inventory, work_dir, injected=False, subphase='directions',
                         inventory_validator=None, subphase_limits=None, authority_context=None,
                         requested_scope=None, requested_keys=None, inventory_path=None, _context_sink=None,
                         allocation_reader=None, require_allocation=True):
    context=authority_context
    if context is not None:
        require(type(context) is _AuthorityContext,'caller dictionaries are not authority contexts')
        context.check(path,inventory,work_dir,subphase,subphase_limits,requested_scope,requested_keys,injected)
        reservation=copy.deepcopy(context._reservation)
    else:reservation=read_object(path)
    require(reservation.get('kind')=='a3_root_execution_reservation_v1','completed root reservation required; cost proposal is not authority')
    require(reservation.get('identity')==inventory['identity'] and reservation.get('inventory_sha256')==inventory['inventory_sha256'],
        'root reservation source/inventory mismatch')
    if context is None:
        upper=read_object(reservation['upper_inventory_path']); (inventory_validator or workload._validate_inventory)(upper)
        if workload.digest(upper)!=workload.digest(inventory):(inventory_validator or workload._validate_inventory)(inventory)
        upper_keys=frozenset(workload.digest(k) for k in upper['expected_keys'])
    else:
        upper=context._upper
        upper_keys=context._upper_keys
    contract=validate_allocation_contract(reservation.get('allocation_contract'),reservation['actual_entry'],inventory,injected=injected)
    allocation=read_current_allocation(reservation,injected=injected,reader=allocation_reader) if require_allocation else None
    if allocation is not None:validate_allocation(allocation,reservation['actual_entry'],inventory,work_dir,injected=injected,allocation_contract=contract)
    mapping_path=context._mapping_path if context is not None else ledger.get('original_mapping_reference',{}).get('path')
    require(mapping_path,'independently loaded root mapping required for reservation authority')
    if allocation is not None:require(allocation['end_time_unix']-time.time()>=inventory['finish_reserve_seconds']+reservation['minimum_shard_seconds'],'current allocation has insufficient finish time')
    ledger=normalize_ledger(mapping_path,identity=inventory['identity'],injected=injected,include_envelope=False,
        refresh_deadline=None if allocation is None else allocation['end_time_unix']-inventory['finish_reserve_seconds']-reservation['minimum_shard_seconds'])
    if contract is not None:
        claimed=ledger.get('storage_capacities',{}).get('host_ram',{}).get('available_bytes')
        require(type(claimed) is int and contract['memory_bytes']>=claimed,'root allocation RAM cannot back declared host capacity')
    matches=[e for e in ledger['entries'] if e['id']==reservation.get('reservation_id')]
    require(len(matches)==1,'root reservation not found in actual RS ledger')
    entry=matches[0]; actual=entry['actual_entry']
    require(entry['state'] in ('reserved','running') and entry['phase']==inventory['phase'] and entry['subphase']==subphase
        and entry['inventory_sha256']==inventory['inventory_sha256'],'reservation status/phase/inventory does not permit execution')
    require(Path(actual['output_dir']).resolve()==Path(work_dir).resolve() and actual['source_commit']==inventory['identity']['commit'],
        'actual reservation source/output differs')
    require(reservation.get('actual_entry')=={k:actual.get(k) for k in RESERVATION_FIELDS},'reservation immutable RS identity differs')
    if require_allocation:require(injected or os.environ.get('SLURM_JOB_ID') in allocation['job_ids'],'reservation is not current Slurm allocation')
    require(reservation.get('admission_reference')==object_reference(reservation['admission_path']),'root admission file bytes changed')
    admission=read_object(reservation['admission_path'])
    require(admission.get('kind') in ROOT_ADMISSION_KINDS,'independent root admission kind required; proposal cannot authorize')
    if contract is not None:require(admission.get('allocation_contract')==contract,'allocation contract not bound by original root admission')
    require(admission in ledger['original_admissions'],'root admission not independently anchored in mapping')
    require(admission['identity']==inventory['identity'] and admission['admission_sha256']==reservation.get('admission_sha256'),
        'root admission identity differs')
    require(admission['upper_inventory_sha256']==upper['inventory_sha256'] and upper['identity']==inventory['identity'],
        'original upper inventory differs')
    if context is None:require(all(workload.digest(k) in upper_keys for k in inventory['expected_keys']),'runtime inventory exceeds original upper inventory')
    anchors=admission.get('reservation_ids')
    require(isinstance(anchors,list) and anchors and len(set(anchors))==len(anchors),'empty original reservation anchors')
    linked=[e for e in ledger['entries'] if e.get('reservation_lineage',{}).get('admission_id')==admission['id']]
    require(set(anchors)<={e['id'] for e in linked} and entry in linked,'unrelated actual reservation admission lineage')
    for e in linked:
        lineage=e['reservation_lineage']
        require(lineage.get('admission_sha256')==admission['admission_sha256'] and lineage.get('max_gpu_hours')==admission['max_gpu_hours']
            and lineage.get('upper_inventory_sha256')==upper['inventory_sha256'] and lineage.get('reserved_gpu_hours')==e['reserved_gpu_hours'],
            'changed original admission ceiling/reserved-hour lineage')
    require(sum(e['reserved_gpu_hours'] for e in linked)<=admission['max_gpu_hours'],'original reserved-hour ceiling exhausted')
    sums=workload._ledger(ledger,inventory['identity'])
    original_totals=validate_global_budgets(ledger['entries'],contingency_remaining=sums['contingency_remaining'])
    limits={'M1':.5,'M2':9} if subphase_limits is None and subphase=='directions' else subphase_limits
    require(isinstance(limits,dict) and limits and all(k in ('M1','M2','M3','M4','M5','contingency') and type(v) in (int,float)
        and math.isfinite(v) and 0<v<=40 for k,v in limits.items()),'frozen subphase ceilings required')
    require(sums['M1']<=2 and sums['all']+sums['contingency_remaining']<=40
        and all(sum(e['reserved_gpu_hours'] for e in ledger['entries'] if e['subphase']==subphase and e['phase']==phase)<=ceiling
            for phase,ceiling in limits.items()),'A3 original reservation caps exceeded')
    if require_allocation:
        # Re-read the scheduler after any mapping-refresh wait: a time-limit
        # update or elapsed queue/lease must never inherit a static deadline.
        allocation=read_current_allocation(reservation,injected=injected,reader=allocation_reader)
        validate_allocation(allocation,actual,inventory,work_dir,injected=injected,allocation_contract=contract)
        require(allocation['end_time_unix']-time.time()>=inventory['finish_reserve_seconds']+reservation['minimum_shard_seconds'],
            'current allocation has insufficient finish time')
    if _context_sink is not None:
        require(context is None and require_allocation,'authority contexts require full live-allocation validation')
        created=_AuthorityContext(_AUTHORITY_SEAL,path,ledger,inventory,work_dir,subphase,subphase_limits,requested_scope,
            reservation,upper,upper_keys,inventory_path,injected)
        _context_sink.append(created)
    return dict(reservation=copy.deepcopy(reservation),reservation_reference=(context._reservation_reference if context is not None else object_reference(path)),
        ledger_sha256=ledger['snapshot_sha256'],ledger_snapshot_time=ledger['snapshot_time'],
        current_mapping_reference=ledger.get('active_mapping_reference',ledger['original_mapping_reference']),
        authority_context_retained_bytes=0 if context is None else context.retained_bytes,original_budget_totals=original_totals,
        original_reserved_gpu_hours=entry['reserved_gpu_hours'],actual_gpu_hours=entry['actual_gpu_hours'],
        allocation=allocation,allocation_verified=bool(require_allocation),execution_authorized=bool(require_allocation),
        live_allocation_admission='verified current Slurm lease' if require_allocation else 'deferred/unverified')


def live_guard(design, protocol, args, inventory=None):
    evidence=artifacts.validate_live(design,protocol,registry_paths=args.registry)
    if not design['injected']:_model_metadata_preflight(design,protocol)
    if inventory is not None:
        require(args.ledger_snapshot and args.reservation,'model execution requires fresh root ledger mapping and reservation')
        scope=('directions',args.stage,args.action,args.panel,args.pilot_part)
        context=getattr(args,'_authority_context',None)
        if context is None:
            ledger=normalize_ledger(args.ledger_snapshot,identity=inventory['identity'],injected=design['injected'],include_envelope=False)
            if not args.dry_run:
                context=make_authority_context(args.reservation,ledger=ledger,inventory=inventory,work_dir=args.work_dir,
                    injected=design['injected'],requested_scope=scope,inventory_path=args.inventory)
                args._authority_context=context;args._authority_ledger_reference=ledger
        else:ledger=args._authority_ledger_reference
        evidence['reservation']=validate_reservation(args.reservation,ledger=ledger,inventory=inventory,work_dir=args.work_dir,injected=design['injected'],
            require_allocation=not args.dry_run,authority_context=context,requested_scope=scope)
        if args.admission:
            require(read_object(args.reservation)['admission_path']==str(Path(args.admission).resolve()),'CLI root admission differs from reservation')
    return evidence


def scientific_identity(design,protocol,profile,*,source,split,sites,ids,condition=None,streams=None):
    source_rows=([r for r in design['access_rows'][source] if r['instance_id'] in set(design['tasks'][source]['fit_ids']) and r['condition'] in pipeline.CONDITIONS]
        if split=='train' else workload._source_rows(design,source,split))
    selected=[copy.deepcopy(r) for r in source_rows if r['instance_id'] in set(ids) and (condition is None or r['condition']==condition)]
    identity=copy.deepcopy(protocol['fit_cache']['capture_identity'])
    core={k:v for k,v in design.items() if k not in ('direction_protocol','direction_protocol_sha256')}
    identity.update(analysis_split=split,injected=design['injected'],design_sha256=ladder.design._hash(core),
        protocol_sha256=ladder.design._hash(protocol),ordered_ids=list(dict.fromkeys(ids)),
        streams=streams or (['clean'] if source=='mmlu' else ['clean','corrupt']),
        conditions=list(dict.fromkeys(r['condition'] for r in selected)),sites=copy.deepcopy(sites),
        row_identity_sha256=ladder.design._hash(selected),capture_lineage=[],numeric_profile=copy.deepcopy(profile))
    return identity


def _capture_bundle(model,batches,sites,identity,path,*,guard):
    """Save only CPU readouts/projections and scalar replay observations."""
    expected=dict(schema_version=1,kind='a3_readout_chunk',split=identity['analysis_split'],injected=identity['injected'],identity=identity)
    if Path(path).exists():
        metadata=artifacts._strict_json(Path(path)/'manifest.json')['metadata']
        require(all(metadata.get(k)==v for k,v in expected.items()),'changed canonical capture identity')
        metadata,arrays=artifacts.read_bundle(path,expected=metadata)
    else:
        arrays={}; rows=[]; projection_names={};lane_receipts=[]
        def sink(chunk):
            if 'lane_consistency' in chunk:lane_receipts.append(chunk['lane_consistency'])
            for p in chunk['projections']:
                key='projection_'+str(len(projection_names))
                site=tuple(p['site'])
                if site not in projection_names:
                    projection_names[site]=key; arrays[key]=p['value'].detach().float().cpu().numpy().copy()
            for row in chunk['rows']:
                entry=copy.deepcopy(row)
                for h in entry['heads']:
                    key=f'row{len(rows)}head{len(arrays)}'; arrays[key]=h.pop('value').detach().float().cpu().numpy().copy(); h['array']=key
                for h in entry['clause_summary'].get('heads',[]):
                    key=f'row{len(rows)}clause{len(arrays)}'; arrays[key]=h.pop('value').detach().float().cpu().numpy().copy(); h['array']=key
                rows.append(entry)
        for batch in batches:
            guard()
            # Calibration capture performs intact replicated lanes only. It does
            # not assert patched packing equivalence or publish scientific rows.
            runner._capture_readouts(model,[batch],sites=sites,sink=sink,identity=identity,measuring=True)
        metadata=dict(expected,runner_rows=rows,capture_lane_consistency=lane_receipts,runtime_profile=runtime_kernel_identity(model),projection_arrays=[dict(site=list(k),array=v) for k,v in projection_names.items()])
        artifacts.write_bundle(path,metadata,arrays)
    require(metadata.get('runtime_profile')==runtime_kernel_identity(model),'capture runtime kernel profile changed')
    index={}
    for raw in metadata['runner_rows']:
        row=copy.deepcopy(raw)
        for h in row['heads']+row['clause_summary'].get('heads',[]):
            h['value']=torch.from_numpy(np.array(arrays[h.pop('array')],copy=True))
        index[(row['profile_id'],row['task'],row['condition'],row['stream'],row['instance_id'])]=row
    return index,artifacts.capture_reference(path,expected=metadata)


def _maps(recipient,donor,pid):
    require(len(recipient.ids)==len(donor.ids),'donor physical batch differs')
    result=[]
    for i,rid in enumerate(recipient.ids):
        row=donor.records[i]
        mapping=dict(recipient_id=rid,recipient_condition=recipient.condition,recipient_stream=recipient.stream,
            donor_id=donor.ids[i],donor_condition=donor.condition,donor_stream=donor.stream,
            supported=True,recipient_positions=[int(recipient.readout[i])],donor_positions=[int(donor.readout[i])],donor_profile_id=pid)
        for field in ('source_hash','source_id','split'):
            if field in row: mapping['donor_'+field]=row[field]
        result.append(mapping)
    return result


def _mmlu_positive(design,split,batch,profile,dummy_sources):
    """Frozen cyclic source donor, including execution-only duplicate recipients."""
    maps=design['mmlu_validation_maps'] if split=='validation' else design['utility']['mmlu_maps']
    indexed={m['recipient_id']:m for m in maps}; donors=[]; mappings=[]
    singleton=dict(profile,physical_batch_size=1,axis_tile_size=1)
    for i,rid in enumerate(batch.ids):
        original=dummy_sources.get(rid,rid); mapping=copy.deepcopy(indexed[original])
        donor=source_batches(design,'mmlu',split,[mapping['donor_id']],mapping['donor_condition'],mapping['donor_stream'],singleton)[0]
        recipient=list(runner.ladder._rows(batch))[i]
        mapping.update(recipient_id=rid,recipient_condition=batch.condition,recipient_stream=batch.stream,
            recipient_positions=[int(batch.readout[i])],donor_positions=donor.readout.tolist(),supported=True)
        mappings.append(mapping); donors.append(donor)
    return donors,mappings


def runtime_environment(model):
    import platform
    import importlib.metadata
    from component_analysis import hooks
    versions={}
    for package in ('torch','transformers','nnsight'):
        try: versions[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: versions[package]='unavailable'
    return dict(python=platform.python_version(),packages=versions,cuda=torch.version.cuda,runtime_profile=runtime_kernel_identity(model),
        geometry=hooks.geometry(model),device=str(hooks.device_and_dtype(model)[0]),dtype=str(hooks.device_and_dtype(model)[1]),
        backend=hooks.attention_implementation(model))


def score_runtime_shard(model,design,protocol,shard,*,axes,output,guard,measured_paths=(),axis_class=False,shared_root=None,measured_index=None):
    """Execute precisely one frozen source/condition/stream and its own controls."""
    started=time.perf_counter()
    if measured_index is None:measured_index=_PackingCandidateIndex([_completed_packing_proof(path) for path in measured_paths])
    require(type(measured_index) is _PackingCandidateIndex,'validated measured candidate index required')
    if type(guard) is not _DependencyGuard:guard=_DependencyGuard(guard,measured_index)
    guard_calls_start=guard.calls;guard_seconds_start=guard.elapsed_seconds
    verified_start=guard.index.forest.verified_bytes;refreshes_start=guard.index.forest.refreshes
    guard(); key=shard['expected_keys'][0]
    panel,analysis,source,split=key[:4]; condition,stream=key[10:12]; profile=shard['profile']
    require(all(k[0:4]==key[0:4] and k[10:12]==key[10:12] for k in shard['expected_keys']), 'mixed source shard unsupported')
    ids=shard.get('execution_ids',shard['instance_ids']); dummies=shard.get('dummy_sources',{})
    batch=source_batches(design,source,split,ids,condition,stream,profile,dummy_sources=dummies)[0]
    identity=scientific_identity(design,protocol,profile,source=source,split=split,sites=profile.get('sites',[key[5]]),ids=shard['instance_ids'],condition=condition,
        streams=['clean'] if source=='mmlu' else ['clean','corrupt'])
    pid=runner.profile_identity(identity); batches=[batch]
    if source!='mmlu':
        donor=source_batches(design,source,split,ids,condition,'corrupt' if stream=='clean' else 'clean',profile,dummy_sources=dummies)[0]
        batches.append(donor); donor_maps=_maps(batch,donor,pid); positive_donors=[donor]
    else:
        positive_donors,donor_maps=_mmlu_positive(design,split,batch,profile,dummies)
    capture_identity=copy.deepcopy(identity)
    capture_path,control_path=shared_execution_paths(shared_root,capture_identity,stream) if shared_root is not None else (Path(output)/'capture',Path(output)/'positive-controls')
    index,reference=_capture_bundle(model,batches,identity['sites'],capture_identity,capture_path,guard=guard)
    identity['capture_lineage']=[reference]
    identity['runtime_profile']=runtime_kernel_identity(model)
    cells=[]
    for raw in shard['cells']:
        cell=copy.deepcopy(raw); cell['axis']=cell.get('axis',cell.get('axis_reference'))
        require(cell['axis'] in axes,'missing frozen actual numeric axis')
        if cell['operation']=='interchange': cell['donor_maps']=donor_maps
        cells.append(cell)
    reuse_context=None
    if profile['axis_tile_size']>1:
        reused=Path(output)/'profile-reuse'
        scope=[runner._cell_scope(batch,c,axes,index) for c in cells]
        snapshots=packing_evidence({},[batch])['snapshots'];target_rows=next(iter(snapshots.values()))
        branches={(row['task'],_mask_branch(row)) for row in target_rows}
        candidates=measured_index.candidates(profile,scope,axis_class=axis_class,
            runtime_profile=runtime_kernel_identity(model),mask_branches=branches)
        require(candidates,'no calibrated target packing scope in validated candidate index')
        if not reused.exists():
            freeze_profile_reuse(reused,measured_path=candidates[0].path,batch=batch,cells=cells,axes=axes,capture_index=index,
                policy=protocol['workload']['reuse_policy'],axis_class=axis_class,runtime_profile=runtime_kernel_identity(model),validated_proof=candidates[0])
        identity['profile_reuse']=str(reused.resolve())
        body=read_object(reused);proof=next((p for p in candidates if Path(p.path).resolve()==Path(body['measured_path']).resolve()),None)
        require(proof is not None,'persisted target attestation uses an unbound measured source')
        reuse_context=_validated_reuse_context(identity,batch,proof=proof)
    guard()
    if control_path.exists():
        stored=read_object(control_path);require(stored.get('runtime_profile')==runtime_kernel_identity(model),'positive-control runtime profile changed')
        controls=stored['rows']
    else:
        controls=runner.run_positive_controls(model,[batch],donor_batches=positive_donors,donor_maps=donor_maps,identity=identity)['rows']
        publish_object(control_path,dict(kind='a3_direction_measured_positive_cache_v1',rows=controls,runtime_profile=runtime_kernel_identity(model)))
    identity.update(panel=panel,analysis_task=analysis,split=split)
    for cell in cells: cell['positive_controls']=controls
    chunks=[]
    if reuse_context is None:
        guard();runner.score_direction_cells(model,[batch],cells=cells,capture_index=index,axes=axes,sink=chunks.append,identity=identity)
    else:
        with reuse_context.operation(guard):
            runner.score_direction_cells(model,[batch],cells=cells,capture_index=index,axes=axes,sink=chunks.append,identity=identity,reuse_context=reuse_context)
    all_rows=[r for c in chunks for r in c['rows']]
    rows=[r for r in all_rows if r['instance_id'] not in dummies]
    artifacts._coverage(rows,shard['expected_keys'])
    evidence=dict(kind='a3_direction_execution_v1',complete=True,exit_code=0,injected=design['injected'],
        actual_execution=True,source_commit=protocol['commit'],code_hashes=protocol['code_hashes'],
        runtime=runtime_environment(model),job_id=os.environ.get('SLURM_JOB_ID','injected-cpu'),
        cluster=os.environ.get('DC_CLUSTER','injected-cpu'),scientific_rows=len(rows),execution_rows=len(all_rows),
        execution_dummy_sources=copy.deepcopy(dummies),dummy_control_count=sum(r['instance_id'] in dummies for r in controls),
        positive_control_reference=object_reference(control_path),positive_control_ids=[r['control_id'] for r in controls],
        capture_reference=object_reference(capture_path))
    final_guard=guard()
    evidence.update(wall_seconds=time.perf_counter()-started,dependency_guard_calls=guard.calls-guard_calls_start,
        dependency_guard_seconds=guard.elapsed_seconds-guard_seconds_start,dependency_verified_bytes=guard.index.forest.verified_bytes-verified_start,
        dependency_refreshes=guard.index.forest.refreshes-refreshes_start,guard=final_guard)
    for field in ('profile_reuse','panel','analysis_task','split','runtime_profile'):identity.pop(field,None)
    return rows,evidence,identity


def _runtime_shard_identity(design,protocol,shard,capture_path):
    key=shard['expected_keys'][0];source=key[2];stream=key[11]
    identity=scientific_identity(design,protocol,shard['profile'],source=source,split=key[3],
        sites=shard['profile'].get('sites',[key[5]]),ids=shard['instance_ids'],condition=key[10],
        streams=['clean'] if source=='mmlu' else ['clean','corrupt'])
    metadata,_=read_bundle(capture_path)
    require(metadata['identity']==identity,'runtime capture source/geometry changed')
    identity['capture_lineage']=[artifacts.capture_reference(capture_path,expected=metadata)]
    return identity


def read_runtime_rows(design,protocol,inventory,root,*,panel=None,guard=lambda:None):
    rows=[];refs=[]
    for shard in inventory['shards']:
        if panel is not None and shard['panel']!=panel: continue
        guard();base=Path(root)/shard['shard_id']
        manifest=artifacts._strict_json(base/'run_manifest.json')
        capture_path=manifest['execution']['capture_reference']['path']
        identity=_runtime_shard_identity(design,protocol,shard,capture_path)
        expected_path,_=shared_execution_paths(Path(root).parent,dict(identity,capture_lineage=[]),shard['expected_keys'][0][11])
        require(Path(capture_path).resolve()==expected_path.resolve(),'capture path is not canonical source scope')
        values=artifacts.read_completed_shards(dict(shards=[shard]),Path(root),identity=identity)
        manifest=artifacts._strict_json(base/'run_manifest.json')
        execution=manifest['execution']
        require(execution.get('actual_execution') is True and execution.get('source_commit')==protocol['commit']
            and execution.get('code_hashes')==protocol['code_hashes'] and execution.get('exit_code')==0
            and execution.get('scientific_rows')==len(shard['expected_keys']),'missing complete actual execution evidence')
        rows.extend(values);refs.append(object_reference(base))
    keys=[k for s in inventory['shards'] if panel is None or s['panel']==panel for k in s['expected_keys']]
    artifacts._coverage(rows,keys)
    return rows,refs


def _print_dry(args,design,protocol,*,inventory=None,missing=()):
    print(json.dumps(dict(dry_run=True,stage=args.stage,action=args.action,design_sha256=ladder.design._hash(design),
        protocol_sha256=ladder.design._hash(protocol),commit=args.commit,
        inventory_sha256=None if inventory is None else inventory['inventory_sha256'],
        missing_prerequisites=list(missing),model_loaded=False,writes=False,execution_authorized=False,
        live_allocation_admission='deferred/unverified'),sort_keys=True))
    return 0


def _read_stage_inventory(args,design,protocol,*,fits=None,selected=None):
    require(args.inventory,'completed frozen inventory required')
    inv=read_object(args.inventory);workload._validate_inventory(inv)
    require(inv['identity']==workload.inventory_identity(design,protocol),'inventory differs from canonical design/protocol')
    if fits is not None: require(inv['frozen_inputs'].get('fits') in (None,fits),'inventory fit bytes differ')
    if selected is not None: require(inv['frozen_inputs'].get('selected')==selected,'inventory selection differs')
    return inv


def dispatch(args, *, tokenizer=None, model_loader=None):
    from component_analysis import a3_pipeline
    root=Path(args.work_dir);design_path=Path(args.design)
    require(design_path.resolve()==(root/'design.json').resolve(),'canonical design must be WORK_DIR/design.json')
    if args.stage=='prepare' and args.action=='freeze':
        for key in ('a1_design','a1_selected','matched_root','historical_csv','root_ruling','execution_settings'):
            require(getattr(args,key),'prepare freeze requires '+key)
        # Canonical prepare independently loads the frozen standard tokenizer;
        # explicit adapters remain available only to injected parent fixtures.
        ruling=artifacts._strict_json(args.root_ruling);settings=artifacts._strict_json(args.execution_settings)
        design=a3_pipeline.prepare(a1_design=args.a1_design,a1_selected=args.a1_selected,matched_root=args.matched_root,
            historical_csv=args.historical_csv,root_ruling=ruling,tokenizer=tokenizer,registry_paths=args.registry,
            output=None if args.dry_run else design_path,commit=args.commit,execution_settings=settings)
        if args.dry_run: return _print_dry(args,design,design['direction_protocol'])
        return 0
    design=ladder.read_artifact(design_path);protocol=design['direction_protocol']
    require(protocol['commit']==args.commit and design['direction_protocol_sha256']==ladder.design._hash(protocol),'CLI execution source differs from frozen protocol')
    require(model_loader is None or design['injected'] is True,'injected loader cannot execute a production lineage')
    require(not args.final or design['injected'] is False,'injected lineage cannot finalize')
    guard=lambda:live_guard(design,protocol,args)
    guard()
    if args.stage=='fit' and args.action=='solve':
        cache=args.fit_cache or root/'cache'/'fit-selection'
        expected,_=pipeline._fit_contract(design,protocol);artifacts.read_bundle(cache,expected=expected)
        if args.dry_run:return _print_dry(args,design,protocol)
        if not design['injected']: require(read_object(root/'cache'/'fit-completion')['cache_reference']==object_reference(cache),'complete capture execution receipt required')
        pipeline.fit_from_cache(design,cache,protocol=protocol,output=root/'fits');return 0
    fits=None;selected=None
    if args.fits: fits,_=read_bundle(args.fits)
    if args.selected: selected,_=read_bundle(args.selected)
    if args.stage=='select' and args.action=='score' and fits is not None:
        require(not fits.get('blocked_task_seeds'),'no valid DOM fit for an original task/seed; validation model access blocked')
    if args.stage=='prepare' and args.action=='inventory':
        inv=workload.build_inventory(design,protocol,stage=args.inventory_stage,fits=fits,selected=selected)
        if args.dry_run:return _print_dry(args,design,protocol,inventory=inv)
        publish_object(args.inventory or root/'inventory'/args.inventory_stage,inv);return 0
    if args.stage=='select' and args.action=='freeze':
        fits_path=args.fits or root/'fits';validation=args.validation_root or root/'validation'
        fits,_=read_bundle(fits_path)
        # All expected validation shard bytes must exist before CPU selection.
        pipeline._read_selection_validation(design,protocol,fits,read_bundle(fits_path)[1],validation,pipeline._bundle_byte_reference(fits_path))
        if args.dry_run:return _print_dry(args,design,protocol)
        pipeline.freeze_selection(design,fits_path,validation,protocol=protocol,output=root/'selected',protocol_path=root/'direction_protocol.json');return 0
    inv=_read_stage_inventory(args,design,protocol,fits=fits,selected=selected)
    if args.finish_reserve_seconds is not None:
        require(args.finish_reserve_seconds==inv['finish_reserve_seconds'],'finish reserve differs from frozen workload')
    if args.stage=='prepare' and args.action=='admit':
        require(args.pilot_receipts and args.ledger_snapshot,'completed pilot receipts and fresh root mapping required')
        receipts,sources=_authenticated_pilot_receipts(design,protocol,inv,args.pilot_receipts,ledger_path=args.ledger_snapshot)
        ledger=normalize_ledger(args.ledger_snapshot,identity=inv['identity'],injected=design['injected'])
        proposal=workload.project_cost(receipts,inv,ledger,packing_proofs=_cost_packing_proofs(receipts))
        proposal['completed_pilot_sources']=[dict(s.value) for s in sources]
        if args.dry_run:return _print_dry(args,design,protocol,inventory=inv)
        publish_object(root/'admission'/(inv['stage']+'.json'),proposal);return 0
    if args.stage=='summarize':
        require(inv['stage']=='remaining' and selected is not None,'summary requires full remaining inventory and selected axes')
        calibration,calibration_refs=read_runtime_rows(design,protocol,inv,root/'runtime-shards',panel='calibration',guard=guard)
        assessment_complete=all((root/'runtime-shards'/s['shard_id']/'COMPLETE.json').is_file() for s in inv['shards'] if s['panel']=='assessment')
        if not assessment_complete:
            require(not args.final,'incomplete original assessment inventory cannot finalize')
            if args.dry_run:return _print_dry(args,design,protocol,inventory=inv,missing=['complete assessment inventory for full summary'])
            summarize_calibration(design,protocol,selected,calibration,calibration_refs,root=root,inventory=inv,guard=guard)
            return 0
        rows,refs=read_runtime_rows(design,protocol,inv,root/'runtime-shards',panel='assessment',guard=guard)
        if args.dry_run:return _print_dry(args,design,protocol,inventory=inv)
        summarize_runtime(design,protocol,selected,rows,calibration,refs,calibration_refs,root=root,inventory=inv,final=args.final,guard=guard)
        return 0
    expected_stage=('prefit' if args.pilot_part=='prefit' else 'selected-pilot') if args.stage=='pilot' else ('fit-select' if args.stage in ('fit','select') else 'remaining')
    require(inv['stage']==expected_stage,'inventory stage incompatible with requested model stage')
    candidates=inv.get('capture_shards',[]) if args.stage=='fit' else inv['shards']
    require(args.shard_id is None or any(s['shard_id']==args.shard_id for s in candidates),'unknown frozen stage shard ID')
    if args.stage=='assess': require(any(s['panel']==args.panel for s in candidates),'inventory does not contain requested panel')
    if args.stage=='assess' and args.panel=='assessment' and not design['injected']:
        assessment_preflight(design,protocol,selected,inv,root=root,reservation_path=args.reservation)
    if not design['injected']:_model_metadata_preflight(design,protocol)
    if args.dry_run:
        missing=[k for k in ('ledger_snapshot','reservation') if not getattr(args,k)]
        if not missing: live_guard(design,protocol,args,inv)
        return _print_dry(args,design,protocol,inventory=inv,missing=missing)
    model_guard=lambda:live_guard(design,protocol,args,inv)
    model_guard()
    if args.stage in ('select','assess'):
        args._candidate_index=_admitted_candidate_index(args,design,protocol)
        model_guard=_DependencyGuard(model_guard,args._candidate_index)
        model_guard()
    if not design['injected']:
        require(os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available(),'model execution requires actual Slurm CUDA allocation')
    load_args=copy.copy(args)
    for k in ('model','model_revision','tokenizer_revision'):setattr(load_args,k,design['a1_identity'][k])
    startup=time.perf_counter();model=(model_loader or ladder.load_model)(load_args)
    if torch.cuda.is_available():torch.cuda.synchronize()
    startup=max(time.perf_counter()-startup,time.time()-float(os.environ.get('A3_WRAPPER_START_SECONDS',_PROCESS_START_TIME)))
    from component_analysis import hooks
    geometry=hooks.geometry(model);cfg=protocol['workload']
    require(all(geometry[k]==cfg[k2] for k,k2 in (('head_dim','head_width'),('hidden_size','hidden_size'),('num_layers','num_layers'))),'actual loaded model geometry differs from frozen operational settings')
    model_guard()
    if args.stage=='pilot': run_pilot(model,design,protocol,inv,root=root,args=args,guard=model_guard,startup_seconds=startup,selected=selected)
    elif args.stage=='fit': run_fit_capture(model,design,protocol,inv,root=root,guard=model_guard,shard_id=args.shard_id,resume=args.resume)
    else:
        require(args.stage in ('select','assess'),'unsupported model stage')
        run_scoring(model,design,protocol,inv,root=root,args=args,guard=model_guard,fits=fits,selected=selected)
    return 0


def _fit_piece_identity(design,protocol,capture):
    return scientific_identity(design,protocol,capture['profile'],source=capture['source_task'],split='train',
        sites=capture['sites'],ids=capture['instance_ids'],condition=capture['condition'],streams=[capture['stream']])


def assemble_fit_pieces(design,protocol,inventory,*,root):
    expected,layout=pipeline._fit_contract(design,protocol);arrays={};seen=set();projections={};references=[]
    source_index={(task,r['condition'],r['instance_id']):r for task,rows in design['access_rows'].items() for r in rows if r.get('split')=='train'}
    wanted={(x['task'],tuple(x['site']),c,rid,s) for x in layout for c in pipeline.CONDITIONS for rid in x['instance_ids'] for s in pipeline.STREAMS}
    for shard in inventory['capture_shards']:
        cap=shard['capture'];path=Path(root)/'cache'/'fit-pieces'/shard['shard_id']/'capture'
        require((path/'COMPLETE.json').is_file(),'incomplete train capture piece coverage')
        meta,cached=read_bundle(path);require(meta['identity']==_fit_piece_identity(design,protocol,cap),'changed train capture piece source/profile')
        references.append(object_reference(path))
        for p in meta['projection_arrays']:
            site=tuple(p['site']);value=np.array(cached[p['array']],copy=True)
            require(site not in projections or np.array_equal(projections[site],value),'train source projection changed between pieces')
            projections[site]=value
        for row in meta['runner_rows']:
            source=source_index[(row['task'],row['condition'],row['instance_id'])]
            require(row.get('record')==pipeline._selection_source_record(source,row['stream'],row['task']), 'train capture source bytes differ')
            for head in row['heads']:
                site=tuple(head['site']);key=(row['task'],site,row['condition'],row['instance_id'],row['stream'])
                if site not in {tuple(s) for s in design['tasks'][row['task']]['direction_sites']}:continue
                require(key in wanted and key not in seen,'duplicate/unexpected train capture piece membership');seen.add(key)
                item=next(x for x in layout if x['task']==row['task'] and tuple(x['site'])==site)
                value=np.array(cached[head['array']],dtype=np.float32,copy=True);name=item['activations'][row['condition']]
                if name not in arrays:arrays[name]=np.empty((len(item['instance_ids']),2,len(value)),dtype=np.float32)
                arrays[name][item['instance_ids'].index(row['instance_id']),pipeline.STREAMS.index(row['stream'])]=value
    require(seen==wanted,'incomplete original train capture membership')
    for item in layout:arrays[item['projection']]=projections[tuple(item['site'])]
    target=Path(root)/'cache'/'fit-selection'
    if target.exists():artifacts.read_bundle(target,expected=expected)
    else:artifacts.write_bundle(target,expected,arrays)
    completion=Path(root)/'cache'/'fit-completion'
    payload=dict(kind='a3_direction_fit_capture_completion_v1',complete=True,injected=design['injected'],
        cache_reference=object_reference(target),capture_references=references,source_commit=protocol['commit'],
        observed_membership=len(seen),expected_membership=len(wanted))
    if completion.exists():require(read_object(completion)==payload,'fit completion evidence changed')
    else:publish_object(completion,payload)
    return expected


def run_fit_capture(model,design,protocol,inventory,*,root,guard,shard_id=None,resume=False):
    candidates=inventory['capture_shards']
    require(candidates and (shard_id is None or any(x['shard_id']==shard_id for x in candidates)),'unknown/empty frozen train capture shard')
    for shard in candidates:
        if shard_id is not None and shard['shard_id']!=shard_id:continue
        guard();cap=shard['capture'];path=Path(root)/'cache'/'fit-pieces'/shard['shard_id']/'capture'
        identity=_fit_piece_identity(design,protocol,cap)
        if path.exists():
            require(resume,'existing capture piece requires resume')
            meta,_=read_bundle(path);require(meta['identity']==identity,'changed resumed capture identity');continue
        batches=source_batches(design,cap['source_task'],'train',cap['instance_ids'],cap['condition'],cap['stream'],cap['profile'])
        _capture_bundle(model,batches,cap['sites'],identity,path,guard=guard)
    guard()
    if all((Path(root)/'cache'/'fit-pieces'/s['shard_id']/'capture'/'COMPLETE.json').is_file() for s in candidates):
        return assemble_fit_pieces(design,protocol,inventory,root=root)
    return dict(complete=False,reason='remaining original train capture pieces required')


_REUSE_CONTEXT_SEAL=object()


class _ValidatedReuseContext:
    """Exact immutable target scope, active only inside one checked model operation."""
    def __init__(self,seal,identity,batch,body,proof):
        require(seal is _REUSE_CONTEXT_SEAL and not getattr(self,'_sealed',False),'reuse context requires independent validation')
        _validated_reuse_body(identity,batch,body,proof.metadata,proof=proof)
        self.pid=os.getpid();self.body=_freeze_json(body);self.proof=proof
        self.witness=_make_file_witness([identity['profile_reuse']]);self.scope_checks=0;self._active=False;self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('validated reuse context is immutable')
        object.__setattr__(self,name,value)
    def __delattr__(self,name):raise TypeError('validated reuse context is immutable')
    def scope(self,identity,batch):
        require(self.pid==os.getpid() and self._active,'reuse context is outside its validated model operation')
        require(self.body['numeric_profile']==identity['numeric_profile'] and self.body.get('runtime_profile')==identity.get('runtime_profile'),'reuse context runtime/profile changed')
        snapshots=packing_evidence({},[batch])['snapshots'];bid=next(iter(snapshots))
        require(self.body['target_batch_sha256']==bid and self.body['target_snapshots']==snapshots[bid],'reuse context target bytes changed')
        object.__setattr__(self,'scope_checks',self.scope_checks+1)
        return self.body['target_scope']
    def operation(self,guard=None):
        from contextlib import contextmanager
        @contextmanager
        def bounded():
            require(not self._active and self.pid==os.getpid(),'reuse operation cannot nest or cross process')
            def fresh():
                if type(guard) is _DependencyGuard:
                    require(self.proof in guard.index.proofs,'reuse proof outside model dependency index');guard()
                else:
                    self.proof.refresh()
                    if guard is not None:guard()
                _check_file_witness(self.witness)
            fresh();object.__setattr__(self,'_active',True)
            try:yield self
            finally:object.__setattr__(self,'_active',False);fresh()
        return bounded()
    def __reduce__(self):raise TypeError('reuse contexts are process-local')


def _validated_reuse_context(identity,batch,*,proof=None):
    body=read_object(identity['profile_reuse'])
    if proof is None:proof=_completed_packing_proof(body['measured_path'],expected_reference=body['measured_reference'])
    require(type(proof) is _CompletedPackingProof and proof.reference==body['measured_reference'],'reuse measured source reference differs')
    return _ValidatedReuseContext(_REUSE_CONTEXT_SEAL,identity,batch,body,proof)


def validate_profile_reuse(identity,batch,*,context=None):
    """Runner validates exact target bytes; sealed operation context avoids duplicate IO."""
    if context is not None:
        require(type(context) is _ValidatedReuseContext,'caller metadata cannot substitute for validated reuse context')
        return context.scope(identity,batch)
    body=read_object(identity['profile_reuse'])
    measured=_validated_measurement(body['measured_path'],expected_reference=body['measured_reference'])
    return _validated_reuse_body(identity,batch,body,measured)


def shared_execution_paths(root,identity,stream):
    core={k:v for k,v in identity.items() if k not in ('capture_lineage','panel','analysis_task','split','profile_reuse')}
    scope=workload.digest(core)
    return Path(root)/'runtime-captures'/scope,Path(root)/'runtime-controls'/workload.digest([scope,stream])


def _admitted_packing_paths(args):
    if not getattr(args,'reservation',None):return []
    reservation=read_object(args.reservation);admission=read_object(reservation['admission_path']);paths=[]
    for receipt_path in admission.get('pilot_receipt_paths',[]):
        receipt=read_object(receipt_path)
        require(receipt.get('complete') is True and receipt.get('status')=='completed' and receipt.get('exit_code')==0,'incomplete admitted pilot receipt')
        for path,ref in receipt.get('packing_references',{}).items():
            require(object_reference(path)==ref,'admitted packing measurement bytes changed')
            _validated_measurement(path,expected_reference=ref);paths.append(path)
    return paths


def _admitted_candidate_index(args,design,protocol):
    start=time.perf_counter();paths=_admitted_packing_paths(args);witnesses=[]
    if getattr(args,'reservation',None):
        reservation=read_object(args.reservation);admission=read_object(reservation['admission_path'])
        pilot_paths=admission.get('pilot_receipt_paths',[])
        if not design.get('injected'):
            upper=read_object(reservation['upper_inventory_path'])
            _authenticated_pilot_receipts(design,protocol,upper,pilot_paths,ledger_path=args.ledger_snapshot)
        for receipt_path in pilot_paths:
            receipt=read_object(receipt_path);witnesses.append(_make_file_witness([receipt_path]))
            for value in receipt.get('serial_numeric_references',{}).values():
                require(object_reference(value['path'])==value['reference'],'admitted serial evidence bytes changed')
                serial=_SerialNumericProof(value['path']);require(serial.source_digest==value['source_digest'],'admitted serial numeric source differs')
                witnesses.append(serial.witness)
    proofs=[_completed_packing_proof(path) for path in paths]
    return _PackingCandidateIndex(proofs,extra_witnesses=witnesses,startup_seconds=time.perf_counter()-start)


def run_scoring(model,design,protocol,inventory,*,root,args,guard,fits=None,selected=None,shard_ids=None):
    requested=None
    if shard_ids is not None:
        require(design.get('injected') is True,'bounded shard_ids is injected verification only')
        require(getattr(args,'shard_id',None) is None,'mixed shard_id/shard_ids selectors')
        chosen=list(shard_ids);require(chosen and len(chosen)==len(set(chosen)),'unique nonempty verification shard IDs required')
        workload._validate_inventory(inventory)
        stage='validation' if args.stage=='select' else getattr(args,'panel',None)
        allowed={s['shard_id'] for s in inventory['shards'] if s['panel']==stage}
        require(set(chosen)<=allowed,'unknown or wrong-stage verification shard IDs');requested=frozenset(chosen)
    root=Path(root);axes={}
    candidate_index=getattr(args,'_candidate_index',None) or _admitted_candidate_index(args,design,protocol)
    paths=[p.path for p in candidate_index.proofs]
    if type(guard) is not _DependencyGuard:guard=_DependencyGuard(guard,candidate_index)
    if args.stage=='select':
        require(fits is not None and args.fits,'completed fits required for validation scoring')
        fitmeta,fitarrays,_,_=pipeline._read_selection_fits(design,protocol,args.fits)
        for record in fitmeta['fit_records']:
            if record['valid']:
                name=workload.digest([record['task'],record['site'],record['seed']])
                axes[name]=pipeline._loaded_fit_axis(fitmeta,fitarrays,record,'dom')
    else: axes=load_selected_axes(args.selected,selected)
    for original in inventory['shards']:
        if requested is not None and original['shard_id'] not in requested:continue
        if args.stage=='assess' and original['panel']!=args.panel:continue
        if args.shard_id is not None and original['shard_id']!=args.shard_id:continue
        guard();shard=copy.deepcopy(original);target=root/'runtime-shards'/shard['shard_id']
        if target.exists():
            require(args.resume,'existing scientific shard requires resume')
            manifest=artifacts._strict_json(target/'run_manifest.json')
            identity=_runtime_shard_identity(design,protocol,shard,manifest['execution']['capture_reference']['path'])
            artifacts.read_completed_shards(dict(shards=[shard]),root/'runtime-shards',identity=identity);continue
        if args.stage=='select':
            for cell in shard['cells']:cell['axis']=workload.digest([shard['expected_keys'][0][1],cell['site'],cell['seed']])
        rows,execution,identity=score_runtime_shard(model,design,protocol,shard,axes=axes,
            output=root/'runtime-execution'/shard['shard_id'],guard=guard,measured_paths=paths,
            axis_class=args.stage=='select',shared_root=root,measured_index=candidate_index)
        if args.stage=='select':execution['fit_reference']=pipeline._bundle_byte_reference(args.fits)
        guard();artifacts.publish_shard(target,identity=identity,expected_keys=shard['expected_keys'],rows=rows,execution=execution)
    if args.stage=='select' and all((root/'runtime-shards'/s['shard_id']/'COMPLETE.json').is_file() for s in inventory['shards']):
        assemble_selection_cache(design,protocol,fits,inventory,root=root,fits_path=args.fits,guard=guard)


def assemble_selection_cache(design,protocol,fits,inventory,*,root,fits_path,guard):
    """Adapt complete runtime validation shards to D's frozen per-profile layout."""
    root=Path(root);rows,_=read_runtime_rows(design,protocol,inventory,root/'runtime-shards',panel='validation',guard=guard)
    for group in pipeline._selection_layout(design,protocol,fits):
        guard();target=root/'validation'/group['group_id'];capture=target/'capture';arrays={};seen={}
        for shard in inventory['shards']:
            key=shard['expected_keys'][0]
            if key[1]!=group['analysis_task'] or key[2]!=group['source_task'] or list(key[5])!=group['site']:continue
            manifest=artifacts._strict_json(root/'runtime-shards'/shard['shard_id']/'run_manifest.json')
            path=manifest['execution']['capture_reference']['path'];meta,source_arrays=read_bundle(path)
            require(meta['identity']['numeric_profile']==group['numeric_profile'],'selection producer profile differs from frozen group')
            for row in meta['runner_rows']:
                if row['instance_id'].startswith('a3-dummy:') or row['stream'] not in group['capture_metadata']['identity']['streams']:continue
                source=group['sources'][(row['condition'],row['instance_id'])]
                require(row['record']==pipeline._selection_source_record(source,row['stream'],group['source_task']),'selection capture source bytes differ')
                head=next(h for h in row['heads'] if h['site']==group['site'])
                k=(row['condition'],row['instance_id'],row['stream']);value=np.array(source_arrays[head['array']],copy=True)
                require(k not in seen or np.array_equal(seen[k],value),'selection replay captures changed')
                seen[k]=value
        expected={(r['condition'],r['instance_id'],s) for r in group['sources'].values() for s in group['capture_metadata']['identity']['streams']}
        require(set(seen)==expected,'incomplete canonical selection capture coverage')
        for j,(k,value) in enumerate(sorted(seen.items())):arrays[f'readout{j}']=value
        if capture.exists():artifacts.read_bundle(capture,expected=group['capture_metadata'])
        else:artifacts.write_bundle(capture,group['capture_metadata'],arrays)
        identity=copy.deepcopy(group['capture_metadata']['identity'])
        identity['capture_lineage']=[artifacts.capture_reference(capture,expected=group['capture_metadata'])]
        scoped=[r for r in rows if r['analysis_task']==group['analysis_task'] and r['source_task']==group['source_task'] and r['site']==group['site']]
        indexed={artifacts.row_key(r):r for r in scoped};artifacts._coverage(scoped,group['expected_keys'])
        for shard in group['shards']:
            guard();values=[indexed[artifacts._freeze(k)] for k in shard['expected_keys']]
            path=target/'shards'/shard['shard_id']
            if path.exists():artifacts.read_completed_shards(dict(shards=[shard]),target/'shards',identity=identity)
            else:artifacts.publish_shard(path,identity=identity,expected_keys=shard['expected_keys'],rows=values,
                execution=dict(fit_reference=pipeline._bundle_byte_reference(fits_path),actual_execution=True,
                    source_commit=protocol['commit'],complete=True))
    return dict(complete=True,validation_root=str((root/'validation').resolve()))


def measure_runner_operations(model,call):
    """Observe actual reviewed runner forwards with synchronized wall clocks.

    CPU patch construction, readout gathering and sink overhead are retained as
    a separately measured conservative addition to every observed forward. No
    GPU synchronization runs for injected CPU models. Methods are restored even
    after interrupted calibration; no generic hook implementation is changed.
    """
    from component_analysis import hooks
    device=hooks.device_and_dtype(model)[0]
    def sync():
        if device.type=='cuda':torch.cuda.synchronize(device)
    old_forward=runner._forward;old_capture=runner._capture_readouts;old_score=runner._score_direction_cells
    active={};samples=[]
    def forward(*a,**kw):
        sync();start=time.perf_counter();out=old_forward(*a,**kw);sync();elapsed=time.perf_counter()-start
        if active:
            op='capture' if active['phase']=='capture' else workload.REPLAYS[active['index']%len(workload.REPLAYS)]
            active['index']+=1
            samples.append(dict(operation=op,profile=copy.deepcopy(active['profile']),dummy=active.get('dummy',False),
                seconds=elapsed,synchronized=True))
        return out
    def invoke(fn,phase,a,kw):
        previous=active.copy();active.clear();active.update(phase=phase,index=0,profile=kw['identity']['numeric_profile'],dummy=phase=='score' and len(kw['cells'])==1)
        first=len(samples);phase_start=time.perf_counter()
        try:return fn(*a,**kw)
        finally:
            local=samples[first:];elapsed=time.perf_counter()-phase_start
            if local:
                overhead=max(0,elapsed-sum(x['seconds'] for x in local))/len(local)
                for sample in local:sample['seconds']+=overhead;sample['profile_host_overhead_seconds']=overhead
            active.clear();active.update(previous)
    def capture(*a,**kw):return invoke(old_capture,'capture',a,kw)
    def score(*a,**kw):return invoke(old_score,'score',a,kw)
    start=time.perf_counter();runner._forward=forward;runner._capture_readouts=capture;runner._score_direction_cells=score
    try: result=call();sync()
    finally:runner._forward=old_forward;runner._capture_readouts=old_capture;runner._score_direction_cells=old_score
    total=time.perf_counter()-start
    require(samples,'timed runner performed no actual forwards')
    overhead=max(0,total-sum(s['seconds'] for s in samples))
    for sample in samples:
        sample['seconds']+=overhead/len(samples)
        sample['host_overhead_allocated_seconds']=overhead/len(samples)
    return result,samples


def _measurement_resources(model,root):
    import resource
    import shutil
    from component_analysis import hooks
    device=hooks.device_and_dtype(model)[0]
    if device.type=='cuda':
        allocated=torch.cuda.max_memory_allocated(device);reserved=torch.cuda.max_memory_reserved(device)
        capacity=torch.cuda.get_device_properties(device).total_memory
    else:
        allocated=reserved=0;capacity=os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')
    existing=Path(root)
    while not existing.exists():existing=existing.parent
    return dict(memory_capacity_bytes=int(capacity),peak_allocated_bytes=int(allocated),peak_reserved_bytes=int(reserved),
        cache_capacity_bytes=shutil.disk_usage(existing).free,host_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024)


def _batch_for_timing(design,profile,inputs):
    require(inputs and all(r['analysis_split']=='validation' for r in inputs),'timing requires validation-only actual source inputs')
    first=inputs[0];require(all((r['source_task'],r['condition'],r['stream'])==(first['source_task'],first['condition'],first['stream']) for r in inputs),'heterogeneous timing input batch')
    dummies={r['instance_id']:r['source_instance_id'] for r in inputs if 'source_instance_id' in r}
    return source_batches(design,first['source_task'],'validation',[r['instance_id'] for r in inputs],first['condition'],first['stream'],profile,dummy_sources=dummies)[0]


def _pilot_axes(model,cells,captures):
    """Named prefit timing-only attainable axes, never fit/selection evidence."""
    from component_analysis import a3_directions,hooks
    axes={};prepared=[];by_site={}
    for cell in cells:
        site=tuple(cell['site'])
        if site not in by_site:
            width=hooks.geometry(model)['head_dim']
            projection=hooks.o_proj_weight(model,site[1])[:,site[2]*width:(site[2]+1)*width].detach().float().cpu()
            geometry=a3_directions.image_geometry(projection)
            by_site[site]=(projection,geometry,[])
        projection,geometry,names=by_site[site]
        name=workload.digest([site,cell['seed'],cell['family'],cell['axis_index']])
        if name not in axes:
            j=len(names);v=geometry['U'][:,j%geometry['rank']]*(1 if j//geometry['rank']%2==0 else -1)
            h=torch.eye(projection.shape[1]);weights=torch.ones(len(h))/len(h)
            axes[name]=a3_directions.prepare_image_direction(projection,v,h,id_weights=weights)
            names.append(name)
        prepared.append(dict(cell,axis=name))
    return axes,prepared


def _pilot_invocation(model,design,protocol,invocation,*,axes,root,guard):
    """Actual full and dedicated dummy producer on frozen validation batches."""
    profile=invocation['profile'];source=invocation['source_task'];cells=copy.deepcopy(invocation['cells'])
    if axes is None:local_axes,cells=_pilot_axes(model,cells,None)
    else:
        local_axes=axes
        for cell in cells:cell['axis']=cell['axis_reference']
    batches=[];donors=[];maps=[];index={};pid=runner.profile_identity({'numeric_profile':profile})
    for group in invocation['batch_groups']:
        ids=list(group['instance_ids']);dummies={}
        while len(ids)<profile['physical_batch_size']//profile['axis_tile_size']:
            alias='a3-dummy:'+workload.digest([source,'validation',group['condition'],group['instance_ids'],len(ids)])
            dummies[alias]=ids[0];ids.append(alias)
        b=source_batches(design,source,'validation',ids,group['condition'],group['stream'],profile,dummy_sources=dummies)[0]
        batches.append(b)
        if source!='mmlu':
            d=source_batches(design,source,'validation',ids,group['condition'],'corrupt' if group['stream']=='clean' else 'clean',profile,dummy_sources=dummies)[0]
            donors.append(d);maps.extend(_maps(b,d,pid))
    identity=dict(injected=True,diagnostic_only=True,panel='pilot',analysis_task=invocation['analysis_task'],split='validation',numeric_profile=profile)
    def save(payload):
        for row in payload['rows']:index[(payload['profile_id'],row['task'],row['condition'],row['stream'],row['instance_id'])]=row
    # Actual donor cache physical geometry is the same as the target profile;
    # serial donor profiles are measured separately and remain distinct.
    donor_samples=[]
    if donors:
        unique={runner._digest([runner._recipient_digest(b,i) for i in range(len(b.ids))]):b for b in donors}
        for lanes in (1,profile['axis_tile_size']):
            ident=copy.deepcopy(identity);ident['numeric_profile']=dict(profile,axis_tile_size=lanes,
                physical_batch_size=profile['physical_batch_size']//profile['axis_tile_size']*lanes)
            _,samples=measure_runner_operations(model,lambda:runner._capture_readouts(model,list(unique.values()),sites=profile['sites'],sink=save,identity=ident,measuring=True))
            donor_samples.extend(samples)
    for cell in cells:
        if cell['operation']=='interchange':cell['donor_maps']=maps
    guard()
    if profile['axis_tile_size']>1:
        receipt,samples=measure_runner_operations(model,lambda:runner.measure_packing_equivalence(model,batches,cells=cells,capture_index=index,axes=local_axes,identity=identity))
        evidence=packing_evidence(receipt,batches)
    else:
        # Serial execution has no packed-equivalence claim. Preserve actual
        # controlled rows and timers, with own positives below.
        runner._capture_readouts(model,batches,sites=profile['sites'],sink=save,identity=identity,measuring=True)
        chunks=[]
        _,samples=measure_runner_operations(model,lambda:runner._score_direction_cells(model,batches,cells=cells,capture_index=index,
            axes=local_axes,sink=chunks.append,identity=identity,measuring=True))
        observed=[r for c in chunks for r in c['rows']]
        evidence=None;receipt=dict(kind='measured_serial_direction_v1',valid=True,profile=profile,
            snapshots=packing_evidence({},batches)['snapshots'],
            batches={runner._digest([runner._recipient_digest(b,i) for i in range(len(b.ids))]):[runner._cell_scope(b,c,local_axes,index) for c in cells] for b in batches},
            rows=observed,comparisons=[dict(key={k:r[k] for k in ('source_task','condition','stream','instance_id','seed','site','family','axis_index','operation')}) for r in observed],
            operation_samples=samples)
        receipt['receipt_sha256']=workload.digest(receipt)
    # Own-source positive controls remain mandatory for every timing recipient.
    positive_samples=[];positive_records=[]
    for b in batches:
        if source=='mmlu':
            dummy={r['instance_id']:r['execution_dummy']['duplicate_of'] for r in b.records if 'execution_dummy' in r}
            ds,ms=_mmlu_positive(design,'validation',b,profile,dummy)
        else:
            ds=[d for d in donors if d.ids==b.ids and d.condition==b.condition and d.stream!=b.stream]
            ms=[m for m in maps if m['recipient_condition']==b.condition and m['recipient_stream']==b.stream and m['recipient_id'] in b.ids]
        start=time.perf_counter()
        controls=runner.run_positive_controls(model,[b],donor_batches=ds,donor_maps=ms,identity=identity)
        positive_records.extend(controls['rows'])
        if runner.hooks.device_and_dtype(model)[0].type=='cuda':torch.cuda.synchronize()
        # Conservative actual complete-batch positive-control duration bounds
        # every singleton three-forward operation in that batch.
        positive_samples.append(time.perf_counter()-start)
    lookup_samples=[]
    for batch in batches:
        start=time.perf_counter()
        [runner._cell_scope(batch,cell,local_axes,index) for cell in cells[:profile['axis_tile_size']]]
        packing_evidence({},[batch])
        lookup_samples.append(time.perf_counter()-start)
    overhead=None
    if evidence is not None:
        overhead=_measure_reuse_overhead(root,profile,evidence,batches,cells,local_axes,index,runtime_kernel_identity(model))
    return dict(lookup_scope_seconds=max(lookup_samples)+(0 if overhead is None else overhead['context_seconds']),packing_overhead=overhead,
        evidence=evidence,receipt=receipt,samples=samples+donor_samples,positive_samples=positive_samples,positive_controls=positive_records,
        local_axes=local_axes,batches=batches,cells=cells)


def _measure_reuse_overhead(root,profile,evidence,batches,cells,axes,capture_index,kernel):
    """Time the actual attestation/context/exact-scope path without model forwards."""
    import tempfile
    parent=Path(root)/'pilot-scratch';parent.mkdir(parents=True,exist_ok=True)
    setup=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='reuse-overhead-',dir=parent) as tmp:
        measured=Path(tmp)/'measured'
        publish_object(measured,dict(injected=True,runtime_profile=kernel,evidence=evidence,
            measurement=dict(profile=profile,timing_inputs=[],axis_scope=[])))
        proof=_CompletedPackingProof(measured);guard=_DependencyGuard(lambda:None,_PackingCandidateIndex([proof]))
        setup_seconds=time.perf_counter()-setup
        batch=batches[0];block=cells[:profile['axis_tile_size']];start=time.perf_counter()
        reuse=Path(tmp)/'reuse'
        freeze_profile_reuse(reuse,measured_path=measured,batch=batch,cells=block,axes=axes,capture_index=capture_index,
            policy=workload.PROFILE_REUSE_POLICY,runtime_profile=kernel,validated_proof=proof)
        identity=dict(numeric_profile=profile,runtime_profile=kernel,profile_reuse=str(reuse))
        context=_validated_reuse_context(identity,batch,proof=proof)
        with context.operation(guard):
            runner._geometry(batch,identity,reuse_context=context)
            covered=runner._packing_receipt(identity,batch,reuse_context=context)
            require([runner._cell_scope(batch,c,axes,capture_index) for c in block]==covered,'measured exact target scope differs')
        seconds=time.perf_counter()-start-guard.elapsed_seconds
        return dict(profile=profile,context_seconds=max(seconds,1e-12),setup_seconds=setup_seconds,
            scope_checks=context.scope_checks,boundary_refreshes=guard.calls,verified_bytes=guard.index.forest.verified_bytes,
            attestation_bytes=sum(p.stat().st_size for p in reuse.iterdir() if p.is_file()),
            includes=['attestation_publication','context_validation','target_byte_witness','runner_geometry','runner_exact_scope'],
            boundary_refresh_accounting='separate measured guard_refresh requirement')


def _serial_invocations(inv):
    """Serial profiles still execute every named cell/operation in timing."""
    grouped={}
    for shard in inv['shards']:
        key=shard['expected_keys'][0]
        group=(key[1],key[2],workload.digest(shard['profile']))
        entry=grouped.setdefault(group,dict(invocation_id=workload.digest(group),analysis_task=key[1],source_task=key[2],profile=shard['profile'],cells=[],batch_groups=[]))
        for cell in shard['cells']:
            if cell not in entry['cells']:entry['cells'].append(cell)
        batch=dict(condition=key[10],stream=key[11],instance_ids=shard['instance_ids'])
        if batch not in entry['batch_groups']:entry['batch_groups'].append(batch)
    return list(grouped.values())


def _timing_inputs_from_batches(batches,profile):
    result=[]
    for b in batches:
        for i,rid in enumerate(b.ids):
            source=copy.deepcopy(b.records[i]);dummy=source.get('execution_dummy')
            row=dict(source_task=b.task,analysis_split='validation',condition=b.condition,stream=b.stream,
                instance_id=rid,record=source,unpadded_length=int(b.attention_mask[i].sum()),
                padded_width=profile['padded_width'],readout=int(b.readout[i]))
            if dummy:row['source_instance_id']=dummy['duplicate_of']
            result.append(row)
    return result


def _time_serialization(shapes,design,protocol,root,guard):
    """Measure real immutable publication, hash reread and numeric serialization.

    Bytes are explicitly inert envelopes derived from frozen source metadata;
    these benchmarks contain no fabricated target outcome observations.
    """
    import tempfile
    raw_sources=[r for rows in design['access_rows'].values() for r in rows]
    raw_sources.extend(r for t in ('ioi','mmlu') for r in design[t+'_validation']+design['utility'][t])
    largest=max((pipeline._selection_source_record(r,s,r.get('task','mechanism')) for r in raw_sources for s in r['streams']),key=lambda r:len(json.dumps(r)))
    times=[];observed=[];total_bytes=0
    parent=Path(root)/'pilot-scratch';parent.mkdir(parents=True,exist_ok=True)
    guard()
    for index,shape in enumerate(shapes):
        if index%32==0:guard()
        with tempfile.TemporaryDirectory(prefix='serialization-',dir=parent) as tmp:
            target=Path(tmp)/'artifact';start=time.perf_counter()
            def writer(directory):
                n=shape['rows'];row=dict(benchmark_no_outcomes=True,source_metadata=largest,
                    numeric_profile=shape.get('profile'),scalar_envelope={f'scalar{k}':-1.7976931348623157e308 for k in range(40)})
                common.write_jsonl(directory/'rows.jsonl',[row for _ in range(n)])
                common.write_json(directory/'run_manifest.json',dict(kind='a3_serialization_benchmark_v1',shape=shape,
                    key_byte_envelope='k'*shape.get('key_bytes',0),not_scientific_evidence=True))
                if 'numeric_bytes' in shape:
                    count=(shape['numeric_bytes']+3)//4;np.save(directory/'readouts.npy',np.zeros(count,dtype=np.float32),allow_pickle=False)
                    require(np.load(directory/'readouts.npy',allow_pickle=False,mmap_mode='r').nbytes>=shape['numeric_bytes'],'short serialization array')
                artifacts._finish(directory)
            common.publish(target,writer);artifacts._complete(target)
            elapsed=time.perf_counter()-start
            total_bytes+=sum(p.stat().st_size for p in target.iterdir() if p.is_file())
            times.append(elapsed);observed.append(workload.digest(shape))
    return times,observed,total_bytes


def _observed_requirement(receipt,requirement):
    wanted=requirement['timing_keys'];seen=[]
    comparisons=receipt['comparisons']
    for key in wanted:
        if len(key)!=12:continue
        fields=dict(source_task=key[2],seed=key[4],site=list(key[5]),family=key[6],axis_index=key[7],operation=key[8],
            instance_id=key[9],condition=key[10],stream=key[11])
        require(any(all(c['key'].get(k)==v for k,v in fields.items()) for c in comparisons),'actual measured producer did not cover frozen timing key')
        seen.append(key)
    return seen


def _pilot_candidates(results,requirement):
    """Match actual measured recipient membership before selecting a receipt.

    Profile identity alone does not bind condition, stream or source IDs. Full
    byte/axis verification remains in the independent packing evidence reader.
    """
    wanted={(r['source_task'],r['condition'],r['stream'],r['instance_id']) for r in requirement['timing_inputs']}
    return [result for result in results if result['invocation']['profile']==requirement['profile']
        and wanted.issubset({(b.task,b.condition,b.stream,rid) for b in result['batches'] for rid in b.ids})]


def _pilot_axes_covered(result,scope):
    if result.get('proof') is not None:return result['proof'].proof.covers_axes(scope)
    return all(any(all(cell.get(k)==v for k,v in wanted.items() if k!='axis_reference') for cell in result['cells']) for wanted in scope)


def _compact_operation_samples(samples):
    result={}
    for sample in samples:
        key=(workload.digest(sample['profile']),sample['operation'],sample['dummy'])
        current=result.get(key)
        if current is None or sample['seconds']>current['seconds']:result[key]=sample
    return list(result.values())


class _PilotReconciliationPass:
    """Atomic model-free scope reconciliation over private immutable inputs."""
    def __init__(self,proofs,inventory,*,guard,injected,extra_witnesses=()):
        require(all(type(p) is _CompletedPackingProof and p.pid==os.getpid() for p in proofs),'validated completed pilot proofs required')
        self.proofs=tuple(proofs);self.inventory=_freeze_json(inventory);self.guard=guard;self.injected=injected
        self._requirement_ids=frozenset(id(r) for r in self.inventory['requirements'])
        expected={}
        for witness in [p.witness for p in proofs]+list(extra_witnesses):
            require(type(witness) is _FileWitness and witness.pid==os.getpid(),'current immutable file witnesses required')
            for path,identity in zip(witness.paths,witness.identities):
                require(path not in expected or expected[path]==identity,'conflicting pilot backing fingerprints')
                expected[path]=identity
        self._paths=tuple(sorted(expected));self._expected=tuple(expected[p] for p in self._paths)
        self._active=False;self._finished=False;self._deadline=None;self._witness=None
        self.verified_bytes=0;self.verification_seconds=0.;self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('pilot reconciliation inputs are immutable')
        object.__setattr__(self,name,value)
    def _refresh(self):
        start=time.perf_counter();witness=_make_file_witness(self._paths)
        require(witness.identities==self._expected,'pilot receipt/numeric backing changed across reconciliation')
        volume=sum(row[2][3] for tree in witness.identities for row in tree if row[0]=='file')
        object.__setattr__(self,'verified_bytes',self.verified_bytes+volume)
        object.__setattr__(self,'verification_seconds',self.verification_seconds+time.perf_counter()-start)
        object.__setattr__(self,'_witness',witness)
    def _live_guard(self):
        evidence=self.guard()
        if evidence is None and self.injected:return
        result=evidence.get('reservation',{}) if isinstance(evidence,dict) else {}
        require(result.get('allocation_verified') is True and result.get('execution_authorized') is True,'reconciliation requires current live allocation authority')
        allocation=result.get('allocation',{});end=allocation.get('end_time_unix')
        require(type(end) in (int,float) and math.isfinite(end),'reconciliation needs effective lease deadline')
        deadline=end-self.inventory['finish_reserve_seconds']-result['reservation']['minimum_shard_seconds']
        object.__setattr__(self,'_deadline',deadline);self.check_deadline()
    def check_deadline(self):
        require(self._deadline is None or time.time()<self._deadline,'reconciliation has insufficient live finish time')
    def __enter__(self):
        self._refresh();self._live_guard();object.__setattr__(self,'_active',True);return self
    def model_guard(self):
        self._refresh();self._live_guard();self.check_deadline()
    def check(self,proof,requirement,measurement=None):
        require(self._active and proof in self.proofs and id(requirement) in self._requirement_ids,'unbound reconciliation target/proof')
        self.check_deadline();measurement=requirement if measurement is None else measurement
        require(all(measurement.get(k)==requirement.get(k) for k in ('profile','timing_inputs','axis_scope','donor_convention')),'reconciliation target scope differs from immutable inventory')
        return proof.proof.check(measurement)
    def __exit__(self,kind,value,traceback):
        object.__setattr__(self,'_active',False)
        if kind is None:
            self._refresh();self._live_guard();object.__setattr__(self,'_finished',True)
        return False
    def before_publication(self):
        require(self._finished,'incomplete reconciliation cannot publish')
        self._refresh();self._live_guard()
    def __reduce__(self):raise TypeError('pilot reconciliation passes are process-local')


def run_pilot(model,design,protocol,inventory,*,root,args,guard,startup_seconds,selected=None):
    """Measure every target requirement from the frozen validation scope only."""
    root=Path(root);part=args.pilot_part
    target=workload.build_inventory(design,protocol,stage='fit-select' if part=='prefit' else 'remaining',selected=selected)
    selected_reference=None;selected_witness=None
    if part=='prefit':axes=None
    else:
        selected_reference=pipeline._bundle_byte_reference(args.selected)
        axes=load_selected_axes(args.selected,selected);selected_witness=_make_file_witness([args.selected])
        require(pipeline._bundle_byte_reference(args.selected)==selected_reference,'selected numeric backing changed during pilot load')
    invocations=inventory['packing_invocations'] or _serial_invocations(inventory)
    measured=[];packing={};packing_refs={};serial_refs={};invocation_results=[];seen_measurements=set();proof_validation_seconds=0;proof_retained_bytes=0;packing_overheads=[]
    for invocation in invocations:
        if selected_witness is not None:_check_file_witness(selected_witness)
        guard();result=_pilot_invocation(model,design,protocol,invocation,axes=axes,root=root,guard=guard)
        if selected_witness is not None:_check_file_witness(selected_witness)
        guard();result['invocation']=invocation;result['packing_id']=None
        if result.get('packing_overhead') is not None:
            packing_overheads.append(result['packing_overhead']);proof_validation_seconds+=result['packing_overhead']['setup_seconds']
        if result['evidence'] is not None:
            general=dict(profile=invocation['profile'],timing_inputs=_timing_inputs_from_batches(result['batches'],invocation['profile']),
                axis_scope=[{k:v for k,v in s.items() if k!='donors'} for specs in result['evidence']['runner_receipt']['scope']['batches'].values() for s in specs])
            path=root/'pilot-evidence'/part/invocation['invocation_id']
            payload=dict(evidence=result['evidence'],measurement=general,not_target_observations=True,
                source_commit=protocol['commit'],timing_only=part=='prefit',injected=design['injected'],runtime_profile=runtime_kernel_identity(model),
                positive_controls=result['positive_controls'],numeric_backing_references={} if part=='prefit' else
                    {str(Path(args.selected).absolute()):selected_reference})
            if path.exists():require(read_object(path)==payload,'pilot evidence output conflict')
            else:publish_object(path,payload)
            proof=_completed_packing_proof(path)
            packing_refs[str(path.resolve())]=proof.reference
            result['packing_id']=invocation['invocation_id']
            packing[result['packing_id']]=dict(kind='a3_packing_proof_reference_v1',evidence_sha256=proof.proof.source_digest,
                measured_path=str(path.resolve()),measured_reference=proof.reference)
            proof_validation_seconds+=proof.validation_seconds;proof_retained_bytes+=proof.retained_bytes
            compact=dict(invocation=invocation,packing_id=result['packing_id'],proof=proof,batches=result['batches'],
                samples=_compact_operation_samples(result['samples']),axis_count=proof.proof.distinct_axes,lookup_scope_seconds=result['lookup_scope_seconds'])
            result=compact
        else:
            path=root/'serial-pilot-evidence'/part/invocation['invocation_id']
            serial_payload=dict(kind='a3_serial_numeric_invocation_v1',injected=design['injected'],actual_execution=True,
                timing_only=part=='prefit',
                source_commit=protocol['commit'],runtime_profile=runtime_kernel_identity(model),receipt=result['receipt'],
                positive_controls=result['positive_controls'],numeric_backing_references={} if part=='prefit' else {str(Path(args.selected).absolute()):selected_reference})
            start=time.perf_counter();publish_object(path,serial_payload)
            serial=_SerialNumericProof(path);proof_validation_seconds+=time.perf_counter()-start
            serial_refs[invocation['invocation_id']]=dict(path=str(path.resolve()),reference=object_reference(path),source_digest=serial.source_digest)
        invocation_results.append(result)
    lookup_index=_PackingCandidateIndex([r['proof'] for r in invocation_results if r.get('proof') is not None])
    proof_validation_seconds+=lookup_index.index_seconds;proof_retained_bytes+=lookup_index.retained_bytes
    serialization_bytes=0
    reconciliation=_PilotReconciliationPass([r['proof'] for r in invocation_results if r.get('proof') is not None],target,guard=guard,
        injected=design['injected'],extra_witnesses=() if selected_witness is None else (selected_witness,))
    with reconciliation:
        target=reconciliation.inventory
        for req in target['requirements']:
            signature=workload.digest({k:req[k] for k in ('operation','profile','timing_keys','axis_ids','axis_scope','timing_inputs','donor_convention')})
            if signature in seen_measurements:continue
            seen_measurements.add(signature)
            reconciliation.check_deadline();op=req['operation'];profile=req['profile'];resources=_measurement_resources(model,root)
            measurement=dict(profile=copy.deepcopy(profile),operation=op,expected_keys=req['timing_keys'],observed_keys=[],
                axis_ids=req['axis_ids'],axis_scope=copy.deepcopy(req['axis_scope']),source_split='validation',synchronized=True,
                timing_inputs=req['timing_inputs'],donor_convention=req['donor_convention'],axis_class=req['axis_class'],
                nonzero_axis_count=0,cache_fit=True,cache_bytes=0,**{k:v for k,v in resources.items() if k!='host_peak_bytes'})
            if op=='guard_refresh':
                samples=[]
                for _ in range(3):
                    start=time.perf_counter();reconciliation.model_guard();samples.append(time.perf_counter()-start)
                measurement['batch_seconds']=samples
            elif op=='packing_lookup':
                start=time.perf_counter();candidates=lookup_index.candidates(profile,req['axis_scope'],axis_class=part=='prefit',runtime_profile=runtime_kernel_identity(model))
                elapsed=time.perf_counter()-start;require(candidates,'measured target lookup scope missing')
                scope_cost=max(r['lookup_scope_seconds'] for r in invocation_results if r.get('proof') in candidates)
                measurement['batch_seconds']=[elapsed+scope_cost]
                measurement['packing_id']=Path(candidates[0].path).name
                measurement['nonzero_axis_count']=candidates[0].proof.distinct_axes
                measurement['observed_keys']=candidates[0].proof.observed_requirement(req)
            elif op=='serialization':
                samples,shape_ids,nbytes=_time_serialization(profile['serialization_shapes'],design,protocol,root,reconciliation.model_guard)
                measurement.update(batch_seconds=samples,serialization_shape_ids=shape_ids);serialization_bytes+=nbytes
            elif op=='warmup':
                reconciliation.model_guard()
                example=next(x for x in target['requirements'] if x['timing_inputs'])
                warm_profile=dict(profile)
                inputs=example['timing_inputs'][:warm_profile['physical_batch_size']]
                b=_batch_for_timing(design,warm_profile,inputs);start=time.perf_counter()
                for _ in range(req['batches']):runner._capture_readouts(model,[b],sites=profile['sites'],sink=lambda _:None,
                    identity=dict(injected=True,numeric_profile=warm_profile),measuring=True)
                if runner.hooks.device_and_dtype(model)[0].type=='cuda':torch.cuda.synchronize()
                measurement['batch_seconds']=[time.perf_counter()-start]
            else:
                candidates=_pilot_candidates(invocation_results,req) if req['timing_inputs'] else []
                if op.startswith('capture_'):
                    reconciliation.model_guard()
                    b=_batch_for_timing(design,profile,req['timing_inputs']);chunks=[]
                    capture_run,samples=measure_runner_operations(model,lambda:runner._capture_readouts(model,[b],sites=profile['sites'],sink=chunks.append,
                        identity=dict(injected=True,numeric_profile=profile),measuring=True))
                    observed=[r for c in chunks for r in c['rows'] if not r['instance_id'].startswith('a3-dummy:')]
                    measurement['observed_keys']=[[r['task'],'validation',r['condition'],r['stream'],r['instance_id']] for r in observed]
                    require(Counter(map(workload._freeze,measurement['observed_keys']))==Counter(map(workload._freeze,req['timing_keys'])),'capture timing source coverage mismatch')
                    measurement['batch_seconds']=[s['seconds'] for s in samples]
                    if profile['axis_tile_size']>1:
                        measurement['capture_lane_equivalence']=capture_lane_evidence(capture_run,chunks,[b],req['timing_inputs'])
                        workload._capture_lane_evidence(measurement['capture_lane_equivalence'],measurement)
                    measurement['cache_bytes']=sum(h['value'].numel()*h['value'].element_size() for c in chunks for r in c['rows'] for h in r['heads'])
                elif op=='positive_control':
                    reconciliation.model_guard()
                    b=_batch_for_timing(design,profile,req['timing_inputs']);pid=runner.profile_identity({'numeric_profile':profile})
                    if b.task=='mmlu':ds,ms=_mmlu_positive(design,'validation',b,profile,{})
                    else:
                        donor=source_batches(design,b.task,'validation',b.ids,b.condition,'corrupt' if b.stream=='clean' else 'clean',profile)[0]
                        ds=[donor];ms=_maps(b,donor,pid)
                    controls,positive_times=measure_positive_operations(model,lambda:runner.run_positive_controls(model,[b],donor_batches=ds,donor_maps=ms,identity=dict(injected=True,numeric_profile=profile)))
                    measurement['batch_seconds']=positive_times
                    measurement['observed_keys']=[[r['task'],'validation',r['condition'],r['stream'],r['instance_id']] for r in controls['rows']]
                else:
                    require(candidates,'missing actual pilot operation profile')
                    result=next((x for x in candidates if _pilot_axes_covered(x,req['axis_scope'])),None)
                    # Prefit target scope freezes named attainable classes, without
                    # numeric axes; serial-only records carry the same named cells.
                    if result is None and part=='prefit':result=candidates[0]
                    require(result is not None,'actual selected timing axes/operations not covered')
                    measurement['observed_keys']=result['proof'].proof.observed_requirement(req) if result.get('proof') is not None else _observed_requirement(result['receipt'],req)
                    actual=[s['seconds'] for s in result['samples'] if s['profile']==profile and s['operation']==op and not s['dummy']]
                    require(actual,'actual synchronized operation timing missing')
                    measurement['batch_seconds']=[max(actual)];measurement['nonzero_axis_count']=result.get('axis_count',len(result.get('local_axes',{})))
                if profile['axis_tile_size']>1 and not op.startswith('capture_'):
                    coverage=next((x for x in candidates if x.get('packing_id') is not None and _pilot_axes_covered(x,req['axis_scope'])),None)
                    require(coverage is not None,'packed capture/operation lacks actual measured equivalence')
                    measurement['packing_id']=coverage['packing_id']
                    reconciliation.check(coverage['proof'],req,measurement)
            measured.append(measurement)
    final_authority=guard();resources=_measurement_resources(model,root)
    target_path=root/'pilot-target-inventory'/part
    if not target_path.exists():publish_object(target_path,target)
    require(workload.digest(read_object(target_path))==workload.digest(target),'pilot target output conflict')
    origin=_pilot_origin(args,root,inventory,target_path,final_authority,injected=design['injected'])
    receipt=dict(kind='a3_direction_timing_v1',status='completed',exit_code=0,complete=True,injected=design['injected'],
        identity=target['identity'],hardware=target['hardware'],inventory_sha256=target['inventory_sha256'],pilot_inventory_sha256=inventory['inventory_sha256'],
        startup_seconds=startup_seconds,proof_validation_seconds=proof_validation_seconds,proof_retained_bytes=proof_retained_bytes,host_peak_bytes=resources['host_peak_bytes'],measurements=measured,packing_evidence=packing,
        packing_references=packing_refs,serial_numeric_references=serial_refs,packing_overhead_measurements=packing_overheads,
        serialization_bytes=serialization_bytes,part=part,runtime=runtime_environment(model),
        job_id=os.environ.get('SLURM_JOB_ID','injected-cpu'),source_split='validation',actual_execution=True,
        origin=origin,runtime_profile=runtime_kernel_identity(model))
    reconciliation.before_publication()
    receipt.update(proof_verified_bytes=reconciliation.verified_bytes,proof_verification_seconds=reconciliation.verification_seconds)
    publish_object(root/'pilot'/part,receipt)
    target_path=root/'pilot-target-inventory'/part
    if not target_path.exists():publish_object(target_path,target)
    return receipt


def capture_lane_evidence(run,chunks,batches,timing_inputs):
    snapshots=packing_evidence({},batches)['snapshots'];vectors={}
    for batch,chunk in zip(batches,chunks):
        bid=runner._digest([runner._recipient_digest(batch,i) for i in range(len(batch.ids))])
        vectors[bid]=[dict(instance_id=row['instance_id'],site=h['site'],values=h['value'].detach().float().cpu().tolist())
            for row in chunk['rows'] for h in row['heads']]
    return dict(kind='a3_intact_lane_equivalence_v1',runner_receipts=run['lane_consistency_receipts'],snapshots=snapshots,
        head_vectors=vectors,timing_inputs_sha256=workload.digest(timing_inputs),serial_comparison_performed=False)


def assessment_probe_results(design,protocol,selected,inventory,*,root,guard):
    """CPU-only selected probe evaluation from completed intact readout caches."""
    from component_analysis import a3_directions
    root=Path(root);fit_path=selected['fit_reference']['path']
    require(pipeline._bundle_byte_reference(fit_path)==selected['fit_reference'],'assessment probe train fit bytes changed')
    fits,arrays,_,_=pipeline._read_selection_fits(design,protocol,fit_path)
    records=[]
    for chosen in selected['selected_records']:
        task=chosen['task'];site=chosen['site'];ids=design['tasks'][task]['assessment_ids'];heads={}
        for shard in inventory['shards']:
            key=shard['expected_keys'][0]
            if key[0]!='assessment' or key[1]!=task or key[2]!=task or list(key[5])!=site or key[6]!='learned' or key[8]!='interchange':continue
            if key[10] not in ('D','I'):continue
            guard();manifest=artifacts._strict_json(root/'runtime-shards'/shard['shard_id']/'run_manifest.json')
            metadata,cached=read_bundle(manifest['execution']['capture_reference']['path'])
            for row in metadata['runner_rows']:
                if row['instance_id'] not in ids or row['condition'] not in ('D','I'):continue
                head=next(h for h in row['heads'] if h['site']==site);value=np.array(cached[head['array']],dtype=np.float32,copy=True)
                k=(row['condition'],row['instance_id'],row['stream'])
                require(k not in heads or np.array_equal(heads[k],value),'assessment probe intact capture changed')
                heads[k]=value
        expected={(c,rid,s) for c in ('D','I') for rid in ids for s in pipeline.STREAMS}
        for name in ('image_probe','metadata_probe'):
            receipt=chosen[name];base=dict(task=task,seed=chosen['seed'],site=site,probe=name,fit_receipt=copy.deepcopy(receipt))
            if receipt['status']!='fitted':
                records.append(dict(base,status='unavailable',reason=receipt['reason']));continue
            if name=='image_probe':
                require(set(heads)==expected,'complete actual assessment readouts required for selected image probe')
                z=torch.from_numpy(np.stack([np.stack([np.stack([heads[(c,rid,s)] for s in pipeline.STREAMS]) for rid in ids]) for c in ('D','I')]))
                geometry=fits['geometries'][chosen['geometry']]
                projection=pipeline._tensor(arrays[geometry['arrays']['projection']]);u=pipeline._tensor(arrays[geometry['arrays']['U']])
                x=z@(projection.T@u)
            else:
                x=torch.stack(pipeline._metadata_features(design,task,ids,split='assessment'))
            probe={k:pipeline._tensor(arrays[v]) for k,v in receipt['arrays'].items()}
            probe.update(intercept=receipt['intercept'],regularization=receipt['regularization'])
            x=x.reshape(-1,x.shape[-1]);labels=torch.cat((torch.ones(len(ids)*2),-torch.ones(len(ids)*2)))
            predictions=a3_directions.probe_predictions(probe,x)
            correct=(predictions==labels).reshape(2,len(ids),2).cpu().numpy()
            mean=float(np.asarray(correct,dtype=float).mean());reviewed=a3_directions.probe_balanced_accuracy(probe,x,labels)
            require(abs(mean-reviewed)<=1e-7,'selected probe correctness differs from reviewed scalar estimator')
            records.append(dict(base,status='completed',instance_ids=list(ids),conditions=['D','I'],streams=list(pipeline.STREAMS),
                correct=correct.astype(int).tolist(),balanced_accuracy=mean,reviewed_balanced_accuracy=reviewed))
    return dict(kind='a3_direction_probe_results',complete=True,split='assessment',fit_reference=copy.deepcopy(selected['fit_reference']),records=records)


def summarize_runtime(design,protocol,selected,rows,calibration_rows,references,calibration_references,*,root,inventory,final,guard):
    from component_analysis import a3_direction_reporting as reporting
    guard()
    if final:require(design.get('injected') is False,'injected lineage cannot finalize')
    artifacts._coverage(rows+calibration_rows,inventory['expected_keys'])
    validate_primary_interpretability(rows+calibration_rows)
    probes=assessment_probe_results(design,protocol,selected,inventory,root=root,guard=guard)
    inputs=dict(design=design,selected=selected,rows=rows,calibration_rows=calibration_rows,probe_results=probes)
    refs={name:dict(sha256=hashlib.sha256(reporting._bytes(value)).hexdigest(),nbytes=len(reporting._bytes(value))) for name,value in inputs.items()}
    refs['rows']['artifact_reference']=references;refs['calibration_rows']['artifact_reference']=calibration_references
    result=reporting.assemble_direction_summary(design,selected,rows,input_references=refs,calibration_rows=calibration_rows,
        probe_results=probes,final=False,n_boot=protocol['bootstrap']['assessment'],seed=protocol['bootstrap']['assessment_seed'],
        n_rep=protocol['bootstrap']['power'],power_seed=protocol['bootstrap']['power_seed'])
    identity=dict(inventory['identity'],injected=design['injected'],pilot=False,complete=True)
    artifacts.validate_final_identity(identity,final=final)
    if final:
        require(set(design['tasks'])=={'far_v2','ser_v2','sdr_v2'} and design['seeds']==[42,1,123]
            and len(design['utility']['ioi'])==100 and len(design['utility']['mmlu'])==32
            and len(design['ioi_validation'])==100 and len(design['mmlu_validation'])==32
            and all(len(s['assessment_ids'])==100 for s in design['tasks'].values()),'complete original production counts required for final')
        require(result['diagnostic_readiness'] is True and all(r.get('supported') is True and r.get('replay_valid') is True
            and r.get('gate_valid') is True and r.get('positive_control',{}).get('valid') is True for r in rows+calibration_rows),
            'complete actual utility/control/secondary/steering/probe evidence required for final')
    result.update(finalized=bool(final),runtime_identity=identity,execution_evidence=dict(complete=True,actual_execution=True,
        observed_rows=len(rows)+len(calibration_rows),expected_rows=len(inventory['expected_keys']),
        inventory_sha256=inventory['inventory_sha256'],assessment_references=references,calibration_references=calibration_references,
        selection_reference=object_reference(Path(root)/'selected'),source_guard=guard()),continuation_authorized=False)
    publish_object(Path(root)/'summary',result)
    return result


def summarize_calibration(design,protocol,selected,rows,references,*,root,inventory,guard):
    from component_analysis import a3_direction_reporting as reporting,a3_statistics
    guard();require(all(r.get('split')=='validation' and r.get('panel')=='calibration' for r in rows),'conditional power requires validation-only calibration rows')
    panel=reporting.pack_statistics_panel(design,selected,rows,split='validation')
    result=a3_statistics.simulate_conditional_power(panel,n_rep=protocol['bootstrap']['power'],seed=protocol['bootstrap']['power_seed'])
    payload=dict(kind='a3_direction_conditional_power_summary_v1',complete=True,injected=design['injected'],source_split='validation',
        inventory_sha256=inventory['inventory_sha256'],design_sha256=workload.digest(design),protocol_sha256=workload.digest(protocol),
        selected_reference=object_reference(Path(root)/'selected'),raw_row_references=references,
        raw_rows_sha256=hashlib.sha256(reporting._bytes(rows)).hexdigest(),conditional_power=result,
        continuation_authorized=False,assessment_outcomes_read=False,source_guard=guard())
    publish_object(Path(root)/'calibration-summary',a3_statistics._json(payload))
    return payload


_MEASURED_PACKING_CACHE={}


_NUMERIC_BACKING_CACHE={}


def _numeric_backing_proof(path,reference,profile,*,injected):
    key=str(Path(path).absolute())
    require(pipeline._bundle_byte_reference(path)==reference,'numeric backing reference bytes changed')
    if key in _NUMERIC_BACKING_CACHE:
        cached=_NUMERIC_BACKING_CACHE[key]
        require(cached['pid']==os.getpid() and cached['reference']==reference,'numeric backing identity/process changed')
        require(cached['injected']==injected and cached['source_signature']==tuple(profile[k] for k in ('model','model_revision','source_sha256')),
            'numeric backing injected/source profile boundary changed')
        _check_file_witness(cached['witness']);return cached
    root=Path(path);axis_hashes=frozenset();identity=None
    if (root/'manifest.json').is_file():
        metadata,_=read_bundle(path)
        require(metadata.get('kind')=='a3_direction_selection','numeric backing must be completed direction selection')
        identity=metadata['inventory_identity']
        require(identity['model']==profile['model'] and identity['model_revision']==profile['model_revision']
            and workload.digest(identity['code_hashes'])==profile['source_sha256'],'numeric backing source/model profile differs')
        axes=load_selected_axes(path,metadata);axis_hashes=frozenset(runner.axis_identity(axis) for axis in axes.values())
    else:
        require(injected and list(root.glob('*.npy')),'nonproduction numeric fixture requires explicit injected arrays')
        for numeric in root.glob('*.npy'):
            array=np.load(numeric,allow_pickle=False,mmap_mode='r');require(np.isfinite(array).all(),'nonfinite injected numeric backing')
    witness=_make_file_witness([path]);require(pipeline._bundle_byte_reference(path)==reference,'numeric backing changed during validation')
    cached=dict(pid=os.getpid(),reference=_freeze_json(reference),axis_hashes=axis_hashes,witness=witness,identity=_freeze_json(identity),
        injected=injected,source_signature=tuple(profile[k] for k in ('model','model_revision','source_sha256')))
    _NUMERIC_BACKING_CACHE[key]=cached;return cached


class _DependencyForest:
    """One immutable expected fingerprint per distinct referenced root."""
    def __init__(self,witnesses):
        if getattr(self,'_sealed',False):raise TypeError('dependency forests cannot be reinitialized')
        expected={}
        for witness in witnesses:
            require(type(witness) is _FileWitness and witness.pid==os.getpid(),'validator-minted file witnesses required')
            for path,identity in zip(witness.paths,witness.identities):
                require(path not in expected or expected[path]==identity,'conflicting immutable dependency references')
                expected[path]=identity
        self.paths=tuple(sorted(expected));self.expected=tuple(expected[p] for p in self.paths);self.pid=os.getpid()
        self.refreshes=0;self.verified_bytes=0;self.elapsed_seconds=0.;self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('dependency metadata is immutable')
        object.__setattr__(self,name,value)
    def __delattr__(self,name):raise TypeError('dependency metadata is immutable')
    def refresh(self):
        require(self.pid==os.getpid(),'dependency forest cannot cross process/restart')
        start=time.perf_counter();actual=tuple(_file_tree_identity(p) for p in self.paths)
        require(actual==self.expected,'immutable referenced dependency bytes changed')
        volume=sum(row[2][3] for tree in actual for row in tree if row[0]=='file')
        elapsed=time.perf_counter()-start
        object.__setattr__(self,'refreshes',self.refreshes+1);object.__setattr__(self,'verified_bytes',self.verified_bytes+volume)
        object.__setattr__(self,'elapsed_seconds',self.elapsed_seconds+elapsed)
        return dict(verified_bytes=volume,elapsed_seconds=elapsed,roots=len(self.paths))
    def __reduce__(self):raise TypeError('dependency forests are process-local')


class _PackingCandidateIndex:
    """Validator-minted immutable metadata lookup; never execution authority."""
    def __init__(self,proofs,*,extra_witnesses=(),startup_seconds=0.):
        if getattr(self,'_sealed',False):raise TypeError('candidate indexes cannot be reinitialized')
        start=time.perf_counter()
        require(all(type(p) is _CompletedPackingProof and p.pid==os.getpid() for p in proofs),'independently validated completed packing proofs required')
        self.proofs=tuple(proofs);groups={}
        for proof in proofs:groups.setdefault(workload.digest(proof.proof._profile),[]).append(proof)
        self._profiles=_freeze_json(groups);self.pid=os.getpid()
        self.forest=_DependencyForest([p.witness for p in proofs]+list(extra_witnesses))
        self.retained_bytes=sum(p.retained_bytes for p in proofs)+_retained_json_bytes([self._profiles,self.forest.expected])[0]
        self.index_seconds=time.perf_counter()-start;self.startup_seconds=startup_seconds+self.index_seconds;self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('candidate index is immutable')
        object.__setattr__(self,name,value)
    def __delattr__(self,name):raise TypeError('candidate index is immutable')
    def candidates(self,profile,axis_scope,*,axis_class=False,runtime_profile=None,mask_branches=None):
        require(self.pid==os.getpid(),'candidate index cannot cross process/restart')
        wanted=[{k:axis[k] for k in ('site','operation')} for axis in axis_scope] if axis_class else axis_scope
        result=[]
        for proof in self._profiles.get(workload.digest(profile),[]):
            if not proof.proof.covers_axes(wanted):continue
            if runtime_profile is not None and proof.metadata.get('runtime_profile')!=runtime_profile:continue
            if mask_branches is not None:
                seen={(r['task'],_mask_branch(r)) for rows in proof.metadata['evidence']['snapshots'].values() for r in rows}
                if not mask_branches<=seen:continue
            result.append(proof)
        return result
    def refresh_dependencies(self):return self.forest.refresh()
    def __reduce__(self):raise TypeError('candidate indexes are process-local')


class _DependencyGuard:
    """Fresh live authority plus one full deduplicated dependency-byte pass."""
    def __init__(self,guard,index):
        require(type(index) is _PackingCandidateIndex,'validated candidate index required')
        self.guard=guard;self.index=index;self.calls=0;self.elapsed_seconds=0.
    def __call__(self):
        start=time.perf_counter();self.index.refresh_dependencies();result=self.guard()
        self.calls+=1;self.elapsed_seconds+=time.perf_counter()-start
        return result


class _CompletedPackingProof:
    """Completed-file-bound numerical proof with bounded immutable metadata."""
    def __init__(self,path):
        start=time.perf_counter();self.pid=os.getpid();self.path=str(Path(path).absolute())
        self.reference=_freeze_json(object_reference(path));payload=read_object(path)
        require(type(payload.get('injected')) is bool,'explicit measured proof execution class required')
        if not payload['injected']:require(type(payload.get('timing_only')) is bool,'explicit production measured timing stage required')
        self.proof=workload._validate_packing_proof(payload['evidence'],payload['measurement'])
        raw=payload['evidence']['runner_receipt']
        snapshots={bid:[self.proof._rows[(r['task'],r['condition'],r['stream'],r['instance_id'])] for r in rows]
            for bid,rows in payload['evidence']['snapshots'].items()}
        self.metadata=_freeze_json(dict({k:v for k,v in payload.items() if k in ('runtime_profile','injected','source_commit','timing_only','not_target_observations')},
            measurement=dict(profile=self.proof._profile),evidence=dict(snapshots=snapshots,
                runner_receipt=dict(receipt_sha256=raw['receipt_sha256'],scope=dict(profile=self.proof._profile,batches=self.proof._batches)))))
        references=payload.get('numeric_backing_references',{})
        require(isinstance(references,dict),'numeric backing references must be immutable completed bindings')
        if payload.get('injected') is not True and payload.get('timing_only') is False:
            require(references,'selected measurements require actual numeric backing references')
        summaries=tuple(_numeric_backing_proof(backing,reference,self.proof._profile,injected=payload.get('injected') is True)
            for backing,reference in references.items())
        hashes=frozenset(h for summary in summaries for h in summary['axis_hashes'])
        if hashes:require(all(spec['axis_sha256'] in hashes for spec in self.proof._specs.values()),'measured axis differs from actual numeric backing')
        self.numeric_backing_summaries=tuple((x['axis_hashes'],x['reference']) for x in summaries)
        self.witness=_make_file_witness([path,*references])
        require(object_reference(path)==self.reference,'measured packing bytes changed during validation')
        self.retained_bytes,_=_retained_json_bytes([self.metadata,self.proof._rows,self.proof._specs,self.proof._observed,self.witness.identities,self.numeric_backing_summaries])
        self.validation_seconds=time.perf_counter()-start;self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('completed packing proofs are immutable')
        object.__setattr__(self,name,value)
    def __delattr__(self,name):raise TypeError('completed packing proofs are immutable')
    def refresh(self):
        require(self.pid==os.getpid(),'packing proofs cannot cross process/restart');_check_file_witness(self.witness)
    def check(self,measurement):self.refresh();return self.proof.check(measurement)
    def __reduce__(self):raise TypeError('completed packing proofs are process-local')


def _completed_packing_proof(path,*,expected_reference=None):
    key=str(Path(path).absolute())
    if key not in _MEASURED_PACKING_CACHE:_MEASURED_PACKING_CACHE[key]=_CompletedPackingProof(path)
    proof=_MEASURED_PACKING_CACHE[key];proof.refresh()
    if expected_reference is not None:require(proof.reference==expected_reference,'measured evidence bytes changed')
    return proof


def _validated_measurement(path,*,expected_reference=None):
    return _completed_packing_proof(path,expected_reference=expected_reference).metadata


_COMPLETED_PILOT_SOURCE_SEAL=object()


class _CompletedPilotSource:
    """Immutable completed execution provenance; explicitly no execution authority."""
    def __init__(self,seal,value):
        require(seal is _COMPLETED_PILOT_SOURCE_SEAL and not hasattr(self,'value'),'completed pilot source requires independent validation')
        object.__setattr__(self,'value',_freeze_json(dict(value,execution_authorized=False)))
    def __setattr__(self,*args):raise TypeError('completed pilot sources are immutable')
    def __delattr__(self,*args):raise TypeError('completed pilot sources are immutable')
    def __reduce__(self):raise TypeError('completed pilot source proofs are process-local')


def _completed_pilot_source(receipt_path,receipt,expected_pilot,origin,*,injected):
    require(isinstance(origin,dict) and origin.get('kind')=='a3_direction_pilot_origin_v1','original pilot execution bindings required')
    def resolved_object(name):
        ref=origin[name];path=ref['path'];require(object_reference(path)==ref,'completed pilot '+name+' bytes changed');return path,read_object(path)
    reservation_path,reservation=resolved_object('reservation_reference')
    mapping_path,_=resolved_object('original_mapping_reference')
    require(reservation.get('kind')=='a3_root_execution_reservation_v1' and reservation.get('identity')==expected_pilot['identity']
        and reservation.get('inventory_sha256')==expected_pilot['inventory_sha256'],'original pilot reservation/source differs')
    pilot_path,pilot=resolved_object('pilot_inventory_reference')
    workload._validate_inventory(pilot)
    require(workload.digest(pilot)==workload.digest(expected_pilot),'original executed pilot inventory differs from rebuilt scope')
    upper=read_object(reservation['upper_inventory_path']);workload._validate_inventory(upper)
    require(workload.digest(upper)==workload.digest(expected_pilot),'completed pilot original upper scope differs')
    ledger=normalize_ledger(mapping_path,identity=expected_pilot['identity'],injected=injected,include_envelope=True)
    matches=[e for e in ledger['entries'] if e['id']==reservation.get('reservation_id')]
    require(len(matches)==1,'completed original pilot RS reservation missing')
    entry=matches[0];actual=entry['actual_entry']
    require(entry['state']=='completed' and entry['phase']=='M1' and entry['subphase']=='directions'
        and entry['inventory_sha256']==expected_pilot['inventory_sha256'],'pilot requires actual COMPLETED M1 direction reservation')
    require(reservation['actual_entry']=={k:actual.get(k) for k in RESERVATION_FIELDS},'completed pilot immutable job/source/output changed')
    require(str(actual['job_id'])==str(receipt['job_id']) and actual['source_commit']==expected_pilot['identity']['commit'],'completed pilot original job/source mismatch')
    root=Path(actual['output_dir']).resolve()
    require(Path(receipt_path).resolve()==root/'pilot'/receipt['part'] and Path(origin['work_dir']).resolve()==root,'pilot receipt is not original canonical job output')
    admission_path,admission=resolved_object('admission_reference')
    require(reservation['admission_path']==admission_path and reservation['admission_reference']==origin['admission_reference']
        and admission in ledger['original_admissions'],'pilot original admission is not independently anchored')
    require(admission.get('kind') in ROOT_ADMISSION_KINDS and admission['identity']==expected_pilot['identity']
        and admission['admission_sha256']==reservation['admission_sha256'] and admission['upper_inventory_sha256']==upper['inventory_sha256'],'completed pilot original admission differs')
    anchors=admission.get('reservation_ids');require(isinstance(anchors,list) and anchors and entry['id'] in anchors,'completed pilot original anchors empty/unrelated')
    linked=[e for e in ledger['entries'] if e.get('reservation_lineage',{}).get('admission_id')==admission['id']]
    require(set(anchors)<={e['id'] for e in linked},'completed pilot admission omitted original charges')
    for e in linked:
        line=e['reservation_lineage']
        require(line.get('admission_sha256')==admission['admission_sha256'] and line.get('max_gpu_hours')==admission['max_gpu_hours']
            and line.get('upper_inventory_sha256')==upper['inventory_sha256'] and line.get('reserved_gpu_hours')==e['reserved_gpu_hours'],'completed pilot original reserved envelope changed')
    require(sum(e['reserved_gpu_hours'] for e in linked)<=admission['max_gpu_hours'],'completed pilot original ceiling exhausted')
    sums=workload._ledger(ledger,expected_pilot['identity']);validate_global_budgets(ledger['entries'],contingency_remaining=sums['contingency_remaining'])
    contract=validate_allocation_contract(reservation.get('allocation_contract'),actual,expected_pilot,injected=injected)
    require(contract is not None and admission.get('allocation_contract')==contract,'completed pilot allocation contract lacks original binding')
    require(contract['memory_bytes']>=ledger['storage_capacities']['host_ram']['available_bytes'],'completed pilot cannot back declared host capacity')
    return _CompletedPilotSource(_COMPLETED_PILOT_SOURCE_SEAL,dict(kind='a3_completed_pilot_source_v1',
        reservation_reference=origin['reservation_reference'],admission_reference=origin['admission_reference'],
        original_mapping_reference=origin['original_mapping_reference'],current_mapping_reference=ledger.get('active_mapping_reference',ledger['original_mapping_reference']),
        live_ledger_sha256=ledger['snapshot_sha256'],actual_entry=actual,receipt_reference=object_reference(receipt_path),pilot_inventory_reference=origin['pilot_inventory_reference']))


def _pilot_origin(args,root,pilot,target_path,guard_result,*,injected):
    if injected:return dict(kind='a3_injected_pilot_origin_v1',execution_authorized=False)
    require(isinstance(guard_result,dict) and guard_result.get('reservation',{}).get('execution_authorized') is True,'actual pilot execution authority required for producer provenance')
    evidence=guard_result['reservation'];reservation=evidence['reservation']
    require(args.reservation and args.ledger_snapshot and args.inventory,'original pilot source paths required')
    return dict(kind='a3_direction_pilot_origin_v1',work_dir=str(Path(root).resolve()),
        reservation_reference=evidence['reservation_reference'],admission_reference=reservation['admission_reference'],
        original_mapping_reference=object_reference(args.ledger_snapshot),pilot_inventory_reference=object_reference(args.inventory),
        target_inventory_reference=object_reference(target_path),allocation=evidence['allocation'],source_snapshot_sha256=evidence['ledger_sha256'])


class _SerialNumericProof:
    """Completed actual serial observations; never a packing-equivalence receipt."""
    def __init__(self,path):
        if getattr(self,'_sealed',False):raise TypeError('serial proofs cannot be reinitialized')
        payload=read_object(path);require(payload.get('kind')=='a3_serial_numeric_invocation_v1' and payload.get('actual_execution') is True,'actual typed serial invocation required')
        receipt=payload['receipt'];require(receipt.get('kind')=='measured_serial_direction_v1' and receipt.get('valid') is True
            and receipt.get('receipt_sha256')==workload.digest({k:v for k,v in receipt.items() if k!='receipt_sha256'}),'serial numeric receipt content differs')
        profile=receipt['profile'];require(profile['axis_tile_size']==1,'serial receipt cannot substitute for packed equivalence')
        snapshots=receipt['snapshots'];require(set(snapshots)==set(receipt['batches']) and snapshots,'serial input scope missing')
        expected={};specs=[];rows={}
        for bid,inputs in snapshots.items():
            require(bid==runner._digest([runner._digest(row) for row in inputs]) and len(inputs)==profile['physical_batch_size'],'serial source/physical batch changed')
            for row in inputs:rows[(row['task'],row['condition'],row['stream'],row['instance_id'])]=row
            for spec in receipt['batches'][bid]:
                specs.append(spec)
                for row in inputs:
                    key=(row['task'],row['condition'],row['stream'],row['instance_id'],spec['seed'],tuple(spec['site']),spec['family'],spec['axis_index'],spec['operation'])
                    require(key not in expected,'duplicate serial execution key');expected[key]=spec['axis_sha256']
        observed={}
        for row in receipt['rows']:
            key=(row['source_task'],row['condition'],row['stream'],row['instance_id'],row['seed'],tuple(row['site']),row['family'],row['axis_index'],row['operation'])
            require(key not in observed and row.get('axis_hash')==expected.get(key),'serial actual numeric axis/row coverage changed')
            require(row.get('replay_valid') is True and set(row.get('replay_errors',{}))=={'empty','head_self','zero_coefficient'}
                and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1e-5 for v in row['replay_errors'].values()),'serial replay evidence invalid')
            require(all(type(row.get(k)) in (int,float) and math.isfinite(row[k]) for k in ('head_norm','intact_margin','patched_margin')),'serial numeric observation nonfinite')
            observed[key]=row
        require(set(observed)==set(expected),'serial actual row coverage incomplete')
        positives={(r['task'],r['condition'],r['stream'],r['instance_id']):r for r in payload['positive_controls']}
        require(set(positives)==set(rows) and all(p.get('valid') is True and p.get('kind')=='measured_all_sender_positive_v2' for p in positives.values()),'serial own positive backing incomplete')
        samples=receipt['operation_samples'];counts=Counter(x['operation'] for x in samples)
        require(all(counts[op]==len(expected)//profile['physical_batch_size'] for op in workload.REPLAYS)
            and all(type(x.get('seconds')) in (int,float) and math.isfinite(x['seconds']) and x['seconds']>0 for x in samples),'serial actual timing/forward counts incomplete')
        references=payload.get('numeric_backing_references',{})
        require(isinstance(references,dict),'serial backing references must be immutable completed bindings')
        if payload.get('injected') is not True:
            require(type(payload.get('timing_only')) is bool,'explicit serial numeric measurement stage required')
            if not payload['timing_only']:require(references,'selected serial measurements require actual numeric backing')
        for root,reference in references.items():
            backing=_numeric_backing_proof(root,reference,profile,injected=payload.get('injected') is True)
            if backing['axis_hashes']:require(set(expected.values())<=backing['axis_hashes'],'serial axis differs from actual selected backing')
        self.profile=_freeze_json(profile);self.rows=_freeze_json(rows);self.specs=_freeze_json(specs)
        self.source_digest=workload.digest(payload);self.reference=_freeze_json(object_reference(path));self.witness=_make_file_witness([path,*references]);self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('serial proof metadata immutable')
        object.__setattr__(self,name,value)
    def __delattr__(self,name):raise TypeError('serial proof metadata immutable')
    def check_scope(self,measurement):
        require(measurement['profile']==self.profile,'serial profile differs');workload._packing_measurement_scope(self.rows,self.specs,measurement)
    def __reduce__(self):raise TypeError('serial proofs are process-local')


def _expected_pilot_batches(design,invocation):
    source=invocation['source_task'];profile=invocation['profile'];result=[]
    for group in invocation['batch_groups']:
        ids,dummies=workload.execution_membership(source,'validation',group['condition'],group['instance_ids'],profile['physical_batch_size']//profile['axis_tile_size'])
        result.extend(source_batches(design,source,'validation',ids,group['condition'],group['stream'],profile,dummy_sources=dummies))
    return result


def _pilot_scope_measurement(design,invocation):
    batches=_expected_pilot_batches(design,invocation)
    scope=[{k:v for k,v in cell.items() if k in ('site','seed','family','axis_index','operation','axis_sha256')} for cell in invocation['cells']]
    return dict(profile=invocation['profile'],timing_inputs=_timing_inputs_from_batches(batches,invocation['profile']),axis_scope=scope)


def _exact_pilot_scope(rows,specs,measurement):
    expected={(x['source_task'],x['condition'],x['stream'],x['instance_id']) for x in measurement['timing_inputs']}
    require(set(rows)==expected,'pilot actual input membership differs from rebuilt invocation')
    fields=('site','seed','family','axis_index','operation')
    key=lambda value:tuple(workload._freeze(value[k]) for k in fields)
    require({key(x) for x in specs}=={key(x) for x in measurement['axis_scope']},'pilot actual cell/axis membership differs from rebuilt invocation')


def _authenticate_serial_references(design,protocol,expected,receipt):
    invocations=_serial_invocations(expected);refs=receipt.get('serial_numeric_references',{})
    require(set(refs)=={x['invocation_id'] for x in invocations},'complete original serial invocation references required')
    for invocation in invocations:
        value=refs[invocation['invocation_id']];path=value['path']
        require(object_reference(path)==value['reference'],'serial numeric evidence bytes changed')
        proof=_SerialNumericProof(path)
        require(proof.source_digest==value['source_digest'] and proof.profile==invocation['profile'],'serial numeric source/profile differs')
        measurement=_pilot_scope_measurement(design,invocation)
        proof.check_scope(measurement);_exact_pilot_scope(proof.rows,proof.specs,measurement)
        payload=read_object(path)
        require(payload['injected'] is receipt['injected'] and payload['runtime_profile']==receipt['runtime_profile'] and payload['source_commit']==expected['identity']['commit']
            and payload.get('timing_only') is (receipt['part']=='prefit'),'serial original runtime/source/stage differs')
        if not design.get('injected'):
            require(Path(path).resolve()==Path(receipt['origin']['work_dir']).resolve()/'serial-pilot-evidence'/receipt['part']/invocation['invocation_id'],'serial evidence is not canonical original output')
        wanted=[{k:v for k,v in cell.items() if k in ('site','seed','family','axis_index','operation','axis_sha256')} for cell in invocation['cells']]
        require(all(any(all(spec.get(k)==v for k,v in cell.items()) for spec in proof.specs) for cell in wanted),'serial rebuilt actual axis scope missing')


def _authenticated_pilot_receipts(design,protocol,target,receipt_paths,*,ledger_path):
    """Authenticate measured production sources before the pure cost projector."""
    require(target['stage'] in ('fit-select','remaining'),'cost intake requires frozen fit/remaining target')
    selected=target.get('frozen_inputs',{}).get('selected');fits=target.get('frozen_inputs',{}).get('fits')
    rebuilt=workload.build_inventory(design,protocol,stage=target['stage'],selected=selected,fits=fits)
    require(workload.digest(rebuilt)==workload.digest(target),'cost target differs from independent rebuilt inventory')
    part='prefit' if target['stage']=='fit-select' else 'selected'
    expected=workload.build_inventory(design,protocol,stage='prefit' if part=='prefit' else 'selected-pilot',selected=selected)
    receipts=[];sources=[]
    for path in receipt_paths:
        receipt=read_object(path)
        require(type(receipt.get('injected')) is bool and receipt['injected'] is bool(design.get('injected')),'pilot execution class differs from target')
        require(receipt.get('actual_execution') is True and receipt.get('status')=='completed' and receipt.get('complete') is True
            and type(receipt.get('exit_code')) is int and receipt['exit_code']==0,'successful actual native pilot required')
        require(receipt.get('part')==part and receipt.get('source_split')=='validation'
            and receipt.get('pilot_inventory_sha256')==expected['inventory_sha256'] and receipt.get('inventory_sha256')==target['inventory_sha256'],
            'completed pilot stage/part/target scope differs')
        require(receipt['identity']==target['identity'] and receipt['hardware']==target['hardware'],'pilot source/model/hardware differs')
        runtime=receipt.get('runtime',{});kernel=receipt.get('runtime_profile')
        require(isinstance(kernel,dict) and runtime.get('runtime_profile')==kernel,'actual consistent pilot runtime/kernel required')
        if not design.get('injected'):
            require(runtime.get('device','').startswith('cuda') and kernel.get('device_type')=='cuda'
                and 'h200' in kernel.get('hardware',{}).get('name','').lower(),'production pilot must use measured H200 CUDA runtime')
            require(kernel.get('backend')==protocol['numeric_profile']['backend']
                and str(kernel.get('dtype')).removeprefix('torch.')==str(protocol['numeric_profile']['dtype']).removeprefix('torch.'),'pilot kernel differs from frozen numeric profile')
            source=_completed_pilot_source(path,receipt,expected,receipt.get('origin'),injected=False)
            origin=receipt['origin'];ref=origin['target_inventory_reference'];require(object_reference(ref['path'])==ref,'pilot target inventory bytes changed')
            original_target=read_object(ref['path']);workload._validate_inventory(original_target)
            require(workload.digest(original_target)==workload.digest(target),'pilot original target differs from admission target')
            sources.append(source)
        expected_ids={x['invocation_id'] for x in expected['packing_invocations']}
        evidence=receipt.get('packing_evidence',{});references=receipt.get('packing_references',{})
        if expected_ids:
            require(set(evidence)==expected_ids,'complete original packed pilot invocation references required')
            for invocation_id,value in evidence.items():
                require(value.get('kind')=='a3_packing_proof_reference_v1','production/native intake refuses synthetic inline packing evidence')
                measured_path=value['measured_path'];reference=value['measured_reference']
                require(references.get(str(Path(measured_path).resolve()))==reference,'pilot packing reference mapping differs')
                proof=_completed_packing_proof(measured_path,expected_reference=reference)
                invocation=next(x for x in expected['packing_invocations'] if x['invocation_id']==invocation_id)
                measurement=_pilot_scope_measurement(design,invocation)
                proof.proof.check(measurement);_exact_pilot_scope(proof.proof._rows,list(proof.proof._specs.values()),measurement)
                require(proof.proof.source_digest==value['evidence_sha256'] and proof.metadata.get('injected') is receipt['injected']
                    and proof.metadata.get('runtime_profile')==kernel and proof.metadata.get('source_commit')==target['identity']['commit']
                    and proof.metadata.get('timing_only') is (part=='prefit'),'pilot measured numeric execution/source/stage differs')
                if not design.get('injected'):
                    require(Path(measured_path).resolve()==Path(receipt['origin']['work_dir']).resolve()/'pilot-evidence'/part/invocation_id,'numeric evidence is not original pilot output')
            require(set(references)=={str(Path(v['measured_path']).resolve()) for v in evidence.values()},'extra/missing original numeric references')
        else:
            require(not evidence and not references,'serial pilot cannot claim packed-equivalence evidence')
            _authenticate_serial_references(design,protocol,expected,receipt)
        receipts.append(receipt)
    require(receipts,'completed actual pilot receipts required')
    if sources:
        current=normalize_ledger(ledger_path,identity=target['identity'],injected=False,include_envelope=True)
        lineage=current.get('mapping_lineage_references',[])+[current['original_mapping_reference'],current.get('active_mapping_reference',current['original_mapping_reference'])]
        require(all(source.value['current_mapping_reference'] in lineage for source in sources),'cost ledger is not the completed pilot original mapping/successor lineage')
    return receipts,sources


def _cost_packing_proofs(receipts):
    proofs={}
    for receipt in receipts:
        sha=workload.digest(receipt)
        for pid,evidence in receipt.get('packing_evidence',{}).items():
            if evidence.get('kind')!='a3_packing_proof_reference_v1':continue
            path=evidence['measured_path'];ref=evidence['measured_reference']
            require(receipt.get('packing_references',{}).get(str(Path(path).resolve()))==ref,'pilot measured reference mapping differs')
            proof=_completed_packing_proof(path,expected_reference=ref)
            require(proof.proof.source_digest==evidence['evidence_sha256'],'pilot measured source digest differs')
            proofs[(sha,pid)]=proof.proof
    return proofs


def validate_global_budgets(entries,*,contingency_remaining):
    """Task 6's additive milestones; reservations charge exactly one phase."""
    totals=Counter();shares=Counter()
    for entry in entries:
        hours=entry['reserved_gpu_hours'];require(type(hours) in (int,float) and math.isfinite(hours) and hours>=0,'invalid original reservation hours')
        phase=entry['phase'];require(phase in ('M1','M2','M3','M4','M5','contingency'),'unknown A3 milestone')
        totals[phase]+=hours;totals['all']+=hours;shares[(phase,entry.get('subphase'))]+=hours
    require(type(contingency_remaining) in (int,float) and math.isfinite(contingency_remaining) and contingency_remaining>=0,'invalid remaining contingency')
    for phase,ceiling in dict(M1=2,M2=9,M3=4,M4=9,M5=10).items():require(totals[phase]<=ceiling+1e-9,'A3 '+phase+' original reservation ceiling exceeded')
    for sub,ceiling in dict(directions=.5,edges=.75,masks=.75).items():require(shares[('M1',sub)]<=ceiling+1e-9,'A3 M1 '+sub+' ceiling exceeded')
    require(totals['contingency']+contingency_remaining>=6-1e-9 and totals['all']+contingency_remaining<=40+1e-9,'A3 total including original contingency exceeded')
    return dict(totals)


_AUTHORITY_SEAL=object()


def _stat_identity(path):
    st=path.lstat()
    return (st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def _file_tree_identity(path):
    """Fresh byte fingerprints, walking resolved directories without repeated parent RPCs."""
    import stat
    path=Path(path).absolute();rows=[];links=set()
    def record_links(node):
        for candidate in [node]+list(node.parents):
            if candidate in links:continue
            if candidate.is_symlink():
                try:target=candidate.resolve(strict=True)
                except (RuntimeError,OSError) as error:raise ValueError('immutable symlink cycle/missing target') from error
                rows.append(('symlink',str(candidate),_stat_identity(candidate),os.readlink(candidate),str(target),_stat_identity(target)))
                links.add(candidate)
    def resolved(node):
        try:return node.resolve(strict=True)
        except (RuntimeError,OSError) as error:raise ValueError('immutable symlink cycle/missing target') from error
    def visit(node,ancestors):
        require(node.exists() or node.is_symlink(),'immutable referenced path missing')
        identity=_stat_identity(node);mode=identity[2]
        if stat.S_ISLNK(mode):
            record_links(node)
            target_literal=Path(os.readlink(node))
            if not target_literal.is_absolute():target_literal=node.parent/target_literal
            record_links(target_literal)
            return visit(resolved(node),ancestors)
        key=identity[:2]
        if stat.S_ISDIR(mode):
            require(key not in ancestors,'immutable directory symlink cycle')
            children=sorted(node.iterdir(),key=lambda p:p.name)
            rows.append(('directory',str(node),identity,tuple(p.name for p in children)))
            for child in children:visit(child,ancestors|{key})
        else:
            require(stat.S_ISREG(mode),'unsupported immutable referenced file kind')
            rows.append(('file',str(node),identity,common.file_hash(node)))
    require(path.exists() or path.is_symlink(),'immutable referenced path missing')
    record_links(path);visit(resolved(path),set())
    return tuple(rows)


class _FileWitness:
    def __init__(self,paths):
        self.pid=os.getpid();self.paths=tuple(str(Path(p).absolute()) for p in paths)
        self.identities=tuple(_file_tree_identity(p) for p in self.paths);self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('immutable file witnesses cannot be modified')
        object.__setattr__(self,name,value)
    def __reduce__(self):raise TypeError('file witnesses are process-local')


def _make_file_witness(paths):return _FileWitness(paths)


def _check_file_witness(witness):
    require(type(witness) is _FileWitness and witness.pid==os.getpid(),'file witness cannot cross a process/restart')
    require(tuple(_file_tree_identity(p) for p in witness.paths)==witness.identities,'immutable referenced file/tree fingerprint changed')


_FrozenJSONDict=workload._FrozenJSONDict
_FrozenJSONList=workload._FrozenJSONList
_freeze_json=workload._freeze_json


def _retained_json_bytes(value):
    import sys
    seen=set()
    def size(v):
        if id(v) in seen:return 0
        seen.add(id(v));n=sys.getsizeof(v)
        if isinstance(v,dict):n+=sum(size(k)+size(x) for k,x in v.items())
        elif isinstance(v,(list,tuple,set,frozenset)):n+=sum(size(x) for x in v)
        return n
    total=size(value)
    return total,len(seen)*72


class _AuthorityContext:
    """Unserializable proof cache minted only after the full root validator."""
    def __init__(self,seal,path,ledger,inventory,work_dir,subphase,limits,scope,reservation,upper,upper_keys,inventory_path,injected):
        require(seal is _AUTHORITY_SEAL,'authority context needs independent validation')
        original_bytes,walk_bytes=_retained_json_bytes(inventory)
        frozen=_freeze_json(inventory)
        for key,value in frozen.items():inventory[key]=value
        self._inventory_values={key:id(value) for key,value in inventory.items()}
        self._pid=os.getpid();self._inventory_id=id(inventory);self._keys_id=id(inventory['expected_keys']);self._key_count=len(inventory['expected_keys'])
        self._binding=workload.digest(dict(identity=inventory['identity'],inventory_sha256=inventory['inventory_sha256'],phase=inventory['phase'],
            finish_reserve_seconds=inventory['finish_reserve_seconds'],work_dir=str(Path(work_dir).resolve()),subphase=subphase,limits=limits,scope=scope,injected=injected))
        self._path=str(Path(path).resolve());self._reservation=copy.deepcopy(reservation);self._reservation_reference=object_reference(path)
        self._mapping_path=ledger['original_mapping_reference']['path'];self._upper_keys=upper_keys
        self._upper=dict(identity=copy.deepcopy(upper['identity']),inventory_sha256=upper['inventory_sha256'])
        roots=[path,reservation['admission_path'],reservation['upper_inventory_path'],self._mapping_path,ledger['original_snapshot_path']]
        roots.extend(a['path'] for a in ledger.get('mapping_lineage_references',[]))
        original_mapping=read_object(self._mapping_path)
        roots.extend(original_mapping['original_admission_paths'])
        if inventory_path is not None:
            require(workload.digest(read_object(inventory_path))==workload.digest(inventory),'authority inventory file bytes/content differ')
            roots.append(inventory_path)
        self._successor_directory=original_mapping.get('successor_directory')
        if self._successor_directory is not None:
            successor=Path(self._successor_directory).resolve()
            require(all(not Path(p).is_dir() or not successor.is_relative_to(Path(p).resolve()) for p in roots),'successor directory must be outside immutable bundles')
            self._successor_identity=_mutable_directory_identity(self._successor_directory)
        self._witness=_make_file_witness(roots)
        self.retained_bytes,_=_retained_json_bytes([upper_keys,self._reservation,self._upper,inventory])
        self.transient_bytes=self.retained_bytes+original_bytes+walk_bytes
        capacity=ledger.get('storage_capacities',{}).get('host_ram',{}).get('available_bytes')
        tiers=inventory.get('storage_requirements',{});floor=tiers.get('tiers',{}).get('host_ram',0)
        charged=tiers.get('components',{}).get('authority_key_proof_host_bytes',0)
        require(type(capacity) is int and capacity>=floor+max(0,self.transient_bytes-charged),'target host capacity must charge retained authority proof')
    def check(self,path,inventory,work_dir,subphase,limits,scope,keys,injected):
        require(self._pid==os.getpid(),'authority context cannot cross process/restart')
        require(set(inventory)==set(self._inventory_values) and all(id(inventory[k])==v for k,v in self._inventory_values.items()),
            'authority context immutable inventory values replaced')
        require(self._path==str(Path(path).resolve()) and self._inventory_id==id(inventory)
            and self._keys_id==id(inventory['expected_keys']) and self._key_count==len(inventory['expected_keys']),'authority context inventory/reference scope changed')
        binding=workload.digest(dict(identity=inventory['identity'],inventory_sha256=inventory['inventory_sha256'],phase=inventory['phase'],
            finish_reserve_seconds=inventory['finish_reserve_seconds'],work_dir=str(Path(work_dir).resolve()),subphase=subphase,limits=limits,scope=scope,injected=injected))
        require(binding==self._binding,'authority context requested source/admission scope changed')
        _check_file_witness(self._witness)
        if self._successor_directory is not None:require(_mutable_directory_identity(self._successor_directory)==self._successor_identity,'root successor directory identity changed')
        if keys is not None:require(all(workload.digest(k) in self._upper_keys for k in keys),'requested model keys exceed original authority proof')
    def __reduce__(self):raise TypeError('authority contexts are nonserializable and process-local')


def make_authority_context(path,*,ledger,inventory,work_dir,injected=False,subphase='directions',inventory_validator=None,
                           subphase_limits=None,requested_scope=None,inventory_path=None,allocation_reader=None):
    sink=[]
    validate_reservation(path,ledger=ledger,inventory=inventory,work_dir=work_dir,injected=injected,subphase=subphase,
        inventory_validator=inventory_validator,subphase_limits=subphase_limits,requested_scope=requested_scope,
        inventory_path=inventory_path,_context_sink=sink,allocation_reader=allocation_reader)
    return sink[0]


def _mutable_directory_identity(path):
    p=Path(path).absolute();require(p.is_dir() and not p.is_symlink(),'root successor directory must exist as an ordinary directory')
    st=p.stat();links=[]
    for ancestor in p.parents:
        if ancestor.is_symlink():links.append((str(ancestor),_stat_identity(ancestor),os.readlink(ancestor),str(ancestor.resolve())))
    return (str(p),st.st_dev,st.st_ino,st.st_mode,tuple(links))


def _mapping_old_entry(entry):
    return dict(reservation_id=entry['reservation_id'],experiment=entry['experiment'],phase=entry.get('phase'),
        subphase=entry.get('subphase'),inventory_sha256=entry.get('inventory_sha256'),original_reserved_gpu_hours=entry['original_reserved_gpu_hours'],
        reservation_lineage=entry.get('reservation_lineage'),actual_entry={k:entry['actual_entry'].get(k) for k in RESERVATION_FIELDS})


def _mapping_admission_references(mapping):
    expected=mapping.get('original_admission_references')
    actual={p:object_reference(p) for p in mapping['original_admission_paths']}
    if expected is not None:require(actual==expected,'root original admission file-byte anchor changed')
    return actual


def _mapping_chain(origin):
    current=read_object(origin);require(current.get('kind')=='a3_root_ledger_mapping_v1','completed root ledger mapping required')
    current_path=Path(origin);refs=[object_reference(origin)];base=current.get('generation',0);directory=current.get('successor_directory')
    if directory is None:return current,current_path,refs
    _mutable_directory_identity(directory);root=Path(directory).resolve()
    require(not root.is_relative_to(Path(origin).resolve()),'successor directory lies inside immutable original mapping')
    candidates=[]
    for child in root.iterdir():
        match=re.fullmatch(r'mapping-(\d{6})',child.name)
        if not match:continue
        generation=int(match.group(1))
        if generation<base:continue
        if generation==base:
            require(child.resolve()==current_path.resolve(),'forked root mapping generation');continue
        require(child.is_dir(),'root mapping successor must be a completed bundle')
        candidates.append((generation,child))
    for generation,path in sorted(candidates):
        successor=read_object(path)
        require(generation==current.get('generation',0)+1 and successor.get('generation')==generation,'skipped root mapping successor generation')
        require(successor.get('predecessor_reference')==object_reference(current_path),'changed/forked root mapping predecessor')
        require(successor.get('kind')=='a3_root_ledger_mapping_v1' and successor.get('ledger_path')==current['ledger_path']
            and successor.get('successor_directory')==directory,'changed root mapping lineage source/directory')
        old={e['reservation_id']:_mapping_old_entry(e) for e in current['entries']}
        new={e['reservation_id']:_mapping_old_entry(e) for e in successor['entries']}
        require(set(current['expected_entry_ids'])<=set(successor['expected_entry_ids']) and set(old)<=set(new)
            and all(old[k]==new[k] for k in old),'root mapping successor changed/omitted original reservation anchors or charges')
        old_refs=_mapping_admission_references(current);new_refs=_mapping_admission_references(successor)
        require(set(old_refs)<=set(new_refs) and all(old_refs[k]==new_refs[k] for k in old_refs),'root mapping successor changed/omitted original admissions')
        # Every original snapshot remains byte-bound, not merely the latest one.
        snapshot=current.get('ledger_snapshot_path',current['ledger_path'])
        require(common.file_hash(snapshot)==current['ledger_sha256'],'old root ledger snapshot bytes changed')
        current=successor;current_path=path;refs.append(object_reference(path))
    return current,current_path,refs


def _current_root_mapping(origin,*,injected,refresh_deadline):
    initial=read_object(origin);wait=initial.get('refresh_wait_seconds',0)
    require(type(wait) in (int,float) and math.isfinite(wait) and 0<=wait<=60,'root mapping refresh wait must be explicitly bounded')
    start=time.monotonic();deadline=time.time()+wait
    if refresh_deadline is not None:deadline=min(deadline,refresh_deadline)
    while True:
        mapping,path,refs=_mapping_chain(origin)
        live=artifacts._strict_json(mapping['ledger_path']);actual={r['id']:r for r in live['reservations']}
        expected=set(mapping['expected_entry_ids'])
        # Old immutable facts are checked before any wait for appended work.
        for entry in mapping['entries']:
            rid=entry['reservation_id']
            require(rid in actual and all(actual[rid].get(k)==entry['actual_entry'].get(k) for k in RESERVATION_FIELDS),
                'changed/omitted live original reservation anchor')
        if set(actual)==expected:return mapping,path,refs,time.monotonic()-start
        require(expected<=set(actual),'live RS omitted an original reservation')
        remaining=deadline-time.time()
        require(mapping.get('successor_directory') is not None and wait>0 and remaining>0,
            'unmapped new reservation requires completed current root successor')
        time.sleep(min(.1,remaining))


def _slurm_memory_bytes(value):
    match=re.fullmatch(r'(\d+)([KMGTPE]?)',str(value),re.I)
    require(match is not None,'finite allocated Slurm memory required')
    amount,unit=match.groups();power='KMGTPE'.index(unit.upper())+1 if unit else 2
    result=int(amount)*1024**power
    require(result>0,'positive allocated Slurm memory required')
    return result


def _node_gpu_types(output):
    """Physical homogeneous node GRES evidence for generic GPU allocations."""
    kinds=[];nodes=set()
    for line in output.splitlines():
        if not line.strip():continue
        fields=dict(re.findall(r'([A-Za-z][A-Za-z0-9_]*)=(\S+)',line))
        name=fields.get('NodeName');require(name and name not in nodes,'independent unique node facts required');nodes.add(name)
        typed=re.findall(r'(?:^|,)gpu:([^:,()]+):(\d+)(?=,|$|\()',fields.get('Gres',''))
        types={t.lower() for t,n in typed if int(n)>0}
        require(len(types)==1,'ambiguous/untyped physical node GPU GRES')
        kinds.append(next(iter(types)))
    require(kinds and len(set(kinds))==1,'heterogeneous/absent allocation node GPU types')
    return sorted(set(kinds))


def _parse_slurm_allocation(output,*,cluster):
    """Parse scontrol's current one-line scheduling facts under TZ=UTC."""
    from datetime import datetime,timezone
    fields=dict(re.findall(r'([A-Za-z][A-Za-z0-9_]*)=(\S+)',output))
    require(fields.get('JobState')=='RUNNING','Slurm allocation is not RUNNING')
    def epoch(key):
        value=fields.get(key,'')
        try:
            stamp=datetime.fromisoformat(value)
            return (stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp).timestamp()
        except ValueError as error:raise ValueError('invalid live Slurm '+key) from error
    value=fields.get('TimeLimit','');match=re.fullmatch(r'(?:(\d+)-)?(\d+):(\d+):(\d+)',value)
    require(match is not None,'finite current Slurm TimeLimit required')
    days,hours,minutes,seconds=match.groups();duration=(int(days or 0)*24+int(hours))*3600+int(minutes)*60+int(seconds)
    tres=fields.get('AllocTRES',fields.get('TRES',''))
    generic=re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)',tres)
    typed=re.findall(r'(?:^|,)gres/gpu:([^=,]+)=(\d+)',tres)
    gpus=int(generic.group(1)) if generic else sum(int(n) for _,n in typed)
    require(gpus>0,'current allocated GPU TRES required')
    cpus=next((x.split('=',1)[1] for x in tres.split(',') if x.startswith('cpu=')),None)
    require(cpus is not None and cpus.isdigit() and int(cpus)>0,'current allocated CPU TRES required')
    if 'NumCPUs' in fields:require(fields['NumCPUs'].isdigit() and int(fields['NumCPUs'])==int(cpus),'conflicting current CPU resource facts')
    ids=[fields.get('JobId','')]
    if fields.get('ArrayJobId'):
        ids.extend([fields['ArrayJobId'],fields['ArrayJobId']+'_'+fields.get('ArrayTaskId','')])
    return dict(job_id=fields.get('JobId'),job_ids=ids,cluster=cluster,account=fields.get('Account'),partition=fields.get('Partition'),
        state='RUNNING',gpus=gpus,gpu_types=[t.lower() for t,_ in typed],cpus=int(cpus),
        memory_bytes=_slurm_memory_bytes(next((x.split('=',1)[1] for x in tres.split(',') if x.startswith('mem=')),'')),
        scheduler_work_dir=fields.get('WorkDir'),node_list=fields.get('NodeList'),
        start_time_unix=epoch('StartTime'),end_time_unix=epoch('EndTime'),
        time_limit_seconds=duration,source='independent current scontrol allocation',raw_sha256=hashlib.sha256(output.encode()).hexdigest())


def read_current_allocation(reservation,*,injected,reader=None):
    """Never derive a live allocation lease from a submit-time deadline."""
    if injected:
        if reader is not None:allocation=reader(copy.deepcopy(reservation['actual_entry']))
        else:
            require(reservation.get('injected_allocation_path'),'injected execution requires an explicit allocation test adapter')
            allocation=read_object(reservation['injected_allocation_path'])
        require(allocation.get('kind')=='a3_injected_slurm_allocation_v1' and allocation.get('injected') is True,'explicit injected allocation adapter kind required')
        result=copy.deepcopy(allocation);result.setdefault('job_ids',[str(result['job_id'])]);return result
    require(reader is None and not reservation.get('injected_allocation_path'),'test allocation adapters forbidden for production')
    import subprocess
    job=os.environ.get('SLURM_JOB_ID','')
    require(re.fullmatch(r'\d+(?:_\d+)?',job) is not None,'real current Slurm allocation required')
    result=subprocess.run(['scontrol','-o','show','job',job],capture_output=True,text=True,check=True,timeout=15,env=dict(os.environ,TZ='UTC'))
    allocation=_parse_slurm_allocation(result.stdout,cluster=os.environ.get('DC_CLUSTER',os.environ.get('DC_CLUSTER_NAME','delta')))
    if not allocation['gpu_types']:
        nodes=allocation['node_list'];require(nodes and re.fullmatch(r'[A-Za-z0-9_,.\[\]\-]+',nodes),'current allocation NodeList required for generic GPU type')
        facts=subprocess.run(['scontrol','-o','show','node',nodes],capture_output=True,text=True,check=True,timeout=15,env=dict(os.environ,TZ='UTC'))
        allocation['gpu_types']=_node_gpu_types(facts.stdout)
        allocation['node_facts_sha256']=hashlib.sha256(facts.stdout.encode()).hexdigest()
    return allocation


def _allocation_requirements(inventory):
    """Source-owned selectors applied only after the owning inventory validator.

    Task4/M1 edge profiles and mask native profiles are single-H200 contracts;
    device expansion requires a new source/profile ruling and measurements.
    """
    kind=inventory.get('kind');numeric=inventory.get('identity',{}).get('numeric_profile',{})
    if kind=='a3_direction_inventory':hardware=inventory.get('hardware',{})
    elif kind=='a3_mask_inventory_v1':hardware=dict(gpu=numeric.get('hardware'),count=1)
    elif kind=='a3_edge_inventory_v2':
        require(numeric.get('hardware','H200').lower()=='h200','edge source profile requires canonical H200')
        hardware=dict(gpu='h200',count=1)
    else:raise ValueError('unknown independently validated allocation inventory kind')
    require(isinstance(hardware.get('gpu'),str) and hardware['gpu'].lower()=='h200','unsupported frozen GPU device label')
    require(type(hardware.get('count')) is int and hardware['count']==1,'accepted single-GPU inventory required')
    floor=inventory.get('storage_requirements',{}).get('tiers',{}).get('host_ram')
    require(type(floor) is int and floor>=0,'independently verified host capacity tier required')
    cpus=hardware.get('cpus',1);require(type(cpus) is int and cpus>0,'positive frozen CPU requirement needed')
    return dict(gpu_type='h200',gpus=1,host_ram=floor,cpus=cpus)


def validate_allocation_contract(contract,actual,inventory,*,injected):
    if injected and contract is None:return None
    require(isinstance(contract,dict) and contract.get('kind')=='a3_allocation_contract_v1','immutable root allocation contract required')
    checkout=Path(__file__).resolve().parents[1]
    require(isinstance(contract.get('scheduler_work_dir'),str) and Path(contract['scheduler_work_dir']).is_absolute()
        and Path(contract['scheduler_work_dir']).resolve()==checkout,'root allocation scheduler checkout differs from execution source')
    require(contract.get('source_commit')==inventory['identity']['commit'],'root allocation source commit differs')
    for key in ('cpus','memory_bytes','gpus'):
        require(type(contract.get(key)) is int and contract[key]>0,'positive frozen allocation '+key+' required')
    expected=_allocation_requirements(inventory)
    require(contract['gpus']==actual['gpus']==expected['gpus'],'root allocation GPU count differs from frozen resources')
    require(contract['cpus']>=expected['cpus'],'root allocation CPU count below frozen profile')
    require(isinstance(contract.get('gpu_type'),str) and contract['gpu_type'].lower()==expected['gpu_type'],
        'root allocation GPU type differs from frozen measured hardware')
    require(contract['memory_bytes']>=expected['host_ram'],'root allocation RAM below frozen inventory capacity tier')
    return contract


def validate_allocation(allocation,actual,inventory,work_dir,*,injected,allocation_contract=None):
    contract=validate_allocation_contract(allocation_contract,actual,inventory,injected=injected)
    if contract is not None:
        require(isinstance(allocation.get('scheduler_work_dir'),str) and Path(allocation['scheduler_work_dir']).is_absolute()
            and Path(allocation['scheduler_work_dir']).resolve()==Path(contract['scheduler_work_dir']).resolve(),'live allocation scheduler checkout mismatch')
        require(type(allocation.get('cpus')) is int and allocation['cpus']>=contract['cpus'],'live allocation CPU resources below frozen contract')
        require(type(allocation.get('memory_bytes')) is int and allocation['memory_bytes']>=contract['memory_bytes'],'live allocation RAM below frozen contract')
        require(allocation.get('gpu_types') and set(t.lower() for t in allocation['gpu_types'])=={contract['gpu_type'].lower()},
            'live allocation GPU type unavailable/differs from measured hardware')
        require(allocation.get('gpus')==contract['gpus'],'live allocation GPU count differs from root contract')
    require(allocation.get('state')=='RUNNING' and str(actual['job_id']) in allocation.get('job_ids',[]),'live allocation job/state differs from original reservation')
    require(allocation.get('cluster')==actual['cluster'] and allocation.get('account')==actual['account']
        and allocation.get('partition') in actual['partition'].split(','),'live allocation cluster/account/partition mismatch')
    require(type(allocation.get('gpus')) is int and 0<allocation['gpus']<=actual['gpus'],'live allocation GPU resources exceed original reservation')
    for key in ('start_time_unix','end_time_unix','time_limit_seconds'):
        require(type(allocation.get(key)) in (int,float) and math.isfinite(allocation[key]),'invalid live allocation '+key)
    start=allocation['start_time_unix'];end=allocation['end_time_unix'];limit=allocation['time_limit_seconds']
    require(0<limit<=actual['requested_minutes']*60 and 0<end-start<=limit+1 and start<=time.time()+5,
        'live allocation duration exceeds/conflicts with original requested limit')
    if 'hardware' in inventory:require(allocation['gpus']==inventory['hardware']['count'],'live allocation GPU count differs from frozen inventory')
    return allocation


def validate_model_metadata(config,settings):
    require(config.get('model_type')=='llama','direction runtime requires the frozen Llama architecture')
    heads=config.get('num_attention_heads');hidden=config.get('hidden_size')
    require(type(heads) is int and heads>0 and type(hidden) is int and hidden>0 and hidden%heads==0,'invalid local model head geometry')
    actual=dict(head_width=config.get('head_dim') or hidden//heads,hidden_size=hidden,num_layers=config.get('num_hidden_layers'),vocabulary_size=config.get('vocab_size'))
    require(all(settings.get(k)==v for k,v in actual.items()),'frozen execution geometry differs from local cached model config')
    maximum=config.get('max_position_embeddings')
    require(type(maximum) is int and maximum>0 and all(width<=maximum for splits in settings['widths'].values() for width in splits.values()),
        'frozen physical width exceeds cached model context')
    return actual


def _model_metadata_preflight(design,protocol):
    identity=protocol.get('model_config_identity')
    require(isinstance(identity,dict) and identity.get('model_revision')==design['a1_identity']['model_revision'],'frozen local model config identity required')
    path=Path(identity['path'])
    require(path.is_file() and common.file_hash(path)==identity['sha256'],'cached model config bytes changed')
    require(path.parent.name==identity['model_revision'] and str(path.parent.absolute())==identity['snapshot'],'cached model snapshot identity differs')
    validate_model_metadata(artifacts._strict_json(path),protocol['workload'])
    return identity


_RUNTIME_PACKAGES=None


def runtime_kernel_identity(model):
    """Actual kernel/library identity; this never substitutes for live authority."""
    global _RUNTIME_PACKAGES
    import platform,importlib.metadata
    from component_analysis import hooks
    if _RUNTIME_PACKAGES is None:
        versions={}
        for name in ('torch','transformers','nnsight'):
            try:versions[name]=importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:versions[name]='unavailable'
        _RUNTIME_PACKAGES=dict(python=platform.python_version(),packages=versions,cuda_build=torch.version.cuda)
    device,dtype=hooks.device_and_dtype(model);hardware=None
    if device.type=='cuda':
        props=torch.cuda.get_device_properties(device)
        hardware=dict(name=props.name,compute_capability=[props.major,props.minor],total_memory=props.total_memory)
    return dict(copy.deepcopy(_RUNTIME_PACKAGES),dtype=str(dtype),backend=hooks.attention_implementation(model),device_type=device.type,
        hardware=hardware,intraop_threads=torch.get_num_threads(),cuda_matmul_tf32=bool(torch.backends.cuda.matmul.allow_tf32),
        cudnn_tf32=bool(torch.backends.cudnn.allow_tf32))


ROOT_ADMISSION_KINDS=frozenset(('a3_root_fit_admission_v1','a3_root_remaining_admission_v1','a3_root_pilot_admission_v1',
    'a3_root_mask_admission_v1','a3_root_edge_admission_v1','a3_root_execution_admission_v1'))


def measure_positive_operations(model,call):
    """Actual three-forward positive-control clocks, with measured host overhead."""
    old=runner.ladder._capture;times=[];device=runner.hooks.device_and_dtype(model)[0]
    def capture(*a,**kw):
        if device.type=='cuda':torch.cuda.synchronize(device)
        start=time.perf_counter();out=old(*a,**kw)
        if device.type=='cuda':torch.cuda.synchronize(device)
        times.append(time.perf_counter()-start);return out
    start=time.perf_counter();runner.ladder._capture=capture
    try:result=call()
    finally:runner.ladder._capture=old
    total=time.perf_counter()-start;require(times and len(times)%3==0,'positive control did not execute complete three-forward passes')
    overhead=max(0,total-sum(times))/len(times)
    return result,[t+overhead for t in times]


def assessment_preflight(design,protocol,selected,inventory,*,root,reservation_path):
    """Root explicitly binds the complete validation power evidence before A."""
    root=Path(root);summary_path=root/'calibration-summary'
    summary=read_object(summary_path)
    require(summary.get('kind')=='a3_direction_conditional_power_summary_v1' and summary.get('complete') is True
        and summary.get('source_split')=='validation' and summary.get('assessment_outcomes_read') is False,
        'complete validation-only conditional power required before assessment')
    require(summary.get('injected') is design['injected'] and summary.get('inventory_sha256')==inventory['inventory_sha256']
        and summary.get('design_sha256')==workload.digest(design) and summary.get('protocol_sha256')==workload.digest(protocol)
        and summary.get('selected_reference')==object_reference(root/'selected'),'calibration summary source/selection bytes differ')
    for reference in summary['raw_row_references']:
        require(object_reference(reference['path'])==reference,'completed calibration source bytes changed')
    require(reservation_path,'root assessment reservation must reference reviewed calibration evidence')
    reservation=read_object(reservation_path)
    require(reservation.get('calibration_summary_reference')==object_reference(summary_path),
        'root assessment reservation lacks the exact complete calibration reference')
    return dict(calibration_summary_reference=object_reference(summary_path),continuation_authorized=False)


def validate_primary_interpretability(rows):
    """Failed scientific gates remain negatives; invalid denominators are blocked."""
    groups={}
    for row in rows:
        if row.get('family') not in ('learned','assessment_null','calibration_null'):continue
        if row.get('source_task')!='mmlu' and row.get('operation')!='interchange':continue
        if row.get('source_task')=='mmlu' and row.get('operation') not in ('zero','h_mean'):continue
        key=(row['panel'],row['analysis_task'],row['seed'],tuple(row['site']),row['family'],row['axis_index'])
        groups.setdefault(key,[]).append(row)
    require(groups,'complete primary denominator/control groups required')
    for key,values in groups.items():
        try:
            point=runner.direction_point_metrics(values,seed=key[2],require_mmlu=True)
            require(all(type(point.get(k)) in (int,float) and math.isfinite(point[k]) for k in ('D_fraction','I_fraction')),
                'nonfinite primary denominator/fraction')
        except (ValueError,KeyError) as error:
            raise ValueError('primary denominator/control scope invalid '+str(key)+': '+str(error)) from error
    return dict(complete=True,groups=len(groups))
