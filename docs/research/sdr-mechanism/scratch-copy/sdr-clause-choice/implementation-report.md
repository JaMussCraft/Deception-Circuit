# Native clause-choice baseline implementation

Implementation owner: clause_choice_impl. Scope: three additive files in the existing isolated `Deception-Circuit/.claude/worktrees/sdr-routing-pilot` worktree, base `29492146127f56c05a4087b1bfdeea0e63a4d24a`. No original source/result changes, Git operations, subagents, model loading/inference, GPUs/jobs, APIs or notebooks were used. Root owns source commit, reviews and any allocation release.

## Deliverables

- `scripts/sdr_clause_choice.py`: metadata-only fixture selection, literal renderer/token freeze, baseline generation adapter, immutable acceptance/resume, full-response semantic export and all-row analysis.
- `scripts/jobs/run_sdr_clause_choice.sh`: absolute original-worktree/interpreter binding, offline flags and actual numeric Slurm start/end, with reviewed `scontrol`/local-time fallback.
- `tests/test_sdr_clause_choice.py`: focused CPU contracts, mocked numerical/generation tests and whole-panel failure/resume tests.

The runner exposes `freeze`, `run`, `export` and `analyze`. There is no conditional intervention execution command. Conditional head sets, Boolean masks and exact donor maps are frozen now; later patch execution remains separate and unreleased.

## Scientific and numerical contract

Original Arrow data is projected to entity, item names, template variant and instance IDs only. Fixture ranking uses the prescribed canonical SHA256 group rank, one global distinct-pair scan, nine groups per template, first eight main and ninth excluded preflight. All source IDs survive grouping. Main is exactly640 rows; preflight is exactly32 disjoint rows with order=`truth XOR target`.

Literal prompts use the archived manual chat shell, an empty assistant stem and no answer examples/date/template substitution. C/U differ only in the final `preserved` versus `wiped` predicate; facts, named target and task system bytes stay fixed. All672 natural prefixes are110–125tokens. All272 C/U pairs (256main,16preflight) have equal token counts/absolute token positions with predicate-confined differences. Character offsets after the edited word shift with that literal word's length; the CPU check normalizes that declared character-span shift and verifies the unchanged token geometry. No wording search, truncation or configurable decoder was needed.

The unchanged audited `scripts.sdr_cue_positions.decode_batch` runs intact at B8/L224/cap64. The adapter adds an independent same-path first forward with actual final-norm-input FP32 full-vocabulary readout. Per-row vector hash, argmax, top-two gap, physical slot, exact frozen input hash and true logical readout must agree with the decoder's actual repeat/empty control expected hashes and its first generated ID/readout. This receipt is numerical identity evidence, not a semantic candidate label. Full responses to EOS/cap remain intact; first-token EOS, mixed EOS, cap64, dummy slots and noncandidate full-vocabulary argmax are tested.

Every accepted batch atomically binds exact row membership, manifest hash, run/allocation/hardware receipt hash, complete generation state and actual numerical receipts. Accepted files are never overwritten. Explicit resume verifies all terminal/control/input/run bindings and skips only accepted batches. Numerical/provenance failure records prohibit resume. Operational timeout preserves partial state and permits a later root-released explicit invocation. Assembly retains unaccepted partial/error/missing rows with failure finish overrides; these cannot certify capability.

## Frozen conditional geometry

All768 pairs are input-defined:128 directed C-target-flip pairs per task and256 reciprocal C/U pairs per task. Scope is question CONTENT through its EOT, followed by the complete supplied assistant header/newlines; system and user header are excluded. Every row stores explicit224-element Boolean masks, absolute scope indices, exact scope text/token IDs and role labels. Every pair stores the exact recipient→donor absolute token map. Generated/padding/dummy positions are excluded.

