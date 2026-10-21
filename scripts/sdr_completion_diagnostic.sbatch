#!/usr/bin/env bash
#SBATCH --job-name=sdr-completion-diagnostic
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:a100:1
# Operator supplies account/partition/time/output; no auto-resubmit or inference on login.
set -euo pipefail
submission_cwd="${SDR_COMPLETION_SUBMISSION_CWD:-${SLURM_SUBMIT_DIR:-$PWD}}"
runner="$submission_cwd/scripts/sdr_completion_diagnostic.py"
[[ -r "$runner" ]] || { echo 'Explicit submission cwd lacks completion runner' >&2; exit 2; }
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
python_bin=/u/swong2/.conda/envs/mgnp/bin/python
[[ -x "$python_bin" ]] || { echo 'Supported mgnp interpreter unavailable' >&2; exit 2; }
for arg in "$@"; do
    if [[ "$arg" == --dry-run ]]; then exec "$python_bin" "$runner" "$@"; fi
done
: "${SLURM_JOB_ID:?single parent-identical A100 Slurm allocation required}"
: "${SLURM_JOB_END_TIME:?allocation deadline required}"
: "${SDR_COMPLETION_ALLOCATED_SECONDS:?operator full reservation seconds required}"
: "${SDR_COMPLETION_STAGE:?operator calibration or main stage required}"
: "${SDR_COMPLETION_PRIOR_RESERVED_GPU_SECONDS:?operator cumulative reservations required}"
: "${SDR_COMPLETION_INITIAL_RESERVED_GPU_SECONDS:?operator initial diagnostic reservations required}"
prior="$SDR_COMPLETION_PRIOR_RESERVED_GPU_SECONDS"
initial="$SDR_COMPLETION_INITIAL_RESERVED_GPU_SECONDS"
allocated="$SDR_COMPLETION_ALLOCATED_SECONDS"
remaining=$((SLURM_JOB_END_TIME - $(date +%s)))
case "$SDR_COMPLETION_STAGE" in
    calibration) ceiling=600 ;;
    main) ceiling=3000 ;;
    *) echo 'Only calibration/main GPU stages supported' >&2; exit 2 ;;
esac
if (( remaining < 120 || allocated < remaining || allocated > ceiling || prior < 0 || initial < 0 || initial + allocated > 3600 || allocated + prior > 14400 )); then
    echo 'Invalid bounded calibration/main reservation ledger or deadline' >&2; exit 2
fi
bound=$((remaining - 90))
trap 'echo "Completion wrapper ended job=${SLURM_JOB_ID} status=$?"' EXIT
timeout --signal=TERM --kill-after=20s "$((bound+30))s" "$python_bin" "$runner" "$@" \
    --stage "$SDR_COMPLETION_STAGE" --allocation-seconds "$allocated" \
    --prior-reserved-gpu-seconds "$prior" --initial-reserved-gpu-seconds "$initial" --max-seconds "$bound"
