python3 - <<'PY'
from pathlib import Path
import subprocess,os,json,time,shutil,tempfile,hashlib,ast
p=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-sharded'); outcomes=[]
for name,py in [('base','/sw/external/python/anaconda3/bin/python3.9'),('mgnp','/u/swong2/.conda/envs/mgnp/bin/python')]:
 env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
 cmd=[py,'-B','-m','pytest','-q','-p','no:cacheprovider','--confcutdir='+str(p),'--rootdir='+str(p),'--basetemp=/tmp/a3-r6-final2-green-'+name,str(p/'test_packet.py')]
 started=time.time(); r=subprocess.run(cmd,cwd=str(p),env=env,capture_output=True,text=True,timeout=30)
 (p/'evidence'/('green-'+name+'.log')).write_text(r.stdout+r.stderr)
 row=dict(argv=cmd,exit_code=r.returncode,seconds=time.time()-started,test_sha256=hashlib.sha256((p/'test_packet.py').read_bytes()).hexdigest())
 (p/'evidence'/('green-'+name+'.json')).write_text(json.dumps(row,indent=2)+'\n'); outcomes.append(row)
 print(name,r.returncode,r.stdout[-300:]); assert r.returncode==0
 with tempfile.TemporaryDirectory(prefix='a3-r6-relocated-') as d:
  relocated=Path(d)/'packet';(relocated/'bridges').mkdir(parents=True)
  names=['cpu.sbatch','supervisor.py','bridges/launch.sh','bridges/host.py','bridges/transport229.py']
  for n in names:shutil.copyfile(p/n,relocated/n)
  command=['bash',str(relocated/'cpu.sbatch'),'--dry-run']
  dry=subprocess.run(command,cwd=d,env=dict(env,A3_HOST_PYTHON=py),capture_output=True,text=True,timeout=30)
  row=dict(argv=command,interpreter=py,exit_code=dry.returncode,stdout=dry.stdout,stderr=dry.stderr,copied_files={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names})
  (p/'evidence'/('relocated-'+name+'.json')).write_text(json.dumps(row,indent=2)+'\n'); outcomes.append(row)
  assert dry.returncode==0; print('relocated',name,dry.returncode)
 cmd=[py,'-B',str(p/'run_packet.py'),'--dry-run']
 dry=subprocess.run(cmd,cwd='/tmp',env=env,capture_output=True,text=True,timeout=30)
 row=dict(argv=cmd,exit_code=dry.returncode,stdout=dry.stdout,stderr=dry.stderr)
 (p/'evidence'/('observer-dryrun-'+name+'.json')).write_text(json.dumps(row,indent=2)+'\n');outcomes.append(row)
 print('observer',name,dry.returncode); assert dry.returncode==0,dry.stderr
for n in ['cpu.sbatch','bridges/launch.sh']:
 result=subprocess.run(['bash','-n',str(p/n)],capture_output=True,text=True,timeout=5); assert result.returncode==0
for path in [p/'supervisor.py',p/'bridges/host.py',p/'bridges/inner.py',p/'bridges/transport229.py']:ast.parse(path.read_text(),feature_version=(3,6))
inventory=json.loads((p/'transport-inventory.json').read_text()); assert len(inventory['aliases'])==8
assert all(hashlib.sha256(Path(r['virtual']).read_bytes()).hexdigest()==r['sha256'] for r in inventory['files'])
source={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['source-pins.json','partition.json','transport-inventory.json','bridges/manifest.json','suite/test_a3_prepared_pilot_target.py','run_packet.py','selector.py','aggregate.py','supervisor.py','bridges/host.py']}
(p/'evidence/run_manifest.json').write_text(json.dumps(dict(status='PURE_CHECKS_ONLY',commit=None,baseline_source_commit='538109e809285b6ddc45d42df8786270a65f7b12',source_hashes=source,commands=outcomes,native_acceptance=False,full_suite_accepted=False,execution_authorized=False,actual_jobs=None,actual_configs=None,normal_completion=True,exit_code=0),indent=2)+'\n')
print(json.dumps(source,indent=2))
PY
