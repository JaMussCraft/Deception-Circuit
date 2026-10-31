# 03 — RS records: registry, renders, worklog, jobs, ledger, init, findings-check

**Status:** claimed
**Type:** task
**Blocked by:** 02 (shared `cli.py` and `state.py`)
**Wave:** A
**Estimated size:** reading about 75k tokens (spec §4 including §4.4 and §4.8, §5.3, §5.4, §5.6, §6.3, §6.5,
R15-R17, R22-R23, R29, R33, R39; lane 4 §1 template and checkpoint block; lane 3 §4 schemas; `F/WORKLOG.md`; the
templates in `W/docs/research/_templates/`), writing about 145k. Total about 220k, inside the R20 budget of 250k.
If the projection passes 250k after the worklog work, stop before `init` and `ledger`, hand back, and name the rest
`03b-ledger-and-init` in the hand-back so the orchestrator can spawn it.
**Hand-back:** `F/reports/03-handback.md`

## What to do

Implement the RS commands that own the research records: schema validation, the rendered views, claims, the
structured worklog writer with the checkpoint block, the head-field setter, direction setup from the templates, the
spend ledger, the Slurm job list, and the findings gates. Every file RS owns must be creatable and changeable through
a command, because the gate refuses hand edits of `state.json` and `worklog.json` (R39).

## Facts to build on

- Templates written by ticket 08 in `W/docs/research/_templates/`: `WORKLOG.md`, `worklog.json`, `state.json`,
  `ledger.json`, `RESUME.md`, `START.md`, `handback.md`, `proposal.md`, `audit.md`. The rendered WORKLOG head must
  match the `_templates/WORKLOG.md` head row for row: State, Directions, Started / last updated, Orchestrator
  auto-compactions, Weekly usage all models, Weekly usage Fable, Review checkpoints, GPU budget, OpenRouter credit,
  Open needs from you, Transcripts; then Right now, Terms, Needs from you, Findings register, Process incidents. Its
  HTML comment block is template guidance and is not rendered into a direction's WORKLOG.
- The worklog in use is `F/WORKLOG.md`. Its head predates the template (one combined usage row, no Transcripts row);
  `--import` maps it onto the template rows and reports the difference instead of refusing on it.
- Checkpoint block: lane 4 §1 and the `_templates/WORKLOG.md` example.
- Two legacy ledger styles for later conversion: `A/.scratch/mechanism-analysis/compute-ledger.json` and
  `DC/outputs/_studies/selective-deception/study/compute-ledger.json` (lane 3 P4). Read their key names only.
- Times: America/New_York computed with `zoneinfo` (available on Python 3.9). DST ends 1 November 2026 (R22).
- Existing provenance field names: `W/scripts/sdr_routing_pilot.py:392-403`.

## Scope

Staged in S (relative to `S/tree/projects/beto/swong2/Alignment/.agents/`):
- `research_session/registry.py`: validators for `directions.json` (§4.2, `claimed_by` as `<tool>-<8 hex>` per
  R29), ledger (§4.4), `state.json` (§4.5), `worklog.json` (§4.8),
  the FINDINGS table (§4.1) and `held_out.json` (§6.4); `render` for `DIRECTIONS.md` and `SESSIONS.md` (§4.3);
  `ledger-rollup`; `claim <slug>` and `release <slug> --status` (R23; they edit `directions.json` under a `--root`
  that defaults to `DC/docs/research`).
- `research_session/worklog.py`: `worklog-append` with every kind and option of spec §5.6, keeping the structured
  fields in `<dir>/worklog.json` (spec §4.8, R33). On every call it regenerates everything above `## Log` in the
  `_templates/WORKLOG.md` layout (the header rows listed under Facts, with compactions, both weekly usage rows and
  checkpoints from `state.json`, and the GPU and OpenRouter rows from `ledger.json` totals and caps; then Right now,
  Terms, Needs from you, Findings register and Process incidents) and leaves everything after `## Log` byte-identical
  except for the appended entry. The head render is one function shared by every command below that changes a
  direction's records, so `worklog-set` and `ledger` re-render the head too. `finding` allocates the next F#, adds a register row and logs an entry; `need` allocates the next N#
  with its default-if-no-answer clause; `need-resolved --id N# --answer` renders that need struck through with the
  answer and time and logs an entry; `incident` allocates the next P#, adds a row and logs an entry; `--checkpoint N`
  writes the checkpoint block of lane 4 §1 and sets that freeze to `recorded`. It updates `last_worklog_entry_at`
  and lints its whole output before an atomic replace. Times use `%-I:%M %p %Z` in America/New_York with lower-case
  `am` and `pm`; day headings are `### <Weekday> <D> <Month> <YYYY>` (match `F/WORKLOG.md`).
