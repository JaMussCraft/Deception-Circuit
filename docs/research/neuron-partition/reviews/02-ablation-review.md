# Review 02: neuron set-ablation machinery (W2, commit e5962fe)

**Verdict: PASS WITH FIXES.** There are no blockers. Two majors must be fixed before the first ablation cell: the
IOI rows change from process to process, and `--ids` rejects W3's own test-sample file.

Reviewer: rev2 (independent; the W2 hand-back was not read). Scope: `component_analysis/hooks.py` (the `mlp_hidden`
kind), `component_analysis/knockout.py` (groups, fills, the mean bank, the twin path, `record_argmax`),
`scripts/neuron_set_ablation.py`, `tests/test_neuron_set_ablation.py` and `jobs/ablation_cells.sbatch`. Measured
against spec rulings R2, R3, R7, R8 and R9 and reader brief sections 2, 4 and 5. No git, GPU or Slurm was used.
"Main" below means the primary checkout's `component_analysis/` modules, which hold the code before this change.

## Findings

1. **Major: the IOI rows are not reproducible across processes.**
   - Evidence: `dataset/ioi_llama.py:86` returns `list(set(all_names))`. Set order for strings depends on
     `PYTHONHASHSEED`, so `random.sample(valid_names, 2)` draws different names even with `seed=1`. The same
     `ioi_rows(n=100, seed=1, pool=1000)` call gave different rows under two hash seeds:

     ```
     PYTHONHASHSEED 0 100 371fde1402292309 | Then, Simon and Coleman had a long argument. Afterwards Coleman said to Simon
     PYTHONHASHSEED 1 100 2683521c6f6465d9 | Then, Vanessa and Tommy had a long argument. Afterwards Tommy said to Vanessa
     ```

   - Consequence: inside one job, intact and ablated runs share their IOI rows, and so do a set and its nulls. So
     each recorded shift is valid on its own terms. Across jobs the rows differ, for example between the two R10
     halves, a rerun after a walltime kill, or the R4 check against 0.51. At n = 100 the sampling spread is about
     5 points, the size of the gate. `run_manifest.json` records `seed=1` as if that seed fixed the rows, and the
     summary keeps no sentence or hash of them.
   - Fix: add `export PYTHONHASHSEED=0` to `ablation_cells.sbatch` before `exec python`. Have `ioi_rows` refuse to
     run when the variable is unset. Write the IOI sentences, or their sha256, into `summary.json`. Sorting the
     names in `load_names` would fix the cause, but it changes every existing IOI caller, so that is the
     orchestrator's decision.

2. **Major: `--ids` rejects the W3 test-sample file, and the sbatch example points at a file that does not exist.**
   - Evidence: `outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json` holds keys `task, seed, split,
     ids, pairing, ...`, with `ids` a `{D,H,F,I,N}` map. `load_ids` (`scripts/neuron_set_ablation.py:209`) unwraps
     `ids` only when it is a list. The top-level keys then fail the per-condition test:

     ```
     SystemExit: outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json: --ids is a JSON list of ids, {"instance_ids": [...]} or {condition: [...]}
     ```

     The sbatch header (line 19) passes `outputs/_analyses/neuron-partition/ids/far_test_seed2.json`, which does not
     exist. The CLI ran only after I extracted `ids` into a flat per-condition file myself (the dry run below).
   - Fix: in `load_ids`, when `raw["ids"]` is a dict whose keys are conditions, use it as the per-condition map.
     Point the sbatch example at the real W3 file. The R10 half files will need the same shape.

3. **Minor: `attach_twin` pairing has two gaps.**
   - (a) At `scripts/neuron_set_ablation.py:519-520` the batches are zipped before the length check. If I loads
     whole extra batches beyond N, `zip` drops them and the check after it still passes. Fix: compare the lengths
     before the zip.
   - (b) The checks are symmetric, so `--i-dir` and `--n-dir` given in swapped order pass `attach_twin`. That covers
     id order, masks, Readout, swapped words and the request-span diff. `check_labels` catches the swap only on I ids
     that are also in D, which is 164 of 300 here, and only when D is loaded. Fix: assert that every I record has
     `condition == "user_inversion"` and every twin record has `condition == "user_neutral"`. Also assert equal
     `request_id`/`neutral_id` where present, since the D-to-H path checks `pressure_id`.

4. **Minor: the mean bank's description contradicts R3.** `collect_mean_bank` writes `"semantics": "per site, every
   unpadded position of the cell's test split ..."` (`knockout.py:942`). The CLI adds `splits: train,validation`
   but keeps that string, so `summary.json` describes the bank as test-split data. Fix: override `semantics` in
   the CLI, or make the string say "the batches given".

