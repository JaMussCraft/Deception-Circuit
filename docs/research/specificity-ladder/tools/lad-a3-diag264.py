from pathlib import Path
import json,hashlib,base64,subprocess,shlex,time,sys
A=Path('/projects/beto/swong2/Alignment');W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';S=W/'.superpowers/sdd';P=S/'plan-a3/diagnostic-transport254-r3';O=S/'plan-a3/diagnostic-deployment264';O.mkdir(exist_ok=True)
R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment');M='ded29ff237b436215d80db6408a878d513b79ffbb0ba7c4ba10fd2c7b391ba2a'
def sha(b):return hashlib.sha256(b).hexdigest()
def physical(p):return str(R/Path(p).relative_to(A))
def save(n,x):
 with(O/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def remote(n,code,x,timeout=60):
 a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
 r=subprocess.run(a,input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=timeout);save(n,dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()));r.check_returncode();return json.loads(r.stdout)
if sys.argv[1]=='stage':
 assert sha((P/'manifest.json').read_bytes())==M
 c=json.loads((P/'config.template.json').read_text());c['status']='ROOT_BOUND_A3_DIAGNOSTIC_PARTIAL';save('config.json',c)
 files=[P/n for n in json.loads((P/'manifest.json').read_text())]+[P/'manifest.json',P/'test_transport.py',O/'config.json']
 files += [Path(x['virtual']) for x in c['files'] if '/green-timeout-diagnosis253/' in x['virtual']]
 rows=[]
 for p in files:
  b=p.read_bytes();rows.append(dict(physical=physical(p),bytes=len(b),sha256=sha(b),base64=base64.b64encode(b).decode()))
 save('stage-inventory.json',[{k:v for k,v in x.items() if k!='base64'} for x in rows])
 code='''import json,sys,hashlib,base64,os,time
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
 v=remote('stage-readback.json',code,rows);print('staged',len(v['files']),'config',sha((O/'config.json').read_bytes()))
elif sys.argv[1]=='check':
 code='''import json,sys,time,unittest,subprocess,os
from pathlib import Path
x=json.load(sys.stdin);sys.path.insert(0,x['packet']);import host,test_transport
assert host.old.sha(Path(x['packet'])/'manifest.json')==x['manifest']
for n,h in json.loads((Path(x['packet'])/'manifest.json').read_text()).items():assert host.old.sha(Path(x['packet'])/n)==h
assert host.old.sha(x['config'])==x['config_sha'];c=json.loads(Path(x['config']).read_text());start=time.time();host.source_check(c)
suite=unittest.TestSuite(test_transport.Tests(n) for n in unittest.defaultTestLoader.getTestCaseNames(test_transport.Tests) if n!='test_selection_environment_and_container_command');r=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(suite);assert r.wasSuccessful() and r.testsRun==7
print(json.dumps(dict(source_check=True,files=len(c['files']),aliases=len(c['aliases']),host_python=sys.version,host_tests=r.testsRun,wall_seconds=time.time()-start)))
'''
 print(remote('host-and-source-check.json',code,dict(packet=physical(P),manifest=M,config=physical(O/'config.json'),config_sha=sha((O/'config.json').read_bytes()))))
elif sys.argv[1]=='container':
 code='''import json,sys,subprocess,time,os
from pathlib import Path
x=json.load(sys.stdin);sys.path.insert(0,x['packet']);import host
c=json.loads(Path(x['config']).read_text());recipe=json.loads(Path(host.old.virtual_to_physical(str(host.RECIPE))).read_text());phase=recipe['commands'][0]
out=host.old.PHYS/host.REL/'jobs/job-dryrun264'/phase['label'];out.mkdir(parents=True,exist_ok=False)
kind='v1' if Path('/sys/fs/cgroup/memory').is_dir() else 'v2';cmd=host.command(c,phase,kind,{'SLURM_JOB_ID':'dryrun264'},None);cut=cmd.index(host.old.IMAGE)
virtual=str(host.old.VIRT/host.REL)
probe="import sys,unittest;sys.path.insert(0,"+repr(virtual)+");import test_transport;r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(test_transport.Tests));assert r.testsRun==8 and r.wasSuccessful()"
# Preserve actual mount/inner path; replace only selected pytest argv by pure test command.
cmd=cmd[:cut+6]+[host.old.PY,'-B','-c',probe]
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30)
print(json.dumps(dict(argv=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,kind=kind,inner_mounts=json.loads((out/'inner-mounts.json').read_text()) if (out/'inner-mounts.json').exists() else None,observed_unix=time.time())))
sys.exit(r.returncode)
'''
 print(remote('container-pure-check.json',code,dict(packet=physical(P),config=physical(O/'config.json')),60))
elif sys.argv[1]=='scheduler':
 a=['sbatch','--parsable','--account=cis260361p','--partition=RM-shared','--qos=rm','--nodes=1','--ntasks=1','--cpus-per-task=18','--mem=32G','--time=00:25:00','--no-requeue','--export=ALL,CUDA_VISIBLE_DEVICES=','--chdir='+physical(P),'--job-name=lad-A3-diag253','--output='+physical(O/'slurm-%j.log'),physical(P/'launch.sh'),physical(O/'config.json'),sha((O/'config.json').read_bytes()),M];save('submission-argv.json',a)
 code='''import json,sys,subprocess,time
