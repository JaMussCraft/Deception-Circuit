# Format Circuit: a task-format control for the deception mechanism circuits

Status: ready-for-agent
Repo: Deception-Circuit (`Alignment/Deception-Circuit`)
Grilled: 2026-10-13. Glossary terms in `Deception-Circuit/CONTEXT.md` (ticket 02 adds
"Format Circuit" and the `nopressure` condition).

## Problem Statement

Knocking out a mechanism circuit (FAR, SDR, SER; deceptive condition) lowers the
model's deception rate on its own task and, in the exploratory EVAL 5 wave, on
external benchmarks. That result does not yet say whether the removed machinery is
deception-specific. The honest-twin wave showed the ambiguity directly: the SDR
honest twin matched the SDR deceptive circuit's benchmark knockout effect and
shares 51 of 69 heads with it. Both circuits were trained on prompts that contain
the Pressure Clause, so neither isolates what the task's format alone recruits:
read the Designating Sentence, map the Predicate, emit one of the two item
tokens at the Readout.

A circuit trained on the same instances with the Pressure Clause deleted, under
honest labels, captures exactly that format machinery. Knocking it out beside the
mechanism circuit, under one evaluation spec, tells apart "the knockout stops the
lie" from "the knockout breaks the answer".

## Pre-registered outcomes and decision rule

Three readings are possible, fixed before any run:

- **(a) Format explains it.** The Format Circuit knockout reduces deception as
  much as the mechanism knockout at equal or lower collateral. The benchmark effect
  is format or answer machinery, not deception. This is the outcome being guarded
  against.
- **(b) Deception-specific machinery exists.** The mechanism knockout reduces
  deception more than the format knockout at matched collateral.
- **(c) Uninformative.** The format knockout destroys answering or coherence. The
  response is to retrain the Format Circuit at a lower NLS, never to reinterpret.

The headline metric is **paired**, never raw delta deception: the deception drop
read against (i) the honest-answer drop on the no-pressure and honest-instruction
rows of eval 2 and (ii) the coherence cost (wikitext KL in eval 2; reference NLL
and distinct-2 in eval 5), with every circuit evaluated under the same suite
settings.

**Decision rule.** The Format Circuit counts as "as effective" when its deception
drop is at least 80 percent of the mechanism circuit's, and its honest-answer drop
and reference-NLL rise are no larger than the mechanism circuit's, with both
circuits' knockouts outside their own size-matched random nulls. Anything else is
(b), unless the Format Circuit knockout is also incoherent (fails the wikitext KL
gate or degenerate generations), which is (c).

## Solution

1. **Control dataset** (`<task>_nopressure`) for FAR and SDR, derived from the
   stored deceptive datasets by deleting the stored Pressure Clause string from
   the stored clean and corrupt prompts, relabelled to honest targets, filtered
   for honest behaviour at margin in both streams with an argmax flip between
   streams. Strictly paired by `instance_id` with the deceptive train, validation
   and test splits.
2. **A third `--deception-condition`**, `nopressure`, so `train.py` and the
   evaluator's `--task-from` treat the control exactly like the honest twin.
3. **Three Format Circuits**: fine NLS 0.3 for FAR and SDR, coarse heads-only
   NLS 0.3 for SDR, each with the training settings of its paired mechanism run.
   A size gap above 25 percent (heads, or leaves for fine) triggers one NLS retune
   step of 0.1 toward the mechanism circuit's size.
4. **An evaluation suite per task** over the three circuits D (deceptive), H
   (honest twin), F (format): the 3 by 3 faithfulness matrix over the D, H and F
   test sets; knockouts with random nulls and flip audits, including the eval 2
   no-pressure and honest-instruction rows and wikitext collateral; Jaccard
   overlap; and delta cells D minus F, D intersect F, F minus D and the three-way
   exclusive-or of D, H, F.
5. **A summary writer** that applies the decision rule and prints (a)/(b)/(c)
   per task with the numbers behind it.
6. **EVAL 5 preparation**, gated on the eval 2 wikitext KL bar and on the
   researcher's explicit go-ahead: one suite per task containing D, H and F, same
   datasets and n as the existing suites, interchange only.

