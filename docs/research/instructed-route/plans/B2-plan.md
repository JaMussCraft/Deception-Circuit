# B2 plan: the falsity signal and the cross-task question

Written Sun 1 Nov 2026 by the B2 planning agent (Opus), session claude-230e4716, under the frozen `spec.md`. Paths are
under W = `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route` unless absolute.
`docs/research/held_out.json` lists no sets. Open questions are in `reports/02-handback.md`.

## 0. Shared facts (checked on the login node, 2026-11-01)

- **Answer convention.** Prompts end at the answer slot ("The result that is failing is"), the Readout. `target` and
  `distractor` are single tokens. The `_honest` twin swaps them, so readings map tokens to items through D's record.
- **Sizes.** far/ser/sdr_v2, their `_honest` twins and `_nopressure` (F) have train 200, validation 200 and test 1,000
  on shared ids. `far_v2_inversion` has 210 test rows and `ser_v2_inversion` 249. `sdr_v2_inversion_reported` holds
  the 618 reported-wish rows of F-mech-012, from 20 D clauses and 41 I clauses. Every D row carries
  `honest_instruction_clean_prompt` (HI), an honest operator instruction.
- **Overlaps.** FAR train and validation ids share no id with SER test. 11 of FAR's 12 test clauses also occur in train.
  57 of the 618 ids lie in SDR's held-out sample.
- **Gaps.** `analyze_components.py` writes no `run_manifest.json`, and every mechanism-analysis ledger row has
  `manifest_hash: null` (T1). mgnp has neither sklearn nor scipy, so new code uses numpy and torch only.
- **Sample ids.** The selection sample (seed 0) is in `outputs/_analyses/mechanism-analysis-p1/s1/U__leaf/<task>_v2/sample.json`,
  local and untracked. The held-out sample (seed 1) is in `docs/research/mechanism-analysis/phase1/groups/<task>_heldout_D_sample.json`.
  T3 copies both into `docs/research/instructed-route/groups/`.

## 1. P1, the falsity probe

**Question.** Does a direction that separates FAR D (literally false answer) from FAR H at the Readout also separate SER D
from SER H, where both options are literally true and D's answer only misleads?

| role | rows (all captured in job P1-cap) | used for |
| --- | --- | --- |
| fit | far_v2 train, 200 ids x {D, H} | probe weights only |
| select | far_v2 validation, 200 ids x {D, H, HI} | layer and C only |
| FAR gate | far_v2 test minus seed-0 and seed-1 ids (800) x {D, H, HI, F}, plus FAR I minus sample ids | 0.75 FAR condition, controls |
| SER test | ser_v2 test minus seed-0 and seed-1 ids (800) x {D, H, HI, F}, plus SER I minus sample ids | the rule number, controls |
| SDR | sdr_v2 test minus both samples (800) x {D, H}, plus the 618 I-reported rows | descriptive, links to P2 |

Fitting and selection never see a SER, SDR or FAR-test row, and B1's held-out sample is never touched.

**Probe.** The Readout residual, rows 0 to 32 (row l+1 follows layer l), fp16, standardised on the fit split. L2 logistic
regression (D = 1, H = 0), float64 torch LBFGS, C in {1e-3, 1e-2, 1e-1, 1}. A mass-mean direction is descriptive.

**Selection (pre-registered, FAR only).** On the select split the score is the AUROC of D against the pooled H and HI
rows. That penalises an instruction detector without ever training on HI. Layers 4 to 31 are eligible. Ties within
0.005 go to the layer nearest 17, where D's lens margin first exceeds +0.5 on all three tasks (synthesis E16). The SER
AUROC at every layer is reported and decides nothing.

**FAR gate.** If the AUROC of D against H on the FAR gate rows is below 0.75, P1 reports the per-token DLA alone.

**Rule number.** The AUROC of SER D against SER H at the selected layer, oriented with FAR D positive. The frozen bands
apply to the point estimate. The 95% CI uses 2,000 resamples clustered by `pressure_id` (17 SER clauses), seed
20261101, and a CI crossing a band edge is flagged. An AUROC under 0.5 falls in the literal-falsity band as written and
is flagged as anti-aligned.

**Controls.** Each AUROC is a cell's rows against their own H twins at the selected layer. Predicted values:

