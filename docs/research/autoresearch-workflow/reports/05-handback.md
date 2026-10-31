# 05 — Hand-back: index and registry seeding

Implementer: Opus, ticket 05, 2026-10-31. No git command was run. Nothing was written outside the worktree W and the scratch directory T. No file in another direction's directory, in `A/.scratch`, in `DC/outputs` or in memory was edited. Every RS command ran with `--root W/docs/research`.

## What changed

### Committed by the orchestrator from W

All paths are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/`.

- `INDEX.md`: the one-page entry point with the reading order, the spec §3 layout, path rules, the finding-id short names, the status vocabularies, ownership rules and protocol pointers.
- `FINDINGS.md`: a header paragraph and 51 rows across seven directions (18 sdr, 8 sel, 13 mech, 3 mds, 1 comp, 4 fmt, 4 ev5).
- `directions.json`: eight rows, written by `T/05/make_directions.py` with the RS JSON writer.
- `DIRECTIONS.md` and `SESSIONS.md`: rendered by `research-session render`.
- `ledger.json`: the global roll-up, rendered by `research-session ledger-rollup`.
- `selective-deception/ledger.json`, `mechanism-analysis/ledger.json`, `mechanism-datasets/ledger.json` and `sdr-mechanism/ledger.json`: converted by `T/05/convert_ledgers.py` with the RS JSON writer. The directory `mechanism-datasets/` is new and holds only this file, as spec §3 allows for a paused direction.
- `autoresearch-workflow/reports/05-handback.md` (this file) and `autoresearch-workflow/issues/05-index-and-registry-seeding.md` (status, checkboxes and comments).

### Staged in S

Nothing. This ticket has no op file.

### Scratch files in T

Helper scripts in `/u/swong2/.claude/jobs/b2cb53cd/tmp/05/`: `list_manifests.py` (legacy manifests and their commits), `ledger_keys.py` and `ledger_values.py` (legacy ledger shapes and value sets), `convert_ledgers.py`, `make_directions.py`, `check_paths.py` (every evidence, report and status-source path), and the staged copies `FINDINGS.txt`, `INDEX.txt` and `handback.txt`. The Write tool refuses Markdown deliverables from a subagent, so each Markdown file was written in T and copied into W with `cp`.

## How verified

### validate

```
research-session validate W/docs/research/FINDINGS.md W/docs/research/directions.json W/docs/research/ledger.json W/docs/research/{sdr-mechanism,selective-deception,mechanism-analysis,mechanism-datasets}/ledger.json
.../FINDINGS.md: valid
.../directions.json: valid
.../ledger.json: valid
.../sdr-mechanism/ledger.json: warning: totals.reserved_gpu_hours is 39.5333 but the rows give 0; the next RS ledger write recomputes it
.../sdr-mechanism/ledger.json: warning: totals.actual_gpu_seconds is 9409 but the rows give 0; the next RS ledger write recomputes it
.../sdr-mechanism/ledger.json: valid with 2 warning(s)
.../selective-deception/ledger.json: valid
.../mechanism-analysis/ledger.json: valid
.../mechanism-datasets/ledger.json: valid
```

The two warnings are expected, because the ticket asks for `reservations: []` with prose totals for sdr-mechanism. `held_out.json` does not exist in W, because ticket 04 has not landed it, so it was not validated.

### findings-check

```
research-session findings-check --root W/docs/research
findings-check: 0 error(s), 0 warning(s)
```

No row is `verified` or `replicated`, so no row needs a commit-naming provenance file.

### Render and roll-up byte stability

The first runs wrote the files. Hashes after the first runs:

```
f0277e1f679701d9854a95021772ce4a7aeb4afe934216c3a0012e0dcf4ba28c  DIRECTIONS.md
f0529596df209b80884af63c326ff11451896b00200b69c05575058c66d49061  SESSIONS.md
f7f5c42967e526eae48823d0cfa2e2b84ea233dfbb0cb19442eac97044bb2c04  ledger.json
```

Second runs:

```
research-session render --root W/docs/research
.../DIRECTIONS.md unchanged
.../SESSIONS.md unchanged
research-session ledger-rollup --root W/docs/research
.../ledger.json unchanged (6 directions)
```

The hashes after the second runs are identical to the three above.

### Paths

```
python3.9 -B T/05/check_paths.py
status_source sdr-mechanism          W        docs/research/sdr-mechanism/README.md
status_source selective-deception    W        docs/research/selective-deception/README.md
status_source mechanism-analysis     W        docs/research/mechanism-analysis/synthesis.md
status_source mechanism-datasets     DC-outside-repo ../.agents/memory/mechanism-datasets-plan.md
status_source component-analysis     DC-outside-repo ../.agents/memory/main-merge-261018.md
status_source format-control         DC-outside-repo ../.agents/memory/format-control-run-state.md
status_source eval5-grader-fixes     DC-outside-repo ../.scratch/eval5-grader-fixes/spec.md
status_source autoresearch-workflow  W        docs/research/autoresearch-workflow/WORKLOG.md
rows checked: 51
resolved in DC: 18 distinct paths
resolved in DC-outside-repo: 32 distinct paths
resolved in W: 38 distinct paths
--- missing: 0
```

The script resolves each path against W, then against DC. The 18 paths that resolve only in DC are ignored outputs under `outputs/_analyses/`, `outputs/_studies/`, `outputs/eval5_format_sdr_coarse/` and `outputs/llama-8b-instruct_sdr_coarse/_launch/`. The 32 paths that start with `../` resolve from the DC root into the Alignment checkout: 30 under `../.scratch/`, one memory note (`../.agents/memory/eval5-grader-fixes-pending.md`) and one research note under `../project_context/`. The full list is printed by the script.

### Lint and secret scan

```
python3.9 -B S/.../research_session/cli.py lint W/docs/research/INDEX.md W/docs/research/FINDINGS.md W/docs/research/SESSIONS.md W/docs/research/DIRECTIONS.md
(no output, exit 0)
```

The same lint on the six JSON files reports no secret rule. It does report join failures, because a JSON file is one long unit; JSON is outside the glue-lint scope of spec §5.5, so these are not failures of this ticket.

### Size

```
wc -c INDEX.md FINDINGS.md SESSIONS.md DIRECTIONS.md
 5060 INDEX.md
