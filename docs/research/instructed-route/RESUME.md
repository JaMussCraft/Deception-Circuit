# Resume: instructed-route

Last rewritten: Sun 1 Nov 2026, 7:20 pm EST by claude-230e4716.

## Status

All three sub-directions have run their pre-registered tests; what remains is review, the B3 fallback transfer and wrap-up. **B2 is complete** with reviewed findings F-rte-001 (only mlp.13 replicates on SER), F-rte-002 (the quartet carries 0.54 of the SDR wish) and F-rte-004 (the FAR falsity probe transfers to SER at AUROC 0.9999 but is instruction-confounded under R2). **B1 has run** on the 100 held-out ids on Bridges-2: both tasks read "bypass" on the offline estimator of record (M_q 0.360 far, 0.462 ser, both under 0.50, intervals clear of it) and "query-side" on T2 (r_Q 0.32 and 0.43 against r_K near 0); the independent review (review-B1) is in progress. **B3**: the sycophancy positive control passed (F-rte-003, reviewed); the alignment-faking premise failed on the 100 test queries (judged gap 7.0, interval 3.9 to 10.2, proxy agreement 0.96), so the pre-registered fallback is the transfer on sycophancy alone; need N2 asks the user whether to run the fallback as written (the default) or spend part of the remaining B3 budget on a second elicitation attempt; analysis-B3 is writing the premise up and setting out J4 on sycophancy; impl-B3-t7 is making null draws exclude set members (R10). Rulings R1 to R10 and freezes G1 and G2 are in spec.md.

## Branch, worktree and commit

- Branch: `instructed-route`, pushed to origin (the Bridges-2 clone tracks it; sync with `scripts/remote/b2.sh sync-code --branch instructed-route`).
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route`.
- Last commit on the branch: `46dbc7c`, "instructed-route B1: readings on the 100 held-out ids".
- Uncommitted work: whatever impl-B3-t7, review-B1 and analysis-B3 are writing (hand-backs 31 and 33, review 05, and spontaneous/sets.py with its tests). `outputs/_launch_instructed_route/`, `outputs/_suites/mechanism-analysis/` and `outputs/_suites/mechanism-v2-coarse.b2local-261025/` are untracked fetch or scratch directories and stay untracked.
- Where the records live: the tool-owned records (state.json, worklog.json, WORKLOG.md, ledger.json) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/`; pass that path as the `dir` argument of every research-session command. Everything else lives in the worktree on the branch.

## In-flight jobs

None. Every submitted job has completed and been reconciled: r-001 to r-010, 10.0 of 65 GPU-hours reserved and about 3.6 used; OpenRouter 2.38 of 20 dollars. Bridges-2 (cis260361p) goes offline about 9 November; its SSH masters (`bridges2`, `b2dtn`) were opened non-interactively this session and die with it. Fetch with `DC_DELTA_REPO_ROOT=<this worktree> scripts/remote/b2.sh fetch`.

## Next action

1. When review-B1 hands back (reviews/05-b1-review.md): commit, log the finding(s), add the FINDINGS rows (next free number F-rte-005), findings-check.
2. When analysis-B3 hands back (reports/33-handback.md): commit, add the premise FINDINGS row after an independent review, and act on need N2 (default: J4 on sycophancy alone under R5 and R10). Before J4: commit impl-B3-t7's member-excluded null draws (hand-back 31), run the knockout parity check (`scripts/jobs/run_b3_patch.sh` with `--parity-check`, about 0.13 GPU-h, FAR held-out f_D 0.893 within 0.01), then submit J4 (`--task syc`, H200 per hand-back 18, about 1 GPU-h) under beto-delta-gpu if bimc is still stalled.
3. After J4: readings, review, FINDINGS row.
4. Wrap-up per `docs/agents/research-session.md`: full test suite on both interpreters compared by name with the baseline, README.md handoff, `research-session release`, render, memory note; delete the stray hand-back copies in the main checkout; ask the user before merging to main.

## Do not

- Do not redo mechanism-analysis phases 0 to 3 or the selection-sample path patching; see `docs/research/mechanism-analysis/synthesis.md`.
- Do not resume the closed SDR gates or stopped assays listed in `docs/research/sdr-mechanism/README.md`.
- Do not write under `docs/research/specificity-ladder/`, which the Codex session codex-01a1987e owns, and do not touch `.scratch/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception` or `.scratch/eval5-grader-fixes`.
- Do not score any set listed in `docs/research/held_out.json`; the held-out sample here means the mechanism-analysis sample of 100 ids with seed 1.
- Do not edit the frozen grader files (`spontaneous/grader/af_judge_prompt.txt`, `af_judge_config.json`, `spontaneous/judge.py`, `spontaneous/grader/proxy_tokens.json`, `proxy_tokens_g2.json`); a change is a new ruling and a new hash.
- Do not put the word for a model's output score (the one ending in "it") in a shell command, nor "git fingerprint" or similar in research-session text: the worktree isolation hook matches the three-letter substring and refuses the command. The hook also refuses research-session commands inside compound commands; run each as a single plain command.
- Do not run `scripts/route_closure_readings.py` without `--out-dir`: its default writes into `docs/research/instructed-route/results/`.

## Open decisions for the user

- N1 (resolved Sun 1 Nov 2026): the B3 grader hashes stay in spec.md only.
- N2 (open, Sun 1 Nov 2026): the B3 premise failed; run the pre-registered sycophancy-only fallback (default) or spend part of the remaining B3 budget on a second elicitation attempt first.
