# SDR shared head position technical evidence

[Final scientific review](final-report-review.md). Earlier ca41 report bytes remain unchanged.

## Frozen scope and evidence

Source 2949214; protocol `b2c7fd65ccb67e93f463553044569248fe85a80b8e1bd72ffef28df2cb3b5fa0`; science `fd0bf5f1415b4ea951d6396753b64ad7c0061d883eeca28960b55a9bf9423b6e`; provenance `952ef49022dc4d676080a9a5d13a8c37954327014a4c4c3ecb6f5a76173af297`. Main assembly `d002052b4a1896ee87fbb511699bf081b033cf733082caea4b0592810c818082`; joined `b38cea9f1fda182edfd178ec23d8c39a5d44690a6d076982e209b6ed291bb597`; analysis `1b530a2f648309014c56c12ec85d2f14429676952eb1851398b2acc0dfb3d5dd`.

[Spec](spec.md); [design review](design-review.md); [main integrity](main-integrity/actual-review.md); [calibration audit](calibration-audit/actual-review.md); [arithmetic verification](scientific-audit/actual-arithmetic-review.json). Dense production artifacts: `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-cue-positions/postprocessing-2949214/analysis` (joined.json, analysis.json, descriptive-digest.json, receipt.json, delivery-receipt.json). Digest pending-audit labels reflect their production timestamp; later independent decisions are recorded separately.

All 384 unchanged input-defined prompts, 640 directed pairs and eight fixtures reused. S32=D∩H∩F and C_S32 retain exact original memberships. early=[0, assistant-header boundary); tail=[boundary, original-prefix end); full=early∪tail. Tail includes supplied assistant header/stem, excludes all generated tokens. These are head-output/query coordinates at o_proj input, not attention source/key/value positions or early/late layers. Sustained ordinary simultaneous multilayer replacement; nonselected heads and all MLPs compute naturally. E changes user examples; T changes system factual truth. One fixed layer/count comparator is not a random-null distribution or activation-importance match.

## Completion and numerical checks

Exactly 528 attempts/terminal batches, 4,224 unique outcomes: 384 fresh baselines + 3,840 interventions. All EOS, maximum 28 tokens; zero capped/error/missing/incomplete rows. 4,220 commitments plus 4 contradictory responses retained. Format_ok 3,580/4,224 is secondary; no format-based denominator filtering. All 4 contradictions occur in S T/retrieval: early 3, tail 0, full 1. Main 4,999 forwards, 15,411 bitwise numerical comparisons, maximum error 0; 480 natural donor banks. Calibration 1,721 forwards/6,648 bitwise comparisons, maximum error 0; its 104 rows (48 forced/56 natural) excluded. No extra job, resume or retry.

Independent arithmetic passed 1,416,357 scalar and 61,566 structure comparisons, zero mismatches. It covers full frozen strata/indicators, transitions/triples with zeros, natural pairs, parent replay and row audit. Dense analysis.json preserves all single-factor/template/fixture/reciprocal-direction/example-alignment strata and matched outside components. These are fixed finite-panel descriptive effects, without p-values/bootstrap/fitted models or outcome-selected subsets.

## Annotation transport and provenance

Two fresh independent blinded raters personally judged all 95 unique views and agreed on every complete tuple; no adjudication. Rater-one first encountered sandbox initialization failure, then automatic-review denial of a scoped file read, and stopped before reading any view. No denied read was retried. The coordinator verified the accepted export and supplied the identical 95 ordered full blind text/options/finish records inline; rater-one used no tools and returned indexed judgments. The coordinator mechanically mapped indices to frozen view IDs and added opaque headers without changing any semantic judgment. Rater-two independently read the blind packet. Both attested freshness, independence and personal reading; mechanical coverage alone cannot prove those properties. The common visible-stem/extra-text format clarification prescribed no view-specific semantic label. No access request remains outstanding.

[Transport resolution](annotation-audit/access-remediation.md); [workflow receipt](annotation-audit/workflow-receipt.json); [coverage](annotation-audit/coverage-receipt.json); [raw indexed judgments](annotation-audit/rater-one-inline-raw.json); [identical inline blind data](annotation-audit/rater-one-inline-views.json). View hash `c3926b9c07e4fd2ec2f5013d489f481ba50d798b133d4961fd649f689cb76cc6`; rater-one 1488f33733c784011a2658cd26a5fcec706a347a3d934c1a56cdd4fa24b16c1c; rater-two d82f9cd75c7b358f4cd5effc787f46a4fdb9ce8323eae7b857238e9790d8dc2d. Independent workflow closure is recorded separately from arithmetic.

