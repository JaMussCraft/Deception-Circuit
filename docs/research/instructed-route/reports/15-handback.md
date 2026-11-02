# Hand-back 15: B2 ticket T6, the falsity-probe capture entrypoint

Agent: ticket implementer (Opus). Ticket: `docs/research/instructed-route/plans/B2-plan.md` section 6, T6. Status: resolved.

## What changed

All four files are new. The orchestrator commits them from the worktree. Nothing is staged for the apply tool.

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/falsity_probe_capture.py`. This is the capture entrypoint, `--plan PLAN --output-dir DIR [--dry-run] [--max-rows N] [--check-encoding] [--batch-size N] [--device D]`, plus `--write-plans DIR`. Its module docstring fixes the plan format, the condition and orientation table, and every output file field by field for T7.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_falsity_probe_capture.py`. It holds 25 tests. The fixture data, the fake tokenizer and the fake capture need no GPU. One test runs the real `hooks`/`dla` capture on a tiny Llama under nnsight 0.7.0 only.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B2-p1-plan.json`. This is the real P1 plan: 18 cells, the split table of plan section 1. It was written by `--write-plans`, and a test asserts it equals the generator's output byte for byte.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B2-p1-smoke.json`. It is the same plan plus `"max_rows": 64`, which `--max-rows` overrides.
- This hand-back: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/15-handback.md`.

Design points T7 and T8 depend on:

- **Row order.** Line i of `rows.<cell>.jsonl` is row i of `resid.<cell>.pt` and `tokens.<cell>.pt`. Both `.pt` files carry the same `ids` list, so the join can be checked.
- **Token columns.** `tokens.pt` columns are fixed as column 0 the honest item and column 1 the deceptive item (`token_order`). The honest item comes from the condition: D, HI, I and I_reported use the record's distractor, and H and F use its target. Every row is checked against `clean_item_d` and `designation_polarity`. Under "inversion" the designated item is the honest one, and under "identity" it is the other item. This held on every v2 split I checked (700/700 per polarity on D, H and F, and on I and I-reported). So `clean_item_d` alone does not name the honest item, and the rule depends on polarity.
- **HI rows.** HI rows are D's records encoded from `honest_instruction_clean_prompt` with `dataloaders._encode`. The cell's target is the honest item. `dataset_margin` is `h_honest_instruction_clean`, which uses the same honest-minus-deceptive orientation. The Readout is `prefix_length - 1` and is asserted against the mask.
- **Encoding length.** Each cell is encoded at `max(dataset max_seq_length, longest prefix in the cell)`, so a longer HI prompt can never be truncated. On the real data every cell fits within 120, with a longest prefix of 106.
- **Margins in each row.** `model_margin` is the fp32 target minus distractor, and `model_honest_margin` is the fp32 honest minus deceptive. `dataset_margin` and `dataset_margin_field` name the dataset's own margin, and `clean_margin` is stored as the record gives it. Each row also carries `role`, `condition`, the clause (`pressure_id`, `pressure`), and the booleans `in_seed0_sample` and `in_seed1_sample`.
- **Exclusions.** Every id in an `exclude_id_files` file must be in the task's D test split, or the run fails. An `id_file` id missing from the split also fails the run.
- **Resumable runs.** A real run writes `done.<cell>.json` and skips completed cells on a rerun into the same directory. `capture_summary.json` records `margin_mean_abs_diff`, `dla_sum_max_abs_error` and `resid_nonfinite` for each cell. The first is the plan section 7 check, which requires D-cell margins within 0.05 of `clean_margin`. The last counts residual elements that overflow on the bfloat16-to-float16 cast (past 65504). The cell is kept and a warning is printed, so T7 decides what to do with them.
- **Manifest.** `run_manifest.json` is written before any model load, in dry runs too. It hashes the plan, every id file and every data file of every dataset directory read, and it records the argv, seed and model.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_falsity_probe_capture.py
```

