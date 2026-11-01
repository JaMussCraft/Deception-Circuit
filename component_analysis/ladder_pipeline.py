"""Immutable CPU prepare, selection-only CUDA select, assessment score and report.

No git, network access or outcome-based assessment filtering. JSON artifacts
carry content hashes; model weights are touched only after registry checks.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import re
import time

from component_analysis import ladder_design as design
from dataset import user_inversion_pipeline as common

REPO=Path(__file__).resolve().parents[1]
PRIMARY=Path('/projects/beto/swong2/Alignment/Deception-Circuit')
TASKS=('far_v2','sdr_v2','ser_v2')
REVISION='0e9e39f249a16976918f6564b8830bc894c89659'
GRADER='866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9'
OPERATIONS=('item_swap','zero','h_mean','h_twin','self_replay','empty','independent_resample')
require=common.require


def write_artifact(path,payload):
    path=Path(path)
    require(not path.exists(),'output exists: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as handle:
        json.dump(dict(sha256=design._hash(payload),payload=payload),handle,sort_keys=True,allow_nan=False)
        handle.write('\n')


def read_artifact(path):
    raw=common.read_json(path)
    require(raw.get('sha256')==design._hash(raw['payload']),'artifact hash mismatch: '+str(path))
    return raw['payload']


def selection_provenance(root):
    result={}; hashes={}
    for task in TASKS:
        path=Path(root)/'outputs/_analyses/mechanism-analysis-p1/s1/U__leaf'/task/'sample.json'
        require(path.is_file(),'missing selection sample provenance: '+str(path))
        raw=common.read_json(path); ids=raw.get('instance_ids')
        require(isinstance(ids,list) and ids and all(isinstance(i,str) and i for i in ids)
                and len(set(ids))==len(ids),'invalid selection instance_ids')
        result[task]=ids; hashes[str(path)]=common.file_hash(path)
    return result,hashes


def prompt_record(tokenizer,prompt,request=None):
    from dataset import build_user_inversion_v2 as pure
    pure._parts(prompt)
    encode=lambda text:list(map(int,tokenizer.encode(text,add_special_tokens=False)))
    tokens=encode(prompt)
    def boundary(char):
        prefix=encode(prompt[:char]); require(tokens[:len(prefix)]==prefix,'non-exact role/content token boundary')
        return len(prefix)
    roles=[]; contents=[]
    for role in ('system','user','assistant'):
        header='<|start_header_id|>'+role+'<|end_header_id|>\n\n'
        start=prompt.index(header); content=start+len(header)
        end=prompt.find('<|eot_id|>',content)
        if end<0: end=len(prompt)
        roles.append([role,boundary(start),boundary(end)])
        contents.append([role,boundary(content),boundary(end)])
    result=dict(prompt=prompt,tokens=tokens,readout=len(tokens)-1,
                layout=dict(role_spans=roles,content_spans=contents))
    if request:
        start=prompt.index(request); require(prompt.count(request)==1,'ambiguous request text')
        from dataset.matched_honest import clause_span
        result['user_request_span']=list(clause_span(tokenizer,prompt,request))
    return result


def normalize(row,canonical,condition,split,task,tokenizer,source_hash):
    from component_analysis.ladder_tasks import _context_token
    result={k:row.get(k) for k in ('instance_id','pressure_id','template_variant','designation_polarity','item_polarity','pressure_slot','item_pair','request_id')}
    result.update(condition=condition,source_condition=condition,split=split,task=task,source_hash=source_hash,streams={})
    for stream in design.STREAMS:
        opposite=canonical['target'] if stream=='clean' else canonical['distractor']
        honest=canonical['distractor'] if stream=='clean' else canonical['target']
        record=prompt_record(tokenizer,row[stream+'_prompt'],row.get('request_text'))
        if condition in ('I','user_neutral'):
            require(record['user_request_span']==row['request_spans'][stream],'builder request span mismatch')
            require(len(record['tokens'])==row['token_lengths'][stream] and record['readout']==row['readouts'][stream],'builder token/readout mismatch')
        record.update(opposite_word=opposite,honest_word=honest,honest_item=canonical[stream+'_item_d'],
                      opposite_token=_context_token(tokenizer,record['prompt'],opposite,record['tokens']),
                      honest_token=_context_token(tokenizer,record['prompt'],honest,record['tokens']))
        record['expected_token']=record['opposite_token'] if condition in ('D','I') else record['honest_token']
        result['streams'][stream]=record
    return result


def load_sources(args,tokenizer):
    from dataset import deception_common as dc
    from dataset import build_user_inversion_v2 as pure
    result={}; hashes={}
    for task in args.tasks:
        rows={c:[] for c in design.CONDITIONS}; canonical={}; original_h={}; source_hashes={}
        for condition,suffix,root in (('D','',args.data_root),('H','_honest',args.data_root),('F','_nopressure',args.data_root),('I','_user_inversion',args.user_control_root),('user_neutral','_user_neutral',args.user_control_root)):
            directory=Path(root)/(task+suffix)
            require(directory.is_dir(),'missing source dataset: '+str(directory))
            config=dc.load_dataset_config(str(directory))
            require(config.get('model')==args.model,'source model mismatch')
            if condition in ('D','H'): source_hashes[condition]={'config':pure._hash(config)}
            for path in sorted(directory.rglob('*')):
                if path.is_file(): hashes[str(path)]=common.file_hash(path)
            if condition in ('I','user_neutral'):
                assembly=common.read_json(directory/'assembly_provenance.json')
                require(assembly['source_hashes']==source_hashes,'stale original D/H assembly source hashes')
                for name,digest in assembly['files'].items():
                    require(common.file_hash(directory/name)==digest,'stale assembled control source')
                receipt=common.read_json(directory/'scoring_provenance.json')
                require(receipt['model_revision']==args.model_revision and receipt['tokenizer_revision']==args.tokenizer_revision,'control revision mismatch')
            for split in common.SPLITS:
                raw=list(dc.load_or_generate_deception_data(str(directory),split))
                digest=design._hash(raw)
                if condition in ('D','H'): source_hashes[condition][split]=pure._hash(raw)
                for row in raw:
                    rid=row['instance_id']
                    if condition=='D': canonical[rid]=(row,split)
                    require(rid in canonical and canonical[rid][1]==split,'missing/cross-split canonical D id')
                    d=canonical[rid][0]
                    if condition=='H':
                        pure._validate_source(d,row,task); original_h[rid]=row
                    if condition in ('I','user_neutral'):
                        require(row['source_row_hashes']==dict(D=pure._hash(d),H=pure._hash(original_h[rid])),'stale builder source row hashes')
                    rows[condition].append(normalize(row,d,condition,split,task,tokenizer,digest))
        # Reassert builder paired prompt/token request alignment, without model scores.
        for condition in ('I','user_neutral'):
            for row in rows[condition]: require(bool(row.get('request_id')),'missing request provenance')
        neutral={r['instance_id']:r for r in rows['user_neutral']}
        require(set(neutral)=={r['instance_id'] for r in rows['I']},'user-control twin id mismatch')
        for inv in rows['I']:
            twin=neutral[inv['instance_id']]
            require(inv['request_id']==twin['request_id'],'request id mismatch')
            for stream in design.STREAMS:
                left,right=inv['streams'][stream],twin['streams'][stream]
                require(left['layout']==right['layout'] and len(left['tokens'])==len(right['tokens']),'user-control twin token/layout mismatch')
                require(left['user_request_span']==right['user_request_span'],'user-control twin request span mismatch')
                a,b=left['user_request_span']
                require(left['tokens'][:a]==right['tokens'][:a] and left['tokens'][b:]==right['tokens'][b:],'user-control twin changes outside request')
        result[task]=rows
    return result,hashes


def registries(args,rows):
    contexts={task:dict(rows={'D':{s:[r for c in groups.values() for r in c if r['split']==s] for s in common.SPLITS}}) for task,groups in rows.items()}
    # Include utility source ids under their own tasks too.
    adapter=copy.copy(args); adapter.splits=list(common.SPLITS)
    return common.check_registry(adapter,contexts)


def utility_registries(args,utility):
    contexts={task:dict(rows={'D':{s:(values if s=='test' else []) for s in common.SPLITS}})
              for task,values in utility.items() if task in ('ioi','mmlu')}
    adapter=copy.copy(args); adapter.splits=list(common.SPLITS)
    return common.check_registry(adapter,contexts)


def grader_registry():
    from evaluation.grader_hash import grader_sha256
    require(grader_sha256(root=str(REPO))==GRADER,'changed grader source differs from frozen grader registry')
    result={}
    for root in (PRIMARY,REPO):
        path=root/'docs/research/directions.json'
        entry=next((r for r in common.read_json(path)['directions'] if r['id']=='specificity-ladder'),{})
        require(entry.get('frozen_grader_sha256')==GRADER,'missing/stale frozen grader registry')
        result[str(path)]=common.file_hash(path)
    return result


def code_hashes():
    paths=['component_analysis/'+name+'.py' for name in ('ladder_pipeline','ladder_design','ladder_tasks','ladder_metrics','specificity_ladder','hooks','dla','knockout')]
    paths+=['models/__init__.py','models/_compat.py','dataset/user_inversion_pipeline.py','dataset/build_user_inversion_v2.py','dataset/matched_honest.py','evaluation/benchmarks/sandbagging.py','evaluation/benchmarks/sources.py','evaluation/grader_hash.py']
    return {p:common.file_hash(REPO/p) for p in paths}


def validate_finalization(manifest,*,final):
    if final:
        require(not manifest.get('pilot'),'pilot cannot emit final verdict')
        require(not manifest.get('injected'),'injected fixtures cannot emit production final verdict')


def row_key(row):
    return tuple(row.get(k) for k in ('task','instance_id','condition','stream','group','operation','donor_seed'))


def validate_rows(rows,expected):
    keys=[row_key(r) for r in rows]
    require(len(keys)==len(set(keys)) and set(keys)==set(map(tuple,expected)),'incomplete/duplicate assessment rows')


def expected_keys(prepared,selected,limit=0):
    expected=[]
    for task in prepared['tasks']:
        g=selected['groups'][task]
        names=[task+'_full']+([] if g['duplicate_group'] else [task+'_minus'])
        ids=prepared['designs'][task]['assessment_ids'][:limit or None]
        for rid in ids:
            for condition in design.CONDITIONS:
                for stream in design.STREAMS:
                    for name in names:
                        for operation in OPERATIONS:
                            for seed in ([101,102,103] if operation=='independent_resample' else [None]):
                                expected.append((task,rid,condition,stream,name,operation,seed))
        for utility in ('ioi','mmlu'):
            operations=('item_swap','zero','h_mean','self_replay','empty') if utility=='ioi' else ('zero','h_mean','self_replay','empty')
            for row in prepared['utility'][utility][:limit or None]:
                for name in names:
                    for operation in operations:
                        expected.append((utility,row['instance_id'],row['condition'],'clean',name,operation,None))
    return expected


def positive_keys(prepared,limit=0):
    expected=[]
    for task in prepared['tasks']:
        for rid in prepared['designs'][task]['assessment_ids'][:limit or None]:
            for condition in design.CONDITIONS:
                for stream in design.STREAMS: expected.append((task,task,rid,condition,stream))
        for utility in ('ioi','mmlu'):
            for row in prepared['utility'][utility][:limit or None]:
                expected.append((task,utility,row['instance_id'],row['condition'],'clean'))
    return expected


def validate_positive_controls(controls,prepared,limit=0):
    keys=[tuple(c.get(k) for k in ('mechanism_task','task','instance_id','condition','stream')) for c in controls]
    require(len(keys)==len(set(keys)) and set(keys)==set(positive_keys(prepared,limit))
            and all(c.get('valid') for c in controls),'incomplete/duplicate/failed positive controls')


def calibrate(model,recipients,donors,maps,mechanism_task):
    from component_analysis import specificity_ladder as runner
    output=runner.positive_control(model,recipients,donor_batches=donors,donor_maps=maps)
    identities=[(b.task,rid,b.condition,b.stream) for b in recipients for rid in b.ids]
    require(len(output)==len(identities),'incomplete positive-control rows')
    result=[]
    for row,(task,rid,condition,stream) in zip(output,identities):
        require((row['task'],row['instance_id'],row['stream'])==(task,rid,stream),'reordered positive-control rows')
        result.append(dict(row,mechanism_task=mechanism_task,condition=condition))
    return result


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',required=True,choices=('prepare','select','score','summarize'))
    for name in ('artifact-root','data-root','user-control-root','work-dir','design','groups'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--tasks',nargs='+',choices=TASKS,required=True)
    p.add_argument('--model',default='meta-llama/Llama-3.1-8B-Instruct')
    p.add_argument('--model-revision',default=REVISION); p.add_argument('--tokenizer-revision',default=REVISION)
    p.add_argument('--commit',required=True); p.add_argument('--registry',action='append',default=[])
    p.add_argument('--dry-run',action='store_true'); p.add_argument('--limit',type=int,default=0)
    p.add_argument('--final',action='store_true'); p.add_argument('--batch-size',type=int,default=8)
    return p


def batches(rows,stream,*,batch_size=8,pad_token_id=0):
    from component_analysis.ladder_tasks import task_batches
    # task_batches expects row-level labels: stream labels must be explicit.
    adapted=[]
    for row in rows:
        s=row['streams'][stream]
        adapted.append(dict(row,expected_token=s['expected_token'],honest_token=s['honest_token'],opposite_token=s['opposite_token']))
    return task_batches(adapted,batch_size=batch_size,stream=stream,pad_token_id=pad_token_id)


def load_model(args):
    import torch
    require(bool(os.environ.get('SLURM_JOB_ID')) and torch.cuda.is_available(),'scoring requires Slurm CUDA allocation')
    from component_analysis.hooks import load_analysis_model
    snapshot=common.resolve_model_snapshot(args)
    return load_analysis_model(snapshot,device='cuda',dtype=torch.bfloat16)


def prepare(args,tokenizer):
    from component_analysis.ladder_tasks import ioi_rows,mmlu_rows,ioi_item_swap_maps,mmlu_calibration_maps
    rows,hashes=load_sources(args,tokenizer)
    selections,selection_hashes=selection_provenance(args.artifact_root)
    exclusion=set().union(*(set(ids) for ids in selections.values()))
    frozen={task:design.freeze_design(conditions,exclusion,mover_selection_ids=selections[task],n=100,seed=1) for task,conditions in rows.items()}
    readings=Path(args.artifact_root)/'docs/research/mechanism-analysis/phase1/p1c_readings.json'
    groups=design.recorded_groups(common.read_json(readings)); hashes[str(readings)]=common.file_hash(readings)
    ioi=ioi_rows(tokenizer,n=100,seed=1); mmlu,mmlu_manifest=mmlu_rows(tokenizer,n=32,seed=1)
    registry=registries(args,rows)
    registry.update(utility_registries(args,dict(ioi=ioi,mmlu=mmlu)))
    utility=dict(ioi=ioi,mmlu=mmlu,mmlu_manifest=mmlu_manifest,ioi_maps=ioi_item_swap_maps(ioi),mmlu_maps=mmlu_calibration_maps(mmlu))
    payload=dict(kind='prepared',tasks=args.tasks,rows=rows,designs=frozen,recorded_groups=groups,utility=utility,
                 source_hashes=hashes,selection_hashes=selection_hashes,registry_hashes=registry,
                 commit=args.commit,model=args.model,model_revision=args.model_revision,tokenizer_revision=args.tokenizer_revision,
                 grader_registry=grader_registry(),grader_sha256=GRADER,code_hashes=code_hashes(),
                 injected=args.injected,tokenizer_identity=common.tokenizer_identity(tokenizer,args.tokenizer_revision,injected=args.injected),
                 tokenizer_loading=common.tokenizer_loading(tokenizer),
                 seed=1,bootstrap_seed=1,n_boot=2000,independent_donor_seeds=[101,102,103],
                 readout='fp32 analysis readout; native diagnostics',dtype='bfloat16',operations=list(OPERATIONS))
    if not args.dry_run: write_artifact(args.design,payload)
    return payload


def validate_prepared(args,prepared):
    require(prepared['kind']=='prepared' and prepared['tasks']==args.tasks,'design scope mismatch')
    for key in ('model','model_revision','tokenizer_revision','commit'):
        require(prepared[key]==getattr(args,key),'stale design '+key)
    require(prepared['code_hashes']==code_hashes(),'stale design code/grader hash')
    for path,digest in dict(prepared['source_hashes'],**prepared['selection_hashes']).items():
        require(common.file_hash(path)==digest,'stale source/selection hash: '+path)
    grader_registry(); registries(args,prepared['rows']); utility_registries(args,prepared['utility'])
    for task in args.tasks:
        f=prepared['designs'][task]
        rebuilt=design.freeze_design(prepared['rows'][task],set(f['selection_exclusion_ids']),mover_selection_ids=f['mover_selection_ids'],n=100,seed=1)
        require(rebuilt==f,'stale design/bank/donor hash')


def validate_tokenization(prepared,tokenizer):
    for conditions in prepared['rows'].values():
        for records in conditions.values():
            for row in records:
                for stream in design.STREAMS:
                    saved=row['streams'][stream]
                    fresh=prompt_record(tokenizer,saved['prompt'])
                    require(fresh['tokens']==saved['tokens'] and fresh['layout']==saved['layout'],'stale source tokenization/layout')
    for task in ('ioi','mmlu'):
        for row in prepared['utility'][task]:
            for stream,saved in row['streams'].items():
                require(list(tokenizer.encode(saved['prompt'],add_special_tokens=task=='ioi'))==saved['tokens'],'stale utility tokenization')


def start_execution(model):
    """Reset per-stage GPU peaks only for the model's actual CUDA device."""
    import torch
    from component_analysis import hooks
    started=time.perf_counter()
    device,dtype=hooks.device_and_dtype(model)
    cuda_device=torch.device(device) if str(device).startswith('cuda') else None
    if cuda_device is not None:
        torch.cuda.synchronize(cuda_device)
        torch.cuda.reset_peak_memory_stats(cuda_device)
    return dict(device=device,dtype=dtype,cuda_device=cuda_device,started=started)


