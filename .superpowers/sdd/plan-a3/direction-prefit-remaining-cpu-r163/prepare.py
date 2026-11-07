"""Unexecuted genuine CPU preparation; original metadata entrypoints only."""
from pathlib import Path
import hashlib,json,os,subprocess,time
P=Path(__file__).resolve().parent

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(1048576),b''):h.update(part)
    return h.hexdigest()

def sources(cfg):
    snapshot=json.loads(Path(cfg['snapshot']).read_text());b=Path(cfg['runtime'])
    assert snapshot['source_commit']==cfg['source_commit'] and not snapshot['source_code_symlinks']
    assert len(snapshot['source_sha256'])==511
    for name,digest in snapshot['source_sha256'].items():assert sha(b/name)==digest,name
    for name,target in snapshot['input_links'].items():assert (b/name).is_symlink() and (b/name).resolve()==Path(target).resolve(),name
    assert {name:sha(Path(cfg['W'])/name) for name in cfg['source13']}==cfg['source13']

def main():
    cfg=json.loads((P/'config.json').read_text());o=Path(cfg['output']);assert o.is_dir() and Path(cfg['canonical']).is_dir();assert not Path(cfg['inventory_paths']['fit-select']).exists()
    from allocation_facts import read_current
    allocation=read_current(Path(cfg['W']),minimum_remaining_seconds=2610);assert allocation['time_limit_seconds']==2700
    e=o/'evidence';e.mkdir(exist_ok=True)
    def write(name,value):
        with (e/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    sources(cfg)
    for path,fingerprint in cfg['completed_artifact_fingerprints'].items():
        assert Path(path).stat().st_size==fingerprint['bytes'] and sha(path)==fingerprint['sha256'],path
    for pin in cfg['pinned_files']:assert sha(pin['path'])==pin['sha256']
    assert sha(P/'execution-settings.json')==cfg['settings_sha256']
    env=dict(os.environ,A3_REPO_ROOT=cfg['runtime'],DC_PYTHON='/u/swong2/.conda/envs/mgnp/bin/python',DC_CLUSTER='delta',PYTHONPATH=cfg['runtime'],PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    assert {k:v for k,v in env.items() if k.startswith('SLURM_')}=={k:v for k,v in os.environ.items() if k.startswith('SLURM_')}
    phases=[];began=time.perf_counter()
    steps=cfg['commands']+[dict(name='validation',argv=['/u/swong2/.conda/envs/mgnp/bin/python',str(P/'validate.py')],cwd=cfg['runtime'])]
    for step in steps:
        if step['name']!='validation':
            a=step['argv'];assert a[:2]==['bash',str(Path(cfg['runtime'])/'scripts/jobs/specificity_a3.sh')]
            stage=a[a.index('--stage')+1];assert stage in ('prepare','pilot')
            if stage=='pilot':assert '--dry-run' in a and a[a.index('--pilot-part')+1]=='prefit'
            else:assert a[a.index('--action')+1] in ('freeze','inventory')
            assert not any(flag in a for flag in ('--admission','--reservation','--pilot-receipts','--selected','--fits','--final'))
        print(json.dumps(dict(event='command_start',**step)),flush=True);start=time.perf_counter()
        with (e/(step['name']+'.log')).open('x') as stream:
            child=subprocess.Popen(step['argv'],cwd=step['cwd'],env=env,stdout=stream,stderr=subprocess.STDOUT)
            _,status,usage=os.wait4(child.pid,0);code=os.waitstatus_to_exitcode(status);child.returncode=code
        row=dict(**step,exit_code=code,wall_seconds=time.perf_counter()-start,user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,peak_wait4_rss_bytes=usage.ru_maxrss*1024)
        phases.append(row);write(step['name']+'-result.json',row);print(json.dumps(row),flush=True)
        if code:raise SystemExit(code if code>0 else 128-code)
    sources(cfg)
    for path,fingerprint in cfg['completed_artifact_fingerprints'].items():
        assert Path(path).stat().st_size==fingerprint['bytes'] and sha(path)==fingerprint['sha256'],path
    write('preparation-complete.json',dict(kind='genuine_direction_prefit_CPU_remaining_preparation',complete=True,commands=phases,wall_seconds=time.perf_counter()-began,actual_job_id=allocation['job_id'],actual_host=allocation['host'],source_unchanged=True,no_model_stages_requested=True,scientific_execution=False,execution_authorized=False,root_GPU_admission=False,direction_M1_budget_feasibility_established=False))

if __name__=='__main__':main()
