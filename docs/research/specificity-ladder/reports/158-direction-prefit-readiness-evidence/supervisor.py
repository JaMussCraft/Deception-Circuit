"""Unexecuted 25-minute CPU proposal; no retry or model execution."""
from pathlib import Path
import json,os,signal,subprocess,time
from allocation_facts import read_current,cgroup_snapshot
P=Path(__file__).resolve().parent
CAP=1320
GRACE=15

def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def main():
    cfg=json.loads((P/'config.json').read_text());w=Path(cfg['W']);o=Path(cfg['output']);assert Path.cwd().resolve()==w
    allocation=read_current(w,minimum_remaining_seconds=1410);assert allocation['time_limit_seconds']==1500
    o.mkdir(parents=True,exist_ok=False);e=o/'evidence';e.mkdir()
    write(e/'allocation-before.json',allocation);before=cgroup_snapshot();write(e/'memory-before.json',before)
    assert any('headroom_bytes' in row for row in before) and all(row.get('headroom_bytes',2**64)>=16*1024**3 for row in before)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    cmd=['/sw/external/python/anaconda3/bin/python3.9',str(P/'prepare.py')]
    log=(e/'driver.log').open('x');samples=(e/'child-samples.jsonl').open('x');child=subprocess.Popen(cmd,stdout=log,stderr=log,env=env,start_new_session=True);start=time.monotonic();term=None;last=-10
    while True:
        pid,status,usage=os.wait4(child.pid,os.WNOHANG);elapsed=time.monotonic()-start
        if pid:break
        if elapsed-last>=5:
            row=dict(elapsed_seconds=elapsed,pid=child.pid)
            try:
                fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{child.pid}/status').read_text().splitlines() if ':' in line};row.update({k:fields.get(k) for k in ('VmRSS','VmHWM','Threads','State')})
            except FileNotFoundError:pass
            samples.write(json.dumps(row)+'\n');samples.flush();last=elapsed
        if elapsed>=CAP and term is None:os.killpg(child.pid,signal.SIGTERM);term=elapsed
        if term is not None and elapsed>=term+GRACE:os.killpg(child.pid,signal.SIGKILL)
        time.sleep(.5)
    code=os.waitstatus_to_exitcode(status);child.returncode=code;log.close();samples.close()
    write(e/'result.json',dict(command=cmd,exit_code=code,elapsed_seconds=elapsed,user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,peak_wait4_rss_bytes=usage.ru_maxrss*1024,timeout_seconds=CAP,kill_grace_seconds=GRACE,term_sent_at=term,actual_job_id=allocation['job_id'],scientific_execution=False,execution_authorized=False))
    write(e/'memory-after.json',cgroup_snapshot());write(e/'allocation-after.json',read_current(w))
    raise SystemExit(124 if term is not None and code==0 else code if code>=0 else 128-code)

if __name__=='__main__':main()
