# Original SDR shared-component evidence map

2026-10-26. Read-only reconnaissance plus retrospective CPU arithmetic; no inference, notebooks, jobs, git operations or archived-artifact edits. Scope is the original coarse D/H/F masks and native SDR evidence. Ordinary-task reuse does not disqualify a component from a compositional deception explanation. This document distinguishes a constrained computation from an established psychological role.

## Exact evidence anchors

Resolve relative paths from `/projects/beto/swong2/Alignment`.

- Native pilot source: `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/sdr_routing_pilot.py` (Stage2 source `6a2ea52`). Core primitives: the same worktree's `component_analysis/path_patching.py:644` (`receiver_inputs`) and `:665` (`readout_from_receivers`).
- Immutable Stage1 directory: `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z` (manifest, baseline.jsonl, maps, patch plan).
- Immutable Stage2 directory: `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-pilot/stage2-main-6a2ea52-20261021T005608Z` (comparisons.jsonl, grid.json, provenance.json, numerical_controls.json, gate.json, story_bootstrap.json). Gate says 51,136/51,136 rows, 0 unmeasured; 544 available donor pairs, 32 excluded pairs, 39 path cells, readout/common sender scopes. Calibration excluded.
- Native analyses: `.scratch/sdr-routing-pilot/{stage1-analysis,stage2-analysis,stage2-analysis-plan}.md`; later source/semantics audit `.scratch/sdr-behavior-identification/analysis.md` and `exploratory-role-addendum.md`.
- Frozen summaries: `project_context/reports/SDR routing pilot findings.md`, `SDR native evidence audit.md`, `SDR cue-circuit transplant findings.md`, `SDR shared-head position findings.md`.

Mask source registry is `Deception-Circuit/outputs/_launch_format_control/suites.json`, key `format-control-sdr-coarse-nls0.3`. D/H/F each read `active_nodes.json` under `Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/`, respectively:

- D: `nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742` (69 heads).
- H: `nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743` (56).
- F: `nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850` (68).

S32=D∩H∩F; D∩H=43; A22=D−H−F; B11=(D∩H)−F; J33=D−F=A∪B. Use saved `active_heads`; do not inherit all-MLP operands through head-level mask composition.

## Components and constrained causal roles

| Component | Existing intervention evidence | Role constrained; unresolved composition |
|---|---|---|
| candidate6 = L12H6,L13H5,L13H20,L13H21,L14H24,L17H26 | All six are in S32. Changed-truth H/N→P same-false-emission stratum corrects margin +1.762 on confirmation; native common patches switch 151/312 baseline-disagreement cases and change 44/232 same-emission cases. | Influences answer processing beyond universal emitted-item copying. Counterexamples all change facts; fixed-fact same-emission changes 0/40. Does not identify truth-selection policy or pure clause route. |
| L12H6,L13H20,L13H21 → L17 Kgroup6 | Confirmation same-false-emission margin +.147,+.201,+.181; positive discovery and H/N separately. Effects collapse for readout-only sender injection. | Context-position perturbations reach key input used by query heads24–27. Compatible with changing what is attended to; not uniquely H24, not a demonstrated abstract selector. Strong evidence is content-confounded. |
| L13H5 → L17H24 Q | Confirmation +.096 in same-false-emission stratum; readout-only +.098 survives. L14H24→Q also +.085 common. | A head-specific query-input route can transmit the tested perturbation. Need show that route is used in freely evolving native replacement and how it combines with key/content input. |
| L17H24,L24H27 (selector2) | Necessary on D and H in earlier component analysis; large paired DLA differentials; native ordinary replacement has substantial effects. Stage2 Q/K/V tests on both receivers, with leading effects at L17 rather than L24. | Late shared answer influence, compatible with selection or output transport. DLA/necessity do not choose roles. L24 null/weak direct edges leave multihop/MLP mediation open. |
| L17H26 | Included in candidate6 and S32; Stage2 omits L17H26→L17Q/K/V because same-layer edges cannot exist. Can reach L24 receivers/readout; direct readout same-false confirmation +.015. | Cannot be described as an upstream cause of L17H24 Q/K. For an L17 dependency experiment use earlier5 or the fixed Ksender3, and state that this is a new joint intervention, not measured candidate6 mediation. |
| outsider2 = L15H8,L17H25 | Both in D but outside D∩H. Candidate+outsider replacement also interferes (same-false confirmation DID−1.120); outsider alone +.848. | Converging conditional influences exist beyond named shared senders/receivers. “Outsider” is a mask-relative name, not inert control; outside_mask2=L17H18,L12H19 is separate. |
| S32 | Native baseline-disagreement common replacements follow donor296/312, preserve16; same-fact H→P restores34/48, P→H loses36/37 accessible truths. Neutral E/T replacement largely reproduces D/H/F; early/tail head-output positions contribute differently. | Reused cue/content processing distributed across prefix positions. Literal donor identity transfer predominates in native fact flips (276/288); ordinary reuse is evidence about computation, not exclusion from a deception mechanism. Sender-to-reader composition within S32 is still missing. |
| A22,B11,J33 | Neutral E transplant: donor-example choices A11/256, B144/256, J102/256 versus intact46/256; signed effects recur across fixtures. Native J knockout strong (.119 accuracy versus matched-null p5 .517). | Exclusive mask pieces can have opposite signed effects under replacement. Overlap subtraction alone assigns no psychological role; neutral effects do not establish native clause mediation. |

