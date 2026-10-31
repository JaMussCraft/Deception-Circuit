# Shared brief for ticket implementers (autoresearch-workflow)

You are implementing one ticket of the autoresearch-workflow setup. The orchestrator gives you the ticket path. Read
this whole file first, then your ticket, then `spec.md` (binding). This feature builds tooling and documents only.
It runs no GPU jobs and spends no API money.

Short names, used in every ticket:

- **F** = `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow` (feature directory).
- **W** = `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow` (worktree root, branch `autoresearch-workflow`).
- **S** = `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging` (staging root).
- **T** = `/u/swong2/.claude/jobs/b2cb53cd/tmp/<NN>` (your scratch directory for helper scripts and copies; NN is your ticket number).
- **A** = `/projects/beto/swong2/Alignment`; **DC** = `/projects/beto/swong2/Alignment/Deception-Circuit` (main checkout).
- **RS staged path** = `S/tree/projects/beto/swong2/Alignment/.agents/research_session/`, with tests in
  `S/tree/projects/beto/swong2/Alignment/.agents/tests/`.

Tickets: 01 lint, apply tool, hygiene and config; 02 RS core (usage, session state, gate, ack); 03 RS records
(registry, renders, worklog, jobs, findings-check); 04 science guards in DC; 05 index and registry seeding; 06 hooks
for both tools; 07 profiles for both tools; 08 protocol docs and templates; 09 migration A (standardize, dedupe, trim
CLAUDE.md); 10 migration B (scripted `.scratch` archive); 11 pilot checklist and audit-scan; 12 wrap-up.

## Hard constraints (non-negotiable)

1. **Models.** You are Opus. If your ticket lets you spawn a subagent, pass `model: "opus"` on every spawn; never
   omit it. Do not spawn unless your ticket says you may.
2. **No git, no worktrees.** Never run `git` (any subcommand), never call EnterWorktree, never create or remove a
   worktree or branch. The orchestrator commits by explicit file list. Library code that calls `git rev-parse` at run
   time is allowed (precedent: `scripts/sdr_routing_pilot.py:392`); its tests must mock that call.
3. **Other sessions' directions are off limits.** Do not edit anything under `A/.scratch/sdr-*`,
   `A/.scratch/selective-deception`, `DC/outputs/_studies/`, `DC/outputs/_analyses/` or any other direction's files,
   except exactly what your ticket names. Reading is fine. Ticket 10 reads them only by script (hashes and the secret
   scan), never into your context.
4. **Where you may write.**
   - Inside W, directly with Write or Edit (DC code, tests, `docs/research/**`, `.claude/settings.json`, `.gitignore`).
   - Inside S and T, directly. These are outside every git repository.
   - Your ticket file's `**Status:**` line, checkboxes and `## Comments`, and `F/reports/<NN>-handback.md`.
   - Nowhere else. The isolation hook refuses writes into the main DC checkout and into A.
5. **Staging for A and user config.** Any file whose final home is in A (for example `docs/agents/*.md`,
   `.claude/settings.json`, `.claude/settings.local.json`, `.claude/CLAUDE.md`, `.claude/agents/*.md`, `.agents/*`,
   `.agents/memory/*`, `project_context/*`, `.scratch` symlinks) or in user config (`~/.claude/settings.json`,
   `~/.claude/profiles/`, `~/.codex/config.toml`, `~/.codex/hooks.json`, `~/.local/bin/*`), or in the main checkout's
   ignored areas (`DC/outputs/_studies/`), is staged under `S/tree/<absolute destination without the leading slash>`
   and listed in your op file `S/ops/<NN>-<slug>.json` (spec §7). The orchestrator runs the apply tool. Never write the
   destination yourself. `~/.codex/config.toml` ops are wave C and wait for the user's go because Codex must restart.
6. **Memory edits.** A Codex session is live and edits `A/.agents/memory/` concurrently. `MEMORY.md` is changed only
   with `replace_text` (an `old_text` copied from the file you just re-read, which must occur exactly once) and
   `append_text` ops, never a whole-file write (spec §7, R18). For any other memory file, re-read it immediately
   before you stage its replacement and record its sha256 as `expect_sha256`. Every memory op sets `"lint": true`,
   and the staged text must pass `research-session lint`.
7. **Secrets.** Never print the `env` block of `~/.claude/settings.json` or any token. When you inspect that file, print
   key names only, for example with
   `/sw/external/python/anaconda3/bin/python3.9 -c "import json;print(sorted(json.load(open('/u/swong2/.claude/settings.json'))))"`.
   `docs/research/**` is pushed to a public GitHub repository: run the secret scan on anything you put there.
