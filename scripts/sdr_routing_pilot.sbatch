#!/usr/bin/env bash
#SBATCH --job-name=sdr-routing-pilot
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:h200:1
# Time/account/partition/output MUST be specified by the lead at submission.
set -euo pipefail
# Slurm executes a spooled copy, so BASH_SOURCE is not the repository path.
# Submit from the intended worktree (and use sbatch --chdir there explicitly).
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
    : "${SLURM_SUBMIT_DIR:?submit from the pilot worktree}"
    SCRIPT_DIR="$(cd -- "$SLURM_SUBMIT_DIR/scripts" && pwd -P)"
else
    SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
fi
if [[ ! -r "$SCRIPT_DIR/sdr_routing_pilot.py" ]]; then
    echo "Pilot runner missing from verified scripts directory: $SCRIPT_DIR" >&2
    exit 2
fi
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
PYTHON=/u/swong2/.conda/envs/mgnp/bin/python
# Direct supported interpreter avoids bashrc side effects; no activation needed.
for argument in "$@"; do
    if [[ "$argument" == --dry-run ]]; then
        exec "$PYTHON" "$SCRIPT_DIR/sdr_routing_pilot.py" "$@"
    fi
done
: "${SLURM_JOB_ID:?submit within one H200 Slurm allocation}"
# Slurm exposes the actual time limit in minutes, including command-line --time.
: "${SLURM_JOB_END_TIME:?Slurm must expose allocation end time}"
remaining=$((SLURM_JOB_END_TIME - $(date +%s)))
if (( remaining < 120 || remaining > 3600 )); then
    echo 'Allocation must have120..3600seconds remaining' >&2
    exit 2
fi
allocated_seconds="${SDR_ALLOCATED_SECONDS:?lead must set SDR_ALLOCATED_SECONDS to full reserved walltime}"
prior_seconds="${SDR_PRIOR_RESERVED_GPU_SECONDS:-0}"
if (( allocated_seconds > 3600 || allocated_seconds < remaining || allocated_seconds + prior_seconds > 3600 )); then
    echo 'Reservation ledger or allocation exceeds Stage1 cap' >&2
    exit 2
fi
max_seconds=$((remaining - 90))
if (( max_seconds > 3300 )); then max_seconds=3300; fi
# CPU dry-run bypasses allocation checks above; real launch is independently
# checked by Python for exactly one H200 and complete offline weight shards.
trap 'echo "SDR wrapper receipt: job=${SLURM_JOB_ID} exit=$? ended=$(date -u +%FT%TZ)"' EXIT
# Defaults come last, so user args cannot widen the deadline/reservation bound.
timeout --signal=TERM --kill-after=20s "$((max_seconds + 30))s" \
    "$PYTHON" "$SCRIPT_DIR/sdr_routing_pilot.py" "$@" \
    --max-seconds "$max_seconds" --allocated-seconds "$allocated_seconds" \
    --reserved-gpu-seconds "$allocated_seconds" --prior-reserved-gpu-seconds "$prior_seconds"
