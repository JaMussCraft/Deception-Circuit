#!/bin/bash
# Submit the Format Circuit training runs (format-control ticket 03).
#
# usage (from anywhere; the script cds to the repo root and submits from there):
#   bash outputs/_launch_format_control/submit_train.sh --dry          # print the sbatch lines
#   bash outputs/_launch_format_control/submit_train.sh --test-only    # sbatch --test-only each line
#   bash outputs/_launch_format_control/submit_train.sh                # submit all three
#   bash outputs/_launch_format_control/submit_train.sh --only sdr_coarse --nls 0.4   # the one retune
# options: --account A  --partition P  --time T  (defaults below)
#
# Circuits (the nopressure condition of each mechanism task, paired run in brackets):
#   far         fine FAR NLS 0.3             [llama-8b-instruct_far/nls0.3_noedge_260819-083914]
#   sdr         fine SDR NLS 0.3             [llama-8b-instruct_sdr/nls0.3_noedge_260819-083414]
#   sdr_coarse  coarse heads-only SDR NLS 0.3
#               [llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742]
#
# Settings are the paired runs' config.json values, passed explicitly so each
# run's config.json records them: seed 42, 500 node epochs, lr 0.03, batch 7,
# max_seq_length 120, no edge pruning, train/val/test 200/200/1000 (the loader
# takes what exists: <task>_nopressure is 150/150/500 for FAR, 150/150/520 for SDR).
#
# --deception-margin-loss 0.7: the paired runs had deception_margin_loss null, so
# their hinge margin came from their dataset's margin_thresh, 0.7. The
# <task>_nopressure datasets were built at margin_thresh 0.3, which would become
# the Format Circuits' default margin. The orchestrator ruled (2026-10-13) to pin
# 0.7 so the training objective matches the paired run.
#
# The coarse run's slug and flags follow the coarse SDR wave
# (llama-8b-instruct_sdr_coarse/_launch/submit_train.sh); after it finishes run
# postprocess_coarse.sh <run_dir> before size_check.py.
#
# Job ids are appended to train_jobs.txt beside this script.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../.."                         # repo root (the worktree root)

MODE=submit
ONLY="far sdr sdr_coarse"
NLS=0.3
ACCOUNT=beto-delta-gpu
PARTITION=gpuA40x4,gpuA100x4,gpuA100x8,gpuH200x8
TIME=05:00:00
while [ $# -gt 0 ]; do
  case "$1" in
    --dry) MODE=dry ;;
    --test-only) MODE=test ;;
    --only) ONLY="$2"; shift ;;
    --nls) NLS="$2"; shift ;;
    --account) ACCOUNT="$2"; shift ;;
    --partition) PARTITION="$2"; shift ;;
    --time) TIME="$2"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

PAIRED="--deception-condition nopressure --no-edge-pruning --seed 42 --node-epochs 500
        --lr 0.03 --batch-size 7 --max-seq-length 120 --train-samples 200 --val-samples 200
        --test-samples 1000 --deception-margin-loss 0.7"
COARSE="--no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output --no-prune-mlp-blocks"
STAMP=$(date +%y%m%d-%H%M%S)
LOG="$HERE/train_jobs.txt"
[ "$MODE" = submit ] && mkdir -p logs   # Slurm opens logs/train_deception_%j.out before the job runs

for circuit in $ONLY; do
  case "$circuit" in
    far)        task=far; root=outputs/llama-8b-instruct_far;        slug=noedge;                     extra="" ;;
    sdr)        task=sdr; root=outputs/llama-8b-instruct_sdr;        slug=noedge;                     extra="" ;;
    sdr_coarse) task=sdr; root=outputs/llama-8b-instruct_sdr_coarse; slug=noedge_noan_nomh_nomo_nomb; extra="$COARSE" ;;
    *) echo "unknown circuit: $circuit (far, sdr, sdr_coarse)" >&2; exit 2 ;;
  esac
  out="$root/nls${NLS}_nopressure_${slug}_${STAMP}"
  cmd=(sbatch --account="$ACCOUNT" --partition="$PARTITION" --time="$TIME" --job-name="fc-${circuit}-${NLS}"
       scripts/train_deception.sbatch "$task" --node-lambda-sparsity "$NLS" $PAIRED $extra --output-dir "$out")
  case "$MODE" in
    dry)  echo "${cmd[*]}" ;;
    test) echo "${cmd[*]}"; "${cmd[0]}" --test-only "${cmd[@]:1}" 2>&1 | tail -1 ;;
    submit)
      jid=$("${cmd[@]}" | awk '{print $NF}')
      echo "$circuit $NLS $out $jid $ACCOUNT $PARTITION $(date +%FT%T)" | tee -a "$LOG" ;;
  esac
done
