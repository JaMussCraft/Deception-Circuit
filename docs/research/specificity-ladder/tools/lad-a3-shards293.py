from pathlib import Path
import json,hashlib,base64,subprocess,shlex,time,sys,os
A=Path('/projects/beto/swong2/Alignment');W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';S=W/'.superpowers/sdd';P=S/'plan/task23-green-r8-sharded';O=S/'plan-a3/sharded-deployment293';O.mkdir(exist_ok=True)
R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def physical(p):return str(R/Path(p).relative_to(A))
def save(n,x):
 with(O/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def remote(n,code,x,timeout=60):
 a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
 r=subprocess.run(a,input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=timeout);save(n,dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()));r.check_returncode();return json.loads(r.stdout)
if sys.argv[1]=='prepare':
 assert sha(P/'source-pins.json')=='36de6e5608f1a2350992b8b31aa5d4544b3a2825aa72b1d850bbb330449734e4'
 assert sha(P/'partition.json')=='88f74d6348e24d828c34b4c9901e988a8c6564eb2ed60e614fe0c1a1e71ddc29'
 rv=S/'plan-a3/sharded-validation-review292/verdict.json';assert sha(rv)=='8adc1eca8f0c8809d0aa463b981e80250a4784eee85bc1b6b45ebfb1d4499ecf'
 c=json.loads((P/'bridges/config.template.json').read_text());rows=[]
 for r in c['files']:
  f=Path(r['virtual']);assert f.is_file() and not f.is_symlink() and f.stat().st_size==r['bytes'] and sha(f)==r['sha256'];rows.append(dict(r,physical=physical(f)))
 assert len(rows)==1133 and len(c['aliases'])==8
 for e in ['base','mgnp']:
  for i in [0,1]:
   d=O/(e+'-'+str(i));d.mkdir(exist_ok=False);root=str(d) if e=='base' else physical(d);packet=str(P) if e=='base' else physical(P)
   text='#!/bin/bash\nset -euo pipefail\nroot='+shlex.quote(root)+'\nread -r config_sha < "$root/config.sha256"\n[[ "$config_sha" =~ ^[0-9a-f]{64}$ ]]\nexec bash '+shlex.quote(packet+'/cpu.sbatch')+' "$root/config.json" "$config_sha" '+sha(P/'bridges/manifest.json')+'\n'
   (d/'dispatch.sh').write_text(text)
 save('input-inventory.json',dict(files=rows,aliases=[dict(r,physical=physical(r['virtual'])) for r in c['aliases']],host_manifest_sha256=sha(P/'bridges/manifest.json'),source_pins_sha256=sha(P/'source-pins.json'),partition_sha256=sha(P/'partition.json'),source_review_sha256=sha(rv)))
 print('prepared',len(rows),'files; host manifest',sha(P/'bridges/manifest.json'))
elif sys.argv[1]=='audit':
 code='''import sys,json,hashlib,time,os
from pathlib import Path
x=json.load(sys.stdin);good=[];missing=[];bad=[];missing_aliases=[]
for r in x['files']:
 p=Path(r['physical'])
 if not p.exists():missing.append(r);continue
 if p.is_symlink() or not p.is_file() or p.stat().st_size!=r['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:bad.append(r['physical'])
 else:good.append(r['physical'])
for r in x['aliases']:
 p=Path(r['physical'])
 if p.is_symlink():assert os.readlink(str(p))==r['literal_target'],str(p)
 elif p.exists():raise RuntimeError('nonalias collision '+str(p))
 else:missing_aliases.append(r)
print(json.dumps(dict(matched=len(good),missing=missing,mismatched=bad,aliases=len(x['aliases']),missing_aliases=missing_aliases,observed_unix=time.time())))
'''
 v=remote('remote-input-audit.json',code,json.loads((O/'input-inventory.json').read_text()),90);assert not v['mismatched'],v['mismatched'];print('matched',v['matched'],'missing',len(v['missing']),'aliases',v['aliases'])
elif sys.argv[1]=='stage':
 audit=json.loads(json.loads((O/'remote-input-audit.json').read_text())['stdout']);assert not audit['mismatched'];rows=list(audit['missing'])
 for n in ['mgnp-0/dispatch.sh','mgnp-1/dispatch.sh']:
  f=O/n;rows.append(dict(virtual=str(f),physical=physical(f),bytes=f.stat().st_size,sha256=sha(f)))
 for r in rows:
  f=Path(r['virtual']);b=f.read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'];r['base64']=base64.b64encode(b).decode()
 code='''import sys,json,hashlib,base64,time,os
from pathlib import Path
rows=json.load(sys.stdin);out=[]
for r in rows:
 p=Path(r['physical']);b=base64.b64decode(r['base64']);assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'];p.parent.mkdir(parents=True,exist_ok=True);assert not p.is_symlink()
 if p.exists():assert p.read_bytes()==b,str(p)
 else:
  with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];out.append({k:v for k,v in r.items() if k!='base64'})
print(json.dumps(dict(files=out,observed_unix=time.time())))
'''
 v=remote('stage-readback.json',code,rows,90);print('staged',len(v['files']),'source/bootstrap files')
