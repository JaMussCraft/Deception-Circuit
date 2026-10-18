#!/bin/bash
# Post-process a coarse heads-only Format Circuit run so the evaluator can load it.
# Steps 1-2 of the coarse SDR wave's _launch/postprocess.sh; no evaluation is
# submitted here (ticket 04 owns the evaluation suite).
#   1. keep the trained masks: copy active_nodes.json / config.json to *.coarse.json
#      (idempotent; never overwrites an existing *.coarse.json)
#   2. expand_coarse_masks.py <run_dir>: every fine unit of a live head opens, and
#      config.json gains the fine gate modules (skipped if already expanded)
# Then run size_check.py, which reads active_nodes.coarse.json and prints the
# in-run sufficiency gate.
# usage: bash outputs/_launch_format_control/postprocess_coarse.sh <run_dir>
#        (PY=<interpreter> to override the default mgnp python)
set -euo pipefail
cd "$(dirname "$0")/../.."               # repo root
RUN=${1:?run_dir}
PY=${PY:-/u/swong2/.conda/envs/mgnp/bin/python}
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
[ -f "$RUN/results.json" ] || { echo "SKIP $RUN: no results.json (run unfinished or crashed)"; exit 3; }
for f in active_nodes config; do
  [ -f "$RUN/$f.coarse.json" ] || cp "$RUN/$f.json" "$RUN/$f.coarse.json"
done
if "$PY" -c "import json,sys; m=json.load(open(sys.argv[1]))['masks']; sys.exit(0 if 'attention_neurons' in m else 1)" "$RUN/active_nodes.json"; then
  echo "already expanded"
else
  "$PY" expand_coarse_masks.py "$RUN" | tail -4
fi