25235 FINDINGS.md
  522 SESSIONS.md
 2647 DIRECTIONS.md
```

INDEX plus FINDINGS plus SESSIONS is 30,817 bytes, which is about 7,704 tokens by bytes divided by four, under the 30,000 limit.

### Spot checks of claims against their sources

- The component-analysis role split of 22, 15 and 3 heads was checked in `outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/result_summary.md`, lines 197 to 199.
- The 0.494 and 0.967 sufficiency figures were not in that summary. They come from `outputs/llama-8b-instruct_sdr_coarse/_launch/wave_status.md`, lines 38, 40 and 52, so the claim is F-sdr-018 with that evidence.
- The format-control verdicts (c) for FAR and fine SDR, the coarse (b) verdict and its numbers were checked in `../.scratch/format-control/reports/09-final-report.md`, lines 20, 21 and 120.
- The selective-deception ledger rows reproduce the README's totals exactly: 38.35 reserved GPU-hours and 45,167 actual GPU-seconds.

## Execution evidence

Not applicable: no runs. No Slurm job, GPU job or paid API call was made.

### Decisions taken (part of What changed)

1. **Evidence outside DC.** Paths that live only in the Alignment checkout are written relative to the DC root with a leading `../`, so they resolve from the repository root. I did not copy the reports' own `../../.scratch/...` links, which resolve to a nonexistent `docs/research/.scratch` from the report directory. These `../.scratch/` paths keep resolving after ticket 10 migrates the directories, because each becomes a symlink.
2. **Status sources outside W.** mechanism-datasets, component-analysis and format-control use their memory notes, and eval5-grader-fixes uses its `.scratch` spec, all through `../`. No W file justifies their status.
3. **mechanism-datasets is `paused`.** The memory note's latest entry, of 2026-10-25, records tickets 05 and 06 as done and says "Awaiting user direction". Its `.scratch` RESUME, written 2026-10-21, still says training was not started, and the MEMORY.md index line says training awaits the user's go. Both are stale, so I used the memory note as the status source.
4. **Future directories.** `dir` for component-analysis, format-control and eval5-grader-fixes points at `docs/research/<slug>`, which does not exist yet. INDEX.md says so. `archive` for sdr-mechanism is empty until ticket 10 runs.
5. **autoresearch-workflow row.** I wrote `status: active` directly, because `claim` sets `claimed`. `claimed_at` is `2026-10-31T09:05:00-04:00`, the start time in the WORKLOG head. `do_not_touch` lists the live-session paths of R28 and `outputs/_studies/` and `outputs/_analyses/`, so SESSIONS.md shows them.
6. **Commit column.** Only one seeded run has a legacy `manifest.json` naming a 40-hex commit: the routing pilot's stage 1 retry, commit f7cb49f. F-sdr-011 carries that commit and the manifest in its evidence. It stays `reviewed`, because the manifest does not record a dirty flag and I did not re-derive the number from the run directory. Every other row is `pre-manifest`. No `manifest.json` under the mechanism-analysis outputs or the suites names a commit.
7. **No `refuted` rows.** A refuted prediction is written as a reviewed claim of what was found, so every pre-manifest row stays at most `reviewed` as R16 requires.
8. **Ledger conversion.**
   - Legacy statuses were upper-cased onto the spec vocabulary, and the converter stops if any value does not map. All mapped except one.
   - One mechanism-datasets row with status `submit-failed`, no job id and 0 reserved GPU-hours was dropped, which changes no total.
   - `cluster` comes from the list each row was in. `source_commit` is the legacy `source_revision` for selective-deception and null for the two mechanism ledgers, whose rows record source file hashes, not commits.
   - Caps: selective-deception keeps 40 GPU-hours, $20 and 2 concurrent jobs. mechanism-analysis gets 53 GPU-hours, the sum of its 18-hour Delta cap and 35-hour Bridges-2 cap. mechanism-datasets gets 81 GPU-hours, its 60-hour Delta cap plus 21 hours of Bridges-2 allocations. No API cap or concurrency limit is stated for either, so both are 0, which blocks new spend until a session sets them with `worklog-set`.
   - API spend: selective-deception has one aggregate row dated 2026-10-26 for its 1,113 paid OpenRouter attempts and $4.18 known cost, with the $0.66 reserve in totals. mechanism-datasets has its 13 OpenRouter rows merged by date into 3.
   - sdr-mechanism totals are the per-phase figures stated in the nine phase reports: 142,320 reserved GPU-seconds, which is 39.5333 GPU-hours, and 9,409 actual GPU-seconds, all single-GPU and $0 API. The native-controls figure of 84,000 includes 39,600 seconds cancelled before any attempt, which the policy keeps reserved. The routing pilot counts the 4,800 seconds used, not its 7,200-second envelope. `sdr-assay-diagnosis` has no ledger and no stated cost.
   - What could not be converted: the eight prose `ledger.md` files hold per-job lines in glued text, so no reservation rows were built from them. Per-cluster caps, allocation histories and the selective-deception API attempt detail have no field in the schema.

## What is NOT done

- `held_out.json` was not validated, because it does not exist in W.
- The ledger roll-up includes `_templates/ledger.json` as a sixth direction named `example-direction`. This is a defect in ticket 03's `rollup`, whose glob `*/ledger.json` should skip directories that start with `_`. The template row is all zeros, so the totals are right. I did not hand-edit the RS-rendered file or the RS code.
- SESSIONS.md shows the state `running`, not "no state yet" as the ticket expected, because `autoresearch-workflow/state.json` now exists. Its last worklog entry shows "none yet" because that `state.json` has `last_worklog_entry_at: null`, although `worklog.json` exists.
- If a session runs `ledger add` on sdr-mechanism, RS will recompute its totals from the empty reservation list and lose the 39.53 GPU-hours. A resuming session should first record the historical total as rows, or RS should gain a carried-total field.

### Findings seen in the sources and not seeded

- **Selective-deception literature and planning notes** `astra_review.md`, `necessity_prior_art.md`, `next_steps.md` and `shared_components.md`: these review other work or plan next steps and make no project claim.
- **Selective-deception `project_evidence.md` knockout table:** seeded once as F-fmt-003 under format-control, which produced the numbers.
- **SDR mechanism investigation status report:** it summarizes the other SDR reports, whose claims are seeded from the primary reports.
- **SDR routing pilot details:** the six-candidate and two-selector interaction of minus 0.740 and the half-dose shared-32 results, left out to keep one row per main result.
- **SDR position and audit details:** the factual-transfer conditional profile, the cross-hardware replay of 1,654 of 1,664 rows, the post-hoc factual-role transfer of the native evidence audit, and the cue probe's per-cue flip counts. These are exploratory or post-hoc.
- **Selective-deception secondary results:** the V5 sandbagging quality warning, convincing-game and MASK inspections, the V6 L13H23 to L17H27 path, V7 natural release of L17H27, the V3 restricted W13 mask, and the 24 of 28 all-head mask heads outside the original union. These were left out for size; each is in the same report as a seeded row.
- **Mechanism-analysis synthesis rows** H7, H9, A3, B3, B4, C2, C5, P1, P2 and D1, and the descriptive and exploratory readings E1 to E19 other than E1 and E18. The synthesis says descriptive readings decide nothing, and the omitted predictions are minor, untested or sanity checks.
- **Mechanism-datasets details:** the D minus H home-task flip audit, whose output sits in the mechanism-datasets worktree that I did not verify, the result that H alone deceives on SDR at 0.905, and the pilot-selection confound.
- **Component-analysis tooling:** its 17 tickets built tools rather than claims; only the D and H core role split is seeded.
- **Work outside the eight directions:** the memory notes on the coarse SDR seed wave, the EVAL 5 honest wave, the cross-task rerun of 2026-09-22 and the deception-circuits survey. They have no direction row, so a synthesis session should decide whether they become `proposed` rows.
- **`sdr-assay-diagnosis`:** it has no report in DC, and I read no bulk files from it.

## Open questions

1. Should the roll-up glob skip `_templates`, and should ticket 03 fix it before ticket 10 edits the registry?
2. The ledgers now carry Slurm account names, job ids and absolute output paths into `docs/research/`, which is pushed to a public repository. The spec §4.4 example includes an account name, so I treated this as allowed. The secret scan passes. Confirm that this is acceptable.
3. Should the ledger schema gain a way to carry legacy totals without reservation rows, so the sdr-mechanism totals survive the next RS ledger write?
4. Three status sources are memory notes, which are ignored and local. When ticket 09 or 12 rewrites those notes, the status sources may need to move to the migrated `.scratch` copies.
5. R39 says no RS-owned file is created by hand, but RS has no command that converts a legacy ledger or seeds the registry. `init` would have created `state.json`, `worklog.json`, `RESUME.md` and `WORKLOG.md` for paused directions, which spec §3 does not allow. I therefore wrote the four ledgers and `directions.json` by script with the RS writer and validator. Should ticket 03 or 12 add a `ledger import` command so this is never done by script again?
6. `findings-check` resolves evidence against `--repo`, which defaults to two levels above `--root`. From this worktree, the `../.scratch/` paths and the ignored `outputs/_analyses/` paths do not resolve there. It passed today because no row is `verified`. The first session that promotes F-sdr-011 must run it from DC main or pass `--repo` with the DC path.
