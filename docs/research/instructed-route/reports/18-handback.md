# Hand-back 18: B3 ticket T6, patching, nulls, bootstrap and the patch entrypoint

Agent: impl-B3-t6 (Opus). Ticket: `docs/research/instructed-route/plans/B3-plan.md` section 7, T6. Status: resolved;
the first GPU step (the parity check) has not run.

## What changed

Committed by the orchestrator from the worktree, all new files:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/stats.py`. It
  ports `layer_matched_nulls` and its constants from `p1c_groups.py`, and `mediated_fraction`, `instance_boot`,
  `f_boot` and `ci` from `p1c_results.py`, with the bodies unchanged. The docstring names both sources. It adds
  `heads_only_nulls`, which is the same draw over a set's heads only.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/patching.py`.
  - The twin interchange uses knockout's recipe: a clean capture, then a twin capture of every key any arm writes,
    then one capture per arm with `Replacement(twin value, positions=mask)`. Each run is read in fp32 through
    `readout_logits`.
  - Masks are `post_tag`, from the first differing token to the Readout inclusive, and `readout`.
  - `CompactProxy` reduces each run to the log-probs of the ids the proxy reads plus one rest-of-mass bucket. It then
    calls `proxy.p1_margin` and `proxy.p2_margin` on remapped ids, which is exact.
  - The C3 bullet margin uses the openers "-", "*", "•" and "1", each a single token.
  - `run_af` handles P1, and P2 as six stem sequences per twin. `run_syc` makes two passes: pass 1 classifies kept
    items and flips, and pass 2 patches the kept items.
  - The statistics are `f_summary` (a ratio of means with the ported bootstrap CI and per-item ratios),
    `gap_summary` (the paired CI on Δ), `flip_table`, `flip_reversal` and `syc_pass_bar`.
  - `transfer_verdict` applies the R5 bands as recorded in `spec.md`, the "non-specific" label when the null maximum
    is at least 0.5, the plan 3.4 qualifiers and the F-mech-003 caveat. `discovery()` is a stub that raises
    NotImplementedError.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/b3_patch.py`.
  - It accepts `--task {af,syc,c3}`, `--sets`, `--null`, `--positions` (a comma list), `--rows`, `--tokens`,
    `--proxy`, `--variant`, `--controls`, `--responsive`, `--out`, `--dry-run`, `--parity-check` and `--discovery`
    (refused).
  - It writes `margins.json`, `results.json` and `run_manifest.json`. `results.json` holds the f values with CIs,
    the null f values and maxima, the probability-scale f, the gap, the R5 verdict, f_C3 and the sycophancy pass bar.
  - Each set's null seed is `NULL_SEED + 1000 × its index in SET_ORDER`, so the seeds do not depend on the order of
    `--sets`.
  - A real af run refuses a token file whose R1 is uncalibrated, because freeze G2 is not yet recorded.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/jobs/run_b3_patch.sh`
  is the wrapper, executable. It has a cwd guard for this worktree, uses mgnp unless `B3_PATCH_PYTHON` is set, runs
  HF offline and sets the BLAS threads to 1.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_b3_patching.py`
  has 45 tests.

Nothing is staged.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_b3_patching.py tests/test_b3_proxy.py tests/test_b3_prompts.py tests/test_b3_judge.py
```

