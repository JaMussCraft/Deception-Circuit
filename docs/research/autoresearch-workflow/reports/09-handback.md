# 09 — Hand-back: migration A (standardize, dedupe, trim CLAUDE.md)

Implementer: Opus, ticket 09, 2026-10-31. No git command was run. Nothing was written outside W, S and T. No file in
`A/.scratch`, in `DC/outputs`, in memory or in another direction's directory was edited.

**Hand-back trigger.** The deduplication part is not staged. All 21 byte-identical duplicates are path-bound by frozen
records of the live Codex session's directions, and the `move` op cannot cross from `/projects` to `/u`. Details and
two options are under Open questions. Everything else in the ticket is done.

## What changed

### Committed by the orchestrator from W

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/mechanism-analysis/README.md`
  (new): the handoff, about one and a half pages. It gives the question, the verdict, where the claims live, what is
  closed and the useful next questions, and it links `synthesis.md`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/sdr-mechanism/history/sdr-clause-choice-RESUME-readable.md`
  (new, with the new `history/` directory): the full-sentence rewrite of the glued RESUME (R14). Its first line names
  the source path and its sha256. The archive copy is untouched. Where the glued text needed a reading, I chose these,
  so a reviewer can check them against the source:
  - "C/U" is expanded as conditional versus unconditional, from the design-direction paragraph of the source.
  - "Root" is glossed as the lead orchestrator. EOS and EOT are expanded as the end-of-sequence and end-of-turn tokens.
  - `900s1A100x4-interactive/beto4CPU64G` is split into 900 s, 1 A100, `A100x4-interactive`, `beto`, 4 CPUs and 64G.
    I did not call `A100x4-interactive` a partition or `beto` an account, because the source does not.
  - `perbatch67forwardguard +publication` is rendered as a per-batch forward guard of 67 plus publication, with no
    unit, as in the source.
  - `84accepted/attempts` is rendered as an accepted-to-attempts count of 84.
  - `32preflight+296main41accepted` is rendered as 32 preflight and 296 main rows, with 41 accepted.
  - `preserved→wiped` is written in words, as a change from "preserved" to "wiped".
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/09-handback.md`
  (this file) and the ticket file `issues/09-migration-a-standardize-dedupe-claude-md.md` (status and comments).

The two existing handoffs, `sdr-mechanism/README.md` and `selective-deception/README.md`, already pass the lint and
already match the paused-direction layout of spec §3 (a README, `reports/` and a `ledger.json`). Both directions are
owned by the live Codex session (R28), so I left them unchanged. `mechanism-analysis/` keeps its `phase*/`, `figures/`
and `jobs/` directories, because `synthesis.md` and `FINDINGS.md` cite paths inside them.

### Staged in S, ops file `S/ops/09-migration-a.json`, wave A

All four are `write` ops with `lint: true`. The three existing files carry `expect_sha256`, re-read immediately
before staging.

| Destination | Staged source under `S/tree/` | expect_sha256 |
|---|---|---|
| `/projects/beto/swong2/Alignment/.claude/CLAUDE.md` | `projects/beto/swong2/Alignment/.claude/CLAUDE.md` | `051f25ce2b7b525d20879abdf970a4d4df7a75d84187634cb7360faa97071f76` |
| `/projects/beto/swong2/Alignment/docs/agents/issue-tracker.md` | `projects/beto/swong2/Alignment/docs/agents/issue-tracker.md` | `6f38f66f9ffce2fdc26c43608d06b527f60e45c6f43003d0ea77d4e2641c9de3` |
| `/projects/beto/swong2/Alignment/project_context/prompts/README.md` | `projects/beto/swong2/Alignment/project_context/prompts/README.md` | new file |
| `/projects/beto/swong2/Alignment/project_context/prompts/autoresearch.md` | `projects/beto/swong2/Alignment/project_context/prompts/autoresearch.md` | `22827ead7230e1341b1d012d2474d10b6da41cd886bdeb92b449134bcb553c90` |

- **CLAUDE.md.** It shrinks from 190 lines to 97. The layout tree and the project-overview bullets are replaced by a
  pointer to `Deception-Circuit/docs/research/INDEX.md`. A new Deception-Circuit section says what the repository is,
  that research state lives in its `docs/research/`, that tests run on both interpreters, that the Slurm and usage
  rules live in memory and in `docs/agents/research-session.md`, and the Codex lint rule. The Agent Workflow section
  now says Opus, with `model: "opus"` on every spawn, and names the three agent definitions. The petri, bloom, notebook
  and benchmark sections are condensed to pointers at their own README files. The stale "Research Directions Under
  Consideration" section is dropped, because INDEX and DIRECTIONS now hold that state. The issue-tracker line now
  names `Deception-Circuit/docs/research/<slug>/`. The bridge block is byte-identical.
- **CLAUDE.md correction.** The old file named `project_context/research_ideas.md`, which does not exist; the real
  location is the directory `project_context/research_ideas/`, and the new text says so.
- **issue-tracker.md.** New features live in `Deception-Circuit/docs/research/<slug>/` (spec, issues, reports), and
  `.scratch/<slug>` entries are legacy, becoming symlinks to archives. The wayfinding paths moved to the same root.
- **prompts/README.md.** The prompts are historical specs; sessions start from `docs/agents/research-session.md` and
  `Deception-Circuit/docs/research/INDEX.md`. It notes that `deception_tasks_shared.md` is still cited by the
  mechanism-datasets agent brief.
- **autoresearch.md.** One dated quote line is prepended, saying the prompt is historical and that Claude subagents now
  run on Opus. The rest of the file is byte for byte the same.

### Scratch files in T

Scripts in `/u/swong2/.claude/jobs/b2cb53cd/tmp/09/`: `dup_check.py` (with its output `dup_rows.json`),
`check_numbers.py`, `build_claude_md.py` (with the head text `claude_md_head.md`), `build_autoresearch.py`,
`check_paths.py` and `sim_wave_h.py` (with its output `CLAUDE.after-wave-H.md`).

## How verified

### Duplicate candidates by sha256

The script hashes every file in `A/project_context/reports/` and `A/project_context/research_notes/` and compares it
with the same-named file in DC main's `docs/research/`. It also records the W copy, which matches for all 21.

```
/sw/external/python/anaconda3/bin/python3.9 -B T/09/dup_check.py T/09/dup_rows.json
```

| Verdict | sha256 of the project_context copy, equal to the DC main copy where EQUAL | project_context file |
|---|---|---|
| UNIQUE | `d7c96465ef314da4dac8022efc54370f7a1e4812db87cbdc91cddb11868e8cc5` | `reports/Deception specificity and shared circuits.md` |
| EQUAL | `d20b90bcd19e9852cec56584bd50cde02fc9d9f66d7a9c6766ee4756484ecfc1` | `reports/SDR circuit mechanism review.md` |
| EQUAL | `082d84cbc82349e64be167bc90dc77116de93a5fc1843bf4973058bf6b5cbdf6` | `reports/SDR cue probe findings.md` |
| EQUAL | `d737c0fa8a992b7696372cdf2d6215edea40544813d47906e8d21a70e3e488f5` | `reports/SDR cue-circuit transplant findings.md` |
| EQUAL | `a80145838ac135f662c81754e39655284e4bdfe4c2e8815dd5cfdd969fd4f8da` | `reports/SDR mechanism investigation status.md` |
| EQUAL | `5339c000fa558f5c5b73ec241a61585ccbef002f676cddaff6c004668c226370` | `reports/SDR named-consequence probe findings.md` |
| EQUAL | `adf362549a67d2fa6885e4ed32d063782aa0a3668f86d0f63c5e759c175bb0eb` | `reports/SDR native controls findings.md` |
| EQUAL | `20d2252da1ca2a75322c018f383e6b6b1f3202a1794a7d65367223fd674f0ef9` | `reports/SDR native evidence audit.md` |
| EQUAL | `1ed95044dd37e2c25ed3aec9481c9320fb03a74be45f0535c633eceb70058e78` | `reports/SDR routing pilot findings.md` |
| EQUAL | `ee78b18e667a75d1a7901bcbf213ff812b2f37c4cf19412bb63e161479cd4654` | `reports/SDR routing validation findings.md` |
| EQUAL | `c891f17b279a9e0c1422c8b10fcf8676758eac091f6e31bce5d589872dafc864` | `reports/SDR shared-component composition findings.md` |
| EQUAL | `7ac7edfb64c85a2d664225d837a75bfb08d38416fbb4cac83f2fe5238925f7f2` | `reports/SDR shared-head position findings.md` |
| EQUAL | `dfc84147cdd40092b5d3f147d683d15d5e1cb8c33165d158c21285644a2cf327` | `research_notes/Deception specificity and shared circuits/astra_review.md` |
| EQUAL | `62b727238ee843f875f53780dd15d20f4e8dab5c705995a9decf2eb039797e79` | `research_notes/Deception specificity and shared circuits/necessity_prior_art.md` |
| EQUAL | `47025b919eee54819905e59aaa8655321e66da8f2b072a12602fa92a557b6a80` | `research_notes/Deception specificity and shared circuits/next_steps.md` |
| EQUAL | `9a9ccf0ab659320dc41c2c8911792478beaed71ed5f8287bdf23c850e8738a74` | `research_notes/Deception specificity and shared circuits/project_evidence.md` |
| EQUAL | `ad1e2e1fdb691b2f0a7547493b843c9dccb17bb15bd6cf4432d2fde534e5e27c` | `research_notes/Deception specificity and shared circuits/shared_components.md` |
| EQUAL | `3be23a078be3230c9d9bb849ead78f96053ab8db4eb3bc3026639aeb11d59fa7` | `research_notes/Deception specificity and shared circuits/stage1_diagnostic.md` |
| EQUAL | `445a829a7805c100d55ff3e6e5c0cea02364e6f5cfd6fcf40af59cfa9ab92a4c` | `research_notes/Deception specificity and shared circuits/v3_extension.md` |
| EQUAL | `b56026a0471c5ea42e374f6ef3d3f1a299a94714a66ef26ea7bcbdd0fb74abac` | `research_notes/Deception specificity and shared circuits/v5_transfer.md` |
| EQUAL | `5954318bfeaf7c6dc482a072acf72e0739f3d175748f05dddc49b91f180eaf49` | `research_notes/Deception specificity and shared circuits/v6_components.md` |
| EQUAL | `821688d3f8f00c4d76b605a73006d1d9050c86e88576536433c71ad1b783ed77` | `research_notes/Deception specificity and shared circuits/v7_positions.md` |
| UNIQUE | `046073994ed1c5f602a84e25a0e9b7040f18b554e9819c653ff85776a6e720ad` | `research_notes/SDR circuit mechanism review/behavior-literature.md` |
| UNIQUE | `7f2afd894fd7ccdf8cd7f75d460ff68aa2ddf1592c8ba3effb45ffd29330eb26` | `research_notes/SDR circuit mechanism review/causal-methods.md` |
| UNIQUE | `572428e54570a8278a2ce6cbbd5ea145e7f3003492032c381b1d07fd01309da7` | `research_notes/SDR circuit mechanism review/coordination.md` |
| UNIQUE | `a15b85bd92400b7f67f276384a0e3ed221bb754ffdfd8df24aec814b7f02d437` | `research_notes/SDR circuit mechanism review/evidence-audit.md` |
| UNIQUE | `780c4533622e3f294d8cd5f55bedef724d7e5d26d0f2057a309fce04e532eda7` | `research_notes/SDR circuit mechanism review/synthesis-review.md` |

The script's last line was `candidates: 27, equal: 21`. The lane 3 claim holds: 11 SDR reports and 10 selective
deception notes are byte-identical to DC main. Besides the one unique report lane 3 named, the five files in
`research_notes/SDR circuit mechanism review/` have no copy in DC. Of those, `coordination.md` was modified on
2026-10-31 at 08:35. No `move` op was staged for any file (see Open questions).

### Who reads the duplicates by path

```
grep -rlI -e "project_context/reports" -e "project_context/research_notes" -e "research_notes/Deception specificity" A/.agents A/.claude A/docs A/.scratch A/project_context DC/docs DC/scripts DC/tests A/AGENTS.md
```

Key lines of the output:

- `A/.scratch/sdr-cue-followup/scientific-audit/check_narrative_tables.py` pins
  `project_context/reports/SDR cue-circuit transplant findings.md` and `SDR mechanism investigation status.md` to
  their sha256 values and reads `SDR shared-head position findings.md` at run time.
- `A/.scratch/sdr-cue-circuits/scientific-audit/review_report_tables.py` reads two of the reports by path.
- `A/.scratch/sdr-session-wrapup/frozen-report-manifest.json` and `report-index.json` each name the 11 SDR paths;
  `RESTART.md` there points readers at `project_context/reports/SDR*`.
- `A/.scratch/sdr-shared-composition/completion-receipt.json` and its `RESUME.md` bind the composition report's path
  and sha256.
- `DC/docs/research/sdr-mechanism/session-archive.json` records the 11 original locations.
- Memory notes `sdr-mechanism-review.md` (12 hits) and `selective-deception-execution.md` (4 hits), and
  `W/docs/research/selective-deception/README.md`, which says the originals remain in `project_context`.

### Readable RESUME keeps every number

```
/sw/external/python/anaconda3/bin/python3.9 -B T/09/check_numbers.py A/.scratch/sdr-clause-choice/RESUME.md W/docs/research/sdr-mechanism/history/sdr-clause-choice-RESUME-readable.md
distinct numbers in source: 123 (occurrences 288)
distinct numbers in rewrite (first line excluded): 123 (occurrences 294)
missing from rewrite: none
fewer occurrences in rewrite than in source: none
numbers only in rewrite: none
```

The script extracts every digit run from the raw text, code spans included, and compares counts. The rewrite's first
line, which carries the source hash, is excluded so it cannot hide a missing number. The full list of the 123 source
numbers is printed by the script.

### CLAUDE.md bridge block

```
/sw/external/python/anaconda3/bin/python3.9 -B T/09/build_claude_md.py A/.claude/CLAUDE.md T/09/claude_md_head.md S/tree/projects/beto/swong2/Alignment/.claude/CLAUDE.md
live sha256    051f25ce2b7b525d20879abdf970a4d4df7a75d84187634cb7360faa97071f76
staged sha256  203f65f2cd0d30f39b0a06d87721e81e04803695fb4a12f2470078543a924a0e
bridge block live   sha256 959a91233ec5d77b23b5afeab962ee032842c21dbd77a56cd4b3f60395c0486e 526 bytes
bridge block staged sha256 959a91233ec5d77b23b5afeab962ee032842c21dbd77a56cd4b3f60395c0486e 526 bytes
bridge block byte-identical: True
staged lines: 97
```

The block runs from `# BEGIN Claude-Codex bridge` through the newline after `# END Claude-Codex bridge`, and the
script copies it from the live file rather than retyping it.

