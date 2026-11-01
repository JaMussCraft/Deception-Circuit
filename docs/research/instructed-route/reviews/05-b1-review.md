# Review 05: B1 loop closure (T1) and key-side versus query-side (T2) on the held-out sample

Reviewer: independent review agent (Claude Opus 5.5), session claude-230e4716, Sun 1 Nov 2026. Scope: the B1 task
jobs on FAR and SER (Bridges-2 jobs 50106660 and 50106721, commit 476c187), their outputs under
`outputs/_analyses/instructed-route-b1/{far,ser}/Ct__leaf/{far,ser}_v2/`, and the readings in
`docs/research/instructed-route/results/b1/`. Read against `spec.md` (B1 exit criteria, R1, R9),
`plans/B1-plan.md` sections 0 to 5, hand-backs 29 and 30, `component_analysis/route_closure.py`,
`scripts/route_closure_readings.py` and `docs/research/mechanism-analysis/synthesis.md`. No git, no job, no code change.

## Verdict

**Agree, both tests stand as read.** T1 is **bypass** on FAR and SER, R1 label "bypass". T2 is **query-side** on
FAR and SER. An independent recomputation from `route_closure.json` reproduces every headline number of
`b1_readings.md` to three decimals, and the intervals to within 0.002 with a different seed and twice the resamples.
The verdicts do not depend on the estimator: offline, forward and the joint swap all give M_q under 0.50 on both
tasks, and every M_q interval excludes 0.50. Two qualifications belong in the finding text. First, the quartet is
partly necessary, not irrelevant: it mediates about a third (FAR) and under half (SER) of the outside-grid share,
and in the reverse direction it is sufficient for about three quarters of the pressure effect. Second, gate G3's
summed check failed on SER at 100 ids, which R9 already covers. The finding status can be `reviewed`.

## Checks

### 1. Independent recomputation

The recomputation sums O from the per-sender `mean_drop` fields, a different path from the per-instance
`outside_sum` the readings use; the two agree exactly. The arm shares come from `arms.<arm>.margins` and the
baseline. The bootstrap resamples whole `pressure_id` clusters, 4,000 resamples, seed 777.

| quantity | far (recomputed) | far (readings) | ser (recomputed) | ser (readings) |
|---|---|---|---|---|
| O, offline | 0.7814 [0.762, 0.803] | 0.781 [0.762, 0.802] | 0.7525 [0.704, 0.784] | 0.752 [0.704, 0.783] |
| O_q, offline | 0.2815 | 0.281 | 0.3473 | 0.347 |
| M_q, offline (rule, R9) | 0.3602 [0.335, 0.395] | 0.360 [0.337, 0.395] | 0.4616 [0.435, 0.485] | 0.462 [0.437, 0.485] |
| M_q, forward (beside) | 0.3561 [0.335, 0.390] | 0.356 [0.335, 0.390] | 0.4469 [0.412, 0.474] | 0.447 [0.413, 0.474] |
| M_q, joint swap (both estimators) | 0.324 | n/a | 0.429 | n/a |
| r_q (dq_all margins) | 0.3423 [0.322, 0.369] | 0.342 | 0.4509 [0.426, 0.472] | 0.451 |
| M_C3 | -0.0306 | -0.031 | -0.0351 | -0.035 |
| C1 draws (M) | 0.002, 0.001, -0.005, 0.009, -0.025 | max 0.175 with C2 | 0.001, -0.000, -0.004, 0.009, -0.024 | max 0.111 with C2 |
| C2 draws (M) | -0.234, 0.117, 0.055, -0.058, 0.175 | | -0.022, -0.038, 0.111, -0.084, -0.016 | |
| M_S | 0.9977 | 0.998 | 1.0384 | 1.038 |
| r_Q | 0.3210 [0.301, 0.345] | 0.321 | 0.4256 [0.396, 0.446] | 0.426 |
| r_K | -0.0115 [-0.017, -0.007] | -0.012 | 0.0136 [0.007, 0.018] | 0.014 |
| r_out | 0.3273 | 0.327 | 0.4328 | 0.433 |
| r_K - r_Q | -0.3325 [-0.360, -0.310] | -0.333 [-0.359, -0.312] | -0.4120 [-0.432, -0.385] | -0.412 [-0.432, -0.384] |

