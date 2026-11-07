"""One proposed4CPU48GiB45min CPU proof, bounded child2400+15; no retry."""
import argparse,datetime,json,os,re,signal,socket,subprocess,time,traceback
from pathlib import Path
import proof_guards as g
CHILD=None
LABELS=dict(MODEL_LOADED=False,EFFECTS_READ=False,SYNTHETIC_SCHEMA_ONLY=True,NUMERICAL_CONTROLS_TESTED=False,GPU_ADMITTED=False)
def normal_child(code,term,finished,deadline,report):
 if not(code==0 and term is None and finished<deadline and report.get('status')=='CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR' and report.get('complete') is False and all(report.get(k) is v for k,v in LABELS.items())):raise ValueError('partial/terminated/late/non-schema child cannot complete')
def allocation():
 job=os.environ['SLURM_JOB_ID'];assert re.fullmatch('[0-9]+',job)
 raw=subprocess.check_output(['scontrol','show','job',job,'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC'));f=dict(v.split('=',1) for v in raw.split() if '=' in v);t=dict(v.split('=',1) for v in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in v)
 assert f['JobId']==job and f['JobState']=='RUNNING' and re.search(r'\('+str(os.getuid())+r'\)',f['UserId'])
 assert f['NumCPUs']=='4' and t['cpu']=='4' and f['NumNodes']=='1' and f['Partition'] in ('cpu','cpu-interactive') and f['Account'].endswith('-cpu') and f['Requeue']=='0' and f['Restarts']=='0'
 assert t.get('mem') in ('48G','49152M') and not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items())
 assert f['TimeLimit'] in ('00:45:00','45:00') and Path(f['WorkDir']).resolve()==g.R.resolve() and os.environ.get('SLURM_CLUSTER_NAME')=='delta'
 assert os.environ.get('SLURM_CPUS_PER_TASK')=='4' and os.environ.get('CUDA_VISIBLE_DEVICES','')==''
 for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS'):assert not os.environ.get(k)
 for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'):assert os.environ.get(k,'') in ('','0')
 hosts=subprocess.check_output(['scontrol','show','hostnames',f['NodeList']],universal_newlines=True,timeout=15).split();assert socket.gethostname().split('.')[0] in {x.split('.')[0] for x in hosts}
 end=datetime.datetime.strptime(f['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp();return dict(job=job,host=socket.gethostname(),raw=raw,fields=f,tres=t,end_epoch=end,captured_unix=time.time())
def terminate():
 if CHILD is not None and CHILD.poll() is None:
  os.killpg(CHILD.pid,signal.SIGTERM)
  try:CHILD.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(CHILD.pid,signal.SIGKILL);CHILD.wait(timeout=5)
def interrupted(sig,frame):raise TimeoutError('supervisor signal '+str(sig))
def main():
 global CHILD
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);a=ap.parse_args();g.packet(a.manifest_sha256);out=Path(a.output);assert out.is_absolute();out=out.resolve();assert not out.is_relative_to(g.G.resolve()) and not out.is_relative_to(g.R.resolve()) and not out.exists();out.mkdir(parents=True,exist_ok=False)
 initial=allocation();g.write(out/'allocation-before.json',initial);assert initial['end_epoch']-time.time()>=2520
 for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,interrupted)
 deadline=min(time.monotonic()+2400,time.monotonic()+initial['end_epoch']-time.time()-120);started=time.time();term=None
 cmd=['/u/swong2/.conda/envs/mgnp/bin/python','-B',str(g.P/'proof_worker.py'),'--output',str(out),'--manifest-sha256',a.manifest_sha256,'--deadline-monotonic',str(deadline)]
 try:
  with (out/'child.log').open('x') as log:
   CHILD=subprocess.Popen(cmd,cwd=str(g.R),env=dict(os.environ,PYTHONPATH=str(g.R),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   while CHILD.poll() is None:
    current=allocation();deadline=min(deadline,time.monotonic()+current['end_epoch']-time.time()-120)
    if time.monotonic()>=deadline:term=time.time();terminate();break
    time.sleep(2)
  finished=time.monotonic();after=allocation();deadline=min(deadline,time.monotonic()+after['end_epoch']-time.time()-120);g.write(out/'allocation-after.json',after)
  child_report=g.read(out/'CHILD-REPORT.json') if (out/'CHILD-REPORT.json').is_file() else {}
  execution=dict(command=cmd,exit_code=CHILD.returncode,term_sent_at=term,started_unix=started,finished_unix=time.time(),deadline_monotonic=deadline,timely=finished<deadline,actual_CPU_job_id=initial['job'],**LABELS);g.write(out/'child-execution.json',execution)
  normal_child(CHILD.returncode,term,finished,deadline,child_report);assert after['end_epoch']-time.time()>=90
  g.packet(a.manifest_sha256);last=allocation();assert min(initial['end_epoch'],last['end_epoch'])-time.time()>=30 and time.time()-started<=2670,'late supervisor publication';g.write(out/'allocation-final.json',last);result=dict(child_report,complete=True,status='COMPLETE_CPU_SCHEMA_RESOURCE_PROOF_ONLY',actual_CPU_job_id=initial['job'],child_report_sha256=g.sha(out/'CHILD-REPORT.json'),child_execution_sha256=g.sha(out/'child-execution.json'),packet_sha256=a.manifest_sha256,GPU_ADMITTED=False)
  g.write(out/'COMPLETE-PROOF.json',result)
 except BaseException as e:
  terminate();g.write(out/'FAILED-supervisor.json',dict(complete=False,error=repr(e),traceback=traceback.format_exc(),**LABELS));raise
 finally:terminate()
if __name__=='__main__':main()
