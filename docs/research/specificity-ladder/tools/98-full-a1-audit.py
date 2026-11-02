#!/usr/bin/env python
"""Independent read-only A1 full artifact and raw primary-gate audit.

--prepare-only audits frozen parents and corrected pilot, without inspecting a
running full job. Default mode requires terminal accounting, full score and the
orchestrator's existing canonical summary. It never writes production artifacts,
loads models/tokenizers, calls canonical summarization, or submits jobs.
"""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from component_analysis import ladder_pipeline as p, specificity_ladder as runner
from component_analysis.ladder_tasks import task_batches
BASE=ROOT/'outputs/_analyses/specificity-ladder'
PARENT=BASE/'ladder-5f450dc'
COMMIT='5f450dc93dac707af649dee8c8ca60888b2831db'
CONDITIONS=('D','H','F','I','user_neutral')


def close(actual,expected,path='value'):
    if isinstance(expected,dict):
        for key,value in expected.items():
            assert key in actual,(path,key)
            close(actual[key],value,path+'.'+key)
    elif isinstance(expected,(list,tuple)):
        assert len(actual)==len(expected),path
        for i,(left,right) in enumerate(zip(actual,expected)):close(left,right,path+f'[{i}]')
    elif isinstance(expected,(float,np.floating)):
        assert actual is not None and math.isclose(float(actual),float(expected),rel_tol=1e-9,abs_tol=1e-9),(path,actual,expected)
    else:assert actual==expected,(path,actual,expected)