- An importer, `worklog-append <dir> --import`, that builds `worklog.json` from an existing hand-written WORKLOG.md in
  the lane 4 format (used once on `F/WORKLOG.md` by the orchestrator, then RS owns it). It regenerates the head in
  the template layout and prints a diff against the old head. It refuses only if a findings, needs or incidents row
  is lost or any byte after `## Log` changes.
- `worklog-set <dir> <field> <value>` (spec §5.6, R39). Text fields: `title`, `state`, `right-now`, `transcripts`.
  List fields take a JSON value and are validated: `directions` as `[{"name", "state"}]`, `terms` as
  `[{"term", "meaning"}]`. Cap fields `gpu-cap` (reserved GPU-hours), `max-gpu-jobs` and `api-cap` (USD) write
  `ledger.json` `caps`. `state` is the base value (Running, Blocked: needs you, Closed); the render shows a freeze or
  cap pause from `state.json` over it. The `budgets` strings in `worklog.json` are rewritten from `ledger.json` on
  every write and never set directly. Text values pass the lint before anything is written.
- `research_session/setup.py`: `init <slug> [--from-start START.md] [--gpu-cap H] [--max-gpu-jobs K] [--api-cap USD]
  [--root DIR]` (root defaults to `DC/docs/research`). It creates `<root>/<slug>/` with `state.json`, `worklog.json`
  and `ledger.json` from the templates with the slug filled in and example rows removed, `WORKLOG.md` rendered from
  them with a first Log entry "Direction created", `RESUME.md` from the template, a `README.md` stub (title and one
  line pointing to START.md), and `START.md` (the given file copied byte for byte, else the template). The title is
  the given START.md's first heading. If the slug is not in `directions.json` it adds a `proposed` row; it never
  claims. It refuses when the directory already holds any of these files, naming them, and `--missing-only` creates
  just the absent ones.
- `research_session/ledger.py`: `ledger add <dir> --cluster --account --partition --gpus --minutes --job-id
  [--commit SHA] [--output-dir P]` appends a reservation with `status: PENDING` and `reserved_gpu_hours = gpus ×
  minutes / 60`, and refuses when the new reserved total exceeds `caps.reserved_gpu_hours` or the count of `PENDING`
  plus `RUNNING` reservations would exceed `caps.max_concurrent_gpu_jobs` (a cap of 0 means no GPU work is allowed).
  `ledger reconcile <dir> <job-id> --actual-seconds S --status STATUS` sets the final fields and refuses an unknown
  job id or status. `ledger api <dir> --usd X [--provider openrouter] [--calls N] [--reserve]` adds to the day's
  `api_calls` row and to `api_usd_known` (or to `api_usd_reserve` with `--reserve`). Spend already incurred is
  always recorded: past `caps.paid_api_usd` it records, prints a cap warning and exits 3, so the orchestrator stops
  paid work and opens a need. Every subcommand recomputes `totals` from the rows, writes atomically under the state lock,
  and re-renders the WORKLOG head. RS code never calls `sbatch` or `sacct`; the caller passes the numbers.
- `research_session/jobs.py`: `job add|update|list` on `state.json` `jobs`, printing the waiter command
  (an `until sacct ...; do sleep 300; done` loop with an explicit timeout of at most 60 minutes).
- `findings-check [--paper DRAFT]` implementing §6.5 and the grader check of §6.3; it accepts legacy `manifest.json`
  with `git_commit` as a warning (R2).
