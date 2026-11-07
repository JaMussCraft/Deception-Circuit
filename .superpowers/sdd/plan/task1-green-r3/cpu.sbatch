#!/bin/bash
#SBATCH --job-name=a3-t1-transport
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
set -euo pipefail
PACKET=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3
exec /sw/external/python/anaconda3/bin/python3.9 "$PACKET/run_packet.py" "$@"
