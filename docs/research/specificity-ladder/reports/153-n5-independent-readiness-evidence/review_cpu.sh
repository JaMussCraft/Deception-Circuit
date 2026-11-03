#!/bin/bash
set -euo pipefail
D=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/153-n5-independent-readiness-evidence
B=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-861f84a3938a/runtime
export PYTHONPATH="$B" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false HF_HOME=/work/nvme/beto/swong2 HF_HUB_CACHE=/work/nvme/beto/swong2/hub
cd "$B"
timeout --signal=TERM --kill-after=10s 240s /u/swong2/.conda/envs/mgnp/bin/python "$D/review.py"
