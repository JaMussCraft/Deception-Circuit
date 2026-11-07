"""CPU-only labeled schema graph/serializer/hash stress; NEVER an A2 result."""
import argparse,collections,copy,hashlib,json,os,resource,sys,time,traceback
from pathlib import Path
import proof_guards as g
import proof_schema as s
LABELS=dict(MODEL_LOADED=False,EFFECTS_READ=False,SYNTHETIC_SCHEMA_ONLY=True,NUMERICAL_CONTROLS_TESTED=False,GPU_ADMITTED=False)
START=time.monotonic();DEADLINE=None

def check():
 assert time.monotonic()<DEADLINE,'proof child deadline reached; incomplete'
def timed(fn):
 check();r0=resource.getrusage(resource.RUSAGE_SELF);t=time.monotonic();v=fn();r1=resource.getrusage(resource.RUSAGE_SELF);return v,dict(wall_seconds=time.monotonic()-t,user_seconds=r1.ru_utime-r0.ru_utime,system_seconds=r1.ru_stime-r0.ru_stime)
def tensor_bytes(batches):
 seen=set();total=0
 for b in batches:
  for v in vars(b).values():
   if hasattr(v,'untyped_storage'):
    st=v.untyped_storage();key=(st.data_ptr(),st.nbytes())
    if key not in seen:seen.add(key);total+=st.nbytes()
 return total

