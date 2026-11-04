from pathlib import Path
import hashlib,json,os,socket,subprocess,time
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(cfg,e,phase):
    rows={}
    for name in cfg['catalogue_paths']:
        p=Path(name);raw=p.read_bytes();data=json.loads(raw)
        if p.name=='held_out.json':
            assert data.get('sets')==[], 'Nonempty protected registry requires complete closure review before release'
        else:
            own=[r for r in data['directions'] if r.get('id')=='specificity-ladder']
            assert len(own)==1 and own[0].get('frozen_grader_sha256')=='866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9'
        rows[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'resolved':str(p.resolve())}
        (e/(phase+'-'+hashlib.sha256(name.encode()).hexdigest()[:12]+'.json')).write_bytes(raw)
    (e/(phase+'-catalogues.json')).write_text(json.dumps(rows,indent=2)+'\n')
    return rows
assert sha(P/'manifest.json')==os.environ['G3_EXPECTED_MANIFEST_SHA'], 'root launch manifest binding'
for name,digest in json.loads((P/'manifest.json').read_text()).items(): assert sha(P/name)==digest,name
cfg=json.loads((P/'config.json').read_text());assert sha(P/'base-parameters.json')==cfg['base_parameters_sha256'];assert sha(cfg['driver'])==cfg['driver_sha256']
job=os.environ['SLURM_JOB_ID'];assert os.environ['SLURM_CLUSTER_NAME']=='delta';e=P/('job-'+job);e.mkdir(exist_ok=False)
raw=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True);facts=dict(x.split('=',1) for x in raw.split() if '=' in x)
assert facts['JobId']==job and facts['JobState']=='RUNNING' and facts['Partition'] in ['cpu','cpu-interactive'] and int(facts['NumCPUs'])>=4
assert facts['BatchHost'].split('.')[0]==socket.gethostname().split('.')[0]
tres=dict(x.split('=',1) for x in facts['AllocTRES'].split(',') if '=' in x);assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in tres.items())
mem=tres['mem'];assert (mem.endswith('G') and float(mem[:-1])>=16) or (mem.endswith('M') and float(mem[:-1])>=16384)
a={'job_id':job,'host':socket.gethostname(),'scontrol_job':raw,'captured_unix':time.time(),'slurm_environment':{k:v for k,v in os.environ.items() if k.startswith('SLURM_')}}
af=e/'allocation.json';af.write_text(json.dumps(a,indent=2)+'\n')
c=json.loads((P/'base-parameters.json').read_text());c['current_cpu_allocation']={'path':str(af),'sha256':sha(af)}
before=capture(cfg,e,'before');c['root_current_catalogue_capture']={'path':str(e/'before-catalogues.json'),'sha256':sha(e/'before-catalogues.json')};cf=e/'parameters.json';cf.write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
cmd=['timeout','--signal=TERM','--kill-after='+str(cfg['kill_grace_seconds'])+'s',str(cfg['child_seconds'])+'s','/u/swong2/.conda/envs/mgnp/bin/python',cfg['driver'],'--parameters',str(cf),'--parameters-sha256',sha(cf)]
start=time.time()
with (e/'driver.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
after=capture(cfg,e,'after');stable=before==after
out={'kind':'Delta_G3_root_CPU_wrapper','job_id':job,'source_commit':cfg['source_commit'],'exit_code':r.returncode,'wall_seconds':time.time()-start,'catalogues_stable':stable,'allocation':a,'parameters_sha256':sha(cf),'driver_sha256':sha(cfg['driver']),'model_admitted':False}
(e/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)
assert stable,'Live catalogue bytes changed across the owning freeze/preflight; no downstream release'
raise SystemExit(r.returncode)
