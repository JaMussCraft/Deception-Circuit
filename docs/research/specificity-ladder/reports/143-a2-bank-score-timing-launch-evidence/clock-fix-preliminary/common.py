"""External orchestration checks; original source/model APIs remain untouched."""
import os,sys,pathlib,json,hashlib,subprocess,time,datetime,math
L=pathlib.Path(__file__).resolve().parent;C=json.loads((L/'config.json').read_text());B=pathlib.Path(C['runtime']);MAIN=pathlib.Path(C['main_root']);PILOT=pathlib.Path(C['pilot_root'])
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def write(path,value):
    with pathlib.Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def environment():
    return dict(os.environ,DC_CLUSTER='delta',DC_PYTHON=C['python'],DC_RUN_MANIFEST_GIT='0',PYTHONPATH=str(B),PYTHONDONTWRITEBYTECODE='1',HF_HOME='/work/nvme/beto/swong2',HF_HUB_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',WANDB_MODE='disabled',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
def packet():
    for name,value in json.loads((L/'manifest.json').read_text()).items():assert sha(L/name)==value,('launch packet changed',name)
    assert sha(C['source_plan'])==C['source_plan_sha256']
def source():
    assert sha(C['snapshot'])==C['snapshot_sha256'];snapshot=json.loads(pathlib.Path(C['snapshot']).read_text());assert snapshot['source_commit']==C['commit'] and len(snapshot['source_sha256'])==511
    for name,value in snapshot['source_sha256'].items():
        path=B/name;assert path.is_file() and not path.is_symlink() and not path.stat().st_mode&0o222 and sha(path)==value,name
    for name,target in snapshot['input_links'].items():assert (B/name).is_symlink() and (B/name).resolve()==pathlib.Path(target).resolve()
    assert sha(C['groups'])==C['groups_file_sha256']
    return dict(source_commit=C['commit'],snapshot_sha256=C['snapshot_sha256'],groups_file_sha256=C['groups_file_sha256'],source_count=511,checked_utc=utc())
def imports():
    os.chdir(B);sys.path.insert(0,str(B))
    from component_analysis import a2_pipeline as a2,a3_direction_runtime as ar
    return a2,ar

def budget(*,prospective,release=None):
    _,ar=imports();identity=dict(purpose='A2 one original-H bank plus prefix4 timing',source_commit=C['commit'],groups_sha256=C['groups_file_sha256'],main_root=C['main_root'],pilot_root=C['pilot_root'])
    normalized=ar.normalize_ledger(C['mapping_origin'],identity=identity,include_envelope=False,refresh_deadline=time.monotonic()+20)
    mapping=ar.read_object(normalized['active_mapping_reference']['path']);ledger=json.loads(pathlib.Path(C['canonical_ledger']).read_text())
    assert sha(C['canonical_ledger'])==normalized['current_snapshot_sha256'],'live ledger changed during budget check'
    assert mapping['ledger_path']==C['canonical_ledger'] and not ledger.get('legacy_totals'),'root must explicitly review unallocated legacy charges'
    entries={row['id']:row for row in ledger['reservations']};phases={name:0. for name in C['experiment_limits']}
    for row in mapping['entries']:phases[row['experiment']]+=row['original_reserved_gpu_hours']
    total=round(sum(row['reserved_gpu_hours'] for row in entries.values()),4);assert total==ledger['totals']['reserved_gpu_hours']
    extra=C['maximum_reserved_gpu_hours'] if prospective else 0.
    assert round(total+extra,4)<=C['global_limit']<=ledger['caps']['reserved_gpu_hours']
    for name,value in phases.items():assert round(value+(extra if name=='A2' else 0),4)<=C['experiment_limits'][name]
    if not prospective:
        row=entries[release['reservation_id']];owned=next(item for item in mapping['entries'] if item['reservation_id']==row['id'])
        assert owned['experiment']=='A2' and row['job_id']==os.environ['SLURM_JOB_ID'] and row['cluster']=='delta'
        assert row['source_commit']==C['commit'] and pathlib.Path(row['output_dir']).resolve()==MAIN.resolve()
        assert row['gpus']==1 and row['requested_minutes']==25 and row['reserved_gpu_hours']==C['maximum_reserved_gpu_hours']
        assert row['account']==release['account'] and row['partition'] in release['allowed_partitions']
        assert row['status'] in ('PENDING','RUNNING')
    return dict(checked_utc=utc(),canonical_ledger=C['canonical_ledger'],ledger_sha256=normalized['current_snapshot_sha256'],active_mapping_reference=normalized['active_mapping_reference'],phase_reserved={name:round(value,4) for name,value in phases.items()},total_reserved=total,prospective_extra=extra,no_old_charge_refunded=True)
def allocation(*,gpu,release=None):
    job=os.environ.get('SLURM_JOB_ID');assert job,'actual Slurm allocation required; never run locally'
    raw=subprocess.run(['scontrol','show','job',job,'-o'],check=True,capture_output=True,text=True).stdout;facts=dict(x.split('=',1) for x in raw.split() if '=' in x)
    assert facts['JobState']=='RUNNING' and str(facts.get('JobId',job))==job
    nodes=subprocess.run(['scontrol','show','hostnames',facts['NodeList']],check=True,capture_output=True,text=True).stdout.split()
    assert os.uname().nodename.split('.')[0] in {node.split('.')[0] for node in nodes}
    tres=dict(x.split('=',1) for x in facts.get('AllocTRES',facts.get('TRES','')).split(',') if '=' in x)
    if gpu:
        assert facts['Account']==release['account'] and facts['Partition'] in release['allowed_partitions']
        assert int(tres.get('gres/gpu','0'))==1 and int(tres.get('gres/gpu:h200','0'))==1
        assert int(facts['NumCPUs'])>=4 and int(facts['NumNodes'])==1
        memory=tres['mem'];scale={'K':1024,'M':1024**2,'G':1024**3,'T':1024**4};allocated_memory=float(memory[:-1])*scale[memory[-1]] if memory[-1] in scale else float(memory)
        assert allocated_memory>=64*1024**3
        assert facts['TimeLimit'] in ('00:25:00','25:00'),'unchanged25min attempt required'
    else:assert not any(key.startswith('gres/gpu') and float(value)>0 for key,value in tres.items())
    return dict(job_id=job,hostname=os.uname().nodename,facts=facts,raw=raw,tres=tres,slurm_environment={k:v for k,v in os.environ.items() if k.startswith('SLURM_') and not any(word in k for word in ('TOKEN','SECRET','JWT','AUTH','CREDENTIAL'))})
def gpu_release():
    r=json.loads(pathlib.Path(os.environ['A2_TIMING_ROOT_RELEASE']).read_text());assert r['launch_manifest_sha256']==sha(L/'manifest.json')
    assert r['source_commit']==C['commit'] and r['groups_file_sha256']==C['groups_file_sha256'] and r['main_root']==C['main_root'] and r['pilot_root']==C['pilot_root']
    assert r['gpu_timing_admitted'] is True and r['bank_and_prefix4_only'] is True and r['full_scoring_admitted'] is False and r['current_usage_pass'] is True
    assert r['job_id']==os.environ['SLURM_JOB_ID']
    pre=pathlib.Path(r['preflight_complete_path']);assert sha(pre)==r['preflight_complete_sha256']
    d=json.loads(pre.read_text());assert d['complete'] is True and d['launch_manifest_sha256']==sha(L/'manifest.json') and d['source']['groups_file_sha256']==C['groups_file_sha256']
    return r
