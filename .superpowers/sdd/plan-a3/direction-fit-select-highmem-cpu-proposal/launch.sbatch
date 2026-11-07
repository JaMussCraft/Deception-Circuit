#!/bin/bash
#SBATCH --job-name=lad-a3-fitselect-highmem
#SBATCH --account=beto-delta-cpu
#SBATCH --partition=cpu
#SBATCH --constraint=projects
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=192G
#SBATCH --gres=none
#SBATCH --time=00:45:00
#SBATCH --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder
#SBATCH --output=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/logs/lad-a3-fitselect-highmem-%j.out
#SBATCH --error=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/logs/lad-a3-fitselect-highmem-%j.err
set -euo pipefail
: "${SLURM_JOB_ID:?Actual CPU allocation required}"
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
exec srun --ntasks=1 --cpus-per-task=4 --cpu-bind=cores --gres=none \
 /sw/external/python/anaconda3/bin/python3.9 \
 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-fit-select-highmem-cpu-proposal/supervisor.py