Five head sets have sizes32/6/32/6/0: original S32, archived candidate6, archived C_S32, prospective outside6 and empty. Outside6 uses canonical JSON `['clause-choice-outside6',20261026,layer,head]`, ascending SHA256 per layer with candidate6 layer counts; excludes original D∪H∪F and named PILOT families including outside_mask2. Root ratified this already-written domain. The initial unexecuted overbroad exclusion of all outside comparator sets was corrected before any C6 draw/freeze/outcome; comparator overlap is allowed. Exact outside6 is `(12,15),(13,3),(13,27),(13,30),(14,22),(17,21)` and overlaps C_S32 at `(13,27),(14,22),(17,21)`. Rank traces, excluded heads, original mask/source bindings and exact lists/hashes are in the manifest. No independence of comparator draws is claimed.

## Runtime policy and reviewed timing fix

Actual execution requires the root-bound full source commit, matching source/cache/software/input reconstruction, and an actual900-second Slurm allocation. All checks precede model loading. The forward deadline is actual EndTime−90seconds (root's60shutdown+30assembly/audit reserve). After all32 excluded preflight rows, main admission requires `1.5 × remaining_main_batches × max_observed(decode+publication seconds) + 90 <= actual remaining allocation`; the initial remaining count is80. Slower main observations update the forecast. Each batch separately requires `1.5 × 67 × slowest_observed_forward_rate + 2 × max_publication_seconds` before the effective deadline. The67 forwards include64decode,2kernel controls and1external first-vector forward; rates include external and decoder/Python/control overhead. Signals/deadlines stop before subsequent forwards. There is no submission, automatic retry or automatic new allocation.

Independent code review found one real interruption gap: scientific acceptance preceded a separate mandatory timing file. The fix keeps accepted science authoritative and makes publication timing optional. Abrupt loss between accepted/timing files recovers decoder and forward durations already atomic with acceptance; unknown publication latency uses at least1second and the bound invocation's declared initial IO budget. Other observed slower publication times still govern the maximum. Optional timing publication OSError cannot invalidate a valid accepted terminal or poison resume. Valid accepted outcomes are neither rerun nor modified. Existing malformed timing receipts still fail integrity checks.

Two fault-injection tests first reproduced this defect (`test-timing-gap-red.txt`), then passed after the surgical accept/timing recovery change. One simulates an abrupt crash between files and verifies byte-identical accepted evidence; the other injects OSError for every optional timing publication, completes all672 fake responses, resumes with zero extra decode calls, and confirms all84 accepted terminal bytes remain identical.

The actual absolute wrapper CPU dry-run then exposed a separate JSON round-trip seam before loading any model or creating its run output. The archived PILOT head lists contained tuples in memory, while a saved/reloaded manifest contains lists. Literal rebuild equality therefore failed despite an identical canonical scientific hash. The focused failing test `test-json-roundtrip-red.txt` identified only `pilot_families` as different; that field is now normalized to JSON-native lists at its source. The failure log `wrapper-cpu-dryrun-timingfix.txt` is retained. This change preserves the exact scientific payload and all head identities/maps. The actual wrapper verification against regenerated `cpu-freeze-provisional-ready.json` now passes without loading a model or creating a run directory.

## Semantic exports and analysis

Public views contain only opaque view ID, exact user question, lexically sorted candidates, complete assistant response and finish. The question is necessarily visible; blinding is partial. System facts/condition/target/truth/head factors and other ratings stay hidden. Deduplication includes the exact question. No regex/parser supplies semantic labels. Two fresh independent raters must personally cover every unique view; complete label-tuple disagreements require a fresh third adjudicator. Annotation artifacts enforce exact coverage, protocol/export hashes, distinct reviewer identities, required independence attestation and the frozen empty-stem rubric. Cap/error/missing overrides early names. `names_only` and factual disclosure remain separate rater judgments.

Analysis restores all640 multiplicities, uses equal fixture weights and reports exact criterion counts, both template deltas, fixture contrasts, truth/order/template/conflict/aligned strata, complete C/U category transitions and refusal/disclosure inventories. Numerical/full-coverage controls and every prospective gate must pass before `proceed` is true. No individual/template filtering, prompt retuning, fake judgments, interpretation of harmless choice as demonstrated concealment, or automatic conditional release occurs.

## Verification and artifacts

Final source-bound CPU freeze and actual wrapper CPU dry-run are complete; exact hashes and commands are below. Earlier freezes are retained as superseded source preparations and must not be used for execution. All freezes remain explicitly `UNCOMMITTED`/provisional until root commits the exact reviewed source and reruns freeze with `--code-commit FULL_SHA`.

Final focused suite:31passed in both environments. Base:30.94seconds with its existing pandas/bottleneck warning (`test-base-ready.txt`); mgnp:24.93seconds without warnings (`test-mgnp-ready.txt`). Prior28/30-test receipts and both failing regression receipts remain retained. Static check: `/u/swong2/.local/bin/ruff check --select F scripts/sdr_clause_choice.py tests/test_sdr_clause_choice.py`; shell check: `bash -n scripts/jobs/run_sdr_clause_choice.sh`. No broad model suite or dependency installation was performed. The base environment emits its existing pandas/bottleneck version warning; mgnp has no such warning.

Final old-source audit `old-source-verification-ready.json` compares all63 files in the original frozen2949214 protocol's source closure: no mismatches. The independent input oracle separately reconstructed matching fixture selection, all672 lengths,272 C/U pairs,768 maps and corrected C6 without importing this builder.

Real GPU numerical controls, natural generation/runtime measurements and semantic judgments are still unexecuted. CPU readiness is not GPU release or evidence of behavioral support. Root/operator must finish independent review, commit/bind source, dry-run that committed binding, and release any actual allocation.

## Final CPU handoff

Ready provisional manifest: `cpu-freeze-provisional-ready.json` (5,504,970bytes). All earlier provisional freezes are superseded only for source binding and retained as preparation history. Scientific payload remains byte-canonically unchanged through both operational fixes.

| Binding | SHA256 |
|---|---|
| Ready manifest file | `b946754d989c5d795758a7282ea46d0a0026ba48f0fd9840f64b641d0df62eaa` |
| Manifest binding | `f2fed5e2e19660005aa4ded900b69b0e8916f1d36bde133e874c3cc2303bee39` |
| Scientific payload | `d22cb1edbb8ed2b3109c3142d74460da9aa360b4cfb4615e6b05d21e6ed94d7c` |
| New runner | `72bd5ac01e3d5cc4b481cb158c052af6a3bf42a06a7a5f657a692b80194f4d3e` |
| New wrapper | `2c3a771d9edd869042efcc81e117aa664961f655930adb123a44dbc1cc827fe3` |
| New tests | `f89b72d28e9cdc7d12bc490b3f15bcd0f0f0dd57b54acdfca2d2b466d1c66db8` |

`cpu-preparation-summary-ready.json` records the full length histogram, source/cache/software identities, model snapshot and source/spec/plan/rubric hashes. The final source closure has66files, with zero mismatches. All63 original source files match the authoritative frozen2949214 protocol. All256 directed target-flip pairs also happen to have equal measured prefix lengths (delta0); their exact absolute maps remain frozen rather than inferred later.

Commands actually verified from the assigned worktree:

```bash
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q tests/test_sdr_clause_choice.py
OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_sdr_clause_choice.py
/u/swong2/.local/bin/ruff check --select F scripts/sdr_clause_choice.py tests/test_sdr_clause_choice.py
bash -n scripts/jobs/run_sdr_clause_choice.sh
```

Actual new absolute-wrapper CPU dry-run (exit0), receipt `wrapper-cpu-dryrun-ready.txt`:

```bash
SDR_CLAUSE_CWD=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot \
SDR_CLAUSE_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python \
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/jobs/run_sdr_clause_choice.sh \
  run --dry-run \
  --protocol /projects/beto/swong2/Alignment/.scratch/sdr-clause-choice/cpu-freeze-provisional-ready.json \
  --output /projects/beto/swong2/Alignment/.scratch/sdr-clause-choice/unused-cpu-dry-run-ready
```

The receipt reports `status=cpu_dry_run`,640main/32preflight, maxprefix125, correct intact kernel, `model_loaded=false` and `output_mutated=false`; the output path is confirmed absent. No GPU behavior, preflight timing or semantic outcome is claimed.

Implementation CPU handoff: DONE. Remaining root-owned steps are independent final code review, exact three-file commit, new committed source binding and its verification, operator accounting/actual allocation release, and eventually two fresh semantic judgments. No job has been submitted and no conditional execution is authorized by this report.