def independent_primary(rows,task,group,*,n_boot=2000,seed=1):
    """Compute item-swap point estimates and paired pressure-cluster bootstrap.

    No calls to ladder_metrics, its private helpers, or qualify_summary. Utility
    never enters pressure denominators; unsupported observations remain counted.
    """
    original=[r for r in rows if r['group']==group and r['operation']=='item_swap'
              and (r['task']==task or r['task'] in ('ioi','mmlu'))]
    by=defaultdict(list)
    for row in original:by[(row['condition'],row['instance_id'])].append(row)
    required_ids={r['instance_id'] for r in original if r['condition']=='D'}
    for condition in CONDITIONS:
        assert {rid for c,rid in by if c==condition}==required_ids
    for (condition,_),records in by.items():
        assert sorted(r['stream'] for r in records)==(['clean'] if condition in ('IOI','MMLU') else ['clean','corrupt'])
    supported={key for key,records in by.items() if all(r.get('supported',True) for r in records)}
    ids=sorted(rid for rid in required_ids if all((c,rid) in supported for c in ('D','H','I','user_neutral')))
    coverage=dict(total=len(original),unsupported=sum(not r.get('supported',True) for r in original),
                  invalid=sum(not r.get('assay_valid',True) for r in original),
                  degenerate=sum(r.get('degenerate',False) for r in original))
    if not ids:return dict(coverage=coverage,n_assessment_ids=len(required_ids),interpretable=False,point_pass=False,strong=False,status='unsupported')
    diagnostic=[r for r in original if (r['condition'],r['instance_id']) in supported
                and (r['condition'] not in CONDITIONS or r['instance_id'] in ids)]
    paired=defaultdict(dict)
    for row in diagnostic:paired[(row['condition'],row['instance_id'])][row['stream']]=row
    epsilon=max(1e-6,10*max(abs(r.get('self_replay_margin_error',0)) for r in original))
    streams=('clean','corrupt')
    arrays={}
    for condition,neutral in (('D','H'),('I','user_neutral')):
        gaps=np.array([[paired[(condition,rid)][s]['intact_margin']-paired[(neutral,rid)][s]['intact_margin'] for s in streams] for rid in ids],dtype=float)
        drops=np.array([[paired[(condition,rid)][s]['intact_margin']-paired[(condition,rid)][s]['patched_margin'] for s in streams] for rid in ids],dtype=float)
        arrays[condition]=(gaps,drops)
    def effects(indices):
        out={}
        for condition,(gaps,drops) in arrays.items():
            selected=gaps[indices];delta=drops[indices]
            gap=float(selected.mean(axis=1).mean());drop=float(delta.mean(axis=1).mean())
            stream_gaps={s:float(selected[:,j].mean()) for j,s in enumerate(streams)}
            valid=math.isfinite(gap) and gap>epsilon and all(math.isfinite(v) and v>epsilon for v in stream_gaps.values()) and math.isfinite(drop)
            out[condition]=dict(gap=gap,drop=drop,fraction_removed=drop/gap if valid else None,stream_gaps=stream_gaps,
                streams={s:dict(gap=stream_gaps[s],drop=float(delta[:,j].mean()),fraction_removed=float(delta[:,j].mean())/stream_gaps[s] if stream_gaps[s]>epsilon else None) for j,s in enumerate(streams)},interpretable=valid)
        return out
    effect=effects(np.arange(len(ids)))
    def accuracy(records):
        return dict(intact_accuracy=float(np.mean([float(r['intact_correct']) for r in records])) if records else None,
                    patched_accuracy=float(np.mean([float(r['patched_correct']) for r in records])) if records else None,
                    accuracy_shift=float(np.mean([float(r['patched_correct'])-float(r['intact_correct']) for r in records])) if records else None,
                    nontrivial=bool(records) and all(r.get('gate_valid',True) and not r.get('degenerate',False) for r in records))
    collateral={c:accuracy([r for r in diagnostic if r['condition']==c]) for c in ('H','F','IOI')}
    mmlu_rows=[r for r in diagnostic if r['condition']=='MMLU']
    assert not mmlu_rows,'MMLU must not acquire an invented native item-swap operation'
    mmlu=dict(intact_accuracy=None,patched_accuracy=None,accuracy_shift=None,nontrivial=False,additional_errors=0,pass_=None)
    mmlu['pass']=mmlu.pop('pass_');mmlu['shift_interval']=None;mmlu['additional_errors_interval']=None
    clusters=defaultdict(list)
    for i,rid in enumerate(ids):
        labels={str(row.get('pressure_id',rid)) for c in CONDITIONS for row in paired.get((c,rid),{}).values()}
        assert len(labels)==1,'pressure cluster mismatch'
        clusters[labels.pop()].append(i)
    names=sorted(clusters);rng=np.random.default_rng(seed)
    draws={c:[] for c in effect};collateral_draws={c:[] for c in collateral}
    utility_ids=sorted(rid for condition,rid in paired if condition=='IOI')
    for _ in range(n_boot):
        sampled=[i for name in rng.choice(names,len(names),replace=True) for i in clusters[name]]
        estimate=effects(sampled)
        for c in draws:
            if estimate[c]['fraction_removed'] is not None:draws[c].append(estimate[c]['fraction_removed'])
        for condition in collateral:
            chosen=([ids[i] for i in sampled] if condition in ('H','F') else rng.choice(utility_ids,len(utility_ids),replace=True) if utility_ids else [])
            records=[row for rid in chosen for row in paired.get((condition,rid),{}).values()]
            shift=accuracy(records)['accuracy_shift']
            if shift is not None:collateral_draws[condition].append(shift)
    for condition,values in draws.items():
        effect[condition]['fraction_interval']=np.percentile(values,[2.5,97.5]).tolist() if len(values)==n_boot else None
        effect[condition]['valid_bootstrap_draws']=len(values)
    for condition,values in collateral_draws.items():collateral[condition]['shift_interval']=np.percentile(values,[2.5,97.5]).tolist() if values else None
    interpretable=all(v['interpretable'] for v in effect.values()) and not coverage['invalid']
    point=bool(not coverage['unsupported'] and interpretable and effect['D']['fraction_removed']>=.5 and effect['I']['fraction_removed']<.25
        and all(v['nontrivial'] and v['accuracy_shift'] is not None and abs(v['accuracy_shift'])<.05-1e-12 for v in collateral.values()))
    strong=bool(point and all(effect[c]['fraction_interval'] is not None for c in effect)
        and effect['D']['fraction_interval'][0]>=.5 and effect['I']['fraction_interval'][1]<.25
        and all(v['shift_interval'] is not None and v['shift_interval'][0]>-.05 and v['shift_interval'][1]<.05 for v in collateral.values()))
    return dict(coverage=coverage,D=effect['D'],I=effect['I'],collateral=collateral,MMLU=mmlu,epsilon=epsilon,n_ids=len(ids),n_assessment_ids=len(required_ids),n_clusters=len(clusters),
                interpretable=interpretable,point_pass=point,strong=strong,status='unsupported' if coverage['unsupported'] else 'strong' if strong else 'uncertain' if point else 'fails' if interpretable else 'uninterpretable')


