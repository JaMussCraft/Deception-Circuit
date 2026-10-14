#!/bin/bash
# EVAL 5 for one format-control family and benchmark group: D, H and F bound in
# ONE evaluate_circuit.py invocation (one screen, one judge cache, identical
# settings; random rows size-matched per circuit). See README_eval5.md.
#
# usage: bash outputs/_launch_format_control/submit_eval5.sh <far|sdr|sdr_coarse> <sm|lb>
#            [--dry] [--standin] [--account A] [--partition P] [--time HH:MM:SS]
#            [--config suites.json] [--manifest suite_manifest.json] [--suite-root DIR]
#            [--log-dir DIR] [--jobs-file FILE]
#
# --dry      print the command, run `evaluate_circuit.py --dry-run` (log under
#            dryrun_eval5/), print the cost estimate, and print the sbatch line
#            only if F is configured and its knockout passes the wikitext KL gate.
#            Never submits. Exit 0 iff the dry-run passed.
# --standin  F := H (plumbing only, logs under dryrun_eval5_standin/); never
#            gets a submit line.
# (no --dry) submits ONLY when every refusal is cleared, in this order:
#            F configured in suites.json; F's knockout wikitext KL <= 0.66 on the
#            D and F test sets of ticket 04's suite; FORMAT_CONTROL_EVAL5_GO=1
#            (the researcher's explicit go-ahead); a passing --dry-run of these
#            exact arguments. Any refusal exits 3 and names its reason.
#
# --partition defaults to gpuA40x4: the cached screens (main checkout,
# outputs/_screens) were made on NVIDIA A40 and the GPU is part of the cache key;
# another GPU re-screens and the items stop matching the existing eval5_* suites.
set -euo pipefail
cd "$(dirname "$0")/../.."

PY=${PYTHON:-python}
EVALUATOR=${EVAL5_EVALUATOR:-evaluate_circuit.py}
E5=outputs/_launch_format_control/eval5_cmd.py

FAMILY=${1:?family: far|sdr|sdr_coarse}; GROUP=${2:?group: sm|lb}; shift 2
DRY=0; STANDIN=0; ACCOUNT=bgrb-delta-gpu; PARTITION=gpuA40x4; TIME=""
LOGDIR=""; JOBS=outputs/_launch_format_control/eval5_jobs.txt
CFG=(); PATHS=()
while [ $# -gt 0 ]; do
    case $1 in
        --dry) DRY=1;;
        --standin) STANDIN=1;;
        --account) ACCOUNT=$2; shift;;
        --partition) PARTITION=$2; shift;;
        --time) TIME=$2; shift;;
        --config) CFG=(--config "$2"); shift;;
        --manifest|--suite-root) PATHS+=("$1" "$2"); shift;;
        --log-dir) LOGDIR=$2; shift;;
        --jobs-file) JOBS=$2; shift;;
        *) echo "unknown argument: $1" >&2; exit 2;;
    esac
    shift
done
SI=(); [ "$STANDIN" = 1 ] && SI=(--standin)
if [ -z "$LOGDIR" ]; then
    LOGDIR=outputs/_launch_format_control/dryrun_eval5
    [ "$STANDIN" = 1 ] && LOGDIR=outputs/_launch_format_control/dryrun_eval5_standin
fi
LOG=$LOGDIR/${FAMILY}_${GROUP}.log
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

# 1. Outside --dry, every refusal before anything else (the dry-run takes minutes).
if [ "$DRY" = 0 ]; then
    "$PY" "$E5" check "$FAMILY" "$GROUP" "${SI[@]}" "${CFG[@]}" "${PATHS[@]}" || exit 3
fi

# 2. The command (refuses when F is null and this is not a stand-in).
ARGS_TXT=$("$PY" "$E5" args "$FAMILY" "$GROUP" "${SI[@]}" "${CFG[@]}") || exit 3
mapfile -t ARGS <<< "$ARGS_TXT"
[ "$STANDIN" = 1 ] && echo "STAND-IN: F := H (plumbing only; never submitted)"
echo "command: python $EVALUATOR ${ARGS[*]}"

# 3. The login-node dry-run of exactly these arguments.
mkdir -p "$LOGDIR"
echo "# $(date +%Y-%m-%dT%H:%M:%S)  python $EVALUATOR ${ARGS[*]} --dry-run" > "$LOG"
if ! "$PY" "$EVALUATOR" "${ARGS[@]}" --dry-run >> "$LOG" 2>&1; then
    echo "DRY-RUN FAILED: see $LOG"; tail -3 "$LOG"; exit 5
fi
grep -E "^ +TOTAL .*min" "$LOG" | tail -1 || true
"$PY" "$E5" cost "$LOG" --family "$FAMILY" --group "$GROUP"
echo "dry-run log: $LOG"

TIME_ARG=(); [ -n "$TIME" ] && TIME_ARG=(--time "$TIME")
SB_TXT=$("$PY" "$E5" sbatch "$FAMILY" "$GROUP" --log "$LOG" --account "$ACCOUNT" \
         --partition "$PARTITION" "${TIME_ARG[@]}" "${SI[@]}" "${CFG[@]}") || exit 5
mapfile -t SB <<< "$SB_TXT"

# 4. --dry: print the submit line only if F is configured and the gate passes.
if [ "$DRY" = 1 ]; then
    if REFUSED=$("$PY" "$E5" check "$FAMILY" "$GROUP" --dry "${SI[@]}" "${CFG[@]}" "${PATHS[@]}"); then
        echo "dry run OK; submit line (needs FORMAT_CONTROL_EVAL5_GO=1 and the script without --dry):"
        echo "  ${SB[*]}"
    else
        echo "dry run OK; no submit line:"
        echo "$REFUSED" | sed 's/^/  /'
    fi
    exit 0
fi

# 5. Every refusal cleared: submit, and record the job id.
OUT=$("${SB[@]}")
echo "$OUT"
JID=$(echo "$OUT" | awk '/Submitted batch job/ {print $NF}')
mkdir -p "$(dirname "$JOBS")"
echo "$(date +%Y-%m-%dT%H:%M:%S) $FAMILY $GROUP $ACCOUNT $PARTITION ${JID:-?} ${ARGS[*]}" >> "$JOBS"