- **The frozen rules.** M_q is 0.360 and 0.462, both under 0.50, so both tasks are bypass. Under R1 the label is
  "bypass" whatever the controls say. For information only: M_q is above every C1 and C2 draw and 0.39 and 0.50
  above M_C3, so a closing M_q of this size would have been labelled "route-specific". r_Q - r_K is 0.333 and
  0.412, beyond the 0.15 margin, and r_out is 0.327 and 0.433, above the 0.15 ceiling, so both tasks are
  query-side.
- **The readings' input hashes match the files.** `b1_readings.json` names sha256 prefixes `9c6bf9f2cbb5` (far) and
  `07cacc9a0d9d` (ser), which are the hashes of the two `route_closure.json` files on disk.
- **Internal consistency.** G = m(D) - m(T) holds per instance to 1e-6. Each sender's `e` equals its
  `mean_drop / mean G` exactly. The T arm's own total share is exactly 1.0 by construction.

### 2. The run against the pre-registration

- **Sample: matches.** Both cells' `sample.json` carry the same 100 `instance_ids`, in the same order, as
  `docs/research/mechanism-analysis/phase1/groups/{far,ser}_heldout_D_sample.json`. `instances.ids` is that list in
  that order, and `without_twin` is empty on both.
- **Grid: matches.** The run's grid equals `phase3/ct.json` `tasks.<task>.members.C_t`: 72 keys on far and 78 on
  ser, with `grid.matches_cell` true. The outside set is exactly the 1,056 heads and MLPs minus C_t, so 984 and 978.
  The quartet is inside C_t and absent from the outside set, and the embedding is never a sender.
- **Deciding set: matches.** It is `greedy_k20` of `{far,ser}_heldout_D.json`, all 20 Components in order, and all
  20 lie inside C_t.
- **Quartet: matches.** It is head.17.24 to head.17.27, KV group 6. The T2 key arms write `k.17.6`, and the query
  arms write `q.17.24..27` at the Readout.
- **Interventions: matches.** Every arm is an interchange with the neutral twin: base D with values from T, or base
  T with values from D for the reverse arms. The pre-clause key and value arm is an exact zero on 100 of 100 rows on
  both tasks, which confirms that D and T are token-aligned and that the mask is right.
- **Controls: seeded and disjoint.** The C1 and T2 query draws are five distinct sets of layer-17 heads, none in
  the quartet or C_t. The C2 draws are five sets of four heads in layers 8 to 16, none in C_t, the deciding set or
  the quartet. The key controls cover the seven other layer-17 KV groups. On the first batch, the random-position
  draws are four post-clause tokens per row, never an option token or the Readout.
- **Path patching ran.** `route_path_patching` is "on" and `t1.path_patching.status` is "computed", with
  `same_instances` true. Plan 1.5 covers the top 20 writers under three sender masks. Plan 2.3 covers the five named
  feeders and 17 layer groups, with no sender skipped.
- **Nothing pre-registered is missing.** `not_implemented` is empty. Every T1 arm of plan 1.1 to 1.3 is present: the
  three dq arms, tq_all, C1 to C3 and S_k. So is every T2 arm, descriptive arm and control of plan 2.2, along with
  the plan 1.2 rows for mlp.31, mlp.30 and L31H0, the positive and negative parts and the joint swaps.
- **The manifest is mostly complete.** It has a 40-hex `git_commit` 476c18770bcd3d461368ce67faeb535e45b29270 with
  `git_dirty` false, the Slurm job ids 50106660 and 50106721, the hosts w004 and w003, the model revision, the
  dataset file hashes and the software versions. `code_sha256` holds only `analyze_components.py`. See problem 4.

### 3. Gates on the full runs

| gate | far | ser |
|---|---|---|
| G1, empty bank equals m(D) | bit-identical, max diff 0.0 | bit-identical, max diff 0.0 |
| G2, every sender from T equals m(T) | max diff 0.0 | max diff 0.0 |
| G3, per sender (tolerance 0.01) | 1.8e-4 (head.20.1) | 3.0e-4 (head.16.16) |
| G3, joint swap | 1.7e-4 | 2.9e-4 |
| G3, summed O (tolerance 0.02) | 0.0103, passed | **0.0290, failed** (T arm; dq_all 0.0019) |