x=json.load(sys.stdin);sys.path.insert(0,x['packet']);import host;host.enable_subreaper()
a=x['argv'];r=subprocess.run(a[:1]+['--test-only']+a[1:],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=25)
print(json.dumps(dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,subreaper_enabled=True,observed_unix=time.time())));sys.exit(r.returncode)
'''
 print(remote('scheduler-dry-run.json',code,dict(packet=physical(P),argv=a)))
elif sys.argv[1]=='submit':
 rv=S/'plan-a3/diagnostic-transport-review256/r3/verdict.json';assert sha(rv.read_bytes())=='53a51ed4cb4cefb7cddab14a174f544ac8a6ca5445e0263d895d802f55958fbc'
 for n in ['host-and-source-check.json','container-pure-check.json','scheduler-dry-run.json']:
  x=json.loads((O/n).read_text());assert x['exit_code']==0
 a=json.loads((O/'submission-argv.json').read_text());a.insert(1,'--hold')
 code='''import json,sys,subprocess,time,hashlib,os
from pathlib import Path
x=json.load(sys.stdin);ops=Path(x['ops']);a=x['argv'];assert '--hold' in a
with(ops/'submission-intent.json').open('x') as f:json.dump(dict(argv=a,observed_unix=time.time()),f,indent=2)
r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30)
v=dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time())
with(ops/'submission-result.json').open('x') as f:json.dump(v,f,indent=2)
print(json.dumps(v));sys.exit(r.returncode)
'''
 v=remote('held-submission.json',code,dict(ops=physical(O),argv=a));print(v['stdout'])
elif sys.argv[1]=='bind':
 job='50318613'
 code='''import sys,json,subprocess,hashlib,time,os
from pathlib import Path
x=json.load(sys.stdin);sys.path.insert(0,x['packet']);import host
raw=subprocess.check_output(['scontrol','show','job',x['job'],'-o'],universal_newlines=True,timeout=15);f=dict(z.split('=',1) for z in raw.split() if '=' in z)
expected={'JobId':x['job'],'JobState':'PENDING','Reason':'JobHeldUser','RunTime':'00:00:00','Account':'cis260361p','QOS':'rm','Partition':'RM-shared','NumCPUs':'18','NumTasks':'1','TimeLimit':'00:25:00','Requeue':'0','Restarts':'0','WorkDir':x['packet']}
for k,v in expected.items():assert f[k]==v,(k,f.get(k))
tres=dict(z.split('=',1) for z in f.get('ReqTRES',f.get('TRES','')).split(',') if '=' in z);assert tres['mem'] in ('32G','32768M') and tres['cpu']=='18' and not any(k.startswith('gres/gpu') for k in tres)
ops=Path(x['ops']);spool=ops/'spooled-batch.sh';subprocess.check_call(['scontrol','write','batch_script',x['job'],str(spool)],stdout=sys.stderr,timeout=15)
assert spool.read_bytes()==(Path(x['packet'])/'launch.sh').read_bytes();assert host.old.sha(Path(x['packet'])/'manifest.json')==x['manifest']
for n,h in json.loads((Path(x['packet'])/'manifest.json').read_text()).items():assert host.old.sha(Path(x['packet'])/n)==h
assert host.old.sha(x['config'])==x['config_sha'];c=json.loads(Path(x['config']).read_text());host.source_check(c)
root=host.old.PHYS/host.REL/'jobs'/('job-'+x['job']);root.mkdir(parents=True,mode=0o700,exist_ok=False);assert root.resolve()==root and not root.is_symlink() and root.stat().st_uid==os.getuid() and not list(root.iterdir())
b=dict(actual_job_id=x['job'],scontrol=raw,fields=f,config_sha256=x['config_sha'],manifest_sha256=x['manifest'],spooled_sha256=host.old.sha(spool),output_physical=str(root),output_mode=oct(root.stat().st_mode&0o777),files=len(c['files']),aliases=len(c['aliases']),observed_unix=time.time(),diagnostic_only=True,scientific_admission=False)
with(ops/'actual-binding.json').open('x') as s:json.dump(b,s,indent=2)
print(json.dumps(b))
'''
 v=remote('actual-binding-readback-r2.json',code,dict(job=job,packet=physical(P),ops=physical(O),manifest=M,config=physical(O/'config.json'),config_sha=sha((O/'config.json').read_bytes())));save('actual-binding.json',v);print('bound held job',job,'spool',v['spooled_sha256'])
elif sys.argv[1]=='release':
 rv=S/'plan-a3/diagnostic-deployment-review264/verdict.json';rh='fa2cc039219c52a80120e94ec5ac8729d1a758355d90e9dd04257f50f793d6e6';assert sha(rv.read_bytes())==rh
 u=subprocess.run(['/u/swong2/.local/bin/codex-usage','--pause-at','80'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20);u.check_returncode();usage=json.loads(u.stdout);assert usage['status']=='ok' and not usage['should_pause']
 status=subprocess.check_output(['research-session','status','--session','codex-01a1a2f4'],universal_newlines=True);assert 'freeze: none' in status;save('release-usage-check.json',dict(usage=usage,session_status=status,review_sha256=rh))
 code='''import json,sys,subprocess,time,os
