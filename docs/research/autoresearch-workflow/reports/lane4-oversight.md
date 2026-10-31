# Lane 4: Low-touch human oversight

Scope: worklog format, checkpoint protocol, session-reliability audit, synthesis hand-off, checkpoint cadence.

## 0. Why the Codex RESUME became unreadable

`.scratch/sdr-clause-choice/RESUME.md` decays inside one session. Paragraphs 0-3 are clean, with 0-5% of tokens being 20+ characters long. Paragraphs 5-16 sit at 53-100%. The two final paragraphs, written after a compaction and from user dictation, are clean again. Clean files in the repo sit at 2-6%.

The Codex rollout logs show the glued text is already in the model's own `exec` write payload. The file content the model read back before each append was also glued. So the write path is not mangling anything. The worker reads its own compressed prose and writes in the same style each time, and the effect compounds. This matches the self-conditioning failure in Sinha et al. (ICLR 2026), where models err more once their context holds their own earlier errors.

The same pattern has already leaked into durable memory. `.agents/memory/sdr-mechanism-review.md` has about 600 letter-digit joins, and the MEMORY.md index lines for selective-deception and SDR are glued too.

Prevention follows from the cause:
1. **Separate readers.** The human worklog never doubles as the machine state file, so its writer never re-reads dense state while writing prose.
2. **Append through a structured writer.** The orchestrator passes fields such as title, what, why and next to a small script that renders the entry. It does not freehand-edit the file after reading it in full.
3. **Lint every write.** Reject any paragraph where more than 15% of tokens are 20+ characters, or with more than 3 letter-digit joins of the `word8` kind. Run this on WORKLOG.md, RESUME.md and every `.agents/memory/*.md`. On Claude, use a PostToolUse hook on Write and Edit. On Codex, which has no confirmed hook surface, `AGENTS.md` must say "run `worklog-lint <file>` after every write", and the orchestrator re-runs the lint at each checkpoint.
4. **Reset on drift.** After two lint failures, regenerate only the failing entry from its fields.

## 1. The worklog

### Decisions
- **One file per session** at `.scratch/<session-slug>/WORKLOG.md`. It sits beside `RESUME.md` (machine state), `session-state.json` (checkpoint and usage numbers) and `compaction-ledger.json`.
- **The orchestrator is the only writer.** Subagents write hand-back reports. The orchestrator translates them into one plain-language entry. This gives one voice and no concurrent edits.
- **The body is append-only and the header is rewritten.** Days run oldest to newest. The header's "Right now" block is rewritten at every trigger, so the user never scrolls to learn the current state.
- **Triggers.** Write an entry on: a subagent hand-back, a job reaching a terminal state, a checkpoint, a compaction (the first action after resuming), a user decision or answer, a process incident, and a direction being blocked or switched. Do not write an entry on: polling, a routine submission (fold it into the completion entry), or a review round that changed nothing.
- **One-way references.** The worklog may point to RESUME, reports and figures, but only in the Evidence column of the Findings register. RESUME never summarizes the worklog.
- **Timezone.** Times are 12-hour with a zone suffix. US Central time leaves daylight saving on 1 Nov 2026, so the suffix flips from CDT to CST. Use `TZ=America/Chicago date '+%-I:%M %p %Z'` and never type the zone by hand.

### Legibility rules
1. **Define any code name on first use.** Code names include ticket numbers, ruling IDs such as R29, set names such as U5 or C6, and condition letters. Add each to the header's "Terms" list, capped at 10 terms. If more are needed, the entry is too low-level.
2. **No hashes, job IDs, file:line references, flags or paths in entries.** Paths appear only as evidence links in the registers.
3. **Each entry gets at most 5 lines and about 80 words.** Each sentence has a verb. Write counts with denominators, as in "23 of 48 pairs".
4. **Say what a result means, not only what it is.** Every finding states the question it answers.
5. **Process incidents are about the agents, not the science.** "The worker hit the spend limit and lost its place" is an incident. "The gate failed" is a finding.
6. **Strikethrough marks only resolved needs.** Never delete history. Corrections go in a new entry that names the entry it corrects.

### Template

