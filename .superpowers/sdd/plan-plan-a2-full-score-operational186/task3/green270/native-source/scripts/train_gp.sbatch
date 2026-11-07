#!/bin/bash
# Train a GP circuit on Llama-3.1-8B. Submit from the repo root:
#
#   sbatch scripts/train_gp.sbatch
#
# Any extra arguments are passed through to train.py, e.g.
#
#   sbatch scripts/train_gp.sbatch --no-edge-pruning
#   sbatch scripts/train_gp.sbatch --node-epochs 12 --edge-epochs 2 \
#       --train-samples 64 --val-samples 32 --test-samples 64 --batch-size 16
#
# A comparable prior run (~500 node + 300 edge epochs) took ~3 h and peaked
# around 40 GB; leave headroom on the wall clock.
#
#SBATCH --job-name=train-gp
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=logs/train_gp_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

set +u
source ~/.bashrc && conda activate mgnp
set -u
python train.py --model llama-8b --task gp "$@"