## Complete main counts

ED=donor-first-example commitment, R=recipient truth, D=donor truth; identity matches 0 for noncommitments, which retain their own categories. Every denominator fixed; E has no truth change, so D=R.

| Axis | Family | Indicator | n | Base | Early | Tail | Full |
|---|---|---|---:|---:|---:|---:|---:|
| E/report | S | ED | 256 | 46 | 106 | 202 | 206 |
| E/report | S | R | 256 | 170 | 132 | 178 | 174 |
| E/report | S | residual | 256 | 0 | 0 | 0 | 0 |
| E/report | S | format_ok | 256 | 256 | 256 | 256 | 256 |
| E/report | C_S | ED | 256 | 46 | 46 | 7 | 3 |
| E/report | C_S | R | 256 | 170 | 170 | 135 | 131 |
| E/report | C_S | residual | 256 | 0 | 0 | 0 | 0 |
| E/report | C_S | format_ok | 256 | 256 | 256 | 256 | 256 |
| T/report | S | D | 256 | 86 | 177 | 141 | 168 |
| T/report | S | R | 256 | 170 | 79 | 115 | 88 |
| T/report | S | residual | 256 | 0 | 0 | 0 | 0 |
| T/report | S | format_ok | 256 | 256 | 256 | 256 | 256 |
| T/report | C_S | D | 256 | 86 | 73 | 71 | 56 |
| T/report | C_S | R | 256 | 170 | 183 | 185 | 200 |
| T/report | C_S | residual | 256 | 0 | 0 | 0 | 0 |
| T/report | C_S | format_ok | 256 | 256 | 256 | 256 | 256 |
| T/retrieval | S | D | 128 | 0 | 84 | 43 | 99 |
| T/retrieval | S | R | 128 | 128 | 41 | 85 | 28 |
| T/retrieval | S | residual | 128 | 0 | 3 | 0 | 1 |
| T/retrieval | S | format_ok | 128 | 32 | 42 | 35 | 43 |
| T/retrieval | C_S | D | 128 | 0 | 1 | 0 | 0 |
| T/retrieval | C_S | R | 128 | 128 | 127 | 128 | 128 |
| T/retrieval | C_S | residual | 128 | 0 | 0 | 0 | 0 |
| T/retrieval | C_S | format_ok | 128 | 32 | 33 | 31 | 36 |

## Conditional and joint contrasts

Columns are exact count numerators divided by n. Early-alone=early − base; tail-alone=tail − base; early-given-tail=full − tail; tail-given-early=full − early; joint=full − early − tail + base. Balanced fixtures make these numerators/n identical to the prespecified equal-fixture-weight effects.