8. **No GPU jobs, no `sbatch`, no paid API calls.** Ticket 11 only writes what the user will launch.
9. **Faithful reporting.** Failures are reported as failures, skipped steps as skipped, unverified facts as
   unverified. Never tick a checkbox you did not verify with a command whose output you read.

## Shell rules (the isolation hook enforces them)

- One plain command per Bash call. No `&&`, `||`, `;`, pipes into interpreters, `cd X && ...`, heredocs, loops, or
  `$VAR` and `$(...)` that compute a program, path or option. Environment assignments in front of a command are fine
  (`OMP_NUM_THREADS=1 /path/python ...`).
- Absolute paths everywhere. Your working directory is reset between calls.
- For anything longer than one line, write a script into T with the Write tool and run it by literal path.
- Interpreters, always by absolute path:
  - mgnp: `/u/swong2/.conda/envs/mgnp/bin/python` (Python 3.12, has `tomllib`, torch, transformers 5.13).
  - base: `/sw/external/python/anaconda3/bin/python3.9` (Python 3.9, no `tomllib`, transformers 4.57.3).
  - RS and the apply tool are stdlib-only and must run on both. The hooks run RS on base python3.9.
- pytest: always add `-p no:cacheprovider`. On base, prefix `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.
  Delete any `core.*` dump a base run leaves in W.
- Run the full DC suite only with `run_in_background` and a timeout of at least 1800000 ms; Lustre can stall IO.
- Use `-I` for Python that reads datasets or untrusted files.

## Must-read files, in order

1. Your ticket. Its checkboxes are the acceptance criteria.
2. `F/spec.md`. Binding: §4 schemas, §5 harness, §6 science guards, §7 staging, §9 rulings. Do not reinterpret a
   ruling; if one seems wrong, hand back.
3. `F/reports/00-plan-handback.md`: verified facts with file:line evidence, and the list of unverified facts.
4. The lane report sections your ticket names, in `F/reports/` (lane1 public patterns, lane2 harness, lane3 repo
   structure, lane4 oversight). `F/reports/proposal-full.md` is the approved design; the spec overrides it.
5. `A/docs/agents/claude-codex.md` if your ticket touches Codex, plugins or the bridge.
6. In W: `CONTEXT.md` only if your ticket touches experiment code (ticket 04).

## Tests

- RS and its tests (staged), from any directory:
  `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/projects/beto/swong2/Alignment/.agents/tests`
  and the same with `OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest ...`. Tests locate the
  package relative to their own file (as `A/.agents/tests/test_codex_usage.py` does), so they pass both staged and
  installed. Use `unittest` style classes with temporary directories; never touch the real `~/.claude`, `~/.codex`
  or memory from a test.
- The apply tool: `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider F/tools/test_apply_staged.py`
  and the same on base.
- DC code (ticket 04): single files often, then the full suite once in each env, compared by failure name against
  `F/reports/04-baseline-failures.md`. Memory says main has 7 baseline failure names plus a MASK repo-root test that
  fails from a worktree. A difference of one fp32 ulp between envs is not a regression.
- Lint your own Markdown deliverables once ticket 01's lint exists:
  `/sw/external/python/anaconda3/bin/python3.9 S/tree/projects/beto/swong2/Alignment/.agents/research_session/cli.py lint <files>`.

## Hand-back

- At start, set your ticket's `**Status:**` to `claimed`. Tick each checkbox only after verifying it.
- Write progress into `F/reports/<NN>-handback.md` as you go, using the headings of spec §4.7: What changed (absolute
  paths, split into "committed by orchestrator from W" and "staged in S, ops file S/ops/NN-*.json"), How verified
  (command in a code block, then the observed output), Execution evidence (write "not applicable: no runs" when no
  job ran), What is NOT done, Open questions.
- At the end, append `## Comments` to the ticket with the same file lists and the test results per env, and set
  `**Status:**` to `resolved`, or leave `claimed` with a blocker note.
- Your final message to the orchestrator is a summary of at most 10 lines: hand-back triggers first, then status,
  files to commit, staged op file and its wave, tests per env, and open questions.

## Ask the orchestrator (hand back, do not proceed) when

- your work needs a file outside your ticket's scope, a git action, an install, or network access beyond reading
  documentation pages;
- a staged memory op would conflict (`expect_sha256` no longer matches when you re-read);
- a lint threshold, a schema field or a ruling would have to change;
- a documented fact your ticket depends on cannot be verified (record the URL you checked);
- a DC test fails that is not in the baseline;
- your projected reading and writing exceed about 250k tokens;
- anything would touch `~/.codex/config.toml` outside a wave C op, a running session, or another direction's files.

## Writing style

Write every document and comment in full sentences with normal spacing. One idea per sentence. Define a code name on
first use. Never compress prose to save tokens; the lint rejects glued text, and glued text is the failure this
feature exists to stop.
