from pathlib import Path
import json,hashlib,subprocess,os,tempfile,shutil,ast,time
S=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');P=S/'plan/task23-green-r6-sharded';O=S/'plan-a3/sharded-validation-root-check271';O.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'source-pins.json')=='25c817e97f7ae276ac49a6f5194c3741885c830df6863e8f2dc0c11be3a1b77f'
assert sha(P/'partition.json')=='0fdb618b919c0622f13cb3bb4af29ffad32df42ee6bfe92dc531a1d73b02a72a'
rows=[]
bootstrap=O/'bootstrap.sh';bootstrap.write_text('#!/bin/bash\nset -euo pipefail\nexec bash '+str(P/'cpu.sbatch')+' --dry-run\n')
for label,py in [('base','/sw/external/python/anaconda3/bin/python3.9'),('mgnp','/u/swong2/.conda/envs/mgnp/bin/python')]:
 env=dict(os.environ,A3_HOST_PYTHON=py,PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
 with tempfile.TemporaryDirectory(prefix='r6-real-spool-') as d:
  spool=Path(d)/'slurm_script';shutil.copyfile(bootstrap,spool)
  for kind,cmd in [('relocated_root_bootstrap',['bash',str(spool)]),('source_bound_observer',[py,'-B',str(P/'run_packet.py'),'--dry-run'])]:
   start=time.monotonic();r=subprocess.run(cmd,cwd=d,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30)
   row=dict(label=label,kind=kind,argv=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,seconds=time.monotonic()-start,bootstrap_sha256=sha(bootstrap));rows.append(row)
   with(O/(label+'-'+kind+'.json')).open('x') as f:json.dump(row,f,indent=2)
   assert r.returncode==0,row;print(label,kind,'passed',round(row['seconds'],3),flush=True)
for name in ['cpu.sbatch','bridges/launch.sh']:subprocess.run(['bash','-n',str(P/name)],check=True,timeout=5)
for name in ['supervisor.py','bridges/host.py','bridges/inner.py','bridges/transport229.py']:ast.parse((P/name).read_text(),feature_version=(3,6))
inventory=json.loads((P/'transport-inventory.json').read_text());assert len(inventory['aliases'])==8
for row in inventory['files']:assert sha(Path(row['virtual']))==row['sha256'],row['virtual']
with(O/'RESULT.json').open('x') as f:json.dump(dict(kind='ROOT_PURE_WRAPPER_AND_PIN_CHECK_ONLY',source_pins_sha256=sha(P/'source-pins.json'),partition_sha256=sha(P/'partition.json'),inventory_files=len(inventory['files']),aliases=8,commands=rows,host_python36_syntax=True,no_native_or_scheduler_execution=True,builder_evidence_unchanged=True),f,indent=2)
print('completed source/AST/spool checks; no native suite or job ran')
