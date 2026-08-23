#!/bin/bash
# Build all three deception-mechanism datasets (FAR / SDR / SER) and their
# honest twins on a GPU node.  sbatch scripts/build_deception.sbatch
#
# DO NOT SUBMIT THIS BEFORE THE PILOT PASSES (scripts/pilot_deception.sbatch).
# At STD's ~2% pass rate a 200/200/1000 build is ~84k pairs per task, and each
# pair costs 3 forward passes (prior-balance, clean, corrupt) — ~250k per task,
# ~750k in total. Set --overgen-factor from the pilot's measured pass rate
# instead of leaving the default 60.
#
# --match-length-distribution is deliberately NOT used here: the shipped pools
# already put the three tasks' median prompt lengths within ~1 token of each
# other, and the flag discards instances on out-of-band pressure slots, which
# shrinks the three-way comparison set. Turn it on only if the pilot's length
# histograms say otherwise.
#
# The same --seed in all three builds is what makes the triplets matched; the
# honest twins are harvested in the same pass, so no second sweep is needed.
#
#SBATCH --job-name=build-ser-test
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=logs/build_ser_test%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

set +u
source ~/.bashrc && conda activate mgnp
set -u

SEED=${SEED:-42}
OVERGEN=${OVERGEN:-6}

for TASK in ser; do
  python dataset/build_deception_dataset.py \
    --task "$TASK" --seed "$SEED" --overgen-factor "$OVERGEN"
done

# The intersection is only complete once all three exist.
python dataset/deception_comparison_set.py
python dataset/deception_comparison_set.py --condition honest
