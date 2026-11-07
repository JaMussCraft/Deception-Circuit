#!/bin/bash
# REVIEW PLAN ONLY. Root may run only after accounting repair, independent review,
# explicit source freeze and explicit release of a fresh injected scenario.
# Scoring chunk size starts at32; root may resize later chunks from observed
# startup/per-shard time with headroom under the unchanged600s process limit.
set -euo pipefail
scenario_root=${1:?supply a new absolute scenario root}
python_bin=/u/swong2/.conda/envs/mgnp/bin/python
export PYTHONPATH=.
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
scoring_chunk_size=${SCORING_CHUNK_SIZE:-32}
cgroup_snapshot() {
    local output_prefix=$1 cgroup_rel cgroup_dir level=0 field
    cgroup_rel=$(awk -F: '$1=="0"{print $3}' /proc/self/cgroup)
    cgroup_dir="/sys/fs/cgroup${cgroup_rel}"
    while :; do
        printf '%s %s\n' "$level" "$cgroup_dir" >> "$output_prefix.cgroup-paths"
        for field in memory.events memory.max; do
            if [[ -r "$cgroup_dir/$field" ]]; then cat "$cgroup_dir/$field" > "$output_prefix.$level.$field"; fi
        done
        if [[ "$cgroup_dir" == /sys/fs/cgroup ]]; then break; fi
        cgroup_dir=${cgroup_dir%/*}
        if [[ "$cgroup_dir" != /sys/fs/cgroup* ]]; then break; fi
        level=$((level+1))
    done
}
run_phase() {
    local phase=$1 start=${2:-0} count=${3:-32}
    local tag="${phase}-${start}-${count}-$(date +%s%N)"
    local exit_code began finished
    mkdir -p "$scenario_root/process-logs"
    cgroup_snapshot "$scenario_root/process-logs/$tag.memory-before"
    /sw/external/python/anaconda3/bin/python3.9 - "$scenario_root/process-logs/$tag.headroom-before.json" <<'MEMORY'
from pathlib import Path
import json,sys
relative=next(x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
path=Path('/sys/fs/cgroup')/relative.lstrip('/');rows=[];enough=True
while True:
    current=path/'memory.current';maximum=path/'memory.max'
    if current.exists() and maximum.exists():
        value=current.read_text().strip();limit=maximum.read_text().strip()
        row=dict(path=str(path),current_bytes=int(value),max_bytes=limit)
        if limit!='max':
            row['headroom_bytes']=int(limit)-int(value)
            enough=enough and row['headroom_bytes']>=17179869184
        rows.append(row)
    if path==Path('/sys/fs/cgroup'):break
    path=path.parent
record=dict(cgroups=rows,minimum_required_headroom_bytes=17179869184,enough=enough)
Path(sys.argv[1]).write_text(json.dumps(record,indent=2)+'\n')
if not enough:raise SystemExit('Finite ancestor has less than16GiB headroom; no model process launched.')
MEMORY
    began=$(date +%s)
    set +e
    /usr/bin/time -v -o "$scenario_root/process-logs/$tag.time" timeout --signal=TERM --kill-after=15s 600s \
        "$python_bin" -m tests.a3_direction_native_scenario --root "$scenario_root" --phase "$phase" \
        --start "$start" --count "$count" --resume > "$scenario_root/process-logs/$tag.log" 2>&1
    exit_code=$?
    set -e
    finished=$(date +%s)
    printf 'exit_code=%s\nelapsed_seconds=%s\n' "$exit_code" "$((finished-began))" > "$scenario_root/process-logs/$tag.exit"
    cgroup_snapshot "$scenario_root/process-logs/$tag.memory-after"
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

case "${2:?phase or count}" in
  count) case_count "${3:?stage}" ;;
  *) run_phase "$2" "${3:-0}" "${4:-32}" ;;
esac
