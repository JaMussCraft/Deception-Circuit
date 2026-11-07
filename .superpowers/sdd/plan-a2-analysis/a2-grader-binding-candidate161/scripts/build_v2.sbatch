#!/bin/bash
# Full v2 build (score stage) of one or more v2 tasks on one GPU:
# dataset/build_deception_v2.py. Every argument is passed through to the builder;
# give several tasks with BUILD_V2_TASKS="far_v2 sdr_v2" to build them in sequence
# (each then gets the same arguments plus its own --task).
#
# Submit from the worktree root, with account, partition and time ON THE COMMAND LINE
# (log a reservation in compute-ledger.json first; reservation = --time x GPUs):
#
#   mkdir -p logs
#   sbatch --account=<acct> --partition=<gpuA100x4|gpuA40x4|...> --time=HH:MM:SS \
#       scripts/build_v2.sbatch --task far_v2 --selection <pilot-selection.json> \
#       --neutral-pool dataset/deception_pools/v2/neutral_candidates_r2.json \
#       --length-window 94 106 --stage score
#
# Dry path FIRST, on the login node, with the exact same arguments plus --no-model
# (renders and asserts every pressure prompt the job would score, applies the
# length window, fully realizes 3 rows per split; loads no weights):
#
#   python dataset/build_deception_v2.py <same arguments> --no-model
#
# The score stage appends per chunk to <work-dir>/<task>/{outcomes,survivors}_<tag>.jsonl
# and records finished chunks, so a job cut by its time limit is resumed by resubmitting
# the same command. Then, on CPU: --stage assemble per task, and --stage finalize once.
# Inference only; an A100 40 GB is enough for Llama-3.1-8B in bf16.
#
#SBATCH --job-name=build-v2
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=logs/build_v2_%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"
mkdir -p logs

set +u
source ~/.bashrc && conda activate mgnp || { echo "Environment initialization failed" >&2; exit 1; }
set -u

export TQDM_DISABLE=1
echo "build_v2: job ${SLURM_JOB_ID:-local} on ${SLURM_JOB_PARTITION:-unknown} ($(hostname)), tasks '${BUILD_V2_TASKS:-}', args: $*"
if [ -n "${BUILD_V2_TASKS:-}" ]; then
    for t in ${BUILD_V2_TASKS}; do
        echo "build_v2: --task ${t}"
        python dataset/build_deception_v2.py --task "${t}" "$@"
    done
else
    python dataset/build_deception_v2.py "$@"
fi
