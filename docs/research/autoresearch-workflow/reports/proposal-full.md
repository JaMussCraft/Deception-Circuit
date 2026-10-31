# Autoresearch workflow: review findings and setup plan (full version for agents)

Date: 2026-10-31. Status: PROPOSAL v2 after user review (same day). Nothing below has been built.
User decisions recorded: D1 = move to Deception-Circuit docs (repo stays public); D2 = FREEZE; superpowers kept in all
profiles; science guards run during setup; GitHub token already rotated.
Source reports (same directory): lane1-public-patterns.md, lane2-harness.md, lane3-repo-structure.md, lane4-oversight.md.
The user's workflow description is in the originating prompt; this document assumes it as the baseline and only lists changes.

## 0. Verdict on the workflow as described

The two-tier design (synthesis session proposes mid-level directions; research sessions execute them with a Fable
orchestrator and Opus/Sol workers) matches the strongest public evidence (Anthropic's automated weak-to-strong
researcher: distinct, deliberately ambiguous directions per agent beat identical prompts, rigid pipelines, and
pre-generated idea pools). Keep it. The repo is already ahead of public systems on pre-registration (spec rulings,
phase gates), GPU ledgers and independent review. The gaps are uniformity and enforcement:

1. Nothing indexes findings or directions, so a synthesis agent needs 60-80k tokens to orient and still misses things.
2. Checkpoints, compaction counts and model choice are enforced by the orchestrator remembering, not by the harness.
3. Model defaults are not pinned: Claude subagents inherit Fable when `model` is omitted (caught twice). Codex agent
   TOMLs inherit the parent, but spawns have named Sol explicitly (215 of 253 sub-agents ran Sol; 38 ran Astra by
   choice for review/adjudication). A default in both tools is a safety net, not a fix for an active failure.
4. State files degrade (whitespace-stripped prose) through model self-conditioning; the glue has leaked into MEMORY.md.
5. Results lack provenance (13 of 2,683 analysis JSONs name a commit) and verdicts are not gated on execution evidence,
   seed replication or frozen graders.

## 1. Decisions proposed (the user approves or edits these)

D1. Canonical home for research state = `Deception-Circuit/docs/research/` (tracked, one commit per milestone, next to
    code and outputs). `.scratch/<slug>` in Alignment becomes a symlink (precedent: selective-deception). Old
    directories migrate text-only, lazily, by an Opus agent; bulk stays in `outputs/_studies/` (ignored).
    Caveat: this pushes specs/worklogs to the Deception-Circuit GitHub remote. Confirm the repo is private.
    Alternative (if the user prefers no move): git-add only spec/RESUME/WORKLOG/ledger under `.scratch/` in Alignment.
D2. Checkpoint = FREEZE (user decision). When a checkpoint fires the orchestrator finishes the atomic step in flight,
    writes the checkpoint block, tells workers to hold at a clean point, and ends its turn. A PreToolUse hook then denies
    Agent spawns, SendMessage to workers and `sbatch` until the user acknowledges, so weekly usage stops rising. Running
    Slurm jobs may finish; their completion is logged on resume. Acknowledgement is a human signal only: a
    UserPromptSubmit hook records the ack when the user's message starts with "continue" (or the user runs
    `! usage-ack`); questions from the user during the freeze are answered without lifting it. Cap pauses (80%) use the
    same deny path but lift automatically at the window reset.
D3. Three separate alarms: review checkpoint (16/25 weekly points, per session), cap pause (80% five-hour or 80% weekly,
    hard hold, re-arm at reset), stall alarm (60 min with no progress event while waiting on compute: switch direction).
    Plus a milestone trigger: a pre-registered gate passing/failing writes an entry and, if it changes the plan, a checkpoint.
D4. Human worklog and machine state are separate files, different writers' discipline: WORKLOG.md (orchestrator only,
    append-only body, rewritten header, plain language) vs RESUME.md (≤150 lines, fixed headings, overwritten) and
    state.json / ledger.json (counters, usage segments, reservations). Every write to these paths is linted.
D5. Paper-gating rules (science rigor): a finding is `verified` only with an evidence path whose manifest names the
    commit; headline claims require seed replication; judge/grader code is frozen and hashed into manifests; a held-out
    instance set is never scored before a paper-gating run; reviewer agents get code+logs+manifests, not the report;
    a script checks every number in a report resolves to a file value.
D6. Lean profiles for BOTH tools. Keep everywhere: superpowers (user), mattpocock-skills (tdd 26 uses, code-review 14),
    code-review plugin (Codex `$claude-pr-review`), github MCP (50 uses), claude-md-management, nnsight (research only).
    Disable by default in both tools, re-enabled only in a `writing` profile: academic-research-skills (ARS: 30 skills,
    a PreToolUse guard on every Write/Edit/Bash, 0 uses), academic-writing-agents (0 uses).
    Disable by default everywhere (0 recorded uses in either tool): context7 MCP, jcodemunch MCP, shinka-* and weco
    user skills (keep installed; enable only for an explicit evolution task), karpathy-guidelines, skill-creator,
    claude-code-setup, cc-plugin-you-should-know. Add session-report (audit profile).
    Mechanism: Claude `claude --settings ~/.claude/profiles/{research,synthesis,writing,audit}.json`; Codex
    `codex --profile <name>` with per-profile skill/MCP enablement (exact Codex keys to be verified during setup; the
    bridge already supports project-level disables). Usage counts from ~/.claude/projects and ~/.codex/sessions.
