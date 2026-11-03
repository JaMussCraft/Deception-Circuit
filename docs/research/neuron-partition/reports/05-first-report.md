# Report 05: First report on neuron-partition, for the advisor meeting of Wed 4 Nov 2026

Agent: report writer (Claude, Opus), read-only on code. Ticket: the lead's first-report brief of Tue 3 Nov 2026 (item
8 of `../START.md`). Status: draft; the ablation results are marked "RESULT PENDING" for the orchestrator. Bare file
names are in `docs/research/neuron-partition/reports/`, and `../` is `docs/research/neuron-partition/`.

**Summary.**

1. **Question.** Do any MLP neurons of Llama-3.1-8B-Instruct matter only for instructed deception (FAR task), and not
   for a transparent inversion control or for the honest answer?
2. **Method.** Rank all 458,752 down-projection-input neurons by attribution patching, cut four classes by rule R6,
   and ablate each against 20 matched random sets under three references (`01-w1-scorer-handback.md`).
3. **Established.** The ranking reproduces the dataset margins, the scores sit mostly in layers 11 to 16, and most
   strong deception neurons are also strong inversion neurons, map correlation 0.775 (`01-w1-scorer-handback.md`).
4. **Established, descriptive.** On the readout-position ranking every class is split-half stable (finding F1).
5. **Pending.** The all-position ranking that ruling R11 made primary, and every ablation result for N1 and N2.
6. **Headline.** RESULT PENDING: one sentence on whether a D-only set passes the N1 bar at any k, and the N2 verdict.

## What changed

### (a) The question and the three directions

The direction asks which MLP neurons matter only for deception, which only for the honest answer, and which for both,
when deception (D) is contrasted with its neutral twin (H) and with a user-turn transparent inversion (I) against its
user-neutral twin (N) (`../START.md`, items 1 and 2).

- **N1, the causal neuron map and partition.** Score every neuron, partition into D-only, D-and-I shared, H-only and
  all-shared, and validate each class by set ablation against matched random sets.
- **N2, honest bypass or suppression.** Ablate the H-only set under H, D and F. If honest accuracy falls while the
  deceptive rate stays, deception bypasses the honest neurons.
- **N3, stability.** Split-half Jaccard of every class against a ceiling and a floor; the rotation test is optional.

**Where this sits.** At head level this project's deception-leaning sets turned out to be cue-routing machinery. The
43-head SDR core splits into 22 shared, 15 deception-leaning and 3 honest-leaning heads (F-comp-001), no exclusive or
difference head set is deception-specific (F-mech-005), and the sycophancy transfer of 0.724 is shared and
non-specific, resting on mlp.5 to mlp.7 (F-rte-008), all in `../../FINDINGS.md`. The Codex ladder's FAR deciding set
removes 23.9% of the D effect but 31.6% of the I effect and fails its specificity rule (`00-reader-brief.md`, section
1). No row has intervened below the head or block, so a passing neuron set would be the project's first
deception-specific unit. A null closes the "maybe it is below the head" reading outside the Codex A3 cell, which this
session leaves alone.

### (b) The method

**Unit and conditions.** The unit is one input of the MLP down-projection after the SwiGLU gate, 32 layers by 14,336
(`../spec.md`, operational definitions). The conditions and their sizes follow (`03-w3-data-handback.md`).

| Condition | Source | Ranking rows, train and validation | Test sample, seed 2 |
|---|---|---|---|
| D, pressured | `far_v2` | 200 and 200 | 300 |
| H, neutral twin of D | `far_v2_honest` | 200 and 200 | 300 |
| F, no pressure | `far_v2_nopressure` | not ranked | 300 |
| I, user-turn inversion | ladder A1 control cell, copied with sha256 | 177 and 177 | 300 |
| N, user-neutral twin of I | same | 177 and 177 | 300 |

The test sample excludes 356 ids: the ladder's 100 assessment and 100 selection ids and two mechanism-analysis held-out
samples. That leaves 644 eligible D ids and 566 eligible I ids; I was drawn independently, and 164 ids are in both.
IOI collateral uses 100 rows rebuilt from the ladder's recipe under ruling R4 (`03-w3-data-handback.md`).

**The score.** Per row, m is logit(opposite) minus logit(honest) at the readout token, in D's orientation, through an
fp32 recomputation of the final norm (ruling R2). The attribution of a neuron is (a_clean minus a_twin) times dm/da.
A positive score means patching the neuron to its twin value lowers m, so the neuron supports the clean condition's
answer (`01-w1-scorer-handback.md`). The scorer stores this at the readout and summed over the pressure or request
clause. Review 01 found that neither covers the 43 positions between the clause end and the readout on FAR, while the
twin interchange writes every position. Ruling R11 therefore made the attribution summed over every position the
primary ranking, with the readout score and the activation contrast as comparisons (`../reviews/01-scorer-review.md`).

