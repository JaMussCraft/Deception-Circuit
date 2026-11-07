#!/usr/bin/env python
"""Read-only independent artifact audit and exact singleton capture-shape census.

No model/tokenizer construction, CUDA, git, or scheduler operations. The census
uses actual batch/map helpers and mirrors score_cell's unsupported-row branch.
Outputs JSON to stdout only; run from the owning worktree.
"""
import collections
import json
import math
from argparse import Namespace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from component_analysis import ladder_pipeline as p, specificity_ladder as r
from component_analysis.ladder_tasks import task_batches

BASE = ROOT/'outputs/_analyses/specificity-ladder'
OLD = BASE/'ladder-0253f49'
NEW = BASE/'ladder-5f450dc'
COMMIT = '5f450dc93dac707af649dee8c8ca60888b2831db'


def main():
    prepared=p.read_artifact(NEW/'design.json')
    old=p.read_artifact(OLD/'design.json')
    old_selected=p.read_artifact(OLD/'selected.json')
    original_args=json.loads((BASE/'calibration-diagnostic-0253f49/run_manifest.json').read_text())['argv']
    args=Namespace(**dict(original_args,commit=COMMIT,design=str(NEW/'design.json'),
                          groups=str(NEW/'selected.json'),work_dir=str(NEW/'pilot-4'),injected=False))
    p.validate_prepared(args,prepared)
    selected=p.read_selection(args,prepared)
    scored=p.read_artifact(NEW/'pilot-4/score/score.json')
    manifest=json.loads((NEW/'pilot-4/score/run_manifest.json').read_text())
    assert manifest==scored['run_manifest']
    assert manifest['commit']==prepared['commit']==COMMIT
    for key in ('model','model_revision','tokenizer_revision','grader_sha256','readout','code_hashes','source_hashes','tokenizer_identity','tokenizer_loading'):
        assert manifest[key]==prepared[key],key
    assert manifest['code_hashes']==p.code_hashes()
    assert manifest['grader_registry']==p.grader_registry()
    assert manifest['registry']==p.registries(args,prepared['rows'])
    assert prepared['registry_hashes']==dict(p.registries(args,prepared['rows']),**p.utility_registries(args,prepared['utility']))
    assert manifest['selection_source_hashes']==prepared['selection_hashes']
    assert manifest['design_sha256']==scored['design_sha256']==p.design._hash(prepared)
    assert manifest['selection_sha256']==scored['selection_sha256']==p.design._hash(selected)
    assert manifest['bank_sha256']==selected['bank_sha256']
    assert manifest['group_sha256']==selected['group_sha256']
    assert manifest['domain_hashes']=={task:f['hashes'] for task,f in prepared['designs'].items()}
    assert manifest['utility_sample_hashes']=={task:p.design._hash(prepared['utility'][task]) for task in ('ioi','mmlu')}
    assert manifest['execution']==scored['execution_provenance']
    assert manifest['seeds']==dict(sample=1,bootstrap=1,independent_donors=[101,102,103])
    assert manifest['operations']==list(p.OPERATIONS)
    assert scored['pilot'] is True and scored['limit']==4 and scored['injected'] is False
    assert manifest['execution']['slurm_job_id']=='23417413'
    assert manifest['execution']['cluster']=='delta'
    assert manifest['dtype']==manifest['execution']['dtype']=='torch.bfloat16'
    p.validate_rows(scored['rows'],p.expected_keys(prepared,selected,4))
    assert set(map(tuple,scored['expected']))==set(p.expected_keys(prepared,selected,4))
    assert len(scored['expected'])==len(set(map(tuple,scored['expected'])))
    p.validate_positive_controls(scored['positive_controls'],prepared,4)
    assert scored['counts']==manifest['counts']==dict(rows=len(scored['rows']),expected=len(scored['expected']),positive_controls=len(scored['positive_controls']))
    for row in scored['rows']:
        assert row['assay_valid'] and row['self_replay_margin_error']==0
        if 'mean_bank_provenance' in row:p.resolve_bank_reference(row['mean_bank_provenance'],selected)
        for key,value in row.items():
            if isinstance(value,float):assert math.isfinite(value),(p.row_key(row),key)
    all_keys=[['embed',0,0]]
    for layer in range(32):
        all_keys.extend([['head',layer,head] for head in range(32)])
        all_keys.append(['mlp',layer,0])
    for control in scored['positive_controls']:
        assert control['valid'] and control['max_abs_logit_error']==0
        assert control['sender_keys']==all_keys
    try:p.validate_finalization(scored,final=True)
    except ValueError as exc:assert str(exc)=='pilot cannot emit final verdict'
    else:raise AssertionError('pilot finalized')
    recipients={}
    for task in prepared['tasks']:
        ids=prepared['designs'][task]['assessment_ids'][:4]
        for condition in p.design.CONDITIONS:
            for stream in p.design.STREAMS:
                batches=p.batches([x for x in prepared['rows'][task][condition] if x['instance_id'] in ids],stream,batch_size=8)
                for batch in batches:
                    for one in r._rows(batch):recipients[(task,one.ids[0],condition,stream)]=one
    for task in ('ioi','mmlu'):
        for batch in task_batches(prepared['utility'][task][:4],batch_size=8):
            for one in r._rows(batch):recipients[(task,one.ids[0],one.condition,one.stream)]=one
    for row in scored['rows']:
        batch=recipients[tuple(row[k] for k in ('task','instance_id','condition','stream'))]
        assert row['source_provenance']==batch.records[0]
        for label in ('honest_token','opposite_token','expected_token'):assert row[label]==int(getattr(batch,label)[0])
        owner=next(task for task in prepared['tasks'] if row['group'].startswith(task+'_'))
        assert row['group_members']==selected['groups'][owner]['minus' if row['group'].endswith('_minus') else 'full']
        if row['operation'] in ('item_swap','h_twin','independent_resample'):
            maps=prepared['designs'][row['task']]['donors'] if row['task'] in prepared['tasks'] else prepared['utility'][row['task']+'_maps']
            matching=[m for m in maps if all(m[k]==v for k,v in [('recipient_id',row['instance_id']),('recipient_condition',row['condition']),('recipient_stream',row['stream']),('operation',row['operation'])]) and (row['donor_seed'] is None or m['seed']==row['donor_seed'])]
            assert len(matching)==1
            for key,value in matching[0].items():
                if key not in ('degenerate','gate_valid','no_op'):assert row['donor_provenance'][key]==value
            assert row['supported']==matching[0]['supported']
    changed_design=sorted(k for k in prepared if prepared[k]!=old[k])
    assert changed_design==['code_hashes','commit','grader_registry']
    assert sorted(k for k in old['code_hashes'] if old['code_hashes'][k]!=prepared['code_hashes'][k])==['component_analysis/specificity_ladder.py']
    assert selected['groups']==old_selected['groups'] and selected['banks']==old_selected['banks']
    changed_selection=sorted(k for k in selected if selected[k]!=old_selected[k])
    assert changed_selection==['design_sha256','execution_provenance']
    receipt=json.loads((NEW/'design-semantic-equivalence.json').read_text())
    assert receipt['old_file_sha256']==p.common.file_hash(OLD/'design.json')
    assert receipt['new_file_sha256']==p.common.file_hash(NEW/'design.json')
    receipt2=json.loads((NEW/'selection-semantic-equivalence.json').read_text())
    assert receipt2['old_selection_sha256']==p.common.file_hash(OLD/'selected.json')
    assert receipt2['new_selection_sha256']==p.common.file_hash(NEW/'selected.json')
    # Current worktree retains the old registry; primary changed instructed-route only.
    registries=[json.loads((root/'docs/research/directions.json').read_text()) for root in (ROOT,p.PRIMARY)]
    changed_directions=[]
    for left,right in zip(registries[0]['directions'],registries[1]['directions']):
        if left!=right:
            assert left['id']==right['id']=='instructed-route'
            changed_directions.append(dict(direction=left['id'],fields=[k for k in left if left[k]!=right[k]],old_status=left['status'],new_status=right['status']))
    assert len(changed_directions)==1
    failed=[c for c in scored['positive_controls'] if (c['mechanism_task'],c['task'],c['condition'],c['instance_id'],c['stream'])==('ser_v2','ser_v2','I','00b809b51070','clean')]
    assert len(failed)==1 and failed[0]['valid'] and failed[0]['max_abs_logit_error']==0

    def inventory(limit):
        captures=[];scope=collections.Counter();geo={}
        def emit(owner,task,kind,batch,width=None):
            width=int(batch.input_ids.shape[1]) if width is None else width
            captures.append(dict(owner=owner,task=task,kind=kind,width=width,
                                 used=int(batch.attention_mask.sum()),id=batch.ids[0],condition=batch.condition,stream=batch.stream))
        def rows(bs):return [one for b in bs for one in r._rows(b)]
        def calibration(owner,recipients,donors,maps):
            ds={(b.condition,b.ids[0],b.stream):b for b in rows(donors)}
            ms={(m['recipient_condition'],m['recipient_id'],m['recipient_stream']):m for m in maps}
            for b in rows(recipients):
                m=ms[(b.condition,b.ids[0],b.stream)];d=ds[(m['donor_condition'],m['donor_id'],m['donor_stream'])]
                assert m['supported']
                w=max(b.input_ids.shape[1],d.input_ids.shape[1])
                emit(owner,b.task,'calibration_intact',b,w);emit(owner,b.task,'calibration_donor',d,w);emit(owner,b.task,'calibration_patch',b,w)
        def cells(owner,recipients,donors,maps,groups,operation,seed=None):
            ds={(b.condition,b.ids[0],b.stream):b for b in rows(donors)}
            ms=r._map_index([m for m in maps if seed is None or m.get('seed')==seed],operation)
            for b in rows(recipients):
                m=ms.get((b.condition,b.ids[0],b.stream));d=None
                supported=True if m is None else m['supported']
                if operation not in ('zero','h_mean','self_replay','empty'):
                    assert m is not None
                    if supported:
                        d=ds[(m['donor_condition'],m['donor_id'],m['donor_stream'])]
                        r._check_map(b,d,m,operation)
                emit(owner,b.task,'intact',b)
                if d is not None:emit(owner,b.task,'donor',d)
                for name,group in groups:
                    emit(owner,b.task,'empty',b);emit(owner,b.task,'self_replay',b)
                    if supported:emit(owner,b.task,'patch',b)
                    scope[(b.task,name,operation,seed)]+=1
        for task in args.tasks:
            frozen=prepared['designs'][task];ids=frozen['assessment_ids'][:limit or None];source=prepared['rows'][task];g=selected['groups'][task]
            groups=[(task+'_full',g['full'])]+([] if g['duplicate_group'] else [(task+'_minus',g['minus'])])
            recipients=[b for c in p.design.CONDITIONS for stream in p.design.STREAMS for b in p.batches([x for x in source[c] if x['instance_id'] in ids],stream,batch_size=8)]
            all_batches=[b for c in p.design.CONDITIONS for stream in p.design.STREAMS for b in p.batches(source[c],stream,batch_size=8)]
            maps=[m for m in frozen['donors'] if m['recipient_id'] in ids]
            calibration(task,recipients,all_batches,[dict(m,supported=True) for m in maps if m['operation']=='item_swap'])
            for op in p.OPERATIONS:
                for seed in ([101,102,103] if op=='independent_resample' else [None]):cells(task,recipients,all_batches,maps,groups,op,seed)
            for utility in ('ioi','mmlu'):
                urs=prepared['utility'][utility][:limit or None]
                ub=task_batches(urs,batch_size=8)
                ums=[m for m in prepared['utility'][utility+'_maps'] if m['recipient_id'] in {x['instance_id'] for x in urs}]
                db=task_batches(prepared['utility'][utility],**({'stream':'corrupt'} if utility=='ioi' else {}))
                calibration(task,ub,db,[dict(m,supported=True) for m in ums])
                for op in (('item_swap','zero','h_mean','self_replay','empty') if utility=='ioi' else ('zero','h_mean','self_replay','empty')):cells(task,ub,db,ums,groups,op)
        assert sum(scope.values())==len(p.expected_keys(prepared,selected,limit))
        # Describe token cost per actual singleton forward, with padding retained.
        def summarize(cs):
            hist=collections.Counter(c['width'] for c in cs)
            return dict(captures=len(cs),sum_padded_tokens=sum(c['width'] for c in cs),sum_squared_widths=sum(c['width']**2 for c in cs),min_width=min(hist),max_width=max(hist),width_histogram=dict(sorted(hist.items())),max_used=max(c['used'] for c in cs))
        by={task:summarize([c for c in captures if c['task']==task]) for task in (*args.tasks,'ioi','mmlu')}
        top=sorted({(c['task'],c['width'],c['used'],c['id'],c['kind']) for c in captures},key=lambda x:x[1],reverse=True)[:20]
        return dict(expected_rows=len(p.expected_keys(prepared,selected,limit)),positive_controls=len(p.positive_keys(prepared,limit)),total=summarize(captures),by_task=by,by_kind={kind:summarize([c for c in captures if c['kind']==kind]) for kind in sorted({c['kind'] for c in captures})},largest_shapes=top)
    pilot=inventory(4);full=inventory(0)
    timing=manifest['execution']; ratios={key:full['total'][key]/pilot['total'][key] for key in ('captures','sum_padded_tokens','sum_squared_widths')}
    # Approximate Llama-8B transformer linear+attention FLOPs, not a measured bound.
    alpha=2*32*4096/8e9
    ratios['llama_linear_plus_attention']=(full['total']['sum_padded_tokens']+alpha*full['total']['sum_squared_widths'])/(pilot['total']['sum_padded_tokens']+alpha*pilot['total']['sum_squared_widths'])
    projection={key:timing['model_load_seconds']+timing['scoring_compute_seconds']*ratio for key,ratio in ratios.items()}
    ledger=json.loads((p.PRIMARY/'docs/research/specificity-ladder/ledger.json').read_text())
    # A2 paths are named a2-timing-* or .../a2-h200; exclude them all.
    a1=[x for x in ledger['reservations'] if not any(part.startswith('a2-') for part in Path(x['output_dir']).parts)]
    output=dict(status='artifact_audit_passed',source_commit=COMMIT,
        checked_hash_counts=dict(code=len(manifest['code_hashes']),sources=len(manifest['source_hashes']),selection_sources=len(manifest['selection_source_hashes']),protected_registries=len(manifest['registry']),grader_registries=len(manifest['grader_registry'])),
        changed_design_fields=changed_design,changed_selection_fields=changed_selection,registry_difference=changed_directions,
        counts=scored['counts'],row_provenance_passed=True,row_statuses={k:sum(bool(x.get(k)) for x in scored['rows']) for k in ('assay_valid','supported','gate_valid','degenerate')},
        by_task_rows=dict(collections.Counter(x['task'] for x in scored['rows'])),by_owner_controls=dict(collections.Counter(x['mechanism_task'] for x in scored['positive_controls'])),
        noop_max_error=max(x['self_replay_margin_error'] for x in scored['rows']),positive_max_error=max(x['max_abs_logit_error'] for x in scored['positive_controls']),
        previously_failing_control={k:v for k,v in failed[0].items() if k!='sender_keys'},pilot_finalization_rejected=True,
        execution=timing,pilot_inventory=pilot,full_inventory=full,cost_ratios=ratios,projected_stage_seconds=projection,
        a1_ledger=dict(jobs=[x['job_id'] for x in a1],reserved_hours=sum(x['reserved_gpu_hours'] for x in a1),actual_seconds=sum(x['actual_seconds'] or 0 for x in a1),cap_hours=25))
    print(json.dumps(output,sort_keys=True,indent=2,allow_nan=False))

if __name__=='__main__':main()