def finish_execution(state,stage):
    """Measure actual GPU resources, or explicit null GPU fields on CPU."""
    import torch
    cuda_device=state['cuda_device']
    if cuda_device is not None: torch.cuda.synchronize(cuda_device)
    return dict(device=str(state['device']),dtype=str(state['dtype']),
                gpu_name=torch.cuda.get_device_name(cuda_device) if cuda_device is not None else None,
                peak_allocated_memory_bytes=int(torch.cuda.max_memory_allocated(cuda_device)) if cuda_device is not None else None,
                peak_reserved_memory_bytes=int(torch.cuda.max_memory_reserved(cuda_device)) if cuda_device is not None else None,
                memory_scope=stage+' compute after model load; includes resident model',
                **{stage+'_compute_seconds':time.perf_counter()-state['started']},**selection_runtime_identity())


def timed_model_stage(args,model_loader,compute,stage):
    """Use the same model-load/compute timing boundary on selection and scoring."""
    started=time.perf_counter()
    model=model_loader(args)
    load_seconds=time.perf_counter()-started
    result=compute(model)
    result['execution_provenance'].update(model_load_seconds=load_seconds,
        stage_time_scope='model load plus '+stage+' compute; excludes artifact publication',
        **{stage+'_stage_seconds':time.perf_counter()-started})
    return result


