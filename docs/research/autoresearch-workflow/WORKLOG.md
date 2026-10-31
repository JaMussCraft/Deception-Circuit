# Worklog: setting up the autoresearch workflow

<!-- HEADER: rewritten at every trigger; body below is append-only -->
| | |
|---|---|
| State | Running: planner applying review fixes; implementation wave A starts next |
| Directions | 1. Hygiene and config: queued · 2. Findings index and layout: queued · 3. Hooks and CLI: queued · 4. Protocol docs and profiles: queued · 5. Science guards and pilot: queued |
| Started / last updated | Sat 31 Oct 2026, 8:05 am CDT / Sat 31 Oct 2026, 12:55 pm CDT |
| Orchestrator auto-compactions | 0 |
| Weekly usage (this session) | account read all-models 11%, Fable 17% at start; cap pause at 80% |
| Human review checkpoints | 1 of 1 acknowledged (plan approved) |
| GPU budget | 0 of 0 GPU-h (none planned for setup) |
| OpenRouter credit | $0 |
| Open needs from you | 0 |

**Right now.** The planner is applying the reviewer's nine fixes to the spec and tickets. When they land, two Opus implementers start wave A: the text lint plus apply tool, and the science guards in the Deception-Circuit code. Nothing outside the worktree has been changed yet.

**Terms.** *Worktree*: an isolated copy of the Deception-Circuit repository on its own branch, where all code changes for this setup are made.

## Needs from you
- ~~N0 (Sat 8:30 am): approve the workflow proposal and plugin disable list.~~ Answered Sat 8:55 am: "go", with corrections (checkpoint is a usage freeze; keep superpowers everywhere; move .scratch text into Deception-Circuit docs; science guards during setup).

## Findings register
| # | When | Finding, in plain words | Setup needed to read it | Strength | Evidence |
|---|---|---|---|---|---|
| F1 | Sat 8:20 am | A fresh synthesis agent needs 60-80k tokens just to learn the current research state, because no index of findings or directions exists. | Token estimate from file sizes across .scratch, memory, reports and docs. | reviewed | reports/lane3-repo-structure.md §1 |
| F2 | Sat 8:25 am | The unreadable glued-together state files come from the model re-reading its own compressed prose and compounding it; the same glue leaked into the memory index. | Measured share of 20+ character tokens per paragraph in the affected file and in Codex rollout logs. | reviewed | reports/lane4-oversight.md §0 |
| F3 | Sat 8:25 am | Only 13 of 2,683 analysis result files record the code commit they came from. | Grep over Deception-Circuit/outputs/_analyses JSON files. | preliminary | reports/lane1-public-patterns.md §1b |

## Process incidents
| # | When | What went wrong (agent workflow) | Effect | Fix or status |
|---|---|---|---|---|
| P1 | Sat 8:40 am | A research agent reported that Codex workers had been running on Astra; the user's own check showed 215 of 253 ran Sol. The agent inferred from config files without checking the spawn logs. | Wrong claim reached the user and a memory note | Memory note corrected; model defaults kept only as a safety net |
| P2 | Sat 9:00 am | The worktree isolation hook refuses writes to the Alignment checkout and compound shell commands, so the feature directory could not be created where first planned. | 10 minutes lost | Feature directory moved into the worktree (matches the approved layout); Alignment-side files are staged and applied by the orchestrator |

## Log
### Saturday 31 October 2026
**8:05 am CDT · Session started.** Goal: review the coding-agent research workflow against public practice and the repo, then set it up. Four Opus research agents launched on non-overlapping lanes.
**8:40 am CDT · Hand-backs: all four research lanes finished.** Main gaps: no findings index, checkpoints and counters enforced only by memory, degrading state files, results without commit stamps. Proposal written and reviewed by the advisor.
**8:55 am CDT · User decision.** Plan approved with corrections (see Needs from you). Setup starts in a pinned Deception-Circuit worktree.
**9:05 am CDT · Planning started.** Feature directory created inside the worktree. Opus planner spawned to write the spec and tickets.
**12:30 pm CDT · Hand-back: plan written.** A binding spec with 25 rulings, 12 tickets in 7 waves, a shared agent brief and a facts report. Its eight open questions were ruled on (session tag format, how to refresh a stale usage reading, which directories the live Codex session still owns, and five smaller ones).
**12:50 pm CDT · Hand-back: independent plan review.** Verdict: approve with nine fixes. The important ones: installing hooks before the tool they call exists could lock a session out of its own tools; the text lint must refuse a bad write before it happens rather than complain after; the migration ticket still touched directories the live Codex session owns. All nine sent back to the planner with rulings. Next: implementation wave A (lint and apply tool; science guards) once the fixes land.
