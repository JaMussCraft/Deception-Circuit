# Ticket 12 — review of `result_summary.md`

Ticket 12's last checkbox replaces the usual code review with a **subagent
review of the write-up for claims not supported by the outputs**. Two
independent sub-agents were run, on the two axes the code-review skill would
have used:

- **Unsupported claims** — locate every quantitative and factual claim in a
  named file under the cell, and report what cannot be located, what disagrees,
  what is interpretation stated as measurement, what cites the wrong file, and
  what is asserted about jobs the write-up did not run.
- **Spec** — judge the write-up against ticket 12's checkboxes, the spec's
  pre-registered hypothesis (including the mid-layer Q-versus-V question),
  `docs/component-roles.md` and ADR-0002.

**Both handbacks failed** — the same `SubagentHandback` failure tickets 02, 02b,
04, 06, 07, 09 and 10 all record — and both reports arrived afterwards by
`SendMessage`, the claims axis also by way of the orchestrator. **The review is
independent of the author.** Both reviewers read the cell's files themselves
and re-derived the numbers rather than trusting the prose.

Verdicts: claims axis, 11 findings with a "suggested minimum fixes" list; spec
axis, **ship with changes**, 9 findings, none needing a rerun.

The orchestrator ruled that every item in the claims reviewer's minimum-fix list
is taken verbatim, added seven further requirements lettered (a) to (g) below,
and made one hard condition: **the ticket does not close until job 22281702 has
completed and section 7 carries its measured numbers; until then nothing in the
write-up may describe the family knockout as run.**

## What both reviewers verified as correct

Worth recording, because it is most of the document. Between them they
re-derived from the files: the whole 18-row head table; the knockout ranking and
its sum `+1.3218`; the five DLA condition totals; the 16.4 percent share; the
`sum_check` numbers; the logit-lens rows and flips; the attention checks
(2.7e-3 against a 2e-2 tolerance, `max_outside` exactly 0.0); both gaps and
their positive counts; the 19 x 41 = 393 grid with no cell lacking a mean; both
direct-effect sums; every cell value in both strongest-cell tables; the Segment
pass selections at threshold 0.01 and the `head.8.15 -> v.9.3` decomposition;
the entire Q/K/V table including the signed column sums; the whole sweep table,
its floor counts and its sums; the sample marginals and strata; the 71 + 29 =
100 split; and the three byte-identity claims (315/315, 72/72, 216/216, with
nine both-empty MLP attention cells). `roles/roles.json` matches `ca10-roles`
in counts and thresholds. `carry_roles`, `PROTECTED_COLUMNS` and `merge_cells`
behave as section 2 describes, and the default `--path-position-threshold` is
0.05 and does select exactly one cell here.

## Claims axis — findings and disposition

| # | finding | disposition |
|---|---|---|
| 1 | **Job 22281702 never ran**, yet sections 1.1, 2, 6.2, 7 and 8 describe it in the past tense, and its "A40" card and "312 forwards" are asserted. | **Taken.** Section 2 now says four analysis jobs plus a fifth for the family knockout and points at section 7 for its state; section 8's row defers to section 7 for card, forwards and wall; caveat 2 is self-contained and no longer leans on section 7; section 7 states the job's state. The ticket is not closed until the job completes and the section carries measured numbers. |
| 2 | Section 8's dry-run error direction is backwards: the estimate **under**-predicts the item-swap grid by 4 percent (994.6 s against 1038.5 s) and over-predicts the honest one by 30 percent. | **Taken**, with both numbers and the `cost` keys named. An earlier self-correction of this sentence had silently failed to apply; the reviewer caught the live text. |
| 3 | "Everything else in the grid is below 0.005" is false for the honest-instruction grid: four more cells clear it (`head.5.5 -> k.8.3` −0.0064, `head.8.14 -> v.14.1` −0.0060, `head.13.17 -> q.14.7` +0.0057, `head.13.17 -> q.14.21` +0.0054). | **Taken.** The sentence is now scoped to the item-swap grid and the four honest cells are listed, with a pointer to section 5 where three of them bear on the hypothesis. |
| 4 | `head.14.22 -> q.17.25` at +0.0068 is called "inside" a 0.005 noise floor it is above, at 5.3 se. | **Taken.** The claim is now "below the 0.01 path floor", with the note that `docs/component-roles.md` uses "inside the noise" for this cell and that the cell is in fact above it. |
| 5 | The headline Q-versus-V conclusion rests on `head.8.15 -> v.9.3`, which is layer 9 — the hypothesis's **binding** band, not the 12-to-15 mid band — and the criteria doc warns that the strongest-single-receiver reading does not test Q-dominance. | **Taken.** Executive summary 6 and section 5's verdict now lead with the mid-band evidence, call the size comparison indeterminate there, demote the layer-9 cell to a binding-band observation, and quote the criteria doc's warning. |
| 6 | Section 5 says the layer 8-to-9 heads have "no direct effect"; L9H12's is significant at z = 2.5 and fails the floor, not significance. | **Taken**, with "(z = 2.5, below the 0.01 floor)" in the sentence. |
| 7 | Section 8's mtimes come from the staging cell, which the sentence never names, and one timestamp is wrong (13:09:42, not 13:09:47, so 8 min 18 s). | **Taken.** Both fixed. |
| 8 | The queue-wait range understates the minimum (12m20s, not 11 minutes) and "submitted together" is true of three of the four jobs. | **Taken**, with all four `Submit`-to-`Start` intervals. |
| 9 | Unsourced numbers: the 2208 eager and 260 knockout forward counts (no cost block in either JSON), the "38 minutes" combined job, the dry-run rehearsals, the attention-sink attribution, ticket 09's cross-card noise, and the model version string. | **Partly taken.** Both forward counts are now marked **derived** and the sentence says neither file records a cost block. The 38-minute figure is now attributed to ticket 09 with the note that no combined job of this run exists to cite, and the cancelled-and-resubmitted history is stated. The attention-sink, cross-card-noise and model-version attributions are left, named to the ticket or doc they come from, because they are context rather than results of this run. |
| 10 | The claim that tickets 06, 07 and 09 ran on A40s is not this run's to assert, the "so" inverts the logic, and those cells live in a different worktree. | **Taken.** Byte-identity is now the evidence and the shared card the inference, and the sibling worktree path is given. |
| 11 | Smaller interpretation items: the knockout fraction's choice of denominator; `max_outside = 0.0` being near-tautological; `sum_check` running on 8 instances; L24H18 and L24H25 clearing z = 2.0 only marginally; the ticket 10 comparison being uncheckable from this cell. | **Mostly taken.** Both denominators are now given for the knockout fraction, and the `sum_check`'s n = 8 is stated. The `max_outside` sentence is left: it is stated as a check that passed, not as a discovery. The marginal z values are visible in the table the sentence sits under. |