elif sys.argv[1] in ('check','check-r2','check-r3'):
 code='''import sys,json,hashlib,subprocess,time,os
from pathlib import Path
x=json.load(sys.stdin);p=Path(x['packet']);sys.path.insert(0,str(p/'bridges'));import host
assert host.old.sha(p/'source-pins.json')==x['source'] and host.old.sha(p/'partition.json')==x['partition']
for n,h in json.loads((p/'bridges/manifest.json').read_text()).items():assert host.old.sha(p/'bridges'/n)==h
host.old.check_records(x['inventory']['files'],x['inventory']['aliases']);assert host.old.sha(host.old.IMAGE)==host.old.IMAGE_SHA;supervisor=host.supervisor;supervisor.enable_subreaper()
r=subprocess.run(['python3','-B',str(p/'bridges/host.py'),'--dry-run'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20);assert r.returncode==0,r.stderr
job=p/'jobs/job-smoke293';child=job/'child';child.mkdir(parents=True,mode=0o700,exist_ok=False);canary=job/'host-before-canary.json';canary.write_text('HOST_ONLY')
virtual=host.old.VIRT/host.PACKET_REL;vjob=virtual/'jobs/job-smoke293';vchild=vjob/'child';c=dict(environment='mgnp',output=str(vchild/'execution'));kind='v1' if Path('/sys/fs/cgroup/memory').is_dir() else 'v2';checks=[]
for stage in ['baseline','oracle','suite']:
 cmd,env=host.command(c,stage,kind,time.time()+60);cut=cmd.index(host.old.IMAGE)
 probe="from pathlib import Path;import os,json;h=Path("+repr(str(vjob/'host-before-canary.json'))+");c=Path("+repr(str(vchild))+");assert os.statvfs(h).f_flag & os.ST_RDONLY;assert not(os.statvfs(c).f_flag & os.ST_RDONLY);assert h.read_text()=='HOST_ONLY';c.joinpath("+repr('smoke-'+stage+'.json')+").write_text('child write works');print(json.dumps(dict(host_readonly=True,child_writable=True,stage="+repr(stage)+")))"
 cmd=cmd[:cut+6]+[host.old.PY,'-B','-c',probe]
 started=time.time();rr=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=25);row=dict(stage=stage,argv=cmd,exit_code=rr.returncode,stdout=rr.stdout,stderr=rr.stderr,seconds=time.time()-started);checks.append(row)
 assert rr.returncode==0,row;assert canary.read_text()=='HOST_ONLY'
 for name in ['host-before.json','baseline-terminal.json','oracle-terminal.json','suite-terminal.json']:assert not(child/name).exists()
mounts={q.name:json.loads(q.read_text()) for q in child.glob('inner-mounts-*.json')};assert len(mounts)==3
print(json.dumps(dict(source_files=len(x['inventory']['files']),aliases=len(x['inventory']['aliases']),host_python=sys.version,subreaper_enabled=True,image_sha256=host.old.IMAGE_SHA,host_dry_run=dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),stages=checks,mount_receipts=mounts,no_native_workload=True,observed_unix=time.time())))
'''
 if sys.argv[1] in ('check-r2','check-r3'):
  smoke_id='smoke293-'+sys.argv[1].split('-',1)[1]
  code=code.replace('job-smoke293','job-'+smoke_id).replace("c=dict(environment='mgnp',output=","c=dict(environment='mgnp',job_id="+repr(smoke_id)+",shard=0,output=")
 v=remote('actual-host-container-'+sys.argv[1]+'.json',code,dict(packet=physical(P),source=sha(P/'source-pins.json'),partition=sha(P/'partition.json'),inventory=json.loads((O/'input-inventory.json').read_text())),110);print('actual host/container checks passed;',v['source_files'],'files,',len(v['stages']),'isolated stage mount checks')

