# Lane 3: Repo structure for agent legibility and cross-session synthesis

Audit date 2026-10-31. Read-only. Token estimates use bytes/4.

## 1. Where research state lives today

| Location | Repo / git status | Files | Text size | ~Tokens |
|---|---|---|---|---|
| `Alignment/.scratch/*/` (16 real dirs + 1 symlink) | Alignment, **untracked but NOT ignored** (`?? .scratch/`) | 728 `.md` (incl. symlink) | 7.5 MB md; 5.75 MB without the symlink | ~1.9M (1.44M w/o symlink) |
| `.scratch/selective-deception` | symlink into `Deception-Circuit/outputs/_studies/selective-deception/study` (ignored there by `outputs/_studies/`) | 254 md, 3954 files | 1.8 MB md, 46 MB md+json | ~450k md |
| `project_context/reports/` | Alignment, tracked status unclear (untracked dir listed) | 12 | 72 KB | 18k |
| `project_context/research_notes/` (2 dirs) | Alignment | 15 | 248 KB | 62k |
| `project_context/research_ideas/` | Alignment | 2 | 64 KB | 16k |
| `project_context/notes.md`, `related_papers.md` | Alignment, tracked | 2 | 39 KB | 10k |
| `project_context/prompts/` | Alignment | 16 | 104 KB | 26k |
| `.agents/memory/` | Alignment, **ignored** (`.gitignore:8`) | 33 | 240 KB | 60k (MEMORY.md 10 KB = 2.5k loaded every session) |
| `Deception-Circuit/docs/research/` (3 dirs + interp-tooling.md) | DC, tracked | 153 | 334 KB md | 83k |
| `Deception-Circuit/CONTEXT.md` + `docs/adr/` (2 ADRs) + other docs | DC, tracked | ~6 | 90 KB | 23k (CONTEXT.md 5k) |
| `Deception-Circuit/outputs/` | DC, mixed: 2359 files tracked (1341 in `_suites`), every `eval5_*` dir and several suites untracked, `_analyses/` and `_studies/` ignored | 571 entries at depth 2 | 25 GB | n/a |

**What a fresh synthesis agent must read today.** No single index exists. The cheapest honest route to "current state" is: MEMORY.md (2.5k), the two oversized memory files it points to (`sdr-mechanism-review.md` 72 KB, `selective-deception-execution.md` 45 KB, ~29k together), `docs/research/{sdr-mechanism,selective-deception}/README.md` (2.5k), `mechanism-analysis/synthesis.md` (10k), `SDR mechanism investigation status.md` and `Deception specificity and shared circuits.md` (5k), CONTEXT.md (5k), plus at least one RESUME per live direction (2k-11k each; mechanism-analysis RESUME is 43 KB = 11k). That is roughly 60-80k tokens just to orient, and it still misses findings that live only in `.scratch/*/analysis.md` or `final-report-review.md`. A full sweep of everything is ~2M tokens. A target of <30k tokens via one index plus per-direction handoffs is achievable.

## 2. Problems found

**P1. No index of findings or directions.** Findings are spread across memory, two report locations, three `docs/research` handoffs, and `.scratch/*/analysis.md`. Status (verified / refuted / paused) exists only in prose. The Alignment `.claude/CLAUDE.md` never mentions Deception-Circuit (0 occurrences); it still describes petri/bloom/probe notebooks as the main work.

**P2. Byte-identical duplication.** All 11 SDR reports in `project_context/reports/` are identical to `Deception-Circuit/docs/research/sdr-mechanism/reports/`. All 10 notes in `project_context/research_notes/Deception specificity and shared circuits/` are identical to `docs/research/selective-deception/reports/`. Only `project_context/reports/Deception specificity and shared circuits.md` is unique. Two homes means future edits will drift.

