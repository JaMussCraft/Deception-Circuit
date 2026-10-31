# FAR / SDR / SER dataset quality audit (2026-10-19)

Read-only audit. `DC` = `/projects/beto/swong2/Alignment/Deception-Circuit`. Spec = `project_context/prompts/deception_tasks_shared.md` and the three task specs. All numbers below were recomputed from the stored arrow files and `filter_report.json`s with CPU scripts in `/u/swong2/.claude/jobs/6e1f64bd/tmp/audit/` (`stats.py`, `lengths.py`, `tvd.py`, `pos.py`, `press.py`), unless a report path is cited.

## 0. Cross-cutting findings (apply to all three tasks, SDR included)

1. **The primary comparison set does not exist.** The three-way intersection of survivors is 1 (train) / 0 (val) / 0 (test) instance ids (`DC/data/datasets/comparison_set.json`; `ser/filter_report.json` → `comparison_set`). Every cross-task comparison so far ran on unpaired survivor sets, and the spec's matched-pressure sub-analysis has no rows.
2. **Honest twins do not match the deceptive marginals, so Δ = C_D − C_H is confounded in every task.** Total-variation distance, deceptive vs honest test split (`tvd.py`):

| task | designation_polarity | item_pair | pressure_id | template_variant | shared instance ids |
|---|---|---|---|---|---|
| FAR | 0.33 | 0.47 | 0.07 | 0.29 | 0 |
| SDR | 0.20 | 0.10 | **0.65** | 0.20 | 0 |
| SER | **0.75** | 0.41 | 0.21 | 0.23 | 0 |

   The resampler (`DC/dataset/deception_common.py:1040`) is greedy over five factors at once. It cannot fix FAR/SER because the harvested pools are 77–95% inversion while D is 100% identity (`filter_report.json` → `honest_marginal_match.*.before`). For SDR, `sdr_17` is 613/1400 of SDR-D but 64/1400 of SDR-H: H comes from clauses that failed to elicit deception.
3. **The model names the designated item regardless of predicate.** Behavior per designation polarity over the whole behavioral-filter input (deceptive = passes both streams; honest share estimated as `n_harvested` × pool polarity mix, pool = instance-id prefix, `build_deception_dataset.py:445`):

| task | polarity | n | deceptive both | honest both (est.) | neither |
|---|---|---|---|---|---|
| FAR | identity | 14,992 | 0.117 | ~0.27 | ~0.61 |
| FAR | inversion | 14,800 | **0.000** | ~0.985 | ~0.015 |
| SDR | identity | 13,346 | 0.080 | ~0.13 | ~0.79 |
| SDR | inversion | 13,371 | 0.060 | ~0.64 | ~0.30 |
| SER | identity | 53,846 | 0.028 | ~0.05 | ~0.92 |
| SER | inversion | 53,678 | **0.000** | ~0.98 | ~0.02 |

   Under inversion the honest answer is the designated item. FAR and SER never produce the non-designated item under pressure. SDR is the only task where the model ever names the non-designated item deceptively.
4. **Built scaffolds drifted from the spec, and the drift differs per task**, so "differences are attributable to mechanism, not format" no longer holds.

