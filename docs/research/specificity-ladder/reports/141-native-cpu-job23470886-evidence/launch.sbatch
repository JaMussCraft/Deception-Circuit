#!/bin/bash
#SBATCH --job-name=lad-a3-native-cpu49-62
#SBATCH --account=bjhz-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --constraint=projects
#SBATCH --dependency=afterok:23470779
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=none
#SBATCH --time=00:44:00
#SBATCH --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder
#SBATCH --output=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/logs/lad-a3-native-cpu49-62-%j.out
#SBATCH --error=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/logs/lad-a3-native-cpu49-62-%j.err
set -euo pipefail
: "${SLURM_JOB_ID:?Real Slurm CPU allocation required; do not run on login}"
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder
# No source ~/.bashrc, no allocation-variable edits, no GPU visibility workaround.
exec srun --ntasks=1 --cpus-per-task=4 --cpu-bind=cores --gres=none \
  /sw/external/python/anaconda3/bin/python3.9 \
  .superpowers/sdd/plan-a3/native-continuation-plan/next-chunk-cpu49-62-proposal/supervisor.py
