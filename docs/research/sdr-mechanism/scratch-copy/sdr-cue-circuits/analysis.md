# SDR cue circuit transplant technical analysis

2026-10-25. Arithmetic, coverage and annotation-binding review **PASS**; final narrative decision: [review](final-report-review.md).

## Scope and provenance

Original source `ca41bfdb2fd4e4c4c784eabd321ea75e41a45299`; science `9a3a3b645fa91ad7b7e84f19288919b5fbcc98aec7c9ecf6452713561f4fb9a9`; protocol `e0fc2da612fe08d29a9f913976e6e83341ef91b18405325356b6e49ad7ceeae8`. Main assembly `58795bf93f7ac929a8ae2c57dd704bbaad6eadca57073bd84b8afa2eba45fab4`; joined `8970633e8d63a3ba063196feec3e1c26b09e2fd2a21ed27c64a10a88be5bce2f`; analysis `c2c05c974ea1e21ef50035696ed8114f85d2cf569b5c176db14ccf884a898d70`.

Eight named input-defined fixtures,256 report/128 retrieval baselines,640 directed pairs per family,14 families,8,960 interventions and9,344 main completions. E reverses permitted-example order alone; T reverses damaging truth alone. Retrieval has T only. Sustained head o_proj-input replacement covers original prefix positions at every forward, never generated positions; other heads and all32 MLPs compute naturally. All112 forced-cap calibration slots excluded.

D69/H56/F68 are original masks; S32=D∩H∩F; A22=D−(H∪F); B11=(D∩H)−F; J33=D−F=A∪B. Each C mask matches target layer/count outside D∪H∪F; C_J=C_A∪C_B. One fixed comparator is not a random-null distribution or activation-importance match.

[Specification](spec.md); [independent review](scientific-audit/actual-review.md); [verification](scientific-audit/actual-results-verification.json); [independent counts](scientific-audit/independent-descriptive-counts.json); [complete contrast supplement](scientific-audit/independent-complete-contrasts.json). Production analysis, digest and receipts remain at `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-cue-circuits/postprocessing-ca41bfd`.

The independent `independent-complete-contrasts.json` supplies frozen requested presentation tables not emitted by the production JSON; it adds no new estimands. It presents complete input-stratum contrast components, per-fixture matched task means and separate natural endpoint/transition tables.

## Completion and integrity

All9,344 main rows reached EOS:9,337 commitments and7 contradictions, all retained. All33,974 main full-vocabulary controls passed bitwise, maximum error0. Calibration also passed29,232 comparisons. Two fresh independent blinded raters covered all101 views with complete tuple agreement. Independent arithmetic reconstructed2,467,664 scalar comparisons without discrepancy, including1,596 summary tables,1,163,484 triple cells and129,276 transitions. No output-selected primary population.

Format is separate:7,964/9,344 format_ok. Intact retrieval was128/128 semantically correct but31/128 format_ok. All seven contradictions occur in T/retrieval: D2,F3,S2.

## Main endpoint counts

R=recipient-truth commitment; D=donor-truth commitment; ED=donor-first-example commitment. Reporting denominators256; retrieval128. Intact E ED46, report R170; T report D86; retrieval R128/D0. E R=D because truth is unchanged.

| Family | E ED /256 | E R /256 | T report R /256 | T retrieval R /128 | T retrieval D /128 | Contradictions |
|---|---:|---:|---:|---:|---:|---:|
| D | 207 | 173 | 87 | 23 | 103 | 2 |
| H | 209 | 171 | 86 | 27 | 101 | 0 |
| F | 214 | 166 | 85 | 24 | 101 | 3 |
| S | 208 | 174 | 86 | 28 | 98 | 2 |
| A | 11 | 139 | 163 | 126 | 2 | 0 |
| B | 144 | 150 | 114 | 115 | 13 | 0 |
| J | 102 | 162 | 128 | 120 | 8 | 0 |
| C_D | 7 | 135 | 220 | 128 | 0 | 0 |
| C_H | 82 | 206 | 192 | 128 | 0 | 0 |
| C_F | 64 | 190 | 207 | 128 | 0 | 0 |
| C_S | 3 | 131 | 198 | 128 | 0 | 0 |
| C_A | 56 | 180 | 181 | 128 | 0 | 0 |
| C_B | 46 | 170 | 170 | 128 | 0 | 0 |
| C_J | 55 | 179 | 178 | 128 | 0 | 0 |

