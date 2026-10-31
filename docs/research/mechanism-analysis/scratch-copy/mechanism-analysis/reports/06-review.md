# Ticket 06 review: numbers, spec rules and the figure builder

Two independent read-only reviews of `docs/research/mechanism-analysis/synthesis.md`, spawned by impl-06 on 2026-10-26
(model opus, run in parallel). Each was given file paths and the spec sections, not impl-06's verdicts. The first report
of each was lost on delivery and re-requested from the same agent; both then arrived in full. The builder
(`figures/figures.py`) was reviewed by impl-06 on both axes by hand, to keep usage down.

## Numbers review

About 313 numbers checked against their cited files, with the right task, condition, sample and rounding. One
mismatch; the rest were citation or wording fixes. All are fixed in synthesis.md.

| # | finding | disposition |
|---|---|---|
| 1 | Jobs total "19 jobs"; the ledger has 18 | **Fixed** (18) |
| 2 | C6 narrative "at most 0.26 logits" read as the flipped write; flipped writes are at most 0.18 (sdr L30H12) | **Fixed**: "honest writes of at most 0.26 logits, flipped writes of at most 0.18" (narrative and L23) |
| 3 | H5/H6 "(derived 0.738 / 0.835)": the values are printed in `figures/fig4_a_prime.csv` | **Fixed**: shares derived from `phase3/a_prime.csv`, printed in fig4's CSV |
| 4 | P1 "v1 1.89" is printed in `reports/03-1b-results.md`, not the cited JSON | **Fixed**: citation added |
| 5 | H4 "0.554" is in `reports/03-1c-results.md`, not `rab_curves.csv` | **Fixed**: citation moved |
| 6 | E1 counts: `rab_curves.csv` lists members but not circuits | **Fixed**: cites the reading (far, ser) and the 03-1c member tables (sdr); see also spec finding 5 |
| 7 | L8 "0.676 / 0.746" uncited | **Fixed**: `phase1/rab_curves.csv` |
| 8 | Lens follow-up "the 1B lens line took about 6 min" not in any record | **Fixed**: now cites spec section 4's estimate (L about 6 min) plus model load |
| 9 | "about a quarter of far's" vs the reading's 0.28 | **Fixed**: "about 0.28 of far's" |
| 10 | E9 "mostly keep the B2 signature on both" is true only among heads with the signature on D | **Fixed**: "of the heads with the B2 signature on D, almost all keep it on I (15/16, 8/9, 6/6)" |
| 11 | E7 "L9-11 heads": far's clause-position heads include L7H12 and L8H15 | **Fixed**: "L7-11 heads" |
| 12 | Four commit hashes not in any report (no git allowed to the reviewer) | **Verified** by impl-06 against `git log --oneline -40`: a4dd35f, 57a43aa, a13c6bd and c8021ea are all on the branch |

## Spec review

The lead relayed both reports on 2026-10-26 with ruling R30; every row below was re-checked against the synthesis
after R30 was applied, and the figures were rebuilt.

