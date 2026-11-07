"""Bridges host stdlib launch; no source or historical artifact edits."""
from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime,time
config=Path(os.environ['A2_H100_BOUND_CONFIG']);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(config)==os.environ['A2_H100_BOUND_CONFIG_SHA256'];c=json.loads(config.read_text());assert c['independent160_accepted'] is True and c['actual_job_id']==os.environ['SLURM_JOB_ID']
assert sha(c['image'])==c['image_sha256']
raw=subprocess.check_output(['scontrol','show','job',c['actual_job_id'],'-o'],universal_newlines=True,env=dict(os.environ,TZ='UTC'));facts=dict(x.split('=',1) for x in raw.split() if '=' in x);assert facts['JobState']=='RUNNING' and facts['Account']==c['expected_account'] and facts['TimeLimit'] in ('00:50:00','50:00')
end=datetime.datetime.strptime(facts['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp();assert end>time.time()
virtual=Path(c['virtual_Alignment_root']);physical=Path(c['physical_Alignment_root']);packet=Path(__file__).resolve().parent
# Root binds the bound-config virtual path; never synthesize a Slurm identity.
profile={k:v for k,v in os.environ.items() if k.startswith('SLURM_') or k in ('CUDA_VISIBLE_DEVICES',)}
profile.update(A2_H100_BOUND_CONFIG=str(virtual/config.relative_to(physical)),A2_H100_BOUND_CONFIG_SHA256=sha(config),A2_H100_PACKET=str(virtual/packet.relative_to(physical)),A2_H100_RUNTIME=c['runtime'],A2_TIMING_EXECUTION_OUTPUT=os.environ['A2_TIMING_EXECUTION_OUTPUT'],A2_H100_RELEASE_DIRECTORY=os.environ['A2_H100_RELEASE_DIRECTORY'],A2_H100_INITIAL_END_EPOCH=str(end),PYTHONDONTWRITEBYTECODE='1',HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',DC_B2_ALLOC='cis260361p')
cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--nv','--pwd',c['runtime'],'--bind',str(physical)+':'+str(virtual)+':rw','--bind','/ocean:/ocean:ro','--bind',c['physical_HF_cache']+':'+c['virtual_HF_cache']+':ro']
for key,value in sorted(profile.items()):cmd+=['--env',key+'='+value]
cmd += [c['image'],'bash',profile['A2_H100_PACKET']+'/inner.sh']
raise SystemExit(subprocess.call(cmd))