## Spec axis — findings and disposition

| # | finding | disposition |
|---|---|---|
| 1 | The direct test is answered with evidence from outside the mid band, and the KV-group asymmetry (Q per head, K and V per group of four, including non-circuit heads) is stated once and never used. | **Taken**, jointly with claims finding 5. Section 5 now leads with the mid-band Q **signs**, states the per-receiver head-count asymmetry where Q and K/V are compared by size, names `covers_heads` against `circuit_heads` for `v.9.3` and `k.17.6`, and notes that layer 17 head 24 is one of the sweep's seven. |
| 2 | The same false universal as claims finding 3. | **Taken** (see above). |
| 3 | Section 5's layer-17 paragraph compares two opposite-signed cells by magnitude to answer a directional question; and the `head.14.22 -> q.17.25` sign flip is exactly what ADR-0002 predicts, which is worth saying. | **Taken.** The layer-17 bullet now separates "which receiver carries the most" from "which way", and section 4 says the flip is the predicted one. |
| 4 | Section 7 is a bare placeholder and the document does not admit it where a reader looks; caveat 2 dangles on it. | **Taken** (see claims finding 1). |
| 5 | `role_confirmed` does not exist as a column, so "empty on every row" is wrong and the ticket's second checkbox reads as unmet. | **Taken, and the ticket says so.** The write-up now explains that the column is absent by design, that `head_table.PROTECTED_COLUMNS` is that one name, that `roles/roles.json` records `role_confirmed: null` per Component, and that the researcher fills it by adding the column, which every later run carries forward. No column was fabricated by hand: a hand-written column would be dropped by the next analysis run into the cell. |
| 6 | The binder clause is answered from the reads view alone; the depends clause's evidence (`head.8.15 -> v.9.3`, `head.5.5 -> k.8.3`) is in the files and is discussed only under selection. | **Taken.** Section 5's binding paragraph now separates the onward-path clause, which two binding-band heads meet, from the reads clause, which none meets. |
| 7 | Executive summary 5 compares opposite signs by magnitude without saying so. | **Taken.** |
| 8 | The 16.4 percent headline reverses on the paired subset: −0.0220 against +1.5857 over the 71. | **Taken**, in caveat 1. |
| 9 | Minor bundle: `sum_check` n; all unknowns being `insufficient` and none `disagree`; the sibling-worktree paths; no pressure-reader signature; the threshold's consequence belonging in section 5's verdict; the executive summary's denominator. | **Taken**, all six. |

On the orchestrator's further calls against this axis: the verdict sentence now
reads "indeterminate in the mid band on size, and against Q on the sign
reading"; the predicted sign flip is stated and **unbolded**, since a predicted
result is not a finding; section 7 says "pending, job 22281702" with the state
`sacct` reports; and the open questions gain **whether the roles pass should
write an empty `role_confirmed` column**, which `head_table.merge_columns`
currently forbids by name — the same refusal that protects a confirmed role.

## Orchestrator's additional requirements

| | requirement | where it landed |
|---|---|---|
| (a) | every number names its file or is marked derived | section 8's two derived counts; the unsourced-number cases in claims finding 9 |
| (b) | executive summary 6 carries section 5's hedge | rewritten as above |
| (c) | knockout fractions state their denominator, both given once | executive summary 3 |
| (d) | say the DLA sum check ran on 8 instances | section 3 |
| (e) | name the `component-analysis` worktree; byte-identity implies the card | executive summary 1 |
| (f) | list the four omitted honest-instruction cells | section 4 |
| (g) | add "(z = 2.5, below the 0.01 floor)" for L9H12 | section 5 |

## Nothing found that needed a rerun

Neither reviewer found a measurement error: every disputed item was prose about
the measurements, a missing denominator, a mis-scoped universal, or an
attribution. The analyses themselves were checked against the files and stand,
which is also what the byte-identity against `ca06-paired2`, `ca07-knockout` and
`ca09-path-patching` says independently.
