from pathlib import Path
import json,subprocess,time,hashlib,sys,shlex,os
Q=Path(__file__).resolve().parent
B=Q/'helper-bindings-continuation-20261106.json';expected='c3eec41b5ca2331ebdb6fa387fa45159894fc8559d09df5e00202030387f09bd'
assert hashlib.sha256(B.read_bytes()).hexdigest()==expected
b=json.loads(B.read_text());c=json.loads(Path(b['gpu_config']['path']).read_text());H=Q.parent.parent/'root-model-phase-release-helper/r5-r2/helper.py'
physical=Path(c['physical_Alignment_root'])/Path(b['GPU_execution_output']).relative_to(c['virtual_Alignment_root'])
end=time.monotonic()+3540
for phase in ('bank','prefix4'):
 print('WAITING_FOR_ACTUAL_GPU_MARKER',phase,flush=True)
 while True:
  if time.monotonic()>=end:raise TimeoutError('bounded root watcher expired; no retry')
  script='import json,subprocess\nfrom pathlib import Path\np=Path('+repr(str(physical))+')\nprint(json.dumps(dict(waiting=(p/'+repr('WAITING-'+phase+'.json')+').is_file(),bank_only=(p/"BANK_ONLY.json").is_file(),failed=(p/"FAILED.json").is_file(),complete=(p/"COMPLETE.json").is_file(),state=subprocess.check_output(["sacct","-j","50189932","-X","-n","-P","-o","State"],universal_newlines=True).strip())))\n'
  r=subprocess.run(b['ssh_argv']+['python3 -'],input=script,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=35)
  if r.returncode:raise RuntimeError(r.stderr)
  x=json.loads(r.stdout)
  if x['failed']:raise RuntimeError('GPU controller failed before '+phase)
  if x['bank_only'] or x['complete']:print('GPU_CONTROL_TERMINAL',json.dumps(x),flush=True);sys.exit(0)
  if x['waiting']:break
  if any(word in x['state'] for word in ('FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','COMPLETED')):print('GPU_SCHEDULER_TERMINAL',json.dumps(x),flush=True);sys.exit(0)
  time.sleep(5)
 assert hashlib.sha256(B.read_bytes()).hexdigest()==expected
 cmd=['/u/swong2/.conda/envs/mgnp/bin/python',str(H),'run-phase','--phase',phase,'--bindings',str(B),'--bindings-sha256',expected,'--execute']
 print('EXECUTING_ONCE_REVIEWED_PHASE_HELPER',phase,flush=True)
 subprocess.run(cmd,check=True,timeout=min(420,max(1,end-time.monotonic())),env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 print('ROOT_PHASE_HELPER_FINISHED',phase,flush=True)
print('BOTH_ROOT_PHASE_PUBLICATIONS_FINISHED',flush=True)
