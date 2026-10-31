# RESUME: autoresearch-workflow setup (machine state; overwrite, keep under 150 lines)

Status: SETUP IN PROGRESS. Approved by user 2026-10-31 ("go"). Orchestrator compactions this session: 0.
Worktree: /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow (branch autoresearch-workflow off main 4253bb6); session pinned there.
Feature dir (canonical): docs/research/autoresearch-workflow/ in the worktree. reports/proposal-full.md is the approved design; reports/lane*.md are the research reports. `.scratch/autoresearch-workflow` in Alignment holds stale copies and becomes a symlink in the migration ticket.
Phases: P0 hygiene/config, P1 index+layout, P2 hooks+CLI, P3 protocol docs+profiles (both tools), P4 science guards, P5 pilot.
Rules: Opus on every spawn; agents never run git or EnterWorktree; orchestrator commits by explicit absolute file list; tests on /u/swong2/.conda/envs/mgnp/bin/python and /sw/external/python/anaconda3/bin/python3.9.
Isolation hook: Write/Edit only inside the worktree or outside any repo (job tmp, home); Bash must be one plain command, absolute paths, no &&/heredoc chains. Files destined for the Alignment checkout or user config are staged under /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ (mirroring the destination tree) with an idempotent apply script; the orchestrator applies them.
Do not: touch other sessions' directories (.scratch/sdr-*, selective-deception) except the planned text migration ticket; push to main; edit ~/.codex/config.toml without the user's go (restart needed).
Plan: spec.md (R1-R38), issues/01-12, agent-brief.md; reviewed by review-00 (approve with fixes, all applied); committed on the branch.
Waves: A = {01, 04} (RUNNING since ~1:05 pm CDT: agents impl-01, impl-04); then {02, 07, 08}; then 03; then {05, 06}; then {09, 10}; then 11; then 12. Hook installation is wave H, only after RS tests pass from the installed path and a smoke test. Wave D (live Codex session's files) waits for the user's confirmation that the Codex session is finished. Wave C (~/.codex/config.toml) waits for the user's go.
Pending from planner: addendum ruling (unregistered sessions get cap and stale checks only; freeze needs registration) to be folded into R5/§5.2/ticket 02 before ticket 02 spawns.
Next action: on each hand-back, read F/reports/<NN>-handback.md, commit the listed W files, run the staged tests, apply wave A ops with the apply tool (dry-run first), then spawn the next wave.
Open decisions for user: none.
