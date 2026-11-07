#!/bin/bash
#SBATCH --job-name=native-sparse
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=00:20:00
#SBATCH --no-requeue
#SBATCH --output=logs/native_sparse_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"
set +u
source ~/.bashrc || true
if ! command -v conda >/dev/null 2>&1 || ! conda activate mgnp; then
    echo 'conda mgnp activation failed' >&2
    exit 1
fi
set -u
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
unset OPENAI_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY WANDB_API_KEY
python evaluate_native_sparse.py "$@"
