#!/bin/bash
# Run one round (or part of one) of v2 Pilot Cells on one GPU: dataset/pilot_v2.py.
# Every argument is passed through to the harness.
#
# Submit from the worktree root, with account, partition and time ON THE COMMAND LINE
# (log a reservation in compute-ledger.json first; reservation = --time x GPUs):
#
#   mkdir -p logs
#   sbatch --account=<acct> --partition=<gpuA100x4|gpuA40x4|...> --time=HH:MM:SS \
#       scripts/pilot_v2.sbatch --cells <cells.json> --round <k> --out-dir <abs dir>
#
# Dry path FIRST, on the login node, with the exact same harness arguments plus
# --no-model (realizes and asserts every prompt of every cell, writes length
# reports and rendered sample pairs, loads no weights):
#
#   python dataset/pilot_v2.py --cells <cells.json> --round <k> --out-dir <abs dir> --no-model
#
# then `sbatch --test-only ...` with the submission line above. After the job:
#
#   python dataset/pilot_v2.py --summarize <abs dir> --markdown <pilot-round-k.md>
#
# A cell whose prompt is misaligned or over --max-seq-length (default 120) is aborted,
# not truncated: <cell_id>.aborted.json is written, the other cells still run, and the
# job exits 1. Inference only; an A100 40 GB is enough for Llama-3.1-8B in bf16.
#
#SBATCH --job-name=pilot-v2
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=logs/pilot_v2_%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"
mkdir -p logs

set +u
source ~/.bashrc && conda activate mgnp || { echo "Environment initialization failed" >&2; exit 1; }
set -u

echo "pilot_v2: job ${SLURM_JOB_ID:-local} on ${SLURM_JOB_PARTITION:-unknown} ($(hostname)), args: $*"
python dataset/pilot_v2.py "$@"
