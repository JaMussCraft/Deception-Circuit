#!/usr/bin/env python3
"""Root Slurm CPU-only dual supported-environment baseline and GREEN observer."""
import argparse,datetime,hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
import xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent
D=P/'closure/sdd';C=D/'plan-a2-full-score-operational186/candidate'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def verify():
    for name in ('packet-pins.json','original-source-pins.json'):
        for path,digest in json.loads((P/name).read_text()).items():
            source=Path(path) if name=='original-source-pins.json' else P/path
            if sha(source)!=digest:raise RuntimeError('immutable source changed: '+str(source))
    snapshot=json.loads((P/'native-snapshot.json').read_text())
    for name,target in snapshot['input_links'].items():
        if os.readlink(str(P/'native-source'/name))!=target:raise RuntimeError('native literal alias changed')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--dry-run',action='store_true');a=parser.parse_args()
    verify();resources=json.loads((P/'resources.json').read_text())
    if a.dry_run:
        print(json.dumps(dict(packet=str(P),packet_pins_sha256=sha(P/'packet-pins.json'),resources=resources,execution=False,normal_environment=True)));return 0
    if not os.environ.get('SLURM_JOB_ID','').isdigit():raise RuntimeError('full/native suite requires root Slurm CPU allocation')
    for key in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS','SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'):
        if os.environ.get(key,'') not in ('','0'):raise RuntimeError('CPU fixture packet rejects GPU allocation')
    output=Path(a.output).resolve();output.mkdir(parents=True,exist_ok=False)
    write(output/'run_manifest.json',dict(kind='UNBOUND_TASK3_CPU_FIXTURES_ONLY',commit='538109e809285b6ddc45d42df8786270a65f7b12',
        source_commit='50e947bb852613e3a270082651f2bd1b7bb0c525',commit_basis='root supplied frozen identity, no worker git',
        host=socket.gethostname(),actual_job_id=os.environ.get('SLURM_JOB_ID'),cluster=os.environ.get('SLURM_CLUSTER_NAME'),
        Slurm_env={k:os.environ.get(k) for k in ('SLURM_JOB_ID','SLURM_CPUS_PER_TASK','SLURM_MEM_PER_NODE','SLURM_JOB_PARTITION')},
        packet_pins_sha256=sha(P/'packet-pins.json'),original_source_pins_sha256=sha(P/'original-source-pins.json'),
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),resources=resources))
    observations=[]
    original=['test_full_score_release.py','test_full_score_cache.py','test_full_score_usage.py']
    accepted=['test_full_score_controller.py','test_full_score_entry198.py','test_full_score_cpu.py']
    for target in resources['interpreters']:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
            CUDA_VISIBLE_DEVICES='',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',A2_TASK3_ACCEPTED=str(C),A2_CPU_UNDER_TEST=str(C/'cpu'),
            A2_TASK3_FIXTURES=str(D/'plan-plan-a2-full-score-operational186/task1'),
            A2_GREEN_OBSERVER=str(P/'observer/run_cpu_green.py'),A2_TASK3_NATIVE_SOURCE=str(P/'native-source'))
        env.pop('PYTHONPATH',None)
        for key in list(env):
            if key.startswith('A2_FULL_SCORE_'):env.pop(key)
        identity_program="import sys,json,pytest;print(json.dumps({'python':sys.version,'minor':list(sys.version_info[:2]),'pytest':pytest.__version__,'pytest_origin':pytest.__file__,'optimize':sys.flags.optimize}))"
        identity=json.loads(subprocess.check_output([target['python'],'-B','-c',identity_program],cwd=str(output),env=env,universal_newlines=True,timeout=15))
        if identity['pytest']!=target['pytest'] or identity['minor']!=target['python_minor'] or identity['optimize']!=0:
            raise RuntimeError('unsupported interpreter identity: '+json.dumps(identity))
        write(output/(target['label']+'-identity.json'),identity)
        for mode in ('RED','GREEN'):
            verify();label=target['label']+'-'+mode;xml=output/(label+'.xml')
            tests=original if mode=='RED' else accepted+original+['test_full_score_root_integration.py','test_full_score_root_wait.py']
            env['A2_ROOT_UNDER_TEST']=str(P/'historical-root' if mode=='RED' else C/'root')
            argv=[target['python'],'-B','-m','pytest','-c','/dev/null','--confcutdir='+str(C/'tests'),'-p','no:cacheprovider',
                '--basetemp='+str(output/(label+'-tmp')),'--junitxml='+str(xml),'-q','--tb=short']+[str(C/'tests'/name) for name in tests]
            started=time.monotonic()
            try:
                with (output/(label+'.log')).open('x') as log:
                    result=subprocess.run(argv,cwd=str(output),env=env,stdout=log,stderr=subprocess.STDOUT,check=False,
                        timeout=resources['baseline_timeout_seconds' if mode=='RED' else 'full_timeout_seconds'])
                cases=list(ET.parse(str(xml)).getroot().iter('testcase'))
                failed=[c.get('name') for c in cases if c.find('failure') is not None]
                errors=[c.get('name') for c in cases if c.find('error') is not None]
                skipped=[c.get('name') for c in cases if c.find('skipped') is not None]
                passed=len(cases)-len(failed)-len(errors)-len(skipped)
                ok=(len(cases)==resources['expected_baseline_cases'] and result.returncode==1 and failed and passed>0) if mode=='RED' else (
                    len(cases)==resources['expected_GREEN_cases'] and result.returncode==0 and not failed)
                ok=bool(ok and not errors and not skipped)
                observations.append(dict(environment=target['label'],mode=mode,identity=identity,argv=argv,exit_code=result.returncode,
                    tests=len(cases),failures=len(failed),errors=len(errors),skips=len(skipped),passed=passed,failed_names=failed,
                    error_names=errors,seconds=time.monotonic()-started,junit_sha256=sha(xml),expected=ok))
            except BaseException as error:
                observations.append(dict(environment=target['label'],mode=mode,expected=False,error=repr(error),seconds=time.monotonic()-started))
            verify()
    ok=all(o['expected'] for o in observations)
    result=dict(complete=ok,status='TASK3_DUAL_NORMAL_RED_GREEN_OBSERVED' if ok else 'FAIL',
        actual_job_id=os.environ['SLURM_JOB_ID'],cluster=os.environ.get('SLURM_CLUSTER_NAME'),observations=observations,
        actual_model_or_GPU_authority=False,resource_bindings=False)
    write(output/'RESULT.json',result);print(json.dumps(result));return 0 if ok else 1
if __name__=='__main__':sys.exit(main())