Observed: `25 passed in 41.08s`, including the tiny-Llama test. In that test, the per-token DLA over every head, MLP and the embedding sums to the centred logit within 1e-4, and the residual shape follows `hooks.geometry`.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rs tests/test_falsity_probe_capture.py
```

Observed: `24 passed, 1 skipped`. The skip is the nnsight 0.7.0 test, because "nnsight 0.5.12 is installed".

The test run before the script existed failed at import (FileNotFoundError), which showed the tests were written first. I ran no other test files. This ticket touches no shared module, so I made no baseline comparison.

The login-node dry run used the real plan, with the real Llama tokenizer encoding every row. Git was disabled in the manifest because workers run no git.

```
DC_RUN_MANIFEST_GIT=0 /u/swong2/.conda/envs/mgnp/bin/python scripts/falsity_probe_capture.py --plan docs/research/instructed-route/jobs/B2-p1-plan.json --output-dir /u/swong2/.claude/jobs/230e4716/tmp/p1-dry --dry-run --check-encoding
```

Observed counts:

| cell | rows | | cell | rows |
| --- | --- | --- | --- | --- |
| far_fit_D | 200 | | ser_test_D | 800 |
| far_fit_H | 200 | | ser_test_H | 800 |
| far_select_D | 200 | | ser_test_HI | 783 (783/800 = 0.979 kept) |
| far_select_H | 200 | | ser_test_F | 800 |
| far_select_HI | 200 (200/200 kept) | | ser_test_I | 194 |
| far_gate_D | 800 | | sdr_test_D | 800 |
| far_gate_H | 800 | | sdr_test_H | 800 |
| far_gate_HI | 800 (800/800 kept) | | sdr_test_I_reported | 618 |
| far_gate_F | 800 | | | |
| far_gate_I | 177 | | **total** | **9,972** |

The total is 9,972, against the plan section 1 estimate of about 10,900. The cells follow the split table exactly. The difference is in the plan's arithmetic, not in the cells: 400 + 600 + 3,377 + 3,377 + 2,218 = 9,972. Both I cells lose their sample ids, FAR I 33 and SER I 55. SER HI keeps 783 of 800 rows. The training-split HI shares, which no cell uses, are FAR 199/200, SER 198/200 and SDR 173/200 (from a login-node count).

The encoding check passed on all 9,972 rows. Every answer is one token, every Readout equals the last unpadded position, and the longest prefix is 106 within the dataset's 120. The manifest recorded `model_revision` `0e9e39f249a16976918f6564b8830bc894c89659`, 120 hashed dataset files, seed 0, and `git_fingerprint_error: "disabled"`.

```
DC_RUN_MANIFEST_GIT=0 /u/swong2/.conda/envs/mgnp/bin/python scripts/falsity_probe_capture.py --plan docs/research/instructed-route/jobs/B2-p1-smoke.json --output-dir /u/swong2/.claude/jobs/230e4716/tmp/p1-smoke-dry --dry-run
```

Observed: 64 rows in each of the 18 cells, `total 1152`.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **No GPU capture has run.** The smoke and full runs belong to T8 and the P1 job. Three things are therefore not yet verified on the real model: the margin check (D within 0.05 of `clean_margin`), the 40-hex `git_commit`, and the real 8B shapes `[n, 33, 4096]` with 1,057 keys.
- **No Slurm wrapper was written.** `scripts/jobs/run_b2_capture.sbatch` is T8's.
- **The git fingerprint was not exercised here.** The login dry run set `DC_RUN_MANIFEST_GIT=0` because workers run no git. On the GPU job the default records the commit, with each git call bounded to 10 s.
- **Per-batch cost on the 8B model is unmeasured.** Each batch makes one traced forward over all 1,057 senders. `readout_logits` makes an fp32 copy of the unembedding (about 2 GB, transient), and `component_contributions` converts each head's `o_proj` slice to fp32. Batch size 8 should fit an A40 or H200, but this is untested. The smoke run should time it before the full run's `--time` is set.
- **The float16 overflow count is untested on the 8B model.** The smoke run's `capture_summary.json` should show `resid_nonfinite` 0 on every cell. If not, T7 or the orchestrator must decide whether to store the residual in bfloat16 instead.

## Open questions

1. **The 618 I-reported rows include 59 seed-0 ids and 57 seed-1 ids, the held-out sample.** Plan section 1 says "B1's held-out sample is never touched", while the split table and the ticket say "plus the 618". Default: capture all 618 as the ticket says. Every row carries `in_seed0_sample` and `in_seed1_sample`, so T7 can drop them. The SDR cell is descriptive and fits nothing.
2. **116 of the 618 I-reported ids have no H twin in the capture,** because `sdr_test_H` excludes both samples. Default: T7 contrasts I-reported against H on the 502 joined ids only. An extra H cell over those 116 ids would cost 116 forwards if the orchestrator wants the full set.
3. **The smoke plan keeps the first 64 rows of each cell in split order,** not a random draw. Default: keep this. The smoke run checks the plumbing, the margins and the timing, and nothing reads it as a sample.
4. **The plan section 1 total of about 10,900 does not match the 9,972 the split table yields.** Default: 9,972 stands, and T8's dry-run evidence should quote it.