def independent_readiness(rows,task,group,expected_ids):
    """Crossed completeness and separately passed fixed MMLU floors."""
    missing=[]
    for op in ('item_swap','zero','h_mean','h_twin'):
        records=[r for r in rows if r['task']==task and r['group']==group and r['operation']==op]
        required=CONDITIONS if op!='h_twin' else ('D','H','I','user_neutral')
        complete=bool(records) and all({r['instance_id'] for r in records if r['condition']==c}==set(expected_ids) for c in required)
        complete=complete and all(r.get('supported',True) and r.get('assay_valid',True) for r in records if r['condition'] in required)
        if not complete:missing.append(op)
    floors={}
    for op in ('zero','h_mean'):
        records=[r for r in rows if r['group']==group and r['task']=='mmlu' and r['condition']=='MMLU' and r['operation']==op]
        ids=[r['instance_id'] for r in records]
        complete=len(ids)==32 and len(set(ids))==32 and all(r['stream']=='clean' and r.get('supported',True) and r.get('assay_valid',True) and r.get('gate_valid',True) and not r.get('degenerate',False) for r in records)
        errors=sum(float(r['intact_correct'])-float(r['patched_correct']) for r in records) if complete else None
        floors[op]=dict(n_rows=len(records),complete=complete,ids=ids,additional_errors=errors,passed=bool(complete and errors<=1))
    same=set(floors['zero']['ids'])==set(floors['h_mean']['ids']);complete=same and all(v['complete'] for v in floors.values())
    mmlu=dict(complete=complete,same_ids=same,operations=floors,missing_operations=[op for op,v in floors.items() if not v['complete']],passed=complete and all(v['passed'] for v in floors.values()))
    ioi=[r for r in rows if r['group']==group and r['task']=='ioi' and r['condition']=='IOI' and r['operation']=='item_swap']
    ioi_complete=bool(ioi) and len({r['instance_id'] for r in ioi})==len(ioi) and all(r['stream']=='clean' and r.get('supported',True) and r.get('assay_valid',True) and r.get('gate_valid',True) and not r.get('degenerate',False) for r in ioi)
    return dict(complete=not missing and complete and ioi_complete,missing_crossed_operations=missing,MMLU=mmlu,IOI=dict(complete=ioi_complete,n_rows=len(ioi)))


