#!/usr/bin/env python3
"""Bridges actual 5-minute visibility probe; no model or resource proof."""
import argparse,datetime,json,os,socket,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import allocation_helper as h
from guards import fresh_output,cgroup_bind
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);a=ap.parse_args();h.check_packet(HERE,a.manifest_sha256)
allowed=h.PHYS/h.REL/'.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/root-cgroup199-r4';out=fresh_output(a.output,allowed,os.getuid());out.mkdir(exist_ok=False)
raw=subprocess.check_output(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC'));f=dict(x.split('=',1) for x in raw.split() if '=' in x);work=str(h.PHYS/h.REL/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime');t=h.validate_allocation(f,os.environ,os.getuid(),socket.gethostname(),work,expected_minutes=5);assert h.sha(h.IMAGE)==h.IMAGE_SHA
h.write(out/'allocation.json',dict(fields=f,tres=t,raw=raw,host=socket.gethostname(),captured_unix=time.time()))
env=dict(os.environ);host=subprocess.run([sys.executable,str(HERE/'cgroup_probe.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,env=env);(out/'host-cgroup.json').write_text(host.stdout)
if host.returncode!=0:
 h.write(out/'probe-result.json',dict(complete=True,host_exit=host.returncode,container_exit=None,host_stderr=host.stderr,no_graph=True,no_model=True,proof_admitted=False));sys.exit(2)
host_data=json.loads(host.stdout);valid=[r for r in host_data['records'] if r.get('job_scoped') and r.get('same_as_frozen_worker_path') and r.get('values')];assert host_data['required_194_counter_visible'] and len(valid)==1
actual_cgroup_bind=cgroup_bind(valid[0]['controller'])
virtual_probe=h.VIRT/HERE.relative_to(h.PHYS)/'inner.sh';virtual_out=h.VIRT/out.relative_to(h.PHYS)
cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',str(h.R),'--bind',str(h.PHYS)+':'+str(h.VIRT)+':ro','--bind','/ocean:/ocean:ro','--bind',h.HUB+':/work/nvme/beto/swong2:ro','--bind',str(out)+':'+str(virtual_out)+':rw','--bind',actual_cgroup_bind]
profile={k:v for k,v in os.environ.items() if k.startswith('SLURM_')};profile.update(PYTHONPATH=str(h.R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',DC_CLUSTER='bridges2',DC_B2_ALLOC='cis260361p')
for k,v in sorted(profile.items()):cmd.extend(['--env',k+'='+v])
cmd.extend([h.IMAGE,'bash',str(virtual_probe)]);h.write(out/'command.json',{'argv':cmd});container=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=120);(out/'container-cgroup.json').write_text(container.stdout);h.write(out/'probe-result.json',dict(complete=True,host_exit=host.returncode,container_exit=container.returncode,host_stderr=host.stderr,container_stderr=container.stderr,no_graph=True,no_model=True,proof_admitted=False));sys.exit(0 if host.returncode==0 and container.returncode==0 else 2)