```markdown
# Worklog: <plain session title>

<!-- HEADER: rewritten at every trigger; body below is append-only -->
| | |
|---|---|
| State | Running / At checkpoint 3, waiting for your review / Paused for usage cap until Wed 4 Nov 7:00 am CST / Blocked: needs you / Closed |
| Directions | 1. <plain name>: active · 2. <plain name>: waiting on GPU queue · 3. <plain name>: parked |
| Started / last updated | Sat 31 Oct 2026, 9:05 am CDT / Sun 1 Nov 2026, 2:40 pm CST |
| Orchestrator auto-compactions | 2 (ledger-confirmed) |
| Weekly usage (this session) | +23 points since start (account reads 37%); next checkpoint at +32; cap pause at 75% |
| Human review checkpoints | 1 of 1 acknowledged (cadence: every 16 weekly points) |
| GPU budget | 6.5 of 20 GPU-h actual (9.0 reserved); clusters: Delta, Bridges-2 |
| OpenRouter credit | $1.84 of $10 cap |
| Open needs from you | 1 (see below) |
| Transcripts (for audits) | Claude session <id>; Codex rollout <file> |

**Right now (≤3 lines).** <What is running, what finishes next, what the session will do if you say nothing.>

**Terms.** *Pressure clause*: the sentence in the prompt that pushes the model to deceive. *U5*: five shared attention heads in layers 12-14 that every deceptive circuit uses.

## Needs from you
- N1 (Sat 9:40 am): May I spend 4 more GPU-h on Bridges-2 for the seed check? Default if no answer: skip it and report without seeds.
- ~~N0 (Sat 9:10 am): Approve the plan.~~ Answered Sat 9:30 am: approved, with "drop the MLP grid".

## Findings register
| # | When | Finding, in plain words | Setup needed to read it | Strength | Evidence |
|---|---|---|---|---|---|
| F1 | Sat 4:10 pm | Swapping five shared heads to their no-pressure values flips the model from hiding to disclosing in 23 of 48 stories. | The model is told to hide a damaging fact. "Swapping" means running the pressured prompt with those heads' outputs taken from the unpressured version. | reviewed | `reports/05-analysis.md` §2 |

Strength is one of: preliminary, reviewed by an independent agent, or final.

## Process incidents
| # | When | What went wrong (agent workflow) | Effect | Fix or status |
|---|---|---|---|---|
| P1 | Sat 5:02 pm | Three workers stopped on the monthly spend limit mid-task. | 15 min lost, no work lost | Resumed by name from their hand-back reports |

## Log
### Saturday 31 October 2026
**9:05 am CDT · Session started.** Goal: <one sentence>. Two directions opened, a third parked as a fallback.
**4:10 pm CDT · Hand-back: composition test finished.** Swapping the five shared heads mostly removes the hiding behavior (F1). This supports the shared-route story but does not show the heads are deception-specific. Next: test which downstream heads read this signal.
**6:30 pm CDT · CHECKPOINT 1 (+16 weekly points).** See the block below.
```

The checkpoint block is one entry with a fixed shape, so the user can find every checkpoint by searching for "CHECKPOINT":

```markdown
**6:30 pm CDT · CHECKPOINT 1 (+16 weekly points; account 30%; resets Wed 4 Nov 7:00 am CST).**
- Since last checkpoint: <2-3 sentences of progress, pointing to new findings F#>.
- Spend: GPU 6.5 h actual of 20; OpenRouter $1.84 of $10; compactions 1.
- Process health: <"no incidents" or P# list>.
- Plan to the next checkpoint: <2 sentences per active direction>.
- Held until you reply: <new spend, new direction, merge, or "nothing">. Continuing meanwhile: <authorized work>.
```

### Prior art used
- Anthropic's long-running-harness guidance keeps a `claude-progress.txt` log plus git history and a JSON feature list that agents may only flip pass/fail. The JSON was chosen because models are "less likely to inappropriately change or overwrite JSON". That motivates keeping counters and checkpoint state in `session-state.json` and the ledger, with Markdown only for prose.
- Nygard-style decision records contribute the rule that history is superseded, never edited.
- The repo's own `reports/00-plan-draft.md` is the best local model. Its "Decisions I made for you (say if you object)" list is what the "Needs from you" register with defaults generalizes.

### Is the SDR findings report legible to a busy PI?
Not as written. The bolded first sentence depends on "five earlier shared heads", "layer 17 interfaces", "query" and "key" before any of them is defined. U5 is defined two paragraphs later.

