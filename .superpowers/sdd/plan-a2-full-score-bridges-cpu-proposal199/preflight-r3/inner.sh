#!/bin/bash
set -euo pipefail
R=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime
P=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r3
cd "$R"
source "$R/scripts/cluster/bridges2.env"
set +u
eval "$DC_ACTIVATE"
set -u
export DC_CLUSTER=bridges2 DC_B2_ALLOC=cis260361p PYTHONPATH="$R" PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
export HF_HOME="$DC_HF_HOME" HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
exec /ocean/projects/cis260361p/swong2/envs/mgnp/bin/python -B "$P/cgroup_probe.py"