5. **Minor: the sbatch defaults can bypass R9 and W3's frozen copy.**
   - The Delta full-cell example (line 24) omits `--max-length 128`, which R9 requires. The pilot example has it.
   - The Delta default pool path (line 106) reads the live specificity-ladder worktree. It does not read W3's copy
     under `outputs/_analyses/neuron-partition/data/pools/`, whose `pools_manifest.json` records sha256.
   - Fix: add `--max-length 128` to the example, or default it in the script. Default the pools to W3's copy on
     both clusters.

6. **Minor: the HF token could be written to `summary.json`.** `--hf-token` defaults to `$HF_TOKEN` (line 160) and
   `"args": vars(args)` (line 1179) writes it out. `HF_TOKEN` is unset in the current shell and in `~/.bashrc`, so
   the risk is latent. Fix: drop or redact `hf_token` before dumping.

7. **Minor: two operational guarantees are not enforced in code.**
   - `cells_partial.jsonl` keeps the finished cells, but no code resumes from it, so a killed job reruns in full.
   - The R4 check of intact IOI accuracy against 0.51 is not enforced. The orchestrator must read
     `sets.<any>.references.mean.conditions.IOI.accuracy_argmax_intact` from the pilot before the full cell, with
     finding 1 fixed first.

## Answers to the eight questions

1. **Site and isolation: yes.**
   - The site is `block.mlp.down_proj.input`. It is reached only under `if layer in neuron_layers:`
     (`hooks.py:538`), where `neuron_layers = set(wanted["sites"]["mlp_hidden"]) | set(neuron_writes)`. That set
     is empty when no `mlp_hidden` key is named.
   - A write is `value = value.clone(); value[:, :, columns] = values`, or `torch.where` under one per-layer mask.
     So only the named columns at the masked positions change.
   - `test_replacing_one_neuron_changes_exactly_that_column` asserts that only column 17 changes and that layer 0
     is untouched.
   - The other changes are order-preserving set dedup (`knockout.py:755`, `:1406`) and argmax recording behind
     `record_argmax`.
   - My golden check ran head 1.2 plus MLP 0 under item-swap, twin, zero and mean on the tiny model with main's
     modules and with the worktree's. The clean, knocked and counterfactual margins were identical by exact float
     equality. So were the capture sums for head, q, k, v, `mlp_in` and `mlp` and the logits.
