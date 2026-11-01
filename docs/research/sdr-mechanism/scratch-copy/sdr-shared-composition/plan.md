# Shared-component composition implementation plan

> For agentic workers: use subagent-driven-development with task review and a final whole-change review. Root owns exact-file git mutations.

**Goal:** Test how earlier shared heads, same-layer H26 and L17 attention interfaces jointly affect original native SDR reporting choices.
**Architecture:** One additive study runner reusing existing native fixture/map construction, activation replacement hooks and fixed-shape FP32-readout decoding; no changes to archived runners. Independently frozen input manifest, numerical/runtime audit and semantic/quantitative analysis.
**Tech stack:** Existing Python3.9 and mgnpPython3.12 environments, PyTorch/NNsight/Transformers as pinned in the final manifest, Delta Slurm for model execution.
**Spec:** spec.md, ratified after independent scientific-design-review.md PASS.

## Global constraints

- Worktree /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot, base expected4f0278487b0285dd27cbc34d20d88c911dc5562a. Preserve all old source and evidence; no merge/push/cleanup.
- Ownership: one implementation worker owns only scripts/sdr_shared_composition.py, scripts/jobs/run_sdr_shared_composition.sh, tests/test_sdr_shared_composition.py. Root may amend this exact list prospectively if a small second module materially improves clarity.
- Original native archived prompts, forced assistant stems and IDs. No new prompted behavior gate or success filtering. The stopped named-consequence assay stays stopped.
- All MLPs evolve naturally; only explicit source and receiver banks intervene. No reuse of the old full-freeze direct-edge capture as natural induced-state capture.
- Fixed source masks use mapped common original prefix positions; receiver masks use original recipient prefix. Generated/padded positions excluded. B8/L224/cap64, cache disabled, full FP32 vocabulary readout.
- GQA K/Vgroup6 belongs to queryheads24–27. SourceU5 excludes same-layerL17H26. SeparateQ24,K6,jointQK,V6,H24output,quartetoutput and fixedoutsideK comparisons as prospectively specified.
- Source/protocol/model cache/software bindings before model execution. Self/empty/repeat controls and same-shape firststep/actualgeneratedID identity; nonfinite/identity failures stop acquisition.
- No notebooks/models on login, no paid APIs, no Bridges2 or other-thread jobs. No worker git or worker-spawned reviewers.
- Runtime forecast based on observed similar jobs; per-batch deadline checks and atomic accepted records. Explicit verified resume only. Whole-panel runtime extrapolation is advisory after admission.

## Review focus

1. Differently masked source versus receiver banks must retain their own positions; no generated-token replacement or padding leak.
2. Natural induced receiver bank must capture the freely evolving U5 run, without freezing other heads/MLPs and without accidental donor/recipient bank interchange.
3. Q/K/V GQA indexing and H24 versusquartet assignment must match actual tensors and source-layer ordering.
4. Accepted checkpoint/resume and provenance mismatch must not silently rerun accepted rows, omit caps or overwrite failure evidence.
5. EOS firststep must match same-shape firsttoken intervention, including full-vocabulary FP32 selection, not historical differently shaped precision outputs.

## Task1 — additive causal composition runner

- [x] Read exact ratified spec and seam note; record baselineHEAD and existing tests relevant to reuseddecoder/hooks.
- [x] Write focused red tests for input-defined coverage, exact20arm bank definitions and U5/H26/U6 partitions, different per-bank positions, correctQ/K/V/head slices, generated-token exclusion, naturalinduced capture plan, strict resume/provenance failures and firststepidentity. Use meaningful toy/hook fixtures; do not load model on login.
- [x] Implement minimal freeze/dry-run/run/export/analyze interfaces needed for the exact study, reusing existing primitives; no generalized framework or oldcode edits. Exact CLI and output schemas must be documented in implementation-report.md.
- [x] Run targeted tests in base and mgnp, ruffF/shellsyntax; exercise the actual absolute jobwrapper CPUdryrun.
- [x] Generate final inputfreeze, check fullcoverage/maps/masks/tokenfit and sourceclosure; provisional uncommitted freeze clearly marked and replaced by committed final binding.
- [x] Write implementation-report.md with commands/results/hashes/limitations and a complete diff review package.
- [x] Independent Soltaskreview (spec+quality); fix reviewed findings with covering tests, scoped rereview.
- [x] Root exact-filecommit, fresh Astrawholechange review, final source/inputrebind and wrapperCPUdryrun before operatorrelease.

## Task2 — acquisition, interpretation and report

- [x] Operator records fresh queue/collision check, prospective timing/calibration plan and ledger. Calibration rows excluded from main scientific aggregation.
- [x] Run small numerical/timing calibration without outcome-based armselection; submit complete frozenmain panel with justifiedwalltime. Explicitresume only if needed and verified.
- [x] Independent raw/runtime audit of coverage, records, source/protocol bindings, numericalchecks and real scheduleraccounting.
- [x] Export complete question-aware blind views; two fresh personal Solraters, resolve fulltuple disagreements without condition/fact/headlabels. Retain allrows includingcaps.
- [x] Independent arithmetic uses normalized row/labeldata and handchecked examples; report rawchoices, margins, fixed interactions and blocked effects byaxis/direction. Avoid mediatedfractions/automaticsemanticroles.
- [x] Synthesize causal constraints, nulls and remaining gaps in concise userreport and standalone scientificfigure if useful; independent narrative review.
- [x] Update live memory/coordination/RESUME and compactioncount (only actual lead compactions). Preserve oldreports/gates unchanged.


Completed after final root verification; see completion-receipt.json. No outstanding required work.