| Axis | Family | Indicator | n | Early alone | Tail alone | Early given tail | Tail given early | Joint |
|---|---|---|---:|---:|---:|---:|---:|---:|
| E/report | S | ED | 256 | 60 | 156 | 4 | 100 | -56 |
| E/report | S | R | 256 | -38 | 8 | -4 | 42 | 34 |
| E/report | S | residual | 256 | 0 | 0 | 0 | 0 | 0 |
| E/report | S | format_ok | 256 | 0 | 0 | 0 | 0 | 0 |
| E/report | C_S | ED | 256 | 0 | -39 | -4 | -43 | -4 |
| E/report | C_S | R | 256 | 0 | -35 | -4 | -39 | -4 |
| E/report | C_S | residual | 256 | 0 | 0 | 0 | 0 | 0 |
| E/report | C_S | format_ok | 256 | 0 | 0 | 0 | 0 | 0 |
| E/report | S−C_S | ED | 256 | 60 | 195 | 8 | 143 | -52 |
| E/report | S−C_S | R | 256 | -38 | 43 | 0 | 81 | 38 |
| E/report | S−C_S | residual | 256 | 0 | 0 | 0 | 0 | 0 |
| E/report | S−C_S | format_ok | 256 | 0 | 0 | 0 | 0 | 0 |
| T/report | S | D | 256 | 91 | 55 | 27 | -9 | -64 |
| T/report | S | R | 256 | -91 | -55 | -27 | 9 | 64 |
| T/report | S | residual | 256 | 0 | 0 | 0 | 0 | 0 |
| T/report | S | format_ok | 256 | 0 | 0 | 0 | 0 | 0 |
| T/report | C_S | D | 256 | -13 | -15 | -15 | -17 | -2 |
| T/report | C_S | R | 256 | 13 | 15 | 15 | 17 | 2 |
| T/report | C_S | residual | 256 | 0 | 0 | 0 | 0 | 0 |
| T/report | C_S | format_ok | 256 | 0 | 0 | 0 | 0 | 0 |
| T/report | S−C_S | D | 256 | 104 | 70 | 42 | 8 | -62 |
| T/report | S−C_S | R | 256 | -104 | -70 | -42 | -8 | 62 |
| T/report | S−C_S | residual | 256 | 0 | 0 | 0 | 0 | 0 |
| T/report | S−C_S | format_ok | 256 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | S | D | 128 | 84 | 43 | 56 | 15 | -28 |
| T/retrieval | S | R | 128 | -87 | -43 | -57 | -13 | 30 |
| T/retrieval | S | residual | 128 | 3 | 0 | 1 | -2 | -2 |
| T/retrieval | S | format_ok | 128 | 10 | 3 | 8 | 1 | -2 |
| T/retrieval | C_S | D | 128 | 1 | 0 | 0 | -1 | -1 |
| T/retrieval | C_S | R | 128 | -1 | 0 | 0 | 1 | 1 |
| T/retrieval | C_S | residual | 128 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | C_S | format_ok | 128 | 1 | -1 | 5 | 3 | 4 |
| T/retrieval | S−C_S | D | 128 | 83 | 43 | 56 | 16 | -27 |
| T/retrieval | S−C_S | R | 128 | -86 | -43 | -57 | -14 | 29 |
| T/retrieval | S−C_S | residual | 128 | 3 | 0 | 1 | -2 | -2 |
| T/retrieval | S−C_S | format_ok | 128 | 9 | 4 | 3 | -2 | -6 |

S E ED: early +60 alone, +4 given tail; tail +156 alone, +100 given early; joint −56/256. Outside joint −4/256; difference −52/256. S T report D: early +91 alone, +27 given tail; tail +55 alone, −9 given early; joint −64/256, outside −2, difference −62. S T retrieval D: early +84 alone, +56 given tail; tail +43 alone, +15 given early; joint −28/128, outside −1, difference −27. These are conditional contrasts, not evidence of natural redundancy/competition.

## Per-fixture endpoints and signs

Fixture IDs are frozen; n=32 for reporting, 16 for retrieval. Counts and all five contrast numerators permit direct sign checks. Complete additional input strata remain in dense analysis.json.

