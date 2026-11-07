from pathlib import Path
import json,hashlib,subprocess,shlex,sys,time
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/sharded-deployment293';P=S/'plan/task23-green-r8-sharded';R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def physical(p):return str(R/Path(p).relative_to(A))
def save(n,x):
 with(O/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
name=sys.argv[2];assert name in ('base-0','base-1','mgnp-0','mgnp-1');d=O/name;remote=name.startswith('mgnp');q=physical if remote else str;job=json.loads((d/'job.json').read_text())['job_id']
code='''import sys,json,hashlib,subprocess,time,os,stat
from pathlib import Path
x=json.load(sys.stdin);d=Path(x['directory']);p=Path(x['packet']);c=json.loads((d/'config.json').read_text());job=c['job_id']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(d/'config.json')==x['config'] and (d/'config.sha256').read_text()==x['config']+'\\n'
assert sha(p/'source-pins.json')==x['source'] and sha(p/'partition.json')==x['partition'] and sha(p/'transport-inventory.json')==x['control'] and sha(p/'bridges/manifest.json')==x['manifest']
for n,h in json.loads((p/'bridges/manifest.json').read_text()).items():assert sha(p/'bridges'/n)==h
sys.path.insert(0,str(p/'bridges'));import host
host.check_source(c)
if c['environment']=='mgnp':assert sha(host.old.IMAGE)==host.old.IMAGE_SHA
root=Path(x['root']);mode=stat.S_IMODE(root.stat().st_mode)
assert root.is_dir() and root.resolve()==root and all(not z.is_symlink() for z in [root]+list(root.parents))
assert root.stat().st_uid==os.getuid() and mode&0o777==0o700 and not list(root.iterdir()) and not(root/'child').exists()
assert sha(d/'dispatch.sh')==x['dispatch']
spool=d/'final-submitted-script.sh';assert not spool.exists();subprocess.check_call(['scontrol','write','batch_script',job,str(spool)],stdout=subprocess.DEVNULL,timeout=15);assert sha(spool)==x['dispatch']
raw=subprocess.check_output(['scontrol','show','job',job,'-o'],universal_newlines=True,timeout=15);f=dict(v.split('=',1) for v in raw.split() if '=' in v)
assert f['JobId']==job and f['JobState']=='PENDING' and f['Reason']=='JobHeldUser' and f['RunTime']=='00:00:00'
assert f['Account']==c['account'] and f['Partition']==c['partition'] and f['QOS']==c['qos'] and f['Command']==str(d/'dispatch.sh') and f['WorkDir']==str(p)
assert f['NumCPUs']==f['CPUs/Task']==str(c['cpus']) and f['NumTasks']=='1' and f['NumNodes'] in ('1','1-1')
t=dict(v.split('=',1) for v in f.get('ReqTRES',f.get('TRES','')).split(',') if '=' in v)
assert t['cpu']==str(c['cpus']) and t['mem'] in ('32G','32768M') and not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items())
assert f['TimeLimit'] in ('01:20:00','1:20:00') and f['Requeue']==f['Restarts']=='0'
assert '('+str(os.getuid())+')' in f['UserId']
print(json.dumps(dict(job_id=job,cluster=c['cluster'],config_sha256=x['config'],root=dict(path=str(root),mode=oct(mode),owner_uid=root.stat().st_uid,own_uid=os.getuid(),empty=True,canonical=True,no_symlink_ancestry=True,child_absent=True),source_files_checked=len(c['files']),aliases_checked=len(c['aliases']),dispatch_sha256=x['dispatch'],spool_sha256=sha(spool),control_inventory_sha256=x['control'],allocation=f,raw_allocation=raw,observed_unix=time.time())))
'''
x=dict(directory=q(d),packet=q(P),root=q(P/('jobs/job-'+job)),config=sha(d/'config.json'),source=sha(P/'source-pins.json'),partition=sha(P/'partition.json'),control=sha(P/'transport-inventory.json'),manifest=sha(P/'bridges/manifest.json'),dispatch=sha(d/'dispatch.sh'))
if sys.argv[1]=='check':
 if remote:a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
 else:a=['/sw/external/python/anaconda3/bin/python3.9','-B','-c',code]
 r=subprocess.run(a,input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=100);save(name+'/final-readback.json',dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()));assert r.returncode==0,r.stderr;v=json.loads(r.stdout);print(name,job,'final check passed',v['root'])
elif sys.argv[1]=='release':
 vpath=S/'plan-a3/sharded-deployment293-review/verdict.json';v=json.loads(vpath.read_text());assert v['verdict']=='ACCEPT_FOUR_EXISTING_HELD_CPU_RELEASES_AFTER_FINAL_ROOT_LIVE_CHECKS'
 binding=next(r for r in v['jobs'] if r['job_id']==job);assert x['config']==binding['config_sha256'] and x['dispatch']==binding['spool_sha256'];assert x['source']==v['source_pins_sha256'] and x['partition']==v['partition_sha256'];assert sha(O/'deployment-manifest.json')==v['deployment_manifest_sha256']
 r=json.loads((d/'final-readback.json').read_text());assert r['exit_code']==0;assert time.time()-r['observed_unix']<600;assert not(d/'root-release.json').exists()
 code=code.replace("spool=d/'final-submitted-script.sh'", "spool=d/'release-submitted-script.sh'")
 before=code.rsplit('print(json.dumps(',1)[0]
 code=before+'''def write(p,z):
 with p.open('x') as stream:json.dump(z,stream,indent=2);stream.write('\\n');stream.flush();os.fsync(stream.fileno())
write(d/'release-intent.json',dict(job_id=job,config_sha256=x['config'],source_pins_sha256=x['source'],deployment_review_sha256=x['review'],raw_allocation=raw,root_mode=oct(mode),source_files_checked=len(c['files']),observed_unix=time.time()))
r=subprocess.run(['scontrol','release',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
result=dict(job_id=job,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time());write(d/'release.json',result);print(json.dumps(result));sys.exit(r.returncode)
'''
 x['review']=sha(vpath)
 if remote:a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
 else:a=['/sw/external/python/anaconda3/bin/python3.9','-B','-c',code]
 r=subprocess.run(a,input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=100);save(name+'/root-release.json',dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,review_sha256=x['review'],observed_unix=time.time()));assert r.returncode==0,r.stderr;print(name,job,'released once',r.stdout)
