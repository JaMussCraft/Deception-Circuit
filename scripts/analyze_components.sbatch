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
# The partition, account and --time below are a starting point, not a budget:
# multi-hour jobs and the A100 (gpuA100x4, gpuA100x8) and H200 (gpuH200x8)
# partitions are all allowed whenever they make a run simpler or faster
# (researcher's decision, 2026-10-13). Override on the sbatch command line,
# before the script name, and always give --time there:
#
#   sbatch --time=02:30:00 --partition=gpuA100x4 scripts/analyze_components.sbatch ...
#
# Size --time from the --dry-run estimate. On an A40 the descriptive trio
# (attention_patterns, dla, knockout) is about 11 minutes, each
# position-agnostic path-patching grid over 100 instances 13 to 18 minutes,
# and the completeness sweep about 30 minutes per 64 instances (ticket 12's
# runtime table). Shorter --time requests backfill sooner on a busy queue.
#
# Several jobs may run into one cell (same --suite-name or --output-dir): each
# replaces the columns of the analyses it runs and carries the rest forward.
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
