# Deception-specific, honest-specific and shared MLP neurons

This is the handoff page of the neuron-partition direction, a Claude session of Tue 3 to Wed 4 Nov 2026. Its
starting prompt is `START.md`, its rulings R1 to R21 are in `spec.md`, and its two reports are
`reports/05-first-report.md` (the original ladder and the confirmation test) and `reports/13-followups-4nov.md`
(the four pre-registered follow-ups).

## Question

Can the MLP neurons of Llama-3.1-8B-Instruct be partitioned, by attribution against a user-turn transparent
inversion control, into a deception-only class whose ablation removes the deception effect on FAR without touching
honest answering, inversion, no-pressure answering or an unrelated task (N1), an honest-only class that deception
bypasses (N2), and a stable partition (N3)?

## Verdict

Partly yes on FAR, and the positive part is reviewed. The all-position attribution ranking gives a deception-only
class of a few hundred neurons, dense in layers 0 to 9, whose twin interchange removes about 0.8 of the deception
margin while honest and no-pressure accuracy do not move, inversion loses 0.01 to 0.22 and the IOI task loses 1 to
3 points. Under the frozen bars of the original ladder that class failed (R13), on the IOI bar alone and on 100
rows. A pre-registered confirmation on fresh ids and 1,000 fresh IOI rows then passed every bar (R14), and a
pre-registered finer ladder passed at sizes 250 to 750 (R19), so the pass is not a tuned point and the class size
is not bounded above by what was tested. N2 is not a bypass: the honest-only class reads "suppression or shared" on
fresh data (R18), because ablating it costs honest and no-pressure accuracy and raises the deception margin. N3
holds at every size (F-np-001). On SER the deception-only class removes the deception effect but costs honest
accuracy, almost entirely on identity rows, so N1 fails there on collateral (R20). The attribution ranking is
faithful to single-neuron interchange in sign and, for mid layers, in size (R21). The readout-position and
activation-contrast rankings fail widely. Nothing here is a deception-specific mechanism in the strong sense: the
class removes the deception effect, but its members are small early-layer contributions and the honest-only class
is shared machinery.

## What was found

- **F-np-001 (N3).** Every class is split-half stable at every size; the deception-only class is the least stable.
- **F-np-002.** The activation-contrast ranking removes almost nothing and costs 23 IOI points.
- **F-np-003 (R13).** On the original ladder N1 fails at every size; the size-500 all-position class misses only
  IOI on 100 rows. Reviewed (review 03).
- **F-np-004.** N2 undetermined on the original ladder; ablating the honest-only class raises deception.
- **F-np-005.** The 100-row IOI fail was a noisy over-estimate of a real cost of about 4 points (exploratory).
- **F-np-006 (R14).** The fixed size-500 class passes every N1 bar on fresh data. Reviewed (review 04).
- **F-np-007 (R18).** N2 on fresh data is suppression or shared; the rate clause is inside the null band.
  Reviewed (review 05).
- **F-np-008 (R19).** The finer ladder passes at 250, 375, 625 and 750. Reviewed (review 06).
- **F-np-009 (R20).** SER: deception effect removed, honest accuracy lost on identity rows, N1 fails on
  collateral; N2 suppression or shared. Reviewed (review 07).
- **F-np-010 (R21).** Single-neuron interchange follows the attribution score in sign; early layers are
  under-predicted. Reviewed (review 08).

## What the controls say

- The user-turn inversion control I is the specificity control; the deception-only class removes at most 0.22 of
  the inversion margin on FAR while removing 0.8 of the deception margin.
- Twenty size-matched random null sets per class bound every effect; the class exceeds the null 95th percentile by
  about 35 times on the confirmation sample.
- Collateral is read under the mean reference (R7); the twin interchange is the primary effect measure (R2).
- The Codex A3 cell (layers 5 to 8 and 11, readout position) is not re-judged here; 210 of the 386 SER class
  neurons lie in A3's SER layers, so the SER reading is a descriptive lead outside that cell (R17).

## Pointers

- Rankings: `outputs/_analyses/neuron-partition/attribution/`; sets and stability:
  `outputs/_analyses/neuron-partition/sets/`; ablation cells: `outputs/_analyses/neuron-partition/ablation/`;
  verdicts: `outputs/_analyses/neuron-partition/verdict/`; Bridges-2 job logs:
  `outputs/_analyses/neuron-partition/bridges2_logs/`. These live in the primary checkout on Delta.
- Reviews 01 to 08 in `reviews/`; worker hand-backs in `reports/`.
- Scripts: `scripts/neuron_attribution.py`, `scripts/neuron_partition_sets.py`, `scripts/neuron_set_ablation.py`,
  `scripts/neuron_partition_verdict.py`, `scripts/neuron_partition_data.py`; jobs in `jobs/`.
- Budget: 21.58 of 30 reserved GPU-hours, 38,632 GPU-seconds used, on Delta interactive partitions and Bridges-2
  GPU-shared H100s.

## Options left to the user

A SER ladder at smaller sizes, or a test of whether the SER collateral stays confined to identity rows; an
all-forms SER run; a FAR ladder above 750; or no further work. Each needs a new pre-registered ruling.
