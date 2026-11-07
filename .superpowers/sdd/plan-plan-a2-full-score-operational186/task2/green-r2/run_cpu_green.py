"""One root CPU packet: preserved-candidate regression RED then corrected GREEN."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import xml.etree.ElementTree as ET

PACKET = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r2')
TASK2 = PACKET.parent
W = PACKET.parents[4]
CANDIDATE = W/'.superpowers/sdd/plan-a2-full-score-operational186/candidate'
TESTS = CANDIDATE/'tests'
BASELINE = TASK2/'green/root-dispatch/candidate-before-interface-review'
PYTHONS = ['/sw/external/python/anaconda3/bin/python3.9','/u/swong2/.conda/envs/mgnp/bin/python']


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def pins(expected):
    assert sha(PACKET/'pins.json') == expected,'r2 pins changed'
    value=json.loads((PACKET/'pins.json').read_text())
    for path,wanted in value['files'].items(): assert sha(path)==wanted,('r2 member/source changed',path)
    for name,wanted in json.loads((BASELINE/'manifest.json').read_text()).items():
        assert sha(BASELINE/name)==wanted,('preserved candidate changed',name)
    return value


def command(python,out,n,mode='green'):
    paths=[str(TESTS/'test_full_score_cpu.py')]
    if mode=='green': paths.extend([str(TESTS/'test_full_score_controller.py'),str(TESTS/'test_full_score_entry198.py')])
    cmd=[python,'-m','pytest','-q','-p','no:cacheprovider','--noconftest','--confcutdir='+str(TESTS),
         '--tb=short','--junitxml='+str(out/('%s-env%d.xml'%(mode,n))),
         '--basetemp='+str(out/('tmp-%s-env%d'%(mode,n)))]+paths
    if mode=='red': cmd.extend(['-k','review224'])
    return cmd


def bounded(cmd,env,stdout,stderr,seconds):
    child=subprocess.Popen(cmd,env=env,stdout=stdout,stderr=stderr,cwd=str(TESTS),start_new_session=True)
    try:return child.wait(timeout=seconds)
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
        raise


def observe(cmd,env,out,mode,n,seconds):
    with (out/('%s-env%d.stdout'%(mode,n))).open('x') as stdout,(out/('%s-env%d.stderr'%(mode,n))).open('x') as stderr:
        code=bounded(cmd,env,stdout,stderr,seconds)
    cases=list(ET.parse(str(out/('%s-env%d.xml'%(mode,n)))).iter('testcase'))
    failed=[c.attrib['name'] for c in cases if c.find('failure') is not None]
    errors=[c.attrib['name'] for c in cases if c.find('error') is not None]
    skipped=[c.attrib['name'] for c in cases if c.find('skipped') is not None]
    value=dict(mode=mode,exit_code=code,tests=len(cases),failures=len(failed),errors=len(errors),skips=len(skipped),
        failed_names=failed,test_names=[c.attrib['name'] for c in cases],command=cmd)
    write(out/('%s-env%d-result.json'%(mode,n)),value)
    return value


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--pins-sha256',required=True);ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args();out=Path(args.output);assert out.is_absolute()
    expected=pins(args.pins_sha256)
    commands={mode:[command(p,out,n,mode) for n,p in enumerate(PYTHONS,1)] for mode in ('red','green')}
    if args.dry_run:
        print(json.dumps(dict(commands=commands,baseline_CPU=str(BASELINE/'cpu'),corrected_CPU=str(CANDIDATE/'cpu'),
            red_cases=22,red_required_failures=20,red_expected_passes=2,green_cases=226,original_Task2=107,
            review224_added=22,accepted_controller=82,accepted_entry198=15,
            red_timeout_seconds_per_environment=30,green_timeout_seconds_per_environment=90,
            no_native_import=True,no_model=True,no_GPU=True),indent=2));return
    assert os.environ.get('SLURM_JOB_ID') and os.environ.get('SLURM_CLUSTER_NAME')=='delta'
    assert not any(os.environ.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS'))
    assert all(os.environ.get(k,'') in ('','0') for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'))
    assert int(os.environ.get('SLURM_CPUS_PER_TASK','0'))>=2
    out.mkdir(parents=True,exist_ok=False);started=time.time()
    raw=subprocess.check_output(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'],universal_newlines=True,timeout=15)
    fields=dict(x.split('=',1) for x in raw.split() if '=' in x)
    assert fields['JobId']==os.environ['SLURM_JOB_ID'] and fields['JobState']=='RUNNING'
    assert fields['Partition'] in ('cpu','cpu-interactive') and fields['Account'].endswith('-cpu') and fields['NumNodes']=='1'
    assert not any(x.startswith('gres/gpu') for x in fields.get('AllocTRES','').split(','))
    write(out/'allocation.json',dict(actual_job_id=os.environ['SLURM_JOB_ID'],cluster='delta',host=socket.gethostname(),scontrol_job=raw,fields=fields))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
        MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    versions=[]
    for n,python in enumerate(PYTHONS,1):
        info=json.loads(subprocess.check_output([python,'-c',
            'import json,sys,pytest; print(json.dumps({"python":list(sys.version_info[:3]),"executable":sys.executable,"pytest":pytest.__version__}))'],
            env=env,universal_newlines=True,timeout=15))
        assert info['python'][:2]==([3,9] if n==1 else [3,12]);versions.append(info)
    observations=[]
    # All RED observations precede any corrected suite in this same allocation.
    for mode,seconds in (('red',30),('green',90)):
        mode_env=dict(env,A2_CPU_UNDER_TEST=str((BASELINE if mode=='red' else CANDIDATE)/'cpu'),
            A2_GREEN_OBSERVER=str(TASK2/'green/run_cpu_green.py' if mode=='red' else PACKET/'run_cpu_green.py'))
        current=[]
        for n,cmd in enumerate(commands[mode],1):
            item=observe(cmd,mode_env,out,mode,n,seconds);item['environment']=versions[n-1];current.append(item);observations.append(item)
        pins(args.pins_sha256)
        if mode=='red':
            accepted=all(o['exit_code']==1 and o['tests']==22 and o['failures']==20 and o['errors']==o['skips']==0 for o in current)
            required={
                'test_review224_actual_Task1_marker_is_accepted_without_renaming[1300.0-1250.0]',
                'test_review224_actual_Task1_marker_is_accepted_without_renaming[1140.0-1125.0]',
                'test_review224_actual_422_manifest_preserves_all_eleven_aliases[None]',
                'test_review224_actual_Task2_COMPLETE_satisfies_actual_Task1_consumer[None]',
                'test_review224_marker_swap_never_reaches_Popen_or_extends_deadline[decoded-buffer]',
                'test_review224_marker_swap_never_reaches_Popen_or_extends_deadline[before-Popen]',
                'test_review224_GREEN_command_includes_original107_and_all_accepted97'}
            accepted=accepted and all(required<=set(o['failed_names']) for o in current)
            write(out/'RED-RESULT.json',dict(complete=accepted,observations=current,baseline=str(BASELINE),baseline_immutable=True))
        else:
            accepted=all(o['exit_code']==0 and o['tests']==226 and o['failures']==o['errors']==o['skips']==0 for o in current)
        accepted=accepted and current[0]['test_names']==current[1]['test_names']
        if not accepted:
            write(out/'RESULT.json',dict(complete=False,status=mode.upper()+'_REJECTED',actual_job_id=os.environ['SLURM_JOB_ID'],
                observations=observations,pins_sha256=args.pins_sha256,no_model=True,no_GPU=True))
            raise AssertionError('attributable '+mode+' not observed; preserve all evidence; no automatic retry')
    value=dict(complete=True,status='TASK2_R224_RED_THEN_GREEN_OBSERVED',actual_job_id=os.environ['SLURM_JOB_ID'],cluster='delta',
        host=socket.gethostname(),observations=observations,pins_sha256=args.pins_sha256,elapsed_seconds=time.time()-started,
        source_commit=expected['source_commit'],no_native_import=True,no_model=True,no_GPU=True,scientific_execution_authorized=False)
    write(out/'RESULT.json',value);print(json.dumps(value,indent=2))


if __name__=='__main__':main()
