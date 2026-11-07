#!/bin/bash
# ROOT submits held with --account=ACTUAL --partition=gpuH200x8 --hold --no-requeue --gpus=1 --cpus-per-task=4 --mem=64G --time=00:45:00 --chdir=FROZEN_RUNTIME.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 DC_CLUSTER=delta
exec /sw/external/python/anaconda3/bin/python3.9 "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/n5-mask-H200-launch-861f84a3938a/run-bounded-pilot.py"
