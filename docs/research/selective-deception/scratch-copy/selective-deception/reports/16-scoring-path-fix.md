# Minimal Stage1 scoring-path correction

Released by root after report15 confirmed report10's first predeclared probe branch: allfour A100 prompts had B=C=E=B_repeat=C_repeat bitwise across the complete vocabulary; old S/C label logits reproduced exactly. The inherited single-stream intact path differed from the uncached dual-stream attention path. The numerical threshold remains0.02.

## Scoped change

Only these Stage1 worktree files changed:

- `evaluation/selective_runner.py`:no-donor scoring now supplies the same `ids` as `corrupted_input_ids`. Existing `ctx.all_gates_open()` remains the baseline context, so both intact recipient rows and intact donor diagnostics use an all-open dual stream. Rows with declared donors retain the identical donor tensors and mask context. This changes no shared model/gate implementation, score readout/labels, mask, generation behavior or threshold.
- `evaluate_selective_deception.py`:adds explicit provenance `scoring_baseline_path=dual_stream_self_donor_all_gates_open_uncached`.
- `tests/test_selective_runner.py`:two regression functions/four cases cover both recipient/donor-score no-donor routing and BF16 full-vocabulary identity at the observed113/116token lengths.

The production diff is two baseline-routing lines plus explanatory comment and one provenance field. Source/run fingerprints intentionally change; r1 results stay immutable. Root must commit and construct a new manifest/run identity while carrying forward the exact frozen r1 row/prompt/donor assignments. No outcome-driven sampling/filtering or mixing old and corrected output stores is introduced.

Forward row counts stay unchanged. Intact recipient and donor-score baselines now execute both streams, so their compute cost is higher than the inherited single-stream baseline; root should measure the fresh smoke. No new budget, retry or launch was authorized by this code change.

## Test-first verification

Before implementation, the required routing/identity regressions produced **4failed/24deselected in13.81s**. Both no-donor kinds lacked the identical corrupted input; BF16 tests also detected that intact and self-mask calls took different paths. CPU cross-path vector equality alone was deliberately not accepted as evidence of correct routing.

After implementation:

- **mgnp83passed in15.83s**.
- **base83passed in21.44s**, retaining3existing dependency warnings (bottleneck/pandas, TRANSFORMERS_CACHE and tensorflow/ml_dtypes).
- Scoped `git diff --check` passed.

The new tests capture actual forwards of tiny random CPU SDPA Llamas. Both recipient and donor-score no-donor forwards must receive identical clean/corrupted IDs, all gates open and use_cache=False. BF16 tests at113/116tokens capture the complete101-entry last-position vocabulary vector, require both forwards to use the same self-donor path, then require exact tensor and returned-metric equality under intact/all-open and heads-only core-like knockout. Existing nontrivial-donor and generation/resume/manifest contracts also pass.

Exact focused commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /u/swong2/.conda/envs/mgnp/bin/python -m pytest \
 tests/test_selective_runner.py tests/test_selective_diagnostics.py -q -p no:cacheprovider
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /sw/external/python/anaconda3/bin/python -m pytest \
 tests/test_selective_runner.py tests/test_selective_diagnostics.py -q -p no:cacheprovider
git diff --check -- evaluation/selective_runner.py evaluate_selective_deception.py tests/test_selective_runner.py
```

Evidence copied beside this report: `16-scoring-path-red.log`, `16-scoring-path-mgnp-green.log`, `16-scoring-path-base-green.log`.

## Frozen SHA256

| file | SHA256 |
|---|---|
| evaluation/selective_runner.py | `dc6e7cae3a774a6e3e2d62488c9cf6c18db00fea97da5cd8f226dd0ab0f84901` |
| evaluate_selective_deception.py | `083647cdfe17e7dc27fc99119c2b05231ce8d76d0ca285272b5626dec47a2c94` |
| tests/test_selective_runner.py | `f347d69378cb044c810cd387e3fb9c6589ca15956af84808ddf0675ef17e0653` |

No pretrained model loads, GPU/API execution, jobs, git writes, subagents, notebook execution, output/manifest edits, shared model/l0 changes or pilot-worktree changes. Only random tiny CPU models ran as explicitly required by the regressions. Root owns review, commit, fresh same-IDsmoke and all later launches. Implementation/report are frozen.
