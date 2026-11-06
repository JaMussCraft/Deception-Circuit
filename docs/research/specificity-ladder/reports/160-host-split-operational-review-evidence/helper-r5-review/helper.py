#!/usr/bin/env python3
"""Root-only phase trigger/release producer. Import/tests have no operational effects.
No scheduler, RS writer, reservation creator, source edits, model loads or retries.
"""
from pathlib import Path
from decimal import Decimal,InvalidOperation
import argparse,hashlib,importlib,json,math,os,re,shlex,subprocess,sys,time
SOURCE='50e947bb852613e3a270082651f2bd1b7bb0c525'
R5='661d16c5f38149b4d258fa372472dd5aab57cd0afe0a131aa6b5683b735657bc'
CPU3='4875845ad3b728980c494657aac2935e29a8a215885ddc1b9bfd81f7ba2b13f9'
import cache_gate
ROOT=Path('/projects/beto/swong2/Alignment')
IMMUTABLE_FIELDS=('id','job_id','cluster','account','partition','gpus','requested_minutes','reserved_gpu_hours','source_commit','output_dir','manifest_hash')
class Rejected(RuntimeError):pass
def need(ok,msg):
 if not ok:raise Rejected(msg)
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def pairs(items):
 d={}
 for k,v in items:need(k not in d,'duplicate JSON key');d[k]=v
 return d
