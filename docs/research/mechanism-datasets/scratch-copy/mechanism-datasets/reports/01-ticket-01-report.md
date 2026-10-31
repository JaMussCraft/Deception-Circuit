# Ticket 01 report: pilot harness and pre-registered acceptance metrics

Implementer: ticket-01 subagent, 2026-10-19. CPU only, no Slurm job, no OpenRouter call, no git.
Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`
(branch `mechanism-datasets`). Ledger delta: none.

## What was built

- **`dataset/contingency.py`** is the pure acceptance rule of spec section 6. It needs no tokenizer and
  no torch. It holds the constants pinned to spec section 6, `classify` and `classify_all`, and
  `cell_metrics`, which builds every metric field of the ticket's report schema. It also holds
  `project_cost` with `min_generated`, plus `cell_verdict` and `round_verdict`.
- **`dataset/pilot_v2.py`** is the harness CLI. It reads a cells file and builds one shared instance
  list per round and seed. It realizes every cell through `dataset/deception_v2.py` and asserts every
  prompt of every condition before the model loads. Then it loads the model once and scores each cell in
  nine `dc.score_prompts` calls: the prior plus four conditions times two streams. It writes the report
  and survivors file per cell, then the round summary. `--summarize` writes the markdown table.
- **`scripts/pilot_v2.sbatch`** is a one-GPU wrapper with the guarded mgnp init from the brief. It passes
  every argument through. Account, partition and time go on the command line.
- **Tests:** `tests/test_contingency.py` (47 tests), `tests/test_pilot_v2.py` (16 tests), and
  `tests/fakes_v2.py`. The fakes file is a stub of the spec section 5 contract, built on the real
  clause surgery. One test in `tests/test_pilot_v2.py` realizes records with the real
  `dataset/deception_v2.py` and scores them with `ScriptedModel`.

## How to run the harness

The cells file is a JSON list. Each cell has a `cell_id`, a `task` (one of the three v2 tasks), a
`framing` path, a `suffix` of on or off, a `ser_wording` (A or B for SER, otherwise null) and `n`. An
optional `neutral_pool` path overrides the CLI default. Run from the worktree root:

```
# 1. CPU dry path on the login node: realize + assert every prompt, length reports, 3 rendered pairs per cell
/u/swong2/.conda/envs/mgnp/bin/python dataset/pilot_v2.py --cells <cells.json> --round 1 \
    --out-dir /abs/path/reports/pilots/round1 --no-model

# 2. GPU (after the ledger reservation and sbatch --test-only)
mkdir -p logs
sbatch --account=<acct> --partition=<part> --time=HH:MM:SS scripts/pilot_v2.sbatch \
    --cells <cells.json> --round 1 --out-dir /abs/path/reports/pilots/round1

# 3. Round table
/u/swong2/.conda/envs/mgnp/bin/python dataset/pilot_v2.py \
    --summarize /abs/path/reports/pilots/round1 --markdown /abs/path/reports/pilot-round-1.md
