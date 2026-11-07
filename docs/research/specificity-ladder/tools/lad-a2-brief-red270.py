from pathlib import Path
import json,subprocess,time,hashlib,os,socket,importlib.util,xml.etree.ElementTree as ET
S=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');P=S/'plan-plan-a2-full-score-operational186/task3/red259';O=S/'plan-plan-a2-full-score-operational186/task3/brief-orchestration-red270';O.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('red259_metadata',P/'run_red.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.verify()
nodes=['test_full_score_release.py::test_request_generated_from_actual_Task1_WAITING_accepted_by_actual_Task2','test_full_score_release.py::test_actual_Task2_COMPLETE_is_read_only_and_valid_full_domain','test_full_score_release.py::test_existing_composite_schema_passes_actual_Task1_consumer','test_full_score_release.py::test_budget_retains_cancelled_charge_and_accepts_reviewed_two_hour_duration','test_full_score_release.py::test_actual_generated_remote_program_publishes_full_only_reviewed_resources','test_full_score_usage.py::test_ordinary80_cannot_be_bypassed_by_old_exception','test_full_score_cache.py::test_metadata_hashed_every_weight_sized_and_blob_bound_no_full_rehash']
rows=[]
for label,py in [('base','/sw/external/python/anaconda3/bin/python3.9'),('mgnp','/u/swong2/.conda/envs/mgnp/bin/python')]:
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',A2_ROOT_UNDER_TEST=str(P/'historical-root'),A2_TASK3_ACCEPTED=str(P/'accepted'),A2_TASK3_FIXTURES=str(P/'task1'),A2_CPU_UNDER_TEST=str(P/'accepted/cpu'))
 for k in list(env):
  if k.startswith('A2_FULL_SCORE_'):env.pop(k)
 xml=O/(label+'.xml');a=[py,'-B','-I','-m','pytest','-c','/dev/null','--confcutdir='+str(P/'tests'),'-p','no:cacheprovider','--basetemp='+str(O/(label+'-tmp')),'--junitxml='+str(xml),'-q','--tb=short']+[str(P/'tests'/n.split('::')[0])+'::'+n.split('::')[1] for n in nodes]
 t=time.monotonic()
 with(O/(label+'.log')).open('x') as f:r=subprocess.run(a,cwd=O,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=12)
 cases=ET.parse(xml).getroot().findall('.//testcase');result=[dict(name=c.attrib['name'],outcome='failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed',message=None if c.find('failure') is None else c.find('failure').attrib.get('message')) for c in cases]
 rows.append(dict(environment=label,python=py,argv=a,exit_code=r.returncode,seconds=time.monotonic()-t,cases=result,junit_sha256=hashlib.sha256(xml.read_bytes()).hexdigest()));m.verify()
result=dict(kind='BRIEF_PURE_ORCHESTRATION_BASELINE_ONLY',host=socket.gethostname(),actual_job_id=None,cluster='local brief-check allowance; not Slurm evidence',selected_nodes=nodes,results=rows,full_RED_job_still_required='23625160',full_Task3_or_native_or_GPU_acceptance=False)
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k not in ('argv','cases')}|{'cases':len(r['cases']),'outcomes':{x:sum(c['outcome']==x for c in r['cases']) for x in ['failed','passed','error','skipped']}} for r in rows]))
