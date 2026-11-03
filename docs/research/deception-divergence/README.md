# Where deception and transparent inversion come apart: listener knowledge, the second turn and a learned partition

This is the handoff page of the deception-divergence direction, a Claude session of Mon 2 to Tue 3 Nov 2026. Its
starting prompt is `START.md`, and its rulings R1 to R15 are in `spec.md`.

## Question

Is there a readout on which deceiving an unaware user (the pressured condition D) and a transparent inversion (I)
actually differ in Llama-3.1-8B-Instruct, with the instruction kept in the operator turn for both? If there is, what
carries the difference: components, a stored state or a learned partition?

## Verdict

No readout in this direction separates deceiving an unaware user from transparent inversion at the pre-registered
bars. The listener-knowledge routes are null on size, with empty flip pools. That covers D1's system-turn sentence
and the phrasing-4 sentence in the user's own turn. The D2 premise passes by one point on SDR, from the classifier arm
alone, and F8's SDR pass is attributed to clause wording. The R15 follow-up with the honest-instructed control labels
(b) on every task, so under R6 iv U1 is closed through D2 as well as through D1. That closure is a consequence of the
ruling, not a demonstration that no listener-knowledge representation exists. D4's four riders closed as F-dd-001 to
F-dd-004. D3 never ran, because D1 showed no honesty override.

## What was found

- **F-dd-001, the static read of the layer 17 quartet.** Both pre-registered static reads fail: head.14.4 ranks 24
  against a cutoff of 16 in Q-composition, and no head of the model reaches the 0.5 copy bar. The routing into
  H24 to H27 is therefore activation-dependent, which fits the parallel route of F-rte-005.
- **F-dd-002, the quartet's attention under the clause.** On FAR and SER the quartet moves its readout attention
  off the designating sentence, onto the items on FAR and onto the pressure clause on SER, and L17H26 is the
  second-largest mover. This is descriptive: there is no interval, and the run does not show that the shift
  carries the effect.
- **F-dd-003, the after-cue sycophancy arm.** Patching S_all only after the cue tokens removes 0.662 of the
  cue-induced gap, against 0.724 over the full span, and the early-MLP increment falls from 0.226 to 0.080. The
  null spread is no narrower after the cue, and F-rte-008 is unchanged.
- **F-dd-004, SDR on the B1 code path.** SDR is query-side like FAR and SER (0.524 against -0.002 for keys), so the
  key-side contrast of F-sdr-012 does not reproduce on this code path. The quartet loop closes on SDR at 0.546, with
  a lower end only 0.011 above the bar.
- **F-dd-005, D1 listener knowledge and honesty override.** Telling the model that the user can see the instruction
  moves first-token compliance by +2.5, -5.2 and -2.4 points on FAR, SDR and SER, against a 10-point bar. Inversion
  minus D is never a pass, and on the 20 content clauses it is negative on every task.
- **F-dd-006, D1 flip pools.** No system-turn listener sentence moves a D-compliant id to the honest gate, and the
  consequence phrasing moves only 8 of 4,789 SDR ids. A flip needs a swing of 1.0 logit per stream, against at most
  0.73 for any sentence, so an empty pool also fits a small graded effect.
- **F-dd-007, the user-turn acknowledgement.** Phrasing 4 is null on every task (+2.4, +1.1 and +1.2 points), and
  its flip pools hold 0, 1 and 0 ids. The visible arm complies slightly more, the opposite of conditioning a lie on
  the listener not knowing.
- **F-dd-008, the D2 premise.** The second-turn classifier fitted on D against H passes R13 on SDR alone, with a gap
  of 0.160 against a 15-point bar, while FAR is at 0.005 and SER at 0.145. The whole gap sits on predicate-form I
  clauses and is zero on act-form clauses. The acts-on-it arm is uninformative, because the model corrects its
  forced wrong answer in 96 to 100 percent of decided rows.
- **F-dd-009, the R15 follow-up.** With the classifier refitted on D against the honest-instructed mirror HI, every
  task labels (b): on form-matched act-form clauses D and I do not differ at the rate readout (FAR gap 0.010,
  interval 0.000 to 0.028; SDR 0.114, interval 0.000 to 0.250). The joint DT and HT reading lands on instruction
  content on every task, so the classifier reads being told to lie, not having lied.

## What the controls say

The controls point to one reading: every second-turn readout here reads which instruction the system turn contains.
None reads whether the listener is deceived.

- **D2's classifier reads the clause.** Its D-I gap tracks the I clause's form. The gap is zero where I names the
  wrong answer as D does, and it is present only where I's wording differs (F-dd-008).
- **The DT and HT 2x2 lands on instruction content everywhere.** With a true first answer, D's instruction still
  reads as D and the honest one near HI: DT minus HT is 1.000, 0.841 and 0.771 on FAR, SDR and SER, positions on
  the HI-to-D axis with intervals excluding zero. The readout follows the instruction, not the answer's truth.