## What Stage2 actually did

“Clean” means the native recipient, which can be pressured; “corrupt” means donor, which can be H/N. Neither is intrinsically truthful. Score is recipient-truth minus other-item logit, patched minus recipient baseline. All MLPs are active in ordinary model execution.

1. Capture recipient embedding, every head output and every MLP output. Capture donor sender heads on donor tokens. A semantic map includes only exact matching named token spans; pressure clause is omitted. Common scope includes matched intro/items/question/stem/readout; readout scope includes the final supplied token.
2. Fill selected sender tensor with mapped donor values and recipient baseline everywhere else. In pass1 inject this sender, while every other component output is clamped to its recipient capture. Capture the selected Q/K/V projection or final-norm input. Q/K are pre-RoPE, with recipient positional geometry. This isolates a direct residual interface under a full freeze.
3. In pass2 run recipient with only the captured receiver tensor inserted; downstream computation evolves freely. **Primary receiver replacement covers all recipient positions.** The preparatory seam's suggested key/query masks are not the executed policy: `receiver_position_mask` exists but is unused; actual `grid.json` says `primary full recipient positions; no optional position followups`.

K/V group6 changes heads24–27 at its layer, Q changes one head. They differ in intervention size. The 39-cell grid is 6 senders×7 receivers minus three invalid same-layer L17H26→L17 cells. Single-sender direct paths cannot be summed or divided by family effects to obtain mediated fractions.

Ordinary candidate, selector, outsider, unions and half-dose S32 use masked donor head-output replacement without the full freeze. Unmapped sites retain the evolving current state. The candidate+selector union inserts **donor selector output**, not recipient-baseline Q/K. Its negative DID (−.740 in diagnostic confirmation) can reflect overwriting the state that otherwise responds to the candidate. It does not establish natural redundancy, competition or a serial mechanism.

## Retrospective support and fixed-cell check

The following CPU-only arithmetic reads exact `manifest.json`/`baseline.jsonl` and completed `comparisons.jsonl` rows; it creates no new inferential confirmation. All96 native primary-P fixed-fact units choose harmless by historical selection. N chooses damaging78/96 (discovery38/48, confirmation40/48); H74/96 (33/48,41/48). Thus no need to require a pristine new prompt setup to investigate the original effect.

Previously measured schedule includes one same-fact P/N truth per story: 48 directed P←N pairs, plus reciprocal N←P; N is damaging39/48 (19/24,20/24); 9/48 have equal baseline emissions. P/H same-fact donor truth is37/48. The other truth variant is available as a baseline but was not patched in that same-fact schedule. P0↔P1 contributes96 directed pairs across48stories; all change facts and retain the same pressure clause/ID, all donor emissions differ from recipient, all equal recipient damaging identity. Their aliases cannot separate literal copying from factual-role transfer. Alternative P wording was baseline-only.

Confirmation/common retrospective fixed-cell means below average eligible rows within story then stories; each P←N column has24rows/24stories and P←P48rows/24stories. No outcome-based row selection. These are existing direct-frozen-path effects, not new effects or natural-path estimates.

| Existing family/path | P←N same facts: Δmargin | P←P fact flip: Δmargin | Distinct-donor switches, clause / facts |
|---|---:|---:|---:|
| L12H6→L17K6 | −.012819 | +.159704 | 0/24;0/48 |
| L13H20→L17K6 | +.011908 | +.211810 | 0/24;0/48 |
| L13H21→L17K6 | +.004895 | +.183615 | 0/24;0/48 |
| L13H5→L17H24Q | +.026130 | +.069519 | 0/24;0/48 |
| Ordinary candidate6 | +1.403017 | +2.385862 | 11/24;41/48 |
| Ordinary selector2 | +1.330332 | +1.679078 | 13/24;27/48 |

The clause route is therefore **not already explained by the strongest content-diagnostic K links**. A new free-background dependency test could still reveal joint or multihop dependence, but must admit small/null clause-only dependence as a discriminating result. Preserve full split/support and baseline-denominator counts rather than choosing successful patch rows.

## Recommended next measurement

In the original fixed native pair schedule, perturb pre-L17 shared senders while letting the rest evolve, then selectively restore recipient-baseline L17K6 and/or L17H24Q. Include baseline, sender-only, receiver-clamp-only, joint sender+clamp, identity/sham and a matched other receiver; compare the interaction on paired rows. Predeclare Ksender3={L12H6,L13H20,L13H21} as a known-interface test, or earlier5 as a broader shared-family test. Do not call candidate6 wholly upstream of L17. Test same-fact P↔N separately from same-pressure fact flips, retaining all frozen pairs. Measure margin and first-token identity; a bounded EOS extension can connect to actual native disclosure commitments if its patch timing is explicit.

This adds the missing link: whether a measured receiver input is required for an upstream replacement's effect in a freely evolving original SDR computation. A reduction under baseline restoration supports conditional receiver dependence; it is still intervention-relative, not proof of unperturbed pressure mediation. Nulls can separate the existing content route from a different clause pathway. Ordinary task/retrieval reuse is acceptable; it should clarify carried information and contextual readout rather than act as a specificity gate. Refusal and semantic validity remain reportable, but the closed named-consequence failed gate is not a prerequisite for this original-native composition test.
