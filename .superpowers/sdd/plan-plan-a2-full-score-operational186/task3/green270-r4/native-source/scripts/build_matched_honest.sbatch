#!/bin/bash
# Filter a deception split to the Honest-Instruction Counterfactual: keep the
# instances where the model deceives under its Pressure Clause and answers
# honestly under that clause's Matched Honest Instruction.
#
#   sbatch scripts/build_matched_honest.sbatch --task sdr
#   sbatch scripts/build_matched_honest.sbatch --task sdr --honest-streams both
#
# The honest criterion defaults to the clean stream; --honest-streams both is
# the strict two-sided reading. Both id lists are written either way.
#
# Every extra argument goes to dataset/build_matched_honest.py.
#
# DRAFT AND CHECK THE POOL ON THE LOGIN NODE FIRST. It needs the tokenizer only:
#
#   python dataset/build_matched_honest.py --task sdr --write-pool --no-model
#
# That drafts the pool and asserts the clause-span alignment on every instance
# of the split, so an unmatched clause costs nothing here.
#
# --time is sized for one 1000-instance split: four forward passes per instance
# (pressure clean, pressure corrupt, honest clean, honest corrupt) at 128 tokens
# is a few minutes on an A40 once the 8B model is resident, and the load itself
# dominates. One hour is generous.
#
#SBATCH --job-name=matched-honest
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/build_matched_honest_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

set +u
source ~/.bashrc && conda activate mgnp
set -u

python dataset/build_matched_honest.py "$@"
