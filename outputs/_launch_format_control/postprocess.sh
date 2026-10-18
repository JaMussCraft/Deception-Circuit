#!/bin/bash
# After a suite's jobs finish: merge the shards, flip-audit every knockout cell
# (with the positional-default check), write the D/H/F overlap table, and the
# evaluation summary with the pre-registered verdict (ticket 05's writer).
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
# Summary and the pre-registered verdict (ticket 05). Add --eval5-dir DIR once eval 5 has run.
python write_format_control_summary.py "$ROOT" --data-dir data/datasets