- **HI exposes what D2's classifier read on each task.** Under the frozen D-against-H classifier, the honest
  instruction HI reads D-like on SER (0.956) and partly on SDR (0.240), but not on FAR (0.005). On SER, D2's
  classifier read the presence of an instruction, and on FAR it did not.
- **The refusal control does not carry the D-I difference.** Ablating the refusal direction leaves SDR's D2 gap at
  0.136. The one D-specific behaviour is a second-turn refusal ("I can't help with that"), seen on SDR and SER and
  removed by the ablation. It is descriptive and outside every rule.

## Open leads for the next synthesis

- **The FAR score-space residual.** FAR shows a descriptive score-space D minus I difference of 2.35 log-odds net
  of the honest control, with an IH interaction of 3.85, which the saturated rate readout cannot register; review 06
  reads it as clause wording (it falls to 1.19 with an interval crossing zero where D's lie word matches I's) and
  advises against a score-space re-read of the existing clauses. The one design worth a new ruling, if listener
  knowledge is pursued again, is a wording-controlled I pool: each I clause is D's own clause plus a transparency
  frame and IH is HI plus the same frame, an exact frame-by-honesty 2x2 with a pre-registered log-odds statistic,
  intervals by D and by I clause, a bar sized against the D-HI span, about 0.5 GPU-hours and no judge.
- **A form-matched readout beyond the first token.** Every reading here is a first-token margin or a first-token
  feature. Free generation and later tokens were not tested for a listener contrast (review 03).
- **The second-turn refusal under D.** It is the only behaviour seen in D and not in I or H. A pre-registered
  refusal-share readout would test it, which review 04 recommended.

## What was not done

- **D3, the honesty override.** It was closed by the D1 null under the frozen rule.
- **U1, the learned three-way partition.** It was never admitted: neither the D1 route nor the D2 route under
  R6 iv met its bar, and no U1 code was written.
- **U2's remainder.** Weight masking, parameter decomposition and LoRA diffing stayed deferred, as START planned.
  Only its static read ran, as D4 rider (d).
- **The D2 patching.** Position-resolved patching of the second-turn readout was never ruled, because no D-I
  separation survived the controls.

## Budget

| item | reserved | actual | cap |
|---|---|---|---|
| GPU-hours, 11 ledger reservations | 10.58 | 3.38 | 55 |
| OpenRouter, the D2 judge only | 5.00 reserve | 2.71 USD over 4,064 calls | 20 USD |

The GPU actual is 12,181 s in the ledger: 2.91 GPU-hours before the R15 follow-up and 0.47 for job 50161975. The
two cancelled reservations, r-003 and r-009, used no GPU time. The two failed ones, r-007 and r-010, used 162 s.

## Pointers

- **Rules and plans.** `spec.md` (R1 to R15), `START.md`, `plans/D2-plan.md` and `plans/D2-followup-plan.md`.
- **Hand-backs.** `reports/01-handback.md` (D1), `02` (D4 riders), `03` (F-rte-008 correction), `06` (D1
  follow-up and phrasing 4), `07` (D2 premise), `10` (R15 follow-up) and `11-findings-handback.md` (findings rows).
- **Reviews.** `reviews/01-d4-review.md`, `02-d1-review.md`, `03-d1-followup-review.md`, `04-d2-review.md`,
  `05-d2-followup-plan-review.md` and `06-d2-followup-review.md`, whose Question 2 logit table belongs beside
  F-dd-009.
- **Results in the repository.** `results/d1/`, `results/d4c/`, `results/d2/` and `results/d2_followup/`. Raw
  features, scores and patterns are under `outputs/_analyses/deception-divergence/`, which is local only.
- **GPU jobs.** D4 riders: Delta 23443932 (a), 23443933 (b) and Bridges-2 50132625 (c); rider (d) ran on CPU. D1:
  Bridges-2 50145353. Phrasing 4: 50152632. D2 premise: 50155519, the path of record under R14, after 50153789
  stopped at its precision guard. R15 follow-up: 50161975, log at `results/d2_followup/job50161975.log`.
- **Code.** `scripts/d1_visibility.py`, `scripts/d1_followup.py`, `scripts/d4_static_quartet.py`,
  `scripts/route_closure_readings.py`, `scripts/d2_rows.py`, `scripts/d2_premise.py`, `scripts/d2_followup.py`,
  `spontaneous/d2_judge.py`, the after-cue arm in `spontaneous/patching.py`, the attention capture in
  `component_analysis/attention_patterns.py`, the job wrappers under `scripts/jobs/` and `jobs/`, and the inputs
  `data/d2/d2_inputs.json` and `data/d2/d2_followup_clauses.json`.
- **Findings.** F-dd-001 to F-dd-009 in `docs/research/FINDINGS.md`.
