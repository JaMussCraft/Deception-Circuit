#!/bin/bash
# Train an STD circuit on Llama-3.1-8B-Instruct, Submit from the repo root:
#
#   sbatch scripts/train_std.sbatch
#
# Any extra arguments are passed through to train.py, e.g.
#
#   sbatch scripts/train_std.sbatch --node-lambda-sparsity 0.7 --edge-lambda-sparsity 0.7
#
# A comparable prior run (~500 node + 300 edge epochs) took ~3 h and peaked
# around 40 GB; leave headroom on the wall clock.
#
#SBATCH --job-name=train-std-hb
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=logs/train_std_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

# Activate your environment here if needed, e.g.:
set +u
source ~/.bashrc && conda activate mgnp
set -u
python train.py --model llama-8b-instruct --task std "$@"