The fix is a three-line head: the question asked, the answer in one sentence, and what it changes for the project. Define terms on first use. Put the table below the prose, with one sentence per row on how to read it.

## 2. Checkpoint protocol

### Three events, kept apart
| Event | Trigger | Effect |
|---|---|---|
| Review checkpoint | Session weekly increment crosses the next multiple of the cadence (16 points on Claude, 25 on Codex, set per session) | Post the block, keep doing authorized work, hold new commitments |
| Cap pause | Account at ≥80% of the 5-hour window, or ≥75% weekly | Hard hold. Workers stop at a clean point. Arm a wake-up at the reset |
| Stall alarm | No progress event for 60 min while something is waiting on compute | Switch to another direction. If none is unblocked, log an incident and tell the user |

### Computing the increment (Claude)
Keep the baseline in `session-state.json`, never in the model's memory:

```json
{"metric": "weekly = max(seven_day, Fable model_scoped)",
 "cadence_points": 16, "next_checkpoint": 2, "acknowledged_through": 1,
 "segments": [{"resets_at": 1793797200, "baseline": 14, "last": 30}],
 "session_points": 16}
```

At every trigger and before every spawn, read `/u/swong2/.claude/usage.json`:
1. **Staleness.** If `timestamp` or `model_scoped_fetched_at` is more than 15 min old, treat the reading as unknown. Unknown means: no new spawns or GPU submissions, keep going on running work, and re-read later. The status line refreshes this file, and background or Codex-driven sessions may not run it. The clause-choice session quoted one 26 Oct 8:10 am reading for hours.
2. **Weekly reading.** `w = max(seven_day.used_percentage, Fable row.used_percentage)`. A missing key reads as 0, per the existing policy.
3. **Window rollover.** If `resets_at` differs from the current segment's value, or `w` falls below the segment's `last`, close the segment at its `last` value. Open a new segment with `baseline = w`. Write a short "Weekly window reset" entry.
4. **Session points.** `session_points = Σ(segment.last − segment.baseline)`. Checkpoint numbers only increase.
5. **Checkpoint test.** Fire when `session_points ≥ cadence × next_checkpoint`. The cap test uses the raw `w` and five-hour readings, not session points.

For Codex, run `codex-usage --pause-at <cap>`. Use `weekly.used_percent` with the same segment logic, keyed on the reset time. Require valid JSON and exit 0 before spawning.

**Shared-meter caveat.** Both meters are account-wide. With two concurrent sessions, each sees the other's burn and checkpoints twice as often. Each session lists its concurrent sessions, taken from the sessions registry in section 4, in its checkpoint block. For per-session attribution, the Claude JSONL `modelUsage` and `cost-state` records give an estimate.

### What happens at a checkpoint
1. Finish the atomic step in flight. Never cancel a running job to checkpoint.
2. **Verify state before writing.** RESUME is current. The ledger count equals the number of compaction-summary messages in this session's transcript. Work is committed. The job list in RESUME matches `squeue` and `sacct`. Budgets are recomputed from `sacct` and the OpenRouter key-usage endpoint, not from memory.
3. Write the checkpoint block and rewrite the header. Set the state to "At checkpoint N, waiting for your review". Increment `next_checkpoint` in `session-state.json`.
4. Post a short message, at most 8 lines. It is the checkpoint block plus the open needs.
5. **Continue on green work only.** Green work is anything inside already-authorized directions: CPU analysis, reviews, writing, and jobs already queued. Amber work waits for acknowledgment: new GPU reservations above a per-session threshold, a new direction, merges, and new paid fleets. A checkpoint gates new commitments. It is not a stop.
6. When green work runs out, end the turn with the message. Do not poll for the reply. A background job resumes when the user replies.
7. The user acknowledges by replying, or by striking the checkpoint's "Held until you reply" line. Record `acknowledged_through = N`.

**Surviving compaction.** Every counter lives in files: checkpoint number, baseline, acknowledgments, compactions. Three hooks keep them in sync. I confirmed the events and which ones inject context, but not their full input schemas:
- A `PostCompact` hook appends to the ledger. It cannot inject context.
- A `SessionStart` hook with matcher `compact` injects an instruction. The instruction says: "Read the WORKLOG header, RESUME and session-state.json. Then write a 'Resumed after compaction #N' entry. Do not restart any work marked done."
- A `SubagentStop` hook injects "log this hand-back in the worklog".

