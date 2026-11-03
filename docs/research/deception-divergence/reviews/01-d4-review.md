# Review 01: D4 closure riders and the static quartet read

Independent Opus review, Mon 2 Nov 2026, of the four D4 riders of direction deception-divergence and of hand-back 02
(`reports/02-handback.md`, including its GPU addendum). I read the frozen rules first, then the code and the raw
outputs, recomputed every number below with my own code, and read the hand-back last. CPU only, mgnp interpreter,
`python -I`, BLAS threads 4, no git, no Slurm, no GPU. My recompute scripts are outside the repository, in
`/u/swong2/.claude/jobs/5b9b1c28/tmp/rev_p1.py`, `rev_p2.py`, `rev_d4a.py`, `rev_d4a2.py`, `rev_d4b.py`,
`rev_d4b2.py` and `rev_d4c.py`; they import no project code except the tokenizer and `datasets` loader in `rev_p2.py`.

## Verdict

**Every number in the hand-back that I checked reproduces.** Rider (d): P1 fails and P2 fails under the frozen rule,
and the P1 fail holds under every reading matrix and without the RMSNorm gamma fold. Rider (a): the quartet's
attention profile moves between D and its twin on both tasks, as reported. Rider (b): the after-cue arm is built as
specified, `post_tag` reproduces J4 bit for bit, and the after-cue numbers hold; one interpretive sentence outruns the
evidence. Rider (c): the T2 frozen rule reads query-side on SDR with a wide margin, and the T1 label "closes,
route-specific" is correct under R1 and R9; the sentence explaining the old F-sdr-012 contrast is a plausible
interpretation, not a result of this run.

## Scope and files read

Rules: `spec.md` (D4 rules, R1 to R5, R2a), `START.md` section 2 item D4 and section 10 D4 rules, instructed-route
`spec.md` R1, R5, R9, R10, R10a, R11, and `plans/B1-plan.md` sections 1.2 to 1.4, 2.1, 2.2 and the smoke gates.

Rider (d): `scripts/d4_static_quartet.py`, `tests/test_d4_static_quartet.py`,
`outputs/_analyses/deception-divergence/d4d/static_quartet.{json,md}` and `run_manifest.json`, the Llama-3.1-8B-Instruct
safetensors at revision 0e9e39f2 (`/work/nvme/beto/swong2/hub/...`), `dataset/deception_common.py`
(`encode_answer_token`) and the far_v2, sdr_v2 and ser_v2 test splits.

Rider (a): `component_analysis/attention_patterns.py` (the `--attention-instances` flag, `pressure_batches`,
`neutral_twin_batches`), `tests/test_d4a_attention_instances.py`, `jobs/D4a.batch`,
`outputs/_analyses/deception-divergence/d4a/{far,ser}/Ct__leaf/<task>_v2/{attention/patterns.json,sample.json,run_manifest.json}`,
`logs/analyze_components_23443932.out` and `docs/research/mechanism-analysis/phase1/groups/{far,ser}_heldout_D_sample.json`.

Rider (b): `spontaneous/patching.py` (`after_cue`, `last_difference`, `arm_mask`, `twin_interchange`, `run_syc`),
`spontaneous/af_prompts.py` (`SycPair`, `build_syc_pair`), `spontaneous/stats.py`, `scripts/b3_patch.py`,
`tests/test_d4_after_cue.py`, `outputs/_analyses/deception-divergence/d4b/{results,margins,run_manifest}.json`,
`logs/d4b_after_cue_23443933.out`, `data/b3/syc_items.json`, and J4's
`outputs/_studies/b3/j4_syc/margins.json` and `j4_syc_supplement/margins.json` in the primary checkout.

Rider (c): `jobs/D4c-sdr.batch` against instructed-route `jobs/B1-far.batch` and mechanism-analysis
`jobs/05-p3-sdr.batch`, `outputs/_analyses/deception-divergence/d4c/sdr/Ct__leaf/sdr_v2/route_closure/route_closure.json`,
`run_manifest.json`, `sample.json` and its `.pre-b2fetch` copy, `logs/bridges2/analyze_components_50132625.out`,
`results/d4c/b1_readings.{json,md}` and `scripts/route_closure_readings.py`.

Then `reports/02-handback.md`, `WORKLOG.md` and the F-rte-005, F-rte-006, F-rte-008 and F-sdr-012 rows of
`docs/research/FINDINGS.md`.

