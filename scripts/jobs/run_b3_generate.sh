#!/usr/bin/env bash
# B3 generation (plan B3 sections 1.3 and 1.4, ticket T4). Submit only with explicit --chdir=<worktree> and --time.
# Example: sbatch --chdir=<worktree> --time=00:45:00 ... scripts/jobs/run_b3_generate.sh \
#   --variant both --split calibration --controls base --batch-size 32 --out outputs/_studies/b3/j1_calibration
set -euo pipefail
if [[ ! -f scripts/b3_generate.py || "$(pwd -P)" != "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route" ]]; then
  echo 'Run from the explicitly approved worktree cwd.' >&2; exit 1
fi
if [[ -z "${B3_PYTHON:-}" ]]; then
  set +u
  { source "$HOME/.bashrc" && conda activate mgnp; } || { echo 'Environment initialization failed' >&2; exit 1; }
  set -u
  B3_PYTHON=python
fi
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export RESEARCH_DIRECTION="${RESEARCH_DIRECTION:-instructed-route}"
exec "$B3_PYTHON" scripts/b3_generate.py "$@"