elif sys.argv[1]=='scheduler':
 import concurrent.futures
 def argv(e,i,account,partition):
  d=O/(e+'-'+str(i));q=str if e=='base' else physical
  a=['sbatch','--parsable','--account='+account,'--partition='+partition,'--nodes=1','--ntasks=1','--cpus-per-task='+('2' if e=='base' else '18'),'--mem=32G','--time=01:20:00','--no-requeue','--export=ALL,CUDA_VISIBLE_DEVICES=,A3_HOST_PYTHON='+('/sw/external/python/anaconda3/bin/python3.9' if e=='base' else '/usr/bin/python3'),'--chdir='+q(P),'--job-name=lad-A3-'+e+'-'+str(i),'--output='+q(d/'slurm-%j.log'),q(d/'dispatch.sh')]
  a.insert(2,'--constraint=projects' if e=='base' else '--qos=rm');return a
 options=[(a,p) for a in ['beto-delta-cpu','bimc-delta-cpu','bjhz-delta-cpu'] for p in ['cpu','cpu-preempt']]
 def check(choice):
  a=argv('base',0,*choice);r=subprocess.run(a[:1]+['--test-only']+a[1:],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=25);return dict(account=choice[0],partition=choice[1],argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time())
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(check,options))
 save('delta-scheduler-previews.json',rows)
 for r in rows:print(r['account'],r['partition'],r['exit_code'],r['stderr'].strip())
 a=argv('mgnp',0,'cis260361p','RM-shared')
 code='''import sys,json,subprocess,time
x=json.load(sys.stdin);a=x['argv'];r=subprocess.run(a[:1]+['--test-only']+a[1:],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=25);print(json.dumps(dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time())));sys.exit(r.returncode)
'''
 v=remote('bridges-scheduler-preview.json',code,dict(argv=a));print('bridges',v['stderr'].strip())
 save('bridges-submission-argv.json',[argv('mgnp',i,'cis260361p','RM-shared') for i in [0,1]])
elif sys.argv[1]=='submit':
 e=sys.argv[2];i=int(sys.argv[3]);assert e in ('base','mgnp') and i in (0,1);name=e+'-'+str(i);d=O/name
 assert not (d/'submission.json').exists()
 if e=='mgnp':a=json.loads((O/'bridges-submission-argv.json').read_text())[i]
 else:
  r=[r for r in json.loads((O/'delta-scheduler-previews.json').read_text()) if r['account']=='beto-delta-cpu' and r['partition']=='cpu-preempt'][0];assert r['exit_code']==0;a=[v.replace('/base-0/','/'+name+'/').replace('lad-A3-base-0','lad-A3-'+name) for v in r['argv']]
 a.insert(1,'--hold')
 if e=='mgnp':
  code="import sys,json,subprocess,time;x=json.load(sys.stdin);r=subprocess.run(x,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);print(json.dumps(dict(argv=x,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time())));sys.exit(r.returncode)"
  v=remote(name+'/submission.json',code,a,45)
 else:
  r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);v=dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time());save(name+'/submission.json',v);r.check_returncode()
 job=v['stdout'].strip().split(';')[0];assert job.isdigit();save(name+'/job.json',dict(job_id=job,cluster='delta' if e=='base' else 'bridges2'))
 r=subprocess.run(['research-session','job','add',str(A/'Deception-Circuit/docs/research/specificity-ladder'),'--job-id',job,'--cluster','delta' if e=='base' else 'bridges2','--status','PENDING','--timeout-min','60'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);save(name+'/registration.json',dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));r.check_returncode();print(name,job,r.stdout)
