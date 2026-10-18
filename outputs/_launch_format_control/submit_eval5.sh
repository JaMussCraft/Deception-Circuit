#!/bin/bash
# EVAL 5 for one format-control family and benchmark group: D, H and F (plus the
# family's eval5_extra_circuits, e.g. coarse D - F) bound in ONE evaluate_circuit.py
# invocation (one screen, one judge cache, identical settings; random rows
# size-matched per circuit). See README_eval5.md.
#
# usage: bash outputs/_launch_format_control/submit_eval5.sh <far|sdr|sdr_coarse> <sm|lb>
#            [--dry] [--standin] [--account A] [--partition P] [--time HH:MM:SS]
#            [--gate-override "reason"] [--allow-rescreen "reason"] [--log-dir DIR]
#   test / inspection only (with --dry, or with EVAL5_ALLOW_PATH_OVERRIDES=1):
#            [--config F] [--manifest F] [--suite-root D] [--record F] [--cache-src D] [--cache-dir D]
#
# Both modes first seed the worktree-local screen cache (A40 copies of the main
# checkout's screens; files, never links) and run `evaluate_circuit.py --dry-run`
# against it. Nothing is ever written into the main checkout.
#
# --dry      print the command, run the dry-run (log under dryrun_eval5/, the
#            cost appended to it), and print the sbatch line only if every
#            refusal below except the go-ahead is cleared. Never submits.
#            Exit 0 iff the dry-run passed.
# --standin  F := H while F is null (plumbing only, logs under
#            dryrun_eval5_standin/); never gets a submit line.
# (no --dry) submits ONLY when every refusal is cleared, in this order, each
#            naming its reason (exit 3; a failing dry-run exits 5):
#              F configured in suites.json;
#              the gate: F's knockout wikitext KL <= 0.66 on the D and F test
#                sets of ticket 04's suite, cells produced by the configured F
#                (only the KL bar yields to --gate-override "reason");
#              FORMAT_CONTROL_EVAL5_GO=1 (the researcher's explicit go-ahead);
#              a passing --dry-run of these exact arguments;
#              every screen an A40 cache hit on an A40 partition (yields only to
#                --allow-rescreen "reason").
# Every dry run and submission is appended to eval5_record.json with any
# override and its reason.
#
# --partition defaults to gpuA40x4 to keep the screened items item-for-item
# comparable with the existing eval5_* suites; other partitions re-screen.
set -euo pipefail
cd "$(dirname "$0")/../.."

PY=${PYTHON:-python}
EVALUATOR=${EVAL5_EVALUATOR:-evaluate_circuit.py}
E5=outputs/_launch_format_control/eval5_cmd.py

FAMILY=${1:?family: far|sdr|sdr_coarse}; GROUP=${2:?group: sm|lb}; shift 2
DRY=0; STANDIN=0; ACCOUNT=bgrb-delta-gpu; PARTITION=gpuA40x4; TIME=""; LOGDIR=""
GATE_OVR=(); RESCREEN=(); CFG=(); GATEPATHS=(); RECORD=(); SEED=(); CACHE=()
OVERRIDDEN_PATHS=()
while [ $# -gt 0 ]; do
    case $1 in
        --dry) DRY=1;;
        --standin) STANDIN=1;;
        --account) ACCOUNT=$2; shift;;
        --partition) PARTITION=$2; shift;;
        --time) TIME=$2; shift;;
        --log-dir) LOGDIR=$2; shift;;
        --gate-override) GATE_OVR=(--gate-override "$2"); shift;;
        --allow-rescreen) RESCREEN=(--allow-rescreen "$2"); shift;;
        --config) CFG=(--config "$2"); OVERRIDDEN_PATHS+=("$1"); shift;;
        --manifest|--suite-root) GATEPATHS+=("$1" "$2"); OVERRIDDEN_PATHS+=("$1"); shift;;
        --record) RECORD=(--record "$2"); OVERRIDDEN_PATHS+=("$1"); shift;;
        --cache-src) SEED=(--cache-src "$2"); OVERRIDDEN_PATHS+=("$1"); shift;;
        --cache-dir) CACHE=(--cache-dir "$2"); OVERRIDDEN_PATHS+=("$1"); shift;;
        *) echo "unknown argument: $1" >&2; exit 2;;
    esac
    shift
