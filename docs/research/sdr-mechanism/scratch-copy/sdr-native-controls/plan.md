# Native SDR Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or executing-plans task-by-task. Root coordinates the authorized worker/reviewer workflow and all git; implementers do not integrate independently.

**Goal:** Prospectively measure native consequence-sensitive result selection with matched adverse/neutral and factual controls, before any causal intervention.

**Architecture:** One additive runner owns CPU freeze, calibration, full main completion, blind-view export, label join and behavioral gate analysis. Reuse immutable shape-generic model/hooks primitives; do not reuse the completion diagnostic's parent-bound manifest/replay/runtime contract. One wrapper handles operations separately from scientific payload.

**Tech Stack:** Existing Python/pytest, torch, transformers, nnsight, cached Llama tokenizer/model; no new dependencies.

**Spec:** `.scratch/sdr-native-controls/spec.md` (read with `data-and-code-seam.md`). Paths below relative to the existing `Deception-Circuit/.claude/worktrees/sdr-routing-pilot` worktree at parent `b7299d8`.

## Global constraints

Additive files only; preserve all old source/manifests/results.3,072 main rows,64 calibration rows excluded from analysis,64-token cap, batch8, frozen audited L, zero paid APIs/notebooks. No causal grid/training/merge/push. Scientific payload excludes allocation ceilings; wrapper/ledger owns operations. New namespace: `outputs/_analyses/sdr-native-controls/<mode>-<source>-<UTC>/`, refuse nonempty output paths.

## Review focus

- Historical literal grammar differs from current generator; byte tests preserve `.THE`, lab wording, manual shell and independently crossed facts/order.
- Excluding old survivors is selection; selection reads pools only and logs overlap afterward without changing the panel.
- Fixed slots, right-padding, EOS/cap and last logical-token readout must hold after mixed early finishes; every planned ID remains.
- Semantic labeling must reject quoted/retracted identities and retain refusal, evasion, contradiction, missing and capped responses separately.
- Calibration/hash provenance and allocation ceilings must not silently mutate scientific payload, source binding or final denominator.

### Task 1: Complete additive behavior protocol

**Files:** Create `scripts/sdr_native_controls.py`, `scripts/jobs/run_sdr_native_controls.sh`, `tests/test_sdr_native_controls.py`. No parent modifications. Worker is not alone; preserve others' edits. Root owns commits and review release.

**Consumes:** Immutable `component_analysis.hooks.load_analysis_model`, `capture_forward`, `READOUT_KEY`, `readout_logits`; shape-generic `scripts.sdr_routing_pilot.capture_logits`, `numerical_receipt` where suitable. Use literal renderer, pool files and cached tokenizer/config directly; never old `run_diagnostic`, `build_completion_manifest`, parent replay receipts or outcome-filtering dataset builder.

**Produces (runner interfaces):** `build_protocol(pool_root: Path, cache: Path) -> dict`; `verify_protocol(protocol: dict) -> None`; `make_batch(rows: list[dict], *, batch_size: int, sequence_length: int, device: str) -> tuple`; `complete_batch(model, rows: list[dict], protocol: dict) -> list[dict]`; `run_calibration(protocol: dict, output: Path, operations: dict) -> dict`; `run_main(protocol: dict, output: Path, operations: dict) -> dict`; `export_blind_views(protocol: dict, generations: list[dict]) -> list[dict]`; `join_annotations(protocol: dict, generations: list[dict], annotation_paths: list[Path]) -> list[dict]`; `analyze_panel(protocol: dict, joined: list[dict]) -> dict`. Rows/receipts are JSON-serializable dictionaries; functions enforce spec schema and hashes. `make_batch` returns input IDs, attention mask and ordered real-row IDs; no CUDA/model calls in CPU freeze/export/join/analyze.

**CLI:** `--mode freeze|calibration|main|export-labels|analyze --output PATH`; freeze additionally `--cache PATH --pool-root PATH`; other modes `--protocol PATH`; calibration/main additionally `--operations PATH`; main additionally `--calibration PATH`; export/analyze additionally `--generations PATH`; analyze additionally repeatable `--annotations PATH` and optional adjudication file. `--dry-run` validates arguments/hashes/paths and renders command/forecast requirements without loading model or submitting jobs. Operational JSON declares approved actual hardware class, reserved seconds, explicit deadline and buffers; bind its hash separately, without changing scientific hash.

