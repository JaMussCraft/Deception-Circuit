# Whole-study H100 Portability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans for the single task below. Root has selected delegated implementation; root reviews this plan before code and owns git. Do not ask the user to choose again.

**Goal:** Make the frozen complete cue-circuit study reproducible from an explicit destination root and Slurm allocation, with truthful60-file provenance and fresh H100 calibration readiness.

**Architecture:** Parameterize physical input resolution in the current runner, leaving source discovery relative to `__file__`. Make its existing shell wrapper portable and timezone-correct. Preserve every scientific calculation and extend its existing CPU contracts; snapshot transfer and resource release remain operator work rather than new application machinery.

**Tech Stack:** Existing Python/PyTorch/pytest, Bash, Slurm and installed base/mgnp environments; no new dependencies.

**Spec:** `.scratch/sdr-cue-circuits/spec.md` plus `.scratch/sdr-cue-circuits/fast-execution/amendment.md`.

## Global constraints

- ROOT from `Path(__file__).resolve().parents[1]`; input alignment root explicit, frozen in provenance and used again by exact rebuild verification. No environment variable may override frozen input resolution.
- Exactly3 existing cue files may change. All54 inherited source files and unchanged `analysis.py`, `config.py`, `l0.py` retain baseca41bfd bytes; new source binding totals60.
- Payload literal equality except individually enumerated physical mask-path leaves and `record_bounds`; publish honest old/new complete science hashes and an independent complete-core equality receipt.
-9,344 rows/1,168 B8/L224 batches/640 pairs/14 families/cap64, all controls/labels/analysis unchanged. No jobs/GPU/APIs/notebooks/install/environment mutation during implementation.
- Proposed snapshot destination `/ocean/projects/cis260361p/swong2/sdr-cue-circuits-20261024/Alignment/Deception-Circuit`; transfer only reviewed commit/input allowlist. Existing destination mgnp/cache read-only.
- Delta23162012 untouched. GPU release held for other-agent B2 capacity/budget clearance, independent release review and fresh zero-attempt cancellation gate. No sharding.

## Review focus

1. A frozen protocol replayed from another cwd or conflicting environment must resolve its frozen alignment root, never the old Delta tree.
2. A source binding missing any one newly discovered module must fail verification, even if all old57 hashes match.
3. Bridges-2 fallback Start/End displayed in Eastern must parse in Eastern despite a Chicago/UTC caller; epoch environment bounds take precedence.
4. Wrong wrapper cwd must fail before inference even if it contains a copied runner; the wrapper's own repository cwd must pass after relocation.
5. Input-core proof must reject every extra changed payload leaf beyond explicit physical mask paths/record_bounds; old parent bytes and all imported source bytes remain immutable.

### Task 1: Portable frozen-root rebuild, complete source binding and allocation wrapper