Ticket 06 stages a wave H `text_block` (marker `autoresearch-workflow-codex-hooks`, position end) on the same file. I
applied it to the staged copy with the apply tool's own `apply_text_block`:

```
/sw/external/python/anaconda3/bin/python3.9 -B T/09/sim_wave_h.py T/09/CLAUDE.after-wave-H.md
lines after wave H: 110
bridge block still present once: True
```

The result also passes the lint. Wave A must apply before wave H, because my op carries `expect_sha256` of today's
file.

### Paths named in the new files

```
/sw/external/python/anaconda3/bin/python3.9 -B T/09/check_paths.py <staged>=<destination> ... W/docs/research/mechanism-analysis/README.md
```

Every path resolves except names the script cannot place from context:

- `INDEX.md`, `FINDINGS.md`, `DIRECTIONS.md` and `SESSIONS.md` in CLAUDE.md are listed inside the sentence about
  `Deception-Circuit/docs/research/`. All four exist in W and land on DC main with the branch merge.
- `Deception-Circuit/docs/research/INDEX.md` (CLAUDE.md, prompts README, issue-tracker) and
  `docs/research/FINDINGS.md` (mechanism-analysis README) exist in W only and land on DC main with the merge.
- `MEMORY.md` is inside the unchanged bridge block and means `.agents/memory/MEMORY.md`, which exists.
- `CONTEXT.md` and `docs/adr/` are the unchanged Domain docs line, kept verbatim. They do not exist at the Alignment
  root; they exist at the DC root.
