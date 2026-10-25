#!/usr/bin/env bash
# Root/operator release only; use sbatch --wrap with this original absolute path.
set -euo pipefail
approved_cwd='/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot'
if [[ "$(pwd -P)" != "$approved_cwd" || ! -f scripts/sdr_cue_positions.py || "$(realpath "${BASH_SOURCE[0]}")" != "$approved_cwd/scripts/jobs/run_sdr_cue_positions.sh" ]]; then
  echo 'Run the original wrapper from the explicitly approved worktree cwd.' >&2; exit 1
fi
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  SDR_POS_WRAPPER_ENTRY=$(date +%s)
  SDR_POS_ALLOCATION_START=${SLURM_JOB_START_TIME:-}
  SDR_POS_ALLOCATION_END=${SLURM_JOB_END_TIME:-}
  if [[ ! "$SDR_POS_ALLOCATION_START" =~ ^[0-9]+$ || ! "$SDR_POS_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
    allocation_record=$(scontrol show job "$SLURM_JOB_ID" --oneliner)
    allocation_start_text= allocation_end_text=
    for allocation_field in $allocation_record; do
      if [[ "$allocation_field" == StartTime=* ]]; then allocation_start_text=${allocation_field#StartTime=}; fi
      if [[ "$allocation_field" == EndTime=* ]]; then allocation_end_text=${allocation_field#EndTime=}; fi
    done
    if [[ ! "$SDR_POS_ALLOCATION_START" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_start_text" && "$allocation_start_text" != Unknown ]] || { echo 'Cannot bind actual Slurm StartTime.' >&2; exit 1; }
      SDR_POS_ALLOCATION_START=$(TZ=America/Chicago date -d "$allocation_start_text" +%s)
    fi
    if [[ ! "$SDR_POS_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_end_text" && "$allocation_end_text" != Unknown ]] || { echo 'Cannot bind actual Slurm EndTime.' >&2; exit 1; }
      SDR_POS_ALLOCATION_END=$(TZ=America/Chicago date -d "$allocation_end_text" +%s)
    fi
    unset allocation_record
  fi
  [[ "$SDR_POS_ALLOCATION_START" -lt "$SDR_POS_ALLOCATION_END" ]] || { echo 'Invalid Slurm allocation interval.' >&2; exit 1; }
  export SDR_POS_ALLOCATION_START SDR_POS_ALLOCATION_END SDR_POS_WRAPPER_ENTRY
fi
if [[ -z "${SDR_POS_PYTHON:-}" ]]; then
  set +u
  { source "$HOME/.bashrc" && conda activate mgnp; } || { echo 'Environment initialization failed' >&2; exit 1; }
  set -u
  SDR_POS_PYTHON=python
fi
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "$SDR_POS_PYTHON" scripts/sdr_cue_positions.py "$@"