E target-minus-outside ED contrasts D/H/F/S/A/B/J:200,127,150,205,−45,98,47 divided by256. T retrieval target-minus-outside R:−105,−101,−104,−100,−2,−13,−8 divided by128. Outside reporting effects are substantial and signed.

## Fixture robustness

Rank order0,1,2,3,4,9,11,12: four lab then four audit. Values are patched-minus-intact counts,32 report or16 retrieval rows per fixture. Descriptive finite-panel counts do not provide population inference.

| Family | E ED deltas by rank | E R deltas by rank | T report R deltas by rank | T retrieval R deltas by rank |
|---|---|---|---|---|
| D | 26, 16, 22, 22, 28, 18, 16, 13 | 4, 0, 0, 0, 0, 0, 0, -1 | -2, -16, -10, -2, -4, -14, -16, -19 | -16, -16, -15, -16, -9, -14, -15, -4 |
| H | 28, 16, 21, 21, 28, 19, 16, 14 | 2, 0, 1, 1, 0, -1, 0, -2 | -2, -16, -10, -2, -4, -14, -16, -20 | -16, -16, -16, -16, -7, -14, -15, -1 |
| F | 28, 16, 22, 23, 28, 19, 17, 15 | 2, 0, 0, -1, 0, -1, -1, -3 | -2, -16, -10, -3, -4, -14, -16, -20 | -16, -16, -16, -16, -7, -15, -16, -2 |
| S | 28, 16, 21, 22, 28, 18, 16, 13 | 2, 0, 1, 2, 0, 0, 0, -1 | -2, -16, -10, -2, -4, -15, -16, -19 | -16, -16, -16, -15, -7, -14, -15, -1 |
| A | -1, -5, -5, -5, -2, -4, -8, -5 | -1, -5, -5, -1, -2, -4, -8, -5 | 1, 1, -1, 1, 0, -1, -6, -2 | 0, 0, 0, -2, 0, 0, 0, 0 |
| B | 17, 13, 9, 15, 21, 11, 4, 8 | 3, -9, -1, -3, 3, -9, -2, -2 | -5, -7, -5, -3, -1, -8, -13, -14 | -1, 0, 0, -4, 0, -4, -4, 0 |
| J | 12, 8, 3, 7, 11, 9, 2, 4 | 2, -2, -1, -1, 3, -7, -6, 4 | 0, -7, -2, -2, 0, -9, -10, -12 | 0, 0, 0, -5, 0, -2, -1, 0 |
| C_D | -1, -8, -5, -5, -1, -3, -8, -8 | -1, -8, -5, -1, -1, -3, -8, -8 | 10, 7, 11, 9, 4, 3, 0, 6 | 0, 0, 0, 0, 0, 0, 0, 0 |
| C_H | 5, 5, 7, 5, 7, 3, 0, 4 | 5, 5, 7, 5, 7, 3, 0, 4 | 6, 1, 6, 3, 3, 1, 0, 2 | 0, 0, 0, 0, 0, 0, 0, 0 |
| C_F | 6, 0, 6, 3, 1, 0, 0, 2 | 6, 0, 6, 5, 1, 0, 0, 2 | 7, 4, 10, 7, 4, 1, 0, 4 | 0, 0, 0, 0, 0, 0, 0, 0 |
| C_S | -1, -7, -5, -5, -2, -6, -8, -9 | -1, -7, -5, -1, -2, -6, -8, -9 | 9, 5, 5, 6, 2, 1, -4, 4 | 0, 0, 0, 0, 0, 0, 0, 0 |
| C_A | 4, 1, 2, 2, 0, 0, 0, 1 | 4, 1, 2, 2, 0, 0, 0, 1 | 3, 0, 2, 3, 1, 1, 0, 1 | 0, 0, 0, 0, 0, 0, 0, 0 |
| C_B | 0, 0, 1, 0, 0, 0, -1, 0 | 0, 0, 1, 0, 0, 0, -1, 0 | 0, 1, 0, 0, 0, 0, -1, 0 | 0, 0, 0, 0, 0, 0, 0, 0 |
| C_J | 4, 1, 2, 1, 0, 0, 0, 1 | 4, 1, 2, 1, 0, 0, 0, 1 | 0, 2, 2, 2, 1, 1, 0, 0 | 0, 0, 0, 0, 0, 0, 0, 0 |