| Axis | Fixture | Family | Indicator | n | Base | Early | Tail | Full | Early alone | Tail alone | Early given tail | Tail given early | Joint |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E/report | nc-1c66593d98bda82c | S | ED | 32 | 7 | 14 | 24 | 25 | 7 | 17 | 1 | 11 | -6 |
| E/report | nc-1c66593d98bda82c | S | R | 32 | 23 | 12 | 24 | 23 | -11 | 1 | -1 | 11 | 10 |
| E/report | nc-1c66593d98bda82c | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-1c66593d98bda82c | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-1c66593d98bda82c | C_S | ED | 32 | 7 | 7 | 2 | 1 | 0 | -5 | -1 | -6 | -1 |
| E/report | nc-1c66593d98bda82c | C_S | R | 32 | 23 | 23 | 18 | 17 | 0 | -5 | -1 | -6 | -1 |
| E/report | nc-1c66593d98bda82c | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-1c66593d98bda82c | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-7364876512c7d4a8 | S | ED | 32 | 2 | 18 | 30 | 29 | 16 | 28 | -1 | 11 | -17 |
| E/report | nc-7364876512c7d4a8 | S | R | 32 | 18 | 24 | 18 | 19 | 6 | 0 | 1 | -5 | -5 |
| E/report | nc-7364876512c7d4a8 | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-7364876512c7d4a8 | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-7364876512c7d4a8 | C_S | ED | 32 | 2 | 2 | 0 | 0 | 0 | -2 | 0 | -2 | 0 |
| E/report | nc-7364876512c7d4a8 | C_S | R | 32 | 18 | 18 | 16 | 16 | 0 | -2 | 0 | -2 | 0 |
| E/report | nc-7364876512c7d4a8 | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-7364876512c7d4a8 | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-8121f8603d662dcf | S | ED | 32 | 5 | 7 | 24 | 26 | 2 | 19 | 2 | 19 | 0 |
| E/report | nc-8121f8603d662dcf | S | R | 32 | 21 | 19 | 24 | 22 | -2 | 3 | -2 | 3 | 0 |
| E/report | nc-8121f8603d662dcf | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-8121f8603d662dcf | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-8121f8603d662dcf | C_S | ED | 32 | 5 | 5 | 0 | 0 | 0 | -5 | 0 | -5 | 0 |
| E/report | nc-8121f8603d662dcf | C_S | R | 32 | 21 | 21 | 16 | 16 | 0 | -5 | 0 | -5 | 0 |
| E/report | nc-8121f8603d662dcf | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-8121f8603d662dcf | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-afa6c76d06448473 | S | ED | 32 | 2 | 12 | 28 | 29 | 10 | 26 | 1 | 17 | -9 |
| E/report | nc-afa6c76d06448473 | S | R | 32 | 18 | 14 | 20 | 19 | -4 | 2 | -1 | 5 | 3 |
| E/report | nc-afa6c76d06448473 | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-afa6c76d06448473 | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-afa6c76d06448473 | C_S | ED | 32 | 2 | 1 | 0 | 0 | -1 | -2 | 0 | -1 | 1 |
| E/report | nc-afa6c76d06448473 | C_S | R | 32 | 18 | 17 | 16 | 16 | -1 | -2 | 0 | -1 | 1 |
| E/report | nc-afa6c76d06448473 | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-afa6c76d06448473 | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c5f0b2f5f348543e | S | ED | 32 | 8 | 14 | 24 | 24 | 6 | 16 | 0 | 10 | -6 |
| E/report | nc-c5f0b2f5f348543e | S | R | 32 | 24 | 16 | 24 | 24 | -8 | 0 | 0 | 8 | 8 |
| E/report | nc-c5f0b2f5f348543e | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c5f0b2f5f348543e | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c5f0b2f5f348543e | C_S | ED | 32 | 8 | 8 | 4 | 1 | 0 | -4 | -3 | -7 | -3 |
| E/report | nc-c5f0b2f5f348543e | C_S | R | 32 | 24 | 24 | 20 | 17 | 0 | -4 | -3 | -7 | -3 |
| E/report | nc-c5f0b2f5f348543e | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c5f0b2f5f348543e | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c8f3b58353fe5dab | S | ED | 32 | 8 | 6 | 24 | 24 | -2 | 16 | 0 | 18 | 2 |
| E/report | nc-c8f3b58353fe5dab | S | R | 32 | 24 | 14 | 24 | 24 | -10 | 0 | 0 | 10 | 10 |
| E/report | nc-c8f3b58353fe5dab | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c8f3b58353fe5dab | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c8f3b58353fe5dab | C_S | ED | 32 | 8 | 7 | 0 | 0 | -1 | -8 | 0 | -7 | 1 |
| E/report | nc-c8f3b58353fe5dab | C_S | R | 32 | 24 | 23 | 16 | 16 | -1 | -8 | 0 | -7 | 1 |
| E/report | nc-c8f3b58353fe5dab | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-c8f3b58353fe5dab | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-d33131117297333a | S | ED | 32 | 9 | 20 | 23 | 23 | 11 | 14 | 0 | 3 | -11 |
| E/report | nc-d33131117297333a | S | R | 32 | 25 | 22 | 25 | 25 | -3 | 0 | 0 | 3 | 3 |
| E/report | nc-d33131117297333a | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-d33131117297333a | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-d33131117297333a | C_S | ED | 32 | 9 | 10 | 1 | 1 | 1 | -8 | 0 | -9 | -1 |
| E/report | nc-d33131117297333a | C_S | R | 32 | 25 | 26 | 17 | 17 | 1 | -8 | 0 | -9 | -1 |
| E/report | nc-d33131117297333a | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-d33131117297333a | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-fc55cb97246d1634 | S | ED | 32 | 5 | 15 | 25 | 26 | 10 | 20 | 1 | 11 | -9 |
| E/report | nc-fc55cb97246d1634 | S | R | 32 | 17 | 11 | 19 | 18 | -6 | 2 | -1 | 7 | 5 |
| E/report | nc-fc55cb97246d1634 | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-fc55cb97246d1634 | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-fc55cb97246d1634 | C_S | ED | 32 | 5 | 6 | 0 | 0 | 1 | -5 | 0 | -6 | -1 |
| E/report | nc-fc55cb97246d1634 | C_S | R | 32 | 17 | 18 | 16 | 16 | 1 | -1 | 0 | -2 | -1 |
| E/report | nc-fc55cb97246d1634 | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E/report | nc-fc55cb97246d1634 | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-1c66593d98bda82c | S | D | 32 | 9 | 25 | 18 | 23 | 16 | 9 | 5 | -2 | -11 |
| T/report | nc-1c66593d98bda82c | S | R | 32 | 23 | 7 | 14 | 9 | -16 | -9 | -5 | 2 | 11 |
| T/report | nc-1c66593d98bda82c | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-1c66593d98bda82c | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-1c66593d98bda82c | C_S | D | 32 | 9 | 9 | 8 | 8 | 0 | -1 | 0 | -1 | 0 |
| T/report | nc-1c66593d98bda82c | C_S | R | 32 | 23 | 23 | 24 | 24 | 0 | 1 | 0 | 1 | 0 |
| T/report | nc-1c66593d98bda82c | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-1c66593d98bda82c | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-7364876512c7d4a8 | S | D | 32 | 14 | 19 | 16 | 18 | 5 | 2 | 2 | -1 | -3 |
| T/report | nc-7364876512c7d4a8 | S | R | 32 | 18 | 13 | 16 | 14 | -5 | -2 | -2 | 1 | 3 |
| T/report | nc-7364876512c7d4a8 | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-7364876512c7d4a8 | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-7364876512c7d4a8 | C_S | D | 32 | 14 | 14 | 12 | 11 | 0 | -2 | -1 | -3 | -1 |
| T/report | nc-7364876512c7d4a8 | C_S | R | 32 | 18 | 18 | 20 | 21 | 0 | 2 | 1 | 3 | 1 |
| T/report | nc-7364876512c7d4a8 | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-7364876512c7d4a8 | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-8121f8603d662dcf | S | D | 32 | 11 | 23 | 16 | 21 | 12 | 5 | 5 | -2 | -7 |
| T/report | nc-8121f8603d662dcf | S | R | 32 | 21 | 9 | 16 | 11 | -12 | -5 | -5 | 2 | 7 |
| T/report | nc-8121f8603d662dcf | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-8121f8603d662dcf | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-8121f8603d662dcf | C_S | D | 32 | 11 | 8 | 10 | 6 | -3 | -1 | -4 | -2 | -1 |
| T/report | nc-8121f8603d662dcf | C_S | R | 32 | 21 | 24 | 22 | 26 | 3 | 1 | 4 | 2 | 1 |
| T/report | nc-8121f8603d662dcf | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-8121f8603d662dcf | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-afa6c76d06448473 | S | D | 32 | 14 | 20 | 16 | 17 | 6 | 2 | 1 | -3 | -5 |
| T/report | nc-afa6c76d06448473 | S | R | 32 | 18 | 12 | 16 | 15 | -6 | -2 | -1 | 3 | 5 |
| T/report | nc-afa6c76d06448473 | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-afa6c76d06448473 | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-afa6c76d06448473 | C_S | D | 32 | 14 | 10 | 10 | 6 | -4 | -4 | -4 | -4 | 0 |
| T/report | nc-afa6c76d06448473 | C_S | R | 32 | 18 | 22 | 22 | 26 | 4 | 4 | 4 | 4 | 0 |
| T/report | nc-afa6c76d06448473 | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-afa6c76d06448473 | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c5f0b2f5f348543e | S | D | 32 | 8 | 25 | 22 | 24 | 17 | 14 | 2 | -1 | -15 |
| T/report | nc-c5f0b2f5f348543e | S | R | 32 | 24 | 7 | 10 | 8 | -17 | -14 | -2 | 1 | 15 |
| T/report | nc-c5f0b2f5f348543e | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c5f0b2f5f348543e | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c5f0b2f5f348543e | C_S | D | 32 | 8 | 6 | 5 | 3 | -2 | -3 | -2 | -3 | 0 |
| T/report | nc-c5f0b2f5f348543e | C_S | R | 32 | 24 | 26 | 27 | 29 | 2 | 3 | 2 | 3 | 0 |
| T/report | nc-c5f0b2f5f348543e | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c5f0b2f5f348543e | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c8f3b58353fe5dab | S | D | 32 | 8 | 23 | 18 | 23 | 15 | 10 | 5 | 0 | -10 |
| T/report | nc-c8f3b58353fe5dab | S | R | 32 | 24 | 9 | 14 | 9 | -15 | -10 | -5 | 0 | 10 |
| T/report | nc-c8f3b58353fe5dab | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c8f3b58353fe5dab | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c8f3b58353fe5dab | C_S | D | 32 | 8 | 10 | 10 | 12 | 2 | 2 | 2 | 2 | 0 |
| T/report | nc-c8f3b58353fe5dab | C_S | R | 32 | 24 | 22 | 22 | 20 | -2 | -2 | -2 | -2 | 0 |
| T/report | nc-c8f3b58353fe5dab | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-c8f3b58353fe5dab | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-d33131117297333a | S | D | 32 | 7 | 26 | 20 | 25 | 19 | 13 | 5 | -1 | -14 |
| T/report | nc-d33131117297333a | S | R | 32 | 25 | 6 | 12 | 7 | -19 | -13 | -5 | 1 | 14 |
| T/report | nc-d33131117297333a | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-d33131117297333a | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-d33131117297333a | C_S | D | 32 | 7 | 3 | 3 | 1 | -4 | -4 | -2 | -2 | 2 |
| T/report | nc-d33131117297333a | C_S | R | 32 | 25 | 29 | 29 | 31 | 4 | 4 | 2 | 2 | -2 |
| T/report | nc-d33131117297333a | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-d33131117297333a | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-fc55cb97246d1634 | S | D | 32 | 15 | 16 | 15 | 17 | 1 | 0 | 2 | 1 | 1 |
| T/report | nc-fc55cb97246d1634 | S | R | 32 | 17 | 16 | 17 | 15 | -1 | 0 | -2 | -1 | -1 |
| T/report | nc-fc55cb97246d1634 | S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-fc55cb97246d1634 | S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-fc55cb97246d1634 | C_S | D | 32 | 15 | 13 | 13 | 9 | -2 | -2 | -4 | -4 | -2 |
| T/report | nc-fc55cb97246d1634 | C_S | R | 32 | 17 | 19 | 19 | 23 | 2 | 2 | 4 | 4 | 2 |
| T/report | nc-fc55cb97246d1634 | C_S | residual | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/report | nc-fc55cb97246d1634 | C_S | format_ok | 32 | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-1c66593d98bda82c | S | D | 16 | 0 | 13 | 8 | 14 | 13 | 8 | 6 | 1 | -7 |
| T/retrieval | nc-1c66593d98bda82c | S | R | 16 | 16 | 3 | 8 | 2 | -13 | -8 | -6 | -1 | 7 |
| T/retrieval | nc-1c66593d98bda82c | S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-1c66593d98bda82c | S | format_ok | 16 | 8 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-1c66593d98bda82c | C_S | D | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-1c66593d98bda82c | C_S | R | 16 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-1c66593d98bda82c | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-1c66593d98bda82c | C_S | format_ok | 16 | 8 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-7364876512c7d4a8 | S | D | 16 | 0 | 6 | 0 | 6 | 6 | 0 | 6 | 0 | 0 |
| T/retrieval | nc-7364876512c7d4a8 | S | R | 16 | 16 | 7 | 16 | 9 | -9 | 0 | -7 | 2 | 2 |
| T/retrieval | nc-7364876512c7d4a8 | S | residual | 16 | 0 | 3 | 0 | 1 | 3 | 0 | 1 | -2 | -2 |
| T/retrieval | nc-7364876512c7d4a8 | S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-7364876512c7d4a8 | C_S | D | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-7364876512c7d4a8 | C_S | R | 16 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-7364876512c7d4a8 | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-7364876512c7d4a8 | C_S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-8121f8603d662dcf | S | D | 16 | 0 | 13 | 0 | 16 | 13 | 0 | 16 | 3 | 3 |
| T/retrieval | nc-8121f8603d662dcf | S | R | 16 | 16 | 3 | 16 | 0 | -13 | 0 | -16 | -3 | -3 |
| T/retrieval | nc-8121f8603d662dcf | S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-8121f8603d662dcf | S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-8121f8603d662dcf | C_S | D | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-8121f8603d662dcf | C_S | R | 16 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-8121f8603d662dcf | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-8121f8603d662dcf | C_S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-afa6c76d06448473 | S | D | 16 | 0 | 12 | 13 | 16 | 12 | 13 | 3 | 4 | -9 |
| T/retrieval | nc-afa6c76d06448473 | S | R | 16 | 16 | 4 | 3 | 0 | -12 | -13 | -3 | -4 | 9 |
| T/retrieval | nc-afa6c76d06448473 | S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-afa6c76d06448473 | S | format_ok | 16 | 8 | 8 | 7 | 8 | 0 | -1 | 1 | 0 | 1 |
| T/retrieval | nc-afa6c76d06448473 | C_S | D | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-afa6c76d06448473 | C_S | R | 16 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-afa6c76d06448473 | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-afa6c76d06448473 | C_S | format_ok | 16 | 8 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c5f0b2f5f348543e | S | D | 16 | 0 | 14 | 0 | 16 | 14 | 0 | 16 | 2 | 2 |
| T/retrieval | nc-c5f0b2f5f348543e | S | R | 16 | 16 | 2 | 16 | 0 | -14 | 0 | -16 | -2 | -2 |
| T/retrieval | nc-c5f0b2f5f348543e | S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c5f0b2f5f348543e | S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c5f0b2f5f348543e | C_S | D | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c5f0b2f5f348543e | C_S | R | 16 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c5f0b2f5f348543e | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c5f0b2f5f348543e | C_S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c8f3b58353fe5dab | S | D | 16 | 0 | 15 | 11 | 15 | 15 | 11 | 4 | 0 | -11 |
| T/retrieval | nc-c8f3b58353fe5dab | S | R | 16 | 16 | 1 | 5 | 1 | -15 | -11 | -4 | 0 | 11 |
| T/retrieval | nc-c8f3b58353fe5dab | S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c8f3b58353fe5dab | S | format_ok | 16 | 9 | 13 | 9 | 13 | 4 | 0 | 4 | 0 | 0 |
| T/retrieval | nc-c8f3b58353fe5dab | C_S | D | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c8f3b58353fe5dab | C_S | R | 16 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c8f3b58353fe5dab | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-c8f3b58353fe5dab | C_S | format_ok | 16 | 9 | 10 | 6 | 8 | 1 | -3 | 2 | -2 | 1 |
| T/retrieval | nc-d33131117297333a | S | D | 16 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 |
| T/retrieval | nc-d33131117297333a | S | R | 16 | 16 | 16 | 16 | 15 | 0 | 0 | -1 | -1 | -1 |
| T/retrieval | nc-d33131117297333a | S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-d33131117297333a | S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-d33131117297333a | C_S | D | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-d33131117297333a | C_S | R | 16 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-d33131117297333a | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-d33131117297333a | C_S | format_ok | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-fc55cb97246d1634 | S | D | 16 | 0 | 11 | 11 | 15 | 11 | 11 | 4 | 4 | -7 |
| T/retrieval | nc-fc55cb97246d1634 | S | R | 16 | 16 | 5 | 5 | 1 | -11 | -11 | -4 | -4 | 7 |
| T/retrieval | nc-fc55cb97246d1634 | S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-fc55cb97246d1634 | S | format_ok | 16 | 7 | 13 | 11 | 14 | 6 | 4 | 3 | 1 | -3 |
| T/retrieval | nc-fc55cb97246d1634 | C_S | D | 16 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | -1 | -1 |
| T/retrieval | nc-fc55cb97246d1634 | C_S | R | 16 | 16 | 15 | 16 | 16 | -1 | 0 | 0 | 1 | 1 |
| T/retrieval | nc-fc55cb97246d1634 | C_S | residual | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T/retrieval | nc-fc55cb97246d1634 | C_S | format_ok | 16 | 7 | 7 | 9 | 12 | 0 | 2 | 3 | 5 | 3 |