def audit_parents():
    original=json.loads((BASE/'calibration-diagnostic-0253f49/run_manifest.json').read_text())['argv']
    args=SimpleNamespace(**dict(original,commit=COMMIT,design=str(PARENT/'design.json'),groups=str(PARENT/'selected.json'),work_dir=str(PARENT/'full'),limit=0,injected=False))
    prepared=p.read_artifact(args.design);p.validate_prepared(args,prepared);selected=p.read_selection(args,prepared)
    old=p.read_artifact(BASE/'ladder-0253f49/design.json');old_selected=p.read_artifact(BASE/'ladder-0253f49/selected.json')
    assert sorted(k for k in prepared if prepared[k]!=old[k])==['code_hashes','commit','grader_registry']
    assert selected['groups']==old_selected['groups'] and selected['banks']==old_selected['banks']
    mover={}
    for task,g in selected['groups'].items():
        evidence=g['selection_evidence'];clean=np.asarray(evidence['clean_dla']);corrupt=np.asarray(evidence['corrupt_dla'])
        assert np.isfinite(clean).all() and np.isfinite(corrupt).all()
        candidate=[head for j,head in enumerate(evidence['head_keys']) if clean[:,j].mean()>0 and int(((clean[:,j]>0)&(corrupt[:,j]>0)).sum())*4>=3*len(clean)]
        assert sorted(candidate)==sorted(g['screen']['removed_keys'])
        assert g['duplicate_group']==(not candidate)
        assert g['minus']==[key for key in g['full'] if key not in candidate]
        assert g['descriptive']==(task=='sdr_v2')
        mover[task]=dict(removed_keys=candidate,n_removed=len(candidate),duplicate_group=g['duplicate_group'],descriptive=g['descriptive'],interpretation='answer-contribution screen only; zero candidates do not establish absence of answer copying')
    assert len(p.expected_keys(prepared,selected,0))==28884
    assert len(p.positive_keys(prepared,0))==3396
    return args,prepared,selected,mover


