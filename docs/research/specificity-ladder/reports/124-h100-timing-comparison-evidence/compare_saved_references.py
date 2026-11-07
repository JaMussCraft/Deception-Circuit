"""Read-only saved JSON comparison; no framework, model, scheduler or remote calls."""
from pathlib import Path
import collections,csv,datetime,hashlib,json,math,statistics,traceback
W=Path(__file__).resolve().parents[5];B=W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102';OUT=Path(__file__).parent
PLAN=W/'.superpowers/sdd/plan-a2-bridges2/reference-check/predeclared-comparison.json'
NAMES=('config.json','active_nodes.json','results.json','history.json','run_manifest.json');PREFIX=Path('outputs/_training_specificity_ladder/a2-h200')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pairs(items):
 result={}
 for k,v in items:
  if k in result:raise ValueError('Duplicate JSON key: '+k)
  result[k]=v
 return result
def load(path):return json.loads(path.read_text(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON '+x)))
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(name,value):
 with (OUT/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def quantify(values):
 assert values and all(math.isfinite(x) for x in values);absolute=sorted(abs(x) for x in values)
 def quantile(p):
  i=(len(absolute)-1)*p/100;lo=math.floor(i);hi=math.ceil(i);return absolute[lo]+(absolute[hi]-absolute[lo])*(i-lo)
 return dict(count=len(values),nonzero=sum(x!=0 for x in values),signed_mean=statistics.fmean(values),mean_absolute=statistics.fmean(absolute),RMS=math.sqrt(statistics.fmean(x*x for x in values)),absolute_p50=quantile(50),absolute_p95=quantile(95),absolute_p99=quantile(99),maximum_absolute=max(absolute))
inputs={str(PLAN):sha(PLAN)};plan=load(PLAN);assert plan['scope']['actual_epochs']==20 and plan['scope']['seed']==42
completion_path=B/'remote-deployment/50147300-completion.json';completion=load(completion_path);assert completion['job_id']=='50147300' and completion['complete'] is True and completion['scientific_seed'] is False
transfer=load(B/'transfer-manifest.json');slots={row['virtual_path']:row for row in transfer['files']}
assert sha(B/'transfer-manifest.json')==sha(B/'remote-deployment/transfer-manifest.json')
frozen_root=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime';snapshot_path=frozen_root.parent/'snapshot.json';snapshot=load(snapshot_path);assert sha(snapshot_path)=='eb5ca854a7157529095ab820252a246f114250144120c6fc66de98bed9733918';assert sha(frozen_root.parent/'application.tar')==snapshot['archive_sha256']=='1a4e6397bb5924f22fc548fb8899a925a58f0b3640730a2602300e7e8c045ac6'
assert len(snapshot['source_files_sha256'])==207
for rel,value in snapshot['source_files_sha256'].items():assert sha(frozen_root/rel)==value
paired=[];trajectory=[];integrity={};comparisons={};masks_result={};times={};all_pretraining_exact=True
try:
 for arm in ('D','I'):
  old_path=W/f'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-{arm}-seed42.json';new_path=B/f'returned-receipts/sdr_v2-{arm}-seed42.json';old=load(old_path);new=load(new_path);inputs[str(old_path)]=sha(old_path);inputs[str(new_path)]=sha(new_path)
  for receipt in (old,new):
   assert receipt['status']=='success' and receipt['errors']==[] and receipt['exit_code']==0 and receipt['test_runner_injected'] is False and receipt['test_clock_injected'] is False
   assert receipt['purpose']=='timing-only' and receipt['actual_epochs']==20 and receipt['planned_epochs']==500 and receipt['seed']==42 and receipt['condition']==arm and receipt['task']=='sdr_v2'
  identity_keys=('task','condition','seed','model','purpose','actual_epochs','planned_epochs','fleet_ready','cohort','source_commit','execution_commit','build_hash','build_manifest_sha256','frozen_config_sha256','resolved_config_sha256','dataset_config_sha256','selected_ids','counts','max_seq_length','granularity','recipient_condition','legacy_deception_condition','config_file_sha256','build_manifest_file_sha256','source_hashes')
  assert all(old[k]==new[k] for k in identity_keys)
  assert old['argv'][2:]==new['argv'][2:] and Path(new['argv'][1]).resolve()==(frozen_root/'train.py').resolve()
  assert new['environment']['SLURM_JOB_ID']=='50147300' and new['environment']['SLURM_CLUSTER_NAME']=='bridges2' and new['gpu_count']==1 and new['gpu_devices']==['NVIDIA H100 80GB HBM3, 81559 MiB']
  for rel,value in new['source_hashes'].items():assert sha(frozen_root/rel)==value
  data={};artifacts={}
  for side,receipt in [('H200',old),('H100',new)]:
   assert set(receipt['artifacts'])==set(NAMES)==set(receipt['artifact_sha256']);out=Path(receipt['output_dir']);suffix=out.relative_to(PREFIX);assert len(suffix.parts)==1
   data[side]={};artifacts[side]={}
   for name in NAMES:
    declared=Path(receipt['artifacts'][name]);assert declared==out/name and '..' not in declared.parts
    actual=(W/declared) if side=='H200' else (B/'returned-native'/suffix/name)
    assert actual.is_file() and not actual.is_symlink()
    if side=='H100':assert actual.resolve().is_relative_to((B/'returned-native').resolve())
    assert sha(actual)==receipt['artifact_sha256'][name];inputs[str(actual)]=sha(actual);artifacts[side][name]=dict(declared_virtual_path=str(declared),actual_path=str(actual),sha256=sha(actual),bytes=actual.stat().st_size,receipt_hash_matches=True);data[side][name]=load(actual)
   native=data[side]['run_manifest.json'];assert native['manifest_hash']==digest({k:v for k,v in native.items() if k!='manifest_hash'})
   assert native['argv']==receipt['argv'][1:] and native['config_sha256']==receipt['artifact_sha256']['config.json'] and native['model_revision']=='0e9e39f249a16976918f6564b8830bc894c89659'
   assert native['execution_commit']==receipt['execution_commit']=='6bd8bf5334f2e83613a129d2fcfeacf83e762191' and native['build_source_commit']==receipt['source_commit']
   assert native['slurm_job_id']==receipt['environment']['SLURM_JOB_ID']
   created=datetime.datetime.fromisoformat(native['created']);assert datetime.datetime.fromisoformat(receipt['started_utc'])<=created<=datetime.datetime.fromisoformat(receipt['finished_utc'])
   for name,value in native['code_sha256'].items():assert sha(frozen_root/name)==value
   for name,value in native['dataset_files'].items():assert sha(Path(name))==value and slots[name]['sha256']==value
   h=data[side]['history.json']['node'];assert h['epochs']==list(range(1,21)) and [e['epoch'] for e in h['evals']]==[0,10,20]
   assert all(len(h[k])==20 and all(math.isfinite(x) for x in h[k]) for k in ('loss','kl','task','sparsity','lr'))
   for stage,value,ids in [('baseline',data[side]['results.json']['baseline'],receipt['selected_ids']['test']),('node_eval',data[side]['results.json']['node_eval'],receipt['selected_ids']['test'])]+[(f'epoch{e["epoch"]}',e,receipt['selected_ids']['validation']) for e in h['evals']]:
    rows=value['outputs'];assert len(ids)==len(set(ids)) and [r['instance_id'] for r in rows]==ids
    assert all(math.isfinite(value[k]) for k in ('accuracy','logit_diff','kl_div','exact_match'))
    assert all(r['logit_difference']==r['logit_target']-r['logit_distractor'] and all(math.isfinite(r[k]) for k in ('logit_difference','logit_target','logit_distractor')) for r in rows)
    assert sum(r['logit_difference']>0 for r in rows)/len(rows)==value['accuracy'] and sum(r['logit_difference'] for r in rows)/len(rows)==value['logit_diff']
   assert data[side]['results.json']['edge_eval'] is None
  old_native=data['H200']['run_manifest.json'];new_native=data['H100']['run_manifest.json'];changed=[k for k in set(old_native)|set(new_native) if old_native.get(k)!=new_native.get(k)];assert set(changed)<=set(('argv','created','cwd','host','slurm_job_id','manifest_hash'))
  assert old_native['software']==new_native['software'] and old_native['dataset_files']==new_native['dataset_files'] and old_native['code_sha256']==new_native['code_sha256']
  # Relocated live-registry aliases bind the same real files and bytes, not a changed protected set.
  normalized=[]
  for receipt in (old,new):
   values={}
   for name,value in receipt['registry_sha256'].items():
    path=Path(name);assert sha(path)==value;values[str(path.resolve())]=value
   normalized.append(values)
  assert normalized[0]==normalized[1]
  executed=load(B/f'remote-deployment/50147300-{arm}-execution.json');assert executed['arm']==arm and executed['exit_code']==0 and executed['job_id']=='50147300' and executed['cosine_T_max']==20
  completed_cell=next(c for c in completion['cells'] if c['arm']==arm)
  assert completed_cell['actual_receipt_sha256']==sha(new_path) and set(completed_cell)-set(executed)=={'actual_receipt_sha256'} and all(completed_cell[k]==v for k,v in executed.items())
  old_log=W/f'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-{arm}-seed42.stdout-stderr.log';new_log=B/f'returned-receipts/sdr_v2-{arm}-seed42.stdout-stderr.log'
  import re
  for receipt,log in ((old,old_log),(new,new_log)):
   text=log.read_text();assert float(re.findall(r'Node pruning time:\s*([0-9.]+)s',text)[-1])==receipt['pruning_seconds'];assert float(re.findall(r'Overall peak:\s*([0-9.]+) GB',text)[-1])==receipt['peak_memory_gb'];inputs[str(log)]=sha(log)
  integrity[arm]=dict(passed=True,identity_keys_equal=list(identity_keys),argv_after_script_exact=True,native_config_full_equal=data['H200']['config.json']==data['H100']['config.json'],registry_aliases_normalize_to_same_files=True,changed_native_manifest_fields=sorted(changed),native_runtime_software=new_native['software'],native_model_revision=new_native['model_revision'],native_host=new_native['host'],native_job=new_native['slurm_job_id'],artifacts=artifacts,exact_scientific_file_equality={name:artifacts['H200'][name]['sha256']==artifacts['H100'][name]['sha256'] for name in NAMES if name!='run_manifest.json'})
  assert integrity[arm]['native_config_full_equal']
  stages=[]
  for label in ('baseline','node_eval'):stages.append((label,data['H200']['results.json'][label],data['H100']['results.json'][label],label=='baseline'))
  for e0,e1 in zip(data['H200']['history.json']['node']['evals'],data['H100']['history.json']['node']['evals']):stages.append((f'validation_epoch{e0["epoch"]}',e0,e1,e0['epoch']==0))
  comparisons[arm]={}
  for label,a,b,pretraining in stages:
   delta={key:[] for key in plan['paired_numeric_fields']};choices=[];decisions=[];ties=[]
   for row0,row1 in zip(a['outputs'],b['outputs']):
    assert set(row0)==set(row1)
    for key in set(row0)-set(plan['paired_numeric_fields'])-{'chosen_word'}:assert row0[key]==row1[key]
    key=[row0[k] for k in plan['row_join_key']];d={field:row1[field]-row0[field] for field in delta}
    for field in delta:delta[field].append(d[field])
    if row0['chosen_word']!=row1['chosen_word']:choices.append(key)
    sign0=(row0['logit_difference']>0)-(row0['logit_difference']<0);sign1=(row1['logit_difference']>0)-(row1['logit_difference']<0)
    if sign0!=sign1 or (row0['logit_difference']>0)!=(row1['logit_difference']>0):decisions.append(key)
    if row0['logit_difference']==0 or row1['logit_difference']==0:ties.append(key)
    paired.append(dict(arm=arm,stage=label,pretraining=pretraining,key=key,H200=row0,H100=row1,H100_minus_H200=d,decoded_choice_equal=row0['chosen_word']==row1['chosen_word'],strict_pairwise_decision_equal=(row0['logit_difference']>0)==(row1['logit_difference']>0),margin_sign_equal=sign0==sign1))
   stats={field:quantify(values) for field,values in delta.items()};exact=all(s['nonzero']==0 for s in stats.values()) and not choices and not decisions
   if pretraining:all_pretraining_exact &= exact
   comparisons[arm][label]=dict(rows=len(a['outputs']),pretraining=pretraining,all_metadata_equal=True,exact_saved_fields=exact,paired_fields=stats,changed_decoded_choice_count=len(choices),changed_decoded_choice_IDs=choices,changed_sign_or_strict_decision_count=len(decisions),changed_sign_or_strict_decision_IDs=decisions,tie_row_IDs=ties,aggregate_H200={k:v for k,v in a.items() if k!='outputs'},aggregate_H100={k:v for k,v in b.items() if k!='outputs'},aggregate_deltas={k:b[k]-a[k] for k in ('accuracy','logit_diff','kl_div','exact_match')})
  h0=data['H200']['history.json']['node'];h1=data['H100']['history.json']['node'];assert h0['lr']==h1['lr']
  for i,epoch in enumerate(h0['epochs']):trajectory.append(dict(arm=arm,epoch=epoch,**{side+'_'+field:h[field][i] for side,h in [('H200',h0),('H100',h1)] for field in ('loss','kl','task','sparsity','lr')},**{'delta_'+field:h1[field][i]-h0[field][i] for field in ('loss','kl','task','sparsity','lr')}))
  comparisons[arm]['trajectory_deltas']={field:quantify([b-a for a,b in zip(h0[field],h1[field])]) for field in ('loss','kl','task','sparsity','lr')}
  active0=data['H200']['active_nodes.json'];active1=data['H100']['active_nodes.json'];masks_result[arm]={}
  for side,active in [('H200',active0),('H100',active1)]:
   masks=active['masks'];assert set(masks)=={'attention_heads','mlp_blocks'} and len(masks['attention_heads'])==32 and len(masks['mlp_blocks'])==32
   assert all(len(bits)==32 and all(type(bit) is int and bit in (0,1) for bit in bits) for bits in masks['attention_heads'].values()) and all(type(bit) is int and bit in (0,1) for bit in masks['mlp_blocks'])
   for layer,bits in masks['attention_heads'].items():assert active['active_heads'][layer]==[i for i,b in enumerate(bits) if b]
   assert active['active_mlps']==[i for i,b in enumerate(masks['mlp_blocks']) if b]
  for kind in ('attention_heads','mlp_blocks'):
   def members(active):
    x=active['masks'][kind];return {(int(layer),i) for layer,bits in x.items() for i,b in enumerate(bits) if b} if isinstance(x,dict) else {(i,) for i,b in enumerate(x) if b}
   a=members(active0);b=members(active1);union=a|b
   masks_result[arm][kind]=dict(H200_count=len(a),H100_count=len(b),intersection=len(a&b),union=len(union),Jaccard=len(a&b)/len(union) if union else 1.,Hamming=len(a^b),changed_members=sorted(map(list,a^b)),per_layer_Hamming={str(layer):sum((item in a)!=(item in b) for item in ({(layer,i) for i in range(32)} if kind=='attention_heads' else {(layer,)})) for layer in range(32)})
  masks_result[arm]['raw_active_nodes_exact']=active0==active1
  times[arm]=dict(H200={k:old[k] for k in ('total_seconds','pruning_seconds','peak_memory_gb')},H100={k:new[k] for k in ('total_seconds','pruning_seconds','peak_memory_gb')},H100_apptainer_wrapper_seconds=executed['elapsed_seconds'],H100_minus_H200={k:new[k]-old[k] for k in ('total_seconds','pruning_seconds','peak_memory_gb')},H100_pruning_seconds_per_epoch=new['pruning_seconds']/20,H200_pruning_seconds_per_epoch=old['pruning_seconds']/20,derived_process_only_full500_seconds=new['total_seconds']-new['pruning_seconds']+new['pruning_seconds']*500/20,full500_extrapolation_is_authorization=False)
 accounting_path=B/'terminal-accounting.txt';raw=accounting_path.read_text();lines=[x.split('|') for x in raw.strip().splitlines()];account={row[0]:dict(zip(lines[0],row)) for row in lines[1:]};job=account['50147300'];assert job['State']=='COMPLETED' and job['ExitCode']=='0:0' and job['ElapsedRaw']=='481'
 total_h100=sum(x['H100']['total_seconds'] for x in times.values());total_h200=sum(x['H200']['total_seconds'] for x in times.values())
 with (OUT/'paired-rows.jsonl').open('x') as stream:
  for row in paired:stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
 with (OUT/'trajectories.csv').open('x',newline='') as stream:
  writer=csv.DictWriter(stream,fieldnames=list(trajectory[0]));writer.writeheader();writer.writerows(trajectory)
 put('mask-comparison.json',masks_result)
 result=dict(status='exact_no_observed_drift' if all_pretraining_exact else 'observed_drift_hold_for_review',integrity_passed=True,predeclared_plan=dict(path=str(PLAN),sha256=sha(PLAN),changed_after_observation=False),scope=dict(arms=['D','I'],seed=42,actual_epochs=20,planned_epochs=500,cosine_T_max=20,train=187,validation=187,test=952,paired_rows=len(paired),paired_selected_logit_values=len(paired)*3,pretraining_paired_rows=sum(row['pretraining'] for row in paired)),integrity=integrity,comparisons=comparisons,masks=masks_result,timing=dict(arms=times,job_accounting=account,H100_child_process_total_seconds=total_h100,H200_child_process_total_seconds=total_h200,job_elapsed_seconds=int(job['ElapsedRaw']),allocation_minus_H100_child_seconds=int(job['ElapsedRaw'])-total_h100,source_protection_container_startup_gaps_and_exit_are_not_attributed_to_pruning=True,observations_not_cold_host_guarantees=True),limits=plan['unavailable_claims'],no_tolerance_change=True,no_efficacy_selection=True,no_fleet_or_full500_acceptance_claim=True,no_models_or_forwards_or_remote_or_jobs=True,input_sha256=inputs)
 inputs[str(completion_path)]=sha(completion_path);inputs[str(accounting_path)]=sha(accounting_path);inputs[str(B/'transfer-manifest.json')]=sha(B/'transfer-manifest.json');put('comparison.json',result)
 print(json.dumps(dict(status=result['status'],paired_rows=len(paired),pretraining_paired_rows=result['scope']['pretraining_paired_rows'],all_stages_exact=all(v['exact_saved_fields'] for c in comparisons.values() for k,v in c.items() if k!='trajectory_deltas'),masks_exact={arm:x['raw_active_nodes_exact'] for arm,x in masks_result.items()},timing=result['timing']),indent=2))
except BaseException as error:
 put('comparison-integrity-failure.json',dict(status='integrity_blocker',error=repr(error),traceback=traceback.format_exc(),inputs=inputs));raise
