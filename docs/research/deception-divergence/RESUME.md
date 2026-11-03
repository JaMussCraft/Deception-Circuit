# Resume: deception-divergence

Last rewritten: Mon 2 Nov 2026, 11:40 pm EST by claude-5b9b1c28 (after compaction 4). Note: Delta file times are Central; these timestamps are Eastern.

## Status

Phase 1 is running under the user's N1 answer (continue under the 80 percent cap, run the option B follow-up, find a defensible route to U1) and ruling R6. Phase 0 is closed: D1 null on size on every task (F5, reviewed, `reviews/02-d1-review.md`); D4 done and reviewed (F1 to F4, `reviews/01-d4-review.md`). Both listener routes to U1 are closed: the phrasing-1 and phrasing-4 flip pools are empty on every task (F6, F7, both reviewed, `reviews/03-d1-followup-review.md`). The D2 premise GPU job is done (Bridges-2 `50155519`, full-sequence path of record under R14; `reports/07-handback.md`): the classifier arm separates D from I on SDR only (gap 0.160, interval 0.086 to 0.227, 0.136 under refusal ablation, so the refusal control does not explain it), FAR shows no gap (0.005) and SER misses the 15-point bar (0.145). The paid judge stage is complete ($2.71, 4,064 calls, five reviewed ledgers) and the final read is written (`outputs/_analyses/deception-divergence/d2/readings.md`, final true): the acts-on-it arm is uninformative because the model corrects its forced wrong answer in 96 to 99 percent of rows in every condition, judge checks agree (cross-check 0.965, re-judge 1.000), and the frozen rule passes the premise on SDR from the classifier arm alone, by one point over the 15-point bar. The independent review (`reviews/04-d2-review.md`) confirms every number and that R13 was applied as frozen, but finds the whole SDR gap on predicate-form inversion clauses (0.241 on 166 ids) with a zero gap on act-form clauses that name the wrong answer as D's do, on every task: the classifier reads the instruction clause and the gap tracks clause wording. The R2 reading on every task is that I patterns like D (instructed falsity, since H states the same falsehood and reads 0.000). The frozen-classifier shift of H toward D under ablation is a common-mode shift, not evidence that the D-against-H axis is the refusal direction (the refit still separates D from H perfectly). The review advises against admitting U1 on this evidence alone (R6 iv's letter is met except for the new ruling it requires) and names two preconditions: an honest-instructed H arm and a form-matched D-I reading. Finding F8 is recorded as reviewed, incident P2 (proxy-freeze wording) is logged, and need N2 asks the user to choose between the pre-registered follow-up, admitting U1 anyway, or wrapping up. Under N2's stated default the follow-up is pre-registered as ruling R15 (plan `plans/D2-followup-plan.md`, independent plan review `reviews/05-d2-followup-plan-review.md`): an honest-instructed HI arm with token-matched honest mirrors of D's clauses, DT and HT arms completing a 2x2 of instruction content by first-answer truth, an IH frame-word control, the classifier refit D against HI, the primary reading the signed act-form D-I gap on FAR, and three per-task branches of which only (c) on FAR can re-admit U1. It costs about 0.45 GPU-hours on Bridges-2 and no judge spend. U1 trainer code and any patching ruling wait for the user's answer to N2 regardless. U1 trainer code still waits for the user's word on Codex coordination.

## Branch, worktree and commit

- Branch: `deception-divergence`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
- Last commit on the branch: `4b63e0b`, "ruling R15 freezes the D2 follow-up; plan review 05" (pushed; Bridges-2 clone at `fb2cb9e`, to be synced before the follow-up job).
- Uncommitted work, if any: this RESUME; the worker's follow-up code, tests, plan amendments and hand-back 09, committed by file list when the hand-back is read.
- Tool-owned records (state, worklog, ledger, handbacks) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/`; pass that path as the `dir` argument of every research-session command. Everything else is on the branch.

## In-flight jobs

No GPU job is in flight. Reservations r-001 to r-008: 8.33 GPU-hours reserved, 2.91 actual. OpenRouter: $2.71 spent on the D2 judge (4,064 paid calls; `ledger.json` shows 8,409 calls because the tool merged the 4,345-call reserve with the actual). Bridges-2 (cis260361p) is the working cluster; Delta's batch queues projected week-long waits and its interactive partitions carry a one-hour cap. The user allows any Delta or Bridges-2 allocation (shared memory note `cluster-allocations`).

| Process | Where | What it does | Output | Expected finish |
|---|---|---|---|---|
| `d2-worker` (Opus) | worktree | amends the follow-up plan to R15, builds `scripts/d2_followup.py` test-first with a Bridges-2 wrapper, runs both test suites and the CPU dry run, writes hand-back 09 | `plans/D2-followup-plan.md`, `scripts/d2_followup.py`, `tests/test_d2_followup.py`, `scripts/jobs/`, `results/d2_followup/build_report.json`, `reports/09-handback.md` | Tue about 1:00 am EST |

## Next action

1. When `d2-worker` reports hand-back 09: read it, commit by file list, push, sync the Bridges-2 clone (`DC_DELTA_REPO_ROOT=<worktree> scripts/remote/b2.sh sync-code --branch deception-divergence`), dry-run the wrapper there (`DC_CLUSTER=bridges2 DC_B2_ALLOC=cis260361p`, mgnp env activated), check the session points against checkpoint 1 (24), `ledger add` 0.75 GPU-hours with `--job-id`, submit with `-t 00:45:00`, `job add`, start the waiter, log the `job` entry.
2. When the job completes: fetch `outputs/_analyses/deception-divergence/d2_followup/`, reconcile the ledger, have the worker run the read and write the per-task branches, the direction label and the joint reading into hand-back 09 (Results); copy readings and manifests into `results/d2_followup/`; independent Opus review; log the finding and a `decision` entry. If the direction label is (a) or (b), U1 is closed through D2 and the direction is ready for wrap-up (handoff README, findings rows, memory). If (c) on FAR, write nothing for U1 until the user answers N2 and confirms Codex coordination.
3. If the user answers N2 before the job: follow the answer (A run, B stop the job and open the U1 ruling question, C cancel and wrap up).
4. Do not write the patching ruling or U1 trainer code before the user's answers.
4. Checkpoint 1 fires at 24 session points (cadence set by the user); cap pause at 80 percent weekly.

## Do not

- Do not redo any first-token "necessary in D, not in user-turn I" test (Codex A1 to A3, `docs/research/specificity-ladder/START.md`), the instructed-route tests B1 to B3 (`docs/research/instructed-route/README.md`), the mechanism-analysis phases or the closed SDR gates.
- Do not write under `docs/research/specificity-ladder/`, the `specificity-ladder` worktree or branch, `.scratch/sdr-*`, `outputs/_analyses/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception`, `.scratch/eval5-grader-fixes`, or `docs/research/instructed-route/` (except the F-rte-008 row in FINDINGS.md).
- Do not score any set listed in `docs/research/held_out.json`.
- Do not write U1 trainer code before the user has said the Codex coordination is done (reaffirmed in R6 v).
- Do not create judge ledgers whose ceilings sum to more than the remaining OpenRouter cap (the D2 ledgers summed to $21 against a $20 cap while spend was $2.71; review 04, hand-back check).

## Open decisions for the user

- N2 (opened Mon 2 Nov 2026, about 10:45 pm EST): after the D2 verdict, (A) run the pre-registered follow-up and decide U1 on its result, (B) admit U1 now on the letter of R6 iv against review 04's advice (needs the Codex coordination confirmed and a ruling on what U1 trains on), or (C) wrap the direction. Default while unanswered: pre-register and run the follow-up (R15, under 0.75 GPU-hours reserved, no judge), no U1 code, no patching ruling. N1 was answered on Mon 2 Nov 2026 (continue, option B, any allocation).
