# Review 01: W1 neuron attribution-patching scorer

**Verdict: PASS WITH FIXES.** There are no blockers. The scorer computes what its docstring says, correctly, on every
check I could run. Two major findings concern what the scores mean for ruling R6, not code defects. Seven minor
findings concern test gaps, a runtime label check and provenance.

Reviewer: independent reviewer (Claude Opus 5.5), read-only, for session claude-5201d56c, Tue 3 Nov 2026. Scope:
commit 1393444 of `component_analysis/neuron_attribution.py`, `scripts/neuron_attribution.py`,
`tests/test_neuron_attribution.py` and `docs/research/neuron-partition/jobs/pilot_attribution.sbatch`. The hand-back
under review (reports/01) was not read. Line numbers below refer to the committed module, whose sha256 is
`ac21a987b0a841f6830612f769eea9110b19ae8667e7b18fc439fdb743ec647a`. That hash matches the full ranking runs'
manifests, and the file did not change during the review.

The CLI and the test file changed on disk during the review. These are W1's uncommitted edits adding `--ids` and
halves. The test file grew from 439 lines with 24 tests to 509 lines with 28 tests. The CLI hash moved from `126574ec…`,
the committed one, to `c7604bfe…`. I reviewed the committed CLI. The 24-test count below is for the committed test
file. The mutation runs ran against the 28-test file.

## Findings

### 1. Major (design): the ranking score targets a different counterfactual than the primary ablation

**Evidence.** The readout AtP is `atp_ro = diff_ro * g[rows, readout]` (lines 516 to 518), which estimates m(D) minus
m(D with this neuron set to its H value at the readout only). The clause variant sums over the clause span only
(lines 524 to 532). The primary ablation writes the twin's value at every position. The header of
`scripts/neuron_set_ablation.py`, lines 12 to 17, says:

> In each D row the set's activations are replaced, at every position, by their values in the same instance's H twin

On the real FAR validation rows, D and H differ from the clause onward. Neither score covers the positions between
the clause end and the readout:

| Pair | Clause length, median [min, max] | Positions between clause end and readout | Readout, median |
|---|---|---|---|
| D vs H | 11.5 [10, 14] | 43 in every row | 96 |
| I vs N | 20 [20, 20] | 10 in every row | 116 |

On FAR D/H, those 43 positions are the whole user question and the assistant prefix. MLP neurons there read the
clause through attention and differ between D and H. The first-order estimate of the actual intervention is the sum
over all positions of `diff * g`, and the readout AtP is one term of it.

**Fix.** Add an all-position AtP pair to `score_batch`. Every tensor needed is already in hand, so the change is
additive and leaves the existing keys unchanged. A sketch:

```python
valid = batch.attention_mask.to(device).unsqueeze(-1).to(work)
atp_all = (diff * g * valid).sum(1)          # positions before the clause contribute 0 (diff == 0)
acc.add(layer, "atp_all_sum", atp_all); acc.add(layer, "atp_all_abs", atp_all.abs())
```

Add a finite-difference test that sums over every position, as the clause test does. Rerunning costs minutes at the
measured 0.085 to 0.11 seconds per row. R6 names the readout position, so the lead must also rule on one of two
options. Either rank on the all-position score, or record why readout-only is the intended target. The intended
target could be readout-only if the ablation were also restricted to the readout. This finding does not block the
ablation, because the ablation tests every set causally whatever the ranking. A mis-targeted ranking loses power,
not validity.

### 2. Major (design): R6's s_H and s_D share the activation difference and disagree near chance on the top neurons

**Evidence.** The forward score is `diff = a_c - a_t` with `atp_ro = diff_ro * g[rows, readout]` (lines 515 to 518).
The reverse score is `rev_ro = -diff_ro * g_t[rows, readout]` (line 535). So s_D = (a_D minus a_H) times g_D, and
R6's s_H = minus rev = (a_D minus a_H) times g_H. The two differ only in which run's gradient multiplies the same
activation difference. Under a locally linear readout they would be nearly equal. On the full D/H run (400 train and
validation rows, `far_v2_dh_train+validation_7386fd3_rev`) they are not:

