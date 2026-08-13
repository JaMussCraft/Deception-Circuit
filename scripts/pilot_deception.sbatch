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
#SBATCH --partition=gpuA100x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/pilot_deception_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

source ~/.bashrc && conda activate mgnp
python dataset/pilot_deception.py --n 300
