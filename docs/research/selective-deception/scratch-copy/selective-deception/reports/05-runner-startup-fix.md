# Scoped Slurm environment startup correction

Frozen fix for the root-diagnosed smoke22994018 startup failure. No GPU/API/model execution, jobs, downloads, notebooks, git writes or subagents. Only `scripts/selective_deception.sbatch` and one parameterized regression in `tests/test_selective_runner.py` changed. Other work, including `blind_packets` outside this worktree, was untouched.

Root CPU reproduction established that standalone `source ~/.bashrc` under `set -e` exits silently on an incidental rc failure before reaching Python. Existing component-analysis wrapper uses an AND-list that permits rc initialization to finish. The corrected wrapper is:

```bash
set +u
source ~/.bashrc && conda activate mgnp || {
    echo "Environment initialization failed" >&2
    exit 1
}
set -u
```

One regression copies the real wrapper into a temporary directory and substitutes only its rc-source path and final Python entry. The fixture rc starts with `false`, then defines a conda stub. Successful activation must reach the probe with the original arguments; true activation failure must exit nonzero with the diagnostic and never reach the probe. No HOME or other common environment variable is repurposed, no real user rc is sourced, and no real conda/model entry is executed by the test.

TDD RED before the wrapper change: **2failed in22.82s**, proving both silent early exit and missing failure diagnostic. GREEN after the small fix: **mgnp2passed in11.31s; base2passed in27.57s**. Base retained the same3dependency warnings (bottleneck/pandas, TRANSFORMERS_CACHE deprecation, tensorflow/ml_dtypes deprecation). `bash -n` and scoped `git diff --check` passed. Root's already-completed full-suite baseline comparison was not repeated.

Exact focused commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /u/swong2/.conda/envs/mgnp/bin/python -m pytest \
 tests/test_selective_runner.py::test_slurm_startup_tolerates_rc_failure_but_requires_activation \
 -q -p no:cacheprovider
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /sw/external/python/anaconda3/bin/python -m pytest \
 tests/test_selective_runner.py::test_slurm_startup_tolerates_rc_failure_but_requires_activation \
 -q -p no:cacheprovider
bash -n scripts/selective_deception.sbatch
git diff --check -- scripts/selective_deception.sbatch tests/test_selective_runner.py
```

SHA256:

- Previous wrapper: `d55c6d37538c4d5df1fde090f950002b502eaf91943fe40cea9e79b95de7b904`.
- Frozen corrected `scripts/selective_deception.sbatch`: `68c131c3346785aeb267678e1a2bac717a0ee311fdd98b1a62255a614840906f`.
- Frozen `tests/test_selective_runner.py`: `20d3f94552150e09ec7ada69c61b7bd62dd6d4927179a1f2645333869eceb889`.

Evidence logs: `05-runner-startup-red.log`, `05-runner-startup-mgnp-green.log`, `05-runner-startup-base-green.log`, beside this report. Root owns scoped review/commit and preparing a new production manifest; old source fingerprints intentionally do not match this wrapper correction. No model outputs existed for the failed startup run. Implementation is frozen; no further edits planned.