from pathlib import Path
x=json.load(sys.stdin);sys.path.insert(0,x['packet']);import host
ops=Path(x['ops']);assert host.old.sha(Path(x['packet'])/'manifest.json')==x['manifest']
for n,h in json.loads((Path(x['packet'])/'manifest.json').read_text()).items():assert host.old.sha(Path(x['packet'])/n)==h
assert host.old.sha(x['config'])==x['config_sha'];host.source_check(json.loads(Path(x['config']).read_text()))
root=host.old.PHYS/host.REL/'jobs'/('job-'+x['job']);assert root.resolve()==root and not root.is_symlink() and root.stat().st_uid==os.getuid() and (root.stat().st_mode&0o777)==0o700 and not list(root.iterdir())
spool=ops/'release-spooled-batch.sh';subprocess.check_call(['scontrol','write','batch_script',x['job'],str(spool)],stdout=sys.stderr,timeout=15);assert host.old.sha(spool)==x['spool'] and spool.read_bytes()==(Path(x['packet'])/'launch.sh').read_bytes()
raw=subprocess.check_output(['scontrol','show','job',x['job'],'-o'],universal_newlines=True,timeout=15);f=dict(z.split('=',1) for z in raw.split() if '=' in z)
for k,v in {'JobId':x['job'],'JobState':'PENDING','Reason':'JobHeldUser','RunTime':'00:00:00','Account':'cis260361p','QOS':'rm','Partition':'RM-shared','NumCPUs':'18','NumTasks':'1','TimeLimit':'00:25:00','Requeue':'0','Restarts':'0','WorkDir':x['packet']}.items():assert f[k]==v,(k,f.get(k))
t=dict(z.split('=',1) for z in f.get('ReqTRES',f.get('TRES','')).split(',') if '=' in z);assert t['cpu']=='18' and t['mem'] in ('32G','32768M') and not any(k.startswith('gres/gpu') for k in t)
with(ops/'release-intent.json').open('x') as f:json.dump(dict(actual_job_id=x['job'],scontrol=raw,review_sha256=x['review_sha'],observed_unix=time.time()),f,indent=2)
r=subprocess.run(['scontrol','release',x['job']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20);out=dict(actual_job_id=x['job'],exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time())
with(ops/'release.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));sys.exit(r.returncode)
'''
 v=remote('release-readback.json',code,dict(job='50318613',packet=physical(P),ops=physical(O),manifest=M,config=physical(O/'config.json'),config_sha=sha((O/'config.json').read_bytes()),spool='917235f21f8c1af586d58297162c407347982f4e7d9a49038ef9d35561b19a8f',review_sha=rh));print('released',v['actual_job_id'],v['exit_code'])
