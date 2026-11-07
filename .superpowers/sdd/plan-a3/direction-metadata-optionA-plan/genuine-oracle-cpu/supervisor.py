from pathlib import Path
import argparse,json,os,signal,subprocess,time,hashlib
from allocation_facts import read_current,cgroup_snapshot
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--config-sha256',required=True);ap.add_argument('--mode',choices=('original','candidate'),required=True);ap.add_argument('--environment',choices=('mgnp','base'),required=True);ap.add_argument('--output',required=True);a=ap.parse_args();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(a.config)==a.config_sha256;c=json.loads(Path(a.config).read_text());assert c['CPU_child_seconds']==3300 and c['kill_grace_seconds']==15
out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
def write(name,value):
 with (out/name).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
allocation=read_current(c['W'],minimum_remaining_seconds=3500);assert allocation['time_limit_seconds']==3600;write('allocation-before.json',allocation);before=cgroup_snapshot();write('memory-before.json',before)
assert any('headroom_bytes' in row for row in before) and all(row.get('headroom_bytes',2**64)>=150*1024**3 for row in before)
interpreter={'mgnp':'/u/swong2/.conda/envs/mgnp/bin/python','base':'/sw/external/python/anaconda3/bin/python3.9'}[a.environment]
cmd=[interpreter,str(P/'run.py'),'--config',a.config,'--config-sha256',a.config_sha256,'--mode',a.mode,'--environment',a.environment,'--output',str(out)]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=c['runtime'],HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',DC_CLUSTER='delta',DC_PYTHON=interpreter)
log=(out/'child.log').open('x');samples=(out/'samples.jsonl').open('x');child=subprocess.Popen(cmd,cwd=c['runtime'],env=env,stdout=log,stderr=log,start_new_session=True);start=time.monotonic();term=None;last=-10
while True:
 pid,status,usage=os.wait4(child.pid,os.WNOHANG);elapsed=time.monotonic()-start
 if pid:break
 if elapsed-last>=5:
  samples.write(json.dumps(dict(elapsed_seconds=elapsed,cgroup=cgroup_snapshot(),host_memory_pressure=Path('/proc/pressure/memory').read_text() if Path('/proc/pressure/memory').exists() else None))+'\n');samples.flush();last=elapsed
 if elapsed>=3300 and term is None:os.killpg(child.pid,signal.SIGTERM);term=elapsed
 if term is not None and elapsed>=term+15:os.killpg(child.pid,signal.SIGKILL)
 time.sleep(.5)
code=os.waitstatus_to_exitcode(status);child.returncode=code;log.close();samples.close();write('child-execution.json',dict(command=cmd,exit_code=code,elapsed_seconds=elapsed,user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,peak_wait4_rss_bytes=usage.ru_maxrss*1024,term_sent_at=term));write('memory-after.json',cgroup_snapshot());write('allocation-after.json',read_current(c['W']))
if code!=0 or term is not None:write('FAILED.json',dict(complete=False,mode=a.mode,automatic_retry=False,exit_code=code));raise SystemExit(1)
result=json.loads((out/'RESULT.json').read_text());assert result['complete'] is False and result['mode']==a.mode and result['environment']==a.environment
result.update(kind='option_A_complete_original_oracle' if a.mode=='original' else 'option_A_complete_candidate_comparison',complete=True,child_exit_code=0,child_result_sha256=sha(out/'RESULT.json'),actual_CPU_allocation=allocation,actual_CPU_wall_seconds=elapsed,actual_CPU_user_seconds=usage.ru_utime,actual_CPU_system_seconds=usage.ru_stime,peak_wait4_rss_bytes=usage.ru_maxrss*1024)
write('COMPLETE_ORACLE.json' if a.mode=='original' else 'COMPLETE_COMPARISON.json',result)
