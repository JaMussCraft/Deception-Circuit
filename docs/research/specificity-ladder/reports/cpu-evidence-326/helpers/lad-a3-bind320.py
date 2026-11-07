from pathlib import Path
import json,hashlib,subprocess,shlex,time,importlib.util
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/producer-deployment320';P=S/'plan-a3/candidate-producer311';c=json.loads((O/'draft-config.json').read_text());c['kind']='ROOT_BOUND_PROVISIONAL_CPU_PRODUCER';c['job_id']=json.loads((O/'job.json').read_text())['job_id'];R=Path(c['physical_alignment']);physical=lambda p:str(R/Path(p).relative_to(A));spec=importlib.util.spec_from_file_location('root311common',P/'common.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.validate(c)
b=(json.dumps(c,indent=2,sort_keys=True)+'\n').encode();h=hashlib.sha256(b).hexdigest()
with(O/'config.json').open('xb') as f:f.write(b)
with(O/'config.sha256').open('x') as f:f.write(h+'\n')
code='''import sys,json,hashlib,subprocess,os,time,stat
from pathlib import Path
x=json.load(sys.stdin);d=Path(x['directory']);b=x['config_text'].encode();assert hashlib.sha256(b).hexdigest()==x['config_sha256'];p=d/'config.json';assert not p.exists()
with p.open('xb') as f:f.write(b)
p.chmod(0o600)
with(d/'config.sha256').open('x') as f:f.write(x['config_sha256']+'\\n')
c=json.loads(b);sys.path.insert(0,x['packet']);import common;import host
common.validate(c);common.check_packet(c,lambda p:host.physical(c,p));source=common.check_sources(c,lambda p:host.physical(c,p))
raw=subprocess.check_output(['scontrol','show','job',c['job_id'],'-o'],universal_newlines=True,timeout=15);f=dict(w.split('=',1) for w in raw.split() if '=' in w)
assert f['JobState']=='PENDING' and f['Reason']=='JobHeldUser' and f['RunTime']=='00:00:00'
assert (f['Account'],f['Partition'],f['QOS'])==(c['account'],c['partition'],c['qos'])
assert f['NumCPUs']==f['CPUs/Task']=='128' and f['NumTasks']=='1' and f['NumNodes'] in ('1','1-1')
t=dict(w.split('=',1) for w in f.get('ReqTRES',f.get('TRES','')).split(',') if '=' in w);assert t['cpu']=='128' and t['mem'] in ('192G','196608M') and not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items())
assert host.seconds(f['TimeLimit'])==5400 and f['Requeue']==f['Restarts']=='0'
assert f['Command']==str(d/'dispatch.sh') and f['WorkDir']==x['packet'] and '('+str(os.getuid())+')' in f['UserId']
spool=d/'submitted-script.sh';assert not spool.exists();subprocess.check_call(['scontrol','write','batch_script',c['job_id'],str(spool)],stdout=subprocess.DEVNULL,timeout=15);assert common.sha(spool)==x['dispatch_sha256']==common.sha(d/'dispatch.sh')
root=Path(host.physical(c,c['run_root']));assert root.resolve()==root and all(not p.is_symlink() for p in [root]+list(root.parents));assert root.stat().st_uid==os.getuid() and stat.S_IMODE(root.stat().st_mode)&0o777==0o700 and not list(root.iterdir());assert not(root/'child').exists()
assert common.sha(c['image'])==c['image_sha256'];st=os.statvfs(str(root));assert st.f_bavail*st.f_frsize>=c['storage_free_bytes_required']
print(json.dumps(dict(job_id=c['job_id'],config_sha256=x['config_sha256'],source=source,spool_sha256=common.sha(spool),raw_allocation=raw,allocation=f,root=dict(path=str(root),uid=root.stat().st_uid,mode=oct(stat.S_IMODE(root.stat().st_mode)),empty=True,canonical=True,no_symlink_ancestry=True,child_absent=True),available_bytes=st.f_bavail*st.f_frsize,observed_unix=time.time())))
'''
x=dict(directory=physical(O),packet=physical(P),config_text=b.decode(),config_sha256=h,dispatch_sha256=hashlib.sha256((O/'dispatch.sh').read_bytes()).hexdigest());ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2'];r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(code)],input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=90)
with(O/'held-binding-readback.json').open('x') as f:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()),f,indent=2)
assert r.returncode==0,r.stderr
pins={n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in ['config.json','dispatch.sh','held-binding-readback.json','actual-host-source-readback.json','actual-container-smoke.json','transport-inventory.json','input-rehash317.json','project-quota.json']}
with(O/'deployment-manifest.json').open('x') as f:json.dump(dict(job_id=c['job_id'],config_sha256=h,files=pins,candidate_commit=c['candidate_commit'],packet_manifest_sha256=c['packet_manifest']['sha256'],source_snapshot_sha256=c['candidate_source']['sha256'],source_review_sha256='a8169126d1044a99690e6044a602f59ce097969e6ee12f697b57f71c5945c0a8',source_snapshot_review_sha256='d518022edbee0121bb78cacb0db8c80e9cbc21e9d85e54478f3db91556754a20',release_authorized=False,execution_authorized=False),f,indent=2)
print('Held job',c['job_id'],'actual binding/spool/source/input/private root passed; config',h,'manifest',hashlib.sha256((O/'deployment-manifest.json').read_bytes()).hexdigest())