**Identity contract:** Implement the exact fixture/row/calibration-factor identities in spec.md; entity ranking uses the literal source `name` string, fixture IDs hash the specified domain/seed/template/entity/sorted-pair array, collisions abort. Add literal expected hash/ID fixtures and calibration-object key tests.

- [ ] Write/run failing renderer/selection tests: exact audit+lab strings, all96 factors/fixture,32 distinct main pairs,16/16 templates,34 disjoint main/calibration pairs,3,072/64 IDs, same clause-triplet bytes outside clause, factual/favored/order correctness, no outcome-file reads, unchanged panel after overlap logging, exact deterministic hash ranking, length failure abort and L rounding.
- [ ] Implement CPU protocol freeze/verification and schemas. Freeze calibration64 rows/8 batches and factor-level coverage, rubric, B/L/EOS, imported/model/tokenizer provenance. Tests require missing pools, source drift, protocol tamper, occupied output or mismatched config to fail explicitly.
- [ ] Write/run failing fake-model tests for slot retention, mixed EOS,64-token cap, right padding/dummies, full-FP32 vocabulary greedy choices, logical append/readout, all-row numerical coverage and nonfinite/tolerance/token failures; self-replacement excludes READOUT_KEY and captures natural readout separately. Implement minimal batch/completion/control logic using immutable hooks.
- [ ] Write/run failing operations tests: calibration cannot enter main/labels; maximum physical-forward timing plus full64-cap/control forecast precedes main; startup/I/O/shutdown buffers and operational deadline are explicit; scientific hash unchanged by operational reservation changes; main rejects calibration mismatches in payload, scientific source/import/model/tokenizer/config/software hashes, exact GPU class/name/capability/memory/count or B/L while allowing separately bound allocation changes; partial/error paths retain every ID; no implicit retries or outputs overwritten. Implement calibration/main and dry-run wrapper, with explicit submission cwd instead of spooled script path and guarded environment startup.
- [ ] Write/run failing export/join tests: exact view keys only (text, unordered options, finish, opaque ID), no factors/gold/parser proposals; duplicate restoration; missing/duplicate labels, provenance mismatch and disagreements block finalization until adjudicated. Cover quoted/rejected candidates and separate refusal/evasion/ambiguity/contradiction/cap categories through label fixtures; no substring correctness shortcut.
- [ ] Write/run failing analysis tests with constructed complete panels: each overall/block capability/effect threshold passes at boundary and fails below; template/wording/order reversal fails despite favorable aggregate; C-only refusal/cap deterioration fails the all-non-correct retrieval guard; both-comparator simultaneous band is reproducible; refusal cannot inflate correctness; all rows weight equally within fixture and fixtures equally overall;family-stratified10,000-bootstrap seed/index and all denominator/status counts are exact. Implement analysis and comprehensive status/report JSON with explicit `behavior_go` and failed criteria.
- [ ] Run focused suite in both supported base and mgnp environments with pinned BLAS threads, then relevant existing routing/completion tests; compare any known environment baseline failures by name. CPU-dry-run the actual wrapper for calibration and main using the frozen manifest. Independent reviewer checks source/spec/tests, exact historical examples, payload/provenance separation and full-cap forecast before root releases calibration. Root commits only the three named additive files after review fixes.

## Operational execution after source review (not another implementation task)

- [ ] Freeze CPU manifest and review selection/overlap/shape/rubric receipt; no model outcomes yet. Root reviews independent scientific critique before source/run release.
- [ ] Operator separately reserves/submits the single fixed64-row calibration, records actual allocation and all controls. Release main only after complete calibration, forecast and numerical receipts pass; failure preserves artifacts and stops for root review.
- [ ] Operator reserves main from full-cap measured forecast, runs3,072 rows under frozen source/payload; terminal integrity audit precedes blinded labeling. No new bridge rows.
- [ ] Export unique main views; two fresh independent annotators cover all views, a third adjudicates disagreements. Join all3,072 rows, execute frozen analysis, independently review final claims/costs and report every gate/stratum. Passing behavior does not run a causal grid; failed behavior is a complete report, not an implementation TODO.

Self-review: renderer/selection, runtime/numerics, scoring/joins, inference and operation contracts each map to Task1 tests above. No other source changes or independent subsystem needed. Execution method is already delegated; root reviews this concrete plan without reasking routine user approval.

Pre-inference ordering clarification: main execution uses native-controls-pair selection ranking; template ranking assigns family only. Calibration order remains audit then lab, hash order within fixture. Test exact agreement with independent selection-audit.json. Bootstrap within-family order follows main execution rank.
