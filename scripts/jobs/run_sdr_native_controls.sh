#!/usr/bin/env bash
# Submit with explicit --chdir=<worktree> and --time=<approved allocation>.
set -euo pipefail
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  SDR_NATIVE_ALLOCATION_START=$(date +%s)
  SDR_NATIVE_ALLOCATION_END=${SLURM_JOB_END_TIME:-}
  if [[ ! "$SDR_NATIVE_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
    allocation_record=$(scontrol show job "$SLURM_JOB_ID" --oneliner)
    allocation_end_text=
    for allocation_field in $allocation_record; do
      if [[ "$allocation_field" == EndTime=* ]]; then allocation_end_text=${allocation_field#EndTime=}; fi
    done
    if [[ -z "$allocation_end_text" || "$allocation_end_text" == Unknown ]]; then
      echo 'Cannot bind actual Slurm allocation deadline.' >&2; exit 1
    fi
    SDR_NATIVE_ALLOCATION_END=$(date -d "$allocation_end_text" +%s)
    unset allocation_record
  fi
  export SDR_NATIVE_ALLOCATION_START SDR_NATIVE_ALLOCATION_END
fi
if [[ ! -f scripts/sdr_native_controls.py ]]; then
  echo 'Run from the explicitly approved worktree cwd.' >&2; exit 1
fi
if [[ -z "${SDR_NATIVE_PYTHON:-}" ]]; then
  set +u
  { source "$HOME/.bashrc" && conda activate mgnp; } || { echo 'Environment initialization failed' >&2; exit 1; }
  set -u
  SDR_NATIVE_PYTHON=python
fi
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "$SDR_NATIVE_PYTHON" scripts/sdr_native_controls.py "$@"
