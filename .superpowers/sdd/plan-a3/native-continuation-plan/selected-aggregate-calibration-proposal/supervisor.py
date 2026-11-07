"""Proposal only: two original isolated CPU phases, stop on first failure."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
from allocation_facts import read_current,cgroup_snapshot
ROOT=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
SCENARIO=ROOT/'outputs/_analyses/specificity-ladder/unit-f-cpu-evidence/native-round3-b66c2d8'
PHASES=(('selected-pilot-aggregate',5400),('calibration',1800))
GRACE=15

def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def main():
    assert Path.cwd().resolve()==ROOT
    allocation=read_current(ROOT,minimum_remaining_seconds=7275)
    directory=SCENARIO/('diagnostics/selected-aggregate-calibration-job'+allocation['job_id']);directory.mkdir(parents=True,exist_ok=False)
    write(directory/'allocation-before.json',allocation)
    write(directory/'driver-identity.json',dict(path=str(Path(__file__).resolve()),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scientific_execution=False))
    for phase,cap in PHASES:
        actual=read_current(ROOT,minimum_remaining_seconds=cap+GRACE+60)
        out=directory/phase;out.mkdir(exist_ok=False);write(out/'allocation-before.json',actual)
        before=cgroup_snapshot();write(out/'memory-before.json',before)
        assert any('headroom_bytes' in row for row in before)
        assert all(row.get('headroom_bytes',2**64)>=16*1024**3 for row in before),'Insufficient finite ancestor memory headroom'
        slurm={k:v for k,v in os.environ.items() if k.startswith('SLURM_')}
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT))
        assert {k:v for k,v in env.items() if k.startswith('SLURM_')}==slurm
        command=['/u/swong2/.conda/envs/mgnp/bin/python',str(Path(__file__).with_name('coordinator.py')),'--root',str(SCENARIO),'--out',str(out),'--phase',phase]
        log=(out/'steps.log').open('x');samples=(out/'child-samples.jsonl').open('x')
        child=subprocess.Popen(command,stdout=log,stderr=log,env=env,start_new_session=True);began=time.monotonic();term=None;last=-10
        while True:
            pid,status,usage=os.wait4(child.pid,os.WNOHANG);elapsed=time.monotonic()-began
            if pid:break
            if elapsed-last>=5:
                row=dict(elapsed_seconds=elapsed,pid=child.pid)
                try:
                    fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{child.pid}/status').read_text().splitlines() if ':' in line}
                    row.update({name:fields.get(name) for name in ('VmRSS','VmHWM','Threads','State')})
                except FileNotFoundError:pass
                samples.write(json.dumps(row)+'\n');samples.flush();last=elapsed
            if elapsed>=cap and term is None:os.killpg(child.pid,signal.SIGTERM);term=elapsed
            if term is not None and elapsed>=term+GRACE:os.killpg(child.pid,signal.SIGKILL)
            time.sleep(.5)
        code=os.waitstatus_to_exitcode(status);child.returncode=code;log.close();samples.close()
        result=dict(phase=phase,command=command,pid=child.pid,exit_code=code,elapsed_seconds=elapsed,user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,peak_child_rss_bytes=usage.ru_maxrss*1024,timeout_seconds=cap,kill_grace_seconds=GRACE,term_sent_at=term,actual_job_id=actual['job_id'],actual_step_id=actual['step_id'],actual_host=actual['host'],scientific_execution=False,production_admission=False)
        write(out/'result.json',result);write(out/'memory-after.json',cgroup_snapshot());write(out/'allocation-after.json',read_current(ROOT))
        print(json.dumps(result),flush=True)
        if code!=0 or term is not None:raise SystemExit((code if code>0 else 128-code) if code!=0 else 124)
        complete=json.loads((out/'coordinator-result.json').read_text());assert complete['result']['complete'] is True and complete['phase']==phase
    write(directory/'allocation-after.json',read_current(ROOT));write(directory/'all-phases-complete.json',dict(phases=[name for name,_ in PHASES],scientific_execution=False,production_admission=False))

if __name__=='__main__':main()
