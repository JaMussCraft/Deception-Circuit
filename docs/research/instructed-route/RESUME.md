# Resume: instructed-route

Last rewritten: Sun 1 Nov 2026, 4:35 pm EST by claude-230e4716 (after compaction 1).

## Status

The direction instructed-route is claimed and registered by session claude-230e4716. B2: P3 (the SER MLP replication) gave F-rte-001 (only mlp.13 replicates; F-mech-009 superseded) and P2 (the SDR wish test) gave F-rte-002 (quartet knockout removes 0.54 of the wish effect, nulls near zero), both independently reviewed; P1 (the falsity probe) waits on its H200 capture job. B3: the calibration run J1 and its judge pass are done, ruling R6 chose variant V-B (judged gap 10.5 on the 20 calibration queries) and proxy P2 (agreement 0.984 against 0.670 for P1), freeze G2 is recorded, and J2 (test generation, 2,600 rows) is queued; J3 (the sycophancy control) is queued. B1: the code is complete through tickets 5 and 6 (committed d73783e); ticket 7 (batch files, dry runs, Bridges-2 and Delta test-only) is in progress and no B1 job has run. Bridges-2 goes offline about 9 November. The pre-registered rules are in spec.md with rulings R1 to R6 and freezes G1 and G2.

## Branch, worktree and commit

- Branch: `instructed-route`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route`.
- Last commit on the branch: `84a0ac9`, "instructed-route B3: ruling R6 (variant V-B, primary proxy P2) and freeze G2 of the calibrated proxy tokens".
- Uncommitted work: ticket 7's files from impl-B1-t7 (`jobs/B1-{smoke,far,ser}.batch`, `tests/test_instructed_route_b1_jobs.py`, a change to `scripts/remote/b2.sh`), to be committed by file list once its hand-back (reports/23-handback.md) lands. `outputs/_launch_instructed_route/` is a scratch launch directory and stays untracked.
- Where the records live: the tool-owned records (state.json, worklog.json, WORKLOG.md, ledger.json) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/`, because the research-session tool mirrors the registered session's state into the checkout that contains the session's launch directory, and the worktree isolation hook refuses other writes there. Pass that main path as the `dir` argument of every research-session command. Everything the session writes itself (RESUME.md, spec.md, plans/, reports/, reviews/, results/, code) lives in the worktree on the branch. The two sets of files meet at the merge.

## In-flight jobs

All on Delta under bimc-delta-gpu; the waiters are armed in this session and must be re-armed from `research-session job list` after a compaction. The ledger holds 5.75 of 65 GPU-hours reserved (r-001 to r-007) and $0.55 of $20 OpenRouter spent.

| Job | Partition | What it computes | Output directory | State at rewrite |
|---|---|---|---|---|
| `23412454` | gpuH200x8-interactive | P1 capture: falsity-probe residuals and per-token attribution for 9,972 rows in 18 cells | `outputs/_analyses/instructed-route-b2/p1-cap` | pending (priority) since 3:42 pm |
| `23412270` | gpuA100x4 | B3 J3, the sycophancy positive control: five sets at the readout against 20 nulls on 800 MMLU items | `outputs/_studies/b3/j3_sycophancy` | pending (priority) since 3:33 pm |
| `23412904` | gpuA100x4 | B3 J2, test generation: V-B, 100 test queries, base with 10 samples plus greedy per tier, greedy-only C1 and C2; 75 min reserved, 0.57 h estimated | `outputs/_studies/b3/j2_test` | submitted 4:30 pm |

## Next action

1. When J2 completes: reconcile the ledger, then judge the 2,200 base rows with `scripts/b3_judge.py` under the existing reviewed main ledger (`outputs/_studies/b3/judge/ledger_main.jsonl`, $10 cap), run the 200-row Sonnet cross-check under a new reviewed ledger ($3) and the 10% re-judge through a separate cache, record the spend with `ledger api`, then `scripts/b3_premise.py` with `--labels`, `--sonnet-labels`, `--rejudge-labels` and `--tokens spontaneous/grader/proxy_tokens_g2.json` for the premise verdict (gap at least 10 on at least 50 queries, agree at least 0.80). Log the verdict as a decision; ask the user before dropping B3 to sycophancy alone if it fails.
2. When J3 completes: reconcile, read the sycophancy control result, hand it to a reviewer, log a finding.
3. When the P1 capture completes: reconcile, run `scripts/falsity_probe.py fit`, `score` and `read` on p1-cap per `plans/B2-plan.md` section 1 and ruling R2, review, log the finding and add the FINDINGS row.
4. When impl-B1-t7 hands back: commit its files by list, push the branch `instructed-route` (not main) so `scripts/remote/b2.sh sync-code` can fetch it, submit the B1 smoke to Bridges-2 (Delta H200 as the fallback), then far and ser, run `scripts/route_closure_readings.py`, review, log findings.
5. After the premise verdict: J4 transfer (`scripts/jobs/run_b3_patch.sh --task af --proxy P2`, split arms, H200), C3 control, optional scratchpad.
6. Before any merge: run the full test suite on both interpreters and compare failures by name with the baseline; wrap up per `docs/agents/research-session.md` (README handoff, FINDINGS rows, release, render, memory note); ask the user before merging to main.

## Do not

- Do not redo mechanism-analysis phases 0 to 3 or the selection-sample path patching; see `docs/research/mechanism-analysis/synthesis.md`.
- Do not resume the closed SDR gates or stopped assays listed in `docs/research/sdr-mechanism/README.md`.
- Do not write under `docs/research/specificity-ladder/`, which the Codex session codex-01a1987e owns, and do not touch `.scratch/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception` or `.scratch/eval5-grader-fixes`.
- Do not score any set listed in `docs/research/held_out.json`; the held-out sample here means the mechanism-analysis sample of 100 ids with seed 1.
- Do not edit `spontaneous/grader/af_judge_prompt.txt`, `af_judge_config.json`, `spontaneous/judge.py`, `spontaneous/grader/proxy_tokens.json` or `proxy_tokens_g2.json` (freezes G1 and G2); a change is a new ruling and a new hash.
- Do not put the word for a model's output score (the one ending in "it") in a shell command: the worktree isolation hook matches a three-letter substring of it and refuses the command. Write "answer-token attribution" instead. The hook also refuses research-session commands with long quoted text inside compound commands; run each as a single plain command.

## Open decisions for the user

- N1 (resolved Sun 1 Nov 2026): the B3 grader hashes stay in spec.md only.
