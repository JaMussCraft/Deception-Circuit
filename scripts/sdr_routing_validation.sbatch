#!/usr/bin/env bash
#SBATCH --job-name=sdr-routing-validation
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:h200:1
# Operator supplies account/partition/time/output; never auto-resubmit.
set -euo pipefail
submission_cwd="${SDR_VALIDATION_SUBMISSION_CWD:-${SLURM_SUBMIT_DIR:-$PWD}}"
runner="$submission_cwd/scripts/sdr_routing_validation.py"
[[ -r "$runner" ]] || { echo 'Explicit submission cwd lacks validation runner' >&2; exit 2; }
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
python_bin=/u/swong2/.conda/envs/mgnp/bin/python
[[ -x "$python_bin" ]] || { echo 'Supported mgnp interpreter unavailable' >&2; exit 2; }
for arg in "$@"; do
    if [[ "$arg" == --dry-run ]]; then exec "$python_bin" "$runner" "$@"; fi
done
: "${SLURM_JOB_ID:?oneA100orH200Slurm allocation required}"
: "${SLURM_JOB_END_TIME:?allocation deadline required}"
: "${SDR_VALIDATION_ALLOCATED_SECONDS:?operator must set full reservation seconds}"
prior="${SDR_VALIDATION_PRIOR_RESERVED_GPU_SECONDS:-0}"
remaining=$((SLURM_JOB_END_TIME - $(date +%s)))
allocated="$SDR_VALIDATION_ALLOCATED_SECONDS"
if (( remaining < 120 || allocated < remaining || allocated > 3600 || prior < 0 || allocated + prior > 14400 )); then
    echo 'Invalid allocation/reservation ledger bounds' >&2; exit 2
fi
bound=$((remaining - 90))
trap 'echo "Validation wrapper ended job=${SLURM_JOB_ID} status=$?"' EXIT
timeout --signal=TERM --kill-after=20s "$((bound+30))s" "$python_bin" "$runner" "$@" \
    --allocation-seconds "$allocated" --prior-reserved-gpu-seconds "$prior" --max-seconds "$bound"
