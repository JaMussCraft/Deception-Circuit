# Independent arithmetic audit plan

2026-10-25. Preparation only. No study outcomes were available or read. The arithmetic checker imports only Python standard-library modules and is independent of production implementation. The prospective specification is `.scratch/sdr-cue-followup/spec.md`; exact reviewed spec/checker/test hashes are in `handcase-pass.json`. All files produced here belong only to this audit directory.

## What is prepared

`independent_arithmetic.py` computes binary endpoint indicators directly from input factors and adjudicated semantic labels. It never accepts production-computed indicators, means, contrasts or selected eligibility populations as its oracle. Exact `fractions.Fraction` arithmetic averages variants within each fixture, then gives each expected fixture equal weight. Output serializes rationals as numerator/denominator pairs.

For each fixed indicator, with I=intact recipient, E=early, T=tail, F=full, the independent formulas are E-I, T-I, F-T, F-E and F-E-T+I. These are computed separately for S and C_S, followed by S-minus-C_S for every endpoint and contrast. Symbols E/T here denote position cells only; task axes remain explicitly recorded as E/report, T/report and T/retrieval.

Truth and example anchors are reconstructed from recipient input factors. Under a truth donor, D=1-recipient truth; under an example donor, D=recipient truth. Donor example-first reverses recipient example order only under E. Anchors remain fixed across the four factorial cells and the donor's emitted answer never defines an identity anchor. Retrieval has no ER/ED indicators. All nine mutually exclusive categories, any noncommitment and independent format_ok are retained. Noncommitments have zero identity matches and remain in denominators.

The checker generates overall task-axis summaries, both reciprocal directions, fixtures, templates, each single input factor and the four crossed example/truth-versus-lexical alignments. Its three intervention arms include complete zero-inclusive81-cell transitions and729-cell intact-recipient/intact-donor/intervention triples. Missing expected fixtures produce explicit missing support and null aggregate effects, rather than silently changing fixture weights. Raw supported/unsupported strata remain visible.

## Normalized input contract

Input is a JSON array with exactly one record per `(pair_id,family)`. A complete real panel will have1,280 such records representing640 pairs and both S/C_S. Each record contains:

- `pair_id`, `family` (`S` or `C_S`), `fixture_id`, `template`, `axis` (`E` or `T`).
- `factors`: recipient `truth`, `example_order`, `record_order`, `question_order`, `favored`, `task`. Binary values are integer0/1; retrieval has example_order=null.
- `labels`: exactly `base`, `early`, `tail`, `full`, each with `kind`, `candidate`, `format_ok`.
- `donor_label`: the fresh intact donor label with the same three fields.

`kind` is `commitment` or one of `explicit_refusal`, `coherent_evasion`, `qualified_ambiguous`, `contradictory`, `malformed`, `capped`, `error_missing`. Commitment candidate is lexically anchored integer0/1; every residual candidate is null. format_ok is Boolean and never gates semantic inclusion.

The checker rejects duplicate/unmatched S/C_S pair records, changed anchors or baselines across comparator families, malformed labels and invalid task-axis combinations. It does not read model activations, determine semantic labels or establish provenance by itself. Its CLI accepts the normalized array and writes the exact summary JSON, binding normalized-input and checker hashes.

Example invocation after actual data arrive:

`python3 .scratch/sdr-cue-followup/scientific-audit/independent_arithmetic.py normalized-actual.json exact-actual-summary.json`

## Steps deferred until actual joined data arrive

1. Obtain the frozen new protocol/input manifests, source/import closure hashes, original parent manifest, completed assembly/control receipt, two independent annotation files plus adjudications, blind-view mapping and actual joined rows. Record exact file bytes/hashes. This preparation has not verified those future artifacts.
2. Independently check all384 unique baselines and3,840 planned interventions, exact4,224 row IDs, all640 directed pairs,528 batch identities, original S/C_S memberships, both families, three positions and all required numerical controls. Check fresh baseline reuse by ID rather than text or observed outcome. Confirm the frozen eight-fixture universe and calibration exclusion before calling the arithmetic code; the CLI alone cannot detect a fixture absent from the entire supplied input.
3. Write a small audit-owned adapter from frozen manifests plus joined labels to the contract above. Do not import production analysis or copy its computed anchors. Reconstruct donor/recipient relationships and input factors from immutable inputs. Independently apply the archived finish-state rule for capped/error labels, verify commitment candidate semantics, and bind each label to the original blinded view/adjudication. Keep all residuals and planned rows. Check1,280 records and per-family256/256/128 task-axis counts. Check equal panel support in each frozen input-defined stratum.
4. Run this checker. Check exact identities among the five contrast formulas, S-minus-C_S components, category partition sums, inventory totals/marginals and reciprocal-direction totals. Compare production counts and rational quantities directly. If production exposes floating means, preserve the exact expected rational and the production value and report any discrepancy explicitly; do not silently relax tolerance or replace an exact denominator with rounded text.
5. Reconstruct natural baseline unordered pairs separately from the baseline manifest:128 E/report,128 T/report,64 T/retrieval. Count both endpoints and same/flip/residual states with original denominators. This preparation's pair-family checker does not yet implement that baseline-manifest adapter; actual manifest structure is pending.
6. Bind all final report/table bytes and independently verify every quoted count/direction/denominator against audited arithmetic. Fresh-versus-parent reproducibility comparisons remain descriptive and cannot delete rows or substitute historical answers. Distinguish fixed comparator evidence, position replacement effects, scientific assumptions and unsupported claims. All old behavioral failures remain failed.

## Hand-derived checks

`test_independent_arithmetic.py` covers13 cases: ceiling effects; signed cancellation/antagonism; interaction range reaching±2; fixed truth/example anchors; all seven residuals; unequal fixture counts; unequal counts inside a single input-factor stratum; reciprocal E directions; reciprocal T retrieval directions; format changes without semantic filtering; exact1/3 S-minus-C_S arithmetic; missing fixture support; duplicate/unmatched/changed-input rejection; complete zero-inclusive inventories. Tests began with unimplemented functions and failed10/10 before implementation; `handcase-red.log` preserves that receipt. All13 current cases pass in `handcase-green.log` and `handcase-pass.json`.

Passing these hand cases verifies the prepared arithmetic tool, not the new experiment. Full-panel provenance, numerical integrity, annotations, actual arithmetic comparisons and scientific narrative review remain pending.
