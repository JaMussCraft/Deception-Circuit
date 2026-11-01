# Paired sparse launcher operational review

Scope: analysis/sparse_pair.py and sparse_pair.sbatch; no scientific re-review, source edits, GPU work, or job submission. Root reports the two-H200 allocation test accepted and actual H-pair wrapper dry run exited zero.

Status: PASS for bounded launch after both operational fixes, with runtime limits below. Final Python syntax and all explicit step resource flags verified.

1. Fixed and verified: primary frozen wrapper changes directory to SLURM_SUBMIT_DIR, overriding Popen cwd. Driver now sets child SLURM_SUBMIT_DIR to the frozen tree. CPU mocks with inherited /wrong/submission confirm both children receive the frozen tree.
2. Fixed and verified: installed man srun documents inherited SLURM_GPUS_PER_NODE. Each child now explicitly sets --gpus=1, --gpus-per-node=1, and --gpus-per-task=1 with one node and one task, avoiding the inherited two-GPU request.
3. Resource shape otherwise appropriate: parent two GPUs, two CPUs, 128G; each exact/exclusive step one task, one CPU, 64G. Primary wrapper limits BLAS/OpenMP threads to one. Slurm controls device isolation; no guessed CUDA IDs.
4. CPU mocked both-success and first-child-failure checks passed. Failure triggers sibling SIGTERM and waits for both; output/temporary paths are separate. These checks do not emulate actual Slurm GPU isolation or remote signal propagation.
5. Existing run/log rejection, no retries, fixed two rho values, and separate receipt/output/cache paths keep execution bounded. Root must hash-bind final driver plus batch script and record allocation request before launch. Reserve one GPU-hour for the two-GPU thirty-minute pair; actual accounting uses both allocated GPUs for the allocation duration.

Runtime limit: static review and CPU mocks cannot prove device assignment on this cluster. Inspect first-pair step allocation/start logs and stop if both learners do not receive separate single GPUs. Allocation walltime is the hard cap.

Reviewed artifact SHA256:

- `sparse_pair.py`: `48be8bd7b660a08dc5c55fd62be56846efe0e2ff1b6511009f38001f22822b61`
- `sparse_pair.sbatch`: `9a77746ee7e6f410d3b46c237c8659782a3d8616b0236fc08b58dd4a2fa18eaa`