D/H/F/S increase E ED and decrease T R in both tasks in every fixture. A decreases E ED/R in all8; T report effects mixed, retrieval changes in1fixture. B increases E ED/decreases T report R in all8; retrieval changes in4. J increases E ED in8, decreases T report R in6 and retrieval R in3. E aggregate R stability does not imply per-item preservation.

## Per-fixture raw anchors

Recipient→patched counts; ED/report R denominator32, retrieval R denominator16.

| Family | Rank | E ED | E R | T report R | T retrieval R |
|---|---:|---:|---:|---:|---:|
| D | 0 | 1→27 | 17→21 | 17→15 | 16→0 |
| D | 1 | 8→24 | 24→24 | 24→8 | 16→0 |
| D | 2 | 5→27 | 21→21 | 21→11 | 16→1 |
| D | 3 | 5→27 | 17→17 | 17→15 | 16→0 |
| D | 4 | 2→30 | 18→18 | 18→14 | 16→7 |
| D | 9 | 7→25 | 23→23 | 23→9 | 16→2 |
| D | 11 | 8→24 | 24→24 | 24→8 | 16→1 |
| D | 12 | 10→23 | 26→25 | 26→7 | 16→12 |
| H | 0 | 1→29 | 17→19 | 17→15 | 16→0 |
| H | 1 | 8→24 | 24→24 | 24→8 | 16→0 |
| H | 2 | 5→26 | 21→22 | 21→11 | 16→0 |
| H | 3 | 5→26 | 17→18 | 17→15 | 16→0 |
| H | 4 | 2→30 | 18→18 | 18→14 | 16→9 |
| H | 9 | 7→26 | 23→22 | 23→9 | 16→2 |
| H | 11 | 8→24 | 24→24 | 24→8 | 16→1 |
| H | 12 | 10→24 | 26→24 | 26→6 | 16→15 |
| F | 0 | 1→29 | 17→19 | 17→15 | 16→0 |
| F | 1 | 8→24 | 24→24 | 24→8 | 16→0 |
| F | 2 | 5→27 | 21→21 | 21→11 | 16→0 |
| F | 3 | 5→28 | 17→16 | 17→14 | 16→0 |
| F | 4 | 2→30 | 18→18 | 18→14 | 16→9 |
| F | 9 | 7→26 | 23→22 | 23→9 | 16→1 |
| F | 11 | 8→25 | 24→23 | 24→8 | 16→0 |
| F | 12 | 10→25 | 26→23 | 26→6 | 16→14 |
| S | 0 | 1→29 | 17→19 | 17→15 | 16→0 |
| S | 1 | 8→24 | 24→24 | 24→8 | 16→0 |
| S | 2 | 5→26 | 21→22 | 21→11 | 16→0 |
| S | 3 | 5→27 | 17→19 | 17→15 | 16→1 |
| S | 4 | 2→30 | 18→18 | 18→14 | 16→9 |
| S | 9 | 7→25 | 23→23 | 23→8 | 16→2 |
| S | 11 | 8→24 | 24→24 | 24→8 | 16→1 |
| S | 12 | 10→23 | 26→25 | 26→7 | 16→15 |
| A | 0 | 1→0 | 17→16 | 17→18 | 16→16 |
| A | 1 | 8→3 | 24→19 | 24→25 | 16→16 |
| A | 2 | 5→0 | 21→16 | 21→20 | 16→16 |
| A | 3 | 5→0 | 17→16 | 17→18 | 16→14 |
| A | 4 | 2→0 | 18→16 | 18→18 | 16→16 |
| A | 9 | 7→3 | 23→19 | 23→22 | 16→16 |
| A | 11 | 8→0 | 24→16 | 24→18 | 16→16 |
| A | 12 | 10→5 | 26→21 | 26→24 | 16→16 |
| B | 0 | 1→18 | 17→20 | 17→12 | 16→15 |
| B | 1 | 8→21 | 24→15 | 24→17 | 16→16 |
| B | 2 | 5→14 | 21→20 | 21→16 | 16→16 |
| B | 3 | 5→20 | 17→14 | 17→14 | 16→12 |
| B | 4 | 2→23 | 18→21 | 18→17 | 16→16 |
| B | 9 | 7→18 | 23→14 | 23→15 | 16→12 |
| B | 11 | 8→12 | 24→22 | 24→11 | 16→12 |
| B | 12 | 10→18 | 26→24 | 26→12 | 16→16 |
| J | 0 | 1→13 | 17→19 | 17→17 | 16→16 |
| J | 1 | 8→16 | 24→22 | 24→17 | 16→16 |
| J | 2 | 5→8 | 21→20 | 21→19 | 16→16 |
| J | 3 | 5→12 | 17→16 | 17→15 | 16→11 |
| J | 4 | 2→13 | 18→21 | 18→18 | 16→16 |
| J | 9 | 7→16 | 23→16 | 23→14 | 16→14 |
| J | 11 | 8→10 | 24→18 | 24→14 | 16→15 |
| J | 12 | 10→14 | 26→30 | 26→14 | 16→16 |
| C_D | 0 | 1→0 | 17→16 | 17→27 | 16→16 |
| C_D | 1 | 8→0 | 24→16 | 24→31 | 16→16 |
| C_D | 2 | 5→0 | 21→16 | 21→32 | 16→16 |
| C_D | 3 | 5→0 | 17→16 | 17→26 | 16→16 |
| C_D | 4 | 2→1 | 18→17 | 18→22 | 16→16 |
| C_D | 9 | 7→4 | 23→20 | 23→26 | 16→16 |
| C_D | 11 | 8→0 | 24→16 | 24→24 | 16→16 |
| C_D | 12 | 10→2 | 26→18 | 26→32 | 16→16 |
| C_H | 0 | 1→6 | 17→22 | 17→23 | 16→16 |
| C_H | 1 | 8→13 | 24→29 | 24→25 | 16→16 |
| C_H | 2 | 5→12 | 21→28 | 21→27 | 16→16 |
| C_H | 3 | 5→10 | 17→22 | 17→20 | 16→16 |
| C_H | 4 | 2→9 | 18→25 | 18→21 | 16→16 |
| C_H | 9 | 7→10 | 23→26 | 23→24 | 16→16 |
| C_H | 11 | 8→8 | 24→24 | 24→24 | 16→16 |
| C_H | 12 | 10→14 | 26→30 | 26→28 | 16→16 |
| C_F | 0 | 1→7 | 17→23 | 17→24 | 16→16 |
| C_F | 1 | 8→8 | 24→24 | 24→28 | 16→16 |
| C_F | 2 | 5→11 | 21→27 | 21→31 | 16→16 |
| C_F | 3 | 5→8 | 17→22 | 17→24 | 16→16 |
| C_F | 4 | 2→3 | 18→19 | 18→22 | 16→16 |
| C_F | 9 | 7→7 | 23→23 | 23→24 | 16→16 |
| C_F | 11 | 8→8 | 24→24 | 24→24 | 16→16 |
| C_F | 12 | 10→12 | 26→28 | 26→30 | 16→16 |
| C_S | 0 | 1→0 | 17→16 | 17→26 | 16→16 |
| C_S | 1 | 8→1 | 24→17 | 24→29 | 16→16 |
| C_S | 2 | 5→0 | 21→16 | 21→26 | 16→16 |
| C_S | 3 | 5→0 | 17→16 | 17→23 | 16→16 |
| C_S | 4 | 2→0 | 18→16 | 18→20 | 16→16 |
| C_S | 9 | 7→1 | 23→17 | 23→24 | 16→16 |
| C_S | 11 | 8→0 | 24→16 | 24→20 | 16→16 |
| C_S | 12 | 10→1 | 26→17 | 26→30 | 16→16 |
| C_A | 0 | 1→5 | 17→21 | 17→20 | 16→16 |
| C_A | 1 | 8→9 | 24→25 | 24→24 | 16→16 |
| C_A | 2 | 5→7 | 21→23 | 21→23 | 16→16 |
| C_A | 3 | 5→7 | 17→19 | 17→20 | 16→16 |
| C_A | 4 | 2→2 | 18→18 | 18→19 | 16→16 |
| C_A | 9 | 7→7 | 23→23 | 23→24 | 16→16 |
| C_A | 11 | 8→8 | 24→24 | 24→24 | 16→16 |
| C_A | 12 | 10→11 | 26→27 | 26→27 | 16→16 |
| C_B | 0 | 1→1 | 17→17 | 17→17 | 16→16 |
| C_B | 1 | 8→8 | 24→24 | 24→25 | 16→16 |
| C_B | 2 | 5→6 | 21→22 | 21→21 | 16→16 |
| C_B | 3 | 5→5 | 17→17 | 17→17 | 16→16 |
| C_B | 4 | 2→2 | 18→18 | 18→18 | 16→16 |
| C_B | 9 | 7→7 | 23→23 | 23→23 | 16→16 |
| C_B | 11 | 8→7 | 24→23 | 24→23 | 16→16 |
| C_B | 12 | 10→10 | 26→26 | 26→26 | 16→16 |
| C_J | 0 | 1→5 | 17→21 | 17→17 | 16→16 |
| C_J | 1 | 8→9 | 24→25 | 24→26 | 16→16 |
| C_J | 2 | 5→7 | 21→23 | 21→23 | 16→16 |
| C_J | 3 | 5→6 | 17→18 | 17→19 | 16→16 |
| C_J | 4 | 2→2 | 18→18 | 18→19 | 16→16 |
| C_J | 9 | 7→7 | 23→23 | 23→24 | 16→16 |
| C_J | 11 | 8→8 | 24→24 | 24→24 | 16→16 |
| C_J | 12 | 10→11 | 26→27 | 26→26 | 16→16 |

