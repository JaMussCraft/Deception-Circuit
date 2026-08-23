#!/bin/bash
# Build both Stipulated-Truth Deception (STD) dataset variants on a GPU node.
# Submit from the repo root:  sbatch scripts/build_std.sbatch
# Filtering runs Llama-3.1-8B-Instruct forward passes over ~5600 example pairs
# per variant; one A100 finishes well within the time limit below.
#
#SBATCH --job-name=build-std
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA100x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=logs/build_std_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

# Activate your environment here if needed, e.g.:
set +u
source ~/.bashrc && conda activate mgnp
set -u
python dataset/build_std_dataset.py --statement-source azaria
python dataset/build_std_dataset.py --statement-source neutral
