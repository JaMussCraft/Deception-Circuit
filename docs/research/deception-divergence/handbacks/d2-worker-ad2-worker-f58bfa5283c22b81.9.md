# Last message of d2-worker ad2-worker-f58bfa5283c22b81 (2026-11-02T22:25:34-05:00)

The D2 verdict under ruling R13 is written: the premise passes on SDR only, and only on the classifier arm. FAR and SER fail. All three Markdown files I touched lint clean, the hand-back keeps its five required headings, and the lead has the list of files to commit.

**Verdict per task.**

| task | classifier gap | 95% interval | gap with refusal ablated | result |
|---|---|---|---|---|
| FAR | 0.005 | 0.000 to 0.018 | 0.000 | fails |
| SDR | 0.160 | 0.086 to 0.227 | 0.136 | passes |
| SER | 0.145 | 0.076 to 0.215 | 0.032 | fails, below the bar and explained by refusal |

**Caveats now in the hand-back.**
- **The classifier may read the instruction, not a lie state.** H has the same false first answer but scores zero. So the classifier reads something D and I share, the instruction or the fact the falsehood was instructed, and nothing in this design tells those apart.
- **The acts-on-it arm cannot separate anything.** The model corrects its forced wrong answer in about 96 to 100 percent of judged rows in every condition. That is a limit of the two-turn design, not evidence about the state.
- **The SDR pass is narrow.** It clears the 15-point bar by one point, and its interval reaches down to 0.086.
- **The first-token proxy is vacuous.** No maintenance token qualified on any task, so it labels every row as a correction. Its 0.987 to 0.997 agreement just equals the share of corrections.
- **The plan's proxy trigger fired.** "I" opens most calibration replies on every task, so a stem-resolved proxy needs a ruling before any first-token proxy can serve as the patching readout.

**Corrections for the lead.**
- **Cross-check disagreements:** there are 7, all involving UNCLEAR, and none between MAINTAINED and CORRECTED. The 21 in the lead's summary is the number of rows where either judge said UNCLEAR.
- **Ledger ceilings:** they sum to $21, above the $20 cap. Actual spend was $2.71, all settled.

I copied the five ledgers, the five label files with their manifests, and the final readings into the results folder. Every copy matches its source by checksum. The three judge caches stay out because they hold full prompts. Their checksums and sizes are listed in the hand-back.

Files are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/`:
- reports/07-handback.md
- results/d2/readings_final.json
- results/d2/readings_final.md
- results/d2/judge/

The patching ruling and the independent review are the orchestrator's.