SER is deferred until its user turn is reworded (it is deceptive on 2 of 3 items
with no pressure and positional under an honest instruction, so an honest-labelled
SER control would be small or would train a positional circuit).

## User stories

1. As a researcher, I want a `<task>_nopressure` dataset built from the stored deceptive dataset's own prompts, so that the control is paired with the circuits I already trained and evaluated and is immune to the FAR/SDR template drift.
2. As a researcher, I want the control relabelled to honest targets and filtered for honest answering at margin in both streams with an argmax flip, so that the Format Circuit is "format under honest answering" and the corruption still carries signal.
3. As a researcher, I want the filter threshold to step 0.7, 0.5, 0.3 until at least 150 train and 500 test instances survive, with a hard floor of 0.3 and every step recorded, so that the threshold is never relaxed silently.
4. As a researcher, I want strict pairing by `instance_id` with the deceptive splits, survivor counts and the item-pair and polarity mix reported, and honest-split instances appended only as a separately tagged subset when survivors fall short, so that cross-condition cells are paired per instance wherever possible.
5. As a researcher, I want the eval-time no-pressure and honest-instruction variants derived from the stored prompt string instead of re-templated, so that eval 2 and eval 4 rows for FAR and SDR are computed on the prompts the circuits were trained on.
6. As a researcher, I want `--deception-condition nopressure` to work in `train.py` and through `--task-from` in the evaluator, so that the Format Circuit and its test set need no special casing.
7. As a researcher, I want the Format Circuits trained with the paired run's settings and their sizes compared to the mechanism circuits, with the retune rule applied at most once, so that size is not the confound.
8. As a researcher, I want the full 3 by 3 faithfulness matrix, the knockouts with nulls and flip audits, the overlap table and the delta cells, at leaf and head granularity for fine circuits (head primary) and head only for coarse, so that sufficiency, necessity, overlap and specificity are all read from one suite.
9. As a researcher, I want a summary that applies the pre-registered decision rule and shows the paired numbers, so that the verdict is mechanical.
10. As a researcher, I want EVAL 5 prepared but not launched without my go-ahead, with D, H and F in one suite on the same screened items, so that the benchmark comparison is apples to apples.

## Implementation Decisions

- **Clause surgery, not re-templating.** Each stored record carries `pressure`
  (the clause text), `clean_prompt` and `corrupt_prompt`. The control prompt is
  the stored prompt with the clause removed together with its leading space. The
  builder asserts the clause occurs exactly once in each stream's prompt, then
  re-runs `assert_aligned_pair` on the pair. The honest-instruction variant
  replaces the clause in place with `dc.HONEST_INSTRUCTION`. The helper refuses an empty clause; on a dataset whose condition is
  `nopressure` the evaluator derives no variant rows (the dataset already is the
  no-pressure variant). The same helper
  serves the dataset builder and `evaluation/variants.py` (ticket 01), which fixes
  the drift: today `deception_records` rebuilds prompts through `dc.SPECS`, whose
  FAR and SDR wording no longer matches the stored datasets (0 of 200 reproduce
  for each; SER 200 of 200).
- **Relabel then reuse the filter.** Swap `target` and `distractor` on every
  stored deceptive record, set `condition` to `nopressure` and `pressure` to the
  empty string, keep `pressure_id` for provenance. Then `filter_by_model_behavior`
  as it stands implements the rule: clean argmax equals the (now honest) target at
  margin, corrupt argmax equals the distractor at margin, which is the flip.
  `evaluate_behavior` runs once; the 0.7 / 0.5 / 0.3 step-down is applied offline
  to the stored margins.
- **Instances.** Train, validation and test come from the deceptive dataset's own
  splits, so the control's `instance_id`s are a subset of the deceptive ones and
  every cross-condition cell on D or F data is paired. The honest twin's instances
  are disjoint from the deceptive ones by construction (0 shared test ids), so any
  honest-split fallback subset is tagged `source: honest_split` and reported
  separately, and cells on H data are unpaired. Fallback triggers below 150 train
  or 500 test survivors after the threshold floor.