- `validate <path>...` dispatching on file name.
- Tests: `tests/test_research_session_registry.py`, `test_research_session_worklog.py`,
  `test_research_session_findings.py`, `test_research_session_ledger.py`, `test_research_session_init.py`, with
  fixture trees built in temporary directories (copy the real `_templates/` into T; never write to W).
- `S/ops/03-rs-records.json`.

## Acceptance criteria

- [ ] Validators reject each malformed case they guard (bad status, missing field, unknown key, duplicate F-id,
      a `verified` row with no provenance, `claimed_by` in the wrong format) and accept the examples in spec §4.
- [ ] `render` is byte-stable: a second run over unchanged input changes nothing (test asserts equal bytes).
- [ ] `render` handles a claimed direction whose `state.json` does not exist yet (the `autoresearch-workflow` row will
      be exactly that in ticket 05): the SESSIONS row shows "no state yet" instead of failing.
- [ ] A test asserts `zoneinfo.ZoneInfo("America/New_York")` loads (the planner confirmed it does on both
      interpreters on 2026-10-31).
- [ ] `claim` refuses a direction already `claimed` or `active` by another session and refuses an unknown slug.
- [ ] `worklog-append` tests: an entry on a new day adds the `### <Weekday> <D> <Month> <YYYY>` heading; the head
      regeneration leaves everything after `## Log` byte-identical apart from the appended entry; `finding`, `need`
      and `incident` allocate F1, N1 and P1 and then F2, N2 and P2; `need-resolved` strikes through the right need with
      its answer and time and refuses an unknown or already-resolved id; the checkpoint block contains both usage rows
      and sets freeze `recorded`; a glued `--body` is refused with the lint message; times render as `8:05 am EDT`
      before 2 a.m. on 1 November 2026 and `8:05 am EST` after (fixed clocks).
- [ ] Head-layout test: a direction created by `init` renders a head whose row labels, in order, equal the row labels
      of `_templates/WORKLOG.md` (parsed from the template at test time, so a template change breaks the test), with
      separate "Weekly usage, all models" and "Weekly usage, Fable" rows filled from a fixture `state.json`.
- [ ] `--import` on a copy of `F/WORKLOG.md` in T produces a `worklog.json` that validates, keeps every findings,
      needs and incidents row and every Log byte, and renders the template head; the head diff is pasted.
- [ ] `worklog-set` tests: each text field round-trips and re-renders the head; `directions` and `terms` reject
      malformed JSON and unknown keys; `gpu-cap` and `api-cap` change `ledger.json` `caps` and the GPU and OpenRouter
      rows; a glued `right-now` value is refused before any write; a freeze in `state.json` shows in the State row
      over a set `Running`.
- [ ] `init` tests: a fresh slug creates all seven files, which validate, with no template example rows left; an
      absent slug gains a `proposed` row in a fixture `directions.json`; `--from-start` copies the file byte for
      byte and takes its title; a second `init` refuses and names the existing files; `--missing-only` creates only
      the absent ones; nothing is written outside `<root>/<slug>/` and `directions.json`.
- [ ] `ledger` tests: `add` computes `reserved_gpu_hours` and recomputes `totals`; `add` refuses past the reserved
      GPU-hour cap, past `max_concurrent_gpu_jobs`, and with a cap of 0; `reconcile` sets `actual_seconds` and
      `status` and refuses an unknown job id or status; `api` adds known and reserve spend to the day's row and, past
      the cap, records the spend and exits 3; the WORKLOG GPU and OpenRouter rows change after each call; two
      concurrent `add` processes lose no reservation.
- [ ] `findings-check` tests: `replicated` with one seed fails, with two distinct seeds passes; grader hash mismatch
      fails; `--paper` fails on a cited `reviewed` row and passes on `replicated` rows only.
- [ ] `job add` and `update` round-trip through `state.json`, and `list` prints the waiter commands.
- [ ] All tests pass in both envs; summaries pasted.
- [ ] `cli.py --help` lists every subcommand named in spec §5.6 that tickets 01-03 own.
- [ ] `apply_staged.py --staging S --wave A --only 03 --dry-run` output pasted.

## Verification

Both interpreters. No test reads the real `DC/docs/research`; ticket 05 runs the commands on real data.

## Comments