Signs below are positive/zero/negative across eight fixtures.

| Axis | Family | Indicator | Early alone | Tail alone | Early given tail | Tail given early | Joint |
|---|---|---|---|---|---|---|---|
| E/report | S | ED | 7/0/1 | 8/0/0 | 4/3/1 | 8/0/0 | 1/1/6 |
| E/report | S | R | 1/0/7 | 4/4/0 | 1/3/4 | 7/0/1 | 6/1/1 |
| E/report | S | residual | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| E/report | S | format_ok | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| E/report | C_S | ED | 2/4/2 | 0/0/8 | 0/6/2 | 0/0/8 | 2/2/4 |
| E/report | C_S | R | 2/4/2 | 0/0/8 | 0/6/2 | 0/0/8 | 2/2/4 |
| E/report | C_S | residual | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| E/report | C_S | format_ok | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| T/report | S | D | 8/0/0 | 7/1/0 | 8/0/0 | 1/1/6 | 1/0/7 |
| T/report | S | R | 0/0/8 | 0/1/7 | 0/0/8 | 6/1/1 | 7/0/1 |
| T/report | S | residual | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| T/report | S | format_ok | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| T/report | C_S | D | 1/2/5 | 1/0/7 | 1/1/6 | 1/0/7 | 1/4/3 |
| T/report | C_S | R | 5/2/1 | 7/0/1 | 6/1/1 | 7/0/1 | 3/4/1 |
| T/report | C_S | residual | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| T/report | C_S | format_ok | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| T/retrieval | S | D | 7/1/0 | 4/4/0 | 8/0/0 | 6/2/0 | 3/1/4 |
| T/retrieval | S | R | 0/1/7 | 0/4/4 | 0/0/8 | 1/1/6 | 5/0/3 |
| T/retrieval | S | residual | 1/7/0 | 0/8/0 | 1/7/0 | 0/7/1 | 0/7/1 |
| T/retrieval | S | format_ok | 2/6/0 | 1/6/1 | 3/5/0 | 1/7/0 | 1/6/1 |
| T/retrieval | C_S | D | 1/7/0 | 0/8/0 | 0/8/0 | 0/7/1 | 0/7/1 |
| T/retrieval | C_S | R | 0/7/1 | 0/8/0 | 0/8/0 | 1/7/0 | 1/7/0 |
| T/retrieval | C_S | residual | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 | 0/8/0 |
| T/retrieval | C_S | format_ok | 1/7/0 | 1/6/1 | 2/6/0 | 1/6/1 | 2/6/0 |

