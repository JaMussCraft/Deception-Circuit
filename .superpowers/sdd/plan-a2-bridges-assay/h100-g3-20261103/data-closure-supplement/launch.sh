#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual CPU job required}"
P="$(cd "$(dirname "$0")" && pwd)"
OUT="$P/result-$SLURM_JOB_ID"
mkdir "$OUT"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2
export PYTHONPATH=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime
# Whole traced unchanged owning read path bounded independently of scheduler; no retry.
timeout --signal=TERM --kill-after=15s 720s strace -f -yy -s 4096 -e trace=open,openat,chdir,fchdir -o "$OUT/filesystem.strace" /u/swong2/.conda/envs/mgnp/bin/python "$P/audit.py" run "$OUT" > "$OUT/owning-run.log" 2>&1
# Collection is also CPU work and has its own bounded finishing window.
timeout --signal=TERM --kill-after=5s 90s /u/swong2/.conda/envs/mgnp/bin/python "$P/audit.py" collect "$OUT" > "$OUT/collection.log" 2>&1