- **The ser miss has the smoke's signature.** The per-sender and joint checks pass by a factor of 30. The summed
  check fails only on the T arm. Across instances the forward estimator scatters far more than the offline one:

  | per-instance spread | forward, far | forward, ser | offline, far | offline, ser |
  |---|---|---|---|---|
  | O range (share of G) | 0.055 to 2.222 | -1.077 to 4.261 | 0.432 to 0.989 | 0.477 to 1.107 |
  | RMS of sum of single swaps minus joint swap, T arm (logits) | 2.68 | 2.38 | 0.84 | 0.40 |
  | M_q range | -0.216 to 1.320 | -1.820 to 2.455 | 0.111 to 0.641 | 0.226 to 0.981 |

  This is hand-back 29's diagnosis at 100 ids, the bf16 forward rebuild. Far passes by cancellation again: the
  offline-minus-forward difference is positive on 51 of 100 instances, with mean +0.007 of G and standard deviation
  0.30.
- **R9 does not change any verdict at 100 ids.** Offline and forward M_q differ by 0.004 on far and 0.015 on ser.
  Both are bypass, with upper interval bounds of 0.395 and 0.485 offline and 0.390 and 0.474 forward. Both estimators
  agree on the joint swap to 3e-4, and the joint-swap M_q is lower still. R9 chose the estimator that gave the
  higher ser M_q on the smoke, 0.472 against 0.414, so it moved the rule toward "closes", not toward the outcome
  observed.

### 4. Sanity

- **M_S is near 1.0.** Restoring the 20-component deciding set after the clause removes 0.998 and 1.038 of the
  outside share, and its own total share is 0.989 and 1.042. Every outside sender's pressure contribution is
  downstream of the deciding set's post-clause outputs. It also shows that this free-recompute estimator can reach
  1.0, so the quartet's 0.36 and 0.46 are not an estimator ceiling.
- **O replicates the selection sample.** Held-out O is 0.781 and 0.752 offline, and 0.771 and 0.781 forward. The
  selection sample gave 0.803 and 0.774 (E14). The E14 measurement was a forward sweep, so forward is the
  like-for-like comparison, and it differs by 0.03 and 0.01.
- **r_q agrees with M_q.** Restoring the quartet removes 0.342 and 0.451 of the whole effect and 0.360 and 0.462 of
  the outside share. The outside writers lose their pressure contribution at about the same rate as the total.
- **No outliers drive the means.** On the offline estimator, no instance has a share below zero or above one. The
  per-instance M_q has median 0.363 and 0.462, and a 10% trimmed mean of 0.345 and 0.477. Dropping the 10 lowest and
  10 highest instances by O gives 0.348 and 0.457, and the ratio of medians gives 0.344 and 0.445. Every robust
  reading is under 0.50.
- **SER is close to the bar.** 44 of the 100 ser instances are individually at or above 0.50, against 11 of 100 on
  far. The ser 90th percentile is 0.698.
- **Signed-sum fragility (plan section 6) is not at work.** The negative part shrinks by about the same fraction as
  the positive part, so no relaxing suppressor inflates O_q:

  | part | far | ser |
  |---|---|---|
  | positive part, split by each arm's own sign | 0.413 | 0.488 |
  | negative part | 0.541 | 0.531 |
  | positive part, senders fixed by their sign under T | 0.404 | 0.481 |
  | mlp.30, the plan's named suppressor | 0.70 | 0.44 |

  The positive part alone stays under 0.50 on both tasks, though ser's 0.481 to 0.488 is close.

### 5. Interpretation of T1

- **What "bypass" means here.** Restoring the quartet does not carry half of the outside-grid share; it carries
  0.36 (FAR) and 0.46 (SER). This says the quartet is partly mediating, below the pre-registered bar. It does not
  say the share is "not mediated by the quartet".
- **The bypass is distributed, not a separate set of writers.** Each large outside sender keeps part of its effect
  and loses part. Among the 25 largest senders by |e_s(T)|, the quartet mediates 0.30 to 0.70 of each one's direct
  effect on far and 0.24 to 0.73 on ser. By layer bucket:

  | layers | far O | far mediated | ser O | ser mediated |
  |---|---|---|---|---|
  | 18 to 23 | 0.237 | 0.32 | 0.266 | 0.42 |
  | 24 to 27 | 0.300 | 0.41 | 0.332 | 0.48 |
  | 30 to 31 | 0.227 | 0.33 | 0.155 | 0.55 |

  Layers 0 to 17 carry almost no outside share (under 0.01), and layers 28 and 29 net near zero. No late writer is
  wholly downstream of the quartet, and none is wholly independent of it. The quartet is one of several parallel
  channels from the deciding set to the same late writers.