**P3. Inconsistent per-direction state files.** Of 16 `.scratch` dirs, 6 have `RESUME.md`; the rest use `progress.md`, `plan.md`, `analysis.md`, `state.json`. Variants: `RESTART.md` (sdr-session-wrapup), `PAUSED.md` plus five `RESUME-*.md` history files (selective-deception), `operator/`, `_orch/`. Spec naming varies: `spec.md`, `draft-spec.md`, `sharding-spec.md`, `completion-diagnostic-spec.md`. The `issues/NN-*.md` convention from `docs/agents/issue-tracker.md` is only used by 4 older dirs.

**P4. Three ledger formats.** `selective-deception/compute-ledger.json` (flat caps + `reservations[]` with `job_id`, `source_revision`, `manifest_hash`), `mechanism-analysis/compute-ledger.json` (`feature`, per-cluster `allocations_gpu_hours`, `totals.reserved/in_flight/reconciled`), and `ledger.md` prose in every `sdr-*` dir. Plus a separate `compaction-ledger.json`. A synthesis agent cannot sum spend across directions.

**P5. Systemic whitespace-stripping corruption.** Not one file. It appears in `.scratch/sdr-clause-choice/RESUME.md` ("Independentprioritycritiqueendorsesfact-preserving contingencycontrast"), `.agents/memory/selective-deception-execution.md` ("all1848records/160identities verified"), and in `MEMORY.md` itself, the index loaded every session ("PAUSED/merged locally2026-10-31 at133fe82;8selectivebranches"). It looks like a writer compressing text to save tokens, getting progressively worse with each rewrite. It reduces both human and model readability and breaks grep.

**P6. Memory used as a session log.** `sdr-mechanism-review.md` (72 KB) and `selective-deception-execution.md` (45 KB) are ~49% of the 240 KB memory directory. Both are chronological execution logs, not single facts. The memory guidance is one fact per file; these belong in the direction's handoff.

**P7. Durable state is not in git.** `.agents/memory/` is ignored (shared memory survives only on Lustre). `.scratch/` is untracked: 16 directories of specs, decisions and reviews have no history. The selective-deception study (46 MB text) is ignored under `outputs/_studies/`.

**P8. Stale branch/worktree.** `Deception-Circuit` worktrees: main (4253bb6) and `.claude/worktrees/mechanism-datasets` (c24b5d9). `mechanism-datasets` is 0 commits ahead of main and 73 behind, and also exists as `origin/mechanism-datasets`. It is fully merged dead state. Main was 51 ahead of origin at my first check and 0 a few minutes later, so another session pushed during the audit; main is now in sync with `origin/main`.

**P9. Spec prompts are no longer entry points.** `project_context/prompts/*.md` files date from April to Sept 13. Only `deception_tasks_shared.md` is referenced anywhere in `.scratch`, memory, or DC docs (2 references, from `mechanism-datasets/agent-brief.md`). Sessions now start from `.scratch/<slug>/spec.md` or from a `docs/research/*/README.md` handoff. The prompts are historical specs; they should be labelled as such, not deleted.

**P10. Run outputs lack provenance at the core.** `outputs/llama-8b-instruct_*/<run>/` has `config.json` (with `seed`), `results.json`, `history.json`, `train.log`, but no git commit, dirty flag, dataset hash or model revision. Newer analysis scripts already write rich manifests (59 `manifest.json` files under `outputs/`, e.g. `_analyses/sdr-routing-pilot/*/manifest.json` with `git_commit`, `dirty_diff_hash`, `code_sha256`, `model_revision`, `families_hash`, `seed`, `schema`, `manifest_hash`, `software`, `tokenizer_files`). `train.py`/`run_io.make_run_dir` and `evaluate_circuit.py` do not. Eval dirs `outputs/eval5_*` are untracked and have no manifest.

**P11 (outside lane, flag to lead).** The Alignment repo's `origin` URL embeds a GitHub personal access token in plaintext (`https://ghp_…@github.com/…`). It should be rotated and moved to a credential helper. Token not reproduced here.

## 3. Reference layouts (borrowed selectively)