def decode(b):return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(Rejected('nonfinite JSON')))
def read(p):return decode(Path(p).read_bytes())
def encoded(x):return (json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
def exclusive(p,b):
 p=Path(p)
 with p.open('xb') as f:f.write(b)
def atomic_new(p,b):
 p=Path(p);pending=p.with_name(p.name+'.pending');exclusive(pending,b)
 try:os.link(pending,p)
 finally:pending.unlink()
def decimal(v):
 need(type(v) in (int,float,str),'invalid numeric type')
 try:r=Decimal(str(v))
 except InvalidOperation:raise Rejected('invalid decimal')
 need(r.is_finite() and r>=0,'invalid finite nonnegative number');return r
def construct_request(w,c,g,gsha,marker,msha,now):
 need(w['phase'] in ('bank','prefix4'),'unknown phase');need(w['job_id']==g['actual_job_id'] and w['source_commit']==SOURCE and w['bound_config_sha256']==gsha,'WAITING identity')
 need(0<=now-w['requested_at']<270,'WAITING stale/future')
 need(c['source_commit']==SOURCE and c['frozen_G3_sha256']==g['groups_file_sha256'] and c['H100_packet_manifest_sha256']==g['launch_packet_manifest_sha256']==R5 and c['packet_manifest_sha256']==CPU3,'standing/GPU binding')
 need(re.fullmatch(r'[0-9]+',g['actual_job_id']) and re.fullmatch(r'[0-9]+',c['standing_CPU_job_id']),'actual numeric jobs')
 return dict(phase=w['phase'],standing_CPU_job_id=c['standing_CPU_job_id'],standing_packet_manifest_sha256=CPU3,accepted_source_commit=SOURCE,frozen_G3_sha256=g['groups_file_sha256'],final_GPU_bound_config_sha256=gsha,H100_packet_manifest_sha256=R5,root_trigger_issued_at=now,actual_future_GPU_job_id=g['actual_job_id'],GPU_WAITING_marker_path=str(marker),GPU_WAITING_marker_sha256=msha,GPU_WAITING_requested_at=w['requested_at'])
def check_request_fresh(r,now):need(0<=now-r['root_trigger_issued_at']<=15 and r['GPU_WAITING_requested_at']<=r['root_trigger_issued_at'],'request stale/future')
def validate_complete(q,r,rsha,g,gsha,now):
 for k in ('complete','timely_window','actual_Delta_owning_guards_passed','stable_Delta_catalogues_before_after'):need(q.get(k) is True,'CPU did not complete '+k)
 need(q['status']=='PASS' and q['source_commit']==SOURCE and q['groups_file_sha256']==g['groups_file_sha256'],'CPU source/G3')
 need(q['phase']==r['phase'] and q['actual_future_GPU_job_id']==g['actual_job_id']==r['actual_future_GPU_job_id'] and q['actual_CPU_job_id']==r['standing_CPU_job_id'],'CPU phase/jobs')
 need(q['standing_packet_manifest_sha256']==CPU3 and q['H100_packet_manifest_sha256']==R5 and q['final_GPU_bound_config_sha256']==gsha and q['request_sha256']==rsha,'CPU immutable bindings')
 need(q['supervisor_finished_unix']<=q['deadline_unix'] and q['supervisor_finished_unix']<=now and now<r['GPU_WAITING_requested_at']+300,'CPU phase publication window')
 for k in ('model_loaded','GPU_admitted','freeze_executed'):need(q.get(k) is False,'unexpected CPU authority/work')
def validate_heldout(value):need(isinstance(value,dict) and value.get('sets')==[],'nonempty/unknown protected set requires full review; stop')
def validate_usage(u,status,session):
 # Fresh meter + targeted public status; never alter bookkeeping or exception state.
 need(isinstance(u,dict) and u.get('status')=='ok' and u.get('should_pause') is False,'usage unavailable/pause')
 first=status.splitlines()[0] if status.splitlines() else ''
 need((first=='session '+session or first.startswith('session '+session+' ')) and re.search(r'^freeze: none;',status,re.M),'session mismatch/frozen')
 match=re.search(r'seven-day ([0-9.]+)%',status);need(match,'cached session percentage unknown')
 weekly=u.get('weekly');need(isinstance(weekly,dict) and type(weekly.get('used_percent')) in (int,float),'invalid live percentage')
 cached=decimal(match.group(1));live=decimal(weekly['used_percent'])
 need(cached<=100 and live<=100 and live>=cached and live<99,'meter bounds, rollback or conservative99point pause')
 counters=re.search(r'session points ([0-9.]+) \(([0-9.]+) since register\); cadence ([0-9.]+); next checkpoint ([0-9]+) at \+([0-9.]+)',status)
 need(counters is not None,'unknown targeted RS counters')
 points,since,cadence,index,relative_next=map(decimal,counters.groups())
 need(cadence>0 and index>=1 and points>=since and relative_next==cadence*index and since<relative_next,'inconsistent targeted checkpoint counters')
 threshold=(points-since)+relative_next;projected=points+(live-cached)
 need(projected<threshold,'fresh usage projects to checkpoint; human acknowledgement required')
 exception=re.search(r'weekly cap exception: ([a-z_-]+) \(last observed\); captured reset ([0-9]+)',status)
 need(exception is not None,'unknown captured reset or exception')
 state=exception.group(1);old_reset=int(exception.group(2));live_reset=weekly.get('resets_at')
 need(type(live_reset) is int and live_reset>0 and old_reset>0 and state in ('active','expired'),'unknown reset or exception state')
 telemetry=re.search(r'last reading:[^\n]* at (\S+) \(([^)]*)\)',status)
 cache_read_at=telemetry.group(1) if telemetry else None;cache_label=telemetry.group(2) if telemetry else None
 checked_at=u.get('checked_at');now=time.time();cache_age=None;checked_age=None
 def parse_timestamp(value):
  import datetime
  try:
   need(isinstance(value,str),'timestamp missing')
   parsed=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
   need(parsed.tzinfo is not None and parsed.utcoffset() is not None,'timestamp timezone missing')
   epoch=parsed.timestamp();need(math.isfinite(epoch),'timestamp nonfinite');return epoch
  except (ValueError,TypeError,OverflowError,OSError):raise Rejected('invalid timestamp')
 if cache_read_at:
  try:cache_age=now-parse_timestamp(cache_read_at)
  except Rejected:pass
 if checked_at:
  try:checked_age=now-parse_timestamp(checked_at)
  except Rejected:pass
 if old_reset==live_reset:
  route='matching_reset'
  if live>=80:need(state=='active','active reset-bound exception required above80')
 else:
  route='expired_post_reset'
  need(live<80 and state=='expired' and old_reset<live_reset,'unknown/mismatched captured reset')
  need(type(now) in (int,float) and math.isfinite(now),'invalid actual time')
  cached_epoch=parse_timestamp(cache_read_at);checked_epoch=parse_timestamp(checked_at)
  need(old_reset<=cached_epoch<=checked_epoch<=now<live_reset and 0<=now-checked_epoch<=60,'post-reset timestamps invalid or stale')
 return dict(route=route,cache_read_at=cache_read_at,cache_age_seconds=cache_age,stored_freshness_label=cache_label,cache_label_authority=False,live_checked_at=checked_at,live_checked_age_seconds=checked_age,live_used_percent=str(live),cached_used_percent=str(cached),status_points=str(points),points_since_register=str(since),cadence=str(cadence),next_checkpoint_index=str(index),next_at_plus=str(relative_next),projected_points=str(projected),next_checkpoint_points=str(threshold),captured_reset=old_reset,live_reset=live_reset,exception_status=state,below_cap_no_exception_authority=route=='expired_post_reset',read_only_interfaces=True)
def validate_budget(ledger,mapping,g):
 need(not ledger.get('legacy_totals') and mapping['ledger_path']==g['canonical_ledger'],'canonical ledger only')
 rows=ledger['reservations'];entries={r['id']:r for r in rows};items=mapping['entries'];need(len(entries)==len(rows) and {e['reservation_id'] for e in items}==set(entries) and len(items)==len(entries),'mapping incomplete/duplicate')
 rounded={k:Decimal(0) for k in ('A1','A2','A3')};exact={k:Decimal(0) for k in rounded}
 for item in items:
  row=entries[item['reservation_id']];phase=item['experiment'];need(phase in rounded,'phase unknown')
  need(all(row.get(k)==item['actual_entry'].get(k) for k in IMMUTABLE_FIELDS),'immutable charge drift')
  need(row['reserved_gpu_hours']==round(row['gpus']*row['requested_minutes']/60,4)==item['original_reserved_gpu_hours'],'rounded charge invalid')
  rounded[phase]+=decimal(row['reserved_gpu_hours']);exact[phase]+=decimal(row['gpus'])*decimal(row['requested_minutes'])*60
 need(round(float(sum(rounded.values())),4)==ledger['totals']['reserved_gpu_hours'],'ledger rounded total mismatch')
 need(g['experiment_limits']=={'A1':25,'A2':60,'A3':40} and g['global_limit']==125,'phase/global caps changed')
 need(sum(rounded.values())<=125 and sum(exact.values())<=125*3600,'global cap')
 for k in rounded:need(rounded[k]<=g['experiment_limits'][k] and exact[k]<=g['experiment_limits'][k]*3600,'phase cap '+k)
 row=entries[g['reservation_id']];item=next(i for i in items if i['reservation_id']==row['id']);need(item['experiment']=='A2','owned charge not A2')
 need(row['job_id']==g['actual_job_id'] and row['cluster']=='bridges2' and row['account']==g['expected_account'] and row['partition'] in g['allowed_partitions'],'owned placement')
 need(row['source_commit']==SOURCE and Path(row['output_dir']).resolve()==Path(g['main_root']).resolve(),'owned source/output')
 need(row['gpus']==1 and row['requested_minutes']==60 and row['reserved_gpu_hours']==g['maximum_reserved_gpu_hours']==1.0 and g['exact_requested_GPU_seconds']==3600,'owned exact60min1GPUh charge')
 need(row['status'] in ('PENDING','RUNNING'),'owned reservation not pending/running')
 return {'phase_reserved':{k:str(v) for k,v in rounded.items()},'exact_requested_GPU_seconds_by_phase':{k:str(v) for k,v in exact.items()},'exact_requested_GPU_seconds_total':str(sum(exact.values())),'all_original_charges_retained':True}
def call(argv,**kw):return subprocess.run(argv,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=25,**kw)
def physical(g,virtual):
 rel=Path(virtual).relative_to(ROOT);need('..' not in rel.parts and Path(virtual).is_absolute(),'remote namespace traversal');return str(Path(g['physical_Alignment_root'])/rel)
def inspection_program(payload):
 return "\n".join([
  "import json,hashlib,subprocess,os", "from pathlib import Path", "p=json.loads("+repr(json.dumps(payload))+")",
  "h=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()",
  "r={'files':{x:(h(x) if Path(x).is_file() else None) for x in p['files']},'waiting_sha256':h(p['waiting']),'release_exists':Path(p['final']).exists(),'pending_exists':Path(p['final']+'.pending').exists(),'raw_scontrol':subprocess.check_output(['scontrol','show','job',p['job'],'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC'))}",
  "print(json.dumps(r))", ""])
def remote_publish_program(payload):
 return "\n".join([
  "import json,hashlib,os,time,subprocess,re,datetime", "from pathlib import Path", "p=json.loads("+repr(json.dumps(payload))+")",
  "h=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()",
  "raw=subprocess.check_output(['scontrol','show','job',p['job'],'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC'))",
  "f=dict(x.split('=',1) for x in raw.split() if '=' in x)",
  "assert f['JobId']==p['job'] and f['JobState']=='RUNNING' and f['Account']==p['account'] and f['QOS']=='gpu' and f['Partition']=='GPU-shared'",
  "assert '('+str(os.getuid())+')' in f['UserId'] and f['NumNodes']=='1' and f['NumCPUs']=='4' and f['Requeue']=='0' and f['Restarts']=='0' and f['TimeLimit'] in ('01:00:00','1:00:00','60:00')",
  "t=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)",
  "assert t.get('gres/gpu')=='1' and (t.get('gres/gpu:h100-80')=='1' or f.get('TresPerNode')=='gres:gpu:h100-80:1')",
  "m=re.fullmatch(r'([0-9]+(?:[.][0-9]+)?)([KMGT]?)',t['mem']);assert m is not None",
  "memory=float(m.group(1))*{'':1,'K':1024,'M':1024**2,'G':1024**3,'T':1024**4}[m.group(2)];assert memory>=64*1024**3",
  "end=datetime.datetime.strptime(f['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp();deadline=min(end,p['initial_end_epoch'])",
  "assert p['phase'] in ('bank','prefix4') and time.time()<deadline-p['finish_reserve_seconds']",
  "assert p['phase']!='prefix4' or deadline-time.time()>=p['score_floor_seconds']",
  "assert h(p['pending'])==p['sha'] and h(p['waiting'])==p['waiting_sha'] and not Path(p['final']).exists()",
  "now=time.time();assert now<p['expiry'] and now<deadline-p['finish_reserve_seconds']",
  "assert p['phase']!='prefix4' or deadline-now>=p['score_floor_seconds']",
  "os.link(p['pending'],p['final']);Path(p['pending']).unlink()",
  "print(json.dumps({'published':True,'sha256':h(p['final']),'actual_scontrol':raw,'deadline_epoch':deadline}))", ""])
class Transport:
 def __init__(self,b,g):self.b=b;self.g=g
 def remote(self,script):return decode(call(self.b['ssh_argv']+['python3 -'],input=script).stdout)
 def inspect(self,paths,waiting,final):
  payload={'files':paths,'waiting':waiting,'final':final,'job':self.g['actual_job_id']}
  return self.remote(inspection_program(payload))
 def fetch(self,remote,local):call(['rsync','-rl','--no-perms','--no-times','-e',shlex.join(self.b['rsync_ssh_argv']),'--',self.b['dtn_host']+':'+remote,str(local)])
 def stage(self,files,work):
  tree=work/'transfer-tree';tree.mkdir();names=[]
  for route,body in sorted(files.items()):
   rel=Path(route).relative_to(ROOT);p=tree/rel;p.parent.mkdir(parents=True,exist_ok=True);exclusive(p,body);names.append(str(rel))
  listing=work/'transfer-files.txt';exclusive(listing,(''.join(n+'\n' for n in names)).encode())
  # DTN parent directories must be created through login; create only exact parents.
  parents=sorted({str(Path(physical(self.g,p)).parent) for p in files})
  self.remote("import json\nfrom pathlib import Path\nfor p in json.loads("+repr(json.dumps(parents))+"):Path(p).mkdir(parents=True,exist_ok=True)\nprint('{}')\n")
  call(['rsync','-rl','--no-perms','--no-times','--checksum','--files-from='+str(listing),'-e',shlex.join(self.b['rsync_ssh_argv']),'--',str(tree)+'/',self.b['dtn_host']+':'+self.g['physical_Alignment_root']+'/'])
 def publish(self,local,final,waiting,waiting_sha,expiry,initial_end_epoch=None):
  self.fetch_upload(local,final+'.pending')
  body=read(local)
  payload={'pending':final+'.pending','final':final,'sha':sha(local),'waiting':waiting,'waiting_sha':waiting_sha,'expiry':expiry,'job':self.g['actual_job_id'],'account':self.g['expected_account'],'phase':body.get('phase'),'initial_end_epoch':initial_end_epoch if initial_end_epoch is not None else expiry,'finish_reserve_seconds':self.g.get('finish_reserve_seconds',300),'score_floor_seconds':self.g.get('score_lease_floor_seconds',1950)}
  return self.remote(remote_publish_program(payload))
 def cache_check(self):
  need(Path(cache_gate.__file__).resolve()==Path(__file__).resolve().parent/'cache_gate.py','exact reviewed cache gate origin')
  ref=self.b['remote_model_cache_reference'];need(ref['sha256']==cache_gate.REFERENCE_SHA,'accepted cache reference pin')
  full=physical(self.g,self.g['model_cache_proof']);need(self.g['model_cache_proof_sha256']==cache_gate.FULL_PROOF_SHA,'original complete weight proof pin')
  script=Path(cache_gate.__file__).read_text()+"\nprint(json.dumps(check_cache("+repr(ref['path'])+","+repr(full)+","+repr(self.g['physical_HF_cache'])+")))\n"
  return self.remote(script)
 def fetch_upload(self,local,remote):call(['rsync','-rl','--no-perms','--no-times','-e',shlex.join(self.b['rsync_ssh_argv']),'--',str(local),self.b['dtn_host']+':'+remote])
def gpu_facts(raw,g):
 f=dict(x.split('=',1) for x in raw.split() if '=' in x);t=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
 need(f.get('JobId')==g['actual_job_id'] and f.get('JobState')=='RUNNING' and f.get('Account')==g['expected_account']=='cis260382p' and f.get('Partition')=='GPU-shared' and f.get('QOS')=='gpu','actual GPU placement')
 need(f.get('NumCPUs')=='4' and f.get('NumNodes')=='1' and f.get('Requeue')=='0' and f.get('Restarts')=='0' and f.get('TimeLimit') in ('01:00:00','1:00:00','60:00'),'actual GPU resource/deadline')
 need(t.get('gres/gpu')=='1' and (t.get('gres/gpu:h100-80')=='1' or f.get('TresPerNode')=='gres:gpu:h100-80:1'),'typed H100 allocation')
 mem=t['mem'];scale={'K':1024,'M':1024**2,'G':1024**3,'T':1024**4};need(decimal(mem[:-1])*scale[mem[-1]]>=64*1024**3,'actual GPU hostmemory');return f
def usage(b,work,label):
 u=decode(call(['/u/swong2/.local/bin/codex-usage','--pause-at',str(b['usage_pause_percent'])]).stdout)
 status=call(['/u/swong2/.local/bin/research-session','status','--session',b['session']]).stdout;projection=validate_usage(u,status,b['session']);exclusive(work/(label+'-usage.json'),encoded({'live':u,'session_status':status,'projection':projection,'checked_unix':time.time()}))
def check_manifest(path,expected):
 path=Path(path);need(sha(path)==expected,'packet manifest changed')
 for name,h in read(path).items():need(sha(path.parent/name)==h,'packet member changed: '+name)
def verify_runtime_pins(b,g,c):
 need(sha(b['gpu_config']['path'])==b['gpu_config']['sha256'] and sha(b['standing_config']['path'])==b['standing_config']['sha256'],'bound config changed')
 check_manifest(Path(b['gpu_packet'])/'manifest.json',R5)
 check_manifest(Path(b['standing_packet'])/'implementation-manifest.json',CPU3)
 need(c['base_parameters_sha256']=='12e1e370d176c09b8f8287c0b772bad16fcffae4ba9a9839e9f3420ef0314c4f' and sha(c['base_parameters'])==c['base_parameters_sha256'],'accepted CPU base parameters changed')
 for key in ('input_manifest','delta_G3_receipt','bridges_G3_receipt','model_cache_proof'):need(sha(g[key])==g[key+'_sha256'],'accepted bound proof changed')
def load_bindings(path,digest):
 need(sha(path)==digest,'root helper bindings SHA');b=read(path);package=Path(__file__).resolve().parent;need(sha(package/'manifest.json')==b['helper_manifest_sha256'],'reviewed helper manifest');
 for name,h in read(package/'manifest.json')['files_sha256'].items():need(sha(package/name)==h,'helper packet changed')
 g=read(b['gpu_config']['path']);c=read(b['standing_config']['path']);need(sha(b['gpu_config']['path'])==b['gpu_config']['sha256'] and sha(b['standing_config']['path'])==b['standing_config']['sha256'],'final configs changed')
 need(g['commit']==SOURCE and g['launch_packet_manifest_sha256']==R5 and c['packet_manifest_sha256']==CPU3 and c['H100_packet_manifest_sha256']==R5,'accepted source/packets')
 need(g['independent160_accepted'] is True and g['maximum_minutes']==60 and g['exact_requested_GPU_seconds']==3600,'unaccepted/unbound GPU config')
 need(sha(Path(b['gpu_packet'])/'manifest.json')==R5 and sha(Path(b['standing_packet'])/'implementation-manifest.json')==CPU3,'packet manifests')
 for parent,name in [(Path(b['gpu_packet']),'manifest.json'),(Path(b['standing_packet']),'implementation-manifest.json')]:
  for n,h in read(parent/name).items():need(sha(parent/n)==h,'packet member changed')
 need(Path(b['state_directory']).is_relative_to(ROOT),'root state must preserve original namespace')
 need(0<b['usage_pause_percent']<=99,'conservative99point ceiling cannot be raised')
 need(g['canonical_ledger']==str(ROOT/'Deception-Circuit/docs/research/specificity-ladder/ledger.json'),'canonical ledger route')
 expected_catalogues={str(base/'docs/research'/n) for base in (ROOT/'Deception-Circuit',Path(g['worktree'])) for n in ('held_out.json','directions.json')}
 need(len(g['minimum_registry_paths'])==4 and set(g['minimum_registry_paths'])==expected_catalogues,'exact current catalogue routes')
 need(g['groups_file_sha256']=='c3095b10aac09a23ee35e4620402581b0407623d1e111a2407a691f60f599de4','accepted G3')
 for name in ('input_manifest','delta_G3_receipt','bridges_G3_receipt','model_cache_proof'):
  need(Path(g[name]).is_relative_to(ROOT) and sha(g[name])==g[name+'_sha256'],'root-local exact proof reference '+name)
 need(sha(g['source_plan'])==g['source_plan_sha256'] and sha(g['groups'])==g['groups_file_sha256'],'source-plan/groups bytes')
 need(not any('HostName=' in x for x in b['rsync_ssh_argv']),'login HostName override must not redirect DTN')
 need(not Path(b['state_directory']).resolve().is_relative_to(Path(c['evidence_output']).resolve()) and not Path(c['evidence_output']).resolve().is_relative_to(Path(b['state_directory']).resolve()),'helper state must not overlap immutable CPU evidence')
 need(b['ssh_argv'][0]=='ssh' and b['rsync_ssh_argv'][0]=='ssh' and b['dtn_host']=='b2dtn','explicit approved SSH/DTN transport')
 return b,g,c
class Producer:
 def __init__(self,b,g,c,phase):self.b=b;self.g=g;self.c=c;self.phase=phase;self.transport=Transport(b,g);self.work=Path(b['state_directory'])/g['actual_job_id']/phase
 def waiting_paths(self):
  virtual=Path(self.b['GPU_execution_output'])/('WAITING-'+self.phase+'.json');final=Path(self.b['GPU_release_directory'])/(self.g['actual_job_id']+'-'+self.phase+'.json');return physical(self.g,virtual),physical(self.g,final)
 def inspect(self,paths):
  waiting,final=self.waiting_paths();x=self.transport.inspect(paths,waiting,final);gpu_facts(x['raw_scontrol'],self.g);need(not x['release_exists'] and not x['pending_exists'],'phase already released/pending; no renewal');return x
 def trigger(self):
  self.work.mkdir(parents=True,exist_ok=False);verify_runtime_pins(self.b,self.g,self.c);usage(self.b,self.work,'trigger')
  waiting,final=self.waiting_paths();marker=self.work/'fetched-GPU-WAITING.json';self.transport.fetch(waiting,marker);w=read(marker);observed=self.inspect([]);need(observed['waiting_sha256']==sha(marker),'actual fetched WAITING changed')
  import datetime
  initial_facts=gpu_facts(observed['raw_scontrol'],self.g);initial_gpu_end=datetime.datetime.strptime(initial_facts['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()
  ready=Path(self.c['evidence_output'])/'READY.json';q=read(ready);need(q['CPU_job_id']==self.c['standing_CPU_job_id'] and q['source_commit']==SOURCE and q['config_sha256']==self.b['standing_config']['sha256'] and q['packet_manifest_sha256']==CPU3,'standing actual READY')
  cpu_raw=call(['scontrol','show','job',self.c['standing_CPU_job_id'],'-o']).stdout;f=dict(x.split('=',1) for x in cpu_raw.split() if '=' in x);need(f['JobId']==self.c['standing_CPU_job_id'] and f['JobState']=='RUNNING' and f['Account'].endswith('-cpu') and f['NumCPUs']=='4','standing CPU not running')
  if self.phase=='prefix4':
   bank=read(self.work.parent/'bank/trigger-record.json');need(bank['actual_GPU_job_id']==self.g['actual_job_id'] and bank['GPU_config_sha256']==self.b['gpu_config']['sha256'],'sticky bank/prefix binding')
  verify_runtime_pins(self.b,self.g,self.c)
  r=construct_request(w,self.c,self.g,self.b['gpu_config']['sha256'],marker,sha(marker),time.time());check_request_fresh(r,time.time())
  request=Path(self.c['request_directory'])/(self.phase+'.json');atomic_new(request,encoded(r));exclusive(self.work/'trigger-record.json',encoded({'actual_GPU_job_id':self.g['actual_job_id'],'GPU_config_sha256':self.b['gpu_config']['sha256'],'request':str(request),'request_sha256':sha(request),'marker':str(marker),'marker_sha256':sha(marker),'CPU_READY_sha256':sha(ready),'actual_GPU_scontrol':observed['raw_scontrol'],'actual_CPU_scontrol':cpu_raw,'initial_GPU_end_epoch':initial_gpu_end}))
  return {'triggered':True,'request':str(request),'phase':self.phase}
 def publish(self):
  need(self.work.is_dir(),'trigger required first');verify_runtime_pins(self.b,self.g,self.c);exclusive(self.work/'publish-once.claim',encoded({'claimed_unix':time.time()}));usage(self.b,self.work,'publish-start')
  record=read(self.work/'trigger-record.json');request_path=Path(record['request']);need(sha(request_path)==record['request_sha256'],'request changed');r=read(request_path);marker=Path(record['marker']);need(sha(marker)==record['marker_sha256'],'fetched WAITING changed')
  phase_dir=Path(self.c['evidence_output'])/self.phase;complete_path=phase_dir/'COMPLETE.json'
  while not complete_path.exists():
   need(not (phase_dir/'FAILED.json').exists() and not (Path(self.c['evidence_output'])/('FAILED-'+self.phase+'.json')).exists(),'actual CPU phase failed; no retry')
   need(time.time()<r['GPU_WAITING_requested_at']+270,'CPU COMPLETE missing before accepted publication margin')
   time.sleep(.2)
  qraw=complete_path.read_bytes();q=decode(qraw);validate_complete(q,r,record['request_sha256'],self.g,self.b['gpu_config']['sha256'],time.time())
  cpu_files={str(path):path.read_bytes() for path in phase_dir.iterdir() if path.is_file()}
  need(cpu_files[str(complete_path)]==qraw and sha_bytes(cpu_files[str(phase_dir/'guard-result.json')])==q['guard_result_sha256'] and sha_bytes(cpu_files[str(phase_dir/'request.json')])==record['request_sha256'],'immutable child/request evidence')
  run=read(phase_dir/'child-execution.json');need(run['exit_code']==0 and run['term_sent_at'] is None and run['timely'] is True,'child incomplete/late')
  rows=q['catalogues'];need(len(rows)==4 and {x['virtual_path'] for x in rows}==set(self.g['minimum_registry_paths']),'complete catalogue closure')
  snapshot={};mutable=set()
  for row in rows:
   route=row['virtual_path'];body=Path(route).read_bytes();need(sha_bytes(body)==row['sha256'],'Delta catalogue changed since actual CPU guard')
   if route.endswith('/held_out.json'):validate_heldout(decode(body))
   snapshot[route]=body;mutable.add(route)
  for row in q['catalogue_capture_files']:need(sha(row['captured_bytes_path'])==row['sha256'],'CPU catalogue snapshot changed')
  runtime=Path(self.g['runtime']);need(sha(self.g['snapshot'])==self.g['snapshot_sha256'],'source snapshot changed');source=read(self.g['snapshot'])
  need(source['source_commit']==SOURCE and Path(source['runtime_root'])==runtime and len(source['source_sha256'])==511 and len(source['input_links'])==4 and not source['source_code_symlinks'],'exact source identity')
  expected_files=set(source['source_sha256']);expected_links=set(source['input_links']);actual_files=set();actual_links=set()
  for item in runtime.rglob('*'):
   rel=str(item.relative_to(runtime))
   if item.is_symlink():actual_links.add(rel)
   elif item.is_file():actual_files.add(rel)
  need(actual_files==expected_files and actual_links==expected_links and not(expected_files&expected_links),'closed511+4 source inventory')
  for name,h in source['source_sha256'].items():
   item=runtime/name;need(not Path(name).is_absolute() and '..' not in Path(name).parts and str(Path(name))==name and not item.is_symlink() and item.resolve().is_relative_to(runtime.resolve()) and sha(item)==h,'source export changed')
  for name,target in source['input_links'].items():
   item=runtime/name;need(item.is_symlink() and os.readlink(item)==target and item.exists() and item.resolve()==Path(target).resolve(),'literal source input alias')
  sys.path.insert(0,str(runtime));ar=importlib.import_module('component_analysis.a3_direction_runtime');need(Path(ar.__file__).resolve().is_relative_to(runtime.resolve()),'native normalize source fallback')
  identity=dict(purpose='A2 H100 original-H bank plus prefix4 timing',source_commit=SOURCE,groups_sha256=self.g['groups_file_sha256'],main_root=self.g['main_root'],pilot_root=self.g['pilot_root'])
  for name,module in list(sys.modules.items()):
   if name.split('.')[0] in ('component_analysis','dataset','evaluation','models','scripts','config') and getattr(module,'__file__',None):need(Path(module.__file__).resolve().is_relative_to(runtime.resolve()),'project import fallback')
  normalized=ar.normalize_ledger(self.g['mapping_origin'],identity=identity,include_envelope=False,refresh_deadline=time.time()+20)
  ledger_path=self.g['canonical_ledger'];ledger_raw=Path(ledger_path).read_bytes();need(sha_bytes(ledger_raw)==normalized['current_snapshot_sha256'],'canonical ledger changed during normalization');mapping=ar.read_object(normalized['active_mapping_reference']['path']);budget=validate_budget(decode(ledger_raw),mapping,self.g);snapshot[ledger_path]=ledger_raw;mutable.add(ledger_path)
  refs=normalized['mapping_lineage_references'];bundle_paths=set();frozen=set()
  for ref in refs:
   path=Path(ref['path']);value=ar.read_object(path);bundle_paths.add(path);frozen.add(value['ledger_snapshot_path']);bundle_paths.update(Path(x) for x in value['original_admission_paths'])
  for path in sorted(bundle_paths):
   for name in ('payload.json','COMPLETE.json'):snapshot[str(path/name)]=(path/name).read_bytes()
  for route in sorted(frozen):snapshot[route]=Path(route).read_bytes()
  # CPU proof is immutable. Composite attests current budget/transfer separately.
  for key in ('input_manifest','delta_G3_receipt','bridges_G3_receipt','model_cache_proof','source_plan'):
   snapshot[self.g[key]]=Path(self.g[key]).read_bytes()
  snapshot.update(cpu_files)
  need(complete_path.read_bytes()==qraw,'CPU COMPLETE rewritten')
  composite=dict(kind='root_composite_model_phase_preflight',complete=True,phase=self.phase,source_commit=SOURCE,groups_file_sha256=self.g['groups_file_sha256'],actual_Delta_owning_guards_passed=True,stable_Delta_catalogues_before_after=True,catalogues=rows,ledger_sha256=normalized['current_snapshot_sha256'],active_mapping_reference=normalized['active_mapping_reference'],actual_CPU_COMPLETE=dict(path=str(complete_path),sha256=sha_bytes(qraw)),actual_CPU_job_id=q['actual_CPU_job_id'],actual_GPU_job_id=self.g['actual_job_id'],budget=budget,continuous_live_Delta=False,immutable_CPU_proof_not_rewritten=True)
  actual_cache=self.transport.cache_check()
  need(actual_cache['reference_sha256']==cache_gate.REFERENCE_SHA and actual_cache['original_full_weight_proof_sha256']==cache_gate.FULL_PROOF_SHA and actual_cache['revision']==cache_gate.REVISION and actual_cache['full_weights_rehashed'] is False,'actual cache gate proof')
  actual_cache.update(actual_job_id=self.g['actual_job_id'],phase=self.phase,source_commit=SOURCE)
  cache_path=self.work/'actual-cache-check.json';exclusive(cache_path,encoded(actual_cache))
  composite['actual_per_start_cache_check']={'path':str(cache_path),'sha256':sha(cache_path)}
  composite_path=self.work/'composite-preflight.json';exclusive(composite_path,encoded(composite))
  snapshot[str(cache_path)]=cache_path.read_bytes();snapshot[str(composite_path)]=composite_path.read_bytes()
  existing=self.inspect([physical(self.g,p) for p in snapshot]);need(existing['waiting_sha256']==record['marker_sha256'],'actual WAITING changed')
  for route,body in snapshot.items():
   found=existing['files'][physical(self.g,route)]
   need(route in mutable or found is None or found==sha_bytes(body),'immutable remote original differs; do not overwrite '+route)
  self.transport.stage(snapshot,self.work)
  checked=self.inspect([physical(self.g,p) for p in snapshot]);need(checked['waiting_sha256']==record['marker_sha256'],'WAITING changed during transfer')
  need(all(checked['files'][physical(self.g,p)]==sha_bytes(body) for p,body in snapshot.items()),'actual remote transfer mismatch')
  need(all(Path(p).read_bytes()==body for p,body in snapshot.items()),'actual Delta bytes changed during transfer')
  usage(self.b,self.work,'publish-final');need(time.time()<r['GPU_WAITING_requested_at']+300,'GPU wait expired before release')
  verify_runtime_pins(self.b,self.g,self.c)
  # Final no-renewal/pin checks after all costly local work, before publication.
  need(complete_path.read_bytes()==qraw and sha(request_path)==record['request_sha256'],'immutable proof/request changed at final entry')
  need({str(p) for p in phase_dir.iterdir() if p.is_file()}==set(cpu_files),'CPU proof directory changed after COMPLETE')
  need(all(Path(p).read_bytes()==body for p,body in snapshot.items()),'actual Delta source changed at final entry')
  need(time.time()<r['GPU_WAITING_requested_at']+300,'GPU wait expired after final integrity checks')
  fields=('groups_file_sha256','snapshot_sha256','image_sha256','input_manifest_sha256','delta_G3_receipt_sha256','bridges_G3_receipt_sha256','placement_sha256','launch_packet_manifest_sha256')
  release={k:self.g[k] for k in fields};now=time.time();release.update(phase=self.phase,actual_job_id=self.g['actual_job_id'],source_commit=SOURCE,bound_config_sha256=self.b['gpu_config']['sha256'],reservation_id=self.g['reservation_id'],ledger_sha256=normalized['current_snapshot_sha256'],active_mapping_reference=normalized['active_mapping_reference'],main_root=self.g['main_root'],pilot_root=self.g['pilot_root'],issued_at=now,expires_at=now+300,bank_and_prefix4_only=True,full_scoring_admitted=False,current_usage_pass=True,delta_fresh_preflight_passed=True,delta_preflight_receipt=str(composite_path),delta_preflight_receipt_sha256=sha(composite_path),catalogues=rows)
  local=self.work/'root-release.json';exclusive(local,encoded(release));waiting,final=self.waiting_paths();published=self.transport.publish(local,final,waiting,record['marker_sha256'],min(release['expires_at'],r['GPU_WAITING_requested_at']+300),record['initial_GPU_end_epoch']);exclusive(self.work/'publication.json',encoded({'release_sha256':sha(local),'published_unix':time.time(),'remote':published,'phase':self.phase,'once_only':True,'actual_per_start_cache_check':{'path':str(cache_path),'sha256':sha(cache_path)}}));return published

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=('trigger','publish','run-phase'));ap.add_argument('--phase',required=True,choices=('bank','prefix4'));ap.add_argument('--bindings',required=True);ap.add_argument('--bindings-sha256',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args();b,g,c=load_bindings(a.bindings,a.bindings_sha256)
 if not a.execute:print(json.dumps({'status':'VALIDATED_BINDINGS_ONLY_NO_EXECUTION','action':a.action,'phase':a.phase}));return
 p=Producer(b,g,c,a.phase)
 if a.action=='run-phase':p.trigger();result=p.publish()
 else:result=getattr(p,a.action)()
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
