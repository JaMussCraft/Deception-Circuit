#!/bin/bash
#SBATCH --job-name=a3-t23-red
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
set -euo pipefail
PACKET=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-red-r1
exec /sw/external/python/anaconda3/bin/python3.9 "$PACKET/run_packet.py" "$@"
