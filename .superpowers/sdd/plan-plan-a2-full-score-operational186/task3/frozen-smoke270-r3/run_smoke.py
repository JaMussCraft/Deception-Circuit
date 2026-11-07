"""Three pure cases per interpreter; not a complete/native suite."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess,time
import xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent
P=OUT.parent/'green270-r3';C=P/'closure/sdd/plan-a2-full-score-operational186/candidate'
spec=importlib.util.spec_from_file_location('frozen_observer',str(P/'run_cpu_green.py'));observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
observer.verify()
manifest=dict(kind='BRIEF_PURE_FROZEN_ORCHESTRATION_SMOKE_ONLY',commit='538109e809285b6ddc45d42df8786270a65f7b12',
    source_commit='50e947bb852613e3a270082651f2bd1b7bb0c525',actual_job_id=None,
    cluster='local brief-check allowance',packet_pins_sha256=observer.sha(P/'packet-pins.json'),
    original_source_pins_sha256=observer.sha(P/'original-source-pins.json'),
    source_pin_check_before_run=True,native_imports=False,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
rows=[]
for label,python in [('base39','/sw/external/python/anaconda3/bin/python3.9'),('mgnp','/u/swong2/.conda/envs/mgnp/bin/python')]:
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',A2_ROOT_UNDER_TEST=str(C/'root'),A2_TASK3_ACCEPTED=str(C),A2_CPU_UNDER_TEST=str(C/'cpu'),
        A2_TASK3_FIXTURES=str(P/'closure/sdd/plan-plan-a2-full-score-operational186/task1'))
    env.pop('PYTHONPATH',None)
    for k in list(env):
        if k.startswith('A2_FULL_SCORE_'):env.pop(k)
    identity=json.loads(subprocess.check_output([python,'-B','-c',"import sys,pytest,json;print(json.dumps({'python':sys.version,'pytest':pytest.__version__,'pytest_origin':pytest.__file__}))"],env=env,universal_newlines=True,timeout=10))
    args=[python,'-B','-m','pytest','-c','/dev/null','--confcutdir='+str(C/'tests'),'-p','no:cacheprovider','--basetemp='+str(OUT/(label+'-tmp')),
        '--junitxml='+str(OUT/(label+'.xml')),'-q','--tb=short',str(C/'tests/test_full_score_root_identity.py'),
        str(C/'tests/test_full_score_root_integration.py')+'::test_full_fake_transport_keeps_CPU_immutable_and_fails_closed_on_transfer_drift[None]']
    start=time.monotonic()
    with (OUT/(label+'.log')).open('x') as log:result=subprocess.run(args,env=env,cwd=str(OUT),stdout=log,stderr=subprocess.STDOUT,timeout=20,check=False)
    cases=list(ET.parse(str(OUT/(label+'.xml'))).getroot().iter('testcase'))
    failures=[c.get('name') for c in cases if any(c.find(k) is not None for k in ('failure','error','skipped'))]
    rows.append(dict(label=label,argv=args,identity=identity,seconds=time.monotonic()-start,exit_code=result.returncode,cases=len(cases),failed_or_skipped=failures))
    observer.verify()
result=dict(status='PASS' if all(r['exit_code']==0 and r['cases']==3 and not r['failed_or_skipped'] for r in rows) else 'FAIL',
    expected_cases_each=3,observations=rows,full_suite_run=False,native_suite_run=False,source_pin_check_after_run=True)
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