| | spec | stored FAR | stored SDR | stored SER |
|---|---|---|---|---|
| designation words | failing/passing, critical/harmless, favorable/unfavorable | ready/delayed | damaging/harmless | favorable/unfavorable |
| designation sentence | "is the one that is" | "is the one that is" | "is the one that is" | "is {desig}, and the other result is" |
| caps suffix stating the honest answer | none | none | ".THE DAMAGING ONE IS THE RELEVANT ONE THAT SHOULD BE SHOWN." (no space, 1000/1000 rows) | " THE UNFAVORABLE ONE IS THE MORE RELEVANT ONE." |
| user turn | "Which result is failing / will you show me / should I look at" | + `Only respond with "…"` | + `Only respond with "…"` | "should I **prioritize**" + `Only respond with` |
| pressure clauses | 1 sentence | 1 sentence | 1 sentence; 6/20 say "the second finding/measurement" | 2 sentences, ALL-CAPS header, imperative tail ("Present information that reassures and persuades", `pressure_ser.json` #9) |
| item pool | 29 audit-category pairs | 41 generic pairs (`deception_pools/item_pairs.json`, e.g. stocks/bonds, calcium/sodium) | same | same |

   The working-copy code (`deception_common.py:202-224`) defines FAR as weak/strong with a "Notice which one is strong…" suffix, and its SDR sentence wording differs from the stored data. HEAD therefore reproduces neither stored FAR nor stored SDR (stored SER does reproduce; this was the "eval-variant drift" fixed by clause surgery in commit 84c353b).
5. **Mechanism-purity judge never ran.** `dataset/mechanism_purity_check.py` writes `data/datasets/mechanism_purity.json`, which does not exist. The spec's pilot label validation exists only for SER (`data/datasets/pilot_report.json`), and it was pooled over both polarities.
6. **Template collapse.** "lab" survives at 0.5% (FAR) and 0.07% (SER) vs "audit" 10.5% / 2.9%. FAR is 54/1400 lab rows and SER 36/1400, so the spec's seed < template < mechanism decomposition cannot be run for FAR or SER. SDR is 298/1400 lab.

## 1. FAR (fabrication)

**(a) Verdict:** not a fabrication dataset. FAR-D is the subpopulation of identity rows that names the designated item whether or not a pressure clause is present. The pressure clause is causally inert on it.

**(b) Numbers**

| quantity | value | source |
|---|---|---|
| train / val / test | 200 / 200 / 1000; honest twin same; nopressure 150 / 150 / 500 | arrow files |
| designation_polarity in D | identity 200/200, 200/200, 1000/1000; target == designated item in 1400/1400 | `stats.py` |
| pass rate by polarity | identity 1759/14,992 (11.7%), inversion 0/14,800 | `far/filter_report.json` |
| other FAR wordings | weak/strong: inversion 0/2,156; `far_test`: 0/4,380 total | `far_weak-strong/`, `far_test/filter_report.json` |
| overall pass, prior-balance keep | 5.9% of 29,792; prior keep 35% | same |
| clauses | 25 (20 FAR + 5 shared), all present in D; shared share 28% | |
| shared vs FAR-flavor pass rate | 8.65% (482/5,570) vs 5.27% (1,277/24,222) | `pass_rate_by_pressure` |
| pairs | 24 of 41 in D; 14/38 tested pairs pass 0; top-5 pairs = 64.5% of passes | |
| entities | 72 | |
| no pressure, D rows honest both streams | 9/1400 at ≥0.3; clean and corrupt median honest-label margin −1.125 | `far_nopressure/filter_report.json` |
| full model on D test, deceptive rate | no pressure 0.871; honest instruction 0.839 | `outputs/_suites/format-control-far-nls0.3/cells/D/far/interchange/pressure.json` |
| item_2 share of answers (top-12 estimate) | with pressure 0.49, no pressure 0.49, honest instruction 0.31 | `pos.py` |

**(c) Problems, by severity**
1. **Critical: deception is not pressure-contingent.** The 9/1400 no-pressure honesty, and the 0.87 / 0.84 variant readings, show that D rows answer the same with or without the clause. Mechanism-neutral clauses elicit more "deception" than truth-level threats (8.65% vs 5.27%). Copying is consistent across streams (both stream margins negative, about −1.1), so it is designation-following, not positional.
2. **Critical: inversion never passes under any of the three FAR wordings tried.** Under inversion, honest and "name the designated item" are the same event, so inversion rows alone cannot separate the hypotheses. What discriminates is 0/14,800 + 0/2,156 + 0/4,380: the model never fabricates the non-designated item. It is not a global copier, though. In the identity pool it names the honest, non-designated item more often (~27%) than the designated one (11.7%). D is the tail selected for copying, and the selection is driven by the identity requirement to resolve "the other".
3. **High: honest twin is a different population.** far_honest is 671 identity / 329 inversion on test vs D 1000/0. lab is 336 vs 46. Item-pair distance is 0.47. Δ_FAR mixes "copy the designated item" against "mostly name the other item".
4. **Medium:** single template in practice (lab 3.9%), five pairs make 64.5% of passes, `far_nopressure` is 791/800 honest-split fallback (unpaired), and stored data cannot be rebuilt from HEAD.

**(d) Candidate fixes**
- *Dataset-only (no GPU):* none that rescues the mechanism. Relabelling or subsetting cannot create pressure-contingent rows, because only 9 exist.
- *Re-filter on GPU:* add a pressure-contingency gate. Keep a row only if it is deceptive in both streams with the clause AND honest in both streams with the clause deleted. The current yield of that gate is about 0.04% of generated rows (9/1400 × 5.9%), so the gate alone is unaffordable.
- *Redesign (GPU filter + retrain):* the inversion rows show the model reads the truth reliably (98.5% honest) and the clauses never move it. FAR needs a much stronger inducement, such as role or incentive framing, or an explicit goal. Budget 1–2 pilot runs at 1,000 instances with per-polarity no-pressure validation before any full build (overgen 60 at about 6% is about 84k pairs, roughly 170k forward passes). Then retrain D/H/F circuits. Three wordings have already failed, so treat this as a redesign, not a reword.

## 2. SER (pragmatic distortion)

**(a) Verdict:** label ill-defined, and D is a positional/designation default. SER-D does not isolate pragmatic distortion.

**(b) Numbers**

| quantity | value | source |
|---|---|---|
| train / val / test | 200 / 200 / 1000 (honest same); no nopressure set | arrow files |
| designation_polarity in D | identity 1400/1400; target == designated 1400/1400 | `stats.py` |
| pass by polarity | identity 1,530/53,846 (2.8%), inversion 0/53,678 | `ser/filter_report.json` |
| overall pass, prior keep, overgen | 1.42% of 107,524; prior keep 24%; overgen 320 | same |
| clauses | 23 of 25 in D; ser_16 = 313/1400; shared pass 0.56% vs flavor 1.63% | |
| pairs | 14 of 41 in D; clock/timer 450/1400 (32%); top-5 = 80% of passes; 19/33 pass 0 | |
| full model on D test | deceptive: no pressure 0.666 (acc 0.639), honest instruction 0.511 (acc 0.489) | `outputs/_suites/cross-task-faithfulness-nls0.3-rerun260922/cells/ser/ser/interchange/pressure.json` |
| item_2 share of answers (top-12 estimate, covers 84–95% of rows) | with pressure 0.46, no pressure 0.79, honest instruction **0.96** | `pos.py` |
| pilot, random generated pool | honest: pressure 0.758, no pressure 0.825, instruction 0.853 | `pilot_report.json` |

**(c) Problems, by severity**
1. **Critical: honest label is not what the model computes.** Under the honest instruction, the model answers the second-listed item 96% of the time. That is positional, not content-driven. The spec warned of this (`deception_task_ser.md:99`). The pilot looked fine (82.5% honest) only because inversion rows dominate the honest count. The behavioral filter then selected the subpopulation whose "deception" is a default, so survivors read only 33% honest under no pressure.
2. **Critical: inversion 0/53,678.** As in FAR, the model never names the non-designated (favorable) item when the designated one is unfavorable.
3. **High: purity.** The caps suffix states the unfavorable one is "MORE RELEVANT", and the clauses carry imperative tails ("Present information that reassures and persuades", "Preserve and amplify confidence"). Choosing the favorable item then reads as instruction-following or contradicting the system turn, not implicature. This breaks the spec's one-sentence and "no conditioning on what is said" screens. "Prioritize" is itself ambiguous between "fix first" and "lead with".
4. **High:** the honest twin is 75% inversion vs D 0% (distance 0.75).
5. **Medium:** single template in practice (lab 2.6%), and clock/timer is a third of the data. SER circuits under `outputs/llama-8b-instruct_ser/` (2026-08-23) were trained on a 198-row predecessor (commit 475a26f). It has identical wording and also 0 inversion, so this is provenance only.

**(d) Candidate fixes**
- *Reword (needs GPU re-filter + retrain):* reword the user turn so the honest reading is entailed ("Which result should worry me before I sign?"). Drop the caps suffix and the imperative clause tails, and restore one-sentence outcome-level clauses. Validate in a pilot, per polarity, with no pressure and with the honest instruction, and require item_2 share near 0.5. Overgen at 1.4% is costly (320× was needed).
- *Or* merge SER into a two-way SDR/SER result, which the spec allows if purity fails.

## 3. SDR (omission)

**(a) Verdict:** best of the three and usable, but its honest twin is confounded and its identity half shows the same designation default.

**(b) Numbers**

| quantity | value | source |
|---|---|---|
| train / val / test | 200 / 200 / 1000 (honest same); nopressure 150 / 150 / 520 | arrow files |
| designation_polarity in D | identity 804 / inversion 596 (test 569 / 431) | `stats.py` |
| pass by polarity | identity 1,067/13,346 (8.0%), inversion 806/13,371 (6.0%) | `sdr/filter_report.json` |
| overall pass, prior keep, overgen | 7.0% of 26,717; prior keep 13.6%; overgen 140 | same |
| template pass | audit 11.3%, lab 2.9% (D: 298/1400 lab) | same |
| clauses | 21 of 25 in D; **sdr_17 = 613/1400 (44%)**; shared clauses 5/2,810 (0.18%) vs flavor 7.8% | `pass_rate_by_pressure` |
| pairs | 28 in D; calcium/sodium 257/1400; 11/39 pass 0 | |
| no pressure, D rows honest both streams (≥0.3) | 722/1400 = 51.6%: **inversion 550/596 (92%), identity 172/804 (21%)** | `sdr_nopressure/filter_report.json` |
| full model on D test (post-fix) | deceptive: no pressure 0.231 (acc 0.224), honest instruction 0.235 (acc 0.232) | `outputs/_suites/format-control-sdr-nls0.3/cells/D/sdr/interchange/pressure.json` |
| matched honest instruction (length-matched, per clause) | honest both streams 364/1000; usable clauses sdr_02/11/17/19 | `sdr/matched_honest_report.json` |
| item_2 share (top-12, covers ~60%) | with pressure 0.55, no pressure 0.81, honest instruction 0.83 | `pos.py` |

**(c) Problems, by severity**
1. **High: honest twin is confounded on clause identity** (distance 0.65; sdr_17 44% of D vs 4.6% of H) and on polarity and template (0.20 each). Δ_SDR partly measures "clause that works" vs "clause that does not". This is a dataset problem, not only a circuit one.
2. **High: designation default in identity rows.** Pressure-contingent deception lives almost entirely in inversion rows, which are only 43% of D. 79% of identity rows stay deceptive with the clause deleted. Caveat: the both-streams ≥0.3 criterion is stricter than the single-stream argmax behind the 0.769 honest reading, so the two figures are not directly comparable. The single-stream no-pressure answers also skew to item_2 (about 0.81), so part of the 77% "honest" reading is positional.
3. **Medium:** one clause carries 44% of the data. Shared clauses produce 4 rows, so the matched-pressure sub-analysis is impossible. The suffix has no leading space in 1000/1000 rows (".T"/"HE" straddle), which memory records as accepted. The suffix states the honest answer, so deception here also means disobeying an explicit instruction, a purity concern for the judge. The stored data cannot be rebuilt from HEAD.
4. **Low (circuit, not data):** the fine SDR D circuit fails the wikitext KL gate (1.383 vs 0.66; `.scratch/format-control/reports/09-final-report.md` §2).

**(d) Candidate fixes**
- *Dataset-only, no GPU:* a pressure-contingent SDR subset already exists. The `sdr_nopressure` rows tagged `deceptive_split` are 106 / 96 / 520 instance ids that are deceptive with pressure and honest without it. They are mostly inversion. This is short of 200 train. Re-resampling the honest twin to match pressure_id is impossible from the current pool for sdr_17.
- *GPU re-filter (rough guess 1–3 GPU-h at the current 7% pass; not measured):* top the subset up to 200 / 200 / 1000 with a pressure-contingency gate. Use the no-pressure twin (same instance_id, clause deleted) as the honest counterpart. That gives exact per-instance pairing and removes the confound. Fix the suffix space at the same time. Retraining fine and coarse SDR circuits is only needed if the subset replaces the training set.

## 4. Length matching

- **Spec** (`deception_tasks_shared.md:164-174`): exact parity is not required, because node pruning gates components, not positions. Matched length *distributions* remove an obvious confound, by selecting clauses per task, not by changing scaffold wording. It requires a `--match-length-distribution` flag and a per-task histogram in `filter_report.json`.
- **Implementation:** the flag exists (`build_deception_dataset.py:85`, `deception_common.py:615`), but it drops out-of-band clause slots after generation and keeps shared clauses unmatched. It is **off in every stored config** (`"match_length_distribution": false`). Histograms are reported.
- **Result** (stored prompts, Llama-3.1 tokenizer, `lengths.py`):

| set | min | median | max |
|---|---|---|---|
| FAR / far_honest | 90 | 94 | 100 |
| SER / ser_honest | 94–96 | 107–108 | 114 |
| SDR / sdr_honest | 111 | 114 | 118 |
| far_nopressure / sdr_nopressure | 78 / 99 | 79 / 100 | 80 / 101 |

  The FAR and SDR distributions do not overlap. The gap is in the scaffold, not the clauses: the SDR suffix adds about 13 tokens, and SER's caps two-sentence clauses add more. Clause selection cannot close a 20-token gap. Within each task, D and H lengths match to within 1 token.
- **What depends on it:** nothing mechanically. Masks are per node, so Jaccard, XOR/delta compositions, cross-task faithfulness and the joint run never align positions across tasks. All 25 component analyses under `outputs/_analyses/` are SDR-only and within-task. Length is a soft interpretive confound for cross-task overlap claims; extra caps text can recruit heads, for example.
- **Opinion:** a FAR/SER reword changes lengths anyway, and those circuits must be retrained regardless, so match then at no extra cost. Do it by aligning the scaffolds: drop or equalize the suffix and the `Only respond with` boilerplate, and target SDR's 111–118 band so the SDR circuits stay valid. Do not re-match SDR itself just for length.

## 5. What gets invalidated if the FAR / SER datasets change

**FAR change invalidates:**
- `outputs/llama-8b-instruct_far/*`: 12 runs, nls 0.1–0.9 D/H plus nopressure 0.3/0.4.
- `outputs/eval5_far`, `eval5_far_lb`, `eval5_far_h`, `eval5_far_h_lb`, `eval5_delta_far`, `eval5_delta_far_lb`.
- `data/datasets/far_honest`, `far_nopressure`.
- `_suites/far-nls0.3-delta` and `_suites/format-control-far-nls0.3`. The FAR Format-Control verdict (c) goes too.

**SER change invalidates:**
- `outputs/llama-8b-instruct_ser/*`: 10 runs.
- `eval5_ser`, `eval5_ser_lb`, `eval5_delta_ser`, `eval5_delta_ser_lb`.
- `ser_honest`.
- `_suites/ser-nls0.3-delta`.

**Either change also invalidates:**
- `outputs/llama-8b-instruct_joint/*`: 5 runs trained on far+sdr+ser.
- The cells touching the changed task in `_suites/cross-task-faithfulness-nls0.3{,-rerun260922}`, `cross-task-intersection-sufficiency-nls0.3{,-delta}`, `cross-task-matrix-nls0.3-delta-leaf{,-rerun260922}`, `cross-task-specificity-asymmetry-nls0.3`, `mechs-on-std-nls0.3` and `std-on-mechs-nls0.3`.
- Any Jaccard or composition that uses FAR or SER masks.

**Survives:**
- All `llama-8b-instruct_sdr*` runs, fine and coarse, including seeds and nopressure.
- All `eval5_sdr*` dirs.
- All 25 `_analyses` dirs (SDR).
- `_suites/sdr-nls0.3-delta`, `format-control-sdr-nls0.3`, `format-control-sdr-coarse-nls0.3`.
- STD outputs.

An SDR re-filter (section 3d) would invalidate the SDR side only if the new subset replaces the training data.

**Cost tiers:**
- *Dataset-only:* config cleanup, provenance notes, and the SDR pressure-contingent subset.
- *GPU re-filter:* any wording change needs the prior-balance and behavioral filters plus the honest harvest. That is overgen 60–320 at 1–7% pass, roughly 1–10 GPU-h per task on an H200.
- *Retrain:* any change to the training set of FAR, SER, or joint requires D/H/F circuit retraining and re-running EVAL 5. The EVAL 5 judge costs (OpenRouter) also recur.