- **Karpathy autoresearch `program.md`.** One human-edited instruction file plus `results.tsv`, tab-separated with columns `commit, val_bpb, memory_gb, status (keep|discard|crash), description`, one row per experiment, branch `autoresearch/<tag>`. Borrow: one row per result with a commit and a status enum, TSV/markdown table not prose. Do not borrow: leaving the results file untracked.
- **Anthropic, "Effective harnesses for long-running agents".** A progress file read at session start and updated at session end, a JSON feature list where agents only flip a `passes` field, and git commits after each change. Their stated reason for JSON: "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files." Borrow: JSON for the ledger and the directions registry claims; markdown for the human worklog.
- **Claude Code best practices (code.claude.com/docs/en/best-practices).** Keep CLAUDE.md short: only what Claude can't work out from the repo; "Describe your architecture and file layout in CLAUDE.md" is listed as a mistake; rules that must never bend belong in hooks. Borrow: replace the stale layout prose in `Alignment/.claude/CLAUDE.md` with a 3-line pointer to the index files below.
- **cookiecutter-data-science.** Raw/interim/processed data separation and a `reports/` folder of finished outputs. Borrow only the idea that finished reports have one home separate from working notes.

## 4. Proposed minimal restructuring

Principle: add index files and fix naming; move only duplicated or misplaced files. Canonical home for research state is **Deception-Circuit** (tracked, has a remote, branches and outputs live there, so one commit per milestone covers code + state). `.scratch/<slug>` in Alignment becomes a symlink, following the existing `selective-deception` precedent.

### Proposed tree (new or changed items marked +, ~)

```
Deception-Circuit/
  CONTEXT.md                          (unchanged glossary)
  docs/
    adr/                              (unchanged)
    research/
  +   INDEX.md                        entry point: how to read, links to the 3 tables below
  +   FINDINGS.md                     one row per claim (rendered from findings.jsonl or hand-kept)
  +   DIRECTIONS.md                   rendered view of directions.json
  +   directions.json                 registry; claims are edits to this file + a commit
  +   ledger.json                     global GPU/API spend roll-up (one schema)
      <slug>/                         one dir per direction (existing: sdr-mechanism, selective-deception, mechanism-analysis)
        README.md                     handoff: question, verdict, pointers (<= 2 pages)
  +     WORKLOG.md                    human-readable dated log, append-only
  +     RESUME.md                     machine state for the next session (overwrite; <= 150 lines)
  +     spec.md                       the frozen question / design (moved from .scratch)
  +     ledger.json                   this direction's reservations (same schema as global)
        reports/                      finished reports (canonical copy)
  +     reviews/                      design/code/scientific reviews (moved from .scratch)
  +     history/                      superseded RESUME-*, RESTART, PAUSED
        issues/NN-<slug>.md           tickets, per docs/agents/issue-tracker.md
  outputs/<run>/manifest.json         + written by run_io.make_run_dir and evaluate_circuit.py

Alignment/
  .claude/CLAUDE.md                   ~ trim layout prose; point to Deception-Circuit/docs/research/INDEX.md
  .scratch/<slug> -> ../Deception-Circuit/docs/research/<slug>     ~ symlinks (precedent exists)
  project_context/reports/            ~ keep only the unique file; README pointer to DC copies
  project_context/research_notes/     ~ same
  project_context/prompts/README.md   + one line: "historical specs; current entry is INDEX.md"
  .agents/memory/                     ~ shrink the two log-like files to pointers
```

Large binaries, receipts, `.log`, test outputs and per-row JSON stay out of `docs/research/<slug>/`; they go to `outputs/_studies/<slug>/` (ignored) and are referenced by path + sha256 from the README.

### File formats

**`docs/research/FINDINGS.md`** (markdown table, no prose rows, greppable; autoresearch-style):

```
| id | date | direction | claim | status | commit | evidence | report |
|----|------|-----------|-------|--------|--------|----------|--------|
| F-sdr-007 | 2026-10-26 | sdr-mechanism | H24-27 restoration blocks most clause effects; rescue incomplete | verified | 695b126 | outputs/_analyses/sdr-shared-composition/... | docs/research/sdr-mechanism/reports/SDR shared-component composition findings.md |
```