- **The mediated part acts at the Readout.** Restoring the quartet at the Readout only gives M 0.344 and 0.441, and
  post-clause without the Readout gives 0.021 and 0.030. Plan 1.5 agrees. Writing the quartet's T value into the
  top 20 writers' receivers gives a joint effect of 0.253 and 0.419 of G at the Readout and 0.0004 and 0.0012 from
  the post-clause positions. The receivers are q and `mlp_in` at the Readout, and the k and v of each writer's KV
  group after the clause.
- **Path patching is not an additive split.** Pass 2 of `quartet_path_patching` lets everything downstream of the
  receivers recompute. The joint effect therefore includes downstream spread and is not a direct-edge share. The
  sum of the 20 single-writer effects, 0.119 and 0.163, is under half the joint effect. One single writer,
  head.26.15, has a path effect of -0.093 and -0.132, larger in size than its whole sweep effect of -0.027 and
  -0.044. The joint effect is 0.74 (far) and 0.93 (ser) of r_q. That supports "most of the quartet's effect enters
  the late writers' Readout inputs directly", as an exploratory reading. Per-writer path numbers should not be
  quoted as a decomposition of M_q.
- **The rest of the outside share has an unnamed route.** It leaves the deciding set (M_S near 1) and reaches the
  same late writers without passing through the quartet's outputs. B1's arms do not name that route. One hint: on
  far, the C2 draws of four outside-grid heads in layers 8 to 16 move the outside share by -0.234 and +0.175, and
  their total share by -0.216 and +0.157. So mid-layer heads outside C_t are not inert on far. That is a reading of
  five draws, not a located route.
- **Necessity and sufficiency differ.** In the reverse direction, giving the twin the quartet's D outputs (tq_all)
  reproduces 0.735 and 0.731 of the pressure effect, and giving it D's quartet query at the Readout (rev_q_readout)
  reproduces 0.745 and 0.691. Restoring the quartet in D removes only 0.342 and 0.451. The quartet's signal is
  enough on its own for most of the effect, but removing it leaves a parallel route carrying the rest. This is
  redundancy, consistent with the distributed per-sender picture.
- **C3 says the late writers do not amplify a layer-17 answer push.** A push along the answer direction at mlp.17,
  matched to the quartet's layer-17 lens change (mean -1.92 and -1.54), moves the final margin by 0.007 and 0.008
  of G. It moves the outside share by -0.031 and -0.035. Because the push is matched on the layer-17 lens at a fixed
  scale, it is a modest push at the final layer. The negative result is real, but it is not strong evidence on its
  own.
- **Self-repair caveat (plan section 6).** M_q uses free recompute, so compensation lowers it. M_S near 1 under the
  same estimator limits how much this can matter, but B1 has no no-compensation counterpart to M_q itself.

### 6. T2: does the key arm do anything?

- **The key arm is implemented and moves the margin per instance.** The k_options arm has no exact-zero rows on
  either task. Its mean absolute drop is 0.208 (far) and 0.169 (ser) logits, against about 0.023 for the other
  layer-17 KV groups and the random post-clause positions. Its per-instance shares run from -0.076 to 0.072 (far)
  and -0.255 to 0.138 (ser). The pre-clause key and value arm, which must be exactly zero by causality, is zero on
  100 of 100 rows.
- **r_K is near zero because the effects cancel, not by construction.** The option-token keys do differ between D
  and T: the option tokens follow the clause and can attend to it. The per-instance effects have both signs and
  cancel in the mean. The ceiling arm agrees: keys at every post-clause position give -0.019 and 0.006.

  | arm | far | ser |
  |---|---|---|
  | values at the options | -0.012 | -0.000 |
  | keys and values at the options | -0.023 | 0.014 |
  | keys at the clause | 0.0005 | 0.0047 |
  | reverse key arm | -0.008 | 0.019 |
  | query and key interaction, r_QK - r_Q - r_K | 0.014 | -0.005 |

  Plan 2.3 finds no upstream sender with a path effect into `k.17.6` at the options larger than 0.0132 in size
  (ser layer 14).
- **The query side carries what the quartet's Readout output carries.**

  | arm | far | ser |
  |---|---|---|
  | query at the Readout, r_Q | 0.321 | 0.426 |
  | quartet output at the Readout, r_out | 0.327 | 0.433 |
  | query at every post-clause position | 0.336 | 0.443 |
  | reverse query arm | 0.745 | 0.691 |

  The five query controls on non-quartet layer-17 heads are each at most 0.0023 in size.