elif sys.argv[1] in ('bind','bind-r2'):
 e=sys.argv[2];i=int(sys.argv[3]);assert e in ('base','mgnp') and i in (0,1);name=e+'-'+str(i);d=O/name;j=json.loads((d/'job.json').read_text());job=j['job_id'];c=json.loads((P/'bridges/config.template.json').read_text());iv=json.loads((O/'input-inventory.json').read_text())
 c.update(status='ROOT_BOUND_A3_SHARDED_VALIDATION',environment=e,shard=i,job_id=job,cluster=j['cluster'],cpus=2 if e=='base' else 18,account='beto-delta-cpu' if e=='base' else 'cis260361p',partition='cpu-preempt' if e=='base' else 'RM-shared',qos='beto-delta-cpu' if e=='base' else 'rm',output=str(P/('jobs/job-'+job+'/child/execution')),physical_root=str(A) if e=='base' else str(R))
 c['files']=[dict(r,physical=r['virtual'] if e=='base' else r['physical']) for r in iv['files']];c['aliases']=[dict(r,physical=r['virtual'] if e=='base' else r['physical']) for r in iv['aliases']]
 if (d/'config.json').exists():assert json.loads((d/'config.json').read_text())==c
 else:save(name+'/config.json',c)
 h=sha(d/'config.json')
 if (d/'config.sha256').exists():assert (d/'config.sha256').read_text()==h+'\n'
 else:
  with(d/'config.sha256').open('x') as f:f.write(h+'\n')
 code='''import sys,json,subprocess,hashlib,base64,os,time
from pathlib import Path
x=json.load(sys.stdin);d=Path(x['directory']);job=x['job'];rows=[]
for n,b64 in x['payload'].items():
 p=d/n;b=base64.b64decode(b64)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 rows.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
raw=subprocess.check_output(['scontrol','show','job',job,'-o'],universal_newlines=True,timeout=15);f=dict(v.split('=',1) for v in raw.split() if '=' in v);c=x['config']
assert f['JobId']==job and f['JobState']=='PENDING' and f['Reason']=='JobHeldUser' and f['RunTime']=='00:00:00'
assert f['Account']==c['account'] and f['Partition']==c['partition'] and f['QOS']==c['qos']
assert f['NumCPUs']==f['CPUs/Task']==str(c['cpus']) and f['NumTasks']=='1' and f['NumNodes'] in ('1','1-1')
t=dict(v.split('=',1) for v in f.get('ReqTRES',f.get('TRES','')).split(',') if '=' in v)
assert t['cpu']==str(c['cpus']) and t['mem'] in ('32G','32768M') and not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items())
assert f['TimeLimit'] in ('01:20:00','1:20:00') and f['Requeue']==f['Restarts']=='0'
assert f['Command']==str(d/'dispatch.sh') and f['WorkDir']==x['packet'] and f['StdOut']==str(d/('slurm-'+job+'.log'))
root=Path(x['jobroot']);root.mkdir(parents=True,mode=0o700,exist_ok=True);assert root.stat().st_uid==os.getuid() and not list(root.iterdir())
spool=d/'submitted-script.sh'
if not spool.exists():subprocess.check_call(['scontrol','write','batch_script',job,str(spool)],stdout=subprocess.DEVNULL,timeout=15)
assert spool.read_bytes()==(d/'dispatch.sh').read_bytes()
sys.path.insert(0,str(Path(x['packet'])/'bridges'));import host
host.check_source(c)
print(json.dumps(dict(job_id=job,config_sha256=hashlib.sha256((d/'config.json').read_bytes()).hexdigest(),bootstrap_sha256=hashlib.sha256(spool.read_bytes()).hexdigest(),files=rows,allocation=f,raw_allocation=raw,jobroot=str(root),empty_jobroot=True,own_uid=os.getuid(),source_files_checked=len(c['files']),aliases_checked=len(c['aliases']),observed_unix=time.time())))
'''
 q=str if e=='base' else physical;x=dict(directory=q(d),job=job,config=c,packet=q(P),jobroot=q(P/('jobs/job-'+job)),payload={n:base64.b64encode((d/n).read_bytes()).decode() for n in ['config.json','config.sha256']})
 if e=='mgnp':v=remote(name+('/binding-r2.json' if sys.argv[1]=='bind-r2' else '/binding.json'),code,x,90)
 else:
  r=subprocess.run(['/sw/external/python/anaconda3/bin/python3.9','-B','-c',code],input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=90);save(name+('/binding-r2.json' if sys.argv[1]=='bind-r2' else '/binding.json'),dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()));r.check_returncode();v=json.loads(r.stdout)
 assert v['config_sha256']==h;print(name,job,'bound',h,'source files',v['source_files_checked'])

elif sys.argv[1]=='stage-control':
 f=P/'transport-inventory.json';b=f.read_bytes();row=dict(virtual=str(f),physical=physical(f),sha256=sha(f),bytes=len(b),base64=base64.b64encode(b).decode())
 save('control-manifest-inventory.json',{k:v for k,v in row.items() if k!='base64'})
 code="import sys,json,base64,hashlib,os;from pathlib import Path;x=json.load(sys.stdin);p=Path(x['physical']);b=base64.b64decode(x['base64']);assert hashlib.sha256(b).hexdigest()==x['sha256'];assert not p.exists();f=p.open('xb');f.write(b);f.flush();os.fsync(f.fileno());f.close();assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'];print(json.dumps(dict(path=str(p),sha256=x['sha256'],bytes=len(b))))"
 print(remote('control-manifest-stage.json',code,row))

elif sys.argv[1]=='stage-aliases':
 audit=json.loads(json.loads((O/'remote-input-audit.json').read_text())['stdout']);rows=audit['missing_aliases']
 code="import sys,json,os,time;from pathlib import Path;rows=json.load(sys.stdin);out=[]\nfor r in rows:\n p=Path(r['physical']);assert not p.exists() and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True);os.symlink(r['literal_target'],str(p));assert p.is_symlink() and os.readlink(str(p))==r['literal_target'];out.append(r)\nprint(json.dumps(dict(aliases=out,observed_unix=time.time())))"
 v=remote('alias-stage-readback.json',code,rows);print('staged',len(v['aliases']),'exact literal aliases')
