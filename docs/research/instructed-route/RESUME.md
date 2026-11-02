# Resume: instructed-route

Last rewritten: Sun 1 Nov 2026, 7:25 pm EST by claude-230e4716, at wrap-up.

## Status

**All three sub-directions are complete and reviewed; the direction is released as paused pending two user decisions
(the merge to main and need N2).** The handoff is `README.md`. Findings F-rte-001 to F-rte-008 are in
`docs/research/FINDINGS.md`, each at status reviewed with an independent Opus review under `reviews/01` to `07`.
Verdicts: B1 bypass on both tasks (M_q 0.360 FAR, 0.462 SER, offline estimator of record under R9) and query-side
on both (T2); B2 falsity probe instruction-confounded (R2), SDR wish through the quartet (0.540), only mlp.13
replicates; B3 premise failed (judged gap 7.0 against 10) so the fallback ran on sycophancy: shared (0.724) but
non-specific (null maximum 0.505), with the band and the label resting on the three shared early MLPs (heads alone
0.498 against a heads-only null maximum of 0.271). Rulings R1 to R12 and freezes G1 and G2 are in `spec.md`.

## Branch, worktree and commit

- Branch: `instructed-route`, pushed to origin at wrap-up, 51 commits ahead of `main`. `main` has one commit the
  branch lacks (16ce5f7, the Codex claim of specificity-ladder in `directions.json`), so the merge is a true merge
  and `directions.json` may need a hand resolution. The Bridges-2 clone tracks the branch.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route`.
- Last commit on the branch before this file: `5cd684b`, "instructed-route B3: J4 supplement folded into review 07;
  FINDINGS gains F-rte-008; README updated".
- Uncommitted work: none in the worktree. `outputs/_launch_instructed_route/`, `outputs/_suites/mechanism-analysis/`
  and `outputs/_suites/mechanism-v2-coarse.b2local-261025/` are untracked fetch or scratch directories and stay
  untracked.
- Where the records live: the tool-owned records (state.json, worklog.json, WORKLOG.md, ledger.json, handbacks/)
  live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/`;
  pass that path as the `dir` argument of every research-session command. Everything else lives in the worktree on
  the branch. The main-checkout copies of hand-backs that workers wrote there by mistake were deleted at wrap-up
  after a byte comparison with the worktree copies.

## In-flight jobs

None. Thirteen reservations r-001 to r-013 are reconciled: 11.83 of 65 GPU-hours reserved and 4.82 used (the last,
job 23416459, the J4 supplement, 1,502 s on an A100). OpenRouter 2.38 of 20 dollars recorded, 2.22 settled.
Bridges-2 (cis260361p) goes offline about 9 November; its SSH masters die with the session. Delta jobs ran under
beto-delta-gpu because bimc-delta-gpu's fair share was exhausted.

## Next action

1. If the user approves the merge: merge `instructed-route` into `main` (a true merge; resolve `directions.json` by
   keeping both claims), run both test suites on main, and commit the main-checkout research-session records
   (`docs/research/instructed-route/{state,worklog,ledger}.json`, `WORKLOG.md`, `RESUME.md`,
   `docs/research/directions.json`, `SESSIONS.md`, `DIRECTIONS.md`, the global `ledger.json`) by explicit file list.
2. If the user chooses a second alignment-faking elicitation for need N2: record it as ruling R13 in `spec.md` (it is
   premise work under the 10-hour sub-cap of R12), re-claim the direction, and reuse `scripts/b3_premise.py` with a
   new variant; the J4 result stands either way.
3. Otherwise nothing runs. Open follow-ups are listed in `README.md` ("What to do next") and are new proposals, not
   unfinished jobs.

## Do not

- Do not redo mechanism-analysis phases 0 to 3 or the selection-sample path patching; see
  `docs/research/mechanism-analysis/synthesis.md`.
- Do not resume the closed SDR gates or stopped assays listed in `docs/research/sdr-mechanism/README.md`.
- Do not write under `docs/research/specificity-ladder/`, which the Codex session codex-01a1987e owns, and do not
  touch `.scratch/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception` or
  `.scratch/eval5-grader-fixes`.
- Do not score any set listed in `docs/research/held_out.json`; the held-out sample here means the
  mechanism-analysis sample of 100 ids with seed 1.
- Do not edit the frozen grader files (`spontaneous/grader/af_judge_prompt.txt`, `af_judge_config.json`,
  `spontaneous/judge.py`, `spontaneous/grader/proxy_tokens.json`, `proxy_tokens_g2.json`); a change is a new ruling
  and a new hash.
- Do not put the word for a model's output score (the one ending in "it") in a shell command, nor "git fingerprint"
  or similar in research-session text: the worktree isolation hook matches the three-letter substring and refuses
  the command. The hook also refuses research-session commands inside compound commands and shell heredocs that
  mention version control; write such files with the editor tool.
- Do not run `scripts/route_closure_readings.py` without `--out-dir`: its default writes into
  `docs/research/instructed-route/results/`.

## Open decisions for the user

- N1 (resolved Sun 1 Nov 2026): the B3 grader hashes stay in spec.md only.
- N2 (open, Sun 1 Nov 2026): the B3 premise failed; the pre-registered sycophancy-only fallback has run (F-rte-008).
  A second elicitation attempt remains possible as a new ruling under the 10-hour sub-cap.
- Merge (open): merge `instructed-route` into `main`, or keep it on the branch.