def select(args,prepared,model):
    import torch
    from component_analysis import specificity_ladder as runner,dla
    execution_state=start_execution(model)
    groups={}; banks={}
    for task in args.tasks:
        frozen=prepared['designs'][task]; records=prepared['rows'][task]['H']
        indexed={r['instance_id']:r for r in records}
        selection=[indexed[rid] for rid in frozen['mover_selection_ids']]
        members=[tuple(k) for k in prepared['recorded_groups'][task[:-3]]['members']]
        heads=[k for k in members if k[0]=='head']; arrays=[]
        for stream in design.STREAMS:
            values=[]
            for b in batches(selection,stream,batch_size=args.batch_size):
                capture,_=runner._capture(model,b,heads)
                values.append(dla.component_logit_difference(model,capture,heads,target=b.honest_token,distractor=b.opposite_token).detach().cpu())
            arrays.append(torch.cat(values).numpy())
        screen=design.choose_mover_candidates(members,*arrays,frozen['mover_selection_ids'])
        evidence=dict(head_keys=[list(k) for k in heads],selection_ids=list(frozen['mover_selection_ids']),
                      clean_dla=arrays[0].tolist(),corrupt_dla=arrays[1].tolist(),
                      direction='original H correct-minus-other in each designation stream',axes=['ordered_selection_ids','head_keys'])
        groups[task]=dict(screen=screen,selection_evidence=evidence,full=[list(k) for k in members],minus=screen['remaining_keys'],
                          descriptive=task=='sdr_v2',duplicate_group=screen['duplicate_group'])
        bank_rows=[indexed[rid] for rid in frozen['bank_ids']]
        bank=runner.collect_h_mean_bank(model,[b for stream in design.STREAMS for b in batches(bank_rows,stream)],members)
        banks[task]=dict(values=[dict(key=list(k),value=v.detach().cpu().tolist()) for k,v in bank['values'].items()],provenance=bank['provenance'])
    execution=finish_execution(execution_state,'selection')
    execution.update(commit=args.commit,model=args.model,model_revision=args.model_revision,tokenizer_revision=args.tokenizer_revision)
    return dict(kind='selected',design_sha256=design._hash(prepared),groups=groups,banks=banks,
                execution_provenance=execution,
                bank_sha256=design._hash(banks),group_sha256=design._hash(groups),injected=args.injected or prepared.get('injected',False))


