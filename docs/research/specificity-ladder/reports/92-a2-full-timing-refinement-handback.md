# Hand-back: A2 full-run timing refinement

Agent: Sol independent operational reviewer. Status: handed-back.

## What changed

Recommendation only: use `59 minutes` for a future FAR D repeat and `54 minutes` for remaining SER D seeds. Keep the original unmeasured-condition limits: FAR I `61`, SDR D `63`, SDR I `64`, SER I `57` minutes. All observed FAR D seeds are already terminal; its refined limit changes no pending job. Keep the original ledger charges. No job, source, training setting or research-session state was changed.

- Orchestrator commit file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/92-a2-full-timing-refinement-handback.md`.
- Calculation receipt: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/92-a2-full-timing-refinement-calculations.json`.
- Identical primary mirrors use `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`.

The following inputs were extracted from actual receipts and the top-level completed accounting rows. No active-node membership or task/faithfulness output was read. Exact source paths and file hashes are retained in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/92-a2-full-timing-refinement-calculations.json`.

| Full condition / seed | Delta job | Pruning seconds | Child seconds | Allocation seconds | Child minus pruning seconds | Allocation minus child seconds |
|---|---|---|---|---|---|---|
| FAR D / 42 | 23416841 | 2756.6 | 2890.141182 | 2902 | 133.541182 | 11.858818 |
| FAR D / 1 | 23416842 | 2749.5 | 2883.308565 | 2895 | 133.808565 | 11.691435 |
| FAR D / 123 | 23416843 | 2735.2 | 2809.634120 | 2827 | 74.434120 | 17.365880 |
| SER D / 42 | 23416761 | 2575.6 | 2643.872125 | 2660 | 68.272125 | 16.127875 |

The short-pilot inputs below come from the timing-only receipts in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/`; their exact file paths, hashes and values are also in the calculation receipt above. Derived fixed child cost means total child time minus printed pruning time; it includes loading, initial/final evaluation and export/publication work inside the child rather than assuming these costs vanish.

These pilot numbers are recorded in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/92-a2-full-timing-refinement-calculations.json`.

| Pilot condition | Pruning seconds | Child seconds |
|---|---|---|
| FAR D | 119.7 | 216.462612 |
| FAR I | 116.4 | 190.958491 |
| SDR D | 121.3 | 191.820913 |
| SDR I | 123.0 | 192.734113 |
| SER D | 108.9 | 173.905511 |
| SER I | 109.0 | 175.999761 |

**Formula and decision rule.** Preserve the existing `20%` multiplicative buffer and `20 seconds` of explicit outer startup/publication allowance from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json`. The allowance exceeds every observed full allocation-minus-child residual. For a measured condition, use `ceil(1.20 * (max(full_pruning) + max(full_child - full_pruning) + 20) / 60)` minutes. The maxima are taken separately, preserving the slowest observed pruning and largest non-pruning child cost even when they came from different seeds. For an unmeasured condition, keep its original same-condition pilot formula: `ceil(1.20 * (25 * short_pruning + short_child - short_pruning + 20) / 60)`. This conservatively repeats pilot periodic-validation cost rather than substituting a smaller unobserved value. No buffer was shaved to fit the interactive limit.

The following derived recommendations and intermediate values are reproduced by `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/92-a2-full-timing-refinement-calculations.json`.

| Condition | Full observations | Original minutes | Prospective minutes | Estimated seconds before buffer | Seconds after buffer | Decision |
|---|---|---|---|---|---|---|
| FAR D | 3 | 63 | 59 | 2910.408565 | 3492.490278 | Same-condition evidence; repeats only |
| FAR I | 0 | 61 | 61 | 3004.558491 | 3605.470189 | Keep original |
| SDR D | 0 | 63 | 63 | 3123.020913 | 3747.625096 | Keep original |
| SDR I | 0 | 64 | 64 | 3164.734113 | 3797.680935 | Keep original |
| SER D | 1 | 57 | 54 | 2663.872125 | 3196.646550 | Same-condition evidence; remaining seeds |
| SER I | 0 | 57 | 57 | 2811.999761 | 3374.399713 | Keep original |

