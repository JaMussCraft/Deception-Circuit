#!/usr/bin/env bash
# Root reserves/submits. This wrapper resolves the existing cluster environment.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
if [[ -n ${SPECIFICITY_A3_MASK_REPO_ROOT:-} ]]; then
    script_root="$SPECIFICITY_A3_MASK_REPO_ROOT"
elif [[ -n ${SLURM_JOB_ID:-} ]]; then
    # sbatch copies BASH_SOURCE into its spool. --chdir controls the real cwd.
    script_root="$(pwd -P)"
else
    script_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
fi
if [[ ! -f "$script_root/component_analysis/a3_mask_pipeline.py" || ! -f "$script_root/scripts/jobs/specificity_a3_mask.sh" ]]; then
    echo 'Mask worktree not found: use --chdir=WORKTREE or SPECIFICITY_A3_MASK_REPO_ROOT.' >&2
    exit 1
fi
if ! cmp -s -- "${BASH_SOURCE[0]}" "$script_root/scripts/jobs/specificity_a3_mask.sh"; then
    echo 'Selected worktree wrapper differs from the launched mask script; use the frozen worktree.' >&2
    exit 1
fi
cd -- "$script_root"
case ${DC_CLUSTER:-delta} in
    delta|bridges2) source "scripts/cluster/${DC_CLUSTER:-delta}.env" ;;
    *) echo 'Unsupported DC_CLUSTER.' >&2; exit 1 ;;
esac
export DC_CLUSTER="$DC_CLUSTER_NAME"
if [[ -n ${A3_MASK_PYTHON:-} ]]; then
    python_bin="$A3_MASK_PYTHON"
elif [[ -n ${DC_PYTHON:-} ]]; then
    python_bin="$DC_PYTHON"
elif [[ -n ${DC_ENV_PREFIX:-} ]]; then
    python_bin="$DC_ENV_PREFIX/bin/python"
else
    python_bin=/u/swong2/.conda/envs/mgnp/bin/python
fi
export SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE="$(command -v -- "$python_bin")"
# Delta's existing pinned snapshots use this flat hub cache (legacy
# TRANSFORMERS_CACHE). Bind both current and legacy readers to that same cache.
export HF_HOME="$DC_HF_HOME"
export HF_HUB_CACHE="$DC_HF_HOME"
export TRANSFORMERS_CACHE="$HF_HUB_CACHE"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
args=("$@")
for arg in "${args[@]}"; do
    if [[ "$arg" == --dry-run ]]; then
        printf '%q ' "$python_bin" -B -m component_analysis.a3_mask_pipeline "${args[@]}"
        printf '\n'
        exec "$python_bin" -B -m component_analysis.a3_mask_pipeline "${args[@]}"
    fi
done
exec "$python_bin" -B -m component_analysis.a3_mask_pipeline "${args[@]}"