Verdict before fixes: rules applied correctly (headline rule, R-AB order and deciding sets, the A′ > 50 % call and
routing gate, R-inv's paired-CI rule, the B-selector conjunction, B-reader, C-own, C-v1, C-MLP, B-lens) and the three R29
wordings followed; not ready as written: 1 blocker, 10 should-fix, 4 nits.

| # | sev. | finding | disposition |
|---|---|---|---|
| 1 | blocker | The far / ser R-inv label rests on I pools of 210 and 249 ids; R22 says a task below 300 "has no I contrast"; R23 used the pools without amending R22 | **Resolved by R30** (orchestrator, spec section 9): R23 and the phase-1 instruction supersede R22's last sentence. The headline, the one-sentence summary, H8, H10, the narrative, L6 and Figure 2's caption and title now carry "below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees"; the reconciliation row is gone from section 6; the I-rebuild follow-up stays as the substantive fix |
| 2 | should-fix | sdr's R-inv shown as a verdict, though sdr has no deciding set | **Fixed**: H9 reads "no R-inv verdict" (R30) with the option-B and R19(3) CIs as description; the headline says "both deciding sets (far, ser)"; Figure 2 labels sdr's rows "descriptive" |
| 3 | should-fix | C-MLP's refutation was listed as a failed difference test; it is the one pre-registered sign of a difference (mlp.11/13/16 on ser alone); B-selector predicts a shared route | **Fixed**: H11 and the narrative rewritten; H11's verdict changed from "not supported" to **inconclusive** |
| 4 | should-fix | "The same heads concentrate the B2 signature" is wrong for ser (6 of 19 deciding-set heads carry it) | **Fixed**: B2 concentration stated across U' heads; deciding sets 16/18 (far) and 6/19 (ser) given |
| 5 | should-fix | "The circuits describe answer selection, not pressure" is unsupported; core L13H20/21 and L17H24-27 read or route the pressure; E1 counted MLPs as outside; sdr's S_20 is mostly inside | **Fixed**: narrative names those core heads; E1 now counts heads only too (far 13/18, ser 11/19, sdr 3/14 outside); the conclusion is limited to far and ser and marked descriptive |
| 6 | should-fix | "same work", "comparable", "does not own" go beyond R-inv's threshold; (ii) and R-inv apply to whole sets, MLPs included; the selection-sample scope of clause-reader was missing from the headline | **Fixed**: narrative and headline reworded to R-inv's label and spec 2.4's consequence; "the set" where (ii) / R-inv are meant; "on the selection sample" added; "lie signal" became "pressure signal" |
| 7 | should-fix | "almost every top-20 mediator acts the same way on I" states a descriptive S7-vs-S2p count as a finding | **Fixed**: "Descriptively, 20, 18 and 16 of the S2p top 20 are inversion-shared" |
| 8 | should-fix | Exclusives "neither deception-leaning nor owned, and they do not differ in what they read" overstates A5, C1 and C2 | **Fixed**: "mostly not deception-leaning, not significantly owned; the read test is uninformative" |
| 9 | should-fix | Per-instance f ratios required by spec 2.3 / R11(i) are reported nowhere | **Fixed**: the builder writes median and quartiles of the 100 per-instance f for every R-AB row (`figures/fig1_mediation.csv`, columns `f_pi_*`; tested); H2-H4 and L25 quote the deciding sets' values (far median 0.902, ser 0.907, sdr 0.494) |
| 10 | should-fix | C5 cited interchange columns, not R-A1's, and omitted counter-evidence | **Fixed**: R-A1's set-6 reading cited as deciding; supporting and counter-evidence listed; phase 1's verdict kept and marked fragile |
| 11 | should-fix | §7.11 missing; parts of §7.2, §7.6, §7.14, §7.19 missing | **Fixed**: L24 (redundancy and self-repair) added; L2, L7, L15, L18 completed; L25 (per-instance spread) added |
| 12 | nit | "re-adjudicates none" contradicted by A3 and A4 | **Fixed**: intro says two ungraded predictions are graded here; A4 is given per task |
| 13 | nit | C6 "confirmed on most heads" has no pre-registered aggregation | **Fixed**: per-head counts, 0 suppressed, 3 undefined, the spec gloss refuted; narrative says "most late H-D heads" |
| 14 | nit | L24 "fed by L17H24" true of the Q-category L24 heads only; B3 wording; E6 / E9 / E15 labels softer than the readings; "sdr is different, but only descriptively"; E17 has no null; R17 is two sentences | **Fixed** all: B1 and narrative name L24H26 / L24H27 (plus L24H17 sdr, L24H20 ser); B3 "holds on sdr; refuted on far and ser"; E6, E9, E15 carry the exploratory parts; heading "sdr reads B; its route contrast is descriptive"; E17 states the missing null; R17 is one sentence |
| 15 | nit | C-reads' exploratory sub-expectation absent; ticket asks for claims.md and clustered lens CIs | **Fixed** E19 (sink-free read: every set reads the frame most). claims.md: the lead's brief put the claims table in synthesis.md, so one copy is kept there (noted in the hand-back). Clustered lens CIs: not possible from the fetched cells (no per-instance trajectories); stated in L7, the figure caption and section 6 |

## Builder review (impl-06, both axes by hand)

Standards:
- `figures.py` reads `reports/03-1c-results.json` from the absolute `.scratch` path and the lens JSONs from the
  git-ignored cells, both outside the commit. **Accepted**: `--render` redraws every PNG from the committed CSVs alone
  (tested), and `figures_meta.json` names each source.
- Python 3.12's `sum()` is compensated, so float sums differed by one ulp from py3.9 and the committed CSVs did not
  match a py3.9 extraction. **Fixed**: `math.fsum`; a test compares the committed CSVs with a fresh extraction and passes
  in both envs.
- Figure 4's sub-reading label maps the call to a sub-reading without the routing gate. **Accepted**: the gate matters
  only for mover / unresolved calls, which no task has; noted here.

Spec:
- Every figure the lead named is built (held-out R-AB curves with nulls; R-inv paired contrast; B2 by layer; A′ shares;
  phase-3 entry paths), plus the ticket's cross-task matrix, exclusives and lens. Task names far / sdr / ser and
  condition names D / H / F / I are used throughout; the palette passed the dataviz validator's colour-blind checks.

## Tests

| run | result |
|---|---|
| `tests/test_mechanism_analysis_figures.py`, mgnp | 14 passed |
| same, base (thread pins) | 14 passed |
| full suite, base | 8 failed = the 8 names of `00-baseline-failures.md`; 2203 passed, 66 skipped (1871 s); run before the per-instance columns, after which the figure tests were rerun green in both envs |
| full suite, mgnp | 8 failed = the 8 names of `00-baseline-failures.md`; 2400 passed, 19 skipped (1647 s). The run started before the R30 caption edits to figures.py; the figure tests were rerun after the last figures.py write, 14 passed in both envs |