**The partition (R6).** Three signed scores per neuron: s_D from D against H, s_I from I against N, and s_H from the
reverse run with H clean, sign flipped so that positive supports the honest answer. For each k on the ladder 500,
1,000 and 2,000, T_D, T_I and T_H are the top k positive neurons of each score. The classes are D-only = T_D minus
(T_I union T_H); D-and-I shared = (T_D and T_I) minus T_H; H-only = T_H minus (T_D union T_I); all-shared = all three.
Every class is ablated at every k, and k is never chosen on the test sample (`../spec.md`).

**Ablation references and effect measures.** The rulings cited here are in `../spec.md`.

- **Twin interchange, primary.** In each D row the set's activations are replaced at every position by the same
  instance's H values; in each I row by N's values.
- **Mean and zero ablation.** The mean is per neuron over F's train and validation splits, never the test split (R3).
- **Effect (R2).** The fraction removed is mean(m_intact minus m_ablated) divided by the intact gap G, the mean of
  m_D minus m_H with the two prompt streams averaged within an id. The rate at margin 0.7 is stored beside it from
  the same logits (`../spec.md`). Under mean and zero, the rate compares ablated D with ablated H (R8).
- **Collateral (R7).** H, F and IOI accuracy shifts are read under the mean reference for every set, because F and
  IOI have no twin. Under the twin reference the H shift is the reverse patch and is descriptive.
- **Halves (R10).** "Both split halves" means two halves of the seed-2 test sample, by pressure cluster (`../spec.md`).
- **Nulls.** 20 random sets per class and k with the same size and per-layer counts, drawn without the tested
  neurons, seed 2, scored on every metric (`04-w4-partition-handback.md`).

**Where the work departs from the frozen item 10.** The pass bars are read on the margin effect, not on the rate
paraphrase in START, because the rate's intact effect is 1.0 by construction (R2). The collateral bars read the mean
reference (R7). Both are dated rulings in `../spec.md`. N3's "IOI floor" is replaced by a uniform random-set floor, as
the lead's brief to W4 said; that change is recorded only in `04-w4-partition-handback.md`.

### (c) What is established

**The ranking baseline reproduces the dataset margins.** On the 400 D/H and 354 I/N ranking rows, every scored margin
correlates with the stored margin at 0.9985 or more, with sign agreement 1.000. The clean-stream gaps are 9.61 for D
against H and 14.61 for I against N, against the Codex audit's 9.915 and 14.979 (`01-w1-scorer-handback.md`).

| Stream | Mean m | Rows with m above 0.7 |
|---|---|---|
| D | 2.412 | 390 of 400 |
| H | −7.198 | 0 of 400 |
| I | 5.763 | 354 of 354 |
| N | −8.844 | 0 of 354 |

**The scores are concentrated, and deception overlaps inversion.** By the readout score, 1,477 of 458,752 neurons pass
0.01 and 46 pass 0.1 for D/H; for I/N the counts are 6,338 and 114. The two maps correlate at 0.775, and 40 of the 46
strongest D/H neurons are also above 0.1 for I/N. D/H mass sits in layers 11 to 16, with 340 neurons in layer 13, and
in layers 29 to 31, with 97 in layer 31 (`01-w1-scorer-handback.md`).

**Class sizes and overlaps, readout-position ranking.** These are the comparison ranking under R11, not the primary
cut. The D and honest top sets overlap little, so the H-only class is not a mirror of T_D
(`04-w4-partition-handback.md`, addendum "real partition").

| k | D-only | D-and-I shared | H-only | all-shared | Jaccard T_D, T_I | Jaccard T_D, T_H |
|---|---|---|---|---|---|---|
| 500 | 174 | 172 | 331 | 111 | 0.395 | 0.182 |
| 1,000 | 409 | 314 | 702 | 209 | 0.354 | 0.161 |
| 2,000 | 895 | 629 | 1,474 | 325 | 0.313 | 0.135 |

