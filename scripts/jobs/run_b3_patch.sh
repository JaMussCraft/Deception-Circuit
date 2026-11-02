#!/usr/bin/env bash
# B3 patching (plan B3 sections 2 and 3; J3 sycophancy, J4 transfer and C3, the knockout parity check).
# Submit only with an explicit --chdir=<worktree> and --time=<allocation> on the sbatch command line, after a
# login-node --dry-run of the same arguments. Patterned on scripts/jobs/run_sdr_cue_probe.sh.
set -euo pipefail
if [[ ! -f scripts/b3_patch.py || "$(pwd -P)" != "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route" ]]; then
  echo 'Run from the explicitly approved worktree cwd.' >&2; exit 1
fi
if [[ -z "${B3_PATCH_PYTHON:-}" ]]; then
  set +u
  { source "$HOME/.bashrc" && conda activate mgnp; } || { echo 'Environment initialization failed' >&2; exit 1; }
  set -u
  B3_PATCH_PYTHON=python
fi
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "$B3_PATCH_PYTHON" scripts/b3_patch.py "$@"