- **Where the query signal comes from (plan 2.3).** These are path effects into the quartet's query at the
  Readout:

  | sender | far | ser |
  |---|---|---|
  | layer 14 | 0.296 | 0.286 |
  | layer 15 | 0.174 | 0.243 |
  | layer 13 | 0.050 | 0.054 |
  | layer 16 | -0.074 | -0.095 |
  | head.15.8 | 0.250 | 0.338 |
  | head.14.4 | 0.188 | 0.176 |

  Layer 16 opposes. Layers 0 to 12 are each under 0.01. This replicates the synthesis's B-selector clause 1 on
  held-out ids under a frozen rule. On far, head.15.8 outranks head.14.4 here, unlike E11's ordering for L17H24
  alone on the selection sample.
- **What query-side licenses.** The clause reaches the quartet through the final-token residual at layer 17, which
  layers 13 to 15 write, and not through changed keys or values at the option tokens. The quartet's Readout output
  changes because of what the final token asks for. B1 captured no attention patterns, so it cannot say which
  positions the changed query attends to more or less. The keys and values that the query reads are almost
  unchanged by the clause. Sun et al.'s option-token routing feature (arXiv 2605.09314) is not supported for this
  quartet on FAR or SER. This contrasts with F-sdr-012, where the grouped keys of KV group 6 were the main input on
  SDR. That is a difference between tasks, not a contradiction: F-sdr-001 already found mixed interfaces on SDR.

## Problems found

None changes a verdict.

1. **G3 failed on ser at 100 ids.** The summed-O difference is 0.0290 against 0.02, on the T arm. The per-sender
   difference is 3.0e-4 and the joint difference 2.9e-4. This repeats the smoke's failure mode, and R9, recorded
   before any 100-id reading, already handles it. The failure should still be recorded as failed and explained, as
   hand-back 29's question 3 proposed, and named in the finding's caveats. Far passed G3 by cancellation.
2. **Stale estimator labels in `route_closure.json`.** Commit 476c187 predates R9. In both files,
   `t1.summary.rule_estimator` is "forward", and `t1.summary` O, O_q and M_q are the forward values; M_q there is
   0.356 and 0.447. `plan_1_5.ranked_by` also says forward. The readings script reads correctly under R9, and the
   top 20 writers are identical under either ranking (20 of 20 on both tasks). Anyone quoting `t1.summary` from the
   JSON will get the beside numbers labelled as the rule. A one-line note in the direction README or results would
   prevent that.
3. **C3 misses its target change.** `max_abs_miss` is 0.032 and 0.037 logits, against ticket 5's 1e-4 test bar.
   That bar was set on a tiny fp32 model, and here the miss is about 2% of a mean target change of -1.9 and -1.5,
   presumably from the bf16 forward. It does not touch the label, because R1 reads C3 only when the loop closes.
4. **The code hash is incomplete.** `code_sha256` in `run_manifest.json` covers `analyze_components.py` only, not
   `component_analysis/route_closure.py` or `hooks.py`. The clean 40-hex commit (`git_dirty` false) pins the code,
   so provenance holds. A future manifest could hash the analysis module too.
5. **The bootstrap has few clusters.** Far has 11 pressure clusters and ser 14, with sizes from 2 to 18. Percentile
   intervals over so few clusters can be too narrow. The verdicts use point estimates as the frozen rule says, so
   this affects how strongly the finding is stated, not the verdict. Ser's upper bound of 0.485 sits 0.015 below the
   bar.
6. **Plan 1.5's split is not additive.** The plan says the sum of path effects against O_q "splits M_q". The path
   patching's free downstream pass makes single-writer effects non-additive: their sum is half the joint effect, and
   one writer exceeds its own sweep effect. Report the joint effect against r_q, and do not use per-writer numbers as
   a split.

## Proposed finding text

Two rows in the shape of F-rte-002, with ids F-rte-005 and F-rte-006 or the next free ids when committed. Both are
`reviewed` at commit 476c187.

**T1 row**

