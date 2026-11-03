# Research index

This tree holds the research state of the Deception-Circuit project. A fresh session orients from three files and should not need anything else to choose its next read.

## Reading order

1. `INDEX.md`, this page: the layout, the vocabularies and the rules for paths.
2. `FINDINGS.md`: one row per claim, with its status, commit, evidence and report.
3. `SESSIONS.md`: which session has claimed which direction right now, and what it must not touch.
4. `DIRECTIONS.md`: every direction, its status and a one-sentence summary.
5. The direction's own `README.md` handoff, then its reports. Read raw evidence only when a claim needs checking.

`INDEX.md`, `FINDINGS.md` and `SESSIONS.md` together stay under 30,000 tokens, counted as bytes divided by four.

## Layout

- `directions.json` is the direction registry. The research-session tool renders it into `DIRECTIONS.md` and `SESSIONS.md`; never edit those two files by hand.
- `ledger.json` at this level is the global spend roll-up, written by `research-session ledger-rollup` from each direction's `ledger.json`.
- `_templates/` holds the starting files for a new direction: `START.md`, `proposal.md`, `WORKLOG.md`, `RESUME.md`, `state.json`, `worklog.json`, `ledger.json`, `handback.md` and `audit.md`.
- Each direction has a directory `<slug>/` with a `README.md` handoff of two pages at most, `START.md`, a frozen `spec.md`, `WORKLOG.md`, `worklog.json`, `RESUME.md`, `state.json`, `ledger.json`, and the subdirectories `reports/`, `reviews/`, `handbacks/`, `history/` and `issues/`.
- A paused direction keeps only what it already has plus a `ledger.json`. The other files are created from `_templates/` with `research-session init` when a session resumes it.
- `component-analysis/`, `format-control/`, `mechanism-analysis/` and `mechanism-datasets/` each hold a `scratch-copy/` folder: byte-identical copies of the Markdown from the direction's old `.scratch/` directory, with a `provenance.json` that names each file's archive path. The working directories themselves move to `outputs/_studies/<slug>/scratch/` in wave B of the autoresearch-workflow setup, after the merge, and `.scratch/<slug>` becomes a symlink to them.
- `eval5-grader-fixes` has no directory here yet. Its files stay in the Alignment checkout under `.scratch/` until the user confirms that the live Codex session is finished; its copy then arrives with wave D.
- `held-out.md` is the held-out instance policy, and `held_out.json` is its registry. Research sessions never score held-out ids. A paper-gating run that does records its provenance path in `scored_runs`, which spends the set for that claim.

## Paths

- Paths in `FINDINGS.md`, `directions.json` and the ledgers are relative to the Deception-Circuit repository root.
- A path that starts with `../` points into the parent Alignment checkout, for example `../.scratch/sdr-cue-probe/analysis.md`. Such files exist only on the local filesystem and are not in this repository.
- Paths under `outputs/_analyses/` and `outputs/_studies/` are ignored by git and also exist only on the local filesystem.
- Entries in a direction's `legacy_scratch` and `do_not_touch` lists that start with `.scratch/` are relative to the Alignment checkout, as in the spec's example.

## Finding ids

A finding id is `F-<short>-NNN`, and an id is never reused.

| Short | Direction |
|---|---|
| sdr | sdr-mechanism |
| sel | selective-deception |
| mech | mechanism-analysis |
| mds | mechanism-datasets |
| comp | component-analysis |
| fmt | format-control |
| ev5 | eval5-grader-fixes |
| arw | autoresearch-workflow |
| rte | instructed-route |
| nrn | neuron-partition |

A new direction picks a short name of two to five lower-case letters and adds it to this table.

## Status vocabularies

- **Finding status:** `proposed`, `executed`, `reviewed`, `verified`, `replicated`, `refuted`, `superseded` or `paused`. A `verified` row needs a provenance file in its evidence that names a commit. A `replicated` row also needs two such runs with distinct seeds. A paper headline needs `replicated`.
- **Commit:** the short SHA of the code that produced the result, or `pre-manifest` when no provenance file exists. A `pre-manifest` row is at most `reviewed`.
- **Direction status:** `proposed`, `open`, `claimed`, `active`, `paused`, `done` or `abandoned`. A closed direction whose status is uncertain is `paused`, not `done`. Each row names the file that justifies its status in `status_source`.
- **Reservation status in a ledger:** `PLANNED`, `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMEOUT` or `OUT_OF_MEMORY`.

## Ownership and claims

- Only an orchestrator claims a direction, with `research-session claim`, and commits the claim on main before branching. A synthesis session may only add `proposed` rows.
- A live Codex session owns the `sdr-*` work, `selective-deception` and `eval5-grader-fixes` until the user says it has finished. Do not edit their `.scratch/` directories or their outputs.
- The research-session tool is the only writer of `state.json`, `worklog.json`, `WORKLOG.md`, every `ledger.json`, `DIRECTIONS.md` and `SESSIONS.md`.

## Protocols

The session protocols live in the Alignment checkout under `docs/agents/`:

- `research-session.md` describes how a research session starts, records its work, pauses at checkpoints and hands back.
- `synthesis-session.md` describes how a synthesis session reads the recorded state, proposes the next research sessions and writes their starting prompts.
- `session-audit.md` gives the rubric for deciding whether a finished or paused session's outputs can be trusted.

The command reference is `research-session --help`.
