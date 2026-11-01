# Hand-back 17: B3 T4, the generation entrypoint

Agent: ticket implementer (Opus), impl-B3-t4. Ticket: `docs/research/instructed-route/plans/B3-plan.md` section 7,
T4. Status: resolved for the code and the login-node checks; the GPU path is not yet verified. No GPU run, no paid call, no git.

## What changed

Committed by the orchestrator from the worktree (all new files):

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/generate.py`: the
  pure helpers. It builds the contexts through `af_prompts.build_af_pair`, so every twin pair is checked for length
  and for a single differing tag token. It plans the jobs and computes the per-row seeds as 63 bits of sha256 over
  (seed, split, variant, control, query, condition, sample). It holds the per-row sampler, the left-padded
  `generate` call, the teacher-forced stem forwards, the margins, the sparse stem records, row assembly and the
  dry-run plan and walltime estimate.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/b3_generate.py`: the
  CLI, with the flags in the brief plus `--seed` and `--control-samples`. It writes `rows.jsonl` for the base prompt,
  `rows_c1.jsonl` and `rows_c2.jsonl` for the controls, `summary.json` and `run_manifest.json`. It refuses to
  overwrite an existing row file. `--dry-run` writes only `dry_run_plan.json`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/jobs/run_b3_generate.sh`:
  the wrapper, patterned on `run_sdr_cue_probe.sh`. It has the cwd guard for this worktree, mgnp (or `B3_PYTHON`),
  offline HF, BLAS threads set to 1 and `RESEARCH_DIRECTION=instructed-route`. It is executable.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_b3_generate.py`:
  18 tests on a tiny random Llama with a word-level fake tokenizer. One of them uses the real cached tokenizer.

Nothing is staged for the apply tool. The frozen G1 files were not touched.

**Design points the orchestrator should know.**

- **Per-row seeding.** HF `generate` runs in greedy mode (`do_sample=False`, so HF adds no warpers in 4.57 or 5.13).
  The last logits processor is a per-row sampler. For each sampled row it applies temperature, then HF's top-p rule,
  then draws from that row's own `torch.Generator`, and it returns scores that are finite only at the drawn token. A
  row's tokens therefore depend on its prompt and seed, not on its batch partners or position. bf16 batched-kernel
  rounding on a GPU is the one caveat. Greedy rows pass through unchanged.
- **Readout.** The Readout is the first generated position. `readout_index` equals `prompt_len`, and the prompt
  includes the V-B `<OUTPUT>\n` prefill.
- **Stems and margins.** The six stems come from `proxy.stem_id_paths`. They are run right-padded through the HF
  base model, and a forward pre-hook on the final norm captures the residual at the last unpadded position.
  `hooks.readout_logits` then gives fp32 logits, so the double normalization of `hidden_states[-1]` is avoided.
- **Greedy rows.** P1 and P2 margins are computed in-job on the full vectors and stored under `margins`, with
  `r1_basis` ("seed" while `r1` is null) and `proxy_tokens_sha256`. The stem records follow `rows.py`. The
  prompt-alone stem keeps the top 1,024 ids plus every id a proxy reads plus every first token seen in the run. The
  other stems keep the top 256 plus the needed ids.
- **Two phases.** Generation finishes before the stem pass, so the first-token set is complete. Sampled rows are
  appended as they are generated, and greedy rows are written after the stem pass.
- **The model's sampling defaults are kept out.** The real `generation_config.json` has `do_sample` true,
  temperature 0.6 and top-p 0.9. On transformers 4.5x, a config stamped 4.50 or later overrides default-valued
  fields, so the call passes explicit neutral values and `use_model_defaults=False` where `generate` accepts it. A
  test stamps the tiny model with those values and version 4.57.0 and shows that greedy and seeded rows are
  unchanged.
- **RoPE guard.** After loading, the script calls `evaluation.gen_engine.assert_rope_is_offset_invariant`. Llama-3.1's
  `llama3` RoPE passes it on the cached config, so left-padded batches equal their rows run alone.
- **Commit fallback.** `summary.json` records the manifest's commit and also HEAD read straight from the repository
  files without a subprocess (`head_commit_from_files`), in case Lustre makes the manifest's 10 s git call time out.
- **Row schema.** Rows conform to `spontaneous/rows.py`. At my request T5 added `control` to `make_row_id`, so ids
  are unique across controls. Extra fields: `control`, `tag_pos`, `prompt_len`, `readout_index`,
  `assistant_prefill`, `finish_reason`, `truncated`, `temperature`, `top_p` and, on greedy rows,
  `readout_argmax_id`. Every row passes `rows.validate_row` before it is written.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_b3_generate.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_b3_generate.py
