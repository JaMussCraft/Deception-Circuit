#!/bin/bash
# After a suite's jobs finish: merge the shards, flip-audit every knockout cell
# (with the positional-default check), write the D/H/F overlap table, and the
# placeholder summary until ticket 05's writer lands.
# usage: bash outputs/_launch_format_control/postprocess.sh <suite>
set -euo pipefail
cd "$(dirname "$0")/../.."
S=${1:?suite}
L=outputs/_launch_format_control
ROOT=outputs/_suites/$S
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python $L/fc_launch.py merge "$S"
python $L/flip_audit_analysis.py "$ROOT" --data-dir data/datasets
python $L/fc_launch.py overlap "$S"
# Placeholder summary (ticket 05 replaces it with the decision-rule writer).
W=/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_suites/_launch_260922/write_suite_summary.py
if [ -f "$W" ]; then python "$W" "$ROOT" || echo "placeholder summary writer failed (non-fatal)"; fi