2. **Twin interchange: yes.**
   - Under `neutral_twin` with `interchange`, the donor is the twin's prompt (`other_ids, other_mask =
     pair.input_ids, pair.attention_mask`, `knockout.py:807`). Its capture of every chunk member is written over
     D's clean run.
   - Positions: the default plan is `all`, so `where` is None and position p gets the twin's position p.
   - Alignment for D and H is enforced by the loader: `assert_clause_aligned_pair` on both streams, equal attention
     masks and the same `pressure_id`. `knockout.py:809` raises if the twin's Readout differs.
   - Alignment for I and N is enforced by `attach_twin`, with the gaps in finding 3.
   - Unpaired rows are skipped and listed (`unpaired.extend`, `:798`). They reach `summary.json` `unpaired`. The
     dry run showed 300 of 300 paired on D and on I.
   - Both prompt streams are scored. `corrupt_stream` swaps the answer words and uses the twin's corrupt prompt as
     the donor.
   - The reverse patch is descriptive under R7: H receives D's values, and N receives I's.
   - `ladder_ratio` computes G = mean over ids of the stream-averaged (m_D − m_twin), and the fraction removed as
     mean(m_intact − m_ablated) / G, a ratio of means. It refuses when `g <= epsilon`, with
     epsilon = max(1e-6, 10 × self-replay) (`:1147`). This matches R2 and reader brief section 2. The rate effect
     is stored beside it.
3. **Mean and zero: yes.**
   - `--mean-bank-split` defaults to `train,validation` of F, loaded through `descriptive_batches`. The bank pools
     the clean and corrupt prompts over every unpadded position, accumulated in fp32, at the same capture site.
   - The bank is reduced once per layer (`bank[key] = layer_sums[...]/tokens`). Fills are cast to the model's dtype
     and expanded over every position (`spread`, `:835`).
   - Zero: in my check, zero-ablating all 128 neurons of tiny layer 1 gave an MLP output of exactly 0.0, and
     `down_proj` has no bias.
4. **Effect measures and signs: correct.**
   - `sign = 1` on D, I and IOI and −1 on H, F and N (`:1084`). So m = logit(opposite) − logit(honest) on every
     stream. `check_labels` checks per id that H's and F's Target is D's Distractor.
   - The rate uses `>=` 0.7. Under mean and zero, the effect compares ablated D with ablated H (R8), and the
     comparison with intact H is stored as `effect_ablated_vs_twin_intact`.
   - Accuracy is full-vocabulary argmax against the row's own Target (`:778`). That is honest on H, F and N,
     opposite on D and I, and the name on IOI.
   - Under the twin reference, F and IOI collateral is null and the H collateral is marked
     "reverse twin (descriptive)", as R7 requires.
5. **I/N pairing: mostly sufficient.**
   - Checked: ids and order, both attention masks, Readout, swapped Target and Distractor, and a token diff
     confined to `request_spans` on both streams.
   - On real data, `request_spans` is a dict of token offsets, for example `{'clean': [85, 105], 'corrupt':
     [85, 105]}`. The full dry run paired all 300 rows.
   - The gaps are in finding 3.
6. **IOI adapter: the recipe is followed.**
   - It calls `generate_ioi_data_llama(1000, tok, seed=1)`, dedups by sentence in generation order and takes the
     first 100 eligible rows with no correctness filter.
   - Eligibility is `whole == prefix + target`, which proves the answer is one contextual token, and the
     distractor must be one token.
   - The Readout is the last prefix token, with BOS, as `IOIDatasetLlama` does. Accuracy is argmax against the
     answer name, which is name A.
   - Reproducibility is finding 1.
7. **Performance and robustness: acceptable.**
   - The model is loaded once in `run`.
   - Each chunk does one clean pass and one twin capture per batch, plus one pass per set.
   - `cells_partial.jsonl` gets one line per finished cell.
   - Twin capture memory at batch 8 × 128 is about 8·128·14336·2 B = 29 MB per layer, so about 0.94 GB for 32
     layers.
   - No quadratic path over keys remains. `effect_metrics` has an O(n²) `one in c.ids` over about 300 ids, which
     costs nothing in practice.
   - For the k = 500 sets file with nulls (84 sets), the dry run estimates 97,210 forwards and about 87 minutes,
     including the model load, at the extrapolated H100 rate.
8. **Tests and the independent CPU check: pass.**
   - mgnp: 32 passed. Base 3.9: 16 passed and 16 skipped.
   - My own check on the tiny model, through torch hooks rather than the code under test, gave these results.
   - Zero on all of layer 1: the MLP output's maximum absolute value was 0.0, and the margins matched a
     zero-MLP-output torch run to 3e-8.
   - Twin interchange on all of layer 0: the down_proj input and MLP output equalled the twin's exactly, with a
     difference of 0.0. The twin's input differs from the clean one by 0.159, so the check is not trivial.
     Margins matched a twin-MLP-output torch run to 1.5e-8.
   - bf16: zero, mean and twin ran without dtype errors. A mean-written column equalled the bank value cast to
     bf16. The tests cover only fp32.

## Commands and key output

Scratch outputs are in `outputs/_analyses/neuron-partition/review2_tmp/`, and the scripts are `ioi_hash.py` and
`indep_check.py`.

```
OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_neuron_set_ablation.py
32 passed, 1 warning in 13.07s
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_neuron_set_ablation.py
16 passed, 16 skipped, 3 warnings in 20.71s

python review2_tmp/indep_check.py <worktree> full
"zero_layer1_mlp_output_max_abs": 0.0, "down_proj_has_bias": false,
"zero_layer1_margin_vs_torch_maxdiff": 2.98e-08,
"twin_layer0_down_input_maxdiff_vs_twin": 0.0, "twin_layer0_mlp_output_maxdiff_vs_twin": 0.0,
"twin_vs_clean_down_input_differs": 0.1588, "twin_layer0_margin_vs_torch_maxdiff": 1.49e-08,
"bf16": {"zero": ok, "mean": ok, "twin": ok, "mean_bf16_col5_equals_bank": true}
python review2_tmp/indep_check.py /projects/beto/swong2/Alignment/Deception-Circuit golden   # main's modules
identical (exact float equality): True

PYTHONHASHSEED={0,1} python review2_tmp/ioi_hash.py     # finding 1, output quoted above

python scripts/neuron_set_ablation.py --task far --sets .../far_atp_66741d7/far_sets_k500_with_nulls.json \
  --ids review2_tmp/ids_by_condition.json --i-dir .../data/pools/far_v2_user_inversion \
  --n-dir .../data/pools/far_v2_user_neutral --output-dir review2_tmp/dry --max-length 128 --dry-run
rows {'D': 300, 'H': 300, 'F': 300, 'I': 300, 'N': 300, 'IOI': 100}  max_length 128 (IOI 21)
D n_with_neutral_twin 300, I n_with_neutral_twin 300, without_neutral_twin [] on both
total 97210 forwards, ~78.9 min of forwards + 7.7 min model load = ~86.6 min
```
