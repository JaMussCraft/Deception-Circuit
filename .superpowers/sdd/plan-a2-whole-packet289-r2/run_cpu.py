#!/usr/bin/env python3
"""Root-dispatched bounded CPU observer for only Task4's new integration cases."""
import argparse
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

P=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def verify():
    for path,digest in read(P/'packet-pins.json').items():
        if sha(P/path)!=digest:raise RuntimeError('Task4 packet member changed: '+path)
    d=read(P/'dependencies.json');frozen=Path(d['frozen_task3_packet'])
    for name,key in [('packet-pins.json','task3_packet_pins_sha256'),('original-source-pins.json','task3_original_source_pins_sha256')]:
        if sha(frozen/name)!=d[key]:raise RuntimeError('frozen dependency pin manifest changed: '+name)
        for path,digest in read(frozen/name).items():
            target=Path(path) if name=='original-source-pins.json' else frozen/path
            if sha(target)!=digest:raise RuntimeError('frozen dependency bytes changed: '+str(target))
    snapshot=read(frozen/'native-snapshot.json');source=Path(d['original_runtime'])
    if str(source)!=snapshot['runtime_root']:raise RuntimeError('original runtime namespace mismatch')
    for name,digest in snapshot['source_sha256'].items():
        if sha(source/name)!=digest:raise RuntimeError('original source byte changed: '+name)
    for name,target in snapshot['input_links'].items():
        if os.readlink(str(source/name))!=target:raise RuntimeError('original source alias changed: '+name)
    for path in (P/'run_cpu.py',P/'candidate/tests/test_full_score_integration.py'):
        ast.parse(path.read_text(),filename=str(path))
    return d

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--dry-run',action='store_true');a=parser.parse_args()
    d=verify();proposal=read(P/'candidate/proposal.json')
    if a.dry_run:
        print(json.dumps(dict(packet=str(P),packet_pins_sha256=sha(P/'packet-pins.json'),
            new_integration_cases=32,CPU_test_proposal=proposal['CPU_test_proposal'],execution=False,native_imports=False)))
        return 0
    if not os.environ.get('SLURM_JOB_ID','').isdigit():raise RuntimeError('native integration requires root Slurm CPU allocation')
    for key in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS','SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'):
        if os.environ.get(key,'') not in ('','0'):raise RuntimeError('fixture observer rejects GPUs')
    output=Path(a.output).resolve()
    if not output.is_relative_to(Path(d['alignment_root'])) or output==Path(d['alignment_root']):
        raise RuntimeError('fixture physical namespace requires fresh output beneath Alignment')
    output.mkdir(parents=True,exist_ok=False)
    write(output/'run_manifest.json',dict(kind='SYNTHETIC_TASK4_CPU_INTEGRATION_ONLY',
        commit=d['root_supplied_worktree_commit'],commit_basis='root supplied, worker never runs git',
        source_commit=d['original_source_commit'],actual_job_id=os.environ['SLURM_JOB_ID'],
        cluster=os.environ.get('SLURM_CLUSTER_NAME'),host=socket.gethostname(),
        Slurm_env={k:os.environ.get(k) for k in ('SLURM_JOB_ID','SLURM_CPUS_PER_TASK','SLURM_MEM_PER_NODE','SLURM_JOB_PARTITION')},
        packet_pins_sha256=sha(P/'packet-pins.json'),dependencies=d,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_authority=False))
    observations=[];test=P/'candidate/tests/test_full_score_integration.py'
    for target in proposal['CPU_test_proposal']['interpreters']:
        verify();label=target['label'];xml=output/(label+'.xml')
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='',
            OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
        env.pop('PYTHONPATH',None)
        for key in list(env):
            if key.startswith('A2_FULL_SCORE_') or key.startswith('A2_TASK3_') or key in ('A2_ROOT_UNDER_TEST','A2_CPU_UNDER_TEST'):
                env.pop(key)
        identity_program="import json,sys,pytest;print(json.dumps({'python':sys.version,'minor':list(sys.version_info[:2]),'pytest':pytest.__version__,'pytest_origin':pytest.__file__,'optimize':sys.flags.optimize}))"
        identity=json.loads(subprocess.check_output([target['python'],'-B','-c',identity_program],cwd=str(output),env=env,universal_newlines=True,timeout=15))
        if identity['minor']!=target['python_minor'] or identity['pytest']!=target['pytest'] or identity['optimize']!=0:
            raise RuntimeError('unsupported normal interpreter identity: '+json.dumps(identity))
        write(output/(label+'-identity.json'),identity)
        argv=[target['python'],'-B','-m','pytest','-c','/dev/null','--rootdir='+str(P/'candidate/tests'),
            '--confcutdir='+str(P/'candidate/tests'),'-p','no:cacheprovider',
            '--basetemp='+str(output/(label+'-tmp')),'--junitxml='+str(xml),'-q','--tb=short',str(test)]
        started=time.monotonic()
        try:
            with (output/(label+'.log')).open('x') as log:
                result=subprocess.run(argv,cwd=str(output),env=env,stdout=log,stderr=subprocess.STDOUT,
                    check=False,timeout=proposal['CPU_test_proposal']['per_environment_timeout_seconds'])
            cases=list(ET.parse(str(xml)).getroot().iter('testcase'))
            failed=[c.get('name') for c in cases if c.find('failure') is not None]
            errors=[c.get('name') for c in cases if c.find('error') is not None]
            skipped=[c.get('name') for c in cases if c.find('skipped') is not None]
            passed=len(cases)-len(failed)-len(errors)-len(skipped)
            observations.append(dict(environment=label,identity=identity,argv=argv,exit_code=result.returncode,
                tests=len(cases),passed=passed,failed_names=failed,error_names=errors,skipped_names=skipped,
                elapsed_seconds=time.monotonic()-started,junit_sha256=sha(xml),
                complete=result.returncode==0 and len(cases)==32 and passed==32))
        except BaseException as error:
            observations.append(dict(environment=label,complete=False,error=repr(error),elapsed_seconds=time.monotonic()-started))
        verify()
    complete=len(observations)==2 and all(o['complete'] for o in observations)
    result=dict(complete=complete,status='SYNTHETIC_TASK4_GREEN' if complete else 'FAIL',observations=observations,
        actual_job_id=os.environ['SLURM_JOB_ID'],cluster=os.environ.get('SLURM_CLUSTER_NAME'),
        scientific_rows_produced=0,actual_GPU_authority=False,actual_resource_bindings=False)
    write(output/'RESULT.json',result);print(json.dumps(result));return 0 if complete else 1
if __name__=='__main__':sys.exit(main())