D7. Usage targets per the user's new message: ≤80% five-hour, ≤80% weekly (both all-models and Fable row), ≤80% Codex
    weekly. Memory note usage-limit-policy (75%) is superseded and will be updated.
D8. Keep Fable and all-models weekly usage close: the gate reports both rows at every checkpoint and hand-back; when the
    Fable row exceeds the all-models row by more than 5 points, the orchestrator must delegate reading/analysis/review
    to Opus agents rather than do it itself, and the worklog header shows both rows. Checkpoint increments are
    measured on max(all-models, Fable), session-relative (see H4).

## 2. Target layout

```
Deception-Circuit/docs/research/
  INDEX.md              how to read this tree; links below; ≤1 page
  FINDINGS.md           one row per claim: id | date | direction | claim | status | commit | evidence | report
                        status ∈ {proposed, executed, reviewed, replicated/verified, refuted, superseded, paused}
  directions.json       registry: id, title, status {proposed, open, claimed, active, paused, done, abandoned},
                        claimed_by (tool-session tag), claimed_at, branch, worktree, spec, resume, worklog, ledger,
                        parent_findings, do_not_touch; rendered to DIRECTIONS.md
  SESSIONS.md           one row per live/paused session: directions claimed, state, last entry, worklog path
                        (rendered from directions.json claims; synthesis reads first)
  ledger.json           global roll-up of GPU-h / API spend across directions (one schema)
  _templates/           START.md, WORKLOG.md, RESUME.md, state.json, ledger.json, handback.md, proposal.md, audit.md
  <slug>/               one per direction
    README.md           handoff (question, verdict, pointers), ≤2 pages
    START.md            the starting prompt the session was launched with
    spec.md             frozen design, pre-registered rules
    WORKLOG.md          human log (template in lane4 report §1)
    RESUME.md           machine narrative state
    state.json          compactions, checkpoint segments, acked_bucket, active jobs + waiter commands
    ledger.json         reservations (job_id, cluster, reserved/actual, source_commit, manifest_hash)
    reports/ reviews/ handbacks/ history/ issues/
Deception-Circuit/outputs/<run>/manifest.json   written by run_io.make_run_dir and evaluate_circuit.py
Alignment/.scratch/<slug> -> symlink into the above
Alignment/.claude/CLAUDE.md   trimmed; points at INDEX.md; Deception-Circuit section added
Alignment/docs/agents/research-session.md, synthesis-session.md, session-audit.md   protocols
```

