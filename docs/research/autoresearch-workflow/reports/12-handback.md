# Hand-back 12: wrap-up (findings, registry, memory note, merge checklist)

Agent: ticket-implementer, Opus. Ticket: `docs/research/autoresearch-workflow/issues/12-wrap-up.md`. Status: resolved,
with two acceptance boxes left open (the wave C dry run keeps one real conflict, and the file-list diff is not
exact; see What is NOT done).

No git command was run, nothing was applied, no Slurm job or paid API call was made, and no session was launched.
Usage at 5:18 pm EDT: all-models 19%, Fable 23%.

**Addendum at 5:29 pm EDT, after the 4:26 pm (local clock) wave A apply.** The orchestrator's message on Comments 20
and 21 names "handed-back" as a terminal word, and the staged hook did not accept it. The staged `hooks.py` now
accepts it, and its block reason lists it. The staged test file has a matching vocabulary case and reason text. The
staged suite gives 273 passed on both interpreters. Ops 12#1 and 12#2 now expect the installed hashes 03a0f2d636e0
and 012ac2d37961, which are the files the 4:26 pm run wrote. A dry run of ticket 12 wave A shows 12#1 and 12#2 WOULD
APPLY and the other 16 SKIP. The orchestrator re-runs `--wave A --only 12`, then the installed tests and the smoke
test. The pre-change op file is at `/u/swong2/.claude/jobs/b2cb53cd/tmp/12/12-wrap-up.before-handed-back.json`. The
durable copy `/u/swong2/.claude/research-session/staging-20261031/` predates this change. Three of its files need a
fresh copy from S: `ops/12-wrap-up.json`, the staged `hooks.py`, and the staged hooks test file.
Usage at 5:29 pm EDT: all-models 20%, Fable 23%.

## What changed

### Committed by the orchestrator from W

