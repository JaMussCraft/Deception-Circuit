#!/bin/bash
# Evaluate a node-pruned circuit saved by train.py.
# Submit from the repo root:
#
#   sbatch scripts/evaluate_circuit.sbatch outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636
#
# Any extra arguments are passed through to evaluate_circuit.py, e.g.
#
#   sbatch scripts/evaluate_circuit.sbatch <run_dir> --ablation mean
#   sbatch scripts/evaluate_circuit.sbatch <run_dir> --evals sanity --strict
#
#
#SBATCH --job-name=eval-circuit
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/evaluate_circuit_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

if [ "$#" -lt 1 ]; then
    echo "usage: sbatch scripts/evaluate_circuit.sbatch <run_dir> [extra args...]" >&2
    exit 2
fi

# Activate your environment here if needed, e.g.:
set +u
source ~/.bashrc && conda activate mgnp
set -u
python evaluate_circuit.py "$@"
