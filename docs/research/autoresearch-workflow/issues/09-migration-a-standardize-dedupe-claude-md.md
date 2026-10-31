# 09 — Migration A: standardize the handoff directories, dedupe project_context, trim CLAUDE.md

**Status:** claimed
**Type:** task
**Blocked by:** 05 (INDEX exists), 08 (protocol docs to point at)
**Wave:** A for Alignment files; W files are committed by the orchestrator.
**Estimated size:** reading about 70k tokens (`A/.claude/CLAUDE.md` 190 lines, `A/docs/agents/issue-tracker.md`,
`A/project_context/prompts/autoresearch.md`, the three handoff directories' file lists,
`A/.scratch/sdr-clause-choice/RESUME.md` 9 KB, `mechanism-analysis/synthesis.md` summary), writing about 30k tokens.
**Hand-back:** `F/reports/09-handback.md`

## What to do

Make the three existing `docs/research` directions follow the layout of spec §3, remove the byte-identical copies in
`project_context`, label the old prompts as historical, and point the project instructions at the new index.

## Facts to build on

- `W/docs/research/mechanism-analysis/` has `synthesis.md` but no `README.md`. The other two directories have one.
- Lane 3 P2: the 11 files in `A/project_context/reports/` named `SDR *.md` match
  `W/docs/research/sdr-mechanism/reports/`; the 10 files in
  `A/project_context/research_notes/Deception specificity and shared circuits/` match
  `W/docs/research/selective-deception/reports/`. `A/project_context/research_notes/SDR circuit mechanism review/`
  also exists. Only `A/project_context/reports/Deception specificity and shared circuits.md` was reported unique.
  Re-check every claim by sha256 before staging anything.
- `A/.claude/CLAUDE.md` describes petri, bloom and probe notebooks as the main work, never mentions
  Deception-Circuit, and its "Agent Workflow" section names Sonnet agents. It contains a bridge block between
  `# BEGIN Claude-Codex bridge` and `# END Claude-Codex bridge` that must stay byte-identical.
- `A/project_context/prompts/autoresearch.md` still says Sonnet subagents (proposal §5).
- `A/docs/agents/issue-tracker.md` puts features under `.scratch/<feature-slug>/`.
- `A/.scratch/sdr-clause-choice/RESUME.md` lines 9-34 are glued; R14 says the archive copy stays untouched.

## Scope

In W:
- `W/docs/research/mechanism-analysis/README.md`: a handoff of at most two pages (question, verdict, where the
  claims live, what is closed, useful next questions), linking `synthesis.md`.
- `W/docs/research/sdr-mechanism/history/sdr-clause-choice-RESUME-readable.md`: a faithful rewrite of that RESUME in
  full sentences, with a first line naming the source path and its sha256 (R14). Do not add or drop facts.

Staged (wave A):
- `move` ops sending each verified duplicate in `A/project_context/reports/` and `research_notes/` to
  `/u/swong2/.claude/research-session/backups/project-context-dedupe-20261031/<same relative path>`, and a
  `README.md` in each affected folder listing the canonical DC path for every moved file. Files that are not
  byte-identical stay and are listed.
- `/projects/beto/swong2/Alignment/project_context/prompts/README.md` stating that the prompts are historical specs
  and that sessions now start from `docs/agents/research-session.md` and `Deception-Circuit/docs/research/INDEX.md`.
  Prepend one dated line to `autoresearch.md` saying it is historical and that subagents now run on Opus.
- `/projects/beto/swong2/Alignment/.claude/CLAUDE.md` (with `expect_sha256`): replace the layout prose with a short
  pointer to `Deception-Circuit/docs/research/INDEX.md`; add a Deception-Circuit section (what it is; research state
  lives in its `docs/research/`; tests run on both interpreters; Slurm and usage rules live in memory and in
  `docs/agents/research-session.md`); change the Agent Workflow section to Opus agents with `model` passed on every
  spawn; add the Codex lint rule; keep the bridge block byte-identical. Target at most 120 lines.
- `/projects/beto/swong2/Alignment/docs/agents/issue-tracker.md`: new features live in
  `Deception-Circuit/docs/research/<slug>/` (spec, issues, reports); `.scratch/<slug>` entries are legacy symlinks
  to archives.
- `S/ops/09-migration-a.json`.

## Acceptance criteria

- [ ] A script in T prints the sha256 pairs for every candidate duplicate; only equal pairs get a `move` op. Output
      pasted. (Partly done: the pairs are printed and pasted, 21 of 27 equal, but no `move` op is staged; see the
      blocker in Comments.)
- [x] The CLAUDE.md bridge block is byte-identical before and after (the script compares the extracted block).
- [x] Every path mentioned in the new CLAUDE.md, the prompts README and issue-tracker.md exists, or will exist after
      the listed waves (a script checks and labels each).
- [x] All new and changed Markdown passes `cli.py lint`.
- [x] The readable RESUME rewrite keeps every number of the source; a script lists the numbers in both files and
      shows no number missing from the rewrite.
- [x] `apply_staged.py --staging S --only 09 --dry-run` output pasted.

## Verification

Lint, the scripted checks above, and the dry run. Do not touch `A/.scratch` here; that is ticket 10.

## Comments

**2026-10-31, implementer (Opus).** Status stays `claimed` with one blocker: the dedupe moves. Full detail is in
`reports/09-handback.md`.

Files to commit from W:

- `docs/research/mechanism-analysis/README.md` (new handoff)
- `docs/research/sdr-mechanism/history/sdr-clause-choice-RESUME-readable.md` (new, R14)
- `docs/research/autoresearch-workflow/reports/09-handback.md`
- `docs/research/autoresearch-workflow/issues/09-migration-a-standardize-dedupe-claude-md.md` (this file)

Staged in S, op file `S/ops/09-migration-a.json`, four `write` ops, all wave A with `lint: true`:
`A/.claude/CLAUDE.md`, `A/docs/agents/issue-tracker.md`, `A/project_context/prompts/README.md` (new) and
`A/project_context/prompts/autoresearch.md`. The dry run reports all four as WOULD APPLY.

Tests per environment: this ticket changes no code, so no test suite was run. The lint ran on base Python 3.9 with
both the installed and the staged `cli.py` and passed. The checker scripts ran on base Python 3.9.

**Blocker.** All 21 byte-identical duplicates in `project_context` belong to the live-session directions of R28, and
frozen manifests, receipts and audit scripts in `A/.scratch/sdr-*` bind their paths. Separately, the `move` op is a bare
`os.rename`, which cannot cross from `/projects` to `/u`. No move op and no folder README was staged. The hand-back's
first open question gives three options for the orchestrator to choose from.
