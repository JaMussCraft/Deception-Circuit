#!/bin/bash
# Train one deception-mechanism circuit on Llama-3.1-8B-Instruct.
# Submit from the repo root:
#
#   sbatch scripts/train_deception.sbatch far
#   sbatch scripts/train_deception.sbatch ser --deception-condition honest
#
# The first argument is the task (far / sdr / ser); everything after it is passed
# through to train.py. The comparison unit is Δ = C_<task> − C_<task>_honest, so
# each mechanism needs BOTH conditions trained with identical hyperparameters —
# a difference in training is otherwise indistinguishable from a difference in
# mechanism.
#
# Budget as for STD: ~500 node + 300 edge epochs ran ~3 h and peaked around
# 40 GB.
#
#SBATCH --job-name=train-joint-deception
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuH200x8
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=logs/train_joint_deception_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

set +u
source ~/.bashrc && conda activate mgnp
set -u
python train.py --model llama-8b-instruct --task joint "$@"
