#!/bin/bash
# REVIEW PLAN ONLY. Root may run only after accounting repair, independent review,
# explicit source freeze and explicit release of a fresh injected scenario.
set -euo pipefail
scenario_root=${1:?supply a new absolute scenario root}
python_bin=/u/swong2/.conda/envs/mgnp/bin/python
export PYTHONPATH=.
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
run_phase() {
    local phase=$1 start=${2:-0} count=${3:-32}
    local tag="${phase}-${start}-${count}-$(date +%s%N)"
    local cgroup_rel cgroup_file exit_code began finished
    mkdir -p "$scenario_root/process-logs"
    cgroup_rel=$(awk -F: '$1=="0"{print $3}' /proc/self/cgroup)
    cgroup_file="/sys/fs/cgroup${cgroup_rel}/memory.events"
    if [[ -r "$cgroup_file" ]]; then cat "$cgroup_file" > "$scenario_root/process-logs/$tag.memory-before"; fi
    began=$(date +%s)
    set +e
    /usr/bin/time -v -o "$scenario_root/process-logs/$tag.time" timeout --signal=TERM --kill-after=15s 600s \
        "$python_bin" -m tests.a3_direction_native_scenario --root "$scenario_root" --phase "$phase" \
        --start "$start" --count "$count" --resume > "$scenario_root/process-logs/$tag.log" 2>&1
    exit_code=$?
    set -e
    finished=$(date +%s)
    printf 'exit_code=%s\nelapsed_seconds=%s\n' "$exit_code" "$((finished-began))" > "$scenario_root/process-logs/$tag.exit"
    if [[ -r "$cgroup_file" ]]; then cat "$cgroup_file" > "$scenario_root/process-logs/$tag.memory-after"; fi
    if [[ "$exit_code" -ne 0 ]]; then return "$exit_code"; fi
}
case_count() {
    "$python_bin" - "$scenario_root" "$1" <<'PY'
import sys
from pathlib import Path
from tests import a3_direction_native_scenario as s
root=Path(sys.argv[1]);phase=sys.argv[2]
d,p,_,_=s.verify_scenario(root,load_model=False)
if phase=='prefit':
    inv=s.r.workload.build_inventory(d,p,stage='prefit');n=len(inv['packing_invocations'] or s.r._serial_invocations(inv))
elif phase=='fit':n=len(s.r.workload.build_inventory(d,p,stage='fit-select')['capture_shards'])
elif phase=='validation':
    fits,_=s.r.read_bundle(root/'fits');n=len(s.r.workload.build_inventory(d,p,stage='fit-select',fits=fits)['shards'])
else:
    selected,_=s.r.read_bundle(root/'selected')
    if phase=='selected-pilot':
        n=len(s.r.workload.build_inventory(d,p,stage='selected-pilot',selected=selected)['packing_invocations']);assert n==63
    else:
        inv=s.r.workload.build_inventory(d,p,stage='remaining',selected=selected)
        n=sum(x['panel']==phase for x in inv['shards']);assert n=={'calibration':630,'assessment':3978}[phase]
print(n)
PY
}
chunk_phase() {
    local phase=$1 size=$2 total start
    total=$(case_count "$phase")
    for ((start=0;start<total;start+=size)); do run_phase "$phase" "$start" "$size"; done
}
# Intended sequential execution; do not parallelize model processes.
# Each timeout bounds one process, not time to finish a whole phase.
# On timeout/error, retain artifacts and resume the failed chunk with --resume;
# authenticated complete cases/shards may be skipped, partial artifacts reject.
if [[ -e "$scenario_root/scenario" ]]; then
    printf 'Fresh initialization required; resume only the explicit failed phase/chunk.\n' >&2
    exit 2
fi
run_phase init
chunk_phase prefit 4
run_phase prefit-aggregate
chunk_phase fit 4
chunk_phase validation 32
run_phase select
chunk_phase selected-pilot 4
run_phase selected-pilot-aggregate
chunk_phase calibration 32
run_phase calibration-summary
chunk_phase assessment 32
run_phase summary
# All original pilot cases and all original calibration/assessment rows remain
# mandatory. An injected final result must still refuse scientific finalization.
