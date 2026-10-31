# 05 — Index and registry seeding

**Status:** resolved
**Type:** task
**Blocked by:** 03 (validators and renders)
**Wave:** none for the index files (in W); A for nothing.
**Estimated size:** reading about 130k tokens (the three handoff READMEs, `mechanism-analysis/synthesis.md`, the 11
SDR reports and 10 selective-deception reports at about 240 KB together, the unique
`A/project_context/reports/Deception specificity and shared circuits.md`, the legacy ledgers' key names, the memory
notes listed below), writing about 40k tokens. Read each report's summary, verdict and claims sections first, and go
deeper only where a claim's evidence path is unclear.
**Hand-back:** `F/reports/05-handback.md`

## What to do

Create the index layer of spec §3 under `W/docs/research/`, seeded from what exists today, so a synthesis agent can
orient in under 30k tokens (goal 1).

## Facts to build on

- Handoffs: `W/docs/research/sdr-mechanism/README.md` (paused 2026-10-31; latest result is the shared-component
  composition report), `W/docs/research/selective-deception/README.md` (paused 2026-10-31; budget 38.35 of 40 GPU-h
  reserved, 45,167 s actual, $4.18 known API cost plus $0.66 reserve), `W/docs/research/mechanism-analysis/synthesis.md`
  (claims table with files for every number).
- Directions to seed (R15), with suggested status and its source; confirm each against the source before writing:
  `sdr-mechanism` paused (its README; `legacy_scratch` lists `sdr-assay-diagnosis`, `sdr-behavior-identification`,
  `sdr-clause-choice`, `sdr-cue-circuits`, `sdr-cue-followup`, `sdr-cue-probe`, `sdr-native-controls`,
  `sdr-routing-pilot`, `sdr-routing-validation`, `sdr-shared-composition`, `sdr-session-wrapup`);
  `selective-deception` paused (its README); `mechanism-analysis` done (memory `mechanism-analysis-plan.md`: merged
  2026-10-28); `mechanism-datasets` paused (memory `mechanism-datasets-plan.md`: training awaits the user's go);
  `component-analysis` done (memory `main-merge-261018.md`); `format-control` done (memory
  `format-control-run-state.md`: closed 2026-10-19); `eval5-grader-fixes` open (memory `eval5-grader-fixes-pending.md`);
  `autoresearch-workflow` active, `claimed_by: "claude-b2cb53cd"` (R29), with `worktree` set to W and `branch`
  `autoresearch-workflow`. Its `state.json` does not exist yet; the render must show "no state yet" (ticket 03).
- The live Codex session owns the `sdr-*`, `selective-deception` and `eval5-grader-fixes` work (R28). Seed their rows
  from what is on disk, but do not edit anything in their directories.
- Legacy ledgers: `A/.scratch/mechanism-analysis/compute-ledger.json`,
  `DC/outputs/_studies/selective-deception/study/compute-ledger.json`, `A/.scratch/mechanism-datasets/compute-ledger.json`,
  and prose `ledger.md` files in the `sdr-*` directories.
- No run output older than this feature has `run_manifest.json`; some SDR analysis outputs have a legacy
  `manifest.json` with `git_commit` (lane 3 P10). Use R2 and R16 when choosing a status.

## Scope

In W:
- `W/docs/research/INDEX.md`: one page; reading order (INDEX, FINDINGS, SESSIONS, DIRECTIONS, then per-direction
  README), the layout of spec §3, the status vocabularies, and pointers to the protocols in `A/docs/agents/`.
- `W/docs/research/FINDINGS.md`: one header paragraph, then the table of §4.1. Seed about 30-60 rows from the
  sources above. Each claim is one sentence and states the question it answers. Statuses follow R16 and R17.
- `W/docs/research/directions.json` with the rows above, validated.
- `W/docs/research/DIRECTIONS.md` and `SESSIONS.md`, rendered by the staged RS (`cli.py render --root W/docs/research`).
- `W/docs/research/<slug>/ledger.json` for `selective-deception`, `mechanism-analysis` and `mechanism-datasets`
  converted from their JSON ledgers (`converted_from` set), and for `sdr-mechanism` with totals from the prose
  ledgers where they state them, `reservations: []`, and a note of what could not be converted.
- `W/docs/research/ledger.json`, rendered by `cli.py ledger-rollup`.

## Acceptance criteria

- [x] `cli.py validate` passes on `FINDINGS.md`, `directions.json`, every new `ledger.json` and `held_out.json` if
      ticket 04 has landed; output pasted.
- [x] `cli.py render` and `ledger-rollup` run twice with no byte change on the second run.
- [x] Every FINDINGS row's evidence and report paths exist in W or DC (a script in T checks this; output pasted).
      Paths that exist only on the local filesystem (ignored outputs) are allowed and listed.
- [x] No `verified` or `replicated` row lacks a provenance file naming a commit (`findings-check` output pasted).
- [x] Every `directions.json` row has a `status_source` that exists.
- [x] `INDEX.md`, `FINDINGS.md`, `SESSIONS.md` and `DIRECTIONS.md` pass the lint, including the secret scan.
- [x] The size of `INDEX.md + FINDINGS.md + SESSIONS.md` divided by 4 is under 30,000; the byte counts are pasted.
- [x] The hand-back lists any finding the agent saw in the sources but did not seed, with the reason.

## Verification

Use the staged RS by absolute path with base python3.9. Do not edit the existing handoff READMEs or reports.

## Comments

**2026-10-31, implementer (Opus, ticket 05): resolved.** The full record is in `reports/05-handback.md`.

Files for the orchestrator to commit from W, all under `docs/research/`:

- `INDEX.md`, `FINDINGS.md` (51 rows), `directions.json` (8 rows), `DIRECTIONS.md`, `SESSIONS.md` and `ledger.json`.
- `sdr-mechanism/ledger.json`, `selective-deception/ledger.json`, `mechanism-analysis/ledger.json` and the new `mechanism-datasets/ledger.json`.
- `autoresearch-workflow/reports/05-handback.md` and this ticket.

Nothing is staged in S, and there is no op file. Helper scripts are in `/u/swong2/.claude/jobs/b2cb53cd/tmp/05/`.

Results on base python3.9: `validate` passes on every file, with two expected warnings on the sdr-mechanism ledger, whose totals have no reservation rows. `findings-check` reports 0 errors and 0 warnings. The second `render` and `ledger-rollup` runs leave all three files unchanged by hash. All 51 rows and all 8 status sources resolve, and none is missing. The lint and secret scan pass on the four Markdown files. INDEX, FINDINGS and SESSIONS total 30,817 bytes, about 7,704 tokens. No test suite applies to this ticket. `held_out.json` does not exist yet.

Defect for ticket 03: `ledger-rollup` counts `_templates/ledger.json` as a direction named `example-direction`. The totals are unaffected because that row is all zeros.
