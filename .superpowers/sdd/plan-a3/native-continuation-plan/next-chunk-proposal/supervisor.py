"""Proposed only: DO NOT RUN until root explicitly releases after contention clears."""
from pathlib import Path
import json,os,signal,subprocess,sys,time
root=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/unit-f-cpu-evidence/native-round3-b66c2d8')
out=root/'diagnostics/next-cases2-4-01';out.mkdir(parents=True,exist_ok=False)
relative=next(x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
def cgroups():
 p=Path('/sys/fs/cgroup')/relative.lstrip('/');data=[]
 while True:
  item=dict(path=str(p))
  for field in ('memory.current','memory.max','memory.events'):
   q=p/field
   if q.exists():item[field]=q.read_text().strip()
  if item.get('memory.max','max')!='max':item['headroom_bytes']=int(item['memory.max'])-int(item.get('memory.current','0'))
  data.append(item)
  if p==Path('/sys/fs/cgroup'):break
  p=p.parent
 return data
before=cgroups();(out/'memory-before.json').write_text(json.dumps(before,indent=2)+'\n')
assert all(x.get('headroom_bytes',2**64)>=17179869184 for x in before),'Less than16GiB ancestor headroom'
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='.')
command=['/u/swong2/.conda/envs/mgnp/bin/python',str(Path(__file__).with_name('coordinator.py')),'--root',str(root),'--out',str(out)]
log=(out/'steps.log').open('w');process=subprocess.Popen(command,stdout=log,stderr=log,env=env,start_new_session=True)
start=time.monotonic();term=None;samples=(out/'child-samples.jsonl').open('w');last=-10
while True:
 pid,status,usage=os.wait4(process.pid,os.WNOHANG)
 elapsed=time.monotonic()-start
 if pid:break
 if elapsed-last>=5:
  entry=dict(elapsed_seconds=elapsed,pid=process.pid)
  try:
   fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{process.pid}/status').read_text().splitlines() if ':' in line}
   entry.update({key:fields.get(key) for key in ('VmRSS','VmHWM','Threads','State')})
  except FileNotFoundError:pass
  samples.write(json.dumps(entry)+'\n');samples.flush();last=elapsed
 if elapsed>=1500 and term is None:
  os.killpg(process.pid,signal.SIGTERM);term=elapsed
 if term is not None and elapsed>=term+15:
  os.killpg(process.pid,signal.SIGKILL)
 time.sleep(.5)
code=os.waitstatus_to_exitcode(status);process.returncode=code;log.close();samples.close()
result=dict(command=command,pid=process.pid,exit_code=code,elapsed_seconds=elapsed,user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,
 peak_child_rss_bytes=usage.ru_maxrss*1024,timeout_seconds=1500,kill_grace_seconds=15,term_sent_at=term,operational_existing_API_coordinator=True,selected_case_start=2,selected_case_count=3,source_unchanged=True)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');(out/'memory-after.json').write_text(json.dumps(cgroups(),indent=2)+'\n')
print(json.dumps(result),flush=True);raise SystemExit(code if code>=0 else 128-code)