def build(p,prepared,receipt,banks,refs,limit):
 from component_analysis.ladder_tasks import task_batches
 from component_analysis.specificity_ladder import _rows
 rows=[];controls=[];mask={};pairs=collections.Counter();buffer_peak=0;staging_python_peak=0;max_raw_rows=0
 shape=receipt['model_geometry']['geometry'];keys=[('embed',0,0)]+[k for layer in range(shape['num_layers']) for k in ([('head',layer,h) for h in range(shape['num_heads'])]+[('mlp',layer,0)])]
 def domain(task,rs,ds,maps,groups,aliases,operations):
  nonlocal buffer_peak,staging_python_peak,max_raw_rows
  check();buffer_peak=max(buffer_peak,tensor_bytes(rs+ds));staging_python_peak=max(staging_python_peak,sum(sys.getsizeof(b)+sys.getsizeof(vars(b))+sum(sys.getsizeof(v) for v in vars(b).values())+s.graph_sizes(b.ids)[1]+s.graph_sizes(b.records)[1] for b in rs+ds));max_raw_rows=max(max_raw_rows,sum(len(b.ids) for b in rs)*len(groups));donors={(b.condition,b.ids[0],b.stream):b for parent in ds for b in _rows(parent)}
  for parent in rs:
   for one in _rows(parent):
    key=(one.condition,one.ids[0],one.stream);row=dict(task=one.task,instance_id=one.ids[0],condition=one.condition,stream=one.stream,expected_token=int(one.expected_token[0]),opposite_token=int(one.opposite_token[0]),honest_token=int(one.honest_token[0]));record=one.records[0]
    # Match original calibration's map transform; numerical valid/error are slots.
    m=next(m for m in maps if (m['recipient_condition'],m['recipient_id'],m['recipient_stream'])==key and (one.task in ('ioi','mmlu') or m['operation']=='item_swap'))
    if one.task!='mmlu':
     donor=donors[(m['donor_condition'],m['donor_id'],m['donor_stream'])];m=dict(m,supported=True,recipient_positions=one.readout.tolist(),donor_positions=donor.readout.tolist())
    assert m['supported'];controls.append(s.bound_control(row,m,keys,task))
  for op in operations:
   bykey={}
   for m in maps:
    if m['operation']==op:
     key=(m['recipient_condition'],m['recipient_id'],m['recipient_stream']);assert key not in bykey;bykey[key]=m
   for parent in rs:
    check()
    for one in _rows(parent):
     key=(one.condition,one.ids[0],one.stream);m=bykey.get(key);row=dict(task=one.task,instance_id=one.ids[0],condition=one.condition,stream=one.stream,expected_token=int(one.expected_token[0]),opposite_token=int(one.opposite_token[0]),honest_token=int(one.honest_token[0]))
     if op not in ('zero','h_mean','self_replay','empty'):assert m is not None
     if m is not None and m['supported'] and op not in ('zero','h_mean','self_replay','empty'):
      import torch
      donor=donors[(m['donor_condition'],m['donor_id'],m['donor_stream'])]
      if torch.equal(one.input_ids[0,one.attention_mask[0].bool()],donor.input_ids[0,donor.attention_mask[0].bool()]):m=dict(m,degenerate=True,gate_valid=False,no_op=True)
     for compute,members in groups:
      for name in aliases[compute]:
       output=s.bound_row(row,one.records[0],m,op,name,receipt['groups'][name],compute,receipt['receipt_sha256'],refs[task],one.choice_tokens is not None)
       rows.append(output);rk=(row['task'],row['instance_id'],row['condition'],row['stream'],name,op,m.get('seed') if m else None);assert rk not in mask;mask[rk]=(output['supported'],output.get('unsupported_reason'))
       if op=='h_mean':pairs[task]+=1
 for task in p.TASKS:
  check();f=prepared['designs'][task];ids=f['assessment_ids'][:limit or None];source=prepared['rows'][task];groups,aliases=p._groups_for_compute(receipt,task)
  rs=[b for c in p.a1.design.CONDITIONS for st in p.a1.design.STREAMS for b in p.a1.batches([r for r in source[c] if r['instance_id'] in ids],st,batch_size=8)];ds=[b for c in p.a1.design.CONDITIONS for st in p.a1.design.STREAMS for b in p.a1.batches(source[c],st,batch_size=8)]
  domain(task,rs,ds,[m for m in f['donors'] if m['recipient_id'] in ids],groups,aliases,receipt['operations'])
  for utility in ('ioi','mmlu'):
   ur=prepared['utility'][utility][:limit or None];ids2={r['instance_id'] for r in ur};rs=task_batches(ur,batch_size=8);ds=task_batches(prepared['utility'][utility],stream='corrupt' if utility=='ioi' else 'clean');maps=[m for m in prepared['utility'][utility+'_maps'] if m['recipient_id'] in ids2]
   domain(task,rs,ds,maps,groups,aliases,('item_swap','zero','h_mean','self_replay','empty') if utility=='ioi' else ('zero','h_mean','self_replay','empty'))
 expected=p.expected_keys(receipt,limit);positive=p.a1.positive_keys(p._prepared_domain(receipt),limit);assert set(mask)==set(expected) and len(mask)==len(rows)
 ckeys=[(x['mechanism_task'],x['task'],x['instance_id'],x['condition'],x['stream']) for x in controls];assert len(ckeys)==len(set(ckeys)) and set(ckeys)==set(positive)
 mask_sha=hashlib.sha256(json.dumps([[list(k),list(mask[k])] for k in sorted(mask)],separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
 assert mask_sha==('b3e4f01c39f5c8152683fcfb8b88acd14574e97d3354021ed5c31248fd947b6c' if limit else '73002c8b74d13947aeb9bf1f6e09d50544b549ea51ab00a50b9510bd6404ffd8')
 expected_rows,expected_controls=(2484,144) if limit else (59652,3396);assert len(rows)==expected_rows and len(controls)==expected_controls
 # Future GPU labels are unknown slots, not measured CPU/GPU execution metrics.
 execution={k:(s.FLOAT_SLOT if isinstance(v,float) else s.INT_SLOT if isinstance(v,int) else v) for k,v in banks['execution_provenance'].items()};execution.pop('bank_compute_seconds',None);execution.pop('bank_stage_seconds',None);execution.update(scoring_compute_seconds=s.FLOAT_SLOT,model_load_seconds=s.FLOAT_SLOT,scoring_stage_seconds=s.FLOAT_SLOT,memory_scope='scoring compute after model load; includes resident model',stage_time_scope='model load plus scoring compute; excludes artifact publication',slurm_job_id='X'*32,cluster='X'*64,cluster_source='SLURM_CLUSTER_NAME')
 graph=dict(kind='SYNTHETIC_SCHEMA_BOUND_NOT_AN_A2_RESULT',receipt_sha256=receipt['receipt_sha256'],bank_artifact_sha256=p.hash_content(banks),rows=rows,positive_controls=controls,expected=[list(k) for k in expected],pilot=bool(limit),limit=limit,injected=False,execution_provenance=execution,counts=dict(rows=len(rows),expected=len(expected),positive_controls=len(controls)))
 # Keep the actual validation working sets alive through encoder/hash stress.
 validation=[expected,list(mask),set(mask),ckeys,set(ckeys),positive,set(positive)]
 return graph,dict(h_mean_pairs=dict(pairs),support_reason_mask_sha256=mask_sha,maximum_current_parent_tensor_bytes=buffer_peak,maximum_parent_python_bound_bytes=staging_python_peak,maximum_score_cell_return_rows=max_raw_rows),validation

def cgroup():
 out={};job=os.environ.get('SLURM_JOB_ID','')
 for line in Path('/proc/self/cgroup').read_text().splitlines():
  fields=line.split(':',2)
  if fields[0]=='0':
   base=Path('/sys/fs/cgroup')/fields[2].lstrip('/');names=('memory.current','memory.peak','memory.events')
  elif 'memory' in fields[1].split(','):
   base=Path('/sys/fs/cgroup/memory')/fields[2].lstrip('/');names=('memory.usage_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')
  else:continue
  out['path']=str(base);out['job_scoped']=bool(job and job in str(base))
  for n in names:
   if (base/n).exists():out[n]=(base/n).read_text()
 return out

def manifest_ceiling(p,args,receipt,graph):
 provenance,binding=p._validate_grader_catalogue(receipt)
 # An explicitly synthetic shape, never a native completion manifest.
 meta=dict(kind='SYNTHETIC_MANIFEST_BOUND_NOT_A_COMPLETION',execution_commit=args.commit,a1_ancestor_commit=receipt['a1_ancestor_commit'],training_execution_commit=receipt['a2_training_execution_commit'],runtime_code_hashes=p.runtime_hashes(),group_receipt_sha256=receipt['receipt_sha256'],comparison_sha256=receipt['comparison_sha256'],source_artifacts=receipt['file_references'],registry_hashes=receipt['registry_hashes'],utility_registry_hashes=receipt['utility_registry_hashes'],grader_registry=provenance,grader_binding=binding,model_identity=receipt['model_identity'],execution=graph['execution_provenance'],payload_sha256='0'*64,counts=graph['counts'],operations=receipt['operations'],mapping='unchanged frozen explicit unpadded position maps',budget_admission='Orchestrator-owned; this artifact does not authorize GPU admission or reserve resources.')
 return sum(len(c.encode()) for c in json.JSONEncoder(sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).iterencode(meta))+1

def main():
 global DEADLINE
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--deadline-monotonic',required=True,type=float);a=ap.parse_args();DEADLINE=a.deadline_monotonic
 out=Path(a.output);assert out.is_dir();cg_initial=cgroup();g.packet(a.manifest_sha256);before,guard_before_time=timed(g.capture);g.write(out/'source-before.json',before)
 context,owning_time=timed(g.owning);p,args,prepared,selected,sidecar,receipt,banks,tokenizer=context;before_ready,guard_ready_time=timed(g.capture);assert {k:v for k,v in before.items() if k!='module_origins'}=={k:v for k,v in before_ready.items() if k!='module_origins'}
 texts={n:(g.R/'component_analysis'/n).read_text() for n in ('specificity_ladder.py','a2_pipeline.py','ladder_pipeline.py','ladder_design.py','hooks.py')};s.verify_runner_schema(texts['specificity_ladder.py']);s.verify_append_schema(texts['a2_pipeline.py']);s.verify_function_pins(texts,g.read(g.P/'native-schema-contract.json')['function_AST_sha256'])
 fixed=[];refs={}
 for task in p.TASKS:refs[task],t=timed(lambda:p.bank_reference(banks,g.G/'bank/banks.json',task));fixed.append(dict(task=task,**t))
 # Prefix is enumerated only for source event counts; no retained prefix graph survives.
 prefix_bundle,prefix_build_time=timed(lambda:build(p,prepared,receipt,banks,refs,4));prefix,pm,pv=prefix_bundle;prefix_pairs=pm['h_mean_pairs'];del prefix,pv,prefix_bundle
 bundle,full_build_time=timed(lambda:build(p,prepared,receipt,banks,refs,0));graph,meta,validation=bundle;assert sum(prefix_pairs.values())==432 and sum(meta['h_mean_pairs'].values())==10188
 (unique,no_share),walk_time=timed(lambda:s.graph_sizes(graph));context_unique,context_bound=s.graph_sizes([prepared,selected,sidecar,receipt,banks]);validation_bytes=s.graph_sizes(validation)[1]
 encoded,enc_time=timed(lambda:s.encoder_accounting(graph));compact,compact_time=timed(lambda:s.encoder_accounting(graph,compact=True));native_artifact_bound=encoded['bytes']+len(json.dumps({'sha256':'0'*64,'payload':None},sort_keys=True,allow_nan=False).encode())-4+1;manifest_bound=manifest_ceiling(p,args,receipt,graph)
 # Conservative phase union: full context incremental; no-sharing graph; all
 # validation structures; old/new parent buffers, native encoder chunks+str+UTF8;
 # allocator/interpreter baseline observed before native serialization, counted
 # separately and with a fixed declared 512MiB operational allowance.
 rss_before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
 bank_CPU_tensor_bytes=max(sum(len(v['value'])*4 for v in banks['banks'][task]['values']) for task in p.TASKS)
 max_members_bound=max(s.graph_sizes(v['members'])[1] for v in receipt['groups'].values());raw_scalar_slots=2*len(s.metric_types(True))+2;raw_row_bound=2*max(sys.getsizeof(r) for r in graph['rows'])+max_members_bound+raw_scalar_slots*max(sys.getsizeof(s.FLOAT_SLOT),sys.getsizeof(s.INT_SLOT),sys.getsizeof(s.BOOL_SLOT))+512
 raw_return_bound=meta['maximum_score_cell_return_rows']*raw_row_bound+sys.getsizeof([None]*meta['maximum_score_cell_return_rows'])
 host_bound=context_bound+no_share+validation_bytes+raw_return_bound+2*bank_CPU_tensor_bytes+2*(meta['maximum_current_parent_tensor_bytes']+meta['maximum_parent_python_bound_bytes'])+max(encoded['full_encoding_overlap_bound'],compact['full_encoding_overlap_bound'])+rss_before+512*1024**2
 assert native_artifact_bound<=2*1024**3,'native artifact bound exceeds2GiB threshold'
 assert native_artifact_bound+manifest_bound+512*1024**2<=4*1024**3,'native stage plus declared operational reserve exceeds4GiB output proposal'
 assert host_bound<=24*1024**3,'conservative incremental host accounting exceeds24GiB threshold'
 check();scratch=out/'DISPOSABLE_SYNTHETIC_SCHEMA_NOT_SCORE.json';assert not scratch.exists();space=os.statvfs(out);assert space.f_bavail*space.f_frsize>=12*1024**3,'private12GiB scratch capacity absent'
 _,scope_time=timed(lambda:p.validate_a2_scope(receipt,graph['rows'],limit=0,banks=banks,bank_path=g.G/'bank/banks.json'))
 hashes=[]
 for i in range(2):value,t=timed(lambda:p.hash_content(graph));hashes.append(dict(index=i,digest=value,diagnostic_repeat=True,**t))
 _,writer_time=timed(lambda:p.a1.write_artifact(scratch,graph));actual_bytes=scratch.stat().st_size;assert actual_bytes<=native_artifact_bound
 assert sum(x.stat().st_size for x in out.iterdir() if x.is_file())<12*1024**3
 serialization=dict(native_hash_repeated_probes=hashes,native_writer_includes_its_own_payload_hash=True,production_publication_charge_seconds=max(x['wall_seconds'] for x in hashes)+writer_time['wall_seconds'],stress_payload_hash_calls=3,production_payload_hash_calls=2,native_writer=writer_time,actual_synthetic_file_bytes=actual_bytes,analytic_native_file_ceiling=native_artifact_bound,synthetic_labels=LABELS)
 g.write(out/'serialization-measurement.json',serialization);scratch.unlink() # only this proof-owned disposable file
 micro=[];full_hash=[];prefix_hash=[]
 for task in p.TASKS:
  provenance=banks['banks'][task]['provenance'];sample=3
  def pairs(n):
   for i in range(n):check();p.hash_content(provenance);p.hash_content(provenance)
  _,t=timed(lambda:pairs(sample));forecast=t['wall_seconds']/sample*(meta['h_mean_pairs'][task]+prefix_pairs[task]);micro.append(dict(task=task,pairs=sample,forecast_full_seconds=forecast,**t))
 # Normal incomplete exit, not a fabricated extrapolated measurement.
 forecast=sum(x['forecast_full_seconds'] for x in micro);g.write(out/'provenance-microbenchmark.json',dict(samples=micro,forecast_full_seconds=forecast,remaining_seconds=DEADLINE-time.monotonic(),**LABELS))
 assert forecast*1.25+180<DEADLINE-time.monotonic(),'full counted provenance loop forecast cannot fit; incomplete proof needs root review'
 for task in p.TASKS:
  provenance=banks['banks'][task]['provenance'];count=meta['h_mean_pairs'][task]
  def exact():
   for i in range(count):check();p.hash_content(provenance);p.hash_content(provenance)
  _,t=timed(exact);full_hash.append(dict(task=task,hash_pairs=count,hash_calls=2*count,**t))
  count=prefix_pairs[task];_,t=timed(exact);prefix_hash.append(dict(task=task,hash_pairs=count,hash_calls=2*count,**t))
 # Postguards and all current metadata are mandatory, not cached passes.
 check();p._validate_live(args,receipt,prepared);p.validate_banks(receipt,prepared,banks);after,guard_after_time=timed(g.capture);assert {k:v for k,v in before_ready.items() if k!='module_origins'}=={k:v for k,v in after.items() if k!='module_origins'},'source/input/catalogue/bank changed';assert all(after['module_origins'].get(k)==v for k,v in before_ready['module_origins'].items()),'existing origin changed';g.packet(a.manifest_sha256);g.write(out/'source-after.json',after)
 peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;cg=cgroup();cgpeak=cg.get('memory.peak',cg.get('memory.max_usage_in_bytes'));assert cg.get('job_scoped') and cgpeak is not None,'job-scoped cgroup peak unavailable: incomplete proof';assert int(cgpeak)<=24*1024**3 and peak<=24*1024**3,'actual schema stress peak exceeds24GiB acceptance threshold'
 def events(c):
  if 'memory.events' in c:return {k:int(v) for k,v in (line.split() for line in c['memory.events'].splitlines())}
  return {'failcnt':int(c.get('memory.failcnt','0'))}
 initial_events=events(cg_initial);final_events=events(cg);assert all(final_events.get(k,0)==initial_events.get(k,0) for k in ('oom','oom_kill','failcnt')),'new cgroup OOM/allocation-failure event'
 full_cpu=sum(x['wall_seconds'] for x in full_hash);prefix_cpu=sum(x['wall_seconds'] for x in prefix_hash);ratio=26.584174781925647;excess=max(0.,full_cpu-prefix_cpu*ratio)
 budget_reconciliation=dict(measured_full_CPU_hash_seconds=full_cpu,measured_prefix_CPU_hash_seconds=prefix_cpu,measured_CPU_hash_growth=full_cpu/prefix_cpu,whole_core_orientation_seconds=518.3888086024672*ratio,whole_core_single_allowance_fraction=.2,measured_CPU_hash_excess_over_sameplatform_exposure_charge_seconds=excess,publication_charge_once_seconds=serialization['production_publication_charge_seconds'],combined_fixed_allowance_seconds=900,unmeasured_fixed_remainder_seconds=900-serialization['production_publication_charge_seconds'],cold_load_once_seconds=555.7060698261485,finish_seconds=300,proposed_seconds=19800,engineering_total_before_platform_decision_seconds=518.3888086024672*ratio*1.2+555.7060698261485+900+300+excess,CPU_timing_platform_host=os.uname().nodename,subtraction_from_observed_prefix518_permitted=False,resource_admission=False,qualification='CPU stress costs are platform measurements. Whole-core orientation already contains CPU; publication charged once within900, never add all hash stress again. Independent root review must resolve platform/fixed-envelope/excess and remaining margin; no GPU theorem or automatic acceptance.')
 final=dict(complete=False,status='CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR',**LABELS,source_commit='50e947bb852613e3a270082651f2bd1b7bb0c525',metadata=meta,budget_reconciliation=budget_reconciliation,full_rows=len(graph['rows']),expected_control_pairs=len(graph['positive_controls']),prefix_h_mean_pairs=prefix_pairs,full_h_mean_timing=full_hash,prefix_h_mean_timing=prefix_hash,fixed_initial_three_bank_references=fixed,native_full_scope_final_three_references=scope_time,owning_context_timing=owning_time,prefix_bound_build_timing=prefix_build_time,full_bound_build_timing=full_build_time,graph_unique_bytes=unique,graph_no_sharing_bound_bytes=no_share,context_unique_bytes=context_unique,context_no_sharing_bound_bytes=context_bound,validation_bytes_bound=validation_bytes,score_cell_raw_return_overlap_bound_bytes=raw_return_bound,task_bank_CPU_tensor_bytes=bank_CPU_tensor_bytes,encoder=encoded,canonical_encoder=compact,incremental_host_bound_bytes=host_bound,actual_peak_RSS_bytes=peak,cgroup=cg,cgroup_initial=cg_initial,guard_timings=dict(before=guard_before_time,ready=guard_ready_time,after=guard_after_time),serialization=serialization,walk_timing=walk_time,encoder_count_timing=enc_time,compact_count_timing=compact_time,elapsed_seconds=time.monotonic()-START,native_JSON_ceiling_bytes=native_artifact_bound,native_manifest_ceiling_bytes=manifest_bound,native_stage_ceiling_bytes=native_artifact_bound+manifest_bound,operational_disk_reserve_bytes=512*1024**2,required_output_free_bytes=4*1024**3,GPU_operational_admission_pending=True,source_event_table=dict(h_mean_pairs_per_prefix=432,h_mean_pairs_per_full=10188,bank_reference_calls_per_native_score=6,bank_payload_return_hash_calls_inside_native_compute=1,initial_validate_banks_before_native_compute_timer=True,full_payload_hashes_outside_native_compute=2,streamed_native_writer_calls=1,CPU_hash_times_are_platform_measurements_not_permission_to_subtract_from_prefix518=True),execution_label_constraints=dict(future_GPU_job_id_max_chars=32,cluster_max_chars=64,gpu_name_exact=banks['execution_provenance']['gpu_name']))
 g.write(out/'CHILD-REPORT.json',final)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  try:
   output=Path(sys.argv[sys.argv.index('--output')+1]);g.write(output/'FAILED-child.json',dict(complete=False,error=repr(e),traceback=traceback.format_exc(),**LABELS))
  finally:raise
