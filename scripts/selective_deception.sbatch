#!/bin/bash
# Root must reserve GPU × requested walltime in the research ledger before submission.
# Dry-run first. Override --time explicitly at submission after measuring smoke.
#SBATCH --job-name=selective-sdr
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --no-requeue
#SBATCH --output=logs/selective_deception_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"
set +u
source ~/.bashrc
conda activate mgnp
set -u
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
unset OPENAI_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY WANDB_API_KEY
python evaluate_selective_deception.py "$@"