def selection_runtime_identity():
    """Read only allowlisted runtime labels; never dump the job environment."""
    job=os.environ.get('SLURM_JOB_ID','')
    job=job if re.fullmatch(r'[0-9]+(?:_[0-9]+)?',job) else None
    cluster=None; source=None
    for name in ('SLURM_CLUSTER_NAME','DC_CLUSTER_NAME','DC_CLUSTER'):
        value=os.environ.get(name,'')
        if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',value):
            cluster=value; source=name; break
    return dict(slurm_job_id=job,cluster=cluster,cluster_source=source)


def selection_manifest_path(groups_path):
    return Path(groups_path).with_name('selection_run_manifest.json')


def selection_manifest_core(args,prepared,selected):
    """One schema shared by the final completion marker and its consumers."""
    return dict(schema_version=1,kind='specificity_ladder_selection',commit=args.commit,model=args.model,
                  model_revision=args.model_revision,tokenizer_revision=args.tokenizer_revision,
                  design_sha256=selected['design_sha256'],group_sha256=selected['group_sha256'],bank_sha256=selected['bank_sha256'],
                  raw_dla_sha256=design._hash({task:group['selection_evidence'] for task,group in selected['groups'].items()}),
                  source_hashes=prepared['source_hashes'],selection_source_hashes=prepared['selection_hashes'],
                  code_hashes=code_hashes(),execution=selected['execution_provenance'],injected=selected['injected'],
                  counts={task:dict(selection_rows=len(group['selection_evidence']['selection_ids']),
                                    head_columns=len(group['selection_evidence']['head_keys']),
                                    bank_instances=len(selected['banks'].get(task,{}).get('provenance',{}).get('source_ids',[])))
                          for task,group in selected['groups'].items()})


