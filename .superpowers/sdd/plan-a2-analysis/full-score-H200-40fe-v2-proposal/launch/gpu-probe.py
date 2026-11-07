"""Tiny allocation-only device inspection; no model weights. Admitted GPU job only."""
import os,json,subprocess
import torch
from common import C,write
assert os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available() and torch.cuda.device_count()==1
props=torch.cuda.get_device_properties(0);assert 'H200' in props.name and props.total_memory>=C['minimum_gpu_total_bytes']
probe=torch.empty(1,device='cuda:0');torch.cuda.synchronize();free,total=torch.cuda.mem_get_info(0);assert free>=C['minimum_gpu_free_bytes']
raw=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader,nounits'],check=True,capture_output=True,text=True).stdout
uuids={line.split(',')[1].strip() for line in raw.splitlines() if line.strip() and line.split(',')[0].strip()==str(os.getpid())};assert len(uuids)==1
write(os.environ['A2_GPU_PROBE_OUTPUT'],dict(gpu_name=props.name,gpu_uuid=next(iter(uuids)),device='cuda:0',visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),total_memory_bytes=total,free_memory_bytes=free,compute_capability=[props.major,props.minor],driver_inventory=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,memory.total,driver_version','--format=csv,noheader'],check=True,capture_output=True,text=True).stdout,job_id=os.environ['SLURM_JOB_ID'],PID=os.getpid(),no_model_loaded=True))
