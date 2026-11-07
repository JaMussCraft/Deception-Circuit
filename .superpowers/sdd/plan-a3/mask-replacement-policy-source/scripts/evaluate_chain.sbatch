#!/bin/bash
# Several evaluate_circuit.py runs in one Slurm job, one after the other.
# Submit from the repo root; groups of evaluate_circuit.py arguments are separated by ':::':
#
#   sbatch scripts/evaluate_chain.sbatch \
#       --circuit D=<run> ... --ablation mean --suite-name x__mean --output-dir <dir_mean> ::: \
#       --circuit D=<run> ... --ablation zero --suite-name x__zero --output-dir <dir_zero>
#
# Why: evaluate_circuit.py takes one --ablation per process, but a job pays the model load only once
# cold. The later groups load from the node's warm page cache (0.4 min on a Bridges-2 H100 against 10.5
# cold). Each group runs through scripts/evaluate_circuit.sbatch, so the cluster profile (DC_CLUSTER,
# DC_ACTIVATE, HF_HOME, the offline flags) acts exactly as it does for a single run.
#
# Every group runs even when an earlier one fails (the groups write separate output dirs); the job exits
# with the first non-zero status. Give every group its own --output-dir and --suite-name.
#
#SBATCH --job-name=eval-chain
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/evaluate_chain_%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"

usage() {
    echo "usage: sbatch scripts/evaluate_chain.sbatch ARGS... [::: ARGS...]..." >&2
    echo "       every ':::'-separated group is one evaluate_circuit.py run; no group may be empty" >&2
    exit 2
}

# Split "$@" on ':::' into groups, kept as NUL-joined strings so arguments with spaces survive.
groups=()
current=()
n_current=0
for arg in "$@"; do
    if [ "$arg" = ":::" ]; then
        [ "$n_current" -gt 0 ] || usage
        groups+=("$(printf '%s\0' "${current[@]}" | base64 -w0)")
        current=(); n_current=0
    else
        current+=("$arg"); n_current=$((n_current + 1))
    fi
done
[ "$n_current" -gt 0 ] || usage
groups+=("$(printf '%s\0' "${current[@]}" | base64 -w0)")

status=0
i=0
for g in "${groups[@]}"; do
    i=$((i + 1))
    args=()
    while IFS= read -r -d '' a; do args+=("$a"); done < <(printf '%s' "$g" | base64 -d)
    echo "=== evaluate_chain: group $i of ${#groups[@]} starts $(date '+%F %T')"
    rc=0
    bash scripts/evaluate_circuit.sbatch "${args[@]}" || rc=$?
    echo "=== evaluate_chain: group $i of ${#groups[@]} exited $rc $(date '+%F %T')"
    if [ "$rc" -ne 0 ] && [ "$status" -eq 0 ]; then status=$rc; fi
done
exit "$status"
