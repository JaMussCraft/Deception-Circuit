from pathlib import Path
import json,hashlib,subprocess,sys,time,shutil,tempfile
A=Path('/projects/beto/swong2/Alignment');W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';S=W/'.superpowers/sdd';P=S/'plan-a2-whole-packet-correction327/packet-r5';O=S/'plan-a2-task4-deployment331';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
 with(O/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def call(a,timeout=30):
 r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=timeout);return dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time())
if sys.argv[1]=='prepare':
 assert sha(P/'packet-pins.json')=='9a5129f6c3fae0455c706a6077ac04047c5062f7abbea0f98018113da1f7e571'
 with tempfile.TemporaryDirectory(prefix='lad-a2-spool-') as tmp:
  f=Path(tmp)/'slurm_script';shutil.copyfile(P/'run_cpu.sh',f);r=call(['bash',str(f),'--output',str(O/'UNRUN-DRYRUN'),'--dry-run']);save('relocated-wrapper-dryrun.json',r);assert r['exit_code']==0
 a=['sbatch','--parsable','--hold','--account=beto-delta-cpu','--partition=cpu-interactive','--constraint=projects','--nodes=1','--ntasks=1','--cpus-per-task=2','--mem=16G','--time=01:00:00','--no-requeue','--export=ALL,CUDA_VISIBLE_DEVICES=','--chdir='+str(W),'--job-name=lad-A2-task4','--output='+str(O/'slurm-%j.log'),str(P/'run_cpu.sh'),'--output',str(O/'run-01')]
 r=call(a[:1]+['--test-only']+[v for v in a[1:] if v!='--hold']);save('scheduler-preview.json',r);assert r['exit_code']==0;save('submission-argv.json',a);print(r['stderr'])
elif sys.argv[1]=='submit':
 assert not(O/'submission.json').exists();a=json.loads((O/'submission-argv.json').read_text());r=call(a);save('submission.json',r);assert r['exit_code']==0;job=r['stdout'].strip().split(';')[0];assert job.isdigit();save('job.json',dict(job_id=job,cluster='delta'));r=call(['research-session','job','add',str(A/'Deception-Circuit/docs/research/specificity-ladder'),'--job-id',job,'--cluster','delta','--status','PENDING','--timeout-min','60']);save('registration.json',r);assert r['exit_code']==0;print(job,r['stdout'])
elif sys.argv[1]=='check':
 job=json.loads((O/'job.json').read_text())['job_id'];r=call(['scontrol','show','job',job,'-o']);save('held-readback.json',r);assert r['exit_code']==0;f=dict(v.split('=',1) for v in r['stdout'].split() if '=' in v)
 assert f['JobState']=='PENDING' and f['Reason']=='JobHeldUser' and f['RunTime']=='00:00:00';assert f['Account']=='beto-delta-cpu' and f['Partition']=='cpu-interactive' and f['QOS']=='beto-delta-cpu';assert f['NumCPUs']==f['CPUs/Task']=='2' and f['NumTasks']=='1' and f['NumNodes'] in ('1','1-1');assert f['TimeLimit']=='01:00:00' and f['Requeue']==f['Restarts']=='0';assert f['WorkDir']==str(W) and f['Command']==str(P/'run_cpu.sh')
 t=dict(v.split('=',1) for v in f['ReqTRES'].split(','));assert t['mem']=='16G' and t['cpu']=='2' and not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items());assert not(O/'run-01').exists()
 spool=O/'submitted-script.sh';r=call(['scontrol','write','batch_script',job,str(spool)]);save('spool-readback.json',r);assert r['exit_code']==0 and spool.read_bytes()==(P/'run_cpu.sh').read_bytes()
 r=call(['bash',str(spool),'--output',str(O/'UNRUN-DRYRUN'),'--dry-run']);save('actual-spool-dryrun.json',r);assert r['exit_code']==0
 save('root-readiness.json',dict(job_id=job,cluster='delta',packet_pins_sha256=sha(P/'packet-pins.json'),dependencies_sha256=sha(P/'dependencies.json'),source_review_sha256=sha(A/'Deception-Circuit/docs/research/specificity-ladder/reports/328-handback.md'),spool_sha256=sha(spool),output=str(O/'run-01'),actual_allocation=f,execution_authorized=False));print(job,'held binding and actual relocated wrapper passed')
elif sys.argv[1]=='release':
 v=json.loads((O/'root-readiness.json').read_text());job=v['job_id'];assert not(O/'release-intent.json').exists()
 u=call(['/u/swong2/.local/bin/codex-usage','--pause-at','80']);save('release-usage.json',u);assert u['exit_code']==0;usage=json.loads(u['stdout']);assert usage['status']=='ok' and usage['should_pause'] is False
 st=call(['research-session','status','--session','codex-01a1a2f4']);save('release-session-status.json',st);assert st['exit_code']==0 and 'freeze: none' in st['stdout']
 assert sha(P/'packet-pins.json')==v['packet_pins_sha256'] and sha(P/'dependencies.json')==v['dependencies_sha256'] and sha(P/'run_cpu.sh')==v['spool_sha256']
 for n,h in json.loads((P/'packet-pins.json').read_text()).items():assert sha(P/n)==h
 r=call(['bash',str(P/'run_cpu.sh'),'--output',str(O/'UNRUN-RELEASE-DRYRUN'),'--dry-run']);save('release-source-dryrun.json',r);assert r['exit_code']==0
 r=call(['scontrol','show','job',job,'-o']);assert r['exit_code']==0;f=dict(x.split('=',1) for x in r['stdout'].split() if '=' in x);assert f['JobState']=='PENDING' and f['Reason']=='JobHeldUser' and f['RunTime']=='00:00:00'
 for k in ['Account','QOS','Partition','TimeLimit','NumCPUs','CPUs/Task','NumTasks','ReqTRES','Requeue','Restarts','Command','WorkDir','StdOut']:assert f[k]==v['actual_allocation'][k],k
 save('release-intent.json',dict(job_id=job,allocation=f,weekly_used_percent=usage['weekly']['used_percent'],observed_unix=time.time()));r=call(['scontrol','release',job]);save('release.json',r);assert r['exit_code']==0;print('Released new A2 whole-pipeline CPU validation',job)
