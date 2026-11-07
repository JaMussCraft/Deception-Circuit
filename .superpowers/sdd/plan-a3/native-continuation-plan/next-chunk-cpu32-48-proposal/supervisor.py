"""UNEXECUTED: real Slurm CPU-only supervisor; never submits or fakes allocation."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
from allocation_facts import environment,read_current,cgroup_snapshot
CAP=2820
GRACE=15
ROOT=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
SCENARIO=ROOT/'outputs/_analyses/specificity-ladder/unit-f-cpu-evidence/native-round3-b66c2d8'
def write(path,value):
 with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def main():
 assert Path.cwd().resolve()==ROOT
 allocation=read_current(ROOT,minimum_remaining_seconds=CAP+GRACE+60)
 out=SCENARIO/('diagnostics/cpu-next-cases32-48-job'+allocation['job_id']);out.mkdir(parents=True,exist_ok=False)
 write(out/'allocation-before.json',allocation)
 before=cgroup_snapshot();write(out/'memory-before.json',before);assert any('headroom_bytes' in item for item in before),'Visible finite memory-controller headroom required';assert all(item.get('headroom_bytes',2**64)>=16*1024**3 for item in before),'Insufficient finite ancestor headroom'
 slurm_original={k:v for k,v in os.environ.items() if k.startswith('SLURM_')}
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT))
 assert {k:v for k,v in env.items() if k.startswith('SLURM_')}==slurm_original
 command=['/u/swong2/.conda/envs/mgnp/bin/python',str(Path(__file__).with_name('coordinator.py')),'--root',str(SCENARIO),'--out',str(out)]
 write(out/'supervisor-identity.json',dict(path=str(Path(__file__).resolve()),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),command=command,allocation_job_id=allocation['job_id'],scientific_execution=False))
 log=(out/'steps.log').open('x');samples=(out/'child-samples.jsonl').open('x');child=subprocess.Popen(command,stdout=log,stderr=log,env=env,start_new_session=True);began=time.monotonic();term=None;last=-10
 while True:
  pid,status,usage=os.wait4(child.pid,os.WNOHANG);elapsed=time.monotonic()-began
  if pid:break
  if elapsed-last>=5:
   row=dict(elapsed_seconds=elapsed,pid=child.pid)
   try:
    fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{child.pid}/status').read_text().splitlines() if ':' in line};row.update({key:fields.get(key) for key in ('VmRSS','VmHWM','Threads','State')})
   except FileNotFoundError:pass
   samples.write(json.dumps(row)+'\n');samples.flush();last=elapsed
  if elapsed>=CAP and term is None:os.killpg(child.pid,signal.SIGTERM);term=elapsed
  if term is not None and elapsed>=term+GRACE:os.killpg(child.pid,signal.SIGKILL)
  time.sleep(.5)
 code=os.waitstatus_to_exitcode(status);child.returncode=code;log.close();samples.close()
 result=dict(command=command,pid=child.pid,exit_code=code,elapsed_seconds=elapsed,user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,peak_child_rss_bytes=usage.ru_maxrss*1024,timeout_seconds=CAP,kill_grace_seconds=GRACE,term_sent_at=term,actual_slurm_job_id=allocation['job_id'],actual_step_id=allocation['step_id'],host=allocation['host'],allocated_CPU_memory_bytes=allocation['allocation_memory_bytes'],allocated_GPUs=0,selected_case_start=32,selected_case_count=17,injected_fixture=True,scientific_execution=False,production_admission=False,prior_login_timings_not_relabelled=True)
 write(out/'result.json',result);write(out/'memory-after.json',cgroup_snapshot())
 try:write(out/'allocation-after.json',read_current(ROOT))
 except BaseException as error:write(out/'allocation-after-read-error.json',dict(error=repr(error)));raise
 print(json.dumps(result),flush=True);raise SystemExit(code if code>=0 else 128-code)

if __name__=='__main__':main()
