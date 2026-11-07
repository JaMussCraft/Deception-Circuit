"""Bounded fixture GREEN observer; root dispatches CPU only, no native import."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PACKET = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green')
W = PACKET.parents[4]
TESTS = W / '.superpowers/sdd/plan-a2-full-score-operational186/candidate/tests'
PYTHONS = ['/sw/external/python/anaconda3/bin/python3.9','/u/swong2/.conda/envs/mgnp/bin/python']


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False); stream.write('\n')


def pins(expected):
    assert sha(PACKET/'pins.json') == expected, 'GREEN pin manifest changed'
    value = json.loads((PACKET/'pins.json').read_text())
    for path,wanted in value['files'].items(): assert sha(path) == wanted, ('GREEN member/source changed',path)
    return value


def command(python,out,n):
    return [python,'-m','pytest','-q','-p','no:cacheprovider','--noconftest',
        '--confcutdir='+str(TESTS),'--tb=short','--junitxml='+str(out/('env%d.xml'%n)),
        '--basetemp='+str(out/('tmp-env%d'%n)),str(TESTS/'test_full_score_cpu.py'),str(TESTS/'test_full_score_controller.py')]


def bounded(cmd,env,stdout,stderr):
    child = subprocess.Popen(cmd,env=env,stdout=stdout,stderr=stderr,cwd=str(TESTS),start_new_session=True)
    try: return child.wait(timeout=90)
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired: os.killpg(child.pid,signal.SIGKILL); child.wait(timeout=5)
        raise


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output',required=True)
    parser.add_argument('--pins-sha256',required=True); parser.add_argument('--dry-run',action='store_true')
    args = parser.parse_args(); out = Path(args.output); assert out.is_absolute()
    expected = pins(args.pins_sha256); commands = [command(p,out,n) for n,p in enumerate(PYTHONS,1)]
    if args.dry_run:
        print(json.dumps(dict(commands=commands,timeout_seconds_per_environment=90,expected_cases=204,
            Task2=107,accepted_Task1_regressions=97,no_native_import=True,no_model=True,no_GPU=True),indent=2)); return
    assert os.environ.get('SLURM_JOB_ID') and os.environ.get('SLURM_CLUSTER_NAME') == 'delta'
    assert not any(os.environ.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS'))
    assert all(os.environ.get(k,'') in ('','0') for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'))
    assert int(os.environ.get('SLURM_CPUS_PER_TASK','0')) >= 2
    out.mkdir(parents=True,exist_ok=False); start = time.time()
    allocation = subprocess.check_output(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'],universal_newlines=True,timeout=15)
    fields = dict(x.split('=',1) for x in allocation.split() if '=' in x)
    assert fields['JobId'] == os.environ['SLURM_JOB_ID'] and fields['JobState'] == 'RUNNING'
    assert fields['Partition'] in ('cpu','cpu-interactive') and fields['Account'].endswith('-cpu') and fields['NumNodes'] == '1'
    assert not any(x.startswith('gres/gpu') for x in fields.get('AllocTRES','').split(','))
    write(out/'allocation.json',dict(actual_job_id=os.environ['SLURM_JOB_ID'],cluster='delta',host=socket.gethostname(),scontrol_job=allocation,fields=fields))
    env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
        CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    observations=[]
    for n,(python,cmd) in enumerate(zip(PYTHONS,commands),1):
        info=json.loads(subprocess.check_output([python,'-c',
            'import json,sys,pytest; print(json.dumps({"python":list(sys.version_info[:3]),"executable":sys.executable,"pytest":pytest.__version__}))'],
            env=env,universal_newlines=True,timeout=15))
        assert info['python'][:2] == ([3,9] if n==1 else [3,12]),info
        with (out/('env%d.stdout'%n)).open('x') as stdout,(out/('env%d.stderr'%n)).open('x') as stderr:
            code=bounded(cmd,env,stdout,stderr)
        cases=list(ET.parse(str(out/('env%d.xml'%n))).iter('testcase'))
        failures=[c for c in cases if c.find('failure') is not None]
        errors=[c for c in cases if c.find('error') is not None]
        skipped=[c for c in cases if c.find('skipped') is not None]
        value=dict(environment=info,exit_code=code,tests=len(cases),failures=len(failures),errors=len(errors),
            skips=len(skipped),command=cmd,test_names=[c.attrib['name'] for c in cases])
        write(out/('env%d-result.json'%n),value); observations.append(value)
    pins(args.pins_sha256)
    passed=all(o['exit_code']==0 and o['tests']==204 and o['failures']==o['errors']==o['skips']==0 for o in observations)
    value=dict(status='TASK2_GREEN_OBSERVED' if passed else 'TASK2_GREEN_REJECTED',complete=passed,
        actual_job_id=os.environ['SLURM_JOB_ID'],cluster='delta',host=socket.gethostname(),observations=observations,
        pins_sha256=args.pins_sha256,elapsed_seconds=time.time()-start,source_commit=expected['source_commit'],
        no_native_import=True,no_model=True,no_GPU=True,scientific_execution_authorized=False)
    write(out/'RESULT.json',value)
    assert passed,value
    assert observations[0]['test_names']==observations[1]['test_names']
    print(json.dumps(value,indent=2))


if __name__=='__main__': main()
