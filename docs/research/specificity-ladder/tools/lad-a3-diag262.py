from pathlib import Path
import json,hashlib,base64,subprocess,shlex,time,sys
A=Path('/projects/beto/swong2/Alignment');W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';S=W/'.superpowers/sdd';P=S/'plan-a3/diagnostic-transport254-r2';O=S/'plan-a3/diagnostic-deployment262';O.mkdir(exist_ok=True)
R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment');M='7ae57ad0089826888d8917e0c01da15d3d5108ff292200a8c26b99d5aeed9eea'
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
out=host.old.PHYS/host.REL/'jobs/job-dryrun262'/phase['label'];out.mkdir(parents=True,exist_ok=False)
kind='v1' if Path('/sys/fs/cgroup/memory').is_dir() else 'v2';cmd=host.command(c,phase,kind,{'SLURM_JOB_ID':'dryrun262'},None);cut=cmd.index(host.old.IMAGE)
virtual=str(host.old.VIRT/host.REL)
probe="import sys,unittest;sys.path.insert(0,"+repr(virtual)+");import test_transport;r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(test_transport.Tests));assert r.testsRun==8 and r.wasSuccessful()"
# Preserve actual mount/inner path; replace only selected pytest argv by pure test command.
cmd=cmd[:cut+6]+[host.old.PY,'-B','-c',probe]
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30)
print(json.dumps(dict(argv=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,kind=kind,inner_mounts=json.loads((out/'inner-mounts.json').read_text()) if (out/'inner-mounts.json').exists() else None,observed_unix=time.time())))
sys.exit(r.returncode)
'''
 print(remote('container-pure-check.json',code,dict(packet=physical(P),config=physical(O/'config.json')),60))