**Layer concentration, readout-position ranking.** D-only, D-and-I shared and H-only put 0.77 to 0.92 of their
neurons in layers 10 to 16, densest at layer 13. All-shared is the only class spread across depth, with 0.20 to 0.25 of
its neurons in layers 30 and 31 (`04-w4-partition-handback.md`). The activation-contrast comparison puts its classes
mostly in layers 30 and 31 instead, so the two rankings pick largely different neurons. Review 01 also found that s_D
and s_H correlate at only 0.013 over all neurons and agree in sign on 0.63 of the top 100, although both use the same
activation difference (`../reviews/01-scorer-review.md`, finding 2). R11 records this as a known property.

**N3 stability, readout-position ranking (preliminary finding F1).** Jaccard between the rank halves; the ceiling is
T_D's own Jaccard (`outputs/_analyses/neuron-partition/sets/far_atp_66741d7/stability_summary.md`).

| k | Ceiling | D-only | D-and-I shared | H-only | all-shared |
|---|---|---|---|---|---|
| 500 | 0.8182 | 0.6602 | 0.7789 | 0.7493 | 0.7500 |
| 1000 | 0.8018 | 0.6480 | 0.7514 | 0.7873 | 0.7817 |
| 2000 | 0.7889 | 0.6608 | 0.7690 | 0.7743 | 0.7989 |

Every class clears the bar of half the ceiling at every k, and the random-set floors are 0.0001 to 0.0022. D-only is
the least stable class. The bar is lenient, so "stable" means "not noise", not that membership is pinned down
(`04-w4-partition-handback.md`, addendum "stability").

**RESULT PENDING: all-position partition (R11 primary).** Class sizes at each k of R6 (`../spec.md`), the Jaccards of
T_D with T_I and with T_H, layer bands, and the N3 stability table on the all-position keys. Say how far the
all-position classes overlap the readout-position classes above.

### (d) The pre-registered pass bars, plainly

These restate item 10 of `../spec.md`. N1 passes if a D-only set of at most 2,000 neurons removes at least half of the
D effect, removes under a quarter of the I effect, moves H, F and IOI accuracy by under 5 points each, and removes
more of the D effect than the 95th percentile of its matched null. All of this must hold under twin interchange and
under mean ablation, on the whole test sample and on each half. Meeting it in one reference or one half is a lead,
not a pass. If no set meets every bar, the reviewed null reads "no deception-specific MLP neuron set at this
granularity under the ladder rule, outside the A3 cell".

N2 calls ablating the H-only set "bypass" if H accuracy drops by at least 20 points while D's deceptive rate moves
under 5 points and the null moves H under 5 points. It is "suppression or shared" if D's deceptive rate also falls by
at least 10 points. Anything else is "undetermined at this size". N3 calls a class stable if its split-half Jaccard is
at least half the ceiling (`../spec.md`).

### (e) Ablation results

**RESULT PENDING: N1.** One table per reference (twin, mean, zero), pasted from the Markdown output of
`scripts/neuron_partition_verdict.py`, with all four classes at every k of R6 (`../spec.md`). Skeleton for D-only:

| class | k | size | D removed (margin) | D removed (rate) | I removed (margin) | I removed (rate) | null p95 of D removed | H shift | F shift | IOI shift | bars (whole) | half 1 | half 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D_only | 500 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| D_only | 1,000 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| D_only | 2,000 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |

**RESULT PENDING: N1 verdict.** Pass, lead or fail at each k, with the bootstrap intervals for D and I removed, and
where the three references disagree.

**RESULT PENDING: N2.** The H-only table from the same output, one row per reference, k and subset, and the verdict:
bypass, suppression or shared, or undetermined.

## How verified

Each worker ran its tests on both interpreters, mgnp and the base Python 3.9, with no failures to compare against the
known baseline (`01-w1-scorer-handback.md`, `02-w2-ablation-handback.md`, `03-w3-data-handback.md`,
`04-w4-partition-handback.md`, `05-w1-verdict-handback.md`).

| Worker and file | mgnp | base Python 3.9 |
|---|---|---|
| W1 scorer, `tests/test_neuron_attribution.py` | 28 passed | 28 passed |
| W2 ablation, its new file plus 14 neighbouring files | 272 passed | 173 passed, 22 skipped |
| W3 data, `tests/test_neuron_partition_data.py` | 20 passed | 20 passed |
| W4 partition, `tests/test_neuron_partition_sets.py` | 18 passed | 18 passed |
| W1 verdict, `tests/test_neuron_partition_verdict.py` | 20 passed, 1 skipped | 20 passed, 1 skipped |

The base skips in W2's suite are 16 tests that need nnsight 0.7.0, plus 6 skipped before the change
(`02-w2-ablation-handback.md`). The verdict skip is the real-cell test, which waits for a finished ablation cell.

