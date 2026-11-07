#!/bin/bash
set -euo pipefail
PACKET=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327/packet-r5
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
exec /sw/external/python/anaconda3/bin/python3.9 -B "$PACKET/run_cpu.py" "$@"
