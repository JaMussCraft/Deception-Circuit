# Hand-back 274: Task 3 bounded CPU validation readiness

Agent: independent source reviewer, gpt-6.1-sol. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task-3-brief.md`. Status: resolved for bounded CPU validation readiness only.

## What changed

Review verdict: **READY for the proposed bounded CPU validation. No blocking source finding identified.** Severity: none within this review scope. This is not Task 3 acceptance or GPU permission.

Only new review artifacts were written: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-review274/check_pins.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-review274/checks.json`, and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/274-handback.md`. No source, authority, research state, scheduler, or Git changes were made; no apply operation is staged. The author's narrative report was not read.

Source findings and citations:

- Full-only request and immutable CPU COMPLETE binding cover actual job/config/bank/packet/domain and publication deadline: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py:73`, `:98`, `:343`. CPU capture and composite remain separate; member hashes and final recapture preserve the original CPU proof (`:605`, `:630`, `:687`).
- Cutover proof must be fresh at its recorded finalization, complete, quiescent and unreleased; subsequent reuse authenticates its sealed bytes and same actual transition/immutable native lineage (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py:119`, `:128`, `:568`, `:608`, `:669`). This matches the root ruling; the helper does not invent a fresh no-reader claim after the authorized reader begins.
- Native normalization originates from the pinned source export, checks project import origins, traverses mapping/admission/snapshot closure, and separately checks every immutable charge plus Decimal exact phase/global totals (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py:267`, `:285`, `:296`, `:191`). No historical one-hour resource default is admitted.
- Live ordinary cap, native checkpoint projection using since-register, targeted session/freeze, and live-versus-cached checks are explicit. The expired-post-reset route requires aware ordered timestamps, live age at most sixty seconds and live below cap; no old exception grants authority (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py:150`, `:219`).
- CPU waiting only shortens the immutable bound. Remote inspection supplies the remote UID; GPU ownership does not assume the Delta UID. Remote publication independently checks Slurm identity/resources and both fixed publication deadline and allocation entry floor before exclusive atomic publication (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py:316`, `:389`, `:412`, `:429`, `:488`).
- Required cases are present: offset near checkpoint and false/incomplete/future cutover (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/closure/sdd/plan-a2-full-score-operational186/candidate/tests/test_full_score_root_integration.py:11`, `:29`); independently expired publication deadline/entry floor (`:38`); fake transport through Producer and release consumer (`:232`); original native origin/successor/admission chain with tamper rejection (`:258`); remote/local UID disagreement (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/closure/sdd/plan-a2-full-score-operational186/candidate/tests/test_full_score_root_identity.py:9`). The fake transport and original native chain are complementary tests; the former stubs the native facade, and the latter invokes the original native implementation with fixture ledger routing.

## How verified

Read the frozen source, manifests, resource declaration, runner, original native fixture and regression tests directly. Accepted Task 1/Task 2 were treated as dependencies, not re-reviewed.

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-review274/check_pins.py
```

Observed: exit zero; both supplied manifest digests matched; all 551 packet entries and 548 original-source entries matched their file hashes; five Python files parsed; helper SHA was `522e6c9a87aaa041a2d63fb3218dd3637791ab859182d8619bc0a4ec0956d085`. The bounded stdlib check took approximately one second. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-review274/checks.json`.

Runner review: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/run_cpu_green.py:25` requires a CPU allocation and rejects GPU allocation variables; it selects normal supported interpreters without isolated mode, checks Python minor/pytest identity and module origin telemetry, isolates pytest configuration, retains historical RED and candidate GREEN logs/XML, authenticates pins before/after each phase, and applies per-environment bounds. `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3/resources.json` declares two CPUs, eight GiB, seven minutes, baseline twenty seconds and full suite 150 seconds per environment. The resulting identity must be checked against Python 3.9.18 / pytest 8.3.3 and Python 3.12.13 / pytest 9.1.1; patch versions are recorded by the runner but not asserted by its minor-version check.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No full/native suite, model import, job, SSH, transport, admission, resource binding or GPU execution occurred. This review does not turn supplied smoke claims into independently observed suite results. Required next gate is root CPU execution with 98 historical RED cases and 379 GREEN cases in each normal supported environment, attribution by test name and actual interpreter identity, complete logs and provenance, within declared resources and timeouts. Missing/error/skip cases or timing failures require review before acceptance.

Actual full scoring remains gated by measured resource/capacity feasibility and actual placement, immutable source/input/bank/protection closure, live budget/usage/checkpoint checks, root-managed fresh reader-safe reservation and COMPLETE successor finalization, original native normalization, authentic CPU preflight, per-start cache proof and once-only remote publication. The historical proof cannot authorize a new transition.

## Open questions

No design question blocks bounded CPU validation. Default: root may proceed only with that validation; keep Task 3 acceptance and all real operational/GPU permissions closed until their evidence is reviewed. Root retains startup adapter synchronization and live session/usage control ownership; this worker did not mutate either.
