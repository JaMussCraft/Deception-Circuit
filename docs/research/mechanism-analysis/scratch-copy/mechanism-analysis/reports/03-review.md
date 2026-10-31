# Ticket 03 self-review (impl-03, 2026-10-25)

Scope: phase 1 (1A, 1B, 1C) as run on Bridges-2, the builders that read it, and the reading in `03-phase1-reading.md`.
This is a self-review; no independent reviewer was spawned (orchestrator's essentials-only usage note).

## What was verified

- **Jobs:** every job ran with all lines ok: 1A 3 jobs (33 cells), 1B 3 jobs (27 lines), 1C-a 6 lines, 1C-b 15 lines. Each
  was fetched and its sacct saved, and the ledger was reconciled under the lock. Ticket 03 used 9.5 of 19.5 H100 GPU-h,
  with no holdback and no Delta fallback.
- **Code reached the cluster only via pushed commits:** 701e0b3, 8bf0109 and ddd1da4. Batch and groups files were
  md5-checked against the clone before each submit. Every batch passed a login dry-run before submission.
- **Paired R-inv lines:** the 1C-b dry-run confirmed that each sample equals its union id file (`--n-causal 1000`), and
  that each held-out D sample equals the committed copy.
- **Pre-registered rules are tested at their seams:** R-A1 bands, R-cls, test (i) with its null, test (ii), the A / A′
  / B order and tie-break, the R-inv label, inversion-shared, B's share, the selectors, nulls, C_t, routing, paired
  strata, the R23 union and the R24 arm.
  - 60 tests pass in mgnp (py3.12) and base (py3.9).
  - `p1_results.py` (the combined linker) has no unit test. It only copies fields from the three block JSONs.
- **Positive control** (layer-0 MLP) reproduces v1 on every task.
- **Flip-audit script** reproduces its precedent verdicts.
- **Ticket-06 interchange cells** of record match the published tables.

## Defects found and fixed during the work

- `p1b_results` first assumed H and F cells are filed under `_honest` / `_nopressure`; every cell is filed under
  `<t>_v2`. The dry-run caught it, and it was fixed before any real data.
- The 1B report lacked a C1 section and sorted figure rows as text. Both were fixed (`c1_summary`, numeric order).
- The `p1c_results` JSON dump failed on numpy booleans. Fixed, and the (i)/(ii) flags are now plain Python values.

## Deviations (all logged in `03-handback.md` or ruled by the orchestrator)

- **1A submission:** all three 1A jobs were submitted at once instead of holding behind far's calibration
  (orchestrator's instruction).
- **R23:** R-inv runs on I's own held-out sample (option B), with D on the same ids. The letter-of-R19(3) subset
  (14 / 73 / 26) is a robustness row.
- **R24:** a descriptive U-only top-k arm, outside the R-AB reading. A test checks that the reading ignores it.
- **Combined report:** `03-phase1-results.md` links the three block reports instead of duplicating their tables.

## Limitations a reader should weigh

- **MLP nulls:** an MLP's layer-matched null is the MLP itself (one block per layer). For all-MLP candidates (sdr
  k = 1, 2) the null equals S_k, so (i) cannot pass. Mixed sets get a partly fixed null. No reading depends on the
  all-MLP k.
- **Test (ii) uses absolute moves:** a margin rise above 25% also fails. Sets with k = 40 and 80 have no (ii) by
  design.
- **R-inv sample:** it conditions on survival of I's filter.
  - FAR's I is mostly inversion-polarity (83 / 17), so its pooled rows are polarity-confounded. The like-for-like
    inversion-polarity row gives the same label.
  - FAR and SER I retention (210, 249) is below the 300 minimum (R22).
  - The R-inv bootstrap clusters by D's pressure_id, which gives few clusters on FAR (10 in option B).
- **Selection and held-out samples share clauses** (spec §2 point 10). The greedy sets were chosen on the selection
  sample; their held-out f_D is the test.
- **Core "answer machinery" (R-A1)** is a positional collapse on far and ser (flip audit), not answer selection by
  content.
- **R-lens** is the raw, uncalibrated lens (exploratory, R12).
- **A′ is provisional:** it is settled only by the phase-3 adjudication. Routing (c) is <= 0.25 on far (0.163) and
  ser (0.006).

## Scope guards

No EVAL 5, no training, no path patching.
