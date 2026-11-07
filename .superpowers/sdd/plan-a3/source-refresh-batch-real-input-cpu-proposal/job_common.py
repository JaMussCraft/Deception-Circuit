"""Operational CPU coordination only; never source/model execution authority."""
import pathlib,os,json,hashlib,subprocess,datetime
P=pathlib.Path(__file__).resolve().parent
CFG=json.loads((P/'config.json').read_text());W=pathlib.Path(CFG['worktree']);B=pathlib.Path(CFG['runtime']);O=pathlib.Path(CFG['output']);C=CFG['commit']
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def write(path,value):pathlib.Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def allocation():
    job=os.environ.get('SLURM_JOB_ID');assert job,'Slurm CPU allocation required; no local execution'
    raw=subprocess.run(['scontrol','show','job',job,'-o'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).stdout
    facts=dict(item.split('=',1) for item in raw.split() if '=' in item)
    assert facts['JobState']=='RUNNING' and facts['Account']==CFG['cpu_account'] and facts['Partition']==CFG['cpu_partition']
    assert int(facts['NumCPUs'])>=CFG['requested_cpus'] and int(facts['NumNodes'])==1
    tres=dict(item.split('=',1) for item in facts.get('AllocTRES',facts.get('TRES','')).split(',') if '=' in item)
    assert not any(key.startswith('gres/gpu') and float(value)>0 for key,value in tres.items())
    nodes=subprocess.run(['scontrol','show','hostnames',facts['NodeList']],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).stdout.split()
    assert os.uname().nodename.split('.')[0] in {node.split('.')[0] for node in nodes},'allocation must be local to this compute node'
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    visible={key:value for key,value in os.environ.items() if key.startswith('SLURM_') and not any(secret in key.upper() for secret in ('TOKEN','SECRET','CREDENTIAL','JWT','AUTH'))}
    return dict(job_id=job,cluster='delta',hostname=os.uname().nodename,facts=facts,raw=raw,allocated_tres=tres,slurm_environment=visible,checked_utc=utc(),model_admission=False)
def environment():
    return dict(os.environ,W=str(W),B=str(B),O=str(O),C=C,E=str(O/'evidence'),PYTHONPATH=str(B),PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',HF_HOME='/work/nvme/beto/swong2',HF_HUB_CACHE='/work/nvme/beto/swong2/hub',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',DC_PYTHON=CFG['python'],A3_REPO_ROOT=str(B),SPECIFICITY_A3_EDGE_REPO_ROOT=str(B),SPECIFICITY_A3_MASK_REPO_ROOT=str(B),A3_MASK_PYTHON=CFG['python'],SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE=CFG['python'],CUDA_VISIBLE_DEVICES='')
def source_binding():
    assert sha(CFG['snapshot'])==CFG['snapshot_sha256']
    snapshot=json.loads(pathlib.Path(CFG['snapshot']).read_text());assert snapshot['source_commit']==C and snapshot['runtime_root']==str(B)
    assert len(snapshot['source_sha256'])==511 and len(snapshot['input_links'])==4
    observed={}
    for name,expected in snapshot['source_sha256'].items():
        path=B/name;assert path.is_file() and not path.is_symlink() and not path.stat().st_mode&0o222
        observed[name]=sha(path);assert observed[name]==expected,name
    assert sha(B.parent/'source.tar')==snapshot['source_archive_sha256']
    links={}
    for name,target in snapshot['input_links'].items():
        path=B/name;assert path.is_symlink() and path.resolve()==pathlib.Path(target).resolve();links[name]=os.readlink(path)
    return dict(commit=C,runtime=str(B),source_sha256=observed,input_links=links,snapshot_sha256=CFG['snapshot_sha256'],source_archive_sha256=snapshot['source_archive_sha256'],readonly=True,checked_utc=utc())
def packet_binding():
    manifest=json.loads((P/'proposal-manifest.json').read_text())
    for name,expected in manifest.items():assert sha(P/name)==expected,name
    release_path=pathlib.Path(os.environ['A3_CPU_PREPARATION_RELEASE']);assert release_path.is_absolute()
    release=json.loads(release_path.read_text())
    assert release['source_commit']==C and release['runtime_root']==str(B) and release['output_root']==str(O)
    assert release['proposal_manifest_sha256']==sha(P/'proposal-manifest.json')
    assert release['independent_review_accepted'] is True and release['root_authorized_cpu_preparation'] is True
    assert release['execution_authorized'] is False and release['grants_model_or_reservation_authority'] is False
    return dict(release_path=str(release_path),release_sha256=sha(release_path),release=release,proposal_manifest_sha256=sha(P/'proposal-manifest.json'))