| Statistic | Value |
|---|---|
| Pearson(s_D, s_H), all 458,752 neurons | 0.013 |
| Pearson(s_D, s_I) | 0.775 |
| Pearson(s_I, s_H) | -0.062 |
| Sign agreement of s_D and s_H, top 10 by abs(s_D) | 0.60 |
| Sign agreement, top 100 by abs(s_D) | 0.63 |
| Sign agreement, top 500 by abs(s_D) | 0.57 |
| Sign agreement, top 100 by abs(s_H) | 0.49 |

The clearest case is L15 n11788, with s_D +0.344, s_H -1.089 and s_I +0.863. L15 n2808 has s_D +0.255 and s_H
-0.608. L16 n8935 has s_D +0.241 and s_H -0.502.

This is not a scorer bug. The reverse test pins the reverse score to the forward score of the swapped row, and a sign
error would give a strongly negative correlation, not zero. The sums are of similar size, 7.29 for s_D and 9.67 for
s_H. Either the gradient context really flips between D and H for these neurons, which is a strong non-linearity,
or first-order AtP is unreliable where it matters most. In both cases, "T_H minus T_D" selects neurons whose
gradient context differs. It does not select neurons that "support the honest answer" in a simple sense. This bears
directly on how the H-only and D-only classes read.

The class sizes under R6 on the full runs follow. The I scores come from 354 rows; see finding 9.

| k | T_D and T_H overlap | T_D and T_I overlap | D-only | D-and-I shared | H-only | all-shared |
|---|---|---|---|---|---|---|
| 500 | 154 | 283 | 174 | 172 | 331 | 111 |
| 1,000 | 277 | 523 | 409 | 314 | 702 | 209 |
| 2,000 | 476 | 954 | 895 | 629 | 1,474 | 325 |

**Fix.** Validate before W4 builds T_H. Run a direct one-neuron interchange, forward with D getting H's value and
reverse with H getting D's value. Patch at the readout to match the current scores, and at every position if
finding 1 is adopted. Use the top 20 neurons by abs(s_D) and the top 20 by abs(s_H), on about 32 ranking rows. That
is a few hundred forwards on one GPU. `shift_neuron` (lines 372 to 389) already does the patch. If the measured
change in m confirms the sign flips, the non-linearity is real and R6's class descriptions need rewording. If it
does not, AtP is unreliable at the head of the ranking, and the head should be re-ranked by actual patches.

### 3. Minor (test gap): no test catches an absmean computed as the absolute value of the mean

**Evidence.** I mutated `finalize` to `s["atp_ro_sum"].abs() / n`, and all 28 tests passed. Every AtP test scores
one row, where the mean of abs(s) equals abs(mean s). The multi-row independence test (lines 225 to 235) checks
`atp_readout_mean`, `atp_clause_mean` and `contrast_readout_mean` but not the absmean keys. The code itself is
right: `acc.add(layer, "atp_ro_abs", atp_ro.abs())` (line 520) takes the absolute value per row before summing.

**Fix.** Add `atp_readout_absmean` and `atp_clause_absmean` to the key list in
`test_rows_in_one_batch_are_scored_independently`. That test averages the per-row single-row scores, so it would
catch the mutation. The impact is low, because R6 ranks on the signed means.

### 4. Minor (test coverage): a wrong readout index and a flipped metric sign are each caught by only one test

**Evidence.** All finite-difference tests use one unpadded row, which `collate` trims, so the readout is the last
position. Mutation results:

| Mutation | Tests failing |
|---|---|
| `diff = a_t - a_c` (swapped sign) | 5, including both FD readout tests and the clause FD test |
| Readout read at position -1 instead of `readout` | 1, `test_rows_in_one_batch_are_scored_independently`, only because it uses `pad_tail` |
| Gradient read at `readout - 1` | 4, including both FD readout tests |
| Metric direction `distractor - target` | 2, `test_readout_metric_matches_the_full_logits` and the new CLI ids test |
| `n_readout` counting batches, not rows | 2 |
| Twin forward fed the clean ids | 6 |
| absmean as abs(mean) | 0 (finding 3) |

The FD family cannot see a flipped metric sign by construction, because both sides use `readout_metric`. A swapped
sign of the activation difference is caught well.

**Fix.** Run one FD readout test on a batch of two rows, one with `pad_tail`, and compare at the padded row's
readout. This puts the main correctness test on a readout that is not the last position.

