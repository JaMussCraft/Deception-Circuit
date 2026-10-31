# RESUME: autoresearch-workflow setup (machine state; overwrite, keep under 150 lines)

Status: SETUP IN PROGRESS. Approved by user 2026-10-31 ("go"). Orchestrator compactions this session: 0.
Worktree: /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow (branch autoresearch-workflow off main 4253bb6); session pinned there.
Feature dir (canonical): docs/research/autoresearch-workflow/ in the worktree. reports/proposal-full.md is the approved design; reports/lane*.md are the research reports. `.scratch/autoresearch-workflow` in Alignment holds stale copies and becomes a symlink in the migration ticket.
Phases: P0 hygiene/config, P1 index+layout, P2 hooks+CLI, P3 protocol docs+profiles (both tools), P4 science guards, P5 pilot.
Rules: Opus on every spawn; agents never run git or EnterWorktree; orchestrator commits by explicit absolute file list; tests on /u/swong2/.conda/envs/mgnp/bin/python and /sw/external/python/anaconda3/bin/python3.9.
Isolation hook: Write/Edit only inside the worktree or outside any repo (job tmp, home); Bash must be one plain command, absolute paths, no &&/heredoc chains. Files destined for the Alignment checkout or user config are staged under /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ (mirroring the destination tree) with an idempotent apply script; the orchestrator applies them.
Do not: touch other sessions' directories (.scratch/sdr-*, selective-deception) except the planned text migration ticket; push to main; edit ~/.codex/config.toml without the user's go (restart needed).
Next action: planner (Opus, name plan-01) writes spec.md + issues/ + agent-brief.md; fresh Opus reviewer (review-00) checks them; then implement.
Open decisions for user: none.
