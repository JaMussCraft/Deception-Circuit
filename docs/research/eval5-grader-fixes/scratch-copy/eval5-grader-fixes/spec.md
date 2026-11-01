# EVAL 5 grader fixes before the paper-scale run

**Status:** needs-triage · opened 2026-09-16

Two grader behaviours were found in the 2026-09-15/16 exploratory EVAL 5 wave
(`Deception-Circuit/outputs/eval5_{delta_sdr,delta_sdr_head,delta_ser,far,sdr,ser}{,_lb}`).
Both are recorded as caveats in those runs' `result_summary.md` files and are
left as-is for now. They must be fixed, and the affected screens regenerated,
before the full-size run for the paper write-up.

- `issues/01-empty-generation-scored-honest.md` — Liars' Bench harm-pressure-knowledge-report
- `issues/02-mask-refusal-coded-deceptive.md` — MASK binary splits, verdict D

Neither changes the exploratory conclusions (both affect a handful of rows),
but both bias in a direction that flatters a knockout: an empty or refusing
generation should never be scored as a committed answer.
