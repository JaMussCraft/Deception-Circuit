# Last message of d2-worker ad2-worker-f58bfa5283c22b81 (2026-11-03T00:55:55-05:00)

The follow-up job's result checks out. Every task reads (b), and so does the direction label. The local re-run of the read matches the job on every rate, gap, interval, label and text field, but it is not byte-identical. 146 floating-point values differ by at most 3.6e-15. They are the classifier coefficients and the IH statistics computed from them, and the difference is rounding between the two machines.

**Checks**
- **Manifests.** All nine say pre-registered and carry the pinned stack (torch 2.11.0+cu128, transformers 5.13.0, an H100) and the pinned refusal-direction hash. They show zero fallback firings and 5,481 rows. The D2 feature hashes the read checked match the local files.
- **Drift anchor.** All 600 recomputed D2 rows are bit-identical to the stored ones.
- **Job log.** It was not at the path the lead gave. I copied it from the Bridges-2 clone over ssh, with matching hashes on both ends. An earlier submission, 50161907, failed after 4 seconds on a wrong allocation path, so it spent nothing.

**Key numbers, FAR first**

| | FAR (primary) | SDR (secondary) | SER |
|---|---|---|---|
| Act-form ids, D-clause clusters | 210, 12 | 35, 7 | 1, excluded |
| Gate AUROC, D against HI | 1.000 | 0.999 | 0.976 |
| Act-form gap, D minus I | 0.010 | 0.114 | n/a |
| Interval (D clause) | 0.000 to 0.028 | 0.000 to 0.250 | n/a |
| Joint p_DT minus p_HT | 1.000 | 0.841 | 0.771 |
| Label | (b) | (b) | (b) |

- **What (b) everywhere means.** The classifier separates the lie instruction from its honest mirror on every task. The joint reading puts DT with D and HT with HI everywhere, so it reads the instruction's content. On the form-matched act-form clauses, though, D and I do not differ. Under R15 the D2 route closes U1, and F8's SDR pass is read as clause-driven on every task. F8 and the D2 verdict stand.
- **Where the D-I gap does appear.** All-ids gaps grow to 0.340 on SDR and 0.530 on SER, against 0.160 and 0.145 under D2's classifier. These sit in the predicate and other forms only.
- **Cost.** The job used 0.47 GPU-hours (28:07) against 0.75 reserved and made no paid calls.

**Surprises, recorded as caveats**
- On FAR the IH interaction holds, but with an unexpected sign. The frame words move the honest mirror toward D, not I away from it, so they do not carry I's D-likeness.
- SDR's refusal control "explains" by an exact tie, since the ablated gap is exactly half. The gap already fails, so the tie changes nothing.

**Open for the lead**
- The test AUROC of D against HI is not in the job's readings. I computed it afterwards with the read's own fit (1.000, 0.999, 0.980) and recorded it in the hand-back as descriptive. The lead can decide whether the read should include it.
- The lead can also decide whether FAR's IH sign needs a note in the finding.

Files to commit, under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`:
- `docs/research/deception-divergence/reports/10-handback.md`
- `docs/research/deception-divergence/results/d2_followup/`: four new top-level files plus nine manifests, one set of three per task folder
- `logs/bridges2/d2_followup_50161975.out` and `logs/bridges2/d2_followup_50161907.out`
