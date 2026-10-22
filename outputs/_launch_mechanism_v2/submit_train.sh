#!/bin/bash
# Submit the v2 mechanism circuit training runs (mechanism-datasets ticket 05).
#
# usage (from anywhere; the script cds to the worktree root and submits from there):
#   bash outputs/_launch_mechanism_v2/submit_train.sh --dry          # print all 12 sbatch lines
#   bash outputs/_launch_mechanism_v2/submit_train.sh --plan         # print the run names a submit would use
#   bash outputs/_launch_mechanism_v2/submit_train.sh --test-only    # sbatch --test-only each selected line
#   bash outputs/_launch_mechanism_v2/submit_train.sh                # submit the 6 coarse runs
#   bash outputs/_launch_mechanism_v2/submit_train.sh --only far_v2_D_coarse
# options: --account A  --partition P  --time T  --only "<run> [<run> ...]"  --include-fine
#
# Runs (12 = 3 v2 tasks x {D deceptive, H honest} x {coarse heads-only, fine}):
#   <task>_D_coarse  <task>_H_coarse  <task>_D_fine  <task>_H_fine   for task in far_v2 sdr_v2 ser_v2
#
# SCOPE RULING G12 (user, 2026-10-21): only the 6 coarse runs are approved. --dry prints all 12
# lines so the fine ones can be reviewed for a later go, but --plan / --test-only / submit select
# the coarse runs only. A fine run is selected (and accepted in --only) only with --include-fine.
#
# Settings match the references (main checkout), passed explicitly so each config.json records them:
#   coarse: outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/config.coarse.json
#           (NOT its config.json, which mask expansion rewrote; spec 14.C2)
#   fine:   outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414/config.json
# seed 42, 500 node epochs, lr 0.03, batch 7, max_seq_length 120, no edge pruning,
# train/val/test 200/200/1000, node lambda sparsity 0.3.
#
# --deception-margin-loss 0.7 is deliberate: both references record deception_margin_loss null
# (their hinge came from the v1 dataset's margin_thresh 0.7). The v2 D datasets are built at margin
# 0.7 and the H twins at 0.3, so without the pin D and H would train on different hinges (spec 9,
# 14.C2; same ruling as outputs/_launch_format_control/submit_train.sh, 2026-10-13).
#
# Coarse runs: the four coarse flags and an explicit output dir
#   outputs/llama-8b-instruct_<task>_coarse/nls0.3[_honest]_noedge_noan_nomh_nomo_nomb_<stamp>
# After a coarse run finishes, run outputs/_launch_format_control/postprocess_coarse.sh <run_dir>
# (backup + mask expansion only). Never the SDR wave's _launch/postprocess.sh (it submits evaluations).
# Fine runs pass no --output-dir: train.py's default slug, outputs/llama-8b-instruct_<task>/nls0.3[_honest]_noedge_<stamp>.
#
# Partitions: gpuH200x8 (default, --time 01:30:00) or gpuA40x4 (fallback, --time 03:00:00). One
# partition per submission, so a single --time fits the card it lands on. Never an A100 partition:
# node pruning on the 8B model needs about 40 GB and the A100 cards have 39.49 GiB.
# gpuH200x8-interactive (--time 01:00:00, its cap) was authorized by the lead for ticket 05 on
# 2026-10-21, when the regular queues projected starts weeks away. A coarse run takes about 33 min on
# an H200. The partition allows one job per user, so it takes exactly one run per submission (--only).
# gpuH200x8,gpuA40x4 (default --time 03:00:00, long enough for the slower A40) is the widened pair the
# lead and user set on 2026-10-21 for the backup jobs; Slurm starts the job on whichever frees first.
#
# Every submission is appended to train_jobs.txt beside this script.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../.."                         # repo root (the worktree root)

TASKS="far_v2 sdr_v2 ser_v2"
ALL_RUNS=""
for t in $TASKS; do ALL_RUNS="$ALL_RUNS ${t}_D_coarse ${t}_H_coarse"; done
for t in $TASKS; do ALL_RUNS="$ALL_RUNS ${t}_D_fine ${t}_H_fine"; done

MODE=submit
ONLY=""
INCLUDE_FINE=0
ACCOUNT=beto-delta-gpu
PARTITION=gpuH200x8
TIME=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry) MODE=dry ;;
    --plan) MODE=plan ;;
    --test-only) MODE=test ;;
    --only) ONLY="$2"; shift ;;
    --include-fine) INCLUDE_FINE=1 ;;
    --account) ACCOUNT="$2"; shift ;;
    --partition) PARTITION="$2"; shift ;;
    --time) TIME="$2"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