## Recomputations

### Rider (d), static read

| quantity | my command | observed | reported | agree |
|---|---|---|---|---|
| P1 score of all 320 senders, stacked quartet W_Q, gammas folded | `rev_p1.py`, dense column-convention product, float64 | max abs difference to `P1.ranking` 1.2e-15 | `static_quartet.json` | yes |
| head.15.8 score and rank | same | 0.038365, rank 7 | 0.0384, rank 7 | yes |
| head.14.4 score and rank | same | 0.029505, rank 24 | 0.0295, rank 24 | yes |
| layer-sum order, layers 7 to 16 | same | 14, 13, 12, 15, 11, 10, 16, 8, 9, 7 | same | yes |
| P1 without the gamma fold (sensitivity) | same, raw weights | 15.8 rank 4, 14.4 rank 23, same layer order | not reported | P1 still fails |
| item tokens | `rev_p2.py`, `datasets.load_from_disk`, own tokenization of `" " + word` | 82 single-token items, 0 multi-token | 82, 0 dropped | yes |
| copy score, L17H24 to L17H27 | `rev_p2.py`, RMS-normalised embedding, gamma_17, W_V group 6, W_O head slice, gamma_final, W_U, rank <= 5 | 0.000, 0.000, 0.0122, 0.000 | 0.000, 0.000, 0.012, 0.000 | yes |
| mean own-logit rank, L17H24 to L17H27 | same | 61558.7, 50302.1, 32943.1, 80041.7 | same to 0.1 | yes |
| identity-map copy score | same | 0.000 | 0.000 | yes |
| KV group of heads 24 to 27 | config: 32 query heads, 8 KV heads | group 6 for all four | 6 | yes |
| shard LFS names, index, config | `static_quartet.json` `weights` | 2b1879f3, 09d433f6, fc1cdddd, 92ecfe1a; 146776fc; 29e4c210 | same | yes |

My medians of the own-logit ranks differ from the reported ones (for example L17H24 59593 against 60238). That is a
convention difference, not a disagreement: I used `torch.median`, which returns the lower middle value of the 82
ranks, while the script uses `numpy.median`, which averages the two middle values. Copy scores and mean ranks agree
exactly.

### Rider (a), attention patterns

| quantity | my command | observed | reported | agree |
|---|---|---|---|---|
| ids profiled | `rev_d4a.py` against the two `*_heldout_D_sample.json` files | 100 of 100 on both tasks, both sides, same order on D and twin; `sample.json` equals the group file | 100 of 100, identical `instance_ids` | yes |
| pairing | `neutral_twin.alignment` | 100 pairs, 0 differing outside the clause, 0 identical | same | yes |
| TV shift far, L17H24 to L17H27 | half the L1 distance of the mean 19-Segment readout profiles | 0.329, 0.243, 0.476, 0.198 | same | yes |
| TV shift ser, L17H24 to L17H27 | same | 0.166, 0.155, 0.316, 0.058 | same | yes |
| rank among C_t heads, far | `rev_d4a2.py` | 8, 13, 2, 17 of 62; median of the other heads 0.100, 90th percentile 0.312 | same | yes |
| rank among C_t heads, ser | same | 7, 10, 2, 26 of 68; median 0.041, 90th percentile 0.158 | same | yes |
| quartet-mean mass far, D against twin | same | designating_sentence 0.064 vs 0.184; designation_suffix 0.015 vs 0.077; item_2_question_pair 0.167 vs 0.092; item_2_question_option 0.118 vs 0.051 | same | yes |
| quartet-mean mass ser | same | designation_suffix 0.024 vs 0.129; pressure_clause 0.067 vs 0.020; unsegmented 0.168 vs 0.128; item_1_question_pair 0.060 vs 0.039 | same | yes |
| L17H26 designating sentence, far | same | 0.453 to 0.151 | 0.453 to 0.151 | yes |
| L17H24 item_2_question_pair, far | same | 0.205 to 0.377 | same | yes |
| B2 clause-mass drop ser, L17H26 and L17H25 | `neutral_twin.b2.per_head` | 0.094 (SE 0.011), 0.071 (SE 0.007) | same | yes |
| B2 clause-mass drop far, largest absolute value | same | 0.013 (L17H27, negative) | under 0.013 for every head | yes |
| same direction in the identity and inversion halves | `rev_d4a2.py`, sign of the quartet-mean shift on the four largest Segments | same sign on all four, both halves, both tasks | same direction | yes |