- **Layout.** Same arrow `DatasetDict` layout as `<task>` and `<task>_honest`
  (train / validation / test directories plus `dataset_dict.json`),
  `dataset_config.json` with `condition: "nopressure"` and the chosen
  `margin_thresh`, `filter_report.json` with pass rates per threshold step, the
  item-pair and polarity mix, unexpected-argmax counts and the fallback subset
  size. The built DatasetDict is committed on the branch like `<task>_honest`.
- **Registration.** `tasks/deception.py` `dataset_dir` gains the `nopressure`
  suffix branch; `train.py` `--deception-condition` gains the choice. The
  evaluator's `--task-from` inherits `deception_condition` from the run's
  `config.json` (`evaluation/circuits.py`), so a Format Circuit run directory is
  also the handle for the no-pressure test set. CONTEXT.md gets a "Format
  Circuit" entry and a `nopressure` note under Honest Condition; "control" stays
  under _Avoid_.
- **Training.** Identical to the paired run: seed 42, 500 node epochs, no edge
  pruning, NLS 0.3. Fine runs are plain; the coarse run adds
  `--no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output
  --no-prune-mlp-blocks` and the coarse post-processing (copy
  `active_nodes.json` / `config.json` to `*.coarse.json`, then
  `expand_coarse_masks.py`). Output slugs follow the existing convention:
  `nls0.3_nopressure_noedge_<stamp>` under `outputs/llama-8b-instruct_<task>/`,
  and `nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_<stamp>` under
  `outputs/llama-8b-instruct_sdr_coarse/`.
- **Pairing targets and the size rule.** Fine FAR D: 48 heads, 5,436 fine units.
  Fine SDR D: 68 heads, 11,251 fine units. Coarse heads-only SDR D: 69 heads.
  A gap above 25 percent in head count, or in fine-unit count for fine circuits,
  triggers one retrain at NLS 0.3 ± 0.1 in the direction that closes the gap, and
  the launcher records both sizes either way. At most one retune.
- **Suite composition.** One suite per task family: `format-control-far-nls0.3`,
  `format-control-sdr-nls0.3`, `format-control-sdr-coarse-nls0.3`, under
  `outputs/_suites/`. Circuits bound as `D`, `H`, `F`; tasks bound through
  `--task-from` for the D, H and F run directories. Cells: 9 faithfulness
  (3 circuits × 3 datasets), knockouts of D, H, F on each dataset with
  `--n-random 20 --knockout-null-count 20`, the deltas `D-F`, `D&F`, `F-D` and
  `--xor D,H,F` on the D dataset, each as its own cell with null and flip audit.
  Fine deltas at `--compose-granularity both` (head primary in the summary);
  coarse at `head`, with the heads-only knockout built as `c - m` against the
  `_allmlp_nomb` operand, as the coarse SDR wave does. Interchange only.
- **Overlap.** Jaccard over heads and fine units for D/H, D/F, H/F, from
  `compare_node_masks.py` or the suite's mask-compare path, written into the
  suite summary.
- **Summary.** `evaluation_summary.md` per suite via a writer that reads the
  cells, prints the paired table (deception drop, honest-answer drop, wikitext KL,
  nulls) for D, H and F, the overlap table, the delta rows with their flip-audit
  verdict, and the decision-rule verdict (a)/(b)/(c) per task with the numbers
  behind it. The knockout-reduces-deception direction is read as the drop in
  accuracy under the deceptive-label convention (`LABEL_CONVENTION` in
  `evaluation/variants.py`).
- **EVAL 5.** One suite per task family with `--circuit D=... --circuit H=...
  --circuit F=...`, the settings of `outputs/_eval5_launch/eval5_args.sh`
  (interchange, `--benchmark-n-per-dataset 50`, `--benchmark-n-random 6`,
  screen budget 600), both benchmark groups (`sm` and `lb`). "One spec" means one
  screen, one judge cache and identical settings, so D, H and F knockouts run on
  the identical screened items; the random rows remain size-matched per circuit.
  Prepared as a dry-run-validated launch script; launched only on the
  researcher's explicit go-ahead. Grader caveats stay as recorded in
  `Alignment/.scratch/eval5-grader-fixes/` (three known issues).
- **Scheduling.** Any account (beto, bimc, bgrb), any partition (A40, A100,
  H200), chosen by queue length and fairshare for speed. `--dry-run` on the login
  node before every submission; `--time` on the command line.