Observed: 149 passed. `tests/test_b3_patching.py` alone gives 45 passed.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_b3_patching.py tests/test_b3_proxy.py tests/test_b3_prompts.py tests/test_b3_judge.py
```

Observed: 141 passed and 8 skipped. The 8 skips are the tiny-model tests, which need nnsight 0.7.0.

The tests cover the following:

- The ported nulls equal the source draws for four seeds and five sets. The source is loaded from
  `outputs/_launch_mechanism_analysis` by file path.
- `instance_boot`, `f_boot` and `ci` equal the source for three seeds.
- f is 1 when the patched run equals the twin and 0 when it equals the clean run, and the CI is the ported bootstrap.
- The flip-reversal count is checked on a hand-built table.
- The pass bar passes at 0.18 and at 9/50, and fails just below 0.18, on a tied null and with no nulls.
- All six R5 bands, the non-specific label at 0.5 and just below, and the cue-following qualifiers are checked.
- The post-tag mask starts at the tag and stops at the Readout under padding.
- The compact P1, P2 and bullet margins equal the full-vocabulary margins.
- On the tiny Llama, the empty set reproduces the clean logits bit-identically (`torch.equal`).
- On the tiny Llama, all heads and MLPs give the twin margin within 1e-3 at both positions arms.
- The interchange equals a direct `capture_forward` replacement.
- The P2 clean margin equals six direct forwards.
- The af and syc runs complete end to end with a fake model and tokenizer.
- The manifest carries a 40-hex `git_commit`. The commit call is faked, because conftest disables it.
- `--dry-run` loads no model: `load_analysis_model` is patched to raise.

```
bash -n scripts/jobs/run_b3_patch.sh
```

Observed: no output, exit 0. Run from `/tmp`, the wrapper prints "Run from the explicitly approved worktree cwd."

Login-node dry runs used `B3_PATCH_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python scripts/jobs/run_b3_patch.sh ...
--dry-run --out <tmp>`. None loaded a model or wrote a file. Walltimes include 8 minutes of model load.

| Run | Pairs, tokens | Forwards | A100 | H100 |
|---|---|---|---|---|
| J3 `--task syc` (default sets gupta6, gupta_writers, L17H24, S_q, S_all; readout; 20 nulls) | 800 kept of 800 (0 dropped), mean 138 | at most 87,200 (pass 1 1,600) | 0.40 h | 0.27 h |
| J4 `--task af --variant V-B --proxy P2`, 6 sets, post_tag and readout | 100, mean 1,048 | 152,400 | 3.69 h | 1.91 h |
| same, post_tag only | 100, 1,048 | 76,800 | 1.92 h | 1.03 h |
| `--sets S_all,gupta6 --positions readout`, V-B P2 | 100, 1,048 | 26,400 | 0.75 h | 0.44 h |
| `--variant V-B --proxy P1`, 6 sets, post_tag | 100, 1,048 | 12,800 | 0.43 h | 0.28 h |
| `--variant V-A --proxy P2`, 6 sets, post_tag and readout | 100, mean 269 | 152,400 | 1.05 h | 0.59 h |
| `--task c3 --variant V-B` (S_all, post_tag) | 100, mean 977 | 2,300 | 0.18 h | 0.16 h |
| `--parity-check` | 10 FAR held-out ids, all twinned, 2 batches of length 120 | 20 batched | 0.13 h | 0.13 h |

The estimates assume about 100 forwards per second at 250 tokens on an H100 (plan section 6), scaled by prompt
length, with an A100 at half that rate. Per-trace nnsight overhead is not included. The parity dry run loaded the FAR
batches and segmentations and built both mask kinds on the login node.

`research-session lint` on this hand-back exits 0. `ruff check --line-length 120` passes on the script, `patching.py` and the test file. In `stats.py` it flags only E741
in the verbatim port, which stays unchanged.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **The parity check has not run.** It needs a GPU. It compares the two methods on 10 ids at knockout's post-clause
  positions and at the B3 post-tag positions against knockout's "all". It does not reproduce the 0.893 itself, which
  was computed on 100 ids.
- **Discovery (plan 3.5) is a stub.** `--discovery` exits with the NotImplementedError message.
- **The C1 and C2 qualifiers are not computed here.** They come from the generation run through `--controls`
  (`delta_c1`, `delta_c2`, `f_c3`). Without that file the verdict says "not computed".
- **The probability-scale f is reported, but the "responsive" subset depends on outside input.** It needs a JSON id
  list from T5's judged per-query gaps. No such file exists yet.
- **Kept and flip classification comes from pass 1.** The f values and reversals use pass-2 values on those items,
  from the same batches as the patched runs. A near-tie letter could classify differently under pass-2 batching.
- **The full V-B P2 transfer is over its reserve.** It estimates 3.69 h on an A100 with both position arms on all six
  sets, against the plan's 1.5 h J4 reserve.

## Open questions

- **Where does the primary proxy choice come from?** The brief said to use P1 or P2 "as the calibrated token file
  says", but `proxy_tokens.json` has no field for the choice, and `ProxyTokens.from_dict` rejects extra keys. So
  `--proxy` is required for af. Default: the orchestrator passes the R-B3-a choice on the command line, and
  `results.json` records it under `readout.proxy`.
- **How should J4 be split under the reserve?** Default: run all six sets at post_tag only, plus S_all and gupta6 at
  the readout arm. That is 1.92 h plus 0.75 h on an A100, or 1.03 h plus 0.44 h on an H200/H100, so use an H200.
  If P1 is primary, the full run is 0.43 h.
- **Should a prefix KV cache be added?** Positions before the tag are identical across the clean, twin and patched
  runs. On V-B the tag sits after the roughly 1,000-token system prompt, so reusing the prefix would cut J4 several
  times over. Doing so needs a `past_key_values` path in `component_analysis/hooks.py`, which this ticket does not
  own. Default: not added. The current costs fit the cap.
- **Is the C3 bullet opener list right?** It is "-", "*", "•" and "1". It is not a frozen grader file, and every C3
  result records it. Default: keep it. Freeze it with G2 if the orchestrator wants it hashed.
- **Is argmax over the four letter logits the right sycophancy readout?** Default: yes, as Gupta reads option-letter
  logits.
- **Is a strict comparison right for "beat all 20 draws"?** A tie fails. Default: strict.
- **Should the proposed R-B3-b replace R5?** Plan 3.3 proposed that "shared" also require beating all nulls. The code
  follows R5 as recorded in `spec.md` and reports `exceeds_all_nulls` beside it. Default: R5 as recorded.