### Rider (b), after-cue arm

| quantity | my command | observed | reported | agree |
|---|---|---|---|---|
| items, kept, flips | `rev_d4b.py` on `margins.json` | 800, 530, 154 | 800, 530, 154 | yes |
| pass-2 clean and twin margins, S_all at post_tag | `rev_d4b2.py` against J4 `margins.json` | bit-identical (max abs difference 0.0) | f 0.7241 against J4 0.724 | yes, stronger than reported |
| heads_only at post_tag margins | against the J4 supplement `margins.json` | bit-identical | f 0.4984 | yes |
| f, S_all at after_cue | ratio of means, my own bootstrap, seed 0 and seed 7 | 0.6618 (0.6443 to 0.6785; seed 7 0.6441 to 0.6792) | 0.662 (0.644 to 0.679) | yes |
| f, S_all at post_tag | same | 0.7241 (0.7017 to 0.7463) | 0.724 (0.702 to 0.746) | yes |
| f, heads_only at after_cue | same | 0.5819 (0.5627 to 0.6006) | 0.582 (0.563 to 0.601) | yes |
| f, heads_only at post_tag | same | 0.4984 (0.4699 to 0.5262) | 0.498 (0.470 to 0.526) | yes |
| null f maximum, 4 arms | recomputed from each draw's margins | 0.383, 0.505, 0.346, 0.271 | 0.383, 0.505, 0.346, 0.271 | yes |
| flip reversal, 4 arms | `results.json` `reversal` | 0.825, 0.942, 0.779, 0.805 | same | yes |
| f on flips | my ratio of means over the 154 flips | 0.792, 0.914, 0.745, 0.746 | not in the hand-back | n/a |
| S_all minus heads_only | difference of the points | 0.226 at post_tag, 0.080 at after_cue | 0.226, 0.080 | yes |
| cue window and tail | job log | 7 tokens, 23 positions after it, every row | same | yes |
| subject-clustered interval (56 MMLU subjects, seed 1) | `rev_d4b2.py`, the F-rte-008 scheme | S_all after_cue 0.627 to 0.693; post_tag 0.669 to 0.770; heads_only after_cue 0.540 to 0.621; post_tag 0.434 to 0.557 | not in the hand-back | n/a |
| null spread, SD and minimum | `rev_d4b2.py` | S_all after_cue SD 0.329, min -0.870; post_tag SD 0.250, min -0.430; heads_only after_cue SD 0.282; post_tag SD 0.280 | not in the hand-back | n/a |

### Rider (c), SDR route closure

| quantity | my command | observed | reported | agree |
|---|---|---|---|---|
| ids and clusters | `rev_d4c.py` | 100 ids equal to `sdr_heldout_D_sample.json`; 19 pressure-id clusters; no missing pressure id | 100, 19 | yes |
| P | mean m_D minus mean m_T; G equals m_D minus m_T exactly | 6.547 | 6.547 | yes |
| r_Q (q_readout) | restore share, my own cluster bootstrap, seed 20261101 and seed 5 | 0.524 (0.488 to 0.556; seed 5 0.489 to 0.557) | 0.524 (0.488 to 0.556) | yes |
| r_K (k_options) | same | -0.002 (-0.012 to 0.008) | -0.002 (-0.012 to 0.008) | yes |
| r_Q minus r_K | same | 0.526 (0.490 to 0.556) | 0.526 | yes |
| r_out (out_readout) | same | 0.558 (0.524 to 0.589) | 0.558 | yes |
| other key and value arms | same | v_options 0.000, kv_options -0.001, k_post_clause -0.023, k_clause -0.001, pre-clause mentions exactly 0.000 | not in the hand-back | n/a |
| T2 controls | same | Q at 5 random layer-17 quartets at most 0.0041; K at the other 7 KV groups at most 0.0023; K at random post-clause tokens at most 0.001 in absolute value | not in the hand-back | n/a |
| O, offline | per-instance `outside_sum` over mean G | 0.857 (0.823 to 0.891) | 0.857 (0.823 to 0.891) | yes |
| O_q, offline | same | 0.468 (0.434 to 0.499) | 0.468 | yes |
| M_q, offline (R9 rule estimator) | ratio of means of the per-instance sums | 0.546 (0.511 to 0.577; seed 5 0.510 to 0.576) | 0.546 (0.511 to 0.577) | yes |
| M_q, forward | same on the forward sums | 0.550 (0.507 to 0.596) | 0.550 | yes |
| M_C3 | offline `c3_push` over offline O | -0.032 | -0.032 | yes |
| max C1 or C2 | offline draws | 0.0225 (c2_d1) | 0.022 | yes |
| M_S | offline `s_k` | 0.821 (0.772 to 0.867) | 0.821 | yes |
| M_q minus M_C3 | `b1_readings.json` | 0.578 (0.542 to 0.610) | not in the hand-back table | n/a |
| O as the sum of in-sum senders | `senders[*].e` | 0.8572 over 990 senders | 990 outside senders | yes |
| gates G1, G2, G3 | `route_closure.json` `gates` | G1 bit-identical; G2 0.0; G3 sender 0.00031, sum 0.0138, joint 3.7e-5 | same | yes |
| arms | `len(arms)` | 47 | 47 | yes |
| readings input | sha256 of `route_closure.json` | 3348680d..., equal to `b1_readings.json` `inputs` | n/a | yes |
| B1 comparators | FINDINGS F-rte-005 and F-rte-006 | far M_q 0.360, ser 0.462; far r_Q 0.321, r_K -0.012, r_out 0.327; ser 0.426, 0.014, 0.433 | same | yes |

