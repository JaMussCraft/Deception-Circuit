import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
plan=json.loads((ROOT/'plan.json').read_text())
assert os.environ.get('SLURM_JOB_ID','').isdigit()
assert not os.environ.get('CUDA_VISIBLE_DEVICES','')
assert int(os.environ['SLURM_CPUS_PER_TASK'])>=2
out=ROOT/'execution';out.mkdir(exist_ok=False)
record={'status':'RUNNING_INDEPENDENT_TEST_PACKETS','job_id':os.environ['SLURM_JOB_ID'],'cluster':os.environ.get('SLURM_CLUSTER_NAME'),'started_unix':time.time(),'gpu':False,'execution_authority':False,'phases':{}}
def save():
 p=out/'RESULT.json';t=out/'RESULT.pending';t.write_text(json.dumps(record,indent=2)+'\n');os.replace(str(t),str(p))
save()
for phase in plan['phases']:
 assert hashlib.sha256(Path(phase['pin_file']).read_bytes()).hexdigest()==phase['pin_sha256']
 assert not Path(phase['output']).exists()
 row={'argv':phase['argv'],'pin_sha256':phase['pin_sha256'],'started_unix':time.time(),'output':phase['output'],'status':'RUNNING'};record['phases'][phase['name']]=row;save()
 with (out/(phase['name']+'.stdout')).open('xb') as stdout,(out/(phase['name']+'.stderr')).open('xb') as stderr:
  child=subprocess.run(phase['argv'],stdout=stdout,stderr=stderr)
 row.update(exit_code=child.returncode,finished_unix=time.time(),status='OBSERVER_EXITED');save()
record.update(status='TEST_PACKETS_TERMINAL',finished_unix=time.time(),exit_code=0 if all(x['exit_code']==0 for x in record['phases'].values()) else 1);save()
raise SystemExit(record['exit_code'])