| cell against H | literal-falsity probe | misleadingness probe | clause or instruction detector |
| --- | --- | --- | --- |
| SER D | under 0.6 | 0.75 or more | high |
| FAR I (false, transparent, nobody misled) | high | low | high |
| FAR HI and SER HI (honest instruction) | low | low | high if it reads any instruction |
| SER I (true, transparent) | low | low | high |
| FAR F and SER F (no clause) | about 0.5 | about 0.5 | about 0.5; anything else means a broken probe |

HI rows are kept only when `h_honest_instruction_clean` >= 0.3 (the twin's bar), and the kept share is reported.
A misleadingness verdict is clean only when FAR I and both HI cells are under 0.6. If the controls match the detector
column, the verdict is reported as "instruction-confounded" (open question 1). Two further checks are reported. One is a
permutation null of 200 refits with D and H labels swapped within random instance pairs, scored on SER. The other is
leave-one-clause-out AUROC over FAR train and validation.

**Per-token readout (always run).** Each row stores the two items' final logits (raw, log-softmax, vocab-centred) and
each Component's direct attribution to each token separately, via `component_analysis/dla.py:424` gathered at the two
ids and centred on the mean unembedding row. The contrasts are D minus H on the honest item (suppression) and on the
deceptive item (promotion), with clustered CIs, for the whole model, the quartet, C6's late heads, mlp.30 and mlp.31.
FAR against SER on these two numbers is review A's knows-versus-says reading.

## 2. P2, the SDR wish test

**Rows.** The 618 rows of `data/datasets/sdr_v2_inversion_reported`, paired by id with `sdr_v2_honest`. The same ids
also run on SDR D (`sdr_v2`) as the pressure reference. The 57 ids shared with SDR's held-out sample stay in, because
nothing is selected on them and B1 reads only FAR and SER. A sensitivity row drops them.

**Wish effect.** Per instance, m_I is logit(I target) minus logit(I distractor) on the wish prompt, and m_tw is the same
difference on the twin. From the dataset, mean m_I is 3.15 and mean m_tw is -2.92, so the gap is about 6.07 logits. With
m_KO the margin after the knockout, f_wish = (mean m_I - mean m_KO) / (mean m_I - mean m_tw). This ratio of means has the
shape of R-AB's f_D. **Rule:** the wish runs through the route when the quartet's f_wish is at least 0.5. CIs use 2,000
resamples clustered by `instructed_inversion_id` (41 clauses), with a second set clustered by `pressure_id` (20).

**Ablation.** A neutral-twin interchange of the outputs of L17H24 to L17H27 (`--knockout-counterfactual neutral_twin`,
scheme `interchange`). Mean ablation is ruled out by L15: its bank comes from pressure prompts and is broadcast to every
position, so on wish rows it would inject D's pressure into the quartet. Zero ablation also removes the quartet's
ordinary answer work (A2) and would overstate the share. The twin interchange feeds the quartet what it computes when
the wish clause becomes a token-matched neutral sentence. It is the counterfactual that defines the gap, as in R-AB.

**Positions.** Primary: `all`, the default, which covers the clause span and the Readout where the quartet is query-fed
(F-mech-007). Runs at `readout` and `after=pressure_clause,exclude=readout` locate the effect and decide nothing.

**Controls (same ids and positions).** 20 layer-matched random quartets of distinct L17 heads outside H24 to H27 use
seeds 20261101 + i. The 7 other L17 KV groups (heads 4g to 4g+3, g not 6) are matched in structure, since the quartet
is exactly KV group 6. L17H24 alone gives context for F-sdr-002. f_wish is reported beside the largest null of each
kind, and a null reaching 0.5 makes the verdict "not quartet-specific" (open question 2). f_D(quartet) on the same ids
shows whether the wish and the instruction share the route.

## 3. P3, the SER MLP replication

**What F-mech-009 measured.** `docs/research/mechanism-analysis/phase1/rcls.csv` comes from the item-swap sweeps S1 (D),
S5 (H) and S6 (F): selection sample, n = 100, seed 0, all positions, U binding, H100 job 49825318. For Component c and
test set X, d_c(X) is the knockout drop over X's clean margin, in X's own direction: deceptive on D, honest on H and F. A
drop is significant when it is at least 2 SE and at least 0.01 logits. U_HF is the maximum over H and F of
max(d + 1.96 SE(d), 0). "Deception-leaning" means d(D) significantly positive and d(D) >= 2 U_HF, once "opposes" and
"shared" are ruled out (`outputs/_launch_mechanism_analysis/p1_readings.py:36`). SER gave 0.239, 0.203 and 0.175.

**Held-out ids.** Run A is seed 1, the mechanism-analysis held-out sample. Run B is seed 2, drawn on CPU by T3 with
`sampling.draw_sample` with seeds 0 and 1 excluded. D, H and F all take `--include-ids` of the tracked id file.

**Cells.** Per run and task there are three `--knockout-groups` invocations with `--knockout-singles off`, all item-swap
at every position, on D, H and F. The groups have one member each: mlp.11, mlp.13 and mlp.16 under test, mlp.30 and
mlp.31 (C-MLP's shared pair), and mlp.0 as positive control (d about 1.9). `knockout/groups.json` holds `mean_drop`,
`standard_error` and the clean margin per group, which is all R-cls needs. SER is required. FAR and SDR cost seconds
and test "SER alone" (open question 3).

**Baseline.** The job reruns seed 0 on SER. mlp.11, 13 and 16 must reproduce `rcls.csv`'s d(D), d(H) and d(F) within
0.01 and keep their class. A miss means a pipeline change or a groups-against-sweep path difference.

**Rule.** An MLP replicates when R-cls calls it "deception-leaning" on SER in both runs and each run directory has a
`run_manifest.json` with a 40-hex `git_commit`. The result is a new FINDINGS row that supersedes `pre-manifest` F-mech-009.

## 4. Jobs and cost (Delta; Bridges-2 not needed)

On Bridges-2 H100 the model loaded in 563 to 619 s, a group knockout on 100 instances took about 0.49 s (job 49830654)
and a 1,056-Component sweep about 500 s (job 49825318). H200 matches H100, and an A40 is about 5x slower. Use
`gpuH200x8-interactive`, then `gpuA100x4-interactive` (inference fits in 40 GB). Every job fits the 1-hour cap.

| job | content | closest prior job (observed) | expected | reserved |
| --- | --- | --- | --- | --- |
| P1-smoke | 64 rows per cell, checks only | 1B lens cell, 48 s plus 563 s load (49825318) | 12 min | 0.5 h |
| P1-cap | about 10,900 rows, residual and per-token DLA | same, scaled | 20 min | 0.75 h |
| P2 | 618 ids x 2 conditions x 3 position sets x 30 groups | 1C-b, 1,835 s for 3 tasks with load (49830654) | 20 min | 0.75 h |
| P3 | seeds 0, 1, 2 x 3 tasks x {D, H, F} x 6 groups | heldout_h, 21 groups x 100 in 13 s | 13 min | 0.5 h |
| contingency | one rerun each of P1-cap, P2 and P3 | - | - | 2.0 h |
| **total** | | | **about 1.1 h** | **4.5 of the 15 GPU-h cap** |

The probe fit and every reader run on the login CPU. Reservations and actual hours go into `ledger.json` through
`research-session`.

## 5. Code: what exists and what is built

| piece | exists | invocation or gap |
| --- | --- | --- |
| group knockouts, twin interchange, positions | `component_analysis/knockout.py` via `analyze_components.py` | `python analyze_components.py batch FILE --timings T` with `--knockout-groups`, `--knockout-singles off`, `--knockout-counterfactual`, `--knockout-positions`, `--seed`, `--include-ids`, `--exclude-ids` |
| fixed-scale DLA | `component_analysis/dla.py:395-475` | target minus distractor only; T5 adds per-token columns |
| Readout residual | `component_analysis/hooks.py:490`, `capture_forward(..., positions=readout)`, `Capture.residual` [batch, 33, hidden] | reused by T6 |
| batches per split | `component_analysis/dataloaders.py:499`, `descriptive_batches(dir, tok, task=, split=)` | HI rows built from the record in T6 |
| R-cls | `outputs/_launch_mechanism_analysis/p1_readings.py:20-62`, untracked | ported in T4 |
| I-reported condition | missing: `TWINNED_CONDITIONS` (`dataloaders.py:82`) and `instances.dataset_dir` know only `inversion` | T2 |
| run_manifest.json | training runs and suite cells only | T1, and T6 for the capture |
| linear probe | none (`scripts/sdr_cue_probe.py` is a behavioural panel) | T6, T7 |

## 6. Tickets (one Opus implementer each, test-first, both interpreters, `-p no:cacheprovider`)

**T1. Provenance in analyze_components.** `analyze_components.run` calls `run_manifest.write_run_manifest(cell, argv=...,
seed=cli.seed, model=..., dataset_files=...)` once per cell, wrapped like `run_io.write_run_provenance` so a failure
never stops a run. It is skipped under `--dry-run`, and each batch line passes its own argv. Tests in
`tests/test_analyze_components_run_manifest.py` assert that a fake-model run writes the file with the invocation's argv
and seed. `DC_RUN_MANIFEST_GIT=0` must record `git_fingerprint_error: "disabled"`. A rerun with other argv writes
`run_manifest.1.json`, two batch lines write two manifests, and a dry run writes none.

**T2. The `inversion_reported` condition.** Add it to `TWINNED_CONDITIONS`, make `instances.dataset_dir` resolve
`<data>/<task>_inversion_reported`, and check `tasks/deception.py:30`. A generator writes the stand-in
`outputs/_launch_instructed_route/standins/sdr_v2_inversion_reported/config.json`, the `sdr_v2_inversion` stand-in with
`deception_condition` changed. Tests in `tests/test_inversion_reported_condition.py` assert that the directory resolves
and `neutral_twin_reason` returns None. A two-row fixture must build aligned `NeutralTwinPair`s, and `inversion` must be
unchanged. Login check: a `--dry-run` on the stand-in with the 618-id file reports 618 instances, all twinned.

**T3. Id and group files.** `scripts/instructed_route_b2_inputs.py` writes `groups/sdr_wish_ids.txt` (618 ids), the
seed-0 and seed-1 id lists, a CPU seed-2 draw per task, `p2_groups.json` and `p3_groups.json`. Redrawing seed 1 must
reproduce the tracked held-out ids.
P2's file holds the quartet, L17H24, seven `kvg_<g>` and `null_d00` to `null_d19`. P3's holds six one-member MLP groups.
Tests in `tests/test_instructed_route_b2_inputs.py` assert that the 618 ids equal the dataset's and are unique, and that
the quartet is `[["head",17,h] for h in 24..27]`. The 20 nulls must be distinct L17 quartets outside 24 to 27 and
identical across calls. The KV groups must be 7 disjoint runs of 4, and each union must be exact.

**T4. R-cls port and readers.** `component_analysis/rcls.py` ports `significant_sign` and `rcls` unchanged.
`scripts/instructed_route_b2_read.py p3` writes `results/p3_rcls.csv` and the verdict. Its `p2` subcommand reads
`groups.json` and `groups_instances.json` and writes f, clustered CIs, the null maximum and the verdict. Tests in
`tests/test_instructed_route_b2_read.py` assert that a golden fixture reproduces `rcls.csv` class and d to 1e-9. The
fixture is the seed-0 sweep entries of SER mlp.11, 13 and 16 and FAR mlp.13, extracted on CPU from
`outputs/_analyses/mechanism-analysis-p1/s{1,5,6}`. f must be 1 when the knockout equals the twin and 0 when it equals
the clean margin. 0.5 passes and 0.4999 fails. The bootstrap resamples clusters and is seed-deterministic, and a run
without a manifest reads "not yet verified".

**T5. Per-token DLA.** Add `component_token_logits(model, capture, keys, token_ids, centre=True)` to `dla.py`, returning
[batch, k, n_tokens] from the gathered unembedding columns plus the mean row only. Tests in `tests/test_dla_model.py`
assert that the column difference equals `component_logit_difference`. The sum over all senders and the embedding must
equal the model's centred logit per token, and centring must cancel a shift added to every unembedding row.

**T6. Capture entrypoint.** `scripts/falsity_probe_capture.py --plan PLAN.json --output-dir DIR [--dry-run]
[--max-rows N]`. The plan lists cell name, dataset directory, split, id file and prompt field. Per cell it writes
`rows.<cell>.jsonl` (ids, clauses, item token ids, model and dataset margins), `resid.<cell>.pt` ([n, 33, 4096] fp16)
and `tokens.<cell>.pt` (item logits in three forms, per-token DLA for every head, MLP and the embedding). It also writes
`run_manifest.json`. HI rows encode `honest_instruction_clean_prompt` with the same `_encode`. Tests in
`tests/test_falsity_probe_capture.py` use a fake tokenizer and model. They assert that counts and ids match the plan and
that H rows map the target to the honest item. The HI Readout must be the prefix length minus 1, with the right residual
shape. `--dry-run` loads no model and fails on a missing id, and the manifest is written.

**T7. Probe fit and score (CPU).** `scripts/falsity_probe.py fit|score|read --capture DIR` uses numpy and torch only. It
does standardisation, LBFGS logistic regression, the mass-mean variant and Mann-Whitney AUROC with ties. It also runs the
clustered bootstrap, the permutation null, leave-one-clause-out and select-split selection, and writes
`results/p1_probe.json`. Tests in `tests/test_falsity_probe.py` assert AUROC against hand values with ties, 1.0 when
separable and 0.5 when equal. The fit must recover a planted direction (cosine above 0.9), and selection must raise on
any SER or FAR-test row. The bands split at 0.75, 0.7499, 0.6 and 0.5999, and the fallback flag sets below a 0.75 FAR
gate. The bootstrap is seed-deterministic, and the module imports without sklearn or scipy.

**T8. Job files and wrapper dry run.** Write `jobs/B2-p2.batch`, `jobs/B2-p3.batch`, `jobs/B2-p1-plan.json` and
`scripts/jobs/run_b2_capture.sbatch`. P2 and P3 run through `scripts/analyze_components.sbatch` with `batch` and
`--timings`, and every `--include-ids` line sets `--n-causal 1000` so the default of 100 cannot subsample. Before any
submission, run from W both `--dry-run`s, `bash -n` on each wrapper and `sbatch --test-only` with `--time`, after
`mkdir -p logs`. The dry runs must show 618 twinned instances (P2), equal D, H and F ids (P3) and the
planned per-cell counts (P1).

**Order.** T1 to T5 run in parallel, T6 needs T5, and T7 needs only T6's file format. P2 follows T1 to T4 and T8, P3
follows T1, T3, T4 and T8, and P1 follows T1, T5, T6, T8 and P1-smoke. Failures are compared by name to the baseline.

## 7. Execution evidence each run must produce

P1's unablated D margins must reproduce the dataset `clean_margin` within a mean absolute difference of 0.05. P2's mean
clean I margin must be 3.15 and mean twin margin -2.92, each within 0.05, with n = 618. P3's seed-0 reproduction must
hold. Every output root needs a manifest with a 40-hex commit.

## 8. Risks, and what each result means for knows-versus-says

1. **Top risk: P1 can pass for the wrong reason.** D and H differ only in the clause, and clause readers in layers 7 to 14
   carry that difference to the Readout on every task (H5, H6, B2). A FAR probe can be a clause or instruction detector
   and still put SER at 0.75 or more. The HI-penalised selection and the control table are the defence. If the controls
   show the detector pattern, P1 is reported as instruction-confounded and the per-token DLA carries the reading.
2. **Saturation.** D against H may sit near 1.0 at most layers. The SER curve shows whether the verdict depends on the layer.
3. **Twin alignment on I-reported.** Clause surgery may fail on some of the 618 rows. T2's dry run catches it.
4. **Self-repair (L24).** Downstream Components may make up for the patched quartet, so f_wish is read against
   f_D(quartet). F-sdr-002 already found quartet restoration incomplete on SDR.
5. **P3 noise.** With n = 100, ser mlp.11 has d(D) 0.239 against d(H) 0.059, near the factor-two bar. Seeds are never
   pooled to rescue a failure.
6. **Collisions with B1.** B1 may edit `knockout.py` or `analyze_components.py`, so the orchestrator should land T1 first.

| result | meaning for knows-versus-says |
| --- | --- |
| P1 misleadingness, FAR I and HI under 0.6 | the deviation signal tracks misleading the asker, not propositional truth: the model knows the non-misleading answer and says the other |
| P1 literal falsity, FAR I high | the FAR signal is propositional; SER deception runs as an option choice without it |
| P1 detector pattern | nothing beyond the cue-routing account; the per-token readout decides |
| SER D suppresses the honest item against H | the honest answer is computed and overridden; pure promotion means no override step |
| P2 f_wish 0.5 or more | the quartet routes any stated preference: a selector, not deception machinery |
| P2 under 0.5 | the wish takes another path |
| P3 replicates / fails | a real SER-specific MLP stage (the H11 sign) / F-mech-009 was sample noise and H11 stays inconclusive |
