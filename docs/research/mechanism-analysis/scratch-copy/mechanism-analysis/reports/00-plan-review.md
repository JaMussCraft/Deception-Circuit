# 00 plan review (review-00, 2026-10-25)

Reviewer: review-00, builder check per
`superpowers/7.0.0/skills/brainstorming/builder-check-prompt.md`. Read-only everywhere except this file. No git,
no Slurm, no analysis run. CPU reads of the v2 test sets ran with `/sw/external/python/anaconda3/bin/python -I`
from `/u/swong2/.claude/jobs/1c836bb8/tmp/review00/`.

Read: `spec.md` (the 10:20 version with rulings R0-R8), `issues/01..07`, `agent-brief.md`, `reports/00-plan-draft.md`,
`reports/00-plan-handback.md`, mechanism-datasets `reports/06-evaluation-reading.md` and `06-stage2-results.md`,
repo `CONTEXT.md`, `docs/component-roles.md`, ADR-0002, and the code named below.

## 0. Spot-checks of the planner's file:line claims

Every claim I checked holds. Paths are relative to `/projects/beto/swong2/Alignment/Deception-Circuit` (main, c24b5d9).

| claim | verified |
| --- | --- |
| knockout is interchange-only: `component_analysis/knockout.py:70-71`, `:95-107`, `:988` | yes |
| single, family and sweep share one loop: `knock_out_groups` `:328`, `family_effects` `:459`, `sweep_effects` `:608` | yes; replacement is at every position, from an unmodified corrupt-stream forward |
| `component_analysis/dataloaders.py:72` `MECHANISM_TASKS` v1-only | yes |
| `segmentation.py:338` reads `dc.SPECS`; `:534-541` registries | yes |
| `analyze_components.py:345` silently skips non-segmentable tasks | yes |
| `evaluation/ablation.py` mean semantics | yes, and more: the mean is **position-pooled and broadcast to every position** (`MeanHook`), collected over the bound task's test loader (`evaluation/context.py:351-372`) |
| `scripts/remote/b2.sh:25` branch, `:35` fetch roots; `.gitignore:8`; `scripts/cluster/delta.env:25` | yes |
| `scripts/analyze_components.sbatch:62` bare `source ~/.bashrc`; profile block in `scripts/evaluate_circuit.sbatch:48-61` | yes |
| path patching K/V receivers per KV group (`component_analysis/path_patching.py:41`) | yes |

Two facts the documents do not state, both used below:

- **Path patching freezes every Component of the model, not only the grid** (`path_patching.py:463`, `:593`). A
  route from a sender through any Component outside `C_t` is cut, including the ~22 MLP blocks phase 3 leaves out.
- **The Pressure Clause is the last sentence of the system turn.** Intro, Designating Sentence and Designation
  Suffix precede it (checked on row 0 of all three D test sets and their `_honest` twins). Under causal attention
  every position before the clause has bit-identical activations in D and in its Neutral-Clause Twin.

## 1. Blocking issues (fix before the user sees the plan)

**B1. R-AB (i) has no null and double-dips.** `S_k` is ranked by the S2 sweep on the 100-instance causal sample and
then knocked out on the same 100 instances. Top-k selection on noisy single effects inflates the joint effect, so
the 0.75 fraction is biased towards "met". Nothing says what a random k-set would do. Fix, in spec §2 and ticket 03:
rank on the seed-0 sample, test on a disjoint sample (another 100 instances, a different `--seed`, ids excluded),
add a 20-draw random-k null (layer-matched if cheap), and report per-instance bootstrap CIs on both (i) numbers.
Cost is minutes of H100 per task.

**B2. The R-AB ranking cannot produce outcome A as defined.** Three mechanical reasons:

1. *Late answer writers win the ranking.* At all positions, a neutral-twin replacement of a late head or MLP writes
   the honest answer at the Readout, so L24 and L30-31 Components will fill the top 5-20. They meet (i) and fail
   (ii) by construction. The spec already says so for A′, but then A is unreachable whenever a single mover ranks
   high, even if a separable upstream set exists further down.
2. *The positive control is in the ranking.* The layer-0 MLP acts as a second embedding (`CONTEXT.md`, Positive
   Control). Its neutral-twin value at the clause positions replaces much of the clause's token identity, so it will
   rank near the top of S2 and decide (ii) on its own. The sweep code already excludes it from `flagged`; R-AB does
   not.
