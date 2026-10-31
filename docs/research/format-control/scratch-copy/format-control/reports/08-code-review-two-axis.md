# Two-axis code review (mattpocock-skills:code-review) of format-control, 5b61031...e47daf3

Run 2026-10-15 by the orchestrator; Standards and Spec axes as parallel sub-agents.

## Standards

**Hard violations of documented standards:** none. The diff uses "Format Circuit", "Scaffold", "Pressure Clause", "nopressure" and "Template Variant" consistently with CONTEXT.md; the one ADR (component-analysis model loading) is untouched.

**Judgement calls: glossary wording**
- "control" as a loose term: CONTEXT.md lists `control` under _Avoid_ (Honest Condition; Format Circuit). In `evaluation/eval5_format_summary.py`, "First-order control", "Control suite", `--control` and `control_overlap` mean a comparison/reference suite, a different referent, so not a breach, but it reuses the ambiguous word next to a feature named "format-control". A name like "reference suite" would avoid the collision; `write_format_control_summary.py` rows also use a `control` key.

**Judgement calls: baseline smells**
- Duplicated Code: `_load`, `_role_of`, `_mean` appear verbatim in both `evaluation/eval5_format_summary.py` and `evaluation/format_control_summary.py`; `ROLES = ("D","H","F")` defined at least four times. Fix: one shared module. Risk: a label-suffix change (e.g. `_hko`) must be made in both copies.
- Duplicated Code in tests: `tok()` repeated in `test_build_nopressure.py` and `test_clause_surgery.py`; `_launch_module()` repeated in `test_format_control_eval5.py` and `test_format_control_launch.py`. Fix: conftest fixtures.
- Duplicated Code, sbatch builders: `sbatch_cmd` in both `eval5_cmd.py` and `fc_launch.py`; 13 `sys.path.insert` lines across the diff. Fix: one launcher helper module.
- Shotgun Surgery: suite names, NLS 0.3, family/task lists as literals in Python, shell and JSON (`PAIRED_NLS`, `SUITES_ROOT`, `TASKS=${TASKS:-"far sdr"}`, `FAMILY=…far|sdr|sdr_coarse`, `suites.json`, hard-coded `eval5_sdr_coarse_nls0.3_nomb_lb`). Fix: derive from `suites.json`.
- Primitive Obsession: roles, family strings, group strings and label suffixes (`__leaf`, `__head`, `_hko`) as plain strings parsed by repeated regex; a small `Cell`/label type would hold this once.
- Data Clumps: `sbatch_cmd(..., account, partition, time_)` and `eval5_cmd` scheduling fields travel together. Fix: a `SlurmSpec`.
- Divergent Change: `evaluation/format_control_summary.py` (47 top-level functions) mixes loading, aggregation, statistics and rendering; `test_format_control_eval5.py` has 90 tests. A split by concern would help.
- Mysterious Name: `tok`, `_mean`, `ctrl`, `nctl`, `sep`, `mx`.

## Spec

**(a) Missing or partial**
- Collateral term: spec "reference-NLL rise are no larger than the mechanism circuit's" (eval 5). EVAL 5 was not run for any family, so all three verdicts use eval 2 wikitext KL as the collateral term (the spec names it as the eval 2 collateral; the summaries state it; now recorded as a ruling in the ledger).
- (c) remedy: spec "retrain the Format Circuit at a lower NLS"; a lower NLS gives a larger circuit, so the remedy cannot apply to the oversized FAR F and the last commit replaces the sentence (spec sentence kept in decision.json as spec_sentence). Now recorded as a ruling; flagged to the researcher as a spec amendment to confirm.
- (c) definition: spec "destroys answering or coherence"; the code checks the KL gate and distinct-2 only; answering is covered indirectly by the honest-answer condition. Minor (the spec's own parenthetical limits (c) to those two checks).
- Retune on FAR: ran (NLS 0.4) but the 0.3 run is carried (ledger ruling).

**(b) Not asked for**
- Validation minimum 150 before accepting a threshold or skipping the fallback (spec names only train 150 / test 500). Ledger ruling exists (ticket 01).
- EVAL 5 overrides `--gate-override` and `--allow-rescreen` (spec: gated on the KL bar and the researcher's go-ahead only). Both record a written reason; ledger ruling exists for the gate override; allow-rescreen now recorded.
- GPU restriction: EVAL 5 limited to A40 (screen comparability), training to A40/H200 (A100 40 GB OOM); spec says "any partition". Now recorded as rulings.
- Extra machinery beyond the spec: a diagnose block and diagnostic caveats in the summary, a 1,264-line copy of flip_audit_analysis.py, a separate eval 5 summary module, a record file, condition tags in the generic suite/evaluate reports. Judgement: reasonable, but noted for the researcher.
- Coarse cells composed at leaf, not head (ledger ruling; legitimate).

**(c) Implemented but looks wrong or hollow**
- Coarse verdict (a) rests on honest-answer rows whose D/H/F drops are near identical (0.530 / 0.519 / 0.519; margin 0.011 < 1 binomial SE); the code's tolerance is 1e-9, so a no-uncertainty "F <= D" decides (a); the caveats disclose it but the verdict line still reads (a). (Pre-registered rule applied as written; the researcher reads the caveats.)
- FAR Format Circuit pairing: ~99% of its training data is honest-split; the spec's premise ("format under honest answering" on the same instances) does not hold for FAR, and its (c) says nothing about format. (Ledger ruling and finding.)
- Distinct-2 threshold 0.5 × full model: not in the spec; ledger ruling; labelled unregistered in every summary.

## Summary line
Standards: 0 hard violations, ~9 judgement-call smells (worst: duplicated helpers across the two summary modules). Spec: 0 missing deliverables; 4 deviations now all recorded as rulings; worst: the coarse (a) passes its honest-answer condition inside one binomial SE (disclosed by caveat, verdict unchanged by the pre-registered rule).
