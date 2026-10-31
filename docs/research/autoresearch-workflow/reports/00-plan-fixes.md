# 00 — Plan fixes after review (planner, 2026-10-31)

The reviewer's verdict in `reports/00-plan-review.md` was "approve with fixes". The orchestrator ruled on all nine
blockers and four extra items. This report lists each one and the exact edits made. Files changed:
`spec.md` (now 519 lines, under the 520 limit), `agent-brief.md`, `issues/01`, `02`, `03`, `04`, `05`, `06`, `07`,
`08`, `10`, `11` and `12`, and `reports/00-orchestrator-rulings.md` (OQ1 struck through and a refinements section).
Ticket 09 needed no change. No git command was run, and nothing was staged or applied.

To fit the line limit, §1 and §2 were condensed into paragraphs, §5.3, §5.4 and §6 lost their subheadings (their
numbers stay as bold leads, so every "§6.2"-style reference still points somewhere), §8 was tightened, and the
rulings R1-R25 were reworded more briefly. No earlier ruling changed meaning except R3, R4, R8, R13 and R18, which
are listed below.

## Blockers

1. **Install order can lock sessions out of their tools (R26).**
   - Spec §5.1: every hook command is now the literal shell guard
     `sh -c 'test -f <cli.py> && ! test -e <DISABLED> && exec <python3.9> -B <cli.py> hook <event> --tool <tool> || exit 0'`,
     written out in full with absolute paths, and `-B` keeps bytecode out of A.
   - Spec §5.1 placement: DC's hook settings are staged at `F/staged/dc-claude-settings.json` and copied into W by the
     orchestrator only in wave H.
   - Spec §7: a new wave **H** holds every hook installation and runs only after wave A, after the RS tests pass from
     the installed path in both envs, and after the hook smoke test.
   - Agent brief: new constraint 9 "Never install a hook"; the "where you may write" list now excludes
     `W/.claude/settings.json`; constraint 5 names all five waves.
   - Ticket 06 rewritten: code ops are wave A and settings ops wave H; new checks that every command matches the guard,
     contains no `$`, and exits 0 with a missing CLI or the kill switch; a timed smoke file `F/tools/hook_smoke.json`.
   - Ticket 12: the merge checklist applies all RS code first, then the installed tests, then the smoke test, then
     wave H.
2. **OQ2 overrides the old R8 (R8 rewritten, R27).**
   - Spec §5.2 "Reading (Claude)" and decision 3: a stale reading is first refreshed by RS; the reading is unknown only
     if the refresh fails, and the denial names the refresh error.
   - R8 now specifies the endpoint, the 8 s bound, the status line's cache, lock (60 s sweep) and 300 s retry floor,
     a token read in-process and never printed, logged or put on a command line, and an atomic merge into
     `usage.json` that keeps every key.
   - Ticket 02: new facts (statusline line ranges and the cache body keys), a new module `oauth_refresh.py`, and seven
     mocked tests, including one proving a planted fake token never reaches any output. Brief constraint 11 forbids
     opening the credentials file.
3. **Live-session protection (R28).**
   - R28 excludes `sdr-*`, `sdr-session-wrapup`, `selective-deception` and `eval5-grader-fixes` from waves A and B, plus
     the two memory logs and `MEMORY.md` lines 27 and 29. Spec §7 adds wave **D**, gated on the user's confirmation
     that the Codex session is finished.
   - Ticket 01 rewritten: it no longer touches lines 27 and 29, the pointer notes or the memory-log copies.
   - Ticket 10 rewritten: wave B migrates only `component-analysis`, `format-control`, `mechanism-analysis`,
     `mechanism-datasets` and the `autoresearch-workflow` exception. The script refuses R28 directories unless
     `--confirmed-live-session-finished` is passed, and the hand-back gives the later one-line command. I chose a
     command over pre-staged wave D migration ops because their hashes would be stale by the time the user confirms.
   - Ticket 12 stages the deferred memory ops in `S/ops/12d-deferred-memory.json` as wave D, staged but not applied.
   - Brief constraint 10 states the rule. The 12-hour mtime skip stays.
   - My reading: I deferred `MEMORY.md` lines 27 and 29 together with the two notes, because the review asked for it
     and those lines describe the live session's work. The orchestrator ruling named only the two notes.
4. **Claim tag (R29).**
   - Spec §4.2 and §4.5 now say `<tool>-<first 8 characters of the session id>`, with `claude-b2cb53cd` for this
     session.
   - Ticket 03's validator checks that format, and ticket 05 seeds `claimed_by: "claude-b2cb53cd"` with the worktree
     and branch.
   - OQ1 in `00-orchestrator-rulings.md` is struck through and points at R29.
5. **The lint refuses before the write (R30).**
   - Spec §5.1: H-d lints Write `content` and Edit `new_string` and denies with the failing units in at most 400
     characters. H-f is now advice only and never claims to block. §5.5 says both checks run before the write.
   - Codex uses `apply_patch` in PreToolUse if ticket 06 verifies its input shape, else the gap is documented.
   - Ticket 01 requires a lint-a-string function. Ticket 02 tests the gate's Write and Edit lint. Ticket 06 asserts
     that H-f never returns a block. Ticket 11's lint drill now expects the file unchanged after the denial.
6. **autoMode extends, never replaces (R31).**
   - Spec §7: `replace_paths` is gone. `json_merge` appends a list entry only when no identical entry (equal
     canonical JSON) exists, and never removes an entry.
   - Ticket 01: the autoMode text says "appended entries", the apply-tool tests cover list extension and
     de-duplication, and the settings check says "adds three keys and appends entries to one list" and compares every
     existing entry by hash.