3. *Local clause encoding is not reading.* At the clause span itself, early heads only re-encode the clause tokens.
   A set of such heads can meet (i) and pass (ii) and be called "separable pressure readers" when it is the
   clause's input encoding.

Fix: rank for R-AB on a neutral-twin sweep restricted to **post-clause positions excluding the Readout** (or S2
minus S3), with the layer-0 MLP excluded, and keep the all-positions S2 as descriptive. That needs one more sweep
per task (about 13 H100-min each) or replacing S2's use. Ticket 02's `--knockout-positions {all, readout,
<Segment>}` cannot express "every position after a Segment, minus the Readout". The flag needs a range form, for
example `after=pressure_clause` with an `exclude=readout` modifier, so the implementer does not discover this
mid-ticket. Also state that ranking by single-Component effect cannot
find redundant sets: either add a greedy joint selection over the top 50 (about one sweep's cost per task), or
reword B as "no set of 20 or fewer, chosen by single-Component neutral-twin effect, mediates the pressure". B's
current text, "distributed through the answer machinery", is not measured by R-AB at all; tie it to a stated
measurement (for example the share of the neutral-twin effect held by Components that R-cls calls shared) or drop
the clause.

**B3. The A′ adjudication and B-selector are not decidable as written.**

- "The pressure arrives at the queries of `S_k`'s members" has no quantifier (all members, a majority, the
  strongest?), no threshold beyond the path floor, and no rule for MLP members, which have no query.
- B-selector's falsifier, "strongest neutral-twin path arrives at K or V from designation or item positions", can
  never fire for designation positions: they precede the clause, so no neutral-twin difference originates there.
- The textbook pressure-reader outcome, strongest path at K or V **from the clause span**, is neither confirmation
  nor falsification. The outcomes must be exhaustive: Q (selector), K/V from the clause span (reads the clause
  directly), K/V from post-clause item or question positions (reads pressure-modulated items), nothing above the
  floor.
- "A′-mover: a distributed upstream route" is inferred from the absence of grid paths. Because path patching freezes
  every non-grid Component, a route through one of the ~22 MLPs outside `C_t` is invisible, and A′-mover would be an
  artifact of the grid. Either put all 32 MLP blocks in `C_t` (get the cost from `--dry-run`; my rough count says
  about 2x phase 3) or add a cheap check: jointly neutral-twin-knock out all MLPs at post-clause positions, then all
  non-`C_t` heads, and report each share of the gap. A′-mover is then claimed only if the share outside `C_t` heads
  and MLPs is large.

**B4. R-A1's no-pressure column under mean ablation injects the pressure.** The variant rows use the task bank
(`evaluation/knockout.py:325`, `ctx.hook_for("task")`), and the task bank is collected on D's test split, which is
all pressure prompts (`evaluation/context.py:359-372`). Mean-ablating a pressure-reading head on a no-pressure prompt
writes in its average under-pressure output and can **create** deception there. So the "deception-specific" row
(no-pressure deceptive rate <= 0.10), and the prediction that the exclusives read <= 0.10 under mean, can fail for
exactly the Components the study is looking for. The mean is also position-pooled and broadcast to every position,
BOS included, which is harsher than position-wise mean ablation. Options:

- a variant-matched bank, collected on `<t>_v2_nopressure` for the no-pressure rows (a change to `evaluation/`,
  shared code, tested);
- or declare the no-pressure column exploratory under mean and decide R-A1 on zero ablation for that column.

Either way, spec §7 needs the position-broadcast caveat.

**B5. R-lens cannot separate mechanism from wording with the planned split.** From the test sets:

- FAR's 12 test clauses are all act-naming, so FAR has no Predicate-naming subset.
- "Split SDR/SER by clause form" has no label to split on. The pool's slot provenance (00-09 strong, 10-19
  relational) does not match act-naming vs Predicate-naming. SDR slot 00 (70 rows) is "show the harmless result in
  place of the critical one", and SER slot 00 (150 rows) is "steer the buyer to the favorable result instead".
- SER's literally act-naming ("wrong result") clauses are 72 of 1,000 rows. SDR's are about 216.
- Clause sizes are lopsided: FAR has two clauses at 150 rows each, and SER has clauses with 1 and 2 rows. Instances
  sharing a clause are not independent.