done
if [ "$DRY" = 0 ] && [ ${#OVERRIDDEN_PATHS[@]} -gt 0 ] && [ "${EVAL5_ALLOW_PATH_OVERRIDES:-}" != 1 ]; then
    echo "REFUSED: ${OVERRIDDEN_PATHS[*]} may only be overridden with --dry (they decide the gate and the cache)" >&2
    exit 2
fi
SI=(); [ "$STANDIN" = 1 ] && SI=(--standin)
if [ -z "$LOGDIR" ]; then
    LOGDIR=outputs/_launch_format_control/dryrun_eval5
    [ "$STANDIN" = 1 ] && LOGDIR=outputs/_launch_format_control/dryrun_eval5_standin
fi
LOG=$LOGDIR/${FAMILY}_${GROUP}.log
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

# 1. Outside --dry, every refusal known before the dry-run (it takes minutes).
if [ "$DRY" = 0 ]; then
    "$PY" "$E5" check "$FAMILY" "$GROUP" "${SI[@]}" "${CFG[@]}" "${GATEPATHS[@]}" \
        "${CACHE[@]}" "${GATE_OVR[@]}" || exit 3
fi

# 2. The command (refuses when F is null and this is not a stand-in).
ARGS_TXT=$("$PY" "$E5" args "$FAMILY" "$GROUP" "${SI[@]}" "${CFG[@]}" "${CACHE[@]}") || exit 3
mapfile -t ARGS <<< "$ARGS_TXT"
[ "$STANDIN" = 1 ] && echo "STAND-IN: F := H (plumbing only; never submitted)"
echo "command: python $EVALUATOR ${ARGS[*]}"

# 3. The worktree-local screen cache, then the login-node dry-run against it.
"$PY" "$E5" seed-cache "$GROUP" "${SEED[@]}" "${CACHE[@]}"
mkdir -p "$LOGDIR"
echo "# $(date +%Y-%m-%dT%H:%M:%S)  python $EVALUATOR ${ARGS[*]} --dry-run" > "$LOG"
if ! "$PY" "$EVALUATOR" "${ARGS[@]}" --dry-run >> "$LOG" 2>&1; then
    echo "DRY-RUN FAILED: see $LOG"; tail -3 "$LOG"; exit 5
fi
grep -E "^ +TOTAL .*min" "$LOG" | tail -1 || true
"$PY" "$E5" cost "$LOG" --family "$FAMILY" --group "$GROUP" "${CFG[@]}" | tee -a "$LOG"
echo "dry-run log: $LOG"

TIME_ARG=(); [ -n "$TIME" ] && TIME_ARG=(--time "$TIME")
SB_TXT=$("$PY" "$E5" sbatch "$FAMILY" "$GROUP" --log "$LOG" --account "$ACCOUNT" \
         --partition "$PARTITION" "${TIME_ARG[@]}" "${SI[@]}" "${CFG[@]}" "${CACHE[@]}") || exit 5
mapfile -t SB <<< "$SB_TXT"
REC=("$PY" "$E5" record "$FAMILY" "$GROUP" --log "$LOG" --account "$ACCOUNT" --partition "$PARTITION"
     "${SI[@]}" "${CFG[@]}" "${GATEPATHS[@]}" "${CACHE[@]}" "${GATE_OVR[@]}" "${RESCREEN[@]}" "${RECORD[@]}")

# 4. --dry: print the submit line only if every refusal but the go-ahead clears.
if [ "$DRY" = 1 ]; then
    OK=1
    CHECK=$("$PY" "$E5" check "$FAMILY" "$GROUP" --dry "${SI[@]}" "${CFG[@]}" "${GATEPATHS[@]}" \
            "${CACHE[@]}" "${GATE_OVR[@]}" 2>&1) || OK=0
    CACHE_CHECK=$("$PY" "$E5" cache-check "$LOG" "$GROUP" --partition "$PARTITION" \
                  "${CACHE[@]}" "${RESCREEN[@]}" 2>&1) || OK=0
    if [ "$OK" = 1 ]; then
        echo "dry run OK; submit line (needs FORMAT_CONTROL_EVAL5_GO=1 and the script without --dry):"
        echo "$CHECK" | sed 's/^/  /'
        echo "$CACHE_CHECK" | sed 's/^/  /'
        echo "  ${SB[*]}"
    else
        echo "dry run OK; no submit line:"
        echo "$CHECK" | sed 's/^/  /'
        echo "$CACHE_CHECK" | sed 's/^/  /'
    fi
    "${REC[@]}" --event dry
    exit 0
fi

# 5. The screens must be A40 cache hits (or a recorded --allow-rescreen).
"$PY" "$E5" cache-check "$LOG" "$GROUP" --partition "$PARTITION" "${CACHE[@]}" "${RESCREEN[@]}" || exit 3

# 6. Every refusal cleared: submit, and record the job id.
OUT=$("${SB[@]}")
echo "$OUT"
JID=$(echo "$OUT" | awk '/Submitted batch job/ {print $NF}')
"${REC[@]}" --event submit --job-id "${JID:-unknown}"
