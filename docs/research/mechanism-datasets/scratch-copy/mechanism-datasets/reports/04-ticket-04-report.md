# Ticket 04 report: purity judge, full v2 build, reproducibility (2026-10-20 to 2026-10-21)

**Outcome: `far_v2`, `sdr_v2` and `ser_v2` are built, each with its `_honest` and `_nopressure` twin.**
- Sizes are 200/200/1000 with identical instance ids and row order across D, H and F.
- Purity is construction-based (spec §14.G11, user decision 2026-10-21). Every row passes its construction check.
- The reproducibility test re-renders every stored prompt byte for byte.
- The cross-task D-prompt band is 12 tokens and the median gap is 5.
- The three-way comparison set holds 5 / 0 / 8 rows (train / validation / test).
- The LLM-judge purity gate failed and is recorded as a limitation (section 2).

Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`, branch
`mechanism-datasets`. No git was run by the implementer; the orchestrator committed the diagnostics code as c18a8ef.

## 1. Built datasets (`data/datasets/`)

| task | cell | cap_used | instances scored | prior kept | deceptive given prior kept | contingent given deceptive | full-build given contingent | full-build survivors |
|---|---|---|---|---|---|---|---|---|
| far_v2 | r8_far_strong_on | 0.15 | 205,000 | 0.42 | 0.145 | 0.993 | 1.00 | 12,428 |
| sdr_v2 | r9_sdr_unified_on | 0.10 | 61,668 | 0.31 | 0.534 | 0.840 | 0.857 | 7,425 |
| ser_v2 (B) | r9_ser_unified_on_B | 0.15 | 114,224 | 0.32 | 0.196 | 0.796 | 0.848 | 4,866 |

- **Selection.** Every split holds exactly 25% per (designation polarity x item polarity) stratum and 12.5% per
  stratum x template variant: audit 100 / lab 100 in train and validation, 500 / 500 in test. The
  `instance_id_order` strategy filled every split.
- **Caps.** The clause cap binds in every split and is never exceeded: FAR and SER 30 / 30 / 150, SDR 20 / 20 /
  100. The largest item-pair counts are below the cap. `cap_used` comes from the pilot selection and is recorded,
  with its reason, in each `filter_report.json`.
- **Overgeneration.** The plan was 1.3 x the pilot's `n_generate`. It was capped at what 200/200/1000 needs (lead
  instruction 2026-10-21): FAR test scored 140,000 of 162,500 instances and SDR test 40,000 of 54,168. Every other
  split was scored in full. The filter reports count only what was scored.
- **Shortfall.** There was none. No top-up was used.
- **Pilot match.** The train list starts with the pilot's instance list, and the build reproduces the pilot's
  contingent survivors exactly: FAR 71/71, SDR 133/133, SER 70/70, none extra.
- **Construction checks (§14.G11).** All 1,400 selected rows of each task pass. So do all full-build survivors:
  FAR 12,428, SDR 7,425, SER 4,866.
  - FAR: the target contradicts the record.
  - SDR: the target is the harmless item, a true disclosure commitment.
  - SER: `ser_literal_truth_violations` is empty in every stream and condition.
- **Honest instruction on the selected rows** (stored as columns): FAR accuracy 1.00, item_2 share 0.50; SDR 0.90
  and 0.41; SER 0.99 and 0.51.
- **Unexpected argmax tokens.** FAR 0, SER 0. SDR had 9 across all conditions (2 pressure, 6 neutral, 1 honest
  instruction) over 61,668 instances.
- **Margin 1.0 re-application** (report only; the full-build counts at margin 0.7 are in the first table):
  FAR 10,645, SDR 7,095, SER 3,938.
- **Shared clauses** (slots 20-24) produced no contingent survivor in any task, as in the pilot. The matched-pressure
  subset is therefore empty.

Prompt lengths in tokens, median (min-max):

| task | D | H (neutral twin) | F (nopressure) | honest instruction | prior |
|---|---|---|---|---|---|
| far_v2 | 97 (94-101) | 97 (94-101) | 86 (84-87) | 99 (97-100) | 89 (86-93) |
| sdr_v2 | 102 (98-106) | 102 (98-106) | 90 (88-91) | 103 (101-104) | 94 (90-98) |
| ser_v2 | 102 (96-104) | 102 (96-104) | 89 (87-90) | 102 (100-103) | 94 (88-96) |

- The maximum is 106, within the 120-token limit.
- The cross-task D band is 94-106, width 12, which meets the G6 limit of 12. It was met by the pre-registered
  window 94-106, which excluded no instance and no clause.
- The median gap is 5 (limit 6).
- H lengths equal D lengths row by row; the neutral twin is asserted clause-aligned.
- The comparison set and the band check are in `data/datasets/comparison_set_v2.json`.

Each D directory holds `dataset_config.json`, `filter_report.json` (every Required-reports statistic, per-stage and
per-stratum counts, pass rates by clause, pair, entity, domain and variant, margin and prior histograms, length
histograms per condition, construction checks, compute) and `provenance.json`. H and F hold `dataset_config.json`:
H `honest_twin_kind: neutral_clause` with margin 0.3, F `nopressure` with margin 0.3.

## 2. Mechanism purity: construction-defined, with the LLM-judge results as a limitation

| task | v1 gate (Sonnet, label first, clause visible) | v2 Sonnet (clause removed, reason then label) | v2 Gemini 2.5 Pro | v2 kappa |
|---|---|---|---|---|
| FAR | fabrication 0.54, fail | fabrication 1.00, pass | fabrication 1.00, pass | 1.00 |
| SDR | omission 0.20 (59 refusals), fail | omission 0.17, fabrication 0.72 (5 refusals), fail | omission 0.56, pd 0.41, fail | 0.00 |
| SER-B | pd 0.73, pass | pd 0.36, fabrication 0.60, fail | pd 0.21, fabrication 0.66, fail | 0.08 |

- **Clause form.** Splitting by clause form did not explain the v1 failure: SDR relational omission is 0.53 against
  act-naming 0.43 of answered rows. Reverting SDR to `r5_sdr_rule_on` is not supported.
- **Why SDR and SER fail.** Both judges read SDR and SER answers as contradicting the suffix sentence ("the
  critical/unfavorable one matters most here"), and many call them fabrication.
- **Where it is recorded.** Details: `reports/purity-hard-stop.md` and `reports/04-purity-diagnostics.md`. The
  limitation and the judge summaries, with their sha256, are recorded in each `provenance.json`
  (`mechanism_purity`) and in each `filter_report.json`. CONTEXT.md has the entry "Mechanism purity (v2)". Spec
  §14.G11 records the decision.

## 3. Code (all new; no existing file edited except CONTEXT.md, additively)

- **`dataset/mechanism_purity_v2.py`.** The v1 judge reused unchanged, seeded sampling, a partial log per call,
  the §8.1 verdict and §14.G4 wording selection.
- **`dataset/purity_judge_v2.py`.** Judge v2: clause removed, reason then label, two raters, refusals out of the
  denominator, Cohen's kappa.
- **`dataset/build_deception_v2.py`.**
  - `score`: GPU, gated, lazy realization, atomic per-chunk files, resumable, split-parallel.
  - `assemble`: CPU, stratified capped selection, D/H/F, re-checks, construction checks, reports, provenance,
    refusal to overwrite.
  - `finalize`: comparison set and cross-task band.
- **`scripts/build_v2.sbatch`.** Guarded mgnp init, `TQDM_DISABLE`, arguments passed through.
- **Tests.**
  - `tests/test_purity_v2.py` (23).
  - `tests/test_purity_judge_v2.py` (12).
  - `tests/test_build_v2.py` (26).
  - `tests/test_v2_reproducibility.py` (7). It now runs against the three built datasets: byte equality of every
    D/H/F prompt and label, pool and source sha256, and neutral re-selection with the Llama tokenizer.

## 4. Tests

| env | result | failure names |
|---|---|---|
| base (py3.9, transformers 4.57.3) | 8 failed, 1665 passed, 58 skipped | exactly the 8 baseline names, none new |
| mgnp (py3.12, transformers 5.13) | 8 failed, 1818 passed, 19 skipped | exactly the 8 baseline names, none new |

Both runs were on the final code and the built datasets. `tests/test_v2_reproducibility.py` ran unskipped in both
envs on all three tasks (7 tests, including the Llama-tokenizer neutral re-selection) and passed.

## 5. Compute

| reservation | job | partition | reserved after reconcile | actual |
|---|---|---|---|---|
| `04-purity-topup` | 23060023 | gpuA100x4-interactive (bgrb) | 0.25 | 341 s |
| `04-build-far-test` | 23099684 | gpuA100x8-interactive (beto) | 1.25 | 3,610 s (TIMEOUT, 7 of 9 chunks kept) |
| `04-build-ser` | 23099685 | gpuA100x4-interactive (beto) | 0.75 | 2,575 s |
| `04-build-sdr` | 23099686 | gpuA40x4-interactive (beto) | 1.25 | 3,610 s (TIMEOUT, 4 of 5 chunks kept) |
| `04-build-far-trainval` | 23100970 | gpuA100x8-interactive (beto) | 0.5 | 1,644 s |

- Ticket 04 used 4.0 of 16 reserved GPU-h, 3.27 GPU-h actual. The feature total is 11.25 of 60.
- Throughput was about 0.011 s per forward on an A100, about 8 min per 20,000-instance chunk. An A40 was about
  2.6x slower.
- OpenRouter: 969 calls, about 2.15 USD (v1 gate 300; v1 probes and re-sends 63; judge v2 606).

## 6. Deviations and interpretations

- **Purity gate.** Replaced by construction checks (§14.G11). Before that ruling the gate was a hard stop, and
  judge refusals counted against purity, as in v1.
- **Length band (G6).** Met by a pre-registered instance-level window, 94-106, applied before scoring. It excluded
  nothing.
- **Overgeneration.** Capped at what the splits need after two interactive jobs timed out (lead instruction).
- **Honest-instruction condition.** Stored as columns on every row, not as a fourth directory. F rows carry
  `honest_twin_kind: "nopressure"`.
- **Lazy realization.** Only rows that pass nopressure go through the full `realize`. Its prompts are asserted
  equal to the scored ones.
- **Selection.** Greedy; documented in the review. It filled every split without a fallback.
- **Review.** Done on both axes by the implementer, because git is unavailable to it:
  `reports/04-purity-judge-full-build-and-reproducibility-review.md`.
- **`provenance.plan`.** Records the base plan; no top-up was used.