```

These files land in the output directory:

- `<cell_id>.json` is the report, written after each cell and before the next is scored.
- `<cell_id>.survivors.jsonl` holds every contingent survivor with all condition prompts, scores and
  flags. Ticket 04's purity judge reads it.
- `round_summary.json` is rewritten after every cell, so a job that hits its time limit still leaves a
  summary.
- `<cell_id>.aborted.json` is written when the cell's framing, spec or pool fails to load, or when any
  prompt is misaligned or over length. The other cells still run, and the job exits 1. If every cell
  aborts, no model is loaded.

Re-running a cell into the same directory first removes that cell's old files, so `--summarize` never
sees a stale outcome.

Other CLI flags: `--seed` (default 42), `--batch-size`, `--model`, `--max-seq-length` (default 120),
`--neutral-pool`, `--item-pairs`, `--entities`, `--partition` (default `$SLURM_JOB_PARTITION`) and
`--hf-token`.

## Test results

Full suite, run from the worktree root, compared by name against `reports/00-baseline-failures.md`.

| env | failed | passed | skipped | new failure names |
|---|---|---|---|---|
| base (py3.9) | 8 | 1546 | 58 | none |
| mgnp (py3.12) | 8 | 1699 | 19 | none |

The 8 failures in each env are exactly the baseline names. All 63 ticket-01 tests pass in both envs. That
includes the integration test, which realizes records with the real `dataset/deception_v2.py`.

A real-tokenizer `--no-model` dry run was also made, after ticket 02's pools landed. It covered four
cells of 200 instances: FAR role_goal with the suffix off, SDR stake with it on, SER consequence with it
on under wording A, and SER self_interest with it off under wording B. The output went to
`/u/swong2/.claude/jobs/6e1f64bd/tmp/dry/out`, a scratch location. Every prompt was aligned and within
120 tokens, no cell aborted and no item pair was dropped. The neutral-twin lengths equal the pressure
lengths.

| cell | pressure prompt tokens (min / median / max) |
|---|---|
| FAR, suffix off | 73 / 76 / 79 |
| SDR, suffix on | 89 / 93 / 95 |
| SER A, suffix on | 91 / 93 / 96 |
| SER B, suffix off | 76 / 79 / 82 |

## Interpretations and deviations

- **Honest-instruction metrics pool both streams.** Accuracy and item_2 share are computed over
  2 x n_survivors stream answers. A stream's answer is the higher-logit word of the pair: the honest
  word if h > 0, otherwise the deceptive word. The reviewer judged this the plain reading of the spec.
  The share of survivors honest in both streams is reported beside it as `accuracy_both_streams`, but
  the gate does not use it.
- **The margin-1.0 re-application changes only the pressure margin.** That is the `behavior_passes`
  rule. The honest margin stays at 0.3.
- **SER wording B drives the selection.** `round_verdict` prefers a passing B cell over a higher-rate A
  cell (spec 14.G4), both for `best_cell` and within a family. The orchestrator ratified this.
- **Verdict precedence.** A rate-floor failure is a `fail`. Once both floors clear, fewer than 30
  survivors gives `insufficient_n` with "rerun at 3000", whatever the other criteria say. A cell that
  already has 3,000 instances and still has fewer than 30 survivors is a `fail`. The orchestrator
  ratified this.
- **Round selection respects the budget.** Within each suffix policy, candidate selections take one
  passing cell per task. Candidates come either from one shared framing family or from any families.
  Ordering is within 14 GPU-h first, then a shared family, then the highest min-polarity rate, then the
  lower cost. If nothing fits, the result is the best shared family, flagged `within_budget: false`, and
  the round does not pass.
- **Cost projection.** The strata are pinned to designation polarity x item polarity x the audit and lab
  variants: 8 strata of 175. The capped selection at a given generated count is the better of two
  fills. The joint fill draws on all strata at once and spreads each evenly over its (clause, item pair)
  cells. The sequential fill takes the scarcest stratum first. Bisection then finds the smallest count at
  which every stratum fills. Six hand-computed toys test it: uncapped, clause cap binding, pair cap
  binding alone, a shared clause that needs the joint fill, infinite at 10% but finite at 15%, and a
  finite cost over budget at 10% that relaxes. No closed form was written. The report also carries
  `n_generate_uncapped`, and the 10% figures (`at_cap_0_10`) when the cap was relaxed.
- **`cell_metrics` returns the metric fields only.** The harness adds `cell_id`, `round`, the framing
  metadata, `lengths` and `samples`, because those need a tokenizer and the contingency module must stay
  tokenizer-free. The ticket wording says `cell_metrics` returns every schema field. The end-to-end test
  asserts the full schema key by key on the written report.
- **Dry-run verdict.** `--no-model` reports carry the verdict status `not_scored` and a null cost
  projection. The ticket's three statuses apply only to scored cells.
- **Infinite costs serialize as `Infinity`.** An infeasible projection is `float("inf")`, which Python's
  `json` writes as `Infinity`. Python reads it back, but `jq` and strict JSON parsers reject it. Tickets 03
  and 04 should load reports with Python.
- **Item pairs.** The harness drops any pair whose words are not single tokens with a leading space, and
  records the dropped pairs in the round summary. Ticket 02 reports that every pair passes under
  Llama-3.1. The instance list is the same `dc.generate_instances` call as ticket 02's
  `generate_instances_v2`: 25 slots, audit and lab, same seed. A longer list starts with the shorter
  one, which is tested.
- **Extra fields.** Reports carry some fields beyond the required schema. These are
  `framing_round`, `framing_hypothesis`, `framing_path`, the `prior` length block, honest-instruction
  metrics per designation x item polarity, stratum rates, keep and pass fractions in the cost
  projection, and token-boundary renderings in the samples.

## Review

The review is in `reports/01-pilot-harness-and-acceptance-metrics-review.md`. The independent reviewer
found two bugs, both fixed with their repros as tests. The selection ignored the three-task budget, and
the sequential fill wasted a clause budget that strata share. Points S3 to S5 were ratified, and nits 7, 9
and 14 were fixed. Optional nits 8, 10, 12 and 13 were left, with reasons. Nit 11 (CONTEXT.md terms)
belongs to ticket 02.

## Open issues

- Scoring with the real model has not run, because this ticket has no GPU allocation. The real-tokenizer
  dry path has run. Scoring reuses v1's `dc.score_prompts` unchanged, so the padding and readout path is
  the one the v1 builds already ran. Ticket 03's first interactive job will be the first real scoring.
- The cost projection scales each cell's empirical counts per (stratum, clause, pair), as the ticket
  specifies. A 1,000-instance cell with very few survivors in some stratum can therefore project
  infinite cost and fail on cost alone. That is the pre-registered behaviour. `n_generate_uncapped`
  shows how much of the cost comes from the cap.
- The capped selection is a heuristic, the better of two fills, and not an exact linear program. mgnp
  has no scipy. The projected count is therefore an upper bound.
