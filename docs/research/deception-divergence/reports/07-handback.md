# Hand-back 07: D2 premise plan and two-turn build

Agent: Opus worker (claude-opus-5-5), direction deception-divergence. Ticket: the lead's message of Mon 2 Nov 2026,
"D2 plan and two-turn premise build". Status: resolved for the plan, the code, the tests and the CPU dry runs; the
GPU job, the judge and the spec.md rulings are the orchestrator's.

## What changed

Committed by the orchestrator from the worktree
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`:

- `docs/research/deception-divergence/plans/D2-plan.md`: the D2 premise plan, with the rulings to record (section 9).
- `docs/research/deception-divergence/reports/07-handback.md`: this file.
- `docs/research/deception-divergence/results/d2/`: the dry-run `build_summary.json` and one `build_report.json`
  per task, copied from the ignored output directory.
- `scripts/d2_rows.py`: the two-turn row builder (forced answer, second user turn, segment spans, prefix/suffix
  split, condition loader with the target asserts).
- `scripts/d2_premise.py`: stages `inputs`, `build --dry-run`, `features`, `direction`, `generate`, `read` and
  `judge`.
- `scripts/jobs/run_d2_premise.sh`: the Slurm wrapper for Delta and Bridges-2, with `--dry-run`.
- `spontaneous/d2_judge.py`, `spontaneous/grader/d2_judge_prompt.txt`, `spontaneous/grader/d2_judge_config.json`:
  the D2 judge, whose three files make freeze G-D2. `spontaneous/judge.py` (B3 freeze G1) is untouched.
- `data/d2/d2_inputs.json`: the derived inputs (sha256 `a91cb15b846a815b631986957fecdf9b03ef705a1dc6f6bd826e3d5637932451`):
  the 48 Pacchiardi questions with their indices and groups, 128 + 32 AdvBench and 128 + 32 Alpaca prompts, seeds and
  the sha256 of every source file.
- `tests/test_d2_rows.py` (8 tests) and `tests/test_d2_premise.py` (24 tests).
- `.gitignore`: one line, `data/d2/_downloads/`, beside the existing `data/b3/_downloads/`.

Not committed: the raw downloads in `data/d2/_downloads/` (`pacchiardi_probes/`, `advbench/`, `alpaca/`, each its
own directory, read with `python -I` only). Nothing is staged for the apply tool.

## How verified

Source files, read as data:

| file | sha256 |
|---|---|
| `probes.csv` (`LoryPack/LLM-LieDetector`, 65 questions) | `21cb2b84bb941131beda9c3d272842137f8128bcb3a76f63e019a55318296710` |
| `lie_indices.npy` (24) | `9f40f628791220aa1e97439b106c50f3eec5879f26555460e3d7d7e91c9ed96a` |
| `no_lie_indices.npy` (14) | `bbd8ace69967cea7a2db0f24f3a58881423973905dbd88ccfc3e1192909c4172` |
| `knowable_indices.npy` (10) | `4b11ea884941e5dfa215d4e8cccfc8cbf1cd2942b3f87e62245e5479d701a361` |
| `harmful_behaviors.csv` (AdvBench, 520 rows) | `6cd1a5c63c07610d7eb67307772ee5606017ee950b5770ab288a2c487489d3e1` |
| `alpaca_data.json` (52,002 rows, 31,323 with no input) | `2eddafc6b977608d778aaab8dfc7e50e547b3af9826dfb9e909d9fc362e4a419` |

The repository README says the paper's 48 elicitation questions are the union of the three group files; the union
has exactly 48 distinct indices, so no question was written by us.

```
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d2_rows.py tests/test_d2_premise.py
```

Observed: 32 passed (mgnp, transformers 5.13.0).

```
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_d2_rows.py tests/test_d2_premise.py
```

Observed: 32 passed (base, transformers 4.57.3; the logistic regression also matches scikit-learn 1.3.0 here).

What the tests cover: the four-turn text is byte-identical to `render_messages` on the real tokenizer; every segment
decodes to its text and the prefix/suffix split is a token boundary; a mid-token span is refused; the forced item
is D's target in D, I and H (the honest twin's own target is the true item); the cached second-turn logits equal
independent unpadded forwards on a tiny Llama with the real vocabulary (within 1e-4); directional ablation leaves
every residual orthogonal to the direction; activation addition at layer 0 equals an embedding shift; the
end-to-end GPU stages and the read stage run on the tiny model; the logistic regression reaches the L2 optimum;
AUROC with ties, the clustered bootstrap, the 15-point rule, the "explains" rule, the R2 reading, the acts-on-it
rates, the proxy calibration and agreement on synthetic rows; the judge request carries no clause, condition or
task; the judge config is canonical and the freeze hash reproduces by the shell recipe; the judge stage samples and
its dry run counts requests; the wrapper parses and refuses a foreign working directory.

```
/u/swong2/.conda/envs/mgnp/bin/python -m spontaneous.d2_judge --print-hash
```

Observed: `1e41b6b92a0d0c92c68c790c9c220cf1f866fae7b30ed3a1d4c7e0fabcf50215`, equal to the `sha256sum | awk | sort |
sha256sum` recipe in the module docstring.

```
/u/swong2/.local/bin/research-session lint docs/research/deception-divergence/plans/D2-plan.md docs/research/deception-divergence/reports/07-handback.md
```

Observed: no findings.

## Execution evidence

CPU dry runs only; no GPU job, no judge call and no paid call were made.

- Local command, mgnp through the wrapper on the Delta login node: `bash scripts/jobs/run_d2_premise.sh --dry-run`,
  exit code 0. Base Python 3.9: `python3.9 scripts/d2_premise.py build --dry-run --out-root <tmp>`, exit code 0
  (run without `-I`, because `-I` drops the user site where the base transformers lives).
- Row counts, identical on both interpreters:

| task | fit ids (D, H) | gate ids (D, H) | test ids with I (used / available) | unablated rows | ablated rows | generations | D-H and D-I aligned |
|---|---|---|---|---|---|---|---|
| far_v2 | 200 | 200 | 210 / 210 | 1,430 | 1,030 | 1,460 | 210, 210 |
| sdr_v2 | 200 | 200 | 250 / 788 | 1,550 | 1,150 | 1,700 | 250, 250 |
| ser_v2 | 200 | 200 | 249 / 249 | 1,547 | 1,147 | 1,694 | 249, 249 |

  Totals: 4,527 unablated and 3,327 ablated rows, 384,846 second-turn sequences (49 per row), 4,854 generations
  (2,127 unablated test, 2,127 ablated test, 600 calibration). The longest acts-on-it row is 136 tokens (SER); FAR 127, SDR 135. The reports are equal key for key on both
  interpreters except the CPU seconds.
  All 320 refusal prompts end in the five post-instruction tokens. YES ids 7566, 9642, 9891, 10035, 14331; NO ids
  912, 2201, 2360, 2822, 9173; refusal id 40 ("I").
- Estimate: 1,835 s, 0.51 GPU-hours on one H100 (10.8M feature tokens, 15,708 feature forwards, 398 refusal
  forwards, 4,854 generations, 460 s load), from D1's measured throughput.
- Baseline reproduces: not applicable to a dry run; the GPU job compares the cached and full feature paths on 8
  rows per task and stops above 0.25 logits.
- Provenance file: none for a dry run; each GPU stage writes a manifest with DD_COMMIT, code hashes, the inputs
  hash and whether the samples are the pre-registered ones.

Nothing here is verified on the 8B model; that waits for the job.

## What is NOT done

- The spec.md rulings R7 to R13 and freeze G-D2 are for the orchestrator to record (plan section 9).
- The GPU job, the judge stages, the proxy token freeze and the verdict have not run.
- The full repository test suite was not run; only the two new test files ran, on both interpreters. No existing
  file other than `.gitignore` was edited.
- The patching payload (plan section 8) is planned only and needs its own ruling if the premise passes.
- No teacher-forced stem set was built for the first-token proxy, although the brief asked for one as
  instructed-route R4 did. The proxy is calibrated from the first generated token of the judged validation
  generations; an ambiguous opener such as "I" falls into neither list and its rows count as `undecided`. If such
  openers start more than a fifth of the calibration rows, a stem-resolved proxy needs a ruling before the proxy
  can be the patching readout (plan section 3b). The judge is the primary readout either way.
- The model tests use a tiny random Llama (2 layers, 64 hidden) with the real 128,256-token vocabulary instead of
  the vocab-101 model in `tests/helpers.py`, so that the real rows, the 48 questions and the real yes, no and
  refusal token ids run unchanged.
- Arditi pooled four harmful sources; only AdvBench is used. The refusal direction's validity is checked, not
  assumed.

## Open questions

- FAR and SER have no unused I ids after the premise (all 210 and 249 are in it), so a passing FAR or SER would
  need its patching ids from the premise ids or from fresh inversion rows. Default: reuse the premise ids and say
  so in the ruling.
- The first-answer full stop follows `deception_v2.demo_exchange`; the brief's wording had no full stop. Default:
  keep the full stop (it is the model's natural continuation of the requested format and defines the prior-answer
  span as item plus full stop plus `<|eot_id|>`).
- Should the D2 judge hash also go into `directions.json`? Default: spec.md only, as B3's hashes were.
