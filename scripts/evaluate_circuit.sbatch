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
# A run directory is optional: bind circuits by name instead and the run
# becomes a suite over every (circuit expression, task) cell.
#
#   sbatch scripts/evaluate_circuit.sbatch \
#       --circuit far=<run_dir> --circuit sdr=<run_dir> --circuit ser=<run_dir> \
#       --xor far,sdr,ser --task far --task sdr --task ser \
#       --suite-name mechanism-xor
#
# --time is sized for a suite: one cell is roughly 20 minutes with the default
# 50-circuit null, and a 3-circuit x 3-task grid is nine of them plus one model
# load. Run --dry-run on the login node first; it prints a runtime estimate.
#
#SBATCH --job-name=eval-circuit
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/evaluate_circuit_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

if [ "$#" -lt 1 ]; then
    echo "usage: sbatch scripts/evaluate_circuit.sbatch <run_dir> [extra args...]" >&2
    echo "       sbatch scripts/evaluate_circuit.sbatch --circuit NAME=<run_dir> ..." >&2
    exit 2
fi

# Cluster profile (scripts/cluster/<name>.env). Unset DC_CLUSTER means Delta, whose
# profile reproduces this wrapper's behaviour from before profiles existed. #SBATCH
# lines cannot read variables, so the header above stays Delta's; other clusters put
# -A/-p/the GPU option/-t on the sbatch command line (scripts/remote/b2.sh does).
profile="scripts/cluster/${DC_CLUSTER:-delta}.env"
if [ ! -f "$profile" ]; then
    echo "unknown cluster profile: $profile (DC_CLUSTER=${DC_CLUSTER:-})" >&2
    exit 2
fi
source "$profile"

set +u
eval "$DC_ACTIVATE"
set -u
export HF_HOME="$DC_HF_HOME"
if [ "$DC_HF_OFFLINE" = "1" ]; then
    export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
fi
python evaluate_circuit.py "$@"