**Why no cross-condition reduction.** The derived full-pruning / naive-pilot-projection multipliers range from `0.914018` to `0.921170` on FAR D, versus `0.946042` on SER D. A leave-family-out check using the slowest FAR factor predicts SER pruning at `2507.884211 seconds`, below its observed `2575.6 seconds` by a derived `2.6291%`; using SER predicts FAR at `2831.031405 seconds`, above its slowest observation by a derived `2.7001%`. These results show modest but real transfer error, not a validated upper bound. There is no full I-condition observation and no full SDR observation. A global calibration would therefore extrapolate to both an unseen task family and, for SDR I, an unseen condition. Details are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/92-a2-full-timing-refinement-calculations.json`.

For sensitivity only, multiply every condition's naive short pruning projection by the largest observed full/short multiplier, retain the largest observed non-pruning child cost across families, add the same outer allowance and apply the unchanged buffer. This gives derived unadopted minute estimates of FAR I `59`, SDR D `61`, SDR I `62`, SER I `55`. Setting that multiplier back to `1` instead gives `62`, `64`, `65`, `58` minutes respectively under the common worst-fixed-cost stress scenario. These are uncertainty diagnostics, not replacements for the existing same-condition limits. Even the empirical calibrated scenario leaves both SDR arms above the interactive ceiling, and there is no basis for choosing a smaller factor because a queue would be faster. The calculation receipt above retains every scenario, including measured conditions.

**Limits.** A same-condition maximum plus buffer is an operational forecast, not a statistical guarantee. SER D currently has only a single full seed. FAR's fixed costs varied materially across nodes/runs, which is why the observed maximum is retained. Short pilots use a different cosine horizon. The recommendations apply only while the native settings, matched cohorts, source build, sequence length, hardware and output path remain equivalent. They do not justify another model, GPU type, changed batch or parallelism. The timing receipts share the approved execution/build/config identities, and full native manifest hashes/argv agree with their wrapper receipts. This review inspected provenance fields only and did not repeat source/mask or scientific-effect audits.

No new GPU calibration is needed to retain the original unmeasured-condition limits. Future naturally completed full runs can update their own conditions' estimates without starting a timing-only job. The derived ledger consequence is deliberately zero: retain the original `1153` reserved minutes and `19.216666666666665` GPU-hours from the frozen fleet plan and calculation receipt; reducing a prospective scheduler limit does not retrospectively reduce reservations or spending.

## How verified

Read only timing/provenance fields from the designated short/full receipts, top-level accounting rows, native run manifests and the original fleet plan. The calculation asserts successful wrapper status/exit, completed Delta accounting with GPU type, full/short epoch identity, identical full-versus-pilot build/cohort/count/source/config/hardware/granularity fields, and identical training arguments except epochs, seed and output path. Native run manifest file hashes match receipt hashes, and native execution commit/argv match each full receipt.

```bash
/sw/external/python/anaconda3/bin/python3.9 /tmp/a2_timing_refinement92.py
```

Observed: exit `0`; the calculation receipt contains all recommended minutes and the leave-family-out/sensitivity values reported above. The script reads only the declared operational inputs, does no model import and performs no job or research-session mutation.

## Execution evidence

Timing evidence only; no scientific baseline result is claimed. All designated full accounting rows report `COMPLETED` and `0:0`, with their jobs, elapsed seconds, child/pruning seconds, native manifest paths, full execution commit and input hashes retained in the calculation receipt. Observed evidence count is `4` full receipts against `4` expected and `6` timing receipts against `6` expected; the script asserts their epoch purposes (`500` versus `20`) and equivalent configuration/provenance fields. Counts and epochs are derived from the enumerated input files above.

- Cluster: Delta; full job ids appear in the input table.
- Baseline timing reproduction: the same-condition original pilot formulas reproduce FAR I `61`, SDR D `63`, SDR I `64` and SER I `57` minutes against those exact frozen fleet limits; measured-condition replacements are explicitly distinguished.
- Provenance: every full `run_manifest.json` names execution commit `6bd8bf5334f2e83613a129d2fcfeacf83e762191`; exact manifest paths and hashes are in the calculation receipt.
- No scientific rows were examined, so no scientific baseline-metric reproduction or specificity claim is made.

## What is NOT done

No code changes, scheduler changes, submissions, cancellations, ledger changes, research-session writes, GPU calibration, model imports, masks, faithfulness/task outcomes, assessment scoring, notebooks, git or additional agents. No current queue forecast was used to select an estimate. Full condition coverage and independent seed-based tail uncertainty are unavailable, so the unmeasured-condition reductions were not adopted.

## Open questions

Default: the orchestrator may apply the same-condition SER D refinement to remaining pending seeds and keep the original limits elsewhere. FAR D is already complete. If normal-queue delay remains unacceptable, retain these estimates and make any scheduling decision separately; do not compress SDR limits to the interactive ceiling. Reassess a condition when its already planned full run completes. Preserve all original ledger charges.