```

Observed in the final state: "18 passed" on mgnp (transformers 5.13) and "18 passed" on base 3.9 (transformers
4.57.3). With `-rs` there were no skips, so the real-tokenizer prefill test ran.

The tests cover these claims:

- Per-row seeds reproduce the same tokens alone, in a mixed batch with a different prompt length, and in swapped
  order. Different seeds give different samples.
- Greedy rows follow the argmax path.
- Teacher-forced fp32 log-probs from right-padded batches equal a direct unpadded forward within 1e-5.
- The in-job margins equal `proxy.p1_margin` and `p2_margin`, and `rows.row_margins` on the sparse record
  reproduces them.
- The V-B prompt ends with the assistant header and then `<OUTPUT>\n`, and the Readout index is right after it.
  This was checked on the fake and on the real tokenizer.
- `--dry-run` with a loader that raises reports the counts and writes only `dry_run_plan.json`.
- A run writes rows that `rows.load_rows` accepts across the base and C1 files, and a `run_manifest.json` whose
  `git_commit` is 40-hex and whose hash verifies. A second run with another batch size gives identical rows.

The whole B3 suite on both interpreters:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_b3_generate.py tests/test_b3_proxy.py tests/test_b3_prompts.py tests/test_b3_premise.py tests/test_b3_judge.py
```

Observed: the first run gave 1 failure on base 3.9, mine, because T5 had added the control to `make_row_id`
mid-run. After I passed the control through, the whole set gave "180 passed" on mgnp and "180 passed" on base 3.9.
`rows.py` was last modified at 14:20 CST, before that rerun. The two later tests are in `tests/test_b3_generate.py`
alone, which gives 18 passed on both.

```
bash -n scripts/jobs/run_b3_generate.sh
```

Observed: exit 0.

Login-node dry runs through the real wrapper, with `B3_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python` and the cached
Llama-3.1-8B-Instruct tokenizer. Every twin pair passed the length and single-tag check. Outputs are in
`/u/swong2/.claude/jobs/230e4716/tmp/t4_dry/`.

```
scripts/jobs/run_b3_generate.sh --variant both --split calibration --controls base --batch-size 32 --out .../j1 --dry-run
```

Observed: V-A prompt tokens min 261, mean 268.1, max 290. V-B min 1040, mean 1047.0, max 1069. 80 contexts, 40 twin
pairs. 880 generations (800 sampled, 80 greedy) in 28 batches. 480 teacher-forced forwards. The estimate is 909 s,
or 0.25 h: load 476, prefill 48, decode 358, stems 26.

| Run (test split unless noted) | Contexts | Generations | Batches | Forwards | Estimate |
|---|---|---|---|---|---|
| V-A, base+c1+c2, control samples 10 | 600 | 6,600 | 207 | 3,600 | 3,355 s (0.93 h) |
| V-B, base+c1+c2, control samples 10 | 600 | 6,600 | 207 | 3,600 | 4,017 s (1.12 h) |
| V-B, base+c1+c2, control samples 0 | 600 | 2,600 | 82 | 3,600 | 2,068 s (0.57 h) |
| Calibration, both variants, base+c1+c2 | 240 | 2,640 | 83 | 1,440 | 1,762 s (0.49 h) |

The test-split V-A prompts were min 259, mean 269.1, max 284. V-B was min 1038, mean 1047.8, max 1063.

The estimate uses the constants of plan section 6 on an A100. Load is 476 s, the forward rate is 12,000 tokens/s
(15 forwards/s at 800 tokens), and a decode step at batch 32 is 25 ms. Every batch is charged the full 512 new
tokens, so the decode term is an upper bound.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **No GPU run.** The bf16 path, the `load_analysis_model` call on CUDA and the real decode speed are not yet
  verified. The first J1 run is the first assertion that they work.
- **Health check.** The plan's 5-call paid health check belongs to the judge (T5 and orchestrator approval), not
  this script, and was not run.
- **Estimate inputs.** The walltime constants are the plan's, not measured. The plan assumed V-A prompts of about 800
  tokens, but they measure about 268, so V-A prefill and stems cost about a third of the plan's figure.
- **Long-generation memory.** Memory at batch 32 with 1,050-token V-B prompts plus 512 new tokens is estimated
  (about 7 GB of KV cache) but not measured. Plan section 8 says to drop to batch 4 or move to an H200 on OOM.

## Open questions

- **Sampled control rows.** The brief asks for 10 sampled rows per control context. Plan 3.4 says C1 and C2 use
  greedy margins only, and the plan's J2 figure of 2,200 generations is base-only. `--control-samples` defaults to
  `--samples`, as the brief asks. That makes J2 about 1.1 h on V-B, against 0.57 h with `--control-samples 0`.
  Default: pass `--control-samples 0` for J2 unless the orchestrator wants judged control rows.
- **Wall-clock reserves.** Default reserves: J1 (calibration, both variants, base) `--time=00:45:00` on an A100,
  with an estimate of 0.25 h. J2 (test, one variant, base+c1+c2, `--control-samples 0`) `--time=01:00:00`. Use
  `--time=01:30:00` if the controls are sampled.
- **Margins on the greedy row only.** The stems are stored on the greedy row only, which `rows.py` allows. Default:
  keep it that way, since sampled rows share the context's stems.