- `START.md` in the prompts README is the generic per-direction file; the template exists at
  `docs/research/_templates/START.md` in W.
- `reports/`, `issues/`, `map.md` and `/wayfinder` in issue-tracker.md are relative to a feature directory or are a
  slash command, as in the old text.
- Templates with `<slug>`, `<effort>` or `<NN>` resolve their fixed prefix.

### Lint

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/.agents/research_session/cli.py lint S/tree/.../.claude/CLAUDE.md S/tree/.../docs/agents/issue-tracker.md S/tree/.../project_context/prompts/README.md S/tree/.../project_context/prompts/autoresearch.md W/docs/research/sdr-mechanism/history/sdr-clause-choice-RESUME-readable.md W/docs/research/mechanism-analysis/README.md
(no output, exit 0)
```

The same files also pass the staged `S/tree/.../research_session/cli.py lint`, and so do the two existing handoffs
`sdr-mechanism/README.md` and `selective-deception/README.md`. The lint includes the secret scan.

### Dry run

```
/sw/external/python/anaconda3/bin/python3.9 -B F/tools/apply_staged.py --staging S --wave A --only 09 --dry-run
dry run, wave A: 4 op(s) selected from 4
[09#1] write /projects/beto/swong2/Alignment/.claude/CLAUDE.md WOULD APPLY: +61 -154 lines
[09#2] write /projects/beto/swong2/Alignment/docs/agents/issue-tracker.md WOULD APPLY: +21 -9 lines
[09#3] write /projects/beto/swong2/Alignment/project_context/prompts/README.md WOULD APPLY: +19 -0 lines, new file
[09#4] write /projects/beto/swong2/Alignment/project_context/prompts/autoresearch.md WOULD APPLY: +2 -0 lines
```

The ticket's command line omits `--wave`, which the tool requires, so I added `--wave A`.

## Execution evidence

Not applicable: no runs. No Slurm job, GPU job or paid API call was made.

## What is NOT done

- **No dedupe `move` ops and no per-folder pointer READMEs** in `project_context/reports/` and
  `project_context/research_notes/`. A README that lists moved files would describe a move that has not happened.
- **The selective-deception README sentence** "Their originals remain in Alignment `project_context/...`" stays as it
  is. It becomes false only when the dedupe runs, and that README belongs to a live-session direction.
- **`directions.json` `status_source`** for mechanism-analysis still points at `synthesis.md`. RS owns that file, so I
  did not change it. The new `README.md` is the better status source.

## Open questions

1. **Dedupe of the 21 duplicates.** Two independent problems block the `move` ops.
   - All 21 belong to the `sdr-*` and `selective-deception` directions that R28 protects. Their paths are bound by
     frozen manifests, receipts and audit scripts in `A/.scratch/sdr-*` (listed above), by the protected memory notes,
     and by the selective-deception README. Spec §2 rules out changing a receipt or hash-pinned record, and a move
     breaks their path binding even though the bytes stay the same.
   - `project_context` is on the `/projects` Lustre file system and the backup root `/u/swong2/.claude/...` is on the
     `/u` NFS file system. `op_move` in `apply_staged.py` (line 456) is a bare `os.rename`, which fails with EXDEV
     across devices. The runner (lines 549 to 552) catches the `OSError` and reports the op as ERROR, then continues
     with the next op, so every move would fail and nothing would be moved. The dry run would not show it, because the
     dry run returns before the rename.

   Option A: stage the moves as wave D, after the user confirms the Codex session is finished, with a destination on
   the same file system, for example `DC/outputs/_studies/project-context-dedupe-20261031/`. Option B: give `op_move` a
   copy, verify and unlink fallback across devices (ticket 01's tool), then stage the moves as wave D. In both cases
   the folder READMEs ship in the same wave, and the selective-deception README sentence needs a matching edit. A
   lighter option C is to leave the duplicates in place and add only a README in each folder that names the canonical
   DC path and says the copy there is frozen.
2. **CLAUDE.md overlap with ticket 06.** The Codex lint rule appears in my Deception-Circuit section and again in
   ticket 06's wave H block. I kept mine because the ticket asks for it and wave H may be delayed. Once wave H applies,
   the orchestrator may want to drop one of the two. There is also an R18 tension: R18 says two tickets reach the same
   destination only through text ops, while ticket 09 mandates a whole-file `write` of CLAUDE.md and ticket 06 adds a
   `text_block` to it. The wave order (A before H) makes this safe, as the simulation above shows, but the orchestrator
   should rule on it.
3. **AGENTS.md regeneration.** Codex reads CLAUDE.md through the root `AGENTS.md` that the bridge generates. After
   wave A, the next `codex` launch or `python3 .agents/claude_codex_sync.py --apply` regenerates it. I did not run the
   bridge.
