#!/usr/bin/env bash
# Root/operator release only; explicit sbatch --chdir and --time required.
set -euo pipefail
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  SDR_CC_WRAPPER_ENTRY=$(date +%s)
  SDR_CC_ALLOCATION_START=${SLURM_JOB_START_TIME:-}
  SDR_CC_ALLOCATION_END=${SLURM_JOB_END_TIME:-}
  if [[ ! "$SDR_CC_ALLOCATION_START" =~ ^[0-9]+$ || ! "$SDR_CC_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
    allocation_record=$(scontrol show job "$SLURM_JOB_ID" --oneliner)
    allocation_start_text= allocation_end_text=
    for allocation_field in $allocation_record; do
      if [[ "$allocation_field" == StartTime=* ]]; then allocation_start_text=${allocation_field#StartTime=}; fi
      if [[ "$allocation_field" == EndTime=* ]]; then allocation_end_text=${allocation_field#EndTime=}; fi
    done
    if [[ ! "$SDR_CC_ALLOCATION_START" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_start_text" && "$allocation_start_text" != Unknown ]] || { echo 'Cannot bind actual Slurm StartTime.' >&2; exit 1; }
      SDR_CC_ALLOCATION_START=$(date -d "$allocation_start_text" +%s)
    fi
    if [[ ! "$SDR_CC_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_end_text" && "$allocation_end_text" != Unknown ]] || { echo 'Cannot bind actual Slurm EndTime.' >&2; exit 1; }
      SDR_CC_ALLOCATION_END=$(date -d "$allocation_end_text" +%s)
    fi
    unset allocation_record
  fi
  export SDR_CC_ALLOCATION_START SDR_CC_ALLOCATION_END SDR_CC_WRAPPER_ENTRY
fi
if [[ ! -f scripts/sdr_cue_circuits.py || "$(pwd -P)" != '/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot' ]]; then
  echo 'Run from the explicitly approved worktree cwd.' >&2; exit 1
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