Fix: pre-register a text rule ("Predicate-naming iff the clause contains a Predicate word; act-naming iff it says
wrong, incorrect, false or not true; otherwise other"), hand-label the 49 test clauses into a committed table before
any lens runs, and make the deciding comparison FAR vs the act-naming subsets of SDR and SER. Use a bootstrap
clustered by `pressure_id` for every between-task CI, R-lens included. If the act-naming subsets are too small,
R-lens is exploratory, and the plan draft must say so. Two more confounds belong in §7: FAR's question and stem name
the Predicate ("The result that is failing is"), which primes the factual answer; and a raw logit lens on Llama
mid-layers is uncalibrated, so the -0.5 cut means different things at layer 8 and layer 28.

**B6. The documents disagree on the rules the user cares about.**

- R4 says phases run back to back and the orchestrator stops only if a reading changes the plan. That contradicts:
  - spec §5.2-4 ("Nothing in phase 2 starts before ... the user says go");
  - the HARD STOP hand-backs in tickets 02-05 and in `agent-brief.md`;
  - the plan draft ("I stop after phases 1, 2 and 3. You see each reading before the next phase starts").

  A builder will follow whichever document they read last.
- R1 (un-reserve "pressure reader") and R7 (amend `docs/component-roles.md`) are orchestrator rulings. Spec §5.5
  says no criteria change "without the user's ruling". Every amendment in the doc's change log so far is "the
  researcher's decision". The standing go ("start making progress once the plan is agent-reviewed") does not
  obviously cover rewriting role criteria.
- The plan draft still asks Q1-Q7, which R1-R8 already answered. The tickets have not been synced to the rulings.
  Ticket 02 says the amendment is drafted only, while R7 applies it in ticket 02. Ticket 06 writes `reports/tables/`,
  while R6 says `docs/research/mechanism-analysis/`. Ticket 07 is now conditional (R5).

Fix: pick one hard-stop rule and write it identically in spec §5, the tickets, the brief and the plan draft. Mark
R1 and R7 as pending the researcher's confirmation, or record that confirmation. Then sync the tickets and the
draft to R0-R8.

## 2. Questions, sorted into three piles

### Pile 1: already answered by the documents

| question | where |
| --- | --- |
| Which honest counterfactual? | R1; HB (c) |
| Mean/zero mechanics; sanity cannot pass under mean/zero | HB (a), caveat 1 |
| How to bind composed sets in phase 2 | `--reference` binds atomic run dirs only; derive membership on CPU (HB revisions; spec §4 phase 2) |
| Does the v1 segmenter cover v2? | HB (b)5: 9,000 of 9,000 rows validate once dispatched |
| Caps and per-ticket allocations | R2; spec §6 |
| Push the branch? | R3 |
| What is of record? | R6 |
| Status of thresholds | R0: proposals, not calibrations; never decided at other values |
| Seeds | R5 |
| GQA in path patching | K and V receivers are per KV group (`path_patching.py:41`) |
| Causal-sample seed | spec §8: 0 |

### Pile 2: minor, with a proposed default

1. **Flip-audit tool path** (ticket 03 names it only by a cell label). Default: `evaluation/knockout.py`
   `_flip_audit`, plus `flip_audit_analysis.py` as listed in mechanism-datasets `06-recon-evals-and-bridges2.md:39`.
2. **`--knockout-groups` format.** Default: JSON `{name: [[kind, layer, index], ...]}` in `head_table.row_key`
   order, written by a script under `outputs/_launch_mechanism_analysis/` that reads `sweep.json`.
3. **(i)'s 0.75 fraction.** The spec does not say whether this is a ratio of means or a mean of per-instance ratios.
   Default: ratio of means decides, and per-instance is reported. The gap is at least 1.0 logit by construction,
   since D margin >= 0.7 and twin honest >= 0.3.
4. **R-cls signs.** The rule takes ratios of signed values and does not say so. Default:
   - classify on signed `d`;
   - add an "opposes" class for a significantly negative `d(D)`;
   - replace "or neither H nor F significant" with "d(D) >= 2 x the upper 95% bound of max(d(H), d(F))".

   At n = 100, "not significant" is weak evidence, and the current clause biases towards the predicted
   "deception-leaning".
5. **Column-name trap.** D rows carry `neutral_prompt` and `neutral_text`. `neutral_prompt` is the Prior-Balance
   prompt: the Designating Sentence is neutralized and the clause is kept. It is **not** the Neutral-Clause Twin.
   Default: ticket 02 says so, and a test asserts that the twin comes from `<t>_v2_honest`.
6. **Drift-control inputs.** Verify that the v1 coarse SDR H run is in the Bridges-2 manifest. Ticket 06's drift
   cells (D_hko, headsko) did not need it, but the D&H-core sweep does.
7. **Phase-2 knockouts duplicate phase 1.** The phase-1 sweeps already give every Component on all 9 test sets
   under item-swap, and on D under neutral twin and mean, on the same causal sample. Default: build the C1 matrix and
   read C-own from the phase-1 sweeps on CPU, and drop the single-knockout passes from the phase-2 cells. Bind U in
   the 1B sweeps (spec §8 allows it) so the in-circuit columns land in the same table.
8. **"Concentrate" in B-reader.** Default: the share of signature heads in L8-17 exceeds the base rate (10 of 32
   layers), by a one-sided binomial test.
9. **C-own definition.** Default: per head, own-task `d(D)` > max of the other two; sign test over heads. Note that
   far's 8 heads give a minimum p of 0.004, so the test has little power.
10. **Ledger race.** Tickets 02 and 03 (1A) run concurrently and both read-modify-write `compute-ledger.json`.
    Default: only the orchestrator writes reservations, or each agent takes a lock file first.
11. **Fetched cells can be lost.** R6 keeps canonical cells under the worktree's git-ignored `outputs/_analyses/`.
    Removing a worktree deletes ignored files without warning. Default: R6 adds "move to the main checkout's
    `outputs/_analyses/` before the worktree is removed", as format-control did.
12. **Delta fallback cap is card-dependent.** Phase 3's expected 5.3 H100 GPU-h is about 21 A40 GPU-h, which is
    above the 12 h fallback cap. Default: H200 only for phases 2-3 on Delta, or state the cap in H100-equivalent
    hours.
13. **Segment-resolved neutral-twin knockout (phase 2).** At Designation Positions, and at every Segment before
    the clause, the result is exactly zero by construction. Default: keep it as a sanity assertion and never report
    it as a finding. The informative Segments are the clause, the post-clause question, the item and response-line
    mentions, the stem and the Readout.

### Pile 3: only the researcher can answer, and the answer changes what gets built

1. **Hard stops (B6).** Does the standing go waive the per-phase user go (R4), or does spec §5 stand? With the
   Bridges-2 date around Nov 9 and three gated stops in about ten days, the answer sets the schedule.
2. **Criteria amendment and pressure reader (R1, R7).** Confirm as your decision, including the pressure-reader
   criteria text, before ticket 02 applies it.
3. **Amended R-AB (B1-B3).** Bless the held-out sample, the random-k null, the post-clause ranking without the
   positive control, the greedy joint selection (or B's rewording), and the exhaustive B-selector outcomes. Each one
   changes a pre-registered test, so it must be fixed before anything runs.
4. **R-lens status (B5).** Is it a gated prediction with the matched-form comparison, or exploratory?
5. **No-pressure column under mean (B4).** Use a variant-matched mean bank (a code change in `evaluation/`) or make
   the column exploratory?
6. **Path-patching grid (B3).** Put all 32 MLPs in `C_t` (about 2x phase-3 GPU, which may need the holdback or a
   cap raise), or keep at most 10 and accept that A′-mover cannot be told apart from an MLP-routed path?
7. **Deception vs rule-following.** The neutral-twin contrast removes an operator rule that says "name the other
   / wrong one". A set that mediates it may be generic instructed-inversion or negation machinery rather than
   deception. A non-deceptive inversion control would separate the two. For example: a transparent game clause,
   "the reviewer asked you to name the result that is NOT failing", with a behaviour filter. That is a dataset
   change, CPU plus under 1 GPU-h. Build it, or state the limitation?

## 3. Non-blocking improvements

- **Split ticket 02.** 02a holds what phase 1B needs: loaders, segmentation, neutral-twin pairing, the knockout
  scheme, position and group flags, the lens summary, the smoke test and drift. 02b holds neutral twin in attention
  and path patching, plus the amendment. As written, phase-2 and phase-3 prerequisites block 1B, which matters with
  the Nov 9 date.
- **Mediation curve.** Ticket 06 plans a "k vs deceptive rate" figure, but 1C computes only k = 5, 10, 20. Compute
  k in {1, 2, 3, 5, 10, 20, 40, 80} with the null; it costs little.
- **Naming.** R-AB's "separable pressure readers" collides with the role "pressure reader" that R1 un-reserves,
  which has attention-based criteria. Rename the R-AB reading "pressure mediators".
- **Outcome A has two halves.** Its second half ("mechanisms differ in where the pressure enters") is decided by
  RQ-B/C, not R-AB. Say so in the headline rule.
- **1A trimming (optional).** Mean cells of sets 1, 2 and 7 (D, H, D&H, about 58-69 heads) will almost surely read
  chance. If budget tightens, run sets 3-6 first.
- **Thresholds: which are calibrated and which are conventions.** R0 labels them all as proposals. More precisely:
  - R-A1's bands lean on one v1 cell, the far fine delta leaf;
  - R-cls's factor of two is inherited from the v1 D&H-core analysis;
  - everything else is a convention with no measurement behind it. That covers k in {5, 10, 20}, the 0.25 / 0.75 /
    0.10 / 25% cuts in R-AB, the -0.5 logit and layers 8..28 in R-lens, its +0.2, C-MLP's 0.1, Jaccard 0.6 / 0.4,
    and the drift tolerance 0.05 / 0.02 / 0.99.

  The paper should say so in one sentence, and the readings should report the neighbouring values as exploratory
  (R0 already allows that).
- **Limitations: the six named in the brief are present.** Spec §7 covers single seed (1), the unpaired comparison
  set (2), instruction-following inducement (4), the FAR wording confound (5), heads-only circuits (7), and Neutral
  Twin vs honest-instruction semantics (10). B5 shows that item 5's planned mitigation does not work as written.
- **Limitations to add to §7:**
  - mean ablation is position-broadcast and uses a pressure-prompt bank (B4);
  - the raw logit lens is uncalibrated (no tuned lens);
  - few clauses per task (12 / 20 / 17, with 1 to 150 rows each), so the effective n for cross-task contrasts is
    clauses, not instances;
  - selection and testing share a sample unless B1 is adopted;
  - single-Component ranking misses redundancy and self-repair;
  - path patching freezes non-grid Components;
  - FAR's question and stem name the Predicate;
  - the neutral twin flips the answer as well as the clause, so a neutral-twin knockout conflates "pressure
    removed" with "honest answer written";
  - deception and instructed inversion are not separated (Pile 3, item 7);
  - about 12 instances per stratum in the causal sample;
  - the four L17H24-27 heads share one KV group, so B-selector's "1 of 4 heads" is close to one test, not four.
- **Cost basis.** The estimates rest on measured jobs:
  - KO cell 401 and 367 s on H100 (49774554, 49774563);
  - load 10.4 min cold and 0.4 min warm (same jobs);
  - v1 sweep 9:33 on H200 (22899543);
  - 43-head component cells 15.1 A40-min (22899541);
  - ticket-06 stage-2 sacct.

  Path patching and every component-analysis H100 rate are extrapolated. Ticket 02's smoke test and the first 1A
  job recalibrate them, which is the right order. The mean-bank collection time (task and wikitext) is not costed
  but is small. With B1-B3 the phase-1 expectation rises by about 1.5-2 H100 GPU-h, which the 3.5 h holdback covers.
- **Order.** Phase 1 is the cheapest, most decision-relevant work, with one reservation: 1B and 1C, not 1A, decide
  the headline. If 1A and 1B compete for the same day, give 1B priority.

## 4. Verdict

**Conditional approve.** The plan is well-evidenced: every file:line claim I checked holds. It is buildable by an
Opus implementer once the Pile 2 defaults are written into the tickets. It respects the Bridges-2 route, the ledger,
the no-git rule and the literal-path rule. It is **not ready for the user** until B1-B6 land in spec §2, §5 and §7,
the tickets, and the one-page draft. The draft currently presents R-AB and R-lens as clean, discriminating,
pre-registered tests. As written, R-AB is biased towards A′ and has no null, R-lens cannot separate mechanism from
wording, and the hard-stop rule is stated two ways. Fixing them costs text and about 2 H100 GPU-h, not a redesign.
