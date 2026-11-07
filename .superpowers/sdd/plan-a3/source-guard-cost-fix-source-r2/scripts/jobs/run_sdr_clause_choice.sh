#!/usr/bin/env bash
# Root/operator release only. Invoke this original absolute wrapper with sbatch --wrap.
set -euo pipefail
approved_cwd='/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot'
SDR_CLAUSE_CWD=${SDR_CLAUSE_CWD:-$approved_cwd}
SDR_CLAUSE_PYTHON=${SDR_CLAUSE_PYTHON:-/u/swong2/.conda/envs/mgnp/bin/python}
[[ "$(realpath "$SDR_CLAUSE_CWD")" == "$approved_cwd" && "$(realpath "${BASH_SOURCE[0]}")" == "$approved_cwd/scripts/jobs/run_sdr_clause_choice.sh" ]] || { echo 'Explicit original wrapper/worktree required.' >&2; exit 1; }
cd "$SDR_CLAUSE_CWD"
[[ -x "$SDR_CLAUSE_PYTHON" ]] || { echo 'Explicit executable interpreter required.' >&2; exit 1; }
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  SDR_CLAUSE_WRAPPER_ENTRY=$(date +%s)
  SDR_CLAUSE_ALLOCATION_START=${SLURM_JOB_START_TIME:-}
  SDR_CLAUSE_ALLOCATION_END=${SLURM_JOB_END_TIME:-}
  if [[ ! "$SDR_CLAUSE_ALLOCATION_START" =~ ^[0-9]+$ || ! "$SDR_CLAUSE_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
    allocation_record=$(scontrol show job "$SLURM_JOB_ID" --oneliner)
    allocation_start_text= allocation_end_text=
    for allocation_field in $allocation_record; do
      if [[ "$allocation_field" == StartTime=* ]]; then allocation_start_text=${allocation_field#StartTime=}; fi
      if [[ "$allocation_field" == EndTime=* ]]; then allocation_end_text=${allocation_field#EndTime=}; fi
    done
    if [[ ! "$SDR_CLAUSE_ALLOCATION_START" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_start_text" && "$allocation_start_text" != Unknown ]] || { echo 'Cannot bind actual Slurm StartTime.' >&2; exit 1; }
      SDR_CLAUSE_ALLOCATION_START=$(TZ=America/Chicago date -d "$allocation_start_text" +%s)
    fi
    if [[ ! "$SDR_CLAUSE_ALLOCATION_END" =~ ^[0-9]+$ ]]; then
      [[ -n "$allocation_end_text" && "$allocation_end_text" != Unknown ]] || { echo 'Cannot bind actual Slurm EndTime.' >&2; exit 1; }
      SDR_CLAUSE_ALLOCATION_END=$(TZ=America/Chicago date -d "$allocation_end_text" +%s)
    fi
    unset allocation_record
  fi
  [[ "$SDR_CLAUSE_ALLOCATION_START" -lt "$SDR_CLAUSE_ALLOCATION_END" ]] || { echo 'Invalid Slurm allocation interval.' >&2; exit 1; }
  export SDR_CLAUSE_ALLOCATION_START SDR_CLAUSE_ALLOCATION_END SDR_CLAUSE_WRAPPER_ENTRY
fi
exec "$SDR_CLAUSE_PYTHON" "$SDR_CLAUSE_CWD/scripts/sdr_clause_choice.py" "$@"
