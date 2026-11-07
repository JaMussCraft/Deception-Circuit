"""Observational audit+cProfile of one actual source refresh; no guard substitutions."""
import os,sys,pathlib,json,time,resource,datetime,subprocess,hashlib,cProfile,pstats,io,collections
O=pathlib.Path(__file__).resolve().parents[2];E=pathlib.Path(__file__).parent
pointer=json.loads((O/'evidence/source-pointer.json').read_text());B=pathlib.Path(pointer['runtime_root']);C=pointer['source_commit'];W=O.parents[2]
if len(sys.argv)==1:
 env=dict(os.environ);env.update(json.loads((O/'evidence/benchmark-command.json').read_text())['environment'])
 env.update(W=str(W),B=str(B),O=str(O),C=C)
 for owner in ('mask','edge'):
  cmd=['/u/swong2/.conda/envs/mgnp/bin/python',str(pathlib.Path(__file__).resolve()),owner];started=time.time()
  receipt=dict(command=cmd,cwd=str(B),environment={k:env.get(k) for k in ('PYTHONPATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES')},started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),timeout_seconds=600,source_only=True)
  with (E/(owner+'.log')).open('w') as log:
   try:r=subprocess.run(cmd,cwd=B,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600);receipt['exit_code']=r.returncode
   except subprocess.TimeoutExpired:receipt['exit_code']=124
  receipt.update(elapsed_seconds=time.time()-started,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  (E/(owner+'-command.json')).write_text(json.dumps(receipt,indent=2)+'\n')
  print(json.dumps(receipt),flush=True)
  if receipt['exit_code']:raise SystemExit(receipt['exit_code'])
 raise SystemExit(0)
owner=sys.argv[1];assert owner in ('mask','edge') and not os.environ.get('SLURM_JOB_ID')
assert os.environ['PYTHONPATH']==str(B)
from types import SimpleNamespace
from component_analysis import a3_direction_runtime as authority,ladder_pipeline as ladder
from component_analysis import a3_mask_pipeline as mask,a3_edge_pipeline as edge
args=SimpleNamespace(commit=C,registry=[str(W/'docs/research/held_out.json')],design=str(O/'canonical/design.json'),prepared=str(O/owner/'prepared'),work_dir=str(O/owner),stage='pilot',seed=None,arm=None,task=None,group=None,chunk_size=4,steps=8,measure_stage='fit')
def observe(fn):
 usage=resource.getrusage(resource.RUSAGE_SELF);start=time.perf_counter();utc=datetime.datetime.now(datetime.timezone.utc).isoformat();value=fn();after=resource.getrusage(resource.RUSAGE_SELF)
 return value,dict(started_utc=utc,wall_seconds=time.perf_counter()-start,user_cpu_seconds=after.ru_utime-usage.ru_utime,system_cpu_seconds=after.ru_stime-usage.ru_stime,host_peak_bytes=after.ru_maxrss*1024)
def cold():
 if owner=='mask':
  args._mask_source_started=time.perf_counter();prepared=authority.read_object(args.prepared);mask._live_mask(prepared,args,inventory=None);state=args._mask_source_context;return prepared,None,state
 args._source_started=time.perf_counter();design=ladder.read_artifact(args.design);prepared=authority.read_object(args.prepared);state=edge._make_edge_source_state(prepared,design,args);assert state is not None;return prepared,design,state
(prepared,design,state),cold_time=observe(cold)
def refresh():
 if owner=='mask':return mask._live_mask(prepared,args,inventory=None)[1]
 return state.refresh(owner='edge',bound_inputs={'prepared':prepared,'design':design},registry_paths=args.registry,scope=edge._edge_source_scope(args))
# The audit observer neither replaces a callable nor changes its return/arguments.
active=False;events=[]
def audit(event,args):
 if not active or event not in ('open','os.listdir','os.scandir'):return
 path=args[0] if args else None
 if not isinstance(path,(str,bytes)):return
 frame=sys._getframe(1);stack=[]
 for _ in range(22):
  if frame is None:break
  stack.append((frame.f_code.co_filename,frame.f_code.co_name));frame=frame.f_back
 events.append(dict(event=event,path=os.fsdecode(path),mode=str(args[1]) if len(args)>1 else None,stack=stack))
sys.addaudithook(audit);prof=cProfile.Profile();active=True;prof.enable()
try:evidence,refresh_time=observe(refresh)
finally:prof.disable();active=False
assert evidence['commit']==C and evidence['injected'] is False and evidence['registry_hashes'] and evidence['grader_registry']
prof.dump_stats(str(E/(owner+'.pstats')))
for order in ('cumulative','tottime'):
 stream=io.StringIO();pstats.Stats(prof,stream=stream).strip_dirs().sort_stats(order).print_stats(55);(E/(owner+'-'+order+'.txt')).write_text(stream.getvalue())
rows=[];stats=pstats.Stats(prof)
for (filename,line,function),(primitive,calls,self_time,cumulative,callers) in stats.stats.items():rows.append(dict(file=filename,line=line,function=function,primitive_calls=primitive,calls=calls,self_seconds=self_time,cumulative_seconds=cumulative))
(E/(owner+'-functions.json')).write_text(json.dumps(sorted(rows,key=lambda r:-r['cumulative_seconds']),indent=2)+'\n')
physical={};opens=[]
for event in events:
 if event['event']!='open':continue
 p=pathlib.Path(event['path']);p=p if p.is_absolute() else B/p
 try:st=p.stat()
 except OSError:continue
 if not p.is_file():continue
 key=str(st.st_dev)+':'+str(st.st_ino)
 is_hash=any(function=='file_hash' for _,function in event['stack'])
 section=('witness' if any(function=='_check_file_witness' for _,function in event['stack']) else 'grader' if any(function=='grader_registry' for _,function in event['stack']) else 'protection' if any(function=='refresh' and filename.endswith('a3_source_validation.py') for filename,function in event['stack']) else 'other')
 row=dict(path=str(p),resolved=str(p.resolve()),physical=key,bytes=st.st_size,is_hash=is_hash,section=section);opens.append(row)
 entry=physical.setdefault(key,dict(bytes=st.st_size,paths=[],opens=0,hash_opens=0,sections=[]));entry['opens']+=1;entry['hash_opens']+=int(is_hash)
 if str(p) not in entry['paths']:entry['paths'].append(str(p))
 if section not in entry['sections']:entry['sections'].append(section)
section_summary={}
for section in sorted(set(row['section'] for row in opens)):
 selected=[row for row in opens if row['section']==section];section_summary[section]=dict(opens=len(selected),hash_opens=sum(row['is_hash'] for row in selected),logical_open_bytes=sum(row['bytes'] for row in selected),hash_bytes=sum(row['bytes'] for row in selected if row['is_hash']),unique_physical_bytes=sum(physical[k]['bytes'] for k in {row['physical'] for row in selected}))
# Static witness physical overlap and lexical ancestor candidates, computed AFTER timing.
witness_files=[]
for root,tree in zip(state._witness.paths,state._witness.identities):
 for row in tree:
  if row[0]=='file':witness_files.append(dict(root=root,path=row[1],physical=str(row[2][0])+':'+str(row[2][1]),bytes=row[2][3]))
ancestors=[str(parent) for path in state._witness.paths for parent in [pathlib.Path(path)]+list(pathlib.Path(path).parents)]
report=dict(owner=owner,commit=C,python=sys.executable,source_only=True,execution_authority_exercised=False,model_loaded=False,cold=cold_time,profiled_refresh=refresh_time,profiler_overhead='cProfile and read-only Python audit event collection enabled for the single refresh; compare clean measurements in parent evidence',events=events,opens=opens,physical_files=physical,sections=section_summary,logical_open_bytes=sum(row['bytes'] for row in opens),unique_physical_open_bytes=sum(row['bytes'] for row in physical.values()),hash_open_bytes=sum(row['bytes'] for row in opens if row['is_hash']),witness_files=witness_files,witness_logical_bytes=sum(row['bytes'] for row in witness_files),witness_unique_physical_bytes=sum({row['physical']:row['bytes'] for row in witness_files}.values()),witness_root_count=len(state._witness.paths),lexical_ancestor_candidates_with_repetition=len(ancestors),lexical_ancestor_candidate_unique=len(set(ancestors)),path_operation_counts={r['function']:r['calls'] for r in rows if r['file'].endswith('pathlib.py') and r['function'] in ('stat','lstat','resolve','is_symlink','exists','is_file','glob','iterdir')},hostname=os.uname().nodename,thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')})
(E/(owner+'-profile.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('owner','cold','profiled_refresh','sections','logical_open_bytes','unique_physical_open_bytes','witness_logical_bytes','witness_unique_physical_bytes','path_operation_counts')},indent=2))
