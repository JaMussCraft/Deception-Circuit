# Orchestrator rulings on the planner's open questions (2026-10-31)

These answer the eight open questions in `00-plan-handback.md`. They are binding for implementers unless the reviewer
finds a contradiction with `spec.md`, in which case the orchestrator resolves it and updates both.

OQ1. Session tag for the directions.json claim: ~~`claude-autoresearch-setup-20261031`, format
`<tool>-<slug>-<YYYYMMDD>`~~. Superseded after the plan review (spec R29): the tag is `<tool>-<first 8 characters of
the session id>`, so this session is `claude-b2cb53cd`. RS resolves sessions by id, so the id form is the machine key.

OQ2. Stale usage readings in background sessions. The status line script (`~/.claude/statusline.sh`) already fetches
the claude.ai usage endpoint (`https://api.anthropic.com/api/oauth/usage`) with the OAuth token from
`~/.claude/.credentials.json`, caches to `~/.claude/.usage_oauth_cache.json`, and merges it into `usage.json`. The
research-session `usage` command must, when `usage.json` is older than 15 minutes, perform the same fetch itself
(reuse the script's function or replicate it in Python with the same cache and lock files, token read from the
credentials file and never printed or passed on a command line) and write the refreshed reading back into
`usage.json` in the same atomic way. Only if that fetch also fails does the reading count as unknown and spawns are
denied with the human `--stale-ok` override. This removes the deadlock for sessions whose status line never runs.

OQ3. Live sessions and migration wave B. A Codex session is live today (it edited shared memory on 2026-10-31 and
owns the `sdr-*` and `selective-deception` directories). Wave B archives only directories whose state shows closed
or paused AND that are not referenced by any live row in SESSIONS.md. `sdr-session-wrapup`, every `sdr-*` directory
and `selective-deception` are excluded until the user confirms the Codex session is finished. The ticket lists the
excluded directories and the one-line command to migrate them later.

OQ4. Deception-Circuit-rooted hooks only work after merge. Accepted. Hooks in the Alignment project settings apply
as soon as the apply script runs; Deception-Circuit project settings travel with the branch. The pilot (ticket 11)
runs after the merge.

OQ5. GitHub token in the user settings env block. The user rotated the token on 2026-10-31 and the bridge needs it
there to pass it to Codex. Leave it; the apply script must never print, copy or log the env block.

OQ6. nnsight plugin: enabled in the `research` profile, disabled in `synthesis`, `writing` and `audit`.

OQ7. The Opus 600k-window test costs weekly usage. Accepted as part of the pilot; cap it at one agent with a long
read task and record the `compact_boundary.preTokens` value in the pilot report.

OQ8. autoMode environment block: extend, do not replace. Keep the SHIFT_RT entries and add Alignment and
Deception-Circuit (remotes, default branch main, accounts beto/bimc/bgrb/bjhz, Bridges-2 allocation cis260361p).

## Refinements after the plan review (2026-10-31)

The planner applied the orchestrator's rulings on the nine review blockers as spec R26-R38. Three of them refine the
answers above:

- OQ2 is now spec R8 and R27. RS refreshes a stale reading itself with the status line's cache, lock and retry
  floor, an 8 s bound, and a token read inside the process; tests mock the credentials reader and the endpoint.
- OQ3 is now spec R28. Besides every `sdr-*` directory, `sdr-session-wrapup` and `selective-deception`, the
  exclusion covers `eval5-grader-fixes` (its direction is open), the two memory logs `sdr-mechanism-review.md` and
  `selective-deception-execution.md`, and their `MEMORY.md` lines 27 and 29. Ticket 10 gives the later migration
  command; ticket 12 stages the memory rewrites as wave D.
- OQ8 is now spec R31. `json_merge` only extends lists, never duplicates an identical entry, and has no
  `replace_paths`.

## Rulings during implementation (2026-10-31, orchestrator)

- **H-i status check (after incident P3, 5:30 pm EDT).** The ticket 04 agent twice ended its turn to wait for a
  background test run that never woke it, and its hand-back read "resolved, pending the full-suite comparison".
  Spec 5.1 row H-i is amended: the SubagentStop hook also blocks once when the newest changed hand-back has no
  `Status:` line, a placeholder status (pending, to be filled, TBD, in progress), or no terminal word (resolved,
  blocked, handed-back, held, done, failed, abandoned). Ticket 12 implemented it (Comment 21); the agent brief,
  the ticket-implementer definition and the research-session protocol carry the matching waiting rule (Comments 20
  and 22).
- **Ticket 09 dedupe (4:15 pm EDT).** The 21 byte-identical `project_context` copies stay until wave D; pointer
  READMEs in wave A; the moves need the apply tool's cross-device move, which ticket 12 added.
- **Ticket 10 (4:20 pm EDT).** Copy-plus-stash for the old `.scratch/autoresearch-workflow` directory accepted; the
  dry run carries planned state forward (ticket 12).
- **Ticket 11 (4:35 pm EDT).** R20 stays binding until pilot step 9; all seven `init` files committed; the pilot-hooks
  summary placeholder stays; the staging root gets a durable copy at
  `/u/swong2/.claude/research-session/staging-20261031/`.
- **Ticket 12 (5:30 pm EDT).** Apply `12c#1` in wave C and treat `01#21` CONFLICT as expected; keep the journal-aware
  skip; apply with `--only`; keep the worktree until wave B verify passes; no symlinks at the old `project_context`
  paths; FINDINGS rows stay `pre-manifest`; resumed older agents add a `Status:` line to their hand-backs.
