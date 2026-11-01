# Sandbagging completion audit helper — 2026-10-24

Prepared `transfer-v5/audit-sandbagging.py`, a standalone standard-library CPU helper. Only this helper/report were created or edited for this task. No running-job output was inspected or polled; no core source, jobs, git, budget, labels or API calls were changed.

The helper reads an eventual completed `benchmarks.json`, its adjacent `frozen_runtime_check.json`, frozen cohort/masks and the actual reviewed execution receipt. It binds cohort/mask bytes to that receipt; checks the cohort content hash and immutable source hashes; compares actual proof source hashes with receipt bindings; and verifies exact technical input/manifest identity. It independently reconstructs expected five-state live-support digests from the frozen head sets and geometry, then checks the actual-model proof's support counts, full-vocabulary identity, BF16/CUDA status and the embedded/external proof match.

For the result, it requires the exact frozen50 item records/IDs/order, prompts, native donor IDs and reference metadata, native1024-token budget, fresh H200 intact/donor provenance, stock cached interchange/honest-reference settings, locally graded labels, exactly five states and complete per-state label/generation/coherence coverage. Saved label counts/rates are recomputed for consistency, without regrading generations or introducing labels. Missing states, unscored/errors, wrong bindings or protocol drift yield `complete:false`, `headline:null` and exit2. A valid complete block exits0. Malformed/missing input also fails closed with no headline.

The JSON audit retains each state's raw deceptive/honest/unparsed counts, raw local verdict counts, missing generation/label counts, empty-text counts, judge/error/unscored counts, token-budget length proxies and existing aggregate coherence metrics. It reports the full three-way paired transition table and raw deception-count change versus fresh intact, plus exact text matches. The sole primary is prospectively fixed `new-allW30`; all other state counts remain visible.

Interpretation is deliberately narrow: `honest` is the local sandbagging normal-tag outcome, not independently verified factual truth. Empty, ambiguous, unparsed and format-damaged outputs do not become confirmed truthful corrections. Length1024 is only an at-token-budget proxy: the saved schema cannot distinguish truncation from EOS exactly at the limit. Historical A40 selection, pressure-only transfer and a single descriptive random comparator remain limitations. The saved global judge-budget snapshot is reported as a cumulative observation, not inferred per-block API spend; local-grader fields must contain no API prompts/text/errors. Mutable runtime ledger/cache bytes are not rehashed as if they were immutable historical sources.

Usage after the block completes (select the actual cell path and retry execution receipt):

```bash
v5_study=/projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5
/u/swong2/.conda/envs/mgnp/bin/python "$v5_study/audit-sandbagging.py" \
  --benchmarks-json "$v5_study/eval5-sandbagging-calibration/cells/self/sdr/interchange/benchmarks.json" \
  --receipt "$v5_study/sandbagging-execution-receipt.json" \
  --output "$v5_study/sandbagging-audit.json"
```

`--proof` can explicitly select the actual proof if it is not adjacent. `--cohort` and `--masks` default to the frozen files beside the helper. Output is prevented from overwriting any input. A partial audit is useful evidence but must not be presented as a completed five-state efficacy result.

CPU verification: `audit-sandbagging.py --self-test` passed under both mgnp and base Python3.9. The synthetic schema test first demonstrates a fully complete50×5 block is accepted (the auditor is nonvacuous), then proves a missing random state refuses a headline, a zero-ablation protocol mutation refuses a headline, and empty/unparsed output increments its own category without receiving an honest label. No synthetic outcome is real experimental evidence. Logs: `/tmp/v5-sb-audit-selftest-{mgnp,base}.log`.