## Cross hardware replay

Fresh A100 baseline/full results compared descriptively to archived H200 parent; no parent answer substituted, no filtering or outcome-based retry. All 1,664 input-matched rows included.

| Group | n | Same category | Same finish | Same format | Same raw text | Same text |
|---|---:|---:|---:|---:|---:|---:|
| all | 1664 | 1654 | 1664 | 1656 | 1636 | 1636 |
| baseline | 384 | 382 | 384 | 379 | 374 | 374 |
| S/full | 640 | 634 | 640 | 640 | 629 | 629 |
| C_S/full | 640 | 638 | 640 | 637 | 633 | 633 |

Same aggregate counts never imply itemwise equivalence. Cross-hardware category agreement 1,654/1,664 and text agreement 1,636/1,664 are descriptive, not bitwise reproduction or independent OOD evidence.

## Interpretation and accounting

The same shared head set supports donor influence at both context and supplied assistant prefix. Tail captures most aggregate example transfer here; early factual transfer is substantial, and effects change with the other region’s replacement. Tail/full proximity does not establish upstream irrelevance; early effects permit propagated influence without isolating natural paths. Ordinary multilayer replacement may overwrite intermediate processing; readout nonlinearities and binary outcomes can create non-additivity. E/T changes have different input locations and intact responsiveness; raw efficacy profiles do not isolate preferential encoding. Contradictory T donors insert alternative facts, so recipient-truth loss does not establish generic damage or clean suppression. No pressure, intent, deception-specific role, latent knowledge, clean selectivity, natural mediation/removal, completeness or OOD claim follows. Old failed gates/stopped grids remain closed. Behavioral identifiability remains the bottleneck; no automatic next experiment.

Fresh calibration 403 A100 GPU-seconds / request 1,200; main 1,109 GPU-seconds / request 3,300. Phase 1,512 actual versus 4,500 reserved GPU-seconds; $0 external API. No resume, retry, wasted allocation or extra job. Same frozen NVIDIA A100-SXM4-40GB class for cal/main; main peak 17.054 GiB. Lead context compactions 7. Earlier ca41 reports and source/data remain unchanged.