- **Work location.** Feature branch `format-control` in a worktree
  `Deception-Circuit/.claude/worktrees/format-control`, cut from the main
  checkout's current HEAD (not from `component-analysis`, which has never merged
  and is not needed here). Built datasets go under the worktree's
  `data/datasets/`; run and suite outputs under the worktree's `outputs/`, with
  absolute paths into the main checkout for untracked inputs.

## Testing Decisions

- A good test asserts external behaviour at a seam the caller sees: the written
  dataset and reports, the records a loader yields, the arguments a launcher
  prints, the summary file.
- **Clause surgery.** With the fake word tokenizer from `tests/fakes.py`: the
  clause is removed once with its leading space; a prompt without the clause, or
  with it twice, raises; the result passes `assert_aligned_pair`; the
  honest-instruction replacement lands in place. `tests/test_variants.py` is
  updated to the new derivation and asserts a stored FAR-style record (old
  wording) round-trips to the stored prompt minus the clause.
- **Builder.** With the scripted model from `tests/fakes.py`: relabelling swaps
  target and distractor; the step-down picks the first threshold meeting the
  minimums and records every step; the fallback subset is appended and tagged only
  when the minimums fail; `dataset_config.json` carries `condition: "nopressure"`.
- **Registration.** `dataset_dir` maps `nopressure` to `<task>_nopressure`;
  `train.py` accepts the choice; a run config with `deception_condition:
  "nopressure"` resolves to the right test set through `--task-from` on the
  2-layer random Llama from `tests/helpers.py` (`tests/test_end_to_end.py`
  pattern).
- **Launchers and summary.** Launch scripts have a `--dry` mode printing the
  exact `sbatch` lines; the size rule is a pure function with tests at the 25
  percent boundary; the summary writer is tested on a fixture suite directory and
  on an incomplete one (missing cells are reported, not crashed on).
- Two environments (login base, mgnp): run both suites, compare failure names to
  the baseline recorded on the branch base, never counts. Prior art:
  `tests/test_deception_common.py`, `tests/test_variants.py`,
  `tests/test_evaluation.py`, `tests/test_suite_layout.py`,
  `tests/test_end_to_end.py`.
- Process: tests before implementation per ticket; an independent subagent review
  against this spec after each ticket, written to
  `Alignment/.scratch/format-control/reports/`.

## Out of Scope

- SER control (deferred until its user turn is reworded and relabelled).
- A trained honest-instruction control; honest instruction is evaluation-only
  unless the no-pressure control lands in outcome (c).
- Re-running the eval 2 and eval 4 variant rows of FAR and SDR runs at NLS levels
  other than 0.3; they are flagged as suspect (computed on mixed-wording prompts)
  in each affected run's summary when touched, not recomputed.
- Regenerating the FAR/SDR/SER datasets from the current templates; the control is
  rebuilt when that happens.
- Mean and zero ablation; STD; the joint task; a joint format circuit over tasks.
- Fixing the three EVAL 5 grader caveats.

## Further Notes

- The honest twin and the deceptive dataset have disjoint instances (a given
  instance either lied or it did not), so of the 9 faithfulness cells per task only
  the D-data and F-data columns are instance-paired. No existing suite evaluates any
  circuit on a `*_honest` test set, so all 9 cells are new.
- The stored FAR dataset uses `ready`/`delayed` as Predicate words and item pairs
  outside the spec's pool (e.g. `trucks/trains`); the stored SDR dataset uses
  `damaging`/`harmless`. Read predicate words from each record's `desig` /
  `desig_inv`, never from `dc.SPECS`.
- Under interchange ablation the empty circuit's no-pressure logit difference on
  FAR is already +1.98, so eval 4 variant rows read the ablation source as much
  as the circuit; the knockout rows of eval 2 are the ones the decision rule uses.
- Expected sizes: the honest twins at NLS 0.3 are 65 heads (FAR) and 69 heads
  (SDR), so a format circuit of similar size would be unsurprising; a much
  smaller one would say the format needs less machinery than either condition.
- A coarse SDR seed-stability wave (seeds 1 and 123, heads-only NLS 0.3) was
  started 2026-10-13 in the main checkout; it is unrelated and must not be
  touched.
