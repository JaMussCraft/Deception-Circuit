# Resume: instructed-route

Last rewritten: Sun 1 Nov 2026, 7:25 pm EST by claude-230e4716, at wrap-up; amended Mon 2 Nov 2026 after the merge.

## Status

**All three sub-directions are complete and reviewed; the direction is released as done.** On Mon 2 Nov 2026 the
user declined a second alignment-faking elicitation for now (need N2 resolved; a later synthesis session may propose
it again) and had the branch merged into main, the worktree removed and main pushed. The handoff is `README.md`. Findings F-rte-001 to F-rte-008 are in
`docs/research/FINDINGS.md`, each at status reviewed with an independent Opus review under `reviews/01` to `07`.
Verdicts: B1 bypass on both tasks (M_q 0.360 FAR, 0.462 SER, offline estimator of record under R9) and query-side
on both (T2); B2 falsity probe instruction-confounded (R2), SDR wish through the quartet (0.540), only mlp.13
replicates; B3 premise failed (judged gap 7.0 against 10) so the fallback ran on sycophancy: shared (0.724) but
non-specific (null maximum 0.505), with the band and the label resting on the three shared early MLPs (heads alone
0.498 against a heads-only null maximum of 0.271). Rulings R1 to R12 and freezes G1 and G2 are in `spec.md`.

## Branch, worktree and commit

- Branch: `instructed-route` was merged into `main` at 087a7ed on Mon 2 Nov 2026 (a clean merge; the branch never
  touched `directions.json`) and then deleted locally and on origin. The Bridges-2 clone still has the branch name;
  it goes offline about 9 November.
- Worktree: removed on Mon 2 Nov 2026. Its git-ignored outputs were moved into the primary checkout at the same
  relative paths: `outputs/_analyses/instructed-route-b1/`, `outputs/_analyses/instructed-route-b2/`,
  `outputs/_studies/b3/`, `outputs/_launch_instructed_route/`, `data/b3/_downloads/` and the Slurm logs in `logs/`.
  Fetched mechanism-analysis head tables that differed from the primary copies are parked in
  `outputs/_analyses/instructed-route-fetch-diffs/`; the primary copies are canonical.
- Last commit on the branch before this file: `5cd684b`, "instructed-route B3: J4 supplement folded into review 07;
  FINDINGS gains F-rte-008; README updated".
- Uncommitted work: none. `outputs/_launch_instructed_route/`, `outputs/_suites/mechanism-analysis/`
  and `outputs/_suites/mechanism-v2-coarse.b2local-261025/` are untracked fetch or scratch directories and stay
  untracked.
- Where the records live: the tool-owned records (state.json, worklog.json, WORKLOG.md, ledger.json, handbacks/)
  live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/`;
  pass that path as the `dir` argument of every research-session command. Everything else is on `main` at the same
  paths. The main-checkout copies of hand-backs that workers wrote there by mistake were deleted at wrap-up
  after a byte comparison with the worktree copies.

## In-flight jobs

None. Thirteen reservations r-001 to r-013 are reconciled: 11.83 of 65 GPU-hours reserved and 4.82 used (the last,
job 23416459, the J4 supplement, 1,502 s on an A100). OpenRouter 2.38 of 20 dollars recorded, 2.22 settled.
Bridges-2 (cis260361p) goes offline about 9 November; its SSH masters die with the session. Delta jobs ran under
beto-delta-gpu because bimc-delta-gpu's fair share was exhausted.

## Next action

1. Nothing runs. Open follow-ups are listed in `README.md` ("What to do next") and are new proposals, not unfinished
   jobs; a synthesis session decides whether any of them, or a second alignment-faking elicitation, becomes a new
   direction.
2. If a second elicitation is ever run: record it as a new ruling in `spec.md` (premise work under the 10-hour
   sub-cap of R12), claim the direction again, and reuse `scripts/b3_premise.py` with a new variant; the J4 result
   stands either way.

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
- N2 (resolved Mon 2 Nov 2026): no second elicitation for now; the sycophancy-only fallback (F-rte-008) is the B3
  result. A later synthesis session may propose the elicitation again.
- Merge (resolved Mon 2 Nov 2026): merged into `main`, branch deleted.
