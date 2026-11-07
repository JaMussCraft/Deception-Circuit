#!/bin/bash
#SBATCH --job-name=a3-t23-green
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
set -euo pipefail
PACKET=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r3
exec /sw/external/python/anaconda3/bin/python3.9 "$PACKET/run_packet.py" "$@"
