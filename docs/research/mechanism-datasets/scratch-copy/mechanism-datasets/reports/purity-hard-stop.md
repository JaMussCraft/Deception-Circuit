# Purity hard stop: FAR and SDR fail the v2 mechanism-purity gate (spec §8.1, §10(i)), 2026-10-20

**Superseded 2026-10-21 by spec §14.G11 (user decision).** The build proceeds on construction-based purity, and
these judge results are recorded as a limitation. The diagnostics that followed (clause-form split, judge v2,
construction checks) are in `reports/04-purity-diagnostics.md`. This file is kept as the record of the v1 gate.

**The pre-registered purity gate fails for `far_v2` and `sdr_v2`.** SER wording B passes. Under spec §10(i)
and ticket 04, a judge failure on FAR, SDR or the selected SER wording is a hard stop. No full build was
submitted and no cell was substituted. This report gives the evidence. It proposes no change of mechanism,
cell, judge or threshold; those decisions are the user's.

| task | cell(s) judged | rows | expected label share | gate line | cross-label | none | verdict |
|---|---|---|---|---|---|---|---|
| far_v2 | r8_far_strong_on (round 8 + top-up) | 100 | fabrication **0.54** | >= 0.80 | omission 0.13, pragmatic_distortion 0.33 | 0.00 | **fail** |
| sdr_v2 | r9_sdr_unified_on (round 9) | 100 | omission **0.20** | >= 0.60 | pragmatic_distortion 0.20 (<= 0.30), fabrication 0.01 | 0.00 | **fail** |
| ser_v2 (B) | r9_ser_unified_on_B (round 9 + top-up) | 100 | pragmatic_distortion 0.73 | >= 0.60 | omission 0.25 (<= 0.30), fabrication 0.01 (<= 0.20) | 0.00 | pass |

SDR's figure counts 59 judge refusals (empty replies) in the denominator, as v1 did. Excluding them does not
change the verdict (section 3).

## 1. What was run

- **Judge.** `dataset/mechanism_purity_v2.py`, which reuses v1's `judge` and `readable_transcript`
  (`dataset/mechanism_purity_check.py`) unchanged: the same system and user prompts, the three
  `dc.MECHANISM_DEFINITIONS`, `anthropic/claude-sonnet-4.5` at temperature 0 via OpenRouter. The transcript is
  the clean-stream pressure prompt; the answer is the deceptive target. The label is the reply's first line.
  Transport errors are retried up to 3 times. Empty, error and unparsed replies stay in the denominator.
- **Rows.** The selected cells' Contingent Survivors from `reports/pilots/round{8,9}/`, pooled with a top-up
  rerun of the same cells at seed 4304 (`reports/pilots/topup04/`), deduplicated by instance id, then 100
  sampled per task with seed 42. Pools: FAR 125 (71 + 54), SDR 133, SER-B 151 (70 + 81). Only wording B passed
  the pilot, so only B was judged (§14.G4).
- **Output.** `reports/purity/purity_v2.json` (confusion, purity, cross-labels, none share, per-polarity
  confusion, verdicts, gate, every verdict with its justification) and the per-call log
  `reports/purity/purity_v2.json.partial.jsonl`.

## 2. Confusion per task and designation polarity (pre-registered run)

| task | polarity | fabrication | omission | pragmatic_distortion | none | empty (refused) |
|---|---|---|---|---|---|---|
| far_v2 | inversion (79) | 45 | 10 | 24 | 0 | 0 |
| far_v2 | identity (21) | 9 | 3 | 9 | 0 | 0 |
| sdr_v2 | inversion (80) | 1 | 15 | 16 | 0 | 48 |
| sdr_v2 | identity (20) | 0 | 5 | 4 | 0 | 11 |
| ser_v2 B | inversion (52) | 1 | 12 | 39 | 0 | 0 |
| ser_v2 B | identity (48) | 0 | 13 | 34 | 0 | 1 |

## 3. Diagnostics (none of them changes the verdict)

**SDR refusals.** 59 of the 100 SDR calls returned no content: `finish_reason: content_filter`,
`native_finish_reason: refusal`, provider Amazon Bedrock (three raw responses inspected). Re-sending all 60
refused rows (59 SDR, 1 SER) with OpenRouter routed to the Anthropic provider only, same judge and prompt, gave
58 SDR refusals again, 1 SDR pragmatic_distortion and 1 SER omission
(`reports/purity/purity_v2_supplementary_empties.{jsonl,json}`). So the model itself declines these transcripts;
the refusals are spread over 17 of the 20 SDR clauses and are 48 inversion, 11 identity. On the 42 SDR rows the
judge did answer, omission is 20 (0.48) and pragmatic_distortion 21 (0.50). That is below the 0.60 purity
line and above the 0.30 cross-label line whatever the refused rows would have been labelled.

**Label-first judge protocol.** The v1 prompt asks for the label on the first line and the justification
after it. In several replies the justification reconsiders the label ("Wait, let me reconsider ...
fabrication"). Re-reading each reply's last mechanism word when it says it reconsiders
(`reports/purity/purity_v2_self_revision_diagnostic.json`):
- FAR: 19 of 33 pragmatic_distortion labels revise to fabrication and 1 to omission. Fabrication would be 0.73,
  still below 0.80.
- SER-B: 9 of 73 pragmatic_distortion labels revise to omission. Omission would be 0.34, above the 0.30
  cross-label line, so SER-B would also fail.
- SDR: no revisions.
This is the pre-registered judge; the revised figures were not used for any decision.

**What the judge says, in its own justifications.**
- FAR: answering "the wrong result" to "Which result is failing?" is read as fabrication most often, but a
  third of first-line labels call it pragmatic distortion ("a technically true statement ... X is one of the
  two readings") and 13 call it omission ("withholds the true information").
- SDR and SER: the same forced choice between two items, under an instruction to show or point to "the wrong
  result", is labelled omission and pragmatic distortion in roughly equal parts for SDR and at about 3 to 1 for
  SER. Many SDR and SER justifications mention that the system turn told the assistant to give the wrong result.
- This is the situation v1's judge was written to detect: with a one-word readout, the judge does not
  separate SDR from SER cleanly, and it does not read FAR's instructed wrong answer as unambiguous fabrication.

## 4. Spend

| item | GPU-h reserved after reconcile | actual | OpenRouter calls | approx USD |
|---|---|---|---|---|
| top-up rerun, job 23060023 (gpuA100x4-interactive, bgrb) | 0.25 | 0.095 (341 s) | | |
| pre-registered gate | | | 300 | 0.60 |
| probes + supplementary re-sends | | | 63 | 0.07 |

Ticket 04 is at 0.25 of 16 reserved GPU-h. The whole feature is at 7.5 of 60.

## 5. State left behind

- The full builder (`dataset/build_deception_v2.py`, `scripts/build_v2.sbatch`), its tests and the
  reproducibility test are written and pass on CPU in both envs. No `far_v2`, `sdr_v2` or `ser_v2` dataset
  exists; nothing under `data/datasets/` or `outputs/` was written.
- The `--no-model` dry path ran on all three selected cells with the length window 94-106 (ticket 04 report).
- The ticket stays `claimed` with this report as its blocker.