7. **Worklog kinds and structure (R33).**
   - New spec §4.8: the `worklog.json` schema. Everything above `## Log` is regenerated from it and from `state.json`;
     only the Log is append-only. It also fixes the time and day-heading formats.
   - Spec §5.6: kinds `finding`, `need`, `need-resolved --id N# --answer` and `incident` (P# row plus a log entry),
     with their options.
   - Spec §3 adds `worklog.json` to the layout. §5.3 makes RS the only writer of `worklog.json` and `WORKLOG.md`.
     The self-ack guard covers `worklog.json`.
   - Ticket 03 rewritten for these kinds, plus an `--import` that builds `worklog.json` from the existing
     `F/WORKLOG.md`. Ticket 08's templates include `worklog.json`. Ticket 12 lists the one-time import.
8. **Turn end at a freeze (R35).**
   - Spec §5.2 adds a protocol paragraph: finish the atomic step, write the block, send HOLD, end the turn, never
     poll. A worker on HOLD finishes its step, writes its hand-back and stops. Decision 6 now says why other tools stay
     allowed.
   - Ticket 08 requires this wording or stronger, and adds it to `ticket-implementer.md`. Brief constraint 12 tells
     implementers what to do on HOLD.
   - Ticket 11's freeze drill observes the turn end and the worker stopping.
9. **Markdown copy and the autoresearch-workflow exception (R34).**
   - R3 now defers to R34: copy every `*.md` at any depth, including `reports/`, `reviews/` and `handbacks/`, within
     200 KB per file and 1.5 MB per directory, with `provenance.json` and a report of cap exclusions.
   - `.scratch/autoresearch-workflow` is the named exception. Each stale file goes to the backup root only if F holds
     a file with the same sha256; any file without a match is kept. The symlink then points at
     `DC/docs/research/autoresearch-workflow` (spec §3 layout, ticket 10).

## Additional rulings

- **R4 and R32 (Codex placement and freeze scope).**
  - R4 now says Codex also loads `<repo>/.codex/hooks.json` when the project layer is trusted. Ticket 06 verifies
    whether that layer loads for A and for DC.
  - Hooks stay in the user-level file for now.
  - R32: a Codex freeze denies spawns and `sbatch` only, because Codex documents no message tool. This is reflected
    in §5.2 step 5, ticket 06 and ticket 08's Codex section.
- **R36 (envelope rejection).** H-g never acks a prompt that starts with `<` or contains a teammate, agent,
  cross-session or task-notification envelope. Ticket 06 has fixtures for each and records whether the payload has a
  source field. Ticket 11's freeze drill sends "continue" from a teammate and from another session and expects no
  ack.
- **R38 (ticket 11 ordering).** Ticket 11 is now blocked by 10 as well. R18 now states that the staged `cli.py` is
  extended by tickets 01, 02, 03, 06 and 11 in sequence.

I also applied these non-blocking review items:
- **Guard scope (R37).** The self-ack guard exempts `_templates/`, and read-only RS subcommands may name a direction
  `state.json`.
- **Ticket 01 sizing (R20).** Ticket 01 hands back after the lint and the apply tool if it projects past 250k tokens.
- **Ticket 08.** The `ticket-implementer.md` write now needs `expect_sha256`.
- **Ticket 12.** The Alignment commit that deletes the deduplicated `project_context` files is a user-approved step.
- **Ticket 07.** It now uses `deniedMcpServers` before falling back to `permissions.deny`.
- **Ticket 04.** It names the third `judge_spec()` call site, `evaluate_circuit.py:916`, and notes which provenance
  field names are new rather than reused.
- **H-j.** It names `background_tasks` and `session_crons`.
- **Ticket 11.** The pilot times one gate call on Lustre.

## Addendum: unregistered sessions (orchestrator ruling after the fix pass)

The orchestrator ruled that only sessions that ran `register` get the checkpoint freeze. Every other session gets
only the cap pause and the stale-reading denial. Edits:

- **spec R5.** Rewritten: a cwd match against `directions.json` is attribution only; only a registered session gets
  the FREEZE; the reason (hooks fire in every A or DC session) is stated.
- **spec §5.2.** New step 4, "Unregistered session": allow, skipping the two freeze steps. The freeze steps and the
  final allow are renumbered 5, 6 and 7. The crossing formula now reads `session_points − points_at_register ≥ N ×
  cadence` in a registered session, so registering late never freezes at once.
- **spec §4.5.** The session file gains `registered_at` and `points_at_register`.
- **spec length.** R8 and §5.2 steps 3 and 6 were tightened to stay at 518 lines; the cache and lock paths remain in
  ticket 02.
- **Ticket 02.** The gate implements steps 1-7. The per-row gate tests add the unregistered row. A new criterion
  lists five unregistered fixtures: points past the cadence still allowed; cap pause still denies; stale reading
  still denies; a cwd match without `register` still unregistered; late `register` counts from
  `points_at_register`. It also states that the self-ack guard and the Write/Edit lint apply in every session.
- **Ticket 06.** H-a in an unregistered session prints the `register` command and the reduced gate scope.
- **Ticket 08.** The research-session doc says a research session must register before its first spawn.

My own call beyond the ruling: the self-ack guard and the lint keep applying to unregistered sessions, because they
run before step 4 and protect files rather than pace work. The orchestrator can narrow that if it meant otherwise.

## Not addressed, for the orchestrator

- The worklog `--import` relies on the hand-written `F/WORKLOG.md` keeping the lane 4 format until ticket 03 lands.