## Natural pairs and emitted-answer diagnostic

Natural example/report pairs:82flips/46same/0residual of128; truth/report44flips/84same/0residual of128; truth/retrieval64flips/0same/0residual of64. Intact lexical0 reporting116/256, first example210/256. Lexical identity is now separated from example order.

The secondary emitted-answer diagnostic has46 directed E pairs where intact recipient=donor≠ED, a subset of92 same-answer directed E pairs. A counterexample must be an actual change, recipient=donor≠patch=ED. Counts D3,H3,F7,S3,A0,B13,J4 of46; outsiders0. All256 E pairs remain primary. Positive cases reject universal actual-emitted-answer copying, without proving abstract cue representation. A0 is no counterexample, not proof of copying. Exact IDs remain in independent-descriptive-counts.json.

## Coherent interactions

Per-pair J−A−B+intact, then equal fixture weights. Exact count equivalents below; outside uses C_J−C_A−C_B+intact.

| Arm indicator | Target | Outside | Difference |
|---|---:|---:|---:|
| E/report ED | -7/256 | -1/256 | -6/256 |
| E/report R | 43/256 | -1/256 | 44/256 |
| T/report R | 21/256 | -3/256 | 24/256 |
| T/retrieval R | 7/128 | 0/128 | 7/128 |
| T/retrieval D | -7/128 | 0/128 | -7/128 |

