#!/bin/bash
# Pilot the FAR / SDR / SER designs before committing to a full build.
# Submit from the repo root:  sbatch scripts/pilot_deception.sbatch
#
# ~300 instances x 3 tasks x 4 conditions (prior-balance, clean, corrupt,
# two label-validation runs) of Llama-3.1-8B-Instruct forward passes: minutes
# on one A100. Read data/datasets/pilot_report.json before building anything.
#
#SBATCH --job-name=pilot-deception
#SBATCH --account=beto-delta-gpu
# SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=logs/pilot_deception_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

set +u
source ~/.bashrc && conda activate mgnp
set -u
python dataset/pilot_deception.py --n 300 "$@"
