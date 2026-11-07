#!/bin/bash
set -euo pipefail
D=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-plan/red-cpu
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-candidate
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
timeout --kill-after=15s 180s /u/swong2/.conda/envs/mgnp/bin/python "$D/run.py" mgnp > "$D/mgnp.log" 2>&1
timeout --kill-after=15s 180s /sw/external/python/anaconda3/bin/python3.9 "$D/run.py" base > "$D/base.log" 2>&1