def audit_score(args,prepared,selected,folder,*,limit,job):
    scored=p.read_artifact(folder/'score/score.json');manifest=json.loads((folder/'score/run_manifest.json').read_text())
    assert manifest==scored['run_manifest']
    assert manifest['commit']==prepared['commit']==COMMIT
    for key in ('model','model_revision','tokenizer_revision','grader_sha256','readout','code_hashes','source_hashes','tokenizer_identity','tokenizer_loading'):assert manifest[key]==prepared[key],key
    assert manifest['code_hashes']==p.code_hashes()
    assert manifest['grader_registry']==p.grader_registry()
    assert manifest['registry']==p.registries(args,prepared['rows'])
    assert prepared['registry_hashes']==dict(p.registries(args,prepared['rows']),**p.utility_registries(args,prepared['utility']))
    assert manifest['selection_source_hashes']==prepared['selection_hashes']
    for key,value in dict(design_sha256=p.design._hash(prepared),selection_sha256=p.design._hash(selected)).items():assert scored[key]==manifest[key]==value
    for key in ('bank_sha256','group_sha256'):assert manifest[key]==selected[key]
    assert manifest['domain_hashes']=={task:f['hashes'] for task,f in prepared['designs'].items()}
    assert manifest['utility_sample_hashes']=={task:p.design._hash(prepared['utility'][task]) for task in ('ioi','mmlu')}
    assert manifest['execution']==scored['execution_provenance']
    assert manifest['seeds']==dict(sample=1,bootstrap=1,independent_donors=[101,102,103]) and manifest['operations']==list(p.OPERATIONS)
    assert scored['pilot']==bool(limit) and scored['limit']==limit and scored['injected'] is False
    execution=manifest['execution'];assert execution['slurm_job_id']==job and execution['cluster']=='delta'
    assert manifest['dtype']==execution['dtype']=='torch.bfloat16'
    assert 0<execution['model_load_seconds'] and 0<execution['scoring_compute_seconds']
    assert execution['scoring_stage_seconds']>=execution['model_load_seconds']+execution['scoring_compute_seconds']
    assert 0<execution['peak_allocated_memory_bytes']<=execution['peak_reserved_memory_bytes']
    expected=p.expected_keys(prepared,selected,limit);p.validate_rows(scored['rows'],expected)
    assert set(map(tuple,scored['expected']))==set(expected) and len(scored['expected'])==len(expected)
    p.validate_positive_controls(scored['positive_controls'],prepared,limit)
    assert scored['counts']==manifest['counts']==dict(rows=len(scored['rows']),expected=len(expected),positive_controls=len(scored['positive_controls']))
    recipients={};maps={}
    for task in prepared['tasks']:
        ids=prepared['designs'][task]['assessment_ids'][:limit or None]
        for condition in p.design.CONDITIONS:
            for stream in p.design.STREAMS:
                for batch in p.batches([x for x in prepared['rows'][task][condition] if x['instance_id'] in ids],stream,batch_size=8):
                    for one in runner._rows(batch):recipients[(task,one.ids[0],condition,stream)]=one
        for m in prepared['designs'][task]['donors']:maps[(task,m['recipient_id'],m['recipient_condition'],m['recipient_stream'],m['operation'],m.get('seed'))]=m
    for task in ('ioi','mmlu'):
        for batch in task_batches(prepared['utility'][task][:limit or None],batch_size=8):
            for one in runner._rows(batch):recipients[(task,one.ids[0],one.condition,one.stream)]=one
        for m in prepared['utility'][task+'_maps']:maps[(task,m['recipient_id'],m['recipient_condition'],m['recipient_stream'],m['operation'],m.get('seed'))]=m
    for row in scored['rows']:
        assert row['assay_valid'] and row['self_replay_margin_error']==0
        batch=recipients[tuple(row[k] for k in ('task','instance_id','condition','stream'))]
        assert row['source_provenance']==batch.records[0]
        for label in ('honest_token','opposite_token','expected_token'):assert row[label]==int(getattr(batch,label)[0])
        owner=next(task for task in prepared['tasks'] if row['group'].startswith(task+'_'))
        assert row['group_members']==selected['groups'][owner]['minus' if row['group'].endswith('_minus') else 'full']
        map_key=tuple(row[k] for k in ('task','instance_id','condition','stream','operation','donor_seed'))
        mapping=maps.get(map_key)
        if mapping is not None:
            mapping=dict(mapping)
            if row['operation'] in ('item_swap','h_twin','independent_resample') and mapping['supported']:
                donor_rows=prepared['rows'][row['task']][mapping['donor_condition']] if row['task'] in prepared['tasks'] else prepared['utility'][row['task']]
                donor=next(x for x in donor_rows if x['instance_id']==mapping['donor_id'])
                if batch.records[0]['streams'][row['stream']]['tokens']==donor['streams'][mapping['donor_stream']]['tokens']:
                    mapping.update(degenerate=True,gate_valid=False,no_op=True)
            assert row['donor_provenance']==mapping
            assert row['supported']==mapping['supported']
            assert row['degenerate']==bool(mapping.get('degenerate',False) or not row['group_members'])
            assert row['gate_valid']==bool(mapping.get('gate_valid',False) and row['group_members'])
        else:
            assert row['donor_provenance'] is None and row['supported']
            assert row['degenerate']==bool(row['operation'] in ('self_replay','empty') or not row['group_members'])
            assert row['gate_valid']==bool(row['operation'] not in ('self_replay','empty') and row['group_members'])
        if 'mean_bank_provenance' in row:p.resolve_bank_reference(row['mean_bank_provenance'],selected)
        for value in row.values():
            if isinstance(value,float):assert math.isfinite(value)
    senders=[['embed',0,0]]
    for layer in range(32):senders.extend([['head',layer,head] for head in range(32)]);senders.append(['mlp',layer,0])
    for control in scored['positive_controls']:
        assert control['valid'] and control['max_abs_logit_error']==0 and control['sender_keys']==senders
        batch=recipients[tuple(control[k] for k in ('task','instance_id','condition','stream'))]
        mapping=control['donor_provenance'];assert mapping['recipient_positions']==batch.readout.tolist()
        if control['task'] in prepared['tasks']:
            donor=next(x for x in prepared['rows'][control['task']][mapping['donor_condition']] if x['instance_id']==mapping['donor_id'])
        else:donor=next(x for x in prepared['utility'][control['task']] if x['instance_id']==mapping['donor_id'])
        assert mapping['donor_positions']==[donor['streams'][mapping['donor_stream']]['readout']]
        frozen=maps[(control['task'],control['instance_id'],control['condition'],control['stream'],mapping['operation'],mapping.get('seed'))]
        expected=dict(frozen,supported=True,recipient_positions=batch.readout.tolist(),donor_positions=[donor['streams'][mapping['donor_stream']]['readout']])
        assert mapping==expected
    return scored,manifest


