"""Read-only tiny device/numeric probe, no model weights or loader callback."""
import os
import subprocess
import torch
import common


def main():
    c = common.validate_config(common.C)
    common.allocation()
    common.require(torch.cuda.is_available() and torch.cuda.device_count() == 1, 'one actual CUDA device')
    props = torch.cuda.get_device_properties(0)
    common.require(props.name == common.GPU_NAME, 'exact H100 80GB HBM3 required')
    probe = torch.empty(1, device='cuda:0', dtype=torch.bfloat16)
    torch.cuda.synchronize()
    free, total = torch.cuda.mem_get_info(0)
    raw = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid', '--format=csv,noheader,nounits'],
                                  universal_newlines=True, timeout=15)
    uuids = {line.split(',')[1].strip() for line in raw.splitlines()
             if line.strip() and line.split(',')[0].strip() == str(os.getpid())}
    common.require(len(uuids) == 1, 'actual current process GPU UUID')
    p, _ = common.imports()
    result = dict(gpu_name=props.name, gpu_uuid=next(iter(uuids)), device=str(probe.device), dtype=str(probe.dtype),
                  numeric_environment=p.numeric_environment(), total_memory_bytes=total, free_memory_bytes=free,
                  compute_capability=[props.major, props.minor], visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                  job_id=os.environ['SLURM_JOB_ID'], PID=os.getpid(), no_model_loaded=True)
    common.validate_gpu_identity(c, result)
    common.write(os.environ['A2_GPU_PROBE_OUTPUT'], result)


if __name__ == '__main__':
    main()