case "$PARTITION" in
  gpuH200x8) DEFAULT_TIME=01:30:00 ;;
  gpuA40x4)  DEFAULT_TIME=03:00:00 ;;
  gpuH200x8-interactive) DEFAULT_TIME=01:00:00 ;;
  gpuH200x8,gpuA40x4|gpuA40x4,gpuH200x8) DEFAULT_TIME=03:00:00 ;;
  *) echo "refusing --partition '$PARTITION': choose one of gpuH200x8 gpuA40x4 gpuH200x8-interactive gpuH200x8,gpuA40x4" \
          "(node pruning needs about 40 GB; the A100 cards have 39.49 GiB)" >&2
     exit 2 ;;
esac
TIME=${TIME:-$DEFAULT_TIME}
case "$PARTITION" in
  *gpuA40x4*)
    [ "${TIME//:/}" -ge 030000 ] 2>/dev/null || { echo "refusing --time $TIME with gpuA40x4: an A40 run needs 03:00:00" >&2; exit 2; } ;;
esac
if [ "$PARTITION" = gpuH200x8-interactive ]; then
  [ "$TIME" = 01:00:00 ] || { echo "refusing --time $TIME on gpuH200x8-interactive: its cap is 01:00:00" >&2; exit 2; }
  if [ "$MODE" != dry ] && [ "$(echo $ONLY | wc -w)" != 1 ]; then
    echo "refusing gpuH200x8-interactive without exactly one --only run (one job per user per partition)" >&2; exit 2
  fi
fi

# Selection: --dry shows all 12 unless --only narrows it; everything else defaults to coarse only.
if [ -n "$ONLY" ]; then
  SELECTED="$ONLY"
elif [ "$MODE" = dry ] || [ "$INCLUDE_FINE" = 1 ]; then
  SELECTED="$ALL_RUNS"
else
  SELECTED=""
  for r in $ALL_RUNS; do case "$r" in *_coarse) SELECTED="$SELECTED $r" ;; esac; done
fi
for r in $SELECTED; do
  case " $ALL_RUNS " in
    *" $r "*) ;;
    *) echo "unknown run: $r (choose from:$ALL_RUNS)" >&2; exit 2 ;;
  esac
  case "$r" in
    *_fine)
      if [ "$MODE" != dry ] && [ "$INCLUDE_FINE" != 1 ]; then
        echo "refusing $r: fine runs are deferred (scope ruling G12); pass --include-fine only after the user's go" >&2
        exit 2
      fi ;;
  esac
done

if [ "$MODE" = plan ]; then
  echo $SELECTED
  exit 0
fi

# Fragmentation headroom suggested by the earlier OOM message; the sbatch wrapper's
# environment passes through with --export=ALL.
EXPORT=ALL,PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
COMMON="--node-lambda-sparsity 0.3 --no-edge-pruning --seed 42 --node-epochs 500 --lr 0.03
        --batch-size 7 --max-seq-length 120 --train-samples 200 --val-samples 200
        --test-samples 1000 --deception-margin-loss 0.7"
COARSE="--no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output --no-prune-mlp-blocks"
STAMP=$(date +%y%m%d-%H%M%S)
LOG="$HERE/train_jobs.txt"
[ "$MODE" = submit ] && mkdir -p logs   # Slurm opens logs/train_deception_%j.out before the job runs

for r in $SELECTED; do
  task=${r%_[DH]_*}
  rest=${r#"${task}"_}
  case "$rest" in
    D_*) cond=deceptive; ctag="" ;;
    H_*) cond=honest;    ctag="_honest" ;;
  esac
  case "$rest" in
    *_coarse) extra="$COARSE --output-dir outputs/llama-8b-instruct_${task}_coarse/nls0.3${ctag}_noedge_noan_nomh_nomo_nomb_${STAMP}"
              out="outputs/llama-8b-instruct_${task}_coarse/nls0.3${ctag}_noedge_noan_nomh_nomo_nomb_${STAMP}" ;;
    *_fine)   extra=""
              out="outputs/llama-8b-instruct_${task}/nls0.3${ctag}_noedge_<stamp-at-start>" ;;
  esac
  cmd=(sbatch --account="$ACCOUNT" --partition="$PARTITION" --time="$TIME" --export="$EXPORT" --job-name="mv2-${r}"
       scripts/train_deception.sbatch "$task" --deception-condition "$cond" $COMMON $extra)
  case "$MODE" in
    dry)  echo "${cmd[*]}" ;;
    test) echo "${cmd[*]}"; "${cmd[0]}" --test-only "${cmd[@]:1}" 2>&1 | tail -1 ;;
    submit)
      jid=$("${cmd[@]}" | awk '{print $NF}')
      echo "$r $task $cond $out $jid $ACCOUNT $PARTITION $TIME $(date +%FT%T)" | tee -a "$LOG" ;;
  esac
done