def self_test():
    rows=[]
    for i in range(4):
        for condition,base,drop in [('D',3+i,1),('H',1+i,0),('F',1,0),('I',2,.1),('user_neutral',1,0),('IOI',1,0)]:
            for stream in (('clean',) if condition=='IOI' else ('clean','corrupt')):
                rows.append(dict(task='ioi' if condition=='IOI' else 'far_v2',instance_id=str(i),pressure_id=str(i//2),condition=condition,stream=stream,group='g',operation='item_swap',intact_margin=base,patched_margin=base-drop,intact_correct=True,patched_correct=True,supported=True,assay_valid=True,gate_valid=True,degenerate=False,self_replay_margin_error=0))
    result=independent_primary(rows,'far_v2','g',n_boot=20)
    close(result['D']['fraction_removed'],.5);close(result['I']['fraction_removed'],.1)
    assert result['point_pass'] and result['strong'] and result['n_clusters']==2
    # Exact strict I boundary, without changing the D threshold or collateral.
    for row in rows:
        if row['condition']=='I':row['patched_margin']=row['intact_margin']-.25
    assert not independent_primary(rows,'far_v2','g',n_boot=20)['point_pass']
    for row in rows:
        if row['condition']=='I':row['patched_margin']=row['intact_margin']-.1
        if row['condition']=='D':
            row['intact_margin']=1+int(row['instance_id'])+(1 if int(row['instance_id'])<2 else 3)
            row['patched_margin']=row['intact_margin']-1
    unequal=independent_primary(rows,'far_v2','g',n_boot=20)
    close(unequal['D']['fraction_removed'],.5)
    assert unequal['point_pass'] and not unequal['strong']
    crossed=list(rows)
    for op in ('zero','h_mean','h_twin'):
        crossed.extend(dict(row,operation=op) for row in rows if row['task']=='far_v2')
    for op in ('zero','h_mean'):
        for i in range(32):crossed.append(dict(rows[0],task='mmlu',condition='MMLU',instance_id='m'+str(i),stream='clean',operation=op,intact_correct=True,patched_correct=not(op=='zero' and i<2)))
    ready=independent_readiness(crossed,'far_v2','g',list(map(str,range(4))))
    assert ready['complete'] and not ready['MMLU']['passed']
    assert ready['MMLU']['operations']['zero']['additional_errors']==2
    print(json.dumps(dict(status='self_test_passed',synthetic_only=True,checks=['ratio-of-means with unequal denominators','paired streams','cluster intervals','inclusive D','strict I','point versus interval strength','MMLU completeness versus pass']),sort_keys=True))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--self-test',action='store_true')
    options=parser.parse_args()
    if options.self_test:return self_test()
    if not options.prepare_only:
        for path in (PARENT/'full/score/score.json',PARENT/'full/score/run_manifest.json',PARENT/'full/summary.json',PARENT/'full/accounting.txt'):
            if not path.is_file():raise SystemExit('Required completed-run evidence missing: '+str(path))
    args,prepared,selected,mover=audit_parents()
    pilot,pilot_manifest=audit_score(args,prepared,selected,PARENT/'pilot-4',limit=4,job='23417413')
    output=dict(status='preparation_passed' if options.prepare_only else 'full_audit_passed',source_commit=COMMIT,mover_screen=mover,
                parent_design_sha256=p.design._hash(prepared),parent_selection_sha256=p.design._hash(selected),pilot_counts=pilot['counts'],
                expected_full_rows=len(p.expected_keys(prepared,selected,0)),expected_full_positive_controls=len(p.positive_keys(prepared,0)),
                full_run_examined=False,canonical_summary_examined=False)
    if options.prepare_only:
        output['next_command']='OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/98-full-a1-audit.py'
    else:
        scored,manifest=audit_score(args,prepared,selected,PARENT/'full',limit=0,job='23417811')
        p.validate_finalization(scored,final=True)
        terminal=(PARENT/'full/accounting.txt').read_text().splitlines()
        main_record=next(line.split('|') for line in terminal if line.split('|')[0]=='23417811')
        assert main_record[1:3]==['delta','COMPLETED'] and main_record[4]=='0:0'
        summary=p.read_artifact(PARENT/'full/summary.json');assert summary['score_sha256']==p.design._hash(scored)
        canonical=summary['summary'];assert canonical['bootstrap']==dict(seed=1,n_boot=2000,confidence=.95,unit='source pressure id; paired id for utility',donor_seed_outer='independent_resample only')
        expected_cells={(task,name,op) for task,g in selected['groups'].items() for name in ([task+'_full']+([] if g['duplicate_group'] else [task+'_minus'])) for op in p.OPERATIONS}
        actual_cells=[(c['task'],c['group'],c['operation']) for c in canonical['cells']]
        assert len(actual_cells)==len(set(actual_cells)) and set(actual_cells)==expected_cells
        assert type(summary['final']) is bool
        primary=[]
        for task,g in selected['groups'].items():
            names=[task+'_full']+([] if g['duplicate_group'] else [task+'_minus'])
            for group in names:
                computed=independent_primary(scored['rows'],task,group)
                cell=next(c for c in canonical['cells'] if (c['task'],c['group'],c['operation'])==(task,group,'item_swap'))
                comparable=dict(cell)
                if g['descriptive']:
                    assert cell['status']=='descriptive_only' and cell['strong'] is False
                    comparable['status']=cell['numerical_status'];comparable['strong']=cell['numerical_strong']
                assert cell['descriptive']==g['descriptive']
                assert cell['source_group_provenance']==dict(task=task,full=g['full'],minus=g['minus'],duplicate_group=g['duplicate_group'])
                close(comparable,computed,task+'.'+group)
                readiness=independent_readiness(scored['rows'],task,group,prepared['designs'][task]['assessment_ids'])
                close(cell['assay_readiness'],readiness,task+'.readiness');assert cell['complete_assay_ready']==readiness['complete']
                eligible=not g['descriptive']
                primary.append(dict(task=task,group=group,independent_estimates=computed,assay_readiness=readiness,descriptive=g['descriptive'],
                    joined_primary_point_pass=bool(eligible and computed['point_pass'] and readiness['complete'] and readiness['MMLU']['passed']),
                    joined_primary_strong=bool(eligible and computed['strong'] and readiness['complete'] and readiness['MMLU']['passed'])))
        if summary['final']:assert all(c['assay_readiness']['complete'] for c in primary)
        # All SDR operations retain their qualification, not merely item-swap.
        for cell in canonical['cells']:
            if cell['task']=='sdr_v2':assert cell['descriptive'] and cell['status']=='descriptive_only' and cell['strong'] is False
        output.update(full_run_examined=True,canonical_summary_examined=True,canonical_summary_final=summary['final'],full_counts=scored['counts'],execution=manifest['execution'],accounting_main_record=main_record,
                      independent_primary=primary,full_noop_max_error=max(r['self_replay_margin_error'] for r in scored['rows']),full_positive_max_error=max(c['max_abs_logit_error'] for c in scored['positive_controls']),
                      full_row_statuses={k:sum(bool(r.get(k)) for r in scored['rows']) for k in ('assay_valid','supported','degenerate','gate_valid')},by_task_rows=dict(Counter(r['task'] for r in scored['rows'])))
    print(json.dumps(output,sort_keys=True,indent=2,allow_nan=False))

if __name__=='__main__':main()