Codex has no equivalent hooks that I could confirm, so its starting prompt carries the same instructions as text.

## 3. Session-reliability audit

**Principle.** The worklog, RESUME, ledger and hand-back reports are claims. Transcripts, git history, `sacct` and output files are evidence. Every check compares the two. METR found spoofed tool calls in agent logs, so agent-writable logs are never evidence.

**Inputs.**
- WORKLOG, RESUME, `session-state.json` and the ledger.
- `git log --stat` over the session window.
- `sacct` for the session's jobs.
- The main transcript `~/.claude/projects/<slug>/<session>.jsonl` and its `subagents/*.jsonl` and `*.meta.json`. For Codex, the rollouts under `~/.codex/sessions/YYYY/MM/DD/`.

Usable transcript fields, seen in a local sample:
- `isCompactSummary` and `compactMetadata` mark compactions.
- `tool_result.is_error` and `toolDenialKind` mark errors and permission denials.
- `system` messages with subtype `away_summary` mark gaps.
- `cost-state` and `modelUsage` carry spend.
- Timestamps are on every record.

### Rubric
Grade each check Green, Amber or Red, and cite a transcript timestamp or file for every Amber or Red.

| # | Check | How |
|---|---|---|
| 1 | **Compaction count honest** | Count `isCompactSummary` in the main transcript and compare with the ledger and the worklog header. A mismatch is Red. |
| 2 | **No compaction amnesia** | For each compaction, read the summary and the next ~30 turns. Flag decisions contradicted, finished work redone (re-spawned tickets, resubmitted jobs) and lost constraints (a cap or "ask before merge" rule no longer obeyed). |
| 3 | **Repeated tool errors** | Group `is_error` results by normalized command. Flag 3 or more consecutive identical failures, or a total over 20. Note whether a fix followed. |
| 4 | **Instructions obeyed** | List the standing rules from the starting prompt, CLAUDE.md and memory (ask before merge or EVAL 5, subagent model, caps, worker git ban, Slurm `--time`). Grep the tool calls for violations. A permission denial followed by an equivalent retry by another route is Red. |
| 5 | **Hand-backs closed** | Every spawned subagent has a hand-back report and a worklog entry. Any agent that ended in error, such as on the 25 Oct spend limit, was resumed or re-spawned, not silently dropped. |
| 6 | **Claims have evidence** | Every finding's evidence path exists and was modified after the producing job ended. Spot-check 3 numbers against the source file. Findings in the final report that are missing from the register are Amber. |
| 7 | **Budget truthful** | Reserved and actual GPU-h from `sacct` match RESUME and the header within 5%. The OpenRouter spend matches. No usage reading at or above a cap shows continued spawning. |
| 8 | **No criteria moved after results** | In git history, find every commit that touches pre-registered criteria, thresholds, filters or rubrics. Each must predate the first appearance of the result files it governs. Count analyses run against analyses reported. A post-hoc "rescue" analysis must be labelled exploratory. The repo's dated, numbered rulings make this checkable: compare ruling time with result-arrival time. |
| 9 | **No silent stalls** | Find gaps over 60 min with jobs pending and no other direction active. Check each against the stall-alarm entries. |
| 10 | **History intact** | `git diff` of WORKLOG and RESUME shows only appends in the body. Deleted or rewritten past entries are Red. |
| 11 | **Text did not degrade** | Run the lint from section 0 over every file the session wrote, including memory. |

**Verdict** is one of three:
- *Trust outputs.* Everything is Green.
- *Trust with listed caveats.* No Red on checks 1, 6, 7, 8 or 10.
- *Do not trust until fixed.* Any Red on those five.

The auditor writes 10 lines or fewer, then the table. It starts from a fresh context and never reads the session's own final report before checking the evidence.

**Prior art.**
- MAST (Cemri et al., 2025) groups multi-agent failures into system design, inter-agent misalignment and task verification. Checks 3-4, 5 and 6-8 map onto those groups. Its LLM annotator reached κ = 0.77 against experts, so Red items need a human spot-check.
- Agent-as-a-Judge (Zhuge et al., ICML 2025) works best when the judge gets an explicit requirements list. The starting prompt's exit criteria and standing rules serve as that list.
- Inspect Scout and Docent run rubric scanners over many transcripts. One fresh agent suffices for a single session.

## 4. Synthesis hand-off

