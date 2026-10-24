#!/usr/bin/env bash
# Root/operator release only; explicit sbatch --chdir and --time required.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
if [[ ! -f "$repo_root/scripts/sdr_cue_circuits.py" || "$(pwd -P)" != "$repo_root" ]]; then
  echo 'Run from the wrapper repository cwd.' >&2; exit 1
fi
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  SDR_CC_WRAPPER_ENTRY=$(date +%s)
  SDR_CC_ALLOCATION_START=${SLURM_JOB_START_TIME:-}
  SDR_CC_ALLOCATION_END=${SLURM_JOB_END_TIME:-}
  for allocation_epoch in "$SDR_CC_ALLOCATION_START" "$SDR_CC_ALLOCATION_END"; do
    [[ -z "$allocation_epoch" || "$allocation_epoch" =~ ^[0-9]{1,10}$ ]] || { echo 'Invalid Slurm epoch.' >&2; exit 1; }
  done
  if [[ ! "$SDR_CC_ALLOCATION_START" =~ ^[0-9]+$ || ! "$SDR_CC_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
    case "${DC_CLUSTER:-delta}" in
      bridges2) allocation_tz=America/New_York ;;
      delta) allocation_tz=America/Chicago ;;
      *) echo 'Unknown allocation cluster timezone.' >&2; exit 1 ;;
    esac
    allocation_record=$(TZ="$allocation_tz" scontrol show job "$SLURM_JOB_ID" --oneliner)
    allocation_start_text= allocation_end_text=
    for allocation_field in $allocation_record; do
      if [[ "$allocation_field" == StartTime=* ]]; then allocation_start_text=${allocation_field#StartTime=}; fi
      if [[ "$allocation_field" == EndTime=* ]]; then allocation_end_text=${allocation_field#EndTime=}; fi
    done
    if [[ ! "$SDR_CC_ALLOCATION_START" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_start_text" && "$allocation_start_text" != Unknown ]] || { echo 'Cannot bind actual Slurm StartTime.' >&2; exit 1; }
      SDR_CC_ALLOCATION_START=$(TZ="$allocation_tz" date -d "$allocation_start_text" +%s)
    fi
    if [[ ! "$SDR_CC_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_end_text" && "$allocation_end_text" != Unknown ]] || { echo 'Cannot bind actual Slurm EndTime.' >&2; exit 1; }
      SDR_CC_ALLOCATION_END=$(TZ="$allocation_tz" date -d "$allocation_end_text" +%s)
    fi
    unset allocation_record
  fi
  if [[ ! "$SDR_CC_ALLOCATION_START" =~ ^[0-9]+$ || ! "$SDR_CC_ALLOCATION_END" =~ ^[0-9]+$ ]] ||
     (( SDR_CC_ALLOCATION_START > SDR_CC_WRAPPER_ENTRY || SDR_CC_ALLOCATION_END <= SDR_CC_WRAPPER_ENTRY || SDR_CC_ALLOCATION_START >= SDR_CC_ALLOCATION_END )); then
    echo 'Invalid actual Slurm allocation bounds.' >&2; exit 1
  fi
  if [[ -n "${SLURM_TIMELIMIT:-}" ]]; then
    [[ "$SLURM_TIMELIMIT" =~ ^[0-9]+$ ]] || { echo 'Invalid Slurm allocation duration.' >&2; exit 1; }
    (( SDR_CC_ALLOCATION_END - SDR_CC_ALLOCATION_START == SLURM_TIMELIMIT * 60 )) || { echo 'Slurm allocation duration mismatch.' >&2; exit 1; }
  fi
  export SDR_CC_ALLOCATION_START SDR_CC_ALLOCATION_END SDR_CC_WRAPPER_ENTRY
fi
if [[ -z "${SDR_CC_PYTHON:-}" ]]; then
  set +u
  { source "$HOME/.bashrc" && conda activate mgnp; } || { echo 'Environment initialization failed' >&2; exit 1; }
  set -u
  SDR_CC_PYTHON=python
fi
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "$SDR_CC_PYTHON" scripts/sdr_cue_circuits.py "$@"
