#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --partition=cpu
#SBATCH --time=01:15:00
#SBATCH --no-requeue
set -euo pipefail
: "${SLURM_JOB_ID:?actual Delta CPU job required}"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
exec /u/swong2/.conda/envs/mgnp/bin/python "$(dirname "$0")/supervisor.py" --config "$1" --config-sha256 "$2"