def write_selection(args,prepared,selected):
    """Publish raw selection evidence and a sidecar linked to exact file bytes."""
    target=Path(args.groups); manifest_path=selection_manifest_path(target)
    require(not target.exists(),'output exists: '+str(target))
    require(not manifest_path.exists(),'output exists: '+str(manifest_path))
    manifest=selection_manifest_core(args,prepared,selected)
    write_artifact(target,selected)
    manifest.update(selection_artifact=str(target.resolve()),selection_artifact_sha256=design._hash(selected),
                    selection_file_sha256=common.file_hash(target))
    with manifest_path.open('x') as handle:
        json.dump(manifest,handle,sort_keys=True,indent=2,allow_nan=False)
        handle.write('\n')


def read_selection(args,prepared):
    """Require the last-written completion marker before scoring or summaries."""
    path=selection_manifest_path(args.groups)
    require(path.is_file(),'missing selection completion manifest: '+str(path))
    try:
        manifest=common.read_json(path)
    except (ValueError,OSError) as exc:
        raise ValueError('malformed selection completion manifest: '+str(path)) from exc
    require(isinstance(manifest,dict) and type(manifest.get('schema_version')) is int
            and manifest.get('schema_version')==1 and manifest.get('kind')=='specificity_ladder_selection',
            'invalid selection completion manifest schema')
    try:
        selected=read_artifact(args.groups)
        require(selected['kind']=='selected','invalid selection artifact kind')
        require(selected['design_sha256']==design._hash(prepared),'stale selection design hash')
        require(selected['bank_sha256']==design._hash(selected['banks']),'stale selection bank hash')
        require(selected['group_sha256']==design._hash(selected['groups']),'stale selection group hash')
        require(set(selected['groups'])==set(args.tasks)==set(selected['banks']),'incomplete selection task scope')
        require(type(selected['injected']) is bool and (not prepared.get('injected') or selected['injected']),
                'invalid selection injected provenance')
        execution=selected['execution_provenance']
        require(isinstance(execution,dict) and isinstance(execution.get('device'),str) and isinstance(execution.get('dtype'),str),
                'incomplete selection execution provenance')
        for field in ('commit','model','model_revision','tokenizer_revision'):
            require(prepared[field]==getattr(args,field)==execution[field],'stale selection identity: '+field)
        require(prepared['code_hashes']==code_hashes(),'stale selection code identity')
        for task,group in selected['groups'].items():
            evidence=group['selection_evidence']; frozen=prepared['designs'][task]
            require(group['full']==prepared['recorded_groups'][task[:-3]]['members'],'stale selection recorded group')
            require(evidence['selection_ids']==frozen['mover_selection_ids'],'stale selection ordered ids')
            require(evidence['head_keys']==[key for key in group['full'] if key[0]=='head'],'stale selection head-key order')
            for stream in ('clean_dla','corrupt_dla'):
                values=evidence[stream]
                require(isinstance(values,list) and len(values)==len(evidence['selection_ids'])
                        and all(isinstance(row,list) and len(row)==len(evidence['head_keys']) for row in values),
                        'incomplete selection raw DLA axes')
            require(selected['banks'][task]['provenance']['source_ids']==frozen['bank_ids'],'stale selection bank ids')
        expected=selection_manifest_core(args,prepared,selected)
        expected.update(selection_artifact=str(Path(args.groups).resolve()),selection_artifact_sha256=design._hash(selected),
                        selection_file_sha256=common.file_hash(args.groups))
        require(set(manifest)==set(expected),'incomplete selection completion manifest fields')
        for field,value in expected.items():
            require(design._hash(manifest[field])==design._hash(value),'stale selection completion manifest link: '+field)
    except (KeyError,TypeError,ValueError,OSError) as exc:
        raise ValueError('invalid selection completion evidence: '+str(exc)) from exc
    return selected