### 5. Minor (Q5): "labels equal to D's" is checked by a test on FAR only, not at run time

**Evidence.** `in_pairs` takes I's own labels: `target = dc.encode_answer_token(tokenizer, record["target"])`
(line 241). Equality with D's labels is asserted only in `test_i_and_n_are_scored_with_d_labels` (lines 419 to 428),
for FAR train and validation. Nothing checks SER. The run-time guard is indirect: the sha256 gate on the pool arrows,
plus the test passing on those exact arrows.

**Fix.** Either pass D's labels by id into `in_pairs` and raise on mismatch, which is cheap at load time, or state
the guard chain in the hand-back and add the SER case to the test before any SER run.

### 6. Minor: the I/N clause check compares span lengths but not offsets

**Evidence.** `if len(twin_span) != 2 or twin_span[1] - twin_span[0] != span[1] - span[0]: use_span = None`
(line 267). I's span is then used for both streams. The case is harmless as far as I can see, because the code also
asserts that every differing token lies inside I's span (lines 261 to 265) and that the total lengths are equal. The
reader brief also says `request_spans` are equal in every row. Measured: 0 clause fallbacks in the pilot and in the
full runs.

**Fix.** Assert `twin_span == span` and drop the length-only fallback, or keep the fallback and also require equal
offsets.

### 7. Minor (provenance): the full runs are labeled with a commit the code was not at

**Evidence.** The full ranking cells are named `..._7386fd3`, and argv contains `'--commit', '7386fd3'`. The manifest
says `"git_commit": "6c6d5be1b631f4f248a29bbc77c0192cb198b4ea"` and `"git_dirty": true`, Slurm job 23476096. The
module's `code_sha256` is `ac21a987…`, the 1393444 module, which is not the 7386fd3 one: 1393444 added the pool
sha256 checks that these cells record. The pilot cells, at f4ce555 and also dirty, predate the sha256 check, so
their `rows.json` has no `arrow_check`. I verified the pilot's two validation arrows by hand against the brief:
inversion `2c7659c2…f38f75` and neutral `7addc5f9…ee3389`, both matching.

**Fix.** Record in the hand-back that the `7386fd3` cells ran the 1393444 module, identified by code sha256
`ac21a987…`. Prefer leaving `--commit` at its default, which reads HEAD, in later runs. The manifests are otherwise
complete. They hold the full commit, `dataset_files` with sha256 (34 files for the I/N cell, 24 for D/H), argv,
code hashes, the "unmerged Codex pool" note naming W3's copy, and in `rows.json` the per-split `arrow_check`, all
`ok: true`.

### 8. Minor (property, not a bug): `contrast_*_std` blows up on near-constant neurons

**Evidence.** The code is `out["contrast_readout_mean"] / (_std(s["twin_ro_sum"], s["twin_ro_sq"], n) + STD_EPS)`
with `STD_EPS = 1e-6` (lines 102 and 454). In the pilot I cell, the largest value is 259.7, at L11 n5288. There the
contrast mean is 0.362 and the implied twin standard deviation is 1.39e-3. 47 neurons exceed 50, with implied
standard deviations of 3.5e-4 to 1.7e-2. The readout token and its local context are identical across rows, so many
neurons are nearly constant there. An epsilon of 1e-6 is far below bf16 activation resolution. This is expected
behavior of a z-score with a tiny epsilon. R6 uses the contrast mean, so nothing depends on it.

**Fix.** None is required. If the standardized contrast is ever ranked, floor the denominator, for example at the
median standard deviation in the layer.

### 9. Minor: s_D and s_I come from different id sets, and only the clean stream is scored

**Evidence.** The D/H full run scores 400 rows. The I/N run scores 354, because the I pool is a 177-of-200 subset per
split. R6 compares top-k sets across the two. The ablation also averages the clean and corrupt streams within an
id, as stated in `neuron_set_ablation.py` (`--streams clean,corrupt`). The scorer reads only `clean_prompt` and
`twin.input_ids`. The clean stream is balanced on answer position in FAR: the target is the first-named item in 100
rows and the second in 100, in both train and validation. So clean-only ranking is not position-confounded. It uses
half the available rows.