`claim` is one sentence. `status` ∈ {proposed, verified, refuted, superseded, paused}. `verified` requires an evidence path whose `manifest.json` names the commit. Superseded rows stay, with `superseded_by` noted in the claim cell. Expected initial size: 30-60 rows, ~4-8k tokens.

**`docs/research/directions.json`** (JSON for the concurrency-sensitive part, rendered to `DIRECTIONS.md`):

```json
{"schema": 1, "directions": [
  {"id": "sdr-mechanism", "title": "SDR shared-component mechanism",
   "status": "paused", "claimed_by": null, "claimed_at": null,
   "branch": null, "worktree": null,
   "parent_findings": ["F-sdr-003"], "spec": "docs/research/sdr-mechanism/spec.md",
   "resume": "docs/research/sdr-mechanism/RESUME.md",
   "ledger": "docs/research/sdr-mechanism/ledger.json",
   "updated": "2026-10-31"}]}
```

`status` ∈ {proposed, open, claimed, active, paused, done, abandoned}. Claim protocol: a session sets `claimed_by` = `<tool>-<session-tag>` and `claimed_at`, commits on main, then creates the branch/worktree. A synthesis session may add `proposed` rows only. This works with the subagent-worktree-pin rule because only the orchestrator edits and commits it.

**`ledger.json`** (one schema, per direction and rolled up globally; merges the two existing JSON styles):

```json
{"schema": 1, "direction": "selective-deception",
 "caps": {"reserved_gpu_hours": 40.0, "paid_api_usd": 20.0, "max_concurrent_gpu_jobs": 2},
 "totals": {"reserved_gpu_hours": 38.35, "actual_gpu_seconds": 45167, "api_usd_known": 4.18, "api_usd_reserve": 0.66},
 "reservations": [{"id": "...", "job_id": "...", "cluster": "delta", "account": "...", "partition": "...",
   "gpus": 1, "requested_minutes": 15, "reserved_gpu_hours": 0.25, "actual_seconds": null,
   "status": "RUNNING|COMPLETED|FAILED|CANCELLED", "source_commit": "...", "manifest_hash": "...", "output_dir": "..."}],
 "api_calls": [{"date": "...", "provider": "...", "calls": 0, "usd": 0.0}],
 "compactions": [{"at": "...", "session": "...", "note": "..."}]}
```

Folding compaction counts into the ledger removes the separate `compaction-ledger.json`.

**`RESUME.md`** fixed headings, overwrite each session, ≤150 lines: `Status`, `Branch/worktree/commit`, `In-flight jobs`, `Next action`, `Do not`, `Open decisions for user`. Anything historical goes to `WORKLOG.md` or `history/`.

**`WORKLOG.md`** append-only, `## YYYY-MM-DD HH:MM (session tag)` entries, full sentences. Ban token-compressed prose here and in memory (P5).

**`outputs/<run>/manifest.json`** (reuse field names already used by `scripts/sdr_routing_pilot.py` and `component_analysis/selective_v6_manifest.py`; do not invent a new schema):

```json
{"schema": "run-manifest/1", "created": "...", "script": "train.py", "argv": [...],
 "git_commit": "...", "git_dirty": false, "dirty_diff_hash": null,
 "config_sha256": "...", "dataset_files": {"data/datasets/sdr_v2/train.json": "sha256..."},
 "model": "llama-8b-instruct", "model_revision": "...", "seed": 42,
 "software": {"python": "...", "torch": "...", "transformers": "..."},
 "host": "...", "slurm_job_id": "...", "direction": "sdr-mechanism"}
```

Write it from `run_io.make_run_dir` (one function, covers every `train.py` run) and from `evaluate_circuit.py`'s output-dir creation. Old runs get no backfill; FINDINGS rows citing them stay `verified` only if a later run with a manifest reproduces them, otherwise mark the evidence cell `pre-manifest`.

### What to track vs ignore