| field | text |
|---|---|
| id | F-rte-005 |
| date | 2026-11-01 |
| direction | instructed-route |
| claim | Does restoring the layer 17 quartet H24 to H27 carry at least half of the outside-grid share of the FAR and SER pressure effect (B1 T1): no, bypass on both, because on the 100 held-out ids the neutral-twin interchange of the quartet's outputs removes 0.360 of the outside-grid share on FAR (interval 0.337 to 0.395 clustered by 11 pressure ids) and 0.462 on SER (0.437 to 0.485 by 14), on the offline estimator of record under R9 (forward 0.356 and 0.447, joint swap 0.324 and 0.429), with outside shares 0.781 and 0.752 against 0.80 and 0.77 on the selection sample; the quartet is partly, not wholly, necessary: it mediates 0.30 to 0.70 (FAR) and 0.24 to 0.73 (SER) of each of the 25 largest outside senders' direct effects across layers 18 to 31, almost all at the readout (0.344 and 0.441 there, 0.021 and 0.030 after the clause without it), while restoring the 20-component deciding set after the clause removes 0.998 and 1.038 and the reverse interchange of the quartet into the twin reproduces 0.735 and 0.731 of the pressure effect, so the rest of the share reaches the same late writers from the deciding set by a parallel route that B1 does not name; C1 draws reach at most 0.009, C2 draws 0.175 and 0.111, and C3 gives -0.031 and -0.035. Caveats: G3's summed check failed on SER (0.029 against 0.02) from the bf16 forward rebuild that R9 diagnosed, while per-sender and joint agreement held and every estimator gives bypass; SER is near the bar, with 44 of 100 instances individually at or above 0.50 and few pressure clusters behind the intervals; M_q uses free recompute, so self-repair would lower it, though M_S near 1 shows the estimator can reach 1; `t1.summary` inside `route_closure.json` still labels the forward estimator as the rule because the run predates R9. |
| status | reviewed |
| commit | 476c187 |
| evidence | docs/research/instructed-route/results/b1/b1_readings.json<br>outputs/_analyses/instructed-route-b1/far/Ct__leaf/far_v2/route_closure/route_closure.json<br>outputs/_analyses/instructed-route-b1/ser/Ct__leaf/ser_v2/route_closure/route_closure.json<br>outputs/_analyses/instructed-route-b1/far/Ct__leaf/far_v2/run_manifest.json<br>outputs/_analyses/instructed-route-b1/ser/Ct__leaf/ser_v2/run_manifest.json<br>docs/research/instructed-route/reviews/05-b1-review.md |
| report | docs/research/instructed-route/reviews/05-b1-review.md |

**T2 row**

| field | text |
|---|---|
| id | F-rte-006 |
| date | 2026-11-01 |
| direction | instructed-route |
| claim | Does the pressure reach the layer 17 quartet H24 to H27 at the option-token keys or at the final-token query on FAR and SER (B1 T2): at the query on both, because on the 100 held-out ids restoring the quartet's queries at the readout from the neutral twin moves 0.321 of the pressure effect on FAR (interval 0.302 to 0.344, clustered by pressure id) and 0.426 on SER (0.396 to 0.446), nearly all that the quartet's readout output carries (0.327 and 0.433), while restoring KV group 6's keys at the four option tokens moves -0.012 and 0.014 (r_Q minus r_K 0.333 and 0.412 against the 0.15 rule); the key arm does move single instances (mean absolute change 0.21 and 0.17 logits against 0.02 for the other layer 17 KV groups and random positions, exactly zero at the pre-clause mentions) but cancels in the mean, as do keys at every post-clause position (-0.019 and 0.006), values at the options (-0.012 and 0.000) and the reverse key arm (-0.008 and 0.019), whereas the reverse query arm reproduces 0.745 and 0.691; path patching puts the query signal in layers 14 and 15 (head.15.8 0.250 and 0.338, head.14.4 0.188 and 0.176), with layer 16 opposing (-0.074 and -0.095) and no upstream sender reaching 0.014 at the option keys. This replicates the synthesis's B-selector clause 1 on held-out ids under a frozen rule and differs from SDR, where F-sdr-012 found the grouped keys the main input. Caveats: queries and keys are patched before RoPE at aligned positions; no attention patterns were captured, so query-side says the clause changes what the final token asks for, not which positions it attends to; on FAR head.15.8 outranks head.14.4, unlike E11's selection-sample ordering for L17H24. |
| status | reviewed |
| commit | 476c187 |
| evidence | docs/research/instructed-route/results/b1/b1_readings.json<br>outputs/_analyses/instructed-route-b1/far/Ct__leaf/far_v2/route_closure/route_closure.json<br>outputs/_analyses/instructed-route-b1/ser/Ct__leaf/ser_v2/route_closure/route_closure.json<br>outputs/_analyses/instructed-route-b1/far/Ct__leaf/far_v2/run_manifest.json<br>outputs/_analyses/instructed-route-b1/ser/Ct__leaf/ser_v2/run_manifest.json<br>docs/research/instructed-route/reviews/05-b1-review.md |
| report | docs/research/instructed-route/reviews/05-b1-review.md |
