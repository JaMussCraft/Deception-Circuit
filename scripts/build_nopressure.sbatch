#!/bin/bash
# Build the <task>_nopressure datasets (the Format Circuit's data) for FAR and
# SDR on a GPU node.  Submit from the repo (or worktree) root:
#
#   sbatch --account=<acct> --partition=<part> --time=01:00:00 \
#       scripts/build_nopressure.sbatch
#
# Nothing is generated: each build derives from the stored data/datasets/<task>
# (and <task>_honest, for the tagged fallback) by deleting the stored Pressure
# Clause, relabelling to honest targets, and running the base model ONCE per
# split (clean + corrupt forward per record, ~2 x 2,800 per task). The 0.7 /
# 0.5 / 0.3 threshold step-down is applied offline to those margins, so the
# whole job is minutes, not hours.
#
# Rehearse first on the login node (no GPU, nothing written):
#   python dataset/build_nopressure_dataset.py --task far --no-model
#   python dataset/build_nopressure_dataset.py --task sdr --no-model
#
# TASKS overrides the task list (default "far sdr"); extra builder flags can be
# passed through EXTRA (e.g. EXTRA="--min-train 150 --min-test 500").
#
#SBATCH --job-name=build-nopressure
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/build_nopressure_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

set +u
source ~/.bashrc && conda activate mgnp
set -u

TASKS=${TASKS:-"far sdr"}
EXTRA=${EXTRA:-}

for TASK in $TASKS; do
  # shellcheck disable=SC2086
  python dataset/build_nopressure_dataset.py --task "$TASK" $EXTRA
done
