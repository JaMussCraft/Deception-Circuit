#!/usr/bin/env bash
# Root/operator release only. Invoke this original absolute wrapper with sbatch --wrap.
set -euo pipefail
approved_cwd='/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot'
SDR_COMPOSITION_CWD=${SDR_COMPOSITION_CWD:-$approved_cwd}
SDR_COMPOSITION_PYTHON=${SDR_COMPOSITION_PYTHON:-/u/swong2/.conda/envs/mgnp/bin/python}
[[ "$(realpath "$SDR_COMPOSITION_CWD")" == "$approved_cwd" && "$(realpath "${BASH_SOURCE[0]}")" == "$approved_cwd/scripts/jobs/run_sdr_shared_composition.sh" ]] || { echo 'Explicit original wrapper/worktree required.' >&2; exit 1; }
cd "$SDR_COMPOSITION_CWD"
[[ -x "$SDR_COMPOSITION_PYTHON" ]] || { echo 'Explicit executable interpreter required.' >&2; exit 1; }
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  SDR_COMPOSITION_WRAPPER_ENTRY=$(date +%s)
  SDR_COMPOSITION_ALLOCATION_START=${SLURM_JOB_START_TIME:-}
  SDR_COMPOSITION_ALLOCATION_END=${SLURM_JOB_END_TIME:-}
  if [[ ! "$SDR_COMPOSITION_ALLOCATION_START" =~ ^[0-9]+$ || ! "$SDR_COMPOSITION_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
    allocation_record=$(scontrol show job "$SLURM_JOB_ID" --oneliner)
    allocation_start_text= allocation_end_text=
    for allocation_field in $allocation_record; do
      if [[ "$allocation_field" == StartTime=* ]]; then allocation_start_text=${allocation_field#StartTime=}; fi
      if [[ "$allocation_field" == EndTime=* ]]; then allocation_end_text=${allocation_field#EndTime=}; fi
    done
    if [[ ! "$SDR_COMPOSITION_ALLOCATION_START" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_start_text" && "$allocation_start_text" != Unknown ]] || { echo 'Cannot bind actual Slurm StartTime.' >&2; exit 1; }
      SDR_COMPOSITION_ALLOCATION_START=$(TZ=America/Chicago date -d "$allocation_start_text" +%s)
    fi
    if [[ ! "$SDR_COMPOSITION_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_end_text" && "$allocation_end_text" != Unknown ]] || { echo 'Cannot bind actual Slurm EndTime.' >&2; exit 1; }
      SDR_COMPOSITION_ALLOCATION_END=$(TZ=America/Chicago date -d "$allocation_end_text" +%s)
    fi
    unset allocation_record
  fi
  [[ "$SDR_COMPOSITION_ALLOCATION_START" -lt "$SDR_COMPOSITION_ALLOCATION_END" ]] || { echo 'Invalid Slurm allocation interval.' >&2; exit 1; }
  export SDR_COMPOSITION_ALLOCATION_START SDR_COMPOSITION_ALLOCATION_END SDR_COMPOSITION_WRAPPER_ENTRY
fi
exec "$SDR_COMPOSITION_PYTHON" "$SDR_COMPOSITION_CWD/scripts/sdr_shared_composition.py" "$@"
