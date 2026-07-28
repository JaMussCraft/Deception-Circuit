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
# Loads two copies of Llama-3.1-8B-Instruct (~33-35 GB peak) and runs ~100
# evaluations; the full set takes about 1.5-2 h on one A100. Check the plan
# first with `python evaluate_circuit.py <run_dir> --dry-run` on the login node
# — it validates the circuit, the random set and the walltime in seconds.
#
#SBATCH --job-name=eval-circuit
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA100x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
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
source ~/.bashrc && conda activate mgnp
python evaluate_circuit.py "$@"
