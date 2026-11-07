from pathlib import Path
import json,subprocess,hashlib,os,sys,time
D=Path(__file__).parent;Q=json.loads((D/'remedy.json').read_text());W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');R=W/'outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime';O=Path(Q['fresh_root']);OLD=W/'outputs/_analyses/specificity-ladder/a2-analysis/all18-40fe57289405-v1'
assert os.environ.get('SLURM_JOB_ID') and not O.exists() and not O.is_symlink();started=time.time()
raw=subprocess.run(['scontrol','-o','show','job',os.environ['SLURM_JOB_ID']],check=True,stdout=subprocess.PIPE,text=True).stdout;f=dict(t.split('=',1) for t in raw.split() if '=' in t);assert f['JobState']=='RUNNING' and f['Partition'].startswith('cpu') and 'gres/gpu' not in f['AllocTRES']
(D/'allocation.json').write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'node':os.uname().nodename,'scontrol':raw,'gpus':0},indent=2)+'\n')
env=dict(os.environ,DC_PYTHON='/u/swong2/.conda/envs/mgnp/bin/python',DC_CLUSTER='delta',DC_RUN_MANIFEST_GIT='0',PYTHONPATH=str(R),HF_HOME='/work/nvme/beto/swong2',HF_HUB_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (D/'freeze.stdout').open('x') as out,(D/'freeze.stderr').open('x') as err:r=subprocess.run(Q['command'],cwd=R,env=env,stdout=out,stderr=err)
(D/'command-result.json').write_text(json.dumps({'command':Q['command'],'exit_code':r.returncode,'job_id':os.environ['SLURM_JOB_ID'],'elapsed_seconds':time.time()-started},indent=2)+'\n');assert r.returncode==0
sys.path.insert(0,str(R));os.chdir(R)
from component_analysis import ladder_pipeline as a1,a2_pipeline as p
old=a1.read_artifact(OLD/'groups.json');new=a1.read_artifact(O/'groups.json');p.validate_receipt(new)
differing=[k for k in set(old)|set(new) if old.get(k)!=new.get(k)];assert set(differing)=={'grader_registry','receipt_sha256'},differing
assert old['groups']==new['groups'] and len(new['groups'])==9 and new['grader_registry']==a1.grader_registry()
summary={'source_commit':'40fe57289405fd53a3fce02e5d4e47a0ebf78b64','job_id':os.environ['SLURM_JOB_ID'],'old_root':str(OLD),'new_root':str(O),'changed_payload_fields':differing,'all_scientific_fields_and_memberships_equal':True,'group_aliases':9,'old_groups_sha256':hashlib.sha256((OLD/'groups.json').read_bytes()).hexdigest(),'new_groups_sha256':hashlib.sha256((O/'groups.json').read_bytes()).hexdigest(),'new_receipt_sha256':new['receipt_sha256'],'new_grader_registry':new['grader_registry'],'old_artifact_preserved':True,'models_loaded':False,'GPU_admission':False}
(D/'COMPLETE.json').write_text(json.dumps(summary,indent=2)+'\n');print('FRESH_PROSPECTIVE_GROUPS_SCIENTIFICALLY_IDENTICAL')
