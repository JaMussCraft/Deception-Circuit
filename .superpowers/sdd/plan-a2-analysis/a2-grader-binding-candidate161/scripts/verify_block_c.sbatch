#!/bin/bash
# One-off GPU verification of the block-C scaffold (ticket 02b).
# Same partition, account and activation as scripts/analyze_components.sbatch;
# it runs scripts/verify_block_c.py, which forwards its arguments to the CLI
# after registering the stub analysis. Submit from the repo root:
#
#   sbatch scripts/verify_block_c.sbatch \
#       --circuit sdr=<sdr_run> --circuit honest_c=<honest_run> \
#       --reference honest=<honest_run> \
#       --expr "delta=sdr \ honest_c" --compose-granularity head \
#       --task-from <sdr_run> --output-dir <somewhere> --stub-batches 0
#
# Minutes, not hours: three forward passes per batch of the causal sample.
#
#SBATCH --job-name=verify-block-c
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=00:20:00
#SBATCH --output=logs/verify_block_c_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

set +u
source ~/.bashrc && conda activate mgnp
set -u
python scripts/verify_block_c.py "$@"