**Fix.** This is optional. Rank s_D on I's 354 ids for the class comparison, or report that the sets differ. A
corrupt-stream pass would reuse `batch.corrupt_input_ids`, `twin.corrupt_input_ids` and the swapped labels.

## Answers to the seven questions

1. **Site and gradient flow.** Correct. The pre-hook on `layer.mlp.down_proj` stores `args[0]`, the tensor
   `down_proj` consumes (lines 346 to 349 and 360). `test_capture_is_the_post_swiglu_down_proj_input` asserts it
   equals `act_fn(gate_proj(x)) * up_proj(x)` with shape (batch, seq, width) for every layer. Gradients use
   `torch.autograd.grad(m_clean.sum(), clean.acts)` (line 490), not `retain_grad`. The graph is rooted at the
   embedding output by `output.requires_grad_(True)` (lines 341 to 344), and parameters are frozen
   (`models/__init__.py`, `load_full_model`, `p.requires_grad = False`). There is no detach before the gradient.
   Hooks are removed in `__exit__` (lines 364 to 368). `autograd.grad` frees the graph, and the activations are
   detached and the capture lists cleared after each batch (lines 491 and 492). Nothing carries across batches. The
   layer-0 FD test passes at 1e-4 relative, which shows the graph is not cut.
2. **Metric and per-row gradient.** Correct. `readout_metric` recomputes the final RMSNorm in fp32 and dots it with
   the difference of the target and distractor unembedding rows (lines 403 to 413). The gradients reaching the
   activations are bf16 on the 8B model, which is fine for ranking. D's target is the deceptive answer. I and N are
   scored with I's labels, which equal D's on FAR (finding 5). The pilot agrees with the stored margins: D/H Pearson
   0.9996 clean and 0.9998 twin, sign agreement 1.000; I/N 0.9991 and 0.9985. The batch-sum gradient equals each
   row's own gradient, because rows do not interact and padding is on the right. `load_tokenizer` sets
   `padding_side = "right"`, and both loaders raise if the readout is not the last unpadded token.
   `test_rows_in_one_batch_are_scored_independently` (with `pad_tail=3`) confirms this. Each row has its own readout
   index (`g[rows, readout]`).
3. **AtP sign and twin readout.** s > 0 means the clean value pushes m up relative to the twin value. That is,
   patching toward the twin lowers m, so the neuron supports the clean condition's Target. The twin's readout cannot
   differ in absolute index. The D/H loader raises unless the twin's attention mask equals D's (`dataloaders.py`
   around lines 445 to 448). `in_pairs` raises unless the masks are equal and the stated readouts match (lines 248 to
   256). The D/H clause span is one span shared by both streams by loader assertion. For I/N, see finding 6.
   Positions between the clause and the readout are unscored (finding 1).
4. **Aggregation.** The sums run in float64, stricter than the float32 asked for (lines 437 and 444). They are divided
   by the number of rows actually scored: `n_readout`, and `n_clause` for rows with a clause (lines 449 to 468 and
   543 to 544). absmean is the mean of abs(s) per row (lines 520 and 529). The standard deviation is the population
   standard deviation over rows of the twin activation, plus 1e-6, which matches numpy in the test. The blow-up is a
   property, not a bug (finding 8).
5. **I/N pool path.** Rows are paired by id and by position, and the code raises otherwise (lines 233 to 237). The
   arrow sha256 values are checked against the brief's table before any row is read (`verify_pool_arrows`,
   `load_rows`). Labels are asserted equal to D's only in a test (finding 5). The manifest is complete (finding 7).
6. **Tests.** The FD test compares AtP with (a_c minus a_t) times a central-difference gradient (step 1e-3) of a
   one-neuron shift. It runs on a float64 tiny Llama at layers 0 and 1, at `rel=1e-4`, and requires at least 5 of 15
   sampled neurons to have an FD value above 1e-6, so the gradient is non-trivial. A full one-neuron patch is also
   checked against AtP at 5 percent. A swapped activation-difference sign is caught by 5 tests. A wrong readout index
   is caught by 1 to 4 tests, depending on the form. Coverage gaps are in findings 3 and 4.
7. **Tests and the independent numeric check.** The results follow.