All paths are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/`.

- `autoresearch-workflow/tools/apply_staged.py`: the `absent` guard of spec 7; a dry run that carries planned state
  forward (Comment 14); the EXDEV fallback in `move` and in rollback (Comment 2); a skip for a `write` that this same
  op applied in an earlier journaled run when later ops have changed the file; and two fixes found by new tests: a
  move whose source path is now a link, either to its destination or to the target a staged symlink op names for that
  path, counts as moved, so a re-run of wave B no longer reports CONFLICT for any of its five moves.
- `autoresearch-workflow/tools/test_apply_staged.py`: 15 new tests (48 in all).
- `autoresearch-workflow/tools/migrate_scratch.py`: Markdown inside a dot-directory is never copied (Comment 16).
- `autoresearch-workflow/tools/test_migrate_scratch.py`: one new test (18 in all).
- `component-analysis/scratch-copy/component-analysis/provenance.json`: the `.pytest_cache/README.md` row removed and
  counted as archive-only (files 4 to 5, bytes 232 to 534).
- `component-analysis/scratch-copy/component-analysis/.pytest_cache/README.md`: deleted, with its empty folder.
- `FINDINGS.md`: rows F-arw-001 to F-arw-008.
- `INDEX.md`: the stale Layout bullet rewritten, the held-out bullet updated, short name `arw` added (Comment 15).
- `directions.json`: the autoresearch-workflow row's `status_source` now names its README (status stays `active`), and
  10 `proposed` follow-up rows were added. `DIRECTIONS.md` and `SESSIONS.md` were re-rendered by `research-session render`.
- `autoresearch-workflow/README.md` (the handoff), `autoresearch-workflow/merge-checklist.md`,
  `autoresearch-workflow/agent-brief.md` (the waiting rule of Comment 20), this file, and the ticket file.

### Staged in S, op file `S/ops/12-wrap-up.json`, wave A (18 ops)

S is `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging`.

1. `/projects/beto/swong2/Alignment/.agents/research_session/hooks.py`, whole-file write, `expect_sha256` e255196b8453
   (the installed file, re-hashed just before staging; 03a0f2d636e0 since the addendum). H-i now also blocks once when the newest changed hand-back has
   no `Status:` line, a placeholder (pending, to be filled, TBD, in progress) or no terminal word (Comment 21).
2. `/projects/beto/swong2/Alignment/.agents/tests/test_research_session_hooks.py`, whole-file write, `expect_sha256`
   3205e28eb977 (012ac2d37961 since the addendum): four new tests, and the existing no-block test now writes a Status line.
3. `.../.agents/tests/fixtures/hooks/claude_subagent_stop_handback_pending.json`, new, `expect_sha256: "absent"`.
4. `/projects/beto/swong2/Alignment/.agents/memory/autoresearch-workflow.md`, new, `expect_sha256: "absent"`, lint.
5. `MEMORY.md`, one `append_text` of exactly one line, lint.
6. `MEMORY.md`, one `replace_text` on the usage line, lint (Comment 5). It keeps ticket 01's text intact, so 01#15
   stays a SKIP.
7. to 10. `usage-limit-policy.md`, four `replace_text` ops, lint: the 76% self-hold under the 80% cap, and the R40
   wording for a missing `five_hour` key (Comment 5).
11. to 14. `/projects/beto/swong2/Alignment/docs/agents/research-session.md`, four `replace_text` ops, lint: the R39
    commands `init`, `worklog-set` and `ledger` (Comment 6), the waiting rule and the idle-notice rule (Comments 20
    and 22), and the R40 cap wording (Comment 5).
15. `/projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md`, `replace_text` with `expect_sha256`
    9963ba25baf4, lint: a "Waiting on runs" section (Comment 20).
16. `/projects/beto/swong2/Alignment/.claude/CLAUDE.md`, `replace_text`, lint: the "Codex lint rule" bullet removed;
    the `autoresearch-workflow-codex-hooks` block stays (Comment 3).
17. and 18. `README.md` in `A/project_context/reports/` and in
    `A/project_context/research_notes/Deception specificity and shared circuits/`, new, `absent`, lint (Comment 2).

### Staged in S, op file `S/ops/12d-deferred-memory.json`, wave D (32 ops)

Written by `S/scripts/restage_12d.py`, which the orchestrator re-runs right before wave D (merge checklist step 8).
The `expect_sha256` values and MEMORY.md line texts will likely be stale by the time the user confirms the Codex
session is finished; the script re-reads the files and rewrites the op file.

- Byte-identical copies of `sdr-mechanism-review.md` and `selective-deception-execution.md` to
  `DC/outputs/_studies/sdr-mechanism/memory-log-20261031.md` and `DC/outputs/_studies/selective-deception/memory-log-20261031.md`.
- Both notes rewritten as pointers of 14 lines each, `expect_sha256` 158e0621dbec and c76241a68ad0, lint.
- `MEMORY.md` lines 27 and 29 rewritten in full sentences, `replace_text` with the current line as `old_text`, lint.
- Two `mkdir` and 21 `move` ops taking the duplicates to `DC/outputs/_studies/project-context-dedupe-20261031/`.
- The two folder READMEs rewritten to say the files moved (sources under `S/tree12d/`, because `S/tree/` holds the
  wave A versions).
- The selective-deception README sentence about the originals, on the DC main path, `replace_text`, lint.

### Staged in S, op file `S/ops/12c-bridge-sentence.json`, wave C (1 op)

`replace_text` on `/projects/beto/swong2/Alignment/.agents/claude_codex_sync.py`: ticket 01's R11 sentence as a text
op. 01#21 is a whole-file write that predates the hook-trust code now in the live bridge; its `expect_sha256` refuses
it, and its staged copy would drop that code. Not asked for; see Open questions.

### Other changes in S

- Shared staged copies updated to the final text, so earlier unguarded writes skip after the apply (the R18 `cli.py`
  practice): `tree/.../research_session/hooks.py` and `tree/.../tests/test_research_session_hooks.py` (06#1, 06#3),
  and `tree/.../docs/agents/research-session.md` (08#1). The live `research-session.md` had been changed after 08#1's
  journaled apply, so no journal records its current copy, and a re-run would otherwise revert ticket 12's four edits.
- `S/records/10-migration-b.json`: the `.pytest_cache/README.md` copy entry removed, so `verify` stays consistent. The
  wave B ops were not re-planned.

### Scratch files in T

`/u/swong2/.claude/jobs/b2cb53cd/tmp/12/`: `stage_12.py`, `stage_12c.py`, `simulate_12.py` (applies op files to copies
under `T/12/sim`), `dryrun_all.py`, `check_layered.py`, `update_rsd_tree.py`, `update_directions.py`,
`fill_index_size.py`, `fix_pytest_cache_copy.py`, `build_lists.py`, `check_checklist.py`, `extract_handbacks.py`,
`checklist-head.md`, and the before copies `directions.before.json` and `10-migration-b.records.before.json`.

## How verified

### Tool tests, both interpreters

```
/u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider F/tools/test_migrate_scratch.py F/tools/test_apply_staged.py
66 passed in 1.42s
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider (same two files)
66 passed in 1.96s
```

The baseline before any change was 50 on both. The first 14 new apply-tool tests failed first (10 failures, with the
other 4 passing for the wrong reason), and the dot-directory test failed first. The review found that ticket 10's
autoresearch-workflow move (its source becomes a link to the feature folder, not to the stash) would still report
CONFLICT on a re-run; the 15th test reproduced that before the fix. New coverage: the chained mkdir, move and
symlink dry run; the overlay leaves a real run unchanged and a re-run after apply skips all three; a planned write
fills its path; EXDEV for a tree with an inner symlink and an empty folder, with rollback; a file move across
devices; a failed verification keeps the source; EACCES is not copied; `absent` creates, then skips, and conflicts on
an existing file; the journal skip for guarded and unguarded writes, a rolled-back write applies again, a changed
staged source is not skipped, and another op's journal entry does not count.

### Staged RS suite, both interpreters

```
/u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider S/tree/projects/beto/swong2/Alignment/.agents/tests
273 passed, 31 subtests passed in 7.97s
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider S/tree/.../.agents/tests
273 passed in 9.62s
```

Baseline 269 on both. The new SubagentStop tests failed first (14 failures counting subtests).

### Ticket 12's ops applied to copies

```
python3.9 -B T/12/simulate_12.py F/tools S 12-wrap-up.json A
first run: exit 0, {'APPLY': 18}
second run: exit 0, {'SKIP': 18}
lint of 8 final Markdown files: exit 1
.../MEMORY.md:27: long-token ...   .../MEMORY.md:29: join ...
python3.9 -B T/12/simulate_12.py F/tools S 12d-deferred-memory.json D
first run: exit 0, {'APPLY': 32}
second run: exit 0, {'SKIP': 32}
lint of 6 final Markdown files: exit 0
python3.9 -B T/12/simulate_12.py F/tools S 01-hygiene.json,07-profiles.json,12c-bridge-sentence.json C
[01#21] ... CONFLICT: destination changed since staging (sha256 differs)
mgnp and base: pytest sim/.../.agents/tests/test_claude_codex_sync.py -> 8 passed (each)
```

After wave A the only lint failures left are MEMORY.md lines 27 and 29, which wave D rewrites; after wave D every
linted file, including the whole MEMORY.md, is clean. The simulated wave C refused the two `config.toml` ops only
because the simulation passes no `--allow codex-config`.

### Earlier writes on files ticket 12 edits

```
python3.9 -B T/12/check_layered.py S
01#13 .../usage-limit-policy.md: journal match ['20261031T131907.581674']
08#1 .../research-session.md: journal match NONE
08#4 .../ticket-implementer.md: journal match ['20261031T133523.278584']
09#1 .../CLAUDE.md: journal match ['20261031T150342.443754']
```

Three of the four will skip after the apply through their journals. For 08#1 the shared staged copy now holds the
final text (above).

### Dry run over all tickets, grouped by wave (the acceptance criterion)

```
python3.9 -B T/12/dryrun_all.py F/tools S
=== wave A: exit 0; dry run, wave A: 136 op(s) selected from 198
    statuses: SKIP 115, WOULD APPLY 21
    WOULD APPLY: 06#1, 06#3, 08#1 (shared staged copies now hold ticket 12's final text), 12#1 to 12#18
=== wave H: exit 0; 4 op(s) selected; statuses: SKIP 4
=== wave B: exit 0; 20 op(s) selected; statuses: WOULD APPLY 20   (mkdir, move, symlink chains plan clean)
=== wave C: exit 1; 6 op(s) selected; statuses: CONFLICT 1, WOULD APPLY 5
    [01#21] write .../claude_codex_sync.py CONFLICT: destination changed since staging (sha256 differs)
=== wave D: exit 1; 32 op(s) selected; statuses: CONFLICT 2, WOULD APPLY 30
    [12d#30] write .../project_context/reports/README.md CONFLICT: expect_sha256 given but the destination is missing
    [12d#31] write .../research_notes/Deception specificity and shared circuits/README.md CONFLICT: (same)
=== placement: 198 ops; per wave {'A': 136, 'B': 20, 'C': 6, 'D': 32, 'H': 4}
    hook-installing ops outside wave H: none
    R28 paths outside wave D: none
```

The full per-op lines are condensed here; the script prints every non-SKIP line. Before ticket 12, wave A exited 1 on
09#1 (CLAUDE.md, applied, then changed by wave H) and wave B exited 1 with 5 ERROR and 5 CONFLICT lines. The two wave
D conflicts clear once ticket 12's wave A creates the two READMEs; the wave D simulation above seeds them and applies
all 32 ops.

### Migration verify after the cache-copy removal

```
python3.9 -B F/tools/migrate_scratch.py verify --wave B
ok      component-analysis: not applied yet; source still matches its 45 recorded entries
(format-control 97, mechanism-analysis 167, mechanism-datasets 648, autoresearch-workflow 5: all ok)
verify .../records/10-migration-b.json: 5 entries, 0 problem(s)
diff T/12/10-migration-b.records.before.json S/records/10-migration-b.json   -> only the one copy entry removed
```

### Registry, findings and renders

```
research-session validate W/docs/research/directions.json        -> valid
research-session validate W/docs/research/FINDINGS.md            -> valid
research-session findings-check --root W/docs/research           -> findings-check: 0 error(s), 0 warning(s)
research-session findings-check --root W/docs/research --repo W  -> findings-check: 0 error(s), 0 warning(s)
research-session render --root W/docs/research (twice); cmp of the two DIRECTIONS.md renders -> identical
```

The second render printed "unchanged" for both files. The round trip of `directions.json` through the RS JSON style
was byte-identical before the edit, so only the intended bytes changed.

### Index size

```
python3.9 -B T/12/fill_index_size.py W/docs/research
sizes {'INDEX.md': 5640, 'FINDINGS.md': 29303, 'SESSIONS.md': 542} total 35485 tokens 8871
```

### Lint and secret scan

```
research-session lint FINDINGS.md INDEX.md DIRECTIONS.md SESSIONS.md F/README.md F/merge-checklist.md  -> exit 0
research-session lint (staged research-session.md, both pointer notes, both wave D READMEs)            -> exit 0
research-session lint --secrets-only --summary (directions.json, the four tool files, agent-brief.md, provenance.json, DIRECTIONS.md) -> lint: 8 file(s), clean
```

The dry run also lints every op that carries `lint: true`, and none was refused. `agent-brief.md` fails the lint at
line 98 ("lane1 ... lane4"), a line I did not write; the file is outside the lint scope.

### Merge checklist paths

```
python3.9 -B T/12/check_checklist.py
blocks 28, paths 276, missing 0, planned by an op 5
01: 4 listed, 4 in hand-back      02: 2 / 2      06: 11 / 11      07: 2 / 2      08: 11 / 11
03: only checklist F/WORKLOG.md (named outside the hand-back's W subsection)
04: only checklist reports/04-handback.md (the hand-back does not list itself)
05: only hand-back T/05 helper scripts and the folder mechanism-datasets (its one file is listed)
09: only checklist the ticket file (named without a path)
10: only hand-back prose mentions: .scratch, INDEX.md, DIRECTIONS.md, apply_staged.py, provenance.json, scratch-copy
11: only hand-back RESUME.md, WORKLOG.md, state.json, worklog.json, ledger.json resolved against the wrong base
    (they belong to pilot-hooks/, where the checklist lists them) and _templates/START.md (the source of START.md)
```

Every file a hand-back names as committed is in the checklist. The script cannot match them exactly, because the
hand-backs name files in prose with relative shorthand; each difference above is one of those.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **Acceptance box 5 is not ticked.** The all-ticket dry run exits 1 for wave C and wave D. Wave C's 01#21 is a real
  conflict: the bridge changed after ticket 01 staged it. I did not edit ticket 01's op file; `12c#1` carries the
  sentence instead, and 01#21 stays a CONFLICT forever. Wave D's two conflicts are expected until ticket 12's wave A
  is applied. The rest of the criterion holds: the summary is grouped by wave, and no hook op sits outside wave H and
  no R28 path outside wave D.
- **Acceptance box 2 is not ticked.** Every listed path exists, and every file a hand-back names as committed is
  listed, but the script diff is not empty, because the hand-backs name files in prose shorthand (classified above).
- **The worklog import** was already done by the orchestrator, so it is recorded as done, not listed.
- **Nothing is applied.** Waves A, C and D of tickets 12, 12c and 12d wait for the orchestrator and the user.
- **The selective-deception README sentence** is staged against the DC main path, so wave D must run after the merge.

## Open questions

1. **Bridge sentence op `12c#1` (scope added).** Ticket 01's whole-file write would erase the live bridge's hook-trust
   code if re-staged naively. Default: apply `12c#1` in wave C and treat the 01#21 CONFLICT as expected.
2. **Journal-aware skip in the apply tool (scope added).** Without it, 09#1 and every earlier write on a file a later
   op edits report CONFLICT or, when unguarded, revert the later edit on a re-run. Default: keep it.
3. **Shared staged copies of 06#1, 06#3 and 08#1 now hold ticket 12's text.** An all-ticket wave A dry run therefore
   shows them as WOULD APPLY until ticket 12 is applied. Default: apply with `--only 12`, as the checklist says.
4. **Worktree lifetime.** The wave B records name the Markdown copies by their worktree paths. Default: keep the
   worktree until wave B's verify passes (checklist step 5).
5. **Symlinks at the old project_context paths.** The wave D moves break the path binding of the frozen SDR manifests,
   as Comment 2 accepts. A symlink from each old path to its canonical Deception-Circuit copy would keep those readers
   working. Default: no symlinks, as ruled.
6. **FINDINGS commit column.** All eight rows use `pre-manifest`, which INDEX.md prescribes when no provenance file
   exists, so no short SHA needs filling. Default: leave them.
7. **Status vocabulary for H-i.** `hooks.py` had no hand-back status words, so I defined them: resolved, blocked, held,
   done, failed and abandoned pass; "claimed" alone does not. Default: keep them.
8. **12#1 changes live hook behaviour the moment it applies.** The hooks already run from the installed path, and this
   session is registered. Hand-backs 01 to 11 have no `Status:` line (they open with "Implementer: Opus, ticket
   NN"), so a resumed earlier agent that touches its hand-back and stops is blocked once with the new reason. That is
   harmless but visible. Default: apply as staged and add a Status line when resuming such an agent.
9. **Spec 5.1, row H-i, is now stale.** It says "block once when no hand-back file changed"; Comment 21 extends that
   to the Status check. The spec is the orchestrator's file. Default: fold Comment 21 into the H-i row as a ruling.

## Proposed WORKLOG entry (for the orchestrator)

Kind `handback`, title "Wrap-up ticket handed back", body:

> The wrap-up ticket is done. Eight findings rows, ten proposed follow-up directions, the handoff and the merge
> checklist are in the feature folder. The apply tool now plans chained migrations cleanly, moves across file
> systems, and skips writes it applied before. Hand-backs with a placeholder status are now blocked once. One staged
> Codex op is stale and is replaced by a text op.

## Proposed process-incident row (for the orchestrator)

Kind `incident`, with `--what "The planning agent ran one read-only git command while drafting the plan."`,
`--effect "None: the command changed nothing, but agents may not run git at all."`, and `--fix "The agent brief
forbids every git subcommand for agents, and the orchestrator alone runs git."`.