## 3. Harness changes
Placement: new hooks go in BOTH `Alignment/.claude/settings.json` and `Deception-Circuit/.claude/settings.json` (project
settings are read from the session's starting directory and repo root), so they never fire in the user's other
repositories. Only H1 env, H6, H7 and H8 are user-level. Scripts also no-op when cwd is outside these two trees.
Codex mirrors via ~/.codex/hooks.json entries (one-time /hooks trust) and AGENTS.md text.

H1. `env.CLAUDE_CODE_SUBAGENT_MODEL = "opus"`; add `model: opus` to idea-critic/paper-reader/paper-searcher frontmatter.
    Codex: `[agents] default_subagent_model = "gpt-6.1-sol"` in ~/.codex/config.toml (bridge generator may also emit model=).
H2. SessionStart(matcher compact) hook: increment `compactions` in the session's state.json, inject pointer to
    RESUME/WORKLOG header + lint result + "write a 'Resumed after compaction #N' entry; do not restart finished work".
    PostCompact: append compact_summary to handbacks/compaction-N.md (Claude only). Never block auto PreCompact.
H3. SubagentStop hook: write `last_assistant_message` to `<slug>/handbacks/<agent_type>-<agent_id>.md`; block once
    (guarded by stop_hook_active) if the agent's required handback file is missing. Codex: must print JSON.
H4. PreToolUse(Agent|Bash) usage gate: read usage.json (Claude) / codex-usage (Codex). Increments are SESSION-RELATIVE:
    state.json keeps per-weekly-window segments {resets_at, baseline, last}; session_points = Σ(last − baseline);
    checkpoint N fires when session_points ≥ N × cadence (16 Claude / 25 Codex, per-session override). Deny per D2 (a)
    or (b) until `usage-ack N`; deny spawns and `sbatch` outright when a cap (80%) is hit or the reading is stale
    (>10-15 min); never deny SendMessage.
    `usage-ack` CLI sets acked_bucket. PostToolUse(Agent) injects the current reading as additionalContext.
    Stop hook: additionalContext reminder only, silent while background tasks exist.
H5. PostToolUse(Write|Edit) lint on WORKLOG/RESUME/memory paths: fail a paragraph with >15% tokens ≥20 chars or >3
    letter-digit joins; feed back as additionalContext. Codex: AGENTS.md rule "run worklog-lint after every write".
H6. `statusLine.refreshInterval: 60` (keeps usage.json fresh while idling on agents); `cleanupPeriodDays: 365`.
H7. Add `session-report@claude-plugins-official`; use `/insights` and superpowers:diagnosing-superpowers for audits.
H8. Fix user-level `autoMode.environment` (describes the SHIFT_RT repo) to cover Alignment + Deception-Circuit.
H9. Slurm waits: `sbatch --wait` or an `until sacct` loop via Bash run_in_background with explicit timeout; record
    job IDs + waiter command in state.json because waiters are not restored on resume.
Codex hooks need one-time `/hooks` trust per edited hook; SessionStart(compact) injection is documented for root only.

## 4. Session protocols (docs/agents/*.md + _templates)

Research session: start from START.md; register claim in directions.json (commit on main, then branch/worktree, one
pinned worktree, orchestrator-only git); read FINDINGS/SESSIONS; ≥2 directions, each with a fallback; triggers for
worklog entries (hand-back, job terminal, checkpoint, compaction, user decision, incident, direction switch); checkpoint
protocol D2/D3; hand-back template with execution-evidence block (job id, exit code, row counts, baseline-reproduces
assertion) before any confirmed/refuted wording; ask-before list (merge, EVAL 5-class spend, dropping a direction, cap
raise); wrap-up = README handoff + FINDINGS rows + directions.json status + SESSIONS row + memory pointer.
Synthesis session: read INDEX → FINDINGS → SESSIONS/directions → recent WORKLOG headers; re-survey only where FINDINGS
has gaps; Fable advisor review when unsure; output = one-screen proposal (template, lane4 §4) + START.md per session;
proposes only unclaimed directions or explicitly hands over a paused one.
Audit session: 11-check rubric (lane4 §3): compaction count vs transcript, amnesia, repeated errors, instructions
obeyed, hand-backs closed, claims have evidence, budget truthful, criteria not moved after results, no silent stalls,
history intact, text not degraded. Verdict: trust / trust with caveats / do not trust until fixed.

## 5. Hygiene items (do regardless)

- GitHub PAT: rotated by the user 2026-10-31. Setup verifies no token remains in settings or remote URLs, and the
  worklog/RESUME lint also scans for secret-shaped strings since docs/research is pushed to a public repo.
- De-glue text: MEMORY.md lines for selective-deception and SDR, selective-deception-execution.md,
  sdr-mechanism-review.md (≈600 joins), sdr-clause-choice/RESUME.md. Shrink the two 45-72 KB memory logs to pointers.
- Update memory: usage-limit-policy (80%), subagent-model-policy (defaults as safety nets; Astra claim corrected 2026-10-31).
- Label project_context/prompts/ historical; `autoresearch.md` still says Sonnet subagents.
- Delete fully merged `mechanism-datasets` worktree/branch (local + origin). Dedupe 21 byte-identical reports in
  project_context/ (pointers to docs/research copies).
- Open test: does modelSettings.claude-opus-5-5.autoCompactWindow=600000 reach subagents? Run one long Opus subagent
  and read compact_boundary.preTokens. Until then size briefs <350k.

## 6. Setup plan (phases; each phase = Opus agents implement, one fresh Opus reviewer, orchestrator commits)

P0 Hygiene + config (≈1 h agent time, no GPU): §5 items except migration; H1, H6, H7, H8; Codex [agents] default.
P1 Index + layout: INDEX/FINDINGS/directions.json/SESSIONS/ledger schema/_templates; seed FINDINGS from the three
   existing handoffs + mechanism-analysis synthesis; standardize the 3 live/paused direction dirs; symlink .scratch.
   Trim CLAUDE.md. (D1 migration of the other ~13 closed .scratch dirs as a follow-up ticket.)
P2 Hooks + CLI: a small Python package `.agents/research_session/` (init, usage-check, usage-ack, worklog-append,
   lint, state) with unit tests on both interpreters; hook entries in ~/.claude/settings.json; Codex hooks.json + AGENTS.md
   text; trust step for the user.
P3 Protocol docs + templates + plugin profiles for both tools (docs/agents/research-session.md, synthesis-session.md,
   session-audit.md; ~/.claude/profiles/{research,synthesis,writing,audit}.json; Codex profiles in ~/.codex/config.toml).
P4 Science guards in Deception-Circuit code (user: run during setup): manifest.json from run_io/evaluate_circuit;
   number-resolution checker; grader freeze hash; held-out set policy doc; hand-back template.
P5 Pilot: one short Claude research session on a trivial direction to exercise hooks, compaction counter, checkpoint
   gate, Opus 600k test; then the first real synthesis session.
Estimated: P0-P3 in one orchestrated Claude session (several Opus agents, no GPU); P4 ≈ half a session; P5 ≈ 2-3 h.
