"""
component_analysis — component-level analysis of discovered deception circuits.

The evaluator (`evaluate_circuit.py`) treats a circuit as an opaque set of
gates and asks whether it is faithful and necessary. This package zooms in: it
coarsens a circuit to its **Components** (attention heads and MLP blocks, in
the vocabulary of CONTEXT.md), and the later analyses — attention patterns,
direct logit attribution, logit lens, knockout, path patching — each add
namespaced columns to one head table keyed by Component.

Layout
------
    components.py   mask object -> Components (pure Python, no model)
    head_table.py   the one table every analysis writes into (CSV + JSON)
    intake.py       circuit / reference / task resolution and the cell layout
    segmentation.py prompt -> Segments (the spans an analysis aggregates over)
    sampling.py     the fixed-seed stratified sample the causal analyses use
    instances.py    the split's records, and segmentation.json / sample.json
    hooks.py        every nnsight call in the package, and nothing else

Only `hooks.py` imports nnsight, and it does so inside its functions, so the
rest of the package imports in the login-node base environment. That env has an
nnsight — 0.5.12, for the parent Alignment repo — but not the 0.7.0 ADR-0001
pins, which needs Python >= 3.10; the nnsight tests therefore gate on the
version being exactly 0.7.0 rather than on nnsight importing. The CLI is
`analyze_components.py` at the repo root, beside `evaluate_circuit.py`.

The package is named `component_analysis` rather than `analysis` because
`analysis.py` at the repo root is the node-mask extraction module and an
`analysis/` package would shadow it.
"""
