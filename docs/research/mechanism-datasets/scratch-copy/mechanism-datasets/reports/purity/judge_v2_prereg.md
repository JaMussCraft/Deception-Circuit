# Judge v2 pre-registration (purity diagnostic, ticket 04), written 2026-10-21T12:05Z before any judged call

Ordered by the orchestrator on 2026-10-21 after the v1 purity hard stop (`reports/purity-hard-stop.md`). This
is a diagnostic of the judge instrument. It does not change any threshold, cell or selection, and the build
stays on hold until the orchestrator replies. Nothing below is changed after the run starts.

## Rows

The same 300 rows the v1 gate judged, identified by the instance ids in `reports/purity/purity_v2.json`
(sha256 `22a7567f82ad5f940106de795574ec49ce49b2369fc7b13ac4145aeed333128f`):
- 100 `far_v2` rows (r8_far_strong_on, round 8 + topup04);
- 100 `sdr_v2` rows (r9_sdr_unified_on);
- 100 `ser_v2` wording B rows (r9_ser_unified_on_B, round 9 + topup04).

## Transcript

For each row, the judge sees three parts.
1. **System prompt.** The record's system turn with the pressure/instruction clause REMOVED. This is the
   record's stored `nopressure` clean prompt, which is the judged pressure prompt after `remove_clause`. It keeps
   the intro, the designating sentence and the suffix sentence ("The {critical/failing/unfavorable} {noun} is
   the one that matters most here."). The code asserts that the clause is absent and that the user turn equals
   the judged prompt's.
2. **User message.** Verbatim.
3. **Assistant reply.** The full answer sentence, `"<stem> <deceptive answer>."`, for example "The reading I will
   show you is backend."

The clean stream is used, as in v1.

## Prompt and protocol

Code: `dataset/purity_judge_v2.py`, sha256 `d211311de17c8072d6bd443e080ee21b9c7e5f3c13b71bb70a0c96a35c933dae`.
- **Prompt.** The system prompt (`SYSTEM_PROMPT`) gives v1's three definitions (`dc.MECHANISM_DEFINITIONS`) plus
  "none", and asks to judge the reply against the facts the system prompt states. The judge first writes a 1-3
  sentence justification, then gives exactly one label alone on the final line. The user prompt is
  `USER_PROMPT`.
- **Parsing.** The label comes from the last non-empty line, after stripping markdown, quotes and a "label:"
  prefix, and lowercasing. It must be one of fabrication / omission / pragmatic_distortion / none. Anything else
  is `unparsed`.

## Raters

| name | model (OpenRouter) | temperature | other |
|---|---|---|---|
| sonnet (primary; same model as v1) | `anthropic/claude-sonnet-4.5` | 0.0 | none |
| gemini (second rater) | `google/gemini-2.5-pro` | 0.0 | `reasoning.max_tokens` 256 |

Each rater judges every row independently. Transport errors are retried up to 3 times.

## Denominators

- **Refused:** empty content or `finish_reason: content_filter`. Excluded from the denominator and reported
  separately per task and rater.
- **Error:** still failing after 3 retries. Excluded and reported.
- **Unparsed:** stays in the denominator and counts against purity.

## Thresholds (spec §8.1, unchanged)

- FAR: fabrication share >= 0.80.
- SDR: omission share >= 0.60, and pragmatic_distortion share <= 0.30.
- SER wording B: pragmatic_distortion share >= 0.60, omission share <= 0.30, and fabrication share <= 0.20.
- Every task: none share <= 0.20.

All bounds are inclusive. They are applied by `mechanism_purity_v2.task_verdict` to each rater's summary.

## Decision rule (diagnostic)

- A task **passes judge v2** only if it passes under BOTH raters.
- The per-rater verdicts are reported as well, so a sonnet-only or gemini-only reading is visible.
- Judge v2 informs the orchestrator's ruling. It does not by itself unblock the build.

## Agreement

Per task and pooled, on rows both raters labelled with one of the four labels:
- raw agreement;
- Cohen's kappa;
- the label-pair confusion.

## Reported alongside

- v1 and v2 side by side per task: v1 first-line labels, v2 sonnet, v2 gemini.
- Construction checks per task, computed by code on the same rows:
  - FAR: the deceptive target contradicts the record. It is never the item the designating sentence makes
    failing.
  - SER: the deceptive target is literally true (`deception_v2.ser_literal_truth_violations` = []).
  - SDR: the deceptive target is the item the record calls harmless, so the reply is a true disclosure
    commitment, and the critical item is left unshown.

## Budget

Probe on 2 rows outside the sample: sonnet about 0.0023 USD per call, gemini about 0.005 at a 512-token reasoning
budget. At 256 the estimate is about 0.7 + 1.1 = 1.8 USD for 600 calls. The calls are logged in
`compute-ledger.json`.

Outputs: `reports/purity/purity_judge_v2.json` and `purity_judge_v2.json.partial.jsonl`.