Ordinary simultaneous multilayer replacement can occlude intermediate computation; binary ceilings and unequal mask sizes further constrain rankings. These interactions do not prove natural redundancy, backup or competition. E/T raw amplitudes do not rank encoding preferences. A/B signed E effects differ consistently, so weak union/necessity effects cannot imply unimportance.

## Meaning and limits

S32 largely recapitulates D/H/F neutral cue and factual transfer, linking original masks to shared task/scaffold processing. Contradictory truth donors can overwrite facts, so recipient-truth loss is not clean generic damage or suppression. Reporting choices are not automatically deceptive assertions. No pressure mediation, intent, reporting-time latent knowledge, removal, natural mediation, completeness, OOD transfer, clean selectivity or deception-specific role follows. All earlier validation FAILs and stopped grids remain closed; no automatic experiment or separate v2 evaluation.

Earlier D−F native knockout was strong (.119 remaining accuracy versus matched-null fifth percentile .517); weak reviewed external advantage must not be generalized to native weakness. Earlier sufficiency/necessity replacement backgrounds differ from this neutral sustained-prefix study.

## Accounting

Phase28,800reserved/1,849actual H200 GPU-seconds (663calibration+1,186main),$0API. Operator ledger authoritative: [ledger](ledger.md), [runtime costs](operator/main-runtime-cost-summary-ca41bfd.json). Lead compactions6. H100 port unused; no Bridges-2 transfer/job/reservation. Preserve source/results unmerged/unpushed. No model/GPU/API/notebook or source change was used to write these reports.
