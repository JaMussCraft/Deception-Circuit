"""Read-only CPU audit; writes only its independent JSON calculation receipt."""
import json,hashlib,math,struct
from pathlib import Path
from datasets import load_from_disk
R=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
B=R/'outputs/_analyses/specificity-ladder'; OUT=R/'docs/research/specificity-ladder/reports/34-full-control-audit-calculations.json'
H=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
FH=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
J=lambda p:json.loads(p.read_text())
L=lambda p:[json.loads(s) for s in p.read_text().splitlines()]
S=['train','validation','test']; tasks=['far_v2','sdr_v2','ser_v2']; arms=['inversion','baseline']; streams=['clean','corrupt']
C='77b6487b08b4410a4e5a9995c6ff5e46834a5ce3'; V='0e9e39f249a16976918f6564b8830bc894c89659'; model='meta-llama/Llama-3.1-8B-Instruct'
def bf16(value):
 bits=struct.unpack('>I',struct.pack('>f',value))[0]
 bits=(bits+0x7fff+((bits>>16)&1))&0xffff0000
 return struct.unpack('>f',struct.pack('>I',bits))[0]
promoted_discrepancies=0
pool=J(R/'dataset/user_inversion_requests_v2.json'); result={'tasks':{},'threshold':.7,'competence_floor':.3,'protected_overlap':0}; total=0; seconds=0; replay=[]
for task in tasks:
 src={}; source_hashes={}
 for a,suffix in [('D',''),('H','_honest')]:
  path=R/'data/datasets'/(task+suffix); ds=load_from_disk(str(path)); cfg=J(path/'dataset_config.json'); assert cfg['model']==model
  src[a]={s:list(ds[s]) for s in S}; source_hashes[a]={'config':H(cfg),**{s:H(src[a][s]) for s in S}}
  ids=[x['instance_id'] for s in S for x in src[a][s]]; assert len(ids)==len(set(ids))
 adirs={a:B/'a1-control-77b6487-m07'/(task+suffix) for a,suffix in [('inversion','_user_inversion'),('baseline','_user_neutral')]}
 datasets={a:load_from_disk(str(path)) for a,path in adirs.items()}; receipts={a:J(path/'scoring_provenance.json') for a,path in adirs.items()}
 assert receipts['inversion']==receipts['baseline']; receipt=receipts['inversion']
 for k,val in [('source_commit',C),('model',model),('model_revision',V),('tokenizer',model),('tokenizer_revision',V),('request_pool_hash',H(pool)),('dtype','torch.bfloat16'),('scorer','dataset.deception_common.score_prompts')]:assert receipt[k]==val,k
 for a,path in adirs.items():
  cfg=J(path/'dataset_config.json'); ap=J(path/'assembly_provenance.json')
  assert cfg['scoring_provenance']=={'path':'scoring_provenance.json','sha256':FH(path/'scoring_provenance.json')}
  assert cfg['model']==model and cfg['condition']==('user_inversion' if a=='inversion' else 'user_neutral') and cfg['margin_thresh']==(.7 if a=='inversion' else .3)
  assert cfg['baseline_kind']=='matched_frame_neutral_request' and cfg['max_seq_length']==256
  assert ap['source_hashes']==source_hashes and ap['request_pool_hash']==H(pool) and ap['threshold']==.7 and ap['baseline_competence_is_diagnostic'] is True
  actual_files={str(x.relative_to(path)) for x in path.rglob('*') if x.is_file()}-{'assembly_provenance.json'}
  assert set(ap['files'])==actual_files
  for f,h in ap['files'].items():assert FH(path/f)==h,f
  ids=[x['instance_id'] for s in S for x in datasets[a][s]];assert len(ids)==len(set(ids))
 tm={}
 for split,expected in zip(S,[200,200,1000]):
  p=B/'a1-full-77b6487-a100'/task/split; d=B/'a1-derive-dd9aed6'/task/split
  m=J(p/'run_manifest.json'); dm=J(d/'derivation_manifest.json'); rows=L(p/'scores.jsonl'); pairs=L(d/'pairs.jsonl')
  assert len(rows)==len(pairs)==m['count']==m['derived_count']==expected
  assert not m['limited'] and m['limit']==0 and m['forwards']==expected*4 and m['baseline_repeat_forwards']==0
  assert m['requested_splits']==S and m['requested_tasks']==tasks and m['job_id']=='23412591' and m['gpu']=='NVIDIA A100-SXM4-40GB'
  for k in ['source_commit','model','model_revision','tokenizer','tokenizer_revision','request_pool_hash','dtype','scorer']:assert m[k]==receipt[k]
  assert m['source_hashes']==dm['source_hashes']==source_hashes and m['request_pool_hash']==dm['request_pool_hash']==H(pool)
  for f,h in dm['files'].items():assert FH(d/f)==h
  assert FH(d/'derivation_manifest.json')==m['derivation_manifest_sha256']
  assert FH(p/'scores.jsonl')==m['files']['scores.jsonl']
  ids=[x['instance_id'] for x in rows];assert ids==m['ids']==dm['ids']==[x['instance_id'] for x in pairs]==[x['instance_id'] for x in src['D'][split]]
  assert len(ids)==len(set(ids))
  ph=H([{a:{s:H(q[a][s+'_prompt']) for s in streams} for a in arms} for q in pairs]);assert ph==m['prompt_hash']==dm['prompt_hash']
  for path,h in m['registry_sha256'].items():assert FH(Path(path))==h and J(Path(path))=={'schema':1,'sets':[]}
  for a,path in adirs.items():
   sf=receipt['score_files'][split];assert sf['path']=='scores/'+split+'.jsonl' and FH(path/sf['path'])==sf['sha256']==FH(p/'scores.jsonl')
   ap=J(path/'assembly_provenance.json'); link=ap['run_manifests'][split];assert FH(R/link['path'])==link['sha256']==FH(p/'run_manifest.json')
  keep=[]; competent=[]; failure=[]; honest_both=[]; margin_only=[]; argmax_fail=[]
  source={a:{x['instance_id']:x for x in src[a][split]} for a in ['D','H']}
  for q,x in zip(pairs,rows):
   sh={a:H(source[a][x['instance_id']]) for a in ['D','H']}; assert q['source_row_hashes']==sh
   for a in arms:
    assert q[a]['source_row_hashes']==sh
    for s in streams:
     score=x[a][s]; honest,opp=(q['inversion']['distractor'],q['inversion']['target']) if s=='clean' else (q['inversion']['target'],q['inversion']['distractor'])
     assert (score['expected_honest'],score['expected_opposite'])==(honest,opp)
     assert score['prompt_hash']==H(q[a][s+'_prompt'])
     assert all(math.isfinite(score[k]) for k in ['margin','logit_a','logit_b','honest_minus_opposite','opposite_minus_honest'])
     assert score['margin']==score['honest_minus_opposite']==-score['opposite_minus_honest']
     assert score['margin']==bf16(score['logit_a']-score['logit_b'])
     promoted_discrepancies+=int(score['margin']!=score['logit_a']-score['logit_b'])
     if score['choice'] in ['a','b']:assert score['argmax']==score['expected_honest_token' if score['choice']=='a' else 'expected_opposite_token']
   if all(x['inversion'][s]['choice']=='b' and -x['inversion'][s]['margin']>=.7 for s in streams):
    keep.append(q); iid=x['instance_id']; bh=all(x['baseline'][s]['choice']=='a' for s in streams)
    if bh:honest_both.append(iid)
    if bh and all(x['baseline'][s]['margin']>=.3 for s in streams):competent.append(iid)
    else:
     failure.append(iid)
     (margin_only if bh else argmax_fail).append(iid)
  kept_ids=[x['instance_id'] for x in keep]
  for a,path in adirs.items():
   actual=list(datasets[a][split]);assert actual==[q[a] for q in keep]
   cfg=J(path/'dataset_config.json'); assert cfg[{'train':'train_samples','validation':'val_samples','test':'test_samples'}[split]]==len(keep)
   fr=J(path/'filter_report.json')[split]
   assert fr['retained_count']==len(keep) and fr['paired_competent_count']==len(competent) and fr['paired_competent_ids']==competent and fr['baseline_failure_ids']==failure
   assert fr['rejected_ids']==[x for x in ids if x not in set(kept_ids)]
   if split=='test':assert fr['pool_gate']['passes']==(len(set(kept_ids))>=300) and fr['pool_gate']['margin']==.7
  clean=sum(x['baseline']['clean']['choice']=='a' for x in rows if x['instance_id'] in set(kept_ids));corrupt=sum(x['baseline']['corrupt']['choice']=='a' for x in rows if x['instance_id'] in set(kept_ids))
  metric={'all_neutral_honest_clean':sum(x['baseline']['clean']['choice']=='a' for x in rows),'all_neutral_honest_corrupt':sum(x['baseline']['corrupt']['choice']=='a' for x in rows),'all_neutral_honest_both':sum(all(x['baseline'][s]['choice']=='a' for s in streams) for x in rows),'all_neutral_competent':sum(all(x['baseline'][s]['choice']=='a' and x['baseline'][s]['margin']>=.3 for s in streams) for x in rows),'scored':len(rows),'retained':len(keep),'paired_competent':len(competent),'retained_neutral_honest_both':len(honest_both),'retained_neutral_honest_clean':clean,'retained_neutral_honest_corrupt':corrupt,'retained_neutral_margin_only_failures':len(margin_only),'retained_neutral_argmax_failures':len(argmax_fail),'retained_failure_ids':failure,'seconds':m['seconds']}
  if split=='test':
   old=L(B/'a1-pilot-dd9aed6'/task/'test/scores.jsonl');assert [x['instance_id'] for x in old]==ids[:32]
   exact=sum(x==y for x,y in zip(rows,old)); choice=sum(x[a][s]['choice']==y[a][s]['choice'] for x,y in zip(rows,old) for a in arms for s in streams);margin=sum(x[a][s]['margin']==y[a][s]['margin'] for x,y in zip(rows,old) for a in arms for s in streams)
   metric['pilot_overlap']={'rows':32,'exact_records':exact,'choice_equal':choice,'margin_equal':margin,'expected_scores':128,'max_abs_margin_difference':max(abs(x[a][s]['margin']-y[a][s]['margin']) for x,y in zip(rows,old) for a in arms for s in streams)}
   replay.extend([x[a][s]['margin']-y[a][s]['margin'] for x,y in zip(rows,old) for a in arms for s in streams])
  tm[split]=metric;total+=len(rows);seconds+=m['seconds']
 result['tasks'][task]=tm
assert total==4200
result['totals']={'scored_rows':total,'prompt_evaluations':total*4,'scoring_seconds':seconds,'elapsed_seconds':429,'gpu_hours':429/3600,'pilot_overlap_scores':len(replay),'pilot_overlap_margin_exact':sum(d==0 for d in replay),'pilot_overlap_max_abs_margin_difference':max(map(abs,replay))}
result['promoted_subtraction_discrepancies']=promoted_discrepancies;result['all_hashes_and_arrow_checks']='passed';OUT.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