def resolve_bank_reference(reference,selected=None):
    """Resolve one row's bank reference through its immutable selected artifact."""
    if selected is None: selected=read_artifact(reference['artifact_reference'])
    require(reference['bank_artifact_sha256']==design._hash(selected),'stale bank artifact reference hash')
    task=reference['task']; require(task in selected['banks'],'unknown referenced bank task')
    bank=selected['banks'][task]; provenance=bank['provenance']
    require(reference['bank_sha256']==design._hash(bank),'stale bank reference hash')
    require(reference['source_ids']==provenance['source_ids'] and
            reference['source_condition']==provenance['source_condition'] and
            reference['splits']==provenance['splits'] and
            reference['n_instances']==len(provenance['source_ids']) and
            reference['n_tokens']==provenance['n_tokens'],'stale bank reference source/counts')
    return provenance


def compact_bank_provenance(rows,selected,artifact_reference):
    """Store full canonical bank provenance once, with checked row references."""
    references={}
    for task,bank in selected['banks'].items():
        p=bank['provenance']
        references[task]=dict(bank_artifact_sha256=design._hash(selected),bank_sha256=design._hash(bank),
                              task=task,artifact_reference=str(artifact_reference),source_condition=p['source_condition'],
                              source_ids=p['source_ids'],splits=p['splits'],n_instances=len(p['source_ids']),n_tokens=p['n_tokens'])
    owners={task+suffix:task for task in selected['groups'] for suffix in ('_full','_minus')}
    checked=set()
    for row in rows:
        if 'mean_bank_provenance' not in row: continue
        require(row['group'] in owners,'unknown mean-bank row group')
        task=owners[row['group']]; reference=references[task]
        key=(task,id(row['mean_bank_provenance']))
        if key not in checked:
            require(design._hash(row['mean_bank_provenance'])==design._hash(resolve_bank_reference(reference,selected)),
                    'row mean-bank provenance differs from selected artifact')
            checked.add(key)
        row['mean_bank_provenance']=reference
    return rows