**Review 01, the scorer: PASS WITH FIXES.** Major 1, that the readout score targets a different counterfactual than
the every-position twin interchange, is resolved by ruling R11. Major 2, that s_D and s_H share the activation
difference and agree in sign on only 0.63 of the top 100, is recorded as a known property; the one-neuron check is
descriptive and has not run (`../reviews/01-scorer-review.md`).

**Review 02, the ablation machinery: PASS WITH FIXES.** Major 1 found that the IOI rows depend on the Python hash
seed, so they differ between jobs. Major 2 found that the ids loader rejected W3's test-sample file. Its independent
checks matched: zero ablation gave an MLP output of exactly 0.0, and the twin interchange reproduced the twin's
down-projection input exactly (`../reviews/02-ablation-review.md`). RESULT PENDING: confirm that both fixes landed
before the full ablation cell; at the time of writing neither was in the worktree.

## Execution evidence

The three completed GPU jobs ran on Delta interactive A40 nodes under account beto-delta-gpu. Totals so far are 2.25 of 20
GPU-hours reserved and 600 GPU-seconds used, with no OpenRouter spend (`01-w1-scorer-handback.md`; the ledger is
`/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/ledger.json`).

| Job | Slurm id | Reserved | Actual | State | Output and manifest commit |
|---|---|---|---|---|---|
| Ranking pilot, 64 validation rows | 23475874 | 45 min | 89 s | COMPLETED | `attribution/far_v2_{dh,in}_validation_f4ce555_limit64`, commit f4ce555, dirty |
| Full FAR ranking, forward and reverse | 23476096 | 30 min | 252 s | COMPLETED | `attribution/far_v2_{dh,in}_train+validation_7386fd3{,_rev}`, manifest commit 6c6d5be, dirty |
| Split-half ranking for N3 | 23476621 | 30 min | 259 s | COMPLETED | `attribution/far_v2_*_half{1,2}_66741d7*`, commits e5962fe, 5e4fd2c, 767d4be, clean |
| Ablation pilot, `--limit 16`, smallest k | 23477197 | 30 min | PENDING | PENDING | `ablation/pilot-e5962fe` |
| All-position ranking rerun (R11) | PENDING | PENDING | PENDING | PENDING | PENDING |
| Full ablation cells | PENDING | PENDING | PENDING | PENDING | PENDING |

The full-ranking directories are named for a commit the code was not at; their scorer is pinned by its code sha256 in
the manifests (`../reviews/01-scorer-review.md`, finding 7). The ablation pilot started before either review 02 fix,
so its IOI rows carry the hash-seed caveat. RESULT PENDING: the pilot's intact IOI accuracy against the ladder's 0.51
(`00-reader-brief.md`, section 2; ruling R4).

## What is NOT done

- **Ablation results.** No N1 or N2 number exists yet; both wait for the ablation cells tonight.
- **The all-position ranking.** R11 made it primary, but the scorer key it needs was not in the worktree at the time
  of writing, so the class sizes and stability above are the readout-position comparison.
- **SER.** No SER ranking or ablation has run. START makes SER a bonus.
- **The one-neuron interchange check** of the scorer review's second major is descriptive and has not run.
- **Dropped or unused.** The N3 rotation test is dropped, as START's fallback allows. The clause-position ranking is
  computed but not used for any partition.
- **The A3 cell.** No verdict is recorded in the Codex A3 neuron cell, as `../START.md` requires.

## Open questions

- **Rate or margin (R2).** The pass bars read on the margin effect, and the rate at margin 0.7 is reported beside it
  (`../spec.md`). The user may prefer START's rate paraphrase. Default: margin, as ruled.
- **The bars themselves.** Are the cap of 2,000 neurons and the 50 percent removal bar the right test for a
  distributed neuron code (`../START.md`)? Default: keep the frozen bars and report every k.
- **SER.** Should the remaining GPU budget go to SER, whose act-naming test rows number only 72
  (`00-reader-brief.md`)? Default: only after the FAR verdict, and only with the user's go.
- **The all-position rerun.** The full ablation should use the R11 classes, so it cannot start before the rerun
  lands. Default: run the readout-position cells as the comparison if the rerun is late, and say so.
- **The pilot's IOI rows.** Does the hash-seed caveat spoil the pilot's check against 0.51 (`00-reader-brief.md`)?
  Default: repeat the check in the first job after the fix.
- **The I sample.** It overlaps the D sample on 164 of 300 ids (`03-w3-data-handback.md`), so D and I effects come
  from partly different instances. Default: report it as a caveat.