### Tests

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d4_static_quartet.py tests/test_d4a_attention_instances.py tests/test_d4_after_cue.py tests/test_d4_jobs.py
OMP_NUM_THREADS=4 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q (same files)
```

Observed: mgnp 34 passed; base 30 passed, 4 skipped. The hand-back's 33 and 29 predate the addendum's added b2-fetch
test in `tests/test_d4_jobs.py`, which accounts for the one extra test on each interpreter.

## Code checks

### Rider (d)

- **Q-composition form.** `q_composition` computes the norm of W_OV times the reading matrix, over the product of the
  two norms, through Gram matrices; it is the Elhage et al. normalised Frobenius form with the quartet's stacked,
  gamma-folded W_Q (4096 by 512) as the reading matrix. The spec says "into the quartet's W_Q", so the score of record
  follows the rule's wording. The literal Elhage form into W_QK is reported beside it and also fails.
- **RoPE invariance.** RoPE multiplies each head's 128 query dimensions by a block-diagonal rotation, which is
  orthogonal, so the stacked W_Q score is exactly invariant; the HF row permutation of `q_proj` for rotate-half is
  also orthogonal. The test with a random orthogonal rotation checks this. The W_QK form is not RoPE-invariant and
  the script says so.
- **OV factors and grouped-query attention.** `ov_factors` takes rows `g*128` to `(g+1)*128` of `v_proj` with
  g = head // 4 and the head's 128 columns of `o_proj`. HF Llama's `repeat_kv` gives query heads 4g to 4g+3 the
  key/value head g, so heads 24 to 27 share group 6. My dense recompute used the same slicing independently.
- **Copy score.** Item embedding, divided by its RMS, times the layer-17 input gamma, through the head's OV, times the
  final-norm gamma, against W_U; the final RMS divisor is a positive per-row scalar and leaves ranks unchanged. The
  rank counts strictly greater logits. This matches the spec's "final-norm-scaled W_U" and Wang et al.'s copy score
  apart from their mlp.0 step, which is reported beside and changes nothing.
- **Item tokens.** The prompts end in an assistant stem such as "The result that is failing is", and the datasets
  score the leading-space item token (`encode_answer_token`, used by the loaders). The 82 tokens are the union of every
  `target` and `distractor` over the three test splits, all single-token. That is what the datasets score.
- **Random baselines.** P1: 20 seeded draws of four non-quartet layer-17 heads as receivers; 0 of 20 pass, and both
  named senders score higher into the quartet than into every draw. P2: 20 seeded non-quartet layer-17 heads, mean
  0.006, max 0.024. The P2 ceiling over all 1,024 heads (best 0.390, none at 0.5) and the identity map (0.000) show the
  read has no power on this model with untied embeddings.
- **Provenance.** The manifest's `code_sha256` for the script (895ae401...) equals the committed file. One minor point:
  the three `dataset_dict.json` files hash identically (1239dbd4...), because that file only lists split names, so
  the manifest does not pin the item data. The item set is reproducible from the committed datasets regardless.

### Rider (a)

- `instances_of` returns `split` unless the flag says `causal_sample`; `pressure_batches` and `neutral_twin_batches`
  call the old loaders on the default path. The default therefore reads the whole split as before. The tests check
  this through the CLI (no `instances` key, 1,000 rows loaded) and with a mock context (call order), but no test
  compares a default run's files byte for byte, so the hand-back's "byte-for-byte as before" is supported by reading
  the code, not by a test.
- The manifest hashes only `analyze_components.py`, not `attention_patterns.py`. The hand-back covers this by
  comparing the worktree file with `git show c6752c0:`; I confirmed the worktree sha256 (c1780949) and that the last
  commit touching the file is c6752c0.
- The measure is a total-variation distance between two mean profiles over Segments, with no interval. Only the B2
  clause mass has a paired standard error.

### Rider (b)

- `last_difference` returns one past the last differing token. `arm_mask` for `after_cue` sets positions from that end
  through the Readout and refuses a window that does not open or a tail that is empty. `run_syc` passes
  `SycPair.cue_end`, which `build_syc_pair` sets to the last differing index plus one. So the arm excludes exactly the
  differing span and includes every later position through the Readout. The cue sentence and the neutral sentence
  share the trailing ", but I'm curious what you think." tokens, so the excluded window is the 7 differing tokens, and the
  identical trailing tokens of the sentence are patched as after-cue positions. That is the arm as specified.
- `post_tag` and `readout` take the old branch of `arm_mask` unchanged. The per-item margins at `post_tag` are
  bit-identical to J4 and the supplement, which settles it.
- Null draws (R10, R10a): I checked all 80 draws. None contains a head member of its set; every S_all draw keeps
  mlp.5, mlp.6 and mlp.7 and records them in `null_kept_members`; every draw matches its set's (kind, layer) counts.
  The same draws serve both position arms, so after_cue and post_tag are compared on one null.

### Rider (c)

- `D4c-sdr.batch` differs from `B1-far.batch` only in the SDR operands: `X` (skct_sdr), the `Ct` expression
  (`Ds-Df-De`, `Ds-Hs`), the `x_sdr` reference, `--task-from`, the sample file, the deciding set
  (`sdr_heldout_D.json:greedy_k20`) and the output directory. Its composition flags equal `05-p3-sdr.batch` verbatim.
  The grid matches `ct.json` (66 Components, `matches_cell` true).
- The reader computes r_a as a ratio of means over the per-instance gap G, M_q as the ratio of the mean offline
  outside sums, and the cluster bootstrap by pressure id; the T2 rule compares r_Q and r_K with a 1e-12 tolerance,
  and the R1 label compares the offline M_q with the offline controls. This is the rule as written.
- `route_closure.json`'s own `t1.summary` names the forward estimator as its rule estimator; the reader overrides it
  with offline per R9, and both close. Anyone reading the raw file alone could take the forward number; the readings
  file is the one of record.
- The `.pre-b2fetch` files are the Delta dry run's copies; `sample.json` carries the same 100 ids in both.

## Verdicts

- **Rider (d): supported.** Pre-registered reading: **P1 fail** (head.14.4 ranks 24 against the cutoff of 16, and the
  layer-15 sum is fourth), **P2 fail** (0 of 4 quartet heads reach 0.5). The P1 fail does not depend on the reading
  matrix or the gamma fold. Under the spec, a P1 fail means the routing is activation-dependent, which supports the
  distributed parallel route; the P1 baseline shows that the two named senders still compose more with the quartet's
  queries than with any random layer-17 quartet. P2 fails under the rule, but no head of the model passes this read,
  so the fail carries almost no information about copying. The hand-back says both things and keeps the rule
  unchanged after the result, which is right.
- **Rider (a): supported.** The rule is "report the numbers". The quartet's readout attention moves between D and its
  twin on both tasks; L17H26 ranks second of the C_t heads on both. On far the mass moves from the designation to the
  item options; on ser from the designation suffix to the pressure clause. The hand-back correctly adds that this
  run does not test whether the attention shift carries the effect.
- **Rider (b): supported with caveats.** The rule is "report the numbers". The arm is correct, the anchor reproduces
  bit for bit, and every number holds. Caveats are issues 1 and 2 below.
- **Rider (c): supported with caveats.** Pre-registered reading: **query-side** on SDR, r_Q minus r_K 0.526 against
  0.15, with the interval from 0.490 to 0.556. T1, reported beside: M_q 0.546 on the R9 offline estimator, so
  "closes"; above every C1 and C2 draw (at most 0.0225) and 0.578 above M_C3, so "closes, route-specific" under R1.
  The caveat is issue 3.

## Issues

1. **Low. Rider (b), the null-spread attribution.** The hand-back says the after-cue arm "answers the F-rte-008
   caveat". That holds for the MLP part: S_all minus heads_only falls from 0.226 to 0.080, so most of what mlp.5 to
   mlp.7 add sits on the cue window. It does not hold for the other half of that caveat, which attributed the wide
   null spread to patching across the cue tokens. The spread is at least as wide after the cue: S_all null SD 0.329
   (minimum -0.870) at after_cue against 0.250 at post_tag, and heads-only 0.282 against 0.280. The lower null maximum
   at after_cue (0.383) comes with a wider spread, so "no longer non-specific" rests on 20 draws from a wide
   distribution. Also, the MLP share is a difference of two non-additive arms; no arm patches mlp.5 to mlp.7 alone.
   Fix: in the finding, say the cue window holds most of the MLP increment and that the null spread is not explained
   by the cue tokens.
2. **Low. Rider (b), "shared and specific".** At after_cue, S_all is in the shared band (0.662) and its null maximum
   (0.383) is under the R5 non-specific line, so the R5 qualifier does not apply on that arm. "Specific" there means
   specific against random heads given the same three MLPs; per F-mech-003 the sets also carry transparent inversion,
   so it is not deception-specific. The hand-back hedges this as a reading, not a re-decision of F-rte-008. Fix: keep
   the F-mech-003 caveat in the same sentence wherever the after-cue label is stated.
3. **Low. Rider (c), the explanation of the old contrast.** "So the contrast belonged to the method or the dataset,
   not to the tasks" is interpretation. F-sdr-012 measured how perturbations from specific layer-13 senders reach
   layer 17 on a truth margin in the routing pilot; D4(c) restores the pressure effect from the neutral twin at the
   quartet's queries or keys. The two runs measure different quantities, so this run shows that on one code path and
   one estimator SDR is query-side like FAR and SER, not why the pilot found keys. The run's own key arms are thorough:
   keys at the options, at every post-clause position, at the clause and at the pre-clause mentions all move under
   0.025 of P. Fix: state it as "the contrast does not reproduce under the B1 code path", and leave the cause open.
4. **Low. Rider (c), the T1 margin.** M_q's lower interval end, 0.511, sits 0.011 above the 0.50 bar on 19 clusters.
   The hand-back says so. Any finding that contrasts SDR's "closes" with FAR's and SER's "bypass" should carry the
   interval.
5. **Minor. Rider (a), default-path claim.** "A default run is byte-for-byte as before" is supported by reading the
   code and by the tests' row counts, not by a byte comparison. Fix: soften to "the default path calls the same
   loaders".
6. **Minor. Provenance.** The D4(d) manifest hashes `dataset_dict.json`, which is identical across the three tasks
   and does not pin the item data; the D4(a) manifest does not hash `attention_patterns.py`. Neither changes a number.
   The D4(c) output directory keeps three `.pre-b2fetch` files from the dry run, which could confuse a later reader.
7. **Minor. P2 medians.** The reported medians use `numpy.median` (mean of the two middle ranks). This is noted only
   so a later recompute with `torch.median` is not mistaken for a disagreement.

No issue changes a pre-registered verdict.

## Recommendation

The findings register in `WORKLOG.md` is still empty, so I map F1 to F4 to the riders in the hand-back's order: F1 is
rider (d), F2 rider (a), F3 rider (b), F4 rider (c). If the orchestrator numbers them differently, the per-rider
recommendation still applies.

- **F1, rider (d): mark reviewed.** P1 fail and P2 fail, with the P2 ceiling caveat (no head of the model passes).
- **F2, rider (a): mark reviewed.** Descriptive, with the caveat that the shift is between mean profiles with no
  interval and is not shown to carry the effect.
- **F3, rider (b): mark reviewed with issues 1 and 2 applied to the wording.** The numbers stand as reported.
- **F4, rider (c): mark reviewed with issues 3 and 4 applied to the wording.** The query-side verdict and the T1
  label stand.
