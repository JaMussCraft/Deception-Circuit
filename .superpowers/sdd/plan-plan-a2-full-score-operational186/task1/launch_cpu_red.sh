#!/bin/bash
set -euo pipefail
# Slurm relocates this file: never derive the packet directory from $0.
PACKET=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1
exec /sw/external/python/anaconda3/bin/python3.9 "$PACKET/run_cpu_red.py" "$@"
