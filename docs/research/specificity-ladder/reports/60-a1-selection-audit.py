"""CPU-only audit of saved A1 selection. Never executes the selection runner/model."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from datasets import load_from_disk
from transformers import AutoTokenizer
R=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');P=Path('/projects/beto/swong2/Alignment/Deception-Circuit')
B=R/'outputs/_analyses/specificity-ladder/ladder-0253f49';OLD=R/'outputs/_analyses/specificity-ladder/ladder-6bd8bf5/design.json';O=R/'docs/research/specificity-ladder/reports/60-a1-selection-audit-calculations.json'
J=lambda p:json.loads(Path(p).read_text());H=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def FH(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for z in iter(lambda:f.read(2**20),b''):h.update(z)
 return h.hexdigest()
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def artifact(p):
 q=J(p);assert q['sha256']==H(q['payload']);return q['payload']
a=artifact(OLD);d=artifact(B/'design.json');s=artifact(B/'selected.json');m=J(B/'selection_run_manifest.json');eq=J(B/'design-semantic-equivalence.json')
C='0253f494af007f93b2a00cb1e63cb3cdf1a8b519';rev='0e9e39f249a16976918f6564b8830bc894c89659'
assert a['commit']=='6bd8bf5334f2e83613a129d2fcfeacf83e762191' and d['commit']==m['commit']==C
assert set(a)==set(d) and {k for k in a if a[k]!=d[k]}=={'commit','code_hashes'}
equalkeys=set(d)-{'commit','code_hashes'};assert all(a[k]==d[k] for k in equalkeys)
assert eq['old_file_sha256']==FH(OLD) and eq['new_file_sha256']==FH(B/'design.json') and eq['old_commit']==a['commit'] and eq['new_commit']==C and eq['all_other_fields_exactly_equal'] is True and eq['model_execution'] is False
assert eq['equal_payload_fields']=={k:H(d[k]) for k in equalkeys}
changed=[p for p in d['code_hashes'] if a['code_hashes'].get(p)!=d['code_hashes'][p]];assert changed==eq['changed_code_files']==['component_analysis/ladder_pipeline.py']
assert m['code_hashes']==d['code_hashes'] and all(FH(R/p)==h for p,h in d['code_hashes'].items())
assert m['source_hashes']==d['source_hashes'] and m['selection_source_hashes']==d['selection_hashes']
for domain in ['source_hashes','selection_hashes','registry_hashes','grader_registry']:
 for p,h in d[domain].items():assert FH(path(p))==h,(domain,p)
for root in [P,R]:
 files=sorted(list((root/'evaluation/benchmarks').glob('*.py'))+[root/'evaluation/benchmark_eval.py'])
 grader=hashlib.sha256(''.join(f'{f.relative_to(root).as_posix()}\t{FH(f)}\n' for f in files).encode()).hexdigest();assert grader==d['grader_sha256']
 row=next(r for r in J(root/'docs/research/directions.json')['directions'] if r['id']=='specificity-ladder');assert row['frozen_grader_sha256']==grader
 assert J(root/'docs/research/held_out.json')=={'schema':1,'sets':[]}
assert s['kind']=='selected' and m['kind']=='specificity_ladder_selection' and m['schema_version']==1
assert d['injected'] is s['injected'] is m['injected'] is False
assert m['selection_artifact']==str((B/'selected.json').resolve()) and m['selection_file_sha256']==FH(B/'selected.json')
assert m['selection_artifact_sha256']==H(s) and m['design_sha256']==s['design_sha256']==H(d)
assert m['group_sha256']==s['group_sha256']==H(s['groups']) and m['bank_sha256']==s['bank_sha256']==H(s['banks'])
assert m['raw_dla_sha256']==H({t:g['selection_evidence'] for t,g in s['groups'].items()})
ex=s['execution_provenance'];assert m['execution']==ex and ex['commit']==C and ex['slurm_job_id']=='23415379' and ex['cluster']=='delta' and ex['cluster_source']=='SLURM_CLUSTER_NAME'
assert ex['device']=='cuda:0' and ex['dtype']=='torch.bfloat16' and ex['gpu_name']=='NVIDIA A100-SXM4-40GB'
for k in ['model','model_revision','tokenizer_revision']:assert m[k]==d[k]==ex[k]
assert d['model_revision']==d['tokenizer_revision']==rev
for k in ['model_load_seconds','selection_compute_seconds','selection_stage_seconds','peak_allocated_memory_bytes','peak_reserved_memory_bytes']:assert isinstance(ex[k],(float,int)) and math.isfinite(ex[k]) and ex[k]>0
assert ex['selection_stage_seconds']>=ex['selection_compute_seconds']+ex['model_load_seconds'] and ex['peak_reserved_memory_bytes']>=ex['peak_allocated_memory_bytes']
account=(B/'selection_accounting.txt').read_text().strip().split('|');assert account[0]=='23415379' and account[1]=='delta' and account[2]=='COMPLETED' and account[3]=='195' and account[4]=='0:0'
config=J(Path(d['tokenizer_loading']['resolved_snapshot'])/'config.json');hidden=config['hidden_size'];head_dim=hidden//config['num_attention_heads'];assert hidden==4096 and head_dim==128
tok=AutoTokenizer.from_pretrained(d['tokenizer_loading']['resolved_snapshot'],local_files_only=True)
assert set(s['groups'])==set(s['banks'])==set(m['counts'])==set(d['tasks'])
all_assessment=set().union(*(set(f['assessment_ids']) for f in d['designs'].values()));all_selection=set();all_banks=set();out={}
for task in d['tasks']:
 f=d['designs'][task];g=s['groups'][task];e=g['selection_evidence'];bank=s['banks'][task];p=bank['provenance'];rows={r['instance_id']:r for r in d['rows'][task]['H']}
 raw=load_from_disk(str(R/'data/datasets'/(task+'_honest')));orig={r['instance_id']:r for split in ['train','validation','test'] for r in raw[split]}
 ids=f['mover_selection_ids'];assert len(ids)==len(set(ids))==100 and ids==e['selection_ids']==g['screen']['selection_ids']
 selectionfile=next(Path(q) for q in d['selection_hashes'] if Path(q).parent.name==task);assert J(selectionfile)['instance_ids']==ids
 all_selection.update(ids);assert not set(ids)&all_assessment
 full=d['recorded_groups'][task[:-3]]['members'];heads=[k for k in full if k[0]=='head'];assert e['head_keys']==heads and g['full']==full and len(full)==20
 reading=J(P/'docs/research/mechanism-analysis/phase1/p1c_readings.json')['rab'][task[:-3]]['deciding_numbers']['members'];assert full==[[v.split('.')[0],int(v.split('.')[1]),int(v.split('.')[2])] for v in reading]
 assert e['axes']==['ordered_selection_ids','head_keys'] and e['direction']=='original H correct-minus-other in each designation stream'
 for rid in ids:
  q=orig[rid];nr=rows[rid];assert nr['split']=='test' and nr['source_condition']=='H'
  for stream in ['clean','corrupt']:
   st=nr['streams'][stream];honest,opposite=(q['target'],q['distractor']) if stream=='clean' else (q['distractor'],q['target'])
   assert st['honest_word']==honest and st['opposite_word']==opposite and st['prompt']==q[stream+'_prompt']
   t=list(tok.encode(st['prompt'],add_special_tokens=False));assert t==st['tokens'] and st['readout']==len(t)-1
   for word,key in [(honest,'honest_token'),(opposite,'opposite_token')]:
    ext=list(tok.encode(st['prompt']+' '+word,add_special_tokens=False));assert ext[:-1]==t and len(ext)==len(t)+1 and st[key]==ext[-1]
   assert st['expected_token']==st['honest_token']
 clean=np.asarray(e['clean_dla'],dtype=float);corrupt=np.asarray(e['corrupt_dla'],dtype=float)
 assert clean.shape==corrupt.shape==(100,len(heads)) and np.isfinite(clean).all() and np.isfinite(corrupt).all()
 rankings=[]
 for j,key in enumerate(heads):
  both=int(np.sum((clean[:,j]>0)&(corrupt[:,j]>0)));mean=float(np.mean(clean[:,j]));rankings.append({'key':key,'clean_mean':mean,'clean_positive_count':int(np.sum(clean[:,j]>0)),'corrupt_positive_count':int(np.sum(corrupt[:,j]>0)),'both_positive_count':both,'n_rows':100,'candidate':mean>0 and both*4>=300})
 rankings.sort(key=lambda q:(-q['clean_mean'],tuple(q['key'])))
 for rank,q in enumerate(rankings,1):q['rank']=rank
 removed=[q['key'] for q in rankings if q['candidate']];remain=[q for q in full if q not in removed]
 assert g['screen']['rankings']==rankings and g['screen']['removed_keys']==removed and g['screen']['remaining_keys']==remain and g['minus']==remain
 assert g['screen']['duplicate_group']==g['duplicate_group']==(not removed) and g['screen']['threshold']==.75 and g['descriptive']==(task=='sdr_v2')
 assert all(key in remain for key in full if key[0]=='mlp')
 bids=f['bank_ids'];assert bids==p['source_ids']==sorted(bids) and len(bids)==len(set(bids))==p['n_instances']==400
 assert set(bids)=={rid for rid,q in rows.items() if q['split'] in ['train','validation']} and not set(bids)&all_assessment
 all_banks.update(bids);assert p['source_condition']=='H' and p['source']=='pooled' and p['splits']==['train','validation'] and p['n_keys']==20
 assert p['semantics']=='original H train+validation, both streams, all unpadded tokens, equal-token fp32 pooling'
 assert [z['instance_id'] for z in p['provenance']]==bids
 token_count=0
 for rid,entry in zip(bids,p['provenance']):
  q=rows[rid];assert q['split'] in ['train','validation'] and q['streams']['clean']['prompt']==orig[rid]['clean_prompt'] and q['streams']['corrupt']['prompt']==orig[rid]['corrupt_prompt']
  for stream in ['clean','corrupt']:
   st=q['streams'][stream];expected=dict(q,expected_token=st['expected_token'],honest_token=st['honest_token'],opposite_token=st['opposite_token'],tokens=st['tokens'],layout=st['layout'],utility_assessment=(stream=='clean'))
   assert entry[stream]==expected
   token_count+=len(st['tokens'])
 assert p['n_tokens']==token_count
 vals=bank['values'];assert [v['key'] for v in vals]==full
 for v in vals:
  arr=np.asarray(v['value'],dtype=float);assert arr.shape==((head_dim,) if v['key'][0]=='head' else (hidden,)) and np.isfinite(arr).all()
 assert m['counts'][task]=={'selection_rows':100,'head_columns':len(heads),'bank_instances':400}
 out[task]={'selection_rows':100,'head_columns':len(heads),'raw_dla_values':clean.size+corrupt.size,'raw_dla_shape_each':[100,len(heads)],'removed_keys':removed,'remaining_count':len(remain),'full_count':len(full),'duplicate_group':g['duplicate_group'],'descriptive':g['descriptive'],'maximum_both_positive_count':max(z['both_positive_count'] for z in rankings),'bank_instances':400,'bank_stream_rows':800,'bank_tokens':token_count,'bank_keys':len(vals),'head_dimension':head_dim,'mlp_dimension':hidden,'bank_values_finite':True,'bank_numeric_means_independently_recomputed':False,'selection_rankings':rankings}
assert not all_assessment&all_selection and not all_assessment&all_banks
result={'verdict':'selection provenance and recomputed screen pass; ready for bounded assessment pilot subject to live resource/registry gates','old_design_file_sha256':FH(OLD),'new_design_file_sha256':FH(B/'design.json'),'semantic_payload_fields_exactly_equal':len(equalkeys),'only_changed_payload_fields':['commit','code_hashes'],'changed_code_files':changed,'current_code_hashes_all_match':True,'source_hashes_checked':len(d['source_hashes']),'selection_hashes_checked':len(d['selection_hashes']),'both_grader_and_protected_registries_current':True,'design_sha256':H(d),'selected_payload_sha256':H(s),'selected_file_sha256':FH(B/'selected.json'),'sidecar_sha256':FH(B/'selection_run_manifest.json'),'raw_dla_sha256':m['raw_dla_sha256'],'group_sha256':m['group_sha256'],'bank_sha256':m['bank_sha256'],'selection_commit':C,'model_revision':rev,'injected':False,'execution':ex,'slurm_state':'COMPLETED','slurm_exit':'0:0','elapsed_seconds':195,'gpu_hours':195/3600,'assessment_overlap_selection':0,'assessment_overlap_banks':0,'selection_union_count':len(all_selection),'assessment_union_count':len(all_assessment),'bank_union_count':len(all_banks),'tasks':out}
O.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['tasks','execution']},indent=2))
for task,q in out.items():print(task,{k:v for k,v in q.items() if k!='selection_rankings'})
