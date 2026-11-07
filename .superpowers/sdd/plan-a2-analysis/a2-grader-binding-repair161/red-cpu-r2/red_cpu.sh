#!/bin/bash
set -euo pipefail
E=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/a2-grader-binding-repair161/red-cpu-r2
export PYTHONPATH=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/a2-grader-binding-candidate161
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
timeout --kill-after=5s 75s /u/swong2/.conda/envs/mgnp/bin/python "$E/run.py" mgnp > "$E/mgnp.log" 2>&1
timeout --kill-after=5s 75s /sw/external/python/anaconda3/bin/python3.9 "$E/run.py" base > "$E/base.log" 2>&1