**Worktree:** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-cue-h100`, baseca41bfd. You are not alone in the codebase: preserve other agents' work, including old worktree/job state; do not revert unrelated changes.

**Files:**

- Modify `scripts/sdr_cue_circuits.py`: `select_families`, `build_protocol`, `verify_protocol`, `source_hashes`, freeze CLI.
- Modify `scripts/jobs/run_sdr_cue_circuits.sh`: own-cwd identity, explicit interpreter and raw allocation-time binding.
- Modify `tests/test_sdr_cue_circuits.py`: CPU relocation/provenance/wrapper regression coverage.

**Interfaces:**

- Freeze CLI consumes required `--alignment-root PATH` plus its existing parent/cache/spec/brief/output/commit arguments; use a resolved absolute path and reject missing/invalid roots before freeze publication.
- `build_protocol(..., alignment_root=...)` resolves only input paths from that explicit root; `select_families` receives the same root. Preserve existing function-call tests using a compatible explicit default for local legacy calls if needed; CLI must not infer destination from cwd/env. Store resolved `provenance['alignment_root']` and pass it into rebuild inside `verify_protocol`.
- `source_hashes()` returns the existing57 bindings plus ROOT-relative `analysis.py`, `config.py`, `l0.py`; exact source-set equality is mandatory.
- Wrapper consumes explicit `SDR_CC_PYTHON`, standard Slurm job/epoch variables and existing CLI. Existing local environment fallback may remain only if its behavior stays compatible; destination always supplies interpreter explicitly. It exports actual allocation start/end epochs and wrapper-entry epoch; Python retains existing proposal/actual duration and remaining-deadline validation.
- Wrapper resolves its own repo from `BASH_SOURCE[0]` and validates `pwd -P` against that repo; it does not silently cd from a wrong cwd. Prefer valid Slurm numeric epochs. For absent epoch fields, invoke `scontrol` and `date` with the **same** chosen cluster timezone; Bridges-2 uses `America/New_York`, Delta `America/Chicago`. Choose from explicit existing cluster binding (B2 operator supplies `DC_CLUSTER=bridges2`), not caller TZ. Mixed epoch/fallback fields must still describe one valid start/end pair. Reject unknown/nonfinite/reversed/future-start/expired or proposal-duration-incompatible allocation bounds before scientific attempts; subtract shutdown exactly once in the existing Python deadline contract.

- [ ] **1. Read and capture baseline.** Read worktree guidance and original spec/amendment. Record base/source file hashes and existing evidence for the45 cue regressions already verified in both environments at byte-identicalca41bfd; prove hash identity instead of rerunning the unchanged baseline. Do not execute notebooks/model loads. Confirm only the three assigned files are writable implementation scope.
- [ ] **2. Add failing CPU portability tests.** Test freeze/build at two fixture roots; identical complete scientific core with only explicit permitted path/ceiling changes; persisted alignment-root rebuild while cwd/env points elsewhere; missing/changed each of the3 added module hashes fails. Stub tokenizer/software/cache for unit tests rather than duplicate model loading.
- [ ] **3. Add failing wrapper tests.** Run actual shell wrapper with fake interpreter/Slurm tools: relocated own repo passes; unrelated cwd containing a runner fails; explicit interpreter bypasses environment activation; valid epoch bounds bypass fallback; Eastern fallback query/parse ignores callerChicago/UTC TZ and agrees with known UTC epoch; partial epoch fallback and Unknown/reversed/expired/duration mismatch fail before forwarding. Keep shell quoting tests for spaced paths.
- [ ] **4. Run new targeted tests red.** Verify failures name the missing portability/source/timezone behavior, not setup/import errors. All tests remain CPU-only.
- [ ] **5. Implement minimal three-file change.** Parameterize physical mask/audit roots without mutating global source ROOT; persist explicit root and rebuild it. Bind3 extra unchanged modules; preserve all inherited source checks. Update wrapper identity/time parsing/interpreter handling with no scheduler abstraction. Leave decoder, hooks, scientific schedule, controls, response generation, analysis, journal recipes and model/cache loading implementation unchanged.
- [ ] **6. Run focused tests green in both environments.** From exact new worktree with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`, run `/sw/external/python/anaconda3/bin/python3.9 -m pytest -q tests/test_sdr_cue_circuits.py` and `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_sdr_cue_circuits.py`. Expected all original45 regressions plus new contracts pass; do not reduce old coverage.
- [ ] **7. Exercise actual wrapper locally.** With the explicit mgnp interpreter only, build/verify destination-shaped CPU freezes and perform actual wrapper calibration/main `--dry-run` against fresh outputs. Preserve status `cpu_dry_run`, `numerical_pass=false`; no model or Slurm allocation. Run `bash -n scripts/jobs/run_sdr_cue_circuits.sh` and source diff checks. Record commands/results, not claims of remote readiness.
- [ ] **8. Independent review and byte proof.** Root assigns independent code/spec review and input audit. Enumerate all payload differences against original freeze; permit only exact physical mask-path leaves and record_bounds. Verify all other keys/values and all54 inherited+3 additional imported source files byte-identical to base,60-source set complete, parent/spec/rubric/audits bytes unchanged, source ROOT intact and no scientific kernel/control changes. Fix findings only within assigned three files, rerunning affected tests.
- [ ] **9. Root commit and snapshot manifest.** Hand root exact three-file diff/test receipts for commit. Rebuild provenance under reviewed local commit; create transfer allowlist/manifest as operator artifacts, not extra application code. Include only60 sources plus required immutable input files at relative destinations; bind sizes/hashes/roles, full new science/provenance hashes and local commit. No remote Git or broad worktree/output copy. Source modifications after freeze invalidate release and require re-review/refreeze.

## Operator continuation after the engineering task

These are release prerequisites, not additional code tickets and not GPU authorization.

- [ ] Validate unique remote path/resource/interpreter/cache/space first; resolve other-agent Bridges-2 capacity/budget concern before GPU release. Operator quotes available SU and proposed incremental reservations using the independently verified site charge rate and primary charging-policy evidence; the rate/capacity audit is pending. Do not guess budget or borrow another investigation's reservation.
- [ ] Transfer exact allowlist into fresh destination; independently verify all60 source hashes,10 model/tokenizer/config/weight hashes, software metadata and input/manifest hashes. No package installs/shared-environment mutation. Build destination-specific freeze and independent complete-core proof; run destination CPU verify and actual wrapper calibration/main dry-runs. Stop on software/path/hash mismatch rather than editing imports/environment opportunistically.
- [ ] Root releases a separately reviewed fresh H100 calibration proposal only after readiness/capacity evidence. Operator decides1–2h duration using measured startup/I/O evidence. Require112 rows/14 batches/5,460 forwards/29,232 controls and all bounded stress/whole-decode checks; independent full receipt/Slurm/forecast review follows.
- [ ] Use fresh complete-cap forecast and live capacity to propose one whole-study main;10/12h allowed if fit/account headroom supports them. No inference from old H200/typical EOS lengths. Recheck Delta state and prove no attempted rows; cancel only when replacement viable and root activates it, retaining terminal zero-attempt receipt. If Delta started, continue old main and do not duplicate.
- [ ] Release matching-runtime H100 main only after all gates. Preserve full single-run output and original downstream labels/analysis/reviews. No sharding, partial salvage, automatic retry, merge or push.

**Handoff:** One cohesive task, delegated implementation and independent review as already selected. Root reviews this plan before code. Resource gates stay held; no additional user permission flow is introduced.