def score(args,prepared,selected,model):
    import torch
    from component_analysis import specificity_ladder as runner
    from component_analysis.ladder_tasks import task_batches
    execution_state=start_execution(model)
    results=[]; controls=[]; expected=[]
    for task in args.tasks:
        frozen=prepared['designs'][task]; ids=frozen['assessment_ids'][:args.limit or None]
        source=prepared['rows'][task]; g=selected['groups'][task]
        groups=[(task+'_full',g['full'])]
        if not g['duplicate_group']: groups.append((task+'_minus',g['minus']))
        bank=selected['banks'][task]; bank=dict(values={tuple(v['key']):torch.tensor(v['value'],dtype=torch.float32) for v in bank['values']},provenance=bank['provenance'])
        recipients=[b for c in design.CONDITIONS for stream in design.STREAMS for b in batches([r for r in source[c] if r['instance_id'] in ids],stream,batch_size=args.batch_size)]
        all_batches=[b for c in design.CONDITIONS for stream in design.STREAMS for b in batches(source[c],stream,batch_size=args.batch_size)]
        maps=[m for m in frozen['donors'] if m['recipient_id'] in ids]
        positive=[]
        for m in maps:
            if m['operation']!='item_swap': continue
            r=next(r for r in source[m['recipient_condition']] if r['instance_id']==m['recipient_id'])
            donor=r['streams'][m['donor_stream']]
            positive.append(dict(m,supported=True,recipient_positions=[r['streams'][m['recipient_stream']]['readout']],donor_positions=[donor['readout']]))
        controls.extend(calibrate(model,recipients,all_batches,positive,task))
        for operation in OPERATIONS:
            for seed in ([101,102,103] if operation=='independent_resample' else [None]):
                subset=[m for m in maps if m['operation']==operation and (seed is None or m['seed']==seed)]
                for b in recipients:
                    for name,_ in groups:
                        for rid in b.ids: expected.append((task,rid,b.condition,b.stream,name,operation,seed))
                results.extend(runner.score_cell(model,recipients,groups=groups,operation=operation,donor_batches=all_batches,mean_bank=bank,donor_maps=subset))
        for utility in ('ioi','mmlu'):
            rows=prepared['utility'][utility][:args.limit or None]
            ub=task_batches(rows,batch_size=args.batch_size)
            maps=prepared['utility'][utility+'_maps']
            maps=[m for m in maps if m['recipient_id'] in {r['instance_id'] for r in rows}]
            if utility=='ioi':
                db=task_batches(prepared['utility']['ioi'],stream='corrupt')
                calibration=[]
                lookup={r['instance_id']:r for r in rows}
                for m in maps:
                    r=lookup[m['recipient_id']]
                    calibration.append(dict(m,recipient_positions=[r['streams']['clean']['readout']],donor_positions=[r['streams']['corrupt']['readout']],supported=True))
            else:
                db=task_batches(prepared['utility']['mmlu']); calibration=maps
            controls.extend(calibrate(model,ub,db,calibration,task))
            for operation in (('item_swap','zero','h_mean','self_replay','empty') if utility=='ioi' else ('zero','h_mean','self_replay','empty')):
                for r in rows:
                    for name,_ in groups: expected.append((utility,r['instance_id'],r['condition'],'clean',name,operation,None))
                results.extend(runner.score_cell(model,ub,groups=groups,operation=operation,donor_batches=db,donor_maps=maps,mean_bank=bank))
    require(set(expected)==set(expected_keys(prepared,selected,args.limit)),'internal assessment scope mismatch')
    validate_rows(results,expected_keys(prepared,selected,args.limit))
    validate_positive_controls(controls,prepared,args.limit)
    compact_bank_provenance(results,selected,getattr(args,'groups','injected-selected-artifact'))
    return dict(kind='scored',execution_provenance=finish_execution(execution_state,'scoring'),pilot=bool(args.limit),injected=args.injected or selected.get('injected',False),limit=args.limit,
                design_sha256=design._hash(prepared),selection_sha256=design._hash(selected),rows=results,expected=[list(k) for k in expected],positive_controls=controls,
                counts=dict(rows=len(results),expected=len(expected),positive_controls=len(controls)),
                not_applicable=dict(mmlu=['item_swap','h_twin','independent_resample'],ioi=['h_twin']),
                optional_robustness='mechanism independent seeds 101/102/103; IOI task_resample not requested')


def qualify_summary(summary,selected):
    """Retain prospective source-set qualifications alongside local estimates."""
    summary=copy.deepcopy(summary)
    for cell in summary.get('cells',[]):
        source=selected['groups'][cell['task']]
        descriptive=source['descriptive']
        cell['descriptive']=descriptive
        cell['source_group_provenance']=dict(task=cell['task'],full=source['full'],
                                             minus=source['minus'],duplicate_group=source['duplicate_group'])
        if descriptive:
            cell['numerical_status']=cell.get('status')
            cell['numerical_strong']=cell.get('strong')
            cell['status']='descriptive_only'
            cell['strong']=False
            cell['interpretation']='Recorded SDR source set is descriptive; local numerical gates are not validated specificity evidence.'
    return summary