| Pilot cell (64 validation rows) | dh | in |
|---|---|---|
| Mean m_clean | 3.090 | 6.820 |
| Mean m_twin | -7.362 | -9.091 |
| Mean gap | 10.453 | 15.911 |
| Neurons with abs(atp_readout_mean) > 0.01 | 2,017 | 6,258 |
| Neurons with abs(atp_readout_mean) > 0.1 | 56 | 117 |

The top five by abs(atp_readout_mean), as (layer, index, score):

- **dh:** (14, 10056, +0.448), (15, 11788, +0.423), (15, 2808, +0.385), (13, 4212, +0.376), (16, 8935, +0.370).
- **in:** (15, 11788, +0.864), (15, 2808, +0.812), (16, 8935, +0.656), (14, 10825, -0.550), (13, 4212, +0.524).

The scores are plausible in magnitude. The top single neuron accounts for about 4 percent of the dh gap and 5 percent
of the in gap. The k-th largest positive score is 0.017, 0.010 and 0.007 at k = 500, 1,000 and 2,000 on dh. Four of
the dh top five are also in the I top five. The per-layer sums concentrate in layers 13 to 16 and 19 to 21, plus layer
31. As a loose check only, the summed readout AtP over all neurons is 9.07 against the dh gap of 10.45, and 17.31
against the in gap of 15.91. These sums double-count downstream paths, so they are not an identity. The full 400-row
D/H run reproduces the head of the ranking: L13 n4212, L14 n10056, L15 n11788, L15 n2808 and L16 n8935.

## Commands run and key output

All commands ran from the worktree root on the login node, on CPU, with no git.

```text
$ OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider \
    tests/test_neuron_attribution.py -q -rs --basetemp=/u/swong2/.claude/jobs/5201d56c/tmp/rev1/pt
24 passed in 31.93s          # committed 439-line test file; an earlier attempt errored only because --basetemp's parent did not exist

$ bash /u/swong2/.claude/jobs/5201d56c/tmp/rev1/mut/run_mutations.sh     # pytest plugin re-execs the module with one mutation
diff_sign: 5 failed; readout_last: 1 failed; grad_readout_minus1: 4 failed; metric_sign: 2 failed;
absmean_is_abs_of_mean: 28 passed (rerun alone); count_batches: 2 failed; twin_uses_clean_ids: 6 failed

$ /u/swong2/.conda/envs/mgnp/bin/python -I /u/swong2/.claude/jobs/5201d56c/tmp/rev1/pilot_check.py \
    far_v2_dh_validation_f4ce555_limit64 far_v2_in_validation_f4ce555_limit64 far_v2_dh_train+validation_7386fd3_rev
dh: mean m_clean 3.090, m_twin -7.362; |s|>0.01: 2017, >0.1: 56; contrast_std max 93.9 (L13 n792, twin std 1.2e-3)
in: mean m_clean 6.820, m_twin -9.091; |s|>0.01: 6258, >0.1: 117; contrast_std max 259.7 (L11 n5288, twin std 1.39e-3)
dh full rev: 400 rows; corr(fwd, rev) -0.013

$ /u/swong2/.conda/envs/mgnp/bin/python -I /u/swong2/.claude/jobs/5201d56c/tmp/rev1/rev_check.py
pearson(s_D, s_H) 0.013; pearson(s_D, s_I) 0.775; pearson(s_I, s_H) -0.062
L15 n11788: s_D +0.3439 s_H -1.0892 s_I +0.8632

$ /u/swong2/.conda/envs/mgnp/bin/python -I /u/swong2/.claude/jobs/5201d56c/tmp/rev1/sign_agree.py
top 100 by |s_D|: sign(s_H) == sign(s_D) in 0.63; top 100 by |s_H|: sign agreement 0.49

$ /u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/5201d56c/tmp/rev1/layout.py
dh: clause length median 11.5 [10, 14]; positions between clause end and readout 43 [43, 43]; readout median 96
in: clause length median 20 [20, 20]; positions between clause end and readout 10 [10, 10]; readout median 116

$ /u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/5201d56c/tmp/rev1/streams.py
train and validation: clean-stream target is the first-named item in 100 rows and the second in 100
```

The scripts are in `/u/swong2/.claude/jobs/5201d56c/tmp/rev1/`, a temporary directory.