- **Track in Deception-Circuit:** `docs/research/**` text (INDEX, FINDINGS, directions.json, per-direction README/RESUME/WORKLOG/spec/ledger/reports/reviews/issues). Per-run `manifest.json`, `config.json`, `results.json` under `outputs/` via whitelist patterns (`outputs/**/manifest.json` etc.) while ignoring `eval5_*` row dumps, shards, checkpoints, `_studies/`, `_analyses/` bulk.
- **Keep ignored:** `outputs/_studies/`, logs, `.pt`, receipts over ~1 MB, `.agents/memory/` (it is per-user Claude/Codex memory; tracking it would publish cluster/account details to the remote).
- **`.scratch/` in Alignment.** Option A (recommended): move the text into `Deception-Circuit/docs/research/<slug>/` and leave symlinks. Pros: one repo, one commit per milestone, history on the remote, branches and state co-located. Cons: a one-time migration of ~16 dirs, and `.scratch` receipts that contain absolute paths keep pointing at the old location (the symlink preserves them). Option B: `git add` `.scratch/**/*.md|json` in Alignment. Pros: no moves. Cons: every research milestone becomes two commits in two repos with no atomicity; the Alignment remote has a leaked credential (P11); Alignment's main is cluttered with unrelated notebook changes. Option A is better. If the user wants zero moves, do B but only for `spec.md`, `RESUME.md`, `WORKLOG.md`, `ledger.json`.

## 5. Ranked recommendations (cost in files)

1. **Add `Deception-Circuit/docs/research/FINDINGS.md` and `INDEX.md`** (2 new files). This is the single highest-value change: one table of claims with status, commit and evidence path lets a synthesis agent orient in under ~10k tokens instead of ~70k. Seed it from the three existing handoffs and `mechanism-analysis/synthesis.md`.
2. **Add `docs/research/directions.json` + rendered `DIRECTIONS.md`** (2 new files). Gives concurrent sessions a claim protocol (edit, commit on main, then branch). JSON resists accidental overwrite.
3. **Write `manifest.json` from `run_io.make_run_dir` and `evaluate_circuit.py`** (2 edited source files, 0 moved). Reuse the field names already in `scripts/sdr_routing_pilot.py`. Results become trustworthy without rerunning.
4. **Fix the whitespace-stripping corruption and ban compressed prose** (rewrite `MEMORY.md`, `selective-deception-execution.md`, `sdr-clause-choice/RESUME.md`; add one line to the memory and worklog guidance). It affects the index every session loads.
5. **Shrink the two log-style memory files to ~10-line pointers** (2 files edited, bodies moved into `docs/research/{selective-deception,sdr-mechanism}/WORKLOG.md`). Cuts memory from 240 KB to ~125 KB.
6. **Standardise per-direction filenames** (`README`, `spec`, `RESUME`, `WORKLOG`, `ledger.json`, `reports/`, `reviews/`, `history/`, `issues/`). Move the 5 `RESUME-*.md`, `PAUSED.md` and `RESTART.md` into `history/` (7 moves) and document the layout once in `INDEX.md` and `docs/agents/issue-tracker.md`.
7. **Unify ledgers into one `ledger.json` schema with a global roll-up** (1 schema, ~3 existing ledgers converted, `compaction-ledger.json` folded in). Lets a synthesis agent report total GPU/API spend.
8. **Move `.scratch/<slug>` text into `Deception-Circuit/docs/research/<slug>/` with symlinks left behind** (16 dirs, text only; bulk to `outputs/_studies/`). Makes research state durable on the remote with single-repo commits. If too costly now, at least `git add` each `spec.md`/`RESUME.md`.
9. **Remove duplication between `project_context/` and `docs/research/*/reports/`** (21 duplicate files become pointers or are deleted after confirming byte-identity; 1 README). Also trim `Alignment/.claude/CLAUDE.md` layout prose to a pointer to `INDEX.md` and label `project_context/prompts/` as historical (1 README).
10. **Clean dead git state and the credential.** Remove the `mechanism-datasets` worktree and branch (local and `origin/`; it is 0 ahead, 73 behind). Rotate the PAT embedded in the Alignment `origin` URL and switch to a credential helper.

Total cost for items 1-7 and 9-10: about 8 new files, ~2 source edits, ~30 moves or pointer replacements. Item 8 is the only large move.