### Sessions registry: `.scratch/SESSIONS.md`
One row per live or paused session. Each session's orchestrator updates its own row at every checkpoint. A synthesis session must read the registry first and may propose only unclaimed directions, or explicitly hand over a paused one.

```markdown
| Session | Directions claimed (plain words) | State | Last worklog entry | Worklog | Do not touch |
|---|---|---|---|---|---|
| sdr-composition-2 | How shared heads in the SDR task combine to produce hiding | Running, checkpoint 2 | Sun 1 Nov 2:40 pm CST | .scratch/sdr-composition-2/WORKLOG.md | SDR v2 circuit outputs |
```

### Concise proposal for the user, one screen

```markdown
# Proposed next sessions (<date>)
Checked against: SESSIONS.md as of <time>; no overlap with <sessions>.

## 1. <Plain direction name>
**What.** <1-2 sentences.>
**Why it is worth it.** <2-3 sentences: the gap, what we already have, what result would change the plan.>
**Cost and risk.** ~<GPU-h>, ~<weekly points>; main risk: <one clause>.

## Not proposed, and why
- <Direction>: already claimed by <session> / closed with a failed gate on <date>.

Your call: approve all / approve 1 and 3 / edit.
```

### Per-session starting prompt: `.scratch/<slug>/START.md`

```markdown
# Starting prompt: <session slug>
- **Goal (1 sentence)** and **mid-level directions (2-4)**, each with a fallback when blocked.
- **Why promising**: 2-3 sentences.
- **What exists**: paths to prior findings, code and data; branch or worktree to start from.
- **Do not redo**: closed protocols, failed gates, explored null results (each with a path).
- **Do not touch**: directions and files claimed by other sessions (from SESSIONS.md).
- **Budgets**: GPU-h cap per cluster, OpenRouter $ cap, weekly-usage cap; reserve-vs-actual rule.
- **Oversight**: checkpoint cadence (default 16 weekly points on Claude, 25 on Codex); what counts as amber work; stall alarm at 60 min.
- **Always ask before**: merge to main, EVAL 5, dropping a direction, any cap raise.
- **Exit criteria**: what "done" or "stop" looks like for each direction, including the pre-registered pass/fail rule.
- **Files**: WORKLOG.md (human, orchestrator-only), RESUME.md (machine), session-state.json, compaction-ledger.json; register in SESSIONS.md on start.
- **Models**: orchestrator <model>; subagents <model> (pass it explicitly on every spawn).
```

The full agent version keeps the same numbering and adds evidence and cost tables, so the two versions cannot drift apart.

## 5. Are the 16% and 25% cadences sensible?

Keep the usage-based cadence. Checkpoints then scale with work done rather than wall-clock time. I cannot derive the burn rate on the current plan. The only measurement, about 5 weekly points per 25 min for two Opus agents, predates the Max 20x upgrade.

Under the 75% weekly cap and a typical starting reading of 10-20%:
- **Claude at 16 points** allows 3-4 checkpoints per weekly window.
- **Codex at 25 points** allows 2-3.

Both are reasonable. Three adjustments:
1. **Account for concurrency.** Two sessions sharing the meter each checkpoint twice as often.
2. **Add the stall alarm as a floor**, and add a milestone trigger. Any direction finishing or failing its pre-registered gate gets a worklog entry and, if it changes the plan, a checkpoint even before the usage threshold.
3. **Calibrate with data.** Log the weekly reading at every hand-back for one full session. Then set the cadence so checkpoints land roughly 6-12 working hours apart.

## Sources
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
- [Cemri et al., Why Do Multi-Agent LLM Systems Fail? (MAST)](https://arxiv.org/abs/2503.13657)
- [Zhuge et al., Agent-as-a-Judge](https://huggingface.co/papers/2410.10934)
- [Sinha et al., The Illusion of Diminishing Returns (self-conditioning)](https://arxiv.org/abs/2509.09677)
- [METR, MALT dataset of natural and prompted behaviors](https://metr.org/blog/2025-10-14-malt-dataset-of-natural-and-prompted-behaviors/)
- [Transluce, Introducing Docent](https://transluce.org/introducing-docent)
- [Inspect Scout](https://meridianlabs-ai.github.io/inspect_scout)
- [Nygard-style ADR template, secondary copy](https://docs.clan.lol/decisions/template)