def main(argv=None,tokenizer=None,model_loader=None):
    args=parser().parse_args(argv); args.injected=tokenizer is not None or model_loader is not None
    require(re.fullmatch('[0-9a-f]{40}',args.commit) is not None,'full 40-hex --commit required')
    require(args.limit>=0 and args.batch_size>0,'invalid limit/batch size')
    require(len(set(args.tasks))==len(args.tasks),'duplicate tasks')
    require(Path(args.design).resolve()!=Path(args.groups).resolve(),'design/groups must be distinct')
    if not args.dry_run and args.stage in ('prepare','select','score'):
        output=Path(args.design) if args.stage=='prepare' else (Path(args.groups) if args.stage=='select' else Path(args.work_dir)/'score')
        require(not output.exists(),'output exists: '+str(output))
        if args.stage=='select': require(not selection_manifest_path(args.groups).exists(),'output exists: '+str(selection_manifest_path(args.groups)))
    require(not args.final or args.stage=='summarize','--final requires summarize')
    require(not args.limit or args.stage in ('score','summarize'),'--limit is scoring pilot only')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    if args.stage=='prepare':
        tokenizer=tokenizer or common.load_tokenizer(args)
        prepare(args,tokenizer)
    else:
        prepared=read_artifact(args.design); validate_prepared(args,prepared)
        if args.stage in ('score','summarize'): selected=read_selection(args,prepared)
        if args.dry_run:
            tokenizer=tokenizer or common.load_tokenizer(args)
            validate_tokenization(prepared,tokenizer)
        if args.stage=='select':
            if not args.dry_run:
                registries(args,prepared['rows']); utility_registries(args,prepared['utility']); grader_registry()
                selected=timed_model_stage(args,model_loader or load_model,lambda model:select(args,prepared,model),'selection')
                write_selection(args,prepared,selected)
        else:
            if args.stage=='score':
                if not args.dry_run:
                    registries(args,prepared['rows']); utility_registries(args,prepared['utility']); grader_registry()
                    scored=timed_model_stage(args,model_loader or load_model,lambda model:score(args,prepared,selected,model),'scoring')
                    scored['run_manifest']=dict(commit=args.commit,model=args.model,model_revision=args.model_revision,tokenizer_revision=args.tokenizer_revision,
                        code_hashes=code_hashes(),grader_registry=grader_registry(),grader_sha256=GRADER,registry=registries(args,prepared['rows']),
                        design_sha256=design._hash(prepared),selection_sha256=design._hash(selected),group_sha256=selected['group_sha256'],bank_sha256=selected['bank_sha256'],
                        domain_hashes={task:frozen['hashes'] for task,frozen in prepared['designs'].items()},
                        source_hashes=prepared['source_hashes'],selection_source_hashes=prepared['selection_hashes'],
                        tokenizer_identity=prepared['tokenizer_identity'],tokenizer_loading=prepared['tokenizer_loading'],
                        utility_sample_hashes={task:design._hash(prepared['utility'][task]) for task in ('ioi','mmlu')},
                        seeds=dict(sample=1,bootstrap=1,independent_donors=[101,102,103]),operations=list(OPERATIONS),mapping='frozen explicit absolute unpadded index maps; unsupported cells retained',
                        counts=scored['counts'],execution=scored['execution_provenance'],dtype=scored['execution_provenance']['dtype'],readout=prepared['readout'])
                    common.publish(Path(args.work_dir)/'score',lambda root: (write_artifact(root/'score.json',scored),common.write_json(root/'run_manifest.json',scored['run_manifest'])))
            else:
                scored=read_artifact(Path(args.work_dir)/'score'/'score.json')
                require(scored['design_sha256']==design._hash(prepared) and scored['selection_sha256']==design._hash(selected),'stale scored design/bank/donor hashes')
                require(scored['expected']==[list(k) for k in expected_keys(prepared,selected,scored['limit'])] or set(map(tuple,scored['expected']))==set(expected_keys(prepared,selected,scored['limit'])),'incomplete frozen expected scope')
                validate_rows(scored['rows'],expected_keys(prepared,selected,scored['limit'])); validate_positive_controls(scored['positive_controls'],prepared,scored['limit']); validate_finalization(scored,final=args.final)
                if args.final:
                    require(all(len(f['assessment_ids'])==100 for f in prepared['designs'].values()),'final requires 100 mechanism ids')
                    require(len(prepared['utility']['ioi'])==100 and len(prepared['utility']['mmlu'])==32,'final requires IOI100/MMLU32')
                    require(scored['positive_controls'] and all(c['valid'] for c in scored['positive_controls']),'final requires positive controls')
                if not args.dry_run:
                    from component_analysis.ladder_metrics import summarize_ladder
                    summary=qualify_summary(summarize_ladder(scored['rows']),selected) if not scored['pilot'] else dict(status='pilot diagnostics only; no final gate verdict',counts=scored['counts'])
                    if args.final:
                        require(summary.get('cells') and all(c.get('complete_assay_ready',False) for c in summary['cells'] if c.get('operation')=='item_swap'),'incomplete assay cannot finalize')
                    write_artifact(Path(args.work_dir)/'summary.json',dict(summary=summary,final=args.final,score_sha256=design._hash(scored)))
    print(args.stage+(': validated dry-run; no model or writes' if args.dry_run else ': complete'))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
