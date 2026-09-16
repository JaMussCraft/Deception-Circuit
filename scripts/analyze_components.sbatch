#!/bin/bash
# Component-level analysis of a circuit, on the GPU partition.
# Mirrors scripts/evaluate_circuit.sbatch. Submit from the repo root:
#
#   sbatch scripts/analyze_components.sbatch outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414
#
# Any extra arguments pass through to analyze_components.py, so a circuit can
# be composed by name exactly as it is for the evaluator:
#
#   sbatch scripts/analyze_components.sbatch \
#       --circuit sdr=<sdr_run> --circuit honest_c=<honest_run> \
#       --reference honest=<honest_run> \
#       --expr "delta=sdr \ honest_c" --compose-granularity head \
#       --task-from <sdr_run> --suite-name sdr-head-delta
#
# --analyses NAME[,NAME] picks which registered analyses run; the default is
# all of them. Run --dry-run on the login node first: it resolves the circuits,
# the segmentation and the causal sample, reports how much of the sample has an
# Honest-Instruction Counterfactual, and prints each analysis's cost estimate,
# all without a GPU.
#
# --time is sized for one cell of the descriptive analyses plus a
# position-agnostic patching pass over 100 instances. A larger grid, or the
# position-specific second pass, wants more.
#
#SBATCH --job-name=analyze-components
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/analyze_components_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

if [ "$#" -lt 1 ]; then
    echo "usage: sbatch scripts/analyze_components.sbatch <run_dir> [extra args...]" >&2
    echo "       sbatch scripts/analyze_components.sbatch --circuit NAME=<run_dir> ..." >&2
    exit 2
fi

set +u
source ~/.bashrc && conda activate mgnp
set -u
python analyze_components.py "$@"
