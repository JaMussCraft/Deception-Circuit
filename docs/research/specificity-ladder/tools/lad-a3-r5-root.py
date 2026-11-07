import pathlib,json,hashlib,subprocess,shlex,base64,time,sys,os
A=pathlib.Path('/projects/beto/swong2/Alignment');W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';S=W/'.superpowers/sdd';P=S/'plan/task23-green-r5';O=S/'plan/a3-green-bridges-deployment245';O.mkdir(exist_ok=True);RA='/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment';T=S/'plan/a3-green-bridges-transport229-r3';M='bd3533cc18025d7d2bf97515060a46f793abd4f4a43609e8dc6c9626d8a6e6e2'
def sha(b):return hashlib.sha256(b).hexdigest()
def physical(p):return RA+'/'+str(pathlib.Path(p).relative_to(A))
def save(n,v):
 with (O/n).open('x') as f:json.dump(v,f,indent=2)
def remote(n,code,x,timeout=60):
 cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
 r=subprocess.run(cmd,input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=timeout);save(n,{'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'observed_unix':time.time()})
 if r.returncode:print(r.stdout,r.stderr);r.check_returncode()
 return json.loads(r.stdout)
if sys.argv[1]=='prepare':
 assert sha((P/'source-pins.json').read_bytes())=='05b53e5f2b2c2d737782753cde63cb6c1b428038d71d7666c644777deb1184c9'
 i=json.loads((P/'transport-inventory.json').read_text());rows={x['virtual']:dict(x,physical=physical(x['virtual'])) for x in i['files']};assert len(rows)==1116
 for root in [A/'Deception-Circuit/docs/research',W/'docs/research']:
  for n in ['held_out.json','directions.json']:
   f=root/n;b=f.read_bytes();assert not f.is_symlink();rows[str(f)]={'virtual':str(f),'physical':physical(f),'sha256':sha(b),'bytes':len(b)}
 aliases=[dict(x,physical=physical(x['virtual'])) for x in i['aliases']];assert len(aliases)==8
 for x in aliases:assert pathlib.Path(x['virtual']).is_symlink() and os.readlink(x['virtual'])==x['literal_target']
 for x in rows.values():
  f=pathlib.Path(x['virtual']);b=f.read_bytes();assert not f.is_symlink() and len(b)==x['bytes'] and sha(b)==x['sha256'],str(f)
 c={'status':'ROOT_BOUND_A3_GREEN_MGNP_TRANSPORT','observer_virtual':str(P/'run_packet.py'),'expected_cases':223,'expected_file_count':len(rows),'files':list(rows.values()),'aliases':aliases,'notes':'Exact reviewed r5 observer closure plus current primary and worktree registry targets; eight unchanged aliases. No source or test semantics change.'}
 save('config.json',c);save('inventory.json',c);print('config',sha((O/'config.json').read_bytes()),len(rows),'files')
elif sys.argv[1]=='stage':
 c=json.loads((O/'config.json').read_text());rows=list(c['files']);raw=(O/'config.json').read_bytes();rows.append({'virtual':str(O/'config.json'),'physical':physical(O/'config.json'),'sha256':sha(raw),'bytes':len(raw)})
 for start in range(0,len(rows),200):
  packet=[]
  for r in rows[start:start+200]:
   b=pathlib.Path(r['virtual']).read_bytes();assert sha(b)==r['sha256'];packet.append(dict(r,base64=base64.b64encode(b).decode()))
  code='''import sys,json,base64,hashlib,time,os
from pathlib import Path
x=json.load(sys.stdin);out=[]
for r in x['files']:
 p=Path(r['physical']);b=base64.b64decode(r['base64']);assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'];p.parent.mkdir(parents=True,exist_ok=True);assert not p.is_symlink()
 if p.exists():assert p.read_bytes()==b,str(p)
 else:
  with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];out.append({k:v for k,v in r.items() if k!='base64'})
for r in x['aliases']:
 p=Path(r['physical']);assert p.is_symlink() and os.readlink(str(p))==r['literal_target']
print(json.dumps({'files':out,'aliases_verified':len(x['aliases']),'observed_unix':time.time()}))
'''
  v=remote('stage-%04d.json'%start,code,{'files':packet,'aliases':c['aliases']});print('staged',start,len(v['files']),flush=True)
elif sys.argv[1]=='dryrun':
 old=S/'plan/a3-green-bridges-deployment234';csha=sha((O/'config.json').read_bytes())
 for src,dest in [('container-dry-run-r2.json','container-dry-run-after-stage.json'),('effective-mount-check.json','effective-mount-check.json')]:
  d=json.loads((old/src).read_text());code=shlex.split(d['command'][-1])[-1];code=code.replace('a3-green-bridges-deployment234','a3-green-bridges-deployment245').replace('dryrun-234','dryrun-245').replace('2fd8748eec825bcc379cb54f40be89c9dac2dceb00fff3433994e900d8e42895',csha)
  v=remote(dest,code,{},90);print(dest,'passed',flush=True)
elif sys.argv[1]=='scheduler':
 old=S/'plan/a3-green-bridges-deployment234';a=json.loads((old/'submission-r2-argv.json').read_text());print(type(a))
 if isinstance(a,dict):a=a['argv']
 a=[x.replace('a3-green-bridges-deployment234','a3-green-bridges-deployment245').replace('2fd8748eec825bcc379cb54f40be89c9dac2dceb00fff3433994e900d8e42895',sha((O/'config.json').read_bytes())).replace('lad-A3-mgnp-green','lad-A3-mgnp-r5') for x in a];a=[x for x in a if x!='--hold'];save('submission-argv.json',a)
 code='''import json,sys,subprocess,time
x=json.load(sys.stdin);a=x['argv'];a.insert(1,'--test-only');r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);print(json.dumps({'argv':a,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'observed_unix':time.time()}));sys.exit(r.returncode)
'''
 v=remote('scheduler-dry-run.json',code,{'argv':a});print(v['stderr'])
elif sys.argv[1]=='submit':
 old=S/'plan/a3-green-bridges-deployment234';d=json.loads((old/'held-r2-submission.json').read_text());code=shlex.split(d['command'][-1])[-1]
 code=code.replace('a3-green-bridges-deployment234','a3-green-bridges-deployment245').replace('2fd8748eec825bcc379cb54f40be89c9dac2dceb00fff3433994e900d8e42895',sha((O/'config.json').read_bytes())).replace('lad-A3-mgnp-green','lad-A3-mgnp-r5').replace('held-r2-submission','held-submission')
 v=remote('held-submission.json',code,{});print(json.dumps(v))
elif sys.argv[1]=='release':
 rv=S/'plan-a3/r5-deployment-review246/verdict.json';rh='e21192f294cebec56264f7ccb846d51581bfcb616693a81ca2f6451a5aa8ad93';assert sha(rv.read_bytes())==rh
 old=S/'plan/a3-green-bridges-deployment234';d=json.loads((old/'release.json').read_text());code=shlex.split(d['command'][-1])[-1]
 for a,b in [('a3-green-bridges-deployment234','a3-green-bridges-deployment245'),("job='50316834'","job='50316975'"),('2fd8748eec825bcc379cb54f40be89c9dac2dceb00fff3433994e900d8e42895',sha((O/'config.json').read_bytes())),('ac6e649a9ae1b90055dd5ce7cdfb6308c3b8cdd6102e4ff9f9ff7f3874e99f6c',rh)]:code=code.replace(a,b)
 v=remote('release.json',code,{});print(json.dumps(v))
